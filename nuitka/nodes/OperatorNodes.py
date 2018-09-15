#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka import PythonOperators

from .ExpressionBases import (
    ExpressionChildHavingBase,
    ExpressionChildrenHavingBase
)
from .shapes.BuiltinTypeShapes import ShapeTypeBool, ShapeTypeTuple
from .shapes.StandardShapes import (
    ShapeLargeConstantValuePredictable,
    ShapeUnknown,
    vshape_unknown
)


class ExpressionOperationBinaryBase(ExpressionChildrenHavingBase):

    named_children = ("left", "right")
    nice_children = tuple(child_name + " operand" for child_name in named_children)

    def __init__(self, operator, left, right, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "left"  : left,
                "right" : right
            },
            source_ref = source_ref
        )

        self.operator = operator

        self.simulator = PythonOperators.binary_operator_functions[ operator ]

    @staticmethod
    def isExpressionOperationBinary():
        return True

    def getDetail(self):
        return self.operator

    def getDetails(self):
        return {
            "operator" : self.operator
        }

    def getOperator(self):
        return self.operator

    def getSimulator(self):
        return self.simulator

    inplace_suspect = False

    def markAsInplaceSuspect(self):
        self.inplace_suspect = True

    def unmarkAsInplaceSuspect(self):
        self.inplace_suspect = False

    def isInplaceSuspect(self):
        return self.inplace_suspect

    def computeExpression(self, trace_collection):
        operator = self.getOperator()

        assert operator not in ("Mult", "Add")

        left = self.subnode_left
        right = self.subnode_right

        if left.isCompileTimeConstant() and right.isCompileTimeConstant():
            left_value = left.getCompileTimeConstant()
            right_value = right.getCompileTimeConstant()

            return trace_collection.getCompileTimeComputationResult(
                node        = self,
                computation = lambda : self.getSimulator()(
                    left_value,
                    right_value
                ),
                description = "Operator '%s' with constant arguments." % operator
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

    getLeft = ExpressionChildrenHavingBase.childGetter("left")
    getRight = ExpressionChildrenHavingBase.childGetter("right")


class ExpressionOperationBinary(ExpressionOperationBinaryBase):
    kind = "EXPRESSION_OPERATION_BINARY"

    def __init__(self, operator, left, right, source_ref):
        assert left.isExpression() and right.isExpression, (left, right)

        ExpressionOperationBinaryBase.__init__(
            self,
            operator   = operator,
            left       = left,
            right      = right,
            source_ref = source_ref
        )



class ExpressionOperationBinaryAdd(ExpressionOperationBinaryBase):
    kind = "EXPRESSION_OPERATION_BINARY_ADD"

    def __init__(self, left, right, source_ref):
        ExpressionOperationBinaryBase.__init__(
            self,
            operator   = "Add",
            left       = left,
            right      = right,
            source_ref = source_ref
        )

    def getDetails(self):
        return {}

    def computeExpression(self, trace_collection):
        # TODO: May go down to MemoryError for compile time constant overflow
        # ones.
        trace_collection.onExceptionRaiseExit(BaseException)

        operator = self.getOperator()

        left = self.subnode_left
        right = self.subnode_right

        if left.isCompileTimeConstant() and right.isCompileTimeConstant():
            left_value = left.getCompileTimeConstant()
            right_value = right.getCompileTimeConstant()

            if left.isKnownToBeIterable(None) and \
               right.isKnownToBeIterable(None):

                iter_length = left.getIterationLength() + \
                              right.getIterationLength()

                if iter_length > 256:
                    return self, None, None

            return trace_collection.getCompileTimeComputationResult(
                node        = self,
                computation = lambda : self.getSimulator()(
                    left_value,
                    right_value
                ),
                description = "Operator '%s' with constant arguments." % operator
            )

        # The value of these nodes escaped and could change its contents.
        trace_collection.removeKnowledge(left)
        trace_collection.removeKnowledge(right)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        return self, None, None


class ExpressionOperationBinaryMult(ExpressionOperationBinaryBase):
    kind = "EXPRESSION_OPERATION_BINARY_MULT"

    def __init__(self, left, right, source_ref):
        ExpressionOperationBinaryBase.__init__(
            self,
            operator   = "Mult",
            left       = left,
            right      = right,
            source_ref = source_ref
        )

        self.shape = None

    def getDetails(self):
        return {}

    def getValueShape(self):
        if self.shape is not None:
            return self.shape
        else:
            return vshape_unknown

    def getTypeShape(self):
        if self.shape is not None:
            return self.shape.getTypeShape()
        else:
            return ShapeUnknown

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

    def computeExpression(self, trace_collection):
        # TODO: May go down to MemoryError for compile time constant overflow
        # ones.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Nothing to do anymore for large constants.
        if self.shape is not None and self.shape.isConstant():
            return self, None, None

        left  = self.subnode_left
        right = self.subnode_right

        if left.isCompileTimeConstant() and right.isCompileTimeConstant():
            left_value = left.getCompileTimeConstant()
            right_value = right.getCompileTimeConstant()

            if right.isNumberConstant():
                iter_length = left.getIterationLength()

                if iter_length is not None:
                    size = iter_length * right_value
                    if size > 256:
                        self.shape = ShapeLargeConstantValuePredictable(
                            size      = size,
                            predictor = None, # predictValuesFromRightAndLeftValue,
                            shape     = left.getTypeShape()
                        )

                        return self, None, None

                if left.isNumberConstant():
                    if left.isIndexConstant() and right.isIndexConstant():
                        # Estimate with logarithm, if the result of number
                        # calculations is computable with acceptable effort,
                        # otherwise, we will have to do it at runtime.

                        if left_value != 0 and right_value != 0:
                            if math.log10(abs(left_value)) + math.log10(abs(right_value)) > 20:
                                return self, None, None

            elif left.isNumberConstant():
                iter_length = right.getIterationLength()

                if iter_length is not None:
                    size = iter_length * left_value
                    if iter_length * left_value > 256:
                        self.shape = ShapeLargeConstantValuePredictable(
                            size      = size,
                            predictor = None, # predictValuesFromRightAndLeftValue,
                            shape     = right.getTypeShape()
                        )

                        return self, None, None

            return trace_collection.getCompileTimeComputationResult(
                node        = self,
                computation = lambda : self.getSimulator()(
                    left_value,
                    right_value
                ),
                description = "Operator '*' with constant arguments."
            )

        # The value of these nodes escaped and could change its contents.
        trace_collection.removeKnowledge(left)
        trace_collection.removeKnowledge(right)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        return self, None, None

    def extractSideEffects(self):
        left_length = self.getLeft().getIterationLength()

        if left_length is not None:
            right_value = self.getRight().getIntegerValue()

            if right_value is not None:
                return self.getLeft().extractSideEffects() + self.getRight().extractSideEffects()

        right_length = self.getRight().getIterationLength()

        if right_length is not None:
            left_value = self.getLeft().getIntegerValue()

            if left_value is not None:
                return self.getLeft().extractSideEffects() + self.getRight().extractSideEffects()

        return ExpressionOperationBinaryBase.extractSideEffects(self)


class ExpressionOperationBinaryDivmod(ExpressionOperationBinaryBase):
    kind = "EXPRESSION_OPERATION_BINARY_DIVMOD"

    def __init__(self, left, right, source_ref):
        ExpressionOperationBinaryBase.__init__(
            self,
            operator   = "Divmod",
            left       = left,
            right      = right,
            source_ref = source_ref
        )

        self.shape = None


    # TODO: Value shape is two elemented tuple of int or float both.
    def getTypeShape(self):
        return ShapeTypeTuple


def makeBinaryOperationNode(operator, left, right, source_ref):
    if operator == "Add":
        return ExpressionOperationBinaryAdd(
            left       = left,
            right      = right,
            source_ref = source_ref
        )
    elif operator == "Mult":
        return ExpressionOperationBinaryMult(
            left       = left,
            right      = right,
            source_ref = source_ref
        )
    else:
        # TODO: Add more specializations for common operators.

        return ExpressionOperationBinary(
            operator   = operator,
            left       = left,
            right      = right,
            source_ref = source_ref
        )


class ExpressionOperationUnaryBase(ExpressionChildHavingBase):
    named_child = "operand"

    __slots__ = (
        "operator",
        "simulator"
    )

    def __init__(self, operator, operand, source_ref):
        ExpressionChildHavingBase.__init__(
            self,
            value      = operand,
            source_ref = source_ref
        )

        self.operator = operator

        self.simulator = PythonOperators.unary_operator_functions[ operator ]

    def getDetail(self):
        return self.operator

    def getDetails(self):
        return {
            "operator" : self.operator
        }

    def getOperator(self):
        return self.operator

    def getSimulator(self):
        return self.simulator

    def computeExpression(self, trace_collection):
        operator = self.getOperator()
        operand = self.subnode_operand

        if operand.isCompileTimeConstant():
            operand_value = operand.getCompileTimeConstant()

            return trace_collection.getCompileTimeComputationResult(
                node        = self,
                computation = lambda : self.getSimulator()(
                    operand_value,
                ),
                description = "Operator '%s' with constant argument." % operator
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

    getOperand = ExpressionChildHavingBase.childGetter("operand")

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
            self,
            operator   = operator,
            operand    = operand,
            source_ref = source_ref
        )


class ExpressionOperationNOT(ExpressionOperationUnaryBase):
    kind = "EXPRESSION_OPERATION_NOT"

    def __init__(self, operand, source_ref):
        ExpressionOperationUnaryBase.__init__(
            self,
            operator   = "Not",
            operand    = operand,
            source_ref = source_ref
        )

    def getTypeShape(self):
        return ShapeTypeBool

    def getDetails(self):
        return {}

    def computeExpression(self, trace_collection):
        return self.getOperand().computeExpressionOperationNot(
            not_node         = self,
            trace_collection = trace_collection
        )

    def mayRaiseException(self, exception_type):
        return self.getOperand().mayRaiseException(exception_type) or \
               self.getOperand().mayRaiseExceptionBool(exception_type)

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


class ExpressionOperationBinaryInplace(ExpressionOperationBinary):
    kind = "EXPRESSION_OPERATION_BINARY_INPLACE"

    def __init__(self, operator, left, right, source_ref):
        ExpressionOperationBinary.__init__(
            self,
            operator   = operator,
            left       = left,
            right      = right,
            source_ref = source_ref
        )

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
                operator   = self.getOperator()[1:],
                left       = left,
                right      = right,
                source_ref = source_ref
            )

            trace_collection.signalChange(
                tags       = "new_expression",
                source_ref = source_ref,
                message    = """\
Lowered in-place binary operation of compile time constant to binary operation."""
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
        operator   = operator,
        left       = left,
        right      = right,
        source_ref = source_ref
    )
