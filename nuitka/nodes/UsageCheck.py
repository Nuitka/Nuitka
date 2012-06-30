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
""" Check if a variable is used.

"""

from nuitka.transform import TreeOperations

class VariableSearch( TreeOperations.VisitorNoopMixin ):
    def __init__( self, search_for ):
        self.search_for = search_for
        self.found = []

    def onEnterNode( self, node ):
        if node.isExpressionVariableRef() or node.isExpressionTargetVariableRef():
            if node.getVariable() is self.search_for:
                self.found.append( node )

    def getResult( self ):
        return self.found


def getVariableUsages( node, variable ):
    visitor = VariableSearch( variable )

    TreeOperations.visitScope( node, visitor )

    return visitor.getResult()
