#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit patches or make the software available to licensors of
#     this software in either form, you automatically them grant them a
#     license for your part of the code under "Apache License 2.0" unless you
#     choose to remove this notice.
#
#     Kay Hayen uses the right to license his code under only GPL version 3,
#     to discourage a fork of Nuitka before it is "finished". He will later
#     make a new "Nuitka" release fully under "Apache License 2.0".
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Options module """

version_string = """\
Nuitka V0.3.18.4
Copyright (C) 2012 Kay Hayen."""

from . import Utils

from optparse import OptionParser, OptionGroup

import sys, os, logging

# Indicator if we were called as "nuitka-python" in which case we assume some other
# defaults and work a bit different with parameters.
is_nuitka_python = os.path.basename( sys.argv[0] ).lower() == "nuitka-python"

def getVersion():
    return version_string.split()[1][1:]

if is_nuitka_python:
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
    "--execute-with-pythonpath",
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
    default = None,
    help    = "Major version of Python to be used, something like 2.6 or 2.7."
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
    "--unstriped",
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
    "--g++-only",
    action  = "store_true",
    dest    = "cpp_only",
    default = False,
    help    = """\
Compile the would-be generated source file. Allows edition and translation with same
options for quick debugging changes to the generated source. Defaults to off."""
)

debug_group.add_option(
    "--experimental",
    action  = "store_true",
    dest    = "experimental",
    default = False,
    help    = """\
Use features declared as "experimental". May have no effect if no experimental features
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
    # TODO: Enable by default for interactive mode.
    default = False and sys.stdout.isatty(),
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

if options.recurse_all and not options.executable:
    sys.exit( "Error, options '--recurse-all' makes no sense without option '--exe'." )

if options.recurse_stdlib and not options.executable:
    sys.exit( "Error, options '--recurse-stdlib' makes no sense without option '--exe'." )

def useValuePropagation():
    return options.experimental

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

def isDebug():
    return options.debug

def isOptimize():
    return not options.no_optimize

def isUnstriped():
    return options.unstriped

def getOutputPath( path ):
    if options.output_dir:
        return os.path.normpath( options.output_dir + "/" + path )
    else:
        return path

def getPositionalArgs():
    return positional_args

def getMainArgs():
    return extra_args

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

def isWindowsTarget():
    return options.windows_target

def isFullCompat():
    return True

def isShowProgress():
    return options.show_progress

def isRemoveBuildDir():
    return options.remove_build
