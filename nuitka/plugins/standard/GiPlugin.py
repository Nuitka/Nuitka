#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Support for gi typelib files and DLLs"""

import os

from nuitka.importing.FakeModules import makeFakeModuleDescription
from nuitka.options.Options import hasNonDeploymentIndicator
from nuitka.plugins.PluginBase import NuitkaPluginBase, standalone_only
from nuitka.PythonVersions import python_version
from nuitka.utils.ModuleNames import ModuleName
from nuitka.utils.Utils import isWin32Windows

_gi_repository_package = ModuleName("gi.repository")
_gi_overrides_package = ModuleName("gi.overrides")

_template_gi_repository_runtime_error = '''\
_importer = DynamicImporter('gi.repository')

def _nuitka_gi_create_module(spec):
    namespace = spec.name.rsplit('.', 1)[-1]
    raise RuntimeError(
        """\
Nuitka: 'gi.repository.%s' was not included at compile time, so it cannot be created at \
runtime in this build. Add '--include-module=gi.repository.%s' or an implicit-imports \
configuration entry and rebuild. Disable this check with \
'--no-deployment-flag=gi-runtime-namespaces'.""" % (namespace, namespace)
    )

_importer.create_module = _nuitka_gi_create_module

sys.meta_path.append(_importer)'''

_template_gi_repository_module_code = """\
import importlib.util
import sys

from gi.importer import DynamicImporter

_loader = DynamicImporter("gi.repository")
_spec = importlib.util.spec_from_loader(__name__, _loader)
sys.modules[__name__] = _loader.create_module(_spec)

# These imports only serve compile time inclusion of what "create_module" has
# already imported at runtime.
%(include_imports)s
"""


class NuitkaPluginGi(NuitkaPluginBase):
    plugin_name = "gi"
    plugin_desc = "Required by 'gi' package."
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
nuitka_info = globals().get("__uncompiled__", globals().get("__compiled__"))
if not os.getenv("GI_TYPELIB_PATH"):
    os.environ["GI_TYPELIB_PATH"] = os.path.join(nuitka_info.python_runtime_dir, "girepository")"""

            return code, "Set typelib search path"

    def onModuleSourceCode(self, module_name, source_filename, source_code):
        """Provide non-deployment errors for runtime gi repository namespaces.

        Args:
            module_name: (str) name of module
            source_filename: (str) filename of module
            source_code: (str) its source code

        Returns:
            source_code (str)
        """
        if (
            module_name != "gi.repository"
            or python_version < 0x300
            or not hasNonDeploymentIndicator("gi-runtime-namespaces")
        ):
            return source_code

        original_line = "sys.meta_path.append(DynamicImporter('gi.repository'))"

        if original_line not in source_code:
            self.warning("""\
Failed to patch module '%s' for runtime repository namespaces, PyGObject may have changed it, \
please report this issue.""" % module_name)

            return source_code

        return source_code.replace(original_line, _template_gi_repository_runtime_error)

    def _getNamespaceInfo(self, namespace):
        """Query typelib path and dependencies for a gi namespace.

        Args:
            namespace: name of the gi namespace, e.g. 'Gtk'.

        Returns:
            Named tuple with 'typelib_path' and 'dependencies', or None.
        """
        return self.queryRuntimeInformationMultiple(
            info_name="namespace_%s" % namespace,
            setup_codes="""\
import gi
Repository = gi.Repository.get_default()
Repository.require('%s', None)""" % namespace,
            values=(
                (
                    "typelib_path",
                    "gi.Repository.get_default().get_typelib_path('%s')" % namespace,
                ),
                (
                    "dependencies",
                    "sorted(set(dependency.rsplit('-', 1)[0] "
                    "for dependency in Repository.get_immediate_dependencies('%s') "
                    "if Repository.is_registered(dependency.rsplit('-', 1)[0]) "
                    "or Repository.enumerate_versions(dependency.rsplit('-', 1)[0])))"
                    % namespace,
                ),
            ),
            warn_import_error=False,
        )

    def _makeTypelibDataFile(self, namespace):
        namespace_info = self._getNamespaceInfo(namespace)

        if namespace_info is None or not namespace_info.typelib_path:
            return None

        return self.makeIncludedDataFile(
            source_path=namespace_info.typelib_path,
            dest_path=os.path.join(
                "girepository", os.path.basename(namespace_info.typelib_path)
            ),
            reason="typelib file for gi namespace '%s'" % namespace,
        )

    @standalone_only
    def considerDataFiles(self, module):
        """Copy typelib files needed for included gi repository namespaces.

        Notes:
            Override modules are always included alongside the repository
            namespace stand-in that imports them, so the stand-in carries the
            typelib data.
        """

        if module.getFullName().getPackageName() != _gi_repository_package:
            return

        namespace = module.getFullName().getBasename()

        included_datafile = self._makeTypelibDataFile(namespace)

        if included_datafile is not None:
            yield included_datafile

        # Platform specific namespaces may be loaded by C code at runtime, so
        # their typelib files are included like PyInstaller does.
        if namespace == "Gio":
            platform_namespace = "GioWin32" if isWin32Windows() else "GioUnix"
        elif namespace == "GLib":
            platform_namespace = "GLibWin32" if isWin32Windows() else "GLibUnix"
        else:
            platform_namespace = None

        if platform_namespace is not None:
            included_datafile = self._makeTypelibDataFile(platform_namespace)

            if included_datafile is not None:
                yield included_datafile

    def createVirtualModule(self, module_name):
        """Provide generated code for "gi.repository.*" virtual modules.

        Args:
            module_name: name of the module that was not found.

        Returns:
            FakeModuleDescription or None
        """
        if python_version < 0x300:
            return None

        if module_name.getPackageName() != _gi_repository_package:
            return None

        namespace = module_name.getBasename()
        namespace_info = self._getNamespaceInfo(namespace)

        include_imports = []

        if namespace_info is not None:
            include_imports.extend(
                "import gi.repository.%s\n" % dependency
                for dependency in namespace_info.dependencies
                if dependency != namespace
                and self._getNamespaceInfo(dependency) is not None
            )

        override_name = _gi_overrides_package.getChildNamed(namespace)

        if self.locateModule(override_name) is not None:
            include_imports.append("import %s\n" % override_name)

        source_filename = self.locateModule("gi.repository")

        if source_filename is not None and os.path.isdir(source_filename):
            source_filename = os.path.join(source_filename, "__init__.py")

        return makeFakeModuleDescription(
            module_name=module_name,
            source_code=_template_gi_repository_module_code
            % {"include_imports": "".join(include_imports)},
            source_filename=source_filename or "gi.repository",
            reason="gi repository namespace '%s'" % module_name,
        )

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
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
