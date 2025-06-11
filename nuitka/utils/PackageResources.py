#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Access package data. """

import os
import pkgutil

from nuitka.importing.Importing import locateModule
from nuitka.PythonVersions import python_version

from .FileOperations import getFileContents


def getPackageData(package_name, resource):
    """Get the package data, but without loading the code, i.e. we try and avoids its loader.

    If it's absolutely necessary, we fallback to "pkgutil.get_data" but
    only if we absolutely cannot find it easily.
    """
    package_directory = locateModule(package_name, None, 0)[1]

    if package_directory is not None:
        resource_filename = os.path.join(package_directory, resource)

        if os.path.exists(resource_filename):
            return getFileContents(resource_filename, mode="rb")

    # Try importlib.resources next for a more standard approach.
    try:
        if python_version >= 0x370:
            import importlib.resources as importlib_resources

            return importlib_resources.read_binary(package_name.asString(), resource)
        elif python_version >= 0x350:
            # Use backport or older importlib.resources
            import importlib.resources as importlib_resources

            with importlib_resources.open_binary(
                package_name.asString(), resource
            ) as fp:
                return fp.read()
    except (ImportError, FileNotFoundError, OSError, TypeError):
        pass

    # Fallback to pkgutil if all else fails, this however may import
    # the package, which is not a good idea at all.
    return pkgutil.get_data(package_name.asString(), resource)


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
