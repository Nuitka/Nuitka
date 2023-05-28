#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Interface to depends.exe on Windows.

We use depends.exe to investigate needed DLLs of Python DLLs.

"""

import os

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.Options import assumeYesForDownloads
from nuitka.Tracing import inclusion_logger
from nuitka.utils.Download import getCachedDownload
from nuitka.utils.Execution import executeProcess, withEnvironmentVarOverridden
from nuitka.utils.FileOperations import (
    deleteFile,
    getExternalUsePath,
    getFileContentByLine,
    isFilenameBelowPath,
    putTextFileContents,
    withFileLock,
)
from nuitka.utils.SharedLibraries import getWindowsRunningProcessDLLPaths
from nuitka.utils.Utils import getArchitecture


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
        url=depends_url,
        is_arch_specific=getArchitecture(),
        binary="depends.exe",
        flatten=True,
        specificity="",  # Note: If there ever was an update, put version here.
        message="""\
Nuitka will make use of Dependency Walker (https://dependencywalker.com) tool
to analyze the dependencies of Python extension modules.""",
        reject="Nuitka does not work in --standalone or --onefile on Windows without.",
        assume_yes_for_downloads=assumeYesForDownloads(),
    )


def _attemptToFindNotFoundDLL(dll_filename):
    """Some heuristics and tricks to find DLLs that dependency walker did not find."""

    # Lets attempt to find it on currently loaded DLLs, this typically should
    # find the Python DLL.
    currently_loaded_dlls = getWindowsRunningProcessDLLPaths()

    if dll_filename in currently_loaded_dlls:
        return currently_loaded_dlls[dll_filename]

    dll_filename = os.path.join(
        os.environ["SYSTEMROOT"],
        "SysWOW64" if getArchitecture() == "x86_64" else "System32",
        dll_filename,
    )
    dll_filename = os.path.normcase(dll_filename)

    if os.path.exists(dll_filename):
        return dll_filename

    return None


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

        if isFilenameBelowPath(
            path=os.path.join(os.environ["SYSTEMROOT"], "WinSxS"), filename=dll_filename
        ):
            continue

        # Skip DLLs that failed to load, apparently not needed anyway.
        if "E" in line[: line.find("]")]:
            continue

        # Skip missing DLLs, apparently not needed anyway, but we can still
        # try a few tricks
        if "?" in line[: line.find("]")]:
            # One exception are "PythonXY.DLL", we try to find them from Windows folder.
            if dll_filename.startswith("python") and dll_filename.endswith(".dll"):
                dll_filename = _attemptToFindNotFoundDLL(dll_filename)

                if dll_filename is None:
                    continue
            else:
                continue

        assert os.path.basename(dll_filename) != "kernel32.dll"

        dll_filename = os.path.abspath(dll_filename)

        dll_name = os.path.basename(dll_filename)

        # Ignore this runtime DLL of Python2, will be coming via manifest.
        if dll_name in ("msvcr90.dll",):
            continue

        # The executable itself is of course exempted. We cannot check its path
        # because depends.exe mistreats unicode paths.
        if first:
            first = False
            continue

        assert os.path.isfile(dll_filename), (dll_filename, line)

        result.add(os.path.normcase(os.path.abspath(dll_filename)))

    return result


def parseDependsExeOutput(filename):
    return _parseDependsExeOutput2(getFileContentByLine(filename, encoding="latin1"))


def detectDLLsWithDependencyWalker(binary_filename, source_dir, scan_dirs):
    dwp_filename = os.path.join(source_dir, os.path.basename(binary_filename) + ".dwp")
    output_filename = os.path.join(
        source_dir, os.path.basename(binary_filename) + ".depends"
    )

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
        _stdout, _stderr, _exit_code = executeProcess(
            command=(
                depends_exe,
                "-c",
                "-ot%s" % output_filename,
                "-d:%s" % dwp_filename,
                "-f1",
                "-pa1",
                "-ps1",
                binary_filename,
            ),
            external_cwd=True,
        )

    if not os.path.exists(output_filename):
        inclusion_logger.sysexit(
            "Error, 'depends.exe' failed to produce expected output."
        )

    # Opening the result under lock, so it is not getting locked by new processes.

    # Note: Do this under lock to avoid forked processes to hold
    # a copy of the file handle on Windows.
    result = parseDependsExeOutput(output_filename)

    deleteFile(output_filename, must_exist=True)
    deleteFile(dwp_filename, must_exist=True)

    return result
