#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .NodeBases import ExpressionChildrenHavingBase


class ExpressionOperationBase(ExpressionChildrenHavingBase):
    def __init__(self, operator, simulator, values, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = values,
            source_ref = source_ref
        )

        self.operator = operator

        self.simulator = simulator

    def getDetail(self):
        return self.operator

    def getDetails(self):
        return { "operator" : self.operator }

    def getOperator(self):
        return self.operator

    def getSimulator(self):
        return self.simulator

    def isKnownToBeIterable(self, count):
        # TODO: Could be true, if the arguments said so
        return None


class ExpressionOperationBinary(ExpressionOperationBase):
    kind = "EXPRESSION_OPERATION_BINARY"

    named_children = ( "left", "right" )

    def __init__(self, operator, left, right, source_ref):
        assert left.isExpression() and right.isExpression, ( left, right )

        ExpressionOperationBase.__init__(
            self,
            operator   = operator,
            simulator  = PythonOperators.binary_operator_functions[ operator ],
            values     = {
                "left"  : left,
                "right" : right
            },
            source_ref = source_ref
        )

        self.inplace_suspect = False

    def markAsInplaceSuspect(self):
        self.inplace_suspect = True

    def isInplaceSuspect(self):
        return self.inplace_suspect

    def computeExpression(self, constraint_collection):
        operator = self.getOperator()
        operands = self.getOperands()

        left, right = operands

        if left.willRaiseException( BaseException ):
            return (
                left,
                "new_raise",
                "Left argument of binary operation raises exception"
            )

        if right.willRaiseException( BaseException ):
            from .NodeMakingHelpers import wrapExpressionWithNodeSideEffects

            result = wrapExpressionWithNodeSideEffects(
                new_node = right,
                old_node = left
            )

            return (
                result,
                "new_raise",
                "Right argument of binary operation raises exception"
            )


        if left.isCompileTimeConstant() and right.isCompileTimeConstant():
            left_value = left.getCompileTimeConstant()
            right_value = right.getCompileTimeConstant()

            if operator == "Mult" and right.isNumberConstant():
                iter_length = left.getIterationLength()

                if iter_length is not None:
                    if iter_length * right_value > 256:
                        return self, None, None

                if left.isNumberConstant():
                    if left.isIndexConstant() and right.isIndexConstant():
                        # Estimate with logarithm, if the result of number
                        # calculations is computable with acceptable effort,
                        # otherwise, we will have to do it at runtime.

                        if left_value != 0 and right_value != 0:
                            if math.log10(abs(left_value)) + math.log10(abs(right_value)) > 20:
                                return self, None, None

            elif operator == "Mult" and left.isNumberConstant():
                iter_length = right.getIterationLength()

                if iter_length is not None:
                    if iter_length * left_value > 256:
                        return self, None, None
            elif operator == "Add" and \
                left.isKnownToBeIterable( None ) and \
                right.isKnownToBeIterable( None ):

                iter_length = left.getIterationLength() + \
                              right.getIterationLength()

                if iter_length > 256:
                    return self, None, None

            from .NodeMakingHelpers import getComputationResult

            return getComputationResult(
                node        = self,
                computation = lambda : self.getSimulator()(
                    left_value,
                    right_value
                ),
                description = "Operator '%s' with constant arguments." % operator
            )
        else:
            return self, None, None

    def getOperands(self):
        return ( self.getLeft(), self.getRight() )

    getLeft = ExpressionChildrenHavingBase.childGetter( "left" )
    getRight = ExpressionChildrenHavingBase.childGetter( "right" )


class ExpressionOperationUnary(ExpressionOperationBase):
    kind = "EXPRESSION_OPERATION_UNARY"

    named_children = ( "operand", )

    def __init__(self, operator, operand, source_ref):
        assert operand.isExpression(), operand

        ExpressionOperationBase.__init__(
            self,
            operator   = operator,
            simulator  = PythonOperators.unary_operator_functions[ operator ],
            values     = {
                "operand" : operand
            },
            source_ref = source_ref
        )

    def computeExpression(self, constraint_collection):
        operator = self.getOperator()
        operand = self.getOperand()

        if operand.isCompileTimeConstant():
            operand_value = operand.getCompileTimeConstant()

            from .NodeMakingHelpers import getComputationResult

            return getComputationResult(
                node        = self,
                computation = lambda : self.getSimulator()(
                    operand_value,
                ),
                description = "Operator '%s' with constant argument." % operator
            )
        else:
            return self, None, None

    getOperand = ExpressionChildrenHavingBase.childGetter( "operand" )

    def getOperands(self):
        return ( self.getOperand(), )

    def isExpressionOperationUnary(self):
        return True


class ExpressionOperationNOT(ExpressionOperationUnary):
    kind = "EXPRESSION_OPERATION_NOT"

    def __init__(self, operand, source_ref):
        ExpressionOperationUnary.__init__(
            self,
            operator   = "Not",
            operand    = operand,
            source_ref = source_ref
        )

    def computeExpression(self, constraint_collection):
        operand = self.getOperand()

        if operand.willRaiseException( BaseException ):
            return (
                operand,
                "new_raise",
                "Argument of 'not' operation raises exception"
            )

        return operand.computeExpressionOperationNot(
            not_node              = self,
            constraint_collection = constraint_collection
        )

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

    def mayProvideReference(self):
        # Dedicated code returns "True" or "False" only, which requires no
        # reference, except for rich comparisons, which do.
        return False


class ExpressionOperationBinaryInplace(ExpressionOperationBinary):
    kind = "EXPRESSION_OPERATION_BINARY_INPLACE"

    def __init__(self, operator, left, right, source_ref):
        operator = "I" + operator

        ExpressionOperationBinary.__init__(
            self,
            operator   = operator,
            left       = left,
            right      = right,
            source_ref = source_ref
        )

    def isExpressionOperationBinary(self):
        return True

    def computeExpression(self, constraint_collection):
        # TODO: Inplace operation requires extra care to avoid corruption of
        # values.
        return self, None, None
