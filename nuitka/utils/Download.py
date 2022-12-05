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
""" Download utilities and extract locally when allowed.

Mostly used on Windows, for dependency walker and ccache binaries.
"""

import os

from nuitka import Tracing
from nuitka.__past__ import raw_input, urlretrieve

from .AppDirs import getCacheDir
from .FileOperations import addFileExecutablePermission, deleteFile, makePath


def getCachedDownload(
    url,
    binary,
    flatten,
    is_arch_specific,
    specificity,
    message,
    reject,
    assume_yes_for_downloads,
):
    # Many branches to deal with.
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements

    nuitka_download_dir = os.path.join(getCacheDir(), "downloads")

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
            reply = "y"
        else:
            Tracing.printLine(
                """\
%s

Is it OK to download and put it in '%s'.

No installer needed, cached, one time question.

Proceed and download? [Yes]/No """
                % (message, nuitka_download_dir)
            )
            Tracing.flushStandardOutputs()

            try:
                reply = raw_input()
            except EOFError:
                reply = "no"

        if reply.lower() in ("no", "n"):
            if reject is not None:
                Tracing.general.sysexit(reject)
        else:
            Tracing.general.info("Downloading '%s'." % url)

            try:
                urlretrieve(url, download_path)
            except Exception as e:  # Any kind of error, pylint: disable=broad-except
                try:
                    urlretrieve(url.replace("https://", "http://"), download_path)
                except Exception:  # Any kind of error, pylint: disable=broad-except
                    Tracing.general.sysexit(
                        "Failed to download '%s' due to '%s'. Contents should manually be copied to '%s'."
                        % (url, e, download_path)
                    )

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

        except Exception:  # Catching anything zip throws, pylint: disable=broad-except
            Tracing.general.info("Problem with the downloaded zip file, deleting it.")

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

    return exe_path


def getCachedDownloadedMinGW64(target_arch, assume_yes_for_downloads):
    # Large URLs, pylint: disable=line-too-long

    if target_arch == "x86_64":
        url = "https://github.com/brechtsanders/winlibs_mingw/releases/download/11.3.0-14.0.3-10.0.0-msvcrt-r3/winlibs-x86_64-posix-seh-gcc-11.3.0-llvm-14.0.3-mingw-w64msvcrt-10.0.0-r3.zip"
        binary = r"mingw64\bin\gcc.exe"
    else:
        url = "https://github.com/brechtsanders/winlibs_mingw/releases/download/11.3.0-14.0.3-10.0.0-msvcrt-r3/winlibs-i686-posix-dwarf-gcc-11.3.0-llvm-14.0.3-mingw-w64msvcrt-10.0.0-r3.zip"
        binary = r"mingw32\bin\gcc.exe"

    gcc_binary = getCachedDownload(
        url=url,
        is_arch_specific=target_arch,
        specificity=url.rsplit("/", 2)[1],
        binary=binary,
        flatten=False,
        message="Nuitka will use gcc from MinGW64 of winlibs to compile on Windows.",
        reject="Only this specific gcc is supported with Nuitka.",
        assume_yes_for_downloads=assume_yes_for_downloads,
    )

    return gcc_binary
