#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Download utilities and extract locally when allowed.

Mostly used on Windows, for dependency walker and ccache binaries.
"""

import os

from nuitka import Tracing
from nuitka.__past__ import urlretrieve
from nuitka.Progress import withNuitkaDownloadProgressBar

from .AppDirs import getCacheDir
from .FileOperations import (
    addFileExecutablePermission,
    deleteFile,
    getNormalizedPath,
    makePath,
    queryUser,
)


def getDownload(name, url, download_path):
    # requests api, spell-checker: ignore reporthook

    with withNuitkaDownloadProgressBar(desc="Download %s" % name) as reporthook:
        try:
            try:
                urlretrieve(url, download_path, reporthook=reporthook)
            except Exception:  # Any kind of error, pylint: disable=broad-except
                urlretrieve(
                    url.replace("https://", "http://"),
                    download_path,
                    reporthook=reporthook,
                )
        except KeyboardInterrupt:
            deleteFile(download_path, must_exist=False)

            raise


def getDownloadCacheName():
    return "downloads"


def getDownloadCacheDir():
    return getCacheDir(getDownloadCacheName())


def getCachedDownload(
    name,
    url,
    binary,
    unzip,
    flatten,
    is_arch_specific,
    specificity,
    message,
    reject,
    assume_yes_for_downloads,
):
    # Many branches to deal with.
    # pylint: disable=too-many-branches,too-many-locals

    nuitka_download_dir = getDownloadCacheDir()

    nuitka_download_dir = os.path.join(
        nuitka_download_dir, os.path.basename(binary).replace(".exe", "")
    )

    if is_arch_specific:
        nuitka_download_dir = os.path.join(nuitka_download_dir, is_arch_specific)

    if specificity:
        nuitka_download_dir = os.path.join(nuitka_download_dir, specificity)

    download_path = os.path.join(nuitka_download_dir, os.path.basename(url))
    exe_path = os.path.join(nuitka_download_dir, binary)

    makePath(nuitka_download_dir)

    if not os.path.isfile(download_path) and not os.path.isfile(exe_path):
        if assume_yes_for_downloads:
            reply = "yes"
        else:
            reply = queryUser(
                question="""\
%s

Is it OK to download and put it in '%s'.

Fully automatic, cached. Proceed and download"""
                % (message, nuitka_download_dir),
                choices=("yes", "no"),
                default="yes",
                default_non_interactive="no",
            )

        if reply != "yes":
            if reject is not None:
                Tracing.general.sysexit(reject)
        else:
            Tracing.general.info("Downloading '%s'." % url)

            try:
                getDownload(
                    name=name,
                    url=url,
                    download_path=download_path,
                )
            except Exception as e:  # Any kind of error, pylint: disable=broad-except
                Tracing.general.sysexit(
                    "Failed to download '%s' due to '%s'. Contents should manually be copied to '%s'."
                    % (url, e, download_path)
                )

    if unzip:
        if not os.path.isfile(exe_path) and os.path.isfile(download_path):
            Tracing.general.info("Extracting to '%s'" % exe_path)

            import zipfile

            try:
                # Not all Python versions support using it as a context manager, pylint: disable=consider-using-with
                zip_file = zipfile.ZipFile(download_path)

                for zip_info in zip_file.infolist():
                    if zip_info.filename[-1] == "/":
                        continue

                    if flatten:
                        zip_info.filename = os.path.basename(zip_info.filename)

                    zip_file.extract(zip_info, nuitka_download_dir)

            except (
                # Catching anything zip throws, pylint: disable=broad-except
                Exception
            ):
                Tracing.general.info(
                    "Problem with the downloaded zip file, deleting it."
                )

                deleteFile(binary, must_exist=False)
                deleteFile(download_path, must_exist=True)

                Tracing.general.sysexit(
                    "Error, need '%s' as extracted from '%s'." % (binary, url)
                )

        # Check success here, and make sure it's executable.
        if os.path.isfile(exe_path):
            addFileExecutablePermission(exe_path)
        else:
            if reject:
                Tracing.general.sysexit(reject)

            exe_path = None

        return getNormalizedPath(exe_path)
    else:
        return getNormalizedPath(download_path)


def getCachedDownloadedMinGW64(target_arch, assume_yes_for_downloads):
    # Large URLs, pylint: disable=line-too-long

    if target_arch == "x86_64":
        url = "https://github.com/brechtsanders/winlibs_mingw/releases/download/14.2.0posix-19.1.1-12.0.0-msvcrt-r2/winlibs-x86_64-posix-seh-gcc-14.2.0-llvm-19.1.1-mingw-w64msvcrt-12.0.0-r2.zip"
        binary = r"mingw64\bin\gcc.exe"
    elif target_arch == "x86":
        url = "https://github.com/brechtsanders/winlibs_mingw/releases/download/14.2.0posix-19.1.1-12.0.0-msvcrt-r2/winlibs-i686-posix-dwarf-gcc-14.2.0-llvm-19.1.1-mingw-w64msvcrt-12.0.0-r2.zip"
        binary = r"mingw32\bin\gcc.exe"
    elif target_arch == "arm64":
        return None
    else:
        assert False, target_arch

    gcc_binary = getCachedDownload(
        name="mingw64",
        url=url,
        is_arch_specific=target_arch,
        specificity=url.rsplit("/", 2)[1],
        binary=binary,
        unzip=True,
        flatten=False,
        message="Nuitka will use gcc from MinGW64 of winlibs to compile on Windows.",
        reject="Only this specific gcc is supported with Nuitka.",
        assume_yes_for_downloads=assume_yes_for_downloads,
    )

    return gcc_binary


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
