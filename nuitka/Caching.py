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
""" Caching of compiled code.

Initially this deals with preserving compiled module state after bytecode demotion
such that it allows to restore it directly.
"""

import os

from nuitka.importing.Importing import getPackageSearchPath, isPackageDir
from nuitka.plugins.Plugins import Plugins
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.FileOperations import listDir, makePath
from nuitka.utils.Hashing import Hash, getStringHash
from nuitka.utils.Importing import getAllModuleSuffixes
from nuitka.utils.Json import loadJsonFromFilename, writeJsonToFilename
from nuitka.utils.ModuleNames import ModuleName
from nuitka.Version import version_string


def _getCacheDir():
    module_cache_dir = os.path.join(getCacheDir(), "module-cache")
    makePath(module_cache_dir)
    return module_cache_dir


def _getCacheFilename(module_name, extension):
    return os.path.join(_getCacheDir(), "%s.%s" % (module_name, extension))


def makeCacheName(module_name, source_code):
    module_importables_hash = getModuleImportableFilesHash(module_name)

    return (
        module_name.asString()
        + "@"
        + module_importables_hash
        + "@"
        + getStringHash(source_code)
    )


def hasCachedImportedModulesNames(module_name, source_code):
    result = getCachedImportedModulesNames(module_name, source_code)

    return result is not None


# Bump this is format is changed or enhanced implementation might different ones.
_cache_format_version = 2


def getCachedImportedModulesNames(module_name, source_code):
    cache_name = makeCacheName(module_name, source_code)
    cache_filename = _getCacheFilename(cache_name, "json")

    if not os.path.exists(cache_filename):
        return None

    data = loadJsonFromFilename(cache_filename)

    if data is None:
        return None

    if data.get("file_format_version") != _cache_format_version:
        return None

    if data["module_name"] != module_name:
        return None

    return [
        (ModuleName(used_module_name), line_number)
        for (used_module_name, line_number) in data["modules_used"]
    ]


def writeImportedModulesNamesToCache(module_name, source_code, used_modules):
    cache_name = makeCacheName(module_name, source_code)
    cache_filename = _getCacheFilename(cache_name, "json")

    data = {
        "file_format_version": _cache_format_version,
        "module_name": module_name.asString(),
        # We use a tuple, so preserve the order.
        "modules_used": tuple(
            (used_module_name.asString(), source_ref.getLineNumber())
            for used_module_name, _filename, _finding, _level, source_ref in used_modules
        ),
    }

    writeJsonToFilename(filename=cache_filename, contents=data)


def getModuleImportableFilesHash(full_name):
    """Calculate hash value of packages importable for a module of this name."""
    package_name = full_name.getPackageName()

    paths = getPackageSearchPath(None)

    if package_name is not None:
        paths.update(getPackageSearchPath(package_name))

    all_suffixes = getAllModuleSuffixes()

    result_hash = Hash()

    for path in paths:
        if not os.path.isdir(path):
            continue

        for fullname, filename in listDir(path):
            if isPackageDir(fullname) or filename.endswith(all_suffixes):
                result_hash.updateFromValues(filename, b"\0")

    result_hash.updateFromValues(*Plugins.getCacheContributionValues(full_name))

    # Take Nuitka version into account as well, ought to catch code changes.
    result_hash.updateFromValues(version_string)

    return result_hash.asHexDigest()
