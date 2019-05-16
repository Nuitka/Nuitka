#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" This tool is generating code variants for helper codes from Jinka templates.

"""

from __future__ import print_function

import os
from abc import ABCMeta, abstractmethod

import jinja2

from nuitka.tools.quality.autoformat.Autoformat import cleanupClangFormat


class TypeMetaClass(ABCMeta):
    pass


# For Python2/3 compatible source, we create a base class that has the metaclass
# used and doesn't require making a choice.
TypeMetaClassBase = TypeMetaClass("TypeMetaClassBase", (object,), {})


class TypeDescBase(TypeMetaClassBase):
    # To be overloaded
    type_name = None
    type_desc = None
    type_decl = None

    python_requirement = None

    def __init__(self):
        assert self.type_name
        assert self.type_desc
        assert self.type_decl

    @classmethod
    def getHelperCodeName(cls):
        return cls.type_name.upper()

    @classmethod
    def getVariableDecl(cls, variable_name):
        if cls.type_decl.endswith("*"):
            return cls.type_decl + variable_name
        else:
            return cls.type_decl + " " + variable_name

    @classmethod
    def getCheckValueCode(cls, operand):
        return "CHECK_OBJECT(%s);" % operand

    @classmethod
    def getTypeValueExpression(cls, operand):
        return "Py_TYPE(%s)" % operand

    @abstractmethod
    def getNewStyleNumberTypeCheckExpression(self, operand):
        pass

    def canTypeCoerceObjects(self, left):
        if left is self and left is not object_desc:
            return "0"

        # TODO: Provide hook for float to say it can do int.
        return (
            "1"
            if self.getSlotValueCheckExpression("type2", "nb_coerce") != "false"
            else "0"
        )

    @classmethod
    def getIntCheckExpression(cls, operand):
        if cls.type_name == "int":
            return "1"
        elif cls.type_name == "object":
            return "PyInt_CheckExact(%s)" % operand
        else:
            return "0"

    def getTypeIdenticalCheckExpression(self, other, operand1, operand2):
        if self is object_desc or other is object_desc:
            return "%s == %s" % (operand1, operand2)
        elif self is other:
            return "1"
        else:
            return "0"

    @staticmethod
    def getRealSubTypeCheckCode(right, operand2, operand1):
        if right is object_desc:
            return "PyType_IsSubtype(%s, %s)" % (operand2, operand1)
        else:
            return 0

    @abstractmethod
    def hasSlot(self, slot):
        pass

    def _getSlotValueExpression(self, operand, slot):
        if slot.startswith("nb_"):
            return "(%s) ? %s : NULL" % (
                operand
                + "->tp_as_number != NULL && "
                + self.getNewStyleNumberTypeCheckExpression(operand),
                operand + "->tp_as_number->" + slot,
            )

        elif slot.startswith("sq_"):
            return "%s ? %s : NULL" % (
                operand + "->tp_as_sequence" + " != NULL",
                operand + "->tp_as_sequence->" + slot,
            )
        else:
            assert False, slot

    def getSlotValueExpression(self, operand, slot):
        if not self.hasSlot(slot):
            return "NULL"

        return self._getSlotValueExpression(operand, slot)

    def getSlotValueCheckExpression(self, operand, slot):
        # Virtual method, pylint: disable=unused-argument
        return "true" if self.hasSlot(slot) else "false"

    def getRaiseUnsupportedTypeError(self, operation, other, operand1, operand2):
        args = []

        if self is object_desc:
            args.append("%s->tp_name" % operand1)
        if other is object_desc:
            args.append("%s->tp_name" % operand2)

        if args:
            args = ", " + ", ".join(args)
        else:
            args = ""

        return """\
PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for %s: '%s' and '%s'"%s);
return NULL;""" % (
            operation,
            "%s" if self is object_desc else self.type_name,
            "%s" if other is object_desc else other.type_name,
            args,
        )

    def getSameTypeSpecializationCode(self, other, slot, operand1, operand2):
        cand = self if self is not object_desc else other

        if cand is object_desc:
            assert cand is not int_desc

            return ""

        helper_name = cand.getHelperCodeName()

        # Special case "+" for sequence concats.
        if slot == "nb_add" and not cand.hasSlot(slot) and cand.hasSlot("sq_concat"):
            return cand.getSqConcatSlotSpecializationCode(
                cand, "sq_concat", operand1, operand2
            )

        return "return SLOT_%s_%s_%s(%s, %s);" % (
            slot,
            helper_name,
            helper_name,
            operand1,
            operand2,
        )

    @abstractmethod
    def getSqConcatSlotSpecializationCode(self, other, slot, operand1, operand2):
        pass


class ConcreteTypeBase(TypeDescBase):
    type_decl = "PyObject *"

    def _getSlotValueExpression(self, operand, slot):
        if slot.startswith("nb_"):
            return self.getTypeValueExpression(operand)[1:] + ".tp_as_number->" + slot
        elif slot.startswith("sq_"):
            return self.getTypeValueExpression(operand)[1:] + ".tp_as_sequence->" + slot
        else:
            assert False, slot

    def getCheckValueCode(self, operand):
        return """\
CHECK_OBJECT(%(operand)s);
assert(%(type_name)s_CheckExact(%(operand)s));
#if PYTHON_VERSION < 300
assert(%(is_newstyle)sNEW_STYLE_NUMBER(%(operand)s));
#endif""" % {
            "operand": operand,
            "type_name": self.getTypeValueExpression(operand)[1:].split("_")[0],
            "is_newstyle": ""
            if self.getNewStyleNumberTypeCheckExpression(operand) == "1"
            else "!",
        }

    @abstractmethod
    def getTypeValueExpression(self, operand):
        pass

    def getSqConcatSlotSpecializationCode(self, other, slot, operand1, operand2):
        if not self.hasSlot(slot):
            return ""

        # TODO: Use second type eventually when we specialize those too.
        return "return SLOT_%s_%s_%s(%s, %s);" % (
            slot,
            self.getHelperCodeName(),
            other.getHelperCodeName(),
            operand1,
            operand2,
        )


class IntDesc(ConcreteTypeBase):
    type_name = "int"
    type_desc = "Python2 'int'"

    python_requirement = "PYTHON_VERSION < 300"

    @classmethod
    def getTypeValueExpression(cls, operand):
        return "&PyInt_Type"

    @classmethod
    def getNewStyleNumberTypeCheckExpression(cls, operand):
        return "1"

    def hasSlot(self, slot):
        if slot.startswith("nb_"):
            return True
        elif slot.startswith("sq_"):
            return False
        else:
            assert False


int_desc = IntDesc()


class StrDesc(ConcreteTypeBase):
    type_name = "str"
    type_desc = "Python2 'str'"

    python_requirement = "PYTHON_VERSION < 300"

    @classmethod
    def getTypeValueExpression(cls, operand):
        return "&PyString_Type"

    @classmethod
    def getNewStyleNumberTypeCheckExpression(cls, operand):
        return "1"

    def hasSlot(self, slot):
        if slot.startswith("nb_"):
            return "slot" == "nb_remainder"
        elif slot.startswith("sq_"):
            return "ass" not in slot
        else:
            assert False, slot


str_desc = StrDesc()


class UnicodeDesc(ConcreteTypeBase):
    type_name = "UNICODE"
    type_desc = "Python2 'unicode', Python3 'str'"

    @classmethod
    def getTypeValueExpression(cls, operand):
        return "&PyUnicode_Type"

    @classmethod
    def getCheckValueCode(cls, operand):
        return """\
CHECK_OBJECT(%(operand)s);
assert(PyUnicode_CheckExact(%(operand)s));
assert(NEW_STYLE_NUMBER(%(operand)s));""" % {
            "operand": operand
        }

    @classmethod
    def getNewStyleNumberTypeCheckExpression(cls, operand):
        return "1"

    def hasSlot(self, slot):
        if slot.startswith("nb_"):
            return "slot" == "nb_remainder"
        elif slot.startswith("sq_"):
            return "ass" not in slot
        else:
            assert False, slot


unicode_desc = UnicodeDesc()


class FloatDesc(ConcreteTypeBase):
    type_name = "float"
    type_desc = "Python 'float'"

    @classmethod
    def getTypeValueExpression(cls, operand):
        return "&PyFloat_Type"

    def hasSlot(self, slot):
        if slot.startswith("nb_"):
            return True
        elif slot.startswith("sq_"):
            return False
        else:
            assert False, slot

    @classmethod
    def getNewStyleNumberTypeCheckExpression(cls, operand):
        return "1"


float_desc = FloatDesc()


class TupleDesc(ConcreteTypeBase):
    type_name = "tuple"
    type_desc = "Python 'tuple'"

    @classmethod
    def getTypeValueExpression(cls, operand):
        return "&PyTuple_Type"

    def hasSlot(self, slot):
        if slot.startswith("nb_"):
            return False
        elif slot.startswith("sq_"):
            return "ass" not in slot
        else:
            assert False, slot

    @classmethod
    def getNewStyleNumberTypeCheckExpression(cls, operand):
        return "0"


tuple_desc = TupleDesc()


class ListDesc(ConcreteTypeBase):
    type_name = "list"
    type_desc = "Python 'list'"

    @classmethod
    def getTypeValueExpression(cls, operand):
        return "&PyList_Type"

    def hasSlot(self, slot):
        if slot.startswith("nb_"):
            return False
        elif slot.startswith("sq_"):
            return True
        else:
            assert False, slot

    @classmethod
    def getNewStyleNumberTypeCheckExpression(cls, operand):
        return "0"


list_desc = ListDesc()


class BytesDesc(ConcreteTypeBase):
    type_name = "bytes"
    type_desc = "Python3 'bytes'"

    python_requirement = "PYTHON_VERSION >= 300"

    @classmethod
    def getTypeValueExpression(cls, operand):
        return "&PyBytes_Type"

    def hasSlot(self, slot):
        if slot.startswith("nb_"):
            return "slot" == "nb_remainder"
        elif slot.startswith("sq_"):
            return "ass" not in slot and slot != "sq_slice"
        else:
            assert False, slot

    @classmethod
    def getNewStyleNumberTypeCheckExpression(cls, operand):
        return "0"


bytes_desc = BytesDesc()


class LongDesc(ConcreteTypeBase):
    type_name = "long"
    type_desc = "Python2 'long', Python3 'int'"

    @classmethod
    def getTypeValueExpression(cls, operand):
        return "&PyLong_Type"

    def hasSlot(self, slot):
        if slot.startswith("nb_"):
            return True
        elif slot.startswith("sq_"):
            return False
        else:
            assert False

    @classmethod
    def getNewStyleNumberTypeCheckExpression(cls, operand):
        return "1"


long_desc = LongDesc()


class ObjectDesc(TypeDescBase):
    type_name = "object"
    type_desc = "Any Python object"
    type_decl = "PyObject *"

    def hasSlot(self, slot):
        # Don't want to get asked, we cannot know.
        assert False

    def getNewStyleNumberTypeCheckExpression(self, operand):
        return "NEW_STYLE_NUMBER_TYPE(%s)" % operand

    def getSlotValueExpression(self, operand, slot):
        # Always check.
        return self._getSlotValueExpression(operand, slot)

    def getSlotValueCheckExpression(self, operand, slot):
        return "(%s) != NULL" % self._getSlotValueExpression(operand, slot)

    def getSqConcatSlotSpecializationCode(self, other, slot, operand1, operand2):
        return ""


object_desc = ObjectDesc()


class CLongDesc(TypeDescBase):
    type_name = "clong"
    type_desc = "C platform long value"
    type_decl = "long"

    @classmethod
    def getCheckValueCode(cls, operand):
        return ""

    @classmethod
    def getTypeValueExpression(cls, operand):
        return "NULL"

    @classmethod
    def getNewStyleNumberTypeCheckExpression(cls, operand):
        return "0"

    def hasSlot(self, slot):
        return False

    def getSqConcatSlotSpecializationCode(self, other, slot, operand1, operand2):
        assert False


clong_desc = CLongDesc()


env = jinja2.Environment(
    loader=jinja2.PackageLoader("nuitka.tools.specialize", "templates"),
    trim_blocks=True,
    lstrip_blocks=True,
)

types = (
    int_desc,
    str_desc,
    unicode_desc,
    float_desc,
    tuple_desc,
    list_desc,
    bytes_desc,
    long_desc,
    object_desc,
)


def makeHelpersBinaryOperationAdd(emit_h, emit_c, emit):
    binary_operation_add_template = env.get_template("HelperOperationBinaryAdd.c.j2")

    emit('/* C helpers for type specialized "+" (Add) operations */')
    emit()

    def emitCode(left, right):
        code = binary_operation_add_template.render(left=left, right=right)

        emit_c(code)
        emit_h("extern " + code.splitlines()[0].replace(" {", ";"))

    for left in types[:-1]:
        if left.python_requirement:
            emit("#if %s" % left.python_requirement)
            emit()

        emit(
            '/* Code referring to "%s" corresponds to %s. */'
            % (left.getHelperCodeName(), left.type_desc)
        )
        emit()

        emitCode(left=object_desc, right=left)

        for right in [object_desc, left]:
            emit()
            emitCode(left=left, right=right)

        if left.python_requirement:
            emit()
            emit("#endif")

    emit()
    emitCode(left=float_desc, right=long_desc)

    emit()
    emitCode(left=long_desc, right=float_desc)

    emit(
        '/* Code referring to "%s" corresponds to %s. */'
        % (object_desc.getHelperCodeName(), object_desc.type_desc)
    )
    emit()
    emitCode(left=object_desc, right=object_desc)

    if False:  # TODO, pylint: disable=using-constant-test
        emit(
            '/* Code referring to "%s" corresponds to %s. */'
            % (clong_desc.getHelperCodeName(), clong_desc.type_desc)
        )
        emit()
        emit(binary_operation_add_template.render(left=long_desc, right=clong_desc))


def main():
    filename_c = "nuitka/build/static_src/HelpersOperationBinaryAdd.c"
    filename_h = "nuitka/build/include/nuitka/helper/operations_binary_add.h"

    def emitGenerationWarning(emit):
        emit("/* WARNING, this code is GENERATED. Modify the template instead! */")

    with open(filename_c, "w") as output_c:
        with open(filename_h, "w") as output_h:

            def writeline(output, *args):
                if not args:
                    output.write("\n")
                elif len(args) == 1:
                    output.write(args[0] + "\n")
                else:
                    assert False, args

            def emit_h(*args):
                writeline(output_h, *args)

            def emit_c(*args):
                writeline(output_c, *args)

            def emit(*args):
                emit_h(*args)
                emit_c(*args)

            emitGenerationWarning(emit_h)
            emitGenerationWarning(emit_c)

            emit_c(
                '#include "%s"' % os.path.basename(filename_c).replace(".c", "Utils.c")
            )

            makeHelpersBinaryOperationAdd(emit_h, emit_c, emit)

    cleanupClangFormat(filename_c)
    cleanupClangFormat(filename_h)


if __name__ == "__main__":
    main()
