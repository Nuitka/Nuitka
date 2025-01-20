#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""
Plugins: Welcome to Nuitka! This is your shortest way to become part of it.

This is to provide the base class for all Yaml plugins. These deal with the
configuration files of Nuitka.
"""

from nuitka.utils.Yaml import getYamlPackageConfiguration

from .PluginBase import NuitkaPluginBase


class NuitkaYamlPluginBase(NuitkaPluginBase):
    """Nuitka base class for all plugins that use yaml config"""

    def __init__(self):
        self.config = getYamlPackageConfiguration()

    def getYamlConfigItem(
        self, module_name, section, item_name, decide_relevant, default, recursive
    ):
        while True:
            module_configs = self.config.get(module_name, section=section)

            if module_configs is not None:
                for module_config in module_configs:
                    config_item = module_config.get(item_name, default)

                    # Avoid condition, if the item is not relevant
                    if decide_relevant is not None and not decide_relevant(config_item):
                        continue

                    if not self.evaluateCondition(
                        full_name=module_name,
                        condition=module_config.get("when", "True"),
                    ):
                        continue

                    if recursive:
                        yield module_name, config_item
                    else:
                        yield config_item

            if not recursive:
                break

            module_name = module_name.getPackageName()
            if not module_name:
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
            default={},
            recursive=recursive,
        ):
            if recursive:
                for key, value in item_config[1].items():
                    if decide_relevant(key, value):
                        yield item_config[0], key, value
            else:
                for key, value in item_config.items():
                    if decide_relevant(key, value):
                        yield key, value

    def getYamlConfigItemSet(
        self, module_name, section, item_name, decide_relevant, recursive
    ):
        for item_config in self.getYamlConfigItem(
            module_name=module_name,
            section=section,
            item_name=item_name,
            decide_relevant=None,
            default=(),
            recursive=recursive,
        ):
            if recursive:
                for value in item_config[1]:
                    if decide_relevant is None or decide_relevant(value):
                        yield item_config[0], value
            else:
                for value in item_config:
                    if decide_relevant is None or decide_relevant(value):
                        yield value


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
