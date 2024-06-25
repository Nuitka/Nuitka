#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Reformulation of with statements.

Consult the Developer Manual for information. TODO: Add ability to sync
source code comments with Developer Manual sections.

"""

from nuitka import Options
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
    makeStatementsSequence,
)


def _buildWithNode(provider, context_expr, assign_target, body, sync, source_ref):
    # Many details, pylint: disable=too-many-branches,too-many-locals
    with_source = buildNode(provider, context_expr, source_ref)

    if python_version < 0x380 and Options.is_full_compat:
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

    # Indicator variable, will end up with C bool type, and need not be released.
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

    with_body = makeStatementsSequence(
        statements=statements, allow_none=True, source_ref=source_ref
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

    enter_value = ExpressionCallEmpty(
        called=attribute_lookup_maker(
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

    # For "async with", await the entered value and exit value must be awaited.
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

    # First assign the with context to a temporary variable.
    statements = [
        makeStatementAssignmentVariable(
            variable=tmp_source_variable, source=with_source, source_ref=source_ref
        )
    ]

    # Before 3.9, __aenter__ is immediately awaited, after we first do __aexit__ lookup.
    if not sync and python_version < 0x390:
        enter_value = ExpressionYieldFromAwaitable(
            expression=ExpressionAsyncWaitEnter(
                expression=enter_value, source_ref=source_ref
            ),
            source_ref=source_ref,
        )

    attribute_enter_assignment = makeStatementAssignmentVariable(
        variable=tmp_enter_variable, source=enter_value, source_ref=source_ref
    )

    attribute_exit_assignment = makeStatementAssignmentVariable(
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

    # Next, assign "__enter__" and "__exit__" attributes to temporary variables, and
    # depending on Python versions switch the order of these lookups and the order of
    # awaiting enter.
    # Normal "with" statements are enter, exit ordered after 3.6, and "async with"
    # are since 3.9, and since 3.9 the enter is not awaited, until an exit is present.
    if python_version >= 0x390 and not sync:
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

        attribute_assignments = (
            attribute_enter_assignment,
            attribute_exit_assignment,
            enter_await_statement,
        )
    elif python_version >= 0x360 and sync:
        attribute_assignments = (attribute_enter_assignment, attribute_exit_assignment)
    else:
        attribute_assignments = (attribute_exit_assignment, attribute_enter_assignment)

    statements.extend(attribute_assignments)

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
                        # Prevents final block from calling __exit__ as
                        # well.
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
    # "with" statements are re-formulated as described in the developer
    # manual. Catches exceptions, and provides them to "__exit__", while making
    # the "__enter__" value available under a given name.

    # Before Python3, multiple context managers are not visible in the parse
    # tree, now we need to handle it ourselves.
    if hasattr(node, "items"):
        context_exprs = [item.context_expr for item in node.items]
        assign_targets = [item.optional_vars for item in node.items]
    else:
        # Make it a list for before Python3
        context_exprs = [node.context_expr]
        assign_targets = [node.optional_vars]

    # The body for the first context manager is the other things.
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
    # "with" statements are re-formulated as described in the developer
    # manual. Catches exceptions, and provides them to "__exit__", while making
    # the "__enter__" value available under a given name.

    # Before Python3, multiple context managers are not visible in the parse
    # tree, now we need to handle it ourselves.
    context_exprs = [item.context_expr for item in node.items]
    assign_targets = [item.optional_vars for item in node.items]

    # The body for the first context manager is the other things.
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
