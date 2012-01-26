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
""" Recursion into other modules.

"""

from nuitka import Utils

from . import TreeBuilding

from logging import info, warning

import os

_warned_about = set()

imported_modules = {}

def recurseTo( module_package, module_filename, module_relpath ):
    if module_relpath not in imported_modules:
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

            return None, False

        assert not module_relpath.endswith( "/__init__.py" )

        imported_modules[ module_relpath ] = imported_module

        return imported_modules[ module_relpath ], True
    else:
        return imported_modules[ module_relpath ], False


def considerFilename( module_filename, module_package ):
    assert module_package is None or ( type( module_package ) is str and module_package != "" )

    module_filename = os.path.normpath( module_filename )

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
                warning( "Recursed to module at '%s' twice.", plugin_info[0] )

            if module.isPackage():
                package_dir = Utils.dirname( module.getFilename() )

                for sub_path, sub_filename in Utils.listDir( package_dir ):
                    if sub_filename == "__init__.py":
                        continue

                    if Utils.isDir( sub_path ) or sub_path.endswith( ".py" ):
                        checkPluginPath( sub_path, module.getFullName() )


        else:
            warning( "Failed to include module from '%s'.", plugin_info[0] )
