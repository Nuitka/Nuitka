#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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

No short-circuit involved, boolean 'not' is an unary operation like '-' is, no real
difference.
"""

from .NodeBases import CPythonExpressionChildrenHavingBase

from .NodeMakingHelpers import getComputationResult

from nuitka import PythonOperators

import math

class CPythonExpressionOperationBase( CPythonExpressionChildrenHavingBase ):
    def __init__( self, operator, simulator, values, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = values,
            source_ref = source_ref
        )

        self.operator = operator

        self.simulator = simulator

    def getOperator( self ):
        return self.operator

    def getDetail( self ):
        return self.operator

    def getDetails( self ):
        return { "operator" : self.operator }

    def getSimulator( self ):
        return self.simulator

    def isKnownToBeIterable( self, count ):
        # TODO: Could be true, if the arguments said so
        return None


class CPythonExpressionOperationBinary( CPythonExpressionOperationBase ):
    kind = "EXPRESSION_OPERATION_BINARY"

    named_children = ( "left", "right" )

    def __init__( self, operator, left, right, source_ref ):
        assert left.isExpression() and right.isExpression, ( left, right )

        CPythonExpressionOperationBase.__init__(
            self,
            operator   = operator,
            simulator  = PythonOperators.binary_operator_functions[ operator ],
            values     = {
                "left"  : left,
                "right" : right
            },
            source_ref = source_ref
        )

    def computeNode( self, constraint_collection ):
        operator = self.getOperator()
        operands = self.getOperands()

        left, right = operands

        if left.isCompileTimeConstant() and right.isCompileTimeConstant():
            left_value = left.getCompileTimeConstant()
            right_value = right.getCompileTimeConstant()

            if operator == "Mult" and right.isNumberConstant():
                iter_length = left.getIterationLength( constraint_collection )

                if iter_length is not None:
                    if iter_length * right_value > 256:
                        return self, None, None

                if left.isNumberConstant():
                    if left.isIndexConstant() and right.isIndexConstant():
                        # Estimate with logarithm, if the result of number calculations is
                        # computable with acceptable effort, otherwise, we will have to do
                        # it at runtime.

                        if left_value != 0 and right_value != 0:
                            if math.log10( abs( left_value ) ) + math.log10( abs( right_value ) ) > 20:
                                return self, None, None

            return getComputationResult(
                node        = self,
                computation = lambda : self.getSimulator()(
                    left_value,
                    right_value
                ),
                description = "Operator '%s' with constant arguments" % operator
            )
        else:
            return self, None, None

    def getOperands( self ):
        return ( self.getLeft(), self.getRight() )

    getLeft = CPythonExpressionChildrenHavingBase.childGetter( "left" )
    getRight = CPythonExpressionChildrenHavingBase.childGetter( "right" )


class CPythonExpressionOperationUnary( CPythonExpressionOperationBase ):
    kind = "EXPRESSION_OPERATION_UNARY"

    named_children = ( "operand", )

    def __init__( self, operator, operand, source_ref ):
        assert operand.isExpression(), operand

        CPythonExpressionOperationBase.__init__(
            self,
            operator   = operator,
            simulator  = PythonOperators.unary_operator_functions[ operator ],
            values     = {
                "operand" : operand
            },
            source_ref = source_ref
        )

    def computeNode( self, constraint_collection ):
        operator = self.getOperator()
        operand = self.getOperand()

        if operand.isCompileTimeConstant():
            operand_value = operand.getCompileTimeConstant()
            return getComputationResult(
                node        = self,
                computation = lambda : self.getSimulator()(
                    operand_value,
                ),
                description = "Operator '%s' with constant argument" % operator
            )
        else:
            return self, None, None

    getOperand = CPythonExpressionChildrenHavingBase.childGetter( "operand" )

    def getOperands( self ):
        return ( self.getOperand(), )


class CPythonExpressionOperationNOT( CPythonExpressionOperationUnary ):
    kind = "EXPRESSION_OPERATION_NOT"

    def __init__( self, operand, source_ref ):
        CPythonExpressionOperationUnary.__init__(
            self,
            operator   = "Not",
            operand    = operand,
            source_ref = source_ref
        )

    def getTruthValue( self, constraint_collection ):
        result = self.getOperand().getTruthValue( constraint_collection )

        return None if result is None else not result

    def mayHaveSideEffects( self, constraint_collection ):
        operand = self.getOperand()

        if operand.mayHaveSideEffects( constraint_collection ):
            return True

        # TODO: Find the common ground of these, and make it an expression method.
        if operand.isExpressionMakeSequence():
            return False

        if operand.isExpressionMakeDict():
            return False

        return True

    def extractSideEffects( self ):
        operand = self.getOperand()

        # TODO: Find the common ground of these, and make it an expression method.
        if operand.isExpressionMakeSequence():
            return self.getOperand().extractSideEffects()

        if operand.isExpressionMakeDict():
            return self.getOperand().extractSideEffects()

        return ( self, )


class CPythonExpressionOperationBinaryInplace( CPythonExpressionOperationBinary ):
    kind = "EXPRESSION_OPERATION_BINARY_INPLACE"

    def __init__( self, operator, left, right, source_ref ):
        operator = "I" + operator

        CPythonExpressionOperationBinary.__init__(
            self,
            operator   = operator,
            left       = left,
            right      = right,
            source_ref = source_ref
        )

    def computeNode( self, constraint_collection ):
        # TODO: Inplace operation requires extra care to avoid corruption of values.
        return self, None, None
