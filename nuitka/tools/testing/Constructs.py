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
""" Tools for construct tests.

"""


def generateConstructCases(construct_source_code):
    inside = False
    case = 0

    case_1 = []
    case_2 = []

    for line in construct_source_code.splitlines():
        if not inside or case == 1:
            case_1.append(line)
        else:
            case_1.append("")

        if "# construct_end" in line:
            inside = False

        if "# construct_alternative" in line:
            case = 2

        if not inside or case == 2:
            case_2.append(line)
        else:
            case_2.append("")

        if "# construct_begin" in line:
            inside = True
            case = 1

    return "\n".join(case_1), "\n".join(case_2)
