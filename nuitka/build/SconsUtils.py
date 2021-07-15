#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
""" Helper functions for the scons file.

"""

from __future__ import print_function

import os
import shutil
import signal
import subprocess
import sys

from nuitka.__past__ import (  # pylint: disable=I0021,redefined-builtin
    basestring,
    unicode,
)
from nuitka.containers.oset import OrderedSet
from nuitka.Tracing import scons_details_logger, scons_logger
from nuitka.utils.Execution import getNullInput
from nuitka.utils.FileOperations import getFileContentByLine, getFileList


def initScons():
    # Avoid localized outputs.
    os.environ["LANG"] = "C"

    def nosync(self):
        # That's a noop, pylint: disable=unused-argument
        pass

    # Avoid scons writing the scons file at all.
    import SCons.dblite  # pylint: disable=I0021,import-error

    SCons.dblite.dblite.sync = nosync


def setupScons(env, source_dir):
    env["BUILD_DIR"] = source_dir

    # Store the file signatures database with the rest of the source files
    # and make it version dependent on the Python version of Scons, as its
    # pickle is being used.
    sconsign_dir = os.path.abspath(
        os.path.join(
            source_dir, ".sconsign-%d%s" % (sys.version_info[0], sys.version_info[1])
        )
    )

    env.SConsignFile(sconsign_dir)


scons_arguments = {}


def setArguments(arguments):
    """Decode command line arguments."""

    arg_encoding = arguments.get("argument_encoding")

    for key, value in arguments.items():
        if arg_encoding is not None:
            value = decodeData(value)
        scons_arguments[key] = value


def getArgumentRequired(name):
    """Helper for string options without default value."""
    return scons_arguments[name]


def getArgumentDefaulted(name, default):
    """Helper for string options with default value."""
    return scons_arguments.get(name, default)


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


def createEnvironment(mingw_mode, msvc_version, target_arch):
    from SCons.Script import Environment  # pylint: disable=I0021,import-error

    args = {}

    # If we are on Windows, and MinGW is not enforced, lets see if we can
    # find "cl.exe", and if we do, disable automatic scan.
    if (
        os.name == "nt"
        and not mingw_mode
        and msvc_version is None
        and (
            getExecutablePath("cl", env=None) is not None
            or getExecutablePath("gcc", env=None) is not None
        )
    ):
        args["MSVC_USE_SCRIPT"] = False

    if mingw_mode:
        # Force usage of MinGW64, not using MSVC tools.
        tools = ["mingw"]

        # This code would be running anyway, make it do not thing by monkey patching.
        import SCons.Tool.MSCommon.vc  # pylint: disable=I0021,import-error

        SCons.Tool.MSCommon.vc.msvc_setup_env = lambda *args: None
    else:
        # Everything else should use default, that is MSVC tools, but not MinGW64.
        tools = ["default"]

    return Environment(
        # We want the outside environment to be passed through.
        ENV=os.environ,
        # Extra tools configuration for scons.
        tools=tools,
        # The shared libraries should not be named "lib...", because CPython
        # requires the filename "module_name.so" to load it.
        SHLIBPREFIX="",
        # Under windows, specify the target architecture is needed for Scons
        # to pick up MSVC.
        TARGET_ARCH=target_arch,
        MSVC_VERSION=msvc_version,
        **args
    )


def decodeData(data):
    """Our own decode tries to workaround MSVC misbehavior."""
    try:
        return data.decode(sys.stdout.encoding)
    except UnicodeDecodeError:
        import locale

        try:
            return data.decode(locale.getpreferredencoding())
        except UnicodeDecodeError:
            return data.decode("utf8", "backslashreplace")


# Windows target mode: Compile for Windows. Used to be an option, but we
# no longer cross compile this way.
win_target = os.name == "nt"


def getExecutablePath(filename, env):
    """Find an execute in either normal PATH, or Scons detected PATH."""

    if os.path.exists(filename):
        return filename

    # Variable substitution from environment is needed, because this can contain
    # "$CC" which should be looked up too.
    while filename.startswith("$"):
        filename = env[filename[1:]]

    # Append ".exe" suffix  on Windows if not already present.
    if win_target and not filename.lower().endswith(".exe"):
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

        full = os.path.join(path_element, filename)

        if os.path.exists(full):
            return full

    return None


def changeKeyboardInteruptToErrorExit():
    def signalHandler(
        signal, frame
    ):  # pylint: disable=redefined-outer-name,unused-argument
        sys.exit(2)

    signal.signal(signal.SIGINT, signalHandler)


def setEnvironmentVariable(env, key, value):
    os.environ[key] = value

    if env is not None:
        env._dict["ENV"][key] = value  # pylint: disable=protected-access


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


def writeSconsReport(source_dir, env, gcc_mode, clang_mode, msvc_mode, clangcl_mode):
    with open(os.path.join(source_dir, "scons-report.txt"), "w") as report_file:
        # We are friends to get at this debug info, pylint: disable=protected-access
        for key, value in sorted(env._dict.items()):
            if type(value) is list and all(isinstance(v, basestring) for v in value):
                value = repr(value)

            if not isinstance(value, basestring):
                continue

            if key.startswith(("_", "CONFIGURE")):
                continue

            if key in ("MSVSSCONS", "BUILD_DIR", "IDLSUFFIXES", "DSUFFIXES"):
                continue

            print(key + "=" + value, file=report_file)

        print("gcc_mode=%s" % gcc_mode, file=report_file)
        print("clang_mode=%s" % clang_mode, file=report_file)
        print("msvc_mode=%s" % msvc_mode, file=report_file)
        print("clangcl_mode=%s" % clangcl_mode, file=report_file)


scons_reports = {}


def readSconsReport(source_dir):
    if source_dir not in scons_reports:
        scons_report = {}

        for line in open(os.path.join(source_dir, "scons-report.txt")):
            if "=" not in line:
                continue

            key, value = line.strip().split("=", 1)

            scons_report[key] = value

        scons_reports[source_dir] = scons_report

    return scons_reports[source_dir]


def getSconsReportValue(source_dir, key):
    return readSconsReport(source_dir).get(key)


def addClangClPathFromMSVC(env, target_arch):
    cl_exe = getExecutablePath("cl", env=env)

    if cl_exe is None:
        scons_logger.sysexit(
            "Error, Visual Studio required for using ClangCL on Windows."
        )

    clang_dir = cl_exe = os.path.join(cl_exe[: cl_exe.lower().rfind("msvc")], "Llvm")

    if target_arch == "x86_64":
        clang_dir = os.path.join(clang_dir, "x64", "bin")
    else:
        clang_dir = os.path.join(clang_dir, "bin")

    if os.path.exists(clang_dir):
        scons_details_logger.info(
            "Adding MSVC directory %r for Clang to PATH." % clang_dir
        )

        addToPATH(env, clang_dir, prefix=True)
    else:
        scons_details_logger.info("No Clang component for MSVC found." % clang_dir)


def switchFromGccToGpp(gcc_version, the_compiler, the_cc_name, env):
    if gcc_version is not None and gcc_version < (5,):
        scons_logger.info("The provided gcc is too old, switching to g++ instead.")

        # Switch to g++ from gcc then if possible, when C11 mode is false.
        the_gpp_compiler = os.path.join(
            os.path.dirname(the_compiler),
            os.path.basename(the_compiler).replace("gcc", "g++"),
        )

        if getExecutablePath(the_gpp_compiler, env=env):
            the_compiler = the_gpp_compiler
            the_cc_name = the_cc_name.replace("gcc", "g++")
        else:
            scons_logger.sysexit(
                "Error, your gcc is too old for C11 support, and no related g++ to workaround that is found."
            )

    return the_compiler, the_cc_name


def isGccName(cc_name):
    return "gcc" in cc_name or "g++" in cc_name or "gnu-cc" in cc_name


def cheapCopyFile(src, dst):
    dirname = os.path.dirname(dst)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    if win_target:
        # Windows has symlinks these days, but they do not integrate well
        # with Python2 at least. So make a copy in any case.
        if os.path.exists(dst):
            os.unlink(dst)
        shutil.copy(src, dst)
    else:
        # Relative paths work badly for links. Creating them relative is
        # not worth the effort.
        src = os.path.abspath(src)

        try:
            link_target = os.readlink(dst)

            # If it's already a proper link, do nothing then.
            if link_target == src:
                return

            os.unlink(dst)
        except OSError as _e:
            # Broken links work like that, remove them, so we can replace
            # them.
            try:
                os.unlink(dst)
            except OSError:
                pass

        try:
            os.symlink(src, dst)
        except OSError:
            shutil.copy(src, dst)


def provideStaticSourceFile(sub_path, nuitka_src, source_dir, c11_mode):
    source_filename = os.path.join(nuitka_src, "static_src", sub_path)
    target_filename = os.path.join(source_dir, "static_src", os.path.basename(sub_path))

    if target_filename.endswith(".c") and not c11_mode:
        target_filename += "pp"  # .cpp suffix then.

    cheapCopyFile(source_filename, target_filename)

    return target_filename


def makeCLiteral(value):
    value = value.replace("\\", r"\\")
    value = value.replace('"', r"\"")

    return '"' + value + '"'


def createDefinitionsFile(source_dir, filename, definitions):
    build_definitions_filename = os.path.join(source_dir, filename)

    with open(build_definitions_filename, "w") as f:
        for key, value in sorted(definitions.items()):
            if type(value) is int:
                f.write("#define %s %s\n" % (key, value))
            else:
                f.write("#define %s %s\n" % (key, makeCLiteral(value)))


def getMsvcVersionString(env):
    import SCons.Tool.MSCommon.vc  # pylint: disable=I0021,import-error

    return SCons.Tool.MSCommon.vc.get_default_version(env)


def getMsvcVersion(env):
    value = getMsvcVersionString(env)

    value = value.replace("exp", "")
    return float(value)


def _getBinaryArch(binary, mingw_mode):
    if "linux" in sys.platform or mingw_mode:
        assert os.path.exists(binary), binary

        command = ["objdump", "-f", binary]

        try:
            proc = subprocess.Popen(
                command,
                stdin=getNullInput(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
            )
        except OSError:
            return None

        data, _err = proc.communicate()
        rv = proc.wait()

        if rv != 0:
            return None

        if str is not bytes:
            data = decodeData(data)

        for line in data.splitlines():
            if " file format " in line:
                return line.split(" file format ")[-1]
    else:
        # TODO: Missing for macOS, FreeBSD, other Linux
        return None


_linker_arch_determined = False
_linker_arch = None


def getLinkerArch(target_arch, mingw_mode):
    # Singleton, pylint: disable=global-statement
    global _linker_arch_determined, _linker_arch

    if not _linker_arch_determined:
        if win_target:
            if target_arch == "x86_64":
                _linker_arch = "pei-x86-64"
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
    if mingw_mode:
        if compiler_path not in _compiler_arch:
            _compiler_arch[compiler_path] = _getBinaryArch(
                binary=compiler_path, mingw_mode=mingw_mode
            )
    elif msvc_mode:
        cmdline = [compiler_path]

        if "-cl" in the_cc_name:
            cmdline.append("--version")

        proc = subprocess.Popen(
            cmdline,
            stdin=getNullInput(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )

        # The cl.exe without further args will give error output indicating
        # arch, while clang outputs in stdout.
        stdout, stderr = proc.communicate()
        _rv = proc.wait()

        if b"x86" in stderr or b"i686" in stdout:
            _compiler_arch[compiler_path] = "pei-i386"
        elif b"x64" in stderr or b"x86_64" in stdout:
            _compiler_arch[compiler_path] = "pei-x86-64"
        else:
            assert False, (stdout, stderr)
    else:
        assert False, compiler_path

    return _compiler_arch[compiler_path]


def decideArchMismatch(target_arch, mingw_mode, msvc_mode, the_cc_name, compiler_path):
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

a) If a suitable Visual Studio version is installed, it will be located
   automatically via registry. But not if you activate the wrong prompt.

b) Using --mingw64 lets Nuitka download MinGW64 for you.

Note: Only MinGW64 will work! MinGW64 does *not* mean 64 bits, just better
Windows compatibility, it is available for 32 and 64 bits. Cygwin based gcc
will not work. MSYS2 based gcc will only work if you know what you are doing.

Note: The clang-cl will only work if Visual Studio already works for you.
"""
        )
    else:
        scons_logger.sysexit("Error, cannot locate suitable C compiler.")


_ldconf_paths = None


def locateStaticLinkLibrary(dll_name):
    # singleton, pylint: disable=global-statement
    #
    global _ldconf_paths
    if _ldconf_paths is None:
        _ldconf_paths = OrderedSet()

        for conf_filemame in getFileList("/etc/ld.so.conf.d", only_suffixes=".conf"):
            for conf_line in getFileContentByLine(conf_filemame):
                conf_line = conf_line.split("#", 1)[0]
                conf_line = conf_line.strip()

                if os.path.exists(conf_line):
                    _ldconf_paths.add(conf_line)

    for ld_config_path in _ldconf_paths:
        candidate = os.path.join(ld_config_path, "lib%s.a" % dll_name)

        if os.path.exists(candidate):
            return candidate

    return None
