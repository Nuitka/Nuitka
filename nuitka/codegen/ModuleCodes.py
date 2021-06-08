#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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

import os

from nuitka import Options
from nuitka.__past__ import iterItems
from nuitka.codegen import Emission
from nuitka.Version import getNuitkaVersion, getNuitkaVersionYear

from .CodeHelpers import (
    decideConversionCheckNeeded,
    generateStatementSequenceCode,
    withObjectCodeTemporaryAssignment,
)
from .CodeObjectCodes import getCodeObjectsDeclCode, getCodeObjectsInitCode
from .Indentation import indented
from .templates.CodeTemplatesModules import (
    template_global_copyright,
    template_module_body_template,
    template_module_exception_exit,
    template_module_external_entry_point,
    template_module_noexception_exit,
)
from .VariableCodes import getVariableReferenceCode


def getModuleAccessCode(context):
    return "module_%s" % context.getModuleCodeName()


def getModuleCode(
    module, function_decl_codes, function_body_codes, module_const_blob_name, context
):

    # For the module code, lots of arguments and attributes come together.
    # pylint: disable=too-many-locals

    # Temporary variable initializations
    # TODO: Move that to a place outside of functions.
    from .FunctionCodes import (
        finalizeFunctionLocalVariables,
        setupFunctionLocalVariables,
    )

    setupFunctionLocalVariables(
        context=context,
        parameters=None,
        closure_variables=(),
        user_variables=module.getOutlineLocalVariables(),
        temp_variables=module.getTempVariables(),
    )

    module_codes = Emission.SourceCodeCollector()

    module = context.getOwner()
    module_body = module.subnode_body

    generateStatementSequenceCode(
        statement_sequence=module_body,
        emit=module_codes,
        allow_none=True,
        context=context,
    )

    for _identifier, code in sorted(iterItems(context.getHelperCodes())):
        function_body_codes.append(code)

    for _identifier, code in sorted(iterItems(context.getDeclarations())):
        function_decl_codes.append(code)

    function_body_codes = "\n\n".join(function_body_codes)
    function_decl_codes = "\n\n".join(function_decl_codes)

    _cleanup = finalizeFunctionLocalVariables(context)

    # TODO: Seems like a bug, classes could produce those.
    # assert not _cleanup, _cleanup

    local_var_inits = context.variable_storage.makeCFunctionLevelDeclarations()

    if module_body is not None and module_body.mayRaiseException(BaseException):
        module_exit = template_module_exception_exit
    else:
        module_exit = template_module_noexception_exit

    function_table_entries_decl = []
    for func_impl_identifier in context.getFunctionCreationInfos():
        function_table_entries_decl.append("%s," % func_impl_identifier)

    module_name = module.getFullName()

    is_package = module.isCompiledPythonPackage()
    is_top = module.isTopModule()

    module_identifier = module.getCodeName()

    template = template_global_copyright + template_module_body_template

    if is_top == 1 and Options.shallMakeModule():
        template += template_module_external_entry_point

    module_code_objects_decl = getCodeObjectsDeclCode(context)
    module_code_objects_init = getCodeObjectsInitCode(context)

    return template % {
        "module_name": module_name,
        "version": getNuitkaVersion(),
        "year": getNuitkaVersionYear(),
        "is_main_module": 1 if module.isMainModule() else 0,
        "is_dunder_main": 1
        if module_name == "__main__"
        and os.path.basename(module.getCompileTimeFilename()) == "__main__.py"
        else 0,
        "is_package": 1 if is_package else 0,
        "module_identifier": module_identifier,
        "module_functions_decl": function_decl_codes,
        "module_functions_code": function_body_codes,
        "module_function_table_entries": indented(function_table_entries_decl),
        "temps_decl": indented(local_var_inits),
        "module_code": indented(module_codes.codes),
        "module_exit": module_exit,
        "module_code_objects_decl": indented(module_code_objects_decl, 0),
        "module_code_objects_init": indented(module_code_objects_init, 1),
        "constants_count": context.getConstantsCount(),
        "module_const_blob_name": module_const_blob_name,
    }


def generateModuleAttributeFileCode(to_name, expression, emit, context):
    # TODO: Special treatment justified?
    with withObjectCodeTemporaryAssignment(
        to_name, "module_fileattr_value", expression, emit, context
    ) as result_name:
        emit("%s = module_filename_obj;" % result_name)


def generateModuleAttributeCode(to_name, expression, emit, context):
    getVariableReferenceCode(
        to_name=to_name,
        variable=expression.getVariable(),
        variable_trace=None,
        needs_check=False,
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        emit=emit,
        context=context,
    )


def generateNuitkaLoaderCreationCode(to_name, expression, emit, context):
    with withObjectCodeTemporaryAssignment(
        to_name, "nuitka_loader_value", expression, emit, context
    ) as result_name:
        emit("%s = Nuitka_Loader_New(module_entry);" % result_name)
