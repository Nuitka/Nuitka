#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Code to generate and interact with compiled function objects.

"""

from nuitka.PythonVersions import python_version
from nuitka.Tracing import general

from .c_types.CTypePyObjectPointers import CTypeCellObject, CTypePyObjectPtrPtr
from .CodeHelpers import (
    decideConversionCheckNeeded,
    generateExpressionCode,
    generateStatementSequenceCode,
    withObjectCodeTemporaryAssignment,
)
from .CodeObjectCodes import getCodeObjectAccessCode
from .Contexts import PythonFunctionOutlineContext
from .Emission import SourceCodeCollector
from .ErrorCodes import getErrorExitCode, getMustNotGetHereCode, getReleaseCode
from .Indentation import indented
from .LabelCodes import getGotoCode, getLabelCode
from .LineNumberCodes import emitErrorLineNumberUpdateCode
from .ModuleCodes import getModuleAccessCode
from .PythonAPICodes import generateCAPIObjectCode, getReferenceExportCode
from .templates.CodeTemplatesFunction import (
    function_direct_body_template,
    template_function_body,
    template_function_direct_declaration,
    template_function_exception_exit,
    template_function_make_declaration,
    template_function_return_exit,
    template_make_function,
    template_maker_function_body,
)
from .TupleCodes import getTupleCreationCode
from .VariableCodes import (
    decideLocalVariableCodeType,
    getLocalVariableDeclaration,
)


def getFunctionCreationArgs(
    defaults_name, kw_defaults_name, annotations_name, closure_variables
):
    result = ["PyThreadState *tstate"]

    if defaults_name is not None:
        result.append("PyObject *defaults")

    if kw_defaults_name is not None:
        result.append("PyObject *kw_defaults")

    if annotations_name is not None:
        result.append("PyObject *annotations")

    if closure_variables:
        result.append("struct Nuitka_CellObject **closure")

    return result


def getFunctionMakerDecl(
    function_identifier,
    closure_variables,
    defaults_name,
    kw_defaults_name,
    annotations_name,
):
    function_creation_args = getFunctionCreationArgs(
        defaults_name=defaults_name,
        kw_defaults_name=kw_defaults_name,
        annotations_name=annotations_name,
        closure_variables=closure_variables,
    )

    return template_function_make_declaration % {
        "function_identifier": function_identifier,
        "function_creation_args": ", ".join(function_creation_args),
    }


def _getFunctionEntryPointIdentifier(function_identifier):
    return "impl_" + function_identifier


def _getFunctionMakerIdentifier(function_identifier):
    return "MAKE_FUNCTION_" + function_identifier


def getFunctionQualnameObj(owner, context):
    """Get code to pass to function alike object creation for qualname.

    Qualname for functions existed for Python3, generators only after
    3.5 and coroutines and asyncgen for as long as they existed.

    If identical to the name, we do not pass it as a value, but
    NULL instead.
    """

    if owner.isExpressionFunctionBody():
        min_version = 0x300
    else:
        min_version = 0x350

    if python_version < min_version:
        return "NULL"

    function_qualname = owner.getFunctionQualname()

    if function_qualname == owner.getFunctionName():
        return "NULL"
    else:
        return context.getConstantCode(constant=function_qualname)


def getFunctionMakerCode(
    function_body,
    function_identifier,
    closure_variables,
    defaults_name,
    kw_defaults_name,
    annotations_name,
    function_doc,
    context,
):
    # We really need this many parameters here and functions have many details,
    # that we express as variables, pylint: disable=too-many-locals
    function_creation_args = getFunctionCreationArgs(
        defaults_name=defaults_name,
        kw_defaults_name=kw_defaults_name,
        annotations_name=annotations_name,
        closure_variables=closure_variables,
    )

    if function_doc is None:
        function_doc = "NULL"
    else:
        function_doc = context.getConstantCode(constant=function_doc)

    (
        is_constant_returning,
        constant_return_value,
    ) = function_body.getConstantReturnValue()

    if is_constant_returning:
        function_impl_identifier = "NULL"

        if constant_return_value is None:
            # Default value, spare the code for common case.
            constant_return_code = ""
        elif constant_return_value is True:
            constant_return_code = "Nuitka_Function_EnableConstReturnTrue(result);"
        elif constant_return_value is False:
            constant_return_code = "Nuitka_Function_EnableConstReturnFalse(result);"
        else:
            constant_return_code = (
                "Nuitka_Function_EnableConstReturnGeneric(result, %s);"
                % context.getConstantCode(constant_return_value)
            )
    else:
        function_impl_identifier = _getFunctionEntryPointIdentifier(
            function_identifier=function_identifier
        )
        constant_return_code = ""

    function_maker_identifier = _getFunctionMakerIdentifier(
        function_identifier=function_identifier
    )

    module_identifier = getModuleAccessCode(context=context)

    result = template_maker_function_body % {
        "function_name_obj": context.getConstantCode(
            constant=function_body.getFunctionName()
        ),
        "function_qualname_obj": getFunctionQualnameObj(function_body, context),
        "function_maker_identifier": function_maker_identifier,
        "function_impl_identifier": function_impl_identifier,
        "function_creation_args": ", ".join(function_creation_args),
        "code_identifier": getCodeObjectAccessCode(
            code_object=function_body.getCodeObject(), context=context
        ),
        "function_doc": function_doc,
        "defaults": "defaults" if defaults_name else "NULL",
        "kw_defaults": "kw_defaults" if kw_defaults_name else "NULL",
        "annotations": "annotations" if annotations_name else "NULL",
        "closure_count": len(closure_variables),
        "closure_name": "closure" if closure_variables else "NULL",
        "module_identifier": module_identifier,
        "constant_return_code": indented(constant_return_code),
    }

    # TODO: Make it optional, only dill plugin really uses that table to
    # transport the C code implementation pointers.
    if function_impl_identifier != "NULL":
        context.addFunctionCreationInfo(function_impl_identifier)

    return result


def generateFunctionCreationCode(to_name, expression, emit, context):
    # This is about creating functions, which is detail ridden stuff,
    # pylint: disable=too-many-locals

    function_body = expression.subnode_function_ref.getFunctionBody()
    defaults = expression.subnode_defaults
    kw_defaults = expression.subnode_kw_defaults
    annotations = expression.subnode_annotations
    defaults_first = not expression.kw_defaults_before_defaults

    assert function_body.needsCreation(), function_body

    def handleKwDefaults():
        if kw_defaults:
            kw_defaults_name = context.allocateTempName("kw_defaults")

            assert not kw_defaults.isExpressionConstantDictEmptyRef(), kw_defaults

            generateExpressionCode(
                to_name=kw_defaults_name,
                expression=kw_defaults,
                emit=emit,
                context=context,
            )
        else:
            kw_defaults_name = None

        return kw_defaults_name

    def handleDefaults():
        if defaults:
            defaults_name = context.allocateTempName("defaults")

            getTupleCreationCode(
                to_name=defaults_name, elements=defaults, emit=emit, context=context
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
            to_name=annotations_name, expression=annotations, emit=emit, context=context
        )
    else:
        annotations_name = None

    function_identifier = function_body.getCodeName()

    # Creation code needs to be done only once.
    if not context.hasHelperCode(function_identifier):
        closure_variables = function_body.getClosureVariables()

        maker_code = getFunctionMakerCode(
            function_body=function_body,
            function_identifier=function_identifier,
            closure_variables=closure_variables,
            defaults_name=defaults_name,
            kw_defaults_name=kw_defaults_name,
            annotations_name=annotations_name,
            function_doc=function_body.getDoc(),
            context=context,
        )

        context.addHelperCode(function_identifier, maker_code)

        function_decl = getFunctionMakerDecl(
            function_identifier=function_body.getCodeName(),
            closure_variables=closure_variables,
            defaults_name=defaults_name,
            kw_defaults_name=kw_defaults_name,
            annotations_name=annotations_name,
        )

        context.addDeclaration(function_identifier, function_decl)

    getFunctionCreationCode(
        to_name=to_name,
        function_identifier=function_body.getCodeName(),
        defaults_name=defaults_name,
        kw_defaults_name=kw_defaults_name,
        annotations_name=annotations_name,
        closure_variables=expression.getClosureVariableVersions(),
        emit=emit,
        context=context,
    )

    getReleaseCode(release_name=annotations_name, emit=emit, context=context)


def getClosureCopyCode(closure_variables, context):
    """Get code to copy closure variables storage.

    This gets used by generator/coroutine/asyncgen with varying "closure_type".
    """
    if closure_variables:
        closure_name = context.allocateTempName(
            "closure", "struct Nuitka_CellObject *[%d]" % len(closure_variables)
        )
    else:
        closure_name = None

    closure_copy = []

    for count, (variable, variable_trace) in enumerate(closure_variables):
        variable_declaration = getLocalVariableDeclaration(
            context, variable, variable_trace
        )

        target_cell_code = "%s[%d]" % (closure_name, count)

        variable_c_type = variable_declaration.getCType()

        variable_c_type.getCellObjectAssignmentCode(
            target_cell_code=target_cell_code,
            variable_code_name=variable_declaration,
            emit=closure_copy.append,
        )

    return closure_name, closure_copy


def getFunctionCreationCode(
    to_name,
    function_identifier,
    defaults_name,
    kw_defaults_name,
    annotations_name,
    closure_variables,
    emit,
    context,
):
    args = ["tstate"]

    if defaults_name is not None:
        getReferenceExportCode(defaults_name, emit, context)
        args.append(defaults_name)

    if kw_defaults_name is not None:
        args.append(kw_defaults_name)

    if annotations_name is not None:
        args.append(annotations_name)

    closure_name, closure_copy = getClosureCopyCode(
        closure_variables=closure_variables, context=context
    )

    if closure_name:
        args.append(closure_name)

    function_maker_identifier = _getFunctionMakerIdentifier(
        function_identifier=function_identifier
    )

    emit(
        template_make_function
        % {
            "to_name": to_name,
            "function_maker_identifier": function_maker_identifier,
            "args": ", ".join(str(arg) for arg in args),
            "closure_copy": indented(closure_copy, 0, True),
        }
    )

    if context.needsCleanup(defaults_name):
        context.removeCleanupTempName(defaults_name)
    if context.needsCleanup(kw_defaults_name):
        context.removeCleanupTempName(kw_defaults_name)
    if context.needsCleanup(annotations_name):
        context.removeCleanupTempName(annotations_name)

    # No error checks, this supposedly, cannot fail.
    context.addCleanupTempName(to_name)


def getDirectFunctionCallCode(
    to_name,
    function_identifier,
    arg_names,
    closure_variables,
    needs_check,
    emit,
    context,
):
    function_identifier = _getFunctionEntryPointIdentifier(
        function_identifier=function_identifier
    )

    suffix_args = []

    # TODO: Does this still have to be a triple, we are stopping to use
    # versions later in the game.
    for closure_variable, variable_trace in closure_variables:
        variable_declaration = getLocalVariableDeclaration(
            context=context, variable=closure_variable, variable_trace=variable_trace
        )

        variable_c_type = variable_declaration.getCType()

        suffix_args.append(
            variable_c_type.getVariableArgReferencePassingCode(variable_declaration)
        )

    # TODO: We ought to not assume references for direct calls, or make a
    # profile if an argument needs a reference at all. Most functions don't
    # bother to release a called argument by "del" or assignment to it. We
    # could well know that ahead of time.
    for arg_name in arg_names:
        if context.needsCleanup(arg_name):
            context.removeCleanupTempName(arg_name)
        else:
            emit("Py_INCREF(%s);" % arg_name)

    if arg_names:
        emit(
            """
{
    PyObject *dir_call_args[] = {%s};
    %s = %s(tstate, dir_call_args%s%s);
}"""
            % (
                ", ".join(str(arg_name) for arg_name in arg_names),
                to_name,
                function_identifier,
                ", " if suffix_args else "",
                ", ".join(str(arg) for arg in suffix_args),
            )
        )
    else:
        emit(
            "%s = %s(tstate, NULL%s%s);"
            % (
                to_name,
                function_identifier,
                ", " if suffix_args else "",
                ", ".join(str(arg) for arg in suffix_args),
            )
        )

    # Arguments are owned to the called in direct function call.
    for arg_name in arg_names:
        if context.needsCleanup(arg_name):
            context.removeCleanupTempName(arg_name)

    getErrorExitCode(
        check_name=to_name, emit=emit, needs_check=needs_check, context=context
    )

    context.addCleanupTempName(to_name)


def getFunctionDirectDecl(function_identifier, closure_variables, file_scope, context):
    parameter_objects_decl = ["PyObject **python_pars"]

    for closure_variable in closure_variables:
        variable_declaration = getLocalVariableDeclaration(
            context=context,
            variable=closure_variable,
            variable_trace=None,  # TODO: See other uses of None
        )

        variable_c_type = variable_declaration.getCType()

        parameter_objects_decl.append(
            variable_c_type.getVariableArgDeclarationCode(variable_declaration)
        )

    result = template_function_direct_declaration % {
        "file_scope": file_scope,
        "function_identifier": function_identifier,
        "direct_call_arg_spec": ", ".join(parameter_objects_decl),
    }

    return result


def setupFunctionLocalVariables(
    context, parameters, closure_variables, user_variables, temp_variables
):
    # Parameter variable initializations
    if parameters is not None:
        for count, variable in enumerate(parameters.getAllVariables()):
            variable_code_name, variable_c_type = decideLocalVariableCodeType(
                context=context, variable=variable
            )

            variable_declaration = context.variable_storage.addVariableDeclarationTop(
                variable_c_type.c_type,
                variable_code_name,
                variable_c_type.getInitValue("python_pars[%d]" % count),
            )

            context.setVariableType(variable, variable_declaration)

    # User local variable initializations
    for variable in user_variables:
        variable_code_name, variable_c_type = decideLocalVariableCodeType(
            context=context, variable=variable
        )

        # Delay cell variable initialization for outlines to their own code.
        if (
            variable_c_type is CTypeCellObject
            and variable.owner.isExpressionOutlineFunctionBase()
        ):
            init_value = "NULL"
        else:
            init_value = variable_c_type.getInitValue(None)

        variable_declaration = context.variable_storage.addVariableDeclarationTop(
            variable_c_type.c_type, variable_code_name, init_value
        )

        context.setVariableType(variable, variable_declaration)

    for variable in sorted(temp_variables, key=lambda variable: variable.getName()):
        variable_code_name, variable_c_type = decideLocalVariableCodeType(
            context=context, variable=variable
        )

        context.variable_storage.addVariableDeclarationTop(
            variable_c_type.c_type,
            variable_code_name,
            variable_c_type.getInitValue(None),
        )

    for closure_variable in closure_variables:
        variable_code_name, variable_c_type = decideLocalVariableCodeType(
            context=context, variable=closure_variable
        )

        variable_declaration = context.variable_storage.addVariableDeclarationClosure(
            variable_c_type.c_type, variable_code_name
        )

        assert variable_c_type in (
            CTypeCellObject,
            CTypePyObjectPtrPtr,
        ), variable_c_type

        if not closure_variable.isTempVariable():
            context.setVariableType(closure_variable, variable_declaration)


def finalizeFunctionLocalVariables(context):
    function_cleanup = []

    # TODO: Many times it will not be necessary to release locals dict, because
    # they already were, but our tracing doesn't yet allow us to know.
    for locals_declaration in sorted(context.getLocalsDictNames(), key=str):
        function_cleanup.append(
            "Py_XDECREF(%(locals_dict)s);\n" % {"locals_dict": locals_declaration}
        )

    # Automatic variable releases if any.
    for variable in context.getOwner().getFunctionVariablesWithAutoReleases():
        variable_declaration = getLocalVariableDeclaration(
            context=context,
            variable=variable,
            variable_trace=None,  # TODO: See other uses of None.
        )
        function_cleanup.append("CHECK_OBJECT(%s);" % variable_declaration)
        function_cleanup.append("Py_DECREF(%s);" % variable_declaration)

    return function_cleanup


def getFunctionCode(
    context,
    function_identifier,
    parameters,
    closure_variables,
    user_variables,
    temp_variables,
    function_doc,
    file_scope,
    needs_exception_exit,
):
    try:
        return _getFunctionCode(
            context=context,
            function_identifier=function_identifier,
            parameters=parameters,
            closure_variables=closure_variables,
            user_variables=user_variables,
            temp_variables=temp_variables,
            function_doc=function_doc,
            file_scope=file_scope,
            needs_exception_exit=needs_exception_exit,
        )
    except Exception:
        general.warning("Problem creating function code %r." % function_identifier)
        raise


def _getFunctionCode(
    context,
    function_identifier,
    parameters,
    closure_variables,
    user_variables,
    temp_variables,
    function_doc,
    file_scope,
    needs_exception_exit,
):
    # Functions have many details, that we express as variables, with many
    # branches to decide, pylint: disable=too-many-locals

    setupFunctionLocalVariables(
        context=context,
        parameters=parameters,
        closure_variables=closure_variables,
        user_variables=user_variables,
        temp_variables=temp_variables,
    )

    function_codes = SourceCodeCollector()

    generateStatementSequenceCode(
        statement_sequence=context.getOwner().subnode_body,
        allow_none=True,
        emit=function_codes,
        context=context,
    )

    function_cleanup = finalizeFunctionLocalVariables(context=context)

    function_locals = context.variable_storage.makeCFunctionLevelDeclarations()

    function_doc = context.getConstantCode(constant=function_doc)

    result = ""

    emit = SourceCodeCollector()

    getMustNotGetHereCode(
        reason="Return statement must have exited already.", emit=emit
    )

    function_exit = indented(emit.codes) + "\n\n"
    del emit

    if needs_exception_exit:
        (
            exception_state_name,
            _exception_lineno,
        ) = context.variable_storage.getExceptionVariableDescriptions()

        function_exit += template_function_exception_exit % {
            "function_cleanup": indented(function_cleanup),
            "exception_state_name": exception_state_name,
        }

    if context.hasTempName("return_value"):
        function_exit += template_function_return_exit % {
            "function_cleanup": indented(function_cleanup)
        }

    if context.isForCreatedFunction():
        parameter_objects_decl = ["struct Nuitka_FunctionObject const *self"]
    else:
        parameter_objects_decl = []

    parameter_objects_decl.append("PyObject **python_pars")

    if context.isForDirectCall():
        for closure_variable in closure_variables:
            variable_declaration = getLocalVariableDeclaration(
                context=context,
                variable=closure_variable,
                variable_trace=None,  # TODO: See other uses of None.
            )

            variable_c_type = variable_declaration.getCType()

            parameter_objects_decl.append(
                variable_c_type.getVariableArgDeclarationCode(variable_declaration)
            )

        result += function_direct_body_template % {
            "file_scope": file_scope,
            "function_identifier": function_identifier,
            "direct_call_arg_spec": ", ".join(parameter_objects_decl),
            "function_locals": indented(function_locals),
            "function_body": indented(function_codes.codes),
            "function_exit": function_exit,
        }
    else:
        result += template_function_body % {
            "function_identifier": function_identifier,
            "parameter_objects_decl": ", ".join(parameter_objects_decl),
            "function_locals": indented(function_locals),
            "function_body": indented(function_codes.codes),
            "function_exit": function_exit,
        }

    return result


def getExportScopeCode(cross_module):
    if cross_module:
        return "NUITKA_CROSS_MODULE"
    else:
        return "NUITKA_LOCAL_MODULE"


def generateFunctionCallCode(to_name, expression, emit, context):
    assert expression.subnode_function.isExpressionFunctionCreation()

    function_body = expression.subnode_function.subnode_function_ref.getFunctionBody()
    function_identifier = function_body.getCodeName()

    argument_values = expression.subnode_values

    arg_names = []
    for count, arg_value in enumerate(argument_values, 1):
        arg_name = context.allocateTempName("direct_call_arg%d" % count)

        generateExpressionCode(
            to_name=arg_name, expression=arg_value, emit=emit, context=context
        )

        arg_names.append(arg_name)

    context.setCurrentSourceCodeReference(expression.getCompatibleSourceReference())

    with withObjectCodeTemporaryAssignment(
        to_name, "call_result", expression, emit, context
    ) as value_name:
        getDirectFunctionCallCode(
            to_name=value_name,
            function_identifier=function_identifier,
            arg_names=arg_names,
            closure_variables=expression.getClosureVariableVersions(),
            needs_check=expression.subnode_function.subnode_function_ref.getFunctionBody().mayRaiseException(
                BaseException
            ),
            emit=emit,
            context=context,
        )


def generateFunctionOutlineCode(to_name, expression, emit, context):
    assert (
        expression.isExpressionOutlineBody()
        or expression.isExpressionOutlineFunctionBase()
    )

    if expression.isExpressionOutlineFunctionBase():
        context = PythonFunctionOutlineContext(parent=context, outline=expression)

        for variable in expression.getUserLocalVariables():
            variable_declaration = getLocalVariableDeclaration(
                context=context, variable=variable, variable_trace=None
            )

            if variable_declaration.getCType() is CTypeCellObject:
                emit("%s = Nuitka_Cell_NewEmpty();" % variable_declaration)

    # Need to set return target, to assign to_name from.

    return_target = context.allocateLabel("outline_result")
    old_return_target = context.setReturnTarget(return_target)
    old_return_release_mode = context.setReturnReleaseMode(False)

    # TODO: Put the return value name as that to_name.c_type too.

    if (
        expression.isExpressionOutlineFunctionBase()
        and expression.subnode_body.mayRaiseException(BaseException)
    ):
        exception_target = context.allocateLabel("outline_exception")
        old_exception_target = context.setExceptionEscape(exception_target)
    else:
        exception_target = None

    with withObjectCodeTemporaryAssignment(
        to_name, "outline_return_value", expression, emit, context
    ) as return_value_name:
        old_return_value_name = context.setReturnValueName(return_value_name)

        generateStatementSequenceCode(
            statement_sequence=expression.subnode_body,
            emit=emit,
            context=context,
            allow_none=False,
        )

        context.addCleanupTempName(return_value_name)

        getMustNotGetHereCode(
            reason="Return statement must have exited already.", emit=emit
        )

        if exception_target is not None:
            getLabelCode(exception_target, emit)

            context.setCurrentSourceCodeReference(expression.getSourceReference())

            emitErrorLineNumberUpdateCode(emit, context)
            getGotoCode(old_exception_target, emit)

            context.setExceptionEscape(old_exception_target)

        # TODO: An outline that cannot return, could be converted probably into
        # something else, maybe mere side effects.
        if expression.subnode_body.mayReturn():
            getLabelCode(return_target, emit)

    # Restore previous "return" handling.
    context.setReturnTarget(old_return_target)
    context.setReturnReleaseMode(old_return_release_mode)
    context.setReturnValueName(old_return_value_name)


def generateFunctionErrorStrCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        # TODO: Should be inline this for
        capi="_PyObject_FunctionStr",
        tstate=False,
        arg_desc=(("func_arg", expression.subnode_value),),
        may_raise=False,
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
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
