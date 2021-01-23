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
""" Standard shapes that commonly appear. """

from nuitka.codegen.c_types.CTypePyObjectPtrs import CTypePyObjectPtr
from nuitka.codegen.Reports import onMissingOperation

from .ControlFlowDescriptions import ControlFlowDescriptionFullEscape
from .ShapeMixins import ShapeIteratorMixin


class ShapeBase(object):
    def __repr__(self):
        return "<%s %s %s>" % (
            self.__class__.__name__,
            self.getTypeName(),
            self.helper_code,
        )

    @staticmethod
    def getTypeName():
        return None

    helper_code = "OBJECT"

    @staticmethod
    def getCType():
        return CTypePyObjectPtr

    @staticmethod
    def getShapeIter():
        return tshape_unknown

    @staticmethod
    def hasShapeModule():
        return None

    @staticmethod
    def hasShapeSlotBytes():
        return None

    @staticmethod
    def hasShapeSlotComplex():
        return None

    @staticmethod
    def hasShapeSlotBool():
        return None

    @staticmethod
    def hasShapeSlotAbs():
        return None

    @staticmethod
    def hasShapeSlotLen():
        return None

    @staticmethod
    def hasShapeSlotInt():
        return None

    @staticmethod
    def hasShapeSlotLong():
        return None

    @staticmethod
    def hasShapeSlotFloat():
        return None

    @staticmethod
    def hasShapeSlotIter():
        return None

    @staticmethod
    def hasShapeSlotNext():
        return None

    @staticmethod
    def hasShapeSlotContains():
        return None

    @staticmethod
    def hasShapeSlotHash():
        return None

    add_shapes = {}

    def getOperationBinaryAddShape(self, right_shape):
        result = self.add_shapes.get(right_shape)

        if result is not None:
            return result
        else:
            right_shape_type = type(right_shape)
            if right_shape_type is ShapeLoopCompleteAlternative:
                return right_shape.getOperationBinaryAddLShape(self)

            if right_shape_type is ShapeLoopInitialAlternative:
                return operation_result_unknown

            onMissingOperation("Add", self, right_shape)

            return operation_result_unknown

    # TODO: Change defaults to be "None" for easier catching of
    # non-overloaders
    iadd_shapes = {}

    def getOperationInplaceAddShape(self, right_shape):
        """Inplace add operation shape, for overload."""
        if self.iadd_shapes:
            result = self.iadd_shapes.get(right_shape)

            if result is not None:
                return result
            else:
                right_shape_type = type(right_shape)
                if right_shape_type is ShapeLoopCompleteAlternative:
                    return right_shape.getOperationBinaryAddLShape(self)

                if right_shape_type is ShapeLoopInitialAlternative:
                    return operation_result_unknown

                onMissingOperation("IAdd", self, right_shape)

                return operation_result_unknown
        else:
            # By default, inplace add is the same as plain add, the
            # only exception known right now is list, which extend
            # from all iterables, but don't add with them.
            return self.getOperationBinaryAddShape(right_shape)

    sub_shapes = {}

    def getOperationBinarySubShape(self, right_shape):
        result = self.sub_shapes.get(right_shape)

        if result is not None:
            return result
        else:
            right_shape_type = type(right_shape)
            if right_shape_type is ShapeLoopCompleteAlternative:
                return right_shape.getOperationBinarySubLShape(self)

            if right_shape_type is ShapeLoopInitialAlternative:
                return operation_result_unknown

            onMissingOperation("Sub", self, right_shape)

            return operation_result_unknown

    mult_shapes = {}

    def getOperationBinaryMultShape(self, right_shape):
        result = self.mult_shapes.get(right_shape)

        if result is not None:
            return result
        else:
            right_shape_type = type(right_shape)
            if right_shape_type is ShapeLoopCompleteAlternative:
                return right_shape.getOperationBinaryMultLShape(self)

            if right_shape_type is ShapeLoopInitialAlternative:
                return operation_result_unknown

            onMissingOperation("Mult", self, right_shape)

            return operation_result_unknown

    floordiv_shapes = {}

    def getOperationBinaryFloorDivShape(self, right_shape):
        result = self.floordiv_shapes.get(right_shape)

        if result is not None:
            return result
        else:
            right_shape_type = type(right_shape)
            if right_shape_type is ShapeLoopCompleteAlternative:
                return right_shape.getOperationBinaryFloorDivLShape(self)

            if right_shape_type is ShapeLoopInitialAlternative:
                return operation_result_unknown

            onMissingOperation("FloorDiv", self, right_shape)

            return operation_result_unknown

    olddiv_shapes = {}

    def getOperationBinaryOldDivShape(self, right_shape):
        result = self.olddiv_shapes.get(right_shape)

        if result is not None:
            return result
        else:
            right_shape_type = type(right_shape)
            if right_shape_type is ShapeLoopCompleteAlternative:
                return right_shape.getOperationBinaryOldDivLShape(self)

            if right_shape_type is ShapeLoopInitialAlternative:
                return operation_result_unknown

            onMissingOperation("OldDiv", self, right_shape)

            return operation_result_unknown

    truediv_shapes = {}

    def getOperationBinaryTrueDivShape(self, right_shape):
        result = self.truediv_shapes.get(right_shape)

        if result is not None:
            return result
        else:
            right_shape_type = type(right_shape)
            if right_shape_type is ShapeLoopCompleteAlternative:
                return right_shape.getOperationBinaryTrueDivLShape(self)

            if right_shape_type is ShapeLoopInitialAlternative:
                return operation_result_unknown

            onMissingOperation("TrueDiv", self, right_shape)

            return operation_result_unknown

    mod_shapes = {}

    def getOperationBinaryModShape(self, right_shape):
        result = self.mod_shapes.get(right_shape)

        if result is not None:
            return result
        else:
            right_shape_type = type(right_shape)
            if right_shape_type is ShapeLoopCompleteAlternative:
                return right_shape.getOperationBinaryModLShape(self)

            if right_shape_type is ShapeLoopInitialAlternative:
                return operation_result_unknown

            onMissingOperation("Mod", self, right_shape)

            return operation_result_unknown

    divmod_shapes = {}

    def getOperationBinaryDivmodShape(self, right_shape):
        result = self.divmod_shapes.get(right_shape)

        if result is not None:
            return result
        else:
            right_shape_type = type(right_shape)
            if right_shape_type is ShapeLoopCompleteAlternative:
                return right_shape.getOperationBinaryDivmodLShape(self)

            if right_shape_type is ShapeLoopInitialAlternative:
                return operation_result_unknown

            onMissingOperation("Divmod", self, right_shape)

            return operation_result_unknown

    pow_shapes = {}

    def getOperationBinaryPowShape(self, right_shape):
        result = self.pow_shapes.get(right_shape)

        if result is not None:
            return result
        else:
            right_shape_type = type(right_shape)
            if right_shape_type is ShapeLoopCompleteAlternative:
                return right_shape.getOperationBinaryPowLShape(self)

            if right_shape_type is ShapeLoopInitialAlternative:
                return operation_result_unknown

            onMissingOperation("Pow", self, right_shape)

            return operation_result_unknown

    lshift_shapes = {}

    def getOperationBinaryLShiftShape(self, right_shape):
        result = self.lshift_shapes.get(right_shape)

        if result is not None:
            return result
        else:
            right_shape_type = type(right_shape)
            if right_shape_type is ShapeLoopCompleteAlternative:
                return right_shape.getOperationBinaryLShiftLShape(self)

            if right_shape_type is ShapeLoopInitialAlternative:
                return operation_result_unknown

            onMissingOperation("LShift", self, right_shape)

            return operation_result_unknown

    rshift_shapes = {}

    def getOperationBinaryRShiftShape(self, right_shape):
        result = self.rshift_shapes.get(right_shape)

        if result is not None:
            return result
        else:
            right_shape_type = type(right_shape)
            if right_shape_type is ShapeLoopCompleteAlternative:
                return right_shape.getOperationBinaryRShiftLShape(self)

            if right_shape_type is ShapeLoopInitialAlternative:
                return operation_result_unknown

            onMissingOperation("RShift", self, right_shape)

            return operation_result_unknown

    bitor_shapes = {}

    def getOperationBinaryBitOrShape(self, right_shape):
        result = self.bitor_shapes.get(right_shape)

        if result is not None:
            return result
        else:
            right_shape_type = type(right_shape)
            if right_shape_type is ShapeLoopCompleteAlternative:
                return right_shape.getOperationBinaryBitOrLShape(self)

            if right_shape_type is ShapeLoopInitialAlternative:
                return operation_result_unknown

            onMissingOperation("BitOr", self, right_shape)

            return operation_result_unknown

    bitand_shapes = {}

    def getOperationBinaryBitAndShape(self, right_shape):
        result = self.bitand_shapes.get(right_shape)

        if result is not None:
            return result
        else:
            right_shape_type = type(right_shape)
            if right_shape_type is ShapeLoopCompleteAlternative:
                return right_shape.getOperationBinaryBitAndLShape(self)

            if right_shape_type is ShapeLoopInitialAlternative:
                return operation_result_unknown

            onMissingOperation("BitAnd", self, right_shape)

            return operation_result_unknown

    bitxor_shapes = {}

    def getOperationBinaryBitXorShape(self, right_shape):
        result = self.bitxor_shapes.get(right_shape)

        if result is not None:
            return result
        else:
            right_shape_type = type(right_shape)
            if right_shape_type is ShapeLoopCompleteAlternative:
                return right_shape.getOperationBinaryBitXorLShape(self)

            if right_shape_type is ShapeLoopInitialAlternative:
                return operation_result_unknown

            onMissingOperation("BitXor", self, right_shape)

            return operation_result_unknown

    ibitor_shapes = {}

    def getOperationInplaceBitOrShape(self, right_shape):
        """Inplace bitor operation shape, for overload."""
        if self.ibitor_shapes:
            result = self.ibitor_shapes.get(right_shape)

            if result is not None:
                return result
            else:
                right_shape_type = type(right_shape)
                if right_shape_type is ShapeLoopCompleteAlternative:
                    return right_shape.getOperationBinaryBitOrLShape(self)

                if right_shape_type is ShapeLoopInitialAlternative:
                    return operation_result_unknown

                onMissingOperation("IBitOr", self, right_shape)

                return operation_result_unknown
        else:
            # By default, inplace add is the same as plain add, the
            # only exception known right now is list, which extend
            # from all iterables, but don't add with them.
            return self.getOperationBinaryBitOrShape(right_shape)

    matmult_shapes = {}

    def getOperationBinaryMatMultShape(self, right_shape):
        result = self.matmult_shapes.get(right_shape)

        if result is not None:
            return result
        else:
            right_shape_type = type(right_shape)
            if right_shape_type is ShapeLoopCompleteAlternative:
                return right_shape.getOperationBinaryBitMatMultLShape(self)

            if right_shape_type is ShapeLoopInitialAlternative:
                return operation_result_unknown

            onMissingOperation("MatMult", self, right_shape)

            return operation_result_unknown

    def getComparisonLtShape(self, right_shape):
        onMissingOperation("Lt", self, right_shape)

        return operation_result_unknown

    def getComparisonLteShape(self, right_shape):
        return self.getComparisonLtShape(right_shape)

    def getComparisonGtShape(self, right_shape):
        return self.getComparisonLtShape(right_shape)

    def getComparisonGteShape(self, right_shape):
        return self.getComparisonLtShape(right_shape)

    def getComparisonEqShape(self, right_shape):
        return self.getComparisonLtShape(right_shape)

    def getComparisonNeqShape(self, right_shape):
        return self.getComparisonLtShape(right_shape)

    def emitAlternatives(self, emit):
        emit(self)


class ShapeTypeUnknown(ShapeBase):
    @staticmethod
    def getOperationBinaryAddShape(right_shape):
        return operation_result_unknown

    @staticmethod
    def getOperationBinarySubShape(right_shape):
        return operation_result_unknown

    @staticmethod
    def getOperationBinaryMultShape(right_shape):
        return operation_result_unknown

    @staticmethod
    def getOperationBinaryFloorDivShape(right_shape):
        return operation_result_unknown

    @staticmethod
    def getOperationBinaryOldDivShape(right_shape):
        return operation_result_unknown

    @staticmethod
    def getOperationBinaryTrueDivShape(right_shape):
        return operation_result_unknown

    @staticmethod
    def getOperationBinaryModShape(right_shape):
        return operation_result_unknown

    @staticmethod
    def getOperationBinaryDivmodShape(right_shape):
        return operation_result_unknown

    @staticmethod
    def getOperationBinaryPowShape(right_shape):
        return operation_result_unknown

    @staticmethod
    def getOperationBinaryLShiftShape(right_shape):
        return operation_result_unknown

    @staticmethod
    def getOperationBinaryRShiftShape(right_shape):
        return operation_result_unknown

    @staticmethod
    def getOperationBinaryBitOrShape(right_shape):
        return operation_result_unknown

    @staticmethod
    def getOperationBinaryBitAndShape(right_shape):
        return operation_result_unknown

    @staticmethod
    def getOperationBinaryBitXorShape(right_shape):
        return operation_result_unknown

    @staticmethod
    def getOperationBinaryMatMultShape(right_shape):
        return operation_result_unknown

    @staticmethod
    def getComparisonLtShape(right_shape):
        return operation_result_unknown


tshape_unknown = ShapeTypeUnknown()


class ShapeTypeUninit(ShapeTypeUnknown):
    pass


tshape_uninit = ShapeTypeUninit()


class ValueShapeBase(object):
    __slots__ = ()

    def hasShapeSlotLen(self):
        return self.getTypeShape().hasShapeSlotLen()


class ValueShapeUnknown(ValueShapeBase):
    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_unknown

    @staticmethod
    def isConstant():
        """ Can't say if it's constant, we don't know anything. """
        return None


# Singleton value for sharing.
vshape_unknown = ValueShapeUnknown()


class ShapeLargeConstantValue(object):
    __slots__ = "shape", "size"

    def __init__(self, size, shape):
        self.size = size
        self.shape = shape

    def getTypeShape(self):
        return self.shape

    @staticmethod
    def isConstant():
        return True

    def hasShapeSlotLen(self):
        return self.shape.hasShapeSlotLen()


class ShapeLargeConstantValuePredictable(ShapeLargeConstantValue):
    __slots__ = ("predictor",)

    def __init__(self, size, predictor, shape):
        ShapeLargeConstantValue.__init__(self, size, shape)

        self.predictor = predictor


class ShapeIterator(ShapeBase, ShapeIteratorMixin):
    @staticmethod
    def hasShapeSlotBool():
        return None

    @staticmethod
    def hasShapeSlotLen():
        return None

    @staticmethod
    def hasShapeSlotInt():
        return None

    @staticmethod
    def hasShapeSlotLong():
        return None

    @staticmethod
    def hasShapeSlotFloat():
        return None

    @staticmethod
    def getShapeIter():
        return tshape_iterator


tshape_iterator = ShapeIterator()


class ShapeLoopInitialAlternative(ShapeBase):
    """Merge of loop wrap around with loop start value.

    Happens at the start of loop blocks. This is for loop closed SSA, to
    make it clear, that the entered value, can be anything really, and
    will only later be clarified.

    They will start out with just one previous, and later be updated with
    all of the variable versions at loop continue times.
    """

    __slots__ = ("type_shapes",)

    def __init__(self, shapes):
        self.type_shapes = shapes

    def emitAlternatives(self, emit):
        for type_shape in self.type_shapes:
            type_shape.emitAlternatives(emit)

    def _collectInitialShape(self, operation):
        result = set()

        for type_shape in self.type_shapes:
            try:
                entry, _description = operation(type_shape)
            except TypeError:
                assert False, type_shape

            if entry is tshape_unknown:
                return tshape_unknown

            result.add(entry)

        return ShapeLoopInitialAlternative(result)

    def getOperationBinaryAddShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown
        else:
            return (
                self._collectInitialShape(
                    operation=lambda left_shape: left_shape.getOperationBinaryAddShape(
                        right_shape
                    )
                ),
                ControlFlowDescriptionFullEscape,
            )

    def getOperationInplaceAddShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown
        else:
            return (
                self._collectInitialShape(
                    operation=lambda left_shape: left_shape.getOperationInplaceAddShape(
                        right_shape
                    )
                ),
                ControlFlowDescriptionFullEscape,
            )

    def getOperationBinarySubShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown
        else:
            return (
                self._collectInitialShape(
                    operation=lambda left_shape: left_shape.getOperationBinarySubShape(
                        right_shape
                    )
                ),
                ControlFlowDescriptionFullEscape,
            )

    def getOperationBinaryMultShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown
        else:
            return (
                self._collectInitialShape(
                    operation=lambda left_shape: left_shape.getOperationBinaryMultShape(
                        right_shape
                    )
                ),
                ControlFlowDescriptionFullEscape,
            )

    def getOperationBinaryFloorDivShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown
        else:
            return (
                self._collectInitialShape(
                    operation=lambda left_shape: left_shape.getOperationBinaryFloorDivShape(
                        right_shape
                    )
                ),
                ControlFlowDescriptionFullEscape,
            )

    def getOperationBinaryOldDivShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown
        else:
            return (
                self._collectInitialShape(
                    operation=lambda left_shape: left_shape.getOperationBinaryOldDivShape(
                        right_shape
                    )
                ),
                ControlFlowDescriptionFullEscape,
            )

    def getOperationBinaryTrueDivShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown
        else:
            return (
                self._collectInitialShape(
                    operation=lambda left_shape: left_shape.getOperationBinaryTrueDivShape(
                        right_shape
                    )
                ),
                ControlFlowDescriptionFullEscape,
            )

    def getOperationBinaryModShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown
        else:
            return (
                self._collectInitialShape(
                    operation=lambda left_shape: left_shape.getOperationBinaryModShape(
                        right_shape
                    )
                ),
                ControlFlowDescriptionFullEscape,
            )

    def getOperationBinaryDivmodShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown
        else:
            return (
                self._collectInitialShape(
                    operation=lambda left_shape: left_shape.getOperationBinaryDivmodShape(
                        right_shape
                    )
                ),
                ControlFlowDescriptionFullEscape,
            )

    def getOperationBinaryPowShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown
        else:
            return (
                self._collectInitialShape(
                    operation=lambda left_shape: left_shape.getOperationBinaryPowShape(
                        right_shape
                    )
                ),
                ControlFlowDescriptionFullEscape,
            )

    def getOperationBinaryLShiftShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown
        else:
            return (
                self._collectInitialShape(
                    operation=lambda left_shape: left_shape.getOperationBinaryLShiftShape(
                        right_shape
                    )
                ),
                ControlFlowDescriptionFullEscape,
            )

    def getOperationBinaryRShiftShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown
        else:
            return (
                self._collectInitialShape(
                    operation=lambda left_shape: left_shape.getOperationBinaryRShiftShape(
                        right_shape
                    )
                ),
                ControlFlowDescriptionFullEscape,
            )

    def getOperationBinaryBitOrShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown
        else:
            return (
                self._collectInitialShape(
                    operation=lambda left_shape: left_shape.getOperationBinaryBitOrShape(
                        right_shape
                    )
                ),
                ControlFlowDescriptionFullEscape,
            )

    def getOperationBinaryBitAndShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown
        else:
            return (
                self._collectInitialShape(
                    operation=lambda left_shape: left_shape.getOperationBinaryBitAndShape(
                        right_shape
                    )
                ),
                ControlFlowDescriptionFullEscape,
            )

    def getOperationBinaryBitXorShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown
        else:
            return (
                self._collectInitialShape(
                    operation=lambda left_shape: left_shape.getOperationBinaryBitXorShape(
                        right_shape
                    )
                ),
                ControlFlowDescriptionFullEscape,
            )

    def getOperationBinaryMatMultShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown
        else:
            return (
                self._collectInitialShape(
                    operation=lambda left_shape: left_shape.getOperationBinaryMatMultShape(
                        right_shape
                    )
                ),
                ControlFlowDescriptionFullEscape,
            )

    def getComparisonLtShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown
        else:
            return (
                self._collectInitialShape(
                    operation=lambda left_shape: left_shape.getComparisonLtShape(
                        right_shape
                    )
                ),
                ControlFlowDescriptionFullEscape,
            )

    def getComparisonLteShape(self, right_shape):
        return self.getComparisonLtShape(right_shape)

    def getComparisonGtShape(self, right_shape):
        return self.getComparisonLtShape(right_shape)

    def getComparisonGteShape(self, right_shape):
        return self.getComparisonLtShape(right_shape)

    def getComparisonEqShape(self, right_shape):
        return self.getComparisonLtShape(right_shape)

    def getComparisonNeqShape(self, right_shape):
        return self.getComparisonLtShape(right_shape)


class ShapeLoopCompleteAlternative(ShapeBase):
    """Merge of loop wrap around with loop start value.

    Happens at the start of loop blocks. This is for loop closed SSA, to
    make it clear, that the entered value, can be one of multiple types,
    but only those.

    They will start out with just one previous, and later be updated with
    all of the variable versions at loop continue times.
    """

    __slots__ = ("type_shapes",)

    def __init__(self, shapes):
        self.type_shapes = shapes

    def __hash__(self):
        # We are unhashable set, and need deep comparison.
        return 27

    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            return False

        return self.type_shapes == other.type_shapes

    def emitAlternatives(self, emit):
        for type_shape in self.type_shapes:
            type_shape.emitAlternatives(emit)

    def _collectShapeOperation(self, operation):
        result = None
        escape_description = None
        single = True

        for type_shape in self.type_shapes:
            entry, description = operation(type_shape)

            if entry is tshape_unknown:
                return operation_result_unknown

            if single:
                if result is None:
                    # First entry, fine.
                    result = entry
                    escape_description = description
                else:
                    # Second entry, not the same, convert to set.
                    if result is not entry:
                        single = False
                        result = set((result, entry))

                        escape_description = set((escape_description, description))
            else:
                result.add(entry)
                escape_description.add(description)

        if single:
            assert result is not None
            return result, escape_description
        else:
            if len(escape_description) > 1:
                if ControlFlowDescriptionFullEscape in escape_description:
                    escape_description = ControlFlowDescriptionFullEscape
                else:
                    assert False
            else:
                (escape_description,) = escape_description

            return ShapeLoopCompleteAlternative(result), escape_description

    def getOperationBinaryAddShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationBinaryAddShape(
                right_shape
            )
        )

    def getOperationInplaceAddShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationInplaceAddShape(
                right_shape
            )
        )

    def getOperationBinarySubShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationBinarySubShape(
                right_shape
            )
        )

    def getOperationBinaryMultShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationBinaryMultShape(
                right_shape
            )
        )

    def getOperationBinaryFloorDivShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationBinaryFloorDivShape(
                right_shape
            )
        )

    def getOperationBinaryOldDivShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationBinaryOldDivShape(
                right_shape
            )
        )

    def getOperationBinaryTrueDivShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationBinaryTrueDivShape(
                right_shape
            )
        )

    def getOperationBinaryModShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationBinaryModShape(
                right_shape
            )
        )

    def getOperationBinaryDivmodShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationBinaryDivmodShape(
                right_shape
            )
        )

    def getOperationBinaryPowShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationBinaryPowShape(
                right_shape
            )
        )

    def getOperationBinaryLShiftShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationBinaryLShiftShape(
                right_shape
            )
        )

    def getOperationBinaryRShiftShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationBinaryRShiftShape(
                right_shape
            )
        )

    def getOperationBinaryBitOrShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationBinaryBitOrShape(
                right_shape
            )
        )

    def getOperationBinaryBitAndShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationBinaryBitAndShape(
                right_shape
            )
        )

    def getOperationBinaryBitXorShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationBinaryBitXorShape(
                right_shape
            )
        )

    def getOperationBinaryMatMultShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationBinaryMatMultShape(
                right_shape
            )
        )

    # Special method to be called by other shapes encountering this type on
    # the right side.
    def getOperationBinaryAddLShape(self, left_shape):
        assert left_shape is not tshape_unknown

        return self._collectShapeOperation(
            operation=left_shape.getOperationBinaryAddShape
        )

    # Special method to be called by other shapes encountering this type on
    # the right side.
    def getOperationBinarySubLShape(self, left_shape):
        assert left_shape is not tshape_unknown

        return self._collectShapeOperation(
            operation=left_shape.getOperationBinarySubShape
        )

    def getOperationBinaryMultLShape(self, left_shape):
        assert left_shape is not tshape_unknown

        return self._collectShapeOperation(
            operation=left_shape.getOperationBinaryMultShape
        )

    def getOperationBinaryFloorDivLShape(self, left_shape):
        assert left_shape is not tshape_unknown

        return self._collectShapeOperation(
            operation=left_shape.getOperationBinaryFloorDivShape
        )

    def getOperationBinaryOldDivLShape(self, left_shape):
        assert left_shape is not tshape_unknown

        return self._collectShapeOperation(
            operation=left_shape.getOperationBinaryOldDivShape
        )

    def getOperationBinaryTrueDivLShape(self, left_shape):
        assert left_shape is not tshape_unknown

        return self._collectShapeOperation(
            operation=left_shape.getOperationBinaryTrueDivShape
        )

    def getOperationBinaryModLShape(self, left_shape):
        assert left_shape is not tshape_unknown

        return self._collectShapeOperation(
            operation=left_shape.getOperationBinaryModShape
        )

    def getOperationBinaryDivmodLShape(self, left_shape):
        assert left_shape is not tshape_unknown

        return self._collectShapeOperation(
            operation=left_shape.getOperationBinaryDivmodShape
        )

    def getOperationBinaryPowLShape(self, left_shape):
        assert left_shape is not tshape_unknown

        return self._collectShapeOperation(
            operation=left_shape.getOperationBinaryPowShape
        )

    def getOperationBinaryLShiftLShape(self, left_shape):
        assert left_shape is not tshape_unknown

        return self._collectShapeOperation(
            operation=left_shape.getOperationBinaryLShiftShape
        )

    def getOperationBinaryRShiftLShape(self, left_shape):
        assert left_shape is not tshape_unknown

        return self._collectShapeOperation(
            operation=left_shape.getOperationBinaryRShiftShape
        )

    def getOperationBinaryBitOrLShape(self, left_shape):
        assert left_shape is not tshape_unknown

        return self._collectShapeOperation(
            operation=left_shape.getOperationBinaryBitOrShape
        )

    def getOperationBinaryBitAndLShape(self, left_shape):
        assert left_shape is not tshape_unknown

        return self._collectShapeOperation(
            operation=left_shape.getOperationBinaryBitAndShape
        )

    def getOperationBinaryBitXorLShape(self, left_shape):
        assert left_shape is not tshape_unknown

        return self._collectShapeOperation(
            operation=left_shape.getOperationBinaryBitXorShape
        )

    def getOperationBinaryMatMultLShape(self, left_shape):
        assert left_shape is not tshape_unknown

        return self._collectShapeOperation(
            operation=left_shape.getOperationBinaryMatMultShape
        )

    def getComparisonLtShape(self, right_shape):
        if right_shape is tshape_unknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getComparisonLtShape(right_shape)
        )

    # Special method to be called by other shapes encountering this type on
    # the right side.
    def getComparisonLtLShape(self, left_shape):
        assert left_shape is not tshape_unknown

        return self._collectShapeOperation(operation=left_shape.getComparisonLtShape)

    def getComparisonLteShape(self, right_shape):
        return self.getComparisonLtShape(right_shape)

    def getComparisonGtShape(self, right_shape):
        return self.getComparisonLtShape(right_shape)

    def getComparisonGteShape(self, right_shape):
        return self.getComparisonLtShape(right_shape)

    def getComparisonEqShape(self, right_shape):
        return self.getComparisonLtShape(right_shape)

    def getComparisonNeqShape(self, right_shape):
        return self.getComparisonLtShape(right_shape)

    def _delegatedCheck(self, check):
        result = None

        for type_shape in self.type_shapes:
            r = check(type_shape)

            if r is None:
                return None
            elif r is True:
                if result is False:
                    return None
                elif result is None:
                    result = True
            elif r is False:
                if result is True:
                    return None
                elif result is None:
                    result = False

        return result

    def hasShapeSlotBool(self):
        return self._delegatedCheck(lambda x: x.hasShapeSlotBool())

    def hasShapeSlotLen(self):
        return self._delegatedCheck(lambda x: x.hasShapeSlotLen())

    def hasShapeSlotIter(self):
        return self._delegatedCheck(lambda x: x.hasShapeSlotIter())

    def hasShapeSlotNext(self):
        return self._delegatedCheck(lambda x: x.hasShapeSlotNext())

    def hasShapeSlotContains(self):
        return self._delegatedCheck(lambda x: x.hasShapeSlotContains())

    def hasShapeSlotInt(self):
        return self._delegatedCheck(lambda x: x.hasShapeSlotInt())

    def hasShapeSlotLong(self):
        return self._delegatedCheck(lambda x: x.hasShapeSlotLong())

    def hasShapeSlotFloat(self):
        return self._delegatedCheck(lambda x: x.hasShapeSlotFloat())

    def hasShapeSlotComplex(self):
        return self._delegatedCheck(lambda x: x.hasShapeSlotComplex())

    def hasShapeSlotBytes(self):
        return self._delegatedCheck(lambda x: x.hasShapeSlotBytes())

    def hasShapeModule(self):
        return self._delegatedCheck(lambda x: x.hasShapeModule())


tshape_unknown_loop = ShapeLoopCompleteAlternative(shapes=(tshape_unknown,))

operation_result_unknown = tshape_unknown, ControlFlowDescriptionFullEscape
