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

from .VariableCodes import (
    getLocalVariableInitCode,
    getVariableCode
)

from .ParameterParsing import (
    getDirectFunctionEntryPointIdentifier,
    getParameterEntryPointIdentifier,
    getQuickEntryPointIdentifier,
    getParameterParsingCode,
)

from .Identifiers import defaultToNullIdentifier

from .OrderedEvaluation import getOrderRelevanceEnforcedArgsCode

from .ConstantCodes import (
    getConstantCode,
)

from .CodeObjectCodes import (
    getCodeObjectHandle,
)

from .Indentation import indented

from .Identifiers import (
    SpecialConstantIdentifier,
    NullIdentifier,
    Identifier
)

from .ModuleCodes import (
    getModuleAccessCode,
)

from . import CodeTemplates

from nuitka import Utils

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

def _getFunctionCreationArgs( defaults_identifier, kw_defaults_identifier,
                              annotations_identifier, closure_variables ):
    result = []

    if not kw_defaults_identifier.isConstantIdentifier():
        result.append( "PyObject *kwdefaults" )

    if not defaults_identifier.isConstantIdentifier():
        result.append( "PyObject *defaults" )

    if annotations_identifier is not None and \
       not annotations_identifier.isConstantIdentifier():
        result.append( "PyObject *annotations" )

    for closure_variable in closure_variables:
        result.append(
            "%s &%s" % (
                ( "PyObjectSharedTempVariable" if
                  closure_variable.isTempVariableReference() else
                  "PyObjectSharedLocalVariable" ),
                closure_variable.getCodeName()
            )
        )

    return result

def _getFuncDefaultValue(defaults_identifier):
    if defaults_identifier.isConstantIdentifier():
        return defaults_identifier
    else:
        return Identifier( "defaults", 1 )


def _getFuncKwDefaultValue(kw_defaults_identifier):
    if kw_defaults_identifier.isConstantIdentifier():
        if kw_defaults_identifier.getConstant():
            return kw_defaults_identifier
        else:
            return SpecialConstantIdentifier( constant_value = None )
    else:
        return Identifier( "kwdefaults", 1 )

def _getFuncAnnotationsValue(annotations_identifier):
    if annotations_identifier is None:
        return NullIdentifier()
    elif annotations_identifier.isConstantIdentifier():
        return annotations_identifier
    else:
        return Identifier( "annotations", 1 )


def getFunctionMakerDecl( function_identifier, defaults_identifier,
                          kw_defaults_identifier, annotations_identifier,
                          closure_variables ):
    function_creation_arg_spec = _getFunctionCreationArgs(
        defaults_identifier    = defaults_identifier,
        kw_defaults_identifier = kw_defaults_identifier,
        annotations_identifier = annotations_identifier,
        closure_variables      = closure_variables
    )

    return CodeTemplates.template_function_make_declaration % {
        "function_identifier"        : function_identifier,
        "function_creation_arg_spec" : ", ".join(
            function_creation_arg_spec
        )
    }

def getFunctionMakerCode( context, function_name, function_qualname,
                          function_identifier, parameters, local_variables,
                          closure_variables, defaults_identifier,
                          kw_defaults_identifier, annotations_identifier,
                          source_ref, function_doc, is_generator ):
    # We really need this many parameters here. pylint: disable=R0913

    # Functions have many details, that we express as variables
    # pylint: disable=R0914

    function_name_obj = getConstantCode(
        context  = context,
        constant = function_name
    )

    var_names = parameters.getCoArgNames()

    # Apply mangled names of local variables too.
    var_names += [
        local_variable.getMangledName()
        for local_variable in
        local_variables
        if not local_variable.isParameterVariable()
    ]

    code_identifier = getCodeObjectHandle(
        context       = context,
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
    )

    function_creation_args = _getFunctionCreationArgs(
        defaults_identifier    = defaults_identifier,
        kw_defaults_identifier = kw_defaults_identifier,
        annotations_identifier = annotations_identifier,
        closure_variables      = closure_variables,
    )

    func_defaults = _getFuncDefaultValue(
        defaults_identifier = defaults_identifier
    )

    func_kwdefaults = _getFuncKwDefaultValue(
        kw_defaults_identifier = kw_defaults_identifier
    )

    func_annotations = _getFuncAnnotationsValue(
        annotations_identifier = annotations_identifier
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
            "function_name_obj"          : function_name_obj,
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
            "code_identifier"            : code_identifier.getCodeTemporaryRef(),
            "context_copy"               : indented( context_copy ),
            "function_doc"               : getConstantCode(
                constant = function_doc,
                context  = context
            ),
            "defaults"                   : func_defaults.getCodeExportRef(),
            "kwdefaults"                 : func_kwdefaults.getCodeExportRef(),
            "annotations"                : func_annotations.getCodeExportRef(),
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
            "function_name_obj"          : function_name_obj,
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
            "code_identifier"            : code_identifier.getCodeTemporaryRef(),
            "function_doc"               : getConstantCode(
                constant = function_doc,
                context  = context
            ),
            "defaults"                   : func_defaults.getCodeExportRef(),
            "kwdefaults"                 : func_kwdefaults.getCodeExportRef(),
            "annotations"                : func_annotations.getCodeExportRef(),
            "module_identifier"          : getModuleAccessCode(
                context = context
            ),
        }

    return result


def getFunctionCreationCode( context, function_identifier, order_relevance,
                             default_args, closure_variables ):

    return getOrderRelevanceEnforcedArgsCode(
        helper          = "MAKE_FUNCTION_%s" % function_identifier,
        export_ref      = 1,
        ref_count       = 1,
        tmp_scope       = "make_func",
        suffix_args     = getClosureVariableProvisionCode(
            context           = context,
            closure_variables = closure_variables
        ),
        order_relevance = order_relevance,
        args            = default_args,
        context         = context
    )

def getDirectionFunctionCallCode( function_identifier, arguments,
                                  order_relevance, closure_variables,
                                  extra_arguments, context ):
    function_identifier = getDirectFunctionEntryPointIdentifier(
        function_identifier = function_identifier
    )

    return getOrderRelevanceEnforcedArgsCode(
        helper          = function_identifier,
        export_ref      = 1,
        ref_count       = 1,
        tmp_scope       = "call_tmp",
        prefix_args     = [
            defaultToNullIdentifier(extra_argument).getCodeTemporaryRef()
            for extra_argument in
            extra_arguments
        ],
        suffix_args     = getClosureVariableProvisionCode(
            context           = context,
            closure_variables = closure_variables
        ),
        order_relevance = order_relevance,
        args            = arguments,
        context         = context
    )

def getFunctionDirectDecl( function_identifier, closure_variables,
                           parameter_variables, file_scope ):

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

def getFunctionContextDefinitionCode( context, function_identifier,
                                      closure_variables ):
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
        "context_decl"        : indented( context_decl ),
        "context_free"        : indented( context_free ),
    }

def getFunctionCode( context, function_name, function_identifier, parameters,
                     closure_variables, user_variables, temp_variables,
                     function_codes, function_doc, file_scope ):

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
            init_from = Identifier( "_python_par_" + variable.getName(), 1 )
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
            if not variable.needsLateDeclaration()
            # TODO: This filter should not be possible.
            if variable.getNeedsFree() is not None
        )
    ]

    function_doc = getConstantCode(
        context  = context,
        constant = function_doc
    )

    function_locals = []

    if context.hasLocalsDict():
        function_locals += CodeTemplates.function_dict_setup.split("\n")

    function_locals += function_parameter_decl + local_var_inits

    result = ""

    if closure_variables and context.isForCreatedFunction():
        context_access_function_impl = CodeTemplates.function_context_access_template % {
            "function_identifier" : function_identifier,
        }
    else:
        context_access_function_impl = str( CodeTemplates.function_context_unused_template )

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
            "function_locals"              : indented( function_locals ),
            "function_body"                : indented( function_codes ),
        }
    else:
        result += CodeTemplates.function_body_template % {
            "function_identifier"          : function_identifier,
            "context_access_function_impl" : context_access_function_impl,
            "parameter_objects_decl"       : ", ".join( parameter_objects_decl ),
            "function_locals"              : indented( function_locals ),
            "function_body"                : indented( function_codes ),
        }

    if context.isForCreatedFunction():
        result += entry_point_code

    return result

def getGeneratorFunctionCode( context, function_name, function_identifier,
                              parameters, closure_variables, user_variables,
                              temp_variables, function_codes, source_ref,
                              function_doc ):
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
            "_python_context->%s.setVariableNameAndValue( %s, _python_par_%s );" % (
                variable.getCodeName(),
                getConstantCode(
                    constant = variable.getName(),
                    context = context
                ),
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
        function_var_inits.append(
            "_python_context->%s.setVariableName( %s );" % (
                user_variable.getCodeName(),
                getConstantCode(
                    constant = user_variable.getName(),
                    context  = context
                )
            )
        )

    for temp_variable in temp_variables:
        assert temp_variable.isTempVariable(), variable

        if temp_variable.needsLateDeclaration():
            continue

        # TODO: This filter should not be possible.
        if temp_variable.getNeedsFree() is None:
            continue

        local_var_decl.append(
            getLocalVariableInitCode(
                context    = context,
                variable   = temp_variable,
                in_context = True
            )
        )

    for closure_variable in closure_variables:
        assert closure_variable.isShared()

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
            "function_common_context_decl"   : indented( context_decl ),
            "function_instance_context_decl" : indented( instance_context_decl ),
            "context_free"                   : indented( context_free, 2 ),
        }
    elif instance_context_decl:
        result = CodeTemplates.genfunc_context_local_only_template % {
            "function_identifier"            : function_identifier,
            "function_instance_context_decl" : indented( instance_context_decl )
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
        function_locals += CodeTemplates.function_dict_setup.split( "\n" )

    function_locals += function_var_inits

    result += CodeTemplates.genfunc_yielder_template % {
        "function_identifier" : function_identifier,
        "function_body"       : indented( function_codes, 2 ),
        "function_var_inits"  : indented( function_locals, 2 ),
        "context_access"      : indented( context_access_instance, 2 ),
    }

    code_identifier = getCodeObjectHandle(
        context       = context,
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

        context_making = context_making.split( "\n" )

        if context.isForDirectCall():
            context_making += context_copy

        generator_making = CodeTemplates.genfunc_generator_with_context_making  % {
            "function_name_obj"   : function_name_obj,
            "function_identifier" : function_identifier,
            "code_identifier"     : code_identifier.getCodeTemporaryRef()
        }
    else:
        generator_making = CodeTemplates.genfunc_generator_without_context_making  % {
            "function_name_obj"   : function_name_obj,
            "function_identifier" : function_identifier,
            "code_identifier"     : code_identifier.getCodeTemporaryRef()
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
        "context_making"             : indented( context_making, 1 ),
        "context_copy"               : indented( parameter_context_assign, 2 ),
        "generator_making"           : generator_making,
        "parameter_objects_decl"     : ", ".join( parameter_objects_decl ),
    }

    if context.isForCreatedFunction():
        result += entry_point_code

    return result
