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
""" Code to generate and interact with compiled module objects.

"""

from nuitka import Options

from .CodeObjectCodes import getCodeObjectsDeclCode, getCodeObjectsInitCode
from .ConstantCodes import (
    allocateNestedConstants,
    getConstantCode,
    getConstantInitCodes
)
from .ErrorCodes import (
    getErrorVariableDeclarations,
    getExceptionKeeperVariableNames,
    getExceptionPreserverVariableNames
)
from .Indentation import indented
from .templates.CodeTemplatesModules import (
    template_global_copyright,
    template_module_body_template,
    template_module_exception_exit,
    template_module_noexception_exit
)
from .VariableCodes import getLocalVariableInitCode


def getModuleAccessCode(context):
    return "module_%s" % context.getModuleCodeName()


def getModuleValues(context, module_name, module_identifier, codes,
                    function_decl_codes, function_body_codes, temp_variables,
                    is_main_module, is_internal_module):
    # For the module code, lots of arguments and attributes come together.
    # pylint: disable=R0914

    # Temporary variable initializations
    local_var_inits = [
        getLocalVariableInitCode(
            variable = variable
        )
        for variable in
        temp_variables
    ]

    if context.needsExceptionVariables():
        local_var_inits.extend(getErrorVariableDeclarations())

    for keeper_index in range(1, context.getKeeperVariableCount()+1):
        local_var_inits.extend(getExceptionKeeperVariableNames(keeper_index))

    for preserver_id in context.getExceptionPreserverCounts():
        local_var_inits.extend(getExceptionPreserverVariableNames(preserver_id))

    local_var_inits += [
        "%s%s%s;" % (
            tmp_type,
            ' ' if not tmp_type.endswith('*') else "",
            tmp_name
        )
        for tmp_name, tmp_type in
        context.getTempNameInfos()
    ]
    for tmp_name, tmp_type in context.getTempNameInfos():
        if tmp_name.startswith("tmp_outline_return_value_"):
            local_var_inits.append("%s = NULL;" % tmp_name)

    local_var_inits += context.getFrameDeclarations()

    if context.needsExceptionVariables():
        module_exit = template_module_exception_exit
    else:
        module_exit = template_module_noexception_exit

    module_body_template_values = {
        "module_name"              : module_name,
        "module_name_obj"          : getConstantCode(
            context  = context,
            constant = module_name
        ),
        "is_main_module"           : 1 if is_main_module else 0,
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
        "version" : Options.getVersion(),
        "year"    : Options.getYear()
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


def generateModuleFileAttributeCode(to_name, expression, emit, context):
    # The expression doesn't really matter, but it is part of the API for
    # the expression registry, pylint: disable=W0613

    emit(
        "%s = module_filename_obj;" % (
            to_name,
        )
    )

    context.markAsNeedsModuleFilenameObject()
