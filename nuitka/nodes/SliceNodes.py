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
