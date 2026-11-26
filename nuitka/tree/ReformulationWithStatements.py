#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Reformulation of with statements."""

from nuitka.nodes.AttributeLookupNodes import ExpressionAttributeLookupSpecial
from nuitka.nodes.AttributeNodes import makeExpressionAttributeLookup
from nuitka.nodes.CallNodes import (
    ExpressionCallEmpty,
    ExpressionCallNoKeywords,
)
from nuitka.nodes.ComparisonNodes import ExpressionComparisonIs
from nuitka.nodes.ConditionalNodes import makeStatementConditional
from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.ContainerMakingNodes import makeExpressionMakeTuple
from nuitka.nodes.CoroutineNodes import (
    ExpressionAsyncWaitEnter,
    ExpressionAsyncWaitExit,
)
from nuitka.nodes.ExceptionNodes import (
    ExpressionCaughtExceptionTracebackRef,
    ExpressionCaughtExceptionTypeRef,
    ExpressionCaughtExceptionValueRef,
)
from nuitka.nodes.StatementNodes import (
    StatementExpressionOnly,
    StatementsSequence,
)
from nuitka.nodes.VariableAssignNodes import makeStatementAssignmentVariable
from nuitka.nodes.VariableRefNodes import ExpressionTempVariableRef
from nuitka.nodes.YieldNodes import ExpressionYieldFromAwaitable
from nuitka.PythonVersions import python_version
from nuitka.States import states

from .ReformulationAssignmentStatements import buildAssignmentStatements
from .ReformulationTryExceptStatements import (
    makeTryExceptSingleHandlerNodeWithPublish,
)
from .ReformulationTryFinallyStatements import (
    makeTryFinallyReleaseStatement,
    makeTryFinallyStatement,
)
from .TreeHelpers import (
    buildNode,
    buildStatementsNode,
    makeReraiseExceptionStatement,
    makeStatementsSequenceWithNone,
)


def _buildWithNode(provider, context_expr, assign_target, body, sync, source_ref):
    # pylint: disable=too-many-branches,too-many-locals
    with_source = buildNode(provider, context_expr, source_ref)

    if python_version < 0x380 and states.is_full_compat:
        source_ref = with_source.getCompatibleSourceReference()

    temp_scope = provider.allocateTempScope("with")

    tmp_source_variable = provider.allocateTempVariable(
        temp_scope=temp_scope, name="source", temp_type="object"
    )
    tmp_exit_variable = provider.allocateTempVariable(
        temp_scope=temp_scope, name="exit", temp_type="object"
    )
    tmp_enter_variable = provider.allocateTempVariable(
        temp_scope=temp_scope, name="enter", temp_type="object"
    )

    tmp_indicator_variable = provider.allocateTempVariable(
        temp_scope=temp_scope, name="indicator", temp_type="bool"
    )

    statements = (
        buildAssignmentStatements(
            provider=provider,
            node=assign_target,
            allow_none=True,
            source=ExpressionTempVariableRef(
                variable=tmp_enter_variable, source_ref=source_ref
            ),
            source_ref=source_ref,
        ),
        body,
    )

    with_body = makeStatementsSequenceWithNone(
        statements=statements, source_ref=source_ref
    )

    if body and python_version < 0x3A0:
        deepest = body

        while deepest.getVisitableNodes():
            deepest = deepest.getVisitableNodes()[-1]

        if python_version < 0x370:
            body_lineno = deepest.getCompatibleSourceReference().getLineNumber()
        else:
            body_lineno = deepest.getSourceReference().getLineNumber()

        with_exit_source_ref = source_ref.atLineNumber(body_lineno)
    else:
        with_exit_source_ref = source_ref

    # The "__enter__" and "__exit__" were normal attribute lookups under
    # CPython2.6, but that changed with CPython2.7.
    if python_version < 0x270:
        attribute_lookup_maker = makeExpressionAttributeLookup
    else:
        attribute_lookup_maker = ExpressionAttributeLookupSpecial

    enter_lookup_assignment = makeStatementAssignmentVariable(
        variable=tmp_enter_variable,
        source=attribute_lookup_maker(
            expression=ExpressionTempVariableRef(
                variable=tmp_source_variable, source_ref=source_ref
            ),
            attribute_name="__enter__" if sync else "__aenter__",
            source_ref=source_ref,
        ),
        source_ref=source_ref,
    )

    exit_value_exception = ExpressionCallNoKeywords(
        called=ExpressionTempVariableRef(
            variable=tmp_exit_variable, source_ref=with_exit_source_ref
        ),
        args=makeExpressionMakeTuple(
            elements=(
                ExpressionCaughtExceptionTypeRef(source_ref=with_exit_source_ref),
                ExpressionCaughtExceptionValueRef(source_ref=with_exit_source_ref),
                ExpressionCaughtExceptionTracebackRef(source_ref=source_ref),
            ),
            source_ref=source_ref,
        ),
        source_ref=with_exit_source_ref,
    )

    exit_value_no_exception = ExpressionCallNoKeywords(
        called=ExpressionTempVariableRef(
            variable=tmp_exit_variable, source_ref=source_ref
        ),
        args=makeConstantRefNode(constant=(None, None, None), source_ref=source_ref),
        source_ref=with_exit_source_ref,
    )

    if not sync:
        exit_value_exception = ExpressionYieldFromAwaitable(
            expression=ExpressionAsyncWaitExit(
                expression=exit_value_exception, source_ref=source_ref
            ),
            source_ref=source_ref,
        )
        exit_value_no_exception = ExpressionYieldFromAwaitable(
            ExpressionAsyncWaitExit(
                expression=exit_value_no_exception, source_ref=source_ref
            ),
            source_ref=source_ref,
        )

    statements = [
        makeStatementAssignmentVariable(
            variable=tmp_source_variable, source=with_source, source_ref=source_ref
        )
    ]

    enter_call_value = ExpressionCallEmpty(
        called=ExpressionTempVariableRef(
            variable=tmp_enter_variable, source_ref=source_ref
        ),
        source_ref=source_ref,
    )

    # Before 3.9, "__aenter__" is immediately awaited, with "__aexit__" looked up
    # first.
    if not sync and python_version < 0x390:
        enter_call_value = ExpressionYieldFromAwaitable(
            expression=ExpressionAsyncWaitEnter(
                expression=enter_call_value, source_ref=source_ref
            ),
            source_ref=source_ref,
        )

    enter_call_assignment = makeStatementAssignmentVariable(
        variable=tmp_enter_variable, source=enter_call_value, source_ref=source_ref
    )

    exit_lookup_assignment = makeStatementAssignmentVariable(
        variable=tmp_exit_variable,
        source=attribute_lookup_maker(
            expression=ExpressionTempVariableRef(
                variable=tmp_source_variable, source_ref=source_ref
            ),
            attribute_name="__exit__" if sync else "__aexit__",
            source_ref=source_ref,
        ),
        source_ref=source_ref,
    )

    # CPython looks up both special methods before calling "__enter__", but the
    # order of the lookups changed over versions: 3.6 for "with", 3.9 for
    # "async with", and 3.14 both returned to "__exit__" first.
    if (sync and 0x360 <= python_version < 0x3E0) or (
        not sync and 0x390 <= python_version < 0x3E0
    ):
        attribute_assignments = (enter_lookup_assignment, exit_lookup_assignment)
    else:
        attribute_assignments = (exit_lookup_assignment, enter_lookup_assignment)

    # Since 3.9, "__aenter__" is not awaited until "__aexit__" was looked up.
    if not sync and python_version >= 0x390:
        enter_await_statement = makeStatementAssignmentVariable(
            variable=tmp_enter_variable,
            source=ExpressionYieldFromAwaitable(
                expression=ExpressionAsyncWaitEnter(
                    expression=ExpressionTempVariableRef(
                        variable=tmp_enter_variable, source_ref=source_ref
                    ),
                    source_ref=source_ref,
                ),
                source_ref=source_ref,
            ),
            source_ref=source_ref,
        )

        statements.extend(
            attribute_assignments + (enter_call_assignment, enter_await_statement)
        )
    else:
        statements.extend(attribute_assignments + (enter_call_assignment,))

    statements.append(
        makeStatementAssignmentVariable(
            variable=tmp_indicator_variable,
            source=makeConstantRefNode(constant=True, source_ref=source_ref),
            source_ref=source_ref,
        )
    )

    statements += (
        makeTryFinallyStatement(
            provider=provider,
            tried=makeTryExceptSingleHandlerNodeWithPublish(
                provider=provider,
                tried=with_body,
                exception_name="BaseException",
                handler_body=StatementsSequence(
                    statements=(
                        makeStatementAssignmentVariable(
                            variable=tmp_indicator_variable,
                            source=makeConstantRefNode(
                                constant=False, source_ref=source_ref
                            ),
                            source_ref=source_ref,
                        ),
                        makeStatementConditional(
                            condition=exit_value_exception,
                            no_branch=makeReraiseExceptionStatement(
                                source_ref=with_exit_source_ref
                            ),
                            yes_branch=None,
                            source_ref=with_exit_source_ref,
                        ),
                    ),
                    source_ref=source_ref,
                ),
                public_exc=python_version >= 0x270,
                source_ref=source_ref,
            ),
            final=makeStatementConditional(
                condition=ExpressionComparisonIs(
                    left=ExpressionTempVariableRef(
                        variable=tmp_indicator_variable, source_ref=source_ref
                    ),
                    right=makeConstantRefNode(constant=True, source_ref=source_ref),
                    source_ref=source_ref,
                ),
                yes_branch=StatementExpressionOnly(
                    expression=exit_value_no_exception, source_ref=source_ref
                ),
                no_branch=None,
                source_ref=source_ref,
            ),
            source_ref=source_ref,
        ),
    )

    return makeTryFinallyReleaseStatement(
        provider=provider,
        tried=statements,
        variables=(
            tmp_source_variable,
            tmp_enter_variable,
            tmp_exit_variable,
        ),
        source_ref=source_ref,
    )


def buildWithNode(provider, node, source_ref):
    # Python 3.3+ stores multiple context managers in "node.items", while
    # earlier versions desugar them into nested "With" AST nodes.
    if hasattr(node, "items"):
        context_exprs = [item.context_expr for item in node.items]
        assign_targets = [item.optional_vars for item in node.items]
    else:
        context_exprs = [node.context_expr]
        assign_targets = [node.optional_vars]

    body = buildStatementsNode(provider, node.body, source_ref)

    assert context_exprs and len(context_exprs) == len(assign_targets)

    context_exprs.reverse()
    assign_targets.reverse()

    for context_expr, assign_target in zip(context_exprs, assign_targets):
        body = _buildWithNode(
            provider=provider,
            body=body,
            context_expr=context_expr,
            assign_target=assign_target,
            sync=True,
            source_ref=source_ref,
        )

    return body


def buildAsyncWithNode(provider, node, source_ref):
    context_exprs = [item.context_expr for item in node.items]
    assign_targets = [item.optional_vars for item in node.items]

    body = buildStatementsNode(provider, node.body, source_ref)

    assert context_exprs and len(context_exprs) == len(assign_targets)

    context_exprs.reverse()
    assign_targets.reverse()

    for context_expr, assign_target in zip(context_exprs, assign_targets):
        body = _buildWithNode(
            provider=provider,
            body=body,
            context_expr=context_expr,
            assign_target=assign_target,
            sync=False,
            source_ref=source_ref,
        )

    return body


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
