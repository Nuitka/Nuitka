#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Registry for hard import data.

Part of it is static, but modules can get at during scan by plugins that
know how to handle these.
"""

import os
import sys

from nuitka import Options
from nuitka.Constants import isConstant
from nuitka.nodes.BuiltinOpenNodes import makeBuiltinOpenRefNode
from nuitka.nodes.ConstantRefNodes import ExpressionConstantSysVersionInfoRef
from nuitka.PythonVersions import (
    getFutureModuleKeys,
    getImportlibSubPackages,
    python_version,
)
from nuitka.utils.Utils import isWin32Windows

# These module are supported in code generation to be imported the hard way.
hard_modules = set(
    (
        "os",
        "ntpath",
        "posixpath",
        # TODO: Add mac path package too
        "sys",
        "types",
        "typing",
        "__future__",
        "importlib",
        "importlib.resources",
        "importlib.metadata",
        "_frozen_importlib",
        "_frozen_importlib_external",
        "pkgutil",
        "functools",
        "sysconfig",
        "unittest",
        "unittest.mock",
        # "cStringIO",
        "io",
        "_io",
        "ctypes",
        "ctypes.wintypes",
        "ctypes.macholib",
        # TODO: Once generation of nodes for functions exists.
        # "platform",
        "builtins",
    )
)

hard_modules_aliases = {
    "os.path": os.path.__name__,
}

# Lets put here, hard modules that are kind of backports only.
hard_modules_stdlib = hard_modules
hard_modules_non_stdlib = set(
    (
        "site",
        "pkg_resources",
        "importlib_metadata",
        "importlib_resources",
        "tensorflow",
        # TODO: Disabled for now, keyword only arguments and star list argument
        # are having ordering issues for call matching and code generation.
        # "networkx.utils.decorators",
    )
)

hard_modules = hard_modules | hard_modules_non_stdlib

hard_modules_version = {
    "cStringIO": (None, 0x300, None),
    "typing": (0x350, None, None),
    "_frozen_importlib": (0x300, None, None),
    "_frozen_importlib_external": (0x350, None, None),
    "importlib.resources": (0x370, None, None),
    "importlib.metadata": (0x380, None, None),
    "ctypes.wintypes": (None, None, "win32"),
    "builtin": (0x300, None, None),
    "unittest.mock": (0x300, None, None),
}

hard_modules_limited = ("importlib.metadata", "ctypes.wintypes", "importlib_metadata")


# The modules were added during compile time, no helper code available.
hard_modules_dynamic = set()


def isHardModule(module_name):
    if module_name not in hard_modules:
        return False

    min_version, max_version, os_limit = hard_modules_version.get(
        module_name, (None, None, None)
    )

    if min_version is not None and python_version < min_version:
        return False

    if max_version is not None and python_version >= max_version:
        return False

    if os_limit is not None:
        if os_limit == "win32":
            return isWin32Windows()

    return True


# These modules can cause issues if imported during compile time.
hard_modules_trust_with_side_effects = set(
    [
        "site",
        "tensorflow",
        "importlib_metadata",
        # TODO: Disabled for now, keyword only arguments and star list argument are
        # having ordering issues for call matching and code generation.
        # "networkx.utils.decorators"
    ]
)
if not isWin32Windows():
    # Crashing on anything but Windows.
    hard_modules_trust_with_side_effects.add("ctypes.wintypes")


def isHardModuleWithoutSideEffect(module_name):
    return (
        module_name in hard_modules
        and module_name not in hard_modules_trust_with_side_effects
    )


trust_undefined = 0
trust_constant = 1
trust_exist = 2
trust_module = trust_exist
trust_future = trust_exist
trust_importable = 3
trust_node = 4
trust_may_exist = 5
trust_not_exist = 6
trust_node_factory = {}

module_importlib_trust = dict(
    (key, trust_importable) for key in getImportlibSubPackages()
)

if "metadata" not in module_importlib_trust:
    module_importlib_trust["metadata"] = trust_undefined
if "resources" not in module_importlib_trust:
    module_importlib_trust["resources"] = trust_undefined

module_sys_trust = {
    "version": trust_constant,
    "hexversion": trust_constant,  # spell-checker: ignore hexversion
    "platform": trust_constant,
    "maxsize": trust_constant,
    "byteorder": trust_constant,
    "builtin_module_names": trust_constant,
    # TODO: Their lookups would have to be nodes, and copy with them being
    # potentially unassigned.
    #    "stdout": trust_exist,
    #    "stderr": trust_exist,
    "exit": trust_node,
}

if python_version < 0x270:
    module_sys_trust["version_info"] = trust_constant
else:
    module_sys_trust["version_info"] = trust_node
    trust_node_factory[("sys", "version_info")] = ExpressionConstantSysVersionInfoRef

module_builtins_trust = {}
if python_version >= 0x300:
    module_builtins_trust["open"] = trust_node
    trust_node_factory[("builtins", "open")] = makeBuiltinOpenRefNode

if python_version < 0x300:
    module_sys_trust["exc_type"] = trust_may_exist
    module_sys_trust["exc_value"] = trust_may_exist
    module_sys_trust["exc_traceback"] = trust_may_exist

    module_sys_trust["maxint"] = trust_constant
    module_sys_trust["subversion"] = trust_constant
else:
    module_sys_trust["exc_type"] = trust_not_exist
    module_sys_trust["exc_value"] = trust_not_exist
    module_sys_trust["exc_traceback"] = trust_not_exist


# If we are not a module, we are not in REPL mode.
if not Options.shallMakeModule():
    module_sys_trust["ps1"] = trust_not_exist
    module_sys_trust["ps2"] = trust_not_exist

module_typing_trust = {
    "TYPE_CHECKING": trust_constant,
}


def makeTypingModuleTrust():
    result = {}

    if python_version >= 0x350:
        import typing

        constant_typing_values = ("TYPE_CHECKING", "Text")
        for name in typing.__all__:
            if name not in constant_typing_values:
                trust = trust_exist
                if Options.is_debug:
                    assert not isConstant(getattr(typing, name))
            else:
                trust = trust_constant
                if Options.is_debug:
                    assert isConstant(getattr(typing, name))

            result[name] = trust


module_os_trust = {
    "name": trust_constant,
    "listdir": trust_node,
    "stat": trust_node,
    "lstat": trust_node,
    "curdir": trust_constant,
    "pardir": trust_constant,
    "sep": trust_constant,
    "extsep": trust_constant,
    "altsep": trust_constant,
    "pathsep": trust_constant,
    "linesep": trust_constant,
}

module_os_path_trust = {
    "exists": trust_node,
    "isfile": trust_node,
    "isdir": trust_node,
    "basename": trust_node,
    "dirname": trust_node,
    "abspath": trust_node,
    "normpath": trust_node,
}


module_ctypes_trust = {
    "CDLL": trust_node,
}

# module_platform_trust = {"python_implementation": trust_function}

hard_modules_trust = {
    "os": module_os_trust,
    "ntpath": module_os_path_trust if os.path.__name__ == "ntpath" else {},
    "posixpath": module_os_path_trust if os.path.__name__ == "posixpath" else {},
    "sys": module_sys_trust,
    #     "platform": module_platform_trust,
    "types": {},
    "typing": module_typing_trust,
    "__future__": dict((key, trust_future) for key in getFutureModuleKeys()),
    "importlib": module_importlib_trust,
    "importlib.metadata": {
        "version": trust_node,
        "distribution": trust_node,
        "metadata": trust_node,
        "entry_points": trust_node,
        "PackageNotFoundError": trust_exist,
    },
    "importlib_metadata": {
        "version": trust_node,
        "distribution": trust_node,
        "metadata": trust_node,
        "entry_points": trust_node,
        "PackageNotFoundError": trust_exist,
    },
    "_frozen_importlib": {},
    "_frozen_importlib_external": {},
    "pkgutil": {"get_data": trust_node},
    "functools": {"partial": trust_exist},
    "sysconfig": {},
    "unittest": {"mock": trust_module, "main": trust_exist},
    "unittest.mock": {},
    "io": {"BytesIO": trust_exist, "StringIO": trust_exist},
    "_io": {"BytesIO": trust_exist, "StringIO": trust_exist},
    # "cStringIO": {"StringIO": trust_exist},
    "pkg_resources": {
        "require": trust_node,
        "get_distribution": trust_node,
        "iter_entry_points": trust_node,
        "resource_string": trust_node,
        "resource_stream": trust_node,
    },
    "importlib.resources": {
        "read_binary": trust_node,
        "read_text": trust_node,
        "files": trust_node,
    },
    "importlib_resources": {
        "read_binary": trust_node,
        "read_text": trust_node,
        "files": trust_node,
    },
    "ctypes": module_ctypes_trust,
    "site": {},
    "ctypes.wintypes": {},
    "ctypes.macholib": {},
    "builtins": module_builtins_trust,
    "tensorflow": {"function": trust_node},
    # TODO: Disabled for now, keyword only arguments and star list argument are
    # having ordering issues for call matching and code generation.
    # "networkx.utils.decorators": {"argmap": trust_node},
}


def _addHardImportNodeClasses():
    from nuitka.nodes.HardImportNodesGenerated import hard_import_node_classes

    for hard_import_node_class, spec in hard_import_node_classes.items():
        module_name, function_name = spec.name.rsplit(".", 1)

        if module_name in hard_modules_aliases:
            module_name = hard_modules_aliases.get(module_name)

        trust_node_factory[(module_name, function_name)] = hard_import_node_class

        # hard_modules_trust[module_name][function_name] = trust_node


_addHardImportNodeClasses()

# Remove this one again, not available on Windows, but the node generation does
# not know that.
if isWin32Windows():
    module_os_trust["uname"] = trust_not_exist


def _checkHardModules():
    for module_name in hard_modules:
        assert module_name in hard_modules_trust, module_name

    for module_name, trust in hard_modules_trust.items():
        assert module_name in hard_modules, module_name

        for attribute_name, trust_value in trust.items():
            if trust_value is trust_node:
                assert (
                    module_name,
                    attribute_name,
                ) in trust_node_factory or os.path.basename(sys.argv[0]).startswith(
                    "generate-"
                ), (
                    module_name,
                    attribute_name,
                )


_checkHardModules()


def addModuleTrust(module_name, attribute_name, trust_value):
    hard_modules_trust[module_name][attribute_name] = trust_value


def addModuleSingleAttributeNodeFactory(module_name, attribute_name, node_class):
    hard_modules_trust[module_name][attribute_name] = trust_node
    trust_node_factory[(module_name, attribute_name)] = node_class


def addModuleAttributeFactory(module_name, attribute_name, node_class):
    trust_node_factory[(module_name, attribute_name)] = node_class


def addModuleDynamicHard(module_name):
    hard_modules.add(module_name)
    hard_modules_dynamic.add(module_name)
    hard_modules_non_stdlib.add(module_name)
    hard_modules_trust_with_side_effects.add(module_name)

    if module_name not in hard_modules_trust:
        hard_modules_trust[module_name] = {}


def isHardModuleDynamic(module_name):
    return module_name in hard_modules_dynamic


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
