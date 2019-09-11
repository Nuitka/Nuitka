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
""" Shapes for Python built-in types.

"""

from nuitka.codegen.c_types.CTypeNuitkaBools import CTypeNuitkaBoolEnum
from nuitka.codegen.c_types.CTypeNuitkaInts import CTypeNuitkaIntOrLongStruct
from nuitka.codegen.Reports import onMissingOperation
from nuitka.Options import isExperimental
from nuitka.PythonVersions import python_version

from .ControlFlowDescriptions import (
    ControlFlowDescriptionAddUnsupported,
    ControlFlowDescriptionBitandUnsupported,
    ControlFlowDescriptionBitorUnsupported,
    ControlFlowDescriptionBitxorUnsupported,
    ControlFlowDescriptionComparisonUnorderable,
    ControlFlowDescriptionElementBasedEscape,
    ControlFlowDescriptionFloorDivUnsupported,
    ControlFlowDescriptionLshiftUnsupported,
    ControlFlowDescriptionModUnsupported,
    ControlFlowDescriptionMulUnsupported,
    ControlFlowDescriptionNoEscape,
    ControlFlowDescriptionOldDivUnsupported,
    ControlFlowDescriptionPowUnsupported,
    ControlFlowDescriptionRshiftUnsupported,
    ControlFlowDescriptionSubUnsupported,
    ControlFlowDescriptionTrueDivUnsupported,
    ControlFlowDescriptionValueErrorNoEscape,
    ControlFlowDescriptionZeroDivisionNoEscape,
)
from .StandardShapes import (
    ShapeBase,
    ShapeIterator,
    ShapeLoopCompleteAlternative,
    ShapeLoopInitialAlternative,
    ShapeUnknown,
    operation_result_unknown,
)

# Updated later only, due to cyclic dependencies, make the dictionary
# available for reference use in class definition.
add_shapes_none = {}
sub_shapes_none = {}
mul_shapes_none = {}
floordiv_shapes_none = {}
truediv_shapes_none = {}
olddiv_shapes_none = {}
mod_shapes_none = {}
pow_shapes_none = {}
bitor_shapes_none = {}
bitand_shapes_none = {}
bitxor_shapes_none = {}
lshift_shapes_none = {}
rshift_shapes_none = {}


add_shapes_bool = {}
sub_shapes_bool = {}
mul_shapes_bool = {}
floordiv_shapes_bool = {}
truediv_shapes_bool = {}
olddiv_shapes_bool = {}
mod_shapes_bool = {}
pow_shapes_bool = {}
bitor_shapes_bool = {}
bitand_shapes_bool = {}
bitxor_shapes_bool = {}
lshift_shapes_bool = {}
rshift_shapes_bool = {}


add_shapes_int = {}
sub_shapes_int = {}
mul_shapes_int = {}
floordiv_shapes_int = {}
truediv_shapes_int = {}
olddiv_shapes_int = {}
mod_shapes_int = {}
pow_shapes_int = {}
bitor_shapes_int = {}
bitand_shapes_int = {}
bitxor_shapes_int = {}
lshift_shapes_int = {}
rshift_shapes_int = {}

add_shapes_long = {}
sub_shapes_long = {}
mul_shapes_long = {}
add_shapes_intorlong = {}
sub_shapes_intorlong = {}
mul_shapes_intorlong = {}
add_shapes_float = {}
sub_shapes_float = {}
mul_shapes_float = {}
add_shapes_complex = {}
sub_shapes_complex = {}
mul_shapes_complex = {}
add_shapes_tuple = {}
sub_shapes_tuple = {}
mul_shapes_tuple = {}
add_shapes_list = {}
sub_shapes_list = {}
mul_shapes_list = {}
add_shapes_set = {}
sub_shapes_set = {}
mul_shapes_set = {}
add_shapes_frozenset = {}
sub_shapes_frozenset = {}
mul_shapes_frozenset = {}
add_shapes_dict = {}
sub_shapes_dict = {}
mul_shapes_dict = mul_shapes_set  # Dicts do not multiply either
add_shapes_str = {}
sub_shapes_str = {}
mul_shapes_str = {}
add_shapes_bytes = {}
sub_shapes_bytes = {}
mul_shapes_bytes = {}
add_shapes_unicode = {}
sub_shapes_unicode = {}
mul_shapes_unicode = {}
add_shapes_strorunicode = {}
sub_shapes_strorunicode = {}
mul_shapes_strorunicode = {}
add_shapes_bytearray = {}
sub_shapes_bytearray = {}
mul_shapes_bytearray = {}


def _getComparisonLtShapeGeneric(cls, right_shape):
    if type(right_shape) is ShapeLoopCompleteAlternative:
        return right_shape.getComparisonLtLShape(cls)

    if type(right_shape) is ShapeLoopInitialAlternative:
        return operation_result_unknown

    onMissingOperation("Lt", cls, right_shape)
    return operation_result_unknown


class ShapeTypeNoneType(ShapeBase):
    typical_value = None

    @staticmethod
    def getTypeName():
        return "NoneType"

    @staticmethod
    def hasShapeSlotBool():
        return False

    @staticmethod
    def hasShapeSlotAbs():
        return False

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return False

    add_shapes = add_shapes_none
    sub_shapes = sub_shapes_none
    mul_shapes = mul_shapes_none
    mod_shapes = mod_shapes_none
    floordiv_shapes = floordiv_shapes_none
    truediv_shapes = truediv_shapes_none
    olddiv_shapes = olddiv_shapes_none
    pow_shapes = pow_shapes_none
    bitor_shapes = bitor_shapes_none
    bitand_shapes = bitand_shapes_none
    bitxor_shapes = bitxor_shapes_none
    lshift_shapes = lshift_shapes_none
    rshift_shapes = rshift_shapes_none

    if python_version < 300:

        @classmethod
        def getComparisonLtShape(cls, right_shape):
            if right_shape is ShapeUnknown:
                return operation_result_unknown

            if right_shape.getTypeName() is not None:
                return operation_result_bool_noescape

            if right_shape in (ShapeTypeIntOrLong, ShapeTypeStrOrUnicode):
                return operation_result_bool_noescape

            return _getComparisonLtShapeGeneric(cls, right_shape)

    else:

        @classmethod
        def getComparisonLtShape(cls, right_shape):
            if right_shape is ShapeUnknown:
                return operation_result_unknown

            # TODO: Actually unorderable, but this requires making a
            # difference with "=="
            # if right_shape.getTypeName() is not None:
            #     return operation_result_unorderable_comparison
            if right_shape is ShapeTypeStr:
                return operation_result_unknown

            return _getComparisonLtShapeGeneric(cls, right_shape)


class ShapeTypeBool(ShapeBase):
    typical_value = True

    @staticmethod
    def getTypeName():
        return "bool"

    @staticmethod
    def getCType():
        return CTypeNuitkaBoolEnum

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotAbs():
        return True

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return True

    @staticmethod
    def hasShapeSlotLong():
        return True

    @staticmethod
    def hasShapeSlotFloat():
        return True

    @staticmethod
    def hasShapeSlotComplex():
        return True

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return False

    add_shapes = add_shapes_bool
    sub_shapes = sub_shapes_bool
    mul_shapes = mul_shapes_bool
    floordiv_shapes = floordiv_shapes_bool
    truediv_shapes = truediv_shapes_bool
    olddiv_shapes = olddiv_shapes_bool
    mod_shapes = mod_shapes_bool
    pow_shapes = pow_shapes_bool
    bitor_shapes = bitor_shapes_bool
    bitand_shapes = bitand_shapes_bool
    bitxor_shapes = bitxor_shapes_bool
    lshift_shapes = lshift_shapes_bool
    rshift_shapes = rshift_shapes_bool

    @classmethod
    def getComparisonLtShape(cls, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        if right_shape in (
            ShapeTypeInt,
            ShapeTypeLong,
            ShapeTypeIntOrLong,
            ShapeTypeBool,
            ShapeTypeFloat,
        ):
            return operation_result_bool_noescape

        if right_shape is ShapeTypeIntOrLongDerived:
            return operation_result_unknown

        return _getComparisonLtShapeGeneric(cls, right_shape)


class ShapeTypeInt(ShapeBase):
    typical_value = 7

    @staticmethod
    def getTypeName():
        return "int"

    helper_code = "INT" if python_version < 300 else "LONG"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotAbs():
        return True

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return True

    @staticmethod
    def hasShapeSlotLong():
        return True

    @staticmethod
    def hasShapeSlotFloat():
        return True

    @staticmethod
    def hasShapeSlotComplex():
        return True

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return False

    add_shapes = add_shapes_int
    sub_shapes = sub_shapes_int
    mul_shapes = mul_shapes_int
    floordiv_shapes = floordiv_shapes_int
    truediv_shapes = truediv_shapes_int
    olddiv_shapes = olddiv_shapes_int
    mod_shapes = mod_shapes_int
    pow_shapes = pow_shapes_int
    bitor_shapes = bitor_shapes_int
    bitand_shapes = bitand_shapes_int
    bitxor_shapes = bitxor_shapes_int
    lshift_shapes = lshift_shapes_int
    rshift_shapes = rshift_shapes_int

    @classmethod
    def getComparisonLtShape(cls, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        if right_shape in (
            ShapeTypeInt,
            ShapeTypeLong,
            ShapeTypeIntOrLong,
            ShapeTypeBool,
            ShapeTypeFloat,
        ):
            return operation_result_bool_noescape

        if right_shape in (ShapeTypeLongDerived, ShapeTypeIntOrLongDerived):
            return operation_result_unknown

        return _getComparisonLtShapeGeneric(cls, right_shape)


if python_version < 300:

    class ShapeTypeLong(ShapeBase):
        typical_value = long(7)  # pylint: disable=I0021,undefined-variable

        @staticmethod
        def getTypeName():
            return "long"

        helper_code = "LONG" if python_version < 300 else "INVALID"

        @staticmethod
        def hasShapeSlotBool():
            return True

        @staticmethod
        def hasShapeSlotAbs():
            return True

        @staticmethod
        def hasShapeSlotLen():
            return False

        @staticmethod
        def hasShapeSlotInt():
            return True

        @staticmethod
        def hasShapeSlotLong():
            return True

        @staticmethod
        def hasShapeSlotFloat():
            return True

        @staticmethod
        def hasShapeSlotComplex():
            return True

        @staticmethod
        def hasShapeSlotIter():
            return False

        @staticmethod
        def hasShapeSlotNext():
            return False

        @staticmethod
        def hasShapeSlotContains():
            return False

        add_shapes = add_shapes_long
        sub_shapes = sub_shapes_long
        mul_shapes = mul_shapes_long

        @classmethod
        def getComparisonLtShape(cls, right_shape):
            if right_shape is ShapeUnknown:
                return operation_result_unknown

            if right_shape in (
                ShapeTypeInt,
                ShapeTypeLong,
                ShapeTypeIntOrLong,
                ShapeTypeBool,
                ShapeTypeFloat,
            ):
                return operation_result_bool_noescape

            if right_shape in (ShapeTypeLongDerived, ShapeTypeIntOrLongDerived):
                return operation_result_unknown

            return _getComparisonLtShapeGeneric(cls, right_shape)

    class ShapeTypeLongDerived(ShapeUnknown):
        @staticmethod
        def getTypeName():
            return None

    class ShapeTypeIntOrLong(ShapeBase):
        if isExperimental("nuitka_ilong"):

            @staticmethod
            def getCType():
                return CTypeNuitkaIntOrLongStruct

        @staticmethod
        def hasShapeSlotBool():
            return True

        @staticmethod
        def hasShapeSlotAbs():
            return True

        @staticmethod
        def hasShapeSlotLen():
            return False

        @staticmethod
        def hasShapeSlotInt():
            return True

        @staticmethod
        def hasShapeSlotLong():
            return True

        @staticmethod
        def hasShapeSlotFloat():
            return True

        @staticmethod
        def hasShapeSlotComplex():
            return True

        @staticmethod
        def hasShapeSlotIter():
            return False

        @staticmethod
        def hasShapeSlotNext():
            return False

        @staticmethod
        def hasShapeSlotContains():
            return False

        add_shapes = add_shapes_intorlong
        sub_shapes = sub_shapes_intorlong
        mul_shapes = mul_shapes_intorlong

        @classmethod
        def getComparisonLtShape(cls, right_shape):
            if right_shape is ShapeUnknown:
                return operation_result_unknown

            if right_shape in (
                ShapeTypeInt,
                ShapeTypeLong,
                ShapeTypeIntOrLong,
                ShapeTypeBool,
                ShapeTypeFloat,
            ):
                return operation_result_bool_noescape

            if right_shape is ShapeTypeIntOrLongDerived:
                return operation_result_unknown

            return _getComparisonLtShapeGeneric(cls, right_shape)


else:
    ShapeTypeLong = None
    ShapeTypeLongDerived = None
    ShapeTypeIntOrLong = ShapeTypeInt


class ShapeTypeIntOrLongDerived(ShapeUnknown):
    pass


class ShapeTypeFloat(ShapeBase):
    typical_value = 0.1

    @staticmethod
    def getTypeName():
        return "float"

    helper_code = "FLOAT"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotAbs():
        return True

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return True

    @staticmethod
    def hasShapeSlotLong():
        return True

    @staticmethod
    def hasShapeSlotFloat():
        return True

    @staticmethod
    def hasShapeSlotComplex():
        return True

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return False

    add_shapes = add_shapes_float
    sub_shapes = sub_shapes_float
    mul_shapes = mul_shapes_float

    @classmethod
    def getComparisonLtShape(cls, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        if right_shape in (
            ShapeTypeFloat,
            ShapeTypeLong,
            ShapeTypeInt,
            ShapeTypeIntOrLong,
            ShapeTypeBool,
        ):
            return operation_result_bool_noescape

        if right_shape is ShapeTypeFloatDerived:
            return operation_result_unknown

        return _getComparisonLtShapeGeneric(cls, right_shape)


class ShapeTypeFloatDerived(ShapeUnknown):
    pass


class ShapeTypeComplex(ShapeBase):
    typical_value = 0j

    @staticmethod
    def getTypeName():
        return "complex"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotAbs():
        return True

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return True

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return False

    add_shapes = add_shapes_complex
    sub_shapes = sub_shapes_complex
    mul_shapes = mul_shapes_complex

    # TODO: No < for complex


class ShapeTypeTuple(ShapeBase):
    typical_value = ()

    @staticmethod
    def getTypeName():
        return "tuple"

    helper_code = "TUPLE"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotAbs():
        return False

    @staticmethod
    def hasShapeSlotLen():
        return True

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return True

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def getShapeIter():
        return ShapeTypeTupleIterator

    @staticmethod
    def hasShapeSlotContains():
        return True

    add_shapes = add_shapes_tuple
    sub_shapes = sub_shapes_tuple
    mul_shapes = mul_shapes_tuple

    @classmethod
    def getComparisonLtShape(cls, right_shape):
        # Need to consider value shape for this.
        return operation_result_unknown


class ShapeTypeTupleIterator(ShapeIterator):
    typical_value = iter(ShapeTypeTuple.typical_value)

    @staticmethod
    def getTypeName():
        return "tupleiterator" if python_version < 300 else "tuple_iterator"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotLen():
        return False


class ShapeTypeList(ShapeBase):
    typical_value = []

    @staticmethod
    def getTypeName():
        return "list"

    helper_code = "LIST"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotAbs():
        return False

    @staticmethod
    def hasShapeSlotLen():
        return True

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return True

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def getShapeIter():
        return ShapeTypeListIterator

    @staticmethod
    def hasShapeSlotContains():
        return True

    add_shapes = add_shapes_list
    sub_shapes = sub_shapes_list
    mul_shapes = mul_shapes_list

    @classmethod
    def getComparisonLtShape(cls, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        # Need to consider value shape for this.
        if right_shape in (ShapeTypeList, ShapeTypeTuple):
            return operation_result_bool_elementbased

        if right_shape is ShapeTypeXrange:
            if python_version < 300:
                return operation_result_bool_elementbased
            else:
                # TODO: Actually unorderable, but this requires making a
                # difference with "=="
                return operation_result_unknown

        return _getComparisonLtShapeGeneric(cls, right_shape)


class ShapeTypeListIterator(ShapeIterator):
    typical_value = iter(ShapeTypeList.typical_value)

    @staticmethod
    def getTypeName():
        return "listiterator" if python_version < 300 else "list_iterator"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotLen():
        return False


class ShapeTypeSet(ShapeBase):
    typical_value = set()

    @staticmethod
    def getTypeName():
        return "set"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotAbs():
        return False

    @staticmethod
    def hasShapeSlotLen():
        return True

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return True

    @staticmethod
    def getShapeIter():
        return ShapeTypeSetIterator

    @staticmethod
    def hasShapeSlotContains():
        return True

    add_shapes = add_shapes_set
    sub_shapes = sub_shapes_set
    mul_shapes = mul_shapes_set

    @classmethod
    def getComparisonLtShape(cls, right_shape):
        # Need to consider value shape for this.
        return operation_result_unknown


class ShapeTypeSetIterator(ShapeIterator):
    typical_value = iter(ShapeTypeSet.typical_value)

    @staticmethod
    def getTypeName():
        return "setiterator" if python_version < 300 else "set_iterator"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotLen():
        return False


class ShapeTypeFrozenset(ShapeBase):
    typical_value = frozenset()

    @staticmethod
    def getTypeName():
        return "frozenset"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotAbs():
        return False

    @staticmethod
    def hasShapeSlotLen():
        return True

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return True

    @staticmethod
    def getShapeIter():
        return ShapeTypeSetIterator

    @staticmethod
    def hasShapeSlotContains():
        return True

    add_shapes = add_shapes_frozenset
    sub_shapes = sub_shapes_frozenset
    mul_shapes = mul_shapes_frozenset


class ShapeTypeDict(ShapeBase):
    typical_value = {}

    @staticmethod
    def getTypeName():
        return "dict"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotAbs():
        return False

    @staticmethod
    def hasShapeSlotLen():
        return True

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return True

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def getShapeIter():
        return ShapeTypeDictIterator

    @staticmethod
    def hasShapeSlotContains():
        return True

    add_shapes = add_shapes_dict
    sub_shapes = sub_shapes_dict
    mul_shapes = mul_shapes_dict

    @classmethod
    def getComparisonLtShape(cls, right_shape):
        # Need to consider value shape for this

        # TODO: Could return bool with annotation that exception is still
        # possible..
        return operation_result_unknown


class ShapeTypeDictIterator(ShapeIterator):
    typical_value = iter(ShapeTypeDict.typical_value)

    @staticmethod
    def getTypeName():
        return "dictionary-keyiterator" if python_version < 300 else "dictkey_iterator"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotLen():
        return False


class ShapeTypeStr(ShapeBase):
    typical_value = "a"

    @staticmethod
    def getTypeName():
        return "str"

    helper_code = "STR" if python_version < 300 else "UNICODE"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotAbs():
        return False

    @staticmethod
    def hasShapeSlotLen():
        return True

    @staticmethod
    def hasShapeSlotInt():
        return True

    @staticmethod
    def hasShapeSlotLong():
        return True

    @staticmethod
    def hasShapeSlotFloat():
        return True

    @staticmethod
    def hasShapeSlotComplex():
        return True

    @staticmethod
    def hasShapeSlotIter():
        return True

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def getShapeIter():
        return ShapeTypeStrIterator

    @staticmethod
    def hasShapeSlotContains():
        return True

    add_shapes = add_shapes_str
    sub_shapes = sub_shapes_str
    mul_shapes = mul_shapes_str

    @classmethod
    def getComparisonLtShape(cls, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        if right_shape is ShapeTypeStr:
            return operation_result_bool_noescape

        if right_shape is ShapeTypeStrDerived:
            return operation_result_unknown

        if right_shape is ShapeTypeBytearray:
            if python_version < 300:
                return operation_result_bool_noescape
            else:
                return operation_result_unknown

        return _getComparisonLtShapeGeneric(cls, right_shape)


class ShapeTypeStrDerived(ShapeUnknown):
    pass


class ShapeTypeStrIterator(ShapeIterator):
    tyical_value = iter(ShapeTypeStr.typical_value)

    @staticmethod
    def getTypeName():
        return "iterator" if python_version < 300 else "str_iterator"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotLen():
        return False


if python_version < 300:

    class ShapeTypeUnicode(ShapeBase):
        typical_value = u"a"

        @staticmethod
        def getTypeName():
            return "unicode"

        helper_code = "UNICODE"

        @staticmethod
        def hasShapeSlotBool():
            return True

        @staticmethod
        def hasShapeSlotAbs():
            return False

        @staticmethod
        def hasShapeSlotLen():
            return True

        @staticmethod
        def hasShapeSlotInt():
            return True

        @staticmethod
        def hasShapeSlotLong():
            return True

        @staticmethod
        def hasShapeSlotFloat():
            return True

        @staticmethod
        def hasShapeSlotComplex():
            return True

        @staticmethod
        def hasShapeSlotIter():
            return True

        @staticmethod
        def hasShapeSlotNext():
            return False

        @staticmethod
        def getShapeIter():
            return ShapeTypeUnicodeIterator

        @staticmethod
        def hasShapeSlotContains():
            return True

        add_shapes = add_shapes_unicode
        sub_shapes = sub_shapes_unicode
        mul_shapes = mul_shapes_unicode

        @classmethod
        def getComparisonLtShape(cls, right_shape):
            if right_shape is ShapeUnknown:
                return operation_result_unknown

            if right_shape is ShapeTypeUnicode:
                return operation_result_bool_noescape

            if right_shape is ShapeTypeUnicodeDerived:
                return operation_result_unknown

            return _getComparisonLtShapeGeneric(cls, right_shape)

    class ShapeTypeUnicodeDerived(ShapeUnknown):
        pass

    class ShapeTypeUnicodeIterator(ShapeIterator):
        typical_value = iter(ShapeTypeUnicode.typical_value)

        @staticmethod
        def getTypeName():
            return "iterator"

        @staticmethod
        def hasShapeSlotBool():
            return True

        @staticmethod
        def hasShapeSlotLen():
            return False


else:
    ShapeTypeUnicode = ShapeTypeStr
    ShapeTypeUnicodeIterator = ShapeTypeStrIterator
    ShapeTypeUnicodeDerived = ShapeTypeStrDerived


if python_version < 300:

    class ShapeTypeStrOrUnicode(ShapeBase):
        @staticmethod
        def hasShapeSlotBool():
            return True

        @staticmethod
        def hasShapeSlotAbs():
            return False

        @staticmethod
        def hasShapeSlotLen():
            return True

        @staticmethod
        def hasShapeSlotInt():
            return True

        @staticmethod
        def hasShapeSlotLong():
            return True

        @staticmethod
        def hasShapeSlotFloat():
            return True

        @staticmethod
        def hasShapeSlotComplex():
            return True

        @staticmethod
        def hasShapeSlotIter():
            return True

        @staticmethod
        def hasShapeSlotNext():
            return False

        @staticmethod
        def hasShapeSlotContains():
            return True

        add_shapes = add_shapes_strorunicode
        sub_shapes = sub_shapes_strorunicode
        mul_shapes = mul_shapes_strorunicode


else:
    ShapeTypeStrOrUnicode = ShapeTypeStr


if python_version >= 300:

    class ShapeTypeBytes(ShapeBase):
        typical_value = b"b"

        @staticmethod
        def getTypeName():
            return "bytes"

        helper_code = "BYTES"

        @staticmethod
        def hasShapeSlotBool():
            return True

        @staticmethod
        def hasShapeSlotAbs():
            return False

        @staticmethod
        def hasShapeSlotLen():
            return True

        @staticmethod
        def hasShapeSlotInt():
            return False

        @staticmethod
        def hasShapeSlotLong():
            return False

        @staticmethod
        def hasShapeSlotFloat():
            return True

        @staticmethod
        def hasShapeSlotComplex():
            return False

        @staticmethod
        def hasShapeSlotIter():
            return True

        @staticmethod
        def hasShapeSlotNext():
            return False

        @staticmethod
        def getShapeIter():
            return ShapeTypeBytesIterator

        @staticmethod
        def hasShapeSlotContains():
            return True

        add_shapes = add_shapes_bytes
        sub_shapes = sub_shapes_bytes
        mul_shapes = mul_shapes_bytes

        @classmethod
        def getComparisonLtShape(cls, right_shape):
            if right_shape is ShapeUnknown:
                return operation_result_unknown

            if right_shape is ShapeTypeBytes:
                return operation_result_bool_noescape

            if right_shape is ShapeTypeBytesDerived:
                return operation_result_unknown

            return _getComparisonLtShapeGeneric(cls, right_shape)

    class ShapeTypeBytesDerived(ShapeUnknown):
        pass

    class ShapeTypeBytesIterator(ShapeIterator):
        typical_value = iter(ShapeTypeBytes.typical_value)

        @staticmethod
        def getTypeName():
            return "bytes_iterator"

        @staticmethod
        def hasShapeSlotBool():
            return True

        @staticmethod
        def hasShapeSlotLen():
            return False


else:
    # Shouldn't happen with Python2
    ShapeTypeBytes = None
    ShapeTypeBytesIterator = None

    ShapeTypeBytesDerived = None


class ShapeTypeBytearray(ShapeBase):
    typical_value = bytearray(b"b")

    @staticmethod
    def getTypeName():
        return "bytearray"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotAbs():
        return False

    @staticmethod
    def hasShapeSlotLen():
        return True

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return True

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def getShapeIter():
        return ShapeTypeBytearrayIterator

    @staticmethod
    def hasShapeSlotContains():
        return True

    add_shapes = add_shapes_bytearray
    sub_shapes = sub_shapes_bytearray
    mul_shapes = mul_shapes_bytearray

    @classmethod
    def getComparisonLtShape(cls, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        if right_shape in (ShapeTypeBytearray, ShapeTypeBytes):
            return operation_result_bool_noescape

        if right_shape is ShapeTypeStr:
            if python_version < 300:
                return operation_result_bool_noescape
            else:
                # TODO: Exception actually for static optimization.
                return operation_result_unknown

        return _getComparisonLtShapeGeneric(cls, right_shape)


class ShapeTypeBytearrayIterator(ShapeIterator):
    typical_value = iter(ShapeTypeBytearray.typical_value)

    @staticmethod
    def getTypeName():
        return "bytearray_iterator"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotLen():
        return False


class ShapeTypeEllipsisType(ShapeBase):
    typical_value = Ellipsis

    @staticmethod
    def getTypeName():
        return "ellipsis"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotAbs():
        return False

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return True


class ShapeTypeSlice(ShapeBase):
    typical_value = slice(7)

    @staticmethod
    def getTypeName():
        return "slice"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotAbs():
        return False

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return False


class ShapeTypeXrange(ShapeBase):
    typical_value = (
        xrange(1)  # pylint: disable=I0021,undefined-variable
        if python_version < 300
        else range(1)
    )

    @staticmethod
    def getTypeName():
        return "xrange" if python_version < 300 else "range"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotAbs():
        return False

    @staticmethod
    def hasShapeSlotLen():
        return True

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return True

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def getShapeIter():
        return ShapeTypeXrangeIterator

    @staticmethod
    def hasShapeSlotContains():
        return True

    @classmethod
    def getComparisonLtShape(cls, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        # TODO: Maybe split in two shapes, they are quite different in the
        # end when it comes to operations.
        if python_version < 300:
            # Need to consider value shape for this.
            if right_shape in (ShapeTypeList, ShapeTypeTuple):
                return operation_result_bool_elementbased

            if right_shape is ShapeTypeXrange:
                return operation_result_bool_elementbased
        else:
            # TODO: Actually unorderable, but this requires making a
            # difference with "=="
            return operation_result_unknown

        return _getComparisonLtShapeGeneric(cls, right_shape)


class ShapeTypeXrangeIterator(ShapeIterator):
    typical_value = iter(ShapeTypeXrange.typical_value)

    @staticmethod
    def getTypeName():
        return "rangeiterator" if python_version < 300 else "range_iterator"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotLen():
        return False


class ShapeTypeType(ShapeBase):
    typical_value = int

    @staticmethod
    def getTypeName():
        return "type"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotAbs():
        return False

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return False

    @classmethod
    def getComparisonLtShape(cls, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        if right_shape is ShapeTypeType:
            return ShapeUnknown, ControlFlowDescriptionNoEscape

        return _getComparisonLtShapeGeneric(cls, right_shape)


class ShapeTypeModule(ShapeBase):
    typical_value = __import__("sys")

    @staticmethod
    def getTypeName():
        return "module"

    @staticmethod
    def hasShapeModule():
        return True

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotAbs():
        return False

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return False


class ShapeTypeBuiltinModule(ShapeTypeModule):
    typical_value = __import__("_ctypes")


class ShapeTypeFile(ShapeBase):
    typical_value = __import__("sys").stdout

    @staticmethod
    def getTypeName():
        return "file"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotAbs():
        return False

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return True

    @staticmethod
    def hasShapeSlotNext():
        return True

    @staticmethod
    def hasShapeSlotContains():
        return True


class ShapeTypeStaticmethod(ShapeBase):
    # TODO: Add typical value.

    @staticmethod
    def getTypeName():
        return "staticmethod"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotAbs():
        return False

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return False


class ShapeTypeClassmethod(ShapeBase):
    # TODO: Add typical value.

    @staticmethod
    def getTypeName():
        return "classmethod"

    @staticmethod
    def hasShapeSlotBool():
        return True

    @staticmethod
    def hasShapeSlotAbs():
        return False

    @staticmethod
    def hasShapeSlotLen():
        return False

    @staticmethod
    def hasShapeSlotInt():
        return False

    @staticmethod
    def hasShapeSlotLong():
        return False

    @staticmethod
    def hasShapeSlotFloat():
        return False

    @staticmethod
    def hasShapeSlotComplex():
        return False

    @staticmethod
    def hasShapeSlotIter():
        return False

    @staticmethod
    def hasShapeSlotNext():
        return False

    @staticmethod
    def hasShapeSlotContains():
        return False


# Precanned tuples to save creating return value tuples:
operation_result_bool_noescape = ShapeTypeBool, ControlFlowDescriptionNoEscape
operation_result_float_noescape = ShapeTypeFloat, ControlFlowDescriptionNoEscape
operation_result_int_noescape = ShapeTypeInt, ControlFlowDescriptionNoEscape
operation_result_long_noescape = ShapeTypeLong, ControlFlowDescriptionNoEscape
operation_result_intorlong_noescape = ShapeTypeIntOrLong, ControlFlowDescriptionNoEscape
operation_result_complex_noescape = ShapeTypeComplex, ControlFlowDescriptionNoEscape
operation_result_tuple_noescape = ShapeTypeTuple, ControlFlowDescriptionNoEscape
operation_result_list_noescape = ShapeTypeList, ControlFlowDescriptionNoEscape
operation_result_set_noescape = ShapeTypeSet, ControlFlowDescriptionNoEscape
operation_result_frozenset_noescape = ShapeTypeFrozenset, ControlFlowDescriptionNoEscape
operation_result_str_noescape = ShapeTypeStr, ControlFlowDescriptionNoEscape
operation_result_unicode_noescape = ShapeTypeUnicode, ControlFlowDescriptionNoEscape
operation_result_strorunicode_noescape = (
    ShapeTypeStrOrUnicode,
    ControlFlowDescriptionNoEscape,
)
operation_result_bytes_noescape = ShapeTypeBytes, ControlFlowDescriptionNoEscape
operation_result_bytearray_noescape = ShapeTypeBytearray, ControlFlowDescriptionNoEscape

operation_result_bool_elementbased = (
    ShapeTypeBool,
    ControlFlowDescriptionElementBasedEscape,
)

operation_result_unorderable_comparison = (
    ShapeUnknown,
    ControlFlowDescriptionComparisonUnorderable,
)

operation_result_unsupported_add = ShapeUnknown, ControlFlowDescriptionAddUnsupported
operation_result_unsupported_sub = ShapeUnknown, ControlFlowDescriptionSubUnsupported
operation_result_unsupported_mul = ShapeUnknown, ControlFlowDescriptionMulUnsupported
operation_result_unsupported_floordiv = (
    ShapeUnknown,
    ControlFlowDescriptionFloorDivUnsupported,
)
operation_result_unsupported_truediv = (
    ShapeUnknown,
    ControlFlowDescriptionTrueDivUnsupported,
)
operation_result_unsupported_olddiv = (
    ShapeUnknown,
    ControlFlowDescriptionOldDivUnsupported,
)
operation_result_unsupported_mod = ShapeUnknown, ControlFlowDescriptionModUnsupported
operation_result_unsupported_pow = ShapeUnknown, ControlFlowDescriptionPowUnsupported
operation_result_unsupported_bitor = (
    ShapeUnknown,
    ControlFlowDescriptionBitorUnsupported,
)
operation_result_unsupported_bitand = (
    ShapeUnknown,
    ControlFlowDescriptionBitandUnsupported,
)
operation_result_unsupported_bitxor = (
    ShapeUnknown,
    ControlFlowDescriptionBitxorUnsupported,
)
operation_result_unsupported_lshift = (
    ShapeUnknown,
    ControlFlowDescriptionLshiftUnsupported,
)
operation_result_unsupported_rshift = (
    ShapeUnknown,
    ControlFlowDescriptionRshiftUnsupported,
)

# ZeroDivisionError can occur for some module and division operations, otherwise they
# are fixed type.
operation_result_zerodiv_int = ShapeTypeInt, ControlFlowDescriptionZeroDivisionNoEscape
operation_result_zerodiv_long = (
    ShapeTypeLong,
    ControlFlowDescriptionZeroDivisionNoEscape,
)
operation_result_zerodiv_intorlong = (
    ShapeTypeIntOrLong,
    ControlFlowDescriptionZeroDivisionNoEscape,
)
operation_result_zerodiv_float = (
    ShapeTypeFloat,
    ControlFlowDescriptionZeroDivisionNoEscape,
)
operation_result_zerodiv_complex = (
    ShapeTypeComplex,
    ControlFlowDescriptionZeroDivisionNoEscape,
)

operation_result_valueerror_intorlong = (
    ShapeTypeIntOrLong,
    ControlFlowDescriptionValueErrorNoEscape,
)
operation_result_valueerror_long = (
    ShapeTypeLong,
    ControlFlowDescriptionValueErrorNoEscape,
)

add_shapes_none.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # None really hates everything concrete for all operations.
        ShapeTypeInt: operation_result_unsupported_add,
        ShapeTypeLong: operation_result_unsupported_add,
        ShapeTypeIntOrLong: operation_result_unsupported_add,
        ShapeTypeBool: operation_result_unsupported_add,
        ShapeTypeLong: operation_result_unsupported_add,
        ShapeTypeFloat: operation_result_unsupported_add,
        ShapeTypeComplex: operation_result_unsupported_add,
        # Sequence repeat:
        ShapeTypeStr: operation_result_unsupported_add,
        ShapeTypeBytes: operation_result_unsupported_add,
        ShapeTypeBytearray: operation_result_unsupported_add,
        ShapeTypeUnicode: operation_result_unsupported_add,
        ShapeTypeTuple: operation_result_unsupported_add,
        ShapeTypeList: operation_result_unsupported_add,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_add,
        ShapeTypeDict: operation_result_unsupported_add,
        ShapeTypeNoneType: operation_result_unsupported_add,
    }
)


def cloneWithUnsupportedChange(op_shapes, operation_result_unsupported):
    r = {}

    for key, value in op_shapes.items():
        if value[1].getExceptionExit() is TypeError:
            value = operation_result_unsupported

        r[key] = value

    return r


sub_shapes_none.update(
    cloneWithUnsupportedChange(add_shapes_none, operation_result_unsupported_sub)
)
mul_shapes_none.update(
    cloneWithUnsupportedChange(add_shapes_none, operation_result_unsupported_mul)
)
floordiv_shapes_none.update(
    cloneWithUnsupportedChange(add_shapes_none, operation_result_unsupported_floordiv)
)
truediv_shapes_none.update(
    cloneWithUnsupportedChange(add_shapes_none, operation_result_unsupported_truediv)
)
olddiv_shapes_none.update(
    cloneWithUnsupportedChange(add_shapes_none, operation_result_unsupported_olddiv)
)
mod_shapes_none.update(
    cloneWithUnsupportedChange(add_shapes_none, operation_result_unsupported_mod)
)
bitor_shapes_none.update(
    cloneWithUnsupportedChange(add_shapes_none, operation_result_unsupported_bitor)
)
bitand_shapes_none.update(
    cloneWithUnsupportedChange(add_shapes_none, operation_result_unsupported_bitand)
)
bitxor_shapes_none.update(
    cloneWithUnsupportedChange(add_shapes_none, operation_result_unsupported_bitxor)
)
lshift_shapes_none.update(
    cloneWithUnsupportedChange(add_shapes_none, operation_result_unsupported_lshift)
)
rshift_shapes_none.update(
    cloneWithUnsupportedChange(add_shapes_none, operation_result_unsupported_rshift)
)

add_shapes_bool.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int keep their type, as bool is 0 or 1 int.
        ShapeTypeInt: operation_result_intorlong_noescape,
        ShapeTypeLong: operation_result_long_noescape,
        ShapeTypeIntOrLong: operation_result_intorlong_noescape,
        ShapeTypeBool: operation_result_int_noescape,
        ShapeTypeLong: operation_result_long_noescape,
        ShapeTypeFloat: operation_result_float_noescape,
        ShapeTypeComplex: operation_result_complex_noescape,
        # Sequence repeat:
        ShapeTypeStr: operation_result_unsupported_add,
        ShapeTypeBytes: operation_result_unsupported_add,
        ShapeTypeBytearray: operation_result_unsupported_add,
        ShapeTypeUnicode: operation_result_unsupported_add,
        ShapeTypeTuple: operation_result_unsupported_add,
        ShapeTypeList: operation_result_unsupported_add,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_add,
        ShapeTypeDict: operation_result_unsupported_add,
        ShapeTypeNoneType: operation_result_unsupported_add,
    }
)

sub_shapes_bool.update(
    cloneWithUnsupportedChange(add_shapes_bool, operation_result_unsupported_sub)
)


mul_shapes_bool.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int keep their type, as bool is 0 or 1 int.
        ShapeTypeInt: operation_result_int_noescape,
        ShapeTypeLong: operation_result_long_noescape,
        ShapeTypeIntOrLong: operation_result_intorlong_noescape,
        ShapeTypeBool: operation_result_int_noescape,
        ShapeTypeFloat: operation_result_float_noescape,
        ShapeTypeComplex: operation_result_complex_noescape,
        # Sequence repeat:
        ShapeTypeStr: operation_result_str_noescape,
        ShapeTypeBytes: operation_result_bytes_noescape,
        ShapeTypeBytearray: operation_result_bytearray_noescape,
        ShapeTypeUnicode: operation_result_unicode_noescape,
        ShapeTypeTuple: operation_result_tuple_noescape,
        ShapeTypeList: operation_result_list_noescape,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_mul,
        ShapeTypeDict: operation_result_unsupported_mul,
        ShapeTypeNoneType: operation_result_unsupported_mul,
    }
)

floordiv_shapes_bool.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Ints do math
        ShapeTypeInt: operation_result_zerodiv_int,
        ShapeTypeLong: operation_result_zerodiv_long,
        ShapeTypeIntOrLong: operation_result_zerodiv_intorlong,
        ShapeTypeBool: operation_result_zerodiv_int,
        ShapeTypeFloat: operation_result_zerodiv_float,
        ShapeTypeComplex: operation_result_zerodiv_complex,
        # Unsupported:
        ShapeTypeStr: operation_result_unsupported_floordiv,
        ShapeTypeBytes: operation_result_unsupported_floordiv,
        ShapeTypeBytearray: operation_result_unsupported_floordiv,
        ShapeTypeUnicode: operation_result_unsupported_floordiv,
        ShapeTypeTuple: operation_result_unsupported_floordiv,
        ShapeTypeList: operation_result_unsupported_floordiv,
        ShapeTypeSet: operation_result_unsupported_floordiv,
        ShapeTypeDict: operation_result_unsupported_floordiv,
        ShapeTypeNoneType: operation_result_unsupported_floordiv,
    }
)

truediv_shapes_bool.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Bool act mostly like 0 or 1 int.
        ShapeTypeInt: operation_result_zerodiv_float,
        ShapeTypeLong: operation_result_zerodiv_float,
        ShapeTypeIntOrLong: operation_result_zerodiv_float,
        ShapeTypeBool: operation_result_zerodiv_float,
        ShapeTypeFloat: operation_result_zerodiv_float,
        ShapeTypeComplex: operation_result_zerodiv_complex,
        # Unsupported:
        ShapeTypeStr: operation_result_unsupported_truediv,
        ShapeTypeBytes: operation_result_unsupported_truediv,
        ShapeTypeBytearray: operation_result_unsupported_truediv,
        ShapeTypeUnicode: operation_result_unsupported_truediv,
        ShapeTypeTuple: operation_result_unsupported_truediv,
        ShapeTypeList: operation_result_unsupported_truediv,
        ShapeTypeSet: operation_result_unsupported_truediv,
        ShapeTypeDict: operation_result_unsupported_truediv,
        ShapeTypeNoneType: operation_result_unsupported_truediv,
    }
)

olddiv_shapes_bool.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Bool act mostly like 0 or 1 int.
        ShapeTypeInt: operation_result_zerodiv_int,
        ShapeTypeLong: operation_result_zerodiv_long,
        ShapeTypeIntOrLong: operation_result_zerodiv_intorlong,
        ShapeTypeBool: operation_result_zerodiv_int,
        ShapeTypeFloat: operation_result_zerodiv_float,
        ShapeTypeComplex: operation_result_zerodiv_complex,
        # Unsupported:
        ShapeTypeStr: operation_result_unsupported_olddiv,
        ShapeTypeBytes: operation_result_unsupported_olddiv,
        ShapeTypeBytearray: operation_result_unsupported_olddiv,
        ShapeTypeUnicode: operation_result_unsupported_olddiv,
        ShapeTypeTuple: operation_result_unsupported_olddiv,
        ShapeTypeList: operation_result_unsupported_olddiv,
        ShapeTypeSet: operation_result_unsupported_olddiv,
        ShapeTypeDict: operation_result_unsupported_olddiv,
        ShapeTypeNoneType: operation_result_unsupported_olddiv,
    }
)

mod_shapes_bool.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int keep their type, as bool is 0 or 1 int.
        ShapeTypeInt: operation_result_zerodiv_int,
        ShapeTypeLong: operation_result_zerodiv_long,
        ShapeTypeIntOrLong: operation_result_zerodiv_intorlong,
        ShapeTypeBool: operation_result_zerodiv_int,
        ShapeTypeFloat: operation_result_zerodiv_float,
        ShapeTypeComplex: operation_result_unsupported_mod,
        # Unsupported:
        ShapeTypeStr: operation_result_unsupported_mod,
        ShapeTypeBytes: operation_result_unsupported_mod,
        ShapeTypeBytearray: operation_result_unsupported_mod,
        ShapeTypeUnicode: operation_result_unsupported_mod,
        ShapeTypeTuple: operation_result_unsupported_mod,
        ShapeTypeList: operation_result_unsupported_mod,
        ShapeTypeSet: operation_result_unsupported_mod,
        ShapeTypeDict: operation_result_unsupported_mod,
        ShapeTypeNoneType: operation_result_unsupported_mod,
    }
)

pow_shapes_bool.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int keep their type, as bool is 0 or 1 int.
        ShapeTypeInt: operation_result_unknown,  # TODO: operation_result_intorfloat,
        ShapeTypeLong: operation_result_unknown,  # TODO: operation_result_longorfloat,
        ShapeTypeIntOrLong: operation_result_unknown,  # TODO: operation_result_intorlongorfloat,
        ShapeTypeBool: operation_result_int_noescape,
        ShapeTypeFloat: operation_result_float_noescape,
        ShapeTypeComplex: operation_result_complex_noescape,
        # Unsupported:
        ShapeTypeStr: operation_result_unsupported_pow,
        ShapeTypeBytes: operation_result_unsupported_pow,
        ShapeTypeBytearray: operation_result_unsupported_pow,
        ShapeTypeUnicode: operation_result_unsupported_pow,
        ShapeTypeTuple: operation_result_unsupported_pow,
        ShapeTypeList: operation_result_unsupported_pow,
        ShapeTypeSet: operation_result_unsupported_pow,
        ShapeTypeDict: operation_result_unsupported_pow,
        ShapeTypeNoneType: operation_result_unsupported_pow,
    }
)

bitor_shapes_bool.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int keep their type, as bool is 0 or 1 int.
        ShapeTypeInt: operation_result_int_noescape,
        ShapeTypeLong: operation_result_long_noescape,
        ShapeTypeIntOrLong: operation_result_intorlong_noescape,
        ShapeTypeBool: operation_result_bool_noescape,
        # Unsupported:
        ShapeTypeFloat: operation_result_unsupported_bitor,
        ShapeTypeComplex: operation_result_unsupported_bitor,
        ShapeTypeStr: operation_result_unsupported_bitor,
        ShapeTypeBytes: operation_result_unsupported_bitor,
        ShapeTypeBytearray: operation_result_unsupported_bitor,
        ShapeTypeUnicode: operation_result_unsupported_bitor,
        ShapeTypeTuple: operation_result_unsupported_bitor,
        ShapeTypeList: operation_result_unsupported_bitor,
        ShapeTypeSet: operation_result_unsupported_bitor,
        ShapeTypeDict: operation_result_unsupported_bitor,
        ShapeTypeNoneType: operation_result_unsupported_bitor,
    }
)

bitand_shapes_bool.update(
    cloneWithUnsupportedChange(bitor_shapes_bool, operation_result_unsupported_bitand)
)
bitxor_shapes_bool.update(
    cloneWithUnsupportedChange(bitor_shapes_bool, operation_result_unsupported_bitand)
)

lshift_shapes_bool.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int keep their type, as bool is 0 or 1 int.
        ShapeTypeInt: operation_result_valueerror_intorlong,
        ShapeTypeLong: operation_result_valueerror_long,
        ShapeTypeIntOrLong: operation_result_valueerror_intorlong,
        ShapeTypeBool: operation_result_valueerror_intorlong,
        # Unsupported:
        ShapeTypeFloat: operation_result_unsupported_lshift,
        ShapeTypeComplex: operation_result_unsupported_lshift,
        ShapeTypeStr: operation_result_unsupported_lshift,
        ShapeTypeBytes: operation_result_unsupported_lshift,
        ShapeTypeBytearray: operation_result_unsupported_lshift,
        ShapeTypeUnicode: operation_result_unsupported_lshift,
        ShapeTypeTuple: operation_result_unsupported_lshift,
        ShapeTypeList: operation_result_unsupported_lshift,
        ShapeTypeSet: operation_result_unsupported_lshift,
        ShapeTypeDict: operation_result_unsupported_lshift,
        ShapeTypeNoneType: operation_result_unsupported_lshift,
    }
)
rshift_shapes_bool.update(
    cloneWithUnsupportedChange(lshift_shapes_bool, operation_result_unsupported_rshift)
)


add_shapes_int.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int might turn into long when growing due to possible overflow.
        ShapeTypeInt: operation_result_intorlong_noescape,
        ShapeTypeLong: operation_result_long_noescape,
        ShapeTypeIntOrLong: operation_result_intorlong_noescape,
        ShapeTypeBool: operation_result_intorlong_noescape,
        ShapeTypeFloat: operation_result_float_noescape,
        ShapeTypeComplex: operation_result_complex_noescape,
        # Unsupported:
        ShapeTypeStr: operation_result_unsupported_add,
        ShapeTypeBytes: operation_result_unsupported_add,
        ShapeTypeBytearray: operation_result_unsupported_add,
        ShapeTypeUnicode: operation_result_unsupported_add,
        ShapeTypeTuple: operation_result_unsupported_add,
        ShapeTypeList: operation_result_unsupported_add,
        ShapeTypeSet: operation_result_unsupported_add,
        ShapeTypeDict: operation_result_unsupported_add,
        ShapeTypeNoneType: operation_result_unsupported_add,
    }
)

sub_shapes_int.update(
    cloneWithUnsupportedChange(add_shapes_int, operation_result_unsupported_sub)
)

mul_shapes_int.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int might turn into long when growing due to possible overflow.
        ShapeTypeInt: operation_result_intorlong_noescape,
        ShapeTypeLong: operation_result_long_noescape,
        ShapeTypeIntOrLong: operation_result_intorlong_noescape,
        ShapeTypeBool: operation_result_int_noescape,  # cannot overflow
        ShapeTypeFloat: operation_result_float_noescape,
        ShapeTypeComplex: operation_result_complex_noescape,
        # Sequence repeat:
        ShapeTypeStr: operation_result_str_noescape,
        ShapeTypeBytes: operation_result_bytes_noescape,
        ShapeTypeBytearray: operation_result_bytearray_noescape,
        ShapeTypeUnicode: operation_result_unicode_noescape,
        ShapeTypeTuple: operation_result_tuple_noescape,
        ShapeTypeList: operation_result_list_noescape,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_mul,
        ShapeTypeDict: operation_result_unsupported_mul,
        ShapeTypeNoneType: operation_result_unsupported_mul,
    }
)

floordiv_shapes_int.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # ints do math ops
        ShapeTypeInt: operation_result_zerodiv_intorlong,
        ShapeTypeLong: operation_result_zerodiv_long,
        ShapeTypeIntOrLong: operation_result_zerodiv_intorlong,
        ShapeTypeBool: operation_result_zerodiv_int,
        ShapeTypeFloat: operation_result_zerodiv_float,
        ShapeTypeComplex: operation_result_zerodiv_complex,
        # Unsupported:
        ShapeTypeStr: operation_result_unsupported_floordiv,
        ShapeTypeBytes: operation_result_unsupported_floordiv,
        ShapeTypeBytearray: operation_result_unsupported_floordiv,
        ShapeTypeUnicode: operation_result_unsupported_floordiv,
        ShapeTypeTuple: operation_result_unsupported_floordiv,
        ShapeTypeList: operation_result_unsupported_floordiv,
        ShapeTypeSet: operation_result_unsupported_floordiv,
        ShapeTypeDict: operation_result_unsupported_floordiv,
        ShapeTypeNoneType: operation_result_unsupported_floordiv,
    }
)

truediv_shapes_int.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # ints do math ops
        ShapeTypeInt: operation_result_zerodiv_float,
        ShapeTypeLong: operation_result_zerodiv_float,
        ShapeTypeIntOrLong: operation_result_zerodiv_float,
        ShapeTypeBool: operation_result_zerodiv_float,
        ShapeTypeFloat: operation_result_zerodiv_float,
        ShapeTypeComplex: operation_result_zerodiv_complex,
        # Unsupported:
        ShapeTypeStr: operation_result_unsupported_truediv,
        ShapeTypeBytes: operation_result_unsupported_truediv,
        ShapeTypeBytearray: operation_result_unsupported_truediv,
        ShapeTypeUnicode: operation_result_unsupported_truediv,
        ShapeTypeTuple: operation_result_unsupported_truediv,
        ShapeTypeList: operation_result_unsupported_truediv,
        ShapeTypeSet: operation_result_unsupported_truediv,
        ShapeTypeDict: operation_result_unsupported_truediv,
        ShapeTypeNoneType: operation_result_unsupported_truediv,
    }
)

olddiv_shapes_int.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # ints do math
        ShapeTypeInt: operation_result_zerodiv_intorlong,
        ShapeTypeLong: operation_result_zerodiv_long,
        ShapeTypeIntOrLong: operation_result_zerodiv_intorlong,
        ShapeTypeBool: operation_result_zerodiv_int,
        ShapeTypeFloat: operation_result_zerodiv_float,
        ShapeTypeComplex: operation_result_zerodiv_complex,
        # Unsupported:
        ShapeTypeStr: operation_result_unsupported_olddiv,
        ShapeTypeBytes: operation_result_unsupported_olddiv,
        ShapeTypeBytearray: operation_result_unsupported_olddiv,
        ShapeTypeUnicode: operation_result_unsupported_olddiv,
        ShapeTypeTuple: operation_result_unsupported_olddiv,
        ShapeTypeList: operation_result_unsupported_olddiv,
        ShapeTypeSet: operation_result_unsupported_olddiv,
        ShapeTypeDict: operation_result_unsupported_olddiv,
        ShapeTypeNoneType: operation_result_unsupported_olddiv,
    }
)

mod_shapes_int.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # ints do math
        ShapeTypeInt: operation_result_zerodiv_intorlong,
        ShapeTypeLong: operation_result_zerodiv_long,
        ShapeTypeIntOrLong: operation_result_zerodiv_intorlong,
        ShapeTypeBool: operation_result_zerodiv_int,
        ShapeTypeFloat: operation_result_zerodiv_float,
        ShapeTypeComplex: operation_result_unsupported_mod,
        # Unsupported:
        ShapeTypeStr: operation_result_unsupported_mod,
        ShapeTypeBytes: operation_result_unsupported_mod,
        ShapeTypeBytearray: operation_result_unsupported_mod,
        ShapeTypeUnicode: operation_result_unsupported_mod,
        ShapeTypeTuple: operation_result_unsupported_mod,
        ShapeTypeList: operation_result_unsupported_mod,
        ShapeTypeSet: operation_result_unsupported_mod,
        ShapeTypeDict: operation_result_unsupported_mod,
        ShapeTypeNoneType: operation_result_unsupported_mod,
    }
)

pow_shapes_int.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int keep their type, as bool is 0 or 1 int.
        ShapeTypeInt: operation_result_unknown,  # TODO: operation_result_intorlongorfloat,
        ShapeTypeLong: operation_result_unknown,  # TODO: operation_result_longorfloat,
        ShapeTypeIntOrLong: operation_result_unknown,  # TODO: operation_result_intorlongorfloat,
        ShapeTypeBool: operation_result_int_noescape,
        ShapeTypeFloat: operation_result_float_noescape,
        ShapeTypeComplex: operation_result_complex_noescape,
        # Unsupported:
        ShapeTypeStr: operation_result_unsupported_pow,
        ShapeTypeBytes: operation_result_unsupported_pow,
        ShapeTypeBytearray: operation_result_unsupported_pow,
        ShapeTypeUnicode: operation_result_unsupported_pow,
        ShapeTypeTuple: operation_result_unsupported_pow,
        ShapeTypeList: operation_result_unsupported_pow,
        ShapeTypeSet: operation_result_unsupported_pow,
        ShapeTypeDict: operation_result_unsupported_pow,
        ShapeTypeNoneType: operation_result_unsupported_pow,
    }
)

bitor_shapes_int.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int keep their type, as bool is 0 or 1 int.
        ShapeTypeInt: operation_result_int_noescape,
        ShapeTypeLong: operation_result_long_noescape,
        ShapeTypeIntOrLong: operation_result_intorlong_noescape,
        ShapeTypeBool: operation_result_bool_noescape,
        # Unsupported:
        ShapeTypeFloat: operation_result_unsupported_bitor,
        ShapeTypeComplex: operation_result_unsupported_bitor,
        ShapeTypeStr: operation_result_unsupported_bitor,
        ShapeTypeBytes: operation_result_unsupported_bitor,
        ShapeTypeBytearray: operation_result_unsupported_bitor,
        ShapeTypeUnicode: operation_result_unsupported_bitor,
        ShapeTypeTuple: operation_result_unsupported_bitor,
        ShapeTypeList: operation_result_unsupported_bitor,
        ShapeTypeSet: operation_result_unsupported_bitor,
        ShapeTypeDict: operation_result_unsupported_bitor,
        ShapeTypeNoneType: operation_result_unsupported_bitor,
    }
)

bitand_shapes_int.update(
    cloneWithUnsupportedChange(bitor_shapes_int, operation_result_unsupported_bitand)
)
bitxor_shapes_int.update(
    cloneWithUnsupportedChange(bitor_shapes_int, operation_result_unsupported_bitand)
)

lshift_shapes_int.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int keep their type, as bool is 0 or 1 int.
        ShapeTypeInt: operation_result_valueerror_intorlong,
        ShapeTypeLong: operation_result_valueerror_long,
        ShapeTypeIntOrLong: operation_result_valueerror_intorlong,
        ShapeTypeBool: operation_result_valueerror_intorlong,
        # Unsupported:
        ShapeTypeFloat: operation_result_unsupported_lshift,
        ShapeTypeComplex: operation_result_unsupported_lshift,
        ShapeTypeStr: operation_result_unsupported_lshift,
        ShapeTypeBytes: operation_result_unsupported_lshift,
        ShapeTypeBytearray: operation_result_unsupported_lshift,
        ShapeTypeUnicode: operation_result_unsupported_lshift,
        ShapeTypeTuple: operation_result_unsupported_lshift,
        ShapeTypeList: operation_result_unsupported_lshift,
        ShapeTypeSet: operation_result_unsupported_lshift,
        ShapeTypeDict: operation_result_unsupported_lshift,
        ShapeTypeNoneType: operation_result_unsupported_lshift,
    }
)
rshift_shapes_int.update(
    cloneWithUnsupportedChange(lshift_shapes_int, operation_result_unsupported_rshift)
)


add_shapes_long.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int might turn into long when growing due to possible overflow.
        ShapeTypeInt: operation_result_long_noescape,
        ShapeTypeLong: operation_result_long_noescape,
        ShapeTypeIntOrLong: operation_result_long_noescape,
        ShapeTypeBool: operation_result_long_noescape,
        ShapeTypeFloat: operation_result_float_noescape,
        ShapeTypeComplex: operation_result_complex_noescape,
        # Sequence repeat:
        ShapeTypeStr: operation_result_unsupported_add,
        ShapeTypeBytes: operation_result_unsupported_add,
        ShapeTypeBytearray: operation_result_unsupported_add,
        ShapeTypeUnicode: operation_result_unsupported_add,
        ShapeTypeTuple: operation_result_unsupported_add,
        ShapeTypeList: operation_result_unsupported_add,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_add,
        ShapeTypeDict: operation_result_unsupported_add,
        ShapeTypeNoneType: operation_result_unsupported_add,
    }
)

sub_shapes_long.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int might turn into long when growing due to possible overflow.
        ShapeTypeInt: operation_result_long_noescape,
        ShapeTypeLong: operation_result_long_noescape,
        ShapeTypeIntOrLong: operation_result_long_noescape,
        ShapeTypeBool: operation_result_long_noescape,
        ShapeTypeFloat: operation_result_float_noescape,
        ShapeTypeComplex: operation_result_complex_noescape,
        # Sequence repeat:
        ShapeTypeStr: operation_result_unsupported_sub,
        ShapeTypeBytes: operation_result_unsupported_sub,
        ShapeTypeBytearray: operation_result_unsupported_sub,
        ShapeTypeUnicode: operation_result_unsupported_sub,
        ShapeTypeTuple: operation_result_unsupported_sub,
        ShapeTypeList: operation_result_unsupported_sub,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_sub,
        ShapeTypeDict: operation_result_unsupported_sub,
        ShapeTypeNoneType: operation_result_unsupported_sub,
    }
)


mul_shapes_long.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int might turn into long when growing due to possible overflow.
        ShapeTypeInt: operation_result_long_noescape,
        ShapeTypeLong: operation_result_long_noescape,
        ShapeTypeIntOrLong: operation_result_long_noescape,
        ShapeTypeBool: operation_result_long_noescape,
        ShapeTypeFloat: operation_result_float_noescape,
        ShapeTypeComplex: operation_result_complex_noescape,
        # Sequence repeat:
        ShapeTypeStr: operation_result_str_noescape,
        ShapeTypeBytes: operation_result_bytes_noescape,
        ShapeTypeBytearray: operation_result_bytearray_noescape,
        ShapeTypeUnicode: operation_result_unicode_noescape,
        ShapeTypeTuple: operation_result_tuple_noescape,
        ShapeTypeList: operation_result_list_noescape,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_mul,
        ShapeTypeDict: operation_result_unsupported_mul,
        ShapeTypeNoneType: operation_result_unsupported_mul,
    }
)


def mergeIntOrLong(op_shapes_int, op_shapes_long):
    r = {}

    for key, value in op_shapes_int.items():
        value2 = op_shapes_long[key]

        if value is value2:
            r[key] = value
        elif value[0] is ShapeTypeIntOrLong and value2[0] is ShapeTypeLong:
            assert value[1] is value2[1]

            r[key] = value
        elif value[0] is ShapeTypeInt and value2[0] is ShapeTypeLong:
            assert value[1] is value2[1] is operation_result_intorlong_noescape[1]

            r[key] = operation_result_intorlong_noescape
        else:
            assert False, (key, "->", value, "!=", value2)

    return r


add_shapes_intorlong.update(mergeIntOrLong(add_shapes_int, add_shapes_long))
sub_shapes_intorlong.update(mergeIntOrLong(sub_shapes_int, sub_shapes_long))
mul_shapes_intorlong.update(mergeIntOrLong(mul_shapes_int, mul_shapes_long))

add_shapes_float.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int might turn into long when growing due to possible overflow.
        ShapeTypeInt: operation_result_float_noescape,
        ShapeTypeLong: operation_result_float_noescape,
        ShapeTypeIntOrLong: operation_result_float_noescape,
        ShapeTypeBool: operation_result_float_noescape,
        ShapeTypeFloat: operation_result_float_noescape,
        ShapeTypeComplex: operation_result_complex_noescape,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_add,
        ShapeTypeBytes: operation_result_unsupported_add,
        ShapeTypeBytearray: operation_result_unsupported_add,
        ShapeTypeUnicode: operation_result_unsupported_add,
        ShapeTypeTuple: operation_result_unsupported_add,
        ShapeTypeList: operation_result_unsupported_add,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_add,
        ShapeTypeDict: operation_result_unsupported_add,
        ShapeTypeNoneType: operation_result_unsupported_add,
    }
)


sub_shapes_float.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int might turn into long when growing due to possible overflow.
        ShapeTypeInt: operation_result_float_noescape,
        ShapeTypeLong: operation_result_float_noescape,
        ShapeTypeIntOrLong: operation_result_float_noescape,
        ShapeTypeBool: operation_result_float_noescape,
        ShapeTypeFloat: operation_result_float_noescape,
        ShapeTypeComplex: operation_result_complex_noescape,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_sub,
        ShapeTypeBytes: operation_result_unsupported_sub,
        ShapeTypeBytearray: operation_result_unsupported_sub,
        ShapeTypeUnicode: operation_result_unsupported_sub,
        ShapeTypeTuple: operation_result_unsupported_sub,
        ShapeTypeList: operation_result_unsupported_sub,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_sub,
        ShapeTypeDict: operation_result_unsupported_sub,
        ShapeTypeNoneType: operation_result_unsupported_sub,
    }
)


mul_shapes_float.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int might turn into long when growing due to possible overflow.
        ShapeTypeInt: operation_result_float_noescape,
        ShapeTypeLong: operation_result_float_noescape,
        ShapeTypeIntOrLong: operation_result_float_noescape,
        ShapeTypeBool: operation_result_float_noescape,
        ShapeTypeFloat: operation_result_float_noescape,
        ShapeTypeComplex: operation_result_complex_noescape,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_mul,
        ShapeTypeBytes: operation_result_unsupported_mul,
        ShapeTypeBytearray: operation_result_unsupported_mul,
        ShapeTypeUnicode: operation_result_unsupported_mul,
        ShapeTypeTuple: operation_result_unsupported_mul,
        ShapeTypeList: operation_result_unsupported_mul,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_mul,
        ShapeTypeDict: operation_result_unsupported_mul,
        ShapeTypeNoneType: operation_result_unsupported_mul,
    }
)

add_shapes_complex.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int might turn into long when growing due to possible overflow.
        ShapeTypeInt: operation_result_complex_noescape,
        ShapeTypeLong: operation_result_complex_noescape,
        ShapeTypeIntOrLong: operation_result_complex_noescape,
        ShapeTypeBool: operation_result_complex_noescape,
        ShapeTypeFloat: operation_result_complex_noescape,
        ShapeTypeComplex: operation_result_complex_noescape,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_add,
        ShapeTypeBytes: operation_result_unsupported_add,
        ShapeTypeBytearray: operation_result_unsupported_add,
        ShapeTypeUnicode: operation_result_unsupported_add,
        ShapeTypeTuple: operation_result_unsupported_add,
        ShapeTypeList: operation_result_unsupported_add,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_add,
        ShapeTypeDict: operation_result_unsupported_add,
        ShapeTypeNoneType: operation_result_unsupported_add,
    }
)


sub_shapes_complex.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int might turn into long when growing due to possible overflow.
        ShapeTypeInt: operation_result_complex_noescape,
        ShapeTypeLong: operation_result_complex_noescape,
        ShapeTypeIntOrLong: operation_result_complex_noescape,
        ShapeTypeBool: operation_result_complex_noescape,
        ShapeTypeFloat: operation_result_complex_noescape,
        ShapeTypeComplex: operation_result_complex_noescape,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_sub,
        ShapeTypeBytes: operation_result_unsupported_sub,
        ShapeTypeBytearray: operation_result_unsupported_sub,
        ShapeTypeUnicode: operation_result_unsupported_sub,
        ShapeTypeTuple: operation_result_unsupported_sub,
        ShapeTypeList: operation_result_unsupported_sub,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_sub,
        ShapeTypeDict: operation_result_unsupported_sub,
        ShapeTypeNoneType: operation_result_unsupported_sub,
    }
)

mul_shapes_complex.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int might turn into long when growing due to possible overflow.
        ShapeTypeInt: operation_result_complex_noescape,
        ShapeTypeLong: operation_result_complex_noescape,
        ShapeTypeIntOrLong: operation_result_complex_noescape,
        ShapeTypeBool: operation_result_complex_noescape,
        ShapeTypeFloat: operation_result_complex_noescape,
        ShapeTypeComplex: operation_result_complex_noescape,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_mul,
        ShapeTypeBytes: operation_result_unsupported_mul,
        ShapeTypeBytearray: operation_result_unsupported_mul,
        ShapeTypeUnicode: operation_result_unsupported_mul,
        ShapeTypeTuple: operation_result_unsupported_mul,
        ShapeTypeList: operation_result_unsupported_mul,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_mul,
        ShapeTypeDict: operation_result_unsupported_mul,
        ShapeTypeNoneType: operation_result_unsupported_mul,
    }
)

add_shapes_tuple.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int is sequence repeat
        ShapeTypeInt: operation_result_unsupported_add,
        ShapeTypeLong: operation_result_unsupported_add,
        ShapeTypeIntOrLong: operation_result_unsupported_add,
        ShapeTypeBool: operation_result_unsupported_add,
        ShapeTypeFloat: operation_result_unsupported_add,
        ShapeTypeComplex: operation_result_unsupported_add,
        # Sequence mixing is not allowed
        ShapeTypeStr: operation_result_unsupported_add,
        ShapeTypeBytes: operation_result_unsupported_add,
        ShapeTypeBytearray: operation_result_unsupported_add,
        ShapeTypeUnicode: operation_result_unsupported_add,
        ShapeTypeTuple: operation_result_tuple_noescape,
        ShapeTypeList: operation_result_unsupported_add,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_add,
        ShapeTypeDict: operation_result_unsupported_add,
        ShapeTypeNoneType: operation_result_unsupported_add,
    }
)


sub_shapes_tuple.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int is sequence repeat
        ShapeTypeInt: operation_result_unsupported_sub,
        ShapeTypeLong: operation_result_unsupported_sub,
        ShapeTypeIntOrLong: operation_result_unsupported_sub,
        ShapeTypeBool: operation_result_unsupported_sub,
        ShapeTypeFloat: operation_result_unsupported_sub,
        ShapeTypeComplex: operation_result_unsupported_sub,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_sub,
        ShapeTypeBytes: operation_result_unsupported_sub,
        ShapeTypeBytearray: operation_result_unsupported_sub,
        ShapeTypeUnicode: operation_result_unsupported_sub,
        ShapeTypeTuple: operation_result_unsupported_sub,
        ShapeTypeList: operation_result_unsupported_sub,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_sub,
        ShapeTypeDict: operation_result_unsupported_sub,
        ShapeTypeNoneType: operation_result_unsupported_sub,
    }
)


mul_shapes_tuple.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int is sequence repeat
        ShapeTypeInt: operation_result_tuple_noescape,
        ShapeTypeLong: operation_result_tuple_noescape,
        ShapeTypeIntOrLong: operation_result_tuple_noescape,
        ShapeTypeBool: operation_result_tuple_noescape,
        ShapeTypeFloat: operation_result_unsupported_mul,
        ShapeTypeComplex: operation_result_unsupported_mul,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_mul,
        ShapeTypeBytes: operation_result_unsupported_mul,
        ShapeTypeBytearray: operation_result_unsupported_mul,
        ShapeTypeUnicode: operation_result_unsupported_mul,
        ShapeTypeTuple: operation_result_unsupported_mul,
        ShapeTypeList: operation_result_unsupported_mul,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_mul,
        ShapeTypeDict: operation_result_unsupported_mul,
        ShapeTypeNoneType: operation_result_unsupported_mul,
    }
)

add_shapes_list.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int is sequence repeat
        ShapeTypeInt: operation_result_unsupported_add,
        ShapeTypeLong: operation_result_unsupported_add,
        ShapeTypeIntOrLong: operation_result_unsupported_add,
        ShapeTypeBool: operation_result_unsupported_add,
        ShapeTypeFloat: operation_result_unsupported_add,
        ShapeTypeComplex: operation_result_unsupported_add,
        # Sequence concat mixing is not allowed
        ShapeTypeStr: operation_result_unsupported_add,
        ShapeTypeBytes: operation_result_unsupported_add,
        ShapeTypeBytearray: operation_result_unsupported_add,
        ShapeTypeUnicode: operation_result_unsupported_add,
        ShapeTypeTuple: operation_result_unsupported_add,
        ShapeTypeList: operation_result_list_noescape,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_add,
        ShapeTypeDict: operation_result_unsupported_add,
        ShapeTypeNoneType: operation_result_unsupported_add,
    }
)

sub_shapes_list.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int is sequence repeat
        ShapeTypeInt: operation_result_unsupported_sub,
        ShapeTypeLong: operation_result_unsupported_sub,
        ShapeTypeIntOrLong: operation_result_unsupported_sub,
        ShapeTypeBool: operation_result_unsupported_sub,
        ShapeTypeFloat: operation_result_unsupported_sub,
        ShapeTypeComplex: operation_result_unsupported_sub,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_sub,
        ShapeTypeBytes: operation_result_unsupported_sub,
        ShapeTypeBytearray: operation_result_unsupported_sub,
        ShapeTypeUnicode: operation_result_unsupported_sub,
        ShapeTypeTuple: operation_result_unsupported_sub,
        ShapeTypeList: operation_result_unsupported_sub,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_sub,
        ShapeTypeDict: operation_result_unsupported_sub,
        ShapeTypeNoneType: operation_result_unsupported_sub,
    }
)

# These multiply with nothing really.
nothing_multiplicants = (
    ShapeTypeNoneType,
    ShapeTypeDict,
    ShapeTypeSet,
    ShapeTypeListIterator,
    ShapeTypeDictIterator,
    ShapeTypeSetIterator,
    ShapeTypeTupleIterator,
)


def updateNonMultiplicants(op_shapes):
    for shape in nothing_multiplicants:
        op_shapes[shape] = operation_result_unsupported_mul


sequence_non_multiplicants = (
    ShapeTypeFloat,
    ShapeTypeStr,
    ShapeTypeBytes,
    ShapeTypeBytearray,
    ShapeTypeUnicode,
    ShapeTypeTuple,
    ShapeTypeList,
    ShapeTypeSet,
    ShapeTypeFrozenset,
    ShapeTypeDict,
)


def updateSequenceNonMultiplicants(op_shapes):
    updateNonMultiplicants(op_shapes)

    for shape in sequence_non_multiplicants:
        op_shapes[shape] = operation_result_unsupported_mul


mul_shapes_list.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int is sequence repeat
        ShapeTypeInt: operation_result_list_noescape,
        ShapeTypeLong: operation_result_list_noescape,
        ShapeTypeIntOrLong: operation_result_list_noescape,
        ShapeTypeBool: operation_result_list_noescape,
    }
)

# Sequence repeat is not allowed
updateSequenceNonMultiplicants(mul_shapes_list)

add_shapes_set.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Sets to do not multiply
        ShapeTypeInt: operation_result_unsupported_add,
        ShapeTypeLong: operation_result_unsupported_add,
        ShapeTypeIntOrLong: operation_result_unsupported_add,
        ShapeTypeBool: operation_result_unsupported_add,
        ShapeTypeFloat: operation_result_unsupported_add,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_add,
        ShapeTypeBytes: operation_result_unsupported_add,
        ShapeTypeBytearray: operation_result_unsupported_add,
        ShapeTypeUnicode: operation_result_unsupported_add,
        ShapeTypeTuple: operation_result_unsupported_add,
        ShapeTypeList: operation_result_unsupported_add,
        ShapeTypeSet: operation_result_unsupported_add,
        ShapeTypeFrozenset: operation_result_unsupported_add,
        # Unsupported:
        ShapeTypeDict: operation_result_unsupported_add,
        ShapeTypeNoneType: operation_result_unsupported_add,
    }
)

sub_shapes_set.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Sets to do not multiply
        ShapeTypeInt: operation_result_unsupported_sub,
        ShapeTypeLong: operation_result_unsupported_sub,
        ShapeTypeIntOrLong: operation_result_unsupported_sub,
        ShapeTypeBool: operation_result_unsupported_sub,
        ShapeTypeFloat: operation_result_unsupported_sub,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_sub,
        ShapeTypeBytes: operation_result_unsupported_sub,
        ShapeTypeBytearray: operation_result_unsupported_sub,
        ShapeTypeUnicode: operation_result_unsupported_sub,
        ShapeTypeTuple: operation_result_unsupported_sub,
        ShapeTypeList: operation_result_unsupported_sub,
        ShapeTypeSet: operation_result_set_noescape,
        # Unsupported:
        ShapeTypeDict: operation_result_unsupported_sub,
        ShapeTypeNoneType: operation_result_unsupported_sub,
    }
)

mul_shapes_set.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Sets to do not multiply
        ShapeTypeInt: operation_result_unsupported_mul,
        ShapeTypeLong: operation_result_unsupported_mul,
        ShapeTypeIntOrLong: operation_result_unsupported_mul,
        ShapeTypeBool: operation_result_unsupported_mul,
        ShapeTypeFloat: operation_result_unsupported_mul,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_mul,
        ShapeTypeBytes: operation_result_unsupported_mul,
        ShapeTypeBytearray: operation_result_unsupported_mul,
        ShapeTypeUnicode: operation_result_unsupported_mul,
        ShapeTypeTuple: operation_result_unsupported_mul,
        ShapeTypeList: operation_result_unsupported_mul,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_mul,
        ShapeTypeDict: operation_result_unsupported_mul,
        ShapeTypeNoneType: operation_result_unsupported_mul,
    }
)

add_shapes_frozenset.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Sets to do not multiply
        ShapeTypeInt: operation_result_unsupported_add,
        ShapeTypeLong: operation_result_unsupported_add,
        ShapeTypeIntOrLong: operation_result_unsupported_add,
        ShapeTypeBool: operation_result_unsupported_add,
        ShapeTypeFloat: operation_result_unsupported_add,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_add,
        ShapeTypeBytes: operation_result_unsupported_add,
        ShapeTypeBytearray: operation_result_unsupported_add,
        ShapeTypeUnicode: operation_result_unsupported_add,
        ShapeTypeTuple: operation_result_unsupported_add,
        ShapeTypeList: operation_result_unsupported_add,
        ShapeTypeSet: operation_result_unsupported_add,
        ShapeTypeFrozenset: operation_result_unsupported_add,
        # Unsupported:
        ShapeTypeDict: operation_result_unsupported_add,
        ShapeTypeNoneType: operation_result_unsupported_add,
    }
)

sub_shapes_frozenset.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Sets to do not multiply
        ShapeTypeInt: operation_result_unsupported_sub,
        ShapeTypeLong: operation_result_unsupported_sub,
        ShapeTypeIntOrLong: operation_result_unsupported_sub,
        ShapeTypeBool: operation_result_unsupported_sub,
        ShapeTypeFloat: operation_result_unsupported_sub,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_sub,
        ShapeTypeBytes: operation_result_unsupported_sub,
        ShapeTypeBytearray: operation_result_unsupported_sub,
        ShapeTypeUnicode: operation_result_unsupported_sub,
        ShapeTypeTuple: operation_result_unsupported_sub,
        ShapeTypeList: operation_result_unsupported_sub,
        ShapeTypeSet: operation_result_frozenset_noescape,
        ShapeTypeFrozenset: operation_result_frozenset_noescape,
        # Unsupported:
        ShapeTypeDict: operation_result_unsupported_sub,
        ShapeTypeNoneType: operation_result_unsupported_sub,
    }
)

mul_shapes_frozenset.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Sets to do not multiply
        ShapeTypeInt: operation_result_unsupported_mul,
        ShapeTypeLong: operation_result_unsupported_mul,
        ShapeTypeIntOrLong: operation_result_unsupported_mul,
        ShapeTypeBool: operation_result_unsupported_mul,
        ShapeTypeFloat: operation_result_unsupported_mul,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_mul,
        ShapeTypeBytes: operation_result_unsupported_mul,
        ShapeTypeBytearray: operation_result_unsupported_mul,
        ShapeTypeUnicode: operation_result_unsupported_mul,
        ShapeTypeTuple: operation_result_unsupported_mul,
        ShapeTypeList: operation_result_unsupported_mul,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_mul,
        ShapeTypeFrozenset: operation_result_unsupported_mul,
        ShapeTypeDict: operation_result_unsupported_mul,
        ShapeTypeNoneType: operation_result_unsupported_mul,
    }
)

add_shapes_dict.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Sets to do not multiply
        ShapeTypeInt: operation_result_unsupported_add,
        ShapeTypeLong: operation_result_unsupported_add,
        ShapeTypeIntOrLong: operation_result_unsupported_add,
        ShapeTypeBool: operation_result_unsupported_add,
        ShapeTypeFloat: operation_result_unsupported_add,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_add,
        ShapeTypeBytes: operation_result_unsupported_add,
        ShapeTypeBytearray: operation_result_unsupported_add,
        ShapeTypeUnicode: operation_result_unsupported_add,
        ShapeTypeTuple: operation_result_unsupported_add,
        ShapeTypeList: operation_result_unsupported_add,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_add,
        ShapeTypeDict: operation_result_unsupported_add,
        ShapeTypeNoneType: operation_result_unsupported_add,
    }
)

sub_shapes_dict.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Sets to do not multiply
        ShapeTypeInt: operation_result_unsupported_sub,
        ShapeTypeLong: operation_result_unsupported_sub,
        ShapeTypeIntOrLong: operation_result_unsupported_sub,
        ShapeTypeBool: operation_result_unsupported_sub,
        ShapeTypeFloat: operation_result_unsupported_sub,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_sub,
        ShapeTypeBytes: operation_result_unsupported_sub,
        ShapeTypeBytearray: operation_result_unsupported_sub,
        ShapeTypeUnicode: operation_result_unsupported_sub,
        ShapeTypeTuple: operation_result_unsupported_sub,
        ShapeTypeList: operation_result_unsupported_sub,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_sub,
        ShapeTypeDict: operation_result_unsupported_sub,
        ShapeTypeNoneType: operation_result_unsupported_sub,
    }
)

add_shapes_str.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int is sequence repeat
        ShapeTypeInt: operation_result_unsupported_add,
        ShapeTypeLong: operation_result_unsupported_add,
        ShapeTypeIntOrLong: operation_result_unsupported_add,
        ShapeTypeBool: operation_result_unsupported_add,
        ShapeTypeFloat: operation_result_unsupported_add,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_str_noescape,
        ShapeTypeBytes: operation_result_unsupported_add,
        ShapeTypeBytearray: operation_result_bytearray_noescape
        if python_version < 300
        else operation_result_unsupported_add,
        ShapeTypeUnicode: operation_result_unicode_noescape,
        ShapeTypeTuple: operation_result_unsupported_add,
        ShapeTypeList: operation_result_unsupported_add,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_add,
        ShapeTypeDict: operation_result_unsupported_add,
        ShapeTypeNoneType: operation_result_unsupported_add,
    }
)

sub_shapes_str.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int is sequence repeat
        ShapeTypeInt: operation_result_unsupported_sub,
        ShapeTypeLong: operation_result_unsupported_sub,
        ShapeTypeIntOrLong: operation_result_unsupported_sub,
        ShapeTypeBool: operation_result_unsupported_sub,
        ShapeTypeFloat: operation_result_unsupported_sub,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_sub,
        ShapeTypeBytes: operation_result_unsupported_sub,
        ShapeTypeBytearray: operation_result_unsupported_sub,
        ShapeTypeUnicode: operation_result_unsupported_sub,
        ShapeTypeTuple: operation_result_unsupported_sub,
        ShapeTypeList: operation_result_unsupported_sub,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_sub,
        ShapeTypeDict: operation_result_unsupported_sub,
        ShapeTypeNoneType: operation_result_unsupported_sub,
    }
)

mul_shapes_str.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int is sequence repeat
        ShapeTypeInt: operation_result_str_noescape,
        ShapeTypeLong: operation_result_str_noescape,
        ShapeTypeIntOrLong: operation_result_str_noescape,
        ShapeTypeBool: operation_result_str_noescape,
        ShapeTypeFloat: operation_result_unsupported_mul,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_mul,
        ShapeTypeBytes: operation_result_unsupported_mul,
        ShapeTypeBytearray: operation_result_unsupported_mul,
        ShapeTypeUnicode: operation_result_unsupported_mul,
        ShapeTypeTuple: operation_result_unsupported_mul,
        ShapeTypeList: operation_result_unsupported_mul,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_mul,
        ShapeTypeDict: operation_result_unsupported_mul,
        ShapeTypeNoneType: operation_result_unsupported_mul,
    }
)

add_shapes_bytes.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int is sequence repeat
        ShapeTypeInt: operation_result_unsupported_add,
        ShapeTypeLong: operation_result_unsupported_add,
        ShapeTypeIntOrLong: operation_result_unsupported_add,
        ShapeTypeBool: operation_result_unsupported_add,
        ShapeTypeFloat: operation_result_unsupported_add,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_add,
        ShapeTypeBytes: operation_result_bytes_noescape,
        ShapeTypeBytearray: operation_result_bytearray_noescape,
        ShapeTypeUnicode: operation_result_unsupported_add,
        ShapeTypeTuple: operation_result_unsupported_add,
        ShapeTypeList: operation_result_unsupported_add,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_add,
        ShapeTypeDict: operation_result_unsupported_add,
        ShapeTypeNoneType: operation_result_unsupported_add,
    }
)

sub_shapes_bytes.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int is sequence repeat
        ShapeTypeInt: operation_result_unsupported_sub,
        ShapeTypeLong: operation_result_unsupported_sub,
        ShapeTypeIntOrLong: operation_result_unsupported_sub,
        ShapeTypeBool: operation_result_unsupported_sub,
        ShapeTypeFloat: operation_result_unsupported_sub,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_sub,
        ShapeTypeBytes: operation_result_unsupported_sub,
        ShapeTypeBytearray: operation_result_unsupported_sub,
        ShapeTypeUnicode: operation_result_unsupported_sub,
        ShapeTypeTuple: operation_result_unsupported_sub,
        ShapeTypeList: operation_result_unsupported_sub,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_sub,
        ShapeTypeDict: operation_result_unsupported_sub,
        ShapeTypeNoneType: operation_result_unsupported_sub,
    }
)

mul_shapes_bytes.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int is sequence repeat
        ShapeTypeInt: operation_result_bytes_noescape,
        ShapeTypeLong: operation_result_bytes_noescape,
        ShapeTypeIntOrLong: operation_result_bytes_noescape,
        ShapeTypeBool: operation_result_bytes_noescape,
        ShapeTypeFloat: operation_result_unsupported_mul,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_mul,
        ShapeTypeBytes: operation_result_unsupported_mul,
        ShapeTypeBytearray: operation_result_unsupported_mul,
        ShapeTypeUnicode: operation_result_unsupported_mul,
        ShapeTypeTuple: operation_result_unsupported_mul,
        ShapeTypeList: operation_result_unsupported_mul,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_mul,
        ShapeTypeDict: operation_result_unsupported_mul,
        ShapeTypeNoneType: operation_result_unsupported_mul,
    }
)

add_shapes_bytearray.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int is sequence repeat
        ShapeTypeInt: operation_result_unsupported_add,
        ShapeTypeLong: operation_result_unsupported_add,
        ShapeTypeIntOrLong: operation_result_unsupported_add,
        ShapeTypeBool: operation_result_unsupported_add,
        ShapeTypeFloat: operation_result_unsupported_add,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_bytearray_noescape
        if python_version < 300
        else operation_result_unsupported_add,
        ShapeTypeBytes: operation_result_bytearray_noescape,
        ShapeTypeBytearray: operation_result_bytearray_noescape,
        ShapeTypeUnicode: operation_result_unsupported_add,
        ShapeTypeTuple: operation_result_unsupported_add,
        ShapeTypeList: operation_result_unsupported_add,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_add,
        ShapeTypeDict: operation_result_unsupported_add,
        ShapeTypeNoneType: operation_result_unsupported_add,
    }
)

sub_shapes_bytearray.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int is sequence repeat
        ShapeTypeInt: operation_result_unsupported_sub,
        ShapeTypeLong: operation_result_unsupported_sub,
        ShapeTypeIntOrLong: operation_result_unsupported_sub,
        ShapeTypeBool: operation_result_unsupported_sub,
        ShapeTypeFloat: operation_result_unsupported_sub,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_sub,
        ShapeTypeBytes: operation_result_unsupported_sub,
        ShapeTypeBytearray: operation_result_unsupported_sub,
        ShapeTypeUnicode: operation_result_unsupported_sub,
        ShapeTypeTuple: operation_result_unsupported_sub,
        ShapeTypeList: operation_result_unsupported_sub,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_sub,
        ShapeTypeDict: operation_result_unsupported_sub,
        ShapeTypeNoneType: operation_result_unsupported_sub,
    }
)

mul_shapes_bytearray.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int is sequence repeat
        ShapeTypeInt: operation_result_bytearray_noescape,
        ShapeTypeLong: operation_result_bytearray_noescape,
        ShapeTypeIntOrLong: operation_result_bytearray_noescape,
        ShapeTypeBool: operation_result_bytearray_noescape,
        ShapeTypeFloat: operation_result_unsupported_mul,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_mul,
        ShapeTypeBytes: operation_result_unsupported_mul,
        ShapeTypeBytearray: operation_result_unsupported_mul,
        ShapeTypeUnicode: operation_result_unsupported_mul,
        ShapeTypeTuple: operation_result_unsupported_mul,
        ShapeTypeList: operation_result_unsupported_mul,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_mul,
        ShapeTypeDict: operation_result_unsupported_mul,
        ShapeTypeNoneType: operation_result_unsupported_mul,
    }
)

add_shapes_unicode.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int is sequence repeat
        ShapeTypeInt: operation_result_unsupported_add,
        ShapeTypeLong: operation_result_unsupported_add,
        ShapeTypeIntOrLong: operation_result_unsupported_add,
        ShapeTypeBool: operation_result_unsupported_add,
        ShapeTypeFloat: operation_result_unsupported_add,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unicode_noescape,
        ShapeTypeBytes: operation_result_unsupported_add,
        ShapeTypeBytearray: operation_result_unsupported_add,
        ShapeTypeUnicode: operation_result_unicode_noescape,
        ShapeTypeTuple: operation_result_unsupported_add,
        ShapeTypeList: operation_result_unsupported_add,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_add,
        ShapeTypeDict: operation_result_unsupported_add,
        ShapeTypeNoneType: operation_result_unsupported_add,
    }
)

sub_shapes_unicode.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int is sequence repeat
        ShapeTypeInt: operation_result_unsupported_sub,
        ShapeTypeLong: operation_result_unsupported_sub,
        ShapeTypeIntOrLong: operation_result_unsupported_sub,
        ShapeTypeBool: operation_result_unsupported_sub,
        ShapeTypeFloat: operation_result_unsupported_sub,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_sub,
        ShapeTypeBytes: operation_result_unsupported_sub,
        ShapeTypeBytearray: operation_result_unsupported_sub,
        ShapeTypeUnicode: operation_result_unsupported_sub,
        ShapeTypeTuple: operation_result_unsupported_sub,
        ShapeTypeList: operation_result_unsupported_sub,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_sub,
        ShapeTypeDict: operation_result_unsupported_sub,
        ShapeTypeNoneType: operation_result_unsupported_sub,
    }
)

mul_shapes_unicode.update(
    {
        # Standard
        ShapeUnknown: operation_result_unknown,
        ShapeTypeLongDerived: operation_result_unknown,
        ShapeTypeIntOrLongDerived: operation_result_unknown,
        ShapeTypeStrDerived: operation_result_unknown,
        ShapeTypeUnicodeDerived: operation_result_unknown,
        ShapeTypeBytesDerived: operation_result_unknown,
        # Int is sequence repeat
        ShapeTypeInt: operation_result_unicode_noescape,
        ShapeTypeLong: operation_result_unicode_noescape,
        ShapeTypeIntOrLong: operation_result_unicode_noescape,
        ShapeTypeBool: operation_result_unicode_noescape,
        ShapeTypeFloat: operation_result_unsupported_mul,
        # Sequence repeat is not allowed
        ShapeTypeStr: operation_result_unsupported_mul,
        ShapeTypeBytes: operation_result_unsupported_mul,
        ShapeTypeBytearray: operation_result_unsupported_mul,
        ShapeTypeUnicode: operation_result_unsupported_mul,
        ShapeTypeTuple: operation_result_unsupported_mul,
        ShapeTypeList: operation_result_unsupported_mul,
        # Unsupported:
        ShapeTypeSet: operation_result_unsupported_mul,
        ShapeTypeDict: operation_result_unsupported_mul,
        ShapeTypeNoneType: operation_result_unsupported_mul,
    }
)


def mergeStrOrUnicode(op_shapes_str, op_shapes_unicode):
    r = {}

    for key, value in op_shapes_str.items():
        value2 = op_shapes_unicode[key]

        if value is value2:
            r[key] = value
        elif value[0] is ShapeTypeStrOrUnicode and value2[0] is ShapeTypeUnicode:
            assert value[1] is value2[1]

            r[key] = value
        elif value[0] is ShapeTypeStr and value2[0] is ShapeTypeUnicode:
            assert value[1] is value2[1] is operation_result_strorunicode_noescape[1]

            r[key] = operation_result_strorunicode_noescape
        elif key == ShapeTypeBytearray:
            # They differ here on Python2
            r[key] = operation_result_unknown
        else:
            assert False, (key, "->", value, "!=", value2)

    return r


add_shapes_strorunicode.update(mergeStrOrUnicode(add_shapes_str, add_shapes_unicode))
sub_shapes_strorunicode.update(mergeStrOrUnicode(sub_shapes_str, sub_shapes_unicode))
mul_shapes_strorunicode.update(mergeStrOrUnicode(mul_shapes_str, mul_shapes_unicode))
