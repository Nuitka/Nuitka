#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Plugin for spacy.

spell-checker: ignore spacy
"""

from nuitka.code_generation.ConstantCodes import addDistributionMetadataValue
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.Options import isStandaloneMode
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.Distributions import getEntryPointGroup
from nuitka.utils.ModuleNames import ModuleName


class NuitkaPluginSpacy(NuitkaPluginBase):
    """This class represents the main logic of the plugin."""

    plugin_name = "spacy"
    plugin_desc = "Required by 'spacy' package."

    def __init__(self, include_language_models):
        self.include_language_models = tuple(
            ModuleName(include_language_model)
            for include_language_model in include_language_models
        )
        self.available_language_models = None

        self.used_language_model_names = None

    @staticmethod
    def isAlwaysEnabled():
        return True

    @staticmethod
    def isRelevant():
        return isStandaloneMode()

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        group.add_option(
            "--spacy-language-model",
            action="append",
            dest="include_language_models",
            default=[],
            help="""\
Spacy language models to use. Can be specified multiple times. Use 'all' to
include all downloaded models.""",
        )

    def _getInstalledSpaceLanguageModels(self):
        if self.available_language_models is None:
            self.available_language_models = tuple(
                entry_point.module_name
                for entry_point in sorted(getEntryPointGroup("spacy_models"))
            )

        return self.available_language_models

    def getImplicitImports(self, module):
        if module.getFullName() == "spacy":
            self.used_language_model_names = OrderedSet()

            if "all" in self.include_language_models:
                self.used_language_model_names.update(
                    self._getInstalledSpaceLanguageModels()
                )
            else:
                for include_language_model_name in self.include_language_models:
                    if (
                        include_language_model_name
                        in self._getInstalledSpaceLanguageModels()
                    ):
                        self.used_language_model_names.add(include_language_model_name)
                    else:
                        self.sysexit(
                            """\
Error, requested to include language model '%s' that was \
not found, the list of installed ones is '%s'."""
                            % (
                                include_language_model_name,
                                ",".join(self._getInstalledSpaceLanguageModels()),
                            )
                        )

            if not self.used_language_model_names:
                self.warning(
                    """\
No language models included. Use the option '--spacy-language-model=language_model_name' to \
include one. Use 'all' to include all downloaded ones, or select from the list of installed \
ones: %s"""
                    % ",".join(self._getInstalledSpaceLanguageModels())
                )

            for used_language_model_name in self.used_language_model_names:
                yield used_language_model_name

    def considerDataFiles(self, module):
        if module.getFullName() == "spacy":
            # Do not use it accidentally for anything else
            del module

            for used_language_model_name in self.used_language_model_names:
                # Meta data is required for language models to be accepted.
                addDistributionMetadataValue(
                    distribution_name=used_language_model_name.asString(),
                    distribution=None,
                    reason="for 'spacy' to locate the language model",
                )

                module_folder = self.locateModule(used_language_model_name)

                yield self.makeIncludedDataDirectory(
                    source_path=module_folder,
                    dest_path=used_language_model_name.asPath(),
                    reason="model data for %r" % (used_language_model_name.asString()),
                    tags="spacy",
                    raw=True,
                )


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
