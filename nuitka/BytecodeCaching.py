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
import sys

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.importing.Importing import locateModule, makeModuleUsageAttempt
from nuitka.plugins.Plugins import Plugins
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.FileOperations import makePath
from nuitka.utils.Hashing import Hash, getStringHash
from nuitka.utils.Json import loadJsonFromFilename, writeJsonToFilename
from nuitka.utils.ModuleNames import ModuleName
from nuitka.Version import version_string


def getBytecodeCacheDir():
    module_cache_dir = os.path.join(getCacheDir(), "module-cache")
    return module_cache_dir


def _getCacheFilename(module_name, extension):
    return os.path.join(getBytecodeCacheDir(), "%s.%s" % (module_name, extension))


def makeCacheName(module_name, source_code):
    module_config_hash = _getModuleConfigHash(module_name)

    return (
        module_name.asString()
        + "@"
        + module_config_hash
        + "@"
        + getStringHash(source_code)
    )


def hasCachedImportedModuleUsageAttempts(module_name, source_code, source_ref):
    result = getCachedImportedModuleUsageAttempts(
        module_name=module_name, source_code=source_code, source_ref=source_ref
    )

    return result is not None


# Bump this is format is changed or enhanced implementation might different ones.
_cache_format_version = 4


def getCachedImportedModuleUsageAttempts(module_name, source_code, source_ref):
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

    result = OrderedSet()

    for module in data["modules_used"]:
        module_name = ModuleName(module["module_name"])

        # Retry the module scan.
        _module_name, filename, module_kind, finding = locateModule(
            module_name=module_name, parent_package=None, level=0
        )

        if finding != module["finding"] or module_kind != module["module_kind"]:
            return None

        result.add(
            makeModuleUsageAttempt(
                module_name=module_name,
                filename=filename,
                finding=module["finding"],
                module_kind=module["module_kind"],
                # TODO: Level might have to be dropped.
                level=0,
                # We store only the line number, so this cheats it to at full one.
                source_ref=source_ref.atLineNumber(module["source_ref_line"]),
            )
        )

    return result


def writeImportedModulesNamesToCache(module_name, source_code, used_modules):
    cache_name = makeCacheName(module_name, source_code)
    cache_filename = _getCacheFilename(cache_name, "json")

    used_modules = [module.asDict() for module in used_modules]
    for module in used_modules:
        module["source_ref_line"] = module["source_ref"].getLineNumber()
        del module["source_ref"]

    data = {
        "file_format_version": _cache_format_version,
        "module_name": module_name.asString(),
        # We use a tuple, so preserve the order.
        "modules_used": used_modules,
    }

    makePath(os.path.dirname(cache_filename))
    writeJsonToFilename(filename=cache_filename, contents=data)


def _getModuleConfigHash(full_name):
    """Calculate hash value for package packages importable for a module of this name."""
    hash_value = Hash()

    # Plugins may change their influence.
    hash_value.updateFromValues(*Plugins.getCacheContributionValues(full_name))

    # Take Nuitka and Python version into account as well, ought to catch code changes.
    hash_value.updateFromValues(version_string, sys.version)

    return hash_value.asHexDigest()
