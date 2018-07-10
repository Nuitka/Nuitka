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
from optparse import SUPPRESS_HELP, OptionGroup, OptionParser

from nuitka.PythonVersions import getSupportedPythonVersions
from nuitka.utils import Utils
from nuitka.Version import getNuitkaVersion

# Indicator if we were called as "nuitka-run" in which case we assume some
# other defaults and work a bit different with parameters.
is_nuitka_run = os.path.basename(sys.argv[0]).lower().endswith("-run")

if not is_nuitka_run:
    usage = "usage: %prog [--module] [--run] [options] main_module.py"
else:
    usage = "usage: %prog [options] main_module.py"

parser = OptionParser(
    usage   = usage,
    version = '\n'.join(
        (
            getNuitkaVersion(),
            sys.version,
            sys.executable
        )
    )
)

# This option is obsolete, and module should be used.
parser.add_option(
    "--exe",
    action  = "store_true",
    dest    = "obsolete_executable",
    default = False,
    help    = SUPPRESS_HELP
)

parser.add_option(
    "--module",
    action  = "store_false",
    dest    = "executable",
    default = True,
    help    = """\
Create an extension module executable instead of a program. Defaults to off."""
)

parser.add_option(
    "--standalone", "--portable",
    action  = "store_true",
    dest    = "is_standalone",
    default = False,
    help    = """\
Enable standalone mode in build. This allows you to transfer the created binary
to other machines without it relying on an existing Python installation. It
implies these option: "--recurse-all". You may also want to use
"--python-flag=no_site" to avoid the "site.py" module, which can save a lot
of code dependencies. Defaults to off.""",
)


parser.add_option(
    "--python-version",
    action  = "store",
    dest    = "python_version",
    choices = getSupportedPythonVersions(),
    default = None,
    help    = SUPPRESS_HELP
#               """\
# Major version of Python to be used, one of %s.
# Defaults to what you run Nuitka with (currently %s)""" % (
#        getSupportedPythonVersionStr(),
#        python_version_str
#     )
)

if os.name == "nt":
    parser.add_option(
        "--python-arch",
        action  = "store",
        dest    = "python_arch",
        choices = ("x86", "x86_64"),
        default = None,
        help    = """\
Architecture of Python to use. One of "x86" or "x86_64".
Defaults to what you run Nuitka with (currently "%s").""" % (
           Utils.getArchitecture()
        )
    )

parser.add_option(
    "--python-debug", "--python-dbg",
    action  = "store_true",
    dest    = "python_debug",
    default = None,
    help    = """\
Use debug version or not. Default uses what you are using to run Nuitka, most
likely a non-debug version."""
)

parser.add_option(
    "--python-flag",
    action  = "append",
    dest    = "python_flags",
    default = [],
    help    = """\
Python flags to use. Default uses what you are using to run Nuitka, this
enforces a specific mode. These are options that also exist to standard
Python executable. Currently supported: "-S" (alias "nosite"),
"static_hashes" (not use hash randomization), "no_warnings" (do not give
Python runtime warnings), "-O" (alias "noasserts"). Default empty."""
)

parser.add_option(
    "--python-for-scons", "--python2-for-scons",
    action  = "store",
    dest    = "python_scons",
    default = None,
    help    = """\
If using Python3.3 or Python3.4, provide the path of a Python binary to use
for Scons. Otherwise Nuitka can use what you run Nuitka with or a "scons"
binary that is found in PATH, or a Python installation from Windows registry."""
)

parser.add_option(
    "--warn-implicit-exceptions",
    action  = "store_true",
    dest    = "warn_implicit_exceptions",
    default = False,
    help    = """\
Enable warnings for implicit exceptions detected at compile time.""",
)

parser.add_option(
    "--warn-unusual-code",
    action  = "store_true",
    dest    = "warn_unusual_code",
    default = False,
    help    = """\
Enable warnings for unusual code detected at compile time.""",
)

parser.add_option(
    "--assume-yes-for-downloads",
    action  = "store_true",
    dest    = "assume_yes_for_downloads",
    default = False,
    help    = """\
Allow Nuitka to download code if necessary, e.g. dependency walker on Windows.""",
)


include_group = OptionGroup(
    parser,
    "Control the inclusion of modules and packages."
)

include_group.add_option(
    "--include-package",
    action  = "append",
    dest    = "include_packages",
    metavar = "PACKAGE",
    default = [],
    help    = """\
Include a whole package. Give as a Python namespace, e.g. ``some_package.sub_package``
and Nuitka will then find it and include it and all the modules found below that
disk location in the binary or extension module it creates, and make it available
for import by the code. Default empty."""
)

include_group.add_option(
    "--include-module",
    action  = "append",
    dest    = "include_modules",
    metavar = "MODULE",
    default = [],
    help    = """\
Include a single module. Give as a Python namespace, e.g. ``some_package.some_module``
and Nuitka will then find it and include it in the binary or extension module
it creates, and make it available for import by the code. Default empty."""
)


recurse_group = OptionGroup(
    parser,
    "Control the recursion into imported modules"
)


recurse_group.add_option(
    "--recurse-stdlib",
    action  = "store_true",
    dest    = "recurse_stdlib",
    default = False,
    help    = """\
Also descend into imported modules from standard library. This will increase
the compilation time by a lot. Defaults to off."""
)

recurse_group.add_option(
    "--recurse-none",
    action  = "store_true",
    dest    = "recurse_none",
    default = False,
    help    = """\
When --recurse-none is used, do not descend into any imported modules at all,
overrides all other recursion options. Defaults to off."""
)

recurse_group.add_option(
    "--recurse-all", "--recurse-on",
    action  = "store_true",
    dest    = "recurse_all",
    default = False,
    help    = """\
When --recurse-all is used, attempt to descend into all imported modules.
Defaults to off."""
)

recurse_group.add_option(
    "--recurse-to",
    action  = "append",
    dest    = "recurse_modules",
    metavar = "MODULE/PACKAGE",
    default = [],
    help    = """\
Recurse to that module, or if a package, to the whole package. Can be given
multiple times. Default empty."""
)

recurse_group.add_option(
    "--recurse-not-to",
    action  = "append",
    dest    = "recurse_not_modules",
    metavar = "MODULE/PACKAGE",
    default = [],
    help    = """\
Do not recurse to that module, or if a package, to the whole package in any
case, overrides all other options. Can be given multiple times. Default
empty."""
)

recurse_group.add_option(
    "--recurse-plugins", "--recurse-directory",
    action  = "append",
    dest    = "recurse_extra",
    metavar = "MODULE/PACKAGE",
    default = [],
    help    = """\
Recurse into that directory, no matter if it's used by the given main program
in a visible form. Overrides all other recursion options. Can be given multiple
times. Default empty."""
)

recurse_group.add_option(
    "--recurse-files", "--recurse-pattern",
    action  = "append",
    dest    = "recurse_extra_files",
    metavar = "PATTERN",
    default = [],
    help    = """\
Recurse into files matching the PATTERN. Overrides all recursion other options.
Can be given multiple times. Default empty."""
)


parser.add_option_group(recurse_group)

execute_group = OptionGroup(
    parser,
    "Immediate execution after compilation"
)

execute_group.add_option(
    "--run", "--execute",
    action  = "store_true",
    dest    = "immediate_execution",
    default = is_nuitka_run,
    help    = """\
Execute immediately the created binary (or import the compiled module).
Defaults to %s.""" %
       ("on" if is_nuitka_run else "off")
)

execute_group.add_option(
    "--debugger", "--gdb",
    action  = "store_true",
    dest    = "debugger",
    default = False,
    help    = """\
Execute inside "gdb" to automatically get a stack trace.
Defaults to off."""
)

execute_group.add_option(
    "--execute-with-pythonpath", "--keep-pythonpath",
    action  = "store_true",
    dest    = "keep_pythonpath",
    default = False,
    help    = """\
When immediately executing the created binary (--execute), don't reset
PYTHONPATH. When all modules are successfully included, you ought to not need
PYTHONPATH anymore."""
)

parser.add_option_group(execute_group)

dump_group = OptionGroup(
    parser,
    "Dump options for internal tree"
)

dump_group.add_option(
    "--dump-xml", "--xml",
    action  = "store_true",
    dest    = "dump_xml",
    default = False,
    help    = "Dump the final result of optimization as XML, then exit."
)

dump_group.add_option(
    "--display-tree",
    action  = "store_true",
    dest    = "display_tree",
    default = False,
    help    = """\
Display the final result of optimization in a GUI, then exit."""
)

parser.add_option_group(dump_group)


codegen_group = OptionGroup(
    parser,
    "Code generation choices"
)

codegen_group.add_option(
    "--improved", "--enhanced",
    action  = "store_true",
    dest    = "disabled",
    default = False,
    help    = SUPPRESS_HELP,
)

codegen_group.add_option(
    "--full-compat",
    action  = "store_false",
    dest    = "improved",
    default = True,
    help    = """\
Enforce absolute compatibility with CPython. Do not even allow minor
deviations from CPython behavior, e.g. better tracebacks, which are
not really incompatible, but different. This is intended for tests
only and should not be necessary for normal use.""",
)

codegen_group.add_option(
    "--code-gen-no-statement-lines",
    action  = "store_false",
    dest    = "statement_lines",
    default = True,
    help    = SUPPRESS_HELP,
#     help    = """\
# Statements shall have their line numbers set. Disable this for less precise
# exceptions and slightly faster code. Not recommended. Defaults to off."""
)

codegen_group.add_option(
    "--file-reference-choice",
    action  = "store",
    dest    = "file_reference_mode",
    choices = ("original", "runtime", "frozen"),
    default = None,
    help    = """\
Select what value "__file__" is going to be. With "runtime" (default for
standalone binary mode and module mode), the created binaries and modules,
use the location of themselves to deduct the value of "__file__". Included
packages pretend to be in directories below that location. This allows you
to include data files in deployments. If you merely seek acceleration, it's
better for you to use the "original" value, where the source files location
will be used. With "frozen" a notation "<frozen module_name>" is used. For
compatibility reasons, the "__file__" value will always have ".py" suffix
independent of what it really is."""
)

parser.add_option_group(codegen_group)

outputdir_group = OptionGroup(
    parser,
    "Output choices"
)

outputdir_group.add_option(
    "--output-dir",
    action  = "store",
    dest    = "output_dir",
    metavar = "DIRECTORY",
    default = "",
    help    = """\
Specify where intermediate and final output files should be put. The DIRECTORY
will be populated with C files, object files, etc.
Defaults to current directory.
"""
)

outputdir_group.add_option(
    "--remove-output",
    action  = "store_true",
    dest    = "remove_build",
    default = False,
    help    = """\
Removes the build directory after producing the module or exe file.
Defaults to off."""
)

outputdir_group.add_option(
    "--no-pyi-file",
    action  = "store_false",
    dest    = "pyi_file",
    default = True,
    help    = """\
Do not create a ".pyi" file for extension modules created by Nuitka.
Defaults to off."""
)



parser.add_option_group(outputdir_group)


windows_group = OptionGroup(
    parser,
    "Windows specific output control"
)


debug_group = OptionGroup(
    parser,
    "Debug features"
)

debug_group.add_option(
    "--debug",
    action  = "store_true",
    dest    = "debug",
    default = False,
    help    = """\
Executing all self checks possible to find errors in Nuitka, do not use for
production. Defaults to off."""
)

debug_group.add_option(
    "--unstripped", "--no-strip", "--unstriped",
    action  = "store_true",
    dest    = "unstripped",
    default = False,
    help    = """\
Keep debug info in the resulting object file for better debugger interaction.
Defaults to off."""
)

debug_group.add_option(
    "--profile",
    action  = "store_true",
    dest    = "profile",
    default = False,
    help    = """\
Enable vmprof based profiling of time spent. Defaults to off."""
)

debug_group.add_option(
    "--graph",
    action  = "store_true",
    dest    = "graph",
    default = False,
    help    = """\
Create graph of optimization process. Defaults to off."""
)

debug_group.add_option(
    "--trace-execution",
    action  = "store_true",
    dest    = "trace_execution",
    default = False,
    help    = """\
Traced execution output, output the line of code before executing it.
Defaults to off."""
)

debug_group.add_option(
    "--recompile-c-only",
    action  = "store_true",
    dest    = "recompile_c_only",
    default = False,
    help    = """\
Take existing files and compile them again. Allows compiling edited C files
with the C compiler for quick debugging changes to the generated source.
Defaults to off. Depends on compiling Python source to determine which files it
should look at."""
)

debug_group.add_option(
    "--generate-c-only",
    action  = "store_true",
    dest    = "generate_c_only",
    default = False,
    help    = """\
Generate only C source code, and do not compile it to binary or module. This
is for debugging and code coverage analysis that doesn't waste CPU. Defaults to
off."""
)

debug_group.add_option(
    "--experimental",
    action  = "append",
    dest    = "experimental",
    default = [],
    help    = """\
Use features declared as 'experimental'. May have no effect if no experimental
features are present in the code. Uses secret tags (check source) per
experimented feature."""
)

debug_group.add_option(
    "--explain-imports",
    action  = "store_true",
    dest    = "explain_imports",
    default = False,
    help    = SUPPRESS_HELP
)

if os.name == "nt":
    debug_group.add_option(
        "--disable-dll-dependency-cache",
        action  = "store_true",
        dest    = "no_dependency_cache",
        default = False,
        help    = """\
Disable the dependency walker cache. Will result in much longer times to create
the distribution folder, but might be used in case the cache is suspect to cause
errors.
"""
    )

    debug_group.add_option(
        "--force-dll-dependency-cache-update",
        action  = "store_true",
        dest    = "update_dependency_cache",
        default = False,
        help    = """\
For an update of the dependency walker cache. Will result in much longer times
to create the distribution folder, but might be used in case the cache is suspect
to cause errors or known to need an update.
"""
    )

# This is for testing framework, "coverage.py" hates to loose the process. And
# we can use it to make sure it's not done unknowingly.
parser.add_option(
    "--must-not-re-execute",
    action  = "store_false",
    dest    = "allow_reexecute",
    default = True,
    help    = SUPPRESS_HELP
)


parser.add_option_group(debug_group)

c_compiler_group = OptionGroup(
    parser,
    "Backend C compiler choice"
)


c_compiler_group.add_option(
    "--clang",
    action  = "store_true",
    dest    = "clang",
    default = False,
    help    = """\
Enforce the use of clang (needs clang 3.2 or higher).
Defaults to off."""
)

c_compiler_group.add_option(
    "--mingw",
    action  = "store_true",
    dest    = "mingw",
    default = False,
    help    = """\
Enforce the use of MinGW on Windows.
Defaults to off."""
)

c_compiler_group.add_option(
    "--msvc",
    action  = "store",
    dest    = "msvc",
    default = None,
    help    = """\
Enforce the use of specific MSVC version on Windows. Allowed values
are e.g. 9.0, 9.0exp, specify an illegal value for a list of installed
compilers. Defaults to the most recent version."""
)

c_compiler_group.add_option(
    "-j", "--jobs",
    action  = "store",
    dest    = "jobs",
    metavar = 'N',
    default = Utils.getCoreCount(),
    help    = """\
Specify the allowed number of parallel C compiler jobs. Defaults to the
system CPU count.""",
)

c_compiler_group.add_option(
    "--lto",
    action  = "store_true",
    dest    = "lto",
    default = False,
    help    = """\
Use link time optimizations if available and usable (g++ 4.6 and higher).
Defaults to off."""
)

parser.add_option_group(c_compiler_group)

tracing_group = OptionGroup(
    parser,
    "Tracing features"
)

tracing_group.add_option(
    "--show-scons",
    action  = "store_true",
    dest    = "show_scons",
    default = False,
    help    = """\
Operate Scons in non-quiet mode, showing the executed commands.
Defaults to off."""
)

tracing_group.add_option(
    "--show-progress",
    action  = "store_true",
    dest    = "show_progress",
    default = False,
    help    = """Provide progress information and statistics.
Defaults to off."""
)

tracing_group.add_option(
    "--show-memory",
    action  = "store_true",
    dest    = "show_memory",
    default = False,
    help    = """Provide memory information and statistics.
Defaults to off."""
)


tracing_group.add_option(
    "--show-modules",
    action  = "store_true",
    dest    = "show_inclusion",
    default = False,
    help    = """Provide a final summary on included modules.
Defaults to off."""
)

tracing_group.add_option(
    "--verbose",
    action  = "store_true",
    dest    = "verbose",
    default = False,
    help    = """\
Output details of actions taken, esp. in optimizations. Can become a lot.
Defaults to off."""
)

parser.add_option_group(tracing_group)

windows_group.add_option(
    "--windows-disable-console",
    action  = "store_true",
    dest    = "win_disable_console",
    default = False,
    help    = """\
When compiling for Windows, disable the console window. Defaults to off."""
)

windows_group.add_option(
    "--windows-icon", "--icon",
    action  = "store",
    dest    = "icon_path",
    metavar = "ICON_PATH",
    default = None,
    help    = "Add executable icon (Windows only).",
)

parser.add_option_group(windows_group)

plugin_group = OptionGroup(
    parser,
    "Plugin control"
)

plugin_group.add_option(
    "--plugin-enable", "--enable-plugin",
    action  = "append",
    dest    = "plugins_enabled",
    default = [],
    help    = """\
Enabled plugins. Must be plug-in names. Use --plugin-list to query the
full list and exit. Default empty."""
)

plugin_group.add_option(
    "--plugin-disable", "--disable-plugin",
    action  = "append",
    dest    = "plugins_disabled",
    default = [],
    help    = """\
Disabled plugins. Must be plug-in names. Use --plugin-list to query the
full list and exit. Default empty."""
)

plugin_group.add_option(
    "--plugin-no-detection",
    action  = "store_false",
    dest    = "detect_missing_plugins",
    default = True,
    help    = """\
Plugins can detect if they might be used, and the you can disable the warning
via --plugin-disable=plugin-that-warned, or you can use this option to disable
the mechanism entirely, which also speeds up compilation slightly of course as
this detection code is run in vain once you are certain of which plug-ins to
use. Defaults to off."""
)

plugin_group.add_option(
    "--plugin-list",
    action  = "store_true",
    dest    = "list_plugins",
    default = False,
    help    = """\
Show list of all available plugins and exit. Defaults to off."""
)


parser.add_option_group(plugin_group)


options = None
positional_args = None
extra_args = []

def parseArgs():
    # singleton with many cases, pylint: disable=global-statement,too-many-branches,too-many-statements
    global options, positional_args, extra_args

    # First, isolate the first non-option arguments.
    if is_nuitka_run:
        count = 0

        for count, arg in enumerate(sys.argv):
            if count == 0:
                continue

            if arg[0] != '-':
                break

            # Treat "--" as a terminator.
            if arg == "--":
                count += 1
                break

        if count > 0:
            extra_args = sys.argv[count+1:]
            sys.argv = sys.argv[0:count+1]

    options, positional_args = parser.parse_args()

    if shallListPlugins():
        from nuitka.plugins.Plugins import listPlugins
        listPlugins()

    if not positional_args:
        parser.print_help()

        sys.exit("""
    Error, need positional argument with python module or main program.""")

    if not options.immediate_execution and len(positional_args) > 1:
        parser.print_help()

        sys.exit("""
    Error, need only one positional argument unless "--run" is specified to
    pass them to the compiled program execution.""")

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
Error, '--recurse-to' takes only module names, not directory path '%s'.""" % \
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
Error, '--recurse-not-to' takes only module names, not directory path '%s'.""" % \
                no_case_module
            )

    scons_python = getPythonPathForScons()

    if scons_python is not None and not os.path.exists(scons_python):
        sys.exit("Error, no such Python2 binary '%s'." % scons_python)


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


def shallDisplayBuiltTree():
    return options.display_tree


def shallOnlyExecCCompilerCall():
    return options.recompile_c_only


def shallNotDoExecCCompilerCall():
    return options.generate_c_only


def shallHaveStatementLines():
    return options.statement_lines


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


def isMingw():
    return options.mingw


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


def getIntendedPythonVersion():
    return options.python_version


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
