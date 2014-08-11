#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

import re

from nuitka import Options, Utils

from . import CodeTemplates
from .CodeObjectCodes import getCodeObjectsDeclCode, getCodeObjectsInitCode
from .ConstantCodes import (
    allocateNestedConstants,
    getConstantCode,
    getConstantInitCodes
)
from .Indentation import indented
from .VariableCodes import getLocalVariableInitCode


def getModuleAccessCode(context):
    return "module_%s" % context.getModuleCodeName()


def getModuleIdentifier(module_name):
    # TODO: This is duplication with ModuleNode.getCodeName, remove it.
    def r(match):
        c = match.group()
        if c == '.':
            return "$"
        else:
            return "$$%d$" % ord(c)

    return "".join(re.sub("[^a-zA-Z0-9_]", r ,c) for c in module_name)


def getModuleMetapathLoaderEntryCode(module_name, is_shlib, is_package):
    if is_shlib:
        assert module_name != "__main__"
        assert not is_package

        return CodeTemplates.template_metapath_loader_shlib_module_entry % {
            "module_name" : module_name
        }
    elif is_package:
        return CodeTemplates.template_metapath_loader_compiled_package_entry % {
            "module_name"       : module_name,
            "module_identifier" : getModuleIdentifier(module_name),
        }
    else:
        return CodeTemplates.template_metapath_loader_compiled_module_entry % {
            "module_name"       : module_name,
            "module_identifier" : getModuleIdentifier(module_name),
        }


def prepareModuleCode(context, module_name, codes, metapath_loader_inittab,
                      metapath_module_decls, function_decl_codes,
                      function_body_codes, temp_variables, is_main_module,
                      is_internal_module):
    # For the module code, lots of attributes come together.
    # pylint: disable=R0914
    module_identifier = getModuleIdentifier(module_name)

    # Temp local variable initializations
    local_var_inits = [
        getLocalVariableInitCode(
            context  = context,
            variable = variable
        )
        for variable in
        temp_variables
    ]

    if context.needsExceptionVariables():
        local_var_inits += [
            "PyObject *exception_type, *exception_value;",
            "PyTracebackObject *exception_tb;"
        ]

    for keeper_variable in range(1, context.getKeeperVariableCount()+1):
        # For finally handlers of Python3, which have conditions on assign and
        # use.
        if Options.isDebug() and Utils.python_version >= 300:
            keeper_init = " = NULL"
        else:
            keeper_init = ""

        local_var_inits += [
            "PyObject *exception_keeper_type_%d%s;" % (
                keeper_variable,
                keeper_init
            ),
            "PyObject *exception_keeper_value_%d%s;" % (
                keeper_variable,
                keeper_init
            ),
            "PyTracebackObject *exception_keeper_tb_%d%s;" % (
                keeper_variable,
                keeper_init
            )
        ]

    local_var_inits += [
        "%s%s%s;" % (
            tmp_type,
            " " if not tmp_type.endswith("*") else "",
            tmp_name
        )
        for tmp_name, tmp_type in
        context.getTempNameInfos()
    ]

    if context.needsExceptionVariables():
        module_exit = CodeTemplates.template_module_exception_exit
    else:
        module_exit = CodeTemplates.template_module_noexception_exit

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
        "metapath_loader_inittab"  : indented(
            sorted(metapath_loader_inittab)
        ),
        "metapath_module_decls"    : indented(
            sorted(metapath_module_decls),
            0
        ),
        "module_code_objects_decl" : indented(
            getCodeObjectsDeclCode(context),
            0
        ),
        "module_code_objects_init" : indented(
            getCodeObjectsInitCode(context),
            1
        ),
        "use_unfreezer"           : 1 if metapath_loader_inittab else 0
    }

    allocateNestedConstants(context)

    # Force internal module to not need constants init, by making all its
    # constants be shared.
    if is_internal_module:
        for constant in context.getConstants():
            context.global_context.countConstantUse(constant)

    return module_body_template_values


def getModuleCode(module_context, template_values):
    header = CodeTemplates.global_copyright % {
        "name"    : module_context.getName(),
        "version" : Options.getVersion()
    }

    decls, inits = getConstantInitCodes(module_context)

    template_values["constant_decl_codes"] = indented(
        decls,
        0
    )

    template_values["constant_init_codes"] = indented(
        inits,
        1
    )

    return header + CodeTemplates.module_body_template % template_values
