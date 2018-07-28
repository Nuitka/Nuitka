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
""" Code to generate and interact with compiled function objects.

"""

from nuitka.PythonVersions import python_version

from .c_types.CTypePyObjectPtrs import CTypeCellObject, CTypePyObjectPtrPtr
from .CodeHelpers import generateExpressionCode, generateStatementSequenceCode
from .Contexts import PythonFunctionOutlineContext
from .Emission import SourceCodeCollector
from .ErrorCodes import (
    getErrorExitCode,
    getErrorVariableDeclarations,
    getExceptionKeeperVariableNames,
    getExceptionPreserverVariableNames,
    getMustNotGetHereCode,
    getReleaseCode
)
from .Indentation import indented
from .LabelCodes import getGotoCode, getLabelCode
from .LineNumberCodes import emitErrorLineNumberUpdateCode
from .ModuleCodes import getModuleAccessCode
from .PythonAPICodes import getReferenceExportCode
from .templates.CodeTemplatesFunction import (
    function_direct_body_template,
    template_function_body,
    template_function_direct_declaration,
    template_function_exception_exit,
    template_function_make_declaration,
    template_function_return_exit,
    template_make_function_template
)
from .TupleCodes import getTupleCreationCode
from .VariableCodes import (
    getLocalVariableCodeType,
    getLocalVariableInitCode,
    getVariableCode,
    getVariableCodeName
)


def getClosureVariableProvisionCode(context, closure_variables):
    result = []

    for variable, variable_trace in closure_variables:
        result.append(
            getVariableCode(
                context        = context,
                variable       = variable,
                variable_trace = variable_trace
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
            "struct Nuitka_CellObject *%s" % (
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

    return template_function_make_declaration % {
        "function_identifier"        : function_identifier,
        "function_creation_arg_spec" : ", ".join(
            function_creation_arg_spec
        )
    }


def getFunctionEntryPointIdentifier(function_identifier):
    return "impl_" + function_identifier


def getFunctionMakerCode(function_name, function_qualname, function_identifier,
                         code_identifier, closure_variables, defaults_name,
                         kw_defaults_name, annotations_name, function_doc,
                         context):
    # We really need this many parameters here and functions have many details,
    # that we express as variables, pylint: disable=too-many-locals
    function_creation_args = _getFunctionCreationArgs(
        defaults_name     = defaults_name,
        kw_defaults_name  = kw_defaults_name,
        annotations_name  = annotations_name,
        closure_variables = closure_variables
    )

    if python_version < 300 or function_qualname == function_name:
        function_qualname_obj = "NULL"
    else:
        function_qualname_obj = context.getConstantCode(
            constant = function_qualname
        )

    closure_copy = []

    for count, closure_variable in enumerate(closure_variables):
        closure_copy.append(
            "result->m_closure[%d] = %s;" % (

                count,
                getVariableCodeName(
                    True,
                    closure_variable
                )
            )
        )
        closure_copy.append(
            "Py_INCREF( result->m_closure[%d] );" %count
        )

    result = template_make_function_template % {
        "function_name_obj"          : context.getConstantCode(
            constant = function_name
        ),
        "function_qualname_obj"      : function_qualname_obj,
        "function_identifier"        : function_identifier,
        "function_impl_identifier"   : getFunctionEntryPointIdentifier(
            function_identifier = function_identifier,
        ),
        "function_creation_args"     : ", ".join(
            function_creation_args
        ),
        "code_identifier"            : code_identifier,
        "closure_copy"               : indented(closure_copy, 0, True),
        "function_doc"               : context.getConstantCode(
            constant = function_doc
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
        "closure_count"              : len(closure_variables),
        "module_identifier"          : getModuleAccessCode(
            context = context
        ),
    }

    return result


def generateFunctionCreationCode(to_name, expression, emit, context):
    # This is about creating functions, which is detail ridden stuff,
    # pylint: disable=too-many-locals

    function_body  = expression.getFunctionRef().getFunctionBody()
    code_object    = expression.getCodeObject()
    defaults       = expression.getDefaults()
    kw_defaults    = expression.getKwDefaults()
    annotations    = expression.getAnnotations()
    defaults_first = not expression.kw_defaults_before_defaults

    assert function_body.needsCreation(), function_body

    def handleKwDefaults():
        if kw_defaults:
            kw_defaults_name = context.allocateTempName("kw_defaults")

            assert not kw_defaults.isExpressionConstantRef() or \
                   kw_defaults.getConstant() != {}, kw_defaults.getConstant()

            generateExpressionCode(
                to_name    = kw_defaults_name,
                expression = kw_defaults,
                emit       = emit,
                context    = context
            )
        else:
            kw_defaults_name = None

        return kw_defaults_name

    def handleDefaults():
        if defaults:
            defaults_name = context.allocateTempName("defaults")

            getTupleCreationCode(
                to_name  = defaults_name,
                elements = defaults,
                emit     = emit,
                context  = context
            )
        else:
            defaults_name = None

        return defaults_name

    if defaults_first:
        defaults_name = handleDefaults()
        kw_defaults_name = handleKwDefaults()
    else:
        kw_defaults_name = handleKwDefaults()
        defaults_name = handleDefaults()

    if annotations:
        annotations_name = context.allocateTempName("annotations")

        generateExpressionCode(
            to_name    = annotations_name,
            expression = annotations,
            emit       = emit,
            context    = context,
        )
    else:
        annotations_name = None

    function_identifier = function_body.getCodeName()

    # Creation code needs to be done only once.
    if not context.hasHelperCode(function_identifier):
        maker_code = getFunctionMakerCode(
            function_name       = function_body.getFunctionName(),
            function_qualname   = function_body.getFunctionQualname(),
            function_identifier = function_identifier,
            code_identifier     = context.getCodeObjectHandle(
                code_object = code_object,
            ),
            closure_variables   = function_body.getClosureVariables(),
            defaults_name       = defaults_name,
            kw_defaults_name    = kw_defaults_name,
            annotations_name    = annotations_name,
            function_doc        = function_body.getDoc(),
            context             = context
        )

        context.addHelperCode(function_identifier, maker_code)

        function_decl = getFunctionMakerDecl(
            function_identifier = function_body.getCodeName(),
            defaults_name       = defaults_name,
            kw_defaults_name    = kw_defaults_name,
            annotations_name    = annotations_name,
            closure_variables   = function_body.getClosureVariables()
        )

        context.addDeclaration(function_identifier, function_decl)

    getFunctionCreationCode(
        to_name             = to_name,
        function_identifier = function_body.getCodeName(),
        defaults_name       = defaults_name,
        kw_defaults_name    = kw_defaults_name,
        annotations_name    = annotations_name,
        closure_variables   = expression.getClosureVariableVersions(),
        emit                = emit,
        context             = context
    )

    getReleaseCode(
        release_name = annotations_name,
        emit         = emit,
        context      = context
    )


def getFunctionCreationCode(to_name, function_identifier, defaults_name,
                            kw_defaults_name, annotations_name,
                            closure_variables, emit, context):
    args = []

    if defaults_name is not None:
        getReferenceExportCode(defaults_name, emit, context)
        args.append(defaults_name)

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
                              closure_variables, needs_check, emit, context):
    function_identifier = getFunctionEntryPointIdentifier(
        function_identifier = function_identifier
    )

    suffix_args = []

    # TODO: Does this still have to be a tripple, we are stopping to use
    # versions later in the game.
    for closure_variable, variable_trace in closure_variables:
        variable_code_name, variable_c_type = getLocalVariableCodeType(
            context        = context,
            variable       = closure_variable,
            variable_trace = variable_trace
        )

        suffix_args.append(
            variable_c_type.getVariableArgReferencePassingCode(variable_code_name)
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


    if arg_names:
        emit(
            """
{
    PyObject *dir_call_args[] = {%s};
    %s = %s( dir_call_args%s%s );
}""" % (
                ", ".join(
                    arg_names
                ),
                to_name,
                function_identifier,
                ", " if suffix_args else "",
                ", ".join(suffix_args)
            )
        )
    else:
        emit(
            "%s = %s( NULL%s%s );" % (
                to_name,
                function_identifier,
                ", " if suffix_args else "",
                ", ".join(suffix_args)
            )
        )


    # Arguments are owned to the called in direct function call.
    for arg_name in arg_names:
        if context.needsCleanup(arg_name):
            context.removeCleanupTempName(arg_name)

    getErrorExitCode(
        check_name  = to_name,
        emit        = emit,
        needs_check = needs_check,
        context     = context
    )

    context.addCleanupTempName(to_name)


def getFunctionDirectDecl(function_identifier, closure_variables, file_scope, context):
    parameter_objects_decl = [
        "PyObject **python_pars"
    ]

    for closure_variable in closure_variables:
        variable_code_name, variable_c_type = getLocalVariableCodeType(
            context        = context,
            variable       = closure_variable,
            variable_trace = None # TODO: See other uses of None
        )

        parameter_objects_decl.append(
            variable_c_type.getVariableArgDeclarationCode(variable_code_name)
        )

    result = template_function_direct_declaration % {
        "file_scope"           : file_scope,
        "function_identifier"  : function_identifier,
        "direct_call_arg_spec" : ", ".join(parameter_objects_decl),
    }

    return result


def setupFunctionLocalVariables(context, parameters, closure_variables,
                                user_variables, temp_variables):

    function_locals = []
    function_cleanup = []

    if parameters is not None:
        for count, variable in enumerate(parameters.getAllVariables()):
            function_locals.append(
                getLocalVariableInitCode(
                    context        = context,
                    variable       = variable,
                    variable_trace = None,
                    init_from      = "python_pars[ %d ]" % count
                )
            )

    # User local variable initializations
    function_locals += [
        getLocalVariableInitCode(
            context        = context,
            variable       = variable,
            variable_trace = None,
            init_from      = None
        )
        for variable in
        user_variables + tuple(
            variable
            for variable in
            sorted(
                temp_variables,
                key = lambda variable: variable.getName()
            )
        )
    ]

    for closure_variable in closure_variables:
        # Temporary variable closures are to be ignored.
        if closure_variable.isTempVariable():
            continue

        variable_code_name, variable_c_type = getLocalVariableCodeType(
            context        = context,
            variable       = closure_variable,
            variable_trace = None # TODO: Not used currently anyway but should
        )

        if variable_c_type in (CTypeCellObject, CTypePyObjectPtrPtr):
            context.setVariableType(closure_variable, variable_code_name, variable_c_type)
        else:
            assert False, (variable_code_name, variable_c_type)

    return function_locals, function_cleanup


def finalizeFunctionLocalVariables(context, function_locals, function_cleanup):
    if context.needsExceptionVariables():
        function_locals.extend(getErrorVariableDeclarations())

    for keeper_index in range(1, context.getKeeperVariableCount()+1):
        function_locals.extend(getExceptionKeeperVariableNames(keeper_index))

    for preserver_id in context.getExceptionPreserverCounts():
        function_locals.extend(getExceptionPreserverVariableNames(preserver_id))

    tmp_infos = context.getTempNameInfos()

    function_locals += [
        "%s%s%s;" % (
            tmp_type,
            ' ' if not tmp_type.endswith('*') else "",
            tmp_name
        )
        for tmp_name, tmp_type in
        tmp_infos
    ]

    function_locals += context.getFrameDeclarations()

    # TODO: Could avoid this unless try/except or try/finally with returns
    # occur.
    if context.hasTempName("return_value"):
        function_locals.append("tmp_return_value = NULL;")
    if context.hasTempName("generator_return"):
        function_locals.append("tmp_generator_return = false;")
    for tmp_name, _tmp_type in tmp_infos:
        if tmp_name.startswith("tmp_outline_return_value_"):
            function_locals.append("%s = NULL;" % tmp_name)

    for locals_dict_name in context.getLocalsDictNames():
        function_locals.append(
            "PyObject *%s = NULL;" % locals_dict_name
        )

        function_cleanup.append(
            "Py_XDECREF( %(locals_dict)s );\n" % {
                "locals_dict" : locals_dict_name
            }
        )


def getFunctionCode(context, function_identifier, parameters, closure_variables,
                    user_variables, outline_variables,
                    temp_variables, function_doc, file_scope, needs_exception_exit):

    # Functions have many details, that we express as variables, with many
    # branches to decide, pylint: disable=too-many-locals

    function_locals, function_cleanup = setupFunctionLocalVariables(
        context           = context,
        parameters        = parameters,
        closure_variables = closure_variables,
        user_variables    = user_variables + outline_variables,
        temp_variables    = temp_variables
    )

    function_codes = SourceCodeCollector()

    generateStatementSequenceCode(
        statement_sequence = context.getOwner().getBody(),
        allow_none         = True,
        emit               = function_codes,
        context            = context
    )

    finalizeFunctionLocalVariables(context, function_locals, function_cleanup)

    function_doc = context.getConstantCode(
        constant = function_doc
    )

    result = ""

    emit = SourceCodeCollector()

    getMustNotGetHereCode(
        reason  = "Return statement must have exited already.",
        context = context,
        emit    = emit
    )

    function_exit = indented(emit.codes) + "\n\n"
    del emit

    if needs_exception_exit:
        function_exit += template_function_exception_exit % {
            "function_cleanup" : indented(function_cleanup),
        }

    if context.hasTempName("return_value"):
        function_exit += template_function_return_exit % {
            "function_cleanup" : indented(function_cleanup),
        }

    if context.isForCreatedFunction():
        parameter_objects_decl = ["struct Nuitka_FunctionObject const *self"]
    else:
        parameter_objects_decl = []

    parameter_objects_decl += [
        "PyObject **python_pars"
    ]

    if context.isForDirectCall():
        for closure_variable in closure_variables:
            variable_code_name, variable_c_type = getLocalVariableCodeType(
                context        = context,
                variable       = closure_variable,
                variable_trace = None # TODO: See other uses of None.
            )

            parameter_objects_decl.append(
                variable_c_type.getVariableArgDeclarationCode(variable_code_name)
            )

        result += function_direct_body_template % {
            "file_scope"           : file_scope,
            "function_identifier"  : function_identifier,
            "direct_call_arg_spec" : ", ".join(
                parameter_objects_decl
            ),
            "function_locals"      : indented(function_locals),
            "function_body"        : indented(function_codes.codes),
            "function_exit"        : function_exit
        }
    else:
        result += template_function_body % {
            "function_identifier"    : function_identifier,
            "parameter_objects_decl" : ", ".join(parameter_objects_decl),
            "function_locals"        : indented(function_locals),
            "function_body"          : indented(function_codes.codes),
            "function_exit"          : function_exit
        }

    return result


def getExportScopeCode(cross_module):
    if cross_module:
        return "NUITKA_CROSS_MODULE"
    else:
        return "NUITKA_LOCAL_MODULE"


def generateFunctionCallCode(to_name, expression, emit, context):
    assert expression.getFunction().isExpressionFunctionCreation()

    function_body = expression.getFunction().getFunctionRef().getFunctionBody()
    function_identifier = function_body.getCodeName()

    argument_values = expression.getArgumentValues()

    arg_names = []
    for count, arg_value in enumerate(argument_values):
        arg_name = context.allocateTempName("dircall_arg%d" % (count+1))

        generateExpressionCode(
            to_name    = arg_name,
            expression = arg_value,
            emit       = emit,
            context    = context
        )

        arg_names.append(arg_name)

    context.setCurrentSourceCodeReference(
        expression.getCompatibleSourceReference()
    )

    getDirectFunctionCallCode(
        to_name             = to_name,
        function_identifier = function_identifier,
        arg_names           = arg_names,
        closure_variables   = expression.getClosureVariableVersions(),
        needs_check         = expression.getFunction().getFunctionRef().\
                                getFunctionBody().mayRaiseException(BaseException),
        emit                = emit,
        context             = context
    )


def generateFunctionOutlineCode(to_name, expression, emit, context):
    assert expression.isExpressionOutlineBody() or \
           expression.isExpressionOutlineFunction() or \
           expression.isExpressionClassBody()

    if expression.isExpressionOutlineFunctionBodyBase():
        context = PythonFunctionOutlineContext(
            parent  = context,
            outline = expression
        )

    # Need to set return target, to assign to_name from.
    old_return_release_mode = context.getReturnReleaseMode()

    return_target = context.allocateLabel("outline_result")
    old_return_target = context.setReturnTarget(return_target)

    return_value_name = context.allocateTempName("outline_return_value")
    old_return_value_name = context.setReturnValueName(return_value_name)

    if expression.isExpressionOutlineFunctionBodyBase() and \
       expression.getBody().mayRaiseException(BaseException):
        exception_target = context.allocateLabel("outline_exception")
        old_exception_target = context.setExceptionEscape(exception_target)
    else:
        exception_target = None

    generateStatementSequenceCode(
        statement_sequence = expression.getBody(),
        emit               = emit,
        context            = context,
        allow_none         = False
    )

    getMustNotGetHereCode(
        reason  = "Return statement must have exited already.",
        context = context,
        emit    = emit
    )

    if exception_target is not None:
        getLabelCode(exception_target, emit)

        context.setCurrentSourceCodeReference(expression.getSourceReference())

        emitErrorLineNumberUpdateCode(emit, context)
        getGotoCode(old_exception_target, emit)

        context.setExceptionEscape(old_exception_target)

    getLabelCode(return_target, emit)
    emit(
        "%s = %s;" % (
            to_name,
            return_value_name
        )
    )

    context.addCleanupTempName(to_name)

    # Restore previous "return" handling.
    context.setReturnTarget(old_return_target)
    context.setReturnReleaseMode(old_return_release_mode)
    context.setReturnValueName(old_return_value_name)
