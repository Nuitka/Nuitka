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

    def __init__( self, variable, source, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "source" : source,
            },
            source_ref = source_ref
        )

        self.variable = variable

    def getDetail( self ):
        return "%s from %s" % ( self.getVariableName(), self.getAssignSource() )

    def getDetails( self ):
        return {
            "name" : self.getVariableName()
        }

    def getVariable( self ):
        return self.variable

    def getVariableName( self ):
        return self.variable.getName()

    getAssignSource = CPythonExpressionChildrenHavingBase.childGetter( "source" )

    def computeNode( self, constraint_collection ):
        if self.variable.getReferenced().isWriteOnly():
            return self.getAssignSource(), "new_expression", "Removed useless temporary keeper assignment."

        return self, None, None


class CPythonExpressionTempKeeperRef( CPythonNodeBase, CPythonExpressionMixin ):
    kind = "EXPRESSION_TEMP_KEEPER_REF"

    def __init__( self, variable, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        self.variable = variable

    def getDetails( self ):
        return {
            "name" : self.getVariableName()
        }

    def getDetail( self ):
        return self.getVariableName()

    def getVariable( self ):
        return self.variable

    def getVariableName( self ):
        return self.variable.getName()

    def computeNode( self, constraint_collection ):
        friend = constraint_collection.getVariableValueFriend( self.getVariable() )

        if friend is not None and not friend.mayHaveSideEffects( None ) and friend.isNode():
            assert hasattr( friend, "makeCloneAt" ), friend

            new_node = friend.makeCloneAt(
                source_ref = self.source_ref,
            )

            change_desc = "Assignment source of '%s' propagated, as it has no side effects." % self.getVariableName()

            return new_node, "new_expression", change_desc

        return self, None, None

    def mayRaiseException( self, exception_type ):
        # Can't happen
        return False

    def mayProvideReference( self ):
        return self.variable.getReferenced().getNeedsFree()
