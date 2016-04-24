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
""" Reformulation of with statements.

Consult the developer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

from nuitka import Options
from nuitka.nodes.AssignNodes import (
    ExpressionTargetTempVariableRef,
    ExpressionTempVariableRef,
    StatementAssignmentVariable,
    StatementReleaseVariable
)
from nuitka.nodes.AttributeNodes import (
    ExpressionAttributeLookup,
    ExpressionAttributeLookupSpecial
)
from nuitka.nodes.CallNodes import (
    ExpressionCallEmpty,
    ExpressionCallNoKeywords
)
from nuitka.nodes.ComparisonNodes import ExpressionComparisonIs
from nuitka.nodes.ConditionalNodes import StatementConditional
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.ContainerMakingNodes import ExpressionMakeTuple
from nuitka.nodes.CoroutineNodes import ExpressionAsyncWait
from nuitka.nodes.ExceptionNodes import (
    ExpressionCaughtExceptionTracebackRef,
    ExpressionCaughtExceptionTypeRef,
    ExpressionCaughtExceptionValueRef
)
from nuitka.nodes.StatementNodes import (
    StatementExpressionOnly,
    StatementsSequence
)
from nuitka.PythonVersions import python_version
from nuitka.tree.Helpers import makeReraiseExceptionStatement

from .Helpers import (
    buildNode,
    buildStatementsNode,
    getKind,
    makeConditionalStatement,
    makeStatementsSequence,
    makeStatementsSequenceFromStatement
)
from .ReformulationAssignmentStatements import buildAssignmentStatements
from .ReformulationTryExceptStatements import \
    makeTryExceptSingleHandlerNodeWithPublish
from .ReformulationTryFinallyStatements import makeTryFinallyStatement


def _buildWithNode(provider, context_expr, assign_target, body, body_lineno,
                   sync, source_ref):
    # Many details, pylint: disable=R0914
    with_source = buildNode(provider, context_expr, source_ref)

    if Options.isFullCompat():
        source_ref = with_source.getCompatibleSourceReference()

    temp_scope = provider.allocateTempScope("with")

    tmp_source_variable = provider.allocateTempVariable(
        temp_scope = temp_scope,
        name       = "source"
    )
    tmp_exit_variable = provider.allocateTempVariable(
        temp_scope = temp_scope,
        name       = "exit"
    )
    tmp_enter_variable = provider.allocateTempVariable(
        temp_scope = temp_scope,
        name       = "enter"
    )
    tmp_indicator_variable = provider.allocateTempVariable(
        temp_scope = temp_scope,
        name       = "indicator"
    )

    statements = (
        buildAssignmentStatements(
            provider   = provider,
            node       = assign_target,
            allow_none = True,
            source     = ExpressionTempVariableRef(
                variable   = tmp_enter_variable,
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
        body
    )

    with_body = makeStatementsSequence(
        statements = statements,
        allow_none = True,
        source_ref = source_ref
    )

    if Options.isFullCompat():
        if body:
            deepest = body

            while deepest.getVisitableNodes():
                deepest = deepest.getVisitableNodes()[-1]

            body_lineno = deepest.getCompatibleSourceReference().getLineNumber()

        with_exit_source_ref = source_ref.atLineNumber(body_lineno)
    else:
        with_exit_source_ref = source_ref

    # The "__enter__" and "__exit__" were normal attribute lookups under
    # CPython2.6, but that changed with CPython2.7.
    if python_version < 270:
        attribute_lookup_class = ExpressionAttributeLookup
    else:
        attribute_lookup_class = ExpressionAttributeLookupSpecial

    enter_value = ExpressionCallEmpty(
        called     = attribute_lookup_class(
            source         = ExpressionTempVariableRef(
                variable   = tmp_source_variable,
                source_ref = source_ref
            ),
            attribute_name = "__enter__" if sync else "__aenter__",
            source_ref     = source_ref
        ),
        source_ref = source_ref
    )

    exit_value_exception = ExpressionCallNoKeywords(
        called     = ExpressionTempVariableRef(
            variable   = tmp_exit_variable,
            source_ref = with_exit_source_ref
        ),
        args       = ExpressionMakeTuple(
            elements   = (
                ExpressionCaughtExceptionTypeRef(
                    source_ref = with_exit_source_ref
                ),
                ExpressionCaughtExceptionValueRef(
                    source_ref = with_exit_source_ref
                ),
                ExpressionCaughtExceptionTracebackRef(
                    source_ref = source_ref
                ),
            ),
            source_ref = source_ref
        ),
        source_ref = with_exit_source_ref
    )

    exit_value_no_exception = ExpressionCallNoKeywords(
        called     = ExpressionTempVariableRef(
            variable   = tmp_exit_variable,
            source_ref = source_ref
        ),
        args       = ExpressionConstantRef(
            constant   = (None, None, None),
            source_ref = source_ref
        ),
        source_ref = with_exit_source_ref
    )

    # For "async with", await the entered value and exit value must be awaited.
    if not sync:
        enter_value = ExpressionAsyncWait(
            expression = enter_value,
            source_ref = source_ref
        )
        exit_value_exception = ExpressionAsyncWait(
            expression = exit_value_exception,
            source_ref = source_ref
        )
        exit_value_no_exception = ExpressionAsyncWait(
            expression = exit_value_no_exception,
            source_ref = source_ref
        )

    statements = [
        # First assign the with context to a temporary variable.
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_source_variable,
                source_ref = source_ref
            ),
            source       = with_source,
            source_ref   = source_ref
        ),
        # Next, assign "__enter__" and "__exit__" attributes to temporary
        # variables.
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_exit_variable,
                source_ref = source_ref
            ),
            source       = attribute_lookup_class(
                source         = ExpressionTempVariableRef(
                    variable   = tmp_source_variable,
                    source_ref = source_ref
                ),
                attribute_name = "__exit__" if sync else "__aexit__",
                source_ref     = source_ref
            ),
            source_ref   = source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_enter_variable,
                source_ref = source_ref
            ),
            source       = enter_value,
            source_ref   = source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_indicator_variable,
                source_ref = source_ref
            ),
            source       = ExpressionConstantRef(
                constant   = True,
                source_ref = source_ref
            ),
            source_ref   = source_ref
        ),
    ]

    statements += [
        makeTryFinallyStatement(
            provider   = provider,
            tried      = makeTryExceptSingleHandlerNodeWithPublish(
                provider       = provider,
                tried          = with_body,
                exception_name = "BaseException",
                handler_body   = StatementsSequence(
                    statements = (
                        # Prevents final block from calling __exit__ as
                        # well.
                        StatementAssignmentVariable(
                            variable_ref = ExpressionTargetTempVariableRef(
                                variable   = tmp_indicator_variable,
                                source_ref = source_ref
                            ),
                            source       = ExpressionConstantRef(
                                constant   = False,
                                source_ref = source_ref
                            ),
                            source_ref   = source_ref
                        ),
                        makeConditionalStatement(
                            condition  = exit_value_exception,
                            no_branch  = makeReraiseExceptionStatement(
                                source_ref = with_exit_source_ref
                            ),
                            yes_branch = None,
                            source_ref = with_exit_source_ref
                        ),
                    ),
                    source_ref = source_ref
                ),
                public_exc     = python_version >= 270,
                source_ref     = source_ref
            ),
            final      = StatementConditional(
                condition  = ExpressionComparisonIs(
                    left       = ExpressionTempVariableRef(
                        variable   = tmp_indicator_variable,
                        source_ref = source_ref
                    ),
                    right      = ExpressionConstantRef(
                        constant   = True,
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
                yes_branch = makeStatementsSequenceFromStatement(
                    statement = StatementExpressionOnly(
                        expression = exit_value_no_exception,
                        source_ref = source_ref
                    )
                ),
                no_branch  = None,
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    ]

    return makeTryFinallyStatement(
        provider   = provider,
        tried      = statements,
        final      = (
            StatementReleaseVariable(
                variable   = tmp_source_variable,
                source_ref = with_exit_source_ref
            ),
            StatementReleaseVariable(
                variable   = tmp_enter_variable,
                source_ref = with_exit_source_ref
            ),
            StatementReleaseVariable(
                variable   = tmp_exit_variable,
                source_ref = with_exit_source_ref
            ),
            StatementReleaseVariable(
                variable   = tmp_indicator_variable,
                source_ref = with_exit_source_ref
            ),
        ),
        source_ref = source_ref
    )


def buildWithNode(provider, node, source_ref):
    # "with" statements are re-formulated as described in the developer
    # manual. Catches exceptions, and provides them to "__exit__", while making
    # the "__enter__" value available under a given name.

    # Before Python3.3, multiple context managers are not visible in the parse
    # tree, now we need to handle it ourselves.
    if hasattr(node, "items"):
        context_exprs = [item.context_expr for item in node.items]
        assign_targets = [item.optional_vars for item in node.items]
    else:
        # Make it a list for before Python3.3
        context_exprs = [node.context_expr]
        assign_targets = [node.optional_vars]


    # The body for the first context manager is the other things.
    body = buildStatementsNode(provider, node.body, source_ref)

    assert len(context_exprs) > 0 and len(context_exprs) == len(assign_targets)

    context_exprs.reverse()
    assign_targets.reverse()

    # For compatibility, we need to gather a line number for the body here
    # already, but only the full compatibility mode will use it.
    terminal_statement = node.body[-1]
    while getKind(terminal_statement) in ("With", "AsyncWith"):
        terminal_statement = terminal_statement.body[-1]
    body_lineno = terminal_statement.lineno

    for context_expr, assign_target in zip(context_exprs, assign_targets):
        body = _buildWithNode(
            provider      = provider,
            body          = body,
            body_lineno   = body_lineno,
            context_expr  = context_expr,
            assign_target = assign_target,
            sync          = True,
            source_ref    = source_ref
        )

    return body


def buildAsyncWithNode(provider, node, source_ref):
    # "with" statements are re-formulated as described in the developer
    # manual. Catches exceptions, and provides them to "__exit__", while making
    # the "__enter__" value available under a given name.

    # Before Python3.3, multiple context managers are not visible in the parse
    # tree, now we need to handle it ourselves.
    context_exprs = [item.context_expr for item in node.items]
    assign_targets = [item.optional_vars for item in node.items]

    # The body for the first context manager is the other things.
    body = buildStatementsNode(provider, node.body, source_ref)

    assert len(context_exprs) > 0 and len(context_exprs) == len(assign_targets)

    context_exprs.reverse()
    assign_targets.reverse()

    # For compatibility, we need to gather a line number for the body here
    # already, but only the full compatibility mode will use it.
    terminal_statement = node.body[-1]
    while getKind(terminal_statement) in ("With", "AsyncWith"):
        terminal_statement = terminal_statement.body[-1]
    body_lineno = terminal_statement.lineno

    for context_expr, assign_target in zip(context_exprs, assign_targets):
        body = _buildWithNode(
            provider      = provider,
            body          = body,
            body_lineno   = body_lineno,
            context_expr  = context_expr,
            assign_target = assign_target,
            sync          = False,
            source_ref    = source_ref
        )

    return body
