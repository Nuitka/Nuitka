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
""" In-lining of functions.

Done by assigning the argument values to variables, and producing an outline
from the in-lined function.
"""

from nuitka.nodes.OutlineNodes import ExpressionOutlineBody
from nuitka.nodes.VariableAssignNodes import makeStatementAssignmentVariable
from nuitka.nodes.VariableReleaseNodes import makeStatementReleaseVariable
from nuitka.tree.Operations import VisitorNoopMixin, visitTree
from nuitka.tree.ReformulationTryFinallyStatements import (
    makeTryFinallyStatement,
)
from nuitka.tree.TreeHelpers import makeStatementsSequence


class VariableScopeUpdater(VisitorNoopMixin):
    def __init__(self, locals_scope, variable_translation):
        self.locals_scope = locals_scope
        self.variable_translation = variable_translation

    def onEnterNode(self, node):
        if hasattr(node, "variable"):
            if node.variable in self.variable_translation:
                node.variable = self.variable_translation[node.variable]

        if hasattr(node, "locals_scope"):
            node.locals_scope = self.locals_scope


def updateLocalsScope(provider, locals_scope, variable_translation):
    visitor = VariableScopeUpdater(
        locals_scope=locals_scope, variable_translation=variable_translation
    )

    visitTree(provider, visitor)


def convertFunctionCallToOutline(provider, function_body, values, call_source_ref):
    # This has got to have pretty man details, pylint: disable=too-many-locals
    function_source_ref = function_body.getSourceReference()

    outline_body = ExpressionOutlineBody(
        provider=provider, name="inline", source_ref=function_source_ref
    )

    # Make a clone first, so we do not harm other references.
    clone = function_body.subnode_body.makeClone()

    locals_scope_clone, variable_translation = function_body.locals_scope.makeClone(
        clone
    )

    # TODO: Lets update all at once maybe, it would take less visits.
    updateLocalsScope(
        clone,
        locals_scope=locals_scope_clone,
        variable_translation=variable_translation,
    )

    argument_names = function_body.getParameters().getParameterNames()
    assert len(argument_names) == len(values), (argument_names, values)

    statements = []

    for argument_name, value in zip(argument_names, values):
        statements.append(
            makeStatementAssignmentVariable(
                variable=variable_translation[argument_name],
                source=value,
                source_ref=call_source_ref,
            )
        )

    body = makeStatementsSequence(
        statements=(statements, clone), allow_none=False, source_ref=function_source_ref
    )

    auto_releases = function_body.getFunctionVariablesWithAutoReleases()

    # TODO: Not possible to auto release with outline bodies too?
    if auto_releases:
        releases = [
            makeStatementReleaseVariable(
                variable=variable, source_ref=function_source_ref
            )
            for variable in auto_releases
        ]

        body = makeTryFinallyStatement(
            provider=outline_body,
            tried=body,
            final=releases,
            source_ref=function_source_ref,
        )

    outline_body.setChildBody(body)

    return outline_body
