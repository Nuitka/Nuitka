#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Extracting visitors.

This is used for lookahead supporting abstract execution. We need to e.g.
know the variables written by a piece of code ahead of abstractly executing a
loop.
"""

from .Operations import VisitorNoopMixin, visitTree


class VariableUsageUpdater(VisitorNoopMixin):
    __slots__ = (
        "old_locals_scope",
        "new_locals_scope",
        "variable_translations",
    )

    def __init__(self, old_locals_scope, new_locals_scope, variable_translations):
        self.old_locals_scope = old_locals_scope
        self.new_locals_scope = new_locals_scope
        self.variable_translations = variable_translations

    def onEnterNode(self, node):
        if hasattr(node, "variable"):
            if node.variable in self.variable_translations:
                node.setVariable(self.variable_translations[node.variable])

        if hasattr(node, "loop_variables") and node.loop_variables is not None:
            if any(
                variable in self.variable_translations
                for variable in node.loop_variables
            ):
                node.loop_variables = None

        if hasattr(node, "locals_scope"):
            if node.locals_scope is self.old_locals_scope:
                node.locals_scope = self.new_locals_scope

        if hasattr(node, "provider"):
            if node.provider is self.old_locals_scope.owner:
                node.provider = self.new_locals_scope.owner


def updateVariableUsage(
    provider, old_locals_scope, new_locals_scope, variable_translations
):
    visitor = VariableUsageUpdater(
        old_locals_scope=old_locals_scope,
        new_locals_scope=new_locals_scope,
        variable_translations=variable_translations,
    )

    visitTree(provider, visitor)


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
