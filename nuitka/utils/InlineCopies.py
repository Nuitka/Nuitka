#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Policies for locating inline copies."""

import os

from nuitka.PythonVersions import python_version


def _getInlineCopyBaseFolder():
    """Base folder for inline copies."""
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "build", "inline_copy")
    )


def getInlineCopyFolder(module_name):
    """Get the inline copy folder for a given name."""
    folder_name = os.path.join(_getInlineCopyBaseFolder(), module_name)

    candidate_27 = folder_name + "_27"
    candidate_35 = folder_name + "_35"

    # Use specific versions if needed.
    if python_version < 0x300 and os.path.exists(candidate_27):
        folder_name = candidate_27
    elif python_version < 0x360 and os.path.exists(candidate_35):
        folder_name = candidate_35

    return folder_name


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
