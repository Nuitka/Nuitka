#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Nodes for comparisons.

"""

from .NodeBases import CPythonExpressionChildrenHavingBase

from nuitka import PythonOperators

from .NodeMakingHelpers import getComputationResult

class CPythonExpressionComparison( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_COMPARISON"

    named_children = ( "left", "right" )

    def __init__( self, left, right, comparator, source_ref ):
        assert left.isExpression()
        assert right.isExpression()
        assert type( comparator ) is str, comparator

        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values = {
                "left"  : left,
                "right" : right
            },
            source_ref = source_ref
        )

        self.comparator = comparator

    def getOperands( self ):
        return (
            self.getLeft(),
            self.getRight()
        )

    getLeft = CPythonExpressionChildrenHavingBase.childGetter( "left" )
    getRight = CPythonExpressionChildrenHavingBase.childGetter( "right" )

    def getComparator( self ):
        return self.comparator

    def getDetails( self ):
        return { "comparator" : self.comparator }

    def getSimulator( self ):
        return PythonOperators.all_comparison_functions[ self.comparator ]

    def computeNode( self, constraint_collection ):
        left, right = self.getOperands()

        if left.isCompileTimeConstant() and right.isCompileTimeConstant():
            left_value = left.getCompileTimeConstant()
            right_value = right.getCompileTimeConstant()

            return getComputationResult(
                node        = self,
                computation = lambda : self.getSimulator()(
                    left_value,
                    right_value
                ),
                description = "Comparison with constant arguments"
            )

        return self, None, None

    def computeNodeOperationNot( self, not_node, constraint_collection ):
        if self.comparator in PythonOperators.comparison_inversions:
            left, right = self.getOperands()

            result = CPythonExpressionComparison(
                left       = left,
                right      = right,
                comparator = PythonOperators.comparison_inversions[ self.comparator ],
                source_ref = self.source_ref
            )

            return result, "new_expression", "Replaced negated comparison with inverse comparision."

        return not_node, None, None

    def mayProvideReference( self ):
        # Dedicated code returns "True" or "False" only, which requires no reference,
        # except for rich comparisons, which do.
        return self.comparator in PythonOperators.rich_comparison_functions
