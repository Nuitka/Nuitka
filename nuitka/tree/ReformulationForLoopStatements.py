#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Reformulation of for loop statements.

Consult the developer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

from nuitka.nodes.AssignNodes import (
    ExpressionTargetTempVariableRef,
    ExpressionTempVariableRef,
    StatementAssignmentVariable,
    StatementReleaseVariable
)
from nuitka.nodes.BuiltinIteratorNodes import (
    ExpressionAsyncIter,
    ExpressionAsyncNext,
    ExpressionBuiltinIter1,
    ExpressionBuiltinNext1
)
from nuitka.nodes.ComparisonNodes import ExpressionComparisonIs
from nuitka.nodes.ConditionalNodes import StatementConditional
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.LoopNodes import StatementLoop, StatementLoopBreak
from nuitka.nodes.StatementNodes import StatementsSequence

from .Helpers import (
    buildNode,
    buildStatementsNode,
    makeStatementsSequence,
    makeStatementsSequenceFromStatements,
    popBuildContext,
    pushBuildContext
)
from .ReformulationAssignmentStatements import buildAssignmentStatements
from .ReformulationTryExceptStatements import makeTryExceptSingleHandlerNode
from .ReformulationTryFinallyStatements import makeTryFinallyStatement


def _buildForLoopNode(provider, node, sync, source_ref):
    # The for loop is re-formulated according to developer manual. An iterator
    # is created, and looped until it gives StopIteration. The else block is
    # taken if a for loop exits normally, i.e. because of iterator
    # exhaustion. We do this by introducing an indicator variable.

    # We handle async and sync both here, leading to cases, pylint: disable=R0914

    source = buildNode(provider, node.iter, source_ref)

    # Temporary variables, we need one for the iterator, and one for the current
    # value.
    temp_scope = provider.allocateTempScope("for_loop")

    tmp_iter_variable = provider.allocateTempVariable(
        temp_scope = temp_scope,
        name       = "for_iterator"
    )
    tmp_value_variable = provider.allocateTempVariable(
        temp_scope = temp_scope,
        name       = "iter_value"
    )

    else_block = buildStatementsNode(
        provider   = provider,
        nodes      = node.orelse if node.orelse else None,
        source_ref = source_ref
    )

    if else_block is not None:
        tmp_break_indicator = provider.allocateTempVariable(
            temp_scope = temp_scope,
            name       = "break_indicator"
        )

        statements = [
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetTempVariableRef(
                    variable   = tmp_break_indicator,
                    source_ref = source_ref
                ),
                source       = ExpressionConstantRef(
                    constant   = True,
                    source_ref = source_ref
                ),
                source_ref   = source_ref
            )
        ]
    else:
        statements = []

    statements.append(
        StatementLoopBreak(
            source_ref = source_ref
        )
    )

    handler_body = makeStatementsSequence(
        statements = statements,
        allow_none = False,
        source_ref = source_ref
    )

    if sync:
        next_node = ExpressionBuiltinNext1(
            value      = ExpressionTempVariableRef(
                variable   = tmp_iter_variable,
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    else:
        next_node = ExpressionAsyncNext(
            value      = ExpressionTempVariableRef(
                variable   = tmp_iter_variable,
                source_ref = source_ref
            ),
            source_ref = source_ref
        )

    statements = (
        makeTryExceptSingleHandlerNode(
            tried          = StatementAssignmentVariable(
                variable_ref = ExpressionTargetTempVariableRef(
                    variable   = tmp_value_variable,
                    source_ref = source_ref
                ),
                source       = next_node,
                source_ref   = source_ref
            ),
            exception_name = "StopIteration" if sync else "StopAsyncIteration",
            handler_body   = handler_body,
            source_ref     = source_ref
        ),
        buildAssignmentStatements(
            provider   = provider,
            node       = node.target,
            source     = ExpressionTempVariableRef(
                variable   = tmp_value_variable,
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    pushBuildContext("loop_body")
    statements += (
        buildStatementsNode(
            provider   = provider,
            nodes      = node.body,
            source_ref = source_ref
        ),
    )
    popBuildContext()

    loop_body = makeStatementsSequence(
        statements = statements,
        allow_none = True,
        source_ref = source_ref
    )

    cleanup_statements = [
        StatementReleaseVariable(
            variable   = tmp_value_variable,
            source_ref = source_ref
        ),
        StatementReleaseVariable(
            variable   = tmp_iter_variable,
            source_ref = source_ref
        )
    ]

    if else_block is not None:
        statements = [
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetTempVariableRef(
                    variable   = tmp_break_indicator,
                    source_ref = source_ref
                ),
                source       = ExpressionConstantRef(
                    constant   = False,
                    source_ref = source_ref
                ),
                source_ref   = source_ref
            )
        ]
    else:
        statements = []

    if sync:
        iter_source = ExpressionBuiltinIter1(
            value      = source,
            source_ref = source.getSourceReference()
        )
    else:
        iter_source = ExpressionAsyncIter(
            value      = source,
            source_ref = source.getSourceReference()
        )

    statements += [
        # First create the iterator and store it.
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_iter_variable,
                source_ref = source_ref
            ),
            source       = iter_source,
            source_ref   = source_ref
        ),
        makeTryFinallyStatement(
            provider   = provider,
            tried      = StatementLoop(
                body       = loop_body,
                source_ref = source_ref
            ),
            final      = StatementsSequence(
                statements = cleanup_statements,
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    ]

    if else_block is not None:
        statements += [
            StatementConditional(
                condition  = ExpressionComparisonIs(
                    left       = ExpressionTempVariableRef(
                        variable   = tmp_break_indicator,
                        source_ref = source_ref
                    ),
                    right      = ExpressionConstantRef(
                        constant   = True,
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
                yes_branch = else_block,
                no_branch  = None,
                source_ref = source_ref
            )
        ]

        statements = (
            makeTryFinallyStatement(
                provider   = provider,
                tried      = statements,
                final      = StatementReleaseVariable(
                    variable   = tmp_break_indicator,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
        )

    return makeStatementsSequenceFromStatements(
        *statements
    )


def buildForLoopNode(provider, node, source_ref):
    return _buildForLoopNode(provider, node, True, source_ref)


def buildAsyncForLoopNode(provider, node, source_ref):
    return _buildForLoopNode(provider, node, False, source_ref)
