#     Copyright 2012, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Keeper nodes.

We need keeper nodes for comparison chains to hold the previous value during the
evaluation of an expression. They are otherwise not used and should be avoided,
all other constructs use real temporary variables.

"""

from .NodeBases import (
    CPythonExpressionChildrenHavingBase,
    CPythonExpressionMixin,
    CPythonNodeBase
)


class CPythonExpressionAssignmentTempKeeper( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_ASSIGNMENT_TEMP_KEEPER"

    named_children = ( "source", )

    def __init__( self, variable_name, source, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "source" : source,
            },
            source_ref = source_ref
        )

        self.variable_name = variable_name

    def getDetail( self ):
        return "%s from %s" % ( self.getVariableName(), self.getAssignSource() )

    def getVariableName( self ):
        return self.variable_name

    getAssignSource = CPythonExpressionChildrenHavingBase.childGetter( "source" )

    def computeNode( self, constraint_collection ):
        # TODO: Nothing to do here? Maybe if the assignment target is unused, it could
        # replace itself with source.

        # TODO: A real variable should be the link, then we could tell if it's used at
        # all.
        return self, None, None


class CPythonExpressionTempKeeperRef( CPythonNodeBase, CPythonExpressionMixin ):
    kind = "EXPRESSION_TEMP_KEEPER_REF"

    def __init__( self, linked, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        # TODO: A real variable should be the link.
        self.linked = linked

    def getDetails( self ):
        return {
            "name" : self.getVariableName()
        }

    def getDetail( self ):
        return self.getVariableName()

    def getVariableName( self ):
        return self.linked.getVariableName()

    def computeNode( self, constraint_collection ):
        # Nothing to do here.
        return self, None, None

    def mayRaiseException( self, exception_type ):
        # Can't happen
        return False
