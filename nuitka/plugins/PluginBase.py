#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


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
import os
import sys
import unittest

from nuitka import Options
from nuitka.__past__ import iter_modules, unicode
from nuitka.containers.Namedtuples import makeNamedtupleClass
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.freezer.IncludedDataFiles import (
    decodeDataFileTags,
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
    addModuleInfluencingDetection,
    addModuleInfluencingParameter,
    addModuleInfluencingVariable,
    getModuleInclusionInfoByName,
)
from nuitka.Options import (
    getCompanyName,
    getFileVersion,
    getProductFileVersion,
    getProductName,
    getProductVersion,
    isDeploymentMode,
    isOnefileMode,
    isOnefileTempDirMode,
    isStandaloneMode,
    shallCreateAppBundle,
    shallMakeModule,
    shallShowExecutedCommands,
)
from nuitka.PythonFlavors import (
    isAnacondaPython,
    isDebianPackagePython,
    isNuitkaPython,
)
from nuitka.PythonVersions import (
    getTestExecutionPythonVersions,
    python_version,
    python_version_full_str,
    python_version_str,
)
from nuitka.Tracing import plugins_logger
from nuitka.utils.AppDirs import getAppdirsModule
from nuitka.utils.Distributions import (
    getDistributionFromModuleName,
    getDistributionName,
    isDistributionCondaPackage,
)
from nuitka.utils.Execution import (
    NuitkaCalledProcessError,
    check_output,
    withEnvironmentVarsOverridden,
)
from nuitka.utils.FileOperations import (
    changeFilenameExtension,
    getFileContents,
)
from nuitka.utils.Importing import getSharedLibrarySuffix, isBuiltinModuleName
from nuitka.utils.ModuleNames import (
    ModuleName,
    makeTriggerModuleName,
    post_module_load_trigger_name,
    pre_module_load_trigger_name,
)
from nuitka.utils.SharedLibraries import locateDLL, locateDLLsInDirectory
from nuitka.utils.SlotMetaClasses import getMetaClassBase
from nuitka.utils.StaticLibraries import getSystemStaticLibPythonPath
from nuitka.utils.Utils import (
    getArchitecture,
    isAndroidBasedLinux,
    isLinux,
    isMacOS,
    isWin32Windows,
    withNoWarning,
)

_warned_unused_plugins = set()

# TODO: Could share data cache with meta data nodes
_package_versions = {}

# Populated during plugin instance creation from their tags given by
# "getEvaluationConditionControlTags" value.
control_tags = {}

_context_dict = None

# Populated when "constants" and "variables" yaml sections get evaluated.
_module_config_constants = {}
_module_config_variables = {}


def _getImportLibModule():
    try:
        import importlib
    except ImportError:
        return None
    else:
        return importlib


def _makeEvaluationContext(logger, full_name, config_name):
    context = TagContext(logger=logger, full_name=full_name, config_name=config_name)
    context.update(control_tags)

    context.update(_getEvaluationContext())

    return context


def _getEvaluationContext():
    # Using global here, as this is really a singleton, in the form of a module,
    # pylint: disable=global-statement
    global _context_dict

    if _context_dict is None:
        _context_dict = {
            "macos": isMacOS(),
            "win32": isWin32Windows(),
            "linux": isLinux(),
            "android": isAndroidBasedLinux(),
            "android32": isAndroidBasedLinux() and sys.maxsize < 2**32,
            "android64": isAndroidBasedLinux() and sys.maxsize >= 2**64 - 1,
            "anaconda": isAnacondaPython(),
            "is_conda_package": _isCondaPackage,
            "debian_python": isDebianPackagePython(),
            "nuitka_python": isNuitkaPython(),
            "standalone": isStandaloneMode(),
            "onefile": isOnefileMode(),
            "onefile_cached": not isOnefileTempDirMode(),
            "module_mode": shallMakeModule(),
            "deployment": isDeploymentMode(),
            # Version information
            "company": getCompanyName(),
            "product": getProductName(),
            "file_version": getFileVersion(),
            "product_version": getProductVersion(),
            "combined_version": getProductFileVersion(),
            # Querying package versions.
            "version": _getPackageVersion,
            "version_str": _getPackageVersionStr,
            "get_dist_name": _getDistributionNameFromPackageName,
            "plugin": _isPluginActive,
            # Iterating packages
            "iterate_modules": _iterate_module_names,
            # Locating package directories
            "get_module_directory": _getModuleDirectory,
            # Checking module presence
            "has_module": _hasModule,
            # Getting data files contents
            "get_data": _getPackageData,
            # Querying package properties
            "has_builtin_module": isBuiltinModuleName,
            # Architectures
            "arch_x86": getArchitecture() == "x86",
            "arch_amd64": getArchitecture() == "x86_64",
            "arch_arm64": getArchitecture() == "arm64",
            # Frequent used modules
            "sys": sys,
            "os": os,
            "importlib": _getImportLibModule(),
            "appdirs": getAppdirsModule(),
            "unittest": unittest,
            # Python version string
            "python_version_str": python_version_str,
            "python_version_full_str": python_version_full_str,
            # Technical requirements
            "static_libpython": getSystemStaticLibPythonPath() is not None,
            # Builtins
            "True": True,
            "False": False,
            "None": None,
            "repr": repr,
            "len": len,
            "str": str,
            "bool": bool,
            "int": int,
            "tuple": tuple,
            "list": list,
            "dict": dict,
            "set": set,
            "getattr": getattr,
            "hasattr": hasattr,
            "frozenset": frozenset,
            "__import__": __import__,
        }

        versions = getTestExecutionPythonVersions()

        for version in versions:
            big, major = version.split(".")
            numeric_version = int(big) * 256 + int(major) * 16
            is_same_or_higher_version = python_version >= numeric_version

            _context_dict["python" + big + major + "_or_higher"] = (
                is_same_or_higher_version
            )
            _context_dict["before_python" + big + major] = not is_same_or_higher_version

        _context_dict["before_python3"] = python_version < 0x300
        _context_dict["python3_or_higher"] = python_version >= 0x300

        if not isNuitkaPython():
            _context_dict["extension_std_suffix"] = getSharedLibrarySuffix(
                preferred=True
            )
            _context_dict["extension_suffix"] = getSharedLibrarySuffix(preferred=False)

    return _context_dict


def _convertVersionToTuple(version_str):
    def numberize(v):
        # For now, we ignore rc/post stuff, hoping it doesn't matter for us.
        return int("".join(d for d in v if d.isdigit()))

    return tuple(numberize(d) for d in version_str.split("."))


def _getPackageNameFromDistributionName(distribution_name):
    # spell-checker: ignore opencv, pyobjc, objc

    if distribution_name in ("opencv-python", "opencv-python-headless"):
        return "cv2"
    elif distribution_name == "pyobjc":
        return "objc"
    else:
        return distribution_name


def _getDistributionNameFromPackageName(package_name):
    package_name = ModuleName(package_name)
    distribution = getDistributionFromModuleName(package_name)

    if distribution is None:
        return package_name.asString()
    else:
        return getDistributionName(distribution)


def _isCondaPackage(package_name):
    distribution_name = _getDistributionNameFromPackageName(package_name)

    return isDistributionCondaPackage(distribution_name)


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
                    extern,
                    get_distribution,
                )
            except ImportError:
                result = None
            else:
                try:
                    result = _convertVersionToTuple(
                        get_distribution(distribution_name).version
                    )
                except DistributionNotFound:
                    result = None
                except extern.packaging.version.InvalidVersion:
                    result = None

        if result is None:
            # Fallback if nothing is available, which may happen if no package is installed,
            # but only source code is found.
            try:
                result = _convertVersionToTuple(
                    __import__(
                        _getPackageNameFromDistributionName(distribution_name)
                    ).__version__
                )
            except ImportError:
                result = None

        _package_versions[distribution_name] = result

    return _package_versions[distribution_name]


def _getPackageVersionStr(distribution_name):
    version = _getPackageVersion(distribution_name)

    if version is not None:
        version = ".".join(str(d) for d in version)

    return version


def _getModuleDirectory(module_name):
    from nuitka.importing.Importing import locateModule

    _module_name, module_filename, _module_kind, _finding = locateModule(
        module_name=ModuleName(module_name), parent_package=None, level=0
    )

    return module_filename


def _hasModule(module_name):
    from nuitka.importing.Importing import locateModule

    _module_name, _module_filename, _module_kind, finding = locateModule(
        module_name=ModuleName(module_name), parent_package=None, level=0
    )

    return finding != "not-found"


def _getPackageData(package_name, resource, default=None):

    from nuitka.utils.PackageResources import getPackageData

    try:
        return getPackageData(package_name=ModuleName(package_name), resource=resource)
    except FileNotFoundError:
        if default is not None:
            return default

        raise


def _iterate_module_names(package_name):
    package_name = ModuleName(package_name)
    package_path = _getModuleDirectory(module_name=package_name)

    result = []

    for module_info in iter_modules([package_path]):
        module_name = package_name.getChildNamed(module_info.name)
        result.append(module_name.asString())

        if module_info.ispkg:  # spell-checker: ignore ispkg
            result.extend(_iterate_module_names(package_name=module_name))

    return result


def _isPluginActive(plugin_name):
    from .Plugins import getUserActivatedPluginNames

    return plugin_name in getUserActivatedPluginNames()


# Workaround for "ast.literal_eval" not working properly for set literals
# before Python3.9, spell-checker: ignore elts
if python_version >= 0x390:
    _literal_eval = ast.literal_eval
else:

    class RewriteName(ast.NodeTransformer):
        @staticmethod
        def visit_Call(node):
            if node.func.id == "set" and node.args == node.keywords == []:
                if python_version >= 0x380:
                    return ast.Constant(
                        value=set(),
                    )
                else:
                    # TODO: For Python2 it doesn't work to parse sets literals,
                    # if we ever find we need them, we need to workaround that
                    # by maybe implementing it entirely.
                    return ast.Set(
                        # spell-checker: ignore elts
                        elts=[],
                    )

    def _literal_eval(value):
        if "set()" in value:
            value = ast.parse(value, mode="eval")
            RewriteName().visit(value)

        return ast.literal_eval(value)


class NuitkaPluginBase(getMetaClassBase("Plugin", require_slots=False)):
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
    def hasCategory(cls, category):
        return category in cls.getCategories()

    @classmethod
    def getCategories(cls):
        plugin_category = getattr(cls, "plugin_category", None)

        if plugin_category is None:
            result = ()
        else:
            result = plugin_category.split(",")

        return OrderedSet(sorted(result))

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        # Call group.add_option() here.
        pass

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

    def onModuleSourceCode(self, module_name, source_filename, source_code):
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
        # Virtual method, pylint: disable=unused-argument
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

    def onModuleEncounter(
        self, using_module_name, module_name, module_filename, module_kind
    ):
        """Help decide whether to include a module.

        Args:
            using_module_name: module that does this (can be None if user)
            module_name: full module name
            module_filename: filename
            module_kind: one of "py", "extension" (shared library)
        Returns:
            True or False
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

    def onModuleUsageLookAhead(
        self, module_name, module_filename, module_kind, get_module_source
    ):
        """React to tentative recursion of a module coming up.

        For definite usage, use onModuleRecursion where it's a fact and
        happening next. This may be a usage that is later optimized away
        and doesn't impact anything. The main usage is to setup e.g.
        hard imports as a factory, e.g. with detectable lazy loaders.

        Args:
            module_name: full module name
            module_filename: filename
            module_kind: one of "py", "extension" (shared library)
            get_module_source: callable to get module source code if any
        Returns:
            None
        """

    def onModuleRecursion(
        self,
        module_name,
        module_filename,
        module_kind,
        using_module_name,
        source_ref,
        reason,
    ):
        """React to recursion of a module coming up.

        Args:
            module_name: full module name
            module_filename: filename
            module_kind: one of "py", "extension" (shared library)
            using_module_name: name of module that does the usage (None if it is a user choice)
            source_ref: code making the import (None if it is a user choice)
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

    def onModuleCompleteSetGUI(self, module_set, plugin_binding_name):
        from .Plugins import getOtherGUIBindingNames, getQtBindingNames

        for module in module_set:
            module_name = module.getFullName()

            if module_name == plugin_binding_name:
                continue

            if module_name in getOtherGUIBindingNames():
                if plugin_binding_name in getQtBindingNames():
                    recommendation = "Use '--nofollow-import-to=%s'" % module_name

                    if module_name in getQtBindingNames():
                        problem = "conflicts with"
                    else:
                        problem = "is redundant with"
                else:
                    recommendation = "Use '--enable-plugin=no-qt'"
                    problem = "is redundant with"

                self.warning(
                    """\
Unwanted import of '%(unwanted)s' that %(problem)s '%(binding_name)s' encountered. \
%(recommendation)s or uninstall it for best compatibility with pure Python execution."""
                    % {
                        "unwanted": module_name,
                        "binding_name": plugin_binding_name,
                        "recommendation": recommendation,
                        "problem": problem,
                    }
                )

    @staticmethod
    def locateModule(module_name):
        """Provide a filename / -path for a to-be-imported module.

        Args:
            module_name: (str or ModuleName) full name of module
        Returns:
            filename for module
        """

        from nuitka.importing.Importing import locateModule

        _module_name, module_filename, _module_kind, _finding = locateModule(
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

    def makeDllEntryPoint(
        self, source_path, dest_path, module_name, package_name, reason
    ):
        """Create an entry point, as expected to be provided by getExtraDlls."""
        return makeDllEntryPoint(
            logger=self,
            source_path=source_path,
            dest_path=dest_path,
            module_name=module_name,
            package_name=package_name,
            reason=reason,
        )

    def makeExeEntryPoint(
        self, source_path, dest_path, module_name, package_name, reason
    ):
        """Create an entry point, as expected to be provided by getExtraDlls."""
        return makeExeEntryPoint(
            logger=self,
            source_path=source_path,
            dest_path=dest_path,
            module_name=module_name,
            package_name=package_name,
            reason=reason,
        )

    def reportFileCount(self, module_name, count, section=None):
        if count:
            msg = "Found %d %s DLLs from %s%s installation." % (
                count,
                "file" if count < 2 else "files",
                "" if not section else ("'%s' " % section),
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

    def getModuleSysPathAdditions(self, module_name):
        """Provide a list of directories, that should be considered in 'PYTHONPATH' when this module is used.

        Args:
            module_name: name of a package or module
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

    def isAcceptableMissingDLL(self, package_name, dll_basename):
        """Check if a missing DLL is acceptable to the plugin.

        Args:
            package_name: name of the package using the DLL
            dll_basename : basename of the DLL, i.e. no suffix
        Returns:
            None (no opinion for that file), True (yes) or False (no)
        """

        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

    def makeIncludedDataFile(self, source_path, dest_path, reason, tags=""):
        return makeIncludedDataFile(
            source_path=source_path,
            dest_path=dest_path,
            reason=reason,
            tracer=self,
            tags=tags,
        )

    def makeIncludedAppBundleResourceFile(
        self, source_path, dest_path, reason, tags=""
    ):
        tags = decodeDataFileTags(tags)
        tags.add("framework_resource")

        assert isMacOS() and shallCreateAppBundle()

        # The default dest path root is the "Contents" folder
        dest_path = os.path.join("..", "Resources", dest_path)

        return self.makeIncludedDataFile(
            source_path=source_path,
            dest_path=dest_path,
            reason=reason,
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
        raw=False,
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
            raw=raw,
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

    def decideAnnotations(self, module_name):
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

    def decideDocStrings(self, module_name):
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

    def decideAssertions(self, module_name):
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

    @classmethod
    def getPluginDataFilesDir(cls):
        """Helper function that returns path, where data files for the plugin are stored."""
        plugin_filename = sys.modules[cls.__module__].__file__
        return changeFilenameExtension(plugin_filename, "")

    def getPluginDataFileContents(self, filename):
        """Helper function that returns contents of a plugin data file."""
        return getFileContents(
            os.path.join(
                self.getPluginDataFilesDir(),
                filename,
            )
        )

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
        # Rather complicated error handling, pylint: disable=too-many-branches

        info_name = self.plugin_name + "_" + info_name
        info_name = info_name.replace("-", "_").replace(".", "_")

        if info_name in self._runtime_information_cache:
            return self._runtime_information_cache[info_name]

        keys = []
        query_codes = []

        for key, value_expression in values:
            keys.append(key)

            query_codes.append("print(repr(%s))" % value_expression)
            query_codes.append('print("-" * 27)')

        if type(setup_codes) is str:
            setup_codes = setup_codes.splitlines()

        if not setup_codes:
            setup_codes = ("pass",)

        cmd = r"""\
from __future__ import print_function
from __future__ import absolute_import
import sys

try:
%(setup_codes)s
except ImportError as e:
    sys.stderr.write("\n%%s" %% repr(e))
    sys.exit(38)
try:
%(query_codes)s
except Exception as e:
    sys.stderr.write("\n%%s" %% repr(e))
    sys.exit(39)
""" % {
            "setup_codes": "\n".join("   %s" % line for line in setup_codes),
            "query_codes": "\n".join("   %s" % line for line in query_codes),
        }

        if shallShowExecutedCommands():
            self.info("Executing query command:\n%s" % cmd, keep_format=True)

        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf8"

        try:
            feedback = check_output([sys.executable, "-c", cmd], env=env)
        except NuitkaCalledProcessError as e:
            if e.returncode == 38:
                self.warning(
                    "Import error (not installed?) during compile time command execution: %s"
                    % e.stderr.splitlines()[-1]
                )

                return None

            if Options.is_debug:
                self.info(cmd, keep_format=True)

            if e.returncode == 39:
                # TODO: Recognize the ModuleNotFoundError or ImportError exceptions
                # and output the missing module.
                self.warning(
                    "Exception during compile time command execution: %s"
                    % e.stderr.splitlines()[-1]
                )

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

        NamedtupleResultClass = makeNamedtupleClass(info_name, keys)

        try:
            self._runtime_information_cache[info_name] = NamedtupleResultClass(
                *(_literal_eval(value) for value in feedback)
            )
        except ValueError:
            self.sysexit(
                "Error, non-constant values in output retrieving %r information."
                % info_name
            )

        return self._runtime_information_cache[info_name]

    def queryRuntimeInformationSingle(self, setup_codes, value, info_name=None):
        if info_name is None:
            info_name = "temp_info_for_" + self.plugin_name.replace("-", "_")

        return self.queryRuntimeInformationMultiple(
            info_name=info_name,
            setup_codes=setup_codes,
            values=(("key", value),),
        ).key

    def onFunctionBodyParsing(self, module_name, function_name, body):
        """Provide a different function body for the function of that module.

        Should return a boolean, indicating if any actual change was done.
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return False

    def onClassBodyParsing(self, module_name, class_name, node):
        # Virtual method, pylint: disable=no-self-use,unused-argument
        """Provide a different class body for the class of that module.

        Should return a boolean, indicating if any actual change was done.
        """
        return False

    def getCacheContributionValues(self, module_name):
        """Provide values that represent the include of a plugin on the compilation.

        This must be used to invalidate cache results, e.g. when using the
        onFunctionBodyParsing function, and other things, that do not directly
        affect the source code. By default a plugin being enabled changes the
        result unless it makes it clear that is not the case.
        """
        # Virtual method, pylint: disable=unused-argument
        return self.plugin_name

    def getExtraConstantDefaultPopulation(self):
        """Provide extra global constant values to code generation."""
        # Virtual method, pylint: disable=no-self-use
        return ()

    def decideAllowOutsideDependencies(self, module_name):
        """Decide if outside of Python dependencies are allowed.

        Returns:
            None (no opinion for that module), True (yes) or False (no)
        """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

    @staticmethod
    def getPackageVersion(module_name):
        """Provide package version of a distribution."""
        distribution_name = _getDistributionNameFromPackageName(module_name)

        return _getPackageVersion(distribution_name)

    def getEvaluationConditionControlTags(self):
        # Virtual method, pylint: disable=no-self-use
        return {}

    @staticmethod
    def isValueForEvaluation(expression):
        return '"' in expression or "'" in expression or "(" in expression

    def evaluateExpressionOrConstant(
        self, full_name, expression, config_name, extra_context, single_value
    ):
        if self.isValueForEvaluation(expression):
            return self.evaluateExpression(
                config_module_name=full_name,
                module_name=full_name,
                expression=expression,
                config_name=config_name,
                extra_context=extra_context,
                single_value=single_value,
            )
        else:
            return expression

    def getExpressionConstants(self, full_name):
        if full_name not in _module_config_constants:
            constants = {}

            for count, constant_config in enumerate(
                self.config.get(full_name, section="constants"), start=1
            ):
                declarations = constant_config.get("declarations")

                if declarations and self.evaluateCondition(
                    full_name=full_name,
                    condition=constant_config.get("when", "True"),
                    allow_constants=False,
                    allow_variables=False,
                ):
                    for constant_name, constant_value in declarations.items():
                        constants[constant_name] = self.evaluateExpressionOrConstant(
                            full_name=full_name,
                            expression=constant_value,
                            config_name="constants config #%d" % count,
                            extra_context=None,
                            single_value=False,
                        )

            _module_config_constants[full_name] = constants

        return _module_config_constants[full_name]

    def getExpressionVariables(self, full_name):
        if full_name not in _module_config_variables:
            variables = {}

            for count, variable_config in enumerate(
                self.config.get(full_name, section="variables")
            ):
                environment = variable_config.get("environment", {})
                setup_codes = variable_config.get("setup_code", [])
                if type(setup_codes) is str:
                    setup_codes = setup_codes.splitlines()
                declarations = variable_config.get("declarations", {})

                if len(declarations) < 1:
                    self.sysexit(
                        "Error, no variable 'declarations' for %s makes no sense."
                        % full_name
                    )

                if self.evaluateCondition(
                    full_name=full_name,
                    condition=variable_config.get("when", "True"),
                    allow_constants=True,
                    allow_variables=False,
                ):
                    setup_codes.extend(
                        "%s=%r" % (constant_name, constant_value)
                        for (
                            constant_name,
                            constant_value,
                        ) in self.getExpressionConstants(full_name=full_name).items()
                    )

                    env_variables = {}

                    for env_name, env_value in environment.items():
                        env_variables[env_name] = self.evaluateExpressionOrConstant(
                            full_name=full_name,
                            expression=env_value,
                            config_name="variables config #%d" % count,
                            extra_context=None,
                            single_value=True,
                        )

                    with withEnvironmentVarsOverridden(env_variables):
                        info = self.queryRuntimeInformationMultiple(
                            "%s_variables_%s" % (full_name.asString(), count),
                            setup_codes=setup_codes,
                            values=tuple(declarations.items()),
                        )

                    if Options.isExperimental("display-yaml-variables"):
                        self.info("Evaluated %r" % info)

                    if info is None:
                        self.sysexit(
                            "Error, failed to evaluate variables for '%s'." % full_name
                        )

                    variables.update(info.asDict())

            _module_config_variables[full_name] = variables

        return _module_config_variables[full_name]

    def evaluateExpression(
        self,
        config_module_name,
        module_name,
        expression,
        config_name,
        extra_context,
        single_value,
    ):
        context = _makeEvaluationContext(
            logger=self, full_name=config_module_name, config_name=config_name
        )

        def get_variable(variable_name):
            assert type(variable_name) is str, variable_name

            result = self.getExpressionVariables(full_name=config_module_name)[
                variable_name
            ]

            addModuleInfluencingVariable(
                module_name=module_name,
                config_module_name=config_module_name,
                plugin_name=self.plugin_name,
                variable_name=variable_name,
                control_tags=context.used_tags,
                result=result,
            )

            return result

        def get_constant(constant_name):
            assert type(constant_name) is str, constant_name

            result = self.getExpressionConstants(full_name=config_module_name)[
                constant_name
            ]

            # TODO: Record the constant value in report.

            return result

        context["get_variable"] = get_variable
        context["get_constant"] = get_constant

        def get_parameter(parameter_name, default):
            result = Options.getModuleParameter(config_module_name, parameter_name)

            if result is None:
                result = default

            self.addModuleInfluencingParameter(
                module_name=config_module_name,
                parameter_name=parameter_name,
                condition_tags_used=context.used_tags,
                result=result,
            )

            return result

        context["get_parameter"] = get_parameter

        if extra_context:
            context.update(extra_context)

        with withNoWarning():
            # We trust the yaml files, pylint: disable=eval-used
            try:
                result = eval(expression, context)
            except Exception as e:  # Catch all the things, pylint: disable=broad-except
                if Options.is_debug:
                    raise

                self.sysexit(
                    "Error, failed to evaluate expression %r in this context, exception was '%r'."
                    % (expression, e)
                )

        if type(result) not in (str, unicode):
            if single_value:
                self._checkStrResult(
                    value=result, expression=expression, full_name=config_module_name
                )
            else:
                self._checkSequenceResult(
                    value=result, expression=expression, full_name=config_module_name
                )

                for v in result:
                    self._checkStrResult(
                        value=v, expression=expression, full_name=config_module_name
                    )

                # Make it immutable in case it's a list.
                result = tuple(result)

        return result

    def _checkStrResult(self, value, expression, full_name):
        if type(value) not in (str, unicode):
            self.sysexit(
                """\
Error, expression '%s' for module '%s' did not evaluate to 'str', 'tuple[str]' or 'list[str]' result, but '%s'"""
                % (expression, full_name, type(value))
            )

    def _checkSequenceResult(self, value, expression, full_name):
        if type(value) not in (tuple, list):
            self.sysexit(
                """\
Error, expression '%s' for module '%s' did not evaluate to 'tuple[str]' or 'list[str]' result."""
                % (expression, full_name)
            )

    def evaluateCondition(
        self, full_name, condition, allow_constants=True, allow_variables=True
    ):
        # Note: Caching makes no sense yet, this should all be very fast and
        # cache themselves. TODO: Allow plugins to contribute their own control
        # tag values during creation and during certain actions.
        if condition == "True":
            return True
        if condition == "False":
            return False

        # TODO: Maybe add module name to config name?
        context = _makeEvaluationContext(
            logger=self, full_name=full_name, config_name="'when' configuration"
        )

        def get_variable(variable_name):
            assert type(variable_name) is str, variable_name

            result = self.getExpressionVariables(full_name=full_name)[variable_name]

            addModuleInfluencingVariable(
                module_name=full_name,
                config_module_name=full_name,
                plugin_name=self.plugin_name,
                variable_name=variable_name,
                control_tags=context.used_tags,
                result=result,
            )

            return result

        def get_constant(constant_name):
            assert type(constant_name) is str, constant_name

            result = self.getExpressionConstants(full_name=full_name)[constant_name]

            # TODO: Record the constant value in report.

            return result

        if allow_constants:
            context["get_constant"] = get_constant
        if allow_variables:
            context["get_variable"] = get_variable

        def get_parameter(parameter_name, default):
            result = Options.getModuleParameter(full_name, parameter_name)

            if result is None:
                result = default

            self.addModuleInfluencingParameter(
                module_name=full_name,
                parameter_name=parameter_name,
                condition_tags_used=context.used_tags,
                result=result,
            )

            return result

        context["get_parameter"] = get_parameter

        with withNoWarning():
            # We trust the yaml files, pylint: disable=eval-used
            try:
                result = eval(condition, context)
            except Exception as e:  # Catch all the things, pylint: disable=broad-except
                if Options.is_debug:
                    raise

                self.sysexit(
                    "Error, failed to evaluate condition '%s' in this context, exception was '%s'."
                    % (condition, e)
                )

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

    def addModuleInfluencingParameter(
        self, module_name, parameter_name, condition_tags_used, result
    ):
        addModuleInfluencingParameter(
            module_name=module_name,
            plugin_name=self.plugin_name,
            parameter_name=parameter_name,
            condition_tags_used=condition_tags_used,
            result=result,
        )

    def addModuleInfluencingDetection(
        self, module_name, detection_name, detection_value
    ):
        addModuleInfluencingDetection(
            module_name=module_name,
            plugin_name=self.plugin_name,
            detection_name=detection_name,
            detection_value=detection_value,
        )

    @classmethod
    def warning(cls, message, **kwargs):
        # Doing keyword only arguments manually, to keep older Python compatibility, and avoid
        # user errors still.
        mnemonic = kwargs.pop("mnemonic", None)
        if kwargs:
            plugins_logger.sysexit("Illegal keyword arguments for self.warning")

        plugins_logger.warning(cls.plugin_name + ": " + message, mnemonic=mnemonic)

    @classmethod
    def info(cls, message, keep_format=False):
        plugins_logger.info(message, prefix=cls.plugin_name, keep_format=keep_format)

    @classmethod
    def debug(cls, message, keep_format=False):
        if Options.is_debug:
            cls.info(message, keep_format=keep_format)

    @classmethod
    def sysexit(cls, message, mnemonic=None, reporting=True):
        plugins_logger.sysexit(
            cls.plugin_name + ": " + message, mnemonic=mnemonic, reporting=reporting
        )


class TagContext(dict):
    def __init__(self, logger, full_name, config_name):
        dict.__init__(self)

        self.logger = logger
        self.full_name = full_name
        self.config_name = config_name

        self.used_tags = OrderedSet()
        self.used_variables = OrderedSet()

    def __getitem__(self, key):
        try:
            self.used_tags.add(key)

            return dict.__getitem__(self, key)
        except KeyError:
            if key.startswith("use_"):
                return False

            if key == "no_asserts":
                # TODO: This should be better decoupled.
                from .Plugins import Plugins

                return Plugins.decideAssertions(self.full_name) is False

            if key == "no_docstrings":
                from .Plugins import Plugins

                return Plugins.decideDocStrings(self.full_name) is False

            if key == "no_annotations":
                from .Plugins import Plugins

                return Plugins.decideAnnotations(self.full_name) is False

            self.logger.sysexit(
                "Identifier '%s' in %s of module '%s' is unknown."
                % (key, self.config_name, self.full_name)
            )


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
