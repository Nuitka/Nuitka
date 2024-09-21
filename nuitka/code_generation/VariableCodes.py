#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Low level variable code generation.

"""

from nuitka.nodes.shapes.BuiltinTypeShapes import (
    tshape_bool,
    tshape_int_or_long,
)
from nuitka.PythonVersions import python_version

from .c_types.CTypeNuitkaBooleans import CTypeNuitkaBoolEnum
from .c_types.CTypePyObjectPointers import (
    CTypeCellObject,
    CTypePyObjectPtr,
    CTypePyObjectPtrPtr,
)
from .CodeHelpers import (
    decideConversionCheckNeeded,
    generateExpressionCode,
    withObjectCodeTemporaryAssignment2,
)
from .ErrorCodes import (
    getAssertionCode,
    getErrorExitCode,
    getLocalVariableReferenceErrorCode,
    getNameReferenceErrorCode,
)
from .VariableDeclarations import VariableDeclaration


def generateAssignmentVariableCode(statement, emit, context):
    assign_source = statement.subnode_source

    variable = statement.getVariable()
    variable_trace = statement.getVariableTrace()

    if variable.isModuleVariable():
        # Use "object" for module variables.
        tmp_name = context.allocateTempName("assign_source")
    else:
        source_shape = assign_source.getTypeShape()

        variable_declaration = getLocalVariableDeclaration(
            context, variable, variable_trace
        )

        if source_shape is tshape_bool and variable_declaration.c_type == "nuitka_bool":
            tmp_name = context.allocateTempName("assign_source", "nuitka_bool")
        elif (
            source_shape is tshape_int_or_long
            and variable_declaration.c_type == "nuitka_ilong"
        ):
            tmp_name = context.allocateTempName("assign_source", "nuitka_ilong")
        else:
            tmp_name = context.allocateTempName("assign_source")

    generateExpressionCode(
        expression=assign_source, to_name=tmp_name, emit=emit, context=context
    )

    getVariableAssignmentCode(
        tmp_name=tmp_name,
        variable=variable,
        variable_trace=variable_trace,
        needs_release=statement.needsReleasePreviousValue(),
        inplace=statement.isInplaceSuspect(),
        emit=emit,
        context=context,
    )

    # Ownership of that reference must have been transferred.
    assert not context.needsCleanup(tmp_name), (statement.source_ref, tmp_name)


def generateDelVariableCode(statement, emit, context):
    with context.withCurrentSourceCodeReference(statement.getSourceReference()):
        _getVariableDelCode(
            variable=statement.getVariable(),
            variable_trace=statement.variable_trace,
            previous_trace=statement.previous_trace,
            tolerant=statement.is_tolerant,
            needs_check=statement.is_tolerant
            or statement.mayRaiseException(BaseException),
            emit=emit,
            context=context,
        )


def getModuleVariableAccessorCodeName(module_identifier, variable_name):
    # For non-ascii names use encoding.
    if str is not bytes:
        variable_name = variable_name.encode("ascii", "c_identifier").decode()

    return "module_var_accessor_%s_$$_%s" % (module_identifier, variable_name)


def getModuleVariableReferenceCode(
    to_name, variable_name, use_caching, needs_check, conversion_check, emit, context
):
    owner = context.getOwner()

    context.setModuleVariableAccessorCaching(variable_name, use_caching)

    with withObjectCodeTemporaryAssignment2(
        to_name, "mvar_value", conversion_check, emit, context
    ) as value_name:
        emit(
            "%(value_name)s = %(module_variable_accessor)s(tstate);"
            % {
                "value_name": value_name,
                "module_variable_accessor": getModuleVariableAccessorCodeName(
                    context.getModuleCodeName(), variable_name
                ),
            }
        )

        if needs_check:
            if (
                python_version < 0x300
                and not owner.isCompiledPythonModule()
                and not owner.isExpressionClassBodyBase()
            ):
                error_helper_name = "RAISE_CURRENT_EXCEPTION_GLOBAL_NAME_ERROR"
            else:
                error_helper_name = "RAISE_CURRENT_EXCEPTION_NAME_ERROR"

            (
                exception_state_name,
                _exception_lineno,
            ) = context.variable_storage.getExceptionVariableDescriptions()

            emit(
                """\
if (unlikely(%(value_name)s == NULL)) {
    %(error_helper_name)s(tstate, &%(exception_state_name)s, %(var_name)s);
}
"""
                % {
                    "value_name": value_name,
                    "error_helper_name": error_helper_name,
                    "var_name": context.getConstantCode(constant=variable_name),
                    "exception_state_name": exception_state_name,
                }
            )

        getErrorExitCode(
            check_name=value_name,
            emit=emit,
            context=context,
            fetched_exception=True,
            needs_check=needs_check,
        )


def getNonModuleVariableReferenceCode(
    to_name, variable, variable_trace, needs_check, conversion_check, emit, context
):
    if variable.isModuleVariable():
        assert False
    else:
        variable_declaration = getLocalVariableDeclaration(
            context, variable, variable_trace
        )

        value_name = variable_declaration.getCType().emitValueAccessCode(
            value_name=variable_declaration, emit=emit, context=context
        )

        if needs_check:
            condition = value_name.getCType().getInitTestConditionCode(
                value_name, inverted=True
            )

            getLocalVariableReferenceErrorCode(
                variable=variable, condition=condition, emit=emit, context=context
            )
        else:
            value_name.getCType().emitValueAssertionCode(
                value_name=value_name, emit=emit
            )

        to_name.getCType().emitAssignConversionCode(
            to_name=to_name,
            value_name=value_name,
            needs_check=conversion_check,
            emit=emit,
            context=context,
        )


def generateVariableReferenceCode(to_name, expression, emit, context):
    variable = expression.getVariable()
    variable_trace = expression.getVariableTrace()

    needs_check = expression.mayRaiseException(BaseException)

    if variable.isModuleVariable():
        user = context.getOwner()
        variable_name = variable.getName()

        if python_version < 0x360:
            # Python2 doesn't have the means to do it, we got some acceleration
            # for it still, but no real caching.
            use_caching = False
        elif user.isCompiledPythonModule():
            # For module level code, cache module variable access only if inside
            # a loop.
            use_caching = False

            if not context.isModuleVariableAccessorCaching(variable_name):
                if expression.getContainingLoopNode() is not None:
                    use_caching = True
        else:
            use_caching = True

        getModuleVariableReferenceCode(
            to_name=to_name,
            variable_name=variable_name,
            use_caching=use_caching,
            needs_check=needs_check,
            conversion_check=decideConversionCheckNeeded(to_name, expression),
            emit=emit,
            context=context,
        )
    else:
        getNonModuleVariableReferenceCode(
            to_name=to_name,
            variable=variable,
            variable_trace=variable_trace,
            needs_check=needs_check,
            conversion_check=decideConversionCheckNeeded(to_name, expression),
            emit=emit,
            context=context,
        )


def _getVariableCodeName(in_context, variable):
    if in_context:
        # Closure case:
        return "closure_" + variable.getCodeName()
    elif variable.isParameterVariable():
        return "par_" + variable.getCodeName()
    elif variable.isTempVariable():
        return "tmp_" + variable.getCodeName()
    else:
        return "var_" + variable.getCodeName()


def getPickedCType(variable, context):
    """Return type to use for specific context."""

    user = context.getEntryPoint()
    owner = variable.getEntryPoint()

    if owner is user:
        if variable.isSharedTechnically():
            # TODO: That need not really be an impedient, we could share pointers to
            # everything.

            result = CTypeCellObject
        else:
            shapes = variable.getTypeShapes()

            if len(shapes) != 1:
                # Avoiding this for now, but we will have to use our enum
                # based code variants, either generated or hard coded in
                # the future.
                result = CTypePyObjectPtr
            else:
                result = shapes.pop().getCType()

    elif context.isForDirectCall():
        if variable.isSharedTechnically():
            result = CTypeCellObject
        else:
            result = CTypePyObjectPtrPtr
    else:
        result = CTypeCellObject

    return result


def decideLocalVariableCodeType(context, variable):
    # Now must be local or temporary variable.

    # Complexity should be moved out of here, pylint: disable=too-many-branches

    user = context.getOwner()
    owner = variable.getOwner()

    user = user.getEntryPoint()

    prefix = ""

    if owner.isExpressionOutlineFunctionBase():
        entry_point = owner.getEntryPoint()

        prefix = (
            "outline_%d_"
            % entry_point.getTraceCollection().getOutlineFunctions().index(owner)
        )
        owner = entry_point

    if variable.isTempVariableBool():
        c_type = CTypeNuitkaBoolEnum
    else:
        c_type = getPickedCType(variable, context)

    if owner is user:
        result = _getVariableCodeName(in_context=False, variable=variable)

        result = prefix + result
    elif context.isForDirectCall():
        if user.isExpressionGeneratorObjectBody():
            closure_index = user.getClosureVariableIndex(variable)

            result = "generator->m_closure[%d]" % closure_index
        elif user.isExpressionCoroutineObjectBody():
            closure_index = user.getClosureVariableIndex(variable)

            result = "coroutine->m_closure[%d]" % closure_index
        elif user.isExpressionAsyncgenObjectBody():
            closure_index = user.getClosureVariableIndex(variable)

            result = "asyncgen->m_closure[%d]" % closure_index
        else:
            result = _getVariableCodeName(in_context=True, variable=variable)

            result = prefix + result
    else:
        closure_index = user.getClosureVariableIndex(variable)

        if user.isExpressionGeneratorObjectBody():
            result = "generator->m_closure[%d]" % closure_index
        elif user.isExpressionCoroutineObjectBody():
            result = "coroutine->m_closure[%d]" % closure_index
        elif user.isExpressionAsyncgenObjectBody():
            result = "asyncgen->m_closure[%d]" % closure_index
        else:
            # TODO: If this were context.getContextObjectName() this would be
            # a one liner.

            result = "self->m_closure[%d]" % closure_index

    return result, c_type


def getLocalVariableDeclaration(context, variable, variable_trace):
    # TODO: Decide if we will use variable trace, pylint: disable=unused-argument

    # Now must be local or temporary variable.

    user = context.getOwner()
    owner = variable.getOwner()

    user = user.getEntryPoint()

    prefix = ""

    if owner.isExpressionOutlineFunctionBase():
        entry_point = owner.getEntryPoint()

        prefix = (
            "outline_%d_"
            % entry_point.getTraceCollection().getOutlineFunctions().index(owner)
        )
        owner = entry_point

    if owner is user:
        result = _getVariableCodeName(in_context=False, variable=variable)

        result = prefix + result

        result = context.variable_storage.getVariableDeclarationTop(result)

        assert result is not None, variable

        return result
    else:
        closure_index = user.getClosureVariableIndex(variable)

        return context.variable_storage.getVariableDeclarationClosure(closure_index)


def getVariableAssignmentCode(
    context, emit, variable, variable_trace, tmp_name, needs_release, inplace
):
    # For transfer of ownership.
    if context.needsCleanup(tmp_name):
        ref_count = 1
    else:
        ref_count = 0

    if variable.isModuleVariable():
        variable_declaration = VariableDeclaration(
            "module_var", variable.getName(), None, None
        )
    else:
        variable_declaration = getLocalVariableDeclaration(
            context, variable, variable_trace
        )

        assert variable_declaration, (variable, context)

        if variable.isLocalVariable():
            context.setVariableType(variable, variable_declaration)

    variable_declaration.getCType().emitVariableAssignCode(
        value_name=variable_declaration,
        needs_release=needs_release,
        tmp_name=tmp_name,
        ref_count=ref_count,
        inplace=inplace,
        emit=emit,
        context=context,
    )

    # print(variable_declaration.getCType())


def _getVariableDelCode(
    variable, variable_trace, previous_trace, tolerant, needs_check, emit, context
):
    if variable.isModuleVariable():
        variable_declaration_old = VariableDeclaration(
            "module_var", variable.getName(), None, None
        )
        variable_declaration_new = variable_declaration_old
    else:
        variable_declaration_old = getLocalVariableDeclaration(
            context, variable, previous_trace
        )
        variable_declaration_new = getLocalVariableDeclaration(
            context, variable, variable_trace
        )

        # TODO: We need to split this operation in two parts. Release and init
        # are not one thing, until then require this.
        assert variable_declaration_old == variable_declaration_new

        if variable.isLocalVariable():
            context.setVariableType(variable, variable_declaration_new)

    if needs_check and not tolerant:
        to_name = context.getBoolResName()
    else:
        to_name = None

    variable_declaration_old.getCType().getDeleteObjectCode(
        to_name=to_name,
        value_name=variable_declaration_old,
        tolerant=tolerant,
        needs_check=needs_check,
        emit=emit,
        context=context,
    )

    if to_name is not None:
        if variable.isModuleVariable():
            getNameReferenceErrorCode(
                variable_name=variable.getName(),
                condition="%s == false" % to_name,
                emit=emit,
                context=context,
            )
        elif variable.isLocalVariable():
            getLocalVariableReferenceErrorCode(
                variable=variable,
                condition="%s == false" % to_name,
                emit=emit,
                context=context,
            )
        else:
            getAssertionCode(check="%s != false" % to_name, emit=emit)


def generateVariableReleaseCode(statement, emit, context):
    variable = statement.getVariable()

    # Only for normal variables we do this.
    assert not variable.isModuleVariable()

    variable_trace = statement.getVariableTrace()

    if variable.isSharedTechnically():
        # TODO: We might start to not allocate the cell object, then a check
        # would be due. But currently we always allocate it.
        needs_check = False
    else:
        needs_check = not variable_trace.mustHaveValue()

    value_name = getLocalVariableDeclaration(context, variable, variable_trace)

    c_type = value_name.getCType()

    if not needs_check:
        c_type.emitReleaseAssertionCode(value_name=value_name, emit=emit)

    c_type.getReleaseCode(value_name=value_name, needs_check=needs_check, emit=emit)

    c_type.emitReInitCode(value_name=value_name, emit=emit)


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
