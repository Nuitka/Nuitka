#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Utilities for private pip space to download packages into.

"""

import os
import subprocess
import sys

from nuitka.PythonVersions import getSitePackageCandidateNames

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


def tryDownloadPackageName(package_name, module_name, package_version):
    download_folder = getDownloadCopyFolder()

    site_packages_folder = _findDownloadSitePackagesDir(download_folder)

    if site_packages_folder is not None:
        candidate = os.path.join(site_packages_folder, module_name)

        if os.path.exists(candidate):
            return site_packages_folder

    if os.getenv("NUITKA_ASSUME_YES_FOR_DOWNLOADS") in ("1", "true", "yes"):
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
        candidate = os.path.join(site_packages_folder, module_name)

        if os.path.exists(candidate):
            return site_packages_folder


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
