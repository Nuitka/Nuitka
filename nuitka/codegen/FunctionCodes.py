#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
from .VariableCodes import (
    getLocalVariableInitCode,
    getVariableCode,
    getVariableCodeName
)


def getClosureVariableProvisionCode(context, closure_variables):
    result = []

    for variable in closure_variables:
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
            "PyCellObject *%s" % (
                getVariableCodeName(
                    variable   = closure_variable,
                    in_context = True
                )
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
                         code_identifier, parameters, closure_variables,
                         defaults_name, kw_defaults_name, annotations_name,
                         function_doc, is_generator, context):
    # We really need this many parameters here. pylint: disable=R0913

    # Functions have many details, that we express as variables
    # pylint: disable=R0914
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

        closure_count = len(closure_variables)
        context_copy.append(
            "PyCellObject **closure = (PyCellObject **)malloc( %d * sizeof(PyCellObject *) );" % closure_count
        )

        for count, closure_variable in enumerate(closure_variables):
            context_copy.append(
                "closure[%d] = %s;" % (
                    count,
                    getVariableCodeName(
                        True,
                        closure_variable
                    )
                )
            )
            context_copy.append(
                "Py_INCREF( closure[%d] );" %count
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
            "closure_count"              : closure_count,
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
            ", ".join(args)
        )
    )

    if context.needsCleanup(defaults_name):
        context.removeCleanupTempName(defaults_name)
    if context.needsCleanup(kw_defaults_name):
        context.removeCleanupTempName(kw_defaults_name)

    # No error checks, this supposedly, cannot fail.
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

    # TODO: We ought to not assume references for direct calls, or make a
    # profile if an argument needs a reference at all. Most functions don't
    # bother to release a called argument by "del" or assignment to it. We
    # could well know that ahead of time.
    for arg_name in arg_names:
        if context.needsCleanup(arg_name):
            context.removeCleanupTempName(arg_name)
        else:
            emit("Py_INCREF( %s );" % arg_name)

    emit(
        "%s = %s( %s );" % (
            to_name,
            function_identifier,
            ", ".join(
                arg_names + suffix_args
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

def getFunctionDirectClosureArgs(closure_variables):
    result = []

    for closure_variable in closure_variables:
        if closure_variable.isSharedTechnically():
            result.append(
                "PyCellObject *%s" % (
                    getVariableCodeName(
                        in_context = True,
                        variable   = closure_variable
                    )
                )
            )
        else:
            # TODO: The reference is only needed for Python3, could make it
            # version dependent.
            result.append(
                "PyObject *&%s" % (
                    getVariableCodeName(
                        in_context = True,
                        variable   = closure_variable
                    )
                )
            )

    return result


def getFunctionDirectDecl(function_identifier, closure_variables,
                          parameter_variables, file_scope):

    parameter_objects_decl = [
        "PyObject *_python_par_" + variable.getCodeName()
        for variable in
        parameter_variables
    ]

    parameter_objects_decl += getFunctionDirectClosureArgs(closure_variables)

    result = CodeTemplates.template_function_direct_declaration % {
        "file_scope"           : file_scope,
        "function_identifier"  : function_identifier,
        "direct_call_arg_spec" : ", ".join(parameter_objects_decl),
    }

    return result


def getFunctionCode(context, function_name, function_identifier, parameters,
                    closure_variables, user_variables, temp_variables,
                    function_codes, function_doc, file_scope,
                    needs_exception_exit):

    # Many arguments, as we need much input transferred, pylint: disable=R0913

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
            variable  = variable,
            init_from = "_python_par_" + variable.getCodeName()
        )
        for variable in
        parameter_variables
    ]


    # User local variable initializations
    local_var_inits = [
        getLocalVariableInitCode(
            variable = variable,
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
            ' ' if not tmp_type.endswith('*') else "",
            tmp_name
        )
        for tmp_name, tmp_type in
        context.getTempNameInfos()
    ]

    local_var_inits += context.getFrameDeclarations()

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
        function_locals += CodeTemplates.function_dict_setup.split('\n')
        function_cleanup = "Py_DECREF( locals_dict );\n"
    else:
        function_cleanup = ""

    function_locals += function_parameter_decl + local_var_inits

    result = ""

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
        parameter_objects_decl += getFunctionDirectClosureArgs(closure_variables)

        result += CodeTemplates.function_direct_body_template % {
            "file_scope"                   : file_scope,
            "function_identifier"          : function_identifier,
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
            "parameter_objects_decl"       : ", ".join(parameter_objects_decl),
            "function_locals"              : indented(function_locals),
            "function_body"                : indented(function_codes),
            "function_exit"                : function_exit
        }

    if context.isForCreatedFunction():
        result += entry_point_code

    return result


def getGeneratorFunctionCode(context, function_name, function_identifier,
                             code_identifier, parameters, closure_variables,
                             user_variables,
                             temp_variables, function_codes,
                             function_doc, needs_exception_exit,
                             needs_generator_return):
    # We really need this many parameters here. pylint: disable=R0913

    # Functions have many details, that we express as variables, with many
    # branches to decide, pylint: disable=R0912,R0914,R0915

    # Parameter parsing code of the function. TODO: Somehow we duplicate a lot
    # of what a function is for these. We should make these generator object
    # creations explicit, so they can be in-lined, and the duplication of some
    # of this code could be avoided.
    parameter_variables, entry_point_code, parameter_objects_decl = \
      getParameterParsingCode(
        function_identifier = function_identifier,
        function_name       = function_name,
        parameters          = parameters,
        needs_creation      = context.isForCreatedFunction(),
        context             = context,
    )

    # For direct calls, append the closure variables to the argument list.
    if context.isForDirectCall():
        for count, variable in enumerate(closure_variables):
            parameter_objects_decl.append(
                "PyCellObject *%s" % (
                    getVariableCodeName(
                        in_context = True,
                        variable   = variable
                    )
                )
            )

    function_locals = []
    for user_variable in user_variables + temp_variables:
        function_locals.append(
            getLocalVariableInitCode(
                variable = user_variable,
            )
        )

    function_doc = getConstantCode(
        context  = context,
        constant = function_doc
    )

    if context.hasLocalsDict():
        function_locals += CodeTemplates.function_dict_setup.split('\n')

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

    if needs_exception_exit:
        generator_exit = CodeTemplates.template_generator_exception_exit % {}
    else:
        generator_exit = CodeTemplates.template_generator_noexception_exit % {}

    if needs_generator_return:
        generator_exit += CodeTemplates.template_generator_return_exit % {}

    result = CodeTemplates.genfunc_yielder_template % {
        "function_identifier" : function_identifier,
        "function_body"       : indented(function_codes),
        "function_var_inits"  : indented(function_locals),
        "generator_exit"      : generator_exit
    }

    # Code to copy parameters into a "PyObject **" array, attaching it to the
    # generator object to be created in the cause of the function call.
    parameter_count = len(parameter_variables)

    # Prepare declaration of parameters array to the generator object creation.
    if parameter_count > 0:
        parameter_copy = []

        for count, variable in enumerate(parameter_variables):

            if variable.isSharedTechnically():
                parameter_copy.append(
                    "parameters[%d] = (PyObject *)PyCell_NEW1( _python_par_%s );" % (
                        count,
                        variable.getCodeName()
                    )
                )
            else:
                parameter_copy.append(
                    "parameters[%d] = _python_par_%s;" % (
                        count,
                        variable.getCodeName()
                    )
                )

        parameters_decl = CodeTemplates.genfunc_generator_with_parameters  % {
            "parameter_copy"      : indented(parameter_copy),
            "parameter_count"     : parameter_count
        }
    else:
        parameters_decl = CodeTemplates.genfunc_generator_no_parameters  % {}

    # Prepare declaration of parameters array to the generator object creation.
    closure_count = len(closure_variables)

    if closure_count > 0:
        if context.isForDirectCall():
            closure_copy = []

            for count, variable in enumerate(closure_variables):
                closure_copy.append(
                    "closure[%d] = %s;" % (
                        count,
                        getVariableCodeName(
                            in_context = True,
                            variable   = variable
                        )
                    )
                )
                closure_copy.append(
                    "Py_INCREF( closure[%d] );" % count
                )


            closure_decl = CodeTemplates.genfunc_generator_with_own_closure % {
                "closure_copy" : '\n'.join(closure_copy),
                "closure_count" : closure_count
            }
        else:
            closure_decl = CodeTemplates.genfunc_generator_with_parent_closure % {
                "closure_count" : closure_count
            }
    else:
        closure_decl = CodeTemplates.genfunc_generator_no_closure % {}

    result += CodeTemplates.genfunc_function_impl_template % {
        "function_name"          : function_name,
        "function_name_obj"      : getConstantCode(context, function_name),
        "function_identifier"    : function_identifier,
        "code_identifier"        : code_identifier,
        "parameter_decl"         : parameters_decl,
        "parameter_count"        : parameter_count,
        "closure_decl"           : closure_decl,
        "closure_count"          : closure_count,
        "parameter_objects_decl" : ", ".join(parameter_objects_decl),
    }

    if context.isForCreatedFunction():
        result += entry_point_code

    return result
