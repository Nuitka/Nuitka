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

from nuitka.freezer.IncludedDataFiles import makeIncludedDataDirectory
from nuitka.plugins.PluginBase import NuitkaPluginBase, standalone_only


class NuitkaPluginGi(NuitkaPluginBase):
    plugin_name = "gi"
    plugin_desc = "Support for GI typelib dependency"

    @staticmethod
    def isAlwaysEnabled():
        """Request to be always enabled."""

        return True

    @staticmethod
    @standalone_only
    def createPreModuleLoadCode(module):
        """Add typelib search path"""

        if module.getFullName() == "gi":
            code = r"""
import os
if not os.environ.get("GI_TYPELIB_PATH="):
    os.environ["GI_TYPELIB_PATH"] = os.path.join(__nuitka_binary_dir, "girepository")"""

            return code, "Set typelib search path"

    @standalone_only
    def considerDataFiles(self, module):
        """Copy typelib files from the default installation path"""
        if module.getFullName() == "gi":
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

    @staticmethod
    def getImplicitImports(module):
        full_name = module.getFullName()

        if full_name == "gi.overrides":
            yield "gi.overrides.Gtk"
            yield "gi.overrides.Gdk"
            yield "gi.overrides.GLib"
            yield "gi.overrides.GObject"
        elif full_name == "gi._gi":
            yield "gi._error"
        elif full_name == "gi._gi_cairo":
            yield "cairo"

    @standalone_only
    def getExtraDlls(self, module):
        if module.getFullName() == "gi._gi":
            gtk_dll_path = self.locateDLL("gtk-3")

            if gtk_dll_path is None:
                gtk_dll_path = self.locateDLL("gtk-3-0")

            if gtk_dll_path is not None:
                yield self.makeDllEntryPoint(
                    gtk_dll_path, os.path.basename(gtk_dll_path), None
                )
