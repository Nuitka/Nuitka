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
""" Node that models side effects.

Sometimes, the effect of an expression needs to be had, but the value itself does
not matter at all.
"""

from .NodeBases import CPythonExpressionChildrenHavingBase


class CPythonExpressionSideEffects( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_SIDE_EFFECTS"

    named_children = ( "side_effects", "expression" )

    def __init__( self, side_effects, expression, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values = {
                "side_effects" : tuple( side_effects ),
                "expression"   : expression
            },
            source_ref = source_ref
        )

    getSideEffects  = CPythonExpressionChildrenHavingBase.childGetter( "side_effects" )
    getExpression = CPythonExpressionChildrenHavingBase.childGetter( "expression" )

    setSideEffects  = CPythonExpressionChildrenHavingBase.childSetter( "side_effects" )

    def setChild( self, name, value ):
        if name == "side_effects":
            real_value = []

            for child in value:
                if child.isExpressionSideEffects():
                    real_value.extend( child.getSideEffects() )
                    real_value.append( child.getExpression() )
                else:
                    real_value.append( child )

            value = real_value

        return CPythonExpressionChildrenHavingBase.setChild( self, name, value )

    def computeNode( self, constraint_collection ):
        side_effects = self.getSideEffects()
        new_side_effects = []

        for side_effect in side_effects:
            if side_effect.mayHaveSideEffects( constraint_collection ):
                new_side_effects.append( side_effect )

        if new_side_effects != side_effects:
            self.setSideEffects( new_side_effects )

        if not new_side_effects:
            return self.getExpression(), "new_expression", "Removed empty side effects."

        return self, None, None
