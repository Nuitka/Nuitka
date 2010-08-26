#!/usr/bin/env python
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

# This main program translates one module to a C++ source code using Python
# C/API and optionally compiles it to either an executable or an extension
# module.

import TreeTransforming
import CodeGeneration
import TreeBuilding
import TreeDisplay
import Generator
import Contexts
import Options

import sys, os

from logging import warning

# Turn that source code into a node tree structure. If recursion into imported
# modules is available, more trees will be available too.
tree = TreeBuilding.buildModuleTree( Options.getPositionalArgs()[0] )

if not Options.shallOnlyExecGcc():
    if Options.shallDumpBuiltTree():
        print "Analysis -> Tree Result"
        print "*" * 80
        print "*" * 80
        print "*" * 80
        tree.dump()
        print "*" * 80
        print "*" * 80
        print "*" * 80


    if Options.shallDisplayBuiltTree():
        # The python-dbg doesn't work with this module due to PyQt, so import it late and only where needed.
        TreeDisplay.displayTreeInspector( tree )

    # Optimizations go here

    # Now build the target language code
    if Options.shallMakeModule():
        generator_module = Generator.PythonModuleGenerator(
            module_name = tree.getName(),
        )

        source_code = CodeGeneration.generateModuleCode(
            module         = tree,
            generator      = generator_module,
            global_context = Contexts.PythonGlobalContext(),
            stand_alone    = True
        )
    else:
        generator_module = Generator.PythonModuleGenerator(
            module_name = "__main__",
        )

        other_modules = TreeBuilding.getOtherModules()

        if tree in other_modules:
            other_modules.remove( tree )

        source_code = CodeGeneration.generateExecutableCode(
            main_module   = tree,
            other_modules = other_modules,
            generator     = generator_module
        )

    # Write the generated source code to the file.
    cpp_filename = Options.getOutputPath( tree.getName() + ".c++" )
    open( cpp_filename, "wb" ).write( source_code )

# Inspect the running Python version for target information.

def getPythonVersionPaths():
    if Options.options.python_version is None:
        major_version = "%d.%d" % ( sys.version_info[0], sys.version_info[1] )
    else:
        major_version = Options.options.python_version

    if Options.options.python_debug is None:
        use_debug = hasattr( sys, "getobjects" )
    else:
        use_debug = Options.options.python_debug

    debug_indicator = "_d" if use_debug else ""

    return major_version, debug_indicator

python_target_major_version, python_target_debug_indicator = getPythonVersionPaths()

python_header_path = "/usr/include/python" + python_target_major_version + python_target_debug_indicator

if not os.path.exists( python_header_path + "/Python.h" ):
    warning( "The Python headers seem to be not installed. Expect C++ compiler failures." )

gcc_options = ["-std=c++0x", "-I" + python_header_path ]

if Options.isDebug():
    gcc_options += [
        # "-save-temps",
        "-g",
        "-O2"
    ]

if Options.isOptimize():
    gcc_options += [
        " -D__PYDRA_NO_ASSERT__",
        "-O3"
    ]

# Compile the generated source immediately.
if Options.shallMakeModule():
    gcc_options += ["-shared", "-fPIC" ]

    target_path = tree.getName() + ".so"
else:
    target_path = tree.getName() + ".exe"

output_filename = Options.getOutputPath( target_path )

gcc_options += [ "-lpython" + python_target_major_version + python_target_debug_indicator, cpp_filename, "-o " + output_filename ]

result = os.system( "g++ " + " ".join( gcc_options ))

# Exit if compilation failed.
if result != 0:
    sys.exit( 1 )

# Execute the module immediately if option was given.
if Options.shallExecuteImmediately():
    if Options.shallMakeModule():
        __import__( tree.getName() )
    else:
        os.execl( output_filename, tree.getName() + ".exe" )
