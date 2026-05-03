#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Plugin to provide transformers package support."""

import ast
import os
import re

from nuitka.options.Options import isStandaloneMode
from nuitka.plugins.PluginBase import NuitkaPluginBase

_transformers_can_set_attn_flag_name = (
    "_nuitka_transformers_can_set_attn_implementation"
)
_transformers_can_set_experts_flag_name = (
    "_nuitka_transformers_can_set_experts_implementation"
)


def _getTransformersRuntimeSourceSupport(module_name, source_filename, source_code):
    try:
        module_tree = ast.parse(source_code, source_filename)
    except SyntaxError:
        return None

    imports_transformers = False
    has_class_defs = False

    for node in ast.walk(module_tree):
        if isinstance(node, ast.ClassDef):
            has_class_defs = True
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "transformers" or alias.name.startswith(
                    "transformers."
                ):
                    imports_transformers = True
        elif (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module is not None
        ):
            if node.module == "transformers" or node.module.startswith("transformers."):
                imports_transformers = True

    if not imports_transformers and module_name.hasNamespace("transformers"):
        imports_transformers = True

    if not has_class_defs or not imports_transformers:
        return None

    can_set_attn_implementation = True

    if re.search(r"class \w+Attention\(nn.Module\)", source_code):
        can_set_attn_implementation = (
            "eager_attention_forward" in source_code
            and "ALL_ATTENTION_FUNCTIONS.get_interface(" in source_code
        )

    can_set_experts_implementation = "@use_experts_implementation" in source_code

    return can_set_attn_implementation, can_set_experts_implementation


_transformers_attn_method_code = "def _can_set_attn_implementation("
_transformers_experts_method_code = "def _can_set_experts_implementation("

_transformers_modeling_utils_standalone_patch_attn_code = """

import re
import sys


def _can_set_attn_implementation_nuitka(cls):
    class_module = sys.modules.get(cls.__module__)

    if class_module is None:
        return False

    can_set_attn_implementation = getattr(
        class_module, "%(attn_flag_name)s", None
    )

    if can_set_attn_implementation is not None:
        return can_set_attn_implementation

    if not hasattr(class_module, "__file__"):
        return False

    class_file = class_module.__file__

    with open(class_file, "r", encoding="utf-8") as f:
        code = f.read()

    if re.search(r"class \\w+Attention\\(nn.Module\\)", code):
        return (
            "eager_attention_forward" in code
            and "ALL_ATTENTION_FUNCTIONS.get_interface(" in code
        )
    else:
        return True
PreTrainedModel._can_set_attn_implementation = classmethod(
    _can_set_attn_implementation_nuitka
)
""" % {
    "attn_flag_name": _transformers_can_set_attn_flag_name,
}

_transformers_modeling_utils_standalone_patch_experts_code = """

import sys


def _can_set_experts_implementation_nuitka(cls):
    class_module = sys.modules.get(cls.__module__)

    if class_module is None:
        return False

    can_set_experts_implementation = getattr(
        class_module, "%(experts_flag_name)s", None
    )

    if can_set_experts_implementation is not None:
        return can_set_experts_implementation

    if not hasattr(class_module, "__file__"):
        return False

    class_file = class_module.__file__

    with open(class_file, "r", encoding="utf-8") as f:
        code = f.read()

    return "@use_experts_implementation" in code


PreTrainedModel._can_set_experts_implementation = classmethod(
    _can_set_experts_implementation_nuitka
)
""" % {
    "experts_flag_name": _transformers_can_set_experts_flag_name,
}


class NuitkaPluginTransformers(NuitkaPluginBase):
    plugin_name = "transformers"
    plugin_desc = "Required by 'transformers' package."
    plugin_category = "package-support"

    @staticmethod
    def isAlwaysEnabled():
        return True

    # Modules that have "_import_structure = {" definitions.
    _import_structure_modules = set()

    # Modules that have "define_import_structure(_file)" calls.
    _define_structure_modules = {}

    def onModuleUsageLookAhead(
        self, module_name, module_filename, module_kind, get_module_source
    ):
        if (
            not module_name.hasNamespace("transformers")
            or module_name == "transformers.utils.import_utils"
        ):
            return

        # Getting the source code will also trigger our modification
        # and potentially tell us if any lazy loading applies.
        source_code = get_module_source()

        if source_code is None:
            return

        if "_import_structure = {" in source_code:
            self._import_structure_modules.add(module_name)

    def _getImportStructureDefinition(self, module_name, source_filename, prefix):
        # TODO: Is caching is not needed, because it does that on
        # its own?

        if prefix is None:
            value = (
                "{tuple(key): value for (key, value) in define_import_structure(%r).items()}"
                % source_filename
            )
        else:
            value = (
                "{tuple(key): value for (key, value) in define_import_structure(%r, prefix=%r).items()}"
                % (source_filename, prefix)
            )

        import_structure_value = self.queryRuntimeInformationSingle(
            setup_codes="from transformers.utils.import_utils import define_import_structure",
            value=value,
            info_name="transformers_%s_import_structure" % module_name.asString(),
        )

        return import_structure_value

    def getImplicitImports(self, module):
        module_name = module.getFullName()

        if module_name in self._import_structure_modules:
            for sub_module_name in self.queryRuntimeInformationSingle(
                setup_codes="import %s" % module_name.asString(),
                value="list(getattr(%(module_name)s, '_import_structure', {}).keys())"
                % {"module_name": module_name.asString()},
                info_name="import_structure_for_%s" % module_name.asString(),
            ):
                sub_module_name = module_name.getChildNamed(sub_module_name)

                if (
                    sub_module_name == "transformers.testing_utils"
                    and not self.evaluateCondition(
                        full_name="transformers", condition="use_pytest"
                    )
                ):
                    continue

                yield sub_module_name

        if module_name in self._define_structure_modules:
            for sub_module_name in (
                self._define_structure_modules[module_name].get(frozenset(), {}).keys()
            ):
                yield module_name.getChildNamed(sub_module_name)

    def onModuleSourceCode(self, module_name, source_filename, source_code):
        transformers_runtime_source_support = None

        if isStandaloneMode() and (
            module_name.hasNamespace("transformers") or "transformers" in source_code
        ):
            transformers_runtime_source_support = _getTransformersRuntimeSourceSupport(
                module_name=module_name,
                source_filename=source_filename,
                source_code=source_code,
            )

        if module_name.hasNamespace("transformers"):
            if isStandaloneMode() and module_name == "transformers.modeling_utils":
                if _transformers_attn_method_code in source_code:
                    source_code += (
                        _transformers_modeling_utils_standalone_patch_attn_code
                    )

                if _transformers_experts_method_code in source_code:
                    source_code += (
                        _transformers_modeling_utils_standalone_patch_experts_code
                    )

            if (
                'define_import_structure(Path(__file__).parent / "models", prefix="models")'
                in source_code
            ):
                import_structure_value = self._getImportStructureDefinition(
                    module_name=module_name,
                    source_filename=os.path.join(
                        os.path.dirname(source_filename), "models"
                    ),
                    prefix="models",
                )

                # Frozenset does not transport as such, so we converted
                # them to tuples and now back for compatibility.
                import_structure_value = dict(
                    (frozenset(key), value)
                    for key, value in import_structure_value.items()
                )

                source_code = source_code.replace(
                    'define_import_structure(Path(__file__).parent / "models", prefix="models")',
                    repr(import_structure_value),
                )

                self._define_structure_modules[module_name] = import_structure_value

            if "define_import_structure(_file)" in source_code:
                import_structure_value = self._getImportStructureDefinition(
                    module_name=module_name,
                    source_filename=source_filename,
                    prefix=None,
                )

                # Frozenset does not transport as such, so we converted
                # them to tuples and now back for compatibility.
                import_structure_value = dict(
                    (frozenset(key), value)
                    for key, value in import_structure_value.items()
                )

                source_code = source_code.replace(
                    "define_import_structure(_file)", repr(import_structure_value)
                )

                self._define_structure_modules[module_name] = import_structure_value

        if transformers_runtime_source_support is not None:
            source_code += """

%(attn_flag_name)s = %(attn_flag_value)s
%(experts_flag_name)s = %(experts_flag_value)s
""" % {
                "attn_flag_name": _transformers_can_set_attn_flag_name,
                "attn_flag_value": repr(transformers_runtime_source_support[0]),
                "experts_flag_name": _transformers_can_set_experts_flag_name,
                "experts_flag_value": repr(transformers_runtime_source_support[1]),
            }

        return source_code


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
