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
""" Nodes for unary and binary operations.

No short-circuit involved, boolean 'not' is an unary operation like '-' is,
no real difference.
"""

import math
from abc import abstractmethod

from nuitka import PythonOperators
from nuitka.Errors import NuitkaAssumptionError
from nuitka.PythonVersions import python_version

from .ExpressionBases import ExpressionChildHavingBase, ExpressionChildrenHavingBase
from .NodeMakingHelpers import (
    makeRaiseExceptionReplacementExpressionFromInstance,
    wrapExpressionWithSideEffects,
)
from .shapes.BuiltinTypeShapes import ShapeTypeBool, ShapeTypeIntOrLong, ShapeTypeTuple
from .shapes.StandardShapes import (
    ShapeLargeConstantValue,
    ShapeLargeConstantValuePredictable,
    vshape_unknown,
)


class ExpressionOperationBinaryBase(ExpressionChildrenHavingBase):
    """ Base class for all binary operation expression.

        Currently, this also implements (badly) the operations
        other than `*``and `+`, where nothing outside of compile
        time constants is really optimized.
    """

    named_children = ("left", "right")
    nice_children = tuple(child_name + " operand" for child_name in named_children)
    getLeft = ExpressionChildrenHavingBase.childGetter("left")
    getRight = ExpressionChildrenHavingBase.childGetter("right")

    def __init__(self, left, right, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self, values={"left": left, "right": right}, source_ref=source_ref
        )

    @staticmethod
    def isExpressionOperationBinary():
        return True

    def getDetails(self):
        return {"operator": self.operator}

    def getOperator(self):
        return self.operator

    inplace_suspect = False

    def markAsInplaceSuspect(self):
        self.inplace_suspect = True

    def unmarkAsInplaceSuspect(self):
        self.inplace_suspect = False

    def isInplaceSuspect(self):
        return self.inplace_suspect

    # TODO: Make this unnecessary by specializing for all operations.
    def computeExpression(self, trace_collection):
        assert self.operator not in (
            "Mult",
            "Add",
            "Sub",
            "FloorDiv",
            "TrueDiv",
            "Div",
        ), self.operator

        left = self.subnode_left
        right = self.subnode_right

        if left.isCompileTimeConstant() and right.isCompileTimeConstant():
            left_value = left.getCompileTimeConstant()
            right_value = right.getCompileTimeConstant()

            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: self.simulator(left_value, right_value),
                description="Operator '%s' with constant arguments." % self.operator,
            )

        # TODO: May go down to MemoryError for compile time constant overflow
        # ones.
        trace_collection.onExceptionRaiseExit(BaseException)

        # The value of these nodes escaped and could change its contents.
        trace_collection.removeKnowledge(left)
        trace_collection.removeKnowledge(right)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        return self, None, None

    def getOperands(self):
        return (self.subnode_left, self.subnode_right)

    def mayRaiseExceptionOperation(self):
        # TODO: This is to keep the same way as before before specializing to
        # actual optimal stuff.
        return self.mayRaiseException(BaseException)


# TODO: Only while ExpressionOperationBinaryBase is still taken.
class ExpressionOperationBinaryConcreteBase(ExpressionOperationBinaryBase):

    shape = None

    def __init__(self, left, right, source_ref):
        ExpressionOperationBinaryBase.__init__(
            self, left=left, right=right, source_ref=source_ref
        )

        self.type_shape = None
        self.escape_desc = None

    def getDetails(self):
        return {}

    def getTypeShape(self):
        return self.type_shape

    def getValueShape(self):
        if self.shape is not None:
            return self.shape
        else:
            return vshape_unknown

    @abstractmethod
    def _getOperationShape(self):
        pass

    @staticmethod
    def _isTooLarge():
        return False

    @staticmethod
    def _onTooLarge():
        pass

    def canCreateUnsupportedException(self):
        return hasattr(self.subnode_left.getTypeShape(), "typical_value") and hasattr(
            self.subnode_right.getTypeShape(), "typical_value"
        )

    def createUnsupportedException(self):
        left = self.subnode_left.getTypeShape().typical_value
        right = self.subnode_right.getTypeShape().typical_value

        try:
            self.simulator(left, right)
        except TypeError as e:
            return e
        else:
            raise NuitkaAssumptionError(
                "Unexpected no-exception doing operation simulation",
                self.operator,
                self.subnode_left.getTypeShape(),
                self.subnode_right.getTypeShape(),
                repr(left),
                repr(right),
            )

    def extractSideEffectsPreOperation(self):
        return self.subnode_left, self.subnode_right

    def computeExpression(self, trace_collection):
        # Nothing to do anymore for large constants.
        if self.shape is not None and self.shape.isConstant():
            return self, None, None

        left = self.subnode_left
        right = self.subnode_right

        self.type_shape, self.escape_desc = self._getOperationShape()

        if left.isCompileTimeConstant() and right.isCompileTimeConstant():
            if not self._isTooLarge():
                left_value = left.getCompileTimeConstant()
                right_value = right.getCompileTimeConstant()

                return trace_collection.getCompileTimeComputationResult(
                    node=self,
                    computation=lambda: self.simulator(left_value, right_value),
                    description="Operator '%s' with constant arguments."
                    % self.operator,
                )

        exception_raise_exit = self.escape_desc.getExceptionExit()
        if exception_raise_exit is not None:
            trace_collection.onExceptionRaiseExit(exception_raise_exit)

            if (
                self.escape_desc.isUnsupported()
                and self.canCreateUnsupportedException()
            ):
                result = wrapExpressionWithSideEffects(
                    new_node=makeRaiseExceptionReplacementExpressionFromInstance(
                        expression=self, exception=self.createUnsupportedException()
                    ),
                    old_node=self,
                    side_effects=self.extractSideEffectsPreOperation(),
                )

                return (
                    result,
                    "new_raise",  # TODO: More appropriate tag maybe.
                    """Replaced operator '%s%s%s' arguments that cannot work."""
                    % (
                        self.operator,
                        self.subnode_left.getTypeShape(),
                        self.subnode_right.getTypeShape(),
                    ),
                )

        if self.escape_desc.isValueEscaping():
            # The value of these nodes escaped and could change its contents.
            trace_collection.removeKnowledge(left)
            trace_collection.removeKnowledge(right)

        if self.escape_desc.isControlFlowEscape():
            # Any code could be run, note that.
            trace_collection.onControlFlowEscape(self)

        return self, None, None

    def mayRaiseExceptionOperation(self):
        return (
            self.escape_desc is None or self.escape_desc.getExceptionExit() is not None
        )

    def mayRaiseException(self, exception_type):
        # TODO: Match more precisely
        return (
            self.escape_desc is None
            or self.escape_desc.getExceptionExit() is not None
            or self.subnode_left.mayRaiseException(exception_type)
            or self.subnode_right.mayRaiseException(exception_type)
        )

    def canPredictIterationValues(self):
        # TODO: Actually we could very well, esp. for sequence repeats.
        # pylint: disable=no-self-use
        return False


class ExpressionOperationBinaryAdd(ExpressionOperationBinaryConcreteBase):
    kind = "EXPRESSION_OPERATION_BINARY_ADD"

    operator = "Add"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryAddShape(
            self.subnode_right.getTypeShape()
        )

    def _isTooLarge(self):
        if self.subnode_left.isKnownToBeIterable(
            None
        ) and self.subnode_right.isKnownToBeIterable(None):
            size = (
                self.subnode_left.getIterationLength()
                + self.subnode_right.getIterationLength()
            )

            # TODO: Actually could make a predictor, but we don't use it yet.
            self.shape = ShapeLargeConstantValuePredictable(
                size=size,
                predictor=None,  # predictValuesFromRightAndLeftValue,
                shape=self.subnode_left.getTypeShape(),
            )

            return size > 256
        else:
            return False


class ExpressionOperationBinarySub(ExpressionOperationBinaryConcreteBase):
    kind = "EXPRESSION_OPERATION_BINARY_SUB"

    operator = "Sub"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinarySubShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationBinaryMult(ExpressionOperationBinaryConcreteBase):
    kind = "EXPRESSION_OPERATION_BINARY_MULT"

    operator = "Mult"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryMultShape(
            self.subnode_right.getTypeShape()
        )

    def _isTooLarge(self):
        if self.subnode_right.isNumberConstant():
            iter_length = self.subnode_left.getIterationLength()

            if iter_length is not None:
                size = iter_length * self.subnode_right.getCompileTimeConstant()
                if size > 256:
                    self.shape = ShapeLargeConstantValuePredictable(
                        size=size,
                        predictor=None,  # predictValuesFromRightAndLeftValue,
                        shape=self.subnode_left.getTypeShape(),
                    )

                    return True

            if self.subnode_left.isNumberConstant():
                if (
                    self.subnode_left.isIndexConstant()
                    and self.subnode_right.isIndexConstant()
                ):
                    # Estimate with logarithm, if the result of number
                    # calculations is computable with acceptable effort,
                    # otherwise, we will have to do it at runtime.
                    left_value = self.subnode_left.getCompileTimeConstant()

                    if left_value != 0:
                        right_value = self.subnode_right.getCompileTimeConstant()

                        # TODO: Is this really useful, can this be really slow.
                        if right_value != 0:
                            if (
                                math.log10(abs(left_value))
                                + math.log10(abs(right_value))
                                > 20
                            ):
                                self.shape = ShapeLargeConstantValue(
                                    size=None, shape=ShapeTypeIntOrLong
                                )

                                return True

        elif self.subnode_left.isNumberConstant():
            iter_length = self.subnode_right.getIterationLength()

            if iter_length is not None:
                left_value = self.subnode_left.getCompileTimeConstant()

                size = iter_length * left_value
                if iter_length * left_value > 256:
                    self.shape = ShapeLargeConstantValuePredictable(
                        size=size,
                        predictor=None,  # predictValuesFromRightAndLeftValue,
                        shape=self.subnode_right.getTypeShape(),
                    )

                    return True

        return False

    def getIterationLength(self):
        left_length = self.getLeft().getIterationLength()

        if left_length is not None:
            right_value = self.getRight().getIntegerValue()

            if right_value is not None:
                return left_length * right_value

        right_length = self.getRight().getIterationLength()

        if right_length is not None:
            left_value = self.getLeft().getIntegerValue()

            if left_value is not None:
                return right_length * left_value

        return ExpressionOperationBinaryBase.getIterationLength(self)

    def extractSideEffects(self):
        left_length = self.getLeft().getIterationLength()

        if left_length is not None:
            right_value = self.getRight().getIntegerValue()

            if right_value is not None:
                return (
                    self.getLeft().extractSideEffects()
                    + self.getRight().extractSideEffects()
                )

        right_length = self.getRight().getIterationLength()

        if right_length is not None:
            left_value = self.getLeft().getIntegerValue()

            if left_value is not None:
                return (
                    self.getLeft().extractSideEffects()
                    + self.getRight().extractSideEffects()
                )

        return ExpressionOperationBinaryBase.extractSideEffects(self)


class ExpressionOperationBinaryFloorDiv(ExpressionOperationBinaryConcreteBase):
    kind = "EXPRESSION_OPERATION_BINARY_FLOOR_DIV"

    operator = "FloorDiv"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryFloorDivShape(
            self.subnode_right.getTypeShape()
        )


if python_version < 300:

    class ExpressionOperationBinaryOldDiv(ExpressionOperationBinaryConcreteBase):
        kind = "EXPRESSION_OPERATION_BINARY_OLD_DIV"

        operator = "Div"
        simulator = PythonOperators.binary_operator_functions[operator]

        def _getOperationShape(self):
            return self.subnode_left.getTypeShape().getOperationBinaryOldDivShape(
                self.subnode_right.getTypeShape()
            )


class ExpressionOperationBinaryTrueDiv(ExpressionOperationBinaryConcreteBase):
    kind = "EXPRESSION_OPERATION_BINARY_TRUE_DIV"

    operator = "TrueDiv"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryTrueDivShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationBinaryMod(ExpressionOperationBinaryConcreteBase):
    kind = "EXPRESSION_OPERATION_BINARY_MOD"

    operator = "Mod"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryModShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationBinaryPow(ExpressionOperationBinaryConcreteBase):
    kind = "EXPRESSION_OPERATION_BINARY_POW"

    operator = "Pow"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryPowShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationBinaryLshift(ExpressionOperationBinaryConcreteBase):
    kind = "EXPRESSION_OPERATION_BINARY_LSHIFT"

    operator = "LShift"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryLShiftShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationBinaryRshift(ExpressionOperationBinaryConcreteBase):
    kind = "EXPRESSION_OPERATION_BINARY_RSHIFT"

    operator = "RShift"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryRShiftShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationBinaryBitOr(ExpressionOperationBinaryConcreteBase):
    kind = "EXPRESSION_OPERATION_BINARY_BIT_OR"

    operator = "BitOr"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryBitOrShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationBinaryBitAnd(ExpressionOperationBinaryConcreteBase):
    kind = "EXPRESSION_OPERATION_BINARY_BIT_AND"

    operator = "BitAnd"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryBitAndShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationBinaryBitXor(ExpressionOperationBinaryConcreteBase):
    kind = "EXPRESSION_OPERATION_BINARY_BIT_XOR"

    operator = "BitXor"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryBitXorShape(
            self.subnode_right.getTypeShape()
        )


if python_version >= 350:

    class ExpressionOperationBinaryMatMult(ExpressionOperationBinaryConcreteBase):
        kind = "EXPRESSION_OPERATION_BINARY_MAT_MULT"

        operator = "MatMult"
        simulator = PythonOperators.binary_operator_functions[operator]

        def _getOperationShape(self):
            return self.subnode_left.getTypeShape().getOperationBinaryMatMultShape(
                self.subnode_right.getTypeShape()
            )


class ExpressionOperationBinaryDivmod(ExpressionOperationBinaryBase):
    kind = "EXPRESSION_OPERATION_BINARY_DIVMOD"

    operator = "Divmod"
    simulator = PythonOperators.binary_operator_functions[operator]

    def __init__(self, left, right, source_ref):
        ExpressionOperationBinaryBase.__init__(
            self, left=left, right=right, source_ref=source_ref
        )

        self.shape = None

    # TODO: Value shape is two elemented tuple of int or float both.
    def getTypeShape(self):
        return ShapeTypeTuple


_operator2nodeclass = {
    "Add": ExpressionOperationBinaryAdd,
    "Sub": ExpressionOperationBinarySub,
    "Mult": ExpressionOperationBinaryMult,
    "FloorDiv": ExpressionOperationBinaryFloorDiv,
    "TrueDiv": ExpressionOperationBinaryTrueDiv,
    "Mod": ExpressionOperationBinaryMod,
    "Pow": ExpressionOperationBinaryPow,
    "LShift": ExpressionOperationBinaryLshift,
    "RShift": ExpressionOperationBinaryRshift,
    "BitOr": ExpressionOperationBinaryBitOr,
    "BitAnd": ExpressionOperationBinaryBitAnd,
    "BitXor": ExpressionOperationBinaryBitXor,
}

if python_version < 300:
    _operator2nodeclass["Div"] = ExpressionOperationBinaryOldDiv

if python_version >= 350:
    _operator2nodeclass["MatMult"] = ExpressionOperationBinaryMatMult


def makeBinaryOperationNode(operator, left, right, source_ref):
    node_class = _operator2nodeclass[operator]

    return node_class(left=left, right=right, source_ref=source_ref)


class ExpressionOperationUnaryBase(ExpressionChildHavingBase):
    named_child = "operand"
    getOperand = ExpressionChildHavingBase.childGetter("operand")

    __slots__ = ("operator", "simulator")

    def __init__(self, operator, operand, source_ref):
        ExpressionChildHavingBase.__init__(self, value=operand, source_ref=source_ref)

        self.operator = operator

        self.simulator = PythonOperators.unary_operator_functions[operator]

    def getDetails(self):
        return {"operator": self.operator}

    def getOperator(self):
        return self.operator

    def computeExpression(self, trace_collection):
        operator = self.getOperator()
        operand = self.subnode_operand

        if operand.isCompileTimeConstant():
            operand_value = operand.getCompileTimeConstant()

            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: self.simulator(operand_value),
                description="Operator '%s' with constant argument." % operator,
            )
        else:
            # TODO: May go down to MemoryError for compile time constant overflow
            # ones.
            trace_collection.onExceptionRaiseExit(BaseException)

            # The value of that node escapes and could change its contents.
            trace_collection.removeKnowledge(operand)

            # Any code could be run, note that.
            trace_collection.onControlFlowEscape(self)

            return self, None, None

    def getOperands(self):
        return (self.getOperand(),)

    @staticmethod
    def isExpressionOperationUnary():
        return True


class ExpressionOperationUnary(ExpressionOperationUnaryBase):
    kind = "EXPRESSION_OPERATION_UNARY"

    def __init__(self, operator, operand, source_ref):
        assert operand.isExpression(), operand

        ExpressionOperationUnaryBase.__init__(
            self, operator=operator, operand=operand, source_ref=source_ref
        )


class ExpressionOperationNot(ExpressionOperationUnaryBase):
    kind = "EXPRESSION_OPERATION_NOT"

    def __init__(self, operand, source_ref):
        ExpressionOperationUnaryBase.__init__(
            self, operator="Not", operand=operand, source_ref=source_ref
        )

    def getTypeShape(self):
        return ShapeTypeBool

    def getDetails(self):
        return {}

    def computeExpression(self, trace_collection):
        return self.getOperand().computeExpressionOperationNot(
            not_node=self, trace_collection=trace_collection
        )

    def mayRaiseException(self, exception_type):
        return self.getOperand().mayRaiseException(
            exception_type
        ) or self.getOperand().mayRaiseExceptionBool(exception_type)

    def mayRaiseExceptionBool(self, exception_type):
        return self.getOperand().mayRaiseExceptionBool(exception_type)

    def getTruthValue(self):
        result = self.getOperand().getTruthValue()

        # Need to invert the truth value of operand of course here.
        return None if result is None else not result

    def mayHaveSideEffects(self):
        operand = self.getOperand()

        if operand.mayHaveSideEffects():
            return True

        return operand.mayHaveSideEffectsBool()

    def mayHaveSideEffectsBool(self):
        return self.getOperand().mayHaveSideEffectsBool()

    def extractSideEffects(self):
        operand = self.getOperand()

        # TODO: Find the common ground of these, and make it an expression
        # method.
        if operand.isExpressionMakeSequence():
            return operand.extractSideEffects()

        if operand.isExpressionMakeDict():
            return operand.extractSideEffects()

        return (self,)


class ExpressionOperationAbs(ExpressionOperationUnaryBase):
    kind = "EXPRESSION_OPERATION_ABS"

    def __init__(self, operand, source_ref):
        ExpressionOperationUnaryBase.__init__(
            self, operator="Abs", operand=operand, source_ref=source_ref
        )

    def computeExpression(self, trace_collection):
        return self.getOperand().computeExpressionAbs(
            abs_node=self, trace_collection=trace_collection
        )

    def mayRaiseException(self, exception_type):
        operand = self.getOperand()

        if operand.mayRaiseException(exception_type):
            return True

        return operand.mayRaiseExceptionAbs(exception_type)

    def mayHaveSideEffects(self):
        operand = self.getOperand()

        if operand.mayHaveSideEffects():
            return True

        return operand.mayHaveSideEffectsAbs()


class ExpressionOperationBinaryInplace(ExpressionOperationBinaryBase):
    """ All binary operation expressions that have no specialization.

        This is used for all operations that do not yet have
        dedicated classes.
    """

    kind = "EXPRESSION_OPERATION_BINARY_INPLACE"

    def __init__(self, operator, left, right, source_ref):
        assert left.isExpression() and right.isExpression, (left, right)

        ExpressionOperationBinaryBase.__init__(
            self, left=left, right=right, source_ref=source_ref
        )

        self.operator = operator
        self.simulator = PythonOperators.binary_operator_functions[operator]

    @staticmethod
    def isExpressionOperationBinary():
        return True

    def computeExpression(self, trace_collection):
        # In-place operation requires extra care to avoid corruption of
        # values.
        left = self.getLeft()
        right = self.getRight()

        if left.isCompileTimeConstant():
            # Then we made a mistake currently.
            assert not left.isMutable(), self
            source_ref = self.getSourceReference()

            result = makeBinaryOperationNode(
                operator=self.getOperator()[1:],
                left=left,
                right=right,
                source_ref=source_ref,
            )

            trace_collection.signalChange(
                tags="new_expression",
                source_ref=source_ref,
                message="""\
Lowered in-place binary operation of compile time constant to binary operation.""",
            )

            return result.computeExpression(trace_collection)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        # The value of these nodes escaped and could change its contents.
        trace_collection.removeKnowledge(left)
        trace_collection.removeKnowledge(right)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        return self, None, None


def makeExpressionOperationBinaryInplace(operator, left, right, source_ref):
    # TODO: Add more specializations for common operators.

    return ExpressionOperationBinaryInplace(
        operator=operator, left=left, right=right, source_ref=source_ref
    )
