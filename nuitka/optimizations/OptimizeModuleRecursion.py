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

So this is called repeatedly mayhaps, each time a constant is added.
"""

from __future__ import print_function

from OptimizeBase import OptimizationVisitorBase

from nuitka import TreeBuilding, Importing, Options, Nodes, Utils

class ModuleRecursionVisitor( OptimizationVisitorBase ):
    imported_modules = {}

    def __init__( self ):
        self.stdlib = Options.shallFollowStandardLibrary()

    def _recurseTo( self, module_filename, module_package, module_relpath ):
        if module_relpath not in self.imported_modules:
            print( "Recurse to import", module_relpath )

            self.signalChange( "new_code" )

            imported_module = TreeBuilding.buildModuleTree(
                filename = module_filename,
                package  = module_package
            )

            self.imported_modules[ module_relpath ] = imported_module

        return self.imported_modules[ module_relpath ]


    def _consider( self, module_filename, module_package ):
        assert module_package is None or type( module_package ) is str

        if module_filename.endswith( ".py" ):
            if self.stdlib or not module_filename.startswith( "/usr/lib/python" ):
                module_relpath = Utils.relpath( module_filename )

                return self._recurseTo(
                    module_filename = module_filename,
                    module_package  = module_package,
                    module_relpath  = module_relpath
                )

    def __call__( self, node ):
        if node.isModule():
            module_filename = node.getFilename()

            if module_filename not in self.imported_modules:
                self.imported_modules[ Utils.relpath( module_filename ) ] = node

            module_package = node.getPackage()

            if module_package is not None:
                package_package, package_module_name, package_filename = Importing.findModule(
                    module_name    = module_package,
                    parent_package = None
                )

                self._recurseTo(
                    module_filename = package_module_name.replace( ".", "/" ),
                    module_package  = package_package,
                    module_relpath  = Utils.relpath( package_filename )
                )
        elif node.isStatementImportExternal():
            module_package, module_name, module_filename = Importing.findModule(
                module_name    = node.getModuleName(),
                parent_package = node.getParentModule().getPackage()
            )

            if module_filename is not None:
                imported_module = self._consider(
                    module_filename = module_filename,
                    module_package  = module_package
                )

                if imported_module is not None:
                    import_cut_len = len( node.getModuleName() ) - len( node.getImportName() )

                    import_name = imported_module.getFullName()
                    import_name = import_name[:len(import_name) - import_cut_len ]

                    new_node = Nodes.CPythonStatementImportEmbedded(
                        target      = node.getTarget(),
                        module_name = imported_module.getFullName(),
                        import_name = import_name,
                        module      = imported_module,
                        source_ref  = node.getSourceReference()
                    )

                    node.replaceWith( new_node )
        elif node.isStatementImportFromExternal():
            module_package, module_name, module_filename = Importing.findModule(
                module_name    = node.getModuleName(),
                parent_package = node.getParentModule().getPackage()
            )

            if module_filename is not None:
                imported_module = self._consider(
                    module_filename = module_filename,
                    module_package  = module_package
                )

                if Utils.isDir( module_filename ):
                    sub_modules = []

                    for imported_name in node.getImports():
                        sub_module_package, sub_module_name, sub_module_filename = Importing.findModule(
                            module_name    = node.getModuleName() + "." + imported_name,
                            parent_package = module_package,
                            warn           = False
                        )

                        if sub_module_filename is not None:
                            sub_module = self._consider(
                                module_filename = sub_module_filename,
                                module_package  = sub_module_package,
                            )

                            if sub_module is not None:
                                sub_modules.append( sub_module )

                    new_node = Nodes.CPythonStatementImportFromEmbedded(
                        targets         = node.getTargets(),
                        module_name     = node.getModuleName(),
                        sub_modules     = sub_modules,
                        imports         = node.getImports(),
                        source_ref      = node.getSourceReference()
                    )

                    node.replaceWith( new_node )

        elif node.isBuiltinImport():
            self._consider(
                module_filename = node.getModuleFilename(),
                module_package  = node.getModulePackage()
            )
