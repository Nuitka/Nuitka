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
""" Reformulation of while loop statements.

Consult the developer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

from nuitka.nodes.AssignNodes import (
    ExpressionTargetTempVariableRef,
    ExpressionTempVariableRef,
    StatementAssignmentVariable,
    StatementReleaseVariable
)
from nuitka.nodes.ComparisonNodes import ExpressionComparisonIs
from nuitka.nodes.ConditionalNodes import StatementConditional
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.LoopNodes import StatementLoop, StatementLoopBreak
from nuitka.nodes.OperatorNodes import ExpressionOperationNOT
from nuitka.nodes.StatementNodes import StatementsSequence

from .Helpers import (
    buildNode,
    buildStatementsNode,
    makeStatementsSequence,
    mergeStatements,
    popBuildContext,
    pushBuildContext
)
from .ReformulationTryFinallyStatements import makeTryFinallyStatement


def buildWhileLoopNode(provider, node, source_ref):
    # The while loop is re-formulated according to developer manual. The
    # condition becomes an early condition to break the loop. The else block is
    # taken if a while loop exits normally, i.e. because of condition not being
    # true. We do this by introducing an indicator variable.

    else_block = buildStatementsNode(
        provider   = provider,
        nodes      = node.orelse if node.orelse else None,
        source_ref = source_ref
    )

    if else_block is not None:
        temp_scope = provider.allocateTempScope("while_loop")

        tmp_break_indicator = provider.allocateTempVariable(
            temp_scope = temp_scope,
            name       = "break_indicator"
        )

        statements = (
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
            ),
            StatementLoopBreak(
                source_ref = source_ref
            )
        )
    else:
        statements = (
            StatementLoopBreak(
                source_ref = source_ref
            ),
        )

    pushBuildContext("loop_body")
    loop_statements = buildStatementsNode(
        provider   = provider,
        nodes      = node.body,
        source_ref = source_ref
    )
    popBuildContext()

    # The loop body contains a conditional statement at the start that breaks
    # the loop if it fails.
    loop_body = makeStatementsSequence(
        statements = (
            StatementConditional(
                condition  = ExpressionOperationNOT(
                    operand    = buildNode(provider, node.test, source_ref),
                    source_ref = source_ref,
                ),
                yes_branch = StatementsSequence(
                    statements = statements,
                    source_ref = source_ref
                ),
                no_branch  = None,
                source_ref = source_ref
            ),
            loop_statements
        ),
        allow_none = True,
        source_ref = source_ref
    )

    loop_statement = StatementLoop(
        body       = loop_body,
        source_ref = source_ref
    )

    if else_block is None:
        return loop_statement
    else:
        statements = (
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
            ),
            loop_statement,
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
        )

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

        return StatementsSequence(
            statements = mergeStatements(statements, False),
            source_ref = source_ref
        )
