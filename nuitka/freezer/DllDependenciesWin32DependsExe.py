#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Interface to depends.exe on Windows.

We use "depends.exe" to investigate needed DLLs of Python DLLs.

"""

import os

# pylint: disable=I0021,import-error,redefined-builtin
from nuitka.__past__ import WindowsError
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.options.Options import assumeYesForDownloads
from nuitka.Tracing import inclusion_logger
from nuitka.utils.Download import getCachedDownload
from nuitka.utils.Execution import executeProcess, withEnvironmentVarOverridden
from nuitka.utils.FileOperations import (
    deleteFile,
    getExternalUsePath,
    getFileContentByLine,
    getNormalizedPath,
    getNormalizedPathJoin,
    getWindowsLongPathName,
    isFilenameBelowPath,
    isFilesystemEncodable,
    putTextFileContents,
    withFileLock,
)
from nuitka.utils.Utils import getArchitecture

from .DllDependenciesCommon import (
    addMissingMsvcRedistDLL,
    attemptToFindNotFoundDLL,
    isMsvcRedistDllName,
    reportMissingMsvcRedistDLLs,
    shallIgnoreMissingDLL,
)


def getDependsExePath():
    """Return the path of depends.exe (for Windows).

    Will prompt the user to download if not already cached in AppData
    directory for Nuitka.
    """
    if getArchitecture() == "x86":
        depends_url = "https://dependencywalker.com/depends22_x86.zip"
    else:
        depends_url = "https://dependencywalker.com/depends22_x64.zip"

    return getCachedDownload(
        name="dependency walker",
        url=depends_url,
        is_arch_specific=getArchitecture(),
        binary="depends.exe",
        unzip=True,
        flatten=True,
        specificity="",  # Note: If there ever was an update, put version here.
        message="""\
Nuitka will make use of Dependency Walker (https://dependencywalker.com) tool
to analyze the dependencies of Python extension modules.""",
        reject="Nuitka does not work in '--mode=standalone' or '--mode=onefile' on Windows without dependency walker.",
        assume_yes_for_downloads=assumeYesForDownloads(),
        download_ok=True,
    )


def _parseDependsExeOutput2(lines):
    # Many cases to deal with, pylint: disable=too-many-branches

    result = OrderedSet()

    inside = False
    first = False

    for line in lines:
        if "| Module Dependency Tree |" in line:
            inside = True
            first = True
            continue

        if not inside:
            continue

        if "| Module List |" in line:
            break

        if "]" not in line:
            continue

        dll_filename = line[line.find("]") + 2 :].rstrip()
        dll_filename = os.path.normcase(dll_filename)

        # spell-checker: ignore SYSTEMROOT
        if isFilenameBelowPath(
            path=getNormalizedPathJoin(os.environ["SYSTEMROOT"], "WinSxS"),
            filename=dll_filename,
        ):
            continue

        # Skip DLLs that failed to load, apparently not needed anyway.
        if "E" in line[: line.find("]")]:
            continue

        # Try to find missing DLLs for PythonXY.dll and keep track of missing
        # MSVC Redist DLLs.
        if "?" in line[: line.find("]")]:
            if isMsvcRedistDllName(dll_filename):
                addMissingMsvcRedistDLL(dll_filename)

            # One exception are "PythonXY.DLL", we try to find them from
            # Windows folder.
            if dll_filename.startswith("python") and dll_filename.endswith(".dll"):
                dll_filename = attemptToFindNotFoundDLL(dll_filename)

                if dll_filename is None:
                    continue
            else:
                continue

        # The executable itself is of course exempted. We cannot check its path
        # because depends.exe mistreats unicode paths.
        if first:
            first = False
            continue

        dll_filename = os.path.abspath(dll_filename)

        # Ignore errors trying to resolve the filename. Sometimes Chinese
        # directory paths do not resolve to long filenames.
        try:
            dll_filename = getWindowsLongPathName(dll_filename)
        except WindowsError:
            pass

        dll_name = os.path.basename(dll_filename)

        if shallIgnoreMissingDLL(dll_name):
            continue

        assert os.path.isfile(dll_filename), (dll_filename, line)

        result.add(getNormalizedPath(os.path.normcase(dll_filename)))

    return result


def parseDependsExeOutput(filename):
    return _parseDependsExeOutput2(getFileContentByLine(filename, encoding="latin1"))


def detectDLLsWithDependsExe(binary_filename, source_dir, scan_dirs):
    source_dir = getExternalUsePath(source_dir)
    temp_base_name = os.path.basename(binary_filename)

    if not isFilesystemEncodable(temp_base_name):
        temp_base_name = "dependency_walker"

    dwp_filename = getNormalizedPathJoin(source_dir, temp_base_name + ".dwp")
    output_filename = getNormalizedPathJoin(source_dir, temp_base_name + ".depends")

    # User query should only happen once if at all.
    with withFileLock(
        "Finding out dependency walker path and creating DWP file for %s"
        % binary_filename
    ):
        depends_exe = getDependsExePath()

        # Note: Do this under lock to avoid forked processes to hold
        # a copy of the file handle on Windows.
        putTextFileContents(
            dwp_filename,
            contents="""\
SxS
%(scan_dirs)s
"""
            % {
                "scan_dirs": "\n".join(
                    "UserDir %s" % getExternalUsePath(dirname) for dirname in scan_dirs
                )
            },
        )

    # Starting the process while locked, so file handles are not duplicated.
    # TODO: At least exit code should be checked, output goes to a filename,
    # but errors might be interesting potentially.

    with withEnvironmentVarOverridden("PATH", ""):
        # TODO: At least exit code should be checked, output goes to a filename,
        # but errors might be interesting potentially.
        _process_result = executeProcess(
            command=(
                depends_exe,
                "-c",
                "-ot%s" % output_filename,
                "-d:%s" % dwp_filename,
                "-f1",
                "-pa1",
                "-ps1",
                getExternalUsePath(binary_filename),
            ),
            external_cwd=True,
        )

    if not os.path.exists(output_filename):
        return inclusion_logger.sysexit(
            "Error, 'depends.exe' failed to produce expected output for binary '%s'."
            % binary_filename
        )

    # Opening the result under lock, so it is not getting locked by new
    # processes.
    result = parseDependsExeOutput(output_filename)

    deleteFile(output_filename, must_exist=True)
    deleteFile(dwp_filename, must_exist=True)

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
