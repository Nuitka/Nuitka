#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" This to keep track of used modules.

    There is a set of root modules, which are user specified, and must be
    processed. As they go, they add more modules to active modules list
    and move done modules out of it.

    That process can be restarted and modules will be fetched back from
    the existing set of modules.
"""

import collections
import os

from nuitka.containers.Namedtuples import makeNamedtupleClass
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.PythonVersions import python_version
from nuitka.utils.CStrings import decodePythonIdentifierFromC

# One or more root modules, i.e. entry points that must be there.
root_modules = OrderedSet()

# To be traversed modules
active_modules = OrderedSet()

# Information about why a module became active.
active_modules_info = {}

ActiveModuleInfo = collections.namedtuple(
    "ActiveModuleInfo", ("using_module", "usage_tag", "reason", "source_ref")
)

# Already traversed modules
done_modules = set()


def addRootModule(module):
    root_modules.add(module)


def getRootModules():
    return root_modules


def getRootTopModule():
    top_module = next(iter(root_modules))

    assert top_module.isTopModule(), top_module

    return top_module


def hasRootModule(module_name):
    for module in root_modules:
        if module.getFullName() == module_name:
            return True

    return False


def replaceRootModule(old, new):
    # Using global here, as this is really a singleton, in the form of a module,
    # pylint: disable=global-statement
    global root_modules
    new_root_modules = OrderedSet()

    for module in root_modules:
        new_root_modules.add(module if module is not old else new)

    assert len(root_modules) == len(new_root_modules)

    root_modules = new_root_modules


def getUncompiledModules():
    result = set()

    for module in getDoneModules():
        if module.isUncompiledPythonModule():
            result.add(module)

    return tuple(sorted(result, key=lambda module: module.getFullName()))


def getCompiledModules():
    result = set()

    for module in getDoneModules():
        if module.isCompiledPythonModule():
            result.add(module)

    return tuple(sorted(result, key=lambda module: module.getFullName()))


def getUncompiledTechnicalModules():
    result = set()

    for module in getDoneModules():
        if module.isUncompiledPythonModule() and module.isTechnical():
            result.add(module)

    return tuple(sorted(result, key=lambda module: module.getFullName()))


def getUncompiledNonTechnicalModules():
    result = set()

    for module in getDoneModules():
        if module.isUncompiledPythonModule():
            result.add(module)

    return tuple(sorted(result, key=lambda module: module.getFullName()))


def _normalizeModuleFilename(filename):
    if python_version >= 0x300:
        filename = filename.replace("__pycache__", "")

        suffix = ".cpython-%d.pyc" % (python_version // 10)

        if filename.endswith(suffix):
            filename = filename[: -len(suffix)] + ".py"
    else:
        if filename.endswith(".pyc"):
            filename = filename[:-3] + ".py"

    if os.path.basename(filename) == "__init__.py":
        filename = os.path.dirname(filename)

    return filename


def startTraversal():
    # Using global here, as this is really a singleton, in the form of a module,
    # pylint: disable=global-statement
    global active_modules, done_modules, active_modules_info

    active_modules = OrderedSet(root_modules)

    active_modules_info = {}
    for root_module in root_modules:
        active_modules_info[root_module] = ActiveModuleInfo(
            using_module=None,
            usage_tag="root_module",
            reason="Root module",
            source_ref=None,
        )
    done_modules = set()

    for active_module in active_modules:
        active_module.startTraversal()


def addUsedModule(module, using_module, usage_tag, reason, source_ref):
    if module not in done_modules and module not in active_modules:
        active_modules.add(module)

        active_modules_info[module] = ActiveModuleInfo(
            using_module=using_module,
            usage_tag=usage_tag,
            reason=reason,
            source_ref=source_ref,
        )

        module.startTraversal()


def nextModule():
    if active_modules:
        result = active_modules.pop()
        done_modules.add(result)

        return result
    else:
        return None


def getRemainingModulesCount():
    return len(active_modules)


def getDoneModulesCount():
    return len(done_modules)


def getDoneModules():
    return sorted(done_modules, key=lambda module: (module.getFullName(), module.kind))


def hasDoneModule(module_name):
    return any(module.getFullName() == module_name for module in done_modules)


def getModuleInclusionInfoByName(module_name):
    for module, info in active_modules_info.items():
        if module.getFullName() == module_name:
            return info

    return None


def getModuleFromCodeName(code_name):
    module_name = decodePythonIdentifierFromC(code_name)

    # TODO: We need something to just load modules.
    for module in root_modules:
        if module.getCodeName() == module_name:
            return module

    assert False, code_name


def getOwnerFromCodeName(code_name):
    code_name = decodePythonIdentifierFromC(code_name)

    if "$$$" in code_name:
        module_code_name, _function_code_name = code_name.split("$$$", 1)

        module = getModuleFromCodeName(module_code_name)
        return module.getFunctionFromCodeName(code_name)
    else:
        return getModuleFromCodeName(code_name)


def getModuleByName(module_name):
    for module in active_modules:
        if module.getFullName() == module_name:
            return module

    for module in done_modules:
        if module.getFullName() == module_name:
            return module

    return None


module_influencing_plugins = {}


def addModuleInfluencingCondition(
    module_name, plugin_name, condition, control_tags, result
):
    if module_name not in module_influencing_plugins:
        module_influencing_plugins[module_name] = OrderedSet()
    module_influencing_plugins[module_name].add(
        (plugin_name, "condition-used", (condition, tuple(control_tags), result))
    )


def addModuleInfluencingVariable(
    module_name, config_module_name, plugin_name, variable_name, control_tags, result
):
    if module_name not in module_influencing_plugins:
        module_influencing_plugins[module_name] = OrderedSet()
    module_influencing_plugins[module_name].add(
        (
            plugin_name,
            "variable-used",
            (variable_name, tuple(control_tags), repr(result), config_module_name),
        )
    )


def addModuleInfluencingParameter(
    module_name, plugin_name, parameter_name, condition_tags_used, result
):
    if module_name not in module_influencing_plugins:
        module_influencing_plugins[module_name] = OrderedSet()
    module_influencing_plugins[module_name].add(
        (
            plugin_name,
            "parameter-used",
            (parameter_name, tuple(condition_tags_used), result),
        )
    )


def addModuleInfluencingDetection(
    module_name, plugin_name, detection_name, detection_value
):
    if module_name not in module_influencing_plugins:
        module_influencing_plugins[module_name] = OrderedSet()
    module_influencing_plugins[module_name].add(
        (plugin_name, "detection", (detection_name, detection_value))
    )


def getModuleInfluences(module_name):
    return module_influencing_plugins.get(module_name, ())


# Information about how long the optimization took.
module_timing_infos = {}


ModuleOptimizationTimingInfo = makeNamedtupleClass(
    "ModuleOptimizationTimingInfo",
    ("pass_number", "time_used", "micro_passes", "merge_counts"),
)


def addModuleOptimizationTimeInformation(
    module_name, pass_number, time_used, micro_passes, merge_counts
):
    module_timing_info = list(module_timing_infos.get(module_name, []))

    # Do not record cached bytecode loaded timing information, not useful
    # and duplicate, we want the original values.
    if pass_number == 1 and len(module_timing_info) == 1:
        assert micro_passes == 0
        return

    module_timing_info.append(
        ModuleOptimizationTimingInfo(
            pass_number=pass_number,
            time_used=time_used,
            micro_passes=micro_passes,
            merge_counts=merge_counts,
        )
    )
    module_timing_infos[module_name] = tuple(module_timing_info)


def getModuleOptimizationTimingInfos(module_name):
    return module_timing_infos.get(module_name, ())


def setModuleOptimizationTimingInfos(module_name, timing_infos):
    module_timing_infos[module_name] = [
        ModuleOptimizationTimingInfo(*timing_info) for timing_info in timing_infos
    ]


def getImportedModuleNames():
    result = OrderedSet()

    for module in getDoneModules():
        for used_module in module.getUsedModules():
            module_name = used_module.module_name

            if hasDoneModule(module_name):
                continue

            result.add(module_name)

    return result


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
