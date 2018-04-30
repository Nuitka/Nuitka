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
""" Code to generate and interact with compiled asyncgen objects.

"""

from .CodeHelpers import generateStatementSequenceCode
from .Emission import SourceCodeCollector
from .FunctionCodes import (
    finalizeFunctionLocalVariables,
    setupFunctionLocalVariables
)
from .GeneratorCodes import getClosureCopyCode
from .Indentation import indented
from .templates.CodeTemplatesAsyncgens import (
    template_asyncgen_exception_exit,
    template_asyncgen_noexception_exit,
    template_asyncgen_object_body_template,
    template_asyncgen_object_decl_template,
    template_asyncgen_return_exit,
    template_make_asyncgen_template
)


def getAsyncgenObjectDeclCode(function_identifier):
    return template_asyncgen_object_decl_template % {
        "function_identifier" : function_identifier,
    }


def getAsyncgenObjectCode(context, function_identifier, closure_variables,
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
        generator_exit = template_asyncgen_exception_exit % {
            "function_identifier" : function_identifier,
            "function_cleanup"    : indented(function_cleanup)
        }
    else:
        generator_exit = template_asyncgen_noexception_exit % {
            "function_identifier" : function_identifier,
            "function_cleanup"    : indented(function_cleanup)
        }

    if needs_generator_return:
        generator_exit += template_asyncgen_return_exit % {}

    return template_asyncgen_object_body_template % {
        "function_identifier" : function_identifier,
        "function_body"       : indented(function_codes.codes),
        "function_var_inits"  : indented(function_locals),
        "asyncgen_exit"      : generator_exit
    }


def generateMakeAsyncgenObjectCode(to_name, expression, emit, context):
    asyncgen_object_body = expression.getAsyncgenRef().getFunctionBody()

    closure_variables = expression.getClosureVariableVersions()

    closure_copy = getClosureCopyCode(
        to_name           = to_name,
        closure_type      = "struct Nuitka_AsyncgenObject *",
        closure_variables = closure_variables,
        context           = context
    )

    emit(
        template_make_asyncgen_template % {
            "closure_copy"          : indented(closure_copy, 0, True),
            "to_name"               : to_name,
            "asyncgen_identifier"   : asyncgen_object_body.getCodeName(),
            "asyncgen_name_obj"     : context.getConstantCode(
                constant = asyncgen_object_body.getFunctionName()
            ),
            "asyncgen_qualname_obj" : context.getConstantCode(
                constant = asyncgen_object_body.getFunctionQualname()
            ),
            "code_identifier"       : context.getCodeObjectHandle(
                code_object = expression.getCodeObject(),
            ),
            "closure_count"         : len(closure_variables)
        }
    )

    context.addCleanupTempName(to_name)
