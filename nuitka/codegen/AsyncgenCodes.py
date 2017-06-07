#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .Emission import SourceCodeCollector
from .FunctionCodes import (
    finalizeFunctionLocalVariables,
    setupFunctionLocalVariables
)
from .GeneratorCodes import getClosureCopyCode
from .Helpers import generateStatementSequenceCode
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
                          user_variables, temp_variables, needs_exception_exit,
                          needs_generator_return):
    function_locals, function_cleanup = setupFunctionLocalVariables(
        context           = context,
        parameters        = None,
        closure_variables = closure_variables,
        user_variables    = user_variables,
        temp_variables    = temp_variables
    )

    # Doesn't apply to asyncgens.
    assert not function_cleanup

    function_codes = SourceCodeCollector()

    generateStatementSequenceCode(
        statement_sequence = context.getOwner().getBody(),
        allow_none         = True,
        emit               = function_codes,
        context            = context
    )

    function_locals += finalizeFunctionLocalVariables(context)

    if needs_exception_exit:
        generator_exit = template_asyncgen_exception_exit % {
            "function_identifier" : function_identifier,
        }
    else:
        generator_exit = template_asyncgen_noexception_exit % {
            "function_identifier" : function_identifier,
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

    parent_module = asyncgen_object_body.getParentModule()

    code_identifier = context.getCodeObjectHandle(
        code_object  = expression.getCodeObject(),
        filename     = parent_module.getRunTimeFilename(),
        line_number  = asyncgen_object_body.getSourceReference().getLineNumber(),
        is_optimized = True,
        new_locals   = not asyncgen_object_body.needsLocalsDict(),
        has_closure  = len(asyncgen_object_body.getParentVariableProvider().getClosureVariables()) > 0,
        future_flags = parent_module.getFutureSpec().asFlags()
    )

    closure_variables = expression.getClosureVariableVersions()

    closure_copy = getClosureCopyCode(
        to_name           = to_name,
        closure_type      = "struct Nuitka_AsyncgenObject *",
        closure_variables = closure_variables,
        context           = context
    )

    emit(
        template_make_asyncgen_template % {
            "closure_copy"        : indented(closure_copy, 0, True),
            "asyncgen_identifier" : asyncgen_object_body.getCodeName(),
            "to_name"             : to_name,
            "code_identifier"     : code_identifier,
            "closure_count"       : len(closure_variables)
        }
    )

    context.addCleanupTempName(to_name)
