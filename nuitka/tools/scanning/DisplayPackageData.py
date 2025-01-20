#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Display the DLLs in a package. """

import os

from nuitka.freezer.IncludedDataFiles import scanIncludedPackageDataFiles
from nuitka.importing.Importing import (
    addMainScriptDirectory,
    hasMainScriptDirectory,
    locateModule,
)
from nuitka.Tracing import tools_logger
from nuitka.utils.ModuleNames import ModuleName


def displayPackageData(module_name):
    """Display the package data for a module name."""
    module_name = ModuleName(module_name)

    if not hasMainScriptDirectory():
        addMainScriptDirectory(os.getcwd())

    module_name, package_directory, _module_kind, finding = locateModule(
        module_name=module_name, parent_package=None, level=0
    )

    if finding == "not-found":
        tools_logger.sysexit(
            "Error, cannot find '%s' package." % module_name.asString()
        )

    if not os.path.isdir(package_directory):
        tools_logger.sysexit(
            "Error, doesn't seem that '%s' is a package on disk but rather a plain module."
            % module_name.asString()
        )

    tools_logger.info("Checking package directory '%s' .. " % package_directory)

    count = 0

    first = True

    for pkg_filename in scanIncludedPackageDataFiles(
        package_directory=package_directory, pattern=None
    ):
        if first:
            tools_logger.my_print(package_directory)
            first = False

        tools_logger.my_print(pkg_filename)

        count += 1

    tools_logger.info("Found %s data files." % count)


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
