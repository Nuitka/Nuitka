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
""" Support for pyzmq, details in below class definitions.

"""

import os
import re
import shutil

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.FileOperations import getFileList
from nuitka.utils.Importing import getSharedLibrarySuffix
from nuitka.utils.Utils import isWin32Windows


class NuitkaPluginZmq(NuitkaPluginBase):
    """This class represents the main logic of the pyzmq plugin.

    This is a plugin to ensure that gldw platform specific backends are loading
    properly. This need to include the correct DLL and make sure it's used by
    setting an environment variable.

    """

    plugin_name = "pyzmq"  # Nuitka knows us by this name
    plugin_desc = "Required for pyzmq in standalone mode"

    def __init__(self):
        # Special DLL directory if detected.
        self.dll_directory = None

    @staticmethod
    def isAlwaysEnabled():
        return True

    @staticmethod
    def getImplicitImports(module):
        module_name = module.getFullName()

        if module_name == "zmq.backend":
            yield "zmq.backend.cython"

    def considerExtraDlls(self, dist_dir, module):
        module_name = module.getFullName()

        if module_name == "zmq.libzmq" and isWin32Windows():
            # TODO: Very strange thing for zmq on Windows, needs the .pyd file in wrong dir too. Have
            # this done in a dedicated form somewhere.
            shutil.copyfile(
                os.path.join(dist_dir, "zmq\\libzmq.pyd"),
                os.path.join(
                    dist_dir, "libzmq" + getSharedLibrarySuffix(preferred=True)
                ),
            )

        return NuitkaPluginBase.considerExtraDlls(
            self, dist_dir=dist_dir, module=module
        )

    def _add_dll_directory(self, arg):
        self.dll_directory = arg

    def onModuleSourceCode(self, module_name, source_code):
        if module_name == "zmq" and Options.isStandaloneMode():
            # TODO: Make the anti-bloat engine to this.

            if "_delvewheel_init_patch" in source_code:
                match = re.search(
                    r"(def _delvewheel_init_patch_(.*?)\(\):\n.*?_delvewheel_init_patch_\2\(\))",
                    source_code,
                    re.S,
                )

                delvewheel_version = match.group(2).replace("_", ".")

                self.info(
                    "Detected usage of 'delvewheel' version %r." % delvewheel_version
                )

                code = match.group(1)

                code = code.replace("os.add_dll_directory", "add_dll_directory")
                code = code.replace("sys.version_info[:2] >= (3, 8)", "True")

                # Fake the __file__ to the proper value.
                exec_globals = {
                    "__file__": self.locateModule(module_name) + "\\__init__.py",
                    "add_dll_directory": self._add_dll_directory,
                }

                # We believe this should be the easiest, pylint: disable=exec-used
                exec(code, exec_globals)

    def getExtraDlls(self, module):
        if module.getFullName() == "zmq" and self.dll_directory is not None:
            for dll_filename in getFileList(self.dll_directory):
                yield self.makeDllEntryPoint(
                    source_path=dll_filename,
                    dest_path=os.path.join(
                        "pyzmq.libs", os.path.basename(dll_filename)
                    ),
                    package_name="zmq",
                )
