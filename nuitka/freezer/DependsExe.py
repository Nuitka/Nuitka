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

from nuitka.Options import assumeYesForDownloads
from nuitka.utils.Download import getCachedDownload
from nuitka.utils.Utils import getArchitecture


def getDependsExePath():
    """Return the path of depends.exe (for Windows).

    Will prompt the user to download if not already cached in AppData
    directory for Nuitka.
    """
    if getArchitecture() == "x86":
        depends_url = "http://dependencywalker.com/depends22_x86.zip"
    else:
        depends_url = "http://dependencywalker.com/depends22_x64.zip"

    return getCachedDownload(
        url=depends_url,
        is_arch_specific=True,
        binary="depends.exe",
        flatten=True,
        specifity="",  # Note: If there ever was an update, put version here.
        message="""\
Nuitka will make use of Dependency Walker (http://dependencywalker.com) tool
to analyze the dependencies of Python extension modules.""",
        reject="Nuitka does not work in --standalone on Windows without.",
        assume_yes_for_downloads=assumeYesForDownloads(),
    )
