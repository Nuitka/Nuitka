#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

import shutil

from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.PythonVersions import python_version
from nuitka.utils.SharedLibraries import locateDLL
from nuitka.utils.Utils import basename, getOS, joinpath


class NuitkaPluginPopularImplicitImports(NuitkaPluginBase):
    def getImplicitImports(self, full_name):
        # Many variables, branches, due to the many cases, pylint: disable=R0912,R0915
        # TODO: Move this out to some kind of configuration format.
        elements = full_name.split('.')

        if elements[0] in ("PyQt4", "PyQt5"):
            if python_version < 300:
                yield "atexit"

            yield "sip"

            child = elements[1] if len(elements) > 1 else None

            if child in ("QtGui", "QtAssistant", "QtDBus", "QtDeclarative",
                         "QtDesigner", "QtHelp", "QtNetwork", "QtScript",
                         "QtScriptTools", "QtSvg", "QtTest", "QtWebKit",
                         "QtXml", "QtXmlPatterns", "QtPrintSupport",
                         "QtWebKitWidgets"):
                yield elements[0] + ".QtCore"

            if child in ("QtDeclarative", "QtWebKit", "QtXmlPatterns",
                         "QtPrintSupport", "QtWebKitWidgets"):
                yield elements[0] + ".QtNetwork"

            if child == "QtScriptTools":
                yield elements[0] + ".QtScript"

            if child in ("QtWidgets", "QtDeclarative", "QtDesigner", "QtHelp",
                         "QtScriptTools", "QtSvg", "QtTest", "QtWebKit",
                         "QtPrintSupport", "QtWebKitWidgets"):
                yield elements[0] + ".QtGui"

            if full_name in ("PyQt5.QtDesigner", "PyQt5.QtHelp", "PyQt5.QtTest",
                             "PyQt5.QtPrintSupport", "PyQt5.QtSvg",
                             "PyQt5.QtWebKitWidgets"):
                yield "PyQt5.QtWidgets"

            if full_name in ("PyQt5.QtPrintSupport",):
                yield "PyQt5.QtSvg"

            if full_name in ("PyQt5.QtWebKitWidgets",):
                yield "PyQt5.QtWebKit"
                yield "PyQt5.QtPrintSupport"

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
        elif full_name == "reportlab.rl_config":
            yield "reportlab.rl_settings"
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

    module_aliases = {
        "requests.packages.urllib3" : "urllib3",
        "requests.packages.chardet" : "chardet"
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

    def suppressBuiltinImportWarning(self, module_name, source_ref):
        if module_name == "setuptools":
            return True

        return False

    def considerExtraDlls(self, dist_dir, module):
        full_name = module.getFullName()

        if getOS() == "Linux" and full_name == "uuid":
            uuid_dll_path = locateDLL("uuid")
            dist_dll_path = joinpath(dist_dir, basename(uuid_dll_path))

            shutil.copy(uuid_dll_path, dist_dir)

            return (
                (dist_dll_path, None),
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
               module_name.startswith(unworthy_namespace + "."):
                return "bytecode"
