#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""DLL dependency scan methods that are shared. """

import os

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.importing.Importing import locateModule
from nuitka.plugins.Plugins import Plugins
from nuitka.Tracing import inclusion_logger
from nuitka.utils.FileOperations import getSubDirectoriesWithDlls
from nuitka.utils.ModuleNames import ModuleName

_ld_library_cache = {}


def getLdLibraryPath(package_name, python_rpaths, original_dir):
    key = package_name, tuple(python_rpaths), original_dir

    if key not in _ld_library_cache:
        ld_library_path = OrderedSet()
        if python_rpaths:
            ld_library_path.update(python_rpaths)

        ld_library_path.update(
            getPackageSpecificDLLDirectories(
                package_name=package_name,
                consider_plugins=True,
            )
        )
        if original_dir is not None:
            ld_library_path.add(original_dir)

        _ld_library_cache[key] = ld_library_path

    return _ld_library_cache[key]


def getPackageSpecificDLLDirectories(
    package_name, consider_plugins, allow_not_found=False
):
    scan_dirs = OrderedSet()

    if package_name is not None:
        package_dir = locateModule(
            module_name=package_name, parent_package=None, level=0
        )[1]

        if package_dir is None:
            if allow_not_found:
                return scan_dirs

            inclusion_logger.sysexit(
                """\
Error, failed to locate package '%s' while trying to look up DLL dependencies, \
that should not happen. Please report the issue."""
                % package_name
            )

        if os.path.isdir(package_dir):
            scan_dirs.add(package_dir)
            scan_dirs.update(getSubDirectoriesWithDlls(package_dir))

        if consider_plugins:
            for plugin_provided_dir in Plugins.getModuleSpecificDllPaths(package_name):
                if os.path.isdir(plugin_provided_dir):
                    scan_dirs.add(plugin_provided_dir)
                    scan_dirs.update(getSubDirectoriesWithDlls(plugin_provided_dir))

    # TODO: Move this to plugins DLLs section.
    if package_name == "torchvision" and consider_plugins:
        scan_dirs.update(
            getPackageSpecificDLLDirectories(
                package_name=ModuleName("torch"),
                consider_plugins=True,
                allow_not_found=True,
            )
        )

    return scan_dirs


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
