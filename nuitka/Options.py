#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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
Nuitka V0.4.3pre5
Copyright (C) 2013 Kay Hayen."""

from . import Utils

from optparse import OptionParser, OptionGroup

import sys, logging

# Indicator if we were called as "nuitka-python" in which case we assume some other
# defaults and work a bit different with parameters.
is_nuitka_python = Utils.basename( sys.argv[0] ).lower().startswith( "nuitka-python" )

def getVersion():
    return version_string.split()[1][1:]

if not is_nuitka_python:
    usage = "usage: %prog [--exe] [--execute] [options] main_module.py"
else:
    usage = "usage: %prog [options] main_module.py"

parser = OptionParser(
    usage   = usage,
    version = getVersion()
)

parser.add_option(
    "--exe",
    action  = "store_true",
    dest    = "executable",
    default = is_nuitka_python,
    help    = """\
Create a standalone executable instead of a compiled extension module. Default is %s.""" %
       ( "on" if is_nuitka_python else "off" )
)

recurse_group = OptionGroup(
    parser,
    "Control the recursion into imported modules with '--exe' mode"
)


recurse_group.add_option(
    "--recurse-stdlib",
    action  = "store_true",
    dest    = "recurse_stdlib",
    default = False,
    help    = "Also descend into imported modules from standard library."
)

recurse_group.add_option(
    "--recurse-none",
    action  = "store_true",
    dest    = "recurse_none",
    default = False,
    help    = """\
When --recurse-none is used, do not descend into any imported modules at all, overrides
all other recursion options. Default %default."""
)

recurse_group.add_option(
    "--recurse-all", "--recurse-on",
    action  = "store_true",
    dest    = "recurse_all",
    default = False,
    help    = """\
When --recurse-all is used, attempt to descend into all imported modules.
Default %default."""
)

recurse_group.add_option(
    "--recurse-to",
    action  = "append",
    dest    = "recurse_modules",
    metavar = "MODULE/PACKAGE",
    default = [],
    help    = """\
Recurse to that module, or if a package, to the whole package. Can be given multiple
times. Default empty."""
)

recurse_group.add_option(
    "--recurse-not-to",
    action  = "append",
    dest    = "recurse_not_modules",
    metavar = "MODULE/PACKAGE",
    default = [],
    help    = """\
Do not recurse to that module, or if a package, to the whole package in any case,
overrides all other options. Can be given multiple times. Default empty."""
)

recurse_group.add_option(
    "--recurse-plugins", "--recurse-directory",
    action  = "append",
    dest    = "recurse_extra",
    metavar = "MODULE/PACKAGE",
    default = [],
    help    = """\
Recurse into that directory, no matter if it's used by the given main program in a
visible form. Overrides all other options. Can be given multiple times. Default empty."""
)

parser.add_option_group( recurse_group )

execute_group = OptionGroup(
    parser,
    "Immediate execution after compilation"
)

execute_group.add_option(
    "--execute",
    action  = "store_true",
    dest    = "immediate_execution",
    default = is_nuitka_python,
    help    = """\
Execute immediately the created binary (or import the compiled module). Default
is %s.""" %
       ( "on" if is_nuitka_python else "off" )
)

execute_group.add_option(
    "--execute-with-pythonpath", "--keep-pythonpath",
    action  = "store_true",
    dest    = "keep_pythonpath",
    default = False,
    help    = """\
When immediately executing the created binary (--execute), don't reset PYTHONPATH. When
all modules are successfully included, you ought to not need PYTHONPATH anymore."""
)

parser.add_option_group( execute_group )

dump_group = OptionGroup(
    parser,
    "Dump options for internal tree"
)

dump_group.add_option(
    "--dump-xml",
    action  = "store_true",
    dest    = "dump_xml",
    default = False,
    help    = """Dump the final result of optimization as XML, then exit."""
)

dump_group.add_option(
    "--dump-tree",
    action  = "store_true",
    dest    = "dump_tree",
    default = False,
    help    = """Dump the final result of optimization as text, then exit."""
)

dump_group.add_option(
    "--display-tree",
    action  = "store_true",
    dest    = "display_tree",
    default = False,
    help    = """Display the final result of optimization in a GUI, then exit."""
)

parser.add_option_group( dump_group )

parser.add_option(
    "--python-version",
    action  = "store",
    dest    = "python_version",
    choices = ( "2.6", "2.7", "3.2", "3.3" ),
    default = None,
    help    = """Major version of Python to be used, one of '2.6', '2.7', or '3.2'."""
)

parser.add_option(
    "--python-debug",
    action  = "store_true",
    dest    = "python_debug",
    default = None,
    help    = """\
Use debug version or not. Default uses what you are using to run Nuitka, most
likely a non-debug version."""
)

codegen_group = OptionGroup(
    parser,
    "Code generation choices"
)

codegen_group.add_option(
    "--code-gen-no-statement-lines",
    action  ="store_false",
    dest    = "statement_lines",
    default = True,
    help    = """\
Statements shall have their line numbers set. Disable this for less precise exceptions and
slightly faster code. Not recommended. Defaults to off."""
)

codegen_group.add_option(
    "--no-optimization",
    action  = "store_true",
    dest    = "no_optimize",
    default = False,
    help    = """Disable all unnecessary optimizations on Python level. Defaults to off."""
)

parser.add_option_group( codegen_group )

outputdir_group = OptionGroup(
    parser,
    "Output directory choices"
)

outputdir_group.add_option(
    "--output-dir",
    action  ="store",
    dest    = "output_dir",
    metavar = "DIRECTORY",
    default = "",
    help    = """\
Specify where intermediate and final output files should be put. DIRECTORY will
be populated with C++ files, object files, etc. Defaults to current directory."""
)

outputdir_group.add_option(
    "--remove-output",
    action  = "store_true",
    dest    = "remove_build",
    default = False,
    help    = """\
Removes the build directory after producing the module or exe file.
Default %default."""
)

parser.add_option_group( outputdir_group )

parser.add_option(
    "--windows-target",
    action  = "store_true",
    dest    = "windows_target",
    default = False,
    help    = """\
Force compilation for windows, useful for cross-compilation. Defaults to off."""
)

parser.add_option(
    "--windows-disable-console",
    action  = "store_true",
    dest    = "win_disable_console",
    default = False,
    help    = """\
When compiling for windows, disable the console window. Defaults to off."""
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
    dest    = "unstriped",
    default = False,
    help    = """\
Keep debug info in the resulting object file for better gdb interaction.
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
    "--c++-only",
    action  = "store_true",
    dest    = "cpp_only",
    default = False,
    help    = """\
Compile the would-be regenerated source file. Allows compiling edited C++ files with the
C++ compiler for quick debugging changes to the generated source. Defaults to off."""
)

debug_group.add_option(
    "--experimental",
    action  = "store_true",
    dest    = "experimental",
    default = False,
    help    = """\
Use features declared as 'experimental'. May have no effect if no experimental features
are present in the code. Defaults to off."""
)

parser.add_option_group( debug_group )

parser.add_option(
    "--lto",
    action  = "store_true",
    dest    = "lto",
    default = False,
    help    = """\
Use link time optimizations if available and usable (g++ 4.6 and higher).
Defaults to off."""
)

parser.add_option(
    "--clang",
    action  = "store_true",
    dest    = "clang",
    default = False,
    help    = """\
Enforce the use of clang (clang 3.0 or higher).
Defaults to off."""
)

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
Operate Scons in non-quiet mode, showing the executed commands. Defaults to off."""
)

tracing_group.add_option(
    "--show-progress",
    action  = "store_true",
    dest    = "show_progress",
    default = False,
    help    = """Provide progress information and statistics. Defaults to off."""
)

tracing_group.add_option(
    "--verbose",
    action  = "store_true",
    dest    = "verbose",
    default = False,
    help    = """\
Output details of actions take, esp. in optimizations. Can become a lot."""
)


parser.add_option_group( tracing_group )

parser.add_option(
    "-j", "--jobs",
    action  ="store",
    dest    = "jobs",
    metavar = "N",
    default = Utils.getCoreCount(),
    help    = """\
Specify the allowed number of parallel C++ compiler jobs. Defaults to the system
CPU count.""",
)

parser.add_option(
    "--improved",
    action  = "store_true",
    dest    = "improved",
    default = False,
    help    = """\
Allow minor devitations from CPython behaviour, e.g. better tracebacks, which are not
really incompatible, but different.""",
)

parser.add_option(
    "--warn-implicit-exceptions",
    action  = "store_true",
    dest    = "warn_implicit_exceptions",
    default = False,
    help    = """\
Given warnings for implicit exceptions detected at compile time.""",
)

parser.add_option(
    "--portable",
    action  = "store_true",
    dest    = "is_portable_mode",
    default = False,
    help    = """\
Enable portable mode in build.""",
)

if is_nuitka_python:
    count = 0

    for count, arg in enumerate( sys.argv ):
        if count == 0:
            continue

        if arg[0] != "-":
            break

    if count > 0:
        extra_args = sys.argv[count+1:]
        sys.argv = sys.argv[0:count+1]
else:
    extra_args = []

options, positional_args = parser.parse_args()

if not positional_args:
    parser.print_help()

    sys.exit( "\nError, need positional argument with python module or main program." )

if options.verbose:
    logging.getLogger().setLevel( logging.DEBUG )

def shallTraceExecution():
    return options.trace_execution

def shallExecuteImmediately():
    return options.immediate_execution

def shallDumpBuiltTree():
    return options.dump_tree

def shallDumpBuiltTreeXML():
    return options.dump_xml

def shallDisplayBuiltTree():
    return options.display_tree

def shallOnlyExecGcc():
    return options.cpp_only

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
    return sum( [ x.split( "," ) for x in options.recurse_modules ], [] )

def getShallFollowInNoCase():
    return sum( [ x.split( "," ) for x in options.recurse_not_modules ], [] )

def getShallFollowExtra():
    return sum( [ x.split( "," ) for x in options.recurse_extra ], [] )

def shallWarnImplicitRaises():
    return options.warn_implicit_exceptions

def isDebug():
    return options.debug

def isOptimize():
    return not options.no_optimize

def isUnstriped():
    return options.unstriped

def getOutputPath( path ):
    if options.output_dir:
        return Utils.normpath( Utils.joinpath( options.output_dir, path ) )
    else:
        return path

def getOutputDir():
    return options.output_dir if options.output_dir else "."

def getPositionalArgs():
    return tuple( positional_args )

def getMainArgs():
    return tuple( extra_args )

def shallOptimizeStringExec():
    return False

def shallClearPythonPathEnvironment():
    return not options.keep_pythonpath

def isShowScons():
    return options.show_scons

def getJobLimit():
    return int( options.jobs )

def isLto():
    return options.lto

def isClang():
    return options.clang

def isWindowsTarget():
    return options.windows_target

def shallDisableConsoleWindow():
    return options.win_disable_console

def isFullCompat():
    return not options.improved

def isShowProgress():
    return options.show_progress

def isRemoveBuildDir():
    return options.remove_build

def getIntendedPythonVersion():
    return options.python_version

def isExperimental():
    return hasattr( options, "experimental" ) and options.experimental

def isPortableMode():
    return options.is_portable_mode
