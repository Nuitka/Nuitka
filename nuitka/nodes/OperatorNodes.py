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
""" Nodes for unary and binary operations.

No short-circuit involved, boolean 'not' is an unary operation like '-' is,
no real difference.
"""

import copy
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
from .shapes.BuiltinTypeShapes import tshape_bool, tshape_int_or_long
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

    shape = vshape_unknown

    def __init__(self, left, right, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self, values={"left": left, "right": right}, source_ref=source_ref
        )

        self.type_shape = None
        self.escape_desc = None

    def getDetails(self):
        return {}

    @staticmethod
    def isExpressionOperationBinary():
        return True

    def getOperator(self):
        return self.operator

    inplace_suspect = False

    def markAsInplaceSuspect(self):
        self.inplace_suspect = True

    def unmarkAsInplaceSuspect(self):
        self.inplace_suspect = False

    def isInplaceSuspect(self):
        return self.inplace_suspect

    def getOperands(self):
        return (self.subnode_left, self.subnode_right)

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

    def getTypeShape(self):
        if self.type_shape is None:
            self.type_shape, self.escape_desc = self._getOperationShape()

        return self.type_shape

    @abstractmethod
    def _getOperationShape(self):
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
                self.simulator,
                self.subnode_left.getTypeShape(),
                self.subnode_right.getTypeShape(),
                repr(left),
                repr(right),
            )

    def extractSideEffectsPreOperation(self):
        return self.subnode_left, self.subnode_right

    @staticmethod
    def _isTooLarge():
        return False

    def _simulateOperation(self, trace_collection):
        left_value = self.subnode_left.getCompileTimeConstant()
        right_value = self.subnode_right.getCompileTimeConstant()

        # Avoid mutating owned by nodes values and potentially shared.
        if self.subnode_left.isMutable():
            left_value = copy.copy(left_value)

        return trace_collection.getCompileTimeComputationResult(
            node=self,
            computation=lambda: self.simulator(left_value, right_value),
            description="Operator '%s' with constant arguments." % self.operator,
        )

    def computeExpression(self, trace_collection):
        # Nothing to do anymore for large constants.
        if self.shape is not None and self.shape.isConstant():
            return self, None, None

        left = self.subnode_left
        right = self.subnode_right

        self.type_shape, self.escape_desc = self._getOperationShape()

        if left.isCompileTimeConstant() and right.isCompileTimeConstant():
            if not self._isTooLarge():
                return self._simulateOperation(trace_collection)

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
                    "new_raise",
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

    def canPredictIterationValues(self):
        # TODO: Actually we could very well, esp. for sequence repeats.
        # pylint: disable=no-self-use
        return False


class ExpressionOperationAddMixin(object):
    def getValueShape(self):
        return self.shape

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


class ExpressionOperationBinaryAdd(
    ExpressionOperationAddMixin, ExpressionOperationBinaryBase
):
    kind = "EXPRESSION_OPERATION_BINARY_ADD"

    operator = "Add"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryAddShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationBinarySub(ExpressionOperationBinaryBase):
    kind = "EXPRESSION_OPERATION_BINARY_SUB"

    operator = "Sub"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinarySubShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationMultMixin(object):
    def getValueShape(self):
        return self.shape

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
                                    size=None, shape=tshape_int_or_long
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


class ExpressionOperationBinaryMult(
    ExpressionOperationMultMixin, ExpressionOperationBinaryBase
):
    kind = "EXPRESSION_OPERATION_BINARY_MULT"

    operator = "Mult"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryMultShape(
            self.subnode_right.getTypeShape()
        )

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


class ExpressionOperationBinaryFloorDiv(ExpressionOperationBinaryBase):
    kind = "EXPRESSION_OPERATION_BINARY_FLOOR_DIV"

    operator = "FloorDiv"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryFloorDivShape(
            self.subnode_right.getTypeShape()
        )


if python_version < 300:

    class ExpressionOperationBinaryOldDiv(ExpressionOperationBinaryBase):
        kind = "EXPRESSION_OPERATION_BINARY_OLD_DIV"

        operator = "OldDiv"
        simulator = PythonOperators.binary_operator_functions[operator]

        def _getOperationShape(self):
            return self.subnode_left.getTypeShape().getOperationBinaryOldDivShape(
                self.subnode_right.getTypeShape()
            )


class ExpressionOperationBinaryTrueDiv(ExpressionOperationBinaryBase):
    kind = "EXPRESSION_OPERATION_BINARY_TRUE_DIV"

    operator = "TrueDiv"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryTrueDivShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationBinaryMod(ExpressionOperationBinaryBase):
    kind = "EXPRESSION_OPERATION_BINARY_MOD"

    operator = "Mod"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryModShape(
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

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryDivmodShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationBinaryPow(ExpressionOperationBinaryBase):
    kind = "EXPRESSION_OPERATION_BINARY_POW"

    operator = "Pow"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryPowShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationBinaryLshift(ExpressionOperationBinaryBase):
    kind = "EXPRESSION_OPERATION_BINARY_LSHIFT"

    operator = "LShift"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryLShiftShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationBinaryRshift(ExpressionOperationBinaryBase):
    kind = "EXPRESSION_OPERATION_BINARY_RSHIFT"

    operator = "RShift"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryRShiftShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationBinaryBitOr(ExpressionOperationBinaryBase):
    kind = "EXPRESSION_OPERATION_BINARY_BIT_OR"

    operator = "BitOr"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryBitOrShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationBinaryBitAnd(ExpressionOperationBinaryBase):
    kind = "EXPRESSION_OPERATION_BINARY_BIT_AND"

    operator = "BitAnd"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryBitAndShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationBinaryBitXor(ExpressionOperationBinaryBase):
    kind = "EXPRESSION_OPERATION_BINARY_BIT_XOR"

    operator = "BitXor"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryBitXorShape(
            self.subnode_right.getTypeShape()
        )


if python_version >= 350:

    class ExpressionOperationBinaryMatMult(
        ExpressionOperationMultMixin, ExpressionOperationBinaryBase
    ):
        kind = "EXPRESSION_OPERATION_BINARY_MAT_MULT"

        operator = "MatMult"
        simulator = PythonOperators.binary_operator_functions[operator]

        def _getOperationShape(self):
            return self.subnode_left.getTypeShape().getOperationBinaryMatMultShape(
                self.subnode_right.getTypeShape()
            )


_operator2binary_operation_nodeclass = {
    "Add": ExpressionOperationBinaryAdd,
    "Sub": ExpressionOperationBinarySub,
    "Mult": ExpressionOperationBinaryMult,
    "FloorDiv": ExpressionOperationBinaryFloorDiv,
    "TrueDiv": ExpressionOperationBinaryTrueDiv,
    "Mod": ExpressionOperationBinaryMod,
    # Divmod only from built-in call.
    "Pow": ExpressionOperationBinaryPow,
    "LShift": ExpressionOperationBinaryLshift,
    "RShift": ExpressionOperationBinaryRshift,
    "BitOr": ExpressionOperationBinaryBitOr,
    "BitAnd": ExpressionOperationBinaryBitAnd,
    "BitXor": ExpressionOperationBinaryBitXor,
}

if python_version < 300:
    _operator2binary_operation_nodeclass["OldDiv"] = ExpressionOperationBinaryOldDiv

if python_version >= 350:
    _operator2binary_operation_nodeclass["MatMult"] = ExpressionOperationBinaryMatMult


def makeBinaryOperationNode(operator, left, right, source_ref):
    node_class = _operator2binary_operation_nodeclass[operator]

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
        return tshape_bool

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


class ExpressionOperationBinaryInplaceBase(ExpressionOperationBinaryBase):
    # Base classes can be abstract, pylint: disable=abstract-method
    """ Base class for all inplace operations.

    """

    inplace_suspect = True

    def __init__(self, left, right, source_ref):
        ExpressionOperationBinaryBase.__init__(
            self, left=left, right=right, source_ref=source_ref
        )

    @staticmethod
    def isExpressionOperationInplace():
        return True


class ExpressionOperationInplaceAdd(
    ExpressionOperationAddMixin, ExpressionOperationBinaryInplaceBase
):
    kind = "EXPRESSION_OPERATION_INPLACE_ADD"

    operator = "IAdd"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationInplaceAddShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationInplaceSub(ExpressionOperationBinaryInplaceBase):
    kind = "EXPRESSION_OPERATION_INPLACE_SUB"

    operator = "ISub"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinarySubShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationInplaceMult(ExpressionOperationBinaryInplaceBase):
    kind = "EXPRESSION_OPERATION_INPLACE_MULT"

    operator = "IMult"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryMultShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationInplaceFloorDiv(ExpressionOperationBinaryInplaceBase):
    kind = "EXPRESSION_OPERATION_INPLACE_FLOOR_DIV"

    operator = "IFloorDiv"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryFloorDivShape(
            self.subnode_right.getTypeShape()
        )


if python_version < 300:

    class ExpressionOperationInplaceOldDiv(ExpressionOperationBinaryInplaceBase):
        kind = "EXPRESSION_OPERATION_INPLACE_OLD_DIV"

        operator = "IOldDiv"
        simulator = PythonOperators.binary_operator_functions[operator]

        def _getOperationShape(self):
            return self.subnode_left.getTypeShape().getOperationBinaryOldDivShape(
                self.subnode_right.getTypeShape()
            )


class ExpressionOperationInplaceTrueDiv(ExpressionOperationBinaryInplaceBase):
    kind = "EXPRESSION_OPERATION_INPLACE_TRUE_DIV"

    operator = "ITrueDiv"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryTrueDivShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationInplaceMod(ExpressionOperationBinaryInplaceBase):
    kind = "EXPRESSION_OPERATION_INPLACE_MOD"

    operator = "IMod"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryModShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationInplacePow(ExpressionOperationBinaryInplaceBase):
    kind = "EXPRESSION_OPERATION_INPLACE_POW"

    operator = "IPow"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryPowShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationInplaceLshift(ExpressionOperationBinaryInplaceBase):
    kind = "EXPRESSION_OPERATION_INPLACE_LSHIFT"

    operator = "ILShift"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryLShiftShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationInplaceRshift(ExpressionOperationBinaryInplaceBase):
    kind = "EXPRESSION_OPERATION_INPLACE_RSHIFT"

    operator = "IRShift"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryRShiftShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationInplaceBitOr(ExpressionOperationBinaryInplaceBase):
    kind = "EXPRESSION_OPERATION_INPLACE_BIT_OR"

    operator = "IBitOr"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryBitOrShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationInplaceBitAnd(ExpressionOperationBinaryInplaceBase):
    kind = "EXPRESSION_OPERATION_INPLACE_BIT_AND"

    operator = "IBitAnd"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryBitAndShape(
            self.subnode_right.getTypeShape()
        )


class ExpressionOperationInplaceBitXor(ExpressionOperationBinaryInplaceBase):
    kind = "EXPRESSION_OPERATION_INPLACE_BIT_XOR"

    operator = "IBitXor"
    simulator = PythonOperators.binary_operator_functions[operator]

    def _getOperationShape(self):
        return self.subnode_left.getTypeShape().getOperationBinaryBitXorShape(
            self.subnode_right.getTypeShape()
        )


if python_version >= 350:

    class ExpressionOperationInplaceMatMult(ExpressionOperationBinaryInplaceBase):
        kind = "EXPRESSION_OPERATION_INPLACE_MAT_MULT"

        operator = "IMatMult"
        simulator = PythonOperators.binary_operator_functions[operator]

        def _getOperationShape(self):
            return self.subnode_left.getTypeShape().getOperationBinaryMatMultShape(
                self.subnode_right.getTypeShape()
            )


_operator2binary_inplace_nodeclass = {
    "IAdd": ExpressionOperationInplaceAdd,
    "ISub": ExpressionOperationInplaceSub,
    "IMult": ExpressionOperationInplaceMult,
    "IFloorDiv": ExpressionOperationInplaceFloorDiv,
    "ITrueDiv": ExpressionOperationInplaceTrueDiv,
    "IMod": ExpressionOperationInplaceMod,
    "IPow": ExpressionOperationInplacePow,
    "ILShift": ExpressionOperationInplaceLshift,
    "IRShift": ExpressionOperationInplaceRshift,
    "IBitOr": ExpressionOperationInplaceBitOr,
    "IBitAnd": ExpressionOperationInplaceBitAnd,
    "IBitXor": ExpressionOperationInplaceBitXor,
}

if python_version < 300:
    _operator2binary_inplace_nodeclass["IOldDiv"] = ExpressionOperationInplaceOldDiv

if python_version >= 350:
    _operator2binary_inplace_nodeclass["IMatMult"] = ExpressionOperationInplaceMatMult


def makeExpressionOperationBinaryInplace(operator, left, right, source_ref):
    node_class = _operator2binary_inplace_nodeclass[operator]

    return node_class(left=left, right=right, source_ref=source_ref)
