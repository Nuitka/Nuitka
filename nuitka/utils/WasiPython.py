#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Utilities for acquiring a WASI CPython prefix."""

import contextlib
import os
import re
import shutil
import tarfile

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.PythonVersions import (
    python_version_full,
    python_version_full_str,
    python_version_short,
    python_version_str,
)
from nuitka.Tracing import general

from .Download import (
    getDownload,
    getDownloadCacheDir,
    shouldDownload,
    withUrlOpen,
)
from .FileOperations import (
    getNormalizedPathJoin,
    makeContainingPath,
    makePath,
    removeDirectory,
    renameDirectory,
    renameFile,
    resetDirectory,
)
from .Json import loadJsonFromContents
from .Zipfiles import extractZipFile, getZipFile

_wasi_python_min_version = (3, 12, 0)
_wasi_python_releases_url = (
    "https://api.github.com/repos/brettcannon/cpython-wasi-build/releases?per_page=100"
)

_wasi_python_prefix = None


def _getVersionString(version):
    return ".".join(str(value) for value in version)


def _checkWasiPythonVersion(python_version_tuple):
    """Exit if the given Python version cannot be used for WASI targets."""
    if python_version_tuple < _wasi_python_min_version:
        return general.sysexit(
            "Error, WASI target requires Python 3.12 or newer, not %s."
            % python_version_full_str
        )


def _getWasiPythonReleases():
    try:
        with withUrlOpen(
            url=_wasi_python_releases_url,
            request_headers=None,
            timeout=30.0,
            allow_http_fallback=False,
        ) as response:
            releases = loadJsonFromContents(response.read())
    except Exception as e:  # pylint: disable=broad-except
        return general.sysexit(
            "Error, failed to download WASI Python release information: %s." % e
        )

    if not isinstance(releases, list):
        return general.sysexit("Error, invalid WASI Python release information.")

    return releases


def _getWasiPythonReleasesParsed():
    result = []

    for release in _getWasiPythonReleases():
        tag_name = release.get("tag_name")

        if tag_name is None:
            continue

        match = re.match(r"^v(\d+)\.(\d+)\.(\d+)$", tag_name)

        if match is None:
            continue

        version = tuple(int(match.group(index)) for index in (1, 2, 3))

        if version < _wasi_python_min_version:
            continue

        version_str = _getVersionString(version)
        runtime_url = None
        build_url = None

        for asset in release.get("assets", []):
            asset_name = asset.get("name", "")
            asset_url = asset.get("browser_download_url")

            if asset_name.startswith(
                "python-%s-wasi_sdk-" % version_str
            ) and asset_name.endswith(".zip"):
                runtime_url = asset_url
            elif asset_name.startswith(
                "_build-python-%s-wasi_sdk-" % version_str
            ) and asset_name.endswith(".zip"):
                build_url = asset_url

        if runtime_url is not None and build_url is not None:
            result.append(
                {
                    "version": version,
                    "version_str": version_str,
                    "runtime_url": runtime_url,
                    "build_url": build_url,
                }
            )

    if not result:
        return general.sysexit(
            "Error, no prebuilt WASI Python build for Python %s or newer found."
            % _getVersionString(_wasi_python_min_version[:2])
        )

    return result


def _getWasiPythonRelease():
    """Return the best prebuilt WASI Python release for the running Python."""
    _checkWasiPythonVersion(python_version_full)

    all_releases = _getWasiPythonReleasesParsed()
    candidates = [
        release
        for release in all_releases
        if release["version"][:2] == python_version_short
        and release["version"] <= python_version_full
    ]

    if not candidates:
        available = OrderedSet(
            release["version_str"]
            for release in sorted(all_releases, key=lambda release: release["version"])
        )

        return general.sysexit(
            """\
Error, no prebuilt WASI Python build available for Python %s or older in \
the %s series. Available: %s."""
            % (
                python_version_full_str,
                python_version_str,
                ", ".join(available),
            )
        )

    return max(candidates, key=lambda release: release["version"])


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


def _isWasiPythonPrefixComplete(prefix_dir, abi_version):
    return (
        os.path.isfile(
            getNormalizedPathJoin(
                prefix_dir,
                "include",
                "python" + abi_version,
                "Python.h",
            )
        )
        and os.path.isfile(
            getNormalizedPathJoin(
                prefix_dir,
                "lib",
                "libpython" + abi_version + ".a",
            )
        )
        and os.path.isdir(
            getNormalizedPathJoin(prefix_dir, "lib", "python" + abi_version)
        )
        and os.path.isfile(
            getNormalizedPathJoin(prefix_dir, "hacl", "Hacl_Hash_SHA2.c")
        )
    )


def _checkWasiPythonPrefix(prefix_dir):
    """Exit if the given directory is not a complete WASI Python prefix."""
    abi_version = python_version_str

    if not _isWasiPythonPrefixComplete(prefix_dir, abi_version):
        return general.sysexit(
            """\
Error, '%(prefix_dir)s' is not a complete WASI Python %(abi_version)s prefix. Need \
'include/python%(abi_version)s/Python.h', 'lib/libpython%(abi_version)s.a', \
'lib/python%(abi_version)s', and 'hacl/Hacl_Hash_SHA2.c'."""
            % {
                "prefix_dir": prefix_dir,
                "abi_version": abi_version,
            }
        )


def _extractRuntimeZip(runtime_zip, prefix_dir):
    with getZipFile(runtime_zip, error_exit=True, logger=general) as zip_file:
        zip_file.extractall(prefix_dir)


def _extractBuildZip(build_zip, prefix_dir, abi_version):
    def get_target_filename(member_name):
        if member_name == "pyconfig.h":
            return getNormalizedPathJoin(
                "include", "python" + abi_version, "pyconfig.h"
            )

        if member_name == "libpython" + abi_version + ".a":
            return getNormalizedPathJoin("lib", "libpython" + abi_version + ".a")

        if member_name.startswith("Modules/") and member_name.endswith(".a"):
            return getNormalizedPathJoin("lib", os.path.basename(member_name))

        return None

    extractZipFile(
        zip_path=build_zip,
        target_dir=prefix_dir,
        get_target_filename=get_target_filename,
        error_exit=True,
        logger=general,
    )


def _extractSourceFiles(source_tar, prefix_dir, abi_version):
    with contextlib.closing(tarfile.open(source_tar, "r:gz")) as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue

            if "/Include/" in member.name:
                target_name = getNormalizedPathJoin(
                    "include",
                    "python" + abi_version,
                    member.name.split("/Include/", 1)[1],
                )
            elif "/Modules/_hacl/" in member.name:
                target_name = getNormalizedPathJoin(
                    "hacl", member.name.split("/Modules/_hacl/", 1)[1]
                )
            else:
                continue

            if ".." in target_name.split("/"):
                continue

            target_path = getNormalizedPathJoin(prefix_dir, target_name)
            makeContainingPath(target_path)

            source = tar.extractfile(member)

            with open(target_path, "wb") as output:
                shutil.copyfileobj(source, output)


def _finalizePythonWasm(prefix_dir, abi_version):
    source_path = getNormalizedPathJoin(prefix_dir, "python.wasm")

    if not os.path.isfile(source_path):
        return

    target_path = getNormalizedPathJoin(
        prefix_dir, "bin", "python" + abi_version + ".wasm"
    )
    makeContainingPath(target_path)

    renameFile(
        source_filename=source_path,
        dest_filename=target_path,
    )


def getWasiPythonPrefix(assume_yes_for_downloads):
    """Return the WASI CPython prefix for the running Python version."""
    global _wasi_python_prefix  # singleton, pylint: disable=global-statement

    if _wasi_python_prefix is not None:
        return _wasi_python_prefix

    # Local import to avoid a circular dependency on Options.
    from nuitka.options.Options import getWasiPythonPrefixPath

    wasi_python_prefix = getWasiPythonPrefixPath()

    if wasi_python_prefix is not None:
        _wasi_python_prefix = wasi_python_prefix
        return wasi_python_prefix

    release = _getWasiPythonRelease()
    abi_version = python_version_str
    version_cache_dir = getNormalizedPathJoin(
        getDownloadCacheDir(), "wasi-python", release["version_str"]
    )
    makePath(version_cache_dir)
    prefix_dir = getNormalizedPathJoin(version_cache_dir, "prefix")

    if _isWasiPythonPrefixComplete(prefix_dir, abi_version):
        _wasi_python_prefix = prefix_dir
        return prefix_dir

    runtime_zip = getNormalizedPathJoin(
        version_cache_dir, os.path.basename(release["runtime_url"])
    )
    build_zip = getNormalizedPathJoin(
        version_cache_dir, os.path.basename(release["build_url"])
    )
    source_tar = getNormalizedPathJoin(
        version_cache_dir, "cpython-%s.tar.gz" % release["version_str"]
    )
    source_url = (
        "https://github.com/python/cpython/archive/refs/tags/v%s.tar.gz"
        % release["version_str"]
    )

    _ensureDownloaded(
        url=release["runtime_url"],
        download_path=runtime_zip,
        description="WASI Python %s runtime" % release["version_str"],
        assume_yes_for_downloads=assume_yes_for_downloads,
    )
    _ensureDownloaded(
        url=release["build_url"],
        download_path=build_zip,
        description="WASI Python %s build" % release["version_str"],
        assume_yes_for_downloads=assume_yes_for_downloads,
    )
    _ensureDownloaded(
        url=source_url,
        download_path=source_tar,
        description="CPython %s headers" % release["version_str"],
        assume_yes_for_downloads=assume_yes_for_downloads,
    )

    tmp_prefix_dir = prefix_dir + ".tmp"

    resetDirectory(
        tmp_prefix_dir,
        logger=general,
        ignore_errors=False,
        extra_recommendation=None,
    )

    _extractRuntimeZip(runtime_zip, tmp_prefix_dir)
    _extractBuildZip(build_zip, tmp_prefix_dir, abi_version)
    _extractSourceFiles(source_tar, tmp_prefix_dir, abi_version)
    _finalizePythonWasm(tmp_prefix_dir, abi_version)

    if not _isWasiPythonPrefixComplete(tmp_prefix_dir, abi_version):
        return general.sysexit(
            "Error, failed to assemble WASI Python %s prefix." % release["version_str"]
        )

    removeDirectory(
        path=prefix_dir,
        logger=general,
        ignore_errors=False,
        extra_recommendation=None,
    )

    renameDirectory(
        source_path=tmp_prefix_dir,
        dest_path=prefix_dir,
    )

    _wasi_python_prefix = prefix_dir
    return prefix_dir


def checkWasiPreconditions(wasi_python_prefix):
    """Exit if the requested WASI compilation is not usable."""
    _checkWasiPythonVersion(python_version_full)

    if wasi_python_prefix is not None:
        _checkWasiPythonPrefix(wasi_python_prefix)


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
