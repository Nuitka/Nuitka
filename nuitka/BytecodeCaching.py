#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Caching of compiled code.

Initially this deals with preserving compiled module state after bytecode demotion
such that it allows to restore it directly.
"""

import os
import sys

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.importing.Importing import locateModule, makeModuleUsageAttempt
from nuitka.ModuleRegistry import getModuleOptimizationTimingInfos
from nuitka.plugins.Plugins import Plugins
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.FileOperations import makePath
from nuitka.utils.Hashing import Hash, getStringHash
from nuitka.utils.Json import loadJsonFromFilename, writeJsonToFilename
from nuitka.utils.ModuleNames import ModuleName
from nuitka.Version import version_string


def getBytecodeCacheDir():
    return getCacheDir("module-cache")


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
_cache_format_version = 7


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

    for module_used in data["modules_used"]:
        used_module_name = ModuleName(module_used["module_name"])

        # Retry the module scan to see if it still gives same result
        if module_used["finding"] == "relative":
            _used_module_name, filename, module_kind, finding = locateModule(
                module_name=used_module_name.getBasename(),
                parent_package=used_module_name.getPackageName(),
                level=1,
            )
        else:
            _used_module_name, filename, module_kind, finding = locateModule(
                module_name=used_module_name, parent_package=None, level=0
            )

        if (
            finding != module_used["finding"]
            or module_kind != module_used["module_kind"]
        ):
            assert module_name != "email._header_value_parser", (
                finding,
                module_used["finding"],
            )

            return None

        result.add(
            makeModuleUsageAttempt(
                module_name=used_module_name,
                filename=filename,
                finding=module_used["finding"],
                module_kind=module_used["module_kind"],
                # TODO: Level might have to be dropped.
                level=0,
                # We store only the line number, so this cheats it to at full one.
                source_ref=source_ref.atLineNumber(module_used["source_ref_line"]),
                reason=module_used["reason"],
            )
        )

    for module_used in data["distribution_names"]:
        # TODO: Consider distributions found and not found and return None if
        # something changed there.
        pass

    # The Json doesn't store integer keys.
    for pass_timing_info in data["timing_infos"]:
        pass_timing_info[3] = dict(
            (int(key), value) for (key, value) in pass_timing_info[3].items()
        )

    return result, data["timing_infos"]


def writeImportedModulesNamesToCache(
    module_name,
    source_code,
    used_modules,
    distribution_names,
):
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
        "distribution_names": distribution_names,
        "timing_infos": getModuleOptimizationTimingInfos(module_name),
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
