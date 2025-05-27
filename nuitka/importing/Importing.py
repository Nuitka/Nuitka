#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Locating modules and package source on disk.

The actual import of a module would already execute code that changes things.
Imagine a module that does ``os.system()``, it would be done during
compilation. People often connect to databases, and these kind of things, at
import time.

Therefore CPython exhibits the interfaces in an ``imp`` module in standard
library, which one can use those to know ahead of time, what file import would
load. For us unfortunately there is nothing in CPython that is easily
accessible and gives us this functionality for packages and search paths
exactly like CPython does, so we implement here a multi step search process
that is compatible.

This approach is much safer of course and there is no loss. To determine if
it's from the standard library, one can abuse the attribute ``__file__`` of the
``os`` module like it's done in ``isStandardLibraryPath`` of this module.

"""

import collections
import os
import sys
import zipfile

from nuitka import SourceCodeReferences
from nuitka.__past__ import iter_modules
from nuitka.containers.Namedtuples import makeNamedtupleClass
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.Errors import NuitkaCodeDeficit
from nuitka.plugins.Plugins import Plugins
from nuitka.PythonFlavors import isNuitkaPython
from nuitka.PythonVersions import python_version
from nuitka.Tracing import recursion_logger
from nuitka.tree.ReformulationMultidist import locateMultidistModule
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.FileOperations import (
    getNormalizedPath,
    listDir,
    removeDirectory,
)
from nuitka.utils.Hashing import getFileContentsHash
from nuitka.utils.Importing import (
    builtin_module_names,
    getExtensionModuleSuffixes,
    getModuleFilenameSuffixes,
    getPackageDirFilename,
    isBuiltinModuleName,
)
from nuitka.utils.ModuleNames import ModuleName
from nuitka.utils.SharedLibraries import (
    hasUniversalOrMatchingMacOSArchitecture,
)
from nuitka.utils.Utils import (
    getLaunchingNuitkaProcessEnvironmentValue,
    isMacOS,
    isWin32OrPosixWindows,
)

from .IgnoreListing import isIgnoreListedNotExistingModule
from .PreloadedPackages import getPreloadedPackagePath, isPreloadedPackagePath
from .StandardLibrary import isStandardLibraryPath

# Debug traces, enabled via --explain-imports
_debug_module_finding = None

# Preference as expressed via --prefer-source-code
_prefer_source_code_over_extension_modules = None

# Do not add current directory to search path.
_safe_path = None


def setupImportingFromOptions():
    """Set up the importing layer from giving options."""

    # Should only be used inside of here.
    from nuitka import Options

    # singleton, pylint: disable=global-statement
    global _debug_module_finding
    _debug_module_finding = Options.shallExplainImports()

    global _prefer_source_code_over_extension_modules
    _prefer_source_code_over_extension_modules = (
        Options.shallPreferSourceCodeOverExtensionModules()
    )

    global _safe_path
    _safe_path = Options.hasPythonFlagNoCurrentDirectoryInPath()

    # Lets try and have this complete, please report failures.
    if Options.is_debug and not isNuitkaPython():
        _checkRaisingBuiltinComplete()

    main_filenames = Options.getMainEntryPointFilenames()
    for filename in main_filenames:
        # Inform the importing layer about the main script directory, so it can use
        # it when attempting to follow imports.
        addMainScriptDirectory(main_dir=os.path.dirname(os.path.abspath(filename)))


def _checkRaisingBuiltinComplete():
    for module_name in builtin_module_names:
        assert module_name in _stdlib_module_raises, module_name


warned_about = set()

# Directory where the main script lives. Should attempt to import from there.
_main_paths = OrderedSet()

# Additions to sys.paths from plugins.
_extra_paths = OrderedSet()

ModuleUsageAttempt = makeNamedtupleClass(
    "ModuleUsageAttempt",
    (
        "module_name",
        "filename",
        "module_kind",
        "finding",
        "level",
        "source_ref",
        "reason",
    ),
)


def makeModuleUsageAttempt(
    module_name, filename, module_kind, finding, level, source_ref, reason
):
    assert source_ref is not None

    return ModuleUsageAttempt(
        module_name=module_name,
        filename=filename,
        module_kind=module_kind,
        finding=finding,
        level=level,
        source_ref=source_ref,
        reason=reason,
    )


def makeParentModuleUsagesAttempts(module_usage_attempt):
    result = []

    for parent_package_name in module_usage_attempt.module_name.getParentPackageNames():
        (
            _parent_package_name,
            parent_module_filename,
            parent_module_kind,
            parent_module_finding,
        ) = locateModule(
            module_name=parent_package_name,
            parent_package=None,
            level=0,
        )

        result.append(
            makeModuleUsageAttempt(
                module_name=parent_package_name,
                filename=parent_module_filename,
                finding=parent_module_finding,
                module_kind=parent_module_kind,
                level=0,
                source_ref=module_usage_attempt.source_ref,
                reason="import path parent",
            )
        )

    result.append(module_usage_attempt)

    return tuple(result)


def addMainScriptDirectory(main_dir):
    """Initialize the main script directory.

    We use this as part of the search path for modules.
    """
    _main_paths.add(main_dir)


def addExtraSysPaths(directories):
    for directory in directories:
        assert os.path.isdir(directory), directory

        _extra_paths.add(directory)


def hasMainScriptDirectory():
    return bool(_main_paths)


def isPackageDir(dirname):
    """Decide if a directory is a package.

    Before Python3 it's required to have a "__init__.py" file, but then
    it became impossible to decide, and for extra fun, there is also the
    extra packages provided via "*.pth" file tricks by "site.py" loading.
    """

    return (
        "." not in os.path.basename(dirname)
        and os.path.isdir(dirname)
        and (
            python_version >= 0x300
            or isPreloadedPackagePath(dirname)
            or getPackageDirFilename(dirname) is not None
        )
    )


_package_module_name_cache = {}


def isPackageModuleName(module_name):
    """Decide if the give n module name is a package or not.

    module, Cached as it involves disk access."""

    if module_name not in _package_module_name_cache:
        _module_name, module_filename, _module_kind, _finding = locateModule(
            module_name=module_name,
            parent_package=None,
            level=0,
        )

        (
            _main_added,
            is_package,
            _is_namespace,
            _source_ref,
            _source_filename,
        ) = decideModuleSourceRef(
            filename=module_filename,
            module_name=module_name,
            is_main=False,
            is_fake=False,
            logger=None,
        )

        _package_module_name_cache[module_name] = is_package

    return _package_module_name_cache[module_name]


def getModuleNameAndKindFromFilename(module_filename):
    """Given a filename, decide the module name and kind.

    Args:
        module_name - file path of the module
    Returns:
        Tuple with the name of the module basename, and the kind of the
        module derived from the file suffix. Can be None, None if is is not a
        known file suffix.
    Notes:
        This doesn't concern itself with packages, that needs to be tracked
        by the using code. It cannot be decided from the filename at all.
    """

    if module_filename.endswith(".py"):
        return ModuleName(os.path.basename(module_filename)[:-3]), "py"

    if module_filename.endswith(".pyc"):
        return ModuleName(os.path.basename(module_filename)[:-4]), "pyc"

    # TODO: This sorting is necessary for at least Python2, but probably
    # elsewhere too, need to be sure we follow the scan order of core Python
    # here.
    for suffix in sorted(getExtensionModuleSuffixes(), key=lambda suffix: -len(suffix)):
        if module_filename.endswith(suffix):
            return (
                ModuleName(os.path.basename(module_filename)[: -len(suffix)]),
                "extension",
            )

    if os.path.isdir(module_filename):
        package_filename = getPackageDirFilename(module_filename)

        if package_filename is not None:
            for suffix in getExtensionModuleSuffixes():
                if package_filename.endswith(suffix):
                    return (
                        ModuleName(os.path.basename(module_filename)),
                        "extension",
                    )

        return ModuleName(os.path.basename(module_filename)), "py"

    return None, None


def isIgnoreListedImportMaker(source_ref):
    if isNuitkaPython():
        return True

    return isStandardLibraryPath(source_ref.getFilename())


def warnAboutNotFoundImport(importing, module_name, level, source_ref):
    # This probably should not be dealt with here
    if module_name == "":
        return

    if not isIgnoreListedNotExistingModule(
        module_name
    ) and not isIgnoreListedImportMaker(source_ref):
        key = module_name, level

        if key not in warned_about:
            warned_about.add(key)

            if Plugins.suppressUnknownImportWarning(
                importing=importing, source_ref=source_ref, module_name=module_name
            ):
                return

            if level == 0:
                level_desc = "as absolute import"
            elif level == -1:
                level_desc = "as relative or absolute import"
            elif level == 1:
                level_desc = "%d package level up" % level
            else:
                level_desc = "%d package levels up" % level

            if _debug_module_finding:
                if importing.getFullName().getPackageName() is not None:
                    recursion_logger.warning(
                        "%s: Cannot find '%s' in package '%s' %s."
                        % (
                            importing.getSourceReference().getAsString(),
                            module_name,
                            importing.getFullName().getPackageName().asString(),
                            level_desc,
                        )
                    )
                else:
                    recursion_logger.warning(
                        "%s: Cannot find '%s' %s."
                        % (
                            importing.getSourceReference().getAsString(),
                            module_name,
                            level_desc,
                        )
                    )


def normalizePackageName(module_name):
    # The "os.path" is strangely hacked into the "os" module, dispatching per
    # platform, we either cannot look into it, or we require that we resolve it
    # here correctly.
    if module_name == "os.path":
        module_name = ModuleName(os.path.basename(os.path.__name__))

    return module_name


def findModule(module_name, parent_package, level, logger):
    """Find a module with given package name as parent.

    The package name can be None of course. Level is the same
    as with "__import__" built-in. Warnings are optional.

    Returns:
        Returns a triple of package name the module is in, filename of
        it, which can be a directory for packages, and the location
        method used.
    """
    # We have many branches here, because there are a lot of cases to try.
    # pylint: disable=too-many-branches,too-many-return-statements

    assert type(module_name) is ModuleName, module_name

    if logger is not None:
        logger.info(
            "findModule: Enter to search %r in package %r level %s."
            % (module_name, parent_package, level)
        )

    # Do not allow star imports to get here. We just won't find modules with
    # that name, but it would be wasteful.
    assert module_name != "*"

    if level > 1:
        # TODO: Should give a warning and return not found if the levels
        # exceed the package name.
        if parent_package is not None:
            parent_package = parent_package.getRelativePackageName(level - 1)
        else:
            return None, None, None, "not-found"

    if level == 1 and not module_name:
        # Not actually allowed, but we only catch that at run-time.
        if parent_package is None:
            return None, None, None, "not-found"

        module_name = parent_package
        parent_package = None
        level = 0

    # Try relative imports first if we have a parent package.
    if level != 0 and parent_package is not None:
        if module_name:
            full_name = ModuleName(parent_package + "." + module_name)
        else:
            full_name = ModuleName(parent_package)

        full_name = normalizePackageName(full_name)

        preloaded_path = getPreloadedPackagePath(module_name)

        if preloaded_path is not None:
            for module_filename in preloaded_path:
                if os.path.exists(module_filename):
                    break
            else:
                module_filename = None

            return full_name.getPackageName(), module_filename, "py", "pth"

        try:
            module_filename, module_kind = _findModule(
                module_name=full_name,
                logger=logger,
            )
        except ImportError:
            # For relative import, that is OK, we will still try absolute.
            pass
        else:
            if logger is not None:
                logger.info(
                    "findModule: Relative imported module '%s' as '%s' in filename '%s':"
                    % (module_name, full_name, module_filename)
                )

            return full_name.getPackageName(), module_filename, module_kind, "relative"

    if level < 1 and module_name:
        module_name = normalizePackageName(module_name)

        package_name = module_name.getPackageName()

        preloaded_path = getPreloadedPackagePath(module_name)

        if preloaded_path is not None:
            for module_filename in preloaded_path:
                if os.path.exists(module_filename):
                    break
            else:
                module_filename = None

            return package_name, module_filename, "py", "pth"

        try:
            module_filename, module_kind = _findModule(
                module_name=module_name,
                logger=logger,
            )
        except ImportError:
            # For relative import, that is OK, we will still try absolute.
            pass
        else:
            if logger is not None:
                logger.info(
                    "findModule: Found absolute imported module '%s' in filename '%s':"
                    % (module_name, module_filename)
                )

            return package_name, module_filename, module_kind, "absolute"

    return None, None, None, "not-found"


# Some platforms are case insensitive.
case_sensitive = not isMacOS() and not isWin32OrPosixWindows()

ImportScanFinding = collections.namedtuple(
    "ImportScanFinding",
    ("found_in", "module_type", "priority", "full_path", "search_order"),
)

# We put here things that are not worth it (Cython is not really used by
# anything really, or where it's know to not have a big # impact, e.g. lxml.

# TODO: Do we really want this warning to persist?
unworthy_namespaces = ("Cython", "lxml", "black", "tomli")


def _reportCandidates(package_name, module_name, candidate, candidates):
    module_name = (
        package_name.getChildNamed(module_name)
        if package_name is not None
        else module_name
    )

    if candidate.priority == 1 and _prefer_source_code_over_extension_modules is None:
        for c in candidates:
            # Don't compare to itself and don't consider unused bytecode a problem.
            if c is candidate or c.priority == 3:
                continue

            if c.search_order == candidate.search_order:
                if not module_name.hasOneOfNamespaces(unworthy_namespaces):
                    recursion_logger.info(
                        """\
Should decide '--prefer-source-code' vs. '--no-prefer-source-code', using \
existing '%s' extension module by default. Candidates were: %s <-> %s."""
                        % (module_name, candidate, c)
                    )


_list_dir_cache = {}


def listDirCached(path):
    """Cached listing of a directory."""

    if path not in _list_dir_cache:
        _list_dir_cache[path] = tuple(listDir(path))

    return _list_dir_cache[path]


def flushImportCache():
    """Clear import related caches.

    In some situations, e.g. during package rebuild, we scan and then decide to remove
    files and scan again. This allows that. Nothing in standard Nuitka should do it,
    as it throws away so much.
    """
    _list_dir_cache.clear()
    module_search_cache.clear()


def _findModuleInPath2(package_name, module_name, search_path, logger):
    """This is out own module finding low level implementation.

    Just the full module name and search path are given. This is then
    tasked to raise "ImportError" or return a path if it finds it, or
    None, if it is a built-in.
    """
    # We have many branches here, because there are a lot of cases to try.
    # pylint: disable=too-many-branches,too-many-locals

    # We may have to decide between package and module, therefore build
    # a list of candidates.
    candidates = OrderedSet()

    considered = set()

    # Higher values are lower priority.
    priority_map = {
        "PY_COMPILED": 3,
        "PY_SOURCE": 0 if _prefer_source_code_over_extension_modules else 2,
        "C_EXTENSION": 1,
    }

    for count, entry in enumerate(search_path):
        # Don't try again, just with an entry of different casing or complete
        # duplicate.
        if os.path.normcase(entry) in considered:
            continue
        considered.add(os.path.normcase(entry))

        package_directory = os.path.join(entry, module_name.asPath())

        # First, check for a package with an init file, that would be the
        # first choice.
        if os.path.isdir(package_directory):
            found = False

            for suffix, module_type in getModuleFilenameSuffixes():
                package_file_name = "__init__" + suffix

                file_path = os.path.join(package_directory, package_file_name)

                if os.path.isfile(file_path):
                    candidates.add(
                        ImportScanFinding(
                            found_in=entry,
                            module_type=module_type,
                            priority=priority_map[module_type],
                            full_path=package_directory,
                            search_order=count,
                        )
                    )
                    found = True

            if not found and python_version >= 0x300:
                candidates.add(
                    ImportScanFinding(
                        found_in=entry,
                        module_type=10,
                        priority=10,
                        full_path=package_directory,
                        search_order=count + len(search_path),
                    )
                )

        # Then, check out suffixes of all kinds, but only for one directory.
        last_module_type = 0
        for suffix, module_type in getModuleFilenameSuffixes():
            # Use first match per kind only.
            if module_type == last_module_type:
                continue

            full_path = os.path.join(entry, module_name + suffix)

            if os.path.isfile(full_path):
                candidates.add(
                    ImportScanFinding(
                        found_in=entry,
                        module_type=module_type,
                        priority=4 + priority_map[module_type],
                        full_path=full_path,
                        search_order=count,
                    )
                )
                last_module_type = module_type

    if logger is not None:
        logger.info("Candidates: %r" % candidates)

    found_candidate = None

    if candidates:
        # Sort by priority, with entries from same path element coming first, then desired type.
        candidates = tuple(
            sorted(candidates, key=lambda c: (c.search_order, c.priority))
        )

        # On case sensitive systems, no resolution needed.
        if case_sensitive:
            found_candidate = candidates[0]
        else:
            for candidate in candidates:
                for fullname, _filename in listDirCached(candidate.found_in):
                    if fullname == candidate.full_path:
                        found_candidate = candidate
                        break

                if found_candidate:
                    break

            # Only exact case matches matter, all candidates were ignored,
            # lets just fall through to raising the import error.

    if found_candidate is None:
        # Nothing found.
        raise ImportError
    if (
        found_candidate.module_type == "C_EXTENSION"
        and isMacOS()
        and not hasUniversalOrMatchingMacOSArchitecture(
            getPackageDirFilename(found_candidate.full_path)
            if os.path.isdir(found_candidate.full_path)
            else found_candidate.full_path
        )
    ):
        # Not usable for target architecture.
        raise ImportError

    _reportCandidates(
        package_name=package_name,
        module_name=module_name,
        candidate=found_candidate,
        candidates=candidates,
    )

    return (
        found_candidate.full_path,
        "extension" if found_candidate.module_type == "C_EXTENSION" else "py",
    )


_egg_files = {}


def _unpackPathElement(path_entry):
    if not path_entry:
        return "."  # empty means current directory

    if os.path.isfile(path_entry):
        if path_entry.lower().endswith((".egg", ".zip")):
            if path_entry not in _egg_files:
                checksum = getFileContentsHash(path_entry)

                target_dir = os.path.join(getCacheDir("egg-content"), checksum)

                if not os.path.exists(target_dir):
                    try:
                        # Not all Python versions allow using with here, pylint: disable=consider-using-with
                        zip_ref = zipfile.ZipFile(path_entry, "r")
                        zip_ref.extractall(target_dir)
                        zip_ref.close()
                    except BaseException:
                        removeDirectory(
                            target_dir,
                            logger=recursion_logger,
                            ignore_errors=True,
                            extra_recommendation=None,
                        )
                        raise

                _egg_files[path_entry] = target_dir

            return _egg_files[path_entry]

    return path_entry


def getPythonUnpackedSearchPath():
    """Python search path with with eggs unpacked."""

    # TODO: Maybe cache this for a given "sys.path" as we do IO checks each time.
    return [_unpackPathElement(path_element) for path_element in sys.path]


def getPackageSearchPath(package_name):
    if not _main_paths:
        return None

    if package_name is None:
        result = []

        if not _safe_path:
            result.append(os.getcwd())

        result += list(_main_paths) + getPythonUnpackedSearchPath() + list(_extra_paths)
    elif "." in package_name:
        parent_package_name, child_package_name = package_name.splitModuleBasename()

        result = []
        for element in getPackageSearchPath(parent_package_name):
            package_dir = os.path.join(element, child_package_name.asPath())

            if isPackageDir(package_dir):
                result.append(package_dir)
                # Hack for "uniconvertor". TODO: Move this to plug-in decision. This
                # fails the above test, but at run time should be a package.
                # spell-checker: ignore uniconvertor
            elif package_name == "uniconvertor.app.modules":
                result.append(package_dir)

        return result

    else:
        preloaded_path = getPreloadedPackagePath(package_name)

        if preloaded_path is not None:
            return preloaded_path

        def getPackageDirCandidates(element):
            yield os.path.join(element, package_name.asPath()), False

            for extra_path in Plugins.getPackageExtraScanPaths(package_name, element):
                yield extra_path, True

        result = []
        for element in getPackageSearchPath(None):
            for package_dir, force_package in getPackageDirCandidates(element):
                if isPackageDir(package_dir) or force_package:
                    result.append(package_dir)

    return OrderedSet(
        element for element in OrderedSet(result) if os.path.exists(element)
    )


def _findModuleInPath(module_name, logger):
    package_name, module_name = module_name.splitModuleBasename()

    if logger is not None:
        logger.info(
            "_findModuleInPath: Enter for %s in %s" % (module_name, package_name)
        )

    # The "site" module must be located based on PYTHONPATH before it was
    # executed, while we normally search in PYTHONPATH after it was executed,
    # and on some systems, that fails.
    if package_name is None and module_name == "site":
        candidate = getLaunchingNuitkaProcessEnvironmentValue("NUITKA_SITE_FILENAME")

        if candidate:
            return candidate, "py"

    # Free pass for built-in modules, they need not exist.
    if package_name is None and isBuiltinModuleName(module_name):
        return None, "built-in"

    search_path = getPackageSearchPath(package_name)

    if logger is not None:
        logger.info(
            "_findModuleInPath: Using search path %s for %s"
            % (search_path, package_name)
        )

    try:
        module_filename, module_kind = _findModuleInPath2(
            package_name=package_name,
            module_name=module_name,
            search_path=search_path,
            logger=logger,
        )
    except SyntaxError:
        # Warn user, as this is kind of unusual.
        recursion_logger.warning(
            "%s: Module cannot be imported due to syntax errors.",
            module_name if package_name is None else package_name + "." + module_name,
        )

        return None, None

    if logger is not None:
        logger.info(
            "_findModuleInPath: _findModuleInPath2 gave %s %s"
            % (module_filename, module_kind)
        )

    return module_filename, module_kind


module_search_cache = {}


def _findModule(module_name, logger):
    # Not a good module name. TODO: Push this to ModuleName() creation maybe.
    assert module_name != ""

    if logger is not None:
        logger.info("_findModule: Enter to search '%s'." % module_name)

    assert module_name.getBasename(), module_name

    key = module_name

    if key in module_search_cache:
        result = module_search_cache[key]

        if logger is not None:
            logger.info("_findModule: Cached result (see previous call).")

        if result is ImportError:
            raise ImportError

        return result

    try:
        module_search_cache[key] = _findModuleInPath(
            module_name=module_name,
            logger=logger,
        )
    except ImportError:
        module_search_cache[key] = ImportError
        raise

    # assert len(module_search_cache[key]) == 2, (module_name, module_search_cache[key])

    return module_search_cache[key]


def locateModule(module_name, parent_package, level, logger=None):
    """Locate a module with given package name as parent.

    The package name can be None of course. Level is the same
    as with "__import__" built-in.

    Returns:
        Returns a tuple of module name the module has considering
        package containing it, and filename of it which can be a
        directory for packages, the module kind, and the finding
        kind.
    """

    if not _main_paths:
        raise NuitkaCodeDeficit(
            "Error, cannot locate modules before import mechanism is setup."
        )

    if module_name.isMultidistModuleName():
        return locateMultidistModule(module_name)

    if _debug_module_finding and logger is None:
        logger = recursion_logger

    module_package, module_filename, module_kind, finding = findModule(
        module_name=module_name,
        parent_package=parent_package,
        level=level,
        logger=logger,
    )

    # Allowing ourselves to be lazy.
    assert module_kind is not None or module_filename is None, module_name

    assert module_package is None or (
        type(module_package) is ModuleName and module_package != ""
    ), ("Must not attempt to locate %r" % module_name)

    if module_filename is not None:
        module_filename = getNormalizedPath(module_filename)

        module_name, module_kind = getModuleNameAndKindFromFilename(module_filename)
        module_name = ModuleName.makeModuleNameInPackage(module_name, module_package)
    elif finding == "not-found":
        if parent_package is not None:
            if not module_name:
                module_name = parent_package
            elif level != 0:
                module_name = ModuleName.makeModuleNameInPackage(
                    package_name=parent_package, module_name=module_name
                )
        elif level > 0:
            module_name = ModuleName("")

    return module_name, module_filename, module_kind, finding


def locateModules(package_name):
    """Determine child module names.

    Return:
        generator of ModuleName objects
    """
    package_name = ModuleName(package_name)

    module_filename = locateModule(
        module_name=ModuleName(package_name), parent_package=None, level=0
    )[1]

    if module_filename is not None:
        for sub_module in iter_modules([module_filename]):
            yield package_name.getChildNamed(sub_module.name)


def decideModuleSourceRef(filename, module_name, is_main, is_fake, logger):
    # Many branches due to the many cases

    assert type(module_name) is ModuleName, module_name
    assert filename is not None

    is_namespace = False
    is_package = False

    if is_main and os.path.isdir(filename):
        source_filename = getNormalizedPath(os.path.join(filename, "__main__.py"))

        if not os.path.isfile(source_filename):
            sys.stderr.write(
                "%s: can't find '__main__' module in '%s'\n"
                % (os.path.basename(sys.argv[0]), filename)
            )
            sys.exit(2)

        filename = source_filename

        main_added = True
    else:
        main_added = False

    if is_fake:
        source_filename = filename

        source_ref = SourceCodeReferences.fromFilename(filename=filename)

        module_name = is_fake

    elif os.path.isfile(filename):
        source_filename = filename

        source_ref = SourceCodeReferences.fromFilename(filename=filename)

    elif isPackageDir(filename):
        is_package = True

        source_filename = getNormalizedPath(os.path.join(filename, "__init__.py"))

        if not os.path.isfile(source_filename):
            source_ref = SourceCodeReferences.fromFilename(
                filename=filename
            ).atInternal()
            is_namespace = True
        else:
            source_ref = SourceCodeReferences.fromFilename(
                filename=getNormalizedPath(os.path.abspath(source_filename))
            )

    else:
        logger.sysexit(
            "%s: can't open file '%s'." % (os.path.basename(sys.argv[0]), filename),
            exit_code=2,
        )

    return (
        main_added,
        is_package,
        is_namespace,
        source_ref,
        source_filename,
    )


# spell-checker: ignore _posixsubprocess,pyexpat,xxsubtype,_bytesio,_interpchannels
# spell-checker: ignore _interpqueues,_lsprof,_multibytecodec,_posixshmem _winapi
# spell-checker: ignore  _testbuffer _testexternalinspection _testimportmultiple
# spell-checker: ignore _testinternalcapi _testmultiphase _testsinglephase
# spell-checker: ignore _xxtestfuzz _xxsubinterpreters imageop _xxinterpchannels
_stdlib_module_raises = {
    "_abc": False,
    "__builtin__": False,
    "_ast": False,
    "_asyncio": False,
    "_bisect": False,
    "_blake2": False,
    "_bytesio": False,
    "_bz2": False,
    "_codecs_cn": False,
    "_codecs_hk": False,
    "_codecs_iso2022": False,
    "_codecs_jp": False,
    "_codecs_kr": False,
    "_codecs_tw": False,
    "_codecs": False,
    "_collections": False,
    "_contextvars": False,
    "_crypt": False,
    "_csv": False,
    "_ctypes": False,
    "_ctypes_test": False,
    "_curses": False,
    "_curses_panel": False,
    "_datetime": False,
    "_dbm": False,
    "_decimal": False,
    "_elementtree": False,
    "_fileio": False,
    "_functools": False,
    "_hashlib": False,
    "_heapq": False,
    "_hotshot": False,
    "_imp": False,
    "_interpchannels": False,
    "_interpqueues": False,
    "_interpreters": False,
    "_io": False,
    "_json": False,
    "_locale": False,
    "_lsprof": False,
    "_lzma": False,
    "_md5": False,
    "_multiprocessing": False,
    "_multibytecodec": False,
    "_opcode": False,
    "_operator": False,
    "_peg_parser": False,
    "_pickle": False,
    "_posixshmem": False,
    "_posixsubprocess": False,
    "_queue": False,
    "_random": False,
    "_sha": False,  # TODO: Not entirely clear if that's true
    "_sha1": False,
    "_sha2": False,
    "_sha256": False,
    "_sha3": False,
    "_sha512": False,
    "_signal": False,
    "_socket": False,
    "_sqlite3": False,
    "_sre": False,
    "_stat": False,
    "_statistics": False,
    "_ssl": True,
    "_string": False,
    "_struct": False,
    "_subprocess": False,
    "_suggestions": False,
    "_symtable": False,
    "_sysconfig": False,
    "_testbuffer": False,
    "_testexternalinspection": False,
    "_testimportmultiple": False,
    "_testinternalcapi": False,
    "_testmultiphase": False,
    "_testsinglephase": False,
    "_thread": False,
    "_tkinter": True,
    "_tokenize": False,
    "_tracemalloc": False,
    "_typing": False,
    "_uuid": False,
    "_warnings": False,
    "_weakref": False,
    "_winapi": False,
    "_winreg": False,
    "_xxtestfuzz": False,
    "_xxsubinterpreters": False,
    "_xxinterpchannels": False,
    "_zoneinfo": False,
    "array": False,
    "atexit": False,
    "audioop": False,
    "binascii": False,
    "builtins": False,
    "cPickle": False,
    "cStringIO": False,
    "cmath": False,
    "datetime": False,
    "errno": False,
    "exceptions": False,
    "faulthandler": False,
    "fcntl": False,
    "future_builtins": False,
    "gc": False,
    "grp": False,
    "imageop": False,
    "imp": False,
    "itertools": False,
    "marshal": False,
    "math": False,
    "mmap": False,
    "msvcrt": False,
    "nis": False,
    "nt": False,
    "operator": False,
    "ossaudiodev": False,
    "parser": False,
    "posix": False,
    "pwd": False,
    "pyexpat": False,
    "readline": True,
    "resource": False,
    "select": False,
    "signal": False,
    "spwd": False,
    "strop": False,
    "sys": False,
    "syslog": False,
    "termios": False,
    "thread": False,
    "time": False,
    "unicodedata": False,
    "winreg": False,
    "xxsubtype": False,
    "zipimport": False,
    "zlib": False,
}


def isNonRaisingBuiltinModule(module_name):
    assert isBuiltinModuleName(module_name), module_name

    # Return None, if we don't know.
    return _stdlib_module_raises.get(module_name)


def _getChildPackageNames(module_name):
    module_name = ModuleName(module_name)

    _module_name, module_filename, _module_kind, _finding = locateModule(
        parent_package=None, module_name=module_name, level=0
    )

    package_dir = module_filename

    for module_info in iter_modules([package_dir]):
        child_name = module_name.getChildNamed(module_info.name)
        yield child_name

        if module_info.ispkg:  # spell-checker: ignore ispkg
            for sub_module_name in getChildPackageNames(child_name):
                yield sub_module_name


def getChildPackageNames(module_name):
    return tuple(_getChildPackageNames(module_name))


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
