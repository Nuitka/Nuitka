#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Support for gi typelib files and DLLs
"""

import os

from nuitka.plugins.PluginBase import NuitkaPluginBase, standalone_only


class NuitkaPluginGi(NuitkaPluginBase):
    plugin_name = "gi"
    plugin_desc = "Support for GI package typelib dependency."
    plugin_category = "package-support"

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
if not os.getenv("GI_TYPELIB_PATH"):
    os.environ["GI_TYPELIB_PATH"] = os.path.join(__nuitka_binary_dir, "girepository")"""

            return code, "Set typelib search path"

    @standalone_only
    def considerDataFiles(self, module):
        """Copy typelib files from the default installation path"""
        if module.getFullName() == "gi":
            gi_typelib_info = self.queryRuntimeInformationMultiple(
                info_name="gi_info",
                setup_codes="import gi; from gi.repository import GObject",
                values=(
                    (
                        "introspection_module",
                        "gi.Repository.get_default().get_typelib_path('GObject')",
                    ),
                ),
            )

            if gi_typelib_info is not None:
                gi_repository_path = os.path.dirname(
                    gi_typelib_info.introspection_module
                )
                yield self.makeIncludedDataDirectory(
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
        def tryLocateAndLoad(dll_name):
            # Support various name forms in MSYS2 over time.
            dll_path = self.locateDLL(dll_name)
            if dll_path is None:
                dll_path = self.locateDLL("%s" % dll_name)
            if dll_path is None:
                dll_path = self.locateDLL("lib%s" % dll_name)

            if dll_path is not None:
                yield self.makeDllEntryPoint(
                    source_path=dll_path,
                    dest_path=os.path.basename(dll_path),
                    module_name="gi._gi",
                    package_name="gi",
                    reason="needed by 'gi._gi'",
                )

        if module.getFullName() == "gi._gi":
            # TODO: Get local relevant DLL names from GI
            for dll_name in (
                "gtk-3-0",
                "soup-2.4-1",
                "soup-gnome-2.4-1",
                "libsecret-1-0",
            ):
                yield tryLocateAndLoad(dll_name)


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
