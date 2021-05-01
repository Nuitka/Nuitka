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
""" Demotion of compiled modules to bytecode modules.

"""

import hashlib
import marshal
import os

from nuitka import Options
from nuitka.importing.ImportCache import (
    isImportedModuleByName,
    replaceImportedModule,
)
from nuitka.importing.Importing import getPackageSearchPath, isPackageDir
from nuitka.ModuleRegistry import replaceRootModule
from nuitka.nodes.ModuleNodes import makeUncompiledPythonModule
from nuitka.plugins.Plugins import Plugins
from nuitka.Tracing import inclusion_logger
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.FileOperations import listDir, makePath, getFileContents
from nuitka.utils.Importing import getAllModuleSuffixes


def getModuleImportableFilesHash(full_name):
    package_name = full_name.getPackageName()

    paths = getPackageSearchPath(None)

    if package_name is not None:
        paths += getPackageSearchPath(package_name)

    all_suffixes = getAllModuleSuffixes()

    result_hash = hashlib.md5()

    for count, path in enumerate(paths):
        if not os.path.isdir(path):
            continue

        for fullname, filename in listDir(path):
            if isPackageDir(fullname) or filename.endswith(all_suffixes):
                entry = "%s:%s" % (count, filename)

                if str is not bytes:
                    entry = entry.encode("utf8")

                result_hash.update(entry)

    return result_hash.hexdigest()


def _getCacheFilename(full_name, module_importables_hash, extension):
    module_cache_dir = os.path.join(getCacheDir(), "module-imports-cache")
    makePath(module_cache_dir)

    return os.path.join(
        module_cache_dir, "%s-%s.%s" % (full_name.asString(), module_importables_hash, extension)
    )

def _loadBytecodeFromCache(cache_filename):
    return getFileContents(cache_filename, "rb")

def demoteCompiledModuleToBytecode(module):
    """Demote a compiled module to uncompiled (bytecode)."""

    full_name = module.getFullName()
    filename = module.getCompileTimeFilename()

    if Options.isShowProgress():
        inclusion_logger.info(
            "Demoting module %r to bytecode from %r." % (full_name, filename)
        )

    module_importables_hash = getModuleImportableFilesHash(full_name)
    if os.path.exists(_getCacheFilename(full_name, module_importables_hash, "txt")):
        inclusion_logger.info("The module %r is already demoted" % (full_name))
        already_demoted = True

    else:
        already_demoted = False
        source_code = module.getSourceCode()

        # Second chance for plugins to modify source code just before turning it
        # to bytecode.
        source_code = Plugins.onFrozenModuleSourceCode(
            module_name=full_name, is_package=False, source_code=source_code
        )

        bytecode = compile(source_code, filename, "exec", dont_inherit=True)

        bytecode = Plugins.onFrozenModuleBytecode(
            module_name=full_name, is_package=False, bytecode=bytecode
        )

    uncompiled_module = makeUncompiledPythonModule(
        module_name=full_name,
        filename=filename,
        bytecode=marshal.dumps(bytecode) if not already_demoted else _loadBytecodeFromCache(_getCacheFilename(
            full_name, module_importables_hash, "dat")
        ),
        is_package=module.isCompiledPythonPackage(),
        user_provided=True,
        technical=False,
    )

    used_modules = module.getUsedModules()
    print(used_modules)
    uncompiled_module.setUsedModules(used_modules)
    module.finalize()

    if isImportedModuleByName(full_name):
        replaceImportedModule(old=module, new=uncompiled_module)
    replaceRootModule(old=module, new=uncompiled_module)

    from nuitka.plugins.PluginBase import isTriggerModule, replaceTriggerModule

    if isTriggerModule(module):
        replaceTriggerModule(old=module, new=uncompiled_module)

    if not already_demoted:
        with open(_getCacheFilename(full_name, module_importables_hash, "txt"), "w") as modules_cache_file:
            for module_name, _filename in used_modules:
                modules_cache_file.write(module_name.asString() + "\n")

        with open(_getCacheFilename(full_name, module_importables_hash, "dat"), "wb") as bytecode_cache_file:
            bytecode_cache_file.write(marshal.dumps(bytecode))
