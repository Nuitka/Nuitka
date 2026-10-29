#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Utilities for acquiring a Wasmtime runtime."""

import contextlib
import os
import tarfile

from nuitka.Tracing import general

from .Download import (
    getDownload,
    getDownloadCacheDir,
    getDownloadMode,
    shouldDownload,
)
from .FileOperations import (
    deleteFile,
    getNormalizedPathJoin,
    makeContainingPath,
    makePath,
    removeDirectory,
    renameFile,
    resetDirectory,
)
from .Utils import getArchitecture, isLinux, isMacOS, isWin32Windows

_wasmtime_version = "50.0.0"


def _getWasmtimeArchiveName():
    architecture = getArchitecture()

    if isLinux():
        platform_name = {
            "x86_64": "x86_64-linux",
            "arm64": "aarch64-linux",
        }.get(architecture)
    elif isMacOS():
        platform_name = {
            "x86_64": "x86_64-macos",
            "arm64": "aarch64-macos",
        }.get(architecture)
    elif isWin32Windows():
        platform_name = {
            "x86_64": "x86_64-windows",
            "x86": "i686-windows",
        }.get(architecture)
    else:
        platform_name = None

    if platform_name is None:
        return general.sysexit(
            "Error, Wasmtime %s is not available for this platform." % _wasmtime_version
        )

    if isWin32Windows():
        return "wasmtime-v%s-%s.zip" % (_wasmtime_version, platform_name)

    return "wasmtime-v%s-%s.tar.xz" % (_wasmtime_version, platform_name)


def _getWasmtimeURL():
    return "https://github.com/bytecodealliance/wasmtime/releases/download/v%s/%s" % (
        _wasmtime_version,
        _getWasmtimeArchiveName(),
    )


def _ensureDownloaded(url, download_path, description, assume_yes_for_downloads):
    if os.path.isfile(download_path):
        return

    makeContainingPath(download_path)

    if not shouldDownload(
        message="Nuitka will download %s to run WASI binaries." % description,
        reject_message="Error, need %s to run WASI binaries." % description,
        download_mode=getDownloadMode(assume_yes_for_downloads),
    ):
        return general.sysexit("Error, need %s to run WASI binaries." % description)

    getDownload(
        name=description,
        url=url,
        download_path=download_path,
    )


def _findWasmtimeBinary(extract_dir):
    for root, _dirs, files in os.walk(extract_dir):
        if "wasmtime" in files:
            return getNormalizedPathJoin(root, "wasmtime")

    return None


def getWasmtimePath(assume_yes_for_downloads):
    """Return a cached Wasmtime binary path."""
    if isWin32Windows():
        return general.sysexit(
            "Error, automatic Wasmtime download is not supported on Windows yet."
        )

    version_dir = getNormalizedPathJoin(
        getDownloadCacheDir(), "wasmtime", _wasmtime_version
    )
    wasmtime_path = getNormalizedPathJoin(version_dir, "wasmtime")

    if os.path.isfile(wasmtime_path):
        return wasmtime_path

    makePath(version_dir)

    archive_name = _getWasmtimeArchiveName()
    archive_path = getNormalizedPathJoin(version_dir, archive_name)
    extract_dir = getNormalizedPathJoin(version_dir, "extract")

    _ensureDownloaded(
        url=_getWasmtimeURL(),
        download_path=archive_path,
        description="Wasmtime %s" % _wasmtime_version,
        assume_yes_for_downloads=assume_yes_for_downloads,
    )

    resetDirectory(
        extract_dir,
        logger=general,
        ignore_errors=False,
        extra_recommendation=None,
    )

    with contextlib.closing(tarfile.open(archive_path, "r:xz")) as tar:
        tar.extractall(extract_dir)

    wasmtime_binary = _findWasmtimeBinary(extract_dir)

    if wasmtime_binary is None:
        return general.sysexit(
            "Error, failed to locate Wasmtime %s binary in '%s'."
            % (_wasmtime_version, archive_path)
        )

    deleteFile(wasmtime_path, must_exist=False)

    renameFile(
        source_filename=wasmtime_binary,
        dest_filename=wasmtime_path,
    )

    removeDirectory(
        path=extract_dir,
        logger=general,
        ignore_errors=False,
        extra_recommendation=None,
    )

    return wasmtime_path


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
