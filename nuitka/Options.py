#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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

    if shallListPlugins():
        from nuitka.plugins.Plugins import listPlugins
        listPlugins()

    if options.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    # Standalone mode implies an executable, not importing "site" module, which is
    # only for this machine, recursing to all modules, and even including the
    # standard library.
    if options.is_standalone:
        if not options.executable:
            sys.exit("""\
Error, conflicting options, cannot make standalone module, only executable.""")

        options.recurse_all = True

        if Utils.getOS() == "NetBSD":
            logging.warning("Standalone mode on NetBSD is not functional, due to $ORIGIN linkage not being supported.")

    for any_case_module in getShallFollowModules():
        if any_case_module.startswith('.'):
            bad = True
        else:
            for char in "/\\:":
                if  char in any_case_module:
                    bad = True
                    break
            else:
                bad = False

        if bad:
            sys.exit(
                """\
Error, '--follow-import-to' takes only module names, not directory path '%s'.""" % \
                any_case_module
            )

    for no_case_module in getShallFollowInNoCase():
        if no_case_module.startswith('.'):
            bad = True
        else:
            for char in "/\\:":
                if  char in no_case_module:
                    bad = True
                    break
            else:
                bad = False

        if bad:
            sys.exit(
                """\
Error, '--nofollow-import-to' takes only module names, not directory path '%s'.""" % \
                no_case_module
            )

    scons_python = getPythonPathForScons()

    if scons_python is not None and not os.path.exists(scons_python):
        sys.exit("Error, no such Python binary '%s'." % scons_python)

    if options.output_filename is not None and \
       (isStandaloneMode() or shallMakeModule()):
        sys.exit(
            """\
Error, can only specify output filename for acceleration mode, not for module
mode where filenames are mandatory, and not for standalone where there is a
sane default used inside the dist folder."""
        )


def isVerbose():
    return options.verbose


def shallTraceExecution():
    return options.trace_execution


def shallExecuteImmediately():
    return options.immediate_execution


def shallRunInDebugger():
    return options.debugger


def shallDumpBuiltTreeXML():
    return options.dump_xml


def shallOnlyExecCCompilerCall():
    return options.recompile_c_only


def shallNotDoExecCCompilerCall():
    return options.generate_c_only


def getFileReferenceMode():
    if options.file_reference_mode is None:
        value = ("runtime"
                   if shallMakeModule() or isStandaloneMode() else
                 "original")
    else:
        value = options.file_reference_mode

    return value


def shallMakeModule():
    return not options.executable


def shallCreatePyiFile():
    return options.pyi_file


def isAllowedToReexecute():
    return options.allow_reexecute


def shallFollowStandardLibrary():
    return options.recurse_stdlib


def shallFollowNoImports():
    return options.recurse_none


def shallFollowAllImports():
    return options.recurse_all


def _splitShellPattern(value):
    return value.split(',') if '{' not in value else [value]


def getShallFollowInNoCase():
    return sum(
        [_splitShellPattern(x) for x in options.recurse_not_modules ],
        []
    )


def getShallFollowModules():
    return sum(
        [_splitShellPattern(x) for x in options.recurse_modules + options.include_modules + options.include_packages],
        []
    )


def getShallFollowExtra():
    return sum(
        [_splitShellPattern(x) for x in options.recurse_extra],
        []
    )


def getShallFollowExtraFilePatterns():
    return sum(
        [_splitShellPattern(x) for x in options.recurse_extra_files],
        []
    )


def getMustIncludeModules():
    return sum(
        [_splitShellPattern(x) for x in options.include_modules],
        []
    )


def getMustIncludePackages():
    return sum(
        [_splitShellPattern(x) for x in options.include_packages ],
        []
    )


def shallWarnImplicitRaises():
    return options.warn_implicit_exceptions


def shallWarnUnusualCode():
    return options.warn_unusual_code


def assumeYesForDownloads():
    return options.assume_yes_for_downloads


def isDebug():
    return options is not None and (options.debug or options.debugger)


def isPythonDebug():
    return options.python_debug or sys.flags.debug


def isUnstripped():
    return options.unstripped or options.profile


def isProfile():
    return options.profile


def shallCreateGraph():
    return options.graph


def getOutputFilename():
    return options.output_filename


def getOutputPath(path):
    if options.output_dir:
        return os.path.normpath(os.path.join(options.output_dir, path))
    else:
        return path


def getOutputDir():
    return options.output_dir if options.output_dir else '.'


def getPositionalArgs():
    return tuple(positional_args)


def getMainArgs():
    return tuple(extra_args)


def shallOptimizeStringExec():
    return False


def shallClearPythonPathEnvironment():
    return not options.keep_pythonpath


def isShowScons():
    return options.show_scons


def getJobLimit():
    return int(options.jobs)


def isLto():
    return options.lto


def isClang():
    return options.clang


def isMingw64():
    return options.mingw64


def getMsvcVersion():
    return options.msvc


def shallDisableConsoleWindow():
    return options.win_disable_console


def isFullCompat():
    return not options.improved


def isShowProgress():
    return options.show_progress


def isShowMemory():
    return options is not None and options.show_memory


def isShowInclusion():
    return options.show_inclusion


def isRemoveBuildDir():
    return options.remove_build and not options.generate_c_only


def getIntendedPythonArch():
    return options.python_arch


def isExperimental(indication):
    """ Are experimental features to be enabled."""

    return hasattr(options, "experimental") and indication in options.experimental


def getExperimentalIndications():
    if hasattr(options, "experimental"):
        return options.experimental
    else:
        return ()


def shallExplainImports():
    return options is not None and options.explain_imports


def isStandaloneMode():
    return options.is_standalone


def getIconPath():
    return options.icon_path

_python_flags = None

def getPythonFlags():
    # singleton, pylint: disable=global-statement
    global _python_flags

    if _python_flags is None:
        _python_flags = set()

        for parts in options.python_flags:
            for part in parts.split(','):
                if part in ("-S", "nosite", "no_site"):
                    _python_flags.add("no_site")
                elif part in ("static_hashes", "norandomization",
                              "no_randomization"):
                    _python_flags.add("no_randomization")
                elif part in ("-v", "trace_imports", "trace_import"):
                    _python_flags.add("trace_imports")
                elif part in ("no_warnings", "nowarnings"):
                    _python_flags.add("no_warnings")
                elif part in ("-O", "no_asserts", "noasserts"):
                    _python_flags.add("no_asserts")
                else:
                    # Do not warn before executing in final context.
                    if "PYTHONHASHSEED" in os.environ:
                        logging.warning("Unsupported flag '%s'.", part)

    return _python_flags


def shallFreezeAllStdlib():
    return not shallFollowStandardLibrary()


def shallNotUseDependsExeCachedResults():
    return options.no_dependency_cache or options.update_dependency_cache


def shallNotStoreDependsExeCachedResults():
    return options.no_dependency_cache


def shallListPlugins():
    return options is not None and options.list_plugins


def getPluginsEnabled():
    """ Return the names of plugin that were enabled.

    """
    result = set()

    if options:
        for plugin_enabled in options.plugins_enabled:
            result.add(plugin_enabled.split('=',1)[0])

    return tuple(result)


def getPluginOptions(plugin_name):
    """ Return the options provided for a specific plugin.

    """
    result = []

    if options:
        for plugin_enabled in options.plugins_enabled:
            if '=' not in plugin_enabled:
                continue

            name, args = plugin_enabled.split('=',1)

            if name == plugin_name:
                result.extend(args.split(','))

    return result


def getPluginsDisabled():
    """ Return the names of plugin that were disabled.

    """
    if not options:
        return ()

    return tuple(set(options.plugins_disabled))


def shallDetectMissingPlugins():
    return options is not None and options.detect_missing_plugins


def getPythonPathForScons():
    return options.python_scons
