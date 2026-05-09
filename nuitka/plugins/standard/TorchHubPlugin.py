#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Torch Hub plugin."""

import ast
import os

from nuitka.__past__ import basestring
from nuitka.Errors import NuitkaForbiddenImportEncounter
from nuitka.importing.Importing import locateModule
from nuitka.importing.Recursion import recurseTo
from nuitka.options.Options import isStandaloneMode
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.tree.SourceHandling import readSourceCodeFromFilename
from nuitka.utils.ModuleNames import ModuleName


class NuitkaPluginTorchHub(NuitkaPluginBase):
    """Scan Torch Hub repositories for hidden imports.

    Notes:
        Torch Hub downloads source code to a cache directory and later imports
        it from there at run time. We therefore scan the cached source tree for
        static imports and include only the external dependencies that are
        discovered. The downloaded repository itself is intentionally not added
        to the distribution, because Torch Hub will source load it again.
    """

    plugin_name = "torch-hub"
    plugin_desc = "Resolve and scan Torch Hub repositories for dependency inclusion."
    plugin_category = "package-support"

    # spell-checker: ignore yolov,hubconf,getargspec

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        group.add_option(
            "--torch-hub-model",
            action="append",
            dest="torch_hub_models",
            default=[],
            help="""\
Specify a Torch Hub model to scan for hidden imports. Use the form
'REPO_OR_DIR=MODEL', e.g. 'ultralytics/yolov5=yolov5s'. The repository part
may also be a local directory containing a 'hubconf.py'. Repeat this option
for multiple models. [REQUIRED]""",
        )

    @classmethod
    def isRelevant(cls):
        return isStandaloneMode()

    def __init__(self, torch_hub_models):
        self.model_specs = []
        self._located_module_cache = {}
        self._hub_dependency_names = set()
        self._hub_directories_seen = set()

        for torch_hub_model in torch_hub_models:
            try:
                model_spec = self._parseHubModelSpec(torch_hub_model)
            except ValueError:
                self.sysexit(
                    "Error, malformed value '%s' for '--torch-hub-model', use 'REPO_OR_DIR=MODEL'."
                    % torch_hub_model
                )
            else:
                self.model_specs.append(model_spec)

        if not self.model_specs:
            self.sysexit(
                "Error, '--torch-hub-model' must be specified when using '--enable-plugin=torch-hub'."
            )

    @staticmethod
    def _parseHubModelSpec(value):
        repo_spec, separator, model_name = value.partition("=")

        repo_spec = repo_spec.strip()
        model_name = model_name.strip()

        if separator != "=" or not repo_spec or not model_name:
            raise ValueError(value)

        return repo_spec, model_name

    def onCompilationStartChecks(self):
        for repo_spec, model_name in self.model_specs:
            hub_dir = self._resolveHubDirectory(repo_spec=repo_spec)

            if hub_dir in self._hub_directories_seen:
                continue

            self._hub_directories_seen.add(hub_dir)

            dependency_names = self._scanHubDirectory(
                hub_dir=hub_dir,
                repo_spec=repo_spec,
            )

            self._hub_dependency_names.update(dependency_names)

            self.info(
                "Torch Hub model '%s' from '%s' added %d dependency modules."
                % (model_name, repo_spec, len(dependency_names))
            )

    def onModuleInitialSet(self):
        included_module_names = set()
        attempted_module_names = set()

        for module_name in sorted(self._hub_dependency_names):
            for candidate_module_name in self._getCandidateRootModuleNames(module_name):
                if candidate_module_name in attempted_module_names:
                    continue

                attempted_module_names.add(candidate_module_name)

                included_module = self._includeDependencyModule(
                    module_name=candidate_module_name
                )

                if included_module is not None:
                    included_module_names.add(candidate_module_name)
                    yield included_module

    @staticmethod
    def _makeInfoName(prefix, value):
        result = []

        for c in value:
            if c.isalnum():
                result.append(c)
            else:
                result.append("_")

        return "%s_%s" % (prefix, "".join(result))

    def _resolveHubDirectory(self, repo_spec):
        hub_dir = self.queryRuntimeInformationSingle(
            info_name=self._makeInfoName("hub_dir", repo_spec),
            setup_codes="""\
import inspect
import os
import torch

def _resolveTorchHubDirectory(repo_spec):
    if os.path.isdir(repo_spec):
        return os.path.abspath(repo_spec)

    cache_or_reload = getattr(torch.hub, "_get_cache_or_reload", None)

    if cache_or_reload is None:
        raise RuntimeError("torch.hub helper '_get_cache_or_reload' is unavailable")

    try:
        argument_names = inspect.getfullargspec(cache_or_reload).args
    except AttributeError:
        argument_names = inspect.getargspec(cache_or_reload).args

    kwargs = {}

    if "force_reload" in argument_names:
        kwargs["force_reload"] = False

    if "trust_repo" in argument_names:
        kwargs["trust_repo"] = True

    if "verbose" in argument_names:
        kwargs["verbose"] = False

    if "skip_validation" in argument_names:
        kwargs["skip_validation"] = True

    return cache_or_reload(repo_spec, **kwargs)
""",
            value="_resolveTorchHubDirectory(%r)" % repo_spec,
        )

        if not hub_dir:
            return self.sysexit(
                "Error, failed to resolve Torch Hub repository '%s'." % repo_spec
            )

        hub_conf_filename = os.path.join(hub_dir, "hubconf.py")

        if not os.path.isfile(hub_conf_filename):
            return self.sysexit(
                "Error, Torch Hub repository '%s' at '%s' has no 'hubconf.py'."
                % (repo_spec, hub_dir)
            )

        return hub_dir

    def _scanHubDirectory(self, hub_dir, repo_spec):
        internal_modules = self._collectHubInternalModules(hub_dir=hub_dir)

        if "hubconf" not in internal_modules:
            return self.sysexit(
                "Error, Torch Hub repository '%s' at '%s' has no importable 'hubconf' module."
                % (repo_spec, hub_dir)
            )

        external_module_names = set()
        pending = ["hubconf"]
        processed = set()

        while pending:
            module_name = pending.pop()

            if module_name in processed:
                continue

            processed.add(module_name)

            source_filename, is_package = internal_modules[module_name]

            if os.path.isdir(source_filename):
                continue

            for dependency_name in self._readModuleDependencyNames(
                module_name=module_name,
                source_filename=source_filename,
                is_package=is_package,
                internal_modules=internal_modules,
            ):
                if dependency_name in internal_modules:
                    pending.append(dependency_name)
                else:
                    external_module_names.add(dependency_name)

        return external_module_names

    @staticmethod
    def _getHubPackageName(hub_dir, root):
        rel_dir = os.path.relpath(root, hub_dir)

        if rel_dir == ".":
            return None

        return rel_dir.replace(os.path.sep, ".")

    @staticmethod
    def _hasHubPackageContent(dirnames, filenames):
        for filename in filenames:
            if filename.endswith(".py"):
                return True

        for dirname in dirnames:
            if not dirname.startswith("."):
                return True

        return False

    @staticmethod
    def _collectHubInternalModules(hub_dir):
        result = {}

        for root, dirnames, filenames in os.walk(hub_dir):
            dirnames[:] = [
                dirname
                for dirname in dirnames
                if dirname != "__pycache__" and not dirname.startswith(".")
            ]

            package_name = NuitkaPluginTorchHub._getHubPackageName(
                hub_dir=hub_dir,
                root=root,
            )

            if package_name is not None and NuitkaPluginTorchHub._hasHubPackageContent(
                dirnames=dirnames,
                filenames=filenames,
            ):
                result[package_name] = root, True

            if package_name is not None and "__init__.py" in filenames:
                result[package_name] = os.path.join(root, "__init__.py"), True

            for filename in filenames:
                if filename == "__init__.py" or not filename.endswith(".py"):
                    continue

                module_basename = filename[:-3]

                if package_name is None:
                    module_name = module_basename
                else:
                    module_name = package_name + "." + module_basename

                result[module_name] = os.path.join(root, filename), False

        return result

    def _readModuleDependencyNames(
        self, module_name, source_filename, is_package, internal_modules
    ):
        module_name_obj = ModuleName(module_name)

        source_code = readSourceCodeFromFilename(
            module_name=module_name_obj,
            source_filename=source_filename,
            pre_load=True,
        )

        try:
            module_tree = ast.parse(source_code, source_filename)
        except SyntaxError:
            self.warning(
                "Torch Hub dependency module '%s' could not be parsed due to a SyntaxError."
                % module_name
            )
            return set()

        result = set()

        for dependency_name in self._extractHubDeclaredDependencies(module_tree):
            result.add(dependency_name)

        for node in ast.walk(module_tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    result.add(name.name)
            elif isinstance(node, ast.ImportFrom):
                imported_module_name = self._resolveImportFromModuleName(
                    module_name=module_name,
                    is_package=is_package,
                    node=node,
                )

                if imported_module_name is None:
                    continue

                result.add(imported_module_name)

                for imported_name in node.names:
                    if imported_name.name == "*":
                        continue

                    child_module_name = imported_module_name + "." + imported_name.name

                    if self._isImportableModuleName(
                        module_name=child_module_name,
                        internal_modules=internal_modules,
                    ):
                        result.add(child_module_name)

        return result

    @staticmethod
    def _extractHubDeclaredDependencies(module_tree):
        result = set()

        for node in module_tree.body:
            if not isinstance(node, ast.Assign):
                continue

            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "dependencies":
                    for value in NuitkaPluginTorchHub._extractStringSequence(
                        node.value
                    ):
                        result.add(value)

        return result

    @staticmethod
    def _extractStringSequence(node):
        if not isinstance(node, (ast.List, ast.Tuple)):
            return ()

        result = []

        for element in node.elts:  # spell-checker: ignore elts
            element_value = NuitkaPluginTorchHub._extractStringConstant(element)

            if element_value is None:
                return ()

            result.append(element_value)

        return tuple(result)

    @staticmethod
    def _extractStringConstant(node):
        constant_type = getattr(ast, "Constant", None)

        if isinstance(node, ast.Str):
            return node.s

        if constant_type is not None and isinstance(node, constant_type):
            if isinstance(node.value, basestring):
                return node.value

        return None

    @staticmethod
    def _getCurrentPackageName(module_name, is_package):
        if is_package:
            return module_name

        if "." not in module_name:
            return None

        return module_name.rsplit(".", 1)[0]

    @staticmethod
    def _resolveImportFromModuleName(module_name, is_package, node):
        if node.level == 0:
            return node.module

        current_package_name = NuitkaPluginTorchHub._getCurrentPackageName(
            module_name=module_name,
            is_package=is_package,
        )

        if current_package_name is None:
            return node.module

        package_parts = current_package_name.split(".")

        if node.level > len(package_parts) + 1:
            return None

        prefix_parts = package_parts[: len(package_parts) - (node.level - 1)]

        if node.module:
            prefix_parts.append(node.module)

        if not prefix_parts:
            return None

        return ".".join(prefix_parts)

    def _isImportableModuleName(self, module_name, internal_modules):
        if module_name in internal_modules:
            return True

        _module_name, module_filename, _module_kind, finding = self._locateModule(
            module_name
        )

        return module_filename is not None and finding != "not-found"

    def _locateModule(self, module_name):
        if module_name not in self._located_module_cache:
            self._located_module_cache[module_name] = locateModule(
                module_name=ModuleName(module_name),
                parent_package=None,
                level=0,
            )

        return self._located_module_cache[module_name]

    @staticmethod
    def _getCandidateRootModuleNames(module_name):
        result = []
        parts = module_name.split(".")

        for count in range(1, len(parts) + 1):
            result.append(".".join(parts[:count]))

        return result

    def _includeDependencyModule(self, module_name):
        (
            resolved_module_name,
            module_filename,
            module_kind,
            finding,
        ) = self._locateModule(module_name)

        if (
            finding == "not-found"
            or module_filename is None
            and module_kind != "built-in"
        ):
            self.warning(
                "Torch Hub dependency module '%s' was not found during inclusion."
                % module_name
            )
            return None

        if module_kind == "built-in":
            return None

        try:
            return recurseTo(
                module_name=resolved_module_name,
                module_filename=module_filename,
                module_kind=module_kind,
                source_ref=None,
                reason="torch hub dependency",
                using_module_name=None,
            )
        except NuitkaForbiddenImportEncounter as e:
            return self.sysexit(
                """\
Error, forbidden import of '%s' (intending to avoid '%s') encountered while including Torch Hub dependency '%s'."""
                % (e.args[0], e.args[1], module_name)
            )


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
