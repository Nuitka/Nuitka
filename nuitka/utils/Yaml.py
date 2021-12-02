#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .Importing import importFromInlineCopy


class Yaml(object):
    def __init__(self, filename, data):
        self.filename = filename
        self.data = data

    def get(self, name):
        return self.data.get(name)


def parseYaml(data):
    try:
        import yaml
    except ImportError:
        yaml = importFromInlineCopy("yaml", must_exist=True)

    try:
        yaml_load_function = yaml.safe_load
    except AttributeError:
        yaml_load_function = yaml.load

    return yaml_load_function(data)


def parsePackageYaml(package_name, filename):
    return Yaml(
        filename=filename, data=parseYaml(pkgutil.get_data(package_name, filename))
    )
