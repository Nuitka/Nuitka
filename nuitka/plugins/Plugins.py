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
"""

Plugins: Welcome to Nuitka! This is your shortest way to become part of it.

This is to provide the base class for all plug-ins. Some of which are part of
proper Nuitka, and some of which are waiting to be created and submitted for
inclusion by you.

The base class in PluginBase will serve as documentation of available.

"""

import inspect
import os
import pkgutil
import shutil
from optparse import OptionGroup

import nuitka.plugins.commercial
import nuitka.plugins.standard
from nuitka import Options
from nuitka.__past__ import basestring  # pylint: disable=I0021,redefined-builtin
from nuitka.build.DataComposerInterface import deriveModuleConstantsBlobName
from nuitka.containers.odict import OrderedDict
from nuitka.containers.oset import OrderedSet
from nuitka.Errors import NuitkaPluginError
from nuitka.freezer.IncludedEntryPoints import makeDllEntryPointOld
from nuitka.ModuleRegistry import addUsedModule
from nuitka.Tracing import plugins_logger, printLine
from nuitka.utils.FileOperations import makePath, relpath
from nuitka.utils.Importing import importFileAsModule
from nuitka.utils.ModuleNames import ModuleName

from .PluginBase import NuitkaPluginBase, post_modules, pre_modules

active_plugins = OrderedDict()
plugin_name2plugin_classes = {}
plugin_options = {}
plugin_values = {}
user_plugins = OrderedSet()


def _addActivePlugin(plugin_class, args, force=False):
    plugin_name = plugin_class.plugin_name

    # No duplicates please.
    if not force:
        assert plugin_name not in active_plugins.keys(), (
            plugin_name,
            active_plugins[plugin_name],
        )

    if args:
        plugin_args = getPluginOptions(plugin_name)
    else:
        plugin_args = {}

    plugin_instance = plugin_class(**plugin_args)
    assert isinstance(plugin_instance, NuitkaPluginBase), plugin_instance

    active_plugins[plugin_name] = plugin_instance


def getActivePlugins():
    """Return list of active plugins.

    Returns:
        list of plugins

    """

    return active_plugins.values()


def hasActivePlugin(plugin_name):
    """Decide if a plugin is active.

    Args:
        plugin_name - name of the plugin

    Notes:
        Detectors do not count as an active plugin and ignored.

    Returns:
        bool - plugin is loaded

    """
    if plugin_name not in active_plugins:
        return False

    # Detectors do not count.
    plugin_instance = active_plugins.get(plugin_name)
    return not hasattr(plugin_instance, "detector_for")


def getPluginClass(plugin_name):
    # First, load plugin classes, to know what we are talking about.
    loadPlugins()

    if plugin_name not in plugin_name2plugin_classes:
        plugins_logger.sysexit("Error, unknown plug-in '%s' referenced." % plugin_name)

    return plugin_name2plugin_classes[plugin_name][0]


def _loadPluginClassesFromPath(scan_path):
    for loader, name, is_pkg in pkgutil.iter_modules(scan_path):
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

        try:
            plugin_module = module_loader.load_module(name)
        except Exception:
            if Options.is_nondebug:
                plugins_logger.warning(
                    "Problem loading plugin %r (%s), ignored. Use --debug to make it visible."
                    % (name, module_loader.get_filename())
                )
                continue

            raise

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

            if plugin_class not in plugin_classes:
                plugins_logger.sysexit(
                    "Plugin detector %r references unknown plugin %r"
                    % (detector, plugin_class)
                )

            plugin_classes.remove(detector)
            plugin_classes.remove(plugin_class)

            plugin_name2plugin_classes[plugin_class.plugin_name] = (
                plugin_class,
                detector,
            )

        for plugin_class in plugin_classes:
            plugin_name2plugin_classes[plugin_class.plugin_name] = plugin_class, None


def loadStandardPluginClasses():
    """Load plugin files located in 'standard' folder.

    Notes:
        Scan through the 'standard' and 'commercial' sub-folder of the folder
        where this script resides. Import each valid Python module (but not
        packages) and process it as a plugin.
    Returns:
        None
    """
    _loadPluginClassesFromPath(nuitka.plugins.standard.__path__)
    _loadPluginClassesFromPath(nuitka.plugins.commercial.__path__)


class Plugins(object):
    @staticmethod
    def isPluginActive(plugin_name):
        """ Is a plugin activated. """

        return plugin_name in active_plugins

    implicit_imports_cache = {}

    @staticmethod
    def _considerImplicitImports(plugin, module):
        from nuitka.importing import Importing

        result = []

        for full_name in plugin.getImplicitImports(module):
            if type(full_name) in (tuple, list):
                raise NuitkaPluginError(
                    "Plugin %r needs to be change to only return modules names, not %r"
                    % (plugin, full_name)
                )

            full_name = ModuleName(full_name)

            try:
                _module_package, module_filename, _finding = Importing.findModule(
                    importing=module,
                    module_name=full_name,
                    parent_package=None,
                    level=-1,
                    warn=False,
                )

                module_filename = plugin.locateModule(
                    importing=module, module_name=full_name
                )
            except Exception:
                plugin.warning(
                    "Problem locating '%s' for implicit imports of '%s'."
                    % (module.getFullName(), full_name)
                )
                raise

            if module_filename is None:
                if Options.isShowInclusion():
                    plugin.info(
                        "Implicit module '%s' suggested for '%s' not found."
                        % (full_name, module.getFullName())
                    )

                continue

            result.append((full_name, module_filename))

        if result:
            plugin.info(
                "Implicit dependencies of module '%s' added '%s'."
                % (module.getFullName(), ",".join(r[0] for r in result))
            )

        return result

    @staticmethod
    def _reportImplicitImports(implicit_imports, signal_change):
        from nuitka.importing import Recursion
        from nuitka.importing.Importing import getModuleNameAndKindFromFilename

        for full_name, module_filename in implicit_imports:
            _module_name2, module_kind = getModuleNameAndKindFromFilename(
                module_filename
            )

            # This will get back to all other plugins allowing them to inhibit it though.
            decision, reason = Recursion.decideRecursion(
                module_filename=module_filename,
                module_name=full_name,
                module_kind=module_kind,
            )

            if decision:
                imported_module, added_flag = Recursion.recurseTo(
                    module_package=full_name.getPackageName(),
                    module_filename=module_filename,
                    module_relpath=relpath(module_filename),
                    module_kind=module_kind,
                    reason=reason,
                )

                addUsedModule(imported_module)

                if added_flag:
                    signal_change(
                        "new_code",
                        imported_module.getSourceReference(),
                        "Recursed to module.",
                    )

    @classmethod
    def considerImplicitImports(cls, module, signal_change):
        for plugin in getActivePlugins():
            key = (module.getFullName(), plugin)

            if key not in cls.implicit_imports_cache:
                cls.implicit_imports_cache[key] = tuple(
                    cls._considerImplicitImports(plugin=plugin, module=module)
                )

            cls._reportImplicitImports(
                implicit_imports=cls.implicit_imports_cache[key],
                signal_change=signal_change,
            )

        # Pre and post load code may have been created, if so indicate it's used.
        full_name = module.getFullName()

        if full_name in pre_modules:
            addUsedModule(pre_modules[full_name])

        if full_name in post_modules:
            addUsedModule(post_modules[full_name])

    @staticmethod
    def onStandaloneDistributionFinished(dist_dir):
        """Let plugins postprocess the distribution folder in standalone mode"""
        for plugin in getActivePlugins():
            plugin.onStandaloneDistributionFinished(dist_dir)

    @staticmethod
    def onOnefileFinished(filename):
        """Let plugins postprocess the onefile executable in onefile mode"""
        for plugin in getActivePlugins():
            plugin.onStandaloneDistributionFinished(filename)

    @staticmethod
    def onFinalResult(filename):
        """Let plugins add to final binary in some way"""
        for plugin in getActivePlugins():
            plugin.onFinalResult(filename)

    @staticmethod
    def considerExtraDlls(dist_dir, module):
        """Ask plugins to provide extra DLLs.

        Notes:
            These will be of type nuitka.freezer.IncludedEntryPoints.IncludedEntryPoint
            and currently there is a backward compatibility for old style plugins that do
            provide tuples of 3 elements. But plugins are really supposed to provide the
            stuff created from factory functions for that type.

        """

        result = []

        for plugin in getActivePlugins():
            for extra_dll in plugin.considerExtraDlls(dist_dir, module):
                # Backward compatibility with plugins not yet migrated to getExtraDlls usage.
                if len(extra_dll) == 3:
                    extra_dll = makeDllEntryPointOld(
                        source_path=extra_dll[0],
                        dest_path=extra_dll[1],
                        package_name=extra_dll[2],
                    )

                    if not os.path.isfile(extra_dll.dest_path):
                        plugin.sysexit(
                            "Error, copied filename %r for module %r that is not a file."
                            % (extra_dll.dest_path, module.getFullName())
                        )
                else:
                    if not os.path.isfile(extra_dll.source_path):
                        plugin.sysexit(
                            "Error, attempting to copy plugin determined filename %r for module %r that is not a file."
                            % (extra_dll.source_path, module.getFullName())
                        )

                    makePath(os.path.dirname(extra_dll.dest_path))

                    shutil.copyfile(extra_dll.source_path, extra_dll.dest_path)

                result.append(extra_dll)

        return result

    @staticmethod
    def removeDllDependencies(dll_filename, dll_filenames):
        """Create list of removable shared libraries by scanning through the plugins.

        Args:
            dll_filename: shared library filename
            dll_filenames: list of shared library filenames
        Returns:
            list of removable files
        """
        dll_filenames = tuple(sorted(dll_filenames))

        to_remove = OrderedSet()

        for plugin in getActivePlugins():
            removed_dlls = tuple(
                plugin.removeDllDependencies(dll_filename, dll_filenames)
            )

            if removed_dlls and Options.isShowInclusion():
                plugin.info(
                    "Removing DLLs %s of %s by plugin decision."
                    % (dll_filename, removed_dlls)
                )

            for removed_dll in removed_dlls:
                to_remove.add(removed_dll)

        for removed in to_remove:
            dll_filenames.discard(removed)

    @staticmethod
    def considerDataFiles(module):
        """For a given module, ask plugins for any needed data files it may require.

        Args:
            module: module object
        Yields:
            Data file description pairs, either (source, dest) or (func, dest)
            where the func will be called to create the content dynamically.
        """
        for plugin in getActivePlugins():
            for value in plugin.considerDataFiles(module):
                if value:
                    yield plugin, value

    @staticmethod
    def onModuleDiscovered(module):
        for plugin in getActivePlugins():
            plugin.onModuleDiscovered(module)

    @staticmethod
    def onModuleSourceCode(module_name, source_code):
        assert type(module_name) is ModuleName
        assert type(source_code) is str

        for plugin in getActivePlugins():
            new_source_code = plugin.onModuleSourceCode(module_name, source_code)
            if new_source_code is not None:
                source_code = new_source_code

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
        result = None

        for plugin in getActivePlugins():
            must_recurse = plugin.onModuleEncounter(
                module_filename, module_name, module_kind
            )

            if must_recurse is None:
                continue

            if result is not None:
                # false alarm, pylint: disable=unsubscriptable-object
                assert result[0] == must_recurse[0]

            result = must_recurse

        return result

    @staticmethod
    def onModuleInitialSet():
        from nuitka.ModuleRegistry import addRootModule

        for plugin in getActivePlugins():
            for module in plugin.onModuleInitialSet():
                addRootModule(module)

    @staticmethod
    def considerFailedImportReferrals(module_name):
        for plugin in getActivePlugins():
            new_module_name = plugin.considerFailedImportReferrals(module_name)

            if new_module_name is not None:
                return ModuleName(new_module_name)

        return None

    @staticmethod
    def suppressUnknownImportWarning(importing, module_name):
        """Let plugins decide whether to suppress import warnings for an unknown module.

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
        """Let plugins decide whether to C compile a module or include as bytecode.

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

    preprocessor_symbols = None

    @classmethod
    def getPreprocessorSymbols(cls):
        """Let plugins provide C defines to be used in compilation.

        Notes:
            The plugins can each contribute, but are hopefully using
            a namespace for their defines.

        Returns:
            OrderedDict(), where None value indicates no define value,
            i.e. "-Dkey=value" vs. "-Dkey"
        """

        if cls.preprocessor_symbols is None:
            cls.preprocessor_symbols = OrderedDict()

            for plugin in getActivePlugins():
                value = plugin.getPreprocessorSymbols()

                if value is not None:
                    assert type(value) is dict, value

                    # We order per plugin, but from the plugins, lets just take a dict
                    # and achieve determism by ordering the defines by name.
                    for key, value in sorted(value.items()):
                        # False alarm, pylint: disable=I0021,unsupported-assignment-operation
                        cls.preprocessor_symbols[key] = value

        return cls.preprocessor_symbols

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
                    if not key.startswith("nuitka_"):
                        key = "plugin." + plugin.plugin_name + "." + key

                    assert key not in result, key
                    result[key] = value

        return result

    extra_link_libraries = None

    @classmethod
    def getExtraLinkLibraries(cls):
        if cls.extra_link_libraries is None:
            cls.extra_link_libraries = OrderedSet()

            for plugin in getActivePlugins():
                value = plugin.getExtraLinkLibraries()

                if value is not None:
                    if isinstance(value, basestring):
                        cls.extra_link_libraries.add(value)
                    else:
                        for library_name in value:
                            cls.extra_link_libraries.add(library_name)

        return cls.extra_link_libraries

    @classmethod
    def onDataComposerResult(cls, blob_filename):
        for plugin in getActivePlugins():
            plugin.onDataComposerResult(blob_filename)

    @classmethod
    def deriveModuleConstantsBlobName(cls, data_filename):
        result = deriveModuleConstantsBlobName(data_filename)

        return cls.encodeDataComposerName(result)

    @classmethod
    def encodeDataComposerName(cls, name):
        if str is not bytes:
            # Encoding needs to match generated source code output.
            name = name.encode("latin1")

        for plugin in getActivePlugins():
            r = plugin.encodeDataComposerName(name)

            if r is not None:
                name = r
                break

        return name


def listPlugins():
    """Print available standard plugins."""

    loadPlugins()

    printLine("The following plugins are available in Nuitka".center(80))
    printLine("-" * 80)

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
        printLine(" " + line[0].ljust(name_len), line[1])


def isObjectAUserPluginBaseClass(obj):
    """Verify that a user plugin inherits from UserPluginBase."""
    try:
        return (
            obj is not NuitkaPluginBase
            and issubclass(obj, NuitkaPluginBase)
            and not inspect.isabstract(obj)
        )
    except TypeError:
        return False


def loadUserPlugin(plugin_filename):
    """Load of a user plugins and store them in list of active plugins.

    Notes:
        A plugin is accepted only if it has a non-empty variable plugin_name, which
        does not equal that of a disabled (standard) plugin.
        Supports plugin option specifications.
    Returns:
        None
    """
    if not os.path.exists(plugin_filename):
        plugins_logger.sysexit("Error, cannot find '%s'." % plugin_filename)

    user_plugin_module = importFileAsModule(plugin_filename)

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
        plugins_logger.sysexit("Error, '%s' is not a plugin file." % plugin_filename)

    return plugin_class


_loaded_plugins = False


def loadPlugins():
    """Initialize plugin class

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
    """Activate selected plugin classes

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
            plugins_logger.sysexit(
                "Error, unknown plug-in '%s' referenced." % plugin_name
            )

        if (
            plugin_name in Options.getPluginsEnabled()
            and plugin_name in Options.getPluginsDisabled()
        ):
            plugins_logger.sysexit(
                "Error, conflicting enable/disable of plug-in '%s'." % plugin_name
            )

    for (plugin_name, (plugin_class, plugin_detector)) in sorted(
        plugin_name2plugin_classes.items()
    ):
        if plugin_name in Options.getPluginsEnabled():
            if plugin_class.isRelevant():
                _addActivePlugin(plugin_class, args=True)
            else:
                plugin_class.warning(
                    "Not relevant with this OS, or Nuitka arguments given, not activated."
                )
        elif plugin_name in Options.getPluginsDisabled():
            pass
        elif plugin_class.isAlwaysEnabled() and plugin_class.isRelevant():
            _addActivePlugin(plugin_class, args=True)
        elif (
            plugin_detector is not None
            and Options.shallDetectMissingPlugins()
            and plugin_detector.isRelevant()
        ):
            _addActivePlugin(plugin_detector, args=False)

    for plugin_class in user_plugins:
        _addActivePlugin(plugin_class, args=True)


def lateActivatePlugin(plugin_name, option_values):
    """Activate plugin after the command line parsing, expects options to be set."""

    values = getPluginClass(plugin_name).getPluginDefaultOptionValues()
    values.update(option_values)
    setPluginOptions(plugin_name, values)

    _addActivePlugin(getPluginClass(plugin_name), args=True, force=True)


def _addPluginCommandLineOptions(parser, plugin_class):
    if plugin_class.plugin_name not in plugin_options:
        option_group = OptionGroup(parser, "Plugin %s" % plugin_class.plugin_name)
        plugin_class.addPluginCommandLineOptions(option_group)

        if option_group.option_list:
            parser.add_option_group(option_group)
            plugin_options[plugin_class.plugin_name] = option_group.option_list
        else:
            plugin_options[plugin_class.plugin_name] = ()


def addPluginCommandLineOptions(parser, plugin_names):
    """Add option group for the plugin to the parser.

    Notes:
        This is exclusively for use in the commandline parsing. Not all
        plugins have to have options. But this will add them to the
        parser in a first pass, so they can be recognized in a second
        pass with them included.

    Returns:
        None
    """
    for plugin_name in plugin_names:
        plugin_class = getPluginClass(plugin_name)
        _addPluginCommandLineOptions(parser, plugin_class)


def addUserPluginCommandLineOptions(parser, filename):
    plugin_class = loadUserPlugin(filename)
    _addPluginCommandLineOptions(parser, plugin_class)

    user_plugins.add(plugin_class)


def setPluginOptions(plugin_name, values):
    """Set the option values for the specified plugin.

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
    """Return the options values for the specified plugin.

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
                plugins_logger.sysexit(
                    "Error, required plugin argument %r of Nuitka plugin %s not given."
                    % (option_name, plugin_name)
                )

        result[option.dest] = arg_value

    return result
