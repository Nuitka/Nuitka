#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Locating modules and package source on disk.

The actual import of a module would already execute code that changes things.
Imagine a module that does "os.system()", it will be done. People often connect
to databases, and these kind of things, at import time. Not a good style, but
it's being done.

Therefore CPython exhibits the interfaces in an "imp" module in standard
library, which one can use those to know ahead of time, what file import would
load. For us unfortunately there is nothing in CPython that gives the fully
compatible functionality we need for packages and search paths exactly like
CPython does, so we implement here a multiple step search process that is
compatible.

This approach is much safer of course and there is no loss. To determine if it's
from the standard library, we can abuse the attribute "__file__" of the "os"
module like it's done in "isStandardLibraryPath" of this module.

"""

from __future__ import print_function

import imp
import os
import sys
from logging import warning

from . import Utils, oset

_debug_module_finding = False

warned_about = set()

# Directory where the main script lives. Should attempt to import from there.
main_path = None

def setMainScriptDirectory(main_dir):
    """ Initialize the main script directory.

        We use this as part of the search path for modules.
    """
    # We need to set this from the outside, pylint: disable=W0603

    global main_path
    main_path = main_dir

def isPackageDir(dirname):
    """ Decide if a directory is a package.

        Before Python3.3 it's required to have a "__init__.py" file, but then
        it became impossible to decide.
    """

    return Utils.isDir(dirname) and \
           (
               Utils.python_version >= 330 or
               Utils.isFile(Utils.joinpath(dirname, "__init__.py"))
           )

def findModule(source_ref, module_name, parent_package, level, warn):
    """ Find a module with given package name as parent.

        The package name can be None of course. Level is the same
        as with "__import__" built-in. Warnings are optional.

        Returns a triple of package name the module is in, module name
        and filename of it, which can be a directory.
    """

    # We have many branches here, because there are a lot of cases to try.
    # pylint: disable=R0912

    if level > 1 and parent_package is not None:
        parent_package = '.'.join(parent_package.split('.')[:-level+1])

        if parent_package == "":
            parent_package = None

    if module_name != "" or parent_package is not None:
        try:
            module_filename, module_package_name = _findModule(
                module_name    = module_name,
                parent_package = parent_package
            )
        except ImportError:
            if warn and not _isWhiteListedNotExistingModule(module_name):
                key = module_name, parent_package, level

                if key not in warned_about:
                    warned_about.add(key)

                    if level == 0:
                        level_desc = "as absolute import"
                    elif level == -1:
                        level_desc = "as relative or absolute import"
                    elif level == 1:
                        level_desc = "%d package level up" % level
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


            if '.' in module_name:
                module_package_name = module_name[:module_name.rfind('.')]
            else:
                module_package_name = None

            module_filename = None
    else:
        if '.' in module_name:
            module_package_name = module_name[:module_name.rfind('.')]
        else:
            module_package_name = None

        module_filename = None

    if _debug_module_finding:
        print(
            "findModule: Result",
            module_package_name,
            module_name,
            module_filename
        )

    return module_package_name, module_name, module_filename

# Some platforms are case insensitive.
case_sensitive = not sys.platform.startswith(("win", "cygwin", "darwin"))

def _findModuleInPath2(module_name, search_path):
    """ This is out own module finding low level implementation.

        Just the full module name and search path are given. This is then
        tasked to raise ImportError or return a path if it finds it, or
        None, if it is a built-in.
    """
    # We have many branches here, because there are a lot of cases to try.
    # pylint: disable=R0912

    if imp.is_builtin(module_name):
        return None

    # We may have to decide between package and module, therefore build
    # a list of candidates.
    candidates = oset.OrderedSet()

    considered = set()

    for entry in search_path:
        # Don't try again, just with an entry of different casing or complete
        # duplicate.
        if Utils.normcase(entry) in considered:
            continue
        considered.add(Utils.normcase(entry))

        package_directory = os.path.join(entry, module_name)

        # First, check for a package with an init file, that would be the
        # first choice.
        if Utils.isDir(package_directory):
            for suffix in (".py", ".pyc"):
                package_file_name = "__init__" + suffix

                file_path = os.path.join(package_directory, package_file_name)

                if Utils.isFile(file_path):
                    candidates.add(
                        (entry, 1, package_directory)
                    )
                    break
            else:
                if Utils.python_version >= 330:
                    candidates.add(
                        (entry, 2, package_directory)
                    )

        # Then, check out suffixes of all kinds.
        for suffix, _mode, _type in imp.get_suffixes():
            file_path = Utils.joinpath(entry, module_name + suffix)
            if Utils.isFile(file_path):
                candidates.add(
                    (entry, 1, file_path)
                )
                break

    if candidates:
        # Ignore lower priority matches, package directories without init.
        min_prio = min(candidate[1] for candidate in candidates)
        candidates = [
            candidate
            for candidate in
            candidates
            if candidate[1] == min_prio
        ]

        # On case sensitive systems, no resolution needed.
        if case_sensitive:
            return candidates[0][2]
        else:
            if len(candidates) == 1:
                # Just one finding, good.
                return candidates[0][2]
            else:
                for candidate in candidates:
                    dir_listing = os.listdir(candidate[0])

                    for filename in dir_listing:
                        if Utils.joinpath(candidate[0], filename) == candidate[2]:
                            return candidate[2]

                # Please report this, but you may uncomment and have luck.
                assert False, candidates

                # If no case matches, just pick the first.
                return candidates[0][2]

    # Nothing found.
    raise ImportError


def _findModuleInPath(module_name, package_name):
    # We have many branches here, because there are a lot of cases to try.
    # pylint: disable=R0912

    if _debug_module_finding:
        print("_findModuleInPath: Enter", module_name, "in", package_name)

    assert main_path is not None
    extra_paths = [os.getcwd(), main_path]

    if package_name is not None:
        # Work around _findModuleInPath2 bug on at least Windows. Won't handle
        # module name empty in find_module. And thinking of it, how could it
        # anyway.
        if module_name == "":
            module_name = package_name.split('.')[-1]
            package_name = '.'.join(package_name.split('.')[:-1])

        def getPackageDirnames(element):
            yield Utils.joinpath(element,*package_name.split('.')), False

            if package_name == "win32com":
                yield Utils.joinpath(element,"win32comext"), True

        ext_path = []
        for element in extra_paths + sys.path:
            for package_dir, force_package in getPackageDirnames(element):
                if isPackageDir(package_dir) or force_package:
                    ext_path.append(package_dir)

        if _debug_module_finding:
            print("_findModuleInPath: Package, using extended path", ext_path)

        try:
            module_filename = _findModuleInPath2(
                module_name = module_name,
                search_path = ext_path
            )

            if _debug_module_finding:
                print(
                    "_findModuleInPath: _findModuleInPath2 worked",
                    module_filename,
                    package_name
                )

            return module_filename, package_name
        except ImportError:
            if _debug_module_finding:
                print("_findModuleInPath: _findModuleInPath2 failed to locate")
        except SyntaxError:
            # Warn user, as this is kind of unusual.
            warning(
                "%s: Module cannot be imported due to syntax errors.",
                module_name,
            )

            return None, None

    ext_path = extra_paths + sys.path

    if _debug_module_finding:
        print("_findModuleInPath: Non-package, using extended path", ext_path)

    try:
        module_filename = _findModuleInPath2(
            module_name = module_name,
            search_path = ext_path
        )
    except SyntaxError:
        # Warn user, as this is kind of unusual.
        warning(
            "%s: Module cannot be imported due to syntax errors.",
            module_name,
        )

        return None, None

    if _debug_module_finding:
        print("_findModuleInPath: _findModuleInPath2 gave", module_filename)

    return module_filename, None


def _findModule(module_name, parent_package):
    if _debug_module_finding:
        print("_findModule: Enter", module_name, "in", parent_package)

    # The os.path is strangely hacked into the "os" module, dispatching per
    # platform, we either cannot look into it, or we require that we resolve it
    # here correctly.
    if module_name == "os.path" and parent_package is None:
        parent_package = "os"

        module_name = Utils.basename(os.path.__file__)
        if module_name.endswith(".pyc"):
            module_name = module_name[:-4]

    assert module_name != "" or parent_package is not None

    # Built-in module names must not be searched any further.
    if module_name in sys.builtin_module_names and parent_package is None:
        return None, None

    if '.' in module_name:
        package_part = module_name[ : module_name.rfind('.') ]
        module_name = module_name[ module_name.rfind('.') + 1 : ]

        # Relative import
        if parent_package is not None:
            try:
                return _findModule(
                    module_name    = module_name,
                    parent_package = parent_package + '.' + package_part
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

def getModuleWhiteList():
    return (
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

        # test_applesingle.py
        "applesingle",

        # test_compile.py
        "__package__.module", "__mangled_mod",

        # test_dbm.py
        "dbm.dumb",

        # test_distutils.py
        "distutils.tests", "distutils.mwerkscompiler",

        # test_docxmlrpc.py
        "xmlrpc.server",

        # test_emails.py
        "email.test.test_email", "email.test.test_email_renamed",
        "email.test.test_email_codecs",

        # test/test_dbm_ndbm.py
        "dbm.ndbm",

        # test_frozen.py
        "__hello__", "__phello__", "__phello__.spam", "__phello__.foo",

        # test_imp.py
        "importlib.test.import_", "pep3147.foo", "pep3147",

        # test_import.py
        "RAnDoM", "infinite_reload", "test_trailing_slash", "nonexistent_xyzzy",
        "_parent_foo.bar", "_parent_foo", "test_unc_path",

        # test_importhooks.py
        "hooktestmodule", "hooktestpackage", "hooktestpackage.sub",
        "reloadmodule", "hooktestpackage.sub.subber", "hooktestpackage.oldabs",
        "hooktestpackage.newrel", "hooktestpackage.sub.subber.subest",
        "hooktestpackage.futrel", "sub", "hooktestpackage.newabs",

        # test_inspect.py
        "inspect_fodder3",

        # test_imageop.py
        "imgfile",

        # test_json.py
        "json.tests",

        # test_lib2to3.py
        "lib2to3.tests",

        # test_logging.py
        "win32evtlog", "win32evtlogutil",

        # test_macostools.py
        "macostools",

        # test_namespace_pkgs.py
        "foo.one", "foo.two", "parent.child.one", "parent.child.two",
        "parent.child.three", "bar.two", "a_test",

        # test_new.py
        "Spam",
        # est_ossaudiodev.py
        "ossaudiodev",

        # test_platform.py
        "gestalt",

        # test_pkg.py
        "t1", "t2", "t2.sub", "t2.sub.subsub", "t3.sub.subsub", "t5", "t6",
        "t7", "t7.sub", "t7.sub.subsub", "t8",

        # test_pkgutil.py
        "foo", "zipimport",

        # test_repr.py
        """areallylongpackageandmodulenametotestreprtruncation.\
areallylongpackageandmodulenametotestreprtruncation""",

        # test_robotparser.py
        "urllib.error",

        # test_runpy.py
        "test.script_helper",

        # test_strftime.py
        "java",

        # test_strop.py
        "strop",

        # test_sundry.py
        "distutils.emxccompiler", "os2emxpath",

        # test_tk.py
        "runtktests",

        # test_tools.py
        "analyze_dxp", "test_unparse",

        # test_traceback.py
        "test_bug737473",

        # test_xml_etree.py
        "xml.parsers.expat.errors",

        # test_zipimport_support.py
        "test_zipped_doctest", "zip_pkg",

        # test/test_zipimport_support.py
        "test.test_cmd_line_script",

        # Python3: modules that no longer exist
        "commands", "dummy_thread", "_dummy_thread", "httplib", "Queue", "sets",

        # Python2: modules that don't yet exit
        "http.client", "queue", "winreg",

        # Very old modules with older names
        "simplejson", "sets",

        # Standalone mode "site" import flexibilities
        "sitecustomize", "usercustomize", "apport_python_hook",
        "_frozen_importlib",

        # Standard library stuff that is optional
        "comtypes.server.inprocserver", "_tkinter", "_scproxy", "EasyDialogs",
        "SOCKS", "rourl2path", "_winapi", "win32api", "win32con", "_gestalt",
        "java.lang", "vms_lib", "ic", "readline", "termios", "_sysconfigdata",
        "al", "AL", "sunaudiodev", "SUNAUDIODEV", "Audio_mac", "nis",
        "test.test_MimeWriter", "dos", "win32pipe", "Carbon", "Carbon.Files",
        "sgi", "ctypes.macholib.dyld", "bsddb3", "_pybsddb", "_xmlrpclib",
        "netbios", "win32wnet", "email.Parser", "elementree.cElementTree",
        "elementree.ElementTree", "_gbdm", "resource", "crypt", "bz2", "dbm",
        "mmap",

        # Nuitka tests
        "test_common",

        # Mercurial test
        "statprof", "email.Generator", "email.Utils",
    )

def _isWhiteListedNotExistingModule(module_name):
    result = module_name in getModuleWhiteList()

    if not result and module_name in sys.builtin_module_names:
        warning("""\
Your CPython version has a built-in module '%s', that is not whitelisted
please report this to http://bugs.nuitka.net.""", module_name)

    return result


def getStandardLibraryPaths():
    """ Get the standard library paths.

    """

    # Using the function object to cache its result, avoiding global variable
    # usage.
    if not hasattr(getStandardLibraryPaths, "result"):
        os_filename = os.__file__
        if os_filename.endswith(".pyc"):
            os_filename = os_filename[:-1]

        os_path = Utils.normcase(Utils.dirname(os_filename))

        stdlib_paths = set([os_path])

        # Happens for virtualenv situation, some modules will come from the link
        # this points to.
        if Utils.isLink(os_filename):
            os_filename = Utils.readLink(os_filename)
            stdlib_paths.add(Utils.normcase(Utils.dirname(os_filename)))

        # Another possibility is "orig-prefix.txt" file near the os.py, which
        # points to the original install.
        orig_prefix_filename = Utils.joinpath(os_path, "orig-prefix.txt")

        if Utils.isFile(orig_prefix_filename):
            # Scan upwards, until we find a "bin" folder, with "activate" to
            # locate the structural path to be added. We do not know for sure
            # if there is a sub-directory under "lib" to use or not. So we try
            # to detect it.
            search = os_path
            lib_part = ""

            while os.path.splitdrive(search)[1] not in (os.path.sep, ""):
                if Utils.isFile(Utils.joinpath(search,"bin/activate")) or \
                   Utils.isFile(Utils.joinpath(search,"scripts/activate")):
                    break

                lib_part = Utils.joinpath(Utils.basename(search), lib_part)

                search = Utils.dirname(search)

            assert search and lib_part

            stdlib_paths.add(
                Utils.normcase(
                    Utils.joinpath(
                        open(orig_prefix_filename).read(),
                        lib_part,
                    )
                )
            )

        # And yet another possibility, for MacOS Homebrew created virtualenv
        # at least is a link ".Python", which points to the original install.
        python_link_filename = Utils.joinpath(os_path, "..", ".Python")
        if Utils.isLink(python_link_filename):
            stdlib_paths.add(
                Utils.normcase(
                    Utils.joinpath(
                        Utils.readLink(python_link_filename),
                        "lib"
                    )
                )
            )

        getStandardLibraryPaths.result = [
            Utils.normcase(stdlib_path)
            for stdlib_path in
            stdlib_paths
        ]

    return getStandardLibraryPaths.result


def isStandardLibraryPath(path):
    """ Check if a path is in the standard library.

    """

    path = Utils.normcase(path)

    # In virtualenv, the "site.py" lives in a place that suggests it is not in
    # standard library, although it is.
    if os.path.basename(path) == "site.py":
        return True

    # These never are in standard library paths.
    if "dist-packages" in path or "site-packages" in path:
        return False

    for candidate in getStandardLibraryPaths():
        if path.startswith(candidate):
            return True
    return False
