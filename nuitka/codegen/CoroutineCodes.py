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
""" Code to generate and interact with compiled coroutine objects.

"""

from .Indentation import indented
from .PythonAPICodes import generateCAPIObjectCode
from .templates.CodeTemplatesCoroutines import (
    template_make_coroutine_with_context_template,
    template_make_coroutine_without_context_template
)
from .templates.CodeTemplatesFunction import (
    template_function_closure_making
)
from .VariableCodes import getVariableCode


def generateAwaitCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "AWAIT_COROUTINE",
        arg_desc   = (
            ("await_arg", expression.getValue()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )


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
                variable_code = "PyCell_NEW0( %s )" % variable_code

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
