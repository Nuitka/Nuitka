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
""" Slice nodes.

Slices are important when working with lists. Tracking them can allow to achieve more
compact code, or predict results at compile time.

This should be done via a slice registry.
"""

from .NodeBases import CPythonExpressionChildrenHavingBase

from .NodeMakingHelpers import convertNoneConstantToNone

from nuitka.transform.optimizations.registry import SliceRegistry


class CPythonExpressionSliceLookup( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_SLICE_LOOKUP"

    named_children = ( "expression", "lower", "upper" )

    def __init__( self, expression, lower, upper, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "expression" : expression,
                "upper"      : convertNoneConstantToNone( upper ),
                "lower"      : convertNoneConstantToNone( lower )
            },
            source_ref = source_ref
        )

    getLookupSource = CPythonExpressionChildrenHavingBase.childGetter( "expression" )

    def setChild( self, name, value ):
        if name in ( "lower", "upper" ):
            value = convertNoneConstantToNone( value )

        return CPythonExpressionChildrenHavingBase.setChild( self, name, value )


    getLower = CPythonExpressionChildrenHavingBase.childGetter( "lower" )
    setLower = CPythonExpressionChildrenHavingBase.childSetter( "lower" )

    getUpper = CPythonExpressionChildrenHavingBase.childGetter( "upper" )
    setUpper = CPythonExpressionChildrenHavingBase.childSetter( "upper" )

    def computeNode( self, constraint_collection ):
        # There is a whole registry dedicated to this.
        return SliceRegistry.computeSlice( self, constraint_collection )

    def isKnownToBeIterable( self, count ):
        # TODO: Should ask SlicetRegistry
        return None


class CPythonExpressionSliceObject( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_SLICE_OBJECT"

    named_children = ( "lower", "upper", "step" )

    def __init__( self, lower, upper, step, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "upper"      : upper,
                "lower"      : lower,
                "step"       : step
            },
            source_ref = source_ref
        )

    getLower = CPythonExpressionChildrenHavingBase.childGetter( "lower" )
    getUpper = CPythonExpressionChildrenHavingBase.childGetter( "upper" )
    getStep  = CPythonExpressionChildrenHavingBase.childGetter( "step" )

    def computeNode( self, constraint_collection ):
        # TODO: Not much to do, potentially simplify to slice instead?
        return self, None, None
