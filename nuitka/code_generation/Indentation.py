#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Indentation of code.

Language independent, the amount of the spaces is not configurable, as it needs
to be the same as in templates.
"""

from nuitka.States import states


def indented(codes, level=4, vert_block=False):
    if states.is_unindented_generated_code:
        if type(codes) is not str:
            codes = "\n".join(codes)

        return codes

    if type(codes) is str:
        codes = codes.split("\n")

    if vert_block and codes != [""]:
        codes.insert(0, "")
        codes.append("")

    return "\n".join(
        " " * level + line if (line and line[0] != "#") else line for line in codes
    )


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
