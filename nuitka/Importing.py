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
""" The virtue of importing modules and packages.

Unfortunately there is nothing in CPython that is easily accessible and gives us this
functionality, so we implement the module search process on our own.

"""

from . import Options

import sys, os, imp

from logging import warning

def findModule( module_name, parent_package, level, warn = True ):
    assert level < 2 or parent_package, (module_name, parent_package, level)

    if level > 1:
        parent_package = ".".join( parent_package.split(".")[ : -level+1 ] )

        if parent_package == "":
            parent_package = None

    if Options.shallFollowImports():
        try:
            module_filename, module_package_name = _findModule(
                module_name    = module_name,
                parent_package = parent_package
            )
        except ImportError:
            if warn and not _isWhiteListedNotExistingModule( module_name ):
                warning( "Warning, cannot find '%s' in '%s' on level %d" % ( module_name, parent_package, level ) )

            if "." in module_name:
                module_package_name = module_name[ : module_name.rfind( "." ) ]
            else:
                module_package_name = None

            module_filename = None
    else:
        if "." in module_name:
            module_package_name = module_name[ : module_name.rfind( "." ) ]
        else:
            module_package_name = None

        module_filename = None

    if _debug_module_finding:
        print( "findModule: Enter", module_package_name, module_name, module_filename )

    return module_package_name, module_name, module_filename

_debug_module_finding = False

def _findModuleInPath( module_name, package_name ):
    if _debug_module_finding:
        print( "_findModuleInPath: Enter", module_name, package_name )

    if package_name is not None:
        # Work around imp.find_module bug on at least Windows. Won't handle
        # module name empty in find_module. And thinking of it, how could it
        # anyway.
        if module_name == "":
            module_name = package_name.split( "." )[ -1 ]
            package_name = ".".join( package_name.split( "." )[:-1] )

        ext_path = [
            element + os.path.sep + package_name.replace( ".", os.path.sep )
            for element in
            sys.path + [ os.getcwd() ]
        ]

        if _debug_module_finding:
            print( "_findModuleInPath: Package, using extended path", ext_path )

        try:
            _module_fh, module_filename, _module_desc = imp.find_module( module_name, ext_path )

            if _debug_module_finding:
                print( "_findModuleInPath: imp.find_module worked", module_filename, package_name )

            return module_filename, package_name
        except ImportError:
            pass

            if _debug_module_finding:
                print( "_findModuleInPath: imp.find_module failed" )

    ext_path = sys.path + [ os.getcwd() ]

    if _debug_module_finding:
        print( "_findModuleInPath: Non-package, using extended path", ext_path )

    _module_fh, module_filename, _module_desc = imp.find_module( module_name, ext_path )

    if _debug_module_finding:
        print( "_findModuleInPath: imp.find_module gave", module_filename )

    return module_filename, None

def _findModule( module_name, parent_package ):
    if _debug_module_finding:
        print( "_findModule: Enter", module_name, "in", parent_package )

    # The os.path is strangely hacked into the os module, dispatching per platform, we
    # either cannot look into it, or we require that we resolve it here correctly.
    if module_name == "os.path" and parent_package is None:
        parent_package = "os"

        if not Options.isWindowsTarget():
            module_name = os.path.basename( os.path.__file__ ).replace( ".pyc", "" )
        else:
            module_name = "ntpath"

    assert module_name != "" or parent_package is not None

    if "." in module_name:
        package_part = module_name[ : module_name.rfind( "." ) ]
        module_name = module_name[ module_name.rfind( "." ) + 1 : ]

        # Relative import
        if parent_package is not None:
            try:
                return _findModule(
                    module_name    = module_name,
                    parent_package = parent_package + "." + package_part
                )
            except ImportError:
                pass

        # Absolute import
        return _findModule(
            module_name    = module_name,
            parent_package = package_part
        )
    elif module_name == "":
        module_filename, package = _findModuleInPath(
            module_name  = module_name,
            package_name = parent_package
        )

        if package is not None:
            package = ".".join( package.split( "." )[:-1] )

            if package == "":
                package = None

        return module_filename, package
    else:
        return _findModuleInPath(
            module_name  = module_name,
            package_name = parent_package
        )

def _isWhiteListedNotExistingModule( module_name ):
    return module_name in (
        "mac", "nt", "os2", "posix", "_emx_link", "riscos", "ce", "riscospath",
        "riscosenviron", "Carbon.File", "org.python.core", "_sha", "_sha256",
        "_sha512", "_md5", "_subprocess", "msvcrt", "cPickle", "marshal", "imp",
        "sys", "itertools", "cStringIO", "time", "zlib", "thread", "math", "errno",
        "operator", "signal", "gc", "exceptions", "win32process", "unicodedata",
        "__builtin__", "fcntl", "_socket", "_ssl", "pwd", "spwd", "_random", "grp",
        "select", "__main__", "_winreg", "_warnings", "_sre", "_functools", "_hashlib",
        "_collections", "_locale", "_codecs", "_weakref", "_struct", "_dummy_threading"
    )
