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


import SourceCodeReferences
import Options
import Nodes

import sys, os, imp

from logging import warning

def findModule( module_name, parent_package ):
    module_topname = module_name.split(".")[0]
    module_basename =  module_name.split(".")[-1]

    parent_package_name = parent_package.getName() if parent_package is not None else None

    if Options.shallFollowImports():
        try:
            module_filename, module_package_name = _findModule( module_name, parent_package_name )
        except ImportError:
            if not _isWhiteListedNotExistingModule( module_name ):
                warning( "Warning, cannot find " + module_name )

            if module_name.find( "." ) != -1:
                module_package_name = module_name[ : module_name.rfind( "." ) ]
            else:
                module_package_name = None

            module_filename = None
    else:
        if module_name.find( "." ) != -1:
            module_package_name = module_name[ : module_name.rfind( "." ) ]
        else:
            module_package_name = None

        module_filename = None

    if module_package_name is None:
        module_package = None
    else:
        module_package = Nodes.CPythonPackage(
            name           = module_package_name,
            parent_package = None, # TODO: Have a registry of it, find it
            source_ref     = SourceCodeReferences.SourceCodeReference.fromFilenameAndLine( "unknown.py", 1 )
        )

    return module_package, module_name, module_filename

_debug_module_finding = False

def _findModuleInPath( module_name, package_name ):
    if _debug_module_finding:
        print( "_findModuleInPath: Enter", module_name, package_name )

    if package_name is not None:
        ext_path = [ element + os.path.sep + package_name.replace( ".", os.path.sep ) for element in sys.path + ["."] ]
        try:
            _module_fh, module_filename, _module_desc = imp.find_module( module_name, ext_path )

            return module_filename
        except ImportError:
            pass

    ext_path = sys.path + ["."]
    _module_fh, module_filename, _module_desc = imp.find_module( module_name, ext_path )

    return module_filename

def _findModule( module_name, parent_package ):
    if _debug_module_finding:
        print( "_findModule: Enter", module_name, "in", parent_package )

    # The os.path is strangely hacked into the os module, dispatching per platform, we
    # either cannot look into it, or we require to be on the target platform. Non-Linux is
    # unusually enough, but common, cross platform compile, lets give up on that.
    if module_name == "os.path" and parent_package is None:
        parent_package = "os"
        module_name = os.path.basename( os.path.__file__ ).replace( ".pyc", "" )

    if module_name.find( "." ) != -1:
        package_part = module_name[ : module_name.rfind( "." ) ]
        module_name = module_name[ module_name.rfind( "." ) + 1 : ]

        if parent_package is not None:
            return _findModule( package_part, parent_package + "." + package_part )
        else:
            return _findModule( module_name, package_part )
    else:
        return _findModuleInPath( module_name, parent_package ), parent_package


def _isWhiteListedNotExistingModule( module_name ):
    return module_name in ( "mac", "nt", "os2", "_emx_link", "riscos", "ce", "riscospath", "riscosenviron", "Carbon.File", "org.python.core", "_sha", "_sha256", "_sha512", "_md5", "_subprocess", "msvcrt", "cPickle", "marshal", "imp", "sys", "itertools", "cStringIO", "time", "zlib", "thread", "math", "errno", "operator" )
