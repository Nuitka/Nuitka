#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
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
""" Optimize operations on constant nodes.

"""

from .OptimizeBase import OptimizationVisitorBase, areConstants, makeRaiseExceptionReplacementExpressionFromInstance

from nuitka import PythonOperators, Nodes

class OptimizeOperationVisitor( OptimizationVisitorBase ):
    def _optimizeConstantOperandsOperation( self, node, operands ):
        operator = node.getOperator()

        if operator != "Repr":
            operands = [ constant.getConstant() for constant in operands ]

            if len( operands ) == 2:
                operator_function = PythonOperators.binary_operator_functions[ operator ]
            elif len( operands ) == 1:
                operator_function = PythonOperators.unary_operator_functions[ operator ]
            else:
                assert False, operands

            # Execute the operation and catch an exception. Turn either the result or the
            # exception generated into a node. pylint: disable=W0703
            try:
                # This is a convinent way to execute no matter what the number of
                # operands is. pylint: disable=W0142
                result = operator_function( *operands )
            except Exception as e:
                new_node = makeRaiseExceptionReplacementExpressionFromInstance(
                    expression = node,
                    exception  = e,
                )

                self.signalChange(
                    "new_code",
                    node.getSourceReference(),
                    "Operation with constant args was predicted to raise an exception."
                )
            else:
                new_node = Nodes.makeConstantReplacementNode(
                    constant = result,
                    node     = node,
                )

                self.signalChange(
                    "new_constant",
                    node.getSourceReference(),
                    "Operation with constant args was predicted to constant result."
                )

            node.replaceWith( new_node )


    def _optimizeConstantOperandsComparison( self, node, comparators, operands ):
        # TODO: Handle cases with multiple comparators too.
        if len( comparators ) != 1:
            return

        for count, comparator in enumerate( comparators ):
            operand1 = operands[ count ]
            operand2 = operands[ count + 1 ]

            if areConstants( ( operand1, operand2 ) ):
                value1 = operand1.getConstant()
                value2 = operand2.getConstant()

                if comparator in PythonOperators.rich_comparison_functions:
                    compare_function = PythonOperators.rich_comparison_functions[ comparator ]
                elif comparator == "Is":
                    compare_function = lambda value1, value2: value1 is value2
                elif comparator == "IsNot":
                    compare_function = lambda value1, value2: value1 is not value2
                elif comparator == "In":
                    compare_function = lambda value1, value2: value1 in value2
                elif comparator == "NotIn":
                    compare_function = lambda value1, value2: value1 not in value2
                else:
                    assert False, comparator

                # Execute the operation and catch an exception. Turn either the result or
                # the exception generated into a node. pylint: disable=W0703
                try:
                    new_value = compare_function( value1, value2 )
                except Exception as e:
                    new_node = makeRaiseExceptionReplacementExpressionFromInstance(
                        expression = node,
                        exception  = e,
                    )

                    self.signalChange(
                        "new_code",
                        node.getSourceReference(),
                        "Comparison with constant args was predicted to raise an exception."
                    )
                else:
                    new_node = Nodes.makeConstantReplacementNode(
                        constant = new_value,
                        node     = node
                    )

                    self.signalChange(
                        "new_constant",
                        node.getSourceReference(),
                        "Comparison with constant args was predicted to a constant value."
                    )

                node.replaceWith( new_node )


    def __call__( self, node ):
        if node.isOperation():
            operands = node.getOperands()

            if areConstants( operands ):
                self._optimizeConstantOperandsOperation(
                    node     = node,
                    operands = operands
                )
        elif node.isExpressionComparison():
            operands = node.getOperands()
            comparators = node.getComparators()

            self._optimizeConstantOperandsComparison(
                node        = node,
                comparators = comparators,
                operands    = operands
            )


        elif node.isStatementConditional():
            condition = node.getCondition()

            if condition.isConstantReference():
                if condition.getConstant():
                    choice = "true"

                    new_node = node.getBranchYes()
                else:
                    choice = "false"

                    new_node = node.getBranchNo()

                    if new_node is None:
                        new_node = Nodes.CPythonStatementPass(
                            source_ref = node.getSourceReference()
                        )

                node.replaceWith( new_node )

                self.signalChange(
                    "new_statements",
                    node.getSourceReference(),
                    "Condition for branch was predicted to be always %s." % choice
                )
