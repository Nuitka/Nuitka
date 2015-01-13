#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

""" Indentation of code.

Language independent, the amount of the spaces is not configurable, as it needs
to be the same as in templates.
"""

def _indentedCode(codes, count):
    return '\n'.join(
        ' ' * count + line
          if (line and not line.startswith('#')) else
        line for line in codes
    )

def indented(codes, level = 1, vert_block = False):
    if type(codes) is str:
        codes = codes.split('\n')

    if vert_block and codes != [""]:
        codes.insert(0, "")
        codes.append("")

    return _indentedCode(codes, level * 4)
