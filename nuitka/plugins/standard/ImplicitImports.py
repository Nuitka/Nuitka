#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
        self.opengl_plugins = None

    def getImplicitImports(self, module):
        # Many variables, branches, due to the many cases, pylint: disable=too-many-branches,too-many-statements
        full_name = module.getFullName()

        if module.isPythonShlibModule():
            for used_module in module.getUsedModules():
                yield used_module[0], False

        # TODO: Move this out to some kind of configuration format.
        elements = full_name.split('.')

        if elements[0] in ("PyQt4", "PyQt5"):
            if python_version < 300:
                yield "atexit", True

            # These are alternatives now:
            # TODO: One day it should avoid including both.
            yield "sip", False
            if elements[0] == "PyQt5":
                yield "PyQt5.sip", False

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
                yield elements[0] + ".QtCore", True

            if child in ("QtDeclarative", "QtWebKit", "QtXmlPatterns", "QtQml",
                         "QtPrintSupport", "QtWebKitWidgets", "QtMultimedia",
                         "QtMultimediaWidgets", "QtQuick", "QtQuickWidgets",
                         "QtWebSockets"):
                yield elements[0] + ".QtNetwork", True

            if child == "QtScriptTools":
                yield elements[0] + ".QtScript", True

            if child in ("QtWidgets", "QtDeclarative", "QtDesigner", "QtHelp",
                         "QtScriptTools", "QtSvg", "QtTest", "QtWebKit",
                         "QtPrintSupport", "QtWebKitWidgets", "QtMultimedia",
                         "QtMultimediaWidgets", "QtOpenGL", "QtQuick",
                         "QtQuickWidgets", "QtSql", "_QOpenGLFunctions_2_0",
                         "_QOpenGLFunctions_2_1", "_QOpenGLFunctions_4_1_Core"):
                yield elements[0] + ".QtGui", True

            if full_name in ("PyQt5.QtDesigner", "PyQt5.QtHelp", "PyQt5.QtTest",
                             "PyQt5.QtPrintSupport", "PyQt5.QtSvg", "PyQt5.QtOpenGL",
                             "PyQt5.QtWebKitWidgets", "PyQt5.QtMultimediaWidgets",
                             "PyQt5.QtQuickWidgets", "PyQt5.QtSql"):
                yield "PyQt5.QtWidgets", True

            if full_name in ("PyQt5.QtPrintSupport",):
                yield "PyQt5.QtSvg", True

            if full_name in ("PyQt5.QtWebKitWidgets",):
                yield "PyQt5.QtWebKit", True
                yield "PyQt5.QtPrintSupport", True

            if full_name in ("PyQt5.QtMultimediaWidgets",):
                yield "PyQt5.QtMultimedia", True

            if full_name in ("PyQt5.QtQuick", "PyQt5.QtQuickWidgets"):
                yield "PyQt5.QtQml", True

            if full_name in ("PyQt5.QtQuickWidgets", "PyQt5.QtQml"):
                yield "PyQt5.QtQuick", True

            if full_name == "PyQt5.Qt":
                yield "PyQt5.QtCore", True
                yield "PyQt5.QtDBus", True
                yield "PyQt5.QtGui", True
                yield "PyQt5.QtNetwork", True
                yield "PyQt5.QtNetworkAuth", False
                yield "PyQt5.QtSensors", False
                yield "PyQt5.QtSerialPort", False
                yield "PyQt5.QtMultimedia", True
                yield "PyQt5.QtQml", False
                yield "PyQt5.QtWidgets", True
        elif full_name == "sip" and python_version < 300:
            yield "enum", False
        elif full_name == "PySide.QtDeclarative":
            yield "PySide.QtGui", True
        elif full_name == "PySide.QtHelp":
            yield "PySide.QtGui", True
        elif full_name == "PySide.QtOpenGL":
            yield "PySide.QtGui", True
        elif full_name == "PySide.QtScriptTools":
            yield "PySide.QtScript", True
            yield "PySide.QtGui", True
        elif full_name == "PySide.QtSql":
            yield "PySide.QtGui", True
        elif full_name == "PySide.QtSvg":
            yield "PySide.QtGui", True
        elif full_name == "PySide.QtTest":
            yield "PySide.QtGui", True
        elif full_name == "PySide.QtUiTools":
            yield "PySide.QtGui", True
            yield "PySide.QtXml", True
        elif full_name == "PySide.QtWebKit":
            yield "PySide.QtGui", True
        elif full_name == "PySide.phonon":
            yield "PySide.QtGui", True
        elif full_name == "lxml.etree":
            yield "gzip", True
            yield "lxml._elementpath", True
        elif full_name == "gtk._gtk":
            yield "pangocairo", True
            yield "pango", True
            yield "cairo", True
            yield "gio", True
            yield "atk", True
        elif full_name == "atk":
            yield "gobject", True
        elif full_name == "gtkunixprint":
            yield "gobject", True
            yield "cairo", True
            yield "gtk", True
        elif full_name == "pango":
            yield "gobject", True
        elif full_name == "pangocairo":
            yield "pango", True
            yield "cairo", True
        elif full_name == "reportlab.rl_config":
            yield "reportlab.rl_settings", True
        elif full_name == "socket":
            yield "_socket", False
        elif full_name == "ctypes":
            yield "_ctypes", True
        elif full_name == "gi._gi":
            yield "gi._error", True
        elif full_name == "gi._gi_cairo":
            yield "cairo", True
        elif full_name == "cairo._cairo":
            yield "gi._gobject", False
        elif full_name in ("Tkinter", "tkinter"):
            yield "_tkinter", False
        elif full_name in ("cryptography.hazmat.bindings._openssl",
                           "cryptography.hazmat.bindings._constant_time",
                           "cryptography.hazmat.bindings._padding"):
            yield "_cffi_backend", True
        elif full_name.startswith("cryptography._Cryptography_cffi_"):
            yield "_cffi_backend", True
        elif full_name == "bcrypt._bcrypt":
            yield "_cffi_backend", True
        elif full_name == "nacl._sodium":
            yield "_cffi_backend", True
        elif full_name == "_dbus_glib_bindings":
            yield "_dbus_bindings", True
        elif full_name == "_mysql":
            yield "_mysql_exceptions", True
        elif full_name == "lxml.objectify":
            yield "lxml.etree", True
        elif full_name == "_yaml":
            yield "yaml", True
        elif full_name == "apt_inst":
            yield "apt_pkg", True
        elif full_name == "PIL._imagingtk":
            yield "PIL._tkinter_finder", True
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
                yield "pkg_resources._vendor." + pkg_util_external, False
        elif full_name == "pkg_resources._vendor.packaging":
            yield "pkg_resources._vendor.packaging.version", True
            yield "pkg_resources._vendor.packaging.specifiers", True
            yield "pkg_resources._vendor.packaging.requirements", True
        elif full_name == "uvloop.loop":
            yield "uvloop._noop", True
        elif full_name == "fitz.fitz":
            yield "fitz._fitz", True
        elif full_name == "pandas._libs":
            yield "pandas._libs.tslibs.np_datetime", False
            yield "pandas._libs.tslibs.nattype", False
        elif full_name == "pandas.core.window":
            yield "pandas._libs.skiplist", False
        elif full_name == "zmq.backend":
            yield "zmq.backend.cython", True
        elif full_name == "OpenGL":
            if self.opengl_plugins is None:
                self.opengl_plugins = []

                for line in open(module.getCompileTimeFilename()):
                    if line.startswith("PlatformPlugin("):
                        os_part, plugin_name_part = line[15:-1].split(',')
                        os_part = os_part.strip("' ")
                        plugin_name_part = plugin_name_part.strip(") '")
                        plugin_name_part = plugin_name_part[:plugin_name_part.rfind('.')]
                        if os_part == "nt":
                            if getOS() == "Windows":
                                self.opengl_plugins.append(plugin_name_part)
                        elif os_part.startswith("linux"):
                            if getOS() == "Linux":
                                self.opengl_plugins.append(plugin_name_part)
                        elif os_part.startswith("darwin"):
                            if getOS() == "Darwin":
                                self.opengl_plugins.append(plugin_name_part)
                        elif os_part.startswith(("posix", "osmesa", "egl")):
                            if getOS() != "Windows":
                                self.opengl_plugins.append(plugin_name_part)
                        else:
                            assert False, os_part

            for opengl_plugin in self.opengl_plugins:
                yield opengl_plugin, True


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

        if full_name == "uuid" and getOS() == "Linux":
            uuid_dll_path = locateDLL("uuid")
            dist_dll_path = os.path.join(dist_dir, os.path.basename(uuid_dll_path))

            shutil.copy(uuid_dll_path, dist_dll_path)

            return (
                (uuid_dll_path, dist_dll_path, None),
            )

        return ()

    unworthy_namespaces = (
        "setuptools",      # Not performance relevant.
        "distutils",       # Not performance relevant.
        "wheel",           # Not performance relevant.
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
