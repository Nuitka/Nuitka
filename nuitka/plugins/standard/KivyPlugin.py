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
""" Details see below in class definition.
"""

from nuitka.Options import isStandaloneMode
from nuitka.plugins.PluginBase import NuitkaPluginBase


class NuitkaPluginKivy(NuitkaPluginBase):
    """This class represents the main logic of the plugin."""

    plugin_name = "kivy"
    plugin_desc = "Required by 'kivy' package."

    @staticmethod
    def isAlwaysEnabled():
        return True

    @classmethod
    def isRelevant(cls):
        """One time only check: may this plugin be required?

        Returns:
            True if this is a standalone compilation.
        """
        return isStandaloneMode()

    def _getKivyInformation(self):
        setup_codes = r"""
import kivy.core.image
import kivy.core.text
# Prevent Window from being created at compile time.
kivy.core.core_select_lib=(lambda *args, **kwargs: None)
import kivy.core.window

# Kivy has packages designed to provide these on Windows
try:
    from kivy_deps.sdl2 import dep_bins as sdl2_dep_bins
except ImportError:
    sdl2_dep_bins = []
try:
    from kivy_deps.glew import dep_bins as glew_dep_bins
except ImportError:
    glew_dep_bins = []
"""
        info = self.queryRuntimeInformationMultiple(
            info_name="kivy_info",
            setup_codes=setup_codes,
            values=(
                ("libs_loaded", "kivy.core.image.libs_loaded"),
                ("window_impl", "kivy.core.window.window_impl"),
                ("label_libs", "kivy.core.text.label_libs"),
                ("sdl2_dep_bins", "sdl2_dep_bins"),
                ("glew_dep_bins", "glew_dep_bins"),
            ),
        )

        if info is None:
            self.sysexit("Error, it seems Kivy is not installed.")

        return info

    def getImplicitImports(self, module):
        # Using branches to dispatch, pylint: disable=too-many-branches

        full_name = module.getFullName()

        if full_name == "kivy.core.image":
            for module_name in self._getKivyInformation().libs_loaded:
                yield full_name.getChildNamed(module_name)
        elif full_name == "kivy.core.window":
            # TODO: It seems only one is actually picked, so this could be made
            # to also reflect decision making.
            for _, module_name, _ in self._getKivyInformation().window_impl:
                yield full_name.getChildNamed(module_name)
        elif full_name == "kivy.core.text":
            for _, module_name, _ in self._getKivyInformation().label_libs:
                yield full_name.getChildNamed(module_name)
        elif full_name == "kivy.core.window.window_sdl2":
            yield "kivy.core.window._window_sdl2"
        elif full_name == "kivy.core.window._window_sdl2":
            yield "kivy.core.window.window_info"
        elif full_name == "kivy.core.window.window_x11":
            yield "kivy.core.window.window_info"
        elif full_name == "kivy.graphics.cgl":
            yield "kivy.graphics.cgl_backend"
        elif full_name == "kivy.graphics.cgl_backend":
            yield "kivy.graphics.cgl_backend.cgl_glew"
        elif full_name == "kivy.graphics.cgl_backend.cgl_glew":
            yield "kivy.graphics.cgl_backend.cgl_gl"
        elif full_name == "kivymd.app":
            yield self.locateModules("kivymd.uix")

    def getExtraDlls(self, module):
        """Copy extra shared libraries or data for this installation.

        Args:
            module: module object
        Yields:
            DLL entry point objects
        """

        full_name = module.getFullName()

        if full_name == "kivy":
            kivy_info = self._getKivyInformation()

            kivy_dlls = []
            for dll_folder in kivy_info.sdl2_dep_bins + kivy_info.glew_dep_bins:
                kivy_dlls.extend(self.locateDLLsInDirectory(dll_folder))

            for full_path, target_filename, _dll_extension in kivy_dlls:
                yield self.makeDllEntryPoint(
                    source_path=full_path,
                    dest_path=target_filename,
                    package_name=full_name,
                    reason="needed by 'kivy'",
                )

            self.reportFileCount(full_name, len(kivy_dlls))
