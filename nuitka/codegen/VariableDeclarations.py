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

class VariableDeclaration(object):
    __slots__ = ("c_type", "code_name", "init_value", "heap_name")

    def __init__(self, c_type, code_name, init_value, heap_name):
        self.c_type = c_type
        self.code_name = code_name
        self.init_value = init_value
        self.heap_name = heap_name

    def makeCFunctionLevelDeclaration(self):
        return "%s%s%s%s;" % (
            self.c_type,
            ' ' if self.c_type[-1] != '*' else "",
            self.code_name,
            "" if self.init_value is None else " = %s" % self.init_value
        )

    def makeCStructDeclaration(self):
        c_type = self.c_type

        if c_type.startswith("NUITKA_MAY_BE_UNUSED"):
            c_type = c_type[21:]

        return "%s%s%s;" % (
            c_type,
            ' ' if self.c_type[-1] != '*' else "",
            self.code_name
        )

    def makeCStructInit(self):
        if self.init_value is None:
            return None

        assert self.heap_name, repr(self)

        return "%s%s = %s;" % (
            ((self.heap_name + "->") if self.heap_name is not None else ""),
            self.code_name,
            self.init_value
        )

    def __str__(self):
        if self.heap_name:
            return "%s->%s" % (
                self.heap_name,
                self.code_name
            )
        else:
            return self.code_name

    def __repr__(self):
        return "<VariableDeclaration %s %s = %r>" % (
            self.c_type,
            self.code_name,
            self.init_value
        )


class VariableStorage(object):
    __slots__ = ("variable_declarations", "exception_variable_declarations", "parent")

    heap_name = None

    def __init__(self, parent):
        self.parent = parent

        self.variable_declarations = []

        self.exception_variable_declarations = None

    def add(self, variable_declaration):
        self.variable_declarations.append(variable_declaration)

    def getVariableDeclaration(self, code_name):
        for variable_declaration in self.variable_declarations:
            if variable_declaration.code_name == code_name:
                return variable_declaration

        if self.parent is not None:
            return self.parent.getVariableDeclaration(code_name)
        else:
            return None

    def addVariableDeclaration(self, c_type, code_name, init_value, level):
        if self.parent is not None and level != "function":
            result = self.parent.addVariableDeclaration(c_type, code_name, init_value, level)
        else:
            result = VariableDeclaration(
                c_type,
                code_name,
                init_value,
                self.heap_name
            )

            self.add(
                result,
            )

        return result

    def addFrameDeclaration(self, frame_identifier):
        self.addVariableDeclaration(
            "struct Nuitka_FrameObject *",
            frame_identifier,
            None,
            level = "top"
        )

    def addFrameCacheDeclaration(self, frame_identifier):
        self.addVariableDeclaration(
            "static struct Nuitka_FrameObject *",
            "cache_%s" % frame_identifier,
            "NULL",
            level = "function"
        )


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

    def makeCStringInits(self):
        return [
            variable_declaration.makeCStructInit()
            for variable_declaration in
            self.variable_declarations
            if variable_declaration.init_value is not None
        ]

    def getExceptionVariableDescriptions(self):
        if self.exception_variable_declarations is None:
            self.exception_variable_declarations = (
                self.addVariableDeclaration("PyObject *", "exception_type", "NULL", True),
                self.addVariableDeclaration("PyObject *", "exception_value", "NULL", True),
                self.addVariableDeclaration("PyTracebackObject *", "exception_tb", "NULL", True),
                self.addVariableDeclaration("NUITKA_MAY_BE_UNUSED int", "exception_lineno", '0', True)
            )

        return self.exception_variable_declarations


class VariableSubStorage(VariableStorage):
    """ Storage per statement or per expression.

        Keeps declarations that are within that scope only.
    """

    __slots__ = ()

    def __init__(self, parent):
        VariableStorage.__init__(
            self,
            parent = parent
        )

    def addVariableDeclaration(self, c_type, code_name, init_value, level):
        if level != "local":
            result = self.parent.addVariableDeclaration(c_type, code_name, init_value, level)
        else:
            result = VariableDeclaration(
                c_type,
                code_name,
                init_value,
                self.heap_name
            )

            self.add(
                result,
            )

        return result

    def getExceptionVariableDescriptions(self):
        return self.parent.getExceptionVariableDescriptions()


class VariableHeapStorage(VariableStorage):
    __slots__ = ("heap_name",)

    def __init__(self, heap_name):
        VariableStorage.__init__(
            self,
            parent = None
        )

        self.heap_name = heap_name
