#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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
import pkgutil
import sys
from optparse import OptionGroup

import nuitka.plugins.standard
from nuitka import Options
from nuitka.__past__ import basestring  # pylint: disable=I0021,redefined-builtin
from nuitka.containers.odict import OrderedDict
from nuitka.containers.oset import OrderedSet
from nuitka.ModuleRegistry import addUsedModule
from nuitka.PythonVersions import python_version
from nuitka.utils.ModuleNames import ModuleName

from .PluginBase import NuitkaPluginBase, post_modules, pre_modules

active_plugins = OrderedDict()
plugin_name2plugin_classes = {}
plugin_options = {}
plugin_values = {}
user_plugins = OrderedSet()


def _addActivePlugin(plugin_class, args=True):
    plugin_name = plugin_class.plugin_name

    # No duplicates please.
    assert plugin_name not in active_plugins.keys(), plugin_name

    if args:
        plugin_args = getPluginOptions(plugin_name)
    else:
        plugin_args = {}

    plugin_instance = plugin_class(**plugin_args)
    assert isinstance(plugin_instance, NuitkaPluginBase), plugin_instance

    active_plugins[plugin_name] = plugin_instance


def getActivePlugins():
    """ Return list of active plugins.

    Returns:
        list of plugins

    """

    return active_plugins.values()


def getPluginClass(plugin_name):
    # First, load plugin classes, to know what we are talking about.
    loadPlugins()

    if plugin_name not in plugin_name2plugin_classes:
        sys.exit("Error, unknown plug-in '%s' referenced." % plugin_name)

    return plugin_name2plugin_classes[plugin_name][0]


def loadStandardPluginClasses():
    """ Load plugin files located in 'standard' folder.

    Notes:
        Scan through the 'standard' sub-folder of the folder where this script
        resides. Import each valid Python script and process it as a plugin.
    Returns:
        None
    """

    for loader, name, is_pkg in pkgutil.iter_modules(nuitka.plugins.standard.__path__):
        if is_pkg:
            continue

        module_loader = loader.find_module(name)

        # Ignore bytecode only left overs.
        try:
            if module_loader.get_filename().endswith(".pyc"):
                continue
        except AttributeError:
            # Not a bytecode loader, but e.g. extension module, which is OK in case
            # it was compiled with Nuitka.
            pass

        plugin_module = module_loader.load_module(name)

        plugin_classes = set(
            obj
            for obj in plugin_module.__dict__.values()
            if isObjectAUserPluginBaseClass(obj)
        )

        detectors = [
            plugin_class
            for plugin_class in plugin_classes
            if hasattr(plugin_class, "detector_for")
        ]

        for detector in detectors:
            plugin_class = detector.detector_for
            assert detector.plugin_name is None, detector
            detector.plugin_name = plugin_class.plugin_name

            assert plugin_class in plugin_classes

            plugin_classes.remove(detector)
            plugin_classes.remove(plugin_class)

            plugin_name2plugin_classes[plugin_class.plugin_name] = (
                plugin_class,
                detector,
            )

        for plugin_class in plugin_classes:
            plugin_name2plugin_classes[plugin_class.plugin_name] = plugin_class, None


class Plugins(object):
    @staticmethod
    def isPluginActive(plugin_name):
        """ Is a plugin activated. """

        return plugin_name in active_plugins

    @staticmethod
    def considerImplicitImports(module, signal_change):
        for plugin in getActivePlugins():
            plugin.considerImplicitImports(module, signal_change)

        # Post load code may have been created, if so indicate it's used.
        full_name = module.getFullName()

        if full_name in pre_modules:
            addUsedModule(pre_modules[full_name])

        if full_name in post_modules:
            addUsedModule(post_modules[full_name])

    @staticmethod
    def onStandaloneDistributionFinished(dist_dir):
        """ Let plugins postprocess the distribution folder if standalone
        """
        for plugin in getActivePlugins():
            plugin.onStandaloneDistributionFinished(dist_dir)

        return None

    @staticmethod
    def considerExtraDlls(dist_dir, module):
        result = []

        for plugin in getActivePlugins():
            for extra_dll in plugin.considerExtraDlls(dist_dir, module):
                if not os.path.isfile(extra_dll[0]):
                    sys.exit(
                        "Error, attempting to copy plugin determined filename %r for module %r that is not a file."
                        % (extra_dll[0], module.getFullName())
                    )

                if not os.path.isfile(extra_dll[1]):
                    sys.exit(
                        "Error, copied filename %r for module %r that is not a file."
                        % (extra_dll[1], module.getFullName())
                    )

                result.append(extra_dll)

        return result

    @staticmethod
    def removeDllDependencies(dll_filename, dll_filenames):
        """ Create list of removable shared libraries by scanning through the plugins.

        Args:
            dll_filename: shared library filename
            dll_filenames: list of shared library filenames
        Returns:
            list of removable files
        """
        dll_filenames = tuple(sorted(dll_filenames))

        result = []

        for plugin in getActivePlugins():
            for removed_dll in plugin.removeDllDependencies(
                dll_filename, dll_filenames
            ):
                result.append(removed_dll)

        return result

    @staticmethod
    def considerDataFiles(module):
        """ For a given module, ask plugins for any needed data files it may require.

        Args:
            module: module object
        Yields:
            Data file description pairs, either (source, dest) or (func, dest)
            where the func will be called to create the content dynamically.
        """
        for plugin in getActivePlugins():
            for value in plugin.considerDataFiles(module):
                if value:
                    yield plugin.plugin_name, value

    @staticmethod
    def onModuleDiscovered(module):
        for plugin in getActivePlugins():
            plugin.onModuleDiscovered(module)

    @staticmethod
    def onModuleSourceCode(module_name, source_code):
        assert type(module_name) is ModuleName
        assert type(source_code) is str

        for plugin in getActivePlugins():
            source_code = plugin.onModuleSourceCode(module_name, source_code)
            assert type(source_code) is str

        return source_code

    @staticmethod
    def onFrozenModuleSourceCode(module_name, is_package, source_code):
        assert type(module_name) is ModuleName
        assert type(source_code) is str

        for plugin in getActivePlugins():
            source_code = plugin.onFrozenModuleSourceCode(
                module_name, is_package, source_code
            )
            assert type(source_code) is str

        return source_code

    @staticmethod
    def onFrozenModuleBytecode(module_name, is_package, bytecode):
        assert type(module_name) is ModuleName
        assert bytecode.__class__.__name__ == "code"

        for plugin in getActivePlugins():
            bytecode = plugin.onFrozenModuleBytecode(module_name, is_package, bytecode)
            assert bytecode.__class__.__name__ == "code"

        return bytecode

    @staticmethod
    def onModuleEncounter(module_filename, module_name, module_kind):
        result = False

        for plugin in getActivePlugins():
            must_recurse = plugin.onModuleEncounter(
                module_filename, module_name, module_kind
            )

            result = result or must_recurse

        return result

    @staticmethod
    def considerFailedImportReferrals(module_name):
        for plugin in getActivePlugins():
            new_module_name = plugin.considerFailedImportReferrals(module_name)

            if new_module_name is not None:
                return ModuleName(new_module_name)

        return None

    @staticmethod
    def suppressUnknownImportWarning(importing, module_name):
        """ Let plugins decide whether to suppress import warnings for an unknown module.

        Notes:
            If all plugins return False or None, the return will be False, else True.
        Args:
            importing: the module which is importing "module_name"
            module_name: the module to be imported
        returns:
            True or False (default)
        """
        if importing.isCompiledPythonModule() or importing.isPythonShlibModule():
            importing_module = importing
        else:
            importing_module = importing.getParentModule()

        source_ref = importing.getSourceReference()

        for plugin in getActivePlugins():
            if plugin.suppressUnknownImportWarning(
                importing_module, module_name, source_ref
            ):
                return True

        return False

    @staticmethod
    def decideCompilation(module_name, source_ref):
        """ Let plugins decide whether to compile a module.

        Notes:
            The decision is made by the first plugin not returning None.

        Returns:
            "compiled" (default) or "bytecode".
        """
        for plugin in getActivePlugins():
            value = plugin.decideCompilation(module_name, source_ref)

            if value is not None:
                assert value in ("compiled", "bytecode")
                return value

        return "compiled"

    @staticmethod
    def getPreprocessorSymbols():
        """ Let plugins provide C defines to be used in compilation.

        Notes:
            The plugins can each contribute, but are hopefully using
            a namespace for their defines.

        Returns:
            OrderedDict(), where None value indicates no define value,
            i.e. "-Dkey=value" vs. "-Dkey"
        """
        result = OrderedDict()

        for plugin in getActivePlugins():
            value = plugin.getPreprocessorSymbols()

            if value is not None:
                assert type(value) is dict

                # We order per plugin, but from the plugins, lets just take a dict
                # and achieve determism by ordering the defines by name.
                for key, value in sorted(value.items()):
                    result[key] = value

        return result

    @staticmethod
    def getExtraCodeFiles():
        result = OrderedDict()

        for plugin in getActivePlugins():
            value = plugin.getExtraCodeFiles()

            if value is not None:
                assert type(value) is dict

                # We order per plugin, but from the plugins, lets just take a dict
                # and achieve determism by ordering the files by name.
                for key, value in sorted(value.items()):
                    assert key not in result, key
                    result["plugin." + plugin.plugin_name + "." + key] = value

        return result

    @staticmethod
    def getExtraLinkLibraries():
        result = OrderedSet()

        for plugin in getActivePlugins():
            value = plugin.getExtraLinkLibraries()

            if value is not None:
                if isinstance(value, basestring):
                    result.add(value)
                else:
                    for library_name in value:
                        result.add(library_name)

        return result


def listPlugins():
    """ Print available standard plugins.
    """

    loadPlugins()

    print("The following optional standard plugins are available in Nuitka".center(80))
    print("-" * 80)
    plist = []
    name_len = 0
    for plugin_name in sorted(plugin_name2plugin_classes):
        plugin = plugin_name2plugin_classes[plugin_name][0]
        if hasattr(plugin, "plugin_desc"):
            plist.append((plugin_name, plugin.plugin_desc))
        else:
            plist.append((plugin_name, ""))
        name_len = max(len(plugin_name) + 1, name_len)
    for line in plist:
        print(" " + line[0].ljust(name_len), line[1])

    sys.exit(0)


def isObjectAUserPluginBaseClass(obj):
    """ Verify that a user plugin inherits from UserPluginBase.
    """
    try:
        return obj is not NuitkaPluginBase and issubclass(obj, NuitkaPluginBase)
    except TypeError:
        return False


def importFilePy3NewWay(filename):
    """ Import a file for Python versions 3.5+.
    """
    import importlib.util  # pylint: disable=I0021,import-error,no-name-in-module

    spec = importlib.util.spec_from_file_location(filename, filename)
    user_plugin_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_plugin_module)
    return user_plugin_module


def importFilePy3OldWay(filename):
    """ Import a file for Python versions 3.x where x < 5.
    """
    from importlib.machinery import (  # pylint: disable=I0021,import-error,no-name-in-module
        SourceFileLoader,
    )

    # pylint: disable=I0021,deprecated-method
    return SourceFileLoader(filename, filename).load_module(filename)


def importFilePy2(filename):
    """ Import a file for Python version 2.
    """
    import imp

    basename = os.path.splitext(os.path.basename(filename))[0]
    return imp.load_source(basename, filename)


def importFile(filename):
    """ Import Python module given as a file name.

    Notes:
        Provides a Python version independent way to import any script files.

    Args:
        filename: complete path of a Python script

    Returns:
        Imported Python module defined in filename.
    """
    if python_version < 300:
        return importFilePy2(filename)
    elif python_version < 350:
        return importFilePy3OldWay(filename)
    else:
        return importFilePy3NewWay(filename)


def loadUserPlugin(plugin_filename):
    """ Load of a user plugins and store them in list of active plugins.

    Notes:
        A plugin is accepted only if it has a non-empty variable plugin_name, which
        does not equal that of a disabled (standard) plugin.
        Supports plugin option specifications.
    Returns:
        None
    """
    if not os.path.exists(plugin_filename):
        sys.exit("Error, cannot find '%s'." % plugin_filename)

    user_plugin_module = importFile(plugin_filename)
    valid_file = False
    plugin_class = None
    for key in dir(user_plugin_module):
        obj = getattr(user_plugin_module, key)
        if not isObjectAUserPluginBaseClass(obj):
            continue

        plugin_name = getattr(obj, "plugin_name", None)
        if plugin_name and plugin_name not in Options.getPluginsDisabled():
            plugin_class = obj

            valid_file = True
            break  # do not look for more in that module

    if not valid_file:  # this is not a plugin file ...
        sys.exit("Error, '%s' is not a plugin file." % plugin_filename)

    return plugin_class


_loaded_plugins = False


def loadPlugins():
    """ Initialize plugin class

    Notes:
        Load user plugins provided as Python script file names, and standard
        plugins via their class attribute 'plugin_name'.

        Several checks are made, see the loader functions.

        User plugins are enabled as a first step, because they themselves may
        enable standard plugins.

    Returns:
        None
    """

    # Singleton, called potentially multiple times, pylint: disable=global-statement
    global _loaded_plugins
    if not _loaded_plugins:
        _loaded_plugins = True

        # now enable standard plugins
        loadStandardPluginClasses()


def activatePlugins():
    """ Activate selected plugin classes

    Args:
        None

    Notes:
        This creates actual plugin instances, before only class objects were
        used.

        User plugins are activated as a first step, because they themselves may
        enable standard plugins.

    Returns:
        None
    """
    loadPlugins()

    # ensure plugin is known and not both, enabled and disabled
    for plugin_name in Options.getPluginsEnabled() + Options.getPluginsDisabled():
        if plugin_name not in plugin_name2plugin_classes:
            sys.exit("Error, unknown plug-in '%s' referenced." % plugin_name)

        if (
            plugin_name in Options.getPluginsEnabled()
            and plugin_name in Options.getPluginsDisabled()
        ):
            sys.exit("Error, conflicting enable/disable of plug-in '%s'." % plugin_name)

    for (plugin_name, (plugin_class, plugin_detector)) in sorted(
        plugin_name2plugin_classes.items()
    ):
        if plugin_name in Options.getPluginsEnabled():
            _addActivePlugin(plugin_class)
        elif plugin_name in Options.getPluginsDisabled():
            pass
        elif plugin_class.isAlwaysEnabled() and plugin_class.isRelevant():
            _addActivePlugin(plugin_class)
        elif (
            plugin_detector is not None
            and Options.shallDetectMissingPlugins()
            and plugin_detector.isRelevant()
        ):
            _addActivePlugin(plugin_detector, args=False)

    for plugin_class in user_plugins:
        _addActivePlugin(plugin_class, args=True)


def _addPluginCommandLineOptions(parser, plugin_class):
    option_group = OptionGroup(parser, "Plugin %s" % plugin_class.plugin_name)
    plugin_class.addPluginCommandLineOptions(option_group)

    if option_group.option_list:
        parser.add_option_group(option_group)
        plugin_options[plugin_class.plugin_name] = option_group.option_list


def addPluginCommandLineOptions(parser, plugin_name):
    """ Add option group for the plugin to the parser.

    Notes:
        This is exclusively for use in the commandline parsing. Not all
        plugins have to have options. But this will add them to the
        parser in a first pass.

    Returns:
        None
    """
    plugin_class = getPluginClass(plugin_name)
    _addPluginCommandLineOptions(parser, plugin_class)


def addUserPluginCommandLineOptions(parser, filename):
    plugin_class = loadUserPlugin(filename)
    _addPluginCommandLineOptions(parser, plugin_class)

    user_plugins.add(plugin_class)


def setPluginOptions(plugin_name, values):
    """ Set the option values for the specified plugin.

    Args:
        plugin_name: plugin identifier
        values: dictionary to be used for the plugin constructor
    Notes:
        Use this function, if you want to set the plugin values, without using
        the actual command line parsing.

        Normally the command line arguments are populating the dictionary for
        the plugin, but this will be used if given, and command line parsing
        is not done.
    """
    assert isinstance(values, dict), values
    plugin_values[plugin_name] = values


def getPluginOptions(plugin_name):
    """ Return the options values for the specified plugin.

    Args:
        plugin_name: plugin identifier
    Returns:
        dict with key, value of options given, potentially from default values.
    """
    result = plugin_values.get(plugin_name, {})

    for option in plugin_options.get(plugin_name, {}):
        option_name = option._long_opts[0]  # pylint: disable=protected-access

        arg_value = getattr(Options.options, option.dest)

        if "[REQUIRED]" in option.help:
            if not arg_value:
                sys.exit("Error, required plugin argument %r not given." % option_name)

        result[option.dest] = arg_value

    return result
