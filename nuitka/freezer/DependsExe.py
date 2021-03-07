#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
import subprocess

from nuitka.containers.oset import OrderedSet
from nuitka.Options import assumeYesForDownloads
from nuitka.Tracing import inclusion_logger
from nuitka.utils.Download import getCachedDownload
from nuitka.utils.Execution import getNullInput
from nuitka.utils.FileOperations import (
    deleteFile,
    getExternalUsePath,
    getFileContentByLine,
    withFileLock,
)
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
        is_arch_specific=True,
        binary="depends.exe",
        flatten=True,
        specifity="",  # Note: If there ever was an update, put version here.
        message="""\
Nuitka will make use of Dependency Walker (https://dependencywalker.com) tool
to analyze the dependencies of Python extension modules.""",
        reject="Nuitka does not work in --standalone or --onefile on Windows without.",
        assume_yes_for_downloads=assumeYesForDownloads(),
    )


def _parseDependsExeOutput2(lines):
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

        # Skip DLLs that failed to load, apparently not needed anyway.
        if "E" in line[: line.find("]")]:
            continue

        # Skip missing DLLs, apparently not needed anyway.
        if "?" in line[: line.find("]")]:
            # One exception are PythonXY.DLL
            if dll_filename.startswith("python") and dll_filename.endswith(".dll"):
                dll_filename = os.path.join(
                    os.environ["SYSTEMROOT"],
                    "SysWOW64" if getArchitecture() == "x86_64" else "System32",
                    dll_filename,
                )
                dll_filename = os.path.normcase(dll_filename)
            else:
                continue

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


def _parseDependsExeOutput(filename):
    return _parseDependsExeOutput2(getFileContentByLine(filename, encoding="latin1"))


def detectDLLsWithDependencyWalker(binary_filename, scan_dirs):
    dwp_filename = binary_filename + ".dwp"
    output_filename = binary_filename + ".depends"

    # User query should only happen once if at all.
    with withFileLock(
        "Finding out dependency walker path and creating DWP file for %s"
        % binary_filename
    ):
        depends_exe = getDependsExePath()

        # Note: Do this under lock to avoid forked processes to hold
        # a copy of the file handle on Windows.
        with open(dwp_filename, "w") as dwp_file:
            dwp_file.write(
                """\
%(scan_dirs)s
SxS
"""
                % {
                    "scan_dirs": "\n".join(
                        "UserDir %s" % getExternalUsePath(dirname)
                        for dirname in scan_dirs
                    )
                }
            )

    # Starting the process while locked, so file handles are not duplicated.
    depends_exe_process = subprocess.Popen(
        (
            depends_exe,
            "-c",
            "-ot%s" % output_filename,
            "-d:%s" % dwp_filename,
            "-f1",
            "-pa1",
            "-ps1",
            binary_filename,
        ),
        stdin=getNullInput(),
        cwd=getExternalUsePath(os.getcwd()),
    )

    # TODO: Exit code should be checked.
    depends_exe_process.wait()

    if not os.path.exists(output_filename):
        inclusion_logger.sysexit(
            "Error, depends.exe failed to produce expected output."
        )

    # Opening the result under lock, so it is not getting locked by new processes.

    # Note: Do this under lock to avoid forked processes to hold
    # a copy of the file handle on Windows.
    result = _parseDependsExeOutput(output_filename)

    deleteFile(output_filename, must_exist=True)
    deleteFile(dwp_filename, must_exist=True)

    return result
