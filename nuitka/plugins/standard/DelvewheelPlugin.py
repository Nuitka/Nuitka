#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Support for pyzmq, details in below class definitions.

"""

import os
import re

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.FileOperations import getFileList

# spell-checker: ignore delvewheel,pyzmq


class NuitkaPluginZmq(NuitkaPluginBase):
    """This class represents the main logic of the delvewheel plugin.

    This is a plugin to ensure that delvewheel DLLs are loading properly in
    standalone mode. This needed to include the correct DLLs to the correct
    place.
    """

    plugin_name = "delvewheel"  # Nuitka knows us by this name
    plugin_desc = "Required for support of delvewheel using packages in standalone mode"

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
        return Options.isStandaloneMode()

    # This is used by our exec below, to capture the dll directory without using a free
    # variable.
    def _add_dll_directory(self, arg):
        self.dll_directory = arg

    def onModuleSourceCode(self, module_name, source_code):
        # Avoid regular expression match if possible.
        if "_delvewheel_init_patch" not in source_code:
            return None

        match = re.search(
            r"(def _delvewheel_init_patch_(.*?)\(\):\n.*?_delvewheel_init_patch_\2\(\))",
            source_code,
            re.S,
        )

        if not match:
            return None

        delvewheel_version = match.group(2).replace("_", ".")

        self.info(
            "Detected usage of 'delvewheel' version '%s' in module '%s'."
            % (delvewheel_version, module_name.asString())
        )

        code = match.group(1)

        code = code.replace("os.add_dll_directory", "add_dll_directory")
        code = code.replace("sys.version_info[:2] >= (3, 8)", "True")

        self.dll_directory = None

        # Fake the "__file__" to the proper value to the exec.
        exec_globals = {
            "__file__": self.locateModule(module_name) + "\\__init__.py",
            "add_dll_directory": self._add_dll_directory,
        }

        self.dll_directory = None

        # We believe this should be the easiest, pylint: disable=exec-used
        exec(code, exec_globals)

        # Copy it over.
        assert self.dll_directory is not None, module_name
        self.dll_directories[module_name] = self.dll_directory

    def getExtraDlls(self, module):
        full_name = module.getFullName()

        dll_directory = self.dll_directories.get(full_name)

        if dll_directory is not None:
            for dll_filename in getFileList(dll_directory):
                yield self.makeDllEntryPoint(
                    source_path=dll_filename,
                    dest_path=os.path.join(
                        os.path.basename(dll_directory), os.path.basename(dll_filename)
                    ),
                    package_name=full_name,
                    reason="needed by '%s'" % full_name.asString(),
                )
