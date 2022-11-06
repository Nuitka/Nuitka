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

The base class will serve as documentation. And it will point to examples of
it being used.
"""

import ast
import functools
import inspect
import sys
from collections import namedtuple

from nuitka.__past__ import getMetaClassBase
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.freezer.IncludedDataFiles import (
    makeIncludedDataDirectory,
    makeIncludedDataFile,
    makeIncludedEmptyDirectory,
    makeIncludedGeneratedDataFile,
    makeIncludedPackageDataFiles,
)
from nuitka.freezer.IncludedEntryPoints import (
    makeDllEntryPoint,
    makeExeEntryPoint,
)
from nuitka.ModuleRegistry import (
    addModuleInfluencingCondition,
    getModuleInclusionInfoByName,
)
from nuitka.Options import (
    isStandaloneMode,
    shallMakeModule,
    shallShowExecutedCommands,
)
from nuitka.PythonFlavors import isAnacondaPython, isDebianPackagePython
from nuitka.PythonVersions import getSupportedPythonVersions, python_version
from nuitka.Tracing import plugins_logger
from nuitka.utils.Execution import NuitkaCalledProcessError, check_output
from nuitka.utils.ModuleNames import (
    ModuleName,
    makeTriggerModuleName,
    post_module_load_trigger_name,
    pre_module_load_trigger_name,
)
from nuitka.utils.SharedLibraries import locateDLL, locateDLLsInDirectory
from nuitka.utils.Utils import isLinux, isMacOS, isWin32Windows

_warned_unused_plugins = set()

# TODO: Could share data cache with meta data nodes
_package_versions = {}


def _convertVersionToTuple(version_str):
    def numberize(v):
        # For now, we ignore rc/post stuff, hoping it doesn't matter for us.
        return int("".join(d for d in v if d.isdigit()))

    return tuple(numberize(d) for d in version_str.split("."))


def _getPackageNameFromDistributionName(distribution_name):
    if distribution_name == "opencv-python":
        return "cv2"
    elif distribution_name == "pyobjc":
        return "objc"
    else:
        return distribution_name


def _getPackageVersion(distribution_name):
    if distribution_name not in _package_versions:
        try:
            if python_version >= 0x380:
                from importlib.metadata import version
            else:
                from importlib_metadata import version

            result = _convertVersionToTuple(version(distribution_name))
        except ImportError:
            try:
                from pkg_resources import (
                    DistributionNotFound,
                    get_distribution,
                )

                try:
                    result = _convertVersionToTuple(
                        get_distribution(distribution_name).version
                    )
                except DistributionNotFound:
                    raise ImportError
            except ImportError:
                # Fallback if nothing is available, which may happen if no package is installed,
                # but only source code is found.
                result = _convertVersionToTuple(
                    __import__(
                        _getPackageNameFromDistributionName(distribution_name)
                    ).__version__
                )

        _package_versions[distribution_name] = result

    return _package_versions[distribution_name]


class NuitkaPluginBase(getMetaClassBase("Plugin")):
    """Nuitka base class for all plugins.

    Derive your plugin from "NuitkaPluginBase" please.
    For instructions, see https://github.com/Nuitka/Nuitka/blob/orsiris/UserPlugin-Creation.rst

    Plugins allow to adapt Nuitka's behavior in a number of ways as explained
    below at the individual methods.

    It is used to deal with special requirements some packages may have (e.g. PyQt
    and tkinter), data files to be included (e.g. "certifi"), inserting hidden
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
        return not cls.isDeprecated()

    @classmethod
    def isDeprecated(cls):
        """Is this a deprecated plugin, i.e. one that has no use anymore."""
        return False

    @classmethod
    def isDetector(cls):
        """Is this a detection plugin, i.e. one which is only there to inform."""
        return hasattr(cls, "detector_for")

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        # Call group.add_option() here.
        pass

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

    @staticmethod
    def createFakeModuleDependency(module):
        """Create module to depend on.

        Notes:
            Called by @onModuleDiscovered.

        Args:
            module: the module object

        Returns:
            None (does not apply, default)
            tuple (code, reason)
            tuple (code, reason, flags)
        """
        # Virtual method, pylint: disable=unused-argument
        return None

    @staticmethod
    def hasPreModuleLoadCode(module_name):
        return (
            getModuleInclusionInfoByName(
                makeTriggerModuleName(module_name, pre_module_load_trigger_name)
            )
            is not None
        )

    @staticmethod
    def hasPostModuleLoadCode(module_name):
        return (
            getModuleInclusionInfoByName(
                makeTriggerModuleName(module_name, post_module_load_trigger_name)
            )
            is not None
        )

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

    def getPackageExtraScanPaths(self, package_name, package_dir):
        """Provide other directories to consider submodules to live in.

        Args:
            module_name: full module name
            package_dir: directory of the package

        Returns:
            Iterable list of directories, non-existent ones are ignored.
        """

        # Virtual method, pylint: disable=no-self-use,unused-argument
        return ()

    def onModuleEncounter(self, module_name, module_filename, module_kind):
        """Help decide whether to include a module.

        Args:
            module_name: full module name
            module_filename: filename
            module_kind: one of "py", "extension" (shared library)
        Returns:
            True or False
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

    def onModuleRecursion(self, module_name, module_filename, module_kind):
        """React to recursion to a module coming up.

        Args:
            module_name: full module name
            module_filename: filename
            module_kind: one of "py", "extension" (shared library)
        Returns:
            None
        """

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

    def makeDllEntryPoint(self, source_path, dest_path, package_name, reason):
        """Create an entry point, as expected to be provided by getExtraDlls."""
        return makeDllEntryPoint(
            logger=self,
            source_path=source_path,
            dest_path=dest_path,
            package_name=package_name,
            reason=reason,
        )

    def makeExeEntryPoint(self, source_path, dest_path, package_name, reason):
        """Create an entry point, as expected to be provided by getExtraDlls."""
        return makeExeEntryPoint(
            logger=self,
            source_path=source_path,
            dest_path=dest_path,
            package_name=package_name,
            reason=reason,
        )

    def reportFileCount(self, module_name, count, section=None):
        if count:
            msg = "Found %d %s DLLs from %s%s installation." % (
                count,
                "file" if count < 2 else "files",
                "" if not section else (" '%s' " % section),
                module_name.asString(),
            )

            self.info(msg)

    def getExtraDlls(self, module):
        """Provide IncludedEntryPoint named tuples describing extra needs of the module.

        Args:
            module: the module object needing the binaries
        Returns:
            yields IncludedEntryPoint objects

        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return ()

    def onCopiedDLL(self, dll_filename):
        """Chance for a plugin to modify DLLs after copy, e.g. to compress it, remove attributes, etc.

        Args:
            dll_filename: the filename of the DLL

        Notes:
            Do not remove or add any files in this method, this will not work well, there
            is e.g. getExtraDLLs API to add things. This is only for post processing as
            described above.

        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

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

    def makeIncludedDataFile(self, source_path, dest_path, reason, tags=""):
        return makeIncludedDataFile(
            source_path=source_path,
            dest_path=dest_path,
            reason=reason,
            tracer=self,
            tags=tags,
        )

    def makeIncludedGeneratedDataFile(self, data, dest_path, reason, tags=""):
        return makeIncludedGeneratedDataFile(
            data=data, dest_path=dest_path, reason=reason, tracer=self, tags=tags
        )

    def makeIncludedDataDirectory(
        self,
        source_path,
        dest_path,
        reason,
        tags="",
        ignore_dirs=(),
        ignore_filenames=(),
        ignore_suffixes=(),
        only_suffixes=(),
        normalize=True,
    ):
        return makeIncludedDataDirectory(
            source_path=source_path,
            dest_path=dest_path,
            reason=reason,
            tracer=self,
            tags=tags,
            ignore_dirs=ignore_dirs,
            ignore_filenames=ignore_filenames,
            ignore_suffixes=ignore_suffixes,
            only_suffixes=only_suffixes,
            normalize=normalize,
        )

    def makeIncludedEmptyDirectory(self, dest_path, reason, tags):
        return makeIncludedEmptyDirectory(
            dest_path=dest_path,
            reason=reason,
            tracer=self,
            tags=tags,
        )

    def makeIncludedPackageDataFiles(
        self, package_name, package_directory, pattern, reason, tags
    ):
        return makeIncludedPackageDataFiles(
            tracer=self,
            package_name=ModuleName(package_name),
            package_directory=package_directory,
            pattern=pattern,
            reason=reason,
            tags=tags,
        )

    def updateDataFileTags(self, included_datafile):
        """Add or remove data file tags."""

    def onDataFileTags(self, included_datafile):
        """Action on data file tags."""

    def onBeforeCodeParsing(self):
        """Prepare for code parsing, normally not needed."""

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

    def onBootstrapBinary(self, filename):
        """Called after successfully creating a bootstrap binary, but without payload.

        Args:
            filename: the created bootstrap binary, will be modified later

        Returns:
            None
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

    def onStandaloneBinary(self, filename):
        """Called after successfully creating a standalone binary.

        Args:
            filename: the created standalone binary

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
        # spell-checker: ignore -Dkey
        return None

    def getBuildDefinitions(self):
        """Decide C source defines to be used in compilation.

        Notes:
            Make sure to use a namespace for your defines, and prefer
            `getPreprocessorSymbols` if you can.

        Returns:
            dict or None for no values
        """
        # Virtual method, pylint: disable=no-self-use
        return None

    def getExtraIncludeDirectories(self):
        """Decide which extra directories to use for C includes in compilation.

        Returns:
            List of directories or None by default
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
        if self.plugin_name not in _warned_unused_plugins:
            _warned_unused_plugins.add(self.plugin_name)

            plugins_logger.warning(
                "Use '--enable-plugin=%s' for: %s" % (self.plugin_name, message)
            )

    def onDataComposerRun(self):
        """Internal use only.

        Returns:
            None
        """
        # Virtual method, pylint: disable=no-self-use
        return None

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
        info_name = self.plugin_name.replace("-", "_") + "_" + info_name

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

        if shallShowExecutedCommands():
            self.info("Executing query command:\n%s" % cmd)

        try:
            feedback = check_output([sys.executable, "-c", cmd])
        except NuitkaCalledProcessError as e:
            if e.returncode == 38:
                return None
            raise

        if str is not bytes:  # We want to work with strings, that's hopefully OK.
            feedback = feedback.decode("utf8")

        if shallShowExecutedCommands():
            self.info("Result of query command:\n%s" % feedback)

        # Ignore Windows newlines difference.
        feedback = [line.strip() for line in feedback.splitlines()]

        if feedback.count("-" * 27) != len(keys):
            self.sysexit(
                "Error, mismatch in output retrieving %r information." % info_name
            )

        feedback = [line for line in feedback if line != "-" * 27]

        NamedTupleResult = namedtuple(info_name, keys)

        self._runtime_information_cache[info_name] = NamedTupleResult(
            *(ast.literal_eval(value) for value in feedback)
        )

        return self._runtime_information_cache[info_name]

    def queryRuntimeInformationSingle(self, setup_codes, value):
        return self.queryRuntimeInformationMultiple(
            info_name="temp_info_for_" + self.plugin_name.replace("-", "_"),
            setup_codes=setup_codes,
            values=(("key", value),),
        ).key

    def onFunctionBodyParsing(self, module_name, function_name, body):
        """Provide a different function body for the function of that module."""
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

    def getCacheContributionValues(self, module_name):
        """Provide values that represent the include of a plugin on the compilation.

        This must be used to invalidate cache results, e.g. when using the
        onFunctionBodyParsing function, and other things, that do not directly
        affect the source code.
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return ()

    @staticmethod
    def getPackageVersion(distribution_name):
        """Provide package version of a distribution."""
        return _getPackageVersion(distribution_name)

    def evaluateCondition(self, full_name, condition, control_tags=()):
        # Note: Caching makes no sense yet, this should all be very fast and
        # cache themselves. TODO: Allow plugins to contribute their own control
        # tag values during creation and during certain actions.
        if condition == "True":
            return True
        if condition == "False":
            return False

        context = TagContext(logger=self, full_name=full_name)
        context.update(control_tags)

        context.update(
            {
                "macos": isMacOS(),
                "win32": isWin32Windows(),
                "linux": isLinux(),
                "anaconda": isAnacondaPython(),
                "debian_python": isDebianPackagePython(),
                "standalone": isStandaloneMode(),
                "module_mode": shallMakeModule(),
                # TODO: Allow to provide this.
                "deployment": False,
                # Module dependent
                "main_module": full_name.getBasename() == "__main__",
                # Querying package versions.
                "version": _getPackageVersion,
            }
        )

        versions = getSupportedPythonVersions()

        for version in versions:
            big, major = version.split(".")
            numeric_version = int(big) * 256 + int(major) * 16
            is_same_or_higher_version = python_version >= numeric_version

            context["python" + big + major + "_or_higher"] = is_same_or_higher_version
            context["before_python" + big + major] = not is_same_or_higher_version

        context["before_python3"] = python_version < 0x300
        context["python3_or_higher"] = python_version >= 0x300

        # We trust the yaml files, pylint: disable=eval-used
        result = eval(condition, context)

        if type(result) is not bool:
            self.sysexit(
                "Error, condition '%s' for module '%s' did not evaluate to boolean result."
                % (condition, full_name)
            )

        addModuleInfluencingCondition(
            module_name=full_name,
            plugin_name=self.plugin_name,
            condition=condition,
            control_tags=context.used_tags,
            result=result,
        )

        return result

    @classmethod
    def warning(cls, message):
        plugins_logger.warning(cls.plugin_name + ": " + message)

    @classmethod
    def info(cls, message):
        plugins_logger.info(cls.plugin_name + ": " + message)

    @classmethod
    def sysexit(cls, message):
        plugins_logger.sysexit(cls.plugin_name + ": " + message)


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


class TagContext(dict):
    def __init__(self, logger, full_name, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

        self.logger = logger
        self.full_name = full_name

        self.used_tags = OrderedSet()

    def __getitem__(self, key):
        try:
            self.used_tags.add(key)

            return dict.__getitem__(self, key)
        except KeyError:
            if key.startswith("use_"):
                return False

            self.logger.sysexit(
                "Identifier '%s' in 'when' configuration of module '%s' is unknown."
                % (key, self.full_name)
            )
