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
""" Code to generate and interact with compiled module objects.

"""

from nuitka.Version import getNuitkaVersion, getNuitkaVersionYear

from .CodeObjectCodes import getCodeObjectsDeclCode, getCodeObjectsInitCode
from .ConstantCodes import allocateNestedConstants, getConstantInitCodes
from .Indentation import indented
from .templates.CodeTemplatesModules import (
    template_global_copyright,
    template_module_body_template,
    template_module_exception_exit,
    template_module_noexception_exit
)
from .VariableCodes import generateModuleVariableAccessCode


def getModuleAccessCode(context):
    return "module_%s" % context.getModuleCodeName()


def getModuleValues(context, module_name, module_identifier, codes,
                    function_decl_codes, function_body_codes, outline_variables,
                    temp_variables, is_main_module, is_internal_module,
                    is_package):
    # For the module code, lots of arguments and attributes come together.
    # pylint: disable=too-many-locals

    # Temporary variable initializations
    # TODO: Move that to a place outside of functions.
    from .FunctionCodes import setupFunctionLocalVariables, finalizeFunctionLocalVariables
    local_var_inits, cleanup = setupFunctionLocalVariables(
        context           = context,
        parameters        = None,
        closure_variables = (),
        user_variables    = outline_variables,
        temp_variables    = temp_variables
    )

    finalizeFunctionLocalVariables(context, local_var_inits, cleanup)

    if context.needsExceptionVariables():
        module_exit = template_module_exception_exit
    else:
        module_exit = template_module_noexception_exit

    module_body_template_values = {
        "module_name"              : module_name,
        "module_name_obj"          : context.getConstantCode(
            constant = module_name
        ),
        "is_main_module"           : 1 if is_main_module else 0,
        "is_package"               : 1 if is_package else 0,
        "module_identifier"        : module_identifier,
        "module_functions_decl"    : function_decl_codes,
        "module_functions_code"    : function_body_codes,
        "temps_decl"               : indented(local_var_inits),
        "module_code"              : indented(codes),
        "module_exit"              : module_exit,
        "module_code_objects_decl" : indented(
            getCodeObjectsDeclCode(context),
            0
        ),
        "module_code_objects_init" : indented(
            getCodeObjectsInitCode(context),
            1
        )
    }

    allocateNestedConstants(context)

    # Force internal module to not need constants init, by making all its
    # constants be shared.
    if is_internal_module:
        for constant in context.getConstants():
            context.global_context.countConstantUse(constant)

    return module_body_template_values


def getModuleCode(module_context, template_values):
    header = template_global_copyright % {
        "name"    : module_context.getName(),
        "version" : getNuitkaVersion(),
        "year"    : getNuitkaVersionYear()
    }

    decls, inits, checks = getConstantInitCodes(module_context)

    if module_context.needsModuleFilenameObject():
        decls.append("static PyObject *module_filename_obj;")

    template_values["constant_decl_codes"] = indented(
        decls,
        0
    )

    template_values["constant_init_codes"] = indented(
        inits,
        1
    )

    template_values["constant_check_codes"] = indented(
        checks,
        1
    )

    return header + template_module_body_template % template_values


def generateModuleAttributeFileCode(to_name, expression, emit, context):
    # The expression doesn't really matter, but it is part of the API for
    # the expression registry, pylint: disable=unused-argument

    emit(
        "%s = module_filename_obj;" % (
            to_name,
        )
    )

    context.markAsNeedsModuleFilenameObject()


def generateModuleAttributeNameCode(to_name, expression, emit, context):
    # The expression doesn't really matter, but it is part of the API for
    # the expression registry, pylint: disable=unused-argument
    generateModuleVariableAccessCode(
        to_name       = to_name,
        variable_name = "__name__",
        needs_check   = False,
        emit          = emit,
        context       = context

    )


def generateModuleAttributePackageCode(to_name, expression, emit, context):
    # The expression doesn't really matter, but it is part of the API for
    # the expression registry, pylint: disable=unused-argument
    generateModuleVariableAccessCode(
        to_name       = to_name,
        variable_name = "__package__",
        needs_check   = False,
        emit          = emit,
        context       = context
    )


def generateModuleAttributeLoaderCode(to_name, expression, emit, context):
    # The expression doesn't really matter, but it is part of the API for
    # the expression registry, pylint: disable=unused-argument

    generateModuleVariableAccessCode(
        to_name       = to_name,
        variable_name = "__loader__",
        needs_check   = False,
        emit          = emit,
        context       = context
    )


def generateModuleAttributeSpecCode(to_name, expression, emit, context):
    # The expression doesn't really matter, but it is part of the API for
    # the expression registry, pylint: disable=unused-argument

    generateModuleVariableAccessCode(
        to_name       = to_name,
        variable_name = "__spec__",
        needs_check   = False,
        emit          = emit,
        context       = context
    )
