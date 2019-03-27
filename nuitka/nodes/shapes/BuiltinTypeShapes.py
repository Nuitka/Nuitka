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

from .ControlFlowEscapeDescriptions import (
    ControlFlowDescriptionAddUnsupported,
    ControlFlowDescriptionComparisonUnorderable,
    ControlFlowDescriptionElementBasedEscape,
    ControlFlowDescriptionFullEscape,
    ControlFlowDescriptionNoEscape,
)
from .StandardShapes import (
    ShapeBase,
    ShapeIterator,
    ShapeLoopCompleteAlternative,
    ShapeLoopInitialAlternative,
    ShapeUnknown,
)

# Very many cases when deciding shapes
# pylint: disable=too-many-return-statements


def _getOperationBinaryAddShapeGeneric(cls, right_shape):
    if type(right_shape) is ShapeLoopCompleteAlternative:
        return right_shape.getOperationBinaryAddLShape(cls)

    if type(right_shape) is ShapeLoopInitialAlternative:
        return operation_result_unknown

    onMissingOperation("Add", cls, right_shape)
    return operation_result_unknown


def _getComparisonLtShapeGeneric(cls, right_shape):
    if type(right_shape) is ShapeLoopCompleteAlternative:
        return right_shape.getComparisonLtLShape(cls)

    if type(right_shape) is ShapeLoopInitialAlternative:
        return operation_result_unknown

    onMissingOperation("Lt", cls, right_shape)
    return operation_result_unknown


class ShapeTypeNoneType(ShapeBase):
    @staticmethod
    def getTypeName():
        return "NoneType"

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
    def getOperationBinaryAddShape(cls, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        # TODO: A lot more should be here.
        if right_shape in (ShapeTypeInt, ShapeTypeStr):
            return operation_result_unsupported_add

        return _getOperationBinaryAddShapeGeneric(cls, right_shape)

    if python_version < 300:

        @classmethod
        def getComparisonLtShape(cls, right_shape):
            if right_shape is ShapeUnknown:
                return operation_result_unknown

            if right_shape.getTypeName() is not None:
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
    @staticmethod
    def getTypeName():
        return "bool"

    @staticmethod
    def getCType():
        return CTypeNuitkaBoolEnum

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

    @classmethod
    def getOperationBinaryAddShape(cls, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        # Int might turn into long when adding anything due to possible
        # overflow.
        if right_shape in (ShapeTypeInt, ShapeTypeIntOrLong, ShapeTypeBool):
            return operation_result_intorlong_noescape

        if right_shape is ShapeTypeLong:
            return operation_result_long_noescape

        if right_shape is ShapeTypeIntOrLongDerived:
            return operation_result_unknown

        return _getOperationBinaryAddShapeGeneric(cls, right_shape)

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
    @staticmethod
    def getTypeName():
        return "int"

    helper_code = "INT" if python_version < 300 else "LONG"

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

    @classmethod
    def getOperationBinaryAddShape(cls, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        # Int might turn into long when adding anything due to possible
        # overflow.
        if right_shape in (ShapeTypeInt, ShapeTypeIntOrLong, ShapeTypeBool):
            return operation_result_intorlong_noescape

        if right_shape is ShapeTypeLong:
            return operation_result_long_noescape

        if right_shape in (ShapeTypeLongDerived, ShapeTypeIntOrLongDerived):
            return operation_result_unknown

        if right_shape is ShapeTypeFloat:
            return operation_result_float_noescape

        # TODO: There must be a lot more than this.
        if right_shape in (ShapeTypeNoneType, ShapeTypeStr):
            return operation_result_unsupported_add

        return _getOperationBinaryAddShapeGeneric(cls, right_shape)

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


class ShapeTypeLong(ShapeBase):
    @staticmethod
    def getTypeName():
        return "long"

    helper_code = "LONG" if python_version < 300 else "INVALID"

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

    @classmethod
    def getOperationBinaryAddShape(cls, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        # Long remains long when adding anything to it.
        if right_shape in (
            ShapeTypeLong,
            ShapeTypeInt,
            ShapeTypeIntOrLong,
            ShapeTypeBool,
        ):
            return operation_result_long_noescape

        if right_shape in (ShapeTypeLongDerived, ShapeTypeIntOrLongDerived):
            return operation_result_unknown

        return _getOperationBinaryAddShapeGeneric(cls, right_shape)

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


if python_version < 300:

    class ShapeTypeIntOrLong(ShapeBase):
        if isExperimental("nuitka_ilong"):

            @staticmethod
            def getCType():
                return CTypeNuitkaIntOrLongStruct

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

        @classmethod
        def getOperationBinaryAddShape(cls, right_shape):
            if right_shape is ShapeUnknown:
                return operation_result_unknown

            if right_shape in (ShapeTypeInt, ShapeTypeIntOrLong, ShapeTypeBool):
                return operation_result_intorlong_noescape

            if right_shape is ShapeTypeLong:
                return operation_result_long_noescape

            if right_shape in (ShapeTypeIntOrLongDerived, ShapeTypeLongDerived):
                return operation_result_unknown

            return _getOperationBinaryAddShapeGeneric(cls, right_shape)

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
    ShapeTypeIntOrLong = ShapeTypeInt


class ShapeTypeIntOrLongDerived(ShapeUnknown):
    pass


class ShapeTypeFloat(ShapeBase):
    @staticmethod
    def getTypeName():
        return "float"

    helper_code = "FLOAT"

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

    @classmethod
    def getOperationBinaryAddShape(cls, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        if right_shape in (
            ShapeTypeFloat,
            ShapeTypeLong,
            ShapeTypeInt,
            ShapeTypeIntOrLong,
            ShapeTypeBool,
        ):
            return operation_result_float_noescape

        if right_shape is ShapeTypeFloatDerived:
            return operation_result_unknown

        return _getOperationBinaryAddShapeGeneric(cls, right_shape)

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
    @staticmethod
    def getTypeName():
        return "complex"

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

    @classmethod
    def getOperationBinaryAddShape(cls, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        if right_shape in (
            ShapeTypeFloat,
            ShapeTypeLong,
            ShapeTypeInt,
            ShapeTypeIntOrLong,
            ShapeTypeBool,
        ):
            return operation_result_complex_noescape

        if right_shape is ShapeTypeFloatDerived:
            return operation_result_unknown

        return _getOperationBinaryAddShapeGeneric(cls, right_shape)

    # TODO: No < for complex


class ShapeTypeTuple(ShapeBase):
    @staticmethod
    def getTypeName():
        return "tuple"

    helper_code = "TUPLE"

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

    @classmethod
    def getOperationBinaryAddShape(cls, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        if right_shape is ShapeTypeTuple:
            return operation_result_tuple_noescape

        if right_shape in (ShapeTypeNoneType, ShapeTypeList):
            return operation_result_unsupported_add

        return _getOperationBinaryAddShapeGeneric(cls, right_shape)

    @classmethod
    def getComparisonLtShape(cls, right_shape):
        # Need to consider value shape for this.
        return operation_result_unknown


class ShapeTypeTupleIterator(ShapeIterator):
    @staticmethod
    def getTypeName():
        return "tupleiterator" if python_version < 300 else "tuple_iterator"

    @staticmethod
    def hasShapeSlotLen():
        return False


class ShapeTypeList(ShapeBase):
    @staticmethod
    def getTypeName():
        return "list"

    helper_code = "LIST"

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

    @classmethod
    def getOperationBinaryAddShape(cls, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        if right_shape is ShapeTypeList:
            return operation_result_list_noescape

        if right_shape in (ShapeTypeNoneType, ShapeTypeTuple):
            return operation_result_unsupported_add

        return _getOperationBinaryAddShapeGeneric(cls, right_shape)

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
    @staticmethod
    def getTypeName():
        return "listiterator" if python_version < 300 else "list_iterator"

    @staticmethod
    def hasShapeSlotLen():
        return False


class ShapeTypeSet(ShapeBase):
    @staticmethod
    def getTypeName():
        return "set"

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

    @classmethod
    def getComparisonLtShape(cls, right_shape):
        # Need to consider value shape for this.
        return operation_result_unknown


class ShapeTypeSetIterator(ShapeIterator):
    @staticmethod
    def getTypeName():
        return "setiterator" if python_version < 300 else "set_iterator"

    @staticmethod
    def hasShapeSlotLen():
        return False


class ShapeTypeFrozenset(ShapeBase):
    @staticmethod
    def getTypeName():
        return "frozenset"

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


class ShapeTypeDict(ShapeBase):
    @staticmethod
    def getTypeName():
        return "dict"

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

    @classmethod
    def getComparisonLtShape(cls, right_shape):
        # Need to consider value shape for this

        # TODO: Could return bool with annotation that exception is still
        # possible..
        return operation_result_unknown


class ShapeTypeDictIterator(ShapeIterator):
    @staticmethod
    def getTypeName():
        return "dictionary-keyiterator" if python_version < 300 else "dictkey_iterator"

    @staticmethod
    def hasShapeSlotLen():
        return False


class ShapeTypeStr(ShapeBase):
    @staticmethod
    def getTypeName():
        return "str"

    helper_code = "STR" if python_version < 300 else "UNICODE"

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

    @classmethod
    def getOperationBinaryAddShape(cls, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        if right_shape is ShapeTypeStr:
            return operation_result_str_noescape

        if right_shape is ShapeTypeStrDerived:
            return operation_result_unknown

        if right_shape is ShapeTypeUnicode:
            return operation_result_unicode_noescape

        if right_shape is ShapeTypeBytearray:
            if python_version < 300:
                return operation_result_bytearray_noescape
            else:
                # TODO: Exception actually for static optimization.
                return operation_result_unknown

        if right_shape in (
            ShapeTypeNoneType,
            ShapeTypeInt,
            ShapeTypeLong,
            ShapeTypeIntOrLong,
        ):
            return operation_result_unsupported_add

        return _getOperationBinaryAddShapeGeneric(cls, right_shape)

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
    @staticmethod
    def getTypeName():
        return "iterator" if python_version < 300 else "str_iterator"

    @staticmethod
    def hasShapeSlotLen():
        return False


if python_version < 300:

    class ShapeTypeUnicode(ShapeBase):
        @staticmethod
        def getTypeName():
            return "unicode"

        helper_code = "UNICODE"

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

        @classmethod
        def getOperationBinaryAddShape(cls, right_shape):
            if right_shape is ShapeUnknown:
                return operation_result_unknown

            if right_shape in (ShapeTypeUnicode, ShapeTypeStr):
                return operation_result_unicode_noescape

            if right_shape is ShapeTypeUnicodeDerived:
                return operation_result_unknown

            return _getOperationBinaryAddShapeGeneric(cls, right_shape)

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
        @staticmethod
        def getTypeName():
            return "iterator"

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


else:
    ShapeTypeStrOrUnicode = ShapeTypeStr


if python_version >= 300:

    class ShapeTypeBytes(ShapeBase):
        @staticmethod
        def getTypeName():
            return "bytes"

        helper_code = "BYTES"

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

        @classmethod
        def getOperationBinaryAddShape(cls, right_shape):
            if right_shape is ShapeUnknown:
                return operation_result_unknown

            if right_shape in (ShapeTypeBytes, ShapeTypeBytearray):
                return operation_result_bytes_noescape

            if right_shape is ShapeTypeBytesDerived:
                return operation_result_unknown

            return _getOperationBinaryAddShapeGeneric(cls, right_shape)

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
        @staticmethod
        def getTypeName():
            return "bytes_iterator"

        @staticmethod
        def hasShapeSlotLen():
            return False


else:
    ShapeTypeBytes = ShapeTypeStr
    ShapeTypeBytesIterator = ShapeTypeStrIterator

    # Shoudln't happen with Python2
    ShapeTypeBytesDerived = None


class ShapeTypeBytearray(ShapeBase):
    @staticmethod
    def getTypeName():
        return "bytearray"

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

    @classmethod
    def getOperationBinaryAddShape(cls, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        if right_shape in (ShapeTypeBytearray, ShapeTypeBytes):
            return operation_result_bytearray_noescape

        if right_shape is ShapeTypeBytesDerived:
            return operation_result_unknown

        if right_shape is ShapeTypeStr:
            if python_version < 300:
                return operation_result_bytearray_noescape
            else:
                # TODO: Exception actually for static optimization.
                return operation_result_unknown

        return _getOperationBinaryAddShapeGeneric(cls, right_shape)

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
    @staticmethod
    def getTypeName():
        return "bytearray_iterator"

    @staticmethod
    def hasShapeSlotLen():
        return False


class ShapeTypeEllipsisType(ShapeBase):
    @staticmethod
    def getTypeName():
        return "ellipsis"

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
    @staticmethod
    def getTypeName():
        return "slice"

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
    @staticmethod
    def getTypeName():
        return "xrange" if python_version < 300 else "range"

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
    @staticmethod
    def getTypeName():
        return "rangeiterator" if python_version < 300 else "range_iterator"

    @staticmethod
    def hasShapeSlotLen():
        return False


class ShapeTypeType(ShapeBase):
    @staticmethod
    def getTypeName():
        return "type"

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
    @staticmethod
    def getTypeName():
        return "module"

    @staticmethod
    def hasShapeModule():
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
    pass


class ShapeTypeFile(ShapeBase):
    @staticmethod
    def getTypeName():
        return "file"

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
    @staticmethod
    def getTypeName():
        return "staticmethod"

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
    @staticmethod
    def getTypeName():
        return "classmethod"

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
operation_result_unknown = ShapeUnknown, ControlFlowDescriptionFullEscape
operation_result_bool_noescape = ShapeTypeBool, ControlFlowDescriptionNoEscape
operation_result_float_noescape = ShapeTypeFloat, ControlFlowDescriptionNoEscape
operation_result_long_noescape = ShapeTypeLong, ControlFlowDescriptionNoEscape
operation_result_intorlong_noescape = ShapeTypeIntOrLong, ControlFlowDescriptionNoEscape
operation_result_complex_noescape = ShapeTypeComplex, ControlFlowDescriptionNoEscape
operation_result_tuple_noescape = ShapeTypeTuple, ControlFlowDescriptionNoEscape
operation_result_list_noescape = ShapeTypeList, ControlFlowDescriptionNoEscape
operation_result_str_noescape = ShapeTypeStr, ControlFlowDescriptionNoEscape
operation_result_unicode_noescape = ShapeTypeUnicode, ControlFlowDescriptionNoEscape
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
