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
""" Options module """

import os
import sys

from nuitka import Progress, Tracing
from nuitka.containers.oset import OrderedSet
from nuitka.OptionParsing import parseOptions
from nuitka.PythonVersions import (
    getSupportedPythonVersions,
    isUninstalledPython,
    python_version_str,
)
from nuitka.utils.FileOperations import resolveShellPatternToFilenames
from nuitka.utils.Utils import getOS, hasOnefileSupportedOS, isWin32Windows

options = None
positional_args = None
extra_args = []
is_nuitka_run = None
is_debug = None
is_nondebug = None
is_fullcompat = None


def parseArgs(will_reexec):
    # singleton with many cases checking the options right away.
    # pylint: disable=global-statement,too-many-branches,too-many-locals,too-many-statements
    global is_nuitka_run, options, positional_args, extra_args, is_debug, is_nondebug, is_fullcompat

    if os.name == "nt":
        # Windows store Python's don't allow looking at the python, catch that.
        try:
            with open(sys.executable):
                pass
        except OSError:
            Tracing.general.sysexit(
                "Error, the Python from Windows store is not supported, check the User Manual of Nuitka ."
            )

    is_nuitka_run, options, positional_args, extra_args = parseOptions(
        logger=Tracing.options_logger
    )

    if options.quiet or int(os.environ.get("NUITKA_QUIET", "0")):
        Tracing.setQuiet()

    if not will_reexec and not shallDumpBuiltTreeXML():
        Tracing.options_logger.info(
            "Used command line options: %s" % " ".join(sys.argv[1:])
        )

    if options.progress_bar and not will_reexec:
        Progress.enableProgressBar()

    if options.verbose_output and not will_reexec:
        Tracing.optimization_logger.setFileHandle(
            # Can only have unbuffered binary IO in Python3, therefore not disabling buffering here.
            open(options.verbose_output, "w")
        )

        options.verbose = True

    Tracing.optimization_logger.is_quiet = not options.verbose

    if options.show_inclusion_output and not will_reexec:
        Tracing.inclusion_logger.setFileHandle(
            # Can only have unbuffered binary IO in Python3, therefore not disabling buffering here.
            open(options.show_inclusion_output, "w")
        )

        options.show_inclusion = True

    Tracing.progress_logger.is_quiet = not options.show_progress

    # Onefile implies standalone build.
    if options.is_onefile:
        options.is_standalone = True

    # Provide a tempdir spec implies onefile tempdir.
    if options.windows_onefile_tempdir_spec:
        options.is_windows_onefile_tempdir = True

    # Standalone mode implies an executable, not importing "site" module, which is
    # only for this machine, recursing to all modules, and even including the
    # standard library.
    if options.is_standalone:
        if not options.executable:
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
Error, '--follow-import-to' takes only module names, not directory path '%s'."""
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
Error, '--nofollow-import-to' takes only module names, not directory path '%s'."""
                % no_case_module
            )

    scons_python = getPythonPathForScons()

    if scons_python is not None and not os.path.isfile(scons_python):
        Tracing.options_logger.sysexit(
            "Error, no such Python binary %r, should be full path." % scons_python
        )

    if options.output_filename is not None and (
        isStandaloneMode() or shallMakeModule()
    ):
        Tracing.options_logger.sysexit(
            """\
Error, can only specify output filename for acceleration mode, not for module
mode where filenames are mandatory, and not for standalone where there is a
sane default used inside the dist folder."""
        )

    if getOS() == "Linux":
        if len(getIconPaths()) > 1:
            Tracing.options_logger.sysexit("Error, can only use one icon on Linux.")

    for icon_path in getIconPaths():
        if "#" in icon_path and isWin32Windows():
            icon_path, icon_index = icon_path.rsplit("#", 1)

            if not icon_index.isdigit() or int(icon_index) < 0:
                Tracing.options_logger.sysexit(
                    "Error, icon number in %r not valid."
                    % (icon_path + "#" + icon_index)
                )

        if not os.path.exists(icon_path):
            Tracing.options_logger.sysexit(
                "Error, icon path %r does not exist." % icon_path
            )

        if getWindowsIconExecutablePath():
            Tracing.options_logger.sysexit(
                "Error, can only use icons from template executable or from icon files, but not both."
            )

    icon_exe_path = getWindowsIconExecutablePath()
    if icon_exe_path is not None and not os.path.exists(icon_exe_path):
        Tracing.options_logger.sysexit(
            "Error, icon path %r does not exist." % icon_exe_path
        )

    try:
        file_version = getWindowsFileVersion()
    except Exception:  # Catch all the things, don't want any interface, pylint: disable=broad-except
        Tracing.options_logger.sysexit(
            "Error, file version must be a tuple of up to 4 integer values."
        )

    try:
        product_version = getWindowsProductVersion()
    except Exception:  # Catch all the things, don't want any interface, pylint: disable=broad-except
        Tracing.options_logger.sysexit(
            "Error, product version must be a tuple of up to 4 integer values."
        )

    if getWindowsCompanyName() == "":
        Tracing.options_logger.sysexit(
            """Error, empty string is not an acceptable company name."""
        )

    if getWindowsProductName() == "":
        Tracing.options_logger.sysexit(
            """Error, empty string is not an acceptable product name."""
        )

    if file_version or product_version or getWindowsVersionInfoStrings():
        if not (file_version or product_version) and getWindowsCompanyName():
            Tracing.options_logger.sysexit(
                "Error, company name and file or product version need to be given when any version information is given."
            )

    if isOnefileMode() and not hasOnefileSupportedOS():
        Tracing.options_logger.sysexit("Error, unsupported OS for onefile %r" % getOS())

    if isOnefileMode() and os.name == "nt":
        if not getWindowsCompanyName() and not isWindowsOnefileTempDirMode():
            Tracing.options_logger.sysexit(
                """Error, onefile on Windows needs more options.

It requires either company name and product version to be given or
the selection of onefile temp directory mode. Check --help output."""
            )

    if options.recurse_none and options.recurse_all:
        Tracing.options_logger.sysexit(
            "Conflicting options '--follow-imports' and '--nofollow-imports' given."
        )

    if getShallIncludePackageData() and not isStandaloneMode():
        Tracing.options_logger.sysexit(
            "Error, package data files are only included in standalone or onefile mode."
        )

    for module_pattern in getShallIncludePackageData():
        if (
            module_pattern.startswith("-")
            or "/" in module_pattern
            or "\\" in module_pattern
        ):
            Tracing.options_logger.sysexit(
                "Error, '--include-package-data' needs module name or pattern as an argument, not %r."
                % module_pattern
            )

    for module_pattern in getShallFollowModules():
        if (
            module_pattern.startswith("-")
            or "/" in module_pattern
            or "\\" in module_pattern
        ):
            Tracing.options_logger.sysexit(
                "Error, '--follow-import-to' options needs module name or pattern as an argument, not %r."
                % module_pattern
            )
    for module_pattern in getShallFollowInNoCase():
        if (
            module_pattern.startswith("-")
            or "/" in module_pattern
            or "\\" in module_pattern
        ):
            Tracing.options_logger.sysexit(
                "Error, '--nofollow-import-to' options needs module name or pattern as an argument, not %r."
                % module_pattern
            )

    for data_file in options.data_files:
        if "=" not in data_file:
            Tracing.options_logger.sysexit(
                "Error, malformed data file description, must specify relative target path with =."
            )

        src, dst = data_file.split("=", 1)

        if os.path.isabs(dst):
            Tracing.options_logger.sysexit(
                "Error, must specify relative target path for data file, not %r."
                % data_file
            )

        if not resolveShellPatternToFilenames(src):
            Tracing.options_logger.sysexit("Error, %r does not match any files." % src)

    for data_dir in options.data_dirs:
        if "=" not in data_dir:
            Tracing.options_logger.sysexit(
                "Error, malformed data dir description, must specify relative target path with '=' separating it."
            )

        src, dst = data_dir.split("=", 1)

        if os.path.isabs(dst):
            Tracing.options_logger.sysexit(
                "Error, must specify relative target path for data dir, not %r as in %r."
                % (dst, data_dir)
            )

        if not os.path.isdir(src):
            Tracing.options_logger.sysexit(
                "Error, must specify existing source data directory, not %r as in %r."
                % (dst, data_dir)
            )

    if (options.data_files or options.data_dirs) and not isStandaloneMode():
        Tracing.options_logger.sysexit(
            "Error, data files are only included in standalone or onefile mode."
        )

    for pattern in getShallFollowExtraFilePatterns():
        if os.path.isdir(pattern):
            Tracing.options_logger.sysexit(
                "Error, pattern %r given to '--include-plugin-files' cannot be a directory name."
                % pattern
            )

    is_debug = _isDebug()
    is_nondebug = not is_debug
    is_fullcompat = _isFullCompat()


def commentArgs():
    """Comment on options, where we know something is not having the intended effect."""
    # A ton of cases to consider, pylint: disable=too-many-boolean-expressions,too-many-branches

    # Inform the user about potential issues with the running version. e.g. unsupported
    # version.
    if python_version_str not in getSupportedPythonVersions():
        # Do not disturb run of automatic tests with, detected from the presence of
        # that environment variable.
        if "PYTHON" not in os.environ:
            Tracing.general.warning(
                "The version %r is not currently supported. Expect problems."
                % python_version_str,
            )

    default_reference_mode = (
        "runtime" if shallMakeModule() or isStandaloneMode() else "original"
    )

    if getFileReferenceMode() is None:
        options.file_reference_mode = default_reference_mode
    else:
        if options.file_reference_mode != default_reference_mode:
            Tracing.options_logger.warning(
                "Using non-default file reference mode %r rather than %r may cause runtime issues."
                % (getFileReferenceMode(), default_reference_mode)
            )
        else:
            Tracing.options_logger.info(
                "Using default file reference mode %r need not be specified."
                % default_reference_mode
            )

    if getOS() != "Windows":
        if (
            getWindowsIconExecutablePath()
            or shallAskForWindowsAdminRights()
            or shallAskForWindowsUIAccessRights()
            or getWindowsCompanyName()
            or getWindowsProductName()
            or getWindowsProductVersion()
            or getWindowsFileVersion()
            or isWindowsOnefileTempDirMode()
            or getWindowsOnefileTempDirSpec(use_default=False)
            or getForcedStderrPath()  # not yet for other platforms
            or getForcedStdoutPath()
        ):
            Tracing.options_logger.warning(
                "Using Windows specific options has no effect on other platforms."
            )

    if not isOnefileMode() and (
        isWindowsOnefileTempDirMode() or getWindowsOnefileTempDirSpec(use_default=False)
    ):
        Tracing.options_logger.warning(
            "Using onefile specific option for Windows without --onefile enabled."
        )

    if isOnefileMode():
        standalone_mode = "onefile"
    elif isStandaloneMode():
        standalone_mode = "standalone"
    else:
        standalone_mode = None

    if standalone_mode and getOS() == "NetBSD":
        Tracing.options_logger.warning(
            "Standalone mode on NetBSD is not functional, due to $ORIGIN linkage not being supported."
        )

    if options.recurse_all and standalone_mode:
        if standalone_mode:
            Tracing.options_logger.info(
                "Following all imports is the default for %s mode and need not be specified."
                % standalone_mode
            )

    if options.recurse_none and standalone_mode:
        if standalone_mode:
            Tracing.options_logger.warning(
                "Following no imports is unlikely to work for %s mode and should not be specified."
                % standalone_mode
            )

    if options.dependency_tool:
        Tracing.options_logger.warning(
            "Using removed option '--windows-dependency-tool' is deprecated and has no impact anymore."
        )


def isVerbose():
    """*bool* = "--verbose" """
    return options is not None and options.verbose


def shallTraceExecution():
    """*bool* = "--trace-execution" """
    return options.trace_execution


def shallExecuteImmediately():
    """*bool* = "--run" """
    return options.immediate_execution


def shallRunInDebugger():
    """*bool* = "--debug" """
    return options.debugger


def shallDumpBuiltTreeXML():
    """*bool* = "--xml" """
    return options.dump_xml


def shallOnlyExecCCompilerCall():
    """*bool* = "--recompile-c-only" """
    return options.recompile_c_only


def shallNotDoExecCCompilerCall():
    """*bool* = "--generate-c-only" """
    return options.generate_c_only


def getFileReferenceMode():
    """*str*, one of "runtime", "original", "frozen", coming from "--file-reference-choice"

    Notes:
        Defaults to runtime for modules and packages, as well as standalone binaries,
        otherwise original is kept.
    """

    return options.file_reference_mode


def shallMakeModule():
    """*bool* = "--module" """
    return not options.executable


def shallCreatePyiFile():
    """*bool* = **not** "--no-pyi-file" """
    return options.pyi_file


def isAllowedToReexecute():
    """*bool* = **not** "--must-not-re-execute" """
    return options.allow_reexecute


def shallFollowStandardLibrary():
    """*bool* = "--follow-stdlib" """
    return options.recurse_stdlib


def shallFollowNoImports():
    """*bool* = "--nofollow-imports" """
    return options.recurse_none


def shallFollowAllImports():
    """*bool* = "--follow-imports" """
    return options.is_standalone or options.recurse_all


def _splitShellPattern(value):
    return value.split(",") if "{" not in value else [value]


def getShallFollowInNoCase():
    """*list*, items of "--nofollow-import-to=" """
    return sum([_splitShellPattern(x) for x in options.recurse_not_modules], [])


def getShallFollowModules():
    """*list*, items of "--follow-import-to=" """
    return sum(
        [
            _splitShellPattern(x)
            for x in options.recurse_modules
            + options.include_modules
            + options.include_packages
        ],
        [],
    )


def getShallFollowExtra():
    """*list*, items of "--include-plugin-directory=" """
    return sum([_splitShellPattern(x) for x in options.recurse_extra], [])


def getShallFollowExtraFilePatterns():
    """*list*, items of "--include-plugin-files=" """
    return sum([_splitShellPattern(x) for x in options.recurse_extra_files], [])


def getMustIncludeModules():
    """*list*, items of "--include-module=" """
    return sum([_splitShellPattern(x) for x in options.include_modules], [])


def getMustIncludePackages():
    """*list*, items of "--include-package=" """
    return sum([_splitShellPattern(x) for x in options.include_packages], [])


def getShallIncludePackageData():
    """*list*, items of "--include-package-data=" """
    return sum([_splitShellPattern(x) for x in options.package_data], [])


def getShallIncludeDataFiles():
    """*list*, items of "--include-data-file=" """
    for data_file in options.data_files:
        src, dest = data_file.split("=", 1)

        for pattern in _splitShellPattern(src):
            yield pattern, dest, data_file


def getShallIncludeDataDirs():
    """*list*, items of "--include-data-dir=" """
    for data_file in options.data_dirs:
        src, dest = data_file.split("=", 1)

        yield src, dest


def shallWarnImplicitRaises():
    """*bool* = "--warn-implicit-exceptions" """
    return options.warn_implicit_exceptions


def shallWarnUnusualCode():
    """*bool* = "--warn-unusual-code" """
    return options.warn_unusual_code


def assumeYesForDownloads():
    """*bool* = "--assume-yes-for-downloads" """
    return options is not None and options.assume_yes_for_downloads


def _isDebug():
    """*bool* = "--debug" or "--debugger" """
    return options is not None and (options.debug or options.debugger)


def isPythonDebug():
    """*bool* = "--python-debug" or "sys.flags.debug" """
    return options.python_debug or sys.flags.debug


def isUnstripped():
    """*bool* = "--unstripped" or "--profile" """
    return options.unstripped or options.profile


def isProfile():
    """*bool* = "--profile" """
    return options.profile


def shallCreateGraph():
    """*bool* = "--graph" """
    return options.graph


def getOutputFilename():
    """*str*, value of "-o" """
    return options.output_filename


def getOutputPath(path):
    """Return output pathname of a given path (filename)."""
    if options.output_dir:
        return os.path.normpath(os.path.join(options.output_dir, path))
    else:
        return path


def getOutputDir():
    """*str*, value of "--output-dir" or "." """
    return options.output_dir if options.output_dir else "."


def getPositionalArgs():
    """*tuple*, command line positional arguments"""
    return tuple(positional_args)


def getMainArgs():
    """*tuple*, arguments following the optional arguments"""
    return tuple(extra_args)


def shallOptimizeStringExec():
    """Inactive yet"""
    return False


def shallClearPythonPathEnvironment():
    """*bool* = **not** "--execute-with-pythonpath" """
    return not options.keep_pythonpath


def shallUseStaticLibPython():
    """*bool* = derived from `sys.prefix` and `os.name`

    Notes:
        Currently only Anaconda on non-Windows can do this.
    """

    if isWin32Windows() and os.path.exists(os.path.join(sys.prefix, "etc/config.site")):
        return True

    # For Anaconda default to trying static lib python library, which
    # normally is just not available or if it is even unusable.
    return (
        os.path.exists(os.path.join(sys.prefix, "conda-meta"))
        and not isWin32Windows()
        and not getOS() == "Darwin"
    )


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


def isShowScons():
    """*bool* = "--show-scons" """
    return options.show_scons


def getJobLimit():
    """*int*, value of "--jobs" / "-j" or number of CPU kernels"""
    return int(options.jobs)


def isLto():
    """*bool* = "--lto" """
    return options.lto


def isClang():
    """*bool* = "--clang" """
    return options.clang


def isMingw64():
    """*bool* = "--mingw64", available only on Windows, otherwise false"""
    return getattr(options, "mingw64", False)


def getMsvcVersion():
    """*str*, value of "--msvc", available only on Windows, otherwise None"""
    return getattr(options, "msvc", None)


def shallDisableConsoleWindow():
    """*bool* = "--win-disable-console" """
    return options.win_disable_console


def _isFullCompat():
    """*bool* = "--full-compat"

    Notes:
        Code should should use "Options.is_fullcompat" instead, this
        is only used to initialize that value.
    """
    return options is not None and not options.improved


def isShowProgress():
    """*bool* = "--show-progress" """
    return options is not None and options.show_progress


def isShowMemory():
    """*bool* = "--show-memory" """
    return options is not None and options.show_memory


def isShowInclusion():
    """*bool* = "--show-modules" """
    return options.show_inclusion


def isRemoveBuildDir():
    """*bool* = "--remove-output" """
    return options.remove_build and not options.generate_c_only


def getIntendedPythonArch():
    """*str*, one of "x86", "x86_64" or None"""
    return options.python_arch


experimental = set()


def isExperimental(indication):
    """Check whether a given experimental feature is enabled.

    Args:
        indication: (str) feature name
    Returns:
        bool
    """
    return (
        indication in experimental
        or hasattr(options, "experimental")
        and indication in options.experimental
    )


def enableExperimental(indication):
    experimental.add(indication)


def disableExperimental(indication):
    experimental.remove(indication)


def getExperimentalIndications():
    """*tuple*, items of "--experimental=" """
    if hasattr(options, "experimental"):
        return options.experimental
    else:
        return ()


def shallExplainImports():
    """*bool* = "--explain-imports" """
    return options is not None and options.explain_imports


def isStandaloneMode():
    """*bool* = "--standalone" """
    return options.is_standalone


def isOnefileMode():
    """*bool* = "--onefile" """
    return options.is_onefile


def isWindowsOnefileTempDirMode():
    """*bool* = "--windows-onefile-tempdir" """
    return options.is_windows_onefile_tempdir


def getWindowsOnefileTempDirSpec(use_default):
    if use_default:
        return options.windows_onefile_tempdir_spec or r"%TEMP%\onefile_%PID%_%TIME%"
    else:
        return options.windows_onefile_tempdir_spec


def getIconPaths():
    """*list of str*, values of "--windows-icon-from-ico" and "--linux-onefile-icon """

    result = options.icon_path

    # Check if Linux icon requirement is met.
    if getOS() == "Linux" and not result and isOnefileMode():
        default_icon = "/usr/share/pixmaps/python.xpm"
        if os.path.exists(default_icon):
            result.append(default_icon)
        else:
            Tracing.options_logger.sysexit(
                """\
Error, the default icon %r does not exist, making --linux-onefile-icon required."""
                % default_icon
            )

    return result


def getWindowsIconExecutablePath():
    """*str* or *None* if not given, value of "--windows-icon-from-exe" """
    return options.icon_exe_path


def shallAskForWindowsAdminRights():
    """*bool*, value of "--windows-uac-admin" or --windows-uac-uiaccess """
    return options.windows_uac_admin


def shallAskForWindowsUIAccessRights():
    """*bool*, value of "--windows-uac-uiaccess" """
    return options.windows_uac_uiaccess


def getWindowsVersionInfoStrings():
    """*dict of str*, values of ."""

    result = {}

    company_name = getWindowsCompanyName()
    if company_name:
        result["CompanyName"] = company_name

    product_name = getWindowsProductName()
    if product_name:
        result["ProductName"] = product_name

    if options.windows_file_description:
        result["FileDescription"] = options.windows_file_description

    return result


def _parseWindowsVersionNumber(value):
    if value:
        parts = value.split(".")

        assert len(parts) <= 4

        while len(parts) < 4:
            parts.append("0")

        r = tuple(int(d) for d in parts)
        assert min(r) >= 0
        assert max(r) < 2 ** 16
        return r
    else:
        return None


def getWindowsProductVersion():
    """*tuple of 4 ints* or None --windows-product-version """
    return _parseWindowsVersionNumber(options.windows_product_version)


def getWindowsFileVersion():
    """*tuple of 4 ints* or None --windows-file-version """
    return _parseWindowsVersionNumber(options.windows_file_version)


def getWindowsCompanyName():
    """*str* name of the company to use """
    return options.windows_company_name


def getWindowsProductName():
    """*str* name of the product to use """
    return options.windows_product_name


_python_flags = None


def getPythonFlags():
    """*list*, value of "--python-flag" """
    # singleton, pylint: disable=global-statement
    global _python_flags

    if _python_flags is None:
        _python_flags = set()

        for parts in options.python_flags:
            for part in parts.split(","):
                if part in ("-S", "nosite", "no_site"):
                    _python_flags.add("no_site")
                elif part in ("static_hashes", "norandomization", "no_randomization"):
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
                else:
                    Tracing.options_logger.sysexit("Unsupported python flag %r." % part)

    return _python_flags


def hasPythonFlagNoSite():
    """*bool* = "no_site" in python flags given """

    return "no_site" in getPythonFlags()


def hasPythonFlagNoAnnotations():
    """*bool* = "no_annotations" in python flags given """

    return "no_annotations" in getPythonFlags()


def shallFreezeAllStdlib():
    """*bool* = **not** shallFollowStandardLibrary"""
    return not shallFollowStandardLibrary()


def getWindowsDependencyTool():
    """*str*, value of "--windows-dependency-tool=" """
    return options.dependency_tool


def shallNotUseDependsExeCachedResults():
    """*bool* = "--disable-dll-dependency-cache" or "--force-dll-dependency-cache-update" """
    return shallNotStoreDependsExeCachedResults() or getattr(
        options, "update_dependency_cache", False
    )


def shallNotStoreDependsExeCachedResults():
    """*bool* = "--disable-dll-dependency-cache" """
    return getattr(options, "no_dependency_cache", False)


def getPluginsEnabled():
    """*tuple*, user enabled (standard) plugins (not including user plugins)

    Note:
        Do not use this outside of main binary, as other plugins, e.g.
        hinted compilation will activate plugins themselves and this
        will not be visible here.
    """
    result = OrderedSet()

    if options:
        for plugin_enabled in options.plugins_enabled:
            result.update(plugin_enabled.split(","))

    return tuple(result)


def getPluginsDisabled():
    """*tuple*, user disabled (standard) plugins.

    Note:
        Do not use this outside of main binary, as other plugins, e.g.
        hinted compilation will activate plugins themselves and this
        will not be visible here.
    """
    if not options:
        return ()

    return tuple(set(options.plugins_disabled))


def getUserPlugins():
    """*tuple*, items user provided of "--user-plugin=" """
    if not options:
        return ()

    return tuple(set(options.user_plugins))


def shallDetectMissingPlugins():
    """*bool* = **not** "--plugin-no-detection" """
    return options is not None and options.detect_missing_plugins


def getPythonPathForScons():
    """*str*, value of "--python-for-scons" """
    return options.python_scons


def shallCompileWithoutBuildDirectory():
    """*bool* currently hard coded, not when using debugger.

    TODO: Make this not hardcoded, but possible to disable via an
    options.
    """
    return not shallRunInDebugger()


def shallPreferSourcecodeOverExtensionModules():
    """*bool* prefer source code over extension modules if both are there"""
    return options is not None and options.prefer_source_code


def shallUseProgressBar():
    """*bool* prefer source code over extension modules if both are there"""
    return options.progress_bar


def getForcedStdoutPath():
    """*str* force program stdout output into that filename"""
    return options.force_stdout_spec


def getForcedStderrPath():
    """*str* force program stderr output into that filename"""
    return options.force_stderr_spec
