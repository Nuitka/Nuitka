#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Utils module to provide helper for our common json operations."""

from __future__ import absolute_import

import json

from .FileOperations import getFileContents, openTextFile


def loadJsonFromFilename(filename):
    try:
        return json.loads(getFileContents(filename))
    except ValueError:
        return None


def writeJsonToFile(file_handle, contents, indent=2):
    json.dump(contents, file_handle, indent=indent, sort_keys=True)
    file_handle.write("\n")


def writeJsonToFilename(filename, contents, indent=2):
    with openTextFile(filename, "w") as output:
        writeJsonToFile(output, contents, indent=indent)


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
