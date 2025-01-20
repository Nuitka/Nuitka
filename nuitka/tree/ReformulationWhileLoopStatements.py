#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Reformulation of while loop statements.

Loops in Nuitka have no condition attached anymore, so while loops are
re-formulated like this:

.. code-block:: python

    while condition:
        something()

.. code-block:: python

    while 1:
        if not condition:
            break

        something()

This is to totally remove the specialization of loops, with the condition moved
to the loop body in an initial conditional statement, which contains a ``break``
statement.

That achieves, that only ``break`` statements exit the loop, and allow for
optimization to remove always true loop conditions, without concerning code
generation about it, and to detect such a situation, consider e.g. endless
loops.

.. note::

   Loop analysis (not yet done) can then work on a reduced problem (which
   ``break`` statements are executed under what conditions) and is then
   automatically very general.

   The fact that the loop body may not be entered at all, is still optimized,
   but also in the general sense. Explicit breaks at the loop start and loop
   conditions are the same.

"""

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
    makeStatementsSequence,
    makeStatementsSequenceFromStatements,
    popBuildContext,
    pushBuildContext,
)


def buildWhileLoopNode(provider, node, source_ref):
    # The while loop is re-formulated according to Developer Manual. The
    # condition becomes an early condition to break the loop. The else block is
    # taken if a while loop exits normally, i.e. because of condition not being
    # true. We do this by introducing an indicator variable.

    else_block = buildStatementsNode(
        provider=provider,
        nodes=node.orelse if node.orelse else None,
        source_ref=source_ref,
    )

    if else_block is not None:
        temp_scope = provider.allocateTempScope("while_loop")

        # Indicator variable, will end up with C bool type, and need not be released.
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

    # The loop body contains a conditional statement at the start that breaks
    # the loop if it fails.
    loop_body = makeStatementsSequence(
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
        allow_none=True,
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
