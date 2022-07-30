#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Extracting visitors.

This is used for look-aheads supporting abstract execution. We need to e.g.
know the variables written by a piece of code ahead of abstractly executing a
loop.
"""

from nuitka.containers.OrderedSets import OrderedSet

from .Operations import VisitorNoopMixin, visitTree


class VariableUsageExtractor(VisitorNoopMixin):
    """Extract variables used."""

    def __init__(self):
        self.written_to = OrderedSet()

    def onEnterNode(self, node):
        if (
            node.isStatementAssignmentVariable()
            or node.isStatementDelVariable()
            or node.isExpressionVariableRef()
        ):
            self.written_to.add(node.getVariable())

    def getResult(self):
        return self.written_to


def getVariablesWrittenOrRead(node):
    visitor = VariableUsageExtractor()
    visitTree(node, visitor)

    return visitor.getResult()


class VariableUsageUpdater(VisitorNoopMixin):
    def __init__(self, old_variable, new_variable):
        self.old_variable = old_variable
        self.new_variable = new_variable

    def onEnterNode(self, node):
        if (
            node.isStatementAssignmentVariable()
            or node.isStatementDelVariable()
            or node.isStatementReleaseVariable()
        ):
            if node.getVariable() is self.old_variable:
                node.setVariable(self.new_variable)


def updateVariableUsage(provider, old_variable, new_variable):
    visitor = VariableUsageUpdater(old_variable=old_variable, new_variable=new_variable)

    visitTree(provider, visitor)
