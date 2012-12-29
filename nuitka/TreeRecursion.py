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
""" Recursion into other modules.

"""

from nuitka import Utils

from . import TreeBuilding, Importing

from logging import info, warning

_warned_about = set()

def recurseTo( module_package, module_filename, module_relpath ):
    if TreeBuilding.isImportedPath( module_relpath ):
        info( "Recurse to import %s", module_relpath )

        try:
            _imported_module = TreeBuilding.buildModuleTree(
                filename = module_filename,
                package  = module_package,
                is_top   = False,
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

            return None, False

        assert not module_relpath.endswith( "/__init__.py" )

        return TreeBuilding.getImportedModule( module_relpath ), True
    else:
        return TreeBuilding.getImportedModule( module_relpath ), False


def considerFilename( module_filename, module_package ):
    assert module_package is None or ( type( module_package ) is str and module_package != "" )

    module_filename = Utils.normpath( module_filename )

    if Utils.isDir( module_filename ):
        module_name = Utils.basename( module_filename )
        module_relpath = Utils.relpath( module_filename )

        return module_filename, module_relpath, module_name
    elif module_filename.endswith( ".py" ):
        module_name = Utils.basename( module_filename )[:-3]
        module_relpath = Utils.relpath( module_filename )

        return module_filename, module_relpath, module_name

def checkPluginPath( plugin_filename, module_package ):
    plugin_info = considerFilename(
        module_package  = module_package,
        module_filename = plugin_filename
    )

    if plugin_info is not None:
        module, added = recurseTo(
            module_filename = plugin_info[0],
            module_relpath  = plugin_info[1],
            module_package  = module_package
        )

        if module:
            if not added:
                warning(
                    "Recursed to %s '%s' at '%s' twice.",
                    "package" if module.isPackage() else "module",
                    module.getName(),
                    plugin_info[0]
                )

            if module.isPackage():
                package_dir = Utils.dirname( module.getFilename() )

                for sub_path, sub_filename in Utils.listDir( package_dir ):
                    if sub_filename == "__init__.py":
                        continue

                    assert sub_path != plugin_filename, package_dir

                    if Importing.isPackageDir( sub_path ) or sub_path.endswith( ".py" ):
                        checkPluginPath( sub_path, module.getFullName() )


        else:
            warning( "Failed to include module from '%s'.", plugin_info[0] )
