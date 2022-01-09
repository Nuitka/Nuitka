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
""" Caching of compiled code.

Initially this deals with preserving compiled module state after bytecode demotion
such that it allows to restore it directly.
"""

import hashlib
import os

from nuitka import Options
from nuitka.importing.Importing import getPackageSearchPath, isPackageDir
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.FileOperations import (
    getFileContents,
    listDir,
    makePath,
    openTextFile,
)
from nuitka.utils.Importing import getAllModuleSuffixes
from nuitka.utils.ModuleNames import ModuleName


def _getCacheDir():
    module_cache_dir = os.path.join(getCacheDir(), "module-cache")
    makePath(module_cache_dir)
    return module_cache_dir


def _getCacheFilename(module_name, extension):
    return os.path.join(_getCacheDir(), "%s.%s" % (module_name, extension))


def getSourceCodeHash(source_code):
    if str is not bytes:
        source_code = source_code.encode("utf8")

    return hashlib.md5(source_code).hexdigest()


def makeCacheName(module_name, source_code):
    module_importables_hash = getModuleImportableFilesHash(module_name)

    return (
        module_name.asString()
        + "@"
        + module_importables_hash
        + "@"
        + getSourceCodeHash(source_code)
    )


def hasCachedImportedModulesNames(module_name, source_code):
    cache_name = makeCacheName(module_name, source_code)

    # TODO: Disabled using cache results for now.
    if not Options.isExperimental("bytecode-cache"):
        return False

    return os.path.exists(_getCacheFilename(cache_name, "txt"))


def getCachedImportedModulesNames(module_name, source_code):
    cache_name = makeCacheName(module_name, source_code)

    return [
        ModuleName(line)
        for line in getFileContents(_getCacheFilename(cache_name, "txt"))
        .strip()
        .split("\n")
    ]


def writeImportedModulesNamesToCache(module_name, source_code, used_modules):
    cache_name = makeCacheName(module_name, source_code)

    with openTextFile(_getCacheFilename(cache_name, "txt"), "w") as modules_cache_file:
        for used_module_name, _filename, _finding, _level, _source_ref in used_modules:
            modules_cache_file.write(used_module_name.asString() + "\n")


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
