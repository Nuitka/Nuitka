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

# TODO: Change this node, so it becomes something easier to handle, i.e. has
# only two operands, expressing the chaining in a different way.

class CPythonExpressionComparison( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_COMPARISON"

    named_children = ( "operands", )

    def __init__( self, comparison, source_ref ):
        operands = []
        comparators = []

        for count, operand in enumerate( comparison ):
            if count % 2 == 0:
                assert operand.isExpression()

                operands.append( operand )
            else:
                comparators.append( operand )

        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "operands" : tuple( operands ),
            }
        )

        self.comparators = tuple( comparators )

    getOperands = CPythonChildrenHaving.childGetter( "operands" )

    def getComparators( self ):
        return self.comparators

    def getDetails( self ):
        return { "comparators" : self.comparators }

    def getSimulator( self, count ):
        return PythonOperators.all_comparison_functions[ self.comparators[ count ] ]

    def computeNode( self ):
        comparators = self.getComparators()
        operands = self.getOperands()

        assert False
