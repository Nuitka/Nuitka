#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Windows MSI release tools.

"""

import sys

from nuitka.PythonVersions import getSupportedPythonVersions


def makeMsiCompatibleFilename(filename):
    filename = filename[:-4]

    for supported_version in getSupportedPythonVersions():
        filename = filename.replace("-py" + supported_version, "")

    filename = filename.replace("Nuitka32","Nuitka")
    filename = filename.replace("Nuitka64","Nuitka")

    parts = [
        filename,
        "py" + sys.version[:3].replace('.',""),
        "msi"
    ]

    return '.'.join(parts)
