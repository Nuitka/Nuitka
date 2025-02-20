#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Access package data. """

import os
import pkgutil

from nuitka.importing.Importing import locateModule

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
