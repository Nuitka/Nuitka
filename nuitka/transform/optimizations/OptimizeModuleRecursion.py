#     Copyright 2012, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Optimization step that expands the tree by imported modules.

Normally imports are relatively static, but Nuitka also attempts to cover the uses of
__import__ and other import techniques, that allow dynamic values. If other optimizations
make it possible to predict these, the compiler can go deeper that what it normally could.

So this is called repeatedly mayhaps, each time a constant is added.
"""

from .OptimizeBase import OptimizationVisitorBase, warning

from nuitka import TreeRecursion, Importing, Options, Utils

import os

_warned_about = set()

def isStandardLibraryPath( path ):
    path = Utils.normcase( path )
    os_path = Utils.normcase( Utils.dirname( os.__file__  ) )

    if not path.startswith( os_path ):
        return False

    if "dist-packages" in path or "site-packages" in path:
        return False

    return True


class ModuleRecursionVisitor( OptimizationVisitorBase ):
    def _recurseTo( self, module_package, module_filename, module_relpath ):
        imported_module, added_flag = TreeRecursion.recurseTo(
            module_package  = module_package,
            module_filename = module_filename,
            module_relpath  = module_relpath
        )

        if added_flag:
            self.signalChange(
                "new_module",
                imported_module.getSourceReference(),
                "Recursed to module."
            )

        return imported_module

    def _consider( self, module_filename, module_package ):
        assert module_package is None or ( type( module_package ) is str and module_package != "" )

        module_filename = Utils.normpath( module_filename )

        if Utils.isDir( module_filename ):
            module_name = Utils.basename( module_filename )
        elif module_filename.endswith( ".py" ):
            module_name = Utils.basename( module_filename )[:-3]
        else:
            module_name = None

        if module_name is not None:
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

                    warning( # long message, but shall be like it, pylint: disable=C0301
                        """\
Not recursing to '%(full_path)s' (%(filename)s), please specify \
--recurse-none (do not warn), \
--recurse-all (recurse to all), \
--recurse-not-to=%(full_path)s (ignore it), \
--recurse-to=%(full_path)s (recurse to it) to change.""" % {
                            "full_path" : module_fullpath,
                            "filename"  : module_filename
                        }
                    )

    @staticmethod
    def _decide( module_filename, module_name, module_package ):
        # Many branches, which make decisions immediately, pylint: disable=R0911

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

        # Mark as attempted, do not retry.
        node.setAttemptedRecurse()

    def onEnterNode( self, node ):
        if node.isExpressionImportModule() and not node.hasAttemptedRecurse():
            self._handleImportModule(
                node = node
            )
