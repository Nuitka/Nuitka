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
""" Support for gi typelib files
"""
import os

from nuitka import Options
from nuitka.freezer.IncludedDataFiles import makeIncludedDataDirectory
from nuitka.plugins.PluginBase import NuitkaPluginBase


def _isGiModule(module):
    full_name = module.getFullName()
    return full_name == "gi"


class NuitkaPluginGi(NuitkaPluginBase):
    plugin_name = "gi"
    plugin_desc = "Support for GI dependencies"

    @classmethod
    def isRelevant(cls):
        """This method is called one time only to check, whether the plugin might make sense at all.

        Returns:
            True if this is a standalone compilation.
        """
        return Options.isStandaloneMode()

    @staticmethod
    def createPreModuleLoadCode(module):
        """Add typelib search path"""

        if _isGiModule(module):
            code = r"""
import os
if not os.environ.get("GI_TYPELIB_PATH="):
    os.environ["GI_TYPELIB_PATH"] = os.path.join(__nuitka_binary_dir, "girepository")"""

            return code, "Set typelib search path"

    def considerDataFiles(self, module):
        """Copy typelib files from the default installation path"""
        if _isGiModule(module):
            path = self.queryRuntimeInformationMultiple(
                info_name="gi_info",
                setup_codes="import gi; from gi.repository import GObject",
                values=(
                    (
                        "introspection_module",
                        "gi.Repository.get_default().get_typelib_path('GObject')",
                    ),
                ),
            )

            gi_repository_path = os.path.dirname(path.introspection_module)
            yield makeIncludedDataDirectory(
                source_path=gi_repository_path,
                dest_path="girepository",
                reason="typelib files for gi modules",
            )


class NuitkaPluginDetectorGi(NuitkaPluginBase):
    """Only used if plugin is NOT activated

    Notes:
         We are given the chance to issue a warning if we think we may be required.
    """

    detector_for = NuitkaPluginGi

    @classmethod
    def isRelevant(cls):
        """Check whether plugin might be required.
        Returns:
            True if this is a standalone compilation.
        """
        return Options.isStandaloneMode()

    def onModuleDiscovered(self, module):
        """This method checks whether gi is required.
        Notes:
            For this we check whether its first name part is gi relevant.
        Args:
            module: the module object
        Returns:
            None
        """
        if module.getFullName() == "gi":
            self.warnUnusedPlugin("Missing gi support.")
