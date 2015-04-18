#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

The actual import of a module would already execute code that changes things.
Consider a module that does "os.system()", it would be executed. People often
connect to databases, and these kind of things, at import time. Not a good
style, but it's being done.

Therefore CPython exhibits the interfaces in an "imp" module or more modern
"importlib" in standard library, which one can use those to know ahead of time,
to tell what filename an import would load from.

For us unfortunately there is nothing in CPython that gives the fully
compatible functionality we need for packages and search paths exactly like
CPython really does, so we implement here a multiple step search process that is
compatible.
"""

from __future__ import print_function

import imp
import os
import sys
from logging import warning

from nuitka import Options
from nuitka.containers import oset
from nuitka.utils import Utils

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
    # We need to set this from the outside, pylint: disable=W0603

    global main_path
    main_path = main_dir


def isPackageDir(dirname):
    """ Decide if a directory is a package.

        Before Python3.3 it's required to have a "__init__.py" file, but then
        it became impossible to decide, and for extra fun, there is also the
        extra packages provided via "*.pth" file tricks by "site.py" loading.
    """

    return Utils.isDir(dirname) and \
           (
               Utils.python_version >= 330 or
               Utils.isFile(Utils.joinpath(dirname, "__init__.py")) or
               isPreloadedPackagePath(dirname)
           )

def getPackageNameFromFullName(full_name):
    if '.' in full_name:
        return full_name[:full_name.rfind('.')]
    else:
        return None

def warnAbout(module_name, parent_package, level, source_ref):
    # This probably should not be dealt with here.
    if module_name == "":
        return

    if not isWhiteListedNotExistingModule(module_name):
        key = module_name, parent_package, level

        if key not in warned_about:
            warned_about.add(key)

            if level == 0:
                level_desc = "as absolute import"
            elif level == -1:
                level_desc = "as relative or absolute import"
            elif level == 1:
                level_desc = "%d package level up" % level
            else:
                level_desc = "%d package levels up" % level

            if parent_package is not None:
                warning(
                    "%s: Cannot find '%s' in package '%s' %s.",
                    source_ref.getAsString(),
                    module_name,
                    parent_package,
                    level_desc
                )
            else:
                warning(
                    "%s: Cannot find '%s' %s.",
                    source_ref.getAsString(),
                    module_name,
                    level_desc
                )

def normalizePackageName(module_name):
    # The "os.path" is strangely hacked into the "os" module, dispatching per
    # platform, we either cannot look into it, or we require that we resolve it
    # here correctly.
    if module_name == "os.path":
        module_name = Utils.basename(os.path.__name__)

    return module_name


def findModule(source_ref, module_name, parent_package, level, warn):
    """ Find a module with given package name as parent.

        The package name can be None of course. Level is the same
        as with "__import__" built-in. Warnings are optional.

        Returns a triple of package name the module is in, module name
        and filename of it, which can be a directory.
    """

    # We have many branches here, because there are a lot of cases to try.
    # pylint: disable=R0912
    if _debug_module_finding:
        print(
            "findModule: Enter to search %r in package %r level %s." % (
                module_name,
                parent_package,
                level
            )
        )

    # Do not allow star imports to get here. We just won't find modules with
    # that name, but it would be wasteful.
    assert module_name != '*'

    if level > 1:
        # TODO: Should give a warning and return not found if the levels
        # exceed the package name.
        if parent_package is not None:
            parent_package = '.'.join(parent_package.split('.')[:-level+1])

            if parent_package == "":
                parent_package = None
        else:
            return None, None, "not-found"

    # Try relative imports first if we have a parent package.
    if level != 0 and parent_package is not None:
        full_name = normalizePackageName(parent_package + '.' + module_name)

        if full_name.endswith('.'):
            full_name = full_name[:-1]

        package_name = getPackageNameFromFullName(full_name)

        try:
            module_filename = _findModule(
                module_name = full_name,
            )
        except ImportError:
            # For relative import, that is OK, we will still try absolute.
            pass
        else:
            package_name = getPackageNameFromFullName(full_name)
            found = "relative"

            if _debug_module_finding:
                print(
                    "findModule: Relative imported module '%s' as '%s' in filename '%s'    ':" % (
                        module_name,
                        full_name,
                        module_filename
                    )
                )

            return package_name, module_filename, found

    if level <= 1 and module_name != "":
        module_name = normalizePackageName(module_name)

        package_name = getPackageNameFromFullName(module_name)

        # Built-in module names must not be searched any further.
        if module_name in sys.builtin_module_names:
            if _debug_module_finding:
                print(
                    "findModule: Absolute imported module '%s' in as built-in':" % (
                        module_name,
                    )
                )
            return package_name, None, "built-in"

        try:
            module_filename = _findModule(
                module_name = module_name,
            )
        except ImportError:
            # For relative import, that is OK, we will still try absolute.
            pass
        else:
            found = "absolute"

            if _debug_module_finding:
                print(
                    "findModule: Found absolute imported module '%s' in filename '%s':" % (
                        module_name,
                        module_filename
                    )
                )

            return package_name, module_filename, found


    if warn:
        warnAbout(
            module_name,
            parent_package,
            level,
            source_ref
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
    # pylint: disable=R0912

    # We may have to decide between package and module, therefore build
    # a list of candidates.
    candidates = oset.OrderedSet()

    considered = set()

    for entry in search_path:
        # Don't try again, just with an entry of different casing or complete
        # duplicate.
        if Utils.normcase(entry) in considered:
            continue
        considered.add(Utils.normcase(entry))

        package_directory = os.path.join(entry, module_name)

        # First, check for a package with an init file, that would be the
        # first choice.
        if Utils.isDir(package_directory):
            for suffix in (".py", ".pyc"):
                package_file_name = "__init__" + suffix

                file_path = os.path.join(package_directory, package_file_name)

                if Utils.isFile(file_path):
                    candidates.add(
                        (entry, 1, package_directory)
                    )
                    break
            else:
                if Utils.python_version >= 330:
                    candidates.add(
                        (entry, 2, package_directory)
                    )

        # Then, check out suffixes of all kinds.
        for suffix, _mode, _type in imp.get_suffixes():
            file_path = Utils.joinpath(entry, module_name + suffix)
            if Utils.isFile(file_path):
                candidates.add(
                    (entry, 1, file_path)
                )
                break

    if _debug_module_finding:
        print("Candidates", candidates)

    if candidates:
        # Ignore lower priority matches from package directories without
        # "__init__.py" file.
        min_prio = min(candidate[1] for candidate in candidates)
        candidates = [
            candidate
            for candidate in
            candidates
            if candidate[1] == min_prio
        ]

        # On case sensitive systems, no resolution needed.
        if case_sensitive:
            return candidates[0][2]
        else:
            for candidate in candidates:
                dir_listing = os.listdir(candidate[0])

                for filename in dir_listing:
                    if Utils.joinpath(candidate[0], filename) == candidate[2]:
                        return candidate[2]

            # Only excact case matches matter, all candidates were ignored,
            # lets just fall through to raising the import error.

    # Nothing found.
    raise ImportError


def getPackageSearchPath(package_name):
    assert main_path is not None
    if package_name is None:
        return [os.getcwd(), main_path] + sys.path
    elif '.' in package_name:
        parent_package_name, package_name = package_name.rsplit('.', 1)

        result = []
        for element in getPackageSearchPath(parent_package_name):
            package_dir = Utils.joinpath(
                element,
                package_name
            )

            if isPackageDir(package_dir):
                result.append(package_dir)

        return result

    else:
        preloaded_path = getPreloadedPackagePath(package_name)

        if preloaded_path is not None:
            return preloaded_path

        def getPackageDirCandidates(element):
            yield Utils.joinpath(element, package_name), False

            # Hack for PyWin32. TODO: Move this __path__ extensions to
            # plug-in decisions.
            if package_name == "win32com":
                yield Utils.joinpath(element, "win32comext"), True

        result = []
        for element in getPackageSearchPath(None):

            for package_dir, force_package in getPackageDirCandidates(element):
                if isPackageDir(package_dir) or force_package:
                    result.append(package_dir)

        return result


def _findModuleInPath(module_name, package_name):
    if _debug_module_finding:
        print("_findModuleInPath: Enter", module_name, "in", package_name)

    # Free pass for built-in modules, the need not exist.
    if package_name is None and imp.is_builtin(module_name):
        return None, module_name

    search_path = getPackageSearchPath(package_name)

    if _debug_module_finding:
        print("_findModuleInPath: Using search path", search_path)

    try:
        module_filename = _findModuleInPath2(
            module_name = module_name,
            search_path = search_path
        )
    except SyntaxError:
        # Warn user, as this is kind of unusual.
        warning(
            "%s: Module cannot be imported due to syntax errors.",
            module_name
              if package_name is None else
            package_name + '.' + module_name,
        )

        return None

    if _debug_module_finding:
        print("_findModuleInPath: _findModuleInPath2 gave", module_filename)

    return module_filename

module_search_cache = {}

def _findModule(module_name):
    if _debug_module_finding:
        print(
            "_findModule: Enter to search '%s'." % (
                module_name,
            )
        )

    assert not module_name.endswith('.'), module_name

    key = module_name

    if key in module_search_cache:
        result = module_search_cache[key]

        if _debug_module_finding:
            print("_findModule: Cached result (see previous call).")

        if result is ImportError:
            raise ImportError
        else:
            return result

    try:
        module_search_cache[key] = _findModule2(module_name)
    except ImportError:
        module_search_cache[key] = ImportError
        raise

    return module_search_cache[key]


def _findModule2(module_name):
    # Need a real module name.
    assert module_name != ""

    if '.' in module_name:
        package_part = module_name[ : module_name.rfind('.') ]
        module_name = module_name[ module_name.rfind('.') + 1 : ]
    else:
        package_part = None

    return _findModuleInPath(
        module_name  = module_name,
        package_name = package_part
    )
