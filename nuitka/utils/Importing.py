#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Helper to import a file as a module.

Used for Nuitka plugins and for test code.
"""

import os
import sys
from contextlib import contextmanager

from nuitka.__past__ import imp
from nuitka.plugins.Hooks import decideRecompileExtensionModules
from nuitka.PythonVersions import python_version

from .FileOperations import listDir
from .ModuleNames import ModuleName

try:
    import importlib.util  # pylint: disable=I0021,import-error,no-name-in-module
except ImportError:
    pass

try:
    import importlib.machinery  # pylint: disable=I0021,import-error,no-name-in-module
except ImportError:
    pass


def _importFilePy3NewWay(filename):
    """Import a file for Python versions 3.5+."""

    spec = importlib.util.spec_from_file_location(
        os.path.basename(filename).split(".")[0], filename
    )
    user_plugin_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_plugin_module)
    return user_plugin_module


def _importFilePy3OldWay(filename):
    """Import a file for Python versions before 3.5."""

    # pylint: disable=I0021,deprecated-method,no-name-in-module
    return importlib.machinery.SourceFileLoader(filename, filename).load_module(
        filename
    )


def importFilePy2(filename):
    """Import a file for Python version 2."""

    basename = os.path.splitext(os.path.basename(filename))[0]
    return imp.load_source(basename, filename)


def importFileAsModule(filename):
    """Import Python module given as a file name.

    Notes:
        Provides a Python version independent way to import any script files.

    Args:
        filename: complete path of a Python script

    Returns:
        Imported Python module with code from the filename.
    """
    if python_version < 0x300:
        return importFilePy2(filename)
    elif python_version < 0x350:
        return _importFilePy3OldWay(filename)
    else:
        return _importFilePy3NewWay(filename)


_extension_module_suffixes = None


def getExtensionModuleSuffixes():
    # Using global here, as this is for caching only
    # pylint: disable=global-statement
    global _extension_module_suffixes

    if _extension_module_suffixes is None:
        if python_version < 0x300:
            _extension_module_suffixes = []

            for suffix, _mode, module_type in imp.get_suffixes():
                if module_type == imp.C_EXTENSION:
                    _extension_module_suffixes.append(suffix)
        else:
            _extension_module_suffixes = list(importlib.machinery.EXTENSION_SUFFIXES)

        # MonolithPy on Windows has that
        if "" in _extension_module_suffixes:
            _extension_module_suffixes.remove("")

        _extension_module_suffixes = tuple(_extension_module_suffixes)

    return _extension_module_suffixes


def getExtensionModuleSuffix(preferred):
    if preferred and python_version >= 0x300:
        return getExtensionModuleSuffixes()[0]

    result = None

    for suffix in getExtensionModuleSuffixes():
        if result is None or len(suffix) < len(result):
            result = suffix

    return result


def isBuiltinModuleName(module_name):
    result = bool(imp.is_builtin(module_name) or imp.is_frozen(module_name))

    # Some frozen modules are not actually in that list, e.g.
    # "importlib._bootstrap_external" on Python3.10 doesn't report to
    # "_imp.is_frozen()" above, so we check if it's already loaded and from the
    # "FrozenImporter" by name.
    if result is False and module_name in sys.modules:
        module = sys.modules[module_name]

        if hasattr(module, "__loader__"):
            loader = module.__loader__

            try:
                result = loader.__name__ == "FrozenImporter"
            except AttributeError:
                pass

    return result


# Have a set for quicker lookups, and we cannot have "__main__" in there.
builtin_module_names = set(
    module_name for module_name in sys.builtin_module_names if module_name != "__main__"
)


def getModuleFilenameSuffixes():
    if python_version < 0x3C0:
        for suffix, _mode, module_type in imp.get_suffixes():
            if module_type == imp.C_EXTENSION:
                module_type = "C_EXTENSION"
            elif module_type == imp.PY_SOURCE:
                module_type = "PY_SOURCE"
            elif module_type == imp.PY_COMPILED:
                module_type = "PY_COMPILED"
            else:
                assert False, module_type

            yield suffix, module_type
    else:
        for suffix in importlib.machinery.EXTENSION_SUFFIXES:
            yield suffix, "C_EXTENSION"
        for suffix in importlib.machinery.SOURCE_SUFFIXES:
            yield suffix, "PY_SOURCE"
        for suffix in importlib.machinery.BYTECODE_SUFFIXES:
            yield suffix, "PY_COMPILED"


def getModuleNameAndKindFromFilenameSuffix(module_filename):
    """Given a filename, decide the module name and kind.

    Args:
        module_name - file path of the module
    Returns:
        Tuple with the name of the module basename, and the kind of the
        module derived from the file suffix. Can be None, None if is is not a
        known file suffix.
    Notes:
        This doesn't handle packages at all.
    """
    if module_filename.endswith(".py"):
        return ModuleName(os.path.basename(module_filename)[:-3]), "py"

    if module_filename.endswith(".pyc"):
        return ModuleName(os.path.basename(module_filename)[:-4]), "pyc"

    for suffix in getExtensionModuleSuffixes():
        if module_filename.endswith(suffix):
            return (
                ModuleName(os.path.basename(module_filename)[: -len(suffix)]),
                "extension",
            )

    return None, None


def isPackageDirFilenameCandidate(path):
    path = os.path.basename(path)

    for suffix, _module_type in getModuleFilenameSuffixes():
        candidate = "__init__" + suffix

        if candidate == path:
            return True

    return False


def hasPackageDirFilename(path):
    """Check if a directory has a package ``__init__`` file of any kind.

    Args:
        path: The directory to check.

    Returns:
        bool, True if any ``__init__`` file exists in the directory.
    """
    return getPackageDirFilename(path, None) is not None


def getPackageDirFilename(path, package_name):
    assert os.path.isdir(path)

    if package_name:
        decision, _reason = decideRecompileExtensionModules(package_name)
    else:
        decision = False

    candidates = []
    # Higher values are lower priority.
    priority_map = {
        "PY_COMPILED": 3,
        "PY_SOURCE": 2,
        "C_EXTENSION": 1,
    }

    for suffix, module_type in getModuleFilenameSuffixes():
        candidate = os.path.join(path, "__init__" + suffix)

        if os.path.isfile(candidate):
            candidates.append((candidate, module_type))

    def prioritize(candidate):
        if candidate[1] == "PY_SOURCE" and decision:
            return priority_map[candidate[1]] - 2
        return priority_map[candidate[1]]

    if len(candidates) == 0:
        return None
    else:
        return sorted(candidates, key=prioritize)[0][0]


def _addModuleCandidate(candidates, filename_full, filename):
    """Add the best candidate for a module filename, keeping one per kind."""
    for suffix_index, (suffix, module_type) in enumerate(getModuleFilenameSuffixes()):
        if filename.endswith(suffix):
            module_name, _ = getModuleNameAndKindFromFilenameSuffix(filename)

            key = module_name, module_type
            previous = candidates.get(key)

            if previous is None or suffix_index < previous[0]:
                candidates[key] = suffix_index, (filename_full, filename)

            break


def _getPreferredModuleEntries(candidates, package_name):
    """Select the preferred entry for each module name found."""
    # Higher values are lower priority.
    priority_map = {
        "PY_COMPILED": 3,
        "PY_SOURCE": 2,
        "C_EXTENSION": 1,
    }

    # Recompilation decisions are only relevant, when source code and an
    # extension module are available for the same module name.
    source_module_names = set(
        module_name
        for (module_name, module_type) in candidates
        if module_type == "PY_SOURCE"
    )
    extension_module_names = set(
        module_name
        for (module_name, module_type) in candidates
        if module_type == "C_EXTENSION"
    )

    recompile_decisions = {}

    for module_name in source_module_names & extension_module_names:
        decision, _reason = decideRecompileExtensionModules(
            ModuleName.makeModuleNameInPackage(module_name, package_name)
        )

        recompile_decisions[module_name] = decision

    def prioritize(candidate):
        (module_name, module_type), (_suffix_index, _entry) = candidate

        if module_type == "PY_SOURCE" and recompile_decisions.get(module_name):
            return priority_map[module_type] - 2
        return priority_map[module_type]

    result = []
    seen = set()

    for (module_name, _module_type), (_suffix_index, entry) in sorted(
        candidates.items(), key=prioritize
    ):
        if module_name in seen:
            continue

        seen.add(module_name)
        result.append(entry)

    return result


def listPackageDirEntries(path, package_name):
    """List directory entries with duplicate modules resolved.

    Args:
        path: The directory to list.
        package_name: The 'ModuleName' of the package that the directory
            belongs to, or 'None' if its modules are top-level, used to
            decide whether source code is preferred over extension modules.

    Returns:
        List of tuples of full filename and basename, with sub-directories
        passed through and only the preferred file for each module name
        found.

    Notes:
        Duplicate modules can occur when a package contains both a source
        file and an extension module file of the same module name, e.g.
        'foo.py' and 'foo.pyd', and only one of them is to be used. The
        decision is made like for package '__init__' files, see
        'getPackageDirFilename'. Where there are multiple files of the same
        module name and kind, the platform suffix order decides, e.g.
        'foo.cpython-312-x86_64-linux-gnu.so' over 'foo.abi3.so'.
    """
    assert os.path.isdir(path)
    assert package_name is None or type(package_name) is ModuleName, package_name

    candidates = {}
    result = []

    for filename_full, filename in listDir(path):
        if os.path.isdir(filename_full):
            result.append((filename_full, filename))
        else:
            _addModuleCandidate(
                candidates, filename_full=filename_full, filename=filename
            )

    result.extend(_getPreferredModuleEntries(candidates, package_name))

    return result


@contextmanager
def withTemporarySysPathExtension(extra_paths, prepend=False):
    old_path = sys.path[:]

    if prepend:
        sys.path = list(extra_paths) + sys.path
    else:
        sys.path.extend(extra_paths)

    yield

    sys.path[:] = old_path


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
