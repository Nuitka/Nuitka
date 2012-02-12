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
""" Yield node.

The yield node returns to the caller of the generator and therefore may execute absolutely
abitrary code, from the point of view of this code. It then returns something, which may
often be 'None', but doesn't have to be.

Often it will be used as a statement, which should also be reflected in a dedicated node.
"""

from .NodeBases import CPythonExpressionChildrenHavingBase

class CPythonExpressionYield( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_YIELD"

    named_children = ( "expression", )

    def __init__( self, expression, for_return, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "expression" : expression
            },
            source_ref = source_ref
        )

        self.for_return = for_return

    def isForReturn( self ):
        return self.for_return

    getExpression = CPythonExpressionChildrenHavingBase.childGetter( "expression" )

    def computeNode( self ):
        # Nothing possible really here.

        return self, None, None
