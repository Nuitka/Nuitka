#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Helper functions for the scons file."""

from __future__ import print_function

import os
import pickle
import signal
import sys

from nuitka.__past__ import (  # pylint: disable=redefined-builtin
    FileNotFoundError,
    basestring,
    unicode,
)
from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.Progress import enableThreading
from nuitka.PythonFlavors import isTermuxPython
from nuitka.Tracing import scons_details_logger, scons_logger
from nuitka.utils.Execution import executeProcess
from nuitka.utils.FileOperations import (
    changeFilenameExtension,
    deleteFile,
    getExternalUsePath,
    getFileContentByLine,
    getFilenameExtension,
    getNormalizedPath,
    getNormalizedPathJoin,
    getWindowsShortPathName,
    hasFilenameExtension,
    isFilesystemEncodable,
    openPickleFile,
    openTextFile,
    withFileLock,
)
from nuitka.utils.Utils import isLinux, isMacOS, isPosixWindows, isWin32Windows


def initScons(arguments):
    # Set the arguments.
    _setArguments(arguments)

    # Avoid localized outputs, spell-checker: ignore VSLANG
    os.environ["LC_ALL"] = "C"
    os.environ["VSLANG"] = "1033"

    def no_sync(self):
        # That's a noop, pylint: disable=unused-argument
        pass

    # Avoid scons writing the scons database at all, we don't care for it,
    # spell-checker: ignore dblite
    import SCons.dblite  # pylint: disable=I0021,import-error

    try:
        SCons.dblite.dblite.sync = no_sync
    except AttributeError:
        SCons.dblite._Dblite.sync = no_sync  # pylint: disable=protected-access

    # We use threads during build, so keep locks if necessary for progress bar
    # updates.
    enableThreading()


scons_arguments = {}


def _setArguments(arguments):
    """Decode command line arguments."""

    arg_encoding = arguments.get("argument_encoding")

    for key, value in arguments.items():
        if arg_encoding is not None:
            value = decodeData(value)
        scons_arguments[key] = value


def setupScons(env, source_dir):
    env["BUILD_DIR"] = source_dir

    # Store the file signatures database with the rest of the source files and
    # make it version dependent on the Python version of running Scons, as its
    # pickle is being used, spell-checker: ignore sconsign
    sconsign_filename = os.path.abspath(
        getNormalizedPathJoin(
            source_dir, ".sconsign-%d%s" % (sys.version_info[0], sys.version_info[1])
        )
    )

    env.SConsignFile(sconsign_filename)


def getArgumentRequired(name):
    """Helper for string options without default value."""
    return scons_arguments[name]


def getArgumentDefaulted(name, default):
    """Helper for string options with default value."""
    return scons_arguments.get(name, default)


def getArgumentInt(option_name, default=None):
    """Small helper for boolean mode flags."""
    if default is None:
        value = scons_arguments[option_name]
    else:
        value = int(scons_arguments.get(option_name, default))

    return value


def getArgumentBool(option_name, default=None):
    """Small helper for boolean mode flags."""
    if default is None:
        value = scons_arguments[option_name]
    else:
        value = scons_arguments.get(option_name, "True" if default else "False")

    return value.lower() in ("yes", "true", "1")


def getArgumentList(option_name, default=None):
    """Small helper for list mode options, default should be command separated str."""
    if default is None:
        value = scons_arguments[option_name]
    else:
        value = scons_arguments.get(option_name, default)

    if value:
        return value.split(",")
    else:
        return []


def enableFlagSettings(env, name, experimental_flags):
    for flag_name in experimental_flags:
        if not flag_name:
            continue

        flag_name = "%s-%s" % (name, flag_name)

        if "=" in flag_name:
            flag_name, value = flag_name.split("=", 1)
        else:
            value = None

        # Allowing for nice names on command line, but using identifiers for C.
        flag_name = flag_name.upper().replace("-", "_").replace(".", "_")

        # Experimental without a value is done as mere define, otherwise
        # the value is passed. spell-checker: ignore cppdefines
        if value:
            env.Append(CPPDEFINES=[("_NUITKA_%s" % flag_name, value)])
        else:
            env.Append(CPPDEFINES=["_NUITKA_%s" % flag_name])


def _prepareFromEnvironmentVar(var_name):
    mingw_mode = False
    zig_mode = False

    # Add environment specified compilers to the PATH variable.
    if var_name in os.environ:
        scons_details_logger.info("%s='%s'" % (var_name, os.environ[var_name]))

        os.environ[var_name] = os.path.normpath(
            os.path.expanduser(os.environ[var_name])
        )

        if os.path.isdir(os.environ[var_name]):
            scons_logger.sysexit(
                "Error, the '%s' variable must point to file, not directory." % var_name
            )

        if os.path.sep in os.environ[var_name]:
            cc_dirname = os.path.dirname(os.environ[var_name])
            if os.path.isdir(cc_dirname):
                addToPATH(None, cc_dirname, prefix=True)

        if os.name == "nt" and isGccName(os.path.basename(os.environ[var_name])):
            scons_details_logger.info(
                "Environment %s seems to be a gcc, enabling mingw_mode." % var_name
            )
            mingw_mode = True

        if isZigName(os.path.basename(os.environ[var_name])):
            scons_details_logger.info(
                "Environment %s seems to be a gcc, enabling zig_mode." % var_name
            )
            zig_mode = True

    return mingw_mode, zig_mode


def _prepareEnvironment(mingw_mode):
    mingw_mode_from_env, zig_mode = _prepareFromEnvironmentVar("CC")
    _prepareFromEnvironmentVar("CXX")

    if mingw_mode_from_env:
        mingw_mode = True

    return mingw_mode, zig_mode


def createEnvironment(
    mingw_mode,
    msvc_version,
    clang_mode,
    clangcl_mode,
    target_arch,
    consider_environ_variables,
    assume_yes_for_downloads,
    source_dir,
):
    # Many settings are directly handled here, getting us a lot of code in here.
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements

    # Zig compiler mode usually from the option --zig.
    zig_exe_path = getArgumentDefaulted("zig_exe_path", None)

    # Prepare environment for compiler detection.
    if consider_environ_variables:
        mingw_mode, zig_mode_env = _prepareEnvironment(mingw_mode=mingw_mode)
    else:
        zig_mode_env = False

    zig_mode = zig_mode_env or zig_exe_path

    from SCons.Script import Environment  # pylint: disable=I0021,import-error

    args = {}

    if msvc_version == "list":
        import SCons.Tool.MSCommon.vc  # pylint: disable=I0021,import-error

        scons_logger.sysexit(
            "Installed MSVC versions are %s."
            % ",".join(repr(v) for v in SCons.Tool.MSCommon.vc.get_installed_vcs()),
        )

    # If we are on Windows, and MinGW is not enforced, lets see if we can
    # find "cl.exe", and if we do, disable automatic scan.
    if (
        os.name == "nt"
        and not mingw_mode
        and not zig_mode
        and msvc_version is None
        and msvc_version != "latest"
        and (getExecutablePath("cl", env=None) is not None)
    ):
        args["MSVC_USE_SCRIPT"] = False

    if mingw_mode or zig_mode or isPosixWindows():
        # Force usage of MinGW64, not using MSVC tools.
        tools = ["mingw"]

        # This code would be running anyway, make it do not thing by monkey patching.
        import SCons.Tool.MSCommon.vc  # pylint: disable=I0021,import-error
        import SCons.Tool.msvc  # pylint: disable=I0021,import-error

        SCons.Tool.MSCommon.vc.msvc_setup_env = lambda *args: None
        SCons.Tool.msvc.msvc_exists = SCons.Tool.MSCommon.msvc_exists = (
            SCons.Tool.MSCommon.vc.msvc_exists
        ) = lambda *args: False
    elif zig_mode:
        tools = ["gcc"]
    else:
        # Everything else should use default, that is MSVC tools, but not MinGW64.
        tools = ["default"]

    env = Environment(
        # We want the outside environment to be passed through.
        ENV=os.environ,
        # Extra tools configuration for scons.
        tools=tools,
        # The shared libraries should not be named "lib...", because CPython
        # requires the filename "module_name.so/pyd" to load it, with no
        # prefix at all, spell-checker: ignore SHLIBPREFIX
        SHLIBPREFIX="",
        # Under windows, specify the target architecture is needed for Scons
        # to pick up MSVC.
        TARGET_ARCH=target_arch,
        # The MSVC version might be fixed by the user.
        MSVC_VERSION=msvc_version if msvc_version != "latest" else None,
        **args
    )

    env.source_dir = source_dir
    env.assume_yes_for_downloads = assume_yes_for_downloads

    if zig_exe_path:
        env["CC"] = zig_exe_path
        env["CXX"] = zig_exe_path
        env["LINK"] = zig_exe_path
        env["CCVERSION"] = None

        # escape backslashes for SCons string interpolation^
        safe_zig_path = zig_exe_path.replace("\\", "\\\\")

        # spell-checker: ignore CCCOM,CFLAGS,CCFLAGS,CCCOMCOM,CXXCOM,CXXFLAGS
        # spell-checker: ignore LINKCOM,LIBDIRFLAGS,LIBFLAGS,SHCCCOM,SHCFLAGS
        # spell-checker: ignore SHCCFLAGS,SHCXXCOM,SHCXXFLAGS,SHLINKCOM,SHLINKFLAGS

        env["CCCOM"] = (
            '"%s" cc -o $TARGET -c $CFLAGS $CCFLAGS $_CCCOMCOM $SOURCES' % safe_zig_path
        )
        env["CXXCOM"] = (
            '"%s" c++ -o $TARGET -c $CXXFLAGS $CCFLAGS $_CCCOMCOM $SOURCES'
            % safe_zig_path
        )
        env["LINKCOM"] = (
            '"%s" cc -o $TARGET $LINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS'
            % safe_zig_path
        )
        env["SHCCCOM"] = (
            '"%s" cc -o $TARGET -c $SHCFLAGS $SHCCFLAGS $_CCCOMCOM $SOURCES'
            % safe_zig_path
        )
        env["SHCXXCOM"] = (
            '"%s" c++ -o $TARGET -c $SHCXXFLAGS $SHCCFLAGS $_CCCOMCOM $SOURCES'
            % safe_zig_path
        )
        env["SHLINKCOM"] = (
            '"%s" cc -o $TARGET $SHLINKFLAGS $__RPATH $SOURCES $_LIBDIRFLAGS $_LIBFLAGS'
            % safe_zig_path
        )

        scons_details_logger.info("Overridden with Zig compiler: %r" % zig_exe_path)

    if consider_environ_variables:
        scons_details_logger.info("Initial CC: %r" % env.get("CC"))
        scons_details_logger.info(
            "Initial CCVERSION: %r" % (env.get("CCVERSION"),),
        )

        if "CC" in os.environ:
            # If the environment variable CC is set, use that.
            env["CC"] = os.environ["CC"]
            env["CCVERSION"] = None

            scons_details_logger.info("Overridden with environment CC: %r" % env["CC"])
        elif clangcl_mode:
            # If possible, add Clang directory from MSVC if available.
            addClangClPathFromMSVC(env=env)
        elif clang_mode and not mingw_mode:
            # If requested by the user, use the clang compiler, overriding what was
            # said in environment.

            env["CC"] = "clang"
            env["CCVERSION"] = None

    # Various flavors could influence builds.
    env.monolithpy = getArgumentBool("monolithpy", False)
    env.debian_python = getArgumentBool("debian_python", False)
    env.fedora_python = getArgumentBool("fedora_python", False)
    env.arch_python = getArgumentBool("arch_python", False)
    env.msys2_mingw_python = getArgumentBool("msys2_mingw_python", False)
    env.anaconda_python = getArgumentBool("anaconda_python", False)
    env.pyenv_python = getArgumentBool("pyenv_python", False)
    env.apple_python = getArgumentBool("apple_python", False)
    env.self_compiled_python_uninstalled = getArgumentBool(
        "self_compiled_python_uninstalled", False
    )

    # No need to pass it from the outside, this cannot use other
    # Pythons for scons.
    env.android_termux_python = isTermuxPython()

    # Non-elf binary, important for linker settings.
    env.noelf_mode = getArgumentBool("noelf_mode", False)

    # Python specific modes have to influence some decisions.
    env.static_libpython = getArgumentDefaulted("static_libpython", "")
    if env.static_libpython:
        assert os.path.exists(env.static_libpython), env.static_libpython

    # Python version we are working on.
    env.python_version_str = getArgumentDefaulted("python_version", None)
    if env.python_version_str is not None:
        env.python_version = tuple(int(d) for d in env.python_version_str.split("."))

        # Do we have a GIL build, or no-GIL (free-threading)
        env.gil_mode = getArgumentBool("gil_mode")

        # Python debug mode: reference count checking, assertions in CPython core.
        env.python_debug = getArgumentBool("python_debug", False)

        # The Python ABI flags to target.
        abiflags = getArgumentDefaulted("abiflags", "")

        if not env.gil_mode and "t" not in abiflags:
            abiflags = "t" + abiflags

        # Python version with ABI included.
        env.python_abi_version = env.python_version_str + abiflags

        # Home of Python to be compiled against, used to find include files and
        # libraries to link against.
        env.python_prefix = getArgumentRequired("python_prefix")

        env.python_prefix_external = getExternalUsePath(env.python_prefix)
    else:
        env.python_version = None

        env.gil_mode = None

        env.python_debug = None

        env.python_abi_version = None

        env.python_prefix = None
        env.python_prefix_external = None

    # Modules count, determines if this is a large compilation.
    env.compiled_module_count = getArgumentInt("compiled_module_count", 0)

    # Target arch for some decisions
    env.target_arch = target_arch

    # Standalone mode
    env.standalone_mode = getArgumentBool("standalone_mode", False)
    if env.standalone_mode:
        env.Append(CPPDEFINES=["_NUITKA_STANDALONE_MODE"])

    # Onefile mode: Create suitable for use in a bootstrap with either dll or
    # exe mode.
    env.onefile_mode = getArgumentBool("onefile_mode", False)
    if env.onefile_mode:
        env.Append(CPPDEFINES=["_NUITKA_ONEFILE_MODE"])

    # Onefile temporary mode: The files are cleaned up after program exit.
    env.onefile_temp_mode = getArgumentBool("onefile_temp_mode", False)
    if env.onefile_temp_mode:
        env.Append(CPPDEFINES=["_NUITKA_ONEFILE_TEMP_BOOL"])

    # Module (or package) mode: Create a Python extension module
    env.module_mode = getArgumentBool("module_mode", False)
    if env.module_mode:
        env.Append(CPPDEFINES=["_NUITKA_MODULE_MODE"])

    # DLL mode: Create a DLL using Python
    env.dll_mode = getArgumentBool("dll_mode", False)
    if env.dll_mode:
        env.Append(CPPDEFINES=["_NUITKA_DLL_MODE"])

    # EXE mode: Create an EXE (using Python for this config)
    env.exe_mode = getArgumentBool("exe_mode", False)
    if env.exe_mode:
        env.Append(CPPDEFINES=["_NUITKA_EXE_MODE"])

    # MacOS bundle: Create an .app on macOS
    env.macos_bundle_mode = getArgumentBool("macos_bundle_mode", False)
    if env.macos_bundle_mode:
        env.Append(CPPDEFINES=["_NUITKA_MACOS_BUNDLE_MODE"])
        env.Append(LINKFLAGS=["-framework", "CoreFoundation"])

    # Announce combination of DLL mode and onefile mode.
    env.onefile_dll_mode = env.onefile_mode and env.dll_mode
    if env.onefile_dll_mode:
        env.Append(CPPDEFINES=["_NUITKA_ONEFILE_DLL_MODE"])

    env.forced_stdout_path = getArgumentDefaulted("forced_stdout_path", None)
    env.forced_stderr_path = getArgumentDefaulted("forced_stderr_path", None)

    env.build_definitions = {}

    return env


def decodeData(data):
    """Our own decode tries to workaround MSVC misbehavior."""
    try:
        return data.decode(sys.__stdout__.encoding)
    except UnicodeDecodeError:
        import locale

        try:
            return data.decode(locale.getpreferredencoding())
        except UnicodeDecodeError:
            return data.decode("utf8", "backslashreplace")


def getExecutablePath(filename, env):
    """Find an execute in either normal PATH, or Scons detected PATH."""

    if os.path.exists(filename):
        return filename

    # Variable substitution from environment is needed, because this can contain
    # "$CC" which should be looked up too.
    while filename.startswith("$"):
        filename = env[filename[1:]]

    # Append ".exe" suffix  on Windows if not already present.
    if os.name == "nt" and not filename.lower().endswith(".exe"):
        filename += ".exe"

    # Either look at the initial "PATH" as given from the outside or look at the
    # current environment.
    if env is None:
        search_path = os.environ["PATH"]
    else:
        search_path = env._dict["ENV"]["PATH"]  # pylint: disable=protected-access

    # Now check in each path element, much like the shell will.
    path_elements = search_path.split(os.pathsep)

    for path_element in path_elements:
        path_element = path_element.strip('"')

        full = getNormalizedPathJoin(path_element, filename)

        if os.path.isfile(full):
            return full

    return None


def changeKeyboardInterruptToErrorExit():
    def signalHandler(
        signal, frame
    ):  # pylint: disable=redefined-outer-name,unused-argument
        sys.exit(2)

    signal.signal(signal.SIGINT, signalHandler)


def setEnvironmentVariable(env, key, value):
    if value is None:
        del os.environ[key]
    elif key in os.environ:
        os.environ[key] = value

    if env is not None:
        # pylint: disable=protected-access
        if value is None:
            del env._dict["ENV"][key]
        else:
            env._dict["ENV"][key] = value


def addToPATH(env, dirname, prefix):
    # Otherwise subprocess will complain in Python2
    if str is bytes and type(dirname) is unicode:
        dirname = dirname.encode("utf8")

    path_value = os.environ["PATH"].split(os.pathsep)

    if prefix:
        path_value.insert(0, dirname)
    else:
        path_value.append(dirname)

    setEnvironmentVariable(env, "PATH", os.pathsep.join(path_value))


def writeSconsReport(env, target):
    with openTextFile(
        _getSconsReportFilename(env.source_dir), "w", encoding="utf8"
    ) as report_file:
        # We are friends to get at this debug info, pylint: disable=protected-access
        for key, value in sorted(env._dict.items()):
            if type(value) is list and all(isinstance(v, basestring) for v in value):
                value = repr(value)

            if not isinstance(value, basestring):
                continue

            if key.startswith(("_", "CONFIGURE")):
                continue

            # Ignore problematic and useless values
            # spell-checker: ignore MSVSSCONS,IDLSUFFIXES,DSUFFIXES
            if key in ("MSVSSCONS", "BUILD_DIR", "IDLSUFFIXES", "DSUFFIXES"):
                continue

            # TODO: For these kinds of prints, maybe have our own method of doing them
            # rather than print, or maybe just json or something similar.
            print(key + "=" + value, file=report_file)

        print("gcc_mode=%s" % env.gcc_mode, file=report_file)
        print("clang_mode=%s" % env.clang_mode, file=report_file)
        print("msvc_mode=%s" % env.msvc_mode, file=report_file)
        print("mingw_mode=%s" % env.mingw_mode, file=report_file)
        print("clangcl_mode=%s" % env.clangcl_mode, file=report_file)

        print("cpp_flags=%s" % (env.cpp_flags or ""), file=report_file)
        print("c_flags=%s" % (env.c_flags or ""), file=report_file)
        print("cc_flags=%s" % (env.cc_flags or ""), file=report_file)
        print("cxx_flags=%s" % (env.cxx_flags or ""), file=report_file)
        print("ld_flags=%s" % (env.ld_flags or ""), file=report_file)

        print("PATH=%s" % os.environ["PATH"], file=report_file)
        print("TARGET=%s" % getNormalizedPath(target[0].abspath), file=report_file)


_checked_msvc_language_pack = False


def reportSconsUnexpectedOutput(env, cmdline, stdout, stderr):
    # Singleton, pylint: disable=global-statement
    global _checked_msvc_language_pack

    if not _checked_msvc_language_pack and env.msvc_mode and (stderr or stdout):
        _checked_msvc_language_pack = True

        cl_path = getExecutablePath(env.the_compiler, env=env)
        bin_dir = os.path.dirname(cl_path)
        eng_dir = os.path.join(bin_dir, "1033")

        if not os.path.exists(eng_dir):
            scons_logger.warning(
                """\
Support language of Nuitka is English. Please install the English \
language pack for Visual Studio in the installer. There is a \
section for that."""
            )

    if env.warn_error_mode and stderr is not None:

        if (
            # gcc does this: "all warnings being treated as errors"
            "all warnings being treated as errors" in stderr
            or
            # clang does this, spell-checker: ignore Werror
            "[-Werror," in stderr
            or
            # macOS clang does this: "warnings generated"
            "warnings generated" in stderr
        ):
            scons_logger.sysexit(
                "Error, C warnings occurred with '--debug' or '--debug-c-warnings', use '--no-debug-c-warnings' or fix them."
            )

    with withFileLock("writing scons error report"):
        file_handle, pickler = openPickleFile(
            _getSconsErrorReportFilename(env.source_dir), "ab", protocol=2
        )
        pickler.dump((cmdline, stdout, stderr))
        file_handle.close()


_scons_reports = {}
_scons_error_reports = {}


def flushSconsReports():
    _scons_reports.clear()
    _scons_error_reports.clear()


def _getSconsReportFilename(source_dir):
    return getNormalizedPathJoin(source_dir, "scons-report.txt")


def _getSconsErrorReportFilename(source_dir):
    return getNormalizedPathJoin(source_dir, "scons-error-report.txt")


def readSconsReport(source_dir):
    if source_dir not in _scons_reports:
        scons_report = OrderedDict()

        for line in getFileContentByLine(
            _getSconsReportFilename(source_dir), encoding="utf8"
        ):
            if "=" not in line:
                continue

            key, value = line.strip().split("=", 1)

            scons_report[key] = value

        _scons_reports[source_dir] = scons_report

    return _scons_reports[source_dir]


def getSconsReportValue(source_dir, key, default=Ellipsis):
    try:
        return readSconsReport(source_dir).get(key)
    except FileNotFoundError:
        if default is not Ellipsis:
            return default

        raise


def readSconsErrorReport(source_dir):
    if source_dir not in _scons_error_reports:
        scons_error_report = OrderedDict()

        scons_error_report_filename = _getSconsErrorReportFilename(source_dir)
        if os.path.exists(scons_error_report_filename):
            file_handle = openTextFile(scons_error_report_filename, "rb")
            try:
                while True:
                    try:
                        cmd, stdout, stderr = pickle.load(file_handle)
                    except EOFError:
                        break

                    if type(cmd) in (tuple, list):
                        cmd = " ".join(cmd)

                    if cmd not in scons_error_report:
                        scons_error_report[cmd] = ["", ""]

                    if type(stdout) in (tuple, list):
                        stdout = "\n".join(stdout)

                    if type(stderr) in (tuple, list):
                        stderr = "\n".join(stderr)

                    if stdout:
                        stdout = stdout.replace("\n\r", "\n")
                        scons_error_report[cmd][0] += stdout
                    if stderr:
                        stderr = stderr.replace("\n\r", "\n")
                        scons_error_report[cmd][1] += stderr

            finally:
                file_handle.close()

        _scons_error_reports[source_dir] = scons_error_report

    return _scons_error_reports[source_dir]


def addClangClPathFromMSVC(env):
    cl_exe = getExecutablePath("cl", env=env)

    if cl_exe is None:
        scons_logger.sysexit(
            "Error, Visual Studio required for using ClangCL on Windows."
        )

    clang_dir = getNormalizedPathJoin(cl_exe[: cl_exe.lower().rfind("msvc")], "Llvm")

    if (
        getCompilerArch(
            mingw_mode=False, msvc_mode=True, the_cc_name="cl.exe", compiler_path=cl_exe
        )
        == "pei-x86-64"
    ):
        clang_dir = getNormalizedPathJoin(clang_dir, "x64", "bin")
    else:
        clang_dir = getNormalizedPathJoin(clang_dir, "bin")

    if not os.path.exists(clang_dir):
        scons_details_logger.sysexit(
            "Visual Studio has no Clang component found at '%s'." % clang_dir
        )

    scons_details_logger.info(
        "Adding Visual Studio directory '%s' for Clang to PATH." % clang_dir
    )

    addToPATH(env, clang_dir, prefix=True)

    clangcl_path = getExecutablePath("clang-cl", env=env)

    if clangcl_path is None:
        scons_details_logger.sysexit(
            "Visual Studio has no Clang component found at '%s'." % clang_dir
        )

    env["CC"] = "clang-cl"
    env["LINK"] = "lld-link"

    # Version information is outdated now, spell-checker: ignore ccversion
    env["CCVERSION"] = None


def isGccName(cc_name):
    cc_name = os.path.normcase(os.path.basename(cc_name))

    return (
        "gcc" in cc_name
        or "g++" in cc_name
        or "gnu-cc" in cc_name
        or "gnu-gcc" in cc_name
    )


def isClangName(cc_name):
    cc_name = os.path.normcase(os.path.basename(cc_name))

    return ("clang" in cc_name and "-cl" not in cc_name) or isZigName(cc_name)


def isZigName(cc_name):
    cc_name = os.path.normcase(os.path.basename(cc_name))

    return "zig" in cc_name


def scanSourceDir(env, dirname, plugins):
    if not os.path.exists(dirname):
        return

    # If we use C11 capable compiler, all good. Otherwise use C++, which Scons
    # needs to derive from filenames, so make copies (or links) with a different
    # name.
    added_path = False

    filenames = sorted(os.listdir(dirname))

    for filename_base in filenames:
        # Only C files are of interest here.
        if not hasFilenameExtension(filename_base, (".c", ".cpp")):
            continue

        # If we have a C file, but a C++ file exists too, use that.
        if filename_base.endswith(".c") and (filename_base[:-2] + ".cpp") in filenames:
            continue

        if filename_base.endswith(".h") and plugins and not added_path:
            # Adding path for source paths on the fly, spell-checker: ignore cpppath
            env.Append(CPPPATH=[dirname])
            added_path = True

        filename = getNormalizedPathJoin(dirname, filename_base)

        target_filename = filename

        if isWin32Windows() and not isFilesystemEncodable(filename_base):
            target_filename = getWindowsShortPathName(target_filename)

            # Avoid ".C" suffixes, that MinGW64 wouldn't recognize.
            target_filename = changeFilenameExtension(
                target_filename, getFilenameExtension(target_filename).lower()
            )

        # We pretend to use C++ if no C11 compiler is present.
        if env.c11_mode:
            yield target_filename
        else:
            if hasFilenameExtension(filename, ".c"):
                target_filename += "pp"  # .cpp" suffix then

                os.rename(filename, target_filename)

            yield target_filename


def makeCLiteral(value):
    value = value.replace("\\", r"\\")
    value = value.replace('"', r"\"")

    return '"' + value + '"'


def createDefinitionsFile(source_dir, filename, definitions):
    for env_name in os.environ["_NUITKA_BUILD_DEFINITIONS_CATALOG"].split(","):
        definitions[env_name] = os.environ[env_name]

    build_definitions_filename = getNormalizedPathJoin(source_dir, filename)

    with openTextFile(build_definitions_filename, "w", encoding="utf8") as f:
        for key, value in sorted(definitions.items()):
            if key == "_NUITKA_BUILD_DEFINITIONS_CATALOG":
                continue

            if type(value) is int or key.endswith(("_BOOL", "_INT")):
                if type(value) is bool:
                    value = int(value)
                f.write("#define %s %s\n" % (key, value))
            elif type(value) in (str, unicode) and key.endswith("_WIDE_STRING"):
                f.write("#define %s L%s\n" % (key, makeCLiteral(value)))
            else:
                f.write("#define %s %s\n" % (key, makeCLiteral(value)))


def getMsvcVersionString(env):
    import SCons.Tool.MSCommon.vc  # pylint: disable=I0021,import-error

    return SCons.Tool.MSCommon.vc.get_default_version(env)


def getMsvcVersion(env):
    value = getMsvcVersionString(env)

    # TODO: Workaround for prompt being used.
    if value is None:
        value = os.getenv("VCToolsVersion", "14.3").rsplit(".", 1)[0]

    value = value.replace("exp", "")
    return tuple((int(d) for d in value.split(".")))


def _getBinaryArch(binary, mingw_mode):
    if isLinux() or mingw_mode:
        assert os.path.exists(binary), binary

        # Binutils binary name, spell-checker: ignore objdump,binutils
        command = ["objdump", "-f", binary]

        try:
            data, _err, rv = executeProcess(command)
        except OSError:
            command[0] = "llvm-objdump"

            try:
                data, _err, rv = executeProcess(command)
            except OSError:
                return None

        if rv != 0:
            return None

        if str is not bytes:
            data = decodeData(data)

        found = None

        for line in data.splitlines():
            if " file format " in line:
                found = line.split(" file format ")[-1]
            if "\tfile format " in line:
                found = line.split("\tfile format ")[-1]

        if os.name == "nt" and found == "coff-x86-64":
            found = "pei-x86-64"

        return found
    else:
        # TODO: Missing for macOS, FreeBSD, other Linux
        return None


_linker_arch_determined = False
_linker_arch = None


def getLinkerArch(target_arch, mingw_mode):
    # Singleton, pylint: disable=global-statement
    global _linker_arch_determined, _linker_arch

    if not _linker_arch_determined:
        if os.name == "nt":
            if target_arch == "x86_64":
                _linker_arch = "pei-x86-64"
            elif target_arch == "arm64":
                _linker_arch = "pei-arm64"
            else:
                _linker_arch = "pei-i386"
        else:
            _linker_arch = _getBinaryArch(
                binary=os.environ["NUITKA_PYTHON_EXE_PATH"], mingw_mode=mingw_mode
            )

        _linker_arch_determined = True

    return _linker_arch


_compiler_arch = {}


def getCompilerArch(mingw_mode, msvc_mode, the_cc_name, compiler_path):
    assert not mingw_mode or not msvc_mode

    if compiler_path not in _compiler_arch:
        if mingw_mode:
            _compiler_arch[compiler_path] = _getBinaryArch(
                binary=compiler_path, mingw_mode=mingw_mode
            )
        elif msvc_mode:
            cmdline = [compiler_path]

            if "-cl" in the_cc_name:
                cmdline.append("--version")

            # The cl.exe without further args will give error
            stdout, stderr, _rv = executeProcess(
                command=cmdline,
            )

            # The MSVC will output on error, while clang outputs in stdout and they
            # use different names for arches.
            if b"x64" in stderr or b"x86_64" in stdout:
                _compiler_arch[compiler_path] = "pei-x86-64"
            elif b"x86" in stderr or b"i686" in stdout:
                _compiler_arch[compiler_path] = "pei-i386"
            elif b"ARM64" in stderr:
                # TODO: The ARM64 output for Clang is not known yet.
                _compiler_arch[compiler_path] = "pei-arm64"
            else:
                assert False, (stdout, stderr)
        else:
            assert False, compiler_path

    return _compiler_arch[compiler_path]


def decideArchMismatch(target_arch, the_cc_name, compiler_path):
    mingw_mode = isGccName(the_cc_name) or isClangName(the_cc_name)
    msvc_mode = not mingw_mode

    linker_arch = getLinkerArch(target_arch=target_arch, mingw_mode=mingw_mode)
    compiler_arch = getCompilerArch(
        mingw_mode=mingw_mode,
        msvc_mode=msvc_mode,
        the_cc_name=the_cc_name,
        compiler_path=compiler_path,
    )

    return linker_arch != compiler_arch, linker_arch, compiler_arch


def raiseNoCompilerFoundErrorExit():
    if os.name == "nt":
        scons_logger.sysexit(
            """\
Error, cannot locate suitable C compiler. You have the following options:

a) If a suitable Visual Studio version is installed (check above trace
   outputs for rejection messages), it will be located automatically via
   registry. But not if you activate the wrong prompt, so don't do that
   unless you know what you are doing.

b) Using "--mingw64" forces Nuitka download MinGW64 for you, but only for
   Python version 3.12 and below, newer versions cannot use it. Note: MinGW64
   is the project name, it does *not* mean 64 bits, just a gcc with better
   Windows compatibility, it is available for 32 and 64 bits. Cygwin based
   gcc e.g. do not work.

c) Using "--zig" forces Nuitka download and use Zig for C compilation, but
   this only works with 64 bit Python versions.
"""
        )
    else:
        scons_logger.sysexit("Error, cannot locate suitable C compiler.")


def addBinaryBlobSection(env, blob_filename, section_name):
    # spell-checker: ignore linkflags, sectcreate

    if isMacOS():
        env.Append(
            LINKFLAGS=[
                "-Wl,-sectcreate,%(section_name)s,%(section_name)s,%(blob_filename)s"
                % {
                    "section_name": section_name,
                    "blob_filename": blob_filename,
                }
            ]
        )
    else:
        assert False


def makeResultPathFileSystemEncodable(env, result_exe):
    deleteFile(result_exe, must_exist=False)

    if os.name == "nt" and not isFilesystemEncodable(result_exe):
        result_exe = getNormalizedPathJoin(
            os.path.dirname(result_exe),
            "_nuitka_temp.pyd" if env.module_mode else "_nuitka_temp.exe",
        )

        if not isFilesystemEncodable(result_exe):
            result_exe = getNormalizedPath(os.path.relpath(result_exe))

            deleteFile(result_exe, must_exist=False)

    return result_exe


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
