#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Automatic formatting of JSON files.

"""

import os

from nuitka.utils.Download import getCachedDownload
from nuitka.utils.Execution import check_call
from nuitka.utils.FileOperations import addFileExecutablePermission
from nuitka.utils.Utils import getArchitecture, getOS

_biome_path = None


def getBiomeBinaryPath(assume_yes_for_downloads=False):
    """
    Downloads and returns the path to the biome executable.
    """
    # Many branches used to map OS and arch, pylint: disable=too-many-branches

    # singleton, pylint: disable=global-statement
    global _biome_path

    if _biome_path is not None:
        return _biome_path

    os_name = getOS()
    architecture = getArchitecture()

    if os_name == "Linux":
        if architecture == "x86_64":
            arch_name = "x64"
        elif architecture == "arm64":
            arch_name = "arm64"
        else:
            return None
        binary_name = "biome-linux-%s" % arch_name
    elif os_name == "Windows":
        if architecture == "x86_64":
            arch_name = "x64"
        elif architecture == "x86":
            arch_name = "ia32"
        elif architecture == "arm64":
            arch_name = "arm64"
        else:
            return None
        binary_name = "biome-win32-%s.exe" % arch_name
    elif os_name == "Darwin":
        if architecture == "x86_64":
            arch_name = "x64"
        elif architecture == "arm64":
            arch_name = "arm64"
        else:
            return None
        binary_name = "biome-darwin-%s" % arch_name
    else:
        return None

    version = "2.2.4"
    url = (
        "https://github.com/biomejs/biome/releases/download/%%40biomejs%%2Fbiome%%40%s/%s"
        % (
            version,
            binary_name,
        )
    )

    _biome_path = getCachedDownload(
        name="biome",
        url=url,
        is_arch_specific=getArchitecture(),
        specificity=version,
        binary=os.path.basename(url),
        unzip=False,
        flatten=False,
        message="Nuitka will make use of 'biome' to format JSON files.",
        reject=None,
        assume_yes_for_downloads=assume_yes_for_downloads,
        download_ok=True,
    )

    addFileExecutablePermission(_biome_path)

    return _biome_path


def formatJsonFile(filename, assume_yes_for_downloads):
    # Many tools work on files, and when they do, they need to be told to
    # treat it as a JSON file.
    biome_path = getBiomeBinaryPath(assume_yes_for_downloads=assume_yes_for_downloads)

    if biome_path:
        command = (
            biome_path,
            "format",
            "--write",
            "--json-formatter-expand=always",
            "--json-formatter-indent-style=space",
            filename,
        )

        check_call(command)


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
