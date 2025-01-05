#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Variable declarations
Holds the information necessary to make C code declarations related to a variable.

"""

from contextlib import contextmanager

from .c_types.CTypeBooleans import CTypeBool
from .c_types.CTypeCFloats import CTypeCFloat
from .c_types.CTypeCLongs import CTypeCLong, CTypeCLongDigit
from .c_types.CTypeModuleDictVariables import CTypeModuleDictVariable
from .c_types.CTypeNuitkaBooleans import CTypeNuitkaBoolEnum
from .c_types.CTypeNuitkaInts import CTypeNuitkaIntOrLongStruct
from .c_types.CTypeNuitkaVoids import CTypeNuitkaVoidEnum
from .c_types.CTypePyObjectPointers import (
    CTypeCellObject,
    CTypePyObjectPtr,
    CTypePyObjectPtrPtr,
)


class VariableDeclaration(object):
    __slots__ = ("c_type", "code_name", "init_value", "heap_name", "maybe_unused")

    def __init__(self, c_type, code_name, init_value, heap_name):
        if c_type.startswith("NUITKA_MAY_BE_UNUSED"):
            self.c_type = c_type[21:]
            self.maybe_unused = True
        else:
            self.c_type = c_type
            self.maybe_unused = False

        self.code_name = code_name
        self.init_value = init_value
        self.heap_name = heap_name

    def makeCFunctionLevelDeclaration(self):
        pos = self.c_type.find("[")
        if pos != -1:
            lead_c_type = self.c_type[:pos]
            suffix_c_type = self.c_type[pos:]
        else:
            lead_c_type = self.c_type
            suffix_c_type = ""

        return "%s%s%s%s%s%s;" % (
            "NUITKA_MAY_BE_UNUSED " if self.maybe_unused else "",
            lead_c_type,
            " " if lead_c_type[-1] != "*" else "",
            self.code_name,
            "" if self.init_value is None else " = %s" % self.init_value,
            suffix_c_type,
        )

    def makeCStructDeclaration(self):
        c_type = self.c_type

        if "[" in c_type:
            array_decl = c_type[c_type.find("[") :]
            c_type = c_type[: c_type.find("[")]
        else:
            array_decl = ""

        return "%s%s%s%s;" % (
            c_type,
            " " if self.c_type[-1] != "*" else "",
            self.code_name,
            array_decl,
        )

    def makeCStructInit(self):
        if self.init_value is None:
            return None

        assert self.heap_name, repr(self)

        return "%s%s = %s;" % (
            ((self.heap_name + "->") if self.heap_name is not None else ""),
            self.code_name,
            self.init_value,
        )

    def getCType(self):
        # TODO: This ought to become unnecessary function
        # In the mean time, many cases: pylint: disable=too-many-return-statements

        c_type = self.c_type

        if c_type == "PyObject *":
            return CTypePyObjectPtr
        elif c_type == "struct Nuitka_CellObject *":
            return CTypeCellObject
        elif c_type == "PyObject **":
            return CTypePyObjectPtrPtr
        elif c_type == "nuitka_bool":
            return CTypeNuitkaBoolEnum
        elif c_type == "bool":
            return CTypeBool
        elif c_type == "nuitka_ilong":
            return CTypeNuitkaIntOrLongStruct
        elif c_type == "module_var":
            return CTypeModuleDictVariable
        elif c_type == "nuitka_void":
            return CTypeNuitkaVoidEnum
        elif c_type == "long":
            return CTypeCLong
        elif c_type == "nuitka_digit":
            return CTypeCLongDigit
        elif c_type == "double":
            return CTypeCFloat

        assert False, c_type

    def __str__(self):
        if self.heap_name:
            return "%s->%s" % (self.heap_name, self.code_name)
        else:
            return self.code_name

    def __repr__(self):
        return "<VariableDeclaration %s %s = %r>" % (
            self.c_type,
            self.code_name,
            self.init_value,
        )


class VariableStorage(object):
    __slots__ = (
        "heap_name",
        "variable_declarations_heap",
        "variable_declarations_main",
        "variable_declarations_closure",
        "variable_declarations_locals",
        "exception_variable_name",
    )

    def __init__(self, heap_name):
        self.heap_name = heap_name

        self.variable_declarations_heap = []
        self.variable_declarations_main = []
        self.variable_declarations_closure = []

        self.variable_declarations_locals = []

        self.exception_variable_name = None

    @contextmanager
    def withLocalStorage(self):
        """Local storage for only just during context usage.

        This is for automatic removal of that scope. These are supposed
        to be nestable eventually.

        """

        self.variable_declarations_locals.append([])

        yield

        self.variable_declarations_locals.pop()

    def getVariableDeclarationTop(self, code_name):
        for variable_declaration in self.variable_declarations_main:
            if variable_declaration.code_name == code_name:
                return variable_declaration

        for variable_declaration in self.variable_declarations_heap:
            if variable_declaration.code_name == code_name:
                return variable_declaration

        return None

    def getVariableDeclarationClosure(self, closure_index):
        return self.variable_declarations_closure[closure_index]

    def addFrameCacheDeclaration(self, frame_identifier):
        return self.addVariableDeclarationFunction(
            "static struct Nuitka_FrameObject *", "cache_%s" % frame_identifier, "NULL"
        )

    def makeCStructLevelDeclarations(self):
        return [
            variable_declaration.makeCStructDeclaration()
            for variable_declaration in self.variable_declarations_heap
        ]

    def makeCStructInits(self):
        return [
            variable_declaration.makeCStructInit()
            for variable_declaration in self.variable_declarations_heap
            if variable_declaration.init_value is not None
        ]

    def getExceptionVariableDescriptions(self):
        if self.exception_variable_name is None:
            self.exception_variable_name = (
                self.addVariableDeclarationTop(
                    "struct Nuitka_ExceptionPreservationItem",
                    "exception_state",
                    "Empty_Nuitka_ExceptionPreservationItem",
                ),
                self.addVariableDeclarationTop(
                    "NUITKA_MAY_BE_UNUSED int", "exception_lineno", "0"
                ),
            )

        return self.exception_variable_name

    def addVariableDeclarationLocal(self, c_type, code_name):
        result = VariableDeclaration(c_type, code_name, None, None)

        self.variable_declarations_locals[-1].append(result)

        return result

    def addVariableDeclarationClosure(self, c_type, code_name):
        result = VariableDeclaration(c_type, code_name, None, None)

        self.variable_declarations_closure.append(result)

        return result

    def addVariableDeclarationFunction(self, c_type, code_name, init_value):
        result = VariableDeclaration(c_type, code_name, init_value, None)

        self.variable_declarations_main.append(result)

        return result

    def addVariableDeclarationTop(self, c_type, code_name, init_value):
        result = VariableDeclaration(c_type, code_name, init_value, self.heap_name)

        if self.heap_name is not None:
            self.variable_declarations_heap.append(result)
        else:
            self.variable_declarations_main.append(result)

        return result

    def makeCLocalDeclarations(self):
        return [
            variable_declaration.makeCFunctionLevelDeclaration()
            for variable_declaration in self.variable_declarations_locals[-1]
        ]

    def makeCFunctionLevelDeclarations(self):
        return [
            variable_declaration.makeCFunctionLevelDeclaration()
            for variable_declaration in self.variable_declarations_main
        ]

    def getLocalPreservationDeclarations(self):
        result = []

        for variable_declarations_local in self.variable_declarations_locals:
            result.extend(variable_declarations_local)

        return result


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
