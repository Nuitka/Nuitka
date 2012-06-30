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
""" Check if a function or class body needs a locals dict."""

# TODO: Merge with the finalization step that uses it.

from nuitka.transform import TreeOperations

class OverflowCheckVisitor( TreeOperations.VisitorNoopMixin ):
    def __init__( self, checked_node ):
        self.result = False

        self.is_class = checked_node.getParent().isExpressionClassBody()

        if checked_node.getParent().isExpressionFunctionBody():
            self.result = checked_node.getParent().isUnoptimized()

    def onEnterNode( self, node ):
        def declareOverflow():
            self.result = True

            raise TreeOperations.ExitVisit

        if node.needsLocalsDict():
            declareOverflow()

    def getResult( self ):
        return self.result


def check( node ):
    visitor = OverflowCheckVisitor( node )

    TreeOperations.visitScope( node, visitor )

    return visitor.getResult()
