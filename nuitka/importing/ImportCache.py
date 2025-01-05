#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Import cache.

This is not about caching the search of modules in the file system, but about
maintaining a cache of module trees built.

It can happen that modules become unused, and then dropped from active modules,
and then later active again, via another import, and in this case, we should
not start anew, but reuse what we already found out about it.
"""

import os

from nuitka.plugins.Plugins import Plugins
from nuitka.utils.Importing import hasPackageDirFilename

imported_modules = {}
imported_by_name = {}


def addImportedModule(imported_module):
    module_filename = os.path.abspath(imported_module.getFilename())

    if hasPackageDirFilename(module_filename):
        module_filename = os.path.dirname(module_filename)

    key = (module_filename, imported_module.getFullName())

    if key in imported_modules:
        assert imported_module is imported_modules[key], key
    else:
        Plugins.onModuleDiscovered(imported_module)

    imported_modules[key] = imported_module
    imported_by_name[imported_module.getFullName()] = imported_module

    # We don't expect that to happen.
    assert not imported_module.isMainModule()


def isImportedModuleByName(full_name):
    return full_name in imported_by_name


def getImportedModuleByName(full_name):
    return imported_by_name[full_name]


def getImportedModuleByNameAndPath(full_name, module_filename):
    if module_filename is None:
        # pyi deps only
        return getImportedModuleByName(full_name)

    # For caching we use absolute paths only.
    module_filename = os.path.abspath(module_filename)

    if hasPackageDirFilename(module_filename):
        module_filename = os.path.dirname(module_filename)

    # KeyError is valid result.
    return imported_modules[module_filename, full_name]


def replaceImportedModule(old, new):
    for key, value in imported_by_name.items():
        if value == old:
            imported_by_name[key] = new
            break
    else:
        assert False, (old, new)

    for key, value in imported_modules.items():
        if value == old:
            imported_modules[key] = new
            break
    else:
        assert False, (old, new)


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
