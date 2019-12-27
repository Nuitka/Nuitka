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
""" This tool is generating code variants for helper codes from Jinja templates.

"""

from __future__ import print_function

import os
from abc import abstractmethod

import jinja2

import nuitka.codegen.OperationCodes
from nuitka.__past__ import getMetaClassBase
from nuitka.tools.quality.autoformat.Autoformat import autoformat


class TypeDescBase(getMetaClassBase("Type")):
    # To be overloaded
    type_name = None
    type_desc = None
    type_decl = None

    python_requirement = None

    def __init__(self):
        assert self.type_name
        assert self.type_desc
        assert self.type_decl

    def __repr__(self):
        return "<%s %s %s>" % (self.__class__.__name__, self.type_name, self.type_desc)

    @classmethod
    def getHelperCodeName(cls):
        return cls.type_name.upper()

    @classmethod
    def getTypeName2(cls):
        return cls.type_name

    @classmethod
    def getTypeName3(cls):
        return cls.type_name

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

    @staticmethod
    def needsIndexConversion():
        return True

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

    def getIndexCheckExpression(self, operand):
        if self.hasSlot("nb_index"):
            return "1"
        elif self.type_name == "object":
            return "PyIndex_Check(%s)" % operand
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

    def getSlotComparisonEqualExpression(self, right, operand1, operand2):
        if right is object_desc or self is object_desc:
            return "%s == %s" % (operand1, operand2)
        else:
            return "0"

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

    @staticmethod
    def getSlotType(slot):
        if slot == "nb_power":
            return "ternaryfunc"
        else:
            return "binaryfunc"

    @staticmethod
    def getSlotCallExpression(nb_slot, slot_var, operand1, operand2):
        if nb_slot == "nb_power":
            return "%s(%s, %s, Py_None)" % (slot_var, operand1, operand2)
        else:
            return "%s(%s, %s)" % (slot_var, operand1, operand2)

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

        def formatOperation(operation):
            if operation == "%":
                return "%%"
            elif operation == "**":
                return "** or pow()"
            else:
                return operation

        if (
            self.getTypeName2() != self.getTypeName3()
            or other.getTypeName2() != other.getTypeName3()
        ):
            return """\
#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for %s: '%s' and '%s'"%s);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for %s: '%s' and '%s'"%s);
#endif
return NULL;""" % (
                formatOperation(operation),
                "%s" if self is object_desc else self.getTypeName2(),
                "%s" if other is object_desc else other.getTypeName2(),
                args,
                formatOperation(operation),
                "%s" if self is object_desc else self.getTypeName3(),
                "%s" if other is object_desc else other.getTypeName3(),
                args,
            )
        else:
            return """\
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for %s: '%s' and '%s'"%s);
    return NULL;""" % (
                formatOperation(operation),
                "%s" if self is object_desc else self.getTypeName2(),
                "%s" if other is object_desc else other.getTypeName2(),
                args,
            )

    def getSameTypeSpecializationCode(
        self, other, nb_slot, sq_slot, operand1, operand2
    ):
        # Many cases, pylint: disable=too-many-branches,too-many-return-statements

        cand = self if self is not object_desc else other

        if cand is object_desc:
            return ""

        # Special case for sequence concats/repeats.
        if sq_slot is not None and not cand.hasSlot(nb_slot) and cand.hasSlot(sq_slot):
            slot = sq_slot
        else:
            slot = nb_slot

        if slot == "sq_repeat":
            if cand in (
                list_desc,
                tuple_desc,
                set_desc,
                dict_desc,
                unicode_desc,
                str_desc,
                bytes_desc,
            ):
                # No repeat with themselves.
                return ""

        if slot == "nb_remainder":
            if cand in (list_desc, tuple_desc, set_desc, dict_desc):
                return ""

        if slot == "nb_multiply":
            if cand in (
                str_desc,
                bytes_desc,
                list_desc,
                tuple_desc,
                set_desc,
                dict_desc,
            ):
                return ""

        if slot == "nb_add":
            # Tuple and list, etc. use sq_concat.
            # TODO: What about unicode_desc
            if cand in (
                str_desc,
                bytes_desc,
                tuple_desc,
                list_desc,
                set_desc,
                dict_desc,
            ):
                return ""

        if slot in ("nb_and", "nb_or", "nb_xor"):
            if cand in (
                str_desc,
                bytes_desc,
                unicode_desc,
                list_desc,
                tuple_desc,
                dict_desc,
            ):
                return ""

        if slot in ("nb_lshift", "nb_rshift"):
            if cand in (
                str_desc,
                bytes_desc,
                unicode_desc,
                tuple_desc,
                list_desc,
                set_desc,
                dict_desc,
            ):
                return ""

        # Nobody has it.
        if slot == "nb_matrix_multiply":
            return ""

        # We sometimes fake these, e.g. for CLONG. Maybe we should make it more
        # distinct function names in those cases and use cand.hasSlot there.

        return "return SLOT_%s_%s_%s(%s, %s);" % (
            slot,
            cand.getHelperCodeName(),
            cand.getHelperCodeName(),
            operand1,
            operand2,
        )

    def getSimilarTypeSpecializationCode(self, other, nb_slot, operand1, operand2):
        return "return SLOT_%s_%s_%s(%s, %s);" % (
            nb_slot,
            self.getHelperCodeName(),
            other.getHelperCodeName(),
            operand1,
            operand2,
        )

    def getTypeSpecializationCode(self, other, nb_slot, sq_slot, operand1, operand2):
        if self is object_desc or other is object_desc:
            return ""

        if self is other:
            return self.getSameTypeSpecializationCode(
                other, nb_slot, sq_slot, operand1, operand2
            )

        if other in related_types.get(self, ()):
            return self.getSimilarTypeSpecializationCode(
                other, nb_slot, operand1, operand2
            )

        return ""

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
            return slot != "nb_matrix_multiply"
        elif slot.startswith("sq_"):
            return False
        else:
            assert False

    @staticmethod
    def needsIndexConversion():
        return False

    @staticmethod
    def getAsLongValueExpression(operand):
        return "PyInt_AS_LONG(%s)" % operand

    @staticmethod
    def getAsObjectValueExpression(operand):
        return operand

    @staticmethod
    def releaseAsObjectValueStatement(operand):
        # Virtual method, pylint: disable=unused-argument
        return ""


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
            return slot == "nb_remainder"
        elif slot.startswith("sq_"):
            return "ass" not in slot
        else:
            assert False, slot


str_desc = StrDesc()


class UnicodeDesc(ConcreteTypeBase):
    type_name = "unicode"
    type_desc = "Python2 'unicode', Python3 'str'"

    @classmethod
    def getTypeName3(cls):
        return "str"

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
            return slot == "nb_remainder"
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
            return slot != "nb_matrix_multiply"
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


class SetDesc(ConcreteTypeBase):
    type_name = "set"
    type_desc = "Python 'set'"

    @classmethod
    def getTypeValueExpression(cls, operand):
        return "&PySet_Type"

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


set_desc = SetDesc()


class DictDesc(ConcreteTypeBase):
    type_name = "dict"
    type_desc = "Python 'dict'"

    @classmethod
    def getTypeValueExpression(cls, operand):
        return "&PyDict_Type"

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


dict_desc = DictDesc()


class BytesDesc(ConcreteTypeBase):
    type_name = "bytes"
    type_desc = "Python3 'bytes'"

    python_requirement = "PYTHON_VERSION >= 300"

    @classmethod
    def getTypeValueExpression(cls, operand):
        return "&PyBytes_Type"

    def hasSlot(self, slot):
        if slot.startswith("nb_"):
            return slot == "nb_remainder"
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
    def getTypeName3(cls):
        return "int"

    @classmethod
    def getTypeValueExpression(cls, operand):
        return "&PyLong_Type"

    def hasSlot(self, slot):
        if slot.startswith("nb_"):
            return slot != "nb_matrix_multiply"
        elif slot.startswith("sq_"):
            return False
        else:
            assert False

    @classmethod
    def getNewStyleNumberTypeCheckExpression(cls, operand):
        return "1"

    @staticmethod
    def needsIndexConversion():
        return False


long_desc = LongDesc()


class ObjectDesc(TypeDescBase):
    type_name = "object"
    type_desc = "any Python object"
    type_decl = "PyObject *"

    def hasSlot(self, slot):
        # Don't want to get asked, we cannot know.
        assert False

    def getIndexCheckExpression(self, operand):
        return "PyIndex_Check(%s)" % operand

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
        return ""

    @staticmethod
    def getAsLongValueExpression(operand):
        return operand

    @staticmethod
    def getAsObjectValueExpression(operand):
        return "PyLong_FromLong(%s)" % operand

    @staticmethod
    def releaseAsObjectValueStatement(operand):
        return "Py_DECREF(%s);" % operand


clong_desc = CLongDesc()

related_types = {clong_desc: (int_desc,), int_desc: (clong_desc,)}


class AlternativeTypeBase(object):
    # TODO: Base class for alternative types
    pass


class AlternativeIntOrClong(AlternativeTypeBase):
    # TODO: Base class for alternative type int or clong.
    pass


env = jinja2.Environment(
    loader=jinja2.PackageLoader("nuitka.tools.specialize", "templates"),
    trim_blocks=True,
    lstrip_blocks=True,
)

env.undefined = jinja2.StrictUndefined

types = (
    int_desc,
    str_desc,
    unicode_desc,
    float_desc,
    tuple_desc,
    list_desc,
    set_desc,
    dict_desc,
    bytes_desc,
    long_desc,
    clong_desc,
    object_desc,
)


def findTypeFromCodeName(code_name):
    for candidate in types:
        if candidate.getHelperCodeName() == code_name:
            return candidate

    assert False, code_name


add_codes = set()


def makeNbSlotCode(operand, op_code, left, right, emit):
    key = operand, op_code, left, right
    if key in add_codes:
        return

    if left in (int_desc, clong_desc):
        template = env.get_template("HelperOperationBinaryInt.c.j2")
    elif left == long_desc:
        template = env.get_template("HelperOperationBinaryLong.c.j2")
    elif left == float_desc:
        template = env.get_template("HelperOperationBinaryFloat.c.j2")
    elif left == list_desc:
        template = env.get_template("HelperOperationBinaryList.c.j2")
    elif left == tuple_desc:
        template = env.get_template("HelperOperationBinaryTuple.c.j2")
    elif left == set_desc:
        template = env.get_template("HelperOperationBinarySet.c.j2")
    elif left == bytes_desc:
        template = env.get_template("HelperOperationBinaryBytes.c.j2")
    else:
        return

    code = template.render(
        operand=operand,
        left=left,
        right=right,
        nb_slot=_getNbSlotFromOperand(operand, op_code),
        name=template.name,
    )

    emit(code)

    add_codes.add(key)


mul_repeats = set()


def makeMulRepeatCode(left, right, emit):
    key = right, left
    if key in mul_repeats:
        return

    template = env.get_template("HelperOperationMulRepeatSlot.c.j2")

    code = template.render(left=left, right=right)

    emit(code)

    mul_repeats.add(key)


def _getNbSlotFromOperand(operand, op_code):
    # pylint: disable=too-many-branches,too-many-return-statements

    if operand == "+":
        return "nb_add"
    elif operand == "*":
        return "nb_multiply"
    elif operand == "-":
        return "nb_subtract"
    elif operand == "//":
        return "nb_floor_divide"
    elif operand == "/":
        if op_code == "TRUEDIV":
            return "nb_true_divide"
        else:
            return "nb_divide"
    elif operand == "%":
        return "nb_remainder"
    elif operand == "**":
        return "nb_power"
    elif operand == "<<":
        return "nb_lshift"
    elif operand == ">>":
        return "nb_rshift"
    elif operand == "|":
        return "nb_or"
    elif operand == "&":
        return "nb_and"
    elif operand == "^":
        return "nb_xor"
    elif operand == "@":
        return "nb_matrix_multiply"
    else:
        assert False, operand


def makeHelperOperations(template, helpers_set, operand, op_code, emit_h, emit_c, emit):
    # Complexity comes natural, pylint: disable=too-many-branches

    emit(
        '/* C helpers for type specialized "%s" (%s) operations */' % (operand, op_code)
    )
    emit()

    for helper_name in helpers_set:
        assert helper_name.split("_")[:3] == ["BINARY", "OPERATION", op_code], (
            op_code,
            helper_name,
        )

        left = findTypeFromCodeName(helper_name.split("_")[3])
        right = findTypeFromCodeName(helper_name.split("_")[4])

        if left.python_requirement:
            emit("#if %s" % left.python_requirement)
        elif right.python_requirement:
            emit("#if %s" % right.python_requirement)

        nb_slot = _getNbSlotFromOperand(operand, op_code)

        code = left.getSameTypeSpecializationCode(
            right, nb_slot, None, "operand1", "operand2"
        )

        if code:
            cand = left if left is not object_desc else right
            makeNbSlotCode(operand, op_code, cand, cand, emit_c)

        if left is not right and right in related_types.get(left, ()):
            code = left.getSimilarTypeSpecializationCode(
                right, nb_slot, "operand1", "operand2"
            )

            if code:
                makeNbSlotCode(operand, op_code, left, right, emit_c)

        if operand == "*":
            repeat = left.getSqConcatSlotSpecializationCode(
                right, "sq_repeat", "operand2", "operand1"
            )

            if repeat:
                makeMulRepeatCode(left, right, emit_c)

            repeat = right.getSqConcatSlotSpecializationCode(
                left, "sq_repeat", "operand2", "operand1"
            )

            if repeat:
                makeMulRepeatCode(right, left, emit_c)

        emit(
            '/* Code referring to "%s" corresponds to %s and "%s" to %s. */'
            % (
                left.getHelperCodeName(),
                left.type_desc,
                right.getHelperCodeName(),
                right.type_desc,
            )
        )

        if operand == "+":
            sq_slot = "sq_concat"
        elif operand == "*":
            sq_slot = "sq_repeat"
        else:
            sq_slot = None

        code = template.render(
            left=left,
            right=right,
            op_code=op_code,
            operand=operand,
            nb_slot=_getNbSlotFromOperand(operand, op_code),
            sq_slot1=sq_slot,
        )

        emit_c(code)
        emit_h("extern " + code.splitlines()[0].replace(" {", ";"))

        if left.python_requirement or right.python_requirement:
            emit("#endif")

        emit()


def makeHelpersBinaryOperation(operand, op_code):

    specialized_op_helpers_set = getattr(
        nuitka.codegen.OperationCodes, "specialized_%s_helpers_set" % op_code.lower()
    )

    template = env.get_template("HelperOperationBinary.c.j2")

    filename_c = "nuitka/build/static_src/HelpersOperationBinary%s.c" % op_code.title()
    filename_h = (
        "nuitka/build/include/nuitka/helper/operations_binary_%s.h" % op_code.lower()
    )

    with open(filename_c, "w") as output_c:
        with open(filename_h, "w") as output_h:

            def emit_h(*args):
                writeline(output_h, *args)

            def emit_c(*args):
                writeline(output_c, *args)

            def emit(*args):
                emit_h(*args)
                emit_c(*args)

            def emitGenerationWarning(emit):
                emit(
                    "/* WARNING, this code is GENERATED. Modify the template %s instead! */"
                    % template.name
                )

            emitGenerationWarning(emit_h)
            emitGenerationWarning(emit_c)

            emit_c(
                """\
// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif
"""
            )

            filename_utils = filename_c[:-2] + "Utils.c"

            if os.path.exists(filename_utils):
                emit_c('#include "%s"' % os.path.basename(filename_utils))

            makeHelperOperations(
                template,
                specialized_op_helpers_set,
                operand,
                op_code,
                emit_h,
                emit_c,
                emit,
            )

    autoformat(filename_c, None, True)
    autoformat(filename_h, None, True)

    # No idea why, but this helps.
    if os.name == "nt":
        autoformat(filename_c, None, True)
        autoformat(filename_h, None, True)


def writeline(output, *args):
    if not args:
        output.write("\n")
    elif len(args) == 1:
        output.write(args[0] + "\n")
    else:
        assert False, args


def main():
    makeHelpersBinaryOperation("**", "POW")
    makeHelpersBinaryOperation("|", "BITOR")
    makeHelpersBinaryOperation("&", "BITAND")
    makeHelpersBinaryOperation("^", "BITXOR")
    makeHelpersBinaryOperation("<<", "LSHIFT")
    makeHelpersBinaryOperation(">>", "RSHIFT")
    makeHelpersBinaryOperation("%", "MOD")
    makeHelpersBinaryOperation("+", "ADD")
    makeHelpersBinaryOperation("-", "SUB")
    makeHelpersBinaryOperation("*", "MUL")
    makeHelpersBinaryOperation("//", "FLOORDIV")
    makeHelpersBinaryOperation("/", "TRUEDIV")
    makeHelpersBinaryOperation("/", "OLDDIV")
    makeHelpersBinaryOperation("@", "MATMULT")


if __name__ == "__main__":
    main()
