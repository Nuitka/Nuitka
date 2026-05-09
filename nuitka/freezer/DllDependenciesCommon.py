#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""DLL dependency scan methods that are shared."""

import os

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.importing.Importing import locateModule
from nuitka.plugins.Hooks import getModuleSpecificDllPaths
from nuitka.Tracing import inclusion_logger
from nuitka.utils.FileOperations import (
    getNormalizedPathJoin,
    getSubDirectoriesWithDlls,
)
from nuitka.utils.ModuleNames import ModuleName
from nuitka.utils.SharedLibraries import getWindowsRunningProcessDLLPaths
from nuitka.utils.Utils import getArchitecture

_ld_library_cache = {}
_missing_msvc_redist_dlls = OrderedSet()

# Names of MSVC redistributable DLLs to pick up
# spell-checker: ignore concrt,msvcp,vcruntime,vcamp,vccorlib,codecvt,vcomp
_msvc_redist_dll_names = set(
    (
        "concrt140.dll",
        "msvcp140.dll",
        "msvcp140_1.dll",
        "msvcp140_2.dll",
        "msvcp140_atomic_wait.dll",
        "msvcp140_codecvt_ids.dll",
        "vccorlib140.dll",
        "vcruntime140.dll",
        "vcruntime140_1.dll",
        "vcruntime140_threads.dll",
        "vcamp140.dll",
        "vcomp140.dll",
    )
)


def isMsvcRedistDllName(dll_name):
    return dll_name in _msvc_redist_dll_names


def attemptToFindNotFoundDLL(dll_filename):
    """Some heuristics and tricks to find DLLs not found otherwise."""

    # Lets attempt to find it on currently loaded DLLs, this typically should
    # find the Python DLL.
    currently_loaded_dlls = getWindowsRunningProcessDLLPaths()

    if dll_filename in currently_loaded_dlls:
        return currently_loaded_dlls[dll_filename]

    # Lets try the Windows system, spell-checker: ignore systemroot
    dll_filename = getNormalizedPathJoin(
        os.environ["SYSTEMROOT"],
        "SysWOW64" if getArchitecture() == "x86" else "System32",
        dll_filename,
    )
    dll_filename = os.path.normcase(dll_filename)

    if os.path.exists(dll_filename):
        return dll_filename

    return None


def addMissingMsvcRedistDLL(dll_name):
    _missing_msvc_redist_dlls.add(dll_name)


def reportMissingMsvcRedistDLLs():
    if _missing_msvc_redist_dlls:
        inclusion_logger.warning(
            """\
The following Visual C++ Redistributable DLLs were not found: %s. \
For a fully portable standalone distribution, these DLLs must be \
available either by installing the Microsoft Visual C++ Redistributable \
for Visual Studio 2015-2022 on the target system or by bundling them with \
the application. To bundle them, Visual Studio must be installed on the build machine."""
            % ", ".join(sorted(_missing_msvc_redist_dlls))
        )
        _missing_msvc_redist_dlls.clear()


def shallIgnoreMissingDLL(dll_name):
    if dll_name.startswith(("api-ms-win-", "ext-ms-win-")):
        return True

    # Ignore this runtime DLL of Python2, will be coming via manifest.
    # spell-checker: ignore msvcr90
    if dll_name == "msvcr90.dll":
        return True

    # Ignore UCRT runtime, this must come from OS, spell-checker: ignore ucrtbase
    if dll_name == "ucrtbase.dll":
        return True

    return False


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

            return inclusion_logger.sysexit("""\
Error, failed to locate package '%s' while trying to look up DLL dependencies, \
that should not happen. Please report the issue.""" % package_name)

        if os.path.isdir(package_dir):
            scan_dirs.add(package_dir)
            scan_dirs.update(getSubDirectoriesWithDlls(package_dir))

        if consider_plugins:
            for plugin_provided_dir in getModuleSpecificDllPaths(package_name):
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
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
