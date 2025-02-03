#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Display the DLLs in a package. """

import os

from nuitka.freezer.DllDependenciesCommon import (
    getPackageSpecificDLLDirectories,
)
from nuitka.importing.Importing import (
    addMainScriptDirectory,
    hasMainScriptDirectory,
    locateModule,
)
from nuitka.Tracing import tools_logger
from nuitka.tree.SourceHandling import readSourceCodeFromFilename
from nuitka.utils.FileOperations import (
    listDllFilesFromDirectory,
    listExeFilesFromDirectory,
    relpath,
)
from nuitka.utils.Importing import (
    getPackageDirFilename,
    getSharedLibrarySuffixes,
)
from nuitka.utils.ModuleNames import ModuleName
from nuitka.utils.SharedLibraries import getDllExportedSymbols
from nuitka.utils.Utils import isMacOS


def getPythonEntryPointExportedSymbolName(module_name):
    result = "%s%s" % ("init" if str is bytes else "PyInit_", module_name.asString())

    if isMacOS():
        result = "_" + result

    return result


def isFileExtensionModule(module_filename):
    for suffix in getSharedLibrarySuffixes():
        if module_filename.endswith(suffix):
            module_name = ModuleName(os.path.basename(module_filename)[: -len(suffix)])

            exported_symbols = getDllExportedSymbols(
                logger=tools_logger, filename=module_filename
            )

            if exported_symbols is None:
                return None

            return (
                getPythonEntryPointExportedSymbolName(module_name) in exported_symbols
            )

    return False


def scanModule(module_name, scan_function):
    module_name = ModuleName(module_name)

    if not hasMainScriptDirectory():
        addMainScriptDirectory(os.getcwd())

    module_name, package_directory, module_kind, finding = locateModule(
        module_name=module_name, parent_package=None, level=0
    )

    if finding == "not-found":
        tools_logger.sysexit(
            "Error, cannot find '%s' package." % module_name.asString()
        )

    if not os.path.isdir(package_directory):
        tools_logger.sysexit(
            "Error, doesn't seem that '%s' is a package on disk."
            % module_name.asString()
        )

    from nuitka.plugins.Plugins import activatePlugins

    activatePlugins()

    if module_kind != "extension":
        package_filename = getPackageDirFilename(package_directory)

        if package_filename is not None:
            readSourceCodeFromFilename(module_name, package_filename, pre_load=False)

    tools_logger.info("Checking package directory '%s' .. " % package_directory)

    for package_dll_dir in getPackageSpecificDLLDirectories(
        module_name, consider_plugins=True
    ):
        for package_dll_filename, _dll_basename in scan_function(package_dll_dir):
            if isFileExtensionModule(package_dll_filename):
                continue

            yield package_directory, package_dll_filename, package_dll_dir


def displayDLLs(module_name):
    """Display the DLLs for a module name."""

    count = 0

    for package_directory, package_dll_filename, _package_dll_dir in scanModule(
        module_name=module_name, scan_function=listDllFilesFromDirectory
    ):
        tools_logger.my_print(
            "  %s" % relpath(package_dll_filename, start=package_directory),
        )

        count += 1

    tools_logger.info("Found %s DLLs." % count)


def displayEXEs(module_name):
    """Display the EXEs for a module name."""

    count = 0

    for package_directory, package_dll_filename, _package_dll_dir in scanModule(
        module_name=module_name, scan_function=listExeFilesFromDirectory
    ):

        tools_logger.my_print(
            "  %s" % relpath(package_dll_filename, start=package_directory),
        )

        count += 1

    tools_logger.info("Found %s EXEs." % count)


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
