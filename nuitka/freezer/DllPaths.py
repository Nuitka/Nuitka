#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Classification of DLL paths for standalone mode."""

from nuitka.importing.Importing import (
    getExtraSysPaths,
    getMainScriptDirectories,
    getPythonUnpackedSearchPath,
)
from nuitka.PythonFlavors import (
    getHomebrewInstallPath,
    getMacPortsInstallPath,
    isAnacondaPython,
    isCPythonOfficialPackage,
    isHomebrewPython,
    isMacPortsPython,
    isMSYS2MingwPython,
    isPyenvHomebrewPython,
    isPythonBuildStandalonePython,
)
from nuitka.PythonPrefixes import getSystemPrefixPath
from nuitka.utils.FileOperations import (
    getNormalizedPathJoin,
    isFilenameBelowPath,
)
from nuitka.utils.Utils import isMacOS, isWin32Windows

from .DllDependenciesWin32 import shallIncludeVCRedistDLL

_inside_paths = None


def _getInsidePaths():
    """Return directories considered inside the Python installation or program.

    Returns:
        tuple of directory paths
    """
    global _inside_paths  # singleton, pylint: disable=global-statement

    if _inside_paths is None:
        inside_paths = getPythonUnpackedSearchPath()

        # Shared libraries that live next to the program rather than in the
        # Python installation must be kept, e.g. packages vendored next to the
        # main script that ship their dependencies in sibling directories.
        inside_paths.extend(getMainScriptDirectories())
        inside_paths.extend(getExtraSysPaths())

        if isAnacondaPython():
            inside_paths.insert(0, getSystemPrefixPath())

        if isMacOS() and (
            isCPythonOfficialPackage() or isPythonBuildStandalonePython()
        ):
            inside_paths.insert(0, getSystemPrefixPath())

        if isMacPortsPython():
            inside_paths.insert(0, getMacPortsInstallPath())

        if isHomebrewPython() or isPyenvHomebrewPython():
            inside_paths.insert(0, getHomebrewInstallPath())

        if isMSYS2MingwPython():
            inside_paths.insert(0, getNormalizedPathJoin(getSystemPrefixPath(), "bin"))

        _inside_paths = tuple(inside_paths)

    return _inside_paths


_dll_path_preferences = {
    "system": 0,
    "vc_redist": 1,
    "inside": 2,
}


def classifyDllPath(dll_filename):
    """Classify a DLL path as being inside the build or from the system.

    Args:
        dll_filename: The DLL filename to classify.

    Returns:
        'inside' for DLLs from the Python installation or program directories,
        'vc_redist' for Windows runtime DLLs to be included explicitly, and
        'system' for system or otherwise external DLLs.
    """
    for inside_path in _getInsidePaths():
        if isFilenameBelowPath(path=inside_path, filename=dll_filename):
            return "inside"

    if isWin32Windows() and shallIncludeVCRedistDLL(dll_filename):
        return "vc_redist"

    return "system"


def compareDllPathClassifications(left, right):
    """Compare two DLL path classifications.

    Args:
        left: One of 'inside', 'vc_redist', or 'system'.
        right: One of 'inside', 'vc_redist', or 'system'.

    Returns:
        int - positive if 'left' is preferred, negative if 'right' is
        preferred, and zero if they are equal.
    """
    return _dll_path_preferences[left] - _dll_path_preferences[right]


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
