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
""" Code to generate and interact with compiled function objects.

"""

from nuitka.PythonVersions import python_version

from .Emission import SourceCodeCollector
from .FunctionCodes import (
    finalizeFunctionLocalVariables,
    setupFunctionLocalVariables
)
from .Helpers import generateStatementSequenceCode
from .Indentation import indented
from .ModuleCodes import getModuleAccessCode
from .templates.CodeTemplatesGeneratorFunction import (
    template_generator_exception_exit,
    template_generator_making,
    template_generator_noexception_exit,
    template_generator_return_exit,
    template_genfunc_yielder_body_template,
    template_genfunc_yielder_decl_template
)
from .VariableCodes import getLocalVariableCodeType


def getGeneratorObjectDeclCode(function_identifier):
    return template_genfunc_yielder_decl_template % {
        "function_identifier" : function_identifier,
    }


def getGeneratorObjectCode(context, function_identifier, closure_variables,
                           user_variables, temp_variables, needs_exception_exit,
                           needs_generator_return):
    function_locals, function_cleanup = setupFunctionLocalVariables(
        context           = context,
        parameters        = None,
        closure_variables = closure_variables,
        user_variables    = user_variables,
        temp_variables    = temp_variables
    )

    function_codes = SourceCodeCollector()

    generateStatementSequenceCode(
        statement_sequence = context.getOwner().getBody(),
        allow_none         = True,
        emit               = function_codes,
        context            = context
    )

    function_locals += finalizeFunctionLocalVariables(context)

    if needs_exception_exit:
        generator_exit = template_generator_exception_exit % {
            "function_cleanup" : function_cleanup
        }
    else:
        generator_exit = template_generator_noexception_exit % {
            "function_cleanup" : function_cleanup
        }

    if needs_generator_return:
        generator_exit += template_generator_return_exit % {}

    return template_genfunc_yielder_body_template % {
        "function_identifier" : function_identifier,
        "function_body"       : indented(function_codes.codes),
        "function_var_inits"  : indented(function_locals),
        "generator_exit"      : generator_exit
    }


def getClosureCopyCode(to_name, closure_variables, closure_type, context):
    """ Get code to copy closure variables storage.

    This gets used by generator/coroutine/asyncgen with varying "closure_type".
    """
    closure_copy = []

    for count, (variable, version) in enumerate(closure_variables):
        variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, version)

        target_cell_code = "((%s)%s)->m_closure[%d]" % (
            closure_type,
            to_name,
            count
        )

        variable_c_type.getCellObjectAssignmentCode(
            target_cell_code   = target_cell_code,
            variable_code_name = variable_code_name,
            emit               = closure_copy.append
        )

    closure_copy.append(
        "assert( Py_SIZE( %s) >= %s ); " % (
            to_name,
            len(closure_variables)
        )
    )

    return closure_copy


def generateMakeGeneratorObjectCode(to_name, expression, emit, context):
    generator_object_body = expression.getGeneratorRef().getFunctionBody()

    if python_version < 350 or context.isForDirectCall():
        generator_name_obj = context.getConstantCode(
            constant = generator_object_body.getFunctionName()
        )
    else:
        generator_name_obj = "self->m_name"

    if python_version < 350:
        generator_qualname_obj = "NULL"
    elif not context.isForDirectCall():
        generator_qualname_obj = "self->m_qualname"
    else:
        generator_qualname_obj = context.getConstantCode(
            constant = generator_object_body.getFunctionQualname()
        )

    parent_module = generator_object_body.getParentModule()

    code_identifier = context.getCodeObjectHandle(
        code_object  = expression.getCodeObject(),
        filename     = parent_module.getRunTimeFilename(),
        line_number  = generator_object_body.getSourceReference().getLineNumber(),
        is_optimized = True,
        new_locals   = not generator_object_body.needsLocalsDict(),
        has_closure  = len(generator_object_body.getParentVariableProvider().getClosureVariables()) > 0,
        future_flags = parent_module.getFutureSpec().asFlags()
    )

    closure_variables = expression.getClosureVariableVersions()

    closure_copy = getClosureCopyCode(
        to_name           = to_name,
        closure_type      = "struct Nuitka_GeneratorObject *",
        closure_variables = closure_variables,
        context           = context
    )

    emit(
        template_generator_making % {
            "closure_copy"           : indented(closure_copy, 0, True),
            "to_name"                : to_name,
            "generator_identifier"   : generator_object_body.getCodeName(),
            "generator_module"       : getModuleAccessCode(context),
            "generator_name_obj"     : generator_name_obj,
            "generator_qualname_obj" : generator_qualname_obj,
            "code_identifier"        : code_identifier,
            "closure_count"          : len(closure_variables)
        }
    )

    context.addCleanupTempName(to_name)
