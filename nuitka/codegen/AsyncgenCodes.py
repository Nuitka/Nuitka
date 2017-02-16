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

from .ErrorCodes import (
    getErrorVariableDeclarations,
    getExceptionKeeperVariableNames,
    getExceptionPreserverVariableNames
)
from .Indentation import indented
from .templates.CodeTemplatesAsyncgens import (
    template_asyncgen_exception_exit,
    template_asyncgen_noexception_exit,
    template_asyncgen_object_body_template,
    template_asyncgen_object_decl_template,
    template_asyncgen_return_exit,
    template_make_asyncgen_template
)
from .templates.CodeTemplatesFunction import function_dict_setup
from .VariableCodes import getLocalVariableCodeType, getLocalVariableInitCode


def getAsyncgenObjectDeclCode(function_identifier):
    return template_asyncgen_object_decl_template % {
        "function_identifier" : function_identifier,
    }


def getAsyncgenObjectCode(context, function_identifier, user_variables,
                           temp_variables, function_codes, needs_exception_exit,
                           needs_generator_return):
    function_locals = []

    for user_variable in user_variables + temp_variables:
        function_locals.append(
            getLocalVariableInitCode(
                context  = context,
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
        "function_body"       : indented(function_codes),
        "function_var_inits"  : indented(function_locals),
        "asyncgen_exit"      : generator_exit
    }


def generateMakeAsyncgenObjectCode(to_name, expression, emit, context):
    asyncgen_object_body = expression.getAsyncgenRef().getFunctionBody()

    closure_variables = asyncgen_object_body.getClosureVariables()

    code_identifier = context.getCodeObjectHandle(
        code_object  = expression.getCodeObject(),
        filename     = asyncgen_object_body.getParentModule().getRunTimeFilename(),
        line_number  = asyncgen_object_body.getSourceReference().getLineNumber(),
        is_optimized = True,
        new_locals   = not asyncgen_object_body.needsLocalsDict(),
        has_closure  = len(asyncgen_object_body.getParentVariableProvider().getClosureVariables()) > 0,
        future_flags = asyncgen_object_body.getSourceReference().getFutureSpec().asFlags()
    )

    # TODO: Copy duplication with generator codes, ought to be shared.
    closure_copy = []

    for count, variable in enumerate(closure_variables):
        variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable)

        # Asyncgens might not use them, but they still need to be put there.
        # TODO: But they don't have to be cells.
        if variable_c_type == "PyObject *":
            closure_copy.append(
                "((struct Nuitka_AsyncgenObject *)%s)->m_closure[%d] = PyCell_NEW0( %s );" % (
                    to_name,
                    count,
                    variable_code_name
                )
            )
        elif variable_c_type == "struct Nuitka_CellObject *":
            closure_copy.append(
                "((struct Nuitka_AsyncgenObject *)%s)->m_closure[%d] = %s;" % (
                    to_name,
                    count,
                    variable_code_name
                )
            )
            closure_copy.append(
                "Py_INCREF( ((struct Nuitka_AsyncgenObject *)%s)->m_closure[%d] );" % (
                    to_name,
                    count
                )
            )
        else:
            assert False, variable

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
