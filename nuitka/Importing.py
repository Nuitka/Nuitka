#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" The virtue of importing modules and packages.

The actual import of a module may already execute code that changes things.
Imagine a module that does "os.system()", it will be done. People often connect
to databases, and these kind of things, at import time. Not a good style, but
it's being done.

Therefore CPython exhibits the interfaces in an "imp" module in standard
library, which one can use those to know ahead of time, what file import would
load. For us unfortunately there is nothing in CPython that is easily accessible
and gives us this functionality for packages and search paths exactly like
CPython does, so we implement here a multi step search process that is
compatible.

This approach is much safer of course and there is no loss. To determine if it's
from the standard library, one can abuse the attribute "__file__" of the "os"
module like it's done in "isStandardLibraryPath" of this module.

"""

from . import Options, Utils

import sys, os, imp

from logging import warning

_debug_module_finding = False

warned_about = set()

# Directory where the main script lives. Should attempt to import from there.
main_path = None

def setMainScriptDirectory( main_dir ):
    # We need to set this from the outside, pylint: disable=W0603

    global main_path
    main_path = main_dir

def isPackageDir( dirname ):
    return Utils.isDir( dirname ) and \
           Utils.isFile( Utils.joinpath( dirname, "__init__.py" ))

def findModule( source_ref, module_name, parent_package, level, warn ):
    # We have many branches here, because there are a lot of cases to try.
    # pylint: disable=R0912

    if level > 1 and parent_package is not None:
        parent_package = ".".join( parent_package.split(".")[ : -level+1 ] )

        if parent_package == "":
            parent_package = None

    if module_name != "" or parent_package is not None:
        try:
            module_filename, module_package_name = _findModule(
                module_name    = module_name,
                parent_package = parent_package
            )
        except ImportError:
            if warn and not _isWhiteListedNotExistingModule( module_name ):
                key = module_name, parent_package, level

                if key not in warned_about:
                    warned_about.add( key )

                    if level == 0:
                        level_desc = "as absolute import"
                    elif level == -1:
                        level_desc = "as relative or absolute import"
                    elif level == 1:
                        level_desc = "one package level up" % level
                    else:
                        level_desc = "%d package levels up" % level

                    if parent_package is not None:
                        warning(
                            "%s: Cannot find '%s' in package '%s' %s.",
                            source_ref.getAsString(),
                            module_name,
                            parent_package,
                            level_desc
                        )
                    else:
                        warning(
                            "%s: Cannot find '%s' %s.",
                            source_ref.getAsString(),
                            module_name,
                            level_desc
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
    # We have many branches here, because there are a lot of cases to try.
    # pylint: disable=R0912

    if _debug_module_finding:
        print( "_findModuleInPath: Enter", module_name, package_name )

    assert main_path is not None
    extra_paths = [ os.getcwd(), main_path  ]

    if package_name is not None:
        # Work around imp.find_module bug on at least Windows. Won't handle
        # module name empty in find_module. And thinking of it, how could it
        # anyway.
        if module_name == "":
            module_name = package_name.split( "." )[ -1 ]
            package_name = ".".join( package_name.split( "." )[:-1] )

        def getPackageDirname( element ):
            return Utils.joinpath( element, *package_name.split( "." ) )

        ext_path = [
            getPackageDirname( element )
            for element in
            extra_paths + sys.path
            if isPackageDir( getPackageDirname( element ) )
        ]

        if _debug_module_finding:
            print( "_findModuleInPath: Package, using extended path", ext_path )

        try:
            module_fh, module_filename, _module_desc = imp.find_module( module_name, ext_path )
            if module_fh is not None:
                module_fh.close()

            if _debug_module_finding:
                print( "_findModuleInPath: imp.find_module worked", module_filename, package_name )

            return module_filename, package_name
        except ImportError:
            if _debug_module_finding:
                print( "_findModuleInPath: imp.find_module failed to locate" )
        except SyntaxError:
            # Warn user, as this is kind of unusual.
            warning(
                "%s: Module cannot be imported due to syntax errors",
                module_name,
            )

            if _debug_module_finding:
                print( "_findModuleInPath: imp.find_module failed with syntax error" )

    ext_path = extra_paths + sys.path

    if _debug_module_finding:
        print( "_findModuleInPath: Non-package, using extended path", ext_path )

    try:
        module_fh, module_filename, _module_desc = imp.find_module( module_name, ext_path )
        if module_fh is not None:
            module_fh.close()
    except SyntaxError:
        # Warn user, as this is kind of unusual.
        warning(
            "%s: Module cannot be imported due to syntax errors",
            module_name,
        )

        if _debug_module_finding:
            print( "_findModuleInPath: imp.find_module failed with syntax error" )

        module_filename = None

    if _debug_module_finding:
        print( "_findModuleInPath: imp.find_module gave", module_filename )

    return module_filename, None

def _findModule( module_name, parent_package ):
    if _debug_module_finding:
        print( "_findModule: Enter", module_name, "in", parent_package )

    # The os.path is strangely hacked into the os module, dispatching per
    # platform, we either cannot look into it, or we require that we resolve it
    # here correctly.
    if module_name == "os.path" and parent_package is None:
        parent_package = "os"

        if not Options.isWindowsTarget():
            module_name = Utils.basename( os.path.__file__ ).replace( ".pyc", "" )
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
    white_list = (
        "mac", "nt", "os2", "posix", "_emx_link", "riscos", "ce", "riscospath",
        "riscosenviron", "Carbon.File", "org.python.core", "_sha", "_sha256",
        "array", "_sha512", "_md5", "_subprocess", "msvcrt", "cPickle",
        "marshal", "imp", "sys", "itertools", "cStringIO", "time", "zlib",
        "thread", "math", "errno", "operator", "signal", "gc", "exceptions",
        "win32process", "unicodedata", "__builtin__", "fcntl", "_socket",
        "_ssl", "pwd", "spwd", "_random", "grp", "_io", "_string", "select",
        "__main__", "_winreg", "_warnings", "_sre", "_functools", "_hashlib",
        "_collections", "_locale", "_codecs", "_weakref", "_struct",
        "_dummy_threading", "binascii", "datetime", "_ast", "xxsubtype",
        "_bytesio", "cmath", "_fileio", "aetypes", "aepack", "MacOS", "cd",
        "cl", "gdbm", "gl", "GL", "aetools", "_bisect", "_heapq", "_symtable",
        "syslog", "_datetime", "_elementtree", "_pickle", "_posixsubprocess",
        "_thread", "atexit", "pyexpat", "_imp", "_sha1", "faulthandler",

        # Python-Qt4 does these if missing python3 parts:
        "PyQt4.uic.port_v3.string_io", "PyQt4.uic.port_v3.load_plugin",
        "PyQt4.uic.port_v3.ascii_upper", "PyQt4.uic.port_v3.proxy_base",
        "PyQt4.uic.port_v3.as_string",

        # CPython3 does these:
        "builtins", "UserDict", "os.path", "StringIO",

        # test_frozen.py
        "__hello__", "__phello__", "__phello__.spam", "__phello__.foo",

        # test_import.py
        "RAnDoM", "infinite_reload", "test_trailing_slash",

        # test_importhooks.py
        "hooktestmodule", "hooktestpackage", "hooktestpackage.sub",
        "reloadmodule", "hooktestpackage.sub.subber", "hooktestpackage.oldabs",
        "hooktestpackage.newrel", "hooktestpackage.sub.subber.subest",
        "hooktestpackage.futrel", "sub", "hooktestpackage.newabs",

        # test_new.py
        "Spam",

        # test_pkg.py
        "t1", "t2", "t2.sub", "t2.sub.subsub", "t3.sub.subsub", "t5", "t6",
        "t7", "t7.sub", "t7.sub.subsub",

        # test_pkgutil.py
        "foo", "zipimport",

        # test_platform.py
        "gestalt",

        # test_repr.py
        """areallylongpackageandmodulenametotestreprtruncation.\
areallylongpackageandmodulenametotestreprtruncation""",

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
        "distutils.tests", "distutils.mwerkscompiler",

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

        # test/test_zipimport_support.py
        "test.test_cmd_line_script",

        # Python3 modules that no longer exist
        "commands",
    )

    # TODO: Turn this into a warning that encourages reporting.
    if False and Options.isDebug():
        for module_name in sys.builtin_module_names:
            assert module_name in white_list, module_name

    return module_name in white_list

def isStandardLibraryPath( path ):
    path = Utils.normcase( path )
    os_path = Utils.normcase( Utils.dirname( os.__file__  ) )

    if not path.startswith( os_path ):
        return False

    if "dist-packages" in path or "site-packages" in path:
        return False

    return True
