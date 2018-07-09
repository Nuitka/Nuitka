#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Standard plug-in to tell Nuitka about implicit imports.

When C extension modules import other modules, we cannot see this and need to
be told that. This encodes the knowledge we have for various modules. Feel free
to add to this and submit patches to make it more complete.
"""

import os
import shutil

from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.PythonVersions import python_version
from nuitka.utils.SharedLibraries import locateDLL
from nuitka.utils.Utils import getOS


class NuitkaPluginPopularImplicitImports(NuitkaPluginBase):
    def __init__(self):
        NuitkaPluginBase.__init__(self)

        self.pkg_utils_externals = None

    def isRequiredImplicitImport(self, module, full_name):
        if full_name == "_tkinter":
            return False

        if full_name.startswith("pkg_resources._vendor"):
            return False

        if module.isPythonShlibModule():
            if full_name in module.getUsedModules():
                return False

        if full_name == "gi._gobject":
            return False

        # Can be built-in.
        if full_name == "_socket":
            return False

        return True


    def getImplicitImports(self, module):
        # Many variables, branches, due to the many cases, pylint: disable=too-many-branches,too-many-statements
        full_name = module.getFullName()

        if module.isPythonShlibModule():
            for used_module in module.getUsedModules():
                yield used_module

        # TODO: Move this out to some kind of configuration format.
        elements = full_name.split('.')

        if elements[0] in ("PyQt4", "PyQt5"):
            if python_version < 300:
                yield "atexit"

            yield "sip"

            child = elements[1] if len(elements) > 1 else None

            if child in ("QtGui", "QtAssistant", "QtDBus", "QtDeclarative",
                         "QtSql", "QtDesigner", "QtHelp", "QtNetwork",
                         "QtScript", "QtQml", "QtScriptTools", "QtSvg",
                         "QtTest", "QtWebKit", "QtOpenGL", "QtXml",
                         "QtXmlPatterns", "QtPrintSupport", "QtNfc",
                         "QtWebKitWidgets", "QtBluetooth", "QtMultimediaWidgets",
                         "QtQuick", "QtWebChannel", "QtWebSockets", "QtX11Extras",
                         "_QOpenGLFunctions_2_0", "_QOpenGLFunctions_2_1",
                         "_QOpenGLFunctions_4_1_Core"):
                yield elements[0] + ".QtCore"

            if child in ("QtDeclarative", "QtWebKit", "QtXmlPatterns", "QtQml",
                         "QtPrintSupport", "QtWebKitWidgets", "QtMultimedia",
                         "QtMultimediaWidgets", "QtQuick", "QtQuickWidgets",
                         "QtWebSockets"):
                yield elements[0] + ".QtNetwork"

            if child == "QtScriptTools":
                yield elements[0] + ".QtScript"

            if child in ("QtWidgets", "QtDeclarative", "QtDesigner", "QtHelp",
                         "QtScriptTools", "QtSvg", "QtTest", "QtWebKit",
                         "QtPrintSupport", "QtWebKitWidgets", "QtMultimedia",
                         "QtMultimediaWidgets", "QtOpenGL", "QtQuick",
                         "QtQuickWidgets", "QtSql", "_QOpenGLFunctions_2_0",
                         "_QOpenGLFunctions_2_1", "_QOpenGLFunctions_4_1_Core"):
                yield elements[0] + ".QtGui"

            if full_name in ("PyQt5.QtDesigner", "PyQt5.QtHelp", "PyQt5.QtTest",
                             "PyQt5.QtPrintSupport", "PyQt5.QtSvg", "PyQt5.QtOpenGL",
                             "PyQt5.QtWebKitWidgets", "PyQt5.QtMultimediaWidgets",
                             "PyQt5.QtQuickWidgets", "PyQt5.QtSql"):
                yield "PyQt5.QtWidgets"

            if full_name in ("PyQt5.QtPrintSupport",):
                yield "PyQt5.QtSvg"

            if full_name in ("PyQt5.QtWebKitWidgets",):
                yield "PyQt5.QtWebKit"
                yield "PyQt5.QtPrintSupport"

            if full_name in ("PyQt5.QtMultimediaWidgets",):
                yield "PyQt5.QtMultimedia"

            if full_name in ("PyQt5.QtQuick", "PyQt5.QtQuickWidgets"):
                yield "PyQt5.QtQml"

            if full_name in ("PyQt5.QtQuickWidgets", "PyQt5.QtQml"):
                yield "PyQt5.QtQuick"

            if full_name == "PyQt5.Qt":
                yield "PyQt5.QtCore"
                yield "PyQt5.QtDBus"
                yield "PyQt5.QtGui"
                yield "PyQt5.QtNetwork"
                yield "PyQt5.QtNetworkAuth"
                yield "PyQt5.QtSensors"
                yield "PyQt5.QtSerialPort"
                yield "PyQt5.QtMultimedia"
                yield "PyQt5.QtQml"
                yield "PyQt5.QtWidgets"


        elif full_name == "PySide.QtDeclarative":
            yield "PySide.QtGui"
        elif full_name == "PySide.QtHelp":
            yield "PySide.QtGui"
        elif full_name == "PySide.QtOpenGL":
            yield "PySide.QtGui"
        elif full_name == "PySide.QtScriptTools":
            yield "PySide.QtScript"
            yield "PySide.QtGui"
        elif full_name == "PySide.QtSql":
            yield "PySide.QtGui"
        elif full_name == "PySide.QtSvg":
            yield "PySide.QtGui"
        elif full_name == "PySide.QtTest":
            yield "PySide.QtGui"
        elif full_name == "PySide.QtUiTools":
            yield "PySide.QtGui"
            yield "PySide.QtXml"
        elif full_name == "PySide.QtWebKit":
            yield "PySide.QtGui"
        elif full_name == "PySide.phonon":
            yield "PySide.QtGui"
        elif full_name == "lxml.etree":
            yield "gzip"
            yield "lxml._elementpath"
        elif full_name == "gtk._gtk":
            yield "pangocairo"
            yield "pango"
            yield "cairo"
            yield "gio"
            yield "atk"
        elif full_name == "atk":
            yield "gobject"
        elif full_name == "gtkunixprint":
            yield "gobject"
            yield "cairo"
            yield "gtk"
        elif full_name == "pango":
            yield "gobject"
        elif full_name == "pangocairo":
            yield "pango"
            yield "cairo"
        elif full_name == "reportlab.rl_config":
            yield "reportlab.rl_settings"
        elif full_name == "socket":
            yield "_socket"
        elif full_name == "ctypes":
            yield "_ctypes"
        elif full_name == "gi._gi":
            yield "gi._error"
        elif full_name == "gi._gi_cairo":
            yield "cairo"
        elif full_name == "cairo._cairo":
            yield "gi._gobject"
        elif full_name in ("Tkinter", "tkinter"):
            yield "_tkinter"
        elif full_name in ("cryptography.hazmat.bindings._openssl",
                           "cryptography.hazmat.bindings._constant_time",
                           "cryptography.hazmat.bindings._padding"):
            yield "_cffi_backend"
        elif full_name.startswith("cryptography._Cryptography_cffi_"):
            yield "_cffi_backend"
        elif full_name == "bcrypt._bcrypt":
            yield "_cffi_backend"
        elif full_name == "nacl._sodium":
            yield "_cffi_backend"
        elif full_name == "_dbus_glib_bindings":
            yield "_dbus_bindings"
        elif full_name == "_mysql":
            yield "_mysql_exceptions"
        elif full_name == "lxml.objectify":
            yield "lxml.etree"
        elif full_name == "_yaml":
            yield "yaml"
        elif full_name == "apt_inst":
            yield "apt_pkg"
        elif full_name == "PIL._imagingtk":
            yield "PIL._tkinter_finder"
        elif full_name == "pkg_resources.extern":
            if self.pkg_utils_externals is None:
                for line in open(module.getCompileTimeFilename()):
                    if line.startswith("names"):
                        line = line.split('=')[-1].strip()
                        parts = line.split(',')

                        self.pkg_utils_externals = [
                            part.strip("' ")
                            for part in
                            parts
                        ]

                        break
                else:
                    self.pkg_utils_externals = ()

            for pkg_util_external in self.pkg_utils_externals:
                yield "pkg_resources._vendor." + pkg_util_external
        elif full_name == "pkg_resources._vendor.packaging":
            yield "pkg_resources._vendor.packaging.version"
            yield "pkg_resources._vendor.packaging.specifiers"
            yield "pkg_resources._vendor.packaging.requirements"


    # We don't care about line length here, pylint: disable=line-too-long

    module_aliases = {
        "six.moves.builtins" : "__builtin__" if python_version < 300 else "builtins",
        "six.moves.configparser" : "ConfigParser" if python_version < 300 else "configparser",
        "six.moves.copyreg" : "copy_reg" if python_version < 300 else "copyreg",
        "six.moves.dbm_gnu" : "gdbm" if python_version < 300 else "dbm.gnu",
        "six.moves._dummy_thread" : "dummy_thread" if python_version < 300 else "_dummy_thread",
        "six.moves.http_cookiejar" : "cookielib"  if python_version < 300 else "http.cookiejar",
        "six.moves.http_cookies" : "Cookie" if python_version < 300 else "http.cookies",
        "six.moves.html_entities" : "htmlentitydefs" if python_version < 300 else "html.entities",
        "six.moves.html_parser" : "HTMLParser" if python_version < 300 else "html.parser",
        "six.moves.http_client" : "httplib"  if python_version < 300 else "http.client",
        "six.moves.email_mime_multipart" : "email.MIMEMultipart" if python_version < 300 else "email.mime.multipart",
        "six.moves.email_mime_nonmultipart" : "email.MIMENonMultipart"  if python_version < 300 else "email.mime.nonmultipart",
        "six.moves.email_mime_text" : "email.MIMEText" if python_version < 300 else "email.mime.text",
        "six.moves.email_mime_base" : "email.MIMEBase" if python_version < 300 else "email.mime.base",
        "six.moves.BaseHTTPServer" : "BaseHTTPServer" if python_version < 300 else "http.server",
        "six.moves.CGIHTTPServer" : "CGIHTTPServer" if python_version < 300 else "http.server",
        "six.moves.SimpleHTTPServer" : "SimpleHTTPServer" if python_version < 300 else "http.server",
        "six.moves.cPickle" : "cPickle" if python_version < 300 else "pickle",
        "six.moves.queue" : "Queue" if python_version < 300 else "queue",
        "six.moves.reprlib" :"repr" if python_version < 300 else "reprlib",
        "six.moves.socketserver" : "SocketServer" if python_version < 300 else "socketserver",
        "six.moves._thread" : "thread" if python_version < 300 else "_thread",
        "six.moves.tkinter" :"Tkinter" if python_version < 300 else "tkinter",
        "six.moves.tkinter_dialog" : "Dialog" if python_version < 300 else "tkinter.dialog",
        "six.moves.tkinter_filedialog" : "FileDialog" if python_version < 300 else "tkinter.filedialog",
        "six.moves.tkinter_scrolledtext" : "ScrolledText" if python_version < 300 else "tkinter.scrolledtext",
        "six.moves.tkinter_simpledialog" : "SimpleDialog" if python_version < 300 else "tkinter.simpledialog",
        "six.moves.tkinter_tix" : "Tix" if python_version < 300 else "tkinter.tix",
        "six.moves.tkinter_ttk" :"ttk" if python_version < 300 else "tkinter.ttk",
        "six.moves.tkinter_constants" :"Tkconstants" if python_version < 300 else "tkinter.constants",
        "six.moves.tkinter_dnd" : "Tkdnd" if python_version < 300 else "tkinter.dnd",
        "six.moves.tkinter_colorchooser" : "tkColorChooser" if python_version < 300 else "tkinter_colorchooser",
        "six.moves.tkinter_commondialog" : "tkCommonDialog" if python_version < 300 else "tkinter_commondialog",
        "six.moves.tkinter_tkfiledialog" : "tkFileDialog" if python_version < 300 else "tkinter.filedialog",
        "six.moves.tkinter_font" : "tkFont" if python_version < 300 else "tkinter.font",
        "six.moves.tkinter_messagebox" : "tkMessageBox" if python_version < 300 else "tkinter.messagebox",
        "six.moves.tkinter_tksimpledialog" :"tkSimpleDialog" if python_version < 300 else "tkinter_tksimpledialog",
        "six.moves.urllib_parse" : None if python_version < 300 else "urllib.parse",
        "six.moves.urllib_error" : None if python_version < 300 else "urllib.error",
        "six.moves.urllib_robotparser" :"robotparser" if python_version < 300 else "urllib.robotparser",
        "six.moves.xmlrpc_client" :"xmlrpclib" if python_version < 300 else "xmlrpc.client",
        "six.moves.xmlrpc_server" :"SimpleXMLRPCServer" if python_version < 300 else "xmlrpc.server",
        "six.moves.winreg" : "_winreg" if python_version < 300 else "winreg",

        "requests.packages.urllib3" : "urllib3",
        "requests.packages.urllib3.contrib" : "urllib3.contrib",
        "requests.packages.urllib3.contrib.pyopenssl" : "urllib3.contrib.pyopenssl",
        "requests.packages.urllib3.contrib.ntlmpool" : "urllib3.contrib.ntlmpool",
        "requests.packages.urllib3.contrib.socks" : "urllib3.contrib.socks",
        "requests.packages.urllib3.exceptions" : "urllib3.exceptions",
        "requests.packages.urllib3._collections" : "urllib3._collections",
        "requests.packages.chardet" : "chardet",
        "requests.packages.idna"    : "idna",
        "requests.packages.urllib3.packages" : "urllib3.packages",
        "requests.packages.urllib3.packages.ordered_dict" : "urllib3.packages.ordered_dict",
        "requests.packages.urllib3.packages.ssl_match_hostname" : "urllib3.packages.ssl_match_hostname",
        "requests.packages.urllib3.packages.ssl_match_hostname._implementation" : "urllib3.packages.ssl_match_hostname._implementation",
        "requests.packages.urllib3.connectionpool" : "urllib3.connectionpool",
        "requests.packages.urllib3.connection" : "urllib3.connection",
        "requests.packages.urllib3.filepost" : "urllib3.filepost",
        "requests.packages.urllib3.request" : "urllib3.request",
        "requests.packages.urllib3.response" : "urllib3.response",
        "requests.packages.urllib3.fields" : "urllib3.fields",
        "requests.packages.urllib3.poolmanager" : "urllib3.poolmanager",
        "requests.packages.urllib3.util" : "urllib3.util",
        "requests.packages.urllib3.util.connection" : "urllib3.util.connection",
        "requests.packages.urllib3.util.request" : "urllib3.util.request",
        "requests.packages.urllib3.util.response" : "urllib3.util.response",
        "requests.packages.urllib3.util.retry" : "urllib3.util.retry",
        "requests.packages.urllib3.util.ssl_" : "urllib3.util.ssl_",
        "requests.packages.urllib3.util.timeout" : "urllib3.util.timeout",
        "requests.packages.urllib3.util.url" : "urllib3.util.url",
    }

    def onModuleSourceCode(self, module_name, source_code):
        if module_name == "numexpr.cpuinfo":

            # We cannot intercept "is" tests, but need it to be "isinstance",
            # so we patch it on the file. TODO: This is only temporary, in
            # the future, we may use optimization that understands the right
            # hand size of the "is" argument well enough to allow for our
            # type too.
            return source_code.replace(
                "type(attr) is types.MethodType",
                "isinstance(attr, types.MethodType)"
            )


        # Do nothing by default.
        return source_code

    def suppressBuiltinImportWarning(self, module, source_ref):
        if module.getFullName() in ("setuptools", "six"):
            return True

        return False

    def considerExtraDlls(self, dist_dir, module):
        full_name = module.getFullName()

        if getOS() == "Linux" and full_name == "uuid":
            uuid_dll_path = locateDLL("uuid")
            dist_dll_path = os.path.join(dist_dir, os.path.basename(uuid_dll_path))

            shutil.copy(uuid_dll_path, dist_dir)

            return (
                (uuid_dll_path, dist_dll_path, None),
            )

        return ()

    unworthy_namespaces = (
        "setuptools",      # Not performance relevant.
        "distutils",       # Not performance relevant.
        "pkg_resources",   # Not performance relevant.
        "numpy.distutils", # Largely unused, and a lot of modules.
        "numpy.f2py",      # Mostly unused, only numpy.distutils import it.
        "numpy.testing",   # Useless.
        "nose",            # Not performance relevant.
        "coverage",        # Not performance relevant.
        "docutils",        # Not performance relevant.
        "pexpect",         # Not performance relevant.
        "Cython",          # Mostly unused, and a lot of modules.
        "cython",
        "pyximport",
        "IPython",         # Mostly unused, and a lot of modules.
        "wx._core",        # Too large generated code
    )

    def decideCompilation(self, module_name, source_ref):
        for unworthy_namespace in self.unworthy_namespaces:
            if module_name == unworthy_namespace or \
               module_name.startswith(unworthy_namespace + '.'):
                return "bytecode"
