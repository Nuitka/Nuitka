#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Support for delvewheel, details in below class definitions.

"""

import os
import re

from nuitka.Options import isStandaloneMode
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.PythonFlavors import isAnacondaPython
from nuitka.utils.FileOperations import listDllFilesFromDirectory

# spell-checker: ignore delvewheel


class NuitkaPluginDelvewheel(NuitkaPluginBase):
    """This class represents the main logic of the delvewheel plugin.

    This is a plugin to ensure that delvewheel DLLs are loading properly in
    standalone mode. This needed to include the correct DLLs to the correct
    place.
    """

    plugin_name = "delvewheel"  # Nuitka knows us by this name
    plugin_desc = (
        "Required for 'support' of delvewheel using packages in standalone mode."
    )
    plugin_category = "core"

    def __init__(self):
        # Special DLL directories if detected for a module.
        self.dll_directories = {}

        # Temporary variable when capturing current DLL directory of a module.
        self.dll_directory = None

    @staticmethod
    def isAlwaysEnabled():
        return True

    @staticmethod
    def isRelevant():
        return isStandaloneMode()

    # This is used by our exec below, to capture the dll directory without using a free
    # variable.
    def _add_dll_directory(self, arg):
        self.dll_directory = arg

    def onModuleSourceCode(self, module_name, source_filename, source_code):
        # Avoid regular expression match if possible.
        if "_delvewheel_" not in source_code:
            return None

        match = re.search(
            r"(def _delvewheel_(?:init_)?patch_(.*?)\(\):\n.*?_delvewheel_(?:init_)?patch_\2\(\))",
            source_code,
            re.S,
        )

        if not match:
            return None

        delvewheel_version = match.group(2).replace("_", ".")

        code = match.group(1)

        code = code.replace("os.add_dll_directory", "add_dll_directory")
        code = code.replace("sys.version_info[:2] >= (3, 8)", "True")
        code = code.replace("sys.version_info[:2] >= (3, 10)", "True")

        self.dll_directory = None

        # Fake the "__file__" to the proper value to the exec.
        exec_globals = {
            "__file__": source_filename,
            "add_dll_directory": self._add_dll_directory,
        }

        self.dll_directory = None

        # We believe this should be the easiest, pylint: disable=exec-used
        exec(code, exec_globals)

        # Copy it over. For Anaconda we allow exceptions, when it's not an
        # Anaconda package, but a PyPI package, those mixes are acting strange.
        if not isAnacondaPython():
            assert self.dll_directory is not None, module_name

        # At least the "scs" package puts the top level package folder there
        # even with there being no DLLs anywhere, maybe a wrong usage of
        # delvewheel SCS, maybe only on Windows.
        if self.dll_directory is not None:
            self.dll_directory = os.path.normpath(self.dll_directory)

            if os.path.basename(self.dll_directory) in (
                "site-packages",
                "dist-packages",
                "vendor-packages",
            ):
                self.dll_directory = None

        self.dll_directories[module_name] = self.dll_directory

        if self.dll_directories[module_name]:
            self.addModuleInfluencingDetection(
                module_name=module_name,
                detection_name="delvewheel_version",
                detection_value=delvewheel_version,
            )

    def getModuleSpecificDllPaths(self, module_name):
        if module_name in self.dll_directories:
            yield self.dll_directories[module_name]

    def getExtraDlls(self, module):
        full_name = module.getFullName()

        dll_directory = self.dll_directories.get(full_name)

        if dll_directory is not None:
            for dll_filename, dll_basename in listDllFilesFromDirectory(dll_directory):
                yield self.makeDllEntryPoint(
                    source_path=dll_filename,
                    dest_path=os.path.join(
                        os.path.basename(dll_directory), dll_basename
                    ),
                    module_name=full_name,
                    package_name=full_name,
                    reason="needed by '%s'" % full_name.asString(),
                )


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
