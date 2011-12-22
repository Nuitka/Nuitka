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
""" Optimization step that expands the tree by imported modules.

Normally imports are relatively static, but Nuitka also attempts to cover the uses of
__import__ and other import techniques, that allow dynamic values. If other optimizations
make it possible to predict these, the compiler can go deeper that what it normally could.

So this is called repeatedly mayhaps, each time a constant is added.
"""

from .OptimizeBase import OptimizationVisitorBase, info, warning

from nuitka import TreeBuilding, Importing, Options, Utils

import os

_warned_about = set()

def isStandardLibraryPath( path ):
    path = os.path.normcase( path )
    os_path = os.path.normcase( os.path.dirname( os.__file__  ) )

    if not path.startswith( os_path ):
        return False

    if "dist-packages" in path or "site-packages" in path:
        return False

    return True

class ModuleRecursionVisitor( OptimizationVisitorBase ):
    imported_modules = {}

    def _recurseTo( self, module_package, module_filename, module_relpath ):
        if module_relpath not in self.imported_modules:
            info( "Recurse to import %s", module_relpath )

            try:
                imported_module = TreeBuilding.buildModuleTree(
                    filename = module_filename,
                    package  = module_package,
                    is_main  = False
                )
            except ( SyntaxError, IndentationError ) as e:
                if module_filename not in _warned_about:
                    _warned_about.add( module_filename )

                    warning(
                        "Cannot recurse to import module '%s' (%s) because of '%s'",
                        module_relpath,
                        module_filename,
                        e.__class__.__name__
                    )

                return

            assert not module_relpath.endswith( "/__init__.py" )

            self.imported_modules[ module_relpath ] = imported_module

            self.signalChange(
                "new_module",
                imported_module.getSourceReference(),
                "Recursed to module."
            )

        return self.imported_modules[ module_relpath ]

    def _consider( self, module_filename, module_package ):
        assert module_package is None or ( type( module_package ) is str and module_package != "" )

        module_filename = os.path.normpath( module_filename )

        if module_filename.endswith( ".py" ) or Utils.isDir( module_filename ):
            module_name = Utils.basename( module_filename ).replace( ".py", "" )

            decision = self._decide( module_filename, module_name, module_package )

            if decision:
                module_relpath = Utils.relpath( module_filename )

                return self._recurseTo(
                    module_package  = module_package,
                    module_filename = module_filename,
                    module_relpath  = module_relpath
                )
            elif decision is None:
                if module_package is None:
                    module_fullpath = module_name
                else:
                    module_fullpath = module_package + "." + module_name

                if module_filename not in _warned_about:
                    _warned_about.add( module_filename )

                    warning(
                        "Not recursing to '%(full_path)s' (%(filename)s), please specify --recurse-none (do not given this warning), --recurse-all (do recurse to all warned), --recurse-not-to=%(full_path)s (ignore it), --recurse-to=%(full_path)s (recurse to it) to change." % {
                            "full_path" : module_fullpath,
                            "filename"  : module_filename
                        }
                    )

    def _decide( self, module_filename, module_name, module_package ):
        no_case_modules = Options.getShallFollowInNoCase()

        if module_package is None:
            full_name = module_name
        else:
            full_name = module_package + "." + module_name

        for no_case_module in no_case_modules:
            if full_name == no_case_module:
                return False

            if full_name.startswith( no_case_module + "." ):
                return False

        any_case_modules = Options.getShallFollowModules()

        for any_case_module in any_case_modules:
            if full_name == any_case_module:
                return True

            if full_name.startswith( any_case_module + "." ):
                return True

        if Options.shallFollowNoImports():
            return False

        if isStandardLibraryPath( module_filename ):
            return Options.shallFollowStandardLibrary()

        if Options.shallFollowAllImports():
            return True

        # Means, I don't know.
        return None


    def _handleModule( self, module ):
        module_filename = module.getFilename()

        if module_filename not in self.imported_modules:
            if module_filename.endswith( "/__init__.py" ):
                module_relpath = Utils.relpath( module_filename[:-12] )
            else:
                module_relpath = Utils.relpath( module_filename )

            self.imported_modules[ Utils.relpath( module_relpath ) ] = module

        module_package = module.getPackage()

        if module_package is not None:
            package_package, _package_module_name, package_filename = Importing.findModule(
                source_ref     = module.getSourceReference(),
                module_name    = module_package,
                parent_package = None,
                level          = 1
            )

            self._recurseTo(
                module_package  = package_package,
                module_filename = package_filename,
                module_relpath  = Utils.relpath( package_filename )
            )

    def _handleImportModule( self, node ):
        if node.getModule() is None:
            source_ref = node.getSourceReference()

            parent_module = node.getParentModule()

            if parent_module.isPackage():
                parent_package = parent_module.getFullName()
            else:
                parent_package = node.getParentModule().getPackage()

            module_package, _module_name, module_filename = Importing.findModule(
                source_ref     = source_ref,
                module_name    = node.getModuleName(),
                parent_package = parent_package,
                level          = node.getLevel()
            )

            assert module_package != "", node

            if module_filename is not None:
                imported_module = self._consider(
                    module_filename = module_filename,
                    module_package  = module_package
                )

                if imported_module is not None:
                    node.setModule( imported_module )

                    import_list = node.getImportList()

                    if import_list and imported_module.isPackage():
                        for import_item in import_list:

                            module_package, _module_name, module_filename = Importing.findModule(
                                source_ref     = source_ref,
                                module_name    = import_item,
                                parent_package = imported_module.getFullName(),
                                level          = -1,
                                warn           = False
                            )

                            if module_filename is not None:
                                _imported_module = self._consider(
                                    module_filename = module_filename,
                                    module_package  = module_package
                                )


        node.setAttemptedRecurse()

    def __call__( self, node ):
        if node.isModule():
            self._handleModule(
                module = node
            )
        elif node.isExpressionImportModule() and not node.hasAttemptedRecurse():
            self._handleImportModule(
                node = node
            )
