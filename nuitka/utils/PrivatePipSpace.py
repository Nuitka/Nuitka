#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Utilities for private pip space to download packages into."""

import os
import subprocess
import sys

from nuitka.PythonVersions import getSitePackageCandidateNames

from .Download import shouldDownload
from .Execution import getExecutablePath
from .FileOperations import getNormalizedPathJoin
from .InlineCopies import getDownloadCopyFolder


def _findDownloadSitePackagesDir(download_folder):
    for root, dirnames, _filenames in os.walk(download_folder):
        found_candidate = None
        for candidate in getSitePackageCandidateNames():
            if candidate in dirnames:
                # Unclear which one to use.
                if found_candidate is not None:
                    return

                found_candidate = candidate

        if found_candidate:
            return os.path.join(root, found_candidate)


def tryDownloadPackageName(
    package_name, module_name, package_version, assume_yes_for_downloads
):
    download_folder = getDownloadCopyFolder()

    site_packages_folder = _findDownloadSitePackagesDir(download_folder)

    if site_packages_folder is not None:
        candidate = os.path.join(site_packages_folder, module_name)

        if os.path.exists(candidate):
            return site_packages_folder

    if shouldDownload(
        message="Nuitka depends on '%s' to compile code, it is recommended."
        % package_name,
        reject="Nuitka needs to use '%s'." % package_name,
        assume_yes_for_downloads=assume_yes_for_downloads,
        download_ok=True,
    ):
        if package_version is not None:
            package_spec = "%s==%s" % (package_name, package_version)
        else:
            package_spec = package_name

        exit_code = subprocess.call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-warn-script-location",
                "--root",
                download_folder,
                package_spec,
            ],
            shell=False,
        )

        if exit_code != 0:
            return None

        if site_packages_folder is None:
            site_packages_folder = _findDownloadSitePackagesDir(download_folder)

    if site_packages_folder is not None:
        candidate = getNormalizedPathJoin(site_packages_folder, module_name)

        if os.path.exists(candidate):
            return site_packages_folder


def getZigBinaryPath(assume_yes_for_downloads):
    download_folder = getDownloadCopyFolder()

    # Potential bin paths in the private pip space
    candidate_bin_paths = [
        os.path.join(download_folder, "bin"),
        os.path.join(download_folder, "usr", "bin"),
        os.path.join(download_folder, "usr", "local", "bin"),
    ]

    if os.name == "nt":
        candidate_bin_paths.append(os.path.join(download_folder, "Scripts"))

    # Construct an extra_dir for search
    extra_dir = os.pathsep.join(candidate_bin_paths)

    zig_exe_path = getExecutablePath("zig", extra_dir=extra_dir)

    if zig_exe_path is not None:
        return zig_exe_path

    # Download, avoiding to use the result, which is the site-packages
    # folder, spell-checker: ignore ziglang
    # Download, avoiding to use the result, which is the site-packages
    # folder, spell-checker: ignore ziglang
    site_packages_folder = tryDownloadPackageName(
        "ziglang",
        "ziglang",
        None,
        assume_yes_for_downloads=assume_yes_for_downloads,
    )

    if site_packages_folder:
        zig_exe_path = getNormalizedPathJoin(site_packages_folder, "ziglang", "zig")

        if os.name == "nt":
            zig_exe_path += ".exe"

        if os.path.exists(zig_exe_path):
            return zig_exe_path

    return None


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
