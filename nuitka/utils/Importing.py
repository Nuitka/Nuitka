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
""" Helper to import a file as a module.

Used for Nuitka plugins and for test code.
"""

import os
import sys

from nuitka.PythonVersions import python_version
from nuitka.Tracing import general

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
    import imp

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
            import imp

            _shared_library_suffixes = []

            for suffix, _mode, module_type in imp.get_suffixes():
                if module_type == imp.C_EXTENSION:
                    _shared_library_suffixes.append(suffix)
        else:
            import importlib.machinery  # pylint: disable=I0021,import-error,no-name-in-module

            _shared_library_suffixes = importlib.machinery.EXTENSION_SUFFIXES

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
        return __import__(module_name)
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


def importFromInlineCopy(module_name, must_exist):
    """Import a module from the inline copy stage."""

    folder_name = os.path.normpath(
        os.path.join(
            os.path.dirname(__file__), "..", "build", "inline_copy", module_name
        )
    )

    candidate_27 = folder_name + "_27"
    candidate_35 = folder_name + "_35"

    # Use specific versions if needed.
    if python_version < 0x300 and os.path.exists(candidate_27):
        folder_name = candidate_27
    elif python_version < 0x360 and os.path.exists(candidate_35):
        folder_name = candidate_35

    return _importFromFolder(
        module_name=module_name,
        path=folder_name,
        must_exist=must_exist,
        message=None,
        logger=general,
    )


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
