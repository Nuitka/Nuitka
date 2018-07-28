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
""" Code to generate and interact with compiled coroutine objects.

"""

from .CodeHelpers import (
    generateChildExpressionsCode,
    generateStatementSequenceCode
)
from .Emission import SourceCodeCollector
from .ErrorCodes import getErrorExitCode
from .FunctionCodes import (
    finalizeFunctionLocalVariables,
    setupFunctionLocalVariables
)
from .GeneratorCodes import getClosureCopyCode
from .Indentation import indented
from .LineNumberCodes import emitLineNumberUpdateCode
from .PythonAPICodes import getReferenceExportCode
from .templates.CodeTemplatesCoroutines import (
    template_coroutine_exception_exit,
    template_coroutine_noexception_exit,
    template_coroutine_object_body_template,
    template_coroutine_object_decl_template,
    template_coroutine_return_exit,
    template_make_coroutine_template
)


def getCoroutineObjectDeclCode(function_identifier):
    return template_coroutine_object_decl_template % {
        "function_identifier" : function_identifier,
    }


def getCoroutineObjectCode(context, function_identifier, closure_variables,
                           user_variables, outline_variables,
                           temp_variables, needs_exception_exit,
                           needs_generator_return):
    function_locals, function_cleanup = setupFunctionLocalVariables(
        context           = context,
        parameters        = None,
        closure_variables = closure_variables,
        user_variables    = user_variables + outline_variables,
        temp_variables    = temp_variables
    )

    function_codes = SourceCodeCollector()

    generateStatementSequenceCode(
        statement_sequence = context.getOwner().getBody(),
        allow_none         = True,
        emit               = function_codes,
        context            = context
    )

    finalizeFunctionLocalVariables(context, function_locals, function_cleanup)

    if needs_exception_exit:
        generator_exit = template_coroutine_exception_exit % {
            "function_identifier" : function_identifier,
            "function_cleanup"    : indented(function_cleanup)
        }
    else:
        generator_exit = template_coroutine_noexception_exit % {
            "function_identifier" : function_identifier,
            "function_cleanup"    : indented(function_cleanup)
        }

    if needs_generator_return:
        generator_exit += template_coroutine_return_exit % {}

    return template_coroutine_object_body_template % {
        "function_identifier" : function_identifier,
        "function_body"       : indented(function_codes.codes),
        "function_var_inits"  : indented(function_locals),
        "coroutine_exit"      : generator_exit
    }


def generateMakeCoroutineObjectCode(to_name, expression, emit, context):
    coroutine_object_body = expression.getCoroutineRef().getFunctionBody()

    closure_variables = expression.getClosureVariableVersions()

    closure_copy = getClosureCopyCode(
        to_name           = to_name,
        closure_type      = "struct Nuitka_CoroutineObject *",
        closure_variables = closure_variables,
        context           = context
    )

    emit(
        template_make_coroutine_template % {
            "closure_copy"         : indented(closure_copy, 0, True),
            "coroutine_identifier" : coroutine_object_body.getCodeName(),
            "to_name"              : to_name,
            "code_identifier"      : context.getCodeObjectHandle(
                code_object = expression.getCodeObject(),
            ),
            "closure_count"        : len(closure_variables)
        }
    )

    context.addCleanupTempName(to_name)


def generateAsyncWaitCode(to_name, expression, emit, context):
    emitLineNumberUpdateCode(emit, context)

    value_name, = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    # In handlers, we must preserve/restore the exception.
    preserve_exception = expression.isExceptionPreserving()

    context_identifier = context.getContextObjectName()

    # This produces AWAIT_COROUTINE or AWAIT_ASYNCGEN calls.
    getReferenceExportCode(value_name, emit, context)

    if expression.isExpressionAsyncWaitEnter():
        wait_kind = "await_enter"
    elif expression.isExpressionAsyncWaitExit():
        wait_kind = "await_exit"
    else:
        wait_kind = "await_normal"

    emit(
        "%s = %s_%s( %s, %s, %s );" % (
            to_name,
            context_identifier.upper(),
            "AWAIT"
              if not preserve_exception else
            "AWAIT_IN_HANDLER",
            context_identifier,
            value_name,
            wait_kind
        )
    )

    if not context.needsCleanup(value_name):
        context.addCleanupTempName(value_name)

    getErrorExitCode(
        check_name   = to_name,
        release_name = value_name,
        emit         = emit,
        context      = context
    )

    context.addCleanupTempName(to_name)


def generateAsyncIterCode(to_name, expression, emit, context):
    value_name, = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    emit(
        "%s = %s_ASYNC_MAKE_ITERATOR( %s, %s );" % (
            to_name,
            context.getContextObjectName().upper(),
            context.getContextObjectName(),
            value_name
        )
    )

    getErrorExitCode(
        check_name   = to_name,
        release_name = value_name,
        emit         = emit,
        context      = context
    )

    context.addCleanupTempName(to_name)


def generateAsyncNextCode(to_name, expression, emit, context):
    value_name, = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    emit(
        "%s = %s_ASYNC_ITERATOR_NEXT( %s, %s );" % (
            to_name,
            context.getContextObjectName().upper(),
            context.getContextObjectName(),
            value_name,
        )
    )

    getErrorExitCode(
        check_name      = to_name,
        release_name    = value_name,
        quick_exception = "StopAsyncIteration",
        emit            = emit,
        context         = context
    )

    context.addCleanupTempName(to_name)
