#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" This module abstracts what site.py is normally doing in .pth files.

This tries to extract "namespaces" packages that were manually created and
point to package directories, which need no "__init__.py" to count as a
package. Nuitka will pretend for those that there be one, but without content.
"""

import sys

from nuitka.utils import Utils


def getLoadedPackages():
    """ Extract packages with no __file__, i.e. they got added manually.

        They are frequently created with "*.pth" files that then check for the
        "__init__.py" to exist, and when it doesn't, then they create during the
        loading of "site.py" an package with "__path__" set.
    """

    for module_name, module in sys.modules.items():
        if not hasattr(module, "__path__"):
            continue

        if hasattr(module, "__file__"):
            continue

        yield module_name, module


def detectPreLoadedPackagePaths():
    result = {}

    for package_name, module  in getLoadedPackages():
        result[package_name] = list(module.__path__)

    return result


preloaded_packages = None

def getPreloadedPackagePaths():
    # We need to set this from the outside, pylint: disable=W0603
    global preloaded_packages

    if preloaded_packages is None:
        preloaded_packages = detectPreLoadedPackagePaths()

    return preloaded_packages


def setPreloadedPackagePaths(value):
    # We need to set this from the outside, pylint: disable=W0603
    global preloaded_packages

    preloaded_packages = value


def getPreloadedPackagePath(package_name):
    return getPreloadedPackagePaths().get(package_name, None)


def isPreloadedPackagePath(path):
    path = Utils.normcase(path)

    for paths in getPreloadedPackagePaths().values():
        for element in paths:
            if Utils.normcase(element) == path:
                return True

    return False
