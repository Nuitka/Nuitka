#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Reformulation of for loop statements.

Consult the Developer Manual for information. TODO: Add ability to sync
source code comments with Developer Manual sections.

"""

from nuitka.nodes.BuiltinIteratorNodes import (
    ExpressionAsyncIter,
    ExpressionAsyncNext,
    ExpressionBuiltinIter1,
)
from nuitka.nodes.BuiltinNextNodes import ExpressionBuiltinNext1
from nuitka.nodes.BuiltinRangeNodes import makeExpressionBuiltinXrange
from nuitka.nodes.ComparisonNodes import ExpressionComparisonIs
from nuitka.nodes.ConditionalNodes import makeStatementConditional
from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.LoopNodes import StatementLoop, StatementLoopBreak
from nuitka.nodes.shapes.BuiltinTypeShapes import tshape_xrange
from nuitka.nodes.VariableAssignNodes import makeStatementAssignmentVariable
from nuitka.nodes.VariableRefNodes import ExpressionTempVariableRef
from nuitka.nodes.YieldNodes import ExpressionYieldFromAwaitable

from .ReformulationAssignmentStatements import buildAssignmentStatements
from .ReformulationTryExceptStatements import makeTryExceptSingleHandlerNode
from .ReformulationTryFinallyStatements import makeTryFinallyReleaseStatement
from .TreeHelpers import (
    buildNode,
    buildStatementsNode,
    getKind,
    makeStatementsSequence,
    makeStatementsSequenceFromStatements,
    makeStatementsSequenceWithNone,
    popBuildContext,
    pushBuildContext,
)


def _buildRangeLoopSource(provider, node, source_ref):
    if getattr(node.iter, "func", None) is None:
        return None

    if getattr(node.iter.func, "id", None) != "range":
        return None

    range_args = node.iter.args

    if len(range_args) == 1:
        return makeExpressionBuiltinXrange(
            low=buildNode(provider, range_args[0], source_ref),
            high=None,
            step=None,
            source_ref=source_ref,
        )

    if len(range_args) == 2:
        return makeExpressionBuiltinXrange(
            low=buildNode(provider, range_args[0], source_ref),
            high=buildNode(provider, range_args[1], source_ref),
            step=None,
            source_ref=source_ref,
        )

    if len(range_args) == 3:
        return makeExpressionBuiltinXrange(
            low=buildNode(provider, range_args[0], source_ref),
            high=buildNode(provider, range_args[1], source_ref),
            step=buildNode(provider, range_args[2], source_ref),
            source_ref=source_ref,
        )

    return None


def _makeForLoopNextExpression(tmp_iter_variable, sync, source_ref):
    tmp_iter_ref = ExpressionTempVariableRef(
        variable=tmp_iter_variable, source_ref=source_ref
    )

    if sync:
        return ExpressionBuiltinNext1(value=tmp_iter_ref, source_ref=source_ref)

    return ExpressionYieldFromAwaitable(
        expression=ExpressionAsyncNext(value=tmp_iter_ref, source_ref=source_ref),
        source_ref=source_ref,
    )


def _buildForLoopNode(provider, node, sync, source_ref):
    # The for loop is re-formulated according to Developer Manual. An iterator
    # is created, and looped until it gives StopIteration. The else block is
    # taken if a for loop exits normally, i.e. because of iterator
    # exhaustion. We do this by introducing an indicator variable.

    # We handle async and sync both here, leading to cases, pylint: disable=too-many-locals

    source = buildNode(provider, node.iter, source_ref)

    if sync:
        range_source = _buildRangeLoopSource(provider, node, source_ref)

        if range_source is not None:
            source = range_source

    # Temporary variables, we need one for the iterator, and one for the current
    # value.
    temp_scope = provider.allocateTempScope("for_loop")

    tmp_value_variable_type = "object"

    if sync and getKind(node.target) == "Name":
        source_shape = source.getTypeShape()

        if source_shape is tshape_xrange:
            tmp_value_variable_type = "nuitka_ilong"

    tmp_iter_variable = provider.allocateTempVariable(
        temp_scope=temp_scope, name="for_iterator", temp_type="object"
    )
    tmp_value_variable = provider.allocateTempVariable(
        temp_scope=temp_scope,
        name="iter_value",
        temp_type=tmp_value_variable_type,
    )

    # ast naming, spell-checker: ignore orelse
    else_block = buildStatementsNode(
        provider=provider,
        nodes=node.orelse if node.orelse else None,
        source_ref=source_ref,
    )

    if else_block is not None:
        # Indicator variable, will end up with C bool type, and need not be released.
        tmp_break_indicator = provider.allocateTempVariable(
            temp_scope=temp_scope, name="break_indicator", temp_type="bool"
        )

        statements = [
            makeStatementAssignmentVariable(
                variable=tmp_break_indicator,
                source=makeConstantRefNode(constant=True, source_ref=source_ref),
                source_ref=source_ref,
            )
        ]
    else:
        statements = []

    statements.append(StatementLoopBreak(source_ref=source_ref))

    handler_body = makeStatementsSequence(statements=statements, source_ref=source_ref)

    next_node = _makeForLoopNextExpression(
        tmp_iter_variable=tmp_iter_variable, sync=sync, source_ref=source_ref
    )

    statements = (
        makeTryExceptSingleHandlerNode(
            tried=makeStatementAssignmentVariable(
                variable=tmp_value_variable, source=next_node, source_ref=source_ref
            ),
            exception_name="StopIteration" if sync else "StopAsyncIteration",
            handler_body=handler_body,
            source_ref=source_ref,
        ),
        buildAssignmentStatements(
            provider=provider,
            node=node.target,
            source=ExpressionTempVariableRef(
                variable=tmp_value_variable, source_ref=source_ref
            ),
            source_ref=source_ref,
        ),
    )

    pushBuildContext("loop_body")
    statements += (
        buildStatementsNode(provider=provider, nodes=node.body, source_ref=source_ref),
    )
    popBuildContext()

    loop_body = makeStatementsSequenceWithNone(
        statements=statements, source_ref=source_ref
    )

    cleanup_variables = (
        tmp_value_variable,
        tmp_iter_variable,
    )

    if else_block is not None:
        statements = [
            makeStatementAssignmentVariable(
                variable=tmp_break_indicator,
                source=makeConstantRefNode(constant=False, source_ref=source_ref),
                source_ref=source_ref,
            )
        ]
    else:
        statements = []

    if sync:
        iter_source = ExpressionBuiltinIter1(
            value=source, source_ref=source.getSourceReference()
        )
    else:
        iter_source = ExpressionYieldFromAwaitable(
            expression=ExpressionAsyncIter(
                value=source, source_ref=source.getSourceReference()
            ),
            source_ref=source.getSourceReference(),
        )

    statements += (
        # First create the iterator and store it.
        makeStatementAssignmentVariable(
            variable=tmp_iter_variable, source=iter_source, source_ref=source_ref
        ),
        makeTryFinallyReleaseStatement(
            provider=provider,
            tried=StatementLoop(loop_body=loop_body, source_ref=source_ref),
            variables=cleanup_variables,
            source_ref=source_ref,
        ),
    )

    if else_block is not None:
        statements.append(
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
            )
        )

    return makeStatementsSequenceFromStatements(*statements)


def buildForLoopNode(provider, node, source_ref):
    return _buildForLoopNode(provider, node, True, source_ref)


def buildAsyncForLoopNode(provider, node, source_ref):
    return _buildForLoopNode(provider, node, False, source_ref)


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
