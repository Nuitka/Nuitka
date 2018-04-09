#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Code generation for implicit and explicit exception raises.

Exceptions from other operations are consider ErrorCodes domain.

"""

from nuitka.Options import isDebug

from .CodeHelpers import generateChildExpressionsCode, generateExpressionCode
from .ErrorCodes import getFrameVariableTypeDescriptionCode
from .LabelCodes import getGotoCode
from .LineNumberCodes import (
    emitErrorLineNumberUpdateCode,
    getErrorLineNumberUpdateCode
)
from .PythonAPICodes import getReferenceExportCode


def generateReraiseCode(statement, emit, context):
    context.markAsNeedsExceptionVariables()

    old_source_ref = context.setCurrentSourceCodeReference(
        value = statement.getCompatibleSourceReference()
    )

    getReRaiseExceptionCode(
        emit    = emit,
        context = context
    )

    context.setCurrentSourceCodeReference(old_source_ref)


def generateRaiseCode(statement, emit, context):
    exception_type  = statement.getExceptionType()
    exception_value = statement.getExceptionValue()
    exception_tb    = statement.getExceptionTrace()
    exception_cause = statement.getExceptionCause()

    context.markAsNeedsExceptionVariables()

    # Exception cause is only possible with simple raise form.
    if exception_cause is not None:
        assert exception_type is not None
        assert exception_value is None
        assert exception_tb is None

        raise_type_name  = context.allocateTempName("raise_type")

        generateExpressionCode(
            to_name    = raise_type_name,
            expression = exception_type,
            emit       = emit,
            context    = context
        )

        raise_cause_name  = context.allocateTempName("raise_cause")

        generateExpressionCode(
            to_name    = raise_cause_name,
            expression = exception_cause,
            emit       = emit,
            context    = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(exception_cause.getSourceReference())

        getRaiseExceptionWithCauseCode(
            raise_type_name  = raise_type_name,
            raise_cause_name = raise_cause_name,
            emit             = emit,
            context          = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)
    elif exception_type is None:
        assert False, statement
    elif exception_value is None and exception_tb is None:
        raise_type_name  = context.allocateTempName("raise_type")

        generateExpressionCode(
            to_name    = raise_type_name,
            expression = exception_type,
            emit       = emit,
            context    = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(
            value = exception_type.getCompatibleSourceReference()
        )

        getRaiseExceptionWithTypeCode(
            raise_type_name = raise_type_name,
            emit            = emit,
            context         = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)
    elif exception_tb is None:
        raise_type_name  = context.allocateTempName("raise_type")

        generateExpressionCode(
            to_name    = raise_type_name,
            expression = exception_type,
            emit       = emit,
            context    = context
        )

        raise_value_name  = context.allocateTempName("raise_value")

        generateExpressionCode(
            to_name    = raise_value_name,
            expression = exception_value,
            emit       = emit,
            context    = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(exception_value.getSourceReference())

        context.setCurrentSourceCodeReference(
            statement.getCompatibleSourceReference()
        )

        getRaiseExceptionWithValueCode(
            raise_type_name  = raise_type_name,
            raise_value_name = raise_value_name,
            implicit         = statement.isStatementRaiseExceptionImplicit(),
            emit             = emit,
            context          = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)
    else:
        raise_type_name  = context.allocateTempName("raise_type")

        generateExpressionCode(
            to_name    = raise_type_name,
            expression = exception_type,
            emit       = emit,
            context    = context
        )

        raise_value_name  = context.allocateTempName("raise_value")

        generateExpressionCode(
            to_name    = raise_value_name,
            expression = exception_value,
            emit       = emit,
            context    = context
        )

        raise_tb_name = context.allocateTempName("raise_tb")

        generateExpressionCode(
            to_name    = raise_tb_name,
            expression = exception_tb,
            emit       = emit,
            context    = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(exception_tb.getSourceReference())

        getRaiseExceptionWithTracebackCode(
            raise_type_name  = raise_type_name,
            raise_value_name = raise_value_name,
            raise_tb_name    = raise_tb_name,
            emit             = emit,
            context          = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)


def generateRaiseExpressionCode(to_name, expression, emit, context):
    arg_names = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    # Missed optimization opportunity, please report it, this should not
    # normally happen. We are supposed to propagate this upwards.
    if isDebug():
        # TODO: Need to optimize ExpressionLocalsVariableRefORFallback once we know
        # it handles cases where the value is not in locals dict properly.

        parent = expression.parent
        assert parent.isExpressionSideEffects() or \
               parent.isExpressionConditional() or \
               parent.isExpressionLocalsVariableRefORFallback(), \
               (expression, expression.parent, expression.asXmlText())

    # That's how we indicate exception to the surrounding world.
    emit("%s = NULL;" % to_name)

    getRaiseExceptionWithValueCode(
        raise_type_name  = arg_names[0],
        raise_value_name = arg_names[1],
        implicit         = True,
        emit             = emit,
        context          = context
    )


def getReRaiseExceptionCode(emit, context):
    keeper_variables = context.getExceptionKeeperVariables()

    if keeper_variables[0] is None:
        emit(
            """\
%(bool_res_name)s = RERAISE_EXCEPTION( &exception_type, &exception_value, &exception_tb );
if (unlikely( %(bool_res_name)s == false ))
{
    %(update_code)s
}
""" % {
                "bool_res_name" : context.getBoolResName(),
                "update_code"   : getErrorLineNumberUpdateCode(context)

            }
        )

        frame_handle = context.getFrameHandle()

        if frame_handle:
            emit(
                """\
if (exception_tb && exception_tb->tb_frame == &%(frame_identifier)s->m_frame) \
%(frame_identifier)s->m_frame.f_lineno = exception_tb->tb_lineno;""" % {
                    "frame_identifier" : context.getFrameHandle()
                }
            )

            emit(
                getFrameVariableTypeDescriptionCode(context)
            )
    else:
        keeper_type, keeper_value, keeper_tb, keeper_lineno = context.getExceptionKeeperVariables()

        emit(
            """\
// Re-raise.
exception_type = %(keeper_type)s;
exception_value = %(keeper_value)s;
exception_tb = %(keeper_tb)s;
exception_lineno = %(keeper_lineno)s;
""" %  {
            "keeper_type"        : keeper_type,
            "keeper_value"       : keeper_value,
            "keeper_tb"          : keeper_tb,
            "keeper_lineno"      : keeper_lineno
            }
        )

    getGotoCode(context.getExceptionEscape(), emit)


def getRaiseExceptionWithCauseCode(raise_type_name, raise_cause_name, emit,
                                   context):
    context.markAsNeedsExceptionVariables()

    emit(
        "exception_type = %s;" % raise_type_name
    )
    getReferenceExportCode(raise_type_name, emit, context)

    emit("exception_value = NULL;")

    getReferenceExportCode(raise_cause_name, emit, context)

    emitErrorLineNumberUpdateCode(emit, context)
    emit(
        """\
RAISE_EXCEPTION_WITH_CAUSE( &exception_type, &exception_value, &exception_tb, \
%s );""" % raise_cause_name
    )

    emit(
        getFrameVariableTypeDescriptionCode(context)
    )

    getGotoCode(context.getExceptionEscape(), emit)

    if context.needsCleanup(raise_type_name):
        context.removeCleanupTempName(raise_type_name)
    if context.needsCleanup(raise_cause_name):
        context.removeCleanupTempName(raise_cause_name)


def getRaiseExceptionWithTypeCode(raise_type_name, emit, context):
    context.markAsNeedsExceptionVariables()

    emit(
        "exception_type = %s;" % raise_type_name
    )
    getReferenceExportCode(raise_type_name, emit, context)

    emitErrorLineNumberUpdateCode(emit, context)
    emit(
        "RAISE_EXCEPTION_WITH_TYPE( &exception_type, &exception_value, &exception_tb );"
    )

    emit(
        getFrameVariableTypeDescriptionCode(context)
    )

    getGotoCode(context.getExceptionEscape(), emit)

    if context.needsCleanup(raise_type_name):
        context.removeCleanupTempName(raise_type_name)


def getRaiseExceptionWithValueCode(raise_type_name, raise_value_name, implicit,
                                   emit, context):
    emit(
        "exception_type = %s;" % raise_type_name
    )
    getReferenceExportCode(raise_type_name, emit, context)
    emit(
        "exception_value = %s;" % raise_value_name
    )
    getReferenceExportCode(raise_value_name, emit, context)

    emitErrorLineNumberUpdateCode(emit, context)
    emit(
        "RAISE_EXCEPTION_%s( &exception_type, &exception_value, &exception_tb );" % (
            ("IMPLICIT" if implicit else "WITH_VALUE")
        )
    )

    emit(
        getFrameVariableTypeDescriptionCode(context)
    )

    getGotoCode(context.getExceptionEscape(), emit)

    if context.needsCleanup(raise_type_name):
        context.removeCleanupTempName(raise_type_name)
    if context.needsCleanup(raise_value_name):
        context.removeCleanupTempName(raise_value_name)


def getRaiseExceptionWithTracebackCode(raise_type_name, raise_value_name,
                                       raise_tb_name, emit, context):
    emit(
        "exception_type = %s;" % raise_type_name
    )
    getReferenceExportCode(raise_type_name, emit, context)
    emit(
        "exception_value = %s;" % raise_value_name
    )
    getReferenceExportCode(raise_value_name, emit, context)
    emit(
        "exception_tb = (PyTracebackObject *)%s;" % raise_tb_name
    )
    getReferenceExportCode(raise_tb_name, emit, context)

    emit(
        "RAISE_EXCEPTION_WITH_TRACEBACK( &exception_type, &exception_value, &exception_tb);"
    )

    # If anything is wrong, that will be used.
    emitErrorLineNumberUpdateCode(emit, context)

    emit(
        getFrameVariableTypeDescriptionCode(context)
    )

    getGotoCode(context.getExceptionEscape(), emit)

    if context.needsCleanup(raise_type_name):
        context.removeCleanupTempName(raise_type_name)
    if context.needsCleanup(raise_value_name):
        context.removeCleanupTempName(raise_value_name)
    if context.needsCleanup(raise_tb_name):
        context.removeCleanupTempName(raise_tb_name)
