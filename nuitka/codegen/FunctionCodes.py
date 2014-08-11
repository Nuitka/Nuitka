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
""" Code to generate and interact with compiled function objects.

"""

from nuitka import Options, Utils

from . import CodeTemplates
from .ConstantCodes import getConstantCode
from .ErrorCodes import getErrorExitCode
from .Indentation import indented
from .ModuleCodes import getModuleAccessCode
from .ParameterParsing import (
    getDirectFunctionEntryPointIdentifier,
    getParameterEntryPointIdentifier,
    getParameterParsingCode,
    getQuickEntryPointIdentifier
)
from .PythonAPICodes import getReferenceExportCode
from .VariableCodes import getLocalVariableInitCode, getVariableCode


def getClosureVariableProvisionCode(context, closure_variables):
    result = []

    for variable in closure_variables:
        assert variable.isClosureReference()

        variable = variable.getProviderVariable()

        result.append(
            getVariableCode(
                context  = context,
                variable = variable
            )
        )

    return result


def _getFunctionCreationArgs(defaults_name, kw_defaults_name,
                             annotations_name, closure_variables):
    result = []

    if defaults_name is not None:
        result.append("PyObject *defaults")

    if kw_defaults_name is not None:
        result.append("PyObject *kw_defaults")

    if annotations_name is not None:
        result.append("PyObject *annotations")

    for closure_variable in closure_variables:
        result.append(
            "%s &%s" % (
                (
                    "PyObjectSharedTempVariable"
                       if closure_variable.isTempVariableReference() else
                     "PyObjectSharedLocalVariable"
                ),
                closure_variable.getCodeName()
            )
        )

    return result


def getFunctionMakerDecl(function_identifier, defaults_name, kw_defaults_name,
                         annotations_name, closure_variables):

    function_creation_arg_spec = _getFunctionCreationArgs(
        defaults_name     = defaults_name,
        kw_defaults_name  = kw_defaults_name,
        annotations_name  = annotations_name,
        closure_variables = closure_variables
    )

    return CodeTemplates.template_function_make_declaration % {
        "function_identifier"        : function_identifier,
        "function_creation_arg_spec" : ", ".join(
            function_creation_arg_spec
        )
    }


def getFunctionMakerCode(function_name, function_qualname, function_identifier,
                         parameters, local_variables, closure_variables,
                         defaults_name, kw_defaults_name, annotations_name,
                         source_ref, function_doc, is_generator, emit,
                         context):
    # We really need this many parameters here. pylint: disable=R0913

    # Functions have many details, that we express as variables
    # pylint: disable=R0914
    var_names = parameters.getCoArgNames()

    # Apply mangled names of local variables too.
    var_names += [
        local_variable.getMangledName()
        for local_variable in
        local_variables
        if not local_variable.isParameterVariable()
    ]

    code_identifier = context.getCodeObjectHandle(
        filename      = source_ref.getFilename(),
        var_names     = var_names,
        arg_count     = parameters.getArgumentCount(),
        kw_only_count = parameters.getKwOnlyParameterCount(),
        line_number   = source_ref.getLineNumber(),
        code_name     = function_name,
        is_generator  = is_generator,
        is_optimized  = not context.hasLocalsDict(),
        has_starlist  = parameters.getStarListArgumentName() is not None,
        has_stardict  = parameters.getStarDictArgumentName() is not None,
        has_closure   = closure_variables != (),
        future_flags  = source_ref.getFutureSpec().asFlags()
    )

    function_creation_args = _getFunctionCreationArgs(
        defaults_name     = defaults_name,
        kw_defaults_name  = kw_defaults_name,
        annotations_name  = annotations_name,
        closure_variables = closure_variables
    )

    if Utils.python_version < 330 or function_qualname == function_name:
        function_qualname_obj = "NULL"
    else:
        function_qualname_obj = getConstantCode(
            constant = function_qualname,
            context  = context
        )

    if closure_variables:
        context_copy = []

        for closure_variable in closure_variables:
            context_copy.append(
                "_python_context->%s.shareWith( %s );" % (
                    closure_variable.getCodeName(),
                    closure_variable.getCodeName()
                )
            )

        if is_generator:
            template = CodeTemplates.make_genfunc_with_context_template
        else:
            template = CodeTemplates.make_function_with_context_template

        result = template % {
            "function_name_obj"          : getConstantCode(
                constant = function_name,
                context  = context
            ),
            "function_qualname_obj"      : function_qualname_obj,
            "function_identifier"        : function_identifier,
            "fparse_function_identifier" : getParameterEntryPointIdentifier(
                function_identifier = function_identifier,
            ),
            "dparse_function_identifier" : getQuickEntryPointIdentifier(
                function_identifier = function_identifier,
                parameters          = parameters
            ),
            "function_creation_args"     : ", ".join(
                function_creation_args
            ),
            "code_identifier"            : code_identifier,
            "context_copy"               : indented(context_copy),
            "function_doc"               : getConstantCode(
                constant = function_doc,
                context  = context
            ),
            "defaults"                   : "defaults"
                                             if defaults_name else
                                           "NULL",
            "kw_defaults"                : "kw_defaults"
                                             if kw_defaults_name else
                                           "NULL",
            "annotations"                : "annotations"
                                             if annotations_name else
                                           context.getConstantCode({}),
            "module_identifier"          : getModuleAccessCode(
                context = context
            ),
        }
    else:
        if is_generator:
            template = CodeTemplates.make_genfunc_without_context_template
        else:
            template = CodeTemplates.make_function_without_context_template


        result = template % {
            "function_name_obj"          : getConstantCode(
                constant = function_name,
                context  = context
            ),
            "function_qualname_obj"      : function_qualname_obj,
            "function_identifier"        : function_identifier,
            "fparse_function_identifier" : getParameterEntryPointIdentifier(
                function_identifier = function_identifier,
            ),
            "dparse_function_identifier" : getQuickEntryPointIdentifier(
                function_identifier = function_identifier,
                parameters          = parameters
            ),
            "function_creation_args"     : ", ".join(
                function_creation_args
            ),
            "code_identifier"            : code_identifier,
            "function_doc"               : getConstantCode(
                constant = function_doc,
                context  = context
            ),
            "defaults"                   : "defaults"
                                             if defaults_name else
                                           "NULL",
            "kw_defaults"                : "kw_defaults"
                                             if kw_defaults_name else
                                           "NULL",
            "annotations"                : "annotations"
                                             if annotations_name else
                                           context.getConstantCode({}),
            "module_identifier"          : getModuleAccessCode(
                context = context
            ),
        }

    return result


def getFunctionCreationCode(to_name, function_identifier, defaults_name,
                            kw_defaults_name, annotations_name,
                            closure_variables, emit, context):
    args = []

    if defaults_name is not None:
        args.append(getReferenceExportCode(defaults_name, context))

    if kw_defaults_name is not None:
        args.append(kw_defaults_name)

    if annotations_name is not None:
        args.append(annotations_name)

    args += getClosureVariableProvisionCode(
        context           = context,
        closure_variables = closure_variables
    )

    emit(
        "%s = MAKE_FUNCTION_%s( %s );" % (
            to_name,
            function_identifier,
            ", ".join( args )
        )
    )

    if context.needsCleanup(defaults_name):
        context.removeCleanupTempName(defaults_name)
    if context.needsCleanup(kw_defaults_name):
        context.removeCleanupTempName(kw_defaults_name)

    # TODO: Error checks
    context.addCleanupTempName(to_name)


def getDirectFunctionCallCode(to_name, function_identifier, arg_names,
                              closure_variables, emit, context):
    function_identifier = getDirectFunctionEntryPointIdentifier(
        function_identifier = function_identifier
    )

    suffix_args = getClosureVariableProvisionCode(
        context           = context,
        closure_variables = closure_variables
    )

    def takeRefs(arg_names):
        result = []

        for arg_name in arg_names:
            if context.needsCleanup(arg_name):
                context.removeCleanupTempName(arg_name)

                result.append(arg_name)
            else:
                result.append("INCREASE_REFCOUNT( %s )" % arg_name)

        return result

    emit(
        "%s = %s( %s );" % (
            to_name,
            function_identifier,
            ", ".join(
                takeRefs(arg_names) + suffix_args
            )
        )
    )

    # Arguments are owned to the called in direct function call.
    for arg_name in arg_names:
        if context.needsCleanup(arg_name):
            context.removeCleanupTempName(arg_name)

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)



def getFunctionDirectDecl(function_identifier, closure_variables,
                          parameter_variables, file_scope):

    parameter_objects_decl = [
        "PyObject *_python_par_" + variable.getName()
        for variable in
        parameter_variables
    ]

    for closure_variable in closure_variables:
        parameter_objects_decl.append(
            closure_variable.getDeclarationCode()
        )

    result = CodeTemplates.template_function_direct_declaration % {
        "file_scope"           : file_scope,
        "function_identifier"  : function_identifier,
        "direct_call_arg_spec" : ", ".join( parameter_objects_decl ),
    }

    return result


def getFunctionContextDefinitionCode(function_identifier, closure_variables,
                                     context):
    context_decl = []

    # Always empty now, but we may not use C++ destructors for everything in the
    # future, so leave it.
    context_free = []

    for closure_variable in closure_variables:
        context_decl.append(
            getLocalVariableInitCode(
                context    = context,
                variable   = closure_variable,
                in_context = True
            )
        )

    return CodeTemplates.function_context_body_template % {
        "function_identifier" : function_identifier,
        "context_decl"        : indented(context_decl),
        "context_free"        : indented(context_free),
    }


def getFunctionCode(context, function_name, function_identifier, parameters,
                    closure_variables, user_variables, temp_variables,
                    function_codes, function_doc, file_scope,
                    needs_exception_exit):

    # Functions have many details, that we express as variables, with many
    # branches to decide, pylint: disable=R0912,R0914

    parameter_variables, entry_point_code, parameter_objects_decl = \
      getParameterParsingCode(
        function_identifier = function_identifier,
        function_name       = function_name,
        parameters          = parameters,
        needs_creation      = context.isForCreatedFunction(),
        context             = context,
    )

    function_parameter_decl = [
        getLocalVariableInitCode(
            context   = context,
            variable  = variable,
            init_from = "_python_par_" + variable.getName()
        )
        for variable in
        parameter_variables
    ]


    # User local variable initializations
    local_var_inits = [
        getLocalVariableInitCode(
            context  = context,
            variable = variable
        )
        for variable in
        user_variables + tuple(
            variable
            for variable in
            temp_variables
        )
    ]

    if context.needsExceptionVariables():
        local_var_inits += [
            "PyObject *exception_type = NULL, *exception_value = NULL;",
            "PyTracebackObject *exception_tb = NULL;"
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

    # TODO: Could avoid this unless try/except or try/finally with returns
    # occur.
    if context.hasTempName("return_value"):
        local_var_inits.append("tmp_return_value = NULL;")

    function_doc = getConstantCode(
        context  = context,
        constant = function_doc
    )

    function_locals = []

    if context.hasLocalsDict():
        function_locals += CodeTemplates.function_dict_setup.split("\n")
        function_cleanup = "Py_DECREF( locals_dict );\n"
    else:
        function_cleanup = ""

    function_locals += function_parameter_decl + local_var_inits

    result = ""

    if closure_variables and context.isForCreatedFunction():
        context_access_function_impl = CodeTemplates.function_context_access_template % {
            "function_identifier" : function_identifier,
        }
    else:
        context_access_function_impl = str(CodeTemplates.function_context_unused_template)

    if needs_exception_exit:
        function_exit = CodeTemplates.template_function_exception_exit % {
            "function_cleanup" : function_cleanup
        }
    else:
        function_exit = CodeTemplates.template_function_noexception_exit % {}

    if context.hasTempName("return_value"):
        function_exit += CodeTemplates.template_function_return_exit % {
            "function_cleanup" : function_cleanup
        }

    if context.isForDirectCall():
        for closure_variable in closure_variables:
            parameter_objects_decl.append(
                closure_variable.getDeclarationCode()
            )

        result += CodeTemplates.function_direct_body_template % {
            "file_scope"                   : file_scope,
            "function_identifier"          : function_identifier,
            "context_access_function_impl" : context_access_function_impl,
            "direct_call_arg_spec"         : ", ".join(
                parameter_objects_decl
            ),
            "function_locals"              : indented(function_locals),
            "function_body"                : indented(function_codes),
            "function_exit"                : function_exit
        }
    else:
        result += CodeTemplates.template_function_body % {
            "function_identifier"          : function_identifier,
            "context_access_function_impl" : context_access_function_impl,
            "parameter_objects_decl"       : ", ".join(parameter_objects_decl),
            "function_locals"              : indented(function_locals),
            "function_body"                : indented(function_codes),
            "function_exit"                : function_exit
        }

    if context.isForCreatedFunction():
        result += entry_point_code

    return result

def getGeneratorFunctionCode( context, function_name, function_identifier,
                              parameters, closure_variables, user_variables,
                              temp_variables, function_codes, source_ref,
                              function_doc, needs_exception_exit,
                              needs_generator_return):
    # We really need this many parameters here. pylint: disable=R0913

    # Functions have many details, that we express as variables, with many
    # branches to decide, pylint: disable=R0912,R0914,R0915

    parameter_variables, entry_point_code, parameter_objects_decl = \
      getParameterParsingCode(
        function_identifier     = function_identifier,
        function_name           = function_name,
        parameters              = parameters,
        needs_creation          = context.isForCreatedFunction(),
        context                 = context,
    )

    context_decl = []
    context_copy = []
    context_free = []

    function_parameter_decl = [
        getLocalVariableInitCode(
            context    = context,
            variable   = variable,
            in_context = True
        )
        for variable in
        parameter_variables
    ]

    parameter_context_assign = []

    for variable in parameter_variables:
        parameter_context_assign.append(
            "_python_context->%s.setVariableValue( _python_par_%s );" % (
                variable.getCodeName(),
                variable.getName()
            )
        )
        del variable

    function_var_inits = []
    local_var_decl = []

    for user_variable in user_variables:
        local_var_decl.append(
            getLocalVariableInitCode(
                context    = context,
                variable   = user_variable,
                in_context = True
            )
        )

    for temp_variable in temp_variables:
        assert temp_variable.isTempVariable(), variable

        local_var_decl.append(
            getLocalVariableInitCode(
                context    = context,
                variable   = temp_variable,
                in_context = True
            )
        )

    for closure_variable in closure_variables:
        context_decl.append(
            getLocalVariableInitCode(
                context    = context,
                variable   = closure_variable,
                in_context = True
            )
        )
        context_copy.append(
            "_python_context->%s.shareWith( %s );" % (
                closure_variable.getCodeName(),
                closure_variable.getCodeName()
            )
        )

    function_doc = getConstantCode(
        context  = context,
        constant = function_doc
    )

    function_name_obj = getConstantCode(
        constant = function_name,
        context  = context,
    )

    instance_context_decl = function_parameter_decl + local_var_decl

    if context.isForDirectCall():
        instance_context_decl = context_decl + instance_context_decl
        context_decl = []

    if context_decl:
        result = CodeTemplates.genfunc_context_body_template % {
            "function_identifier"            : function_identifier,
            "function_common_context_decl"   : indented(context_decl),
            "function_instance_context_decl" : indented(instance_context_decl),
            "context_free"                   : indented(context_free, 2),
        }
    elif instance_context_decl:
        result = CodeTemplates.genfunc_context_local_only_template % {
            "function_identifier"            : function_identifier,
            "function_instance_context_decl" : indented(instance_context_decl)
        }
    else:
        result = ""

    if instance_context_decl or context_decl:
        context_access_instance = CodeTemplates.generator_context_access_template2  % {
            "function_identifier" : function_identifier
        }
    else:
        context_access_instance = ""

    function_locals = []

    if context.hasLocalsDict():
        function_locals += CodeTemplates.function_dict_setup.split("\n")

    function_locals += function_var_inits

    if context.needsExceptionVariables():
        function_locals += [
            "PyObject *exception_type = NULL, *exception_value = NULL;",
            "PyTracebackObject *exception_tb = NULL;"
        ]

    for keeper_variable in range(1, context.getKeeperVariableCount()+1):
        # For finally handlers of Python3, which have conditions on assign and
        # use.
        if Options.isDebug() and Utils.python_version >= 300:
            keeper_init = " = NULL"
        else:
            keeper_init = ""

        function_locals += [
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

    function_locals += [
        "%s%s%s;" % (
            tmp_type,
            " " if not tmp_type.endswith("*") else "",
            tmp_name
        )
        for tmp_name, tmp_type in
        context.getTempNameInfos()
    ]

    # TODO: Could avoid this unless try/except or try/finally with returns
    # occur.
    if context.hasTempName("generator_return"):
        function_locals.append("tmp_generator_return = false;")
    if context.hasTempName("return_value"):
        function_locals.append("tmp_return_value = NULL;")

    if needs_exception_exit:
        generator_exit = CodeTemplates.template_generator_exception_exit % {}
    else:
        generator_exit = CodeTemplates.template_generator_noexception_exit % {}

    if needs_generator_return:
        generator_exit += CodeTemplates.template_generator_return_exit % {}

    result += CodeTemplates.genfunc_yielder_template % {
        "function_identifier" : function_identifier,
        "function_body"       : indented(function_codes, 1),
        "function_var_inits"  : indented(function_locals, 1),
        "context_access"      : indented(context_access_instance, 1),
        "generator_exit"      : generator_exit
    }

    code_identifier = context.getCodeObjectHandle(
        filename      = source_ref.getFilename(),
        var_names     = parameters.getCoArgNames(),
        arg_count     = parameters.getArgumentCount(),
        kw_only_count = parameters.getKwOnlyParameterCount(),
        line_number   = source_ref.getLineNumber(),
        code_name     = function_name,
        is_generator  = True,
        is_optimized  = not context.hasLocalsDict(),
        has_starlist  = parameters.getStarListArgumentName() is not None,
        has_stardict  = parameters.getStarDictArgumentName() is not None,
        has_closure   = closure_variables != (),
        future_flags  = source_ref.getFutureSpec().asFlags()
    )

    if context_decl or instance_context_decl:
        if context_decl:
            context_making = CodeTemplates.genfunc_common_context_use_template % {
                "function_identifier" : function_identifier,
            }
        else:
            context_making = CodeTemplates.genfunc_local_context_use_template  % {
                "function_identifier" : function_identifier,
            }

        context_making = context_making.split("\n")

        if context.isForDirectCall():
            context_making += context_copy

        generator_making = CodeTemplates.genfunc_generator_with_context_making  % {
            "function_name_obj"   : function_name_obj,
            "function_identifier" : function_identifier,
            "code_identifier"     : code_identifier
        }
    else:
        generator_making = CodeTemplates.genfunc_generator_without_context_making  % {
            "function_name_obj"   : function_name_obj,
            "function_identifier" : function_identifier,
            "code_identifier"     : code_identifier
        }

        context_making = []

    if context.isForDirectCall():
        for closure_variable in closure_variables:
            parameter_objects_decl.append(
                closure_variable.getDeclarationCode()
            )

    result += CodeTemplates.genfunc_function_maker_template % {
        "function_name"              : function_name,
        "function_identifier"        : function_identifier,
        "context_making"             : indented(context_making),
        "context_copy"               : indented(parameter_context_assign),
        "generator_making"           : generator_making,
        "parameter_objects_decl"     : ", ".join(parameter_objects_decl),
    }

    if context.isForCreatedFunction():
        result += entry_point_code

    return result
