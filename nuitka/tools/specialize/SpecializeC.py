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
""" This tool is generating code variants for helper codes from Jinja templates.

"""

import nuitka.Options

nuitka.Options.is_fullcompat = False

# isort:start

import math
import os
from abc import abstractmethod

import nuitka.codegen.ComparisonCodes
import nuitka.codegen.HelperDefinitions
import nuitka.codegen.Namify
import nuitka.specs.BuiltinDictOperationSpecs
import nuitka.specs.BuiltinStrOperationSpecs
import nuitka.specs.BuiltinUnicodeOperationSpecs
from nuitka.__past__ import getMetaClassBase, long
from nuitka.codegen.CallCodes import (
    getQuickCallCode,
    getQuickMethodCallCode,
    getQuickMethodDescrCallCode,
    getQuickMixedCallCode,
    getTemplateCodeDeclaredFunction,
    max_quick_call,
)
from nuitka.nodes.ImportNodes import hard_modules
from nuitka.utils.Jinja2 import getTemplateC

from .Common import (
    formatArgs,
    getMethodVariations,
    python2_dict_methods,
    python2_str_methods,
    python2_unicode_methods,
    python3_dict_methods,
    python3_str_methods,
    withFileOpenedAndAutoformatted,
    writeline,
)


def getDoExtensionUsingTemplateC(template_name):
    return getTemplateC(
        package_name="nuitka.codegen",
        template_subdir="templates_c",
        template_name=template_name,
        extensions=("jinja2.ext.do",),
    )


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

    def isKnownToNotCoerce(self, right):
        if right is self and right is not object_desc:
            return True

        if self in (int_desc, long_desc, float_desc):
            if right in (
                str_desc,
                unicode_desc,
                tuple_desc,
                list_desc,
                set_desc,
                dict_desc,
            ):
                return True

        if (
            self.getNewStyleNumberTypeCheckExpression("dummy") == "1"
            and right.getNewStyleNumberTypeCheckExpression("dummy") == "1"
        ):
            return True

        if self is not object_desc:
            return not self.hasSlot("nb_coerce")
        else:
            return False

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
        # At least one match
        if type_name not in (cls.type_name, right.type_name):
            return False

        # Two matches perfect.
        if cls.type_name == right.type_name:
            return True

        if "object" not in (cls.type_name, right.type_name):
            return False

        return True

    @classmethod
    def mayBothHaveType(cls, right, type_name):
        return cls.type_name in (type_name, "object") and right.type_name in (
            type_name,
            "object",
        )

    @classmethod
    def getTypeCheckExactExpression(cls, operand):
        if cls.type_name == "str":
            return "PyStr_CheckExact(%s)" % operand
        elif cls.type_name == "dict":
            return "PyDict_CheckExact(%s)" % operand
        else:
            assert False, cls

    @classmethod
    def getIntCheckExpression(cls, operand):
        if cls.type_name == "int":
            return "1"
        elif cls.type_name == "object":
            return "PyInt_CheckExact(%s)" % operand
        else:
            return "0"

    @classmethod
    def getLongCheckExpression(cls, operand):
        if cls.type_name == "long":
            return "1"
        elif cls.type_name == "object":
            return "PyLong_CheckExact(%s)" % operand
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

    def getSequenceCheckExpression(self, operand, right):
        # Dictionaries are not really sequences despite slots.
        if self.type_name == "dict":
            return "0"
        elif self.type_name == "object":
            if right.type_name == "tuple":
                return "(PyTuple_CheckExact(%s) || PySequence_Check(%s))" % (
                    operand,
                    operand,
                )
            else:
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
            # Try to detect fallbacks, this needs version specific management
            # for at least "LONG", maybe others.

            assert self is object_desc, self
            return "RICHCOMPARE(%s)" % operand
        elif slot == "tp_compare":
            return operand + "->tp_compare"
        else:
            assert False, slot

    @staticmethod
    def getSlotType(slot):
        if slot in ("nb_power", "nb_inplace_power"):
            return "ternaryfunc"
        elif slot in ("sq_repeat", "sq_inplace_repeat"):
            return "ssizeargfunc"
        else:
            return "binaryfunc"

    @staticmethod
    def getSlotCallExpression(nb_slot, slot_var, operand1, operand2):
        if nb_slot in ("nb_power", "nb_inplace_power"):
            return "%s(%s, %s, Py_None)" % (slot_var, operand1, operand2)
        else:
            return "%s(%s, %s)" % (slot_var, operand1, operand2)

    def getSlotValueExpression(self, operand, slot):
        assert (
            "inplace_" not in slot
            or not self.hasSlot(slot)
            or self in (set_desc, list_desc)
        ), self.hasSlot

        if not self.hasSlot(slot):
            return "NULL"

        return self._getSlotValueExpression(operand, slot)

    def getSlotValueCheckExpression(self, operand, slot):
        # Virtual method, pylint: disable=unused-argument
        return "true" if self.hasSlot(slot) else "false"

    @staticmethod
    def getOperationErrorMessageName(operator):
        if operator == "%":
            return "%%"
        elif operator == "**":
            return "** or pow()"
        elif operator == "divmod":
            return "divmod()"
        else:
            return operator

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
#if PYTHON_VERSION < 0x300
PyErr_Format(PyExc_TypeError, "unorderable types: %(left_type2)s() %(operator)s %(right_type2)s()"%(args)s);
#elif PYTHON_VERSION < 0x360
PyErr_Format(PyExc_TypeError, "unorderable types: %(left_type3)s() %(operator)s %(right_type3)s()"%(args)s);
#else
PyErr_Format(PyExc_TypeError, "'%(operator)s' not supported between instances of '%(left_type3)s' and '%(right_type3)s'"%(args)s);
#endif
return %(return_value)s;""" % {
                "operator": operator,
                "left_type2": "%s" if left is object_desc else left.getTypeName2(),
                "right_type2": "%s" if right is object_desc else right.getTypeName2(),
                "left_type3": "%s" if left is object_desc else left.getTypeName3(),
                "right_type3": "%s" if right is object_desc else right.getTypeName3(),
                "args": args,
                "return_value": self.getExceptionResultIndicatorValue(),
            }
        else:
            return """\
#if PYTHON_VERSION < 0x360
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

    def hasSameTypeOperationSpecializationCode(self, other, nb_slot, sq_slot):
        # Many cases, pylint: disable=too-many-branches,too-many-return-statements

        cand = self if self is not object_desc else other

        # Both are objects, nothing to be done.
        if cand is object_desc:
            assert self is object_desc
            assert other is object_desc
            return False

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
                return False

        if slot == "nb_remainder":
            if cand in (list_desc, tuple_desc, set_desc, dict_desc):
                # No remainder with themselves.
                return False

        if slot == "nb_multiply":
            if cand in (
                str_desc,
                bytes_desc,
                list_desc,
                tuple_desc,
                set_desc,
                dict_desc,
            ):
                # No multiply with themselves.
                return False

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
                # No add with themselves.
                return False

        if slot in ("nb_and", "nb_or", "nb_xor"):
            if cand in (
                str_desc,
                bytes_desc,
                unicode_desc,
                list_desc,
                tuple_desc,
                dict_desc,
                float_desc,
            ):
                return False

        if slot in ("nb_lshift", "nb_rshift"):
            if cand in (
                str_desc,
                bytes_desc,
                unicode_desc,
                tuple_desc,
                list_desc,
                set_desc,
                dict_desc,
                float_desc,
            ):
                return False

        if slot == "nb_matrix_multiply":
            # Nobody has it for anything
            return False

        return True

    def hasSimilarTypeSpecializationCode(self, other):
        return other in related_types.get(self, ())

    def getSameTypeType(self, other):
        if self is object_desc:
            return other
        elif other is object_desc:
            return self
        else:
            return object_desc

    def isSimilarOrSameTypesAsOneOf(self, *others):
        for other in others:
            assert other is not None

            if self is other or other in related_types.get(self, ()):
                return True

        return False

    def hasTypeSpecializationCode(self, other, nb_slot, sq_slot):
        if self is object_desc and other is object_desc:
            return False

        if self is other:
            return self.hasSameTypeOperationSpecializationCode(
                other=other,
                nb_slot=nb_slot,
                sq_slot=sq_slot,
            )

        return self.hasSimilarTypeSpecializationCode(
            other=other,
        )

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
    def getAssignFromObjectExpressionCode(cls, result, operand, take_ref=False):
        if cls.type_name == "object":
            if take_ref:
                return "Py_INCREF(%s); %s = %s;" % (operand, result, operand)
            else:
                return "%s = %s;" % (result, operand)
        else:
            if take_ref:
                return """%s = %s; """ % (
                    result,
                    cls.getToValueFromObjectExpression(operand),
                )
            else:
                return """%s = %s; Py_DECREF(%s); """ % (
                    result,
                    cls.getToValueFromObjectExpression(operand),
                    operand,
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
                return """{ %s r = %s; return r; }""" % (
                    cls.getTypeDecl(),
                    cls.getToValueFromObjectExpression(operand),
                )
            else:
                return """{ %s r = %s; Py_DECREF(%s); return r; }""" % (
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
    def getAssignFromLongExpressionCode(cls, result, operand):
        if cls.type_name == "object":
            # TODO: Python3?
            return "%s = PyInt_FromLong(%s);" % (result, operand)
        elif cls.type_name == "nbool":
            return "%s = %s;" % (
                result,
                cls.getToValueFromBoolExpression("%s != 0" % operand),
            )
        else:
            assert False, cls

    @classmethod
    def getAssignFromBoolExpressionCode(cls, result, operand, give_ref):
        if cls.type_name == "object":
            # TODO: Python3?
            code = "%s = BOOL_FROM(%s);" % (result, operand)
            if give_ref:
                code += "Py_INCREF(%s);" % result

            return code
        elif cls.type_name == "nbool":
            return "%s = %s;" % (
                result,
                cls.getToValueFromBoolExpression("%s" % operand),
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
    def getAssignFromFloatExpressionCode(cls, result, operand):
        if cls.type_name in ("object", "int", "float"):
            return "%s = PyFloat_FromDouble(%s);" % (result, operand)
        elif cls.type_name == "nbool":
            return "%s = %s;" % (
                result,
                cls.getToValueFromBoolExpression("%s != 0.0" % operand),
            )
        elif cls.type_name == "float":
            return "%s = %s;" % (result, operand)
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
    def getAssignFromFloatConstantCode(cls, result, value):
        if value == "nan":
            value = float(value)

        if cls.type_name in ("object", "int"):
            # TODO: Type checks for value are needed for "int".

            const_name = "const_" + nuitka.codegen.Namify.namifyConstant(value)

            return "Py_INCREF(%(const_name)s); %(result)s = %(const_name)s;" % {
                "result": result,
                "const_name": const_name,
            }
        elif cls.type_name in ("nbool", "float"):
            if math.isnan(value):
                value = "Py_NAN"

            return cls.getAssignFromFloatExpressionCode(result, value)
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

    @classmethod
    def getAssignFromIntConstantCode(cls, result, value):
        if cls.type_name in ("object", "int"):
            const_name = "const_" + nuitka.codegen.Namify.namifyConstant(value)

            return "Py_INCREF(%(const_name)s); %(result)s = %(const_name)s;" % {
                "result": result,
                "const_name": const_name,
            }
        elif cls.type_name in ("nbool", "float"):
            return cls.getAssignFromLongExpressionCode(result, value)
        else:
            assert False, (cls, cls.type_name)

    @classmethod
    def getAssignFromLongConstantCode(cls, result, value):
        if cls.type_name in ("object", "long"):
            if str is bytes:
                # Cannot put "L" in Jinja code for constant value.
                value = long(value)

            # The only on we surely know right now.
            assert value == 0

            # TODO: This works for small constants only and only for Python3.
            const_name2 = "const_" + nuitka.codegen.Namify.namifyConstant(value)
            const_name3 = (
                "Nuitka_Long_SmallValues[NUITKA_TO_SMALL_VALUE_OFFSET(%d)]" % value
            )

            return """\
#if PYTHON_VERSION < 0x300
%(result)s = %(const_name2)s;
#else
%(result)s = %(const_name3)s;
#endif
Py_INCREF(%(result)s);""" % {
                "result": result,
                "const_name2": const_name2,
                "const_name3": const_name3,
            }
        elif cls.type_name in ("nbool", "float"):
            return cls.getAssignFromLongExpressionCode(result, value)
        else:
            assert False, (cls, cls.type_name)

    @classmethod
    def getAssignConversionCode(cls, result, left, value):
        def _getObjectObject():
            code = "%s = %s;" % (result, value)
            code += cls.getTakeReferenceStatement(result)

            return code

        if cls is left:
            return _getObjectObject()
        else:
            if cls.type_name in ("object", "float"):
                if left.type_name in ("int", "float"):
                    return _getObjectObject()
                elif left.type_name == "clong":
                    return cls.getAssignFromLongExpressionCode(result, value)
                else:
                    assert False, left.type_name
            elif cls.type_name == "nbool":

                if left.type_name == "int":
                    return "%s = %s;" % (
                        result,
                        cls.getToValueFromBoolExpression(
                            "%s != 0" % left.getAsLongValueExpression(value)
                        ),
                    )
                elif left.type_name == "float":
                    return "%s = %s;" % (
                        result,
                        cls.getToValueFromBoolExpression(
                            "%s != 0.0" % left.getAsDoubleValueExpression(value)
                        ),
                    )
                else:
                    assert False, left.type_name
            else:
                assert False, cls.type_name


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
assert(%(type_name)s_CheckExact(%(operand)s));""" % {
            "operand": operand,
            "type_name": self.getTypeValueExpression(operand)[1:].split("_")[0],
        }

    @abstractmethod
    def getTypeValueExpression(self, operand):
        pass

    @staticmethod
    def getTakeReferenceStatement(operand):
        return ""


class IntDesc(ConcreteTypeBase):
    type_name = "int"
    type_desc = "Python2 'int'"

    python_requirement = "PYTHON_VERSION < 0x300"

    @classmethod
    def getTypeValueExpression(cls, operand):
        return "&PyInt_Type"

    @classmethod
    def getNewStyleNumberTypeCheckExpression(cls, operand):
        return "1"

    def hasSlot(self, slot):
        if slot.startswith("nb_inplace"):
            return False
        elif slot.startswith("nb_"):
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

    python_requirement = "PYTHON_VERSION < 0x300"

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
            return "ass" not in slot and "inplace" not in slot
        elif slot == "tp_richcompare":
            return True
        elif slot == "tp_compare":
            return False
        else:
            assert False, (self, slot)


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
assert(PyUnicode_CheckExact(%(operand)s));""" % {
            "operand": operand
        }

    @classmethod
    def getNewStyleNumberTypeCheckExpression(cls, operand):
        return "1"

    def hasSlot(self, slot):
        if slot.startswith("nb_"):
            return slot == "nb_remainder"
        elif slot.startswith("sq_"):
            return "ass" not in slot and "inplace" not in slot
        elif slot == "tp_richcompare":
            return True
        elif slot == "tp_compare":
            return True
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
        if slot.startswith("nb_inplace"):
            return False
        elif slot.startswith("nb_"):
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
            return "ass" not in slot and "inplace" not in slot
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
        elif slot == "tp_richcompare":
            return True
        elif slot == "tp_compare":
            return False
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
        if slot.startswith("nb_inplace_"):
            return slot in (
                "nb_inplace_subtract",
                "nb_inplace_and",
                "nb_inplace_or",
                "nb_inplace_xor",
            )
        elif slot.startswith("nb_"):
            return slot in ("nb_subtract", "nb_and", "nb_or", "nb_xor")
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

    python_requirement = "PYTHON_VERSION >= 0x300"

    @classmethod
    def getTypeValueExpression(cls, operand):
        return "&PyBytes_Type"

    def hasSlot(self, slot):
        if slot.startswith("nb_"):
            return slot == "nb_remainder"
        elif slot.startswith("sq_"):
            return "ass" not in slot and slot != "sq_slice" and "inplace" not in slot
        elif slot == "tp_richcompare":
            return True
        elif slot == "tp_compare":
            return False
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
        if slot.startswith("nb_inplace_"):
            return False
        elif slot.startswith("nb_"):
            return slot != "nb_matrix_multiply"
        elif slot.startswith("sq_"):
            return False
        elif slot == "tp_richcompare":
            assert False
            # For Python3 it's there though
            return False
        elif slot == "tp_compare":
            # For Python2 it's tp_compare though
            return True
        else:
            assert False, slot

    def getSlotValueExpression(self, operand, slot):
        # Python2 long does have "tp_compare", Python3 does have "tp_richcompare",
        # therefore create code that makes this a conditional expression on the
        # Python version
        if slot == "tp_richcompare":
            return "(PYTHON_VERSION < 0x300 ? NULL : RICHCOMPARE(%s))" % operand

        return ConcreteTypeBase.getSlotValueExpression(self, operand=operand, slot=slot)

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
        return "CHECK_IF_TRUE(%s) == 1" % operand

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
        template = getDoExtensionUsingTemplateC("HelperOperationComparisonInt.c.j2")
    elif left == long_desc:
        template = getDoExtensionUsingTemplateC("HelperOperationComparisonLong.c.j2")
    elif left == float_desc:
        template = getDoExtensionUsingTemplateC("HelperOperationComparisonFloat.c.j2")
    elif left == tuple_desc:
        template = getDoExtensionUsingTemplateC("HelperOperationComparisonTuple.c.j2")
    elif left == list_desc:
        template = getDoExtensionUsingTemplateC("HelperOperationComparisonList.c.j2")
    # elif left == set_desc:
    #     template = env.get_template("HelperOperationComparisonSet.c.j2")
    elif left == bytes_desc:
        template = getDoExtensionUsingTemplateC("HelperOperationComparisonBytes.c.j2")
    elif left == str_desc:
        template = getDoExtensionUsingTemplateC("HelperOperationComparisonStr.c.j2")
    elif left == unicode_desc:
        template = getDoExtensionUsingTemplateC("HelperOperationComparisonUnicode.c.j2")
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

    template = getDoExtensionUsingTemplateC("HelperOperationMulRepeatSlot.c.j2")

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


def _getNbInplaceSlotFromOperand(operand, op_code):
    if operand == "divmod":
        return None

    nb_slot = _getNbSlotFromOperand(operand, op_code)
    return nb_slot.replace("nb_", "nb_inplace_")


def _parseTypesFromHelper(helper_name):
    (
        target_code,
        left_code,
        right_code,
    ) = nuitka.codegen.HelperDefinitions.parseTypesFromHelper(helper_name)

    if target_code is not None:
        target = findTypeFromCodeName(target_code)
    else:
        target = None

    left = findTypeFromCodeName(left_code)
    right = findTypeFromCodeName(right_code)

    return target_code, target, left, right


def _parseRequirements(op_code, target, left, right, emit):
    python_requirement = set()

    # There is an obsolete Python2 operation too, making sure it's guarded in code.
    if op_code == "OLDDIV":
        python_requirement.add(int_desc.python_requirement)
    if op_code == "MATMULT":
        python_requirement.add("PYTHON_VERSION >= 0x350")
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
    template, inplace, helpers_set, operator, op_code, emit_h, emit_c, emit
):
    # Complexity comes natural, pylint: disable=too-many-locals

    emit(
        '/* C helpers for type %s "%s" (%s) operations */'
        % ("in-place" if inplace else "specialized", operator, op_code)
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

        python_requirement = _parseRequirements(op_code, target, left, right, emit)

        emit(
            '/* Code referring to "%s" corresponds to %s and "%s" to %s. */'
            % (
                left.getHelperCodeName(),
                left.type_desc,
                right.getHelperCodeName(),
                right.type_desc,
            )
        )

        if operator == "+":
            sq_slot = "sq_concat"
        elif operator == "*":
            sq_slot = "sq_repeat"
        else:
            sq_slot = None

        if inplace and sq_slot is not None:
            sq_islot = sq_slot.replace("sq_", "sq_inplace_")
        else:
            sq_islot = None

        code = template.render(
            target=target,
            left=left,
            right=right,
            op_code=op_code,
            operator=operator,
            nb_slot=_getNbSlotFromOperand(operator, op_code),
            nb_islot=_getNbInplaceSlotFromOperand(operator, op_code)
            if inplace
            else None,
            sq_slot=sq_slot,
            sq_islot=sq_islot,
            object_desc=object_desc,
            int_desc=int_desc,
            long_desc=long_desc,
            float_desc=float_desc,
            list_desc=list_desc,
            tuple_desc=tuple_desc,
            set_desc=set_desc,
            str_desc=str_desc,
            unicode_desc=unicode_desc,
            bytes_desc=bytes_desc,
        )

        emit_c(code)
        emit_h(getTemplateCodeDeclaredFunction(code))

        if python_requirement:
            emit("#endif")

        emit()


def makeHelperComparisons(
    template, helpers_set, operator, op_code, emit_h, emit_c, emit
):
    # Details to look for, pylint: disable=too-many-locals

    emit(
        '/* C helpers for type specialized "%s" (%s) comparisons */'
        % (operator, op_code)
    )
    emit()

    for target in (object_desc, cbool_desc, nbool_desc):
        python_requirement = _parseRequirements(
            op_code, target, int_desc, int_desc, emit_c
        )

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

        python_requirement = _parseRequirements(op_code, target, left, right, emit)

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

        if not python_requirement:
            is_py3_only = False
            is_py2_only = False
        elif python_requirement == "PYTHON_VERSION < 0x300":
            is_py3_only = False
            is_py2_only = True
        elif python_requirement == "PYTHON_VERSION >= 0x300":
            is_py3_only = True
            is_py2_only = False
        else:
            assert False, python_requirement

        code = template.render(
            target=target,
            left=left,
            right=right,
            op_code=op_code,
            reversed_args_op_code=reversed_args_compare_op_codes[op_code],
            operator=operator,
            is_py3_only=is_py3_only,
            is_py2_only=is_py2_only,
        )

        emit_c(code)
        emit_h(getTemplateCodeDeclaredFunction(code))

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


def makeHelpersComparisonOperation(operand, op_code):
    specialized_cmp_helpers_set = getattr(
        nuitka.codegen.ComparisonCodes, "specialized_cmp_helpers_set"
    )

    template = getDoExtensionUsingTemplateC("HelperOperationComparison.c.j2")

    filename_c = "nuitka/build/static_src/HelpersComparison%s.c" % op_code.capitalize()
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

            emitGenerationWarning(emit, template.name)

            emitIDE(emit)

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

    template = getDoExtensionUsingTemplateC("HelperOperationBinary.c.j2")

    filename_c = (
        "nuitka/build/static_src/HelpersOperationBinary%s.c" % op_code.capitalize()
    )
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

            emitGenerationWarning(emit, template.name)

            emitIDE(emit)

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

    template = getDoExtensionUsingTemplateC("HelperOperationInplace.c.j2")

    filename_c = (
        "nuitka/build/static_src/HelpersOperationInplace%s.c" % op_code.capitalize()
    )
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

            emitGenerationWarning(emit, template.name)

            emitIDE(emit)

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


def makeHelpersImportHard():
    filename_c = "nuitka/build/static_src/HelpersImportHard.c"
    filename_h = "nuitka/build/include/nuitka/helper/import_hard.h"

    template = getDoExtensionUsingTemplateC("HelperImportHard.c.j2")

    with withFileOpenedAndAutoformatted(filename_c) as output_c:
        with withFileOpenedAndAutoformatted(filename_h) as output_h:

            def emit_h(*args):
                writeline(output_h, *args)

            def emit_c(*args):
                writeline(output_c, *args)

            def emit(*args):
                emit_h(*args)
                emit_c(*args)

            emitGenerationWarning(emit, template.name)

            emitIDE(emit)

            for module_name in sorted(hard_modules):
                makeHelperImportModuleHard(
                    template,
                    module_name,
                    emit_h,
                    emit_c,
                    emit,
                )


def makeHelperImportModuleHard(template, module_name, emit_h, emit_c, emit):
    emit('/* C helper for hard import of module "%s" import. */' % module_name)
    emit()

    if module_name == "_frozen_importlib":
        python_requirement = "PYTHON_VERSION >= 0x300"
    elif module_name == "_frozen_importlib_external":
        python_requirement = "PYTHON_VERSION >= 0x350"
    else:
        python_requirement = None

    if python_requirement:
        emit("#if %s" % python_requirement)

    code = template.render(
        module_name=module_name, name=template.name, target=object_desc
    )

    emit_c(code)
    emit_h(getTemplateCodeDeclaredFunction(code))

    if python_requirement:
        emit("#endif")


def makeHelperCalls():
    filename_c = "nuitka/build/static_src/HelpersCalling2.c"
    filename_h = "nuitka/build/include/nuitka/helper/calling2.h"

    with withFileOpenedAndAutoformatted(filename_c) as output_c:
        with withFileOpenedAndAutoformatted(filename_h) as output_h:

            def emit_h(*args):
                assert args[0] != "extern "
                writeline(output_h, *args)

            def emit_c(*args):
                writeline(output_c, *args)

            def emit(*args):
                emit_h(*args)
                emit_c(*args)

            template = getTemplateC(
                "nuitka.codegen", "CodeTemplateCallsPositional.c.j2"
            )

            emitGenerationWarning(emit, template.name)

            emitIDE(emit)

            for args_count in range(max_quick_call + 1):
                code = getQuickCallCode(args_count=args_count, has_tuple_arg=False)

                emit_c(code)
                emit_h(getTemplateCodeDeclaredFunction(code))

                if args_count >= 1:
                    code = getQuickCallCode(args_count=args_count, has_tuple_arg=True)

                    emit_c(code)
                    emit_h(getTemplateCodeDeclaredFunction(code))

            template = getTemplateC("nuitka.codegen", "CodeTemplateCallsMixed.c.j2")

            # Only keywords, but not positional arguments, via split args.
            code = getQuickMixedCallCode(
                args_count=0,
                has_tuple_arg=False,
                has_dict_values=True,
            )

            emit_c(code)
            emit_h(getTemplateCodeDeclaredFunction(code))

            for args_count in range(1, max_quick_call + 1):
                for has_tuple_arg in (False, True):
                    for has_dict_values in (False, True):
                        # We do not do that.
                        if not has_dict_values and has_tuple_arg:
                            continue

                        code = getQuickMixedCallCode(
                            args_count=args_count,
                            has_tuple_arg=has_tuple_arg,
                            has_dict_values=has_dict_values,
                        )

                        emit_c(code)
                        emit_h(getTemplateCodeDeclaredFunction(code))

            for args_count in range(1, 5):
                code = getQuickMethodDescrCallCode(args_count=args_count)

                emit_c(code)
                emit_h(getTemplateCodeDeclaredFunction(code))

            for args_count in range(max_quick_call + 1):
                code = getQuickMethodCallCode(args_count=args_count)

                emit_c(code)
                emit_h(getTemplateCodeDeclaredFunction(code))


def _makeHelperBuiltinTypeAttributes(
    type_prefix,
    type_name,
    python2_methods,
    python3_methods,
    emit_c,
):
    def getVarName(method_name):
        return "%s_builtin_%s" % (type_prefix, method_name)

    for method_name in sorted(set(python2_methods + python3_methods)):
        if method_name in python2_methods and method_name not in python3_methods:
            emit_c("#if PYTHON_VERSION < 0x300")
            needs_endif = True
        elif method_name not in python2_methods and method_name in python3_methods:
            emit_c("#if PYTHON_VERSION >= 0x300")
            needs_endif = True
        else:
            needs_endif = False

        emit_c("static PyObject *%s = NULL;" % getVarName(method_name))

        if needs_endif:
            emit_c("#endif")

    if not python3_methods:
        emit_c("#if PYTHON_VERSION < 0x300")

    emit_c("static void _init%sBuiltinMethods() {" % type_prefix.capitalize())
    for method_name in sorted(set(python2_methods + python3_methods)):
        if method_name in python2_methods and method_name not in python3_methods:
            emit_c("#if PYTHON_VERSION < 0x300")
            needs_endif = True
        elif method_name not in python2_methods and method_name in python3_methods:
            emit_c("#if PYTHON_VERSION >= 0x300")
            needs_endif = True
        else:
            needs_endif = False

        emit_c(
            '%s = PyObject_GetAttrString((PyObject *)&%s, "%s");'
            % (getVarName(method_name), type_name, method_name)
        )

        if needs_endif:
            emit_c("#endif")

    emit_c("}")

    if not python3_methods:
        emit_c("#endif")


generate_builtin_type_operations = [
    # TODO: For these, we would need an implementation for adding/deleting dictionary values. That
    # has turned out to be too hard so far and these are very good friends, not doing hashing
    # multiple times when reading and writing, so can't do it unless we add something for the
    # Nuitka-Python eventually.
    (
        "tshape_dict",
        dict_desc,
        nuitka.specs.BuiltinDictOperationSpecs,
        ("pop", "setdefault"),
    ),
    # TODO: These are very complex things using stringlib in Python, that we do not have easy access to,
    # but we might one day for Nuitka-Python expose it for the static linking of it and then we
    # could in fact call these directly.
    (
        "tshape_str",
        str_desc,
        nuitka.specs.BuiltinStrOperationSpecs,
        (
            "strip",
            "rstrip",
            "lstrip",
            "partition",
            "rpartition",
            "find",
            "rfind",
            "index",
            "rindex",
            "capitalize",
            "upper",
            "lower",
            "swapcase",
            "title",
            "isalnum",
            "isalpha",
            "isdigit",
            "islower",
            "isupper",
            "isspace",
            "istitle",
            "split",
            "rsplit",
            "startswith",
            "endswith",
            "replace",
            "encode",
            "decode",
        ),
    ),
    # TODO: This is using Python2 spec module for Python3 strings, that will be a problem down the
    # road, when version specifics come in.
    (
        "tshape_unicode",
        unicode_desc,
        nuitka.specs.BuiltinUnicodeOperationSpecs,
        (
            "strip",
            "rstrip",
            "lstrip",
            "find",
            "rfind",
            "index",
            "rindex",
            "capitalize",
            "upper",
            "lower",
            "swapcase",
            "title",
            "isalnum",
            "isalpha",
            "isdigit",
            "islower",
            "isupper",
            "isspace",
            "istitle",
            "split",
            "rsplit",
            "startswith",
            "endswith",
            "replace",
            "encode",
        ),
    ),
]


def makeHelperBuiltinTypeMethods():
    # Many details, pylint: disable=too-many-locals
    filename_c = "nuitka/build/static_src/HelpersBuiltinTypeMethods.c"
    filename_h = "nuitka/build/include/nuitka/helper/operations_builtin_types.h"
    with withFileOpenedAndAutoformatted(filename_c) as output_c:
        with withFileOpenedAndAutoformatted(filename_h) as output_h:

            def emit_h(*args):
                writeline(output_h, *args)

            def emit_c(*args):
                writeline(output_c, *args)

            def emit(*args):
                emit_h(*args)
                emit_c(*args)

            emitIDE(emit)

            _makeHelperBuiltinTypeAttributes(
                "str",
                "PyString_Type",
                python2_str_methods,
                (),
                emit_c,
            )
            _makeHelperBuiltinTypeAttributes(
                "unicode",
                "PyUnicode_Type",
                python2_unicode_methods,
                python3_str_methods,
                emit_c,
            )
            _makeHelperBuiltinTypeAttributes(
                "dict",
                "PyDict_Type",
                python2_dict_methods,
                python3_dict_methods,
                emit_c,
            )

            template = getDoExtensionUsingTemplateC("HelperBuiltinMethodOperation.c.j2")

            for (
                shape_name,
                type_desc,
                spec_module,
                method_names,
            ) in generate_builtin_type_operations:
                if type_desc.python_requirement:
                    emit("#if %s" % type_desc.python_requirement)

                for method_name in sorted(method_names):
                    (
                        present,
                        arg_names,
                        arg_name_mapping,
                        arg_counts,
                    ) = getMethodVariations(
                        spec_module=spec_module,
                        shape_name=shape_name,
                        method_name=method_name,
                        must_exist=True,
                    )

                    assert present, method_name

                    def formatArgumentDeclaration(arg_types, arg_names, starting):
                        return formatArgs(
                            [
                                arg_type.getVariableDecl(arg_name)
                                for arg_type, arg_name in zip(arg_types, arg_names)
                            ],
                            starting=starting,
                        )

                    # Function is used immediately in same loop, pylint: disable=cell-var-from-loop
                    def replaceArgNameForC(arg_name):
                        if arg_name in arg_name_mapping:
                            arg_name = arg_name_mapping[arg_name]

                        if arg_name in ("default", "new"):
                            return arg_name + "_value"
                        else:
                            return arg_name

                    for arg_count in arg_counts:
                        variant_args = [
                            replaceArgNameForC(arg_name)
                            for arg_name in arg_names[:arg_count]
                        ]

                        code = template.render(
                            object_desc=object_desc,
                            builtin_type=type_desc,
                            builtin_arg_name=type_desc.type_name,
                            method_name=method_name,
                            api_suffix=str(arg_count + 1)
                            if len(arg_counts) > 1
                            else "",
                            arg_names=variant_args,
                            arg_types=[object_desc] * len(variant_args),
                            formatArgumentDeclaration=formatArgumentDeclaration,
                            zip=zip,
                            len=len,
                            name=template.name,
                        )

                        emit_c(code)
                        emit_h(getTemplateCodeDeclaredFunction(code))
                if type_desc.python_requirement:
                    emit("#endif")


def main():

    # Cover many things once first, then cover all for quicker turnaround during development.
    makeHelperBuiltinTypeMethods()
    makeHelpersComparisonOperation("==", "EQ")
    makeHelpersBinaryOperation("+", "ADD")
    makeHelpersInplaceOperation("+", "ADD")

    makeHelpersImportHard()

    makeHelperCalls()

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

    makeHelpersComparisonOperation("!=", "NE")
    makeHelpersComparisonOperation("<=", "LE")
    makeHelpersComparisonOperation(">=", "GE")
    makeHelpersComparisonOperation(">", "GT")
    makeHelpersComparisonOperation("<", "LT")
