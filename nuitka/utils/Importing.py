#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Helper to import a file as a module.

Used for Nuitka plugins and for test code.
"""

import os
import sys

from nuitka.PythonVersions import python_version
from nuitka.Tracing import general

from .InlineCopies import getInlineCopyFolder
from .ModuleNames import ModuleName
from .Utils import withNoDeprecationWarning


def _importFilePy3NewWay(filename):
    """Import a file for Python versions 3.5+."""
    import importlib.util  # pylint: disable=I0021,import-error,no-name-in-module

    spec = importlib.util.spec_from_file_location(
        os.path.basename(filename).split(".")[0], filename
    )
    user_plugin_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_plugin_module)
    return user_plugin_module


def _importFilePy3OldWay(filename):
    """Import a file for Python versions before 3.5."""
    from importlib.machinery import (  # pylint: disable=I0021,import-error,no-name-in-module
        SourceFileLoader,
    )

    # pylint: disable=I0021,deprecated-method
    return SourceFileLoader(filename, filename).load_module(filename)


def importFilePy2(filename):
    """Import a file for Python version 2."""
    import imp  # Python2 only, pylint: disable=I0021,import-error

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


_shared_library_suffixes = None


def getSharedLibrarySuffixes():
    # Using global here, as this is for caching only
    # pylint: disable=global-statement
    global _shared_library_suffixes

    if _shared_library_suffixes is None:
        if python_version < 0x300:
            import imp  # Python2 only, pylint: disable=I0021,import-error

            _shared_library_suffixes = []

            for suffix, _mode, module_type in imp.get_suffixes():
                if module_type == imp.C_EXTENSION:
                    _shared_library_suffixes.append(suffix)
        else:
            import importlib.machinery  # pylint: disable=I0021,import-error,no-name-in-module

            _shared_library_suffixes = list(importlib.machinery.EXTENSION_SUFFIXES)

        # Nuitka-Python on Windows has that
        if "" in _shared_library_suffixes:
            _shared_library_suffixes.remove("")

        _shared_library_suffixes = tuple(_shared_library_suffixes)

    return _shared_library_suffixes


def getSharedLibrarySuffix(preferred):
    if preferred and python_version >= 0x300:
        return getSharedLibrarySuffixes()[0]

    result = None

    for suffix in getSharedLibrarySuffixes():
        if result is None or len(suffix) < len(result):
            result = suffix

    return result


def _importFromFolder(logger, module_name, path, must_exist, message):
    """Import a module from a folder by adding it temporarily to sys.path"""

    # Cyclic dependency here
    from .FileOperations import isFilenameBelowPath

    if module_name in sys.modules:
        # May already be loaded, but the wrong one from a ".pth" file of
        # clcache that we then don't want to use.
        if module_name != "clcache" or isFilenameBelowPath(
            path=path, filename=sys.modules[module_name].__file__
        ):
            return sys.modules[module_name]
        else:
            del sys.modules[module_name]

    # Temporarily add the inline path of the module to the import path.
    sys.path.insert(0, path)

    # Handle case without inline copy too.
    try:
        return __import__(module_name, level=0)
    except (ImportError, SyntaxError, RuntimeError) as e:
        if not must_exist:
            return None

        exit_message = (
            "Error, expected inline copy of '%s' to be in '%s', error was: %r."
            % (module_name, path, e)
        )

        if message is not None:
            exit_message += "\n" + message

        logger.sysexit(exit_message)
    finally:
        # Do not forget to remove it from sys.path again.
        del sys.path[0]


_deleted_modules = {}


def importFromInlineCopy(module_name, must_exist, delete_module=False):
    """Import a module from the inline copy stage."""

    folder_name = getInlineCopyFolder(module_name)

    module = _importFromFolder(
        module_name=module_name,
        path=folder_name,
        must_exist=must_exist,
        message=None,
        logger=general,
    )

    if delete_module and module_name in sys.modules:
        delete_module_names = set([module_name])

        for m in sys.modules:
            if m.startswith(module_name + "."):
                delete_module_names.add(m)

        for delete_module_name in delete_module_names:
            _deleted_modules[delete_module_name] = sys.modules[delete_module_name]
            del sys.modules[delete_module_name]

    return module


_compile_time_modules = {}


def importFromCompileTime(module_name, must_exist):
    """Import a module from the compiled time stage.

    This is not for using the inline copy, but the one from the actual
    installation of the user. It suppresses warnings and caches the value
    avoid making more __import__ calls that necessary.
    """

    if module_name not in _compile_time_modules:
        with withNoDeprecationWarning():
            try:
                __import__(module_name)
            except (ImportError, RuntimeError):
                # Preventing a retry, converted to None for return
                _compile_time_modules[module_name] = False
            else:
                _compile_time_modules[module_name] = sys.modules[module_name]

    # Some code should only use this, after knowing it will be found. Complain if
    # that is not the case.
    assert _compile_time_modules[module_name] or not must_exist

    return _compile_time_modules[module_name] or None


def isBuiltinModuleName(module_name):
    if python_version < 0x300:
        import imp as _imp  # Python2 only, pylint: disable=I0021,import-error
    else:
        import _imp

    result = _imp.is_builtin(module_name) or _imp.is_frozen(module_name)

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
        import imp  # Older Python only, pylint: disable=I0021,import-error

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
        import importlib.machinery

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

    for suffix in getSharedLibrarySuffixes():
        if module_filename.endswith(suffix):
            return (
                ModuleName(os.path.basename(module_filename)[: -len(suffix)]),
                "extension",
            )

    return None, None


def hasPackageDirFilename(path):
    path = os.path.basename(path)

    for suffix in (".py",) + getSharedLibrarySuffixes():
        candidate = "__init__" + suffix

        if candidate == path:
            return True

    return False


def getPackageDirFilename(path):
    assert os.path.isdir(path)

    for suffix in getSharedLibrarySuffixes() + (".py",):
        candidate = os.path.join(path, "__init__" + suffix)

        if os.path.isfile(candidate):
            return candidate

    return None


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
