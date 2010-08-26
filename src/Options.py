# 
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
# 
#     Part of "Nuitka", my attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
# 
#     If you submit patches to this software in either form, you automatically
#     grant me a copyright assignment to the code, or in the alternative a BSD
#     license to the code, should your jurisdiction prevent this. This is to
#     reserve my ability to re-license the code at any time.
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
""" Options module """

from optparse import OptionParser

parser = OptionParser()

parser.add_option(
    "--exe", action="store_true", dest = "executable", default = False, help = "Create a standalone executable instead of a compiled extension module.",
)
parser.add_option(
    "--deep", action="store_true", dest = "follow_imports", default = False, help = "Descend into imported modules and compile them recursively.",
)

parser.add_option(
    "--execute", action="store_true", dest = "immediate_execution", default = False, help = "Immediate execute the created binary or import the freshly compiled module.",
)

parser.add_option(
    "--trace-execution", action="store_true", dest = "trace_execution", default = False, help = "Debug aid: Traced execution output.",
)
parser.add_option(
    "--dump-tree", action="store_true", dest = "dump_tree", default = False, help = "Debug aid: Dump the final result of analysis.",
)
parser.add_option(
    "--g++-only", action="store_true", dest = "cpp_only", default = False, help = "Debug aid: Compile the would be generated source file only. To allow editing and translation with same options for quick debugging changes to the generated source."
)
parser.add_option(
    "--display-tree", action="store_true", dest = "display_tree", default = False, help = "Debug aid: Display the final result of analysis.",
)


parser.add_option(
    "--python-version", action="store", dest = "python_version", default = None, help = "Major version of Python to be used, something like 2.5 or 2.6",
)

parser.add_option(
    "--python-debug", action="store_true", dest = "python_debug", default = None, help = "Use the debug version or not. Default is use what you are using with Nuitka, likely no debug.",
)

parser.add_option(
    "--code-gen-statement-lines", action="store_true", dest = "statement_lines", default = True, help = "Statements shall have their line numbers set. Disable this for less precise exceptions and slightly faster code. Not recommended.",
)

parser.add_option(
    "--output-dir", action="store", dest = "output_dir", default = "", help = "Where to put intermediate and final output files.",
)


options, positional_args = parser.parse_args()

def shallTraceExecution():
    return options.trace_execution

def shallExecuteImmediately():
    return options.immediate_execution

def shallDumpBuiltTree():
    return options.dump_tree

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

def isDebug():
    return True

def isOptimize():
    return False

def getOutputPath( path ):
    if options.output_dir:
        return options.output_dir + "/" + path
    else:
        return path

def includeStandardLibrary():
    return False

def getPositionalArgs():
    return positional_args
