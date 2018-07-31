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

    def makeCStructDeclaration(self):
        return "%s%s%s;" % (
            self.c_type,
            ' ' if self.c_type[-1] != '*' else "",
            self.code_name
        )


class VariableStorage(object):
    def __init__(self):
        self.variable_declarations = []

    def add(self, variable_declaration, top_level):
        # This is top level, pylint: disable=unused-argument
        self.variable_declarations.append(variable_declaration)

    def remove(self, code_name):
        self.variable_declarations = [
            variable_declaration
            for variable_declaration in self.variable_declarations
            if variable_declaration.code_name != code_name
        ]

    def extend(self, iterable):
        self.variable_declarations.extend(iterable)

    def makeCFunctionLevelDeclarations(self):
        return [
            variable_declaration.makeCFunctionLevelDeclaration()
            for variable_declaration in
            self.variable_declarations
        ]

    def makeCStructDeclarations(self):
        return [
            variable_declaration.makeCStructDeclaration()
            for variable_declaration in
            self.variable_declarations
        ]



class VariableSubStorage(VariableStorage):
    def __init__(self, parent):
        VariableStorage.__init__(self)

        self.parent = parent

    def add(self, variable_declaration, top_level):
        if top_level:
            self.parent.add(variable_declaration, True)
        else:
            self.variable_declarations.append(variable_declaration)
