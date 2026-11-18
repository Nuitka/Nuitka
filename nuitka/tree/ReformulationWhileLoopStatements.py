#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Reformulation of while loop statements."""

from nuitka.nodes.ComparisonNodes import ExpressionComparisonIs
from nuitka.nodes.ConditionalNodes import makeStatementConditional
from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.LoopNodes import StatementLoop, StatementLoopBreak
from nuitka.nodes.OperatorNodesUnary import ExpressionOperationNot
from nuitka.nodes.StatementNodes import StatementsSequence
from nuitka.nodes.VariableAssignNodes import makeStatementAssignmentVariable
from nuitka.nodes.VariableRefNodes import ExpressionTempVariableRef

from .TreeHelpers import (
    buildNode,
    buildStatementsNode,
    makeStatementsSequenceFromStatements,
    makeStatementsSequenceWithNone,
    popBuildContext,
    pushBuildContext,
)


def buildWhileLoopNode(provider, node, source_ref):
    else_block = buildStatementsNode(
        provider=provider,
        nodes=node.orelse if node.orelse else None,  # spell-checker: ignore orelse
        source_ref=source_ref,
    )

    if else_block is not None:
        temp_scope = provider.allocateTempScope("while_loop")

        tmp_break_indicator = provider.allocateTempVariable(
            temp_scope=temp_scope, name="break_indicator", temp_type="bool"
        )

        statements = (
            makeStatementAssignmentVariable(
                variable=tmp_break_indicator,
                source=makeConstantRefNode(constant=True, source_ref=source_ref),
                source_ref=source_ref,
            ),
            StatementLoopBreak(source_ref=source_ref),
        )
    else:
        statements = (StatementLoopBreak(source_ref=source_ref),)

    pushBuildContext("loop_body")
    loop_statements = buildStatementsNode(
        provider=provider, nodes=node.body, source_ref=source_ref
    )
    popBuildContext()

    loop_body = makeStatementsSequenceWithNone(
        statements=(
            makeStatementConditional(
                condition=ExpressionOperationNot(
                    operand=buildNode(provider, node.test, source_ref),
                    source_ref=source_ref,
                ),
                yes_branch=StatementsSequence(
                    statements=statements, source_ref=source_ref
                ),
                no_branch=None,
                source_ref=source_ref,
            ),
            loop_statements,
        ),
        source_ref=source_ref,
    )

    loop_statement = StatementLoop(loop_body=loop_body, source_ref=source_ref)

    if else_block is None:
        return loop_statement
    else:
        return makeStatementsSequenceFromStatements(
            makeStatementAssignmentVariable(
                variable=tmp_break_indicator,
                source=makeConstantRefNode(constant=False, source_ref=source_ref),
                source_ref=source_ref,
            ),
            loop_statement,
            makeStatementConditional(
                condition=ExpressionComparisonIs(
                    left=ExpressionTempVariableRef(
                        variable=tmp_break_indicator, source_ref=source_ref
                    ),
                    right=makeConstantRefNode(constant=True, source_ref=source_ref),
                    source_ref=source_ref,
                ),
                yes_branch=else_block,
                no_branch=None,
                source_ref=source_ref,
            ),
        )


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
