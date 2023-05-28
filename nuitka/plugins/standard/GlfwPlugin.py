#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Support for glfw, details in below class definitions.

"""

import os

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.FileOperations import getFileContentByLine
from nuitka.utils.ModuleNames import ModuleName
from nuitka.utils.Utils import isLinux, isMacOS, isWin32Windows

# spell-checker: ignore glfw,opengl,osmesa,pyglfw,xwayland


class NuitkaPluginGlfw(NuitkaPluginBase):
    """This class represents the main logic of the glfw plugin.

    This is a plugin to ensure that glfw platform specific backends are loading
    properly. This need to include the correct DLL and make sure it's used by
    setting an environment variable.

    """

    # TODO: Maybe rename to opengl maybe
    plugin_name = "glfw"  # Nuitka knows us by this name
    plugin_desc = "Required for OpenGL and 'glfw' package in standalone mode."

    @staticmethod
    def isAlwaysEnabled():
        return True

    @classmethod
    def isRelevant(cls):
        """Check whether plugin might be required.

        Returns:
            True if this is a standalone compilation.
        """
        return Options.isStandaloneMode()

    def getImplicitImports(self, module):
        # Dealing with OpenGL is a bit detailed, pylint: disable=too-many-branches
        if module.getFullName() == "OpenGL":
            opengl_infos = self.queryRuntimeInformationSingle(
                setup_codes="import OpenGL.plugins",
                value="[(f.name, f.import_path) for f in OpenGL.plugins.FormatHandler.all()]",
            )

            # TODO: Filter by name.
            for _name, import_path in opengl_infos:
                yield ModuleName(import_path).getPackageName()

            for line in getFileContentByLine(module.getCompileTimeFilename()):
                line = line.partition("#")[0]

                if line.startswith("PlatformPlugin("):
                    os_part, plugin_name_part = line[15:-1].split(",")
                    os_part = os_part.strip("' ")
                    plugin_name_part = plugin_name_part.strip(") '")
                    plugin_name_part = plugin_name_part[: plugin_name_part.rfind(".")]

                    if os_part == "nt":
                        if isWin32Windows():
                            yield plugin_name_part
                    elif os_part.startswith("linux"):
                        if isLinux():
                            yield plugin_name_part
                    elif os_part.startswith("darwin"):
                        if isMacOS():
                            yield plugin_name_part
                    elif os_part.startswith(
                        ("posix", "osmesa", "egl", "x11", "wayland", "xwayland")
                    ):
                        if not isWin32Windows() and not isMacOS():
                            yield plugin_name_part
                    else:
                        self.sysexit(
                            "Undetected OS specific glfw plugin '%s', please report bug for."
                            % os_part
                        )

    def _getDLLFilename(self):
        glfw_info = self.queryRuntimeInformationMultiple(
            info_name="glfw_info",
            setup_codes="import glfw.library",
            values=(("dll_filename", "glfw.library.glfw._name"),),
        )

        return glfw_info.dll_filename

    def getExtraDlls(self, module):
        if module.getFullName() == "glfw":
            dll_filename = self._getDLLFilename()

            yield self.makeDllEntryPoint(
                source_path=dll_filename,
                dest_path=os.path.join("glfw", os.path.basename(dll_filename)),
                package_name="glfw.library",
                reason="needed by 'glfw'",
            )

    def createPreModuleLoadCode(self, module):
        if module.getFullName() == "glfw":
            dll_filename = self._getDLLFilename()

            code = r"""
import os
os.environ["PYGLFW_LIBRARY"] = os.path.join(__nuitka_binary_dir, "glfw", "%s")
""" % os.path.basename(
                dll_filename
            )
            return (
                code,
                "Setting 'PYGLFW_LIBRARY' environment variable for glfw to find platform DLL.",
            )
