#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Variable declarations

Holds the information necessary to make C code declarations related to a variable.
"""

from collections import namedtuple

# TODO: Maybe have another place for this to live in.
VariableDeclarationBase = namedtuple(
    "VariableDeclaration",
    field_names = ("c_type", "code_name", "init_value")
)

class VariableDeclaration(VariableDeclarationBase):
    def makeCFunctionLevelDeclaration(self):
        return "%s%s%s%s;" % (
            self.c_type,
            ' ' if self.c_type[-1] != '*' else "",
            self.code_name,
            "" if self.init_value is None else " = %s" % self.init_value
        )
