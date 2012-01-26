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
""" Nodes for comparisons.

"""

from .NodeBases import CPythonChildrenHaving, CPythonNodeBase

from nuitka import PythonOperators

from .NodeMakingHelpers import getComputationResult

class CPythonExpressionComparison( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_COMPARISON"

    named_children = ( "left", "right" )

    def __init__( self, left, right, comparator, source_ref ):
        assert left.isExpression()
        assert right.isExpression()
        assert type( comparator ) is str, comparator

        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "left" : left,
                "right" : right
            }
        )

        self.comparator = comparator

    def getOperands( self ):
        return (
            self.getLeft(),
            self.getRight()
        )

    getLeft = CPythonChildrenHaving.childGetter( "left" )
    getRight = CPythonChildrenHaving.childGetter( "right" )

    def getComparator( self ):
        return self.comparator

    def getDetails( self ):
        return { "comparator" : self.comparator }

    def getSimulator( self ):
        return PythonOperators.all_comparison_functions[ self.comparator ]

    def computeNode( self ):
        left, right = self.getOperands()

        if left.isConstant() and right.isConstant():
            return getComputationResult(
                node        = self,
                computation = self.getSimulator(),
                description = "Comparison"
            )

        return self, None, None
