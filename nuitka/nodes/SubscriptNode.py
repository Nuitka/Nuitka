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
""" Subscript node.

Subscripts are important when working with lists and dictionaries. Tracking them can allow
to achieve more compact code, or predict results at compile time.

This should be done via a subscript registry.
"""

from .NodeBases import CPythonExpressionChildrenHavingBase


class CPythonExpressionSubscriptLookup( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_SUBSCRIPT_LOOKUP"

    named_children = ( "expression", "subscript" )

    def __init__( self, expression, subscript, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "expression" : expression,
                "subscript"  : subscript
            },
            source_ref = source_ref
        )

    getLookupSource = CPythonExpressionChildrenHavingBase.childGetter( "expression" )
    getSubscript = CPythonExpressionChildrenHavingBase.childGetter( "subscript" )

    def computeNode( self, constraint_collection ):
        lookup_source = self.getLookupSource()

        return lookup_source.computeNodeSubscript(
            lookup_node           = self,
            subscript             = self.getSubscript(),
            constraint_collection = constraint_collection
        )

    def isKnownToBeIterable( self, count ):
        return None
