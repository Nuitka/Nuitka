#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#
""" Nuitka yaml utility functions.

Because we want to work with Python2.6 or higher, we play a few tricks with
what library to use for what Python. We have an inline copy of PyYAML that
still does 2.6, on other Pythons, we expect the system to have it installed.

Also we put loading for specific packages in here and a few helpers to work
with these config files.
"""

import pkgutil

from nuitka.containers.odict import OrderedDict
from nuitka.Tracing import general

from .Importing import importFromInlineCopy


class Yaml(object):
    __slots__ = ("data", "filename")

    def __init__(self, filename, data):
        self.filename = filename

        assert type(data) is list

        self.data = OrderedDict()

        for item in data:
            module_name = item.pop("module-name")

            if "/" in module_name:
                general.sysexit(
                    "Error, invalid module name in '%s' looks like a file path '%s'."
                    % (filename, module_name)
                )

            if module_name in self.data:
                general.sysexit("Duplicate module-name '%s' encountered." % module_name)

            self.data[module_name] = item

    def get(self, name, section):
        result = self.data.get(name)

        if result is not None:
            result = result.get(section)

        return result

    def keys(self):
        return self.data.keys()


def parseYaml(data):
    try:
        import yaml
    except ImportError:
        yaml = importFromInlineCopy("yaml", must_exist=True)

    # Make sure dictionaries are ordered even before 3.6 in the result. We use
    # them for hashing in caching keys.
    class OrderedLoader(yaml.SafeLoader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)

        return OrderedDict(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
    )

    return yaml.load(data, OrderedLoader)


_yaml_cache = {}


def parsePackageYaml(package_name, filename):
    key = package_name, filename

    if key not in _yaml_cache:
        _yaml_cache[key] = Yaml(
            filename=filename, data=parseYaml(pkgutil.get_data(package_name, filename))
        )

    return _yaml_cache[key]
