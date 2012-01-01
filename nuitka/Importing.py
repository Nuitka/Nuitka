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

The actual import of a module may already execute code that changes things. Imagine a
module that does "os.system()", it will be done. People often connect to databases,
and these kind of things, at import time. Not a good style, but it's being done.

Therefore CPython exhibits the interfaces in an "imp" module in standard library,
which one can use those to know ahead of time, what file import would load. For us
unfortunately there is nothing in CPython that is easily accessible and gives us this
functionality for packages and search paths exactly like CPython does, so we implement
here a multi step search process that is compatible.

This approach is much safer of course and there is no loss. To determine if it's from
the standard library, one can abuse the attribute "__file__" of the "os" module like
it's done in "isStandardLibraryPath" of this module.

"""

from . import Options, Utils

import sys, os, imp

from logging import warning

_debug_module_finding = False

_warned_about = set()

def findModule( source_ref, module_name, parent_package, level, warn = True ):
    assert level < 2 or parent_package, (module_name, parent_package, level)

    if level > 1:
        parent_package = ".".join( parent_package.split(".")[ : -level+1 ] )

        if parent_package == "":
            parent_package = None

    if not Options.shallMakeModule() and ( module_name != "" or parent_package is not None ):
        try:
            module_filename, module_package_name = _findModule(
                module_name    = module_name,
                parent_package = parent_package
            )
        except ImportError:
            if warn and not _isWhiteListedNotExistingModule( module_name ):
                key = module_name, parent_package, level

                if key not in _warned_about:
                    _warned_about.add( key )

                    warning(
                        "%s: Cannot find '%s' in '%s' on level %d",
                        source_ref.getAsString(),
                        module_name,
                        parent_package,
                        level
                    )

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
        print( "findModule: Result", module_package_name, module_name, module_filename )

    return module_package_name, module_name, module_filename

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
            Utils.joinpath( element, *package_name.split( "." ) )
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
    else:
        module_filename, package = _findModuleInPath(
            module_name  = module_name,
            package_name = parent_package
        )

        if package == "":
            package = None

        return module_filename, package

def _isWhiteListedNotExistingModule( module_name ):
    return module_name in (
        "mac", "nt", "os2", "posix", "_emx_link", "riscos", "ce", "riscospath",
        "riscosenviron", "Carbon.File", "org.python.core", "_sha", "_sha256", "array",
        "_sha512", "_md5", "_subprocess", "msvcrt", "cPickle", "marshal", "imp",
        "sys", "itertools", "cStringIO", "time", "zlib", "thread", "math", "errno",
        "operator", "signal", "gc", "exceptions", "win32process", "unicodedata",
        "__builtin__", "fcntl", "_socket", "_ssl", "pwd", "spwd", "_random", "grp",
        "select", "__main__", "_winreg", "_warnings", "_sre", "_functools", "_hashlib",
        "_collections", "_locale", "_codecs", "_weakref", "_struct", "_dummy_threading",
        "binascii", "datetime", "_ast", "xxsubtype", "_bytesio", "cmath", "_fileio",


        # CPython3 does these:
        "builtins", "UserDict", "os.path",

        # test_frozen.py
        "__hello__", "__phello__", "__phello__.spam", "__phello__.foo",

        # test_import.py
        "RAnDoM", "infinite_reload", "test_trailing_slash",

        # test_importhooks.py
        "hooktestmodule", "hooktestpackage", "hooktestpackage.sub", "reloadmodule",
        "hooktestpackage.sub.subber", "hooktestpackage.oldabs", "hooktestpackage.newrel",
        "hooktestpackage.sub.subber.subest", "hooktestpackage.futrel", "sub",
        "hooktestpackage.newabs",

        # test_new.py
        "Spam",

        # test_pkg.py
        "t1", "t2", "t2.sub", "t2.sub.subsub", "t3.sub.subsub", "t5", "t6", "t7",
        "t7.sub", "t7.sub.subsub",

        # test_pkgutil.py
        "foo", "zipimport",

        # test_platform.py
        "gestalt",

        # test_repr.py
        "areallylongpackageandmodulenametotestreprtruncation.areallylongpackageandmodulenametotestreprtruncation",

        # test_runpy.py
        "test.script_helper",

        # test_strftime.py
        "java",

        # test_strop.py
        "strop",

        # test_applesingle.py
        "applesingle",

        # test_compile.py
        "__package__.module", "__mangled_mod",

        # test_distutils.py
        "distutils.tests",

        # test_emails.py
        "email.test.test_email", "email.test.test_email_renamed",

        # test_imageop.py
        "imgfile",

        # test_json.py
        "json.tests",

        # test_lib2to3.py
        "lib2to3.tests",

        # test_macostools.py
        "macostools",

        # test_pkg.py
        "t8",

        # test_tk.py
        "runtktests",

        # test_traceback.py
        "test_bug737473",

        # test_zipimport_support.py
        "test_zipped_doctest", "zip_pkg",
    )
