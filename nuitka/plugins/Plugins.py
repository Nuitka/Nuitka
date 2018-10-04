#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
"""

Plugins: Welcome to Nuitka! This is your shortest way to become part of it.

This is to provide the base class for all plug-ins. Some of which are part of
proper Nuitka, and some of which are waiting to be created and submitted for
inclusion by you.

The base class in PluginBase will serve as documentation of available.

"""

from __future__ import print_function

import os
from logging import info
import sys

from nuitka import Options
from nuitka.PythonVersions import python_version
from nuitka.ModuleRegistry import addUsedModule

from .PluginBase import post_modules, pre_modules, UserPluginBase
from .standard.DataFileCollectorPlugin import NuitkaPluginDataFileCollector
from .standard.ImplicitImports import NuitkaPluginPopularImplicitImports
from .standard.PmwPlugin import NuitkaPluginDetectorPmw, NuitkaPluginPmw

from .standard.ConsiderPyLintAnnotationsPlugin import (  # isort:skip
    NuitkaPluginDetectorPylintEclipseAnnotations,
    NuitkaPluginPylintEclipseAnnotations
)
from .standard.MultiprocessingPlugin import (  # isort:skip
    NuitkaPluginDetectorMultiprocessingWorkarounds,
    NuitkaPluginMultiprocessingWorkarounds
)
from .standard.PySidePyQtPlugin import (  # isort:skip
    NuitkaPluginDetectorPyQtPySidePlugins,
    NuitkaPluginPyQtPySidePlugins
)
# The standard plug-ins have their list hard-coded here. User plug-ins will
# be scanned later, TODO.

active_plugin_list = [
    NuitkaPluginPopularImplicitImports(),
    NuitkaPluginDataFileCollector(),
]

# List of optional plug-in classes. Until we have the meta class to do it, just
# add your class here. The second one is a detector, which is supposed to give
# a missing plug-in message, should it find the condition to make it useful.
optional_plugin_classes = (
    (NuitkaPluginMultiprocessingWorkarounds, NuitkaPluginDetectorMultiprocessingWorkarounds),
    (NuitkaPluginPyQtPySidePlugins, NuitkaPluginDetectorPyQtPySidePlugins),
    (NuitkaPluginPylintEclipseAnnotations, NuitkaPluginDetectorPylintEclipseAnnotations),
    (NuitkaPluginPmw, NuitkaPluginDetectorPmw),
)

plugin_name2plugin_classes = dict(
    (plugin[0].plugin_name, plugin)
    for plugin in
    optional_plugin_classes
)


class Plugins(object):
    @staticmethod
    def considerImplicitImports(module, signal_change):
        for plugin in active_plugin_list:
            plugin.considerImplicitImports(module, signal_change)

        # Post load code may have been created, if so indicate it's used.
        full_name = module.getFullName()

        if full_name in post_modules:
            addUsedModule(post_modules[full_name])

        if full_name in pre_modules:
            addUsedModule(pre_modules[full_name])

    @staticmethod
    def considerExtraDlls(dist_dir, module):
        result = []

        for plugin in active_plugin_list:
            for extra_dll in plugin.considerExtraDlls(dist_dir, module):
                assert os.path.isfile(extra_dll[1]), extra_dll[1]

                result.append(extra_dll)

        return result

    @staticmethod
    def removeDllDependencies(dll_filename, dll_filenames):
        dll_filenames = tuple(sorted(dll_filenames))

        result = []

        for plugin in active_plugin_list:
            for removed_dll in plugin.removeDllDependencies(dll_filename, dll_filenames):
                result.append(removed_dll)

        return result

    @staticmethod
    def considerDataFiles(module):
        for plugin in active_plugin_list:
            for value in plugin.considerDataFiles(module):
                yield value

    @staticmethod
    def onModuleDiscovered(module):
        for plugin in active_plugin_list:
            plugin.onModuleDiscovered(module)

    @staticmethod
    def onModuleSourceCode(module_name, source_code):
        assert type(module_name) is str
        assert type(source_code) is str

        for plugin in active_plugin_list:
            source_code = plugin.onModuleSourceCode(module_name, source_code)
            assert type(source_code) is str

        return source_code

    @staticmethod
    def onFrozenModuleSourceCode(module_name, is_package, source_code):
        assert type(module_name) is str
        assert type(source_code) is str

        for plugin in active_plugin_list:
            source_code = plugin.onFrozenModuleSourceCode(module_name, is_package, source_code)
            assert type(source_code) is str

        return source_code

    @staticmethod
    def onFrozenModuleBytecode(module_name, is_package, bytecode):
        assert type(module_name) is str
        assert bytecode.__class__.__name__ == "code"

        for plugin in active_plugin_list:
            bytecode = plugin.onFrozenModuleBytecode(module_name, is_package, bytecode)
            assert bytecode.__class__.__name__ == "code"

        return bytecode

    @staticmethod
    def onModuleEncounter(module_filename, module_name, module_package,
                          module_kind):
        result = False

        for plugin in active_plugin_list:
            must_recurse = plugin.onModuleEncounter(
                module_filename,
                module_name,
                module_package,
                module_kind
            )

            result = result or must_recurse

        return result

    @staticmethod
    def considerFailedImportReferrals(module_name):
        for plugin in active_plugin_list:
            new_module_name = plugin.considerFailedImportReferrals(module_name)

            if new_module_name is not None:
                return new_module_name

        return None

    @staticmethod
    def suppressBuiltinImportWarning(module, source_ref):
        for plugin in active_plugin_list:
            if plugin.suppressBuiltinImportWarning(module, source_ref):
                return True

        return False

    @staticmethod
    def suppressUnknownImportWarning(importing, module_name):
        if importing.isCompiledPythonModule() or importing.isPythonShlibModule():
            importing_module = importing
        else:
            importing_module = importing.getParentModule()

        source_ref = importing.getSourceReference()

        for plugin in active_plugin_list:
            if plugin.suppressUnknownImportWarning(importing_module, module_name, source_ref):
                return True

        return False

    @staticmethod
    def decideCompilation(module_name, source_ref):
        for plugin in active_plugin_list:
            value = plugin.decideCompilation(module_name, source_ref)

            if value is not None:
                assert value in ("compiled", "bytecode")
                return value

        return "compiled"


def listPlugins():
    for plugin_name in sorted(plugin_name2plugin_classes):
        print(plugin_name)

    sys.exit(0)


def isObjectAUserPluginBaseClass(obj):
    try:
        return obj is not UserPluginBase and issubclass(obj, UserPluginBase)
    except TypeError:
        return False


def importFilePy3NewWay(filename):
    import importlib.util   # @UnresolvedImport pylint: disable=I0021,import-error,no-name-in-module
    spec = importlib.util.spec_from_file_location(filename, filename)
    user_plugin_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_plugin_module)
    return user_plugin_module


def importFilePy3OldWay(filename):
    from importlib.machinery import SourceFileLoader  # @UnresolvedImport pylint: disable=I0021,import-error,no-name-in-module
    return SourceFileLoader(filename, filename).load_module(filename)   # pylint: disable=I0021,deprecated-method


def importFilePy2(filename):
    import imp
    return imp.load_source(filename, filename)


def importFile(filename):
    if python_version < 300:
        return importFilePy2(filename)
    if python_version < 350:
        return importFilePy3OldWay(filename)
    return importFilePy3NewWay(filename)


def importUserPlugins():
    for plugin_filename in Options.getUserPlugins():
        if not os.path.exists(plugin_filename):
            sys.exit("Error, cannot find '%s'." % plugin_filename)

        user_plugin_module = importFile(plugin_filename)
        for key in dir(user_plugin_module):
            obj = getattr(user_plugin_module, key)
            if not isObjectAUserPluginBaseClass(obj):
                continue

            plugin_name = getattr(obj, "plugin_name", None)
            if plugin_name and plugin_name not in Options.getPluginsDisabled():
                active_plugin_list.append(obj())
                info("User plugin '%s' loaded." % plugin_filename)


def initPlugins():
    for plugin_name in Options.getPluginsEnabled() + Options.getPluginsDisabled():
        if plugin_name not in plugin_name2plugin_classes:
            sys.exit("Error, unknown plug-in '%s' referenced." % plugin_name)

        if plugin_name in Options.getPluginsEnabled() and \
           plugin_name in Options.getPluginsDisabled():
            sys.exit("Error, conflicting enable/disable of plug-in '%s'." % plugin_name)

    for plugin_name, (plugin_class, plugin_detector) in plugin_name2plugin_classes.items():
        if plugin_name in Options.getPluginsEnabled():
            active_plugin_list.append(
                plugin_class()
            )
        elif plugin_name not in Options.getPluginsDisabled():
            if plugin_detector is not None \
               and Options.shallDetectMissingPlugins() and \
               plugin_detector.isRelevant():
                active_plugin_list.append(
                    plugin_detector()
                )

    importUserPlugins()


initPlugins()
