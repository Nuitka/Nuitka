#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

version_string = """\
Nuitka V0.5.10.2
Copyright (C) 2015 Kay Hayen."""

import logging
import re
import sys
from optparse import SUPPRESS_HELP, OptionGroup, OptionParser

from . import Utils

# Indicator if we were called as "nuitka-run" in which case we assume some
# other defaults and work a bit different with parameters.
is_nuitka_run = Utils.basename(sys.argv[0]).lower().startswith("nuitka-run")

def getVersion():
    return version_string.split()[1][1:]

def getYear():
    return int(version_string.split()[4])

if not is_nuitka_run:
    usage = "usage: %prog [--module] [--execute] [options] main_module.py"
else:
    usage = "usage: %prog [options] main_module.py"

parser = OptionParser(
    usage   = usage,
    version = getVersion()
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
implies these options: "--recurse-all --recurse-stdlib". Defaults to off.""",
)

parser.add_option(
    "--nofreeze-stdlib",
    action  = "store_false",
    dest    = "freeze_stdlib",
    default = True,
    help    = """\
In standalone mode by default all modules of standard library will be frozen
as bytecode. As a result compilation time will increase very much.
""",
    )


def getSupportedPythonVersions():
    return ("2.6", "2.7", "3.2", "3.3", "3.4")

def getSupportedPythonVersionStr():
    supported_python_versions = getSupportedPythonVersions()

    supported_python_versions_str = repr(supported_python_versions)[1:-1]
    supported_python_versions_str = re.sub(
        r"(.*),(.*)$",
        r"\1, or\2",
        supported_python_versions_str
    )

    return supported_python_versions_str

parser.add_option(
    "--python-version",
    action  = "store",
    dest    = "python_version",
    choices = getSupportedPythonVersions(),
    default = None,
    help    = """\
Major version of Python to be used, one of %s.
Defaults to what you run Nuitka with.""" % (
       getSupportedPythonVersionStr()
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
Python executable. Currently supported: "-S" (alias nosite),
"static_hashes" (not use Randomization), "no_warnings" (do not give
Python runtime warnings). Default empty."""
)


parser.add_option(
    "--warn-implicit-exceptions",
    action  = "store_true",
    dest    = "warn_implicit_exceptions",
    default = False,
    help    = """\
Given warnings for implicit exceptions detected at compile time.""",
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
Also descend into imported modules from standard library. Defaults to off."""
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
    dest    = "improved",
    default = False,
    help    = """\
Allow minor deviations from CPython behavior, e.g. better tracebacks, which
are not really incompatible, but different.""",
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
    "--no-optimization",
    action  = "store_true",
    dest    = "no_optimize",
    default = False,
    help    = SUPPRESS_HELP
# """Disable all unnecessary optimizations on Python level. Defaults to off."""
)

parser.add_option_group(codegen_group)

outputdir_group = OptionGroup(
    parser,
    "Output directory choices"
)

outputdir_group.add_option(
    "--output-dir",
    action  = "store",
    dest    = "output_dir",
    metavar = "DIRECTORY",
    default = "",
    help    = """\
Specify where intermediate and final output files should be put. DIRECTORY will
be populated with C++ files, object files, etc. Defaults to current directory.
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

parser.add_option_group(outputdir_group)


windows_group = OptionGroup(
    parser,
    "Windows specific output control:"
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
    "--trace-execution",
    action  = "store_true",
    dest    = "trace_execution",
    default = False,
    help    = """\
Traced execution output, output the line of code before executing it.
Defaults to off."""
)

debug_group.add_option(
    "--recompile-c++-only",
    action  = "store_true",
    dest    = "recompile_cpp_only",
    default = False,
    help    = """\
Take existing files and compile them again.Allows compiling edited C++ files
with the C++ compiler for quick debugging changes to the generated source.
Defaults to off. Depends on compiling Python source to determine which files it
should look at."""
)

debug_group.add_option(
    "--generate-c++-only",
    action  = "store_true",
    dest    = "generate_cpp_only",
    default = False,
    help    = """\
Generate only C++ source code, and do not compile it to binary or module. This
is for debugging and code coverage analysis that doesn't waste CPU. Defaults to
off."""
)


debug_group.add_option(
    "--experimental",
    action  = "store_true",
    dest    = "experimental",
    default = False,
    help    = """\
Use features declared as 'experimental'. May have no effect if no experimental
features are present in the code. Defaults to off."""
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

cpp_compiler_group = OptionGroup(
    parser,
    "Backend C++ compiler choice"
)


cpp_compiler_group.add_option(
    "--clang",
    action  = "store_true",
    dest    = "clang",
    default = False,
    help    = """\
Enforce the use of clang (needs clang 3.2 or higher).
Defaults to off."""
)

cpp_compiler_group.add_option(
    "--mingw",
    action  = "store_true",
    dest    = "mingw",
    default = False,
    help    = """\
Enforce the use of MinGW on Windows.
Defaults to off."""
)

cpp_compiler_group.add_option(
    "--msvc",
    action  = "store",
    dest    = "msvc",
    default = None,
    help    = """\
Enforce the use of specific MSVC version on Windows. Allowed values
are e.g. 9.0, 9.0exp, specify an illegal value for a list of installed
compilers. Defaults to the most recent version."""
)

cpp_compiler_group.add_option(
    "-j", "--jobs",
    action  = "store",
    dest    = "jobs",
    metavar = 'N',
    default = Utils.getCoreCount(),
    help    = """\
Specify the allowed number of parallel C++ compiler jobs. Defaults to the
system CPU count.""",
)

cpp_compiler_group.add_option(
    "--lto",
    action  = "store_true",
    dest    = "lto",
    default = False,
    help    = """\
Use link time optimizations if available and usable (g++ 4.6 and higher).
Defaults to off."""
)

parser.add_option_group(cpp_compiler_group)

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
else:
    extra_args = []

options, positional_args = parser.parse_args()

if not positional_args:
    parser.print_help()

    sys.exit("""
Error, need positional argument with python module or main program.""")

if options.verbose:
    logging.getLogger().setLevel(logging.DEBUG)
else:
    logging.getLogger().setLevel(logging.INFO)

# Standalone mode implies an executable, not importing "site" module, which is
# only for this machine, recursing to all modules, and even including the
# standard library.
if options.is_standalone:
    options.executable = True
    options.recurse_all = True
    options.recurse_stdlib = True

def shallTraceExecution():
    return options.trace_execution

def shallExecuteImmediately():
    return options.immediate_execution

def shallDumpBuiltTreeXML():
    return options.dump_xml

def shallDisplayBuiltTree():
    return options.display_tree

def shallOnlyExecCppCall():
    return options.recompile_cpp_only

def shallNotDoExecCppCall():
    return options.generate_cpp_only

def shallHaveStatementLines():
    return options.statement_lines

def shallMakeModule():
    return not options.executable

def shallFollowStandardLibrary():
    return options.recurse_stdlib

def shallFollowNoImports():
    return options.recurse_none

def shallFollowAllImports():
    return options.recurse_all

def getShallFollowModules():
    return sum([ x.split(',') for x in options.recurse_modules ], [])

def isAllowedToReexecute():
    return options.allow_reexecute

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
        sys.exit("""
Error, '--recurse-to' takes only module names, not directory path '%s'.""" % \
any_case_module)

def getShallFollowInNoCase():
    return sum([ x.split(',') for x in options.recurse_not_modules ], [])

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
        sys.exit("""
Error, '--recurse-not-to' takes only module names, not directory path '%s'.""" % \
no_case_module)


def getShallFollowExtra():
    return sum([ x.split(',') for x in options.recurse_extra ], [])

def getShallFollowExtraFilePatterns():
    return sum([ x.split(',') for x in options.recurse_extra_files ], [])

def shallWarnImplicitRaises():
    return options.warn_implicit_exceptions

def isDebug():
    return options.debug

def isPythonDebug():
    return options.python_debug or sys.flags.debug

def isOptimize():
    return not options.no_optimize

def isUnstripped():
    return options.unstripped

def getOutputPath(path):
    if options.output_dir:
        return Utils.normpath(Utils.joinpath(options.output_dir, path))
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

def isShowInclusion():
    return options.show_inclusion

def isRemoveBuildDir():
    return options.remove_build and not options.generate_cpp_only

def getIntendedPythonVersion():
    return options.python_version

def isExperimental():
    return hasattr(options, "experimental") and options.experimental

def isStandaloneMode():
    return options.is_standalone

def getIconPath():
    return options.icon_path

def getPythonFlags():
    result = []

    for part in options.python_flags:
        if part in ("-S", "nosite", "no_site"):
            result.append("no_site")
        elif part in ("static_hashes", "norandomization", "no_randomization"):
            result.append("no_randomization")
        elif part in ("-v", "trace_imports", "trace_import"):
            result.append("trace_imports")
        elif part in ("no_warnings", "nowarnings"):
            result.append("no_warnings")
        else:
            logging.warning("Unsupported flag '%s'.", part)

    return result

def freezeAllStdlib():
    return options.freeze_stdlib
