#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Interface to pefile on Windows."""

import os

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.utils.FileOperations import listDllFilesFromDirectory
from nuitka.utils.SharedLibraries import getPEFileUsedDllNames

from .DllDependenciesCommon import (
    addMissingMsvcRedistDLL,
    attemptToFindNotFoundDLL,
    isMsvcRedistDllName,
    reportMissingMsvcRedistDLLs,
    shallIgnoreMissingDLL,
)

_scan_dir_dll_cache = {}


def _getScanDirectoryDLLs(scan_dirs):
    cache_key = tuple(scan_dirs)

    if cache_key not in _scan_dir_dll_cache:
        result = {}

        for scan_dir in scan_dirs:
            for dll_filename, dll_basename in listDllFilesFromDirectory(scan_dir):
                dll_basename = dll_basename.lower()

                if dll_basename not in result:
                    result[dll_basename] = os.path.normcase(
                        os.path.abspath(dll_filename)
                    )

        _scan_dir_dll_cache[cache_key] = result

    return _scan_dir_dll_cache[cache_key]


def detectDLLsWithPEFile(binary_filename, scan_dirs):
    """Detect DLLs used by a binary using recursive PE import analysis.

    Args:
        binary_filename: The binary to check.
        scan_dirs: Directories to search for DLLs.

    Returns:
        OrderedSet: Set of found DLL filenames.
    """
    result = OrderedSet()

    scan_dir_dlls = _getScanDirectoryDLLs(scan_dirs=scan_dirs)
    pending = [os.path.normcase(os.path.abspath(binary_filename))]
    scanned = set()

    while pending:
        current_binary = pending.pop()

        if current_binary in scanned:
            continue

        scanned.add(current_binary)

        pe_dll_names = getPEFileUsedDllNames(current_binary)

        if pe_dll_names is None:
            continue

        for dll_name in pe_dll_names:
            dll_name = dll_name.lower()

            dll_filename = scan_dir_dlls.get(dll_name)

            if dll_filename is None and isMsvcRedistDllName(dll_name):
                addMissingMsvcRedistDLL(dll_name)

            if (
                dll_filename is None
                and dll_name.startswith("python")
                and dll_name.endswith(".dll")
            ):
                dll_filename = attemptToFindNotFoundDLL(dll_name)

            if dll_filename is None:
                if shallIgnoreMissingDLL(dll_name):
                    continue

                continue

            dll_filename = os.path.normcase(os.path.abspath(dll_filename))
            dll_basename = os.path.basename(dll_filename).lower()

            if shallIgnoreMissingDLL(dll_basename):
                continue

            result.add(dll_filename)

            if dll_filename not in scanned:
                pending.append(dll_filename)

    reportMissingMsvcRedistDLLs()

    return result


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
