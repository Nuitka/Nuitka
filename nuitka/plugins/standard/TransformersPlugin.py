#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Plugin to provide transformers implicit dependencies.

"""

from nuitka.plugins.PluginBase import NuitkaPluginBase


class NuitkaPluginTransformers(NuitkaPluginBase):
    plugin_name = "transformers"
    plugin_desc = "Provide implicit imports for transformers package."
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

    def _getImportStructureDefinition(self, module_name, source_filename):
        # TODO: Is caching is not needed, because it does that on
        # its own?
        import_structure_value = self.queryRuntimeInformationSingle(
            setup_codes="from transformers.utils.import_utils import define_import_structure",
            value="{tuple(key): value for (key, value) in define_import_structure(%r).items()}"
            % source_filename,
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
            for sub_module_name in self._define_structure_modules[module_name][
                frozenset()
            ].keys():
                yield module_name.getChildNamed(sub_module_name)

    def onModuleSourceCode(self, module_name, source_filename, source_code):
        if module_name.hasNamespace("transformers"):
            if "define_import_structure(_file)" in source_code:
                import_structure_value = self._getImportStructureDefinition(
                    module_name=module_name, source_filename=source_filename
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

        return source_code


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
