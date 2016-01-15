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
""" Code to generate and interact with compiled coroutine objects.

"""

from .ErrorCodes import (
    getErrorExitCode,
    getErrorVariableDeclarations,
    getExceptionKeeperVariableNames,
    getExceptionPreserverVariableNames,
    getReleaseCode
)
from .Helpers import generateChildExpressionsCode
from .Indentation import indented
from .templates.CodeTemplatesCoroutines import (
    template_coroutine_exception_exit,
    template_coroutine_noexception_exit,
    template_coroutine_object_body_template,
    template_coroutine_object_decl_template,
    template_coroutine_return_exit,
    template_make_coroutine_with_context_template,
    template_make_coroutine_without_context_template
)
from .templates.CodeTemplatesFunction import (
    function_dict_setup,
    template_function_closure_making
)
from .VariableCodes import getLocalVariableInitCode, getVariableCode


def getCoroutineObjectDeclCode(function_identifier):
    return template_coroutine_object_decl_template % {
        "function_identifier" : function_identifier,
    }


def getCoroutineObjectCode(context, function_identifier, user_variables,
                           temp_variables, function_codes, needs_exception_exit,
                           needs_generator_return):
    function_locals = []

    for user_variable in user_variables + temp_variables:
        function_locals.append(
            getLocalVariableInitCode(
                variable = user_variable,
            )
        )

    if context.hasLocalsDict():
        function_locals += function_dict_setup.split('\n')

    if context.needsExceptionVariables():
        function_locals.extend(getErrorVariableDeclarations())

    for keeper_index in range(1, context.getKeeperVariableCount()+1):
        function_locals.extend(getExceptionKeeperVariableNames(keeper_index))

    for preserver_id in context.getExceptionPreserverCounts():
        function_locals.extend(getExceptionPreserverVariableNames(preserver_id))

    function_locals += [
        "%s%s%s;" % (
            tmp_type,
            ' ' if not tmp_type.endswith('*') else "",
            tmp_name
        )
        for tmp_name, tmp_type in
        context.getTempNameInfos()
    ]

    function_locals += context.getFrameDeclarations()

    # TODO: Could avoid this unless try/except or try/finally with returns
    # occur.
    if context.hasTempName("generator_return"):
        function_locals.append("tmp_generator_return = false;")
    if context.hasTempName("return_value"):
        function_locals.append("tmp_return_value = NULL;")
    for tmp_name, tmp_type in context.getTempNameInfos():
        if tmp_name.startswith("tmp_outline_return_value_"):
            function_locals.append("%s = NULL;" % tmp_name)

    if needs_exception_exit:
        generator_exit = template_coroutine_exception_exit % {
            "function_identifier" : function_identifier,
        }
    else:
        generator_exit = template_coroutine_noexception_exit % {
            "function_identifier" : function_identifier,
        }

    if needs_generator_return:
        generator_exit += template_coroutine_return_exit % {}

    return template_coroutine_object_body_template % {
        "function_identifier" : function_identifier,
        "function_body"       : indented(function_codes),
        "function_var_inits"  : indented(function_locals),
        "coroutine_exit"      : generator_exit
    }


def generateMakeCoroutineObjectCode(to_name, expression, emit, context):
    coroutine_object_body = expression.getCoroutineRef().getFunctionBody()

    closure_variables = coroutine_object_body.getClosureVariables()

    code_identifier = context.getCodeObjectHandle(
        code_object  = expression.getCodeObject(),
        filename     = coroutine_object_body.getParentModule().getRunTimeFilename(),
        line_number  = coroutine_object_body.getSourceReference().getLineNumber(),
        is_optimized = True,
        new_locals   = not coroutine_object_body.needsLocalsDict(),
        has_closure  = len(closure_variables) > 0,
        future_flags = coroutine_object_body.getSourceReference().getFutureSpec().asFlags()
    )

    if closure_variables:
        # TODO: Copy duplication with generator codes, ought to be shared.
        closure_copy = []

        for count, variable in enumerate(closure_variables):
            variable_code = getVariableCode(
                context  = context,
                variable = variable
            )

            # Generators might not use them, but they still need to be put there.
            # TODO: But they don't have to be cells.
            if not variable.isSharedTechnically():
                closure_copy.append(
                    "closure[%d] = PyCell_NEW0( %s );" % (
                        count,
                        variable_code
                    )
                )
            else:
                closure_copy.append(
                    "closure[%d] = %s;" % (
                        count,
                        variable_code
                    )
                )
                closure_copy.append(
                    "Py_INCREF( closure[%d] );" % count
                )

        closure_making = template_function_closure_making % {
            "closure_copy"  : indented(closure_copy),
            "closure_count" : len(closure_variables)
        }

        emit(
            template_make_coroutine_with_context_template % {
                "closure_making"       : closure_making,
                "coroutine_identifier" : coroutine_object_body.getCodeName(),
                "to_name"              : to_name,
                "code_identifier"      : code_identifier,
                "closure_count"        : len(closure_variables)
            }
        )
    else:
        emit(
            template_make_coroutine_without_context_template % {
                "coroutine_identifier" : coroutine_object_body.getCodeName(),
                "to_name"              : to_name,
                "code_identifier"      : code_identifier,
            }
        )

    context.addCleanupTempName(to_name)


def generateAsyncWaitCode(to_name, expression, emit, context):
    value_name, = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    emit(
        "%s = %s( coroutine, %s );" % (
            to_name,
            "AWAIT_COROUTINE",
            value_name
              if context.needsCleanup(value_name) else
            "INCREASE_REFCOUNT( %s )" % value_name
        )
    )

    if not context.needsCleanup(value_name):
        context.addCleanupTempName(value_name)

    getReleaseCode(
        release_name = value_name,
        emit         = emit,
        context      = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def generateAsyncIterCode(to_name, expression, emit, context):
    value_name, = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    emit(
        "%s = MAKE_ASYNC_ITERATOR( coroutine, %s );" % (
            to_name,
            value_name
        )
    )

    getReleaseCode(
        release_name = value_name,
        emit         = emit,
        context      = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def generateAsyncNextCode(to_name, expression, emit, context):
    value_name, = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    emit(
        "%s = ASYNC_ITERATOR_NEXT( coroutine, %s );" % (
            to_name,
            value_name,
        )
    )

    getReleaseCode(
        release_name = value_name,
        emit         = emit,
        context      = context
    )

    getErrorExitCode(
        check_name      = to_name,
        quick_exception = "StopAsyncIteration",
        emit            = emit,
        context         = context
    )

    context.addCleanupTempName(to_name)
