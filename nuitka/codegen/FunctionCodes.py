#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .VariableCodes import getVariableCode

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

def getClosureVariableProvisionCode( context, closure_variables ):
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
                "PyObjectSharedTempVariable" if closure_variable.isTempVariableReference() else "PyObjectSharedLocalVariable",
                closure_variable.getCodeName()
            )
        )

    return result

def _getFuncDefaultValue( defaults_identifier ):
    if defaults_identifier.isConstantIdentifier():
        return defaults_identifier
    else:
        return Identifier( "defaults", 1 )


def _getFuncKwDefaultValue( kw_defaults_identifier ):
    if kw_defaults_identifier.isConstantIdentifier():
        if kw_defaults_identifier.getConstant():
            return kw_defaults_identifier
        else:
            return SpecialConstantIdentifier( constant_value = None )
    else:
        return Identifier( "kwdefaults", 1 )

def _getFuncAnnotationsValue( annotations_identifier ):
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
            defaultToNullIdentifier( extra_argument ).getCodeTemporaryRef()
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
