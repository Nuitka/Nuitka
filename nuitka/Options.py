#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
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
Nuitka V0.3.12pre2
Copyright (C) 2011 Kay Hayen."""

from . import Utils, Tracing

from optparse import OptionParser

import sys, os, logging

# Indicator if we were called as "Python" in which case we assume some other
# defaults and work a bit different with parameters.
is_Python = os.path.basename( sys.argv[0] ) == "Python"

parser = OptionParser()

parser.add_option(
    "--exe",
    action  = "store_true",
    dest    = "executable",
    default = is_Python,
    help    = "Create a standalone executable instead of a compiled extension module."
)
parser.add_option(
    "--deep",
    action  = "store_true",
    dest    = "follow_imports",
    default = False,
    help    = "Descend into imported modules and compile them recursively."
)

parser.add_option(
    "--execute",
    action  = "store_true",
    dest    = "immediate_execution",
    default = is_Python,
    help    = "Execute immediately the created binary. (or import the compiled module)"
)

parser.add_option(
    "--trace-execution",
    action  = "store_true",
    dest    = "trace_execution",
    default = False,
    help    = "Debugging: Traced execution output."
)
parser.add_option(
    "--dump-tree",
    action  = "store_true",
    dest    = "dump_tree",
    default = False,
    help    = "Debugging: Dump the final result of analysis."
)

parser.add_option(
    "--dump-xml",
    action  = "store_true",
    dest    = "dump_xml",
    default = False,
    help    = "Debugging: Dump the final result of analysis."
)


parser.add_option(
    "--g++-only",
    action  = "store_true",
    dest    = "cpp_only",
    default = False,
    help    = """\
Debugging: Only compile the would-be generated source file.
Allows edition and translation with same options for quick
debugging changes to the generated source."""
)
parser.add_option(
    "--display-tree",
    action  = "store_true",
    dest    = "display_tree",
    default = False,
    help    = "Debugging: Display the final result of analysis."
)

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

parser.add_option(
    "--code-gen-no-statement-lines",
    action  ="store_false",
    dest    = "statement_lines",
    default = True,
    help    = """\
Statements shall have their line numbers set. Disable this for
less precise exceptions and slightly faster code. Not recommended."""
)

parser.add_option(
    "--no-optimization",
    action  = "store_true",
    dest    = "no_optimize",
    default = False,
    help    = "Disable all optimizations."
)

parser.add_option(
    "--output-dir",
    action  ="store",
    dest    = "output_dir",
    default = "",
    help    = "Where intermediate and final output files should be put."
)

parser.add_option(
    "--windows-target",
    action  = "store_true",
    dest    = "windows_target",
    default = False,
    help    = "Force compilation for windows, useful for cross-compilation."
)

parser.add_option(
    "--version",
    action  = "store_true",
    dest    = "version",
    default = False,
    help    = "Only output version, then exit."
)

parser.add_option(
    "--debug",
    action  = "store_true",
    dest    = "debug",
    default = False,
    help    = """\
Executing all self checks possible to find errors in Nuitka, do not use for production."""
)

parser.add_option(
    "--unstriped",
    action  = "store_true",
    dest    = "unstriped",
    default = False,
    help    = """\
Keep debug info in the resulting object file for better gdb interaction."""
)

parser.add_option(
    "--lto",
    action  = "store_true",
    dest    = "lto",
    default = False,
    help    = "Use link time optimizations if available and usable (g++ 4.6 and higher)."
)

parser.add_option(
    "--verbose",
    action  = "store_true",
    dest    = "verbose",
    default = False,
    help    = "Output details of actions take, esp. in optimizations."
)

parser.add_option(
    "--show-scons",
    action  = "store_true",
    dest    = "show_scons",
    default = False,
    help    = "Operate scons in non-quiet mode, showing the executed commands."
)


core_count = Utils.getCoreCount()

parser.add_option(
    "-j", "--jobs", action="store", dest = "jobs", default = core_count,
    help = """\
Specify the allowed number of jobs. Defaults to system CPU count (%d).""" % core_count,
)


if is_Python:
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

if options.version:
    Tracing.printError( version_string )
    sys.exit(0)

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

def shallFollowImports():
    return options.follow_imports

def shallFollowStandardLibrary():
    return False

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

def getVersion():
    return version_string.split()[1][1:]
