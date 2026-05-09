#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Torch JIT plugin."""

import ast
import os

from nuitka.options.Options import getModuleParameter, isStandaloneMode
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.FileOperations import (
    copyFileWithPermissions,
    isRelativePath,
    makeContainingPath,
)
from nuitka.utils.ModuleNames import ModuleName


def _isTorchJitScriptCall(node, torch_names, torch_jit_names, script_names):
    called = node.func

    if isinstance(called, ast.Name):
        return called.id in script_names

    if not isinstance(called, ast.Attribute) or called.attr != "script":
        return False

    called_value = called.value

    if isinstance(called_value, ast.Name):
        return called_value.id in torch_jit_names

    if not isinstance(called_value, ast.Attribute) or called_value.attr != "jit":
        return False

    called_value = called_value.value

    return isinstance(called_value, ast.Name) and called_value.id in torch_names


def _considerTorchJitImport(alias, torch_names, torch_jit_names):
    if alias.name == "torch":
        torch_names.add(alias.asname or "torch")
    elif alias.name == "torch.jit":
        if alias.asname is None:
            torch_names.add("torch")
        else:
            torch_jit_names.add(alias.asname)


def _considerTorchJitImportFrom(node, torch_jit_names, script_names):
    if node.module == "torch":
        for alias in node.names:
            if alias.name == "jit":
                torch_jit_names.add(alias.asname or "jit")
    elif node.module == "torch.jit":
        for alias in node.names:
            if alias.name == "script":
                script_names.add(alias.asname or "script")
            elif alias.name == "*":
                script_names.add("script")


def _collectTorchJitImportNames(module_tree):
    torch_names = set()
    torch_jit_names = set()
    script_names = set()

    for node in ast.walk(module_tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                _considerTorchJitImport(
                    alias=alias,
                    torch_names=torch_names,
                    torch_jit_names=torch_jit_names,
                )
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            _considerTorchJitImportFrom(
                node=node,
                torch_jit_names=torch_jit_names,
                script_names=script_names,
            )

    return torch_names, torch_jit_names, script_names


def _moduleUsesTorchJitScript(module):
    source_filename = module.getCompileTimeFilename()

    if not os.path.isfile(source_filename):
        return False

    source_code = module.getSourceCode()

    try:
        module_tree = ast.parse(source_code, source_filename)
    except SyntaxError:
        return False

    torch_names, torch_jit_names, script_names = _collectTorchJitImportNames(
        module_tree=module_tree
    )

    if not torch_names and not torch_jit_names and not script_names:
        return False

    for node in ast.walk(module_tree):
        if isinstance(node, ast.Call) and _isTorchJitScriptCall(
            node=node,
            torch_names=torch_names,
            torch_jit_names=torch_jit_names,
            script_names=script_names,
        ):
            return True

    return False


class NuitkaPluginTorchJit(NuitkaPluginBase):
    """Include source files for compiled modules using Torch JIT."""

    plugin_name = "torch-jit"
    plugin_desc = "Required by 'torch.jit' source inspection in standalone mode."
    plugin_category = "package-support"

    @staticmethod
    def isAlwaysEnabled():
        return True

    @classmethod
    def isRelevant(cls):
        return isStandaloneMode()

    def __init__(self):
        self.torch_jit_source_files = ()

    @staticmethod
    def _isTorchJitEnabled():
        return getModuleParameter(ModuleName("torch"), "disable-jit") == "no"

    def onModuleCompleteSet(self, module_set):
        source_files = []
        seen_runtime_filenames = set()

        if not self._isTorchJitEnabled():
            self.torch_jit_source_files = ()
            return

        for module in module_set:
            if not module.isCompiledPythonModule():
                continue

            if not _moduleUsesTorchJitScript(module):
                continue

            runtime_filename = module.getRunTimeFilename()

            if runtime_filename in seen_runtime_filenames:
                continue

            seen_runtime_filenames.add(runtime_filename)

            if runtime_filename.startswith("<") or not isRelativePath(runtime_filename):
                self.warning(
                    "Cannot include source code for '%s' with runtime filename '%s'."
                    % (module.getFullName(), runtime_filename)
                )
                continue

            source_files.append(
                (
                    module.getFullName().asString(),
                    module.getCompileTimeFilename(),
                    runtime_filename,
                )
            )

        self.torch_jit_source_files = tuple(source_files)

        if self.torch_jit_source_files:
            self.info(
                "Including %d source file%s for Torch JIT."
                % (
                    len(self.torch_jit_source_files),
                    "" if len(self.torch_jit_source_files) == 1 else "s",
                )
            )

    def onStandaloneDistributionFinished(self, dist_dir):
        if not self.torch_jit_source_files:
            return

        for _module_name, source_path, runtime_filename in self.torch_jit_source_files:
            dest_path = os.path.normpath(os.path.join(dist_dir, runtime_filename))

            makeContainingPath(dest_path)

            copyFileWithPermissions(
                source_path=source_path,
                dest_path=dest_path,
                target_dir=dist_dir,
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
