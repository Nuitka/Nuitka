#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Try/finally statement and expression related code generation.

There is quite a bit of complexity in there, and they work with labels and
goto statements in the generated codes. This is nearly the most important
structure to us, due to the heavy use in re-formulations.
"""

from nuitka.utils import Utils

from . import CodeTemplates, Generator, LineNumberCodes

_temp_whitelist = [()]

def getTryFinallyTempWhitelist():
    return _temp_whitelist[-1]


def generateTryFinallyCode(to_name, statement, emit, context):
    # The try/finally is very hard for C-ish code generation. We need to react
    # on break, continue, return, raise in the tried blocks with re-raise. We
    # need to publish it to the handler (Python3) or save it for re-raise,
    # unless another exception or continue, break, return occurs. So this is
    # full of detail stuff, pylint: disable=R0914,R0912,R0915

    # TODO: This should come from Helpers module.
    from .CodeGeneration import generateStatementSequenceCode, generateExpressionCode

    # First, this may be used as an expression, in which case to_name won't be
    # set, we ask the checks to ignore currently set values.
    if to_name is not None:
        _temp_whitelist.append(context.getCleanupTempnames())

    tried_block = statement.getBlockTry()
    final_block = statement.getBlockFinal()

    if to_name is not None:
        expression = statement.getExpression()
    else:
        expression = None

    # The tried statements might raise, for which we define an escape. As we
    # only want to have the final block one, we use this as the target for the
    # others, but make them set flags.
    old_escape = context.getExceptionEscape()
    tried_handler_escape = context.allocateLabel("try_finally_handler")
    context.setExceptionEscape(tried_handler_escape)

    # This is the handler start label, that is where we jump to.
    if statement.needsContinueHandling() or \
       statement.needsBreakHandling() or \
       statement.needsReturnHandling():
        handler_start_target = context.allocateLabel(
            "try_finally_handler_start"
        )
    else:
        handler_start_target = None

    # Set the indicator for "continue" and "break" first. Mostly for ease of
    # use, the C++ compiler can push it back as it sees fit. When an actual
    # continue or break occurs, they will set the indicators. We indicate
    # the name to use for that in the targets.
    if statement.needsContinueHandling():
        continue_name = context.allocateTempName("continue", "bool")

        emit("%s = false;" % continue_name)

        old_continue_target = context.getLoopContinueTarget()
        context.setLoopContinueTarget(
            handler_start_target,
            continue_name
        )

    # See above.
    if statement.needsBreakHandling():
        break_name = context.allocateTempName("break", "bool")

        emit("%s = false;" % break_name)

        old_break_target = context.getLoopBreakTarget()
        context.setLoopBreakTarget(
            handler_start_target,
            break_name
        )

    # For return, we need to catch that too.
    if statement.needsReturnHandling():
        old_return = context.getReturnTarget()
        context.setReturnTarget(handler_start_target)

    # Initialize expression, so even if it exits, the compiler will not see a
    # random value there. This shouldn't be necessary and hopefully the C++
    # compiler will find out. Since these are rare, it doesn't matter.
    if to_name is not None:
        # TODO: Silences the compiler for now. If we are honest, a real
        # Py_XDECREF would be needed at release time then.
        emit("%s = NULL;" % to_name)

    # Now the tried block can be generated.
    emit("// Tried code")
    generateStatementSequenceCode(
        statement_sequence = tried_block,
        emit               = emit,
        allow_none         = True,
        context            = context
    )

    # An eventual assignment of the tried expression if any is practically part
    # of the tried block, just last.
    if to_name is not None:
        generateExpressionCode(
            to_name    = to_name,
            expression = expression,
            emit       = emit,
            context    = context
        )

    # So this is when we completed the handler without exiting.
    if statement.needsReturnHandling() and Utils.python_version >= 330:
        emit(
            "tmp_return_value = NULL;"
        )

    if handler_start_target is not None:
        Generator.getLabelCode(handler_start_target,emit)

    # For the try/finally expression, we allow that the tried block may in fact
    # not raise, continue, or break at all, but it would merely be there to do
    # something before an expression. Kind of as a side effect. To address that
    # we need to check.
    tried_block_may_raise = tried_block is not None and \
                            tried_block.mayRaiseException(BaseException)
    # TODO: This should be true, but it isn't.
    # assert tried_block_may_raise or to_name is not None

    if not tried_block_may_raise:
        tried_block_may_raise = expression is not None and \
                                expression.mayRaiseException(BaseException)

    if tried_block_may_raise:
        emit("// Final block of try/finally")

        # The try/finally of Python3 might publish an exception to the handler,
        # which makes things more complex.
        if not statement.needsExceptionPublish():
            keeper_type, keeper_value, keeper_tb = \
                context.getExceptionKeeperVariables()

            emit(
                CodeTemplates.template_final_handler_start % {
                    "final_error_target" : context.getExceptionEscape(),
                    "keeper_type"        : keeper_type,
                    "keeper_value"       : keeper_value,
                    "keeper_tb"          : keeper_tb
                }
            )
        else:
            emit(
                CodeTemplates.template_final_handler_start_python3 % {
                    "final_error_target" : context.getExceptionEscape(),
                }
            )

    # Restore the handlers changed during the tried block. For the final block
    # we may set up others later.
    context.setExceptionEscape(old_escape)
    if statement.needsContinueHandling():
        context.setLoopContinueTarget(old_continue_target)
    if statement.needsBreakHandling():
        context.setLoopBreakTarget(old_break_target)
    if statement.needsReturnHandling():
        context.setReturnTarget(old_return)
    old_return_value_release = context.getReturnReleaseMode()
    context.setReturnReleaseMode(statement.needsReturnValueRelease())

    # If the final block might raise, we need to catch that, so we release a
    # preserved exception and don't leak it.
    final_block_may_raise = \
      final_block is not None and \
      final_block.mayRaiseException(BaseException) and \
      not statement.needsExceptionPublish()

    final_block_may_return = \
      final_block is not None and \
      final_block.mayReturn()

    final_block_may_break = \
      final_block is not None and \
      final_block.mayBreak()

    final_block_may_continue = \
      final_block is not None and \
      final_block.mayContinue()

    # That would be a SyntaxError
    assert not final_block_may_continue

    old_return = context.getReturnTarget()
    old_break_target = context.getLoopBreakTarget()
    old_continue_target = context.getLoopContinueTarget()

    if final_block is not None:
        if Utils.python_version < 300 and context.getFrameHandle() is not None:
            tried_lineno_name = context.allocateTempName("tried_lineno", "int")
            LineNumberCodes.getLineNumberCode(tried_lineno_name, emit, context)

        if final_block_may_raise:
            old_escape = context.getExceptionEscape()
            context.setExceptionEscape(
                context.allocateLabel("try_finally_handler_error")
            )

        if final_block_may_return:
            context.setReturnTarget(
                context.allocateLabel("try_finally_handler_return")
            )

        if final_block_may_break:
            context.setLoopBreakTarget(
                context.allocateLabel("try_finally_handler_break")
            )

        generateStatementSequenceCode(
            statement_sequence = final_block,
            emit               = emit,
            context            = context
        )

        if Utils.python_version < 300 and context.getFrameHandle() is not None:
            LineNumberCodes.getSetLineNumberCodeRaw(
                to_name = tried_lineno_name,
                emit    = emit,
                context = context
            )
    else:
        # Final block is only optional for try/finally expressions. For
        # statements, they should be optimized way.
        assert to_name is not None

    context.setReturnReleaseMode(old_return_value_release)

    emit("// Re-raise as necessary after finally was executed.")

    if tried_block_may_raise and not statement.needsExceptionPublish():
        emit(
            Generator.CodeTemplates.template_final_handler_reraise % {
                "exception_exit" : old_escape,
                "keeper_type"    : keeper_type,
                "keeper_value"   : keeper_value,
                "keeper_tb"      : keeper_tb
            }
        )

    if Utils.python_version >= 330:
        return_template = Generator.CodeTemplates.\
          template_final_handler_return_reraise
    else:
        provider = statement.getParentVariableProvider()

        if not provider.isExpressionFunctionBody() or \
           not provider.isGenerator():
            return_template = Generator.CodeTemplates.\
              template_final_handler_return_reraise
        else:
            return_template = Generator.CodeTemplates.\
              template_final_handler_generator_return_reraise

    if statement.needsReturnHandling():
        emit(
            return_template % {
                "parent_return_target" : old_return
            }
        )

    if statement.needsContinueHandling():
        emit(
            """\
// Continue if entered via continue.
if ( %(continue_name)s )
{
""" % {
                "continue_name" : continue_name
            }
        )

        if type(old_continue_target) is tuple:
            emit("%s = true;" % old_continue_target[1])
            Generator.getGotoCode(old_continue_target[0], emit)
        else:
            Generator.getGotoCode(old_continue_target, emit)

        emit('}')
    if statement.needsBreakHandling():
        emit(
            """\
// Break if entered via break.
if ( %(break_name)s )
{
""" % {
                "break_name" : break_name
            }
        )

        if type(old_break_target) is tuple:
            emit("%s = true;" % old_break_target[1])
            Generator.getGotoCode(old_break_target[0], emit)
        else:
            Generator.getGotoCode(old_break_target, emit)

        emit('}')

    final_end_target = context.allocateLabel("finally_end")
    Generator.getGotoCode(final_end_target, emit)

    if final_block_may_raise:
        Generator.getLabelCode(context.getExceptionEscape(),emit)

        # TODO: Avoid the labels in this case
        if tried_block_may_raise:
            if Utils.python_version < 300:
                emit(
                    """\
Py_XDECREF( %(keeper_type)s );%(keeper_type)s = NULL;
Py_XDECREF( %(keeper_value)s );%(keeper_value)s = NULL;
Py_XDECREF( %(keeper_tb)s );%(keeper_tb)s = NULL;""" % {
                        "keeper_type"  : keeper_type,
                        "keeper_value" : keeper_value,
                        "keeper_tb"    : keeper_tb
                    }
                )
            else:
                emit("""\
if ( %(keeper_type)s )
{
    NORMALIZE_EXCEPTION( &%(keeper_type)s, &%(keeper_value)s, &%(keeper_tb)s );
    if( exception_value != %(keeper_value)s )
    {
        PyException_SetContext( %(keeper_value)s, exception_value );
    }
    else
    {
        Py_DECREF( exception_value );
    }
    Py_DECREF( exception_type );
    exception_type = %(keeper_type)s;
    exception_value = %(keeper_value)s;
    Py_XDECREF( exception_tb );
    exception_tb = %(keeper_tb)s;
}
""" % {
                        "keeper_type"  : keeper_type,
                        "keeper_value" : keeper_value,
                        "keeper_tb"    : keeper_tb
                    })


        context.setExceptionEscape(old_escape)
        Generator.getGotoCode(context.getExceptionEscape(), emit)

    if final_block_may_return:
        Generator.getLabelCode(context.getReturnTarget(),emit)

        # TODO: Avoid the labels in this case
        if tried_block_may_raise and not statement.needsExceptionPublish():
            emit(
                """\
Py_XDECREF( %(keeper_type)s );%(keeper_type)s = NULL;
Py_XDECREF( %(keeper_value)s );%(keeper_value)s = NULL;
Py_XDECREF( %(keeper_tb)s );%(keeper_tb)s = NULL;""" % {
                "keeper_type"  : keeper_type,
                "keeper_value" : keeper_value,
                "keeper_tb"    : keeper_tb
            }
        )

        context.setReturnTarget(old_return)
        Generator.getGotoCode(context.getReturnTarget(), emit)

    if final_block_may_break:
        Generator.getLabelCode(context.getLoopBreakTarget(),emit)

        # TODO: Avoid the labels in this case
        if tried_block_may_raise and not statement.needsExceptionPublish():
            emit(
            """\
Py_XDECREF( %(keeper_type)s );%(keeper_type)s = NULL;
Py_XDECREF( %(keeper_value)s );%(keeper_value)s = NULL;
Py_XDECREF( %(keeper_tb)s );%(keeper_tb)s = NULL;""" % {
                "keeper_type"  : keeper_type,
                "keeper_value" : keeper_value,
                "keeper_tb"    : keeper_tb
            }
        )

        context.setLoopBreakTarget(old_break_target)
        Generator.getGotoCode(context.getLoopBreakTarget(),emit)

    Generator.getLabelCode(final_end_target,emit)

    # Restore whitelist to previous state.
    if to_name is not None:
        _temp_whitelist.pop()
