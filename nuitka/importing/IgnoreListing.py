#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Ignore listing of modules that are not found, but probably that's acceptable.

"""

import sys

from nuitka.Errors import NuitkaOptimizationError


def getModuleIgnoreList():
    return (
        "mac",
        "nt",
        "os2",
        "posix",
        "_emx_link",
        "riscos",
        "ce",
        "riscospath",
        "riscosenviron",
        "Carbon.File",
        "org.python.core",
        "_sha",
        "_sha256",
        "array",
        "_sha512",
        "_md5",
        "_subprocess",
        "msvcrt",
        "cPickle",
        "marshal",
        "imp",
        "sys",
        "itertools",
        "cStringIO",
        "time",
        "zlib",
        "thread",
        "math",
        "errno",
        "operator",
        "signal",
        "gc",
        "exceptions",
        "win32process",
        "unicodedata",
        "__builtin__",
        "fcntl",
        "_socket",
        "_ssl",
        "pwd",
        "spwd",
        "_random",
        "grp",
        "_io",
        "_string",
        "select",
        "__main__",
        "_winreg",
        "_warnings",
        "_sre",
        "_functools",
        "_hashlib",
        "_collections",
        "_locale",
        "_codecs",
        "_weakref",
        "_struct",
        "_dummy_threading",
        "binascii",
        "datetime",
        "_ast",
        "xxsubtype",
        "_bytesio",
        "cmath",
        "_fileio",
        "aetypes",
        "aepack",
        "MacOS",
        "cd",
        "cl",
        "gdbm",
        "gl",
        "GL",
        "aetools",
        "_bisect",
        "_heapq",
        "_symtable",
        "syslog",
        "_datetime",
        "_elementtree",
        "_pickle",
        "_posixsubprocess",
        "_thread",
        "atexit",
        "pyexpat",
        "_imp",
        "_sha1",
        "faulthandler",
        "_osx_support",
        "sysconfig",
        "copyreg",
        "ipaddress",
        "reprlib",
        "win32event",
        "win32file",
        # Python-Qt4 does these if missing python3 parts:
        "PyQt4.uic.port_v3.string_io",
        "PyQt4.uic.port_v3.load_plugin",
        "PyQt4.uic.port_v3.ascii_upper",
        "PyQt4.uic.port_v3.proxy_base",
        "PyQt4.uic.port_v3.as_string",
        # CPython3 does these:
        "builtins",
        "UserDict",
        "os.path",
        "StringIO",
        # "test_array",
        "_testcapi",
        # test_applesingle.py
        "applesingle",
        # test_buffer.py
        "_testbuffer",
        # test_bsddb.py
        "bsddb.test",
        # test_collections.py
        "collections.abc",
        # test_compile.py
        "__package__.module",
        "__mangled_mod",
        "__package__",
        # test_ctypes
        "ctypes.test",
        # test_dbm.py
        "dbm.dumb",
        # test_dbm_ndbm.py
        "dbm.ndbm",
        # test_distutils.py
        "distutils.tests",
        "distutils.mwerkscompiler",
        # test_docxmlrpc.py
        "xmlrpc",
        # test_emails.py
        "email.test.test_email",
        "email.test.test_email_renamed",
        "email.test.test_email_codecs",
        # test_email_codecs.py
        "email.test",
        # test_enum.py
        "enum",
        # test_file.py
        "_pyio",
        # test_frozen.py
        "__hello__",
        "__phello__",
        "__phello__.spam",
        "__phello__.foo",
        # test_fork1.py
        "fake test module",
        # test_html.py
        "html",
        "html.entities",
        # test_http_cookiejar.py
        "urllib.request",
        "http",
        # test_imp.py
        "importlib.test.import_",
        "pep3147.foo",
        "pep3147",
        # test_import.py
        "RAnDoM",
        "infinite_reload",
        "test_trailing_slash",
        "nonexistent_xyzzy",
        "_parent_foo.bar",
        "_parent_foo",
        "test_unc_path",
        # test_importhooks.py
        "hooktestmodule",
        "hooktestpackage",
        "hooktestpackage.sub",
        "reloadmodule",
        "hooktestpackage.sub.subber",
        "hooktestpackage.oldabs",
        "hooktestpackage.newrel",
        "hooktestpackage.sub.subber.subest",
        "hooktestpackage.futrel",
        "sub",
        "hooktestpackage.newabs",
        # test_imporlib.py"
        "importlib.test.__main__",
        "importlib",
        # test_inspect.py
        "inspect_fodder3",
        "test.test_import",
        # test_imageop.py
        "imgfile",
        # test_json.py
        "json.tests",
        # test_lib2to3.py
        "lib2to3.tests",
        # test_logging.py
        "win32evtlog",
        "win32evtlogutil",
        "pywintypes",
        # test_lzma.py
        "lzma",
        # test_macostools.py
        "macostools",
        # test_msilib.py
        "msilib",
        # test_namespace_pkgs.py
        "foo.one",
        "foo.two",
        "parent.child.one",
        "parent.child.two",
        "parent.child.three",
        "bar.two",
        "a_test",
        "parent.child",
        "parent",
        "bar",
        # test_new.py
        "Spam",
        # test_ossaudiodev.py
        "ossaudiodev",
        # test_pathlib.py
        "pathlib",
        # test_platform.py
        "gestalt",
        # test_pickleable.py
        "email.headerregistry",
        # test_pkg.py
        "t1",
        "t2",
        "t2.sub",
        "t2.sub.subsub",
        "t3.sub.subsub",
        "t5",
        "t6",
        "t7",
        "t7.sub",
        "t7.sub.subsub",
        "t8",
        "t3.sub",
        "t3",
        # test_pkgutil.py
        "foo",
        "foo.bar",
        "foo.baz",
        "zipimport",
        "pkg",
        "pkg.subpkg",
        "pkg.subpkg.c",
        "pkg.subpkg.d",
        # test_policy.py
        "email.policy",
        # test_urllib.py
        "urllib.parse",
        # test_urllib_response.py
        "urllib.response",
        # test_repr.py
        """areallylongpackageandmodulenametotestreprtruncation.\
areallylongpackageandmodulenametotestreprtruncation""",
        "areallylongpackageandmodulenametotestreprtruncation",
        # test_robotparser.py
        "urllib.error",
        "urllib.robotparser",
        # test_runpy.py
        "test.script_helper",
        # test_secrets.py
        "secrets",
        # test_selectors.py
        "selectors",
        # test_statistics.py
        "statistics",
        # test_shelve.py
        "test.test_dbm",
        # test_strftime.py
        "java",
        # test_strop.py
        "strop",
        # test_sqlite3.py
        "sqlite3.test",
        # test_sundry.py
        "distutils.emxccompiler",
        "os2emxpath",
        # test_tcl.py
        "tkinter",
        # test_tk.py
        "runtktests",
        "tkinter.test",
        "tkinter.test.support",
        # test_tools.py
        "analyze_dxp",
        "test_unparse",
        "importlib.machinery",
        # test_traceback.py
        "test_bug737473",
        # test_tracemalloc
        "tracemalloc",
        # test_typing.py
        "mock",
        "typing.io",
        "typing.re",
        # test_unittest.py
        "unittest.test",
        # test_wsgiref.py
        "test.test_httpservers",
        # test_xml_etree.py
        "xml.parsers.expat.errors",
        # test_xmlrpc.py
        "xmlrpc.client",
        # test_zipimport_support.py
        "test_zipped_doctest",
        "zip_pkg",
        # test/test_zipimport_support.py
        "test.test_cmd_line_script",
        # test_winconsoleio.py
        "_testconsole",
        # Python3: modules that no longer exist
        "commands",
        "dummy_thread",
        "_dummy_thread",
        "httplib",
        "Queue",
        "sets",
        # Python2: modules that don't yet exit
        "http.client",
        "queue",
        "winreg",
        # Very old modules with older names
        "simplejson",
        "sets",
        # Standalone mode "site" import flexibilities
        "sitecustomize",
        "usercustomize",
        "apport_python_hook",
        "_frozen_importlib",
        # Standard library stuff that is optional
        "comtypes.server.inprocserver",
        "_tkinter",
        "_scproxy",
        "EasyDialogs",
        "SOCKS",
        "rourl2path",
        "_winapi",
        "win32api",
        "win32con",
        "_gestalt",
        "java.lang",
        "vms_lib",
        "ic",
        "readline",
        "termios",
        "_sysconfigdata",
        "al",
        "AL",
        "sunaudiodev",
        "SUNAUDIODEV",
        "Audio_mac",
        "nis",
        "test.test_MimeWriter",
        "dos",
        "win32pipe",
        "Carbon",
        "Carbon.Files",
        "sgi",
        "ctypes.macholib.dyld",
        "bsddb3",
        "_pybsddb",
        "_xmlrpclib",
        "netbios",
        "win32wnet",
        "email.Parser",
        "elementree.cElementTree",
        "elementree.ElementTree",
        "_gbdm",
        "resource",
        "crypt",
        "bz2",
        "dbm",
        "mmap",
        "Mailman",
        # Mercurial test
        "statprof",
        "email.Generator",
        "email.Utils",
        # setuptools does a lot of speculative stuff
        "wincertstore",
        "setuptools_svn",
        # reportlab does use this if present only and warns about itself.
        "pyfribidi2",
        "macfs",
        # psutils
        "_psutil_windows",
        # nose
        "unittest2",
        "IronPython",
        "clr",
        "compiler.consts",
        "new",
        # pkg_resources
        "pkg_resources.extern",
        "ordereddict",
        # appdirs
        "com",
        "win32com",
        # gtk
        "gdk",
        # six
        "six.moves",
        # Python3 namespace packages.
        "_frozen_importlib_external",
        # Garbage from PyWin32
        "pywin32_bootstrap",
    )


def isIgnoreListedNotExistingModule(module_name):
    if module_name in sys.builtin_module_names:
        raise NuitkaOptimizationError(
            """
Your CPython version has a built-in module '%s', that is not ignore listed
please report this as a bug."""
            % module_name,
        )

    return module_name.hasOneOfNamespaces(getModuleIgnoreList())
