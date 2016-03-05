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
from sys import getfilesystemencoding

from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.PythonVersions import python_version
from nuitka.utils.Utils import basename, getOS, joinpath


class NuitkaPluginPopularImplicitImports(NuitkaPluginBase):
    def getImplicitImports(self, full_name):
        elements = full_name.split('.')

        if elements[0] in ("PyQt4", "PyQt5"):
            if python_version < 300:
                yield "atexit"

            yield "sip"

            child = elements[1] if len(elements) > 1 else None

            if child == "QtGui":
                yield elements[0] + ".QtCore"

            if child == "QtWidgets":
                yield elements[0] + ".QtGui"
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
        elif full_name in ("Tkinter", "tkinter"):
            yield "_tkinter"

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

    def locateDLL(self, dll_name):
        import ctypes.util

        dll_name = ctypes.util.find_library(dll_name)

        import subprocess
        process = subprocess.Popen(
            args   = ["/sbin/ldconfig", "-p"],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
        )
        stdout, _stderr = process.communicate()

        dll_map = {}

        for line in stdout.splitlines()[1:]:
            assert line.count(b"=>") == 1, line
            left, right = line.strip().split(b" => ")
            assert b" (" in left, line
            left = left[:left.rfind(b" (")]

            if python_version >= 300:
                left = left.decode(getfilesystemencoding())
                right = right.decode(getfilesystemencoding())

            if left not in dll_map:
                dll_map[left] = right

        return dll_map[dll_name]

    def considerExtraDlls(self, dist_dir, module):
        full_name = module.getFullName()

        if getOS() == "Linux" and full_name == "uuid":
            uuid_dll_path = self.locateDLL("uuid")
            dist_dll_path = joinpath(dist_dir, basename(uuid_dll_path))

            shutil.copy(uuid_dll_path, dist_dir)

            return (
                (dist_dll_path, None),
            )

        return ()
