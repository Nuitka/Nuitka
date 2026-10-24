#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Utilities for acquiring a WASI SDK toolchain."""

import contextlib
import os
import tarfile

from nuitka.Tracing import general

from .Download import getDownload, getDownloadCacheDir, shouldDownload
from .FileOperations import (
    getNormalizedPathJoin,
    makeContainingPath,
    makePath,
    removeDirectory,
    renameDirectory,
    resetDirectory,
)
from .Utils import isLinux, isMacOS, isWin32Windows

_wasi_sdk_version = "20.0"


def _getWasiSDKArchiveName():
    if isLinux():
        return "wasi-sdk-%s-linux.tar.gz" % _wasi_sdk_version
    elif isMacOS():
        return "wasi-sdk-%s-macos.tar.gz" % _wasi_sdk_version
    elif isWin32Windows():
        return "wasi-sdk-%s.m-mingw.tar.gz" % _wasi_sdk_version

    return general.sysexit(
        "Error, WASI SDK %s is not available for this OS." % _wasi_sdk_version
    )


def _getWasiSDKURL():
    return (
        "https://github.com/WebAssembly/wasi-sdk/releases/download/wasi-sdk-20/%s"
        % (_getWasiSDKArchiveName())
    )


def _getExecutableName(name):
    if isWin32Windows():
        return name + ".exe"

    return name


def _isWasiSDKComplete(wasi_sdk_path):
    return (
        os.path.isfile(
            getNormalizedPathJoin(wasi_sdk_path, "bin", _getExecutableName("clang"))
        )
        and os.path.isfile(
            getNormalizedPathJoin(wasi_sdk_path, "bin", _getExecutableName("clang++"))
        )
        and os.path.isfile(
            getNormalizedPathJoin(wasi_sdk_path, "bin", _getExecutableName("llvm-ar"))
        )
        and os.path.isfile(
            getNormalizedPathJoin(
                wasi_sdk_path, "bin", _getExecutableName("llvm-ranlib")
            )
        )
        and os.path.isfile(
            getNormalizedPathJoin(
                wasi_sdk_path,
                "share",
                "wasi-sysroot",
                "lib",
                "wasm32-wasi",
                "libc.a",
            )
        )
    )


def checkWasiSDKPath(wasi_sdk_path):
    """Exit if the given directory is not a complete WASI SDK."""
    if not _isWasiSDKComplete(wasi_sdk_path):
        return general.sysexit(
            """\
Error, '%s' is not a complete WASI SDK %s installation."""
            % (wasi_sdk_path, _wasi_sdk_version)
        )


def _ensureDownloaded(url, download_path, description, assume_yes_for_downloads):
    if os.path.isfile(download_path):
        return

    makeContainingPath(download_path)

    if not shouldDownload(
        message="Nuitka will download %s for WASI compilation." % description,
        reject_message="Error, need %s for WASI compilation." % description,
        assume_yes_for_downloads=assume_yes_for_downloads,
        download_ok=True,
    ):
        return general.sysexit("Error, need %s for WASI compilation." % description)

    getDownload(
        name=description,
        url=url,
        download_path=download_path,
    )


def _findWasiSDKRoot(extract_dir):
    for root, _dirs, files in os.walk(extract_dir):
        if _getExecutableName("clang") in files and os.path.basename(root) == "bin":
            candidate = os.path.dirname(root)

            if _isWasiSDKComplete(candidate):
                return candidate

    return None


def _extractWasiSDK(archive_path, target_dir):
    resetDirectory(
        target_dir,
        logger=general,
        ignore_errors=False,
        extra_recommendation=None,
    )

    with contextlib.closing(tarfile.open(archive_path, "r:gz")) as tar:
        tar.extractall(target_dir)

    sdk_root = _findWasiSDKRoot(target_dir)

    if sdk_root is None:
        return general.sysexit(
            "Error, failed to locate WASI SDK %s in '%s'."
            % (_wasi_sdk_version, archive_path)
        )

    return sdk_root


def getWasiSDKPath(assume_yes_for_downloads):
    """Return the WASI SDK path, preferring an explicit --wasi-sdk-path value."""
    # Local import to avoid a circular dependency on Options.
    from nuitka.options.Options import getWasiSDKPath as getWasiSDKPathOption

    wasi_sdk_path = getWasiSDKPathOption()

    if wasi_sdk_path is not None:
        return wasi_sdk_path

    version_dir = getNormalizedPathJoin(
        getDownloadCacheDir(), "wasi-sdk", _wasi_sdk_version
    )
    sdk_path = getNormalizedPathJoin(version_dir, "sdk")

    if _isWasiSDKComplete(sdk_path):
        return sdk_path

    makePath(version_dir)

    archive_name = _getWasiSDKArchiveName()
    archive_path = getNormalizedPathJoin(version_dir, archive_name)
    extract_dir = getNormalizedPathJoin(version_dir, "extract")

    _ensureDownloaded(
        url=_getWasiSDKURL(),
        download_path=archive_path,
        description="WASI SDK %s" % _wasi_sdk_version,
        assume_yes_for_downloads=assume_yes_for_downloads,
    )

    sdk_root = _extractWasiSDK(archive_path, extract_dir)

    removeDirectory(
        path=sdk_path,
        logger=general,
        ignore_errors=False,
        extra_recommendation=None,
    )

    renameDirectory(
        source_path=sdk_root,
        dest_path=sdk_path,
    )

    removeDirectory(
        path=extract_dir,
        logger=general,
        ignore_errors=False,
        extra_recommendation=None,
    )

    if not _isWasiSDKComplete(sdk_path):
        return general.sysexit(
            "Error, failed to assemble WASI SDK %s." % _wasi_sdk_version
        )

    return sdk_path


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
