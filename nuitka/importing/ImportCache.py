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
""" Import cache.

This is not about caching the search of modules in the file system, but about
maintaining a cache of module trees built.

It can happen that modules become unused, and then dropped from active modules,
and then later active again, via another import, and in this case, we should
not start anew.
"""

from logging import warning

from nuitka.plugins.PluginBase import Plugins
from nuitka.utils import Utils

imported_modules = {}
imported_by_name = {}

def addImportedModule(module_relpath, imported_module):
    if (module_relpath, "__main__") in imported_modules:
        warning("""\
Re-importing __main__ module via its filename duplicates the module.""")

    key = module_relpath, imported_module.getFullName()

    if key in imported_modules:
        assert imported_module is imported_modules[ key ], key
    else:
        Plugins.onModuleDiscovered(imported_module)

    imported_modules[ key ] = imported_module
    imported_by_name[ imported_module.getFullName() ] = imported_module

def isImportedModuleByPath(module_relpath):
    module_name = Utils.basename(module_relpath)

    if module_name.endswith(".py"):
        module_name = module_name[:-3]

    key = module_relpath, module_name

    return key in imported_modules

def isImportedModuleByName(full_name):
    return full_name in imported_by_name

def getImportedModuleByName(full_name):
    return imported_by_name[ full_name ]

def getImportedModuleByPath(module_relpath):
    module_name = Utils.basename(module_relpath)

    if module_name.endswith(".py"):
        module_name = module_name[:-3]

    key = module_relpath, module_name

    return imported_modules[ key ]
