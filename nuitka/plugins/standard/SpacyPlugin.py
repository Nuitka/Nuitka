""" Plugin for spacy.

spell-checker: ignore spacy
"""

from nuitka.plugins.PluginBase import NuitkaPluginBase


class NuitkaPluginSpacy(NuitkaPluginBase):
    """This class represents the main logic of the plugin."""

    plugin_name = "spacy"
    plugin_desc = "Plugin to include language models for 'spacy' package."

    def __init__(self, spacy_language_models):
        self.language_models = spacy_language_models

    @staticmethod
    def isAlwaysEnabled():
        return True

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        group.add_option(
            "--spacy-language-model",
            action="append",
            dest="spacy_language_models",
            default=[],
            help="""\
The Spacy language model to use. this option can be used multiple times to include multiple language models.""",
        )

    def getImplicitImports(self, module):
        if module.getFullName() == "spacy.utils":
            for language_model in self.language_models:
                yield language_model


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
