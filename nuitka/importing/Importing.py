#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Locating modules and package source on disk.

The actual import of a module would already execute code that changes
things. Imagine a module that does ``os.system()``, it would be done during
compilation. People often connect to databases, and these kind of things,
at import time.

Therefore CPython exhibits the interfaces in an ``imp`` module in standard
library, which one can use those to know ahead of time, what file import would
load. For us unfortunately there is nothing in CPython that is easily
accessible and gives us this functionality for packages and search paths
exactly like CPython does, so we implement here a multi step search process
that is compatible.

This approach is much safer of course and there is no loss. To determine if
it's from the standard library, one can abuse the attribute ``__file__`` of
the ``os`` module like it's done in ``isStandardLibraryPath`` of this module.

"""

from __future__ import print_function

import hashlib
import imp
import os
import sys
import zipfile
from logging import warning

from nuitka import Options
from nuitka.containers.oset import OrderedSet
from nuitka.importing import StandardLibrary
from nuitka.plugins.Plugins import Plugins
from nuitka.PythonVersions import python_version
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.FileOperations import listDir

from .PreloadedPackages import getPreloadedPackagePath, isPreloadedPackagePath
from .Whitelisting import isWhiteListedNotExistingModule

_debug_module_finding = Options.shallExplainImports()

warned_about = set()

# Directory where the main script lives. Should attempt to import from there.
main_path = None


def setMainScriptDirectory(main_dir):
    """ Initialize the main script directory.

        We use this as part of the search path for modules.
    """
    # We need to set this from the outside, pylint: disable=global-statement

    global main_path
    main_path = main_dir


def isPackageDir(dirname):
    """ Decide if a directory is a package.

        Before Python3.3 it's required to have a "__init__.py" file, but then
        it became impossible to decide, and for extra fun, there is also the
        extra packages provided via "*.pth" file tricks by "site.py" loading.
    """

    return (
        "." not in os.path.basename(dirname)
        and os.path.isdir(dirname)
        and (
            python_version >= 300
            or os.path.isfile(os.path.join(dirname, "__init__.py"))
            or isPreloadedPackagePath(dirname)
        )
    )


def getPackageNameFromFullName(full_name):
    if "." in full_name:
        return full_name[: full_name.rfind(".")]
    else:
        return None


def getModuleFullNameFromPackageAndName(package, name):
    if not package:
        return name
    else:
        return package + "." + name


def getExtensionModuleSuffixes():
    for suffix, _mode, kind in imp.get_suffixes():
        if kind == imp.C_EXTENSION:
            yield suffix


def getModuleNameAndKindFromFilename(module_filename):
    """ Given a filename, decide the module name and kind.

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

    # TODO: This does not handle ".pyw" files it seems.
    if os.path.isdir(module_filename):
        module_name = os.path.basename(module_filename)
        module_kind = "py"
    elif module_filename.endswith(".py"):
        module_name = os.path.basename(module_filename)[:-3]
        module_kind = "py"
    else:
        for suffix, _mode, kind in imp.get_suffixes():
            if kind != imp.C_EXTENSION:
                continue

            if module_filename.endswith(suffix):
                module_name = os.path.basename(module_filename)[: -len(suffix)]
                module_kind = "shlib"

                break
        else:
            module_kind = None
            module_name = None

    return module_name, module_kind


def isWhiteListedImport(node):
    module = node.getParentModule()

    return StandardLibrary.isStandardLibraryPath(module.getFilename())


def warnAbout(importing, module_name, parent_package, level, tried_names):
    # This probably should not be dealt with here, pylint: disable=too-many-branches
    if module_name == "":
        return

    if not isWhiteListedImport(importing) and not isWhiteListedNotExistingModule(
        module_name
    ):
        key = module_name, parent_package, level

        if key not in warned_about:
            warned_about.add(key)

            if parent_package is None:
                full_name = module_name
            else:
                full_name = module_name

            if Plugins.suppressUnknownImportWarning(importing, full_name):
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
                if parent_package is not None:
                    warning(
                        "%s: Cannot find '%s' in package '%s' %s (tried %s).",
                        importing.getSourceReference().getAsString(),
                        module_name,
                        parent_package,
                        level_desc,
                        ",".join(tried_names),
                    )
                else:
                    warning(
                        "%s: Cannot find '%s' %s.",
                        importing.getSourceReference().getAsString(),
                        module_name,
                        level_desc,
                    )


def normalizePackageName(module_name):
    # The "os.path" is strangely hacked into the "os" module, dispatching per
    # platform, we either cannot look into it, or we require that we resolve it
    # here correctly.
    if module_name == "os.path":
        module_name = os.path.basename(os.path.__name__)

    return module_name


def findModule(importing, module_name, parent_package, level, warn):
    """ Find a module with given package name as parent.

        The package name can be None of course. Level is the same
        as with "__import__" built-in. Warnings are optional.

        Returns a triple of package name the module is in, filename of
        it, which can be a directory for packages, and the location
        method.
    """

    # We have many branches here, because there are a lot of cases to try.
    # pylint: disable=too-many-branches
    if _debug_module_finding:
        print(
            "findModule: Enter to search %r in package %r level %s."
            % (module_name, parent_package, level)
        )

    # Do not allow star imports to get here. We just won't find modules with
    # that name, but it would be wasteful.
    assert module_name != "*"

    tried_names = []

    if level > 1:
        # TODO: Should give a warning and return not found if the levels
        # exceed the package name.
        if parent_package is not None:
            parent_package = ".".join(parent_package.split(".")[: -level + 1])

            if parent_package == "":
                parent_package = None
        else:
            return None, None, "not-found"

    # Try relative imports first if we have a parent package.
    if level != 0 and parent_package is not None:
        full_name = normalizePackageName(parent_package + "." + module_name)

        if full_name.endswith("."):
            full_name = full_name[:-1]

        tried_names.append(full_name)

        try:
            module_filename = _findModule(module_name=full_name)
        except ImportError:
            # For relative import, that is OK, we will still try absolute.
            pass
        else:
            if _debug_module_finding:
                print(
                    "findModule: Relative imported module '%s' as '%s' in filename '%s':"
                    % (module_name, full_name, module_filename)
                )

            return getPackageNameFromFullName(full_name), module_filename, "relative"

    if level <= 1 and module_name != "":
        module_name = normalizePackageName(module_name)
        tried_names.append(module_name)

        package_name = getPackageNameFromFullName(module_name)

        # Built-in module names must not be searched any further.
        if module_name in sys.builtin_module_names:
            if _debug_module_finding:
                print(
                    "findModule: Absolute imported module '%s' in as built-in':"
                    % (module_name,)
                )
            return package_name, None, "built-in"

        try:
            module_filename = _findModule(module_name=module_name)
        except ImportError:
            # For relative import, that is OK, we will still try absolute.
            pass
        else:
            if _debug_module_finding:
                print(
                    "findModule: Found absolute imported module '%s' in filename '%s':"
                    % (module_name, module_filename)
                )

            return package_name, module_filename, "absolute"

    if warn:
        warnAbout(
            importing=importing,
            module_name=module_name,
            parent_package=parent_package,
            tried_names=tried_names,
            level=level,
        )

    return None, None, "not-found"


# Some platforms are case insensitive.
case_sensitive = not sys.platform.startswith(("win", "cygwin", "darwin"))


def _findModuleInPath2(module_name, search_path):
    """ This is out own module finding low level implementation.

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

    for entry in search_path:
        # Don't try again, just with an entry of different casing or complete
        # duplicate.
        if os.path.normcase(entry) in considered:
            continue
        considered.add(os.path.normcase(entry))

        package_directory = os.path.join(entry, module_name)

        # First, check for a package with an init file, that would be the
        # first choice.
        if os.path.isdir(package_directory):
            for suffix, _mode, mtype in imp.get_suffixes():
                if mtype == imp.C_EXTENSION:
                    continue

                package_file_name = "__init__" + suffix

                file_path = os.path.join(package_directory, package_file_name)

                if os.path.isfile(file_path):
                    candidates.add((entry, 1, package_directory))
                    break
            else:
                if python_version >= 300:
                    candidates.add((entry, 2, package_directory))

        # Then, check out suffixes of all kinds.
        for suffix, _mode, _type in imp.get_suffixes():
            file_path = os.path.join(entry, module_name + suffix)
            if os.path.isfile(file_path):
                candidates.add((entry, 1, file_path))
                break

    if _debug_module_finding:
        print("Candidates", candidates)

    if candidates:
        # Ignore lower priority matches from package directories without
        # "__init__.py" file.
        min_prio = min(candidate[1] for candidate in candidates)
        candidates = [candidate for candidate in candidates if candidate[1] == min_prio]

        # On case sensitive systems, no resolution needed.
        if case_sensitive:
            return candidates[0][2]
        else:
            for candidate in candidates:
                for fullname, _filename in listDir(candidate[0]):
                    if fullname == candidate[2]:
                        return candidate[2]

            # Only exact case matches matter, all candidates were ignored,
            # lets just fall through to raising the import error.

    # Nothing found.
    raise ImportError


_egg_files = {}


def _unpackPathElement(path_entry):
    if not path_entry:
        return "."  # empty means current directory

    if os.path.isfile(path_entry) and path_entry.lower().endswith(".egg"):
        if path_entry not in _egg_files:
            with open(path_entry, "rb") as f:
                checksum = hashlib.md5(f.read()).hexdigest()

            target_dir = os.path.join(getCacheDir(), "egg-content", checksum)

            zip_ref = zipfile.ZipFile(path_entry, "r")
            zip_ref.extractall(target_dir)
            zip_ref.close()

            _egg_files[path_entry] = target_dir

        return _egg_files[path_entry]

    return path_entry


def getPackageSearchPath(package_name):
    assert main_path is not None

    if package_name is None:
        return [os.getcwd(), main_path] + [
            _unpackPathElement(path_element) for path_element in sys.path
        ]
    elif "." in package_name:
        parent_package_name, child_package_name = package_name.rsplit(".", 1)

        result = []
        for element in getPackageSearchPath(parent_package_name):
            package_dir = os.path.join(element, child_package_name)

            if isPackageDir(package_dir):
                result.append(package_dir)
                # Hack for "uniconverter". TODO: Move this to plug-in decision. This
                # fails the above test, but at run time should be a package.
            elif package_name == "uniconvertor.app.modules":
                result.append(package_dir)

        return result

    else:
        preloaded_path = getPreloadedPackagePath(package_name)

        if preloaded_path is not None:
            return preloaded_path

        def getPackageDirCandidates(element):
            yield os.path.join(element, package_name), False

            # Hack for PyWin32. TODO: Move this "__path__" extensions to be
            # plug-in decisions.
            if package_name == "win32com":
                yield os.path.join(element, "win32comext"), True

        result = []
        for element in getPackageSearchPath(None):
            for package_dir, force_package in getPackageDirCandidates(element):
                if isPackageDir(package_dir) or force_package:
                    result.append(package_dir)

        return result


def _findModuleInPath(module_name, package_name):
    if _debug_module_finding:
        print("_findModuleInPath: Enter", module_name, "in", package_name)

    # The "site" module must be located based on PYTHONPATH before it was
    # executed, while we normally search in PYTHONPATH after it was executed,
    # and on some systems, that fails.
    if package_name is None and module_name == "site":
        candidate = os.environ.get("NUITKA_SITE_FILENAME", "")

        if candidate:
            return candidate

    # Free pass for built-in modules, the need not exist.
    if package_name is None and imp.is_builtin(module_name):
        return None

    search_path = getPackageSearchPath(package_name)

    if _debug_module_finding:
        print("_findModuleInPath: Using search path", search_path, "for", package_name)

    try:
        module_filename = _findModuleInPath2(
            module_name=module_name, search_path=search_path
        )
    except SyntaxError:
        # Warn user, as this is kind of unusual.
        warning(
            "%s: Module cannot be imported due to syntax errors.",
            module_name if package_name is None else package_name + "." + module_name,
        )

        return None

    if _debug_module_finding:
        print("_findModuleInPath: _findModuleInPath2 gave", module_filename)

    return module_filename


module_search_cache = {}


def _findModule(module_name):
    if _debug_module_finding:
        print("_findModule: Enter to search '%s'." % (module_name,))

    assert not module_name.endswith("."), module_name

    key = module_name

    if key in module_search_cache:
        result = module_search_cache[key]

        if _debug_module_finding:
            print("_findModule: Cached result (see previous call).")

        if result is ImportError:
            raise ImportError

        return result

    try:
        module_search_cache[key] = _findModule2(module_name)
    except ImportError:
        new_module_name = Plugins.considerFailedImportReferrals(module_name)

        if new_module_name is None:
            module_search_cache[key] = ImportError
            raise

        module_search_cache[key] = _findModule(new_module_name)

    return module_search_cache[key]


def _findModule2(module_name):
    # Need a real module name.
    assert module_name != ""

    preloaded_path = getPreloadedPackagePath(module_name)

    if preloaded_path is not None:
        return preloaded_path[0]

    if "." in module_name:
        package_part = module_name[: module_name.rfind(".")]
        module_name = module_name[module_name.rfind(".") + 1 :]
    else:
        package_part = None

    return _findModuleInPath(module_name=module_name, package_name=package_part)
