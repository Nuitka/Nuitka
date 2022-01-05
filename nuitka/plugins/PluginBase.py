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

This is to provide the base class for all plugins. Some of which are part of
proper Nuitka, and some of which are waiting to be created and submitted for
inclusion by you.

The base class will serve as documentation. And it will point to examples of
it being used.
"""

import inspect
import os
import shutil
import sys
from collections import namedtuple

from nuitka.__past__ import getMetaClassBase
from nuitka.freezer.IncludedEntryPoints import makeDllEntryPoint
from nuitka.Options import isStandaloneMode
from nuitka.Tracing import plugins_logger
from nuitka.utils.Execution import NuitkaCalledProcessError, check_output
from nuitka.utils.FileOperations import makePath
from nuitka.utils.ModuleNames import ModuleName
from nuitka.utils.SharedLibraries import locateDLL, locateDLLsInDirectory

pre_modules = {}
post_modules = {}

warned_unused_plugins = set()


class NuitkaPluginBase(getMetaClassBase("Plugin")):
    """Nuitka base class for all plugins.

    Derive your plugin from "NuitkaPluginBase" please.
    For instructions, see https://github.com/Nuitka/Nuitka/blob/orsiris/UserPlugin-Creation.rst

    Plugins allow to adapt Nuitka's behaviour in a number of ways as explained
    below at the individual methods.

    It is used to deal with special requirements some packages may have (e.g. PyQt
    and tkinter), data files to be included (e.g. certifi), inserting hidden
    code, coping with otherwise undetectable needs, or issuing messages in
    certain situations.

    A plugin in general must be enabled to be used by Nuitka. This happens by
    specifying "--enable-plugin" (standard plugins) or by "--user-plugin" (user
    plugins) in the Nuitka command line. However, some plugins are always enabled
    and invisible to the user.

    Nuitka comes with a number of "standard" plugins to be enabled as needed.
    What they are can be displayed using "nuitka --plugin-list file.py" (filename
    required but ignored).

    User plugins may be specified (and implicitly enabled) using their Python
    script pathname.
    """

    # Standard plugins must provide this as a unique string which Nuitka
    # then uses to identify them.
    #
    # User plugins are identified by their path and implicitly activated.
    # They however still need to specify some arbitrary non-blank string here,
    # which does not equal the name of an inactivated standard plugin.
    # For working with options, user plugins must set this variable to
    # the script's path (use __file__, __module__ or __name__).
    plugin_name = None

    @staticmethod
    def isAlwaysEnabled():
        """Request to be always enabled.

        Notes:
            Setting this to true is only applicable to standard plugins. In
            this case, the plugin will be enabled upon Nuitka start-up. Any
            plugin detector class will then be ignored. Method isRelevant() may
            also be present and can be used to fine-control enabling the
            plugin: A to-be-enabled, but irrelevant plugin will still not be
            activated.
        Returns:
            True or False
        """
        return False

    @classmethod
    def isRelevant(cls):
        """Consider if the plugin is relevant.

        Notes:
            A plugin may only be a needed on a certain OS, or with some options,
            but this is only a class method, so you will not have much run time
            information.

        Returns:
            True or False

        """
        return True

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        # Call group.add_option() here.
        pass

    @classmethod
    def getTagDataFileTagOptions(cls):
        # Return tag_name, description tuples
        return ()

    @classmethod
    def getPluginDefaultOptionValues(cls):
        """This method is used to get a values to use as defaults.

        Since the defaults are in the command line options, we call
        that and extract them.
        """

        from optparse import OptionGroup, OptionParser

        parser = OptionParser()
        group = OptionGroup(parser, "Pseudo Target")
        cls.addPluginCommandLineOptions(group)

        result = {}
        for option in group.option_list:
            result[option.dest] = option.default

        return result

    def isRequiredImplicitImport(self, module, full_name):
        """Indicate whether an implicitly imported module should be accepted.

        Notes:
            You may negate importing a module specified as "implicit import",
            although this is an unexpected event.

        Args:
            module: the module object
            full_name: of the implicitly import module
        Returns:
            True or False
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return True

    def getImplicitImports(self, module):
        """Return the implicit imports for a given module (iterator).

        Args:
            module: the module object
        Yields:
            implicit imports for the module
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return ()

    def onModuleSourceCode(self, module_name, source_code):
        """Inspect or modify source code.

        Args:
            module_name: (str) name of module
            source_code: (str) its source code
        Returns:
            source_code (str)
        Notes:
            Default implementation forwards to `checkModuleSourceCode` which is
            going to allow simply checking the source code without the need to
            pass it back.
        """
        self.checkModuleSourceCode(module_name, source_code)

        return source_code

    def checkModuleSourceCode(self, module_name, source_code):
        """Inspect source code.

        Args:
            module_name: (str) name of module
            source_code: (str) its source code
        Returns:
            None
        """

    def onFrozenModuleSourceCode(self, module_name, is_package, source_code):
        """Inspect or modify frozen module source code.

        Args:
            module_name: (str) full name of module
            is_package: (bool) True indicates a package
            source_code: (str) its source code
        Returns:
            source_code (str)
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return source_code

    def onFrozenModuleBytecode(self, module_name, is_package, bytecode):
        """Inspect or modify frozen module byte code.

        Args:
            module_name: (str) name of module
            is_package: (bool) True indicates a package
            bytecode: (bytes) byte code
        Returns:
            bytecode (bytes)
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return bytecode

    @staticmethod
    def createPreModuleLoadCode(module):
        """Create code to execute before importing a module.

        Notes:
            Called by @onModuleDiscovered.

        Args:
            module: the module object
        Returns:
            None (does not apply, default)
            tuple (code, documentary string)
            tuple (code, documentary string, flags)
        """
        # Virtual method, pylint: disable=unused-argument
        return None

    @staticmethod
    def createPostModuleLoadCode(module):
        """Create code to execute after loading to a module.

        Notes:
            Called by @onModuleDiscovered.

        Args:
            module: the module object

        Returns:
            None (does not apply, default)
            tuple (code, documentary string)
            tuple (code, documentary string, flags)
        """
        # Virtual method, pylint: disable=unused-argument
        return None

    def onModuleDiscovered(self, module):
        """Called with a module to be loaded.

        Notes:
            We may specify code to be prepended and/or appended to this module.
            This code is stored in the appropriate dict.
            For every imported module and each of these two options, only one plugin may do this.
            We check this condition here.

        Args:
            module: the module object
        Returns:
            None
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

    def onModuleEncounter(self, module_filename, module_name, module_kind):
        """Help decide whether to include a module.

        Args:
            module_filename: filename
            module_name: full module name
            module_kind: one of "py", "shlib" (shared library)
        Returns:
            True or False
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

    def onModuleInitialSet(self):
        """Provide extra modules to the initial root module set.

        Args:
            None
        Returns:
            Iterable of modules, may yield.
        """
        # Virtual method, pylint: disable=no-self-use
        return ()

    def onModuleCompleteSet(self, module_set):
        """Provide extra modules to the initial root module set.

        Args:
            module_set - tuple of module objects
        Returns:
            None
        Notes:
            You must not change anything, this is purely for warning
            and error checking, and potentially for later stages to
            prepare.
        """

    @staticmethod
    def locateModule(module_name):
        """Provide a filename / -path for a to-be-imported module.

        Args:
            importing: module object that asked for it (tracing only)
            module_name: (str or ModuleName) full name of module
        Returns:
            filename for module
        """

        from nuitka.importing.Importing import locateModule

        _module_name, module_filename, _finding = locateModule(
            module_name=ModuleName(module_name), parent_package=None, level=0
        )

        return module_filename

    @staticmethod
    def locateModules(module_name):
        """Provide a filename / -path for a to-be-imported module.

        Args:
            module_name: (str or ModuleName) full name of module
        Returns:
            list of ModuleName
        """

        from nuitka.importing.Importing import locateModules

        return locateModules(module_name)

    @classmethod
    def locateDLL(cls, dll_name):
        """Locate a DLL by name."""
        return locateDLL(dll_name)

    @classmethod
    def locateDLLsInDirectory(cls, directory):
        """Locate all DLLs in a folder

        Returns:
            list of (filename, filename_relative, dll_extension)
        """
        return locateDLLsInDirectory(directory)

    @classmethod
    def makeDllEntryPoint(cls, source_path, dest_path, package_name):
        """Create an entry point, as expected to be provided by getExtraDlls."""
        return makeDllEntryPoint(
            source_path=source_path, dest_path=dest_path, package_name=package_name
        )

    def reportFileCount(self, module_name, count, section=None):
        if count:
            msg = "Found %d %s DLLs from '%s' %sinstallation." % (
                count,
                "file" if count < 2 else "files",
                "" if not section else section,
                module_name.asString(),
            )

            self.info(msg)

    def considerExtraDlls(self, dist_dir, module):
        """Provide a tuple of names of binaries to be included.

        Args:
            dist_dir: the distribution folder
            module: the module object needing the binaries
        Returns:
            tuple
        """
        # TODO: This should no longer be here, as this API is obsolete, pylint: disable=unused-argument
        for included_entry_point in self.getExtraDlls(module):
            # Copy to the dist directory, which normally should not be a plugin task, but is for now.
            makePath(os.path.dirname(included_entry_point.dest_path))

            shutil.copyfile(
                included_entry_point.source_path, included_entry_point.dest_path
            )

            yield included_entry_point

    def getExtraDlls(self, module):
        """Provide IncludedEntryPoint named tuples describing extra needs of the module.

        Args:
            module: the module object needing the binaries
        Returns:
            yields IncludedEntryPoint objects

        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return ()

    def getModuleSpecificDllPaths(self, module_name):
        """Provide a list of directories, where DLLs should be searched for this package (or module).

        Args:
            module_name: name of a package or module, for which the DLL path addition applies.
        Returns:
            iterable of paths
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return ()

    def removeDllDependencies(self, dll_filename, dll_filenames):
        """Yield any DLLs / shared libraries not to be included in distribution.

        Args:
            dll_filename: DLL name
            dll_filenames: list of DLLs
        Yields:
            yielded filenames to exclude
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return ()

    def considerDataFiles(self, module):
        """Yield data file names (source|func, target) for inclusion (iterator).

        Args:
            module: module object that may need extra data files
        Yields:
            Data file description pairs, either (source, dest) or (func, dest)
            where the func will be called to create the content dynamically.

        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return ()

    def onStandaloneDistributionFinished(self, dist_dir):
        """Called after successfully creating a standalone distribution.

        Note:
            It is up to the plugin to take subsequent action. Examples are:
            insert additional information (license, copyright, company or
            application description), create installation material, further
            folder clean-up, start downstream applications etc.

        Args:
            dist_dir: the created distribution folder

        Returns:
            None
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

    def onOnefileFinished(self, filename):
        """Called after successfully creating a onefile executable.

        Note:
            It is up to the plugin to take subsequent action. Examples are:
            insert additional information (license, copyright, company or
            application description), create installation material, further
            folder clean-up, start downstream applications etc.

        Args:
            filename: the created onefile executable

        Returns:
            None
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

    def onFinalResult(self, filename):
        """Called after successfully finishing a compilation.

        Note:
            Plugins normally don't need this, and what filename is will be
            heavily dependent on compilation modes. Actions can be take here,
            e.g. commercial plugins output generated keys near that executable
            path.
        Args:
            filename: the created binary (module, accelerated exe, dist exe, onefile exe)

        Returns:
            None
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

    def suppressUnknownImportWarning(self, importing, module_name, source_ref):
        """Suppress import warnings for unknown modules.

        Args:
            importing: the module object
            module_name: name of module
            source_ref: ???
        Returns:
            True or False
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return False

    def decideCompilation(self, module_name):
        """Decide whether to compile a module (or just use its bytecode).

        Notes:
            The first plugin not returning None makes the decision. Thereafter,
            no other plugins will be checked. If all plugins return None, the
            module will be compiled.

        Args:
            module_name: name of module

        Returns:
            "compiled" or "bytecode" or None (no opinion, use by default)
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

    def getPreprocessorSymbols(self):
        """Decide which C defines to be used in compilation.

        Notes:
            The plugins can each contribute, but are hopefully using
            a namespace for their defines.

        Returns:
            None for no defines, otherwise dictionary of key to be
            defined, and non-None values if any, i.e. no "-Dkey" only
        """

        # Virtual method, pylint: disable=no-self-use
        return None

    def getExtraCodeFiles(self):
        """Add extra code files to the compilation.

        Notes:
            This is generally a bad idea to use unless you absolutely
            know what you are doing.

        Returns:
            None for no extra codes, otherwise dictionary of key to be
            filename, and value to be source code.
        """

        # Virtual method, pylint: disable=no-self-use
        return None

    def getExtraLinkLibraries(self):
        """Decide which link library should be added.

        Notes:
            Names provided multiple times, e.g. by multiple plugins are
            only added once.

        Returns:
            None for no extra link library, otherwise the name as a **str**
            or an iterable of names of link libraries.
        """

        # Virtual method, pylint: disable=no-self-use
        return None

    def getExtraLinkDirectories(self):
        """Decide which link directories should be added.

        Notes:
            Directories provided multiple times, e.g. by multiple plugins are
            only added once.

        Returns:
            None for no extra link directory, otherwise the name as a **str**
            or an iterable of names of link directories.
        """

        # Virtual method, pylint: disable=no-self-use
        return None

    def warnUnusedPlugin(self, message):
        """An inactive plugin may issue a warning if it believes this may be wrong.

        Returns:
            None
        """
        if self.plugin_name not in warned_unused_plugins:
            warned_unused_plugins.add(self.plugin_name)

            plugins_logger.warning(
                "Use '--enable-plugin=%s' for: %s" % (self.plugin_name, message)
            )

    def onDataComposerResult(self, blob_filename):
        """Internal use only.

        Returns:
            None
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

    def encodeDataComposerName(self, data_name):
        """Internal use only.

        Returns:
            None
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

    _runtime_information_cache = {}

    def queryRuntimeInformationMultiple(self, info_name, setup_codes, values):
        info_name = self.plugin_name + "_" + info_name

        if info_name in self._runtime_information_cache:
            return self._runtime_information_cache[info_name]

        keys = []
        query_codes = []

        for key, value_expression in values:
            keys.append(key)

            query_codes.append("print(repr(%s))" % value_expression)
            query_codes.append('print("-" * 27)')

        if type(setup_codes) is str:
            setup_codes = setup_codes.split("\n")

        cmd = r"""\
from __future__ import print_function
from __future__ import absolute_import

try:
    %(setup_codes)s
except ImportError:
    import sys
    sys.exit(38)
%(query_codes)s
""" % {
            "setup_codes": "\n   ".join(setup_codes),
            "query_codes": "\n".join(query_codes),
        }

        try:
            feedback = check_output([sys.executable, "-c", cmd])
        except NuitkaCalledProcessError as e:
            if e.returncode == 38:
                return None
            raise

        if str is not bytes:  # We want to work with strings, that's hopefully OK.
            feedback = feedback.decode("utf8")

        # Ignore Windows newlines difference.
        feedback = [line.strip() for line in feedback.splitlines()]

        if feedback.count("-" * 27) != len(keys):
            self.sysexit(
                "Error, mismatch in output retrieving %r information." % info_name
            )

        feedback = [line for line in feedback if line != "-" * 27]

        NamedTupleResult = namedtuple(info_name, keys)

        # We are being lazy here, the code is trusted, pylint: disable=eval-used
        self._runtime_information_cache[info_name] = NamedTupleResult(
            *(eval(value) for value in feedback)
        )

        return self._runtime_information_cache[info_name]

    def queryRuntimeInformationSingle(self, setup_codes, value):
        return self.queryRuntimeInformationMultiple(
            info_name="temp_info_for_" + self.plugin_name.replace("-", "_"),
            setup_codes=setup_codes,
            values=(("key", value),),
        ).key

    @staticmethod
    def onFunctionBodyParsing(module_name, function_name, body):
        pass

    @classmethod
    def warning(cls, message):
        plugins_logger.warning(cls.plugin_name + ": " + message)

    @classmethod
    def info(cls, message):
        plugins_logger.info(cls.plugin_name + ": " + message)

    @classmethod
    def sysexit(cls, message):
        plugins_logger.sysexit(cls.plugin_name + ": " + message)


def isTriggerModule(module):
    return module in pre_modules.values() or module in post_modules.values()


def replaceTriggerModule(old, new):
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


import functools


def standalone_only(func):
    """For plugins that have functionality that should be done in standalone mode only."""

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        if isStandaloneMode():
            return func(*args, **kwargs)
        else:
            if inspect.isgeneratorfunction(func):
                return ()
            else:
                return None

    return wrapped
