#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka import Utils, SyntaxErrors, Options

from nuitka.nodes.VariableRefNodes import (
    ExpressionTargetTempVariableRef,
    ExpressionTempVariableRef
)
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.ExceptionNodes import ExpressionCaughtExceptionValueRef
from nuitka.nodes.BuiltinRefNodes import ExpressionBuiltinExceptionRef
from nuitka.nodes.ComparisonNodes import ExpressionComparisonIs
from nuitka.nodes.StatementNodes import StatementsSequence
from nuitka.nodes.ConditionalNodes import StatementConditional
from nuitka.nodes.AssignNodes import StatementAssignmentVariable
from nuitka.nodes.TryNodes import (
    StatementExceptHandler,
    StatementTryExcept
)

from .ReformulationAssignmentStatements import (
    buildDeleteStatementFromDecoded,
    buildAssignmentStatements,
    decodeAssignTarget
)


from .Helpers import (
    makeStatementsSequence,
    buildStatementsNode,
    buildNode
)


def makeTryExceptNoRaise(provider, temp_scope, tried, handlers, no_raise,
                         source_ref):
    # This helper executes the core re-formulation of "no_raise" blocks, which
    # are the "else" blocks of "try"/"except" statements. In order to limit the
    # execution, we use an indicator variable instead, which will signal that
    # the tried block executed up to the end. And then we make the else block be
    # a conditional statement checking that.

    # This is a separate function, so it can be re-used in other
    # re-formulations, e.g. with statements.

    assert no_raise is not None
    assert len(handlers) > 0

    tmp_handler_indicator_variable = provider.allocateTempVariable(
        temp_scope = temp_scope,
        name       = "unhandled_indicator"
    )

    for handler in handlers:
        statements = (
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetTempVariableRef(
                    variable   = tmp_handler_indicator_variable.makeReference(
                        provider
                    ),
                    source_ref = source_ref.atInternal()
                ),
                source       = ExpressionConstantRef(
                    constant   = False,
                    source_ref = source_ref
                ),
                source_ref   = no_raise.getSourceReference().atInternal()
            ),
            handler.getExceptionBranch()
        )

        handler.setExceptionBranch(
            makeStatementsSequence(
                statements = statements,
                allow_none = True,
                source_ref = source_ref
            )
        )

    statements = (
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_handler_indicator_variable.makeReference(
                    provider
                ),
                source_ref = source_ref.atInternal()
            ),
            source     = ExpressionConstantRef(
                constant   = True,
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
        StatementTryExcept(
            tried      = tried,
            handlers   = handlers,
            source_ref = source_ref
        ),
        StatementConditional(
            condition  = ExpressionComparisonIs(
                left = ExpressionTempVariableRef(
                    variable   = tmp_handler_indicator_variable.makeReference(
                        provider
                    ),
                    source_ref = source_ref
                ),
                right = ExpressionConstantRef(
                    constant   = True,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            yes_branch = no_raise,
            no_branch  = None,
            source_ref = source_ref
        )
    )

    return StatementsSequence(
        statements = statements,
        source_ref = source_ref
    )


def makeTryExceptSingleHandlerNode(tried, exception_name, handler_body,
                                   source_ref):
    return StatementTryExcept(
        tried      = tried,
        handlers   = (
            StatementExceptHandler(
                exception_types = (
                    ExpressionBuiltinExceptionRef(
                        exception_name = exception_name,
                        source_ref     = source_ref
                    ),
                ),
                body            = handler_body,
                source_ref      = source_ref
            ),
        ),
        source_ref = source_ref
    )


def buildTryExceptionNode(provider, node, source_ref):
    # Try/except nodes. Re-formulated as described in the developer
    # manual. Exception handlers made the assignment to variables explicit. Same
    # for the "del" as done for Python3. Also catches always work a tuple of
    # exception types and hides away that they may be built or not.

    # Many variables, due to the re-formulation that is going on here, which
    # just has the complexity, pylint: disable=R0914

    handlers = []

    for handler in node.handlers:
        exception_expression, exception_assign, exception_block = (
            handler.type,
            handler.name,
            handler.body
        )

        statements = [
            buildAssignmentStatements(
                provider   = provider,
                node       = exception_assign,
                allow_none = True,
                source     = ExpressionCaughtExceptionValueRef(
                    source_ref = source_ref.atInternal()
                ),
                source_ref = source_ref.atInternal()
            ),
            buildStatementsNode(
                provider   = provider,
                nodes      = exception_block,
                source_ref = source_ref
            )
        ]

        if Utils.python_version >= 300:
            target_info = decodeAssignTarget(
                provider   = provider,
                node       = exception_assign,
                source_ref = source_ref,
                allow_none = True
            )

            if target_info is not None:
                kind, detail = target_info

                assert kind == "Name", kind
                kind = "Name_Exception"

                statements.append(
                    buildDeleteStatementFromDecoded(
                        kind       = kind,
                        detail     = detail,
                        source_ref = source_ref
                    )
                )

        handler_body = makeStatementsSequence(
            statements = statements,
            allow_none = True,
            source_ref = source_ref
        )

        exception_types = buildNode(
            provider   = provider,
            node       = exception_expression,
            source_ref = source_ref,
            allow_none = True
        )

        # The exception types should be a tuple, so as to be most general.
        if exception_types is None:
            exception_types = ()

            if handler is not node.handlers[-1]:
                SyntaxErrors.raiseSyntaxError(
                    reason    = "default 'except:' must be last",
                    source_ref = source_ref.atLineNumber(
                        handler.lineno-1
                          if Options.isFullCompat() else
                        handler.lineno
                    )
                )
        elif exception_types.isExpressionMakeSequence():
            exception_types = exception_types.getElements()
        else:
            exception_types = (exception_types,)

        handlers.append(
            StatementExceptHandler(
                exception_types = exception_types,
                body            = handler_body,
                source_ref      = source_ref
            )
        )

    tried = buildStatementsNode(
        provider   = provider,
        nodes      = node.body,
        source_ref = source_ref
    )

    no_raise = buildStatementsNode(
        provider   = provider,
        nodes      = node.orelse,
        source_ref = source_ref
    )

    if no_raise is None:
        return StatementTryExcept(
            handlers   = handlers,
            tried      = tried,
            source_ref = source_ref
        )
    else:
        return makeTryExceptNoRaise(
            provider   = provider,
            temp_scope = provider.allocateTempScope("try_except"),
            handlers   = handlers,
            tried      = tried,
            no_raise   = no_raise,
            source_ref = source_ref
        )
