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
"""

Plugins: Welcome to Nuitka! This is your shortest way to become part of it.

This is to provide the base class for all plugins. Some of which are part of
proper Nuitka, and some of which are waiting to be created and submitted for
inclusion by you.

The base class in PluginBase will serve as documentation of available.

"""

import inspect
import os
from optparse import OptionConflictError, OptionGroup

from nuitka import Options, OutputDirectories
from nuitka.__past__ import basestring, iter_modules
from nuitka.build.DataComposerInterface import deriveModuleConstantsBlobName
from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.freezer.IncludedDataFiles import IncludedDataFile
from nuitka.freezer.IncludedEntryPoints import IncludedEntryPoint
from nuitka.ModuleRegistry import addUsedModule
from nuitka.Tracing import plugins_logger, printLine
from nuitka.utils.FileOperations import makePath, putTextFileContents
from nuitka.utils.Importing import importFileAsModule
from nuitka.utils.ModuleNames import (
    ModuleName,
    checkModuleName,
    makeTriggerModuleName,
    post_module_load_trigger_name,
    pre_module_load_trigger_name,
)

from .PluginBase import NuitkaPluginBase

# Maps plugin name to plugin instances.
active_plugins = OrderedDict()
plugin_name2plugin_classes = {}
plugin_options = {}
plugin_values = {}
user_plugins = OrderedSet()

# Trigger modules
pre_modules = {}
pre_modules_reasons = {}
post_modules = {}
post_modules_reasons = {}
fake_modules = {}
has_active_gui_toolkit_plugin = False


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

    try:
        plugin_instance = plugin_class(**plugin_args)
    except TypeError as e:
        plugin_class.sysexit("Problem initializing plugin: %s" % e)

    assert isinstance(plugin_instance, NuitkaPluginBase), plugin_instance

    active_plugins[plugin_name] = plugin_instance

    # Singleton, pylint: disable=global-statement
    global has_active_gui_toolkit_plugin
    has_active_gui_toolkit_plugin = has_active_gui_toolkit_plugin or getattr(
        plugin_class, "plugin_gui_toolkit", False
    )


def getActivePlugins():
    """Return list of active plugins.

    Returns:
        list of plugins

    """

    return active_plugins.values()


def getActiveQtPlugin():
    for plugin_name in getQtPluginNames():
        if hasActivePlugin(plugin_name):
            if hasActivePlugin(plugin_name):
                return plugin_name

    return None


def getQtBindingNames():
    return ("PySide", "PySide2", "PySide6", "PyQt4", "PyQt5", "PyQt6")


def getOtherGUIBindingNames():
    return ("wx", "tkinter", "Tkinter")


def getQtPluginNames():
    return tuple(qt_binding_name.lower() for qt_binding_name in getQtBindingNames())


def getOtherGuiPluginNames():
    return ("tk-inter",)


def getGuiPluginNames():
    return getQtPluginNames() + getOtherGuiPluginNames()


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


def getUserActivatedPluginNames():
    for plugin_name, plugin_instance in active_plugins.items():
        # Detectors do not count.
        if hasattr(plugin_instance, "detector_for"):
            continue

        # Always activated does not count either
        if plugin_instance.isAlwaysEnabled():
            continue

        yield plugin_name


def getPluginClass(plugin_name):
    # First, load plugin classes, to know what we are talking about.
    loadPlugins()

    # Backward compatibility.
    plugin_name = Options.getPluginNameConsideringRenames(plugin_name)

    if plugin_name not in plugin_name2plugin_classes:
        plugins_logger.sysexit("Error, unknown plug-in '%s' referenced." % plugin_name)

    return plugin_name2plugin_classes[plugin_name][0]


def _addPluginClass(plugin_class, detector):
    plugin_name = plugin_class.plugin_name

    if plugin_name in plugin_name2plugin_classes:
        plugins_logger.sysexit(
            "Error, plugins collide by name %s: %s <-> %s"
            % (plugin_name, plugin_class, plugin_name2plugin_classes[plugin_name])
        )

    plugin_name2plugin_classes[plugin_name] = (
        plugin_class,
        detector,
    )


def _loadPluginClassesFromPackage(scan_package):
    scan_path = scan_package.__path__

    for item in iter_modules(scan_path):
        if item.ispkg:  # spell-checker: ignore ispkg
            continue

        module_loader = item.module_finder.find_module(item.name)

        # Ignore bytecode only left overs.
        try:
            if module_loader.get_filename().endswith(".pyc"):
                continue
        except AttributeError:
            # Not a bytecode loader, but e.g. extension module, which is OK in case
            # it was compiled with Nuitka.
            pass

        try:
            plugin_module = module_loader.load_module(item.name)
        except Exception:
            if Options.is_non_debug:
                plugins_logger.warning(
                    "Problem loading plugin %r ('%s'), ignored. Use '--debug' to make it visible."
                    % (item.name, module_loader.get_filename())
                )
                continue

            raise

        # At least for Python2, this is not set properly, but we use it for package
        # data loading.
        plugin_module.__package__ = scan_package.__name__

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

        # First the ones with detectors.
        for detector in detectors:
            plugin_class = detector.detector_for

            if detector.__name__.replace(
                "NuitkaPluginDetector", ""
            ) != plugin_class.__name__.replace("NuitkaPlugin", ""):
                plugins_logger.warning(
                    "Class names %r and %r do not match NuitkaPlugin* and NuitkaPluginDetector* naming convention."
                    % (plugin_class.__name__, detector.__name__)
                )

            assert detector.plugin_name is None, detector
            detector.plugin_name = plugin_class.plugin_name

            if plugin_class not in plugin_classes:
                plugins_logger.sysexit(
                    "Plugin detector %r references unknown plugin %r"
                    % (detector, plugin_class)
                )

            plugin_classes.remove(detector)
            plugin_classes.remove(plugin_class)

            _addPluginClass(
                plugin_class=plugin_class,
                detector=detector,
            )

        # Remaining ones have no detector.
        for plugin_class in plugin_classes:
            _addPluginClass(plugin_class=plugin_class, detector=None)


def loadStandardPluginClasses():
    """Load plugin files located in 'standard' folder.

    Notes:
        Scan through the 'standard' and 'commercial' plugins. Import each valid
        Python module (but not packages) and process it as a plugin.
    Returns:
        None
    """
    import nuitka.plugins.standard

    _loadPluginClassesFromPackage(nuitka.plugins.standard)

    try:
        import nuitka.plugins.commercial
    except ImportError:
        pass
    else:
        _loadPluginClassesFromPackage(nuitka.plugins.commercial)


class Plugins(object):
    implicit_imports_cache = {}

    @staticmethod
    def _considerImplicitImports(plugin, module):
        result = []

        def iterateModuleNames(value):
            for v in value:
                if type(v) in (tuple, list):
                    plugin.sysexit(
                        "Plugin %r needs to be change to only return modules names, not %r (for %s)"
                        % (plugin.plugin_name, v, module.getFullName().asString())
                    )

                if inspect.isgenerator(v):
                    for w in iterateModuleNames(v):
                        yield w

                    return

                if not checkModuleName(v):
                    plugin.sysexit(
                        "Plugin %r returned an invalid module name, not %r (for %s)"
                        % (plugin, v, module.getFullName().asString())
                    )

                yield ModuleName(v)

        seen = set()

        for full_name in iterateModuleNames(plugin.getImplicitImports(module)):
            if full_name in seen:
                continue
            seen.add(full_name)

            # Ignore dependencies on self. TODO: Make this an error for the
            # plugin.
            if full_name == module.getFullName():
                continue

            try:
                module_filename = plugin.locateModule(full_name)
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

        if result and Options.isShowInclusion():
            plugin.info(
                "Implicit dependencies of module '%s' added '%s'."
                % (module.getFullName(), ",".join(r[0] for r in result))
            )

        return result

    @staticmethod
    def _reportImplicitImports(plugin, module, implicit_imports, signal_change):
        from nuitka.importing import Recursion
        from nuitka.importing.Importing import getModuleNameAndKindFromFilename

        for full_name, module_filename in implicit_imports:

            # TODO: The module_kind should be forwarded from previous in the class using locateModule code.
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
                imported_module = Recursion.recurseTo(
                    signal_change=signal_change,
                    module_name=full_name,
                    module_filename=module_filename,
                    module_kind=module_kind,
                    using_module=module,
                    source_ref=module.getSourceReference(),
                    reason=reason,
                )

                addUsedModule(
                    module=imported_module,
                    using_module=module,
                    usage_tag="plugin:" + plugin.plugin_name,
                    reason=reason,
                    source_ref=module.source_ref,
                )

    @classmethod
    def getPackageExtraScanPaths(cls, package_name, package_dir):
        for plugin in getActivePlugins():
            for path in plugin.getPackageExtraScanPaths(package_name, package_dir):
                if os.path.isdir(path):
                    yield path

    @classmethod
    def considerImplicitImports(cls, module, signal_change):
        for plugin in getActivePlugins():
            key = (module.getFullName(), plugin)

            if key not in cls.implicit_imports_cache:
                cls.implicit_imports_cache[key] = tuple(
                    cls._considerImplicitImports(plugin=plugin, module=module)
                )

            cls._reportImplicitImports(
                plugin=plugin,
                module=module,
                implicit_imports=cls.implicit_imports_cache[key],
                signal_change=signal_change,
            )

        # Pre and post load code may have been created, if so indicate it's used.
        full_name = module.getFullName()

        if full_name in pre_modules:
            addUsedModule(
                pre_modules[full_name],
                using_module=module,
                usage_tag="plugins",
                reason=" ".join(pre_modules_reasons[full_name]),
                source_ref=module.source_ref,
            )

        if full_name in post_modules:
            addUsedModule(
                module=post_modules[full_name],
                using_module=module,
                usage_tag="plugins",
                reason=" ".join(post_modules_reasons[full_name]),
                source_ref=module.source_ref,
            )

        if full_name in fake_modules:
            for fake_module, plugin, reason in fake_modules[full_name]:
                addUsedModule(
                    module=fake_module,
                    using_module=module,
                    usage_tag="plugins",
                    reason=reason,
                    source_ref=module.source_ref,
                )

    @staticmethod
    def onCopiedDLLs(dist_dir, standalone_entry_points):
        """Lets the plugins modify entry points on disk."""
        for entry_point in standalone_entry_points:
            if entry_point.kind.endswith("_ignored"):
                continue

            for plugin in getActivePlugins():
                plugin.onCopiedDLL(os.path.join(dist_dir, entry_point.dest_path))

    @staticmethod
    def onBeforeCodeParsing():
        """Let plugins prepare for code parsing"""
        for plugin in getActivePlugins():
            plugin.onBeforeCodeParsing()

    @staticmethod
    def onStandaloneDistributionFinished(dist_dir):
        """Let plugins post-process the distribution folder in standalone mode"""
        for plugin in getActivePlugins():
            plugin.onStandaloneDistributionFinished(dist_dir)

        standalone_binary = OutputDirectories.getResultFullpath(onefile=False)

        for plugin in getActivePlugins():
            plugin.onStandaloneBinary(standalone_binary)

    @staticmethod
    def onOnefileFinished(filename):
        """Let plugins post-process the onefile executable in onefile mode"""
        for plugin in getActivePlugins():
            plugin.onStandaloneDistributionFinished(filename)

    @staticmethod
    def onBootstrapBinary(filename):
        """Let plugins add to bootstrap binary in some way"""
        for plugin in getActivePlugins():
            plugin.onBootstrapBinary(filename)

    @staticmethod
    def onFinalResult(filename):
        """Let plugins add to final binary in some way"""
        for plugin in getActivePlugins():
            plugin.onFinalResult(filename)

    @staticmethod
    def considerExtraDlls(module):
        """Ask plugins to provide extra DLLs.

        Notes:
            These will be of type IncludedEntryPoint or generators providing them, so
            we get "yield from" effective with simple yield.

        """

        result = []

        # TODO: This is probably something generic that only different
        def _iterateExtraBinaries(plugin, value):
            if value is None:
                pass
            elif isinstance(value, IncludedEntryPoint):
                yield value
            elif isinstance(value, (tuple, list)) or inspect.isgenerator(value):
                for val in value:
                    for v in _iterateExtraBinaries(plugin, val):
                        yield v
            else:
                plugin.sysexit(
                    "Returned object '%s' for module '%s' but should do 'IncludedEntryPoint' or generator."
                    % (repr(value), module.asString())
                )

        for plugin in getActivePlugins():
            for entry_point in _iterateExtraBinaries(
                plugin, plugin.getExtraDlls(module)
            ):
                result.append(entry_point)

        return result

    @staticmethod
    def getModuleSpecificDllPaths(module_name):
        """Provide a list of directories, where DLLs should be searched for this package (or module).

        Args:
            module_name: name of a package or module, for which the DLL path addition applies.

        """
        result = OrderedSet()
        for plugin in getActivePlugins():
            for dll_path in plugin.getModuleSpecificDllPaths(module_name):
                result.add(dll_path)

        return result

    sys_path_additions_cache = {}

    @classmethod
    def getModuleSysPathAdditions(cls, module_name):
        """Provide a list of directories, that should be considered in 'PYTHONPATH' when this module is used.

        Args:
            module_name: name of a package or module
        Returns:
            iterable of paths
        """

        if module_name not in cls.sys_path_additions_cache:
            cls.sys_path_additions_cache[module_name] = OrderedSet()

            for plugin in getActivePlugins():
                for dll_path in plugin.getModuleSysPathAdditions(module_name):
                    cls.sys_path_additions_cache[module_name].add(dll_path)

        return cls.sys_path_additions_cache[module_name]

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

        return to_remove

    @staticmethod
    def considerDataFiles(module):
        """For a given module, ask plugins for any needed data files it may require.

        Args:
            module: module object
        Yields:
            Data file description pairs, either (source, dest) or (func, dest)
            where the func will be called to create the content dynamically.
        """

        def _iterateIncludedDataFiles(plugin, value):
            if value is None:
                pass
            elif isinstance(value, IncludedDataFile):
                yield value
            elif inspect.isgenerator(value):
                for val in value:
                    for v in _iterateIncludedDataFiles(plugin, val):
                        yield v
            else:
                plugin.sysexit("Plugin return non-datafile '%s'" % repr(value))

        for plugin in getActivePlugins():
            for value in plugin.considerDataFiles(module):
                for included_datafile in _iterateIncludedDataFiles(plugin, value):
                    yield included_datafile

    @staticmethod
    def getDataFileTags(included_datafile):
        tags = OrderedSet([included_datafile.kind])

        tags.update(Options.getDataFileTags(tags))

        for plugin in getActivePlugins():
            plugin.updateDataFileTags(included_datafile)

        return tags

    @staticmethod
    def onDataFileTags(included_datafile):
        for plugin in getActivePlugins():
            plugin.onDataFileTags(included_datafile)

    @classmethod
    def _createTriggerLoadedModule(cls, module, trigger_name, code, flags):
        """Create a "trigger" for a module to be imported.

        Notes:
            The trigger will incorporate the code to be prepended / appended.
            Called by @onModuleDiscovered.

        Args:
            module: the module object (serves as dict key)
            trigger_name: string ("preLoad"/"postLoad")
            code: the code string

        Returns
            trigger_module
        """

        from nuitka.tree.Building import buildModule

        module_name = makeTriggerModuleName(module.getFullName(), trigger_name)

        # In debug mode, put the files in the build folder, so they can be looked up easily.
        if Options.is_debug and "HIDE_SOURCE" not in flags:
            source_path = os.path.join(
                OutputDirectories.getSourceDirectoryPath(), module_name + ".py"
            )

            putTextFileContents(filename=source_path, contents=code)

        try:
            trigger_module, _added = buildModule(
                module_filename=os.path.join(
                    os.path.dirname(module.getCompileTimeFilename()),
                    module_name.asPath() + ".py",
                ),
                module_name=module_name,
                source_code=code,
                is_top=False,
                is_main=False,
                is_extension=False,
                is_fake=module_name,
                hide_syntax_error=False,
            )
        except SyntaxError:
            plugins_logger.sysexit(
                "SyntaxError in plugin provided source code for '%s'." % module_name
            )

        if trigger_module.getCompilationMode() == "bytecode":
            trigger_module.setSourceCode(code)

        return trigger_module

    @classmethod
    def onModuleDiscovered(cls, module):
        # We offer plugins many ways to provide extra stuff
        # pylint: disable=too-many-branches,too-many-locals,too-many-statements

        full_name = module.getFullName()

        def _untangleLoadDescription(description):
            if description and inspect.isgenerator(description):
                description = tuple(description)

            if description:
                if type(description[0]) not in (tuple, list):
                    description = [description]

                for desc in description:
                    if desc is None:
                        pass
                    elif len(desc) == 2:
                        code, reason = desc
                        flags = ()
                    else:
                        code, reason, flags = desc
                        if type(flags) is str:
                            flags = (flags,)

                    yield plugin, code, reason, flags

        def _untangleFakeDesc(description):
            if description and inspect.isgenerator(description):
                description = tuple(description)

            if description:
                if type(description[0]) not in (tuple, list):
                    description = [description]

                for desc in description:
                    assert len(desc) == 4, desc
                    yield plugin, desc[0], desc[1], desc[2], desc[3]

        pre_module_load_descriptions = []
        post_module_load_descriptions = []
        fake_module_descriptions = []

        for plugin in getActivePlugins():
            plugin.onModuleDiscovered(module)

            pre_module_load_descriptions.extend(
                _untangleLoadDescription(
                    description=plugin.createPreModuleLoadCode(module)
                )
            )
            post_module_load_descriptions.extend(
                _untangleLoadDescription(
                    description=plugin.createPostModuleLoadCode(module)
                )
            )
            fake_module_descriptions.extend(
                _untangleFakeDesc(description=plugin.createFakeModuleDependency(module))
            )

        if pre_module_load_descriptions:
            total_code = []
            total_flags = OrderedSet()
            reasons = []

            for plugin, pre_code, reason, flags in pre_module_load_descriptions:
                if pre_code:
                    plugin.info(
                        "Injecting pre-module load code for module '%s':" % full_name
                    )
                    for line in reason.split("\n"):
                        plugin.info("    " + line)

                    total_code.append(pre_code)
                    total_flags.update(flags)
                    reasons.append(reason)

            if total_code:
                assert full_name not in pre_modules

                pre_modules[full_name] = cls._createTriggerLoadedModule(
                    module=module,
                    trigger_name=pre_module_load_trigger_name,
                    code="\n\n".join(total_code),
                    flags=total_flags,
                )
                pre_modules_reasons[full_name] = tuple(reasons)

        if post_module_load_descriptions:
            total_code = []
            total_flags = OrderedSet()
            reasons = []

            for plugin, post_code, reason, flags in post_module_load_descriptions:
                if post_code:
                    plugin.info(
                        "Injecting post-module load code for module '%s':" % full_name
                    )
                    for line in reason.split("\n"):
                        plugin.info("    " + line)

                    total_code.append(post_code)
                    total_flags.update(flags)
                    reasons.append(reason)

            if total_code:
                assert full_name not in post_modules

                post_modules[full_name] = cls._createTriggerLoadedModule(
                    module=module,
                    trigger_name=post_module_load_trigger_name,
                    code="\n\n".join(total_code),
                    flags=total_flags,
                )
                post_modules_reasons[full_name] = reasons

        if fake_module_descriptions:
            fake_modules[full_name] = []

            from nuitka.tree.Building import buildModule

            for (
                plugin,
                fake_module_name,
                source_code,
                fake_filename,
                reason,
            ) in fake_module_descriptions:
                fake_module, _added = buildModule(
                    module_filename=fake_filename,
                    module_name=fake_module_name,
                    source_code=source_code,
                    is_top=False,
                    is_main=False,
                    is_extension=False,
                    is_fake=fake_module_name,
                    hide_syntax_error=False,
                )

                if fake_module.getCompilationMode() == "bytecode":
                    fake_module.setSourceCode(source_code)

                fake_modules[full_name].append((fake_module, plugin, reason))

    @staticmethod
    def onModuleSourceCode(module_name, source_code):
        assert type(module_name) is ModuleName
        assert type(source_code) is str

        contributing_plugins = OrderedSet()

        for plugin in getActivePlugins():
            new_source_code = plugin.onModuleSourceCode(module_name, source_code)
            if new_source_code is not None and new_source_code != source_code:
                source_code = new_source_code
                contributing_plugins.add(plugin)

            assert type(source_code) is str

        return source_code, contributing_plugins

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
    def onModuleEncounter(module_name, module_filename, module_kind):
        result = None
        deciding_plugins = []

        for plugin in getActivePlugins():
            must_recurse = plugin.onModuleEncounter(
                module_name=module_name,
                module_filename=module_filename,
                module_kind=module_kind,
            )

            if must_recurse is None:
                continue

            if type(must_recurse) is not tuple and must_recurse not in (True, False):
                plugin.sysexit(
                    "Error, onModuleEncounter code failed to return a None or tuple(bool, reason) result."
                )

            if result is not None:
                # false alarm, pylint: disable=unsubscriptable-object
                if result[0] != must_recurse[0]:
                    plugin.sysexit(
                        "Error, decision %s does not match other plugin '%s' decision."
                        % (must_recurse[0], ".".join(deciding_plugins))
                    )

            deciding_plugins.append(plugin.plugin_name)
            result = must_recurse

        return result

    @staticmethod
    def onModuleRecursion(
        module_name, module_filename, module_kind, using_module, source_ref
    ):
        for plugin in getActivePlugins():
            plugin.onModuleRecursion(
                module_name=module_name,
                module_filename=module_filename,
                module_kind=module_kind,
                using_module=using_module,
                source_ref=source_ref,
            )

    @staticmethod
    def onModuleInitialSet():
        """The initial set of root modules is complete, plugins may add more."""

        from nuitka.ModuleRegistry import addRootModule

        for plugin in getActivePlugins():
            for module in plugin.onModuleInitialSet():
                addRootModule(module)

    @staticmethod
    def onModuleCompleteSet():
        """The final set of modules is determined, this is only for inspection, cannot change."""
        from nuitka.ModuleRegistry import getDoneModules

        # Make sure it's immutable.
        module_set = tuple(getDoneModules())

        for plugin in getActivePlugins():
            plugin.onModuleCompleteSet(module_set)

    @staticmethod
    def suppressUnknownImportWarning(importing, source_ref, module_name):
        """Let plugins decide whether to suppress import warnings for an unknown module.

        Notes:
            If all plugins return False or None, the return will be False, else True.
        Args:
            importing: the module which is importing "module_name"
            source_ref: pointer to file source code or bytecode
            module_name: the module to be imported
        returns:
            True or False (default)
        """
        source_ref = importing.getSourceReference()

        for plugin in getActivePlugins():
            if plugin.suppressUnknownImportWarning(importing, module_name, source_ref):
                return True

        return False

    @staticmethod
    def decideCompilation(module_name):
        """Let plugins decide whether to C compile a module or include as bytecode.

        Notes:
            The decision is made by the first plugin not returning None.

        Returns:
            "compiled" (default) or "bytecode".
        """
        for plugin in getActivePlugins():
            value = plugin.decideCompilation(module_name)

            if value is not None:
                assert value in ("compiled", "bytecode")
                return value

        return None

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

        # spell-checker: ignore -Dkey

        if cls.preprocessor_symbols is None:
            cls.preprocessor_symbols = OrderedDict()

            for plugin in getActivePlugins():
                value = plugin.getPreprocessorSymbols()

                if value is not None:
                    assert type(value) is dict, value

                    # We order per plugin, but from the plugins, lets just take a dict
                    # and achieve determinism by ordering the defines by name.
                    for key, value in sorted(value.items()):
                        # False alarm, pylint: disable=I0021,unsupported-assignment-operation
                        cls.preprocessor_symbols[key] = value

        return cls.preprocessor_symbols

    build_definitions = None

    @classmethod
    def getBuildDefinitions(cls):
        """Let plugins provide C source defines to be used in compilation.

        Notes:
            The plugins can each contribute, but are hopefully using
            a namespace for their defines. Only specific code sees these
            if it chooses to include "build_definitions.h" file.

        Returns:
            OrderedDict() with keys and values."
        """

        if cls.build_definitions is None:
            cls.build_definitions = OrderedDict()

            for plugin in getActivePlugins():
                value = plugin.getBuildDefinitions()

                if value is not None:
                    assert type(value) is dict, value

                    # We order per plugin, but from the plugins themselves, lets just assume
                    # unordered dict and achieve determinism by ordering the defines by name.
                    for key, value in sorted(value.items()):
                        # False alarm, pylint: disable=I0021,unsupported-assignment-operation
                        cls.build_definitions[key] = value

        return cls.build_definitions

    extra_include_directories = None

    @classmethod
    def getExtraIncludeDirectories(cls):
        """Let plugins extra directories to use for C includes in compilation.

        Notes:
            The plugins can each contribute, but are hopefully not colliding,
            order will be plugin order.

        Returns:
            OrderedSet() of paths to include as well.
        """
        if cls.extra_include_directories is None:
            cls.extra_include_directories = OrderedSet()

            for plugin in getActivePlugins():
                value = plugin.getExtraIncludeDirectories()

                if value:
                    cls.extra_include_directories.update(value)

        return cls.extra_include_directories

    @staticmethod
    def _getExtraCodeFiles(for_onefile):
        result = OrderedDict()

        for plugin in getActivePlugins():
            value = plugin.getExtraCodeFiles()

            if value is not None:
                assert type(value) is dict

                # We order per plugin, but from the plugins, lets just take a dict
                # and achieve determinism by ordering the files by name.
                for key, value in sorted(value.items()):

                    if (for_onefile and not "onefile_" in key) or (
                        not for_onefile and "onefile_" in key
                    ):
                        continue

                    if not key.startswith("nuitka_"):
                        key = "plugin." + plugin.plugin_name + "." + key

                    assert key not in result, key
                    result[key] = value

        return result

    @staticmethod
    def writeExtraCodeFiles(onefile):
        # Circular dependency.
        from nuitka.tree.SourceHandling import writeSourceCode

        source_dir = OutputDirectories.getSourceDirectoryPath(onefile=onefile)

        for filename, source_code in Plugins._getExtraCodeFiles(onefile).items():
            target_dir = os.path.join(source_dir, "plugins")

            if not os.path.isdir(target_dir):
                makePath(target_dir)

            writeSourceCode(
                filename=os.path.join(target_dir, filename), source_code=source_code
            )

    extra_link_libraries = None

    @classmethod
    def getExtraLinkLibraries(cls):
        if cls.extra_link_libraries is None:
            cls.extra_link_libraries = OrderedSet()

            for plugin in getActivePlugins():
                value = plugin.getExtraLinkLibraries()

                if value is not None:
                    if isinstance(value, basestring):
                        cls.extra_link_libraries.add(os.path.normcase(value))
                    else:
                        for library_name in value:
                            cls.extra_link_libraries.add(os.path.normcase(library_name))

        return cls.extra_link_libraries

    extra_link_directories = None

    @classmethod
    def getExtraLinkDirectories(cls):
        if cls.extra_link_directories is None:
            cls.extra_link_directories = OrderedSet()

            for plugin in getActivePlugins():
                value = plugin.getExtraLinkDirectories()

                if value is not None:
                    if isinstance(value, basestring):
                        cls.extra_link_directories.add(value)
                    else:
                        for dir_name in value:
                            cls.extra_link_directories.add(dir_name)

        return cls.extra_link_directories

    @classmethod
    def onDataComposerRun(cls):
        for plugin in getActivePlugins():
            plugin.onDataComposerRun()

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

    @classmethod
    def onFunctionBodyParsing(cls, provider, function_name, body):
        module_name = provider.getParentModule().getFullName()

        for plugin in getActivePlugins():
            plugin.onFunctionBodyParsing(
                module_name=module_name,
                function_name=function_name,
                body=body,
            )

    @classmethod
    def getCacheContributionValues(cls, module_name):
        for plugin in getActivePlugins():
            for value in plugin.getCacheContributionValues(module_name):
                yield value


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
            and not obj.__name__.endswith("PluginBase")
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


def addStandardPluginCommandLineOptions(parser):
    loadPlugins()

    for (_plugin_name, (plugin_class, _plugin_detector)) in sorted(
        plugin_name2plugin_classes.items()
    ):
        if plugin_class.isAlwaysEnabled():
            _addPluginCommandLineOptions(
                parser=parser,
                plugin_class=plugin_class,
            )


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
    # Many cases, often with UI related decisions, pylint: disable=too-many-branches

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

    plugin_detectors = OrderedSet()

    for (plugin_name, (plugin_class, plugin_detector)) in sorted(
        plugin_name2plugin_classes.items()
    ):
        if plugin_name in Options.getPluginsEnabled():
            if plugin_class.isAlwaysEnabled():
                plugin_class.warning(
                    "Plugin is defined as always enabled, no need to enable it."
                )

            if plugin_class.isRelevant():
                _addActivePlugin(plugin_class, args=True)
            elif plugin_class.isDeprecated():
                plugin_class.warning(
                    "This plugin has been deprecated, do not enable it anymore."
                )
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
            plugin_detectors.add(plugin_detector)

    for plugin_class in user_plugins:
        _addActivePlugin(plugin_class, args=True)

    # Suppress GUI toolkit detectors automatically.
    for plugin_detector in plugin_detectors:
        if (
            not has_active_gui_toolkit_plugin
            or plugin_detector.plugin_name not in getGuiPluginNames()
        ):
            _addActivePlugin(plugin_detector, args=False)


def _addPluginCommandLineOptions(parser, plugin_class):
    plugin_name = plugin_class.plugin_name

    if plugin_name not in plugin_options:
        option_group = OptionGroup(parser, "Plugin options of '%s'" % plugin_name)
        try:
            plugin_class.addPluginCommandLineOptions(option_group)
        except OptionConflictError as e:
            for other_plugin_name, other_plugin_option_list in plugin_options.items():
                for other_plugin_option in other_plugin_option_list:
                    # no public interface for that, pylint: disable=protected-access
                    if (
                        e.option_id in other_plugin_option._long_opts
                        or other_plugin_option._short_opts
                    ):
                        plugins_logger.sysexit(
                            "Plugin '%s' failed to add options due to conflict with '%s' from plugin '%s."
                            % (plugin_name, e.option_id, other_plugin_name)
                        )

        if option_group.option_list:
            parser.add_option_group(option_group)
            plugin_options[plugin_name] = option_group.option_list
        else:
            plugin_options[plugin_name] = ()


def addPluginCommandLineOptions(parser, plugin_names):
    """Add option group for the plugin to the parser.

    Notes:
        This is exclusively for use in the command line parsing. Not all
        plugins have to have options. But this will add them to the
        parser in a first pass, so they can be recognized in a second
        pass with them included.

    Returns:
        None
    """
    for plugin_name in plugin_names:
        plugin_class = getPluginClass(plugin_name)
        _addPluginCommandLineOptions(parser=parser, plugin_class=plugin_class)


def addUserPluginCommandLineOptions(parser, filename):
    plugin_class = loadUserPlugin(filename)
    _addPluginCommandLineOptions(parser=parser, plugin_class=plugin_class)

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
                    "Error, required plugin argument '%s' of Nuitka plugin '%s' not given."
                    % (option_name, plugin_name)
                )

        result[option.dest] = arg_value

    return result


def replaceTriggerModule(old, new):
    """Replace a trigger module with another form if it. For use in bytecode demotion."""

    found = None
    for key, value in pre_modules.items():
        if value is old:
            found = key
            break

    if found is not None:
        pre_modules[found] = new

    found = None
    for key, value in post_modules.items():
        if value is old:
            found = key
            break

    if found is not None:
        post_modules[found] = new


def isTriggerModule(module):
    """Decide of a module is a trigger module."""
    return module in pre_modules.values() or module in post_modules.values()
