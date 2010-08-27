#!/usr/bin/env python
#
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
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
#
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
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

"""

This main program translates one module to a C++ source code using Python
C/API and optionally compiles it to either an executable or an extension
module.

"""

import MainControl
import Options

import sys

# Turn that source code into a node tree structure.
tree = MainControl.createNodeTree(
    filename = Options.getPositionalArgs()[0]
)

cpp_filename = Options.getOutputPath(
    tree.getName() + ".c++"
)

if not Options.shallOnlyExecGcc():
    if Options.shallDumpBuiltTree():
        MainControl.dumpTree( tree )

    if Options.shallDisplayBuiltTree():
        MainControl.displayTree( tree )

    # Now build the target language code
    if Options.shallMakeModule():
        source_code = MainControl.makeModuleSource( tree )
    else:
        source_code = MainControl.makeMainSource( tree )

    # Write it to disk. May consider using -pipe some day
    MainControl.writeSourceCode(
        cpp_filename = cpp_filename,
        source_code  = source_code
    )

# Inspect the running Python version for target information.
python_target_major_version, python_target_debug_indicator, python_header_path = MainControl.getPythonVersionPaths()

# Build the output filename and the g++ options
gcc_options, output_filename = MainControl.getGccOptions(
    tree                          = tree,
    cpp_filename                  = cpp_filename,
    python_target_major_version   = python_target_major_version,
    python_target_debug_indicator = python_target_debug_indicator,
    python_header_path            = python_header_path
)

result = MainControl.runCompiler(
    gcc_options = gcc_options
)

# Exit if compilation failed.
if not result:
    sys.exit( 1 )


# Execute the module immediately if option was given.
if Options.shallExecuteImmediately():
    if Options.shallMakeModule():
        MainControl.executeModule( tree )
    else:
        MainControl.executeMain( output_filename, tree )
