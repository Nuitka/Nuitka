#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Visitors that update variable, scope, and provider references in cloned trees."""

from contextlib import contextmanager

from .Operations import VisitorNoopMixin, visitTree

_clone_provider_translations = {}


@contextmanager
def withClonedProvider(old_provider, new_provider):
    """Map a cloned provider to its replacement while cloning its body."""

    has_previous = old_provider in _clone_provider_translations
    previous = _clone_provider_translations.get(old_provider)
    _clone_provider_translations[old_provider] = new_provider
    try:
        yield
    finally:
        if has_previous:
            _clone_provider_translations[old_provider] = previous
        else:
            del _clone_provider_translations[old_provider]


def getClonedProvider(provider):
    return _clone_provider_translations.get(provider, provider)


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
        if hasattr(node, "variable") and node.variable in self.variable_translations:
            new_variable = self.variable_translations[node.variable]

            if node.isStatementReleaseVariable():
                from nuitka.nodes.VariableReleaseNodes import (
                    makeStatementReleaseVariable,
                )

                new_node = makeStatementReleaseVariable(
                    variable=new_variable,
                    source_ref=node.getSourceReference(),
                )

                if new_node.__class__ is not node.__class__:
                    node.parent.replaceChild(node, new_node)
                    node.finalize()
                    return

            node.setVariable(new_variable)

        if (
            hasattr(node, "class_variable")
            and node.class_variable in self.variable_translations
        ):
            node.setClassVariable(self.variable_translations[node.class_variable])

        if (
            hasattr(node, "loop_variables")
            and node.loop_variables is not None
            and any(
                variable in self.variable_translations
                for variable in node.loop_variables
            )
        ):
            node.loop_variables = None

        if hasattr(node, "locals_scope") and node.locals_scope is self.old_locals_scope:
            node.locals_scope = self.new_locals_scope

        if hasattr(node, "provider") and node.provider is self.old_locals_scope.owner:
            node.provider = self.new_locals_scope.owner

        if (
            hasattr(node, "qualname_provider")
            and node.qualname_provider is self.old_locals_scope.owner
        ):
            node.qualname_provider = self.new_locals_scope.owner


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
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
