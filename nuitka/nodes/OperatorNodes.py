#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit patches or make the software available to licensors of
#     this software in either form, you automatically them grant them a
#     license for your part of the code under "Apache License 2.0" unless you
#     choose to remove this notice.
#
#     Kay Hayen uses the right to license his code under only GPL version 3,
#     to discourage a fork of Nuitka before it is "finished". He will later
#     make a new "Nuitka" release fully under "Apache License 2.0".
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Nodes for unary and binary operations.

No short-circuit involved, boolean 'not' is an unary operation like '-' is, no real
difference.
"""

from .NodeBases import CPythonExpressionChildrenHavingBase

from .NodeMakingHelpers import getComputationResult

from nuitka import PythonOperators

class CPythonExpressionOperationBase( CPythonExpressionChildrenHavingBase ):
    named_children = ( "operands", )

    def __init__( self, operator, simulator, operands, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "operands" : operands
            },
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

    getOperands = CPythonExpressionChildrenHavingBase.childGetter( "operands" )

    def isKnownToBeIterable( self, count ):
        # TODO: Could be true, if the arguments said so
        return None


class CPythonExpressionOperationBinary( CPythonExpressionOperationBase ):
    kind = "EXPRESSION_OPERATION_BINARY"

    def __init__( self, operator, left, right, source_ref ):
        assert left.isExpression() and right.isExpression, ( left, right )

        CPythonExpressionOperationBase.__init__(
            self,
            operator   = operator,
            simulator  = PythonOperators.binary_operator_functions[ operator ],
            operands   = ( left, right ),
            source_ref = source_ref
        )

    def computeNode( self ):
        operator = self.getOperator()
        operands = self.getOperands()

        left, right = operands

        if left.isCompileTimeConstant() and right.isCompileTimeConstant():
            left_value = left.getCompileTimeConstant()
            right_value = right.getCompileTimeConstant()

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


class CPythonExpressionOperationUnary( CPythonExpressionOperationBase ):
    kind = "EXPRESSION_OPERATION_UNARY"

    def __init__( self, operator, operand, source_ref ):
        assert operand.isExpression(), operand

        CPythonExpressionOperationBase.__init__(
            self,
            operator   = operator,
            simulator  = PythonOperators.unary_operator_functions[ operator ],
            operands   = ( operand, ),
            source_ref = source_ref
        )

    def computeNode( self ):
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

    def getOperand( self ):
        operands = self.getOperands()

        assert len( operands ) == 1
        return operands[ 0 ]


class CPythonExpressionOperationNOT( CPythonExpressionOperationUnary ):
    kind = "EXPRESSION_OPERATION_NOT"

    def __init__( self, operand, source_ref ):
        CPythonExpressionOperationUnary.__init__(
            self,
            operator   = "Not",
            operand    = operand,
            source_ref = source_ref
        )

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

    def computeNode( self ):
        # TODO: Inplace operation requires extra care to avoid corruption of values.
        return self, None, None
