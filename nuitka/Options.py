#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

import logging
import os
import sys

from nuitka.OptionParsing import parseOptions
from nuitka.utils import Utils

options = None
positional_args = None
extra_args = []
is_nuitka_run = None


def parseArgs():
    # singleton with many cases, pylint: disable=global-statement,too-many-branches
    global is_nuitka_run, options, positional_args, extra_args

    is_nuitka_run, options, positional_args, extra_args = parseOptions()

    if options.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    # Standalone mode implies an executable, not importing "site" module, which is
    # only for this machine, recursing to all modules, and even including the
    # standard library.
    if options.is_standalone:
        if not options.executable:
            sys.exit(
                """\
Error, conflicting options, cannot make standalone module, only executable."""
            )

        options.recurse_all = True

        if Utils.getOS() == "NetBSD":
            logging.warning(
                "Standalone mode on NetBSD is not functional, due to $ORIGIN linkage not being supported."
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
            sys.exit(
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
            sys.exit(
                """\
Error, '--nofollow-import-to' takes only module names, not directory path '%s'."""
                % no_case_module
            )

    scons_python = getPythonPathForScons()

    if scons_python is not None and not os.path.exists(scons_python):
        sys.exit("Error, no such Python binary '%s'." % scons_python)

    if options.output_filename is not None and (
        isStandaloneMode() or shallMakeModule()
    ):
        sys.exit(
            """\
Error, can only specify output filename for acceleration mode, not for module
mode where filenames are mandatory, and not for standalone where there is a
sane default used inside the dist folder."""
        )


def isVerbose():
    """ *bool* = "--verbose"
    """
    return options.verbose


def shallTraceExecution():
    """ *bool* = "--trace-execution"
    """
    return options.trace_execution


def shallExecuteImmediately():
    """ *bool* = "--run"
    """
    return options.immediate_execution


def shallRunInDebugger():
    """ *bool* = "--debug"
    """
    return options.debugger


def shallDumpBuiltTreeXML():
    """ *bool* = "--xml"
    """
    return options.dump_xml


def shallOnlyExecCCompilerCall():
    """ *bool* = "--recompile-c-only"
    """
    return options.recompile_c_only


def shallNotDoExecCCompilerCall():
    """ *bool* = "--generate-c-only"
    """
    return options.generate_c_only


def getFileReferenceMode():
    """ *str*, one of "runtime", "original" or "--file-reference-mode"
    """
    if options.file_reference_mode is None:
        value = "runtime" if shallMakeModule() or isStandaloneMode() else "original"
    else:
        value = options.file_reference_mode

    return value


def shallMakeModule():
    """ *bool* = "--module"
    """
    return not options.executable


def shallCreatePyiFile():
    """ *bool* = **not** "--no-pyi-file"
    """
    return options.pyi_file


def isAllowedToReexecute():
    """ *bool* = **not** "--must-not-re-execute"
    """
    return options.allow_reexecute


def shallFollowStandardLibrary():
    """ *bool* = "--follow-stdlib" / "--recurse-stdlib"
    """
    return options.recurse_stdlib


def shallFollowNoImports():
    """ *bool* = "--nofollow-imports" / "--recurse-none"
    """
    return options.recurse_none


def shallFollowAllImports():
    """ *bool* = "--follow-imports" / "--recurse-all"
    """
    return options.recurse_all


def _splitShellPattern(value):
    return value.split(",") if "{" not in value else [value]


def getShallFollowInNoCase():
    """ *list*, items of "--nofollow-import-to=" / "--recurse-not-to="
    """
    return sum([_splitShellPattern(x) for x in options.recurse_not_modules], [])


def getShallFollowModules():
    """ *list*, items of "--follow-import-to=" / "--recurse-to="
    """
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
    """ *list*, items of "--include-plugin-directory="
    """
    return sum([_splitShellPattern(x) for x in options.recurse_extra], [])


def getShallFollowExtraFilePatterns():
    """ *list*, items of "--include-plugin-files="
    """
    return sum([_splitShellPattern(x) for x in options.recurse_extra_files], [])


def getMustIncludeModules():
    """ *list*, items of "--include-module="
    """
    return sum([_splitShellPattern(x) for x in options.include_modules], [])


def getMustIncludePackages():
    """ *list*, items of "--include-package="
    """
    return sum([_splitShellPattern(x) for x in options.include_packages], [])


def shallWarnImplicitRaises():
    """ *bool* = "--warn-implicit-exceptions"
    """
    return options.warn_implicit_exceptions


def shallWarnUnusualCode():
    """ *bool* = "--warn-unusual-code"
    """
    return options.warn_unusual_code


def assumeYesForDownloads():
    """ *bool* = "--assume-yes-for-downloads"
    """
    return options.assume_yes_for_downloads


def isDebug():
    """ *bool* = "--debug" or "--debugger"
    """
    return options is not None and (options.debug or options.debugger)


def isPythonDebug():
    """ *bool* = "--python-debug" or "sys.flags.debug"
    """
    return options.python_debug or sys.flags.debug


def isUnstripped():
    """ *bool* = "--unstripped" or "--profile"
    """
    return options.unstripped or options.profile


def isProfile():
    """ *bool* = "--profile"
    """
    return options.profile


def shallCreateGraph():
    """ *bool* = "--graph"
    """
    return options.graph


def getOutputFilename():
    """ *str*, value of "-o"
    """
    return options.output_filename


def getOutputPath(path):
    """ Return output pathname of a given path (filename).
    """
    if options.output_dir:
        return os.path.normpath(os.path.join(options.output_dir, path))
    else:
        return path


def getOutputDir():
    """ *str*, value of "--output-dir" or "."
    """
    return options.output_dir if options.output_dir else "."


def getPositionalArgs():
    """ *tuple*, command line positional arguments
    """
    return tuple(positional_args)


def getMainArgs():
    """ *tuple*, arguments following the optional arguments
    """
    return tuple(extra_args)


def shallOptimizeStringExec():
    """ Inactive yet
    """
    return False


def shallClearPythonPathEnvironment():
    """ *bool* = **not** "--execute-with-pythonpath"
    """
    return not options.keep_pythonpath


def isShowScons():
    """ *bool* = "--show-scons"
    """
    return options.show_scons


def getJobLimit():
    """ *int*, value of "--jobs" / "-j" or number of CPU kernels
    """
    return int(options.jobs)


def isLto():
    """ *bool* = "--lto"
    """
    return options.lto


def isClang():
    """ *bool* = "--clang"
    """
    return options.clang


def isMingw64():
    """ *bool* = "--mingw64"
    """
    return options.mingw64


def getMsvcVersion():
    """ *str*, value of "--msvc"
    """
    return options.msvc


def shallDisableConsoleWindow():
    """ *bool* = "--win-disable-console"
    """
    return options.win_disable_console


def isFullCompat():
    """ *bool* = "--full-compat"
    """
    return options is not None and not options.improved


def isShowProgress():
    """ *bool* = "--show-progress"
    """
    return options.show_progress


def isShowMemory():
    """ *bool* = "--show-memory"
    """
    return options is not None and options.show_memory


def isShowInclusion():
    """ *bool* = "--show-modules"
    """
    return options.show_inclusion


def isRemoveBuildDir():
    """ *bool* = "--remove-output"
    """
    return options.remove_build and not options.generate_c_only


def getIntendedPythonArch():
    """ *str*, one of "x86", "x86_64" or None
    """
    return options.python_arch


def isExperimental(indication):
    """ Check whether a given experimental feature is enabled.

    Args:
        indication: (str) feature name
    Returns:
        bool
    """
    return hasattr(options, "experimental") and indication in options.experimental


def getExperimentalIndications():
    """ *tuple*, items of "--experimental="
    """
    if hasattr(options, "experimental"):
        return options.experimental
    else:
        return ()


def shallExplainImports():
    """ *bool* = "--explain-imports"
    """
    return options is not None and options.explain_imports


def isStandaloneMode():
    """ *bool* = "--standalone"
    """
    return options.is_standalone


def getIconPath():
    """ *str*, value of "--windows-icon"
    """
    return options.icon_path


_python_flags = None


def getPythonFlags():
    """ *list*, value of "--python-flag"
    """
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
                elif part in ("-OO", "no_docstrings", "nodocstrings"):
                    _python_flags.add("no_docstrings")
                    _python_flags.add("no_asserts")
                else:
                    # Do not warn before executing in final context.
                    if "PYTHONHASHSEED" in os.environ:
                        logging.warning("Unsupported flag '%s'.", part)

    return _python_flags


def shallFreezeAllStdlib():
    """ *bool* = **not** shallFollowStandardLibrary
    """
    return not shallFollowStandardLibrary()


def shallNotUseDependsExeCachedResults():
    """ *bool* = "--disable-dll-dependency-cache" or "--force-dll-dependency-cache-update"
    """
    return options.no_dependency_cache or options.update_dependency_cache


def shallNotStoreDependsExeCachedResults():
    """ *bool* = "--disable-dll-dependency-cache"
    """
    return options.no_dependency_cache


def getPluginsEnabled():
    """ *tuple*, enabled plugins (including user plugins)

    """
    result = set()

    if options:
        for plugin_enabled in options.plugins_enabled:
            result.add(plugin_enabled.split("=", 1)[0])

    return tuple(result)


def getPluginOptions(plugin_name):
    """ Return the options provided for the specified plugin.

    Args:
        plugin_name: plugin identifier
    Returns:
        list created by split(',') for the string following "=" after plugin_name.
    """
    result = []

    if options:
        for plugin_enabled in options.plugins_enabled + options.user_plugins:
            if "=" not in plugin_enabled:
                continue

            name, args = plugin_enabled.split("=", 1)

            if name == plugin_name:
                result.extend(args.split(","))

    return result


def getPluginsDisabled():
    """ Return the names of disabled (standard) plugins.
    """
    if not options:
        return ()

    return tuple(set(options.plugins_disabled))


def getUserPlugins():
    """ *tuple*, items of "--user-plugin="
    """
    if not options:
        return ()

    return tuple(set(options.user_plugins))


def shallDetectMissingPlugins():
    """ *bool* = **not** "--plugin-no-detection"
    """
    return options is not None and options.detect_missing_plugins


def getPythonPathForScons():
    """ *str*, value of "--python-for-scons"
    """
    return options.python_scons
