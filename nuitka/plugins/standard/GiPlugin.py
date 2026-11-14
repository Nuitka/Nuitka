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


def _nuitka_include_for_compile_time():
    # These imports only serve compile time inclusion. At runtime,
    # "create_module" imports the namespaces needed for the version the program
    # has selected, and importing other versions here would be a conflict, e.g.
    # "Gdk-4.0" after "Gdk-3.0" was loaded already.
    pass
%(include_imports)s
"""


class NuitkaPluginGi(NuitkaPluginBase):
    plugin_name = "gi"
    plugin_desc = "Required by 'gi' package."
    plugin_category = "package-support"

    def __init__(self, gi_versions):
        self._given_namespace_versions = {}
        self._dependency_namespace_versions = {}
        self._namespace_versions = {}

        for gi_version in gi_versions:
            namespace, separator, version = gi_version.partition("=")

            namespace = namespace.strip()
            version = version.strip()

            if separator != "=" or not namespace or not version:
                self.sysexit(
                    "Error, malformed value '%s' for '--gi-version', use 'NAMESPACE=VERSION'."
                    % gi_version
                )

            self._given_namespace_versions[namespace] = version

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        group.add_option(
            "--gi-version",
            action="append",
            dest="gi_versions",
            default=[],
            help="""\
Specify the version of a gi namespace to compile against, e.g. "Gtk=3.0".
This is required for namespaces that have multiple installed versions, unless
the version is dictated by a parent namespace. Repeat this option for multiple
namespaces. It must match the version that the program selects with
"gi.require_version" at runtime.""",
        )

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

        for original_line in (
            "sys.meta_path.append(DynamicImporter('gi.repository'))",
            'sys.meta_path.append(DynamicImporter("gi.repository"))',
        ):
            if original_line in source_code:
                source_code = source_code.replace(
                    original_line, _template_gi_repository_runtime_error
                )
                break
        else:
            self.warning("""\
Failed to patch module '%s' for runtime repository namespaces, PyGObject may have changed it, \
please report this issue.""" % module_name)

        return source_code

    def _getNamespaceInfo(self, namespace, version):
        """Query typelib path and dependencies for a gi namespace.

        Args:
            namespace: name of the gi namespace, e.g. 'Gtk'.
            version: version to load, or None for the default version.

        Returns:
            Named tuple with 'typelib_path' and 'dependencies' as (namespace,
            version) tuples, or None.
        """
        if version is None:
            require_version = "None"
            info_name = "namespace_%s" % namespace
        else:
            require_version = "'%s'" % version
            info_name = "namespace_%s_%s" % (namespace, version)

        return self.queryRuntimeInformationMultiple(
            info_name=info_name,
            setup_codes="""\
import gi
Repository = gi.Repository.get_default()
try:
    Repository.require('%s', %s)
except Exception:
    raise ImportError("gi typelib not available")""" % (namespace, require_version),
            values=(
                (
                    "typelib_path",
                    "Repository.get_typelib_path('%s')" % namespace,
                ),
                (
                    "dependencies",
                    "sorted(set(tuple(dependency.rsplit('-', 1)) "
                    "for dependency in Repository.get_immediate_dependencies('%s') "
                    "if Repository.is_registered(dependency.rsplit('-', 1)[0]) "
                    "or Repository.enumerate_versions(dependency.rsplit('-', 1)[0])))"
                    % namespace,
                ),
            ),
            warn_import_error=False,
        )

    def _getNamespaceVersions(self, namespace):
        """Get the installed versions of a gi namespace.

        Args:
            namespace: name of the gi namespace, e.g. 'Gtk'.

        Returns:
            Tuple of version strings, may be empty.
        """
        namespace_info = self.queryRuntimeInformationMultiple(
            info_name="versions_%s" % namespace,
            setup_codes="""\
import gi
Repository = gi.Repository.get_default()""",
            values=(
                (
                    "versions",
                    "tuple(sorted(Repository.enumerate_versions('%s')))" % namespace,
                ),
            ),
            warn_import_error=False,
        )

        if namespace_info is None:
            return ()

        return namespace_info.versions

    def _getNamespaceVersion(self, namespace):
        """Get the version of a gi namespace to compile against.

        Notes:
            The version can be given with '--gi-version', or is dictated by the
            typelib of a parent namespace. If neither is the case, only a single
            installed version requires no selection, otherwise it is an error.

        Args:
            namespace: name of the gi namespace, e.g. 'Gtk'.

        Returns:
            Version string or None if the namespace is not available.
        """
        if namespace in self._namespace_versions:
            return self._namespace_versions[namespace]

        version = self._given_namespace_versions.get(namespace)

        if version is not None:
            versions = self._getNamespaceVersions(namespace)

            if versions and version not in versions:
                self.sysexit(
                    "Error, gi namespace '%s' version '%s' was selected, but installed "
                    "versions are: %s." % (namespace, version, ", ".join(versions))
                )

            self._namespace_versions[namespace] = version
            return version

        version = self._dependency_namespace_versions.get(namespace)

        if version is not None:
            self._namespace_versions[namespace] = version
            return version

        versions = self._getNamespaceVersions(namespace)

        if len(versions) == 1:
            self._namespace_versions[namespace] = versions[0]
            return versions[0]

        if not versions:
            return None

        return self.sysexit(
            "Error, gi namespace '%s' is available in multiple versions (%s), select "
            "the one the program uses with '--gi-version=%s=VERSION'."
            % (namespace, ", ".join(versions), namespace)
        )

    def _getNamespaceInfos(self, namespace):
        """Get namespace information for the version to be included.

        Args:
            namespace: name of the gi namespace, e.g. 'Gtk'.

        Returns:
            Tuple with the named tuple of the selected version, or empty.
        """
        namespace_info = self._getNamespaceInfo(
            namespace=namespace, version=self._getNamespaceVersion(namespace)
        )

        if namespace_info is None:
            return ()

        return (namespace_info,)

    def _getNamespaceDependencies(self, namespace):
        """Get dependencies of the gi namespace version to be included.

        Notes:
            Dependencies carry the namespace version they were built against,
            which is propagated to the stand-in of the dependency, so that e.g.
            Gtk 3.0 selects Gdk 3.0.

        Args:
            namespace: name of the gi namespace, e.g. 'Gtk'.

        Returns:
            Sorted list of namespace names, or None if namespace is unavailable.
        """
        namespace_info = self._getNamespaceInfo(
            namespace=namespace, version=self._getNamespaceVersion(namespace)
        )

        if namespace_info is None:
            return None

        dependencies = set()

        for dependency_name, dependency_version in namespace_info.dependencies:
            if dependency_name == namespace:
                continue

            if dependency_name in self._given_namespace_versions:
                dependencies.add(dependency_name)
                continue

            previous_version = self._dependency_namespace_versions.get(dependency_name)

            if previous_version is None:
                self._dependency_namespace_versions[dependency_name] = (
                    dependency_version
                )

            if previous_version is None or previous_version == dependency_version:
                dependencies.add(dependency_name)

        if namespace == "Gdk":
            # PyGObject's Gdk override imports GdkX11 with the Gdk version.
            gdk_version = self._namespace_versions.get(namespace)

            if gdk_version is not None:
                self._dependency_namespace_versions.setdefault("GdkX11", gdk_version)

        return sorted(dependencies)

    @staticmethod
    def _getPlatformNamespace(namespace):
        """Get platform specific gi namespace for a namespace.

        Args:
            namespace: name of the gi namespace, e.g. 'GLib'.

        Returns:
            Name of the platform specific namespace or None.
        """

        if namespace == "Gio":
            return "GioWin32" if isWin32Windows() else "GioUnix"

        if namespace == "GLib":
            return "GLibWin32" if isWin32Windows() else "GLibUnix"

        return None

    def _makeTypelibDataFiles(self, namespace):
        included_paths = set()

        for namespace_info in self._getNamespaceInfos(namespace):
            if (
                not namespace_info.typelib_path
                or namespace_info.typelib_path in included_paths
            ):
                continue

            included_paths.add(namespace_info.typelib_path)

            yield self.makeIncludedDataFile(
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

        for included_datafile in self._makeTypelibDataFiles(namespace):
            yield included_datafile

    def _addPlatformNamespaceImports(
        self, namespace, included_namespaces, include_imports
    ):
        """Add compile time import for the platform specific namespace variant.

        Notes:
            PyGObject imports the platform specific namespace from the overrides
            at runtime, so its stand-in must exist even though there is no
            static import for it, also its override module must be included.

        Args:
            namespace: name of the gi namespace, e.g. 'Gio'.
            included_namespaces: set of namespace names already included.
            include_imports: list of import statements to append to.

        Returns:
            None
        """
        platform_namespace = self._getPlatformNamespace(namespace)

        if platform_namespace is None:
            return

        namespace_version = self._getNamespaceVersion(namespace)

        if namespace_version is None:
            return

        # PyGObject requires the same version for the platform specific
        # namespace as for the namespace it belongs to.
        self._dependency_namespace_versions.setdefault(
            platform_namespace, namespace_version
        )

        if platform_namespace not in included_namespaces and self._getNamespaceInfos(
            platform_namespace
        ):
            include_imports.append("import gi.repository.%s" % platform_namespace)

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
        dependencies = self._getNamespaceDependencies(namespace)

        include_imports = []
        included_namespaces = set()

        if dependencies is not None:
            for dependency in dependencies:
                if dependency not in included_namespaces:
                    included_namespaces.add(dependency)
                    include_imports.append("import gi.repository.%s" % dependency)

        override_name = _gi_overrides_package.getChildNamed(namespace)

        if self.locateModule(override_name) is not None:
            include_imports.append("import %s" % override_name)

        self._addPlatformNamespaceImports(
            namespace=namespace,
            included_namespaces=included_namespaces,
            include_imports=include_imports,
        )

        source_filename = self.locateModule("gi.repository")

        if source_filename is not None and os.path.isdir(source_filename):
            source_filename = os.path.join(source_filename, "__init__.py")

        return makeFakeModuleDescription(
            module_name=module_name,
            source_code=_template_gi_repository_module_code
            % {
                "include_imports": "".join(
                    "    %s\n" % include_import for include_import in include_imports
                )
            },
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
