#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""
Plugins: Welcome to Nuitka! This is your shortest way to become part of it.

This is to provide the base class for all Yaml plugins. These deal with the
configuration files of Nuitka.
"""

from nuitka.containers.Namedtuples import makeNamedtupleClass
from nuitka.options.Options import assumeYesForDownloads
from nuitka.utils.Yaml import getYamlPackageConfiguration

from .PluginBase import NuitkaPluginBase

YamlConfigItem = makeNamedtupleClass(
    "YamlConfigItem",
    ("config_module_name", "value", "priority"),
)

YamlConfigKeyValue = makeNamedtupleClass(
    "YamlConfigKeyValue",
    ("config_module_name", "key", "value", "priority"),
)


class NuitkaYamlPluginBase(NuitkaPluginBase):
    """Nuitka base class for all plugins that use yaml config"""

    def __init__(self):
        self.config = None

    def onCompilationStartChecks(self):
        self.config = getYamlPackageConfiguration(
            logger=None,
            assume_yes_for_downloads=assumeYesForDownloads(),
            check_checksums=True,
        )

    def getYamlConfigItem(
        self, module_name, section, item_name, decide_relevant, recursive
    ):
        config_module_name = module_name

        while True:
            module_configs = self.config.get(config_module_name, section=section)

            if module_configs is not None:
                for module_config in module_configs:
                    if item_name not in module_config:
                        continue

                    config_item = module_config[item_name]

                    # Avoid condition, if the item is not relevant
                    if decide_relevant is not None and not decide_relevant(config_item):
                        continue

                    if not self.evaluateCondition(
                        full_name=module_name,
                        condition=module_config.get("when", "True"),
                        config_module_name=config_module_name,
                    ):
                        continue

                    yield YamlConfigItem(
                        config_module_name=config_module_name,
                        value=config_item,
                        priority=self.config.getEntryPriority(module_config),
                    )

            if not recursive:
                break

            config_module_name = config_module_name.getPackageName()
            if not config_module_name:
                break

    def getYamlConfigItemItems(
        self, module_name, section, item_name, decide_relevant, recursive
    ):
        def dict_decide_relevant(item_dict):
            if not item_dict:
                return False

            if decide_relevant is None:
                return True

            for key, value in item_dict.items():
                if decide_relevant(key, value):
                    return True

            return False

        for item_config in self.getYamlConfigItem(
            module_name=module_name,
            section=section,
            item_name=item_name,
            decide_relevant=dict_decide_relevant,
            recursive=recursive,
        ):
            for key, value in item_config.value.items():
                if decide_relevant is None or decide_relevant(key, value):
                    yield YamlConfigKeyValue(
                        config_module_name=item_config.config_module_name,
                        key=key,
                        value=value,
                        priority=item_config.priority,
                    )

    def getYamlConfigItemSet(
        self, module_name, section, item_name, decide_relevant, recursive
    ):
        seen = set()

        def isRelevantValue(value):
            return value not in seen and (
                decide_relevant is None or decide_relevant(value)
            )

        def decideRelevantForSet(item_set):
            if not item_set:
                return False

            return any(isRelevantValue(value) for value in item_set)

        for item_config in self.getYamlConfigItem(
            module_name=module_name,
            section=section,
            item_name=item_name,
            decide_relevant=decideRelevantForSet,
            recursive=recursive,
        ):
            for value in item_config.value:
                if isRelevantValue(value):
                    seen.add(value)
                    yield YamlConfigItem(
                        config_module_name=item_config.config_module_name,
                        value=value,
                        priority=item_config.priority,
                    )


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
