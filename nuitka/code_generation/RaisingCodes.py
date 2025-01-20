#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Code generation for implicit and explicit exception raises.

Exceptions from other operations are consider ErrorCodes domain.

"""

from nuitka import Options
from nuitka.Builtins import isBaseExceptionSimpleExtension
from nuitka.PythonVersions import python_version

from .CodeHelpers import (
    generateChildExpressionsCode,
    generateExpressionCode,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getErrorExitCode, getFrameVariableTypeDescriptionCode
from .ExceptionCodes import getExceptionIdentifier
from .LabelCodes import getGotoCode
from .LineNumberCodes import (
    emitErrorLineNumberUpdateCode,
    getErrorLineNumberUpdateCode,
)
from .PythonAPICodes import getReferenceExportCode


def generateReraiseCode(statement, emit, context):
    with context.withCurrentSourceCodeReference(
        value=statement.getCompatibleSourceReference()
    ):
        getReRaiseExceptionCode(emit=emit, context=context)


def _haveQuickExceptionCreationCode(exception_name):
    result = exception_name in ("StopIteration",)

    # TODO: Get this complete for larger test suites.
    # assert result, exception_name

    return result


def _generateExceptionNormalizeCode(to_name, exception_type, emit, context):

    if exception_type.isExpressionBuiltinExceptionRef():
        exception_name = exception_type.getExceptionName()
        if isBaseExceptionSimpleExtension(exception_type.getCompileTimeConstant()):
            emit(
                "%s = MAKE_BASE_EXCEPTION_DERIVED_EMPTY(%s);"
                % (to_name, getExceptionIdentifier(exception_name))
            )
            context.addCleanupTempName(to_name)

            return
        elif _haveQuickExceptionCreationCode(exception_type.getExceptionName()):
            # TODO: Code generation like this here, ought to be shared with
            # the one for ExpressionBuiltinMakeExceptionRef once that is
            # done too.
            if exception_name == "StopIteration":
                emit("%s = MAKE_STOP_ITERATION_EMPTY();" % to_name)
            else:
                assert False, exception_name

            context.addCleanupTempName(to_name)
            return

    # TODO: Can only fall through if exception builtins are not fully handled,
    # but we should make sure that doesn't ever happen by handling them all.

    if exception_type.isExpressionBuiltinMakeException():
        # TODO: Make this shape based, but currently the nodes do not
        # provide the shape, we need to add that.

        # No need to normalize these.
        generateExpressionCode(
            to_name=to_name,
            expression=exception_type,
            emit=emit,
            context=context,
        )
    else:
        # Need to normalize exceptions.
        raise_type_input_name = context.allocateTempName("raise_type_input")

        generateExpressionCode(
            to_name=raise_type_input_name,
            expression=exception_type,
            emit=emit,
            context=context,
        )

        emit(
            "%s = NORMALIZE_EXCEPTION_VALUE_FOR_RAISE(tstate, %s);"
            % (to_name, raise_type_input_name)
        )

        getErrorExitCode(
            check_name=to_name,
            release_name=raise_type_input_name,
            needs_check=True,
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(to_name)


def generateRaiseCode(statement, emit, context):
    exception_type = statement.subnode_exception_type
    exception_value = statement.subnode_exception_value
    exception_tb = statement.subnode_exception_trace
    exception_cause = statement.subnode_exception_cause

    # Exception cause is only possible with simple raise form.
    if exception_cause is not None:
        assert exception_type is not None
        assert exception_value is None
        assert exception_tb is None

        raise_type_name = context.allocateTempName("raise_type")

        if python_version >= 0x3C0:
            _generateExceptionNormalizeCode(
                to_name=raise_type_name,
                exception_type=exception_type,
                emit=emit,
                context=context,
            )
        else:
            generateExpressionCode(
                to_name=raise_type_name,
                expression=exception_type,
                emit=emit,
                context=context,
            )

        raise_cause_name = context.allocateTempName("raise_cause")

        generateExpressionCode(
            to_name=raise_cause_name,
            expression=exception_cause,
            emit=emit,
            context=context,
        )

        with context.withCurrentSourceCodeReference(
            exception_cause.getSourceReference()
        ):
            _getRaiseExceptionWithCauseCode(
                raise_type_name=raise_type_name,
                raise_cause_name=raise_cause_name,
                emit=emit,
                context=context,
            )
    elif exception_type is None:
        assert False, statement
    elif exception_value is None and exception_tb is None:
        raise_type_name = context.allocateTempName("raise_type")

        if python_version >= 0x3C0:
            _generateExceptionNormalizeCode(
                to_name=raise_type_name,
                exception_type=exception_type,
                emit=emit,
                context=context,
            )
        else:
            generateExpressionCode(
                to_name=raise_type_name,
                expression=exception_type,
                emit=emit,
                context=context,
            )

        with context.withCurrentSourceCodeReference(
            value=exception_type.getCompatibleSourceReference()
        ):
            _getRaiseExceptionWithTypeCode(
                raise_type_name=raise_type_name, emit=emit, context=context
            )

    elif exception_tb is None:
        raise_type_name = context.allocateTempName("raise_type")

        generateExpressionCode(
            to_name=raise_type_name,
            expression=exception_type,
            emit=emit,
            context=context,
        )

        raise_value_name = context.allocateTempName("raise_value")

        generateExpressionCode(
            to_name=raise_value_name,
            expression=exception_value,
            emit=emit,
            context=context,
        )

        with context.withCurrentSourceCodeReference(
            exception_value.getCompatibleSourceReference()
        ):
            _getRaiseExceptionWithValueCode(
                raise_type_name=raise_type_name,
                raise_value_name=raise_value_name,
                emit=emit,
                context=context,
            )
    else:
        raise_type_name = context.allocateTempName("raise_type")

        generateExpressionCode(
            to_name=raise_type_name,
            expression=exception_type,
            emit=emit,
            context=context,
        )

        raise_value_name = context.allocateTempName("raise_value")

        generateExpressionCode(
            to_name=raise_value_name,
            expression=exception_value,
            emit=emit,
            context=context,
        )

        raise_tb_name = context.allocateTempName("raise_tb")

        generateExpressionCode(
            to_name=raise_tb_name, expression=exception_tb, emit=emit, context=context
        )

        with context.withCurrentSourceCodeReference(exception_tb.getSourceReference()):
            _getRaiseExceptionWithTracebackCode(
                raise_type_name=raise_type_name,
                raise_value_name=raise_value_name,
                raise_tb_name=raise_tb_name,
                emit=emit,
                context=context,
            )


def generateRaiseExpressionCode(to_name, expression, emit, context):
    (exception_value_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    # Missed optimization opportunity, please report it, this should not
    # normally happen. We are supposed to propagate this upwards.
    if Options.is_debug:
        # TODO: Need to optimize ExpressionLocalsVariableRefOrFallback once we know
        # it handles cases where the value is not in locals dict properly.

        parent = expression.parent
        assert (
            parent.isExpressionSideEffects()
            or parent.isExpressionConditional()
            or parent.isExpressionConditionalOr()
            or parent.isExpressionConditionalAnd()
            or parent.isExpressionLocalsVariableRefOrFallback()
        ), (expression, expression.parent, expression.asXmlText())

    with withObjectCodeTemporaryAssignment(
        to_name, "raise_exception_result", expression, emit, context
    ) as value_name:
        # That's how we indicate exception to the surrounding world.
        emit("%s = NULL;" % value_name)

        _getRaiseExceptionWithTypeCode(
            raise_type_name=exception_value_name,
            emit=emit,
            context=context,
        )


def getReRaiseExceptionCode(emit, context):
    (
        exception_state_name,
        exception_lineno,
    ) = context.variable_storage.getExceptionVariableDescriptions()

    (
        keeper_exception_state_name,
        _keeper_lineno,
    ) = context.getExceptionKeeperVariables()

    if keeper_exception_state_name is None:
        emit(
            """\
%(bool_res_name)s = RERAISE_EXCEPTION(tstate, &%(exception_state_name)s);
if (unlikely(%(bool_res_name)s == false)) {
    %(update_code)s
}
"""
            % {
                "exception_state_name": exception_state_name,
                "bool_res_name": context.getBoolResName(),
                "update_code": getErrorLineNumberUpdateCode(context),
            }
        )

        frame_handle = context.getFrameHandle()

        if frame_handle:
            emit(
                """\
{
    PyTracebackObject *exception_tb = GET_EXCEPTION_STATE_TRACEBACK(&%(exception_state_name)s);

    if ((exception_tb != NULL) && (exception_tb->tb_frame == &%(frame_identifier)s->m_frame)) {
        %(frame_identifier)s->m_frame.f_lineno = exception_tb->tb_lineno;
    }
}"""
                % {
                    "exception_state_name": exception_state_name,
                    "frame_identifier": context.getFrameHandle(),
                }
            )

            emit(getFrameVariableTypeDescriptionCode(context))
    else:
        (
            keeper_exception_state_name,
            keeper_lineno,
        ) = context.getExceptionKeeperVariables()

        emit(
            """\
// Re-raise.
%(exception_state_name)s = %(keeper_exception_state_name)s;
%(exception_lineno)s = %(keeper_lineno)s;
"""
            % {
                "exception_state_name": exception_state_name,
                "exception_lineno": exception_lineno,
                "keeper_exception_state_name": keeper_exception_state_name,
                "keeper_lineno": keeper_lineno,
            }
        )

    getGotoCode(context.getExceptionEscape(), emit)


def _getRaiseExceptionWithCauseCode(raise_type_name, raise_cause_name, emit, context):
    (
        exception_state_name,
        _exception_lineno,
    ) = context.variable_storage.getExceptionVariableDescriptions()

    if python_version < 0x3C0:
        emit("%s.exception_type = %s;" % (exception_state_name, raise_type_name))
    else:
        emit("%s.exception_value = %s;" % (exception_state_name, raise_type_name))

    getReferenceExportCode(raise_type_name, emit, context)

    getReferenceExportCode(raise_cause_name, emit, context)

    emitErrorLineNumberUpdateCode(emit, context)
    emit(
        "RAISE_EXCEPTION_WITH_CAUSE(tstate, &%s, %s);"
        % (exception_state_name, raise_cause_name)
    )

    emit(getFrameVariableTypeDescriptionCode(context))

    getGotoCode(context.getExceptionEscape(), emit)

    if context.needsCleanup(raise_type_name):
        context.removeCleanupTempName(raise_type_name)
    if context.needsCleanup(raise_cause_name):
        context.removeCleanupTempName(raise_cause_name)


def _getRaiseExceptionWithTypeCode(raise_type_name, emit, context):
    (
        exception_state_name,
        _exception_lineno,
    ) = context.variable_storage.getExceptionVariableDescriptions()

    if python_version < 0x3C0:
        emit("%s.exception_type = %s;" % (exception_state_name, raise_type_name))
        getReferenceExportCode(raise_type_name, emit, context)

        emitErrorLineNumberUpdateCode(emit, context)

        emit("RAISE_EXCEPTION_WITH_TYPE(tstate, &%s);" % exception_state_name)
    else:
        emit("%s.exception_value = %s;" % (exception_state_name, raise_type_name))
        getReferenceExportCode(raise_type_name, emit, context)

        emitErrorLineNumberUpdateCode(emit, context)

        emit("RAISE_EXCEPTION_WITH_VALUE(tstate, &%s);" % exception_state_name)

    emit(getFrameVariableTypeDescriptionCode(context))

    getGotoCode(context.getExceptionEscape(), emit)

    if context.needsCleanup(raise_type_name):
        context.removeCleanupTempName(raise_type_name)


def _getRaiseExceptionWithValueCode(raise_type_name, raise_value_name, emit, context):
    (
        exception_state_name,
        _exception_lineno,
    ) = context.variable_storage.getExceptionVariableDescriptions()

    emit("%s.exception_type = %s;" % (exception_state_name, raise_type_name))
    getReferenceExportCode(raise_type_name, emit, context)
    emit("%s.exception_value = %s;" % (exception_state_name, raise_value_name))
    getReferenceExportCode(raise_value_name, emit, context)

    emitErrorLineNumberUpdateCode(emit, context)

    emit("RAISE_EXCEPTION_WITH_TYPE_AND_VALUE(tstate, &%s);" % (exception_state_name,))

    emit(getFrameVariableTypeDescriptionCode(context))

    getGotoCode(context.getExceptionEscape(), emit)

    if context.needsCleanup(raise_type_name):
        context.removeCleanupTempName(raise_type_name)
    if context.needsCleanup(raise_value_name):
        context.removeCleanupTempName(raise_value_name)


def _getRaiseExceptionWithTracebackCode(
    raise_type_name, raise_value_name, raise_tb_name, emit, context
):
    (
        exception_state_name,
        _exception_lineno,
    ) = context.variable_storage.getExceptionVariableDescriptions()

    emit("%s.exception_type = %s;" % (exception_state_name, raise_type_name))
    getReferenceExportCode(raise_type_name, emit, context)
    emit("%s.exception_value = %s;" % (exception_state_name, raise_value_name))
    getReferenceExportCode(raise_value_name, emit, context)
    emit(
        "%s.exception_tb = (PyTracebackObject *)%s;"
        % (exception_state_name, raise_tb_name)
    )
    getReferenceExportCode(raise_tb_name, emit, context)

    emit("RAISE_EXCEPTION_WITH_TRACEBACK(tstate, &%s);" % (exception_state_name))

    # If anything is wrong, that will be used.
    emitErrorLineNumberUpdateCode(emit, context)

    emit(getFrameVariableTypeDescriptionCode(context))

    getGotoCode(context.getExceptionEscape(), emit)

    if context.needsCleanup(raise_type_name):
        context.removeCleanupTempName(raise_type_name)
    if context.needsCleanup(raise_value_name):
        context.removeCleanupTempName(raise_value_name)
    if context.needsCleanup(raise_tb_name):
        context.removeCleanupTempName(raise_tb_name)


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
