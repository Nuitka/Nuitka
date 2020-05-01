#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.PythonVersions import python_version


def _importFilePy3NewWay(filename):
    """ Import a file for Python versions 3.5+.
    """
    import importlib.util  # pylint: disable=I0021,import-error,no-name-in-module

    spec = importlib.util.spec_from_file_location(
        os.path.basename(filename).split(".")[0], filename
    )
    user_plugin_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_plugin_module)
    return user_plugin_module


def _importFilePy3OldWay(filename):
    """ Import a file for Python versions before 3.5.
    """
    from importlib.machinery import (  # pylint: disable=I0021,import-error,no-name-in-module
        SourceFileLoader,
    )

    # pylint: disable=I0021,deprecated-method
    return SourceFileLoader(filename, filename).load_module(filename)


def importFilePy2(filename):
    """ Import a file for Python version 2.
    """
    import imp

    basename = os.path.splitext(os.path.basename(filename))[0]
    return imp.load_source(basename, filename)


def importFileAsModule(filename):
    """ Import Python module given as a file name.

    Notes:
        Provides a Python version independent way to import any script files.

    Args:
        filename: complete path of a Python script

    Returns:
        Imported Python module with code from the filename.
    """
    if python_version < 300:
        return importFilePy2(filename)
    elif python_version < 350:
        return _importFilePy3OldWay(filename)
    else:
        return _importFilePy3NewWay(filename)
