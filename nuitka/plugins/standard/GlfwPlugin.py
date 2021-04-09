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
""" Support for glfw, details in below class definitions.

"""

import os

from nuitka import Options
from nuitka.freezer.IncludedEntryPoints import makeDllEntryPoint
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.ModuleNames import ModuleName


class GlfwPlugin(NuitkaPluginBase):
    """This class represents the main logic of the glfw plugin.

    This is a plugin to ensure that glfw platform specific backends are loading
    properly. This need to include the correct DLL and make sure it's used by
    setting an environment variable.

    """

    plugin_name = "glfw"  # Nuitka knows us by this name
    plugin_desc = "Required for glfw in standalone mode"

    @classmethod
    def isRelevant(cls):
        """Check whether plugin might be required.

        Returns:
            True if this is a standalone compilation.
        """
        return Options.isStandaloneMode()

    def getImplicitImports(self, module):
        if module.getFullName() == "OpenGL":
            opengl_infos = self.queryRuntimeInformationSingle(
                setup_codes="import OpenGL.plugins",
                value="[(f.name, f.import_path) for f in OpenGL.plugins.FormatHandler.all()]",
            )

            # TODO: Filter by name.
            for _name, import_path in opengl_infos:
                yield ModuleName(import_path).getPackageName()

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

            yield makeDllEntryPoint(
                source_path=dll_filename,
                dest_path=os.path.join("glfw", os.path.basename(dll_filename)),
                package_name="glfw.library",
            )

    def createPreModuleLoadCode(self, module):
        if module.getFullName() == "glfw":
            dll_filename = self._getDLLFilename()

            code = r"""
import os
os.environ["PYGLFW_LIBRARY"] = os.path.join(__nuitka_binary_dir, "glfw", %r)
""" % os.path.basename(
                dll_filename
            )
            return (
                code,
                "Setting 'PYGLFW_LIBRARY' environment variable for glfw to find platform DLL.",
            )


class GlfwPluginDetector(NuitkaPluginBase):
    """Only used if plugin is NOT activated.

    Notes:
        We are given the chance to issue a warning if we think we may be required.
    """

    detector_for = GlfwPlugin

    @classmethod
    def isRelevant(cls):
        """Check whether plugin might be required.

        Returns:
            True if this is a standalone compilation.
        """
        return Options.isStandaloneMode()

    def onModuleDiscovered(self, module):
        """This method checks whether numpy is required.

        Notes:
            For this we check whether its first name part is numpy relevant.
        Args:
            module: the module object
        Returns:
            None
        """
        if module.getFullName() == "glfw":
            self.warnUnusedPlugin("Missing glfw support.")
