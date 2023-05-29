#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Reformulation of try/except statements.

Consult the Developer Manual for information. TODO: Add ability to sync
source code comments with Developer Manual sections.

"""

from nuitka.nodes.BuiltinRefNodes import ExpressionBuiltinExceptionRef
from nuitka.nodes.ComparisonNodes import (
    ExpressionComparisonExceptionMatch,
    ExpressionComparisonIs,
)
from nuitka.nodes.ConditionalNodes import makeStatementConditional
from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.ExceptionNodes import (
    ExpressionCaughtExceptionTypeRef,
    ExpressionCaughtExceptionValueRef,
)
from nuitka.nodes.StatementNodes import (
    StatementPreserveFrameException,
    StatementPublishException,
    StatementRestoreFrameException,
    StatementsSequence,
)
from nuitka.nodes.TryNodes import StatementTry
from nuitka.nodes.VariableAssignNodes import makeStatementAssignmentVariable
from nuitka.nodes.VariableRefNodes import ExpressionTempVariableRef
from nuitka.PythonVersions import python_version

from .ReformulationAssignmentStatements import (
    buildAssignmentStatements,
    buildDeleteStatementFromDecoded,
    decodeAssignTarget,
)
from .ReformulationTryFinallyStatements import makeTryFinallyStatement
from .SyntaxErrors import raiseSyntaxError
from .TreeHelpers import (
    buildNode,
    buildStatementsNode,
    makeReraiseExceptionStatement,
    makeStatementsSequence,
    makeStatementsSequenceFromStatement,
    makeStatementsSequenceFromStatements,
    mergeStatements,
)


def makeTryExceptNoRaise(provider, temp_scope, tried, handling, no_raise, source_ref):
    # This helper executes the core re-formulation of "no_raise" blocks, which
    # are the "else" blocks of "try"/"except" statements. In order to limit the
    # execution, we use an indicator variable instead, which will signal that
    # the tried block executed up to the end. And then we make the else block be
    # a conditional statement checking that.

    # Indicator variable, will end up with C bool type, and need not be released.
    tmp_handler_indicator_variable = provider.allocateTempVariable(
        temp_scope=temp_scope, name="unhandled_indicator", temp_type="bool"
    )

    statements = mergeStatements(
        (
            makeStatementAssignmentVariable(
                variable=tmp_handler_indicator_variable,
                source=makeConstantRefNode(constant=False, source_ref=source_ref),
                source_ref=no_raise.getSourceReference(),
            ),
            handling,
        ),
        allow_none=True,
    )

    handling = StatementsSequence(statements=statements, source_ref=source_ref)

    return makeStatementsSequenceFromStatements(
        makeStatementAssignmentVariable(
            variable=tmp_handler_indicator_variable,
            source=makeConstantRefNode(constant=True, source_ref=source_ref),
            source_ref=source_ref,
        ),
        StatementTry(
            tried=tried,
            except_handler=handling,
            break_handler=None,
            continue_handler=None,
            return_handler=None,
            source_ref=source_ref,
        ),
        makeStatementConditional(
            condition=ExpressionComparisonIs(
                left=ExpressionTempVariableRef(
                    variable=tmp_handler_indicator_variable, source_ref=source_ref
                ),
                right=makeConstantRefNode(constant=True, source_ref=source_ref),
                source_ref=source_ref,
            ),
            yes_branch=no_raise,
            no_branch=None,
            source_ref=source_ref,
        ),
    )


def _makeTryExceptSingleHandlerNode(
    provider, public_exc, tried, exception_name, handler_body, source_ref
):
    # No need to create this in the first place if nothing is tried.
    if tried is None:
        return None

    if public_exc:
        preserver_id = provider.allocatePreserverId()

        handling = [
            StatementPreserveFrameException(
                preserver_id=preserver_id, source_ref=source_ref
            ),
            StatementPublishException(source_ref=source_ref),
        ]
    else:
        handling = []

    if not handler_body.isStatementsSequence():
        handler_body = makeStatementsSequenceFromStatement(statement=handler_body)

    if not tried.isStatementsSequence():
        tried = makeStatementsSequenceFromStatement(statement=tried)

    handling.append(
        makeStatementConditional(
            condition=ExpressionComparisonExceptionMatch(
                left=ExpressionCaughtExceptionTypeRef(source_ref=source_ref),
                right=ExpressionBuiltinExceptionRef(
                    exception_name=exception_name, source_ref=source_ref
                ),
                source_ref=source_ref,
            ),
            yes_branch=handler_body,
            no_branch=makeReraiseExceptionStatement(source_ref=source_ref),
            source_ref=source_ref,
        )
    )

    if python_version >= 0x300 and public_exc:
        handling = (
            makeTryFinallyStatement(
                provider=provider,
                tried=handling,
                final=StatementRestoreFrameException(
                    preserver_id=preserver_id, source_ref=source_ref.atInternal()
                ),
                source_ref=source_ref.atInternal(),
            ),
        )

    handling = makeStatementsSequenceFromStatements(*handling)

    return StatementTry(
        tried=tried,
        except_handler=handling,
        break_handler=None,
        continue_handler=None,
        return_handler=None,
        source_ref=source_ref,
    )


def makeTryExceptSingleHandlerNode(tried, exception_name, handler_body, source_ref):
    return _makeTryExceptSingleHandlerNode(
        provider=None,
        public_exc=False,
        tried=tried,
        exception_name=exception_name,
        handler_body=handler_body,
        source_ref=source_ref,
    )


def makeTryExceptSingleHandlerNodeWithPublish(
    provider, public_exc, tried, exception_name, handler_body, source_ref
):
    return _makeTryExceptSingleHandlerNode(
        provider=provider,
        public_exc=public_exc,
        tried=tried,
        exception_name=exception_name,
        handler_body=handler_body,
        source_ref=source_ref,
    )


def buildTryExceptionNode(provider, node, source_ref):
    # Try/except nodes. Re-formulated as described in the developer
    # manual. Exception handlers made the assignment to variables explicit. Same
    # for the "del" as done for Python3. Also catches always work a tuple of
    # exception types and hides away that they may be built or not.

    # Many variables and branches, due to the re-formulation that is going on
    # here, which just has the complexity, pylint: disable=too-many-branches,too-many-locals

    tried = buildStatementsNode(
        provider=provider, nodes=node.body, source_ref=source_ref
    )

    handlers = []

    for handler in node.handlers:
        exception_expression, exception_assign, exception_block = (
            handler.type,
            handler.name,
            handler.body,
        )

        if exception_assign is None:
            statements = [
                buildStatementsNode(
                    provider=provider, nodes=exception_block, source_ref=source_ref
                )
            ]
        elif python_version < 0x300:
            statements = [
                buildAssignmentStatements(
                    provider=provider,
                    node=exception_assign,
                    source=ExpressionCaughtExceptionValueRef(
                        source_ref=source_ref.atInternal()
                    ),
                    source_ref=source_ref.atInternal(),
                ),
                buildStatementsNode(
                    provider=provider, nodes=exception_block, source_ref=source_ref
                ),
            ]
        else:
            # Python3 requires temporary assignment of exception assignment.
            target_info = decodeAssignTarget(
                provider=provider, node=exception_assign, source_ref=source_ref
            )

            kind, detail = target_info

            assert kind == "Name", kind
            kind = "Name_Exception"

            statements = [
                buildAssignmentStatements(
                    provider=provider,
                    node=exception_assign,
                    source=ExpressionCaughtExceptionValueRef(
                        source_ref=source_ref.atInternal()
                    ),
                    source_ref=source_ref.atInternal(),
                ),
                makeTryFinallyStatement(
                    provider=provider,
                    tried=buildStatementsNode(
                        provider=provider, nodes=exception_block, source_ref=source_ref
                    ),
                    final=buildDeleteStatementFromDecoded(
                        provider=provider,
                        kind=kind,
                        detail=detail,
                        source_ref=source_ref,
                    ),
                    source_ref=source_ref,
                ),
            ]

        handler_body = makeStatementsSequence(
            statements=statements, allow_none=True, source_ref=source_ref
        )

        exception_types = buildNode(
            provider=provider,
            node=exception_expression,
            source_ref=source_ref,
            allow_none=True,
        )

        # The exception types should be a tuple, so as to be most general.
        if exception_types is None:
            if handler is not node.handlers[-1]:
                raiseSyntaxError(
                    "default 'except:' must be last",
                    source_ref.atLineNumber(handler.lineno).atColumnNumber(
                        handler.col_offset
                    ),
                )

        handlers.append((exception_types, handler_body))

    # Re-raise by default
    exception_handling = makeReraiseExceptionStatement(source_ref=source_ref)

    for exception_type, handler in reversed(handlers):
        if exception_type is None:
            # A default handler was given, so use that indeed.
            exception_handling = handler
        else:
            exception_handling = StatementsSequence(
                statements=(
                    makeStatementConditional(
                        condition=ExpressionComparisonExceptionMatch(
                            left=ExpressionCaughtExceptionTypeRef(
                                source_ref=exception_type.source_ref
                            ),
                            right=exception_type,
                            source_ref=exception_type.source_ref,
                        ),
                        yes_branch=handler,
                        no_branch=exception_handling,
                        source_ref=exception_type.source_ref,
                    ),
                ),
                source_ref=exception_type.source_ref,
            )

    if exception_handling is None:
        # For Python3, we need not publish at all, if all we do is to revert
        # that immediately. For Python2, the publish may release previously
        # published exception, which has side effects potentially.
        if python_version < 0x300:
            exception_handling = StatementsSequence(
                statements=(
                    StatementPreserveFrameException(
                        preserver_id=0,  # unused with Python2
                        source_ref=source_ref.atInternal(),
                    ),
                    StatementPublishException(source_ref=source_ref.atInternal()),
                ),
                source_ref=source_ref.atInternal(),
            )
    else:
        if python_version < 0x300:
            exception_handling.setChildStatements(
                (
                    StatementPreserveFrameException(
                        preserver_id=0,  # unused with Python2
                        source_ref=source_ref.atInternal(),
                    ),
                    StatementPublishException(source_ref=source_ref.atInternal()),
                )
                + exception_handling.subnode_statements,
            )
        else:
            preserver_id = provider.allocatePreserverId()

            exception_handling = makeStatementsSequenceFromStatements(
                StatementPreserveFrameException(
                    preserver_id=preserver_id, source_ref=source_ref.atInternal()
                ),
                StatementPublishException(source_ref=source_ref.atInternal()),
                makeTryFinallyStatement(
                    provider=provider,
                    tried=exception_handling,
                    final=StatementRestoreFrameException(
                        preserver_id=preserver_id, source_ref=source_ref.atInternal()
                    ),
                    source_ref=source_ref,
                ),
            )

    no_raise = buildStatementsNode(
        provider=provider, nodes=node.orelse, source_ref=source_ref
    )

    if no_raise is None:
        if tried is None:
            return None

        return StatementTry(
            tried=tried,
            except_handler=exception_handling,
            break_handler=None,
            continue_handler=None,
            return_handler=None,
            source_ref=source_ref,
        )
    else:
        if tried is None:
            return no_raise

        return makeTryExceptNoRaise(
            provider=provider,
            temp_scope=provider.allocateTempScope("try_except"),
            handling=exception_handling,
            tried=tried,
            no_raise=no_raise,
            source_ref=source_ref,
        )
