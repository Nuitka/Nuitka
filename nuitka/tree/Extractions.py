#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .Operations import VisitorNoopMixin, visitTree


class VariableWriteExtractor(VisitorNoopMixin):
    """ Extract variables written to.

    """
    def __init__(self):
        self.written_to = set()

    def onEnterNode(self, node):
        if node.isExpressionTargetVariableRef() or \
           node.isExpressionTargetTempVariableRef():
            key = node.getVariable(), node.getVariableVersion()

            self.written_to.add(key)

    def getResult(self):
        return self.written_to


def getVariablesWritten(node):
    visitor = VariableWriteExtractor()
    visitTree(node, visitor)

    return visitor.getResult()
