#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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

import contextlib
import os
import shutil
from abc import abstractmethod

import jinja2

import nuitka.codegen.ComparisonCodes
import nuitka.codegen.HelperDefinitions
import nuitka.codegen.Namify
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
    def getTypeDecl(cls):
        return cls.type_decl

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

    def getMostSpecificType(self, right):
        if self is not object_desc:
            return self
        else:
            return right

    def getLeastSpecificType(self, right):
        if self is object_desc:
            return self
        else:
            return right

    @classmethod
    def hasOneOrBothType(cls, right, type_name):
        return type_name in (cls.type_name, right.type_name)

    @classmethod
    def mayBothHaveType(cls, right, type_name):
        return cls.type_name in (type_name, "object") and right.type_name in (
            type_name,
            "object",
        )

    @classmethod
    def getIntCheckExpression(cls, operand):
        if cls.type_name == "int":
            return "1"
        elif cls.type_name == "object":
            return "PyInt_CheckExact(%s)" % operand
        else:
            return "0"

    @classmethod
    def getStringCheckExpression(cls, operand):
        if cls.type_name == "str":
            return "1"
        elif cls.type_name == "object":
            return "PyString_CheckExact(%s)" % operand
        else:
            return "0"

    @classmethod
    def getBytesCheckExpression(cls, operand):
        if cls.type_name == "bytes":
            return "1"
        elif cls.type_name == "object":
            return "PyBytes_CheckExact(%s)" % operand
        else:
            return "0"

    @classmethod
    def getUnicodeCheckExpression(cls, operand):
        if cls.type_name == "unicode":
            return "1"
        elif cls.type_name == "object":
            return "PyUnicode_CheckExact(%s)" % operand
        else:
            return "0"

    @classmethod
    def getFloatCheckExpression(cls, operand):
        if cls.type_name == "float":
            return "1"
        elif cls.type_name == "object":
            return "PyFloat_CheckExact(%s)" % operand
        else:
            return "0"

    @classmethod
    def getListCheckExpression(cls, operand):
        if cls.type_name == "list":
            return "1"
        elif cls.type_name == "object":
            return "PyList_CheckExact(%s)" % operand
        else:
            return "0"

    def getSequenceCheckExpression(self, operand):
        # Dictionaries are not really sequences despite slots.
        if self.type_name == "dict":
            return "0"
        elif self.type_name == "object":
            return "PySequence_Check(%s)" % operand
        elif self.hasSlot("sq_item"):
            return "1"
        else:
            return "0"

    def getInstanceCheckCode(self, operand):
        # We do not yet specialize for instances, therefore everything but object is one.
        if self.type_name == "object":
            return "PyInstance_Check(%s)" % operand
        else:
            return "0"

    def getIndexCheckExpression(self, operand):
        if self.hasSlot("nb_index"):
            return "1"
        elif self.type_name == "object":
            return "PyIndex_Check(%s)" % operand
        else:
            return "0"

    def getSaneTypeCheckCode(self, operand):
        # Is the type known to behave well for comparisons and object identity, e.g. not float.
        if self.type_name == "object":
            return "IS_SANE_TYPE(Py_TYPE(%s))" % operand
        elif self in (str_desc, int_desc, long_desc, list_desc, tuple_desc):
            return "1"
        elif self in (float_desc,):
            return "0"
        else:
            # Detect types not yet annotated.
            assert False, self
            return "0"

    def getTypeIdenticalCheckExpression(self, other, operand1, operand2):
        if self is object_desc or other is object_desc:
            return "%s == %s" % (operand1, operand2)
        elif self is other:
            return "1"
        else:
            return "0"

    @staticmethod
    def getRealSubTypeCheckCode(right, type2, type1):
        if right is object_desc:
            return "PyType_IsSubtype(%s, %s)" % (type2, type1)
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
        elif slot == "tp_richcompare":
            # Try to detect fallbacks

            assert self is object_desc, self
            return "RICHCOMPARE(%s)" % operand
        elif slot == "tp_compare":
            return operand + "->tp_compare"
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

    def getReturnUnsupportedTypeErrorCode(
        self, operator, left, right, operand1, operand2
    ):
        args = []

        if left is object_desc:
            args.append("%s->tp_name" % operand1)
        if right is object_desc:
            args.append("%s->tp_name" % operand2)

        if args:
            args = ", " + ", ".join(args)
        else:
            args = ""

        def formatOperation(operator):
            if operator == "%":
                return "%%"
            elif operator == "**":
                return "** or pow()"
            elif operator == "divmod":
                return "divmod()"
            else:
                return operator

        if (
            left.getTypeName2() != left.getTypeName3()
            or right.getTypeName2() != right.getTypeName3()
        ):
            return """\
#if PYTHON_VERSION < 300
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for %s: '%s' and '%s'"%s);
#else
    PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for %s: '%s' and '%s'"%s);
#endif
return %s;""" % (
                formatOperation(operator),
                "%s" if left is object_desc else left.getTypeName2(),
                "%s" if right is object_desc else right.getTypeName2(),
                args,
                formatOperation(operator),
                "%s" if left is object_desc else left.getTypeName3(),
                "%s" if right is object_desc else right.getTypeName3(),
                args,
                self.getExceptionResultIndicatorValue(),
            )
        else:
            return """\
PyErr_Format(PyExc_TypeError, "unsupported operand type(s) for %s: '%s' and '%s'"%s);
return %s;""" % (
                formatOperation(operator),
                "%s" if left is object_desc else left.getTypeName2(),
                "%s" if right is object_desc else right.getTypeName2(),
                args,
                self.getExceptionResultIndicatorValue(),
            )

    def getReturnUnorderableTypeErrorCode(
        self, operator, left, right, operand1, operand2
    ):
        args = []

        if left is object_desc:
            args.append("%s->tp_name" % operand1)
        if right is object_desc:
            args.append("%s->tp_name" % operand2)

        if args:
            args = ", " + ", ".join(args)
        else:
            args = ""

        if (
            left.getTypeName2() != left.getTypeName3()
            or right.getTypeName2() != right.getTypeName3()
        ):
            # TODO: The message for Python2, can it be triggered at all for non-objects?
            return """\
#if PYTHON_VERSION < 300
PyErr_Format(PyExc_TypeError, "unorderable types: %(left_type2)s() %(operator)s %(right_type2)s()"%(args)s);
#elif PYTHON_VERSION < 360
PyErr_Format(PyExc_TypeError, "unorderable types: %(left_type3)s() %(operator)s %(right_type3)s()"%(args)s);
#else
PyErr_Format(PyExc_TypeError, "'%(operator)s' not supported between instances of '%(left_type3)s' and '%(right_type3)s'"%(args)s);
#endif
return %(return_value)s;""" % {
                "operator": operator,
                "left_type2": "%s" if left is object_desc else left.getTypeName2(),
                "right_type2": "%s" if right is object_desc else right.getTypeName2(),
                "left_type3": "%s" if left is object_desc else left.getTypeName2(),
                "right_type3": "%s" if right is object_desc else right.getTypeName2(),
                "args": args,
                "return_value": self.getExceptionResultIndicatorValue(),
            }
        else:
            return """\
#if PYTHON_VERSION < 360
PyErr_Format(PyExc_TypeError, "unorderable types: %(left_type)s() %(operator)s %(right_type)s()"%(args)s);
#else
PyErr_Format(PyExc_TypeError, "'%(operator)s' not supported between instances of '%(left_type)s' and '%(right_type)s'"%(args)s);
#endif
return %(return_value)s;""" % {
                "operator": operator,
                "left_type": "%s" if left is object_desc else left.getTypeName2(),
                "right_type": "%s" if right is object_desc else right.getTypeName2(),
                "args": args,
                "return_value": self.getExceptionResultIndicatorValue(),
            }

    def getSameTypeOperationSpecializationCode(
        self, target, other, nb_slot, sq_slot, operand1, operand2
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

        return "return SLOT_%s_%s_%s_%s(%s, %s);" % (
            slot,
            target.getHelperCodeName(),
            cand.getHelperCodeName(),
            cand.getHelperCodeName(),
            operand1,
            operand2,
        )

    def getSimilarTypeSpecializationCode(
        self, target, other, nb_slot, operand1, operand2
    ):
        return "return SLOT_%s_%s_%s_%s(%s, %s);" % (
            nb_slot,
            target.getHelperCodeName(),
            self.getHelperCodeName(),
            other.getHelperCodeName(),
            operand1,
            operand2,
        )

    def getTypeSpecializationCode(
        self, target, other, nb_slot, sq_slot, operand1, operand2
    ):
        if self is object_desc or other is object_desc:
            return ""

        if self is other:
            return self.getSameTypeOperationSpecializationCode(
                target=target,
                other=other,
                nb_slot=nb_slot,
                sq_slot=sq_slot,
                operand1=operand1,
                operand2=operand2,
            )

        if other in related_types.get(self, ()):
            return self.getSimilarTypeSpecializationCode(
                target=target,
                other=other,
                nb_slot=nb_slot,
                operand1=operand1,
                operand2=operand2,
            )

        return ""

    @abstractmethod
    def getSqConcatSlotSpecializationCode(
        self, target, other, slot, operand1, operand2
    ):
        pass

    def getSameTypeComparisonSpecializationCode(
        self, other, op_code, target, operand1, operand2
    ):
        cand = self if self is not object_desc else other

        if cand is object_desc:
            return ""

        return "return COMPARE_%s_%s_%s_%s(%s, %s);" % (
            op_code,
            target.getHelperCodeName(),
            cand.getHelperCodeName(),
            cand.getHelperCodeName(),
            operand1,
            operand2,
        )

    @staticmethod
    def getTakeReferenceStatement(operand):
        return "Py_INCREF(%s);" % operand

    @classmethod
    def getReturnFromObjectExpressionCode(
        cls, operand, take_ref=False, check_exception=True
    ):
        if check_exception and not (cls.type_name == "object" and not take_ref):
            r = """if (unlikely(%s == NULL)) { return %s; }\n\n""" % (
                operand,
                cls.getExceptionResultIndicatorValue(),
            )
        else:
            r = ""

        return r + cls._getReturnFromObjectExpressionCode(
            operand=operand, take_ref=take_ref
        )

    @classmethod
    def _getReturnFromObjectExpressionCode(cls, operand, take_ref):
        if cls.type_name == "object":
            if take_ref:
                return "Py_INCREF(%s); return %s;" % (operand, operand)
            else:
                return "return %s;" % operand
        else:
            if take_ref:
                return """%s r = %s; return r; """ % (
                    cls.getTypeDecl(),
                    cls.getToValueFromObjectExpression(operand),
                )
            else:
                return """%s r = %s; Py_DECREF(%s); return r; """ % (
                    cls.getTypeDecl(),
                    cls.getToValueFromObjectExpression(operand),
                    operand,
                )

    @classmethod
    def getReturnFromLongExpressionCode(cls, operand):
        if cls.type_name == "object":
            # TODO: Python3?
            return "return PyInt_FromLong(%s);" % operand
        elif cls.type_name == "nbool":
            return "return %s;" % cls.getToValueFromBoolExpression("%s != 0" % operand)
        else:
            assert False, cls

    @classmethod
    def getReturnTupleFromLongExpressionsCode(cls, *operands):
        if cls.type_name == "object":
            return 'return Py_BuildValue("(%s)", %s);' % (
                "l" * len(operands),
                ", ".join(operands),
            )
        else:
            assert False, cls

    @classmethod
    def getReturnTupleFromFloatExpressionsCode(cls, *operands):
        if cls.type_name == "object":
            return 'return Py_BuildValue("(%s)", %s);' % (
                "d" * len(operands),
                ", ".join(operands),
            )
        else:
            assert False, cls

    @classmethod
    def getReturnFromFloatExpressionCode(cls, operand):
        if cls.type_name == "object":
            return "return PyFloat_FromDouble(%s);" % operand
        elif cls.type_name == "nbool":
            return "return %s;" % cls.getToValueFromBoolExpression(
                "%s == 0.0" % operand
            )
        elif cls.type_name == "float":
            return "return %s;" % operand
        else:
            assert False, cls

    @classmethod
    def getReturnFromFloatConstantCode(cls, value):
        if cls.type_name == "object":
            const_name = "const_" + nuitka.codegen.Namify.namifyConstant(value)

            return "Py_INCREF(%(const_name)s); return %(const_name)s;" % {
                "const_name": const_name
            }
        elif cls.type_name in ("nbool", "float"):
            return cls.getReturnFromFloatExpressionCode(value)
        else:
            assert False, cls

    @classmethod
    def getReturnFromIntConstantCode(cls, value):
        if cls.type_name == "object":
            const_name = "const_" + nuitka.codegen.Namify.namifyConstant(value)

            return "Py_INCREF(%(const_name)s); return %(const_name)s;" % {
                "const_name": const_name
            }
        elif cls.type_name in ("nbool", "float"):
            return cls.getReturnFromLongExpressionCode(value)
        else:
            assert False, cls


class ConcreteTypeBase(TypeDescBase):
    type_decl = "PyObject *"

    def _getSlotValueExpression(self, operand, slot):
        if slot.startswith("nb_"):
            return self.getTypeValueExpression(operand)[1:] + ".tp_as_number->" + slot
        elif slot.startswith("sq_"):
            return self.getTypeValueExpression(operand)[1:] + ".tp_as_sequence->" + slot
        elif slot.startswith("tp_"):
            return self.getTypeValueExpression(operand)[1:] + "." + slot
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

    def getSqConcatSlotSpecializationCode(
        self, target, other, slot, operand1, operand2
    ):
        if not self.hasSlot(slot):
            return ""

        # TODO: Use second type eventually when we specialize those too.
        return "return SLOT_%s_%s_%s_%s(%s, %s);" % (
            slot,
            target.getHelperCodeName(),
            self.getHelperCodeName(),
            other.getHelperCodeName(),
            operand1,
            operand2,
        )

    @staticmethod
    def getTakeReferenceStatement(operand):
        return ""


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
        elif slot == "tp_richcompare":
            return False
        elif slot == "tp_compare":
            return True
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

    @staticmethod
    def getAsDoubleValueExpression(operand):
        return "PyFloat_AS_DOUBLE(%s)" % operand

    def hasSlot(self, slot):
        if slot.startswith("nb_"):
            return slot != "nb_matrix_multiply"
        elif slot.startswith("sq_"):
            return False
        elif slot == "tp_richcompare":
            return True
        elif slot == "tp_compare":
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
        elif slot == "tp_richcompare":
            return True
        elif slot == "tp_compare":
            return False
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

    def getSqConcatSlotSpecializationCode(
        self, target, other, slot, operand1, operand2
    ):
        return ""

    @staticmethod
    def getToValueFromBoolExpression(operand):
        return "BOOL_FROM(%s)" % operand

    @staticmethod
    def getToValueFromObjectExpression(operand):
        return operand

    @staticmethod
    def getExceptionResultIndicatorValue():
        return "NULL"


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

    def getSqConcatSlotSpecializationCode(
        self, target, other, slot, operand1, operand2
    ):
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


class CBoolDesc(TypeDescBase):
    type_name = "cbool"
    type_desc = "C platform bool value"
    type_decl = "bool"

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

    def getSqConcatSlotSpecializationCode(
        self, target, other, slot, operand1, operand2
    ):
        return ""

    @staticmethod
    def getAsLongValueExpression(operand):
        return operand

    @staticmethod
    def getAsObjectValueExpression(operand):
        return "BOOL_FROM(%s)" % operand

    @staticmethod
    def getToValueFromBoolExpression(operand):
        return operand

    @staticmethod
    def getToValueFromObjectExpression(operand):
        return "CHECK_IF_TRUE(%s)" % operand

    @staticmethod
    def getTakeReferenceStatement(operand):
        return ""

    @staticmethod
    def getExceptionResultIndicatorValue():
        return "false"


cbool_desc = CBoolDesc()


class NBoolDesc(TypeDescBase):
    type_name = "nbool"
    type_desc = "Nuitka C bool value"
    type_decl = "nuitka_bool"

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

    def getSqConcatSlotSpecializationCode(
        self, target, other, slot, operand1, operand2
    ):
        return ""

    @staticmethod
    def getAsLongValueExpression(operand):
        return operand

    @staticmethod
    def getAsObjectValueExpression(operand):
        return "BOOL_FROM(%s)" % operand

    @staticmethod
    def getToValueFromBoolExpression(operand):
        return "%s ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE" % operand

    @classmethod
    def getToValueFromObjectExpression(cls, operand):
        return cls.getToValueFromBoolExpression("CHECK_IF_TRUE(%s)" % operand)

    @staticmethod
    def getTakeReferenceStatement(operand):
        return ""

    @staticmethod
    def getExceptionResultIndicatorValue():
        return "NUITKA_BOOL_EXCEPTION"


nbool_desc = NBoolDesc()


class NVoidDesc(TypeDescBase):
    type_name = "nvoid"
    type_desc = "Nuitka C void value"
    type_decl = "nuitka_void"

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

    def getSqConcatSlotSpecializationCode(
        self, target, other, slot, operand1, operand2
    ):
        return ""

    @staticmethod
    def getAsLongValueExpression(operand):
        assert False

        return operand

    @staticmethod
    def getAsObjectValueExpression(operand):
        assert False

        return "BOOL_FROM(%s)" % operand

    @staticmethod
    def getToValueFromBoolExpression(operand):
        # All values are the same, pylint: disable=unused-argument
        return "NUITKA_VOID_OK"

    @classmethod
    def getToValueFromObjectExpression(cls, operand):
        # All values are the same, pylint: disable=unused-argument
        return "NUITKA_VOID_OK"

    @staticmethod
    def getTakeReferenceStatement(operand):
        return ""

    @staticmethod
    def getExceptionResultIndicatorValue():
        return "NUITKA_VOID_EXCEPTION"


nvoid_desc = NVoidDesc()


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
    cbool_desc,
    nbool_desc,
    object_desc,
)


def findTypeFromCodeName(code_name):
    for candidate in types:
        if candidate.getHelperCodeName() == code_name:
            return candidate


op_slot_codes = set()


def makeNbSlotCode(operand, op_code, target, left, right, emit):
    key = operand, op_code, target, left, right
    if key in op_slot_codes:
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
        target=target,
        left=left,
        right=right,
        nb_slot=_getNbSlotFromOperand(operand, op_code),
        name=template.name,
    )

    emit(code)

    op_slot_codes.add(key)


# Reverse operation mapping.
reversed_args_compare_op_codes = {
    "LE": "GE",
    "LT": "GT",
    "EQ": "EQ",
    "NE": "NE",
    "GT": "LT",
    "GE": "LE",
}


def makeCompareSlotCode(operator, op_code, target, left, right, emit):
    key = operator, op_code, target, left, right
    if key in op_slot_codes:
        return

    if left in (int_desc, clong_desc):
        template = env.get_template("HelperOperationComparisonInt.c.j2")
    # elif left == long_desc:
    #     template = env.get_template("HelperOperationBinaryLong.c.j2")
    elif left == float_desc:
        template = env.get_template("HelperOperationComparisonFloat.c.j2")
    # elif left == list_desc:
    #     template = env.get_template("HelperOperationComparisonList.c.j2")
    elif left == tuple_desc:
        template = env.get_template("HelperOperationComparisonTuple.c.j2")
    # elif left == set_desc:
    #     template = env.get_template("HelperOperationComparisonSet.c.j2")
    # elif left == bytes_desc:
    #     template = env.get_template("HelperOperationComparisonBytes.c.j2")
    else:
        return

    code = template.render(
        operand=operator,  # TODO: rename
        target=target,
        left=left,
        right=right,
        op_code=op_code,
        reversed_args_op_code=reversed_args_compare_op_codes[op_code],
        name=template.name,
    )

    emit(code)

    op_slot_codes.add(key)


mul_repeats = set()


def makeMulRepeatCode(target, left, right, emit):
    key = right, left
    if key in mul_repeats:
        return

    template = env.get_template("HelperOperationMulRepeatSlot.c.j2")

    code = template.render(target=target, left=left, right=right)

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
    elif operand == "divmod":
        return "nb_divmod"
    else:
        assert False, operand


def _parseTypesFromHelper(helper_name):
    target_code, left_code, right_code = nuitka.codegen.HelperDefinitions.parseTypesFromHelper(
        helper_name
    )

    if target_code is not None:
        target = findTypeFromCodeName(target_code)
    else:
        target = None

    left = findTypeFromCodeName(left_code)
    right = findTypeFromCodeName(right_code)

    return target_code, target, left, right


def _parseRequirements(target, left, right, emit):
    python_requirement = set()

    if target is not None and target.python_requirement:
        python_requirement.add(target.python_requirement)
    if left.python_requirement:
        python_requirement.add(left.python_requirement)
    if right.python_requirement:
        python_requirement.add(right.python_requirement)

    if python_requirement:
        assert len(python_requirement) == 1, (target, left, right)
        python_requirement = python_requirement.pop()

        emit("#if %s" % python_requirement)

    return python_requirement


def makeHelperOperations(
    template, inplace, helpers_set, operand, op_code, emit_h, emit_c, emit
):
    # Complexity comes natural, pylint: disable=too-many-branches,too-many-locals

    emit(
        '/* C helpers for type %s "%s" (%s) operations */'
        % ("in-place" if inplace else "specialized", operand, op_code)
    )
    emit()

    for helper_name in helpers_set:
        assert helper_name.split("_")[:3] == ["BINARY", "OPERATION", op_code], (
            op_code,
            helper_name,
        )

        target_code, target, left, right = _parseTypesFromHelper(helper_name)

        assert target is None or not inplace

        if target is None and not inplace:
            if target_code == "NILONG":
                continue

            assert False, target_code

        python_requirement = _parseRequirements(target, left, right, emit)

        nb_slot = _getNbSlotFromOperand(operand, op_code)

        if not inplace:
            code = left.getSameTypeOperationSpecializationCode(
                target=target,
                other=right,
                nb_slot=nb_slot,
                sq_slot=None,
                operand1="operand1",
                operand2="operand2",
            )

            if code:
                cand = left if left is not object_desc else right
                makeNbSlotCode(operand, op_code, target, cand, cand, emit_c)

        if (
            target is not None
            and left is not right
            and right in related_types.get(left, ())
        ):
            code = left.getSimilarTypeSpecializationCode(
                target=target,
                other=right,
                nb_slot=nb_slot,
                operand1="operand1",
                operand2="operand2",
            )

            if code:
                makeNbSlotCode(operand, op_code, target, left, right, emit_c)

        if operand == "*" and target is not None:
            repeat = left.getSqConcatSlotSpecializationCode(
                target, right, "sq_repeat", "operand2", "operand1"
            )

            if repeat:
                makeMulRepeatCode(target, left, right, emit_c)

            repeat = right.getSqConcatSlotSpecializationCode(
                target, left, "sq_repeat", "operand2", "operand1"
            )

            if repeat:
                makeMulRepeatCode(target, right, left, emit_c)

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
            target=target,
            left=left,
            right=right,
            op_code=op_code,
            operator=operand,  # TODO: Rename operand to operator
            nb_slot=_getNbSlotFromOperand(operand, op_code),
            sq_slot1=sq_slot,
        )

        emit_c(code)
        emit_h(
            "extern "
            + code.splitlines()[0]
            .replace(" {", ";")
            .replace("static ", "")
            .replace("_BINARY", "BINARY")
        )

        if python_requirement:
            emit("#endif")

        emit()


def makeHelperComparisons(
    template, helpers_set, operator, op_code, emit_h, emit_c, emit
):
    emit(
        '/* C helpers for type specialized "%s" (%s) comparions */'
        % (operator, op_code)
    )
    emit()

    for target in (object_desc, cbool_desc, nbool_desc):
        python_requirement = _parseRequirements(target, int_desc, int_desc, emit_c)

        makeCompareSlotCode(operator, op_code, target, int_desc, int_desc, emit_c)

        if python_requirement:
            emit_c("#endif")

    for helper_name in helpers_set:
        assert helper_name.split("_")[:3] == ["RICH", "COMPARE", "xx"], (helper_name,)

        target_code, target, left, right = _parseTypesFromHelper(helper_name)

        if target is None:
            if target_code == "NILONG":
                continue

            assert False, target_code

        python_requirement = _parseRequirements(target, left, right, emit)

        code = left.getSameTypeComparisonSpecializationCode(
            right, op_code, target, "operand1", "operand2"
        )

        if code:
            cand = left if left is not object_desc else right
            makeCompareSlotCode(operator, op_code, target, cand, cand, emit_c)

        emit(
            '/* Code referring to "%s" corresponds to %s and "%s" to %s. */'
            % (
                left.getHelperCodeName(),
                left.type_desc,
                right.getHelperCodeName(),
                right.type_desc,
            )
        )

        code = template.render(
            target=target,
            left=left,
            right=right,
            op_code=op_code,
            reversed_args_op_code=reversed_args_compare_op_codes[op_code],
            operator=operator,
        )

        emit_c(code)
        emit_h("extern " + code.splitlines()[0].replace(" {", ";"))

        if python_requirement:
            emit("#endif")

        emit()


def emitGenerationWarning(emit, template_name):
    emit(
        "/* WARNING, this code is GENERATED. Modify the template %s instead! */"
        % template_name
    )


def emitIDE(emit):
    emit(
        """
/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif
"""
    )


@contextlib.contextmanager
def withFileOpenedAndAutoformatted(filename):
    tmp_filename = filename + ".tmp"
    with open(tmp_filename, "w") as output:
        yield output

    autoformat(tmp_filename, None, True, effective_filename=filename)

    # No idea why, but this helps.
    if os.name == "nt":
        autoformat(tmp_filename, None, True, effective_filename=filename)

    shutil.copy(tmp_filename, filename)
    os.unlink(tmp_filename)


def makeHelpersComparisonOperation(operand, op_code):
    specialized_cmp_helpers_set = getattr(
        nuitka.codegen.ComparisonCodes, "specialized_cmp_helpers_set"
    )

    template = env.get_template("HelperOperationComparison.c.j2")

    filename_c = "nuitka/build/static_src/HelpersComparison%s.c" % op_code.title()
    filename_h = "nuitka/build/include/nuitka/helper/comparisons_%s.h" % op_code.lower()

    with withFileOpenedAndAutoformatted(filename_c) as output_c:
        with withFileOpenedAndAutoformatted(filename_h) as output_h:

            def emit_h(*args):
                writeline(output_h, *args)

            def emit_c(*args):
                writeline(output_c, *args)

            def emit(*args):
                emit_h(*args)
                emit_c(*args)

            emitGenerationWarning(emit_h, template.name)
            emitGenerationWarning(emit_c, template.name)

            emitIDE(emit_c)
            emitIDE(emit_h)

            filename_utils = filename_c[:-2] + "Utils.c"

            if os.path.exists(filename_utils):
                emit_c('#include "%s"' % os.path.basename(filename_utils))

            makeHelperComparisons(
                template,
                specialized_cmp_helpers_set,
                operand,
                op_code,
                emit_h,
                emit_c,
                emit,
            )


def makeHelpersBinaryOperation(operand, op_code):
    specialized_op_helpers_set = getattr(
        nuitka.codegen.HelperDefinitions, "specialized_%s_helpers_set" % op_code.lower()
    )

    template = env.get_template("HelperOperationBinary.c.j2")

    filename_c = "nuitka/build/static_src/HelpersOperationBinary%s.c" % op_code.title()
    filename_h = (
        "nuitka/build/include/nuitka/helper/operations_binary_%s.h" % op_code.lower()
    )

    with withFileOpenedAndAutoformatted(filename_c) as output_c:
        with withFileOpenedAndAutoformatted(filename_h) as output_h:

            def emit_h(*args):
                writeline(output_h, *args)

            def emit_c(*args):
                writeline(output_c, *args)

            def emit(*args):
                emit_h(*args)
                emit_c(*args)

            emitGenerationWarning(emit_h, template.name)
            emitGenerationWarning(emit_c, template.name)

            emitIDE(emit_c)
            emitIDE(emit_h)

            filename_utils = filename_c[:-2] + "Utils.c"

            if os.path.exists(filename_utils):
                emit_c('#include "%s"' % os.path.basename(filename_utils))

            makeHelperOperations(
                template,
                False,
                specialized_op_helpers_set,
                operand,
                op_code,
                emit_h,
                emit_c,
                emit,
            )


def makeHelpersInplaceOperation(operand, op_code):
    specialized_op_helpers_set = getattr(
        nuitka.codegen.HelperDefinitions,
        "specialized_i%s_helpers_set" % op_code.lower(),
    )

    template = env.get_template("HelperOperationInplace.c.j2")

    filename_c = "nuitka/build/static_src/HelpersOperationInplace%s.c" % op_code.title()
    filename_h = (
        "nuitka/build/include/nuitka/helper/operations_inplace_%s.h" % op_code.lower()
    )

    with withFileOpenedAndAutoformatted(filename_c) as output_c:
        with withFileOpenedAndAutoformatted(filename_h) as output_h:

            def emit_h(*args):
                writeline(output_h, *args)

            def emit_c(*args):
                writeline(output_c, *args)

            def emit(*args):
                emit_h(*args)
                emit_c(*args)

            emitGenerationWarning(emit_h, template.name)
            emitGenerationWarning(emit_c, template.name)

            emitIDE(emit_c)
            emitIDE(emit_h)

            filename_utils = filename_c[:-2] + "Utils.c"

            if os.path.exists(filename_utils):
                emit_c('#include "%s"' % os.path.basename(filename_utils))

            makeHelperOperations(
                template,
                True,
                specialized_op_helpers_set,
                operand,
                op_code,
                emit_h,
                emit_c,
                emit,
            )


def writeline(output, *args):
    if not args:
        output.write("\n")
    elif len(args) == 1:
        output.write(args[0] + "\n")
    else:
        assert False, args


def main():
    makeHelpersComparisonOperation("==", "EQ")
    makeHelpersComparisonOperation("!=", "NE")
    makeHelpersComparisonOperation("<=", "LE")
    makeHelpersComparisonOperation(">=", "GE")
    makeHelpersComparisonOperation(">", "GT")
    makeHelpersComparisonOperation("<", "LT")

    makeHelpersInplaceOperation("+", "ADD")
    makeHelpersInplaceOperation("-", "SUB")
    makeHelpersInplaceOperation("*", "MULT")
    makeHelpersInplaceOperation("%", "MOD")
    makeHelpersInplaceOperation("|", "BITOR")
    makeHelpersInplaceOperation("&", "BITAND")
    makeHelpersInplaceOperation("^", "BITXOR")
    makeHelpersInplaceOperation("<<", "LSHIFT")
    makeHelpersInplaceOperation(">>", "RSHIFT")
    makeHelpersInplaceOperation("//", "FLOORDIV")
    makeHelpersInplaceOperation("/", "TRUEDIV")
    makeHelpersInplaceOperation("/", "OLDDIV")
    makeHelpersInplaceOperation("**", "POW")
    makeHelpersInplaceOperation("@", "MATMULT")

    makeHelpersBinaryOperation("+", "ADD")
    makeHelpersBinaryOperation("-", "SUB")
    makeHelpersBinaryOperation("*", "MULT")
    makeHelpersBinaryOperation("%", "MOD")
    makeHelpersBinaryOperation("|", "BITOR")
    makeHelpersBinaryOperation("&", "BITAND")
    makeHelpersBinaryOperation("^", "BITXOR")
    makeHelpersBinaryOperation("<<", "LSHIFT")
    makeHelpersBinaryOperation(">>", "RSHIFT")
    makeHelpersBinaryOperation("//", "FLOORDIV")
    makeHelpersBinaryOperation("/", "TRUEDIV")
    makeHelpersBinaryOperation("/", "OLDDIV")
    makeHelpersBinaryOperation("divmod", "DIVMOD")
    makeHelpersBinaryOperation("**", "POW")
    makeHelpersBinaryOperation("@", "MATMULT")


if __name__ == "__main__":
    main()
