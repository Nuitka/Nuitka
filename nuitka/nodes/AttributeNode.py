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
""" Attribute node

Knowing attributes of an object is very important, esp. when it comes to 'self' and
objects and classes. There will be a registry to aid predicting them.
"""

from .NodeBases import CPythonExpressionChildrenHavingBase

from nuitka.transform.optimizations.registry import AttributeRegistry


class CPythonExpressionAttributeLookup( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_ATTRIBUTE_LOOKUP"

    named_children = ( "expression", )

    def __init__( self, expression, attribute_name, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "expression" : expression
            },
            source_ref = source_ref
        )

        self.attribute_name = attribute_name

    def getAttributeName( self ):
        return self.attribute_name

    def getDetails( self ):
        return { "attribute" : self.getAttributeName() }

    def getDetail( self ):
        return "attribute %s from %s" % ( self.getAttributeName(), self.getLookupSource() )

    getLookupSource = CPythonExpressionChildrenHavingBase.childGetter( "expression" )

    def makeCloneAt( self, source_ref ):
        return CPythonExpressionAttributeLookup(
            expression     = self.getLookupSource().makeCloneAt( source_ref ),
            attribute_name = self.getAttributeName(),
            source_ref     = source_ref
        )


    def computeNode( self, constraint_collection ):
        # There is a whole registry dedicated to this.
        return AttributeRegistry.computeAttribute( self, constraint_collection )

    def isKnownToBeIterable( self, count ):
        # TODO: Should ask AttributeRegistry
        return None


class CPythonExpressionSpecialAttributeLookup( CPythonExpressionAttributeLookup ):
    kind = "EXPRESSION_SPECIAL_ATTRIBUTE_LOOKUP"

    # TODO: Special lookups should be treated somehow different.
    def computeNode( self, constraint_collection ):
        # There is a whole registry dedicated to this.
        return self, None, None
