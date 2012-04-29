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
