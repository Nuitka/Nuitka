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
""" Standard shapes that commonly appear. """

from nuitka.codegen.c_types.CTypePyObjectPtrs import CTypePyObjectPtr
from nuitka.codegen.Reports import onMissingOperation

from .ControlFlowDescriptions import ControlFlowDescriptionFullEscape


class ShapeBase(object):
    @staticmethod
    def getTypeName():
        return None

    helper_code = "OBJECT"

    @staticmethod
    def getCType():
        return CTypePyObjectPtr

    @staticmethod
    def getShapeIter():
        return ShapeUnknown

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

    add_shapes = {}

    @classmethod
    def getOperationBinaryAddShape(cls, right_shape):
        result = cls.add_shapes.get(right_shape)

        if result is not None:
            return result
        else:
            right_shape_type = type(right_shape)
            if right_shape_type is ShapeLoopCompleteAlternative:
                return right_shape.getOperationBinaryAddLShape(cls)

            if right_shape_type is ShapeLoopInitialAlternative:
                return operation_result_unknown

            onMissingOperation("Add", cls, right_shape)

            return operation_result_unknown

    sub_shapes = {}

    @classmethod
    def getOperationBinarySubShape(cls, right_shape):
        result = cls.sub_shapes.get(right_shape)

        if result is not None:
            return result
        else:
            right_shape_type = type(right_shape)
            if right_shape_type is ShapeLoopCompleteAlternative:
                return right_shape.getOperationBinarySubLShape(cls)

            if right_shape_type is ShapeLoopInitialAlternative:
                return operation_result_unknown

            onMissingOperation("Sub", cls, right_shape)

            return operation_result_unknown

    mul_shapes = {}

    @classmethod
    def getOperationBinaryMultShape(cls, right_shape):
        result = cls.mul_shapes.get(right_shape)

        if result is not None:
            return result
        else:
            right_shape_type = type(right_shape)
            if right_shape_type is ShapeLoopCompleteAlternative:
                return right_shape.getOperationBinaryMultLShape(cls)

            if right_shape_type is ShapeLoopInitialAlternative:
                return operation_result_unknown

            onMissingOperation("Mult", cls, right_shape)

            return operation_result_unknown

    floordiv_shapes = {}

    @classmethod
    def getOperationBinaryFloorDivShape(cls, right_shape):
        result = cls.floordiv_shapes.get(right_shape)

        if result is not None:
            return result
        else:
            right_shape_type = type(right_shape)
            if right_shape_type is ShapeLoopCompleteAlternative:
                return right_shape.getOperationBinaryFloorDivLShape(cls)

            if right_shape_type is ShapeLoopInitialAlternative:
                return operation_result_unknown

            # TODO: Not yet there.
            # onMissingOperation("FloorDiv", cls, right_shape)

            return operation_result_unknown

    olddiv_shapes = {}

    @classmethod
    def getOperationBinaryOldDivShape(cls, right_shape):
        result = cls.olddiv_shapes.get(right_shape)

        if result is not None:
            return result
        else:
            right_shape_type = type(right_shape)
            if right_shape_type is ShapeLoopCompleteAlternative:
                return right_shape.getOperationBinaryOldDivLShape(cls)

            if right_shape_type is ShapeLoopInitialAlternative:
                return operation_result_unknown

            # TODO: Not yet there.
            # onMissingOperation("OldDiv", cls, right_shape)

            return operation_result_unknown

    truediv_shapes = {}

    @classmethod
    def getOperationBinaryTrueDivShape(cls, right_shape):
        result = cls.truediv_shapes.get(right_shape)

        if result is not None:
            return result
        else:
            right_shape_type = type(right_shape)
            if right_shape_type is ShapeLoopCompleteAlternative:
                return right_shape.getOperationBinaryTrueDivLShape(cls)

            if right_shape_type is ShapeLoopInitialAlternative:
                return operation_result_unknown

            # TODO: Not yet there.
            # onMissingOperation("TrueDiv", cls, right_shape)

            return operation_result_unknown

    @classmethod
    def getComparisonLtShape(cls, right_shape):
        onMissingOperation("Lt", cls, right_shape)

        return operation_result_unknown

    @classmethod
    def getComparisonLteShape(cls, right_shape):
        return cls.getComparisonLtShape(right_shape)

    @classmethod
    def getComparisonGtShape(cls, right_shape):
        return cls.getComparisonLtShape(right_shape)

    @classmethod
    def getComparisonGteShape(cls, right_shape):
        return cls.getComparisonLtShape(right_shape)

    @classmethod
    def getComparisonEqShape(cls, right_shape):
        return cls.getComparisonLtShape(right_shape)

    @classmethod
    def getComparisonNeqShape(cls, right_shape):
        return cls.getComparisonLtShape(right_shape)

    @classmethod
    def emitAlternatives(cls, emit):
        emit(cls)


class ShapeUnknown(ShapeBase):
    @classmethod
    def getOperationBinaryAddShape(cls, right_shape):
        return operation_result_unknown

    @classmethod
    def getOperationBinarySubShape(cls, right_shape):
        return operation_result_unknown

    @classmethod
    def getOperationBinaryMultShape(cls, right_shape):
        return operation_result_unknown

    @classmethod
    def getOperationBinaryFloorDivShape(cls, right_shape):
        return operation_result_unknown

    @classmethod
    def getOperationBinaryOldDivShape(cls, right_shape):
        return operation_result_unknown

    @classmethod
    def getOperationBinaryTrueDivShape(cls, right_shape):
        return operation_result_unknown

    @classmethod
    def getComparisonLtShape(cls, right_shape):
        return operation_result_unknown


class ValueShapeBase(object):
    __slots__ = ()

    def hasShapeSlotLen(self):
        return self.getTypeShape().hasShapeSlotLen()


class ValueShapeUnknown(ValueShapeBase):
    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return ShapeUnknown


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


class ShapeIterator(ShapeBase):
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
    def hasShapeSlotIter():
        return True

    @staticmethod
    def hasShapeSlotNext():
        return True

    @staticmethod
    def getShapeIter():
        return ShapeIterator

    @staticmethod
    def hasShapeSlotContains():
        return True


class ShapeLoopInitialAlternative(ShapeBase):
    """ Merge of loop wrap around with loop start value.

        Happens at the start of loop blocks. This is for loop closed SSA, to
        make it clear, that the entered value, can be anything really, and
        will only later be clarified.

        They will start out with just one previous, and later be updated with
        all of the variable versions at loop continue times.
    """

    __slots__ = ("type_shapes",)

    def __init__(self, shapes):
        self.type_shapes = shapes

        assert ShapeLoopCompleteAlternative not in shapes

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

            if entry is ShapeUnknown:
                return ShapeUnknown

            result.add(entry)

        return ShapeLoopInitialAlternative(result)

    def getOperationBinaryAddShape(self, right_shape):
        if right_shape is ShapeUnknown:
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

    def getOperationBinarySubShape(self, right_shape):
        if right_shape is ShapeUnknown:
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
        if right_shape is ShapeUnknown:
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
        if right_shape is ShapeUnknown:
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
        if right_shape is ShapeUnknown:
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
        if right_shape is ShapeUnknown:
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

    def getComparisonLtShape(self, right_shape):
        if right_shape is ShapeUnknown:
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
    """ Merge of loop wrap around with loop start value.

        Happens at the start of loop blocks. This is for loop closed SSA, to
        make it clear, that the entered value, can be one of multiple types,
        but only those.

        They will start out with just one previous, and later be updated with
        all of the variable versions at loop continue times.
    """

    __slots__ = ("type_shapes",)

    def __init__(self, shapes):
        self.type_shapes = shapes

        assert ShapeLoopCompleteAlternative not in shapes

    def emitAlternatives(self, emit):
        for type_shape in self.type_shapes:
            type_shape.emitAlternatives(emit)

    def _collectShapeOperation(self, operation):
        result = None
        escape_description = None
        single = True

        for type_shape in self.type_shapes:
            entry, description = operation(type_shape)

            if entry is ShapeUnknown:
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
                escape_description, = escape_description

            return ShapeLoopCompleteAlternative(result), escape_description

    def getOperationBinaryAddShape(self, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationBinaryAddShape(
                right_shape
            )
        )

    def getOperationBinarySubShape(self, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationBinarySubShape(
                right_shape
            )
        )

    def getOperationBinaryMultShape(self, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationBinaryMultShape(
                right_shape
            )
        )

    def getOperationBinaryFloorDivShape(self, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationBinaryFloorDivShape(
                right_shape
            )
        )

    def getOperationBinaryOldDivShape(self, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationBinaryOldDivShape(
                right_shape
            )
        )

    def getOperationBinaryTrueDivShape(self, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getOperationBinaryTrueDivShape(
                right_shape
            )
        )

    # Special method to be called by other shapes encountering this type on
    # the right side.
    def getOperationBinaryAddLShape(self, left_shape):
        assert left_shape is not ShapeUnknown

        return self._collectShapeOperation(
            operation=left_shape.getOperationBinaryAddShape
        )

    # Special method to be called by other shapes encountering this type on
    # the right side.
    def getOperationBinarySubLShape(self, left_shape):
        assert left_shape is not ShapeUnknown

        return self._collectShapeOperation(
            operation=left_shape.getOperationBinarySubShape
        )

    def getOperationBinaryMultLShape(self, left_shape):
        assert left_shape is not ShapeUnknown

        return self._collectShapeOperation(
            operation=left_shape.getOperationBinaryMultShape
        )

    def getOperationBinaryFloorDivLShape(self, left_shape):
        assert left_shape is not ShapeUnknown

        return self._collectShapeOperation(
            operation=left_shape.getOperationBinaryFloorDivShape
        )

    def getOperationBinaryOldDivLShape(self, left_shape):
        assert left_shape is not ShapeUnknown

        return self._collectShapeOperation(
            operation=left_shape.getOperationBinaryOldDivShape
        )

    def getOperationBinaryTrueDivLShape(self, left_shape):
        assert left_shape is not ShapeUnknown

        return self._collectShapeOperation(
            operation=left_shape.getOperationBinaryTrueDivShape
        )

    def getComparisonLtShape(self, right_shape):
        if right_shape is ShapeUnknown:
            return operation_result_unknown

        return self._collectShapeOperation(
            operation=lambda left_shape: left_shape.getComparisonLtShape(right_shape)
        )

    # Special method to be called by other shapes encountering this type on
    # the right side.
    def getComparisonLtLShape(self, left_shape):
        assert left_shape is not ShapeUnknown

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


operation_result_unknown = ShapeUnknown, ControlFlowDescriptionFullEscape
