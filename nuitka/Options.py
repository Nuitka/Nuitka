#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Options module

This exposes the choices made by the user. Defaults will be applied here, and
some handling of defaults.

"""

# These are for use in option values.
# spell-checker: ignore uiaccess,noannotations,reexecution,etherium
# spell-checker: ignore nodocstrings,noasserts,nowarnings,norandomization

import fnmatch
import os
import re
import shlex
import sys

from nuitka import Progress, Tracing
from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.containers.OrderedSets import (
    OrderedSet,
    recommended_orderedset_package_name,
)
from nuitka.importing.StandardLibrary import isStandardLibraryPath
from nuitka.OptionParsing import (
    parseOptions,
    run_time_variable_names,
    runSpecialCommandsFromOptions,
)
from nuitka.PythonFlavors import (
    getPythonFlavorName,
    isAnacondaPython,
    isApplePython,
    isArchPackagePython,
    isCPythonOfficialPackage,
    isDebianPackagePython,
    isHomebrewPython,
    isManyLinuxPython,
    isMSYS2MingwPython,
    isNuitkaPython,
    isPyenvPython,
    isTermuxPython,
    isUninstalledPython,
)
from nuitka.PythonVersions import (
    getLaunchingSystemPrefixPath,
    getNotYetSupportedPythonVersions,
    getSupportedPythonVersions,
    isDebugPython,
    isPythonWithGil,
    isStaticallyLinkedPython,
    python_version,
    python_version_str,
)
from nuitka.utils.Execution import getExecutablePath
from nuitka.utils.FileOperations import (
    getNormalizedPath,
    getReportPath,
    isLegalPath,
    isPathExecutable,
    openTextFile,
    resolveShellPatternToFilenames,
)
from nuitka.utils.Images import checkIconUsage
from nuitka.utils.Importing import getInlineCopyFolder
from nuitka.utils.StaticLibraries import getSystemStaticLibPythonPath
from nuitka.utils.Utils import (
    getArchitecture,
    getCPUCoreCount,
    getLaunchingNuitkaProcessEnvironmentValue,
    getLinuxDistribution,
    getMacOSRelease,
    getOS,
    getWindowsRelease,
    hasOnefileSupportedOS,
    hasStandaloneSupportedOS,
    isDebianBasedLinux,
    isFreeBSD,
    isLinux,
    isMacOS,
    isOpenBSD,
    isPosixWindows,
    isWin32OrPosixWindows,
    isWin32Windows,
)
from nuitka.Version import getCommercialVersion, getNuitkaVersion

options = None
positional_args = None
extra_args = []
is_nuitka_run = None
is_debug = None
is_non_debug = None
is_full_compat = None
report_missing_code_helpers = None
report_missing_trust = None
is_verbose = None


def _convertOldStylePathSpecQuotes(value):
    quote = None

    result = ""
    for c in value:
        if c == "%":
            if quote is None:
                quote = "{"
                result += quote
            elif quote == "{":
                result += "}"
                quote = None
        else:
            result += c

    return result


def checkPathSpec(value, arg_name, allow_disable):
    # There are never enough checks here, pylint: disable=too-many-branches
    old = value
    value = _convertOldStylePathSpecQuotes(value)
    if old != value:
        Tracing.options_logger.warning(
            "Adapted '%s' option value from legacy quoting style to '%s' -> '%s'"
            % (arg_name, old, value)
        )

    # This changes the '/' to '\' on Windows at least.
    value = getNormalizedPath(value)

    if "\n" in value or "\r" in value:
        Tracing.options_logger.sysexit(
            "Using a new line in value '%s=%r' value is not allowed."
            % (arg_name, value)
        )

    if "{NONE}" in value:
        if not allow_disable:
            Tracing.options_logger.sysexit(
                "Using value '{NONE}' in '%s=%s' value is not allowed."
                % (arg_name, value)
            )

        if value != "{NONE}":
            Tracing.options_logger.sysexit(
                "Using value '{NONE}' in '%s=%s' value does not allow anything else used too."
                % (arg_name, value)
            )

    if "{NULL}" in value:
        if not allow_disable:
            Tracing.options_logger.sysexit(
                "Using value '{NULL}' in '%s=%s' value is not allowed."
                % (arg_name, value)
            )

        if value != "{NULL}":
            Tracing.options_logger.sysexit(
                "Using value '{NULL}' in '%s=%s' value does not allow anything else used too."
                % (arg_name, value)
            )

    if "{COMPANY}" in value and not getCompanyName():
        Tracing.options_logger.sysexit(
            "Using value '{COMPANY}' in '%s=%s' value without being specified."
            % (arg_name, value)
        )

    if "{PRODUCT}" in value and not getProductName():
        Tracing.options_logger.sysexit(
            "Using value '{PRODUCT}' in '%s=%s' value without being specified."
            % (arg_name, value)
        )

    if "{VERSION}" in value and not (getFileVersionTuple() or getProductVersionTuple()):
        Tracing.options_logger.sysexit(
            "Using value '{VERSION}' in '%s=%s' value without being specified."
            % (arg_name, value)
        )

    if value.count("{") != value.count("}"):
        Tracing.options_logger.sysexit(
            """Unmatched '{}' is wrong for '%s=%s' and may \
definitely not do what you want it to do."""
            % (arg_name, value)
        )

    # Catch nested or illegal variable names.
    var_name = None
    for c in value:
        if c in "{":
            if var_name is not None:
                Tracing.options_logger.sysexit(
                    """Nested '{' is wrong for '%s=%s'.""" % (arg_name, value)
                )
            var_name = ""
        elif c == "}":
            if var_name is None:
                Tracing.options_logger.sysexit(
                    """Stray '}' is wrong for '%s=%s'.""" % (arg_name, value)
                )

            if var_name not in run_time_variable_names:
                Tracing.onefile_logger.sysexit(
                    "Found unknown variable name '%s' in for '%s=%s'."
                    "" % (var_name, arg_name, value)
                )

            var_name = None
        else:
            if var_name is not None:
                var_name += c

    for candidate in (
        "{PROGRAM}",
        "{PROGRAM_BASE}",
        "{CACHE_DIR}",
        "{HOME}",
        "{TEMP}",
    ):
        if candidate in value[1:]:
            Tracing.options_logger.sysexit(
                """\
Absolute run time paths of '%s' can only be at the start of \
'%s=%s', using it in the middle of it is not allowed."""
                % (candidate, arg_name, value)
            )

        if candidate == value:
            Tracing.options_logger.sysexit(
                """Cannot use general system folder %s, may only be the \
start of '%s=%s', using that alone is not allowed."""
                % (candidate, arg_name, value)
            )

        if value.startswith(candidate):
            if value[len(candidate)] != os.path.sep:
                Tracing.options_logger.sysexit(
                    """Cannot use general system folder %s, without a path \
separator '%s=%s', just appending to these is not allowed, needs to be \
below them."""
                    % (candidate, arg_name, value)
                )

    is_legal, reason = isLegalPath(value)
    if not is_legal:
        Tracing.options_logger.sysexit(
            """Cannot use illegal paths '%s=%s', due to %s."""
            % (arg_name, value, reason)
        )

    return value


def _checkOnefileTargetSpec():
    options.onefile_tempdir_spec = checkPathSpec(
        options.onefile_tempdir_spec,
        arg_name="--onefile-tempdir-spec",
        allow_disable=False,
    )

    if os.path.normpath(options.onefile_tempdir_spec) == ".":
        Tracing.options_logger.sysexit(
            """\
Error, using '.' as a value for '--onefile-tempdir-spec' is not supported,
you cannot unpack the onefile payload into the same directory as the binary,
as that would overwrite it and cause locking issues as well."""
        )

    if options.onefile_tempdir_spec.count("{") == 0:
        Tracing.options_logger.warning(
            """Not using any variables for '--onefile-tempdir-spec' should only be \
done if your program absolutely needs to be in the same path always: '%s'"""
            % options.onefile_tempdir_spec
        )

    if os.path.isabs(options.onefile_tempdir_spec):
        Tracing.options_logger.warning(
            """\
Using an absolute path should be avoided unless you are targeting a \
very well known environment: anchoring it with e.g. '{TEMP}', \
'{CACHE_DIR}' is recommended: You seemingly gave the value '%s'"""
            % options.onefile_tempdir_spec
        )
    elif not options.onefile_tempdir_spec.startswith(
        ("{TEMP}", "{HOME}", "{CACHE_DIR}")
    ):
        Tracing.options_logger.warning(
            """\
Using a relative to the onefile executable should be avoided \
unless you are targeting a very well known environment, anchoring \
it with e.g. '{TEMP}', '{CACHE_DIR}' is recommended: '%s'"""
            % options.onefile_tempdir_spec
        )


def _getVersionInformationValues():
    yield getNuitkaVersion()
    yield "Commercial: %s" % getCommercialVersion()
    yield "Python: %s" % sys.version.split("\n", 1)[0]
    yield "Flavor: %s" % getPythonFlavorName()
    if python_version >= 0x3D0:
        yield "GIL: %s" % ("yes" if isPythonWithGil() else "no")
    yield "Executable: %s" % getReportPath(sys.executable)
    yield "OS: %s" % getOS()
    yield "Arch: %s" % getArchitecture()

    if isLinux():
        dist_name, dist_base, dist_version = getLinuxDistribution()

        if dist_base is not None:
            yield "Distribution: %s (based on %s) %s" % (
                dist_name,
                dist_base,
                dist_version,
            )
        else:
            yield "Distribution: %s %s" % (dist_name, dist_version)

    if isWin32OrPosixWindows():
        yield "WindowsRelease: %s" % getWindowsRelease()

    if isMacOS():
        yield "macOSRelease: %s" % getMacOSRelease()


def printVersionInformation():
    print("\n".join(_getVersionInformationValues()))

    from nuitka.build.SconsInterface import (
        asBoolStr,
        runScons,
        setCommonSconsOptions,
    )

    scons_options = {"compiler_version_mode": asBoolStr("true")}
    env_values = setCommonSconsOptions(options=scons_options)

    runScons(
        options=scons_options,
        env_values=env_values,
        scons_filename="CCompilerVersion.scons",
    )


def _warnOnefileOnlyOption(option_name):
    if not options.is_onefile:
        Tracing.options_logger.warning(
            """\
Using onefile specific option '%s' has no effect \
when '--onefile' is not specified."""
            % option_name
        )


def _checkDataDirOptionValue(data_dir, option_name):
    if "=" not in data_dir:
        Tracing.options_logger.sysexit(
            "Error, malformed '%s' value '%s' description, must specify a relative target path with '=' separating it."
            % (option_name, data_dir)
        )

    src, dst = data_dir.split("=", 1)

    if os.path.isabs(dst):
        Tracing.options_logger.sysexit(
            "Error, malformed '%s' value, must specify relative target path for data dir, not '%s' as in '%s'."
            % (option_name, dst, data_dir)
        )

    if not os.path.isdir(src):
        Tracing.options_logger.sysexit(
            "Error, malformed '%s' value, must specify existing source data directory, not '%s' as in '%s'."
            % (option_name, dst, data_dir)
        )


def parseArgs():
    """Parse the command line arguments

    :meta private:
    """
    # singleton with many cases checking the options right away.
    # pylint: disable=global-statement,too-many-branches,too-many-locals,too-many-statements
    global is_nuitka_run, options, positional_args, extra_args, is_debug, is_non_debug
    global is_full_compat, report_missing_code_helpers, report_missing_trust, is_verbose

    if os.name == "nt":
        # Windows store Python's don't allow looking at the python, catch that.
        try:
            with openTextFile(sys.executable, "rb"):
                pass
        except OSError:
            Tracing.general.sysexit(
                """\
Error, the Python from Windows app store is not supported.""",
                mnemonic="unsupported-windows-app-store-python",
            )

    is_nuitka_run, options, positional_args, extra_args = parseOptions(
        logger=Tracing.options_logger
    )

    is_debug = _isDebug()
    is_non_debug = not is_debug
    is_full_compat = _isFullCompat()

    if hasattr(options, "experimental"):
        _experimental.update(options.experimental)

    # Dedicated option for caches, ccache and bytecode
    if options.disable_ccache:
        options.disabled_caches.append("ccache")
    if options.disable_bytecode_cache:
        options.disabled_caches.append("bytecode")
    if getattr(options, "disable_dll_dependency_cache", False):
        options.disabled_caches.append("dll-dependencies")

    report_missing_code_helpers = options.report_missing_code_helpers
    report_missing_trust = options.report_missing_trust

    if options.quiet or int(os.getenv("NUITKA_QUIET", "0")):
        Tracing.setQuiet()

    def _quoteArg(arg):
        if " " in arg:
            if "=" in arg and arg.startswith("--"):
                arg_name, value = arg.split("=", 1)

                return '%s="%s"' % (arg_name, value)
            else:
                return '"%s"' % arg
        else:
            return arg

    # This will not return if a non-compiling command is given.
    runSpecialCommandsFromOptions(options)

    if not options.version:
        Tracing.options_logger.info(
            "Used command line options: %s"
            % " ".join(_quoteArg(arg) for arg in sys.argv[1:])
        )

    if (
        getLaunchingNuitkaProcessEnvironmentValue("NUITKA_RE_EXECUTION")
        and not isAllowedToReexecute()
    ):
        Tracing.general.sysexit(
            "Error, not allowed to re-execute, but that has happened."
        )

    # Force to persist this one early.
    getLaunchingSystemPrefixPath()

    if options.progress_bar:
        Progress.enableProgressBar()

    if options.verbose_output:
        Tracing.optimization_logger.setFileHandle(
            # Can only have unbuffered binary IO in Python3, therefore not disabling buffering here.
            openTextFile(options.verbose_output, "w", encoding="utf8")
        )

        options.verbose = True

    is_verbose = options.verbose

    Tracing.optimization_logger.is_quiet = not options.verbose

    if options.version:
        printVersionInformation()
        sys.exit(0)

    if options.clean_caches:
        from nuitka.CacheCleanup import cleanCaches

        cleanCaches()

        if not positional_args:
            sys.exit(0)

    if options.show_inclusion_output:
        Tracing.inclusion_logger.setFileHandle(
            # Can only have unbuffered binary IO in Python3, therefore not disabling buffering here.
            openTextFile(options.show_inclusion_output, "w", encoding="utf8")
        )

        options.show_inclusion = True

    Tracing.progress_logger.is_quiet = not options.show_progress

    if options.compilation_mode is not None:
        if (
            options.is_onefile
            or options.is_standalone
            or options.module_mode
            or options.macos_create_bundle
        ):
            Tracing.options_logger.sysexit(
                "Cannot use both '--mode=' and deprecated options that specify mode."
            )

        if options.compilation_mode == "onefile":
            options.is_onefile = True
        elif options.compilation_mode == "standalone":
            options.is_standalone = True
        elif options.compilation_mode == "module":
            options.module_mode = True
        elif options.compilation_mode == "app":
            if isMacOS():
                options.macos_create_bundle = True
            else:
                options.is_onefile = True

    # Onefile implies standalone build.
    if options.is_onefile:
        options.is_standalone = True

    # macOS bundle implies standalone build.
    if shallCreateAppBundle():
        options.is_standalone = True

    if isMacOS():
        macos_target_arch = getMacOSTargetArch()

        if macos_target_arch == "universal":
            Tracing.options_logger.sysexit(
                "Cannot create universal macOS binaries (yet), please pick an arch and create two binaries."
            )

        if (options.macos_target_arch or "native") != "native":
            from nuitka.utils.SharedLibraries import (
                hasUniversalOrMatchingMacOSArchitecture,
            )

            if not hasUniversalOrMatchingMacOSArchitecture(
                os.path.realpath(sys.executable)
            ):
                Tracing.options_logger.sysexit(
                    """\
Cannot cross compile to other arch, using non-universal Python binaries \
for macOS. Please install the "universal" Python package as offered on \
the Python download page."""
                )

    # Standalone implies no_site build unless overridden, therefore put it
    # at start of flags, so "site" can override it.
    if options.is_standalone:
        options.python_flags.insert(0, "no_site")

    # Check onefile tempdir spec.
    if options.onefile_tempdir_spec:
        _checkOnefileTargetSpec()

        _warnOnefileOnlyOption("--onefile-tempdir-spec")

    # Check onefile splash image
    if options.splash_screen_image:
        if not os.path.exists(options.splash_screen_image):
            Tracing.options_logger.sysexit(
                "Error, splash screen image path '%s' does not exist."
                % options.splash_screen_image
            )

        _warnOnefileOnlyOption("--onefile-windows-splash-screen-image")

    if options.onefile_child_grace_time is not None:
        if not options.onefile_child_grace_time.isdigit():
            Tracing.options_logger.sysexit(
                """\
Error, the value given for '--onefile-child-grace-time' must be integer."""
            )

        _warnOnefileOnlyOption("--onefile-child-grace-time")

    if getShallIncludeExternallyDataFilePatterns():
        _warnOnefileOnlyOption("--include-onefile-external-data")

    if options.force_stdout_spec:
        options.force_stdout_spec = checkPathSpec(
            options.force_stdout_spec, "--force-stdout-spec", allow_disable=True
        )

    if options.force_stderr_spec:
        options.force_stderr_spec = checkPathSpec(
            options.force_stderr_spec, "--force-stderr-spec", allow_disable=True
        )

    # Provide a tempdir spec implies onefile tempdir, even on Linux.
    # Standalone mode implies an executable, not importing "site" module, which is
    # only for this machine, recursing to all modules, and even including the
    # standard library.
    if options.is_standalone:
        if options.module_mode:
            Tracing.options_logger.sysexit(
                """\
Error, conflicting options, cannot make standalone module, only executable.

Modules are supposed to be imported to an existing Python installation, therefore it
makes no sense to include a Python runtime."""
            )

    for any_case_module in getShallFollowModules():
        if any_case_module.startswith("."):
            bad = True
        else:
            for char in "/\\:":
                if char in any_case_module:
                    bad = True
                    break
            else:
                bad = False

        if bad:
            Tracing.options_logger.sysexit(
                """\
Error, '--follow-import-to' takes only module names or patterns, not directory path '%s'."""
                % any_case_module
            )

    for no_case_module in getShallFollowInNoCase():
        if no_case_module.startswith("."):
            bad = True
        else:
            for char in "/\\:":
                if char in no_case_module:
                    bad = True
                    break
            else:
                bad = False

        if bad:
            Tracing.options_logger.sysexit(
                """\
Error, '--nofollow-import-to' takes only module names or patterns, not directory path '%s'."""
                % no_case_module
            )

    scons_python = getPythonPathForScons()

    if scons_python is not None and not os.path.isfile(scons_python):
        Tracing.options_logger.sysexit(
            "Error, no such Python binary '%s', should be full path." % scons_python
        )

    output_filename = getOutputFilename()

    if output_filename is not None:
        if shallMakeModule():
            Tracing.options_logger.sysexit(
                """\
Error, may not module mode where filenames and modules matching are
mandatory."""
            )
        elif (
            isStandaloneMode() and os.path.basename(output_filename) != output_filename
        ):
            Tracing.options_logger.sysexit(
                """\
Error, output filename for standalone cannot contain a directory part."""
            )

        output_dir = os.path.dirname(output_filename) or "."

        if not os.path.isdir(output_dir):
            Tracing.options_logger.sysexit(
                """\
Error, specified output directory does not exist, you have to create
it before using it: '%s' (from --output-filename='%s')."""
                % (
                    output_dir,
                    output_filename,
                )
            )

    if isLinux():
        if len(getLinuxIconPaths()) > 1:
            Tracing.options_logger.sysexit(
                "Error, can only use one icon file on Linux."
            )

    if isMacOS():
        if len(getMacOSIconPaths()) > 1:
            Tracing.options_logger.sysexit(
                "Error, can only use one icon file on macOS."
            )

    for icon_path in getWindowsIconPaths():
        if "#" in icon_path and isWin32Windows():
            icon_path, icon_index = icon_path.rsplit("#", 1)

            if not icon_index.isdigit() or int(icon_index) < 0:
                Tracing.options_logger.sysexit(
                    "Error, icon number in '%s#%s' not valid."
                    % (icon_path + "#" + icon_index)
                )

        if getWindowsIconExecutablePath():
            Tracing.options_logger.sysexit(
                "Error, can only use icons from template executable or from icon files, but not both."
            )

    icon_exe_path = getWindowsIconExecutablePath()
    if icon_exe_path is not None and not os.path.exists(icon_exe_path):
        Tracing.options_logger.sysexit(
            "Error, icon path executable '%s' does not exist." % icon_exe_path
        )

    try:
        file_version = getFileVersionTuple()
    # Catch all the things, don't want any interface, pylint: disable=broad-except
    except Exception:
        Tracing.options_logger.sysexit(
            "Error, file version must be a tuple of up to 4 integer values."
        )

    try:
        product_version = getProductVersionTuple()
    # Catch all the things, don't want any interface, pylint: disable=broad-except
    except Exception:
        Tracing.options_logger.sysexit(
            "Error, product version must be a tuple of up to 4 integer values."
        )

    if getCompanyName() == "":
        Tracing.options_logger.sysexit(
            """Error, empty string is not an acceptable company name."""
        )

    if getProductName() == "":
        Tracing.options_logger.sysexit(
            """Error, empty string is not an acceptable product name."""
        )

    splash_screen_filename = getWindowsSplashScreen()

    if splash_screen_filename is not None:
        if not os.path.isfile(splash_screen_filename):
            Tracing.options_logger.sysexit(
                "Error, specified splash screen image '%s' does not exist."
                % splash_screen_filename
            )

    if (
        file_version
        or product_version
        or getWindowsVersionInfoStrings()
        and isWin32Windows()
    ):
        if not (file_version or product_version) and getCompanyName():
            Tracing.options_logger.sysexit(
                "Error, company name and file or product version need to be given when any version information is given."
            )

    if isOnefileMode() and not hasOnefileSupportedOS():
        Tracing.options_logger.sysexit(
            "Error, unsupported OS for onefile '%s'." % getOS()
        )

    for module_pattern, _filename_pattern in getShallIncludePackageData():
        if (
            module_pattern.startswith("-")
            or "/" in module_pattern
            or "\\" in module_pattern
        ):
            Tracing.options_logger.sysexit(
                "Error, '--include-package-data' needs module name or pattern as an argument, not '%s'."
                % module_pattern
            )

    for module_pattern in getShallFollowModules():
        if (
            module_pattern.startswith("-")
            or "/" in module_pattern
            or "\\" in module_pattern
        ):
            Tracing.options_logger.sysexit(
                "Error, '--follow-import-to' options needs module name or pattern as an argument, not '%s'."
                % module_pattern
            )
    for module_pattern in getShallFollowInNoCase():
        if (
            module_pattern.startswith("-")
            or "/" in module_pattern
            or "\\" in module_pattern
        ):
            Tracing.options_logger.sysexit(
                "Error, '--nofollow-import-to' options needs module name or pattern as an argument, not '%s'."
                % module_pattern
            )

    for data_file_desc in options.data_files:
        if "=" not in data_file_desc:
            Tracing.options_logger.sysexit(
                "Error, malformed data file description, must specify relative target path separated with '='."
            )

        if data_file_desc.count("=") == 1:
            src, dst = data_file_desc.split("=", 1)
            src = os.path.expanduser(src)
            src_pattern = src
        else:
            src, dst, pattern = data_file_desc.split("=", 2)
            src = os.path.expanduser(src)
            src_pattern = os.path.join(src, pattern)

        filenames = resolveShellPatternToFilenames(src_pattern)

        if len(filenames) > 1 and not dst.endswith(("/", os.path.sep)):
            Tracing.options_logger.sysexit(
                "Error, pattern '%s' matches more than one file, but target has no trailing slash, not a directory."
                % src
            )

        if not filenames:
            Tracing.options_logger.sysexit(
                "Error, '%s' does not match any files." % src
            )

        if os.path.isabs(dst):
            Tracing.options_logger.sysexit(
                "Error, must specify relative target path for data file, not absolute path '%s'."
                % data_file_desc
            )

    for data_dir in options.data_dirs:
        _checkDataDirOptionValue(data_dir=data_dir, option_name="--include-data-dir")

    for data_dir in options.raw_dirs:
        _checkDataDirOptionValue(data_dir=data_dir, option_name="--include-raw-dir")

    for pattern in getShallFollowExtraFilePatterns():
        if os.path.isdir(pattern):
            Tracing.options_logger.sysexit(
                "Error, pattern '%s' given to '--include-plugin-files' cannot be a directory name."
                % pattern
            )

    for directory_name in getShallFollowExtra():
        if not os.path.isdir(directory_name):
            Tracing.options_logger.sysexit(
                "Error, value '%s' given to '--include-plugin-directory' must be a directory name."
                % directory_name
            )

        if isStandardLibraryPath(directory_name):
            Tracing.options_logger.sysexit(
                """\
Error, directory '%s' given to '--include-plugin-directory' must not be a \
standard library path. Use '--include-module' or '--include-package' \
options instead."""
                % pattern
            )

    if options.static_libpython == "yes" and getSystemStaticLibPythonPath() is None:
        Tracing.options_logger.sysexit(
            "Error, static libpython is not found or not supported for this Python installation."
        )

    if shallUseStaticLibPython() and getSystemStaticLibPythonPath() is None:
        Tracing.options_logger.sysexit(
            """Error, usable static libpython is not found for this Python installation. You \
might be missing required packages. Disable with --static-libpython=no" if you don't \
want to install it."""
        )

    if isApplePython():
        if isStandaloneMode():
            Tracing.options_logger.sysexit(
                """\
Error, on macOS, for standalone mode, Apple Python is not supported \
due to being tied to specific OS releases, use e.g. CPython instead \
which is available from https://www.python.org/downloads/macos/ for \
download. With that, your program will work on macOS 10.9 or higher."""
            )

        if str is bytes:
            Tracing.options_logger.sysexit(
                "Error, Apple Python 2.7 from macOS is not usable as per Apple decision, use e.g. CPython 2.7 instead."
            )

    if isStandaloneMode() and isLinux():
        # Cyclic dependency
        from nuitka.utils.SharedLibraries import (
            checkPatchElfPresenceAndUsability,
        )

        checkPatchElfPresenceAndUsability(Tracing.options_logger)

    pgo_executable = getPgoExecutable()
    if pgo_executable and not isPathExecutable(pgo_executable):
        Tracing.options_logger.sysexit(
            "Error, path '%s' to binary to use for PGO is not executable."
            % pgo_executable
        )

    if (
        isOnefileMode()
        and isTermuxPython()
        and getExecutablePath("termux-elf-cleaner") is None
    ):
        Tracing.options_logger.sysexit(
            """\
Error, onefile mode on Termux requires 'termux-elf-cleaner' to be installed, \
use 'pkg install termux-elf-cleaner' to use it."""
        )

    for user_yaml_filename in getUserProvidedYamlFiles():
        if not os.path.exists(user_yaml_filename):
            Tracing.options_logger.sysexit(
                """\
Error, cannot find user provider yaml file '%s'."""
                % user_yaml_filename
            )

    # This triggers checks inside that code
    getCompilationReportUserData()


def commentArgs():
    """Comment on options, where we know something is not having the intended effect.

    :meta private:

    """
    # A ton of cases to consider, pylint: disable=too-many-branches,too-many-statements

    # Check files to exist or be suitable first before giving other warnings.
    for filename in getMainEntryPointFilenames():
        if not os.path.exists(filename):
            Tracing.general.sysexit("Error, file '%s' is not found." % filename)

        if (
            shallMakeModule()
            and os.path.normcase(os.path.basename(filename)) == "__init__.py"
        ):
            Tracing.general.sysexit(
                """\
Error, to compile a package, specify its directory but, not the '__init__.py'."""
            )

    # Inform the user about potential issues with the running version. e.g. unsupported
    # version.
    if python_version_str not in getSupportedPythonVersions():
        # Do not disturb run of automatic tests with, detected from the presence of
        # that environment variable.
        if "PYTHON" not in os.environ:
            Tracing.general.warning(
                """\
The Python version '%s' is only experimentally supported by Nuitka '%s', \
but an upcoming release will change that. In the mean time use Python \
version '%s' instead or newer Nuitka."""
                % (
                    python_version_str,
                    getNuitkaVersion(),
                    getSupportedPythonVersions()[-1],
                )
            )

    # spell-checker: ignore releaselevel
    if sys.version_info.releaselevel not in ("final", "candidate"):
        if python_version_str not in getNotYetSupportedPythonVersions():
            Tracing.general.sysexit(
                """\
Non-final versions '%s' '%s' are not supported by Nuitka, use the \
final version instead."""
                % (python_version_str, sys.version_info.releaselevel)
            )

    if python_version_str in getNotYetSupportedPythonVersions():
        if sys.version_info.releaselevel != "final" and not isExperimental(
            "python" + python_version_str
        ):
            Tracing.general.warning(
                """\
The Python version '%s' '%s' is only experimentally supported by \
and recommended only for use in Nuitka development and testing."""
                % (python_version_str, sys.version_info.releaselevel)
            )

        elif not isExperimental("python" + python_version_str):
            Tracing.general.sysexit(
                """\
The Python version '%s' is not supported by Nuitka '%s', but an upcoming \
release will add it. In the mean time use '%s' instead."""
                % (
                    python_version_str,
                    getNuitkaVersion(),
                    getSupportedPythonVersions()[-1],
                )
            )

    if not isPythonWithGil():
        Tracing.general.warning(
            """\
The Python without GIL is only experimentally supported by \
and recommended only for use in Nuitka development and testing."""
        )

    default_reference_mode = (
        "runtime" if shallMakeModule() or isStandaloneMode() else "original"
    )

    if getFileReferenceMode() is None:
        options.file_reference_mode = default_reference_mode
    else:
        if options.file_reference_mode != default_reference_mode:
            Tracing.options_logger.warning(
                "Using non-default file reference mode '%s' rather than '%s' may cause run time issues."
                % (getFileReferenceMode(), default_reference_mode)
            )
        else:
            Tracing.options_logger.info(
                "Using default file reference mode '%s' need not be specified."
                % default_reference_mode
            )

    default_mode_name_mode = "runtime" if shallMakeModule() else "original"

    if getModuleNameMode() is None:
        options.module_name_mode = default_mode_name_mode
    elif getModuleNameMode() == default_mode_name_mode:
        Tracing.options_logger.info(
            "Using module name mode '%s' need not be specified."
            % default_mode_name_mode
        )

    # TODO: Not all of these are usable with MSYS2 really, split those off.
    if not isWin32OrPosixWindows():
        # Too many Windows specific options clearly
        if (
            getWindowsIconExecutablePath()
            or shallAskForWindowsAdminRights()
            or shallAskForWindowsUIAccessRights()
            or getWindowsSplashScreen()
        ):
            Tracing.options_logger.warning(
                "Using Windows specific options has no effect on other platforms."
            )

        if options.mingw64 or options.msvc_version:
            Tracing.options_logger.warning(
                "Requesting Windows specific compilers has no effect on other platforms."
            )

    if options.msvc_version:
        if isMSYS2MingwPython() or isPosixWindows():
            Tracing.options_logger.sysexit("Requesting MSVC on MSYS2 is not allowed.")

        if isMingw64():
            Tracing.options_logger.sysexit(
                "Requesting both Windows specific compilers makes no sense."
            )

    if getMsvcVersion() and getMsvcVersion() not in ("list", "latest"):
        if getMsvcVersion().count(".") != 1 or not all(
            x.isdigit() for x in getMsvcVersion().split(".")
        ):
            Tracing.options_logger.sysexit(
                "For --msvc only values 'latest', 'info', and 'X.Y' values are allowed, but not '%s'."
                % getMsvcVersion()
            )

    try:
        getJobLimit()
    except ValueError:
        Tracing.options_logger.sysexit(
            "For '--jobs' value, use integer values only, not, but not '%s'."
            % options.jobs
        )

    if isOnefileMode():
        standalone_mode = "onefile"
    elif isStandaloneMode():
        standalone_mode = "standalone"
    else:
        standalone_mode = None

    if standalone_mode and not hasStandaloneSupportedOS():
        Tracing.options_logger.warning(
            "Standalone mode on %s is not known to be supported, might fail to work."
            % getOS()
        )

    if options.follow_all is True and shallMakeModule():
        Tracing.optimization_logger.sysexit(
            """\
In module mode you must follow modules more selectively, and e.g. should \
not include standard library or all foreign modules or else it will fail \
to work. You need to instead selectively add them with \
'--follow-import-to=name' though."""
        )

    if options.follow_all is True and standalone_mode:
        Tracing.options_logger.info(
            "Following all imports is the default for %s mode and need not be specified."
            % standalone_mode
        )

    if options.follow_all is False and standalone_mode:
        Tracing.options_logger.warning(
            "Following no imports is unlikely to work for %s mode and should not be specified."
            % standalone_mode
        )

    if options.follow_stdlib:
        if standalone_mode:
            Tracing.options_logger.warning(
                "Following imports to stdlib is the default in standalone mode.."
            )
        else:
            Tracing.options_logger.warning(
                "Following imports to stdlib not well tested and should not be specified."
            )

    if (
        not shallCreatePythonPgoInput()
        and not standalone_mode
        and options.follow_all is None
        and not options.follow_modules
        and not options.follow_stdlib
        and not options.include_modules
        and not options.include_packages
        and not options.include_extra
        and not options.follow_not_modules
    ):
        Tracing.options_logger.warning(
            """You did not specify to follow or include anything but main %s. Check options and \
make sure that is intended."""
            % ("module" if shallMakeModule() else "program")
        )

    if options.dependency_tool:
        Tracing.options_logger.warning(
            "Using removed option '--windows-dependency-tool' is deprecated and has no impact anymore."
        )

    if shallMakeModule() and options.static_libpython == "yes":
        Tracing.options_logger.warning(
            "In module mode, providing '--static-libpython' has no effect, it's not used."
        )

        options.static_libpython = "no"

    if (
        not isCPgoMode()
        and not isPythonPgoMode()
        and (getPgoArgs() or getPgoExecutable())
    ):
        Tracing.optimization_logger.warning(
            "Providing PGO arguments without enabling PGO mode has no effect."
        )

    if isCPgoMode():
        if isStandaloneMode():
            Tracing.optimization_logger.warning(
                """\
Using C level PGO with standalone/onefile mode is not \
currently working. Expect errors."""
            )

        if shallMakeModule():
            Tracing.optimization_logger.warning(
                """\
Using C level PGO with module mode is not currently \
working. Expect errors."""
            )

    if (
        options.static_libpython == "auto"
        and not shallMakeModule()
        and not shallUseStaticLibPython()
        and getSystemStaticLibPythonPath() is not None
        and not shallUsePythonDebug()
    ):
        Tracing.options_logger.info(
            """Detected static libpython to exist, consider '--static-libpython=yes' for better performance, \
but errors may happen."""
        )

    if not shallExecuteImmediately():
        if shallRunInDebugger():
            Tracing.options_logger.warning(
                "The '--debugger' option has no effect outside of '--debug' without '--run' option."
            )

    # Check if the fallback is used, except for Python2 on Windows, where we cannot
    # have it.
    if hasattr(OrderedSet, "is_fallback") and not (
        isWin32Windows() and python_version < 0x360
    ):
        # spell-checker: ignore orderedset
        Tracing.general.warning(
            """\
Using very slow fallback for ordered sets, please install '%s' \
PyPI package for best Python compile time performance."""
            % recommended_orderedset_package_name
        )

    if shallUsePythonDebug() and not isDebugPython():
        Tracing.general.sysexit(
            """\
Error, for using the debug Python version, you need to run it will that version
and not with the non-debug version.
"""
        )

    if isMacOS() and shallCreateAppBundle() and not getMacOSIconPaths():
        Tracing.general.warning(
            """\
For application bundles, you ought to specify an icon with '--macos-app-icon'.", \
otherwise a dock icon may not be present."""
        )

    if (
        isMacOS()
        and shallUseSigningForNotarization()
        and getMacOSSigningIdentity() == "-"
    ):
        Tracing.general.sysexit(
            """\
Error, need to provide signing identity with '--macos-sign-identity' for \
notarization capable signature, the default identify 'ad-hoc' is not going \
to work."""
        )

    if (
        isWin32Windows()
        and 0x340 <= python_version < 0x380
        and getWindowsConsoleMode() != "disable"
    ):
        Tracing.general.warning(
            """\
On Windows, support for input/output on the console Windows, does \
not work on non-UTF8 systems, unless Python 3.8 or higher is used \
but this is %s, so please consider upgrading, or disabling the \
console window for deployment.
"""
            % python_version_str,
            mnemonic="old-python-windows-console",
        )

    if shallMakeModule() and (getForcedStderrPath() or getForcedStdoutPath()):
        Tracing.general.warning(
            """\
Extension modules do not control process outputs, therefore the \
options '--force-stdout-spec' and '--force-stderr-spec' have no \
impact and should not be specified."""
        )

    if shallMakeModule() and options.console_mode is not None:
        Tracing.general.warning(
            """\
Extension modules are not binaries, and therefore the option \
'--windows-console-mode' does not have an impact and should \
not be specified."""
        )

    if options.disable_console in (True, False):
        if isWin32Windows():
            Tracing.general.warning(
                """\
The old console option '%s' should not be given anymore, use '%s' \
instead. It also has the extra mode 'attach' to consider."""
                % (
                    (
                        "--disable-console"
                        if options.disable_console
                        else "--enable-console"
                    ),
                    "--windows-console-mode=%s"
                    % ("disable" if options.disable_console else "force"),
                )
            )
        else:
            Tracing.general.warning(
                """The old console option '%s' should not be given anymore, and doesn't
have any effect anymore on non-Windows."""
                % (
                    "--disable-console"
                    if options.disable_console
                    else "--enable-console"
                )
            )


def isVerbose():
    """:returns: bool derived from ``--verbose``"""
    return options is not None and options.verbose


def shallTraceExecution():
    """:returns: bool derived from ``--trace-execution``"""
    return options.trace_execution


def shallExecuteImmediately():
    """:returns: bool derived from ``--run``"""
    return options is not None and options.immediate_execution


def shallRunInDebugger():
    """:returns: bool derived from ``--debug``"""
    return options.debugger


def getXMLDumpOutputFilename():
    """:returns: str derived from ``--xml``"""
    return options.xml_output


def shallOnlyExecCCompilerCall():
    """:returns: bool derived from ``--recompile-c-only``"""
    return options.recompile_c_only


def shallNotDoExecCCompilerCall():
    """:returns: bool derived from ``--generate-c-only``"""
    return options.generate_c_only


def getFileReferenceMode():
    """*str*, one of "runtime", "original", "frozen", coming from ``--file-reference-choice``

    Notes:
        Defaults to runtime for modules and packages, as well as standalone binaries,
        otherwise original is kept.
    """

    return options.file_reference_mode


def getModuleNameMode():
    """*str*, one of "runtime", "original", coming from ``--module-name-choice``

    Notes:
        Defaults to runtime for modules and packages, otherwise original is kept.
    """

    return options.module_name_mode


def shallMakeModule():
    """:returns: bool derived from ``--module``"""
    return options is not None and options.module_mode


def shallCreatePyiFile():
    """*bool* = **not** ``--no-pyi-file``"""
    return options.pyi_file


def shallCreatePyiFileContainStubs():
    """*bool* = **not** ``--no-pyi-stubs``"""
    return options.pyi_stubs


def isAllowedToReexecute():
    """*bool* = **not** ``--must-not-re-execute``"""
    return options.allow_reexecute


def shallFollowStandardLibrary():
    """:returns: bool derived from ``--follow-stdlib``"""
    return options.follow_stdlib


def shallFollowNoImports():
    """:returns: bool derived from ``--nofollow-imports``"""
    return options.follow_all is False


def shallFollowAllImports():
    """:returns: bool derived from ``--follow-imports``"""
    if shallCreatePythonPgoInput() and options.is_standalone:
        return True

    return options.is_standalone or options.follow_all is True


def _splitShellPattern(value):
    return value.split(",") if "{" not in value else [value]


def getShallFollowInNoCase():
    """*list*, items of ``--nofollow-import-to=``"""
    return sum([_splitShellPattern(x) for x in options.follow_not_modules], [])


def getShallFollowModules():
    """*list*, items of ``--follow-import-to=`` amended with what ``--include-module`` and ``--include-package`` got"""
    return sum(
        [
            _splitShellPattern(x)
            for x in options.follow_modules
            + options.include_modules
            + options.include_packages
        ],
        [],
    )


def getShallFollowExtra():
    """*list*, items of ``--include-plugin-directory=``"""
    return sum([_splitShellPattern(x) for x in options.include_extra], [])


def getShallFollowExtraFilePatterns():
    """*list*, items of ``--include-plugin-files=``"""
    return sum([_splitShellPattern(x) for x in options.include_extra_files], [])


def getMustIncludeModules():
    """*list*, items of ``--include-module=``"""
    return sum([_splitShellPattern(x) for x in options.include_modules], [])


def getMustIncludePackages():
    """*list*, items of ``--include-package=``"""
    return sum([_splitShellPattern(x) for x in options.include_packages], [])


def getShallIncludeDistributionMetadata():
    """*list*, items of ``--include-distribution-metadata=``"""
    return sum(
        [_splitShellPattern(x) for x in options.include_distribution_metadata], []
    )


def getShallIncludePackageData():
    """*iterable of (module name, filename pattern)*, derived from ``--include-package-data=``

    The filename pattern can be None if not given. Empty values give None too.
    """
    for package_data_pattern in sum(
        [_splitShellPattern(x) for x in options.package_data], []
    ):
        if ":" in package_data_pattern:
            module_pattern, filename_pattern = package_data_pattern.split(":", 1)
            # Empty equals None.
            filename_pattern = filename_pattern or None
        else:
            module_pattern = package_data_pattern
            filename_pattern = None

        yield module_pattern, filename_pattern


def getShallIncludeDataFiles():
    """*list*, items of ``--include-data-files=``"""
    for data_file_desc in options.data_files:
        if data_file_desc.count("=") == 1:
            src, dest = data_file_desc.split("=", 1)

            for pattern in _splitShellPattern(src):
                pattern = os.path.expanduser(pattern)

                yield pattern, None, dest, data_file_desc
        else:
            src, dest, pattern = data_file_desc.split("=", 2)

            for pattern in _splitShellPattern(pattern):
                pattern = os.path.expanduser(pattern)

                yield os.path.join(src, pattern), src, dest, data_file_desc


def getShallIncludeDataDirs():
    """*list*, items of ``--include-data-dir=``"""
    for data_file in options.data_dirs:
        src, dest = data_file.split("=", 1)

        yield src, dest


def getShallIncludeRawDirs():
    """*list*, items of ``--include-raw-dir=``"""
    for data_file in options.raw_dirs:
        src, dest = data_file.split("=", 1)

        yield src, dest


def getShallNotIncludeDataFilePatterns():
    """*list*, items of ``--noinclude-data-files=``"""

    return options.data_files_inhibited


def getShallIncludeExternallyDataFilePatterns():
    """*list*, items of ``--include-onefile-external-data=``"""

    return options.data_files_external


def getShallNotIncludeDllFilePatterns():
    """*list*, items of ``--noinclude-dlls=``"""

    return options.dll_files_inhibited


def shallWarnImplicitRaises():
    """:returns: bool derived from ``--warn-implicit-exceptions``"""
    return options.warn_implicit_exceptions


def shallWarnUnusualCode():
    """:returns: bool derived from ``--warn-unusual-code``"""
    return options.warn_unusual_code


def assumeYesForDownloads():
    """:returns: bool derived from ``--assume-yes-for-downloads``"""
    return options is not None and options.assume_yes_for_downloads


def _isDebug():
    """:returns: bool derived from ``--debug`` or ``--debugger``"""
    return options is not None and (options.debug or options.debugger)


def shallUsePythonDebug():
    """:returns: bool derived from ``--python-debug`` or ``sys.flags.debug``

    Passed to Scons as ``python_debug`` so it can consider it when picking
    link libraries to choose the correct variant. Also enables the define
    ``Py_DEBUG`` for C headers. Reference counting checks and other debug
    asserts of Python will happen in this mode.

    """
    return options.python_debug or sys.flags.debug


def isUnstripped():
    """:returns: bool derived from ``--unstripped`` or ``--profile``

    A binary is called stripped when debug information is not present, an
    unstripped when it is present. For profiling and debugging it will be
    necessary, but it doesn't enable debug checks like ``--debug`` does.

    Passed to Scons as ``unstripped_mode`` to it can ask the linker to
    include symbol information.
    """
    return options.unstripped or options.profile or is_debug


def isProfile():
    """:returns: bool derived from ``--profile``"""
    return options.profile


def shallCreateGraph():
    """:returns: bool derived from ``--internal-graph``"""
    return options.internal_graph


def getOutputFilename():
    """*str*, value of "-o" """
    return options.output_filename


def getOutputPath(path):
    """Return output pathname of a given path (filename)."""
    if options.output_dir:
        return getNormalizedPath(os.path.join(options.output_dir, path))
    else:
        return path


def getOutputDir():
    """*str*, value of ``--output-dir`` or "." """
    return options.output_dir if options.output_dir else "."


def getPositionalArgs():
    """*tuple*, command line positional arguments"""
    return tuple(positional_args)


def getMainArgs():
    """*tuple*, arguments following the optional arguments"""
    return tuple(extra_args)


def getMainEntryPointFilenames():
    """*tuple*, main programs, none, one or more"""
    if options.mains:
        if len(options.mains) == 1:
            assert not positional_args

        result = tuple(options.mains)
    else:
        result = (positional_args[0],)

    return tuple(getNormalizedPath(r) for r in result)


def isMultidistMode():
    return options is not None and options.mains and len(options.mains) > 1


def shallOptimizeStringExec():
    """Inactive yet"""
    return False


_shall_use_static_lib_python = None


def _shallUseStaticLibPython():
    # many cases and return driven, pylint: disable=too-many-branches,too-many-return-statements

    if shallMakeModule():
        return False, "not used in module mode"

    if options.static_libpython == "auto":
        # Nuitka-Python is good to to static linking.
        if isNuitkaPython():
            return True, "Nuitka-Python is unexpectedly broken."

        if isHomebrewPython():
            return True, "Homebrew Python is unexpectedly broken."

        # Debian packages with are usable if the OS is new enough
        from nuitka.utils.StaticLibraries import (
            isDebianSuitableForStaticLinking,
        )

        if (
            isDebianBasedLinux()
            and isDebianPackagePython()
            and isDebianSuitableForStaticLinking()
            and not shallUsePythonDebug()
        ):
            if python_version >= 0x3C0 and not os.path.exists(
                getInlineCopyFolder("python_hacl")
            ):
                return (
                    False,
                    "Nuitka on Debian-Python needs inline copy of hacl not included.",
                )

            return True, "Nuitka on Debian-Python needs package '%s' installed." % (
                "python2-dev" if str is bytes else "python3-dev"
            )

        if isMSYS2MingwPython():
            return True, "Nuitka on MSYS2 needs package 'python-devel' installed."

        # For Anaconda default to trying static lib python library, which
        # normally is just not available or if it is even unusable.
        if isAnacondaPython():
            if isMacOS():
                # TODO: Maybe some linker options can make it happen.
                return (
                    False,
                    "Anaconda on macOS exports not all symbols when using it.",
                )
            elif not isWin32Windows():
                return (
                    True,
                    """\
Nuitka on Anaconda needs package for static libpython installed. \
Execute 'conda install libpython-static'.""",
                )

        if isPyenvPython():
            return True, "Nuitka on pyenv should not use '--enable-shared'."

        if isManyLinuxPython():
            return (
                True,
                """\
Nuitka on 'manylinux' has no shared libraries. Use container with \
the command 'RUN cd /opt/_internal && tar xf static-libs-for-embedding-only.tar.xz' \
added to provide the static link library.""",
            )

        if isMacOS() and isCPythonOfficialPackage():
            return True, None

        if isArchPackagePython():
            return True, None

        # If not dynamic link library is available, the static link library will
        # have to do it.
        if isStaticallyLinkedPython():
            return True, None

    return options.static_libpython == "yes", None


def shallUseStaticLibPython():
    """:returns: bool derived from ``--static-libpython=yes|auto`` and not module mode

    Notes:
        Currently only Anaconda on non-Windows can do this and MSYS2.
    """

    global _shall_use_static_lib_python  # singleton, pylint: disable=global-statement

    if _shall_use_static_lib_python is None:
        _shall_use_static_lib_python, reason = _shallUseStaticLibPython()

        if _shall_use_static_lib_python and reason:
            static_libpython = getSystemStaticLibPythonPath()

            if not static_libpython:
                Tracing.options_logger.sysexit(
                    """\
Automatic detection of static libpython failed. %s Disable with '--static-libpython=no' if you don't \
want to install it."""
                    % reason
                )

    return _shall_use_static_lib_python


def shallTreatUninstalledPython():
    """*bool* = derived from Python installation and modes

    Notes:
        Not done for standalone mode obviously. The Python DLL will
        be a dependency of the executable and treated that way.

        Also not done for extension modules, they are loaded with
        a Python runtime available.

        Most often uninstalled Python versions are self compiled or
        from Anaconda.
    """

    if shallMakeModule() or isStandaloneMode():
        return False

    return isUninstalledPython()


def shallCreateCmdFileForExecution():
    """*bool* = derived from Python installation and modes

    Notes: Mostly for accelerated mode on Windows with uninstalled python, to
    make sure they find their Python DLL.
    """
    return isWin32Windows() and shallTreatUninstalledPython()


def isShowScons():
    """:returns: bool derived from ``--show-scons``"""
    return options.show_scons


def getJobLimit():
    """*int*, value of ``--jobs`` / "-j" or number of CPU kernels"""
    jobs = options.jobs

    # Low memory has a default of 1.
    if jobs is None and isLowMemory():
        return 1

    if jobs is None:
        result = getCPUCoreCount()
    else:
        result = int(jobs)

        if result <= 0:
            result = max(1, getCPUCoreCount() + result)

    return result


def getLtoMode():
    """:returns: bool derived from ``--lto``"""
    return options.lto


def isClang():
    """:returns: bool derived from ``--clang`` or enforced by platform, e.g. macOS or FreeBSD some targets."""

    return (
        options.clang
        or isMacOS()
        or isOpenBSD()
        or (isFreeBSD() and getArchitecture() != "powerpc")
        or isTermuxPython()
    )


def isMingw64():
    """:returns: bool derived from ``--mingw64``, available only on Windows, otherwise false"""
    if isWin32Windows():
        return options.mingw64 or isMSYS2MingwPython()
    else:
        return None


def getMsvcVersion():
    """:returns: str derived from ``--msvc`` on Windows, otherwise None"""
    if isWin32Windows():
        return options.msvc_version
    else:
        return None


def shallCleanCache(cache_name):
    """:returns: bool derived from ``--clean-cache``"""

    if cache_name == "clcache":
        cache_name = "ccache"

    return "all" in options.clean_caches or cache_name in options.clean_caches


def shallDisableCacheUsage(cache_name):
    """:returns: bool derived from ``--disable-cache``"""
    if options is None:
        return False

    return "all" in options.disabled_caches or cache_name in options.disabled_caches


def shallDisableCCacheUsage():
    """:returns: bool derived from ``--disable-ccache`` or ``--disable--cache=ccache``"""
    return shallDisableCacheUsage("ccache")


def shallDisableBytecodeCacheUsage():
    """:returns: bool derived from ``--disable-bytecode-cache``"""
    return shallDisableCacheUsage("bytecode")


def shallDisableCompressionCacheUsage():
    """:returns: bool derived from ``--disable-cache=compression``"""
    return shallDisableCacheUsage("compression")


def getWindowsConsoleMode():
    """:returns: str from ``--windows-console-mode``"""
    if options.disable_console is True:
        return "disable"
    if options.disable_console is False:
        return "force"
    return options.console_mode or "force"


def _isFullCompat():
    """:returns: bool derived from ``--full-compat``

    Notes:
        Code should should use "Options.is_full_compat" instead, this
        is only used to initialize that value.
    """
    return options is not None and not options.improved


def isShowProgress():
    """:returns: bool derived from ``--show-progress``"""
    return options is not None and options.show_progress


def isShowMemory():
    """:returns: bool derived from ``--show-memory``"""
    return options is not None and options.show_memory


def isShowInclusion():
    """:returns: bool derived from ``--show-modules``"""
    return options.show_inclusion


def isRemoveBuildDir():
    """:returns: bool derived from ``--remove-output``"""
    return options.remove_build and not options.generate_c_only


def isDeploymentMode():
    """:returns: bool derived from ``--deployment``"""
    return options.is_deployment


def getNoDeploymentIndications():
    """:returns: list derived from ``--no-deployment-flag``"""
    return options.no_deployment_flags


_experimental = set()


def isExperimental(indication):
    """Check whether a given experimental feature is enabled.

    Args:
        indication: (str) feature name
    Returns:
        bool
    """
    return indication in _experimental


def enableExperimental(indication):
    _experimental.add(indication)


def getExperimentalIndications():
    """*tuple*, items of ``--experimental=``"""
    if hasattr(options, "experimental"):
        return options.experimental
    else:
        return ()


def getDebugModeIndications():
    result = []

    for debug_option_value_name in ("debug_immortal",):
        if debug_option_value_name == "debug_immortal" and python_version < 0x3C0:
            continue

        if _isDebug():
            if getattr(options, debug_option_value_name) is not False:
                result.append(debug_option_value_name)
        else:
            if getattr(options, debug_option_value_name) is True:
                result.append(debug_option_value_name)

    return result


def shallExplainImports():
    """:returns: bool derived from ``--explain-imports``"""
    return options is not None and options.explain_imports


def isStandaloneMode():
    """:returns: bool derived from ``--standalone``"""
    if shallCreatePythonPgoInput():
        return False

    return bool(options.is_standalone or options.list_package_dlls)


def isOnefileMode():
    """:returns: bool derived from ``--onefile``"""
    if shallCreatePythonPgoInput():
        return False

    return bool(options.is_onefile)


def isAcceleratedMode():
    """:returns: bool derived from ``--standalone`` and `--module`"""
    return not isStandaloneMode() and not shallMakeModule()


def isOnefileTempDirMode():
    """:returns: bool derived from ``--onefile-tempdir-spec``

    Notes:
        Using cached onefile execution when the spec doesn't contain
        volatile things.
    """
    if shallCreatePythonPgoInput():
        return False

    spec = getOnefileTempDirSpec()

    for candidate in (
        "{PID}",
        "{TIME}",
        "{PROGRAM}",
        "{PROGRAM_BASE}",
    ):
        if candidate in spec:
            return True

    return False


def isCPgoMode():
    """:returns: bool derived from ``--pgo-c``"""
    if shallCreatePythonPgoInput():
        return False

    return options.is_c_pgo


def isPythonPgoMode():
    """:returns: bool derived from ``--pgo-python``"""
    return options.is_python_pgo


def getPythonPgoInput():
    """:returns: str derived from ``--pgo-python-input``"""
    return options.python_pgo_input


def shallCreatePythonPgoInput():
    return isPythonPgoMode() and getPythonPgoInput() is None


def getPgoArgs():
    """*list* = ``--pgo-args``"""
    return shlex.split(options.pgo_args)


def getPgoExecutable():
    """*str* = ``--pgo-args``"""

    if options.pgo_executable and os.path.exists(options.pgo_executable):
        if not os.path.isabs(options.pgo_executable):
            options.pgo_executable = os.path.join(".", options.pgo_executable)

    return options.pgo_executable


def getPythonPgoUnseenModulePolicy():
    """*str* = ``--python-pgo-unused-module-policy``"""
    return options.python_pgo_policy_unused_module


def getOnefileTempDirSpec():
    """*str* = ``--onefile-tempdir-spec``"""
    result = (
        options.onefile_tempdir_spec or "{TEMP}" + os.path.sep + "onefile_{PID}_{TIME}"
    )

    return result


def getOnefileChildGraceTime():
    """*int* = ``--onefile-child-grace-time``"""
    return (
        int(options.onefile_child_grace_time)
        if options.onefile_child_grace_time is not None
        else 5000
    )


def shallNotCompressOnefile():
    """*bool* = ``--onefile-no-compression``"""
    return options.onefile_no_compression


def shallOnefileAsArchive():
    """*bool* = ``--onefile-as-archive``"""
    return options.onefile_as_archive


def _checkIconPaths(icon_paths):
    for icon_path in icon_paths:
        if not os.path.exists(icon_path):
            Tracing.options_logger.sysexit(
                "Error, icon path '%s' does not exist." % icon_path
            )

        checkIconUsage(logger=Tracing.options_logger, icon_path=icon_path)

    return icon_paths


def getWindowsIconPaths():
    """*list of str*, values of ``--windows-icon-from-ico``"""
    return _checkIconPaths(options.windows_icon_path)


def getLinuxIconPaths():
    """*list of str*, values of ``--linux-icon``"""
    result = options.linux_icon_path

    # Check if Linux icon requirement is met.
    if isLinux() and not result and isOnefileMode():
        # spell-checker: ignore pixmaps
        default_icons = (
            "/usr/share/pixmaps/python%s.xpm" % python_version_str,
            "/usr/share/pixmaps/python%s.xpm" % sys.version_info[0],
            "/usr/share/pixmaps/python.xpm",
        )

        for icon in default_icons:
            if os.path.exists(icon):
                result.append(icon)
                break

    return _checkIconPaths(result)


def getMacOSIconPaths():
    """*list of str*, values of ``--macos-app-icon``"""
    return _checkIconPaths(options.macos_icon_path)


def getWindowsIconExecutablePath():
    """*str* or *None* if not given, value of ``--windows-icon-from-exe``"""
    return options.icon_exe_path


def shallAskForWindowsAdminRights():
    """*bool*, value of ``--windows-uac-admin`` or ``--windows-uac-uiaccess``"""
    return options.windows_uac_admin


def shallAskForWindowsUIAccessRights():
    """*bool*, value of ``--windows-uac-uiaccess``"""
    return options.windows_uac_uiaccess


def getLegalCopyright():
    """*str* name of the product to use derived from ``--copyright``"""
    return options.legal_copyright


def getLegalTrademarks():
    """*str* name of the product to use derived from ``--trademarks``"""
    return options.legal_trademarks


def getLegalInformation():
    result = options.legal_copyright

    if options.legal_trademarks:
        if result is not None:
            result += "\nTrademark information:" + options.legal_trademarks
        else:
            result = options.legal_trademarks

    return result


def getWindowsVersionInfoStrings():
    """*dict of str*, values of ."""

    result = {}

    company_name = getCompanyName()
    if company_name:
        result["CompanyName"] = company_name

    product_name = getProductName()
    if product_name:
        result["ProductName"] = product_name

    if options.file_description:
        result["FileDescription"] = options.file_description

    if options.legal_copyright:
        result["LegalCopyright"] = options.legal_copyright

    if options.legal_trademarks:
        result["LegalTrademarks"] = options.legal_trademarks

    return result


def _parseVersionNumber(value):
    if value:
        parts = value.split(".")

        assert len(parts) <= 4

        while len(parts) < 4:
            parts.append("0")

        r = tuple(int(d) for d in parts)
        assert min(r) >= 0
        assert max(r) < 2**16
        return r
    else:
        return None


def getProductVersion():
    """:returns: str, derived from ``--product-version``"""
    return options.product_version


def getProductVersionTuple():
    """:returns: tuple of 4 ints or None, derived from ``--product-version``"""
    return _parseVersionNumber(options.product_version)


def getFileVersion():
    """:returns str, derived from ``--file-version``"""
    return options.file_version


def getFileVersionTuple():
    """:returns tuple of 4 ints or None, derived from ``--file-version``"""
    return _parseVersionNumber(options.file_version)


def getProductFileVersion():
    if options.product_version:
        if options.file_version:
            return "%s-%s" % (options.product_version, options.file_version)
        else:
            return options.product_version
    else:
        return options.file_version


def getWindowsSplashScreen():
    """:returns: bool derived from ``--onefile-windows-splash-screen-image``"""
    return options.splash_screen_image


def getCompanyName():
    """*str* name of the company to use derived from ``--company-name``"""
    return options.company_name


def getProductName():
    """*str* name of the product to use derived from ``--product-name``"""
    return options.product_name


def getMacOSTargetArch():
    """:returns: str enum ("universal", "arm64", "x86_64") derived from ``--macos-target-arch`` value"""
    macos_target_arch = options.macos_target_arch or "native"

    if macos_target_arch == "native":
        macos_target_arch = getArchitecture()

    return macos_target_arch


def shallCreateAppBundle():
    """*bool* shall create an application bundle, derived from ``--macos-create-app-bundle`` value"""
    if shallCreatePythonPgoInput():
        return False

    return options.macos_create_bundle and isMacOS()


def getMacOSSigningIdentity():
    """*str* value to use as identity for codesign, derived from ``--macos-sign-identity`` value"""
    result = options.macos_sign_identity

    if result == "ad-hoc":
        result = "-"

    return result


def shallUseSigningForNotarization():
    """*bool* flag to use for codesign, derived from ``--macos-sign-notarization`` value"""
    return options.macos_sign_notarization


def getMacOSAppName():
    """*str* name of the app to use bundle"""
    return options.macos_app_name


def getMacOSSignedAppName():
    """*str* name of the app to use during signing"""
    return options.macos_signed_app_name


def getMacOSAppVersion():
    """*str* version of the app to use for bundle"""
    return options.macos_app_version


def getMacOSAppProtectedResourcesAccesses():
    """*list* key, value for protected resources of the app to use for bundle"""
    for macos_protected_resource in options.macos_protected_resources:
        yield macos_protected_resource.split(":", 1)


def isMacOSBackgroundApp():
    """*bool*, derived from ``--macos-app-mode``"""
    return options.macos_app_mode == "background"


def isMacOSUiElementApp():
    """*bool*, derived from ``--macos-app-mode``"""
    return options.macos_app_mode == "ui-element"


_python_flags = None


def _getPythonFlags():
    """*list*, values of ``--python-flag``"""
    # There is many flags, pylint: disable=too-many-branches

    # singleton, pylint: disable=global-statement
    global _python_flags

    if _python_flags is None:
        _python_flags = set()

        for parts in options.python_flags:
            for part in parts.split(","):
                if part in ("-S", "nosite", "no_site"):
                    _python_flags.add("no_site")
                elif part in ("site",):
                    if "no_site" in _python_flags:
                        _python_flags.remove("no_site")
                elif part in (
                    "-R",
                    "static_hashes",
                    "norandomization",
                    "no_randomization",
                ):
                    _python_flags.add("no_randomization")
                elif part in ("-v", "trace_imports", "trace_import"):
                    _python_flags.add("trace_imports")
                elif part in ("no_warnings", "nowarnings"):
                    _python_flags.add("no_warnings")
                elif part in ("-O", "no_asserts", "noasserts"):
                    _python_flags.add("no_asserts")
                elif part in ("no_docstrings", "nodocstrings"):
                    _python_flags.add("no_docstrings")
                elif part in ("-OO",):
                    _python_flags.add("no_docstrings")
                    _python_flags.add("no_asserts")
                elif part in ("no_annotations", "noannotations"):
                    _python_flags.add("no_annotations")
                elif part in ("unbuffered", "-u"):
                    _python_flags.add("unbuffered")
                elif part in ("-m", "package_mode"):
                    _python_flags.add("package_mode")
                elif part in ("-I", "isolated"):
                    _python_flags.add("isolated")
                elif part in ("-B", "dontwritebytecode"):
                    _python_flags.add("dontwritebytecode")
                else:
                    Tracing.options_logger.sysexit(
                        "Unsupported python flag '%s'." % part
                    )

    return _python_flags


def hasPythonFlagNoSite():
    """*bool* = "no_site" in python flags given"""

    return "no_site" in _getPythonFlags()


def hasPythonFlagNoAnnotations():
    """*bool* = "no_annotations" in python flags given"""

    return "no_annotations" in _getPythonFlags()


def hasPythonFlagNoAsserts():
    """*bool* = "no_asserts" in python flags given"""

    return "no_asserts" in _getPythonFlags()


def hasPythonFlagNoDocStrings():
    """*bool* = "no_docstrings" in python flags given"""

    return "no_docstrings" in _getPythonFlags()


def hasPythonFlagNoWarnings():
    """*bool* = "no_warnings" in python flags given"""

    return "no_warnings" in _getPythonFlags()


def hasPythonFlagIsolated():
    """*bool* = "isolated" in python flags given"""

    return "isolated" in _getPythonFlags()


def hasPythonFlagTraceImports():
    """*bool* = "trace_imports", "-v" in python flags given"""

    return "trace_imports" in _getPythonFlags()


def hasPythonFlagNoRandomization():
    """*bool* = "no_randomization", "-R", "static_hashes" in python flags given"""

    return "no_randomization" in _getPythonFlags()


def hasPythonFlagNoBytecodeRuntimeCache():
    """*bool* = "dontwritebytecode", "-u" in python flags given"""

    return "dontwritebytecode" in _getPythonFlags()


def hasPythonFlagUnbuffered():
    """*bool* = "unbuffered", "-u" in python flags given"""

    return "unbuffered" in _getPythonFlags()


def hasPythonFlagPackageMode():
    """*bool* = "package_mode", "-m" in python flags given"""

    return "package_mode" in _getPythonFlags()


def shallNotUseDependsExeCachedResults():
    """:returns: bool derived from ``--disable-dll-dependency-cache`` or ``--force-dll-dependency-cache-update``"""
    return shallNotStoreDependsExeCachedResults() or getattr(
        options, "update_dependency_cache", False
    )


def shallNotStoreDependsExeCachedResults():
    """:returns: bool derived from ``--disable-dll-dependency-cache``"""
    return shallDisableCacheUsage("dll-dependencies")


def getPluginNameConsideringRenames(plugin_name):
    """Name of the plugin with renames considered."""

    # spell-checker: ignore delvewheel,pyzmq

    if plugin_name == "etherium":
        return "ethereum"
    if plugin_name == "pyzmq":
        return "delvewheel"

    return plugin_name


def getPluginsEnabled():
    """*tuple*, user enabled (standard) plugins (not including user plugins)

    Note:
        Do not use this outside of main binary, as plugins are allowed
        to activate plugins themselves and that will not be visible here.
    """
    result = OrderedSet()

    if options:
        for plugin_enabled in options.plugins_enabled:
            result.update(
                getPluginNameConsideringRenames(plugin_name)
                for plugin_name in plugin_enabled.split(",")
            )

    return tuple(result)


def getPluginsDisabled():
    """*tuple*, user disabled (standard) plugins.

    Note:
        Do not use this outside of main binary, as other plugins, e.g.
        hinted compilation will activate plugins themselves and this
        will not be visible here.
    """
    result = OrderedSet()

    if options:
        for plugin_disabled in options.plugins_disabled:
            result.update(
                getPluginNameConsideringRenames(plugin_name)
                for plugin_name in plugin_disabled.split(",")
            )

    return tuple(result)


def getUserPlugins():
    """*tuple*, items user provided of ``--user-plugin=``"""
    if not options:
        return ()

    return tuple(set(options.user_plugins))


def shallDetectMissingPlugins():
    """*bool* = **not** ``--plugin-no-detection``"""
    return options is not None and options.detect_missing_plugins


def getPythonPathForScons():
    """*str*, value of ``--python-for-scons``"""
    return options.python_scons


def shallCompileWithoutBuildDirectory():
    """*bool* currently hard coded, not when using debugger.

    When this is used, compilation is executed in a fashion that it runs
    inside the build folder, hiding it, attempting to make results more
    reproducible across builds of different programs.

    TODO: Make this not hardcoded, but possible to disable via an
    options.
    """
    return not shallRunInDebugger()


def shallPreferSourceCodeOverExtensionModules():
    """*bool* prefer source code over extension modules if both are there"""
    return options is not None and options.prefer_source_code


def shallUseProgressBar():
    """*bool* prefer source code over extension modules if both are there"""
    return options.progress_bar


def getForcedStdoutPath():
    """*str* force program stdout output into that filename"""
    if shallCreatePythonPgoInput():
        return False

    return options.force_stdout_spec


def getForcedStderrPath():
    """*str* force program stderr output into that filename"""
    if shallCreatePythonPgoInput():
        return False

    return options.force_stderr_spec


def shallShowSourceModifications(module_name):
    """*bool* display plugin source changes derived from --show-source-changes"""
    if options is None:
        return False

    result, _reason = module_name.matchesToShellPatterns(options.show_source_changes)

    return result


def isLowMemory():
    """*bool* low memory usage requested"""
    return options.low_memory


def getCompilationReportFilename():
    """*str* filename to write XML report of compilation to"""
    return options.compilation_report_filename


def getCompilationReportTemplates():
    """*tuple of str,str* template and output filenames to write reports to"""
    result = []
    for value in options.compilation_report_templates:
        result.append(value.split(":", 1))

    return tuple(result)


def getCompilationReportUserData():
    result = OrderedDict()

    for desc in options.compilation_report_user_data:
        if "=" not in desc:
            Tracing.options_logger.sysexit(
                "Error, user report data must be of key=value form not '%s'." % desc
            )

        key, value = desc.split("=", 1)

        if key in result and value != result[key]:
            Tracing.options_logger.sysexit(
                "Error, user report data key '%s' has been given conflicting values '%s' and '%s'."
                % (
                    key,
                    result[key],
                    value,
                )
            )

        if not re.match(
            r"^([_a-z][\w]?|[a-w_yz][\w]{2,}|[_a-z][a-l_n-z\d][\w]+|[_a-z][\w][a-k_m-z\d][\w]*)$",
            key,
        ):
            Tracing.options_logger.sysexit(
                "Error, user report data key '%s' is not valid as an XML tag, and therefore cannot be used."
                % key
            )

        result[key] = value

    return result


def shallCreateDiffableCompilationReport():
    """*bool*" derived from --report-diffable"""
    return options.compilation_report_diffable


def getUserProvidedYamlFiles():
    """*list* files with user provided Yaml files"""
    return options.user_yaml_files


def _getWarningMnemonicsDisabled():
    return sum([_splitShellPattern(x) for x in options.nowarn_mnemonics], [])


def shallDisplayWarningMnemonic(mnemonic):
    """*bool*" derived from --nowarn-mnemonic"""
    for pattern in _getWarningMnemonicsDisabled():
        if fnmatch.fnmatch(mnemonic, pattern):
            return False

    return True


def shallShowExecutedCommands():
    return isExperimental("show-commands")


def getTargetPythonDescription():
    """:returns: tuple(python_version,OS/arch) string derived from ``--target``"""
    if options.target_spec is not None:
        # TODO: Only one we are working on right now.
        assert options.target_spec == "wasi"

        return python_version, "wasi"

    return None


def getFcfProtectionMode():
    """:returns: string derived from ``--fcf-protection``"""
    return options.cf_protection


def getModuleParameter(module_name, parameter_name):
    """:returns: string derived from ``--module-parameter``"""

    module_name_prefix = module_name.getTopLevelPackageName().asString()

    if parameter_name.startswith(module_name_prefix + "-"):
        option_name = parameter_name
    else:
        option_name = module_name_prefix + "-" + parameter_name

    for module_option in options.module_parameters:
        module_option_name, module_option_value = module_option.split("=", 1)

        if option_name == module_option_name:
            return module_option_value

    return None


def getForcedRuntimeEnvironmentVariableValues():
    """:returns: iterable (string, string) derived from ``----force-runtime-environment-variable``"""

    for forced_runtime_env_variables_spec in options.forced_runtime_env_variables:
        name, value = forced_runtime_env_variables_spec.split("=", 1)

        yield (name, value)


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
