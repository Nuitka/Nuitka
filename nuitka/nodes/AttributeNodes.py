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


class CPythonExpressionBuiltinGetattr( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_BUILTIN_GETATTR"

    named_children = ( "source", "attribute", "default" )

    def __init__( self, object, name, default, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "source"    : object,
                "attribute" : name,
                "default"   : default
            },
            source_ref = source_ref
        )

    getLookupSource = CPythonExpressionChildrenHavingBase.childGetter( "source" )
    getAttribute = CPythonExpressionChildrenHavingBase.childGetter( "attribute" )
    getDefault = CPythonExpressionChildrenHavingBase.childGetter( "default" )

    def computeNode( self, constraint_collection ):
        # Note: Might be possible to predict or downgrade to mere attribute lookup.
        return self, None, None


class CPythonExpressionBuiltinSetattr( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_BUILTIN_SETATTR"

    named_children = ( "source", "attribute", "value" )

    def __init__( self, object, name, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "source"    : object,
                "attribute" : name,
                "value"     : value
            },
            source_ref = source_ref
        )

    getLookupSource = CPythonExpressionChildrenHavingBase.childGetter( "source" )
    getAttribute = CPythonExpressionChildrenHavingBase.childGetter( "attribute" )
    getValue = CPythonExpressionChildrenHavingBase.childGetter( "value" )

    def computeNode( self, constraint_collection ):
        # Note: Might be possible to predict or downgrade to mere attribute set.
        return self, None, None


class CPythonExpressionBuiltinHasattr( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_BUILTIN_HASATTR"

    named_children = ( "source", "attribute" )

    def __init__( self, object, name, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "source"    : object,
                "attribute" : name,
            },
            source_ref = source_ref
        )

    getLookupSource = CPythonExpressionChildrenHavingBase.childGetter( "source" )
    getAttribute = CPythonExpressionChildrenHavingBase.childGetter( "attribute" )

    def computeNode( self, constraint_collection ):
        # Note: Might be possible to predict or downgrade to mere attribute check.
        return self, None, None
