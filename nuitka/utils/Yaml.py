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
"""

from nuitka.PythonVersions import python_version

from .Importing import importFromInlineCopy


def parseYaml(data):
    if python_version < 0x270:
        yaml = importFromInlineCopy("yaml", must_exist=False)
        return yaml.load(data)
    else:
        try:
            import yaml
        except ImportError:
            yaml = importFromInlineCopy("yaml", must_exist=False)

        return yaml.safe_load(data)
