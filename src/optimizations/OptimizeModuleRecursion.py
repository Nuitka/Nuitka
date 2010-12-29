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
""" Optimization step that expands the tree by imported modules.


Normally imports are relatively static, but Nuitka also attempts to cover the uses of
__import__ and other import techniques, that allow dynamic values. If other optimizations
make it possible to predict these, the compiler can go deeper that what it normally could.

So this is called repeatedly mayhaps, each time a constant is added. TODO: Therefore it
registers an observer to nodes of interest, checking if they become constant at a later
stage.
"""

from __future__ import print_function

import os

from optimizations.OptimizeBase import OptimizationVisitorBase

import TreeBuilding
import Options
import Nodes

class ModuleRecursionVisitor( OptimizationVisitorBase ):
    imported_modules = {}

    def __init__( self ):
        self.stdlib = Options.shallFollowStandardLibrary()

    def _consider( self, module_filename, module_package ):
        assert module_package is None or isinstance( module_package, Nodes.CPythonPackage )

        if module_filename.endswith( ".py" ):
            if self.stdlib or not module_filename.startswith( "/usr/lib/python" ):
                if os.path.relpath( module_filename ) not in self.imported_modules:
                    print( "Recurse to", module_filename )

                    self.signalChange( "new_code" )

                    imported_module = TreeBuilding.buildModuleTree(
                        filename = module_filename,
                        package  = module_package
                    )

                    self.imported_modules[ os.path.relpath( module_filename ) ] = imported_module

    def __call__( self, node ):
        if node.isModule():
            module_filename = node.getFilename()

            if module_filename not in self.imported_modules:
                self.imported_modules[ os.path.relpath( module_filename ) ] = node
        elif node.isStatementImport() or node.isStatementImportFrom():
            for module_filename, module_package in zip( node.getModuleFilenames(), node.getModulePackages() ):
                self._consider(
                    module_filename = module_filename,
                    module_package  = module_package
                )
        elif node.isBuiltinImport():
            self._consider(
                module_filename = node.getModuleFilename(),
                module_package  = node.getModulePackage()
            )
