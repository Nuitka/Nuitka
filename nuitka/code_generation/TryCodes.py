#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Try statement and related code generation.

For Nuitka, all try/except and try/finally are dealt with this, where the
finally block gets duplicated into handlers. So this is a common low level
structure used, where exception handling and everything is made explicit.
"""

from nuitka import Options

from .CodeHelpers import generateExpressionCode, generateStatementSequenceCode
from .ErrorCodes import getMustNotGetHereCode
from .ExceptionCodes import getExceptionUnpublishedReleaseCode
from .IteratorCodes import getBuiltinLoopBreakNextCode
from .LabelCodes import getGotoCode, getLabelCode
from .VariableCodes import getVariableAssignmentCode


def generateTryCode(statement, emit, context):
    # The try construct is the most complex for code generation. We may need to
    # react on break, continue, return, raise in the handlers. For exception
    # and return handlers, we need to be able to re-raise or re-return.
    # So this is full of detail stuff, pylint: disable=too-many-branches,too-many-locals,too-many-statements

    if generateTryNextExceptStopIterationCode(statement, emit, context):
        return

    # Get the statement sequences involved. All except the tried block can be
    # None. For the tried block it would be a missed optimization. Also not all
    # the handlers must be None, then it's also a missed optimization.
    tried_block = statement.subnode_tried

    except_handler = statement.subnode_except_handler
    continue_handler = statement.subnode_continue_handler
    break_handler = statement.subnode_break_handler
    return_handler = statement.subnode_return_handler

    tried_block_may_raise = tried_block.mayRaiseException(BaseException)

    assert (
        tried_block_may_raise
        or continue_handler is not None
        or break_handler is not None
        or return_handler is not None
    ), statement.asXmlText()

    # The tried statements might raise, for which we define an escape.
    tried_handler_escape = context.allocateLabel("try_except_handler")
    if tried_block_may_raise:
        old_exception_escape = context.setExceptionEscape(tried_handler_escape)

    # The tried statements might continue, for which we define an escape.
    continue_handler_escape = context.allocateLabel("try_continue_handler")
    if continue_handler is not None:
        old_continue_target = context.setLoopContinueTarget(continue_handler_escape)

    # The tried statements might break, for which we define an escape.
    break_handler_escape = context.allocateLabel("try_break_handler")
    if break_handler is not None:
        old_break_target = context.setLoopBreakTarget(break_handler_escape)

    # The tried statements might return, for which we define an escape.
    return_handler_escape = context.allocateLabel("try_return_handler")
    if return_handler is not None:
        old_return_target = context.setReturnTarget(return_handler_escape)

    # Now the tried block can be generated, cannot be "None" or else the
    # optimization failed.
    emit("// Tried code:")
    generateStatementSequenceCode(
        statement_sequence=tried_block, emit=emit, allow_none=False, context=context
    )

    # Restore the old escape targets as preserved above, during the handlers,
    # the parent handlers should be back in effect.
    if tried_block_may_raise:
        context.setExceptionEscape(old_exception_escape)

    if continue_handler:
        context.setLoopContinueTarget(old_continue_target)

    if break_handler:
        context.setLoopBreakTarget(old_break_target)

    if return_handler:
        context.setReturnTarget(old_return_target)

    post_label = None

    if not tried_block.isStatementAborting():
        if post_label is None:
            post_label = context.allocateLabel("try_end")

        getGotoCode(post_label, emit)
    else:
        getMustNotGetHereCode(reason="tried codes exits in all cases", emit=emit)

    if return_handler is not None:
        assert tried_block.mayReturn()

        emit("// Return handler code:")
        getLabelCode(return_handler_escape, emit)

        # During the return value, the value being returned is in a variable,
        # and therefore needs to be released before being updated with a new
        # return value.
        old_return_value_release = context.setReturnReleaseMode(True)

        generateStatementSequenceCode(
            statement_sequence=return_handler,
            emit=emit,
            allow_none=False,
            context=context,
        )

        context.setReturnReleaseMode(old_return_value_release)

        assert return_handler.isStatementAborting()

    if tried_block_may_raise:
        emit("// Exception handler code:")
        getLabelCode(tried_handler_escape, emit)

        # Need to preserve exception state.
        (
            keeper_exception_state_name,
            keeper_lineno,
        ) = context.allocateExceptionKeeperVariables()

        old_keepers = context.setExceptionKeeperVariables(
            (keeper_exception_state_name, keeper_lineno)
        )

        (
            exception_state_name,
            exception_lineno,
        ) = context.variable_storage.getExceptionVariableDescriptions()

        emit(
            """\
%(keeper_lineno)s = %(exception_lineno)s;
%(exception_lineno)s = 0;
%(keeper_exception_state_name)s = %(exception_state_name)s;
INIT_ERROR_OCCURRED_STATE(&%(exception_state_name)s);
"""
            % {
                "keeper_exception_state_name": keeper_exception_state_name,
                "keeper_lineno": keeper_lineno,
                "exception_state_name": exception_state_name,
                "exception_lineno": exception_lineno,
            }
        )

        generateStatementSequenceCode(
            statement_sequence=except_handler,
            emit=emit,
            allow_none=True,
            context=context,
        )

        if except_handler is None or not except_handler.isStatementAborting():
            getExceptionUnpublishedReleaseCode(emit, context)

            if post_label is None:
                post_label = context.allocateLabel("try_end")

            getGotoCode(post_label, emit)

            getMustNotGetHereCode(
                reason="exception handler codes exits in all cases", emit=emit
            )

        context.setExceptionKeeperVariables(old_keepers)
    else:
        assert except_handler is None, tried_block.asXmlText()

    if break_handler is not None:
        assert tried_block.mayBreak()

        emit("// try break handler code:")
        getLabelCode(break_handler_escape, emit)

        generateStatementSequenceCode(
            statement_sequence=break_handler,
            emit=emit,
            allow_none=False,
            context=context,
        )

        assert break_handler.isStatementAborting()

    if continue_handler is not None:
        assert tried_block.mayContinue()

        emit("// try continue handler code:")
        getLabelCode(continue_handler_escape, emit)

        generateStatementSequenceCode(
            statement_sequence=continue_handler,
            emit=emit,
            allow_none=False,
            context=context,
        )

        assert continue_handler.isStatementAborting()

    emit("// End of try:")

    if post_label is not None:
        getLabelCode(post_label, emit)


def generateTryNextExceptStopIterationCode(statement, emit, context):
    # This has many branches which mean this optimized code generation is not
    # applicable, we return each time. pylint: disable=too-many-branches,too-many-return-statements

    except_handler = statement.subnode_except_handler

    if except_handler is None:
        return False

    if statement.subnode_break_handler is not None:
        return False

    if statement.subnode_continue_handler is not None:
        return False

    if statement.subnode_return_handler is not None:
        return False

    tried_statements = statement.subnode_tried.subnode_statements

    if len(tried_statements) != 1:
        return False

    handling_statements = except_handler.subnode_statements

    if len(handling_statements) != 1:
        return False

    tried_statement = tried_statements[0]

    if not tried_statement.isStatementAssignmentVariable():
        return False

    assign_source = tried_statement.subnode_source

    if not assign_source.isExpressionBuiltinNext1():
        return False

    handling_statement = handling_statements[0]

    if not handling_statement.isStatementConditional():
        return False

    yes_statements = handling_statement.subnode_yes_branch.subnode_statements
    no_statements = handling_statement.subnode_no_branch.subnode_statements

    if len(yes_statements) != 1:
        return False

    if not yes_statements[0].isStatementLoopBreak():
        return False

    if len(no_statements) != 1:
        return False

    if not no_statements[0].isStatementReraiseException():
        return False

    tmp_name = context.allocateTempName("next_source")

    generateExpressionCode(
        expression=assign_source.subnode_value,
        to_name=tmp_name,
        emit=emit,
        context=context,
    )

    tmp_name2 = context.allocateTempName("assign_source")

    with context.withCurrentSourceCodeReference(
        assign_source.getSourceReference()
        if Options.is_full_compat
        else statement.getSourceReference()
    ):
        getBuiltinLoopBreakNextCode(
            expression=assign_source.subnode_value,
            to_name=tmp_name2,
            value=tmp_name,
            emit=emit,
            context=context,
        )

        getVariableAssignmentCode(
            tmp_name=tmp_name2,
            variable=tried_statement.getVariable(),
            variable_trace=tried_statement.getVariableTrace(),
            needs_release=None,
            inplace=False,
            emit=emit,
            context=context,
        )

        if context.needsCleanup(tmp_name2):
            context.removeCleanupTempName(tmp_name2)

    return True


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
