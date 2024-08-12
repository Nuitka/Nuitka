#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Code to generate and interact with compiled module objects.

"""

from nuitka import Options
from nuitka.__past__ import iterItems
from nuitka.code_generation import Emission
from nuitka.utils.CStrings import encodePythonStringToC
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
    template_module_no_exception_exit,
)
from .templates.CodeTemplatesVariables import (
    template_module_variable_accessor_function,
)
from .VariableCodes import (
    getModuleVariableAccessorCodeName,
    getModuleVariableReferenceCode,
)


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

    module_identifier = module.getCodeName()

    if module_body is not None and module_body.mayRaiseException(BaseException):
        module_exit = template_module_exception_exit % {
            "module_identifier": module_identifier,
            "is_top": 1 if module.isTopModule() else 0,
        }
    else:
        module_exit = template_module_no_exception_exit

    local_var_inits = context.variable_storage.makeCFunctionLevelDeclarations()

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

    is_dunder_main = module.isMainModule()

    dunder_main_package = context.getConstantCode(
        module.getRuntimePackageValue() if is_dunder_main else ""
    )

    if str is bytes:
        module_dll_entry_point = "init" + module_identifier
        module_def_size = -1
    else:
        try:
            module_dll_entry_point = module_name.encode("ascii")
            module_dll_entry_point_prefix = "PyInit_"
            module_def_size = -1
        except UnicodeEncodeError:
            module_dll_entry_point = module_name.encode("punycode")
            module_dll_entry_point_prefix = "PyInitU_"
            module_def_size = 0

        module_dll_entry_point = (
            module_dll_entry_point_prefix + module_dll_entry_point.decode("ascii")
        )

    module_variable_accessor_codes = []
    for module_variable_name, caching in sorted(
        context.getModuleVariableAccessors().items()
    ):
        module_variable_accessor_codes.append(
            template_module_variable_accessor_function
            % {
                "accessor_function_name": getModuleVariableAccessorCodeName(
                    module_identifier, module_variable_name
                ),
                "var_name": context.getConstantCode(constant=module_variable_name),
                "module_identifier": module_identifier,
                "caching": "1" if caching else "0",
            }
        )

    return template % {
        "module_name_cstr": encodePythonStringToC(
            module_name.asString().encode("utf8")
        ),
        "version": getNuitkaVersion(),
        "year": getNuitkaVersionYear(),
        "is_top": 1 if module.isTopModule() else 0,
        "is_dunder_main": 1 if is_dunder_main else 0,
        "dunder_main_package": dunder_main_package,
        "is_package": 1 if is_package else 0,
        "module_identifier": module_identifier,
        "module_functions_decl": function_decl_codes,
        "module_functions_code": function_body_codes,
        "module_function_table_entries": indented(function_table_entries_decl),
        "temps_decl": indented(local_var_inits),
        "module_variable_accessors": indented(module_variable_accessor_codes, 0),
        "module_variable_accessors_count": len(module_variable_accessor_codes),
        "module_init_codes": indented(context.getModuleInitCodes()),
        "module_codes": indented(module_codes.codes),
        "module_exit": module_exit,
        "module_code_objects_decl": indented(module_code_objects_decl, 0),
        "module_code_objects_init": indented(module_code_objects_init),
        "constants_count": context.getConstantsCount(),
        "module_const_blob_name": module_const_blob_name,
        "module_dll_entry_point": module_dll_entry_point,
        "module_def_size": module_def_size,
    }


def generateModuleAttributeFileCode(to_name, expression, emit, context):
    # TODO: Special treatment justified?
    with withObjectCodeTemporaryAssignment(
        to_name, "module_fileattr_value", expression, emit, context
    ) as result_name:
        emit("%s = module_filename_obj;" % result_name)


def generateModuleAttributeCode(to_name, expression, emit, context):
    getModuleVariableReferenceCode(
        to_name=to_name,
        variable_name=expression.getVariable().getName(),
        use_caching=False,
        needs_check=False,
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        emit=emit,
        context=context,
    )


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
