#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
"""DLL dependency scan methods for Win32 Windows.

Note: MSYS2, aka POSIX Windows is dealt with in the "DllDependenciesPosix" module.
"""

import hashlib
import os
import sys

from nuitka.__past__ import iterItems
from nuitka.build.SconsUtils import readSconsReport
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.Options import isShowProgress
from nuitka.Tracing import inclusion_logger
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.FileOperations import (
    areSamePaths,
    getDirectoryRealPath,
    getFileContentByLine,
    getSubDirectoriesWithDlls,
    listDllFilesFromDirectory,
    makePath,
    putTextFileContents,
    withFileLock,
)
from nuitka.utils.SharedLibraries import getPyWin32Dir

from .DependsExe import detectDLLsWithDependencyWalker
from .DllDependenciesCommon import getPackageSpecificDLLDirectories

_scan_dir_cache = {}


def detectBinaryPathDLLsWindowsDependencyWalker(
    is_main_executable,
    source_dir,
    original_dir,
    binary_filename,
    package_name,
    use_cache,
    update_cache,
):
    # This is the caching mechanism and plugin handling for DLL imports.
    if use_cache or update_cache:
        cache_filename = _getCacheFilename(
            dependency_tool="depends.exe",
            is_main_executable=is_main_executable,
            source_dir=source_dir,
            original_dir=original_dir,
            binary_filename=binary_filename,
        )

        if use_cache:
            with withFileLock():
                if not os.path.exists(cache_filename):
                    use_cache = False

        if use_cache:
            result = OrderedSet()

            for line in getFileContentByLine(cache_filename):
                line = line.strip()

                result.add(line)

            return result

    if isShowProgress():
        inclusion_logger.info("Analyzing dependencies of '%s'." % binary_filename)

    scan_dirs = _getScanDirectories(package_name, original_dir)

    result = detectDLLsWithDependencyWalker(
        binary_filename=binary_filename, source_dir=source_dir, scan_dirs=scan_dirs
    )

    if update_cache:
        putTextFileContents(filename=cache_filename, contents=result)

    return result


def _getScanDirectories(package_name, original_dir):
    cache_key = package_name, original_dir

    if cache_key in _scan_dir_cache:
        return _scan_dir_cache[cache_key]

    scan_dirs = [sys.prefix]

    if package_name is not None:
        scan_dirs.extend(getPackageSpecificDLLDirectories(package_name))

    if original_dir is not None:
        scan_dirs.append(original_dir)
        scan_dirs.extend(getSubDirectoriesWithDlls(original_dir))

    if package_name is not None and package_name.isBelowNamespace("win32com"):
        py_win32_dir = getPyWin32Dir()

        if py_win32_dir is not None:
            scan_dirs.append(py_win32_dir)

    for path_dir in os.environ["PATH"].split(";"):
        if not os.path.isdir(path_dir):
            continue

        if areSamePaths(path_dir, os.path.join(os.environ["SYSTEMROOT"])):
            continue
        if areSamePaths(path_dir, os.path.join(os.environ["SYSTEMROOT"], "System32")):
            continue
        if areSamePaths(path_dir, os.path.join(os.environ["SYSTEMROOT"], "SysWOW64")):
            continue

        scan_dirs.append(path_dir)

    result = []

    # Remove directories that hold no DLLs.
    for scan_dir in scan_dirs:
        scan_dir = getDirectoryRealPath(scan_dir)

        # Not a directory, or no DLLs, no use.
        if not os.path.isdir(scan_dir) or not any(listDllFilesFromDirectory(scan_dir)):
            continue

        result.append(os.path.realpath(scan_dir))

    _scan_dir_cache[cache_key] = result
    return result


def _getCacheFilename(
    dependency_tool, is_main_executable, source_dir, original_dir, binary_filename
):
    original_filename = os.path.join(original_dir, os.path.basename(binary_filename))
    original_filename = os.path.normcase(original_filename)

    if is_main_executable:
        # Normalize main program name for caching as well, but need to use the
        # scons information to distinguish different compilers, so we use
        # different libs there.

        # Ignore values, that are variable per compilation.
        hashed_value = "".join(
            key + value
            for key, value in iterItems(readSconsReport(source_dir=source_dir))
            if key not in ("CLCACHE_STATS", "CCACHE_LOGFILE", "CCACHE_DIR")
        )
    else:
        hashed_value = original_filename

    # Have different values for different Python major versions.
    hashed_value += sys.version + sys.executable

    if str is not bytes:
        hashed_value = hashed_value.encode("utf8")

    cache_dir = os.path.join(getCacheDir(), "library_dependencies", dependency_tool)

    makePath(cache_dir)

    return os.path.join(cache_dir, hashlib.md5(hashed_value).hexdigest())
