#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Low level variable code generation."""

from nuitka.nodes.shapes.BuiltinTypeShapes import (
    tshape_bool,
    tshape_int_or_long,
)
from nuitka.PythonVersions import isPythonWithGil, python_version
from nuitka.States import states
from nuitka.utils.CStrings import encodePythonIdentifierToC

from .c_types.CTypeNuitkaBooleans import CTypeNuitkaBoolEnum
from .c_types.CTypePyObjectPointers import (
    CTypeCellObject,
    CTypePyCellObject,
    CTypePyObjectPtr,
    CTypePyObjectPtrPtr,
)
from .CodeHelpers import (
    decideConversionCheckNeeded,
    generateExpressionCode,
    isObjectReferenceValue,
    promoteBorrowedValuesForVariable,
    withObjectCodeTemporaryAssignment2,
)
from .DeferredReleaseCodes import checkDeferredReleaseUse
from .ErrorCodes import (
    getAssertionCode,
    getErrorExitCode,
    getLocalVariableReferenceErrorCode,
    getNameReferenceErrorCode,
)
from .LineNumberCodes import emitLineNumberUpdateCode
from .VariableDeclarations import VariableDeclaration


def generateAssignmentVariableCode(statement, emit, context):
    assign_source = statement.subnode_source

    variable = statement.getVariable()
    variable_trace = statement.getVariableTrace()

    if variable.isModuleVariable():
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

    # The in-place transfer assumes the variable still owns the left value. If
    # the operation had to take its own reference, then the result owns a
    # reference and must be stored with normal release handling.
    inplace = statement.isInplaceSuspect() and not context.needsCleanup(tmp_name)

    getVariableAssignmentCode(
        tmp_name=tmp_name,
        variable=variable,
        variable_trace=variable_trace,
        needs_release=statement.needsReleasePreviousValue(),
        inplace=inplace,
        emit=emit,
        context=context,
    )

    assert not context.needsCleanup(tmp_name), (statement.source_ref, tmp_name)


def generateDelVariableCode(statement, emit, context):
    with context.withCurrentSourceCodeReference(statement.getSourceReference()):
        if states.is_full_compat:
            emitLineNumberUpdateCode(None, emit, context)

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
    return "module_var_accessor_" + encodePythonIdentifierToC(
        "%s.%s" % (module_identifier, variable_name)
    )


def getModuleVariableReferenceCode(
    to_name,
    variable_name,
    use_caching,
    needs_check,
    conversion_check,
    no_global_deletion,
    emit,
    context,
):
    owner = context.getOwner()

    needs_global_name = (
        python_version < 0x300
        and not owner.isCompiledPythonModule()
        and not owner.isExpressionClassBodyBase()
    )

    context.registerModuleVariableAccessor(
        variable_name=variable_name,
        caching=use_caching,
        needs_check=needs_check,
        needs_global_name=needs_global_name,
        no_global_deletion=no_global_deletion,
    )

    with withObjectCodeTemporaryAssignment2(
        to_name, "mvar_value", conversion_check, emit, context
    ) as value_name:
        accessor_function_name = getModuleVariableAccessorCodeName(
            context.getModuleCodeName(), variable_name
        )

        if needs_check:
            (
                exception_state_name,
                _exception_lineno,
            ) = context.getExceptionVariableDescriptions()

            accessor_function_name += (
                "$checked_global" if needs_global_name else "$checked"
            )

            emit(
                "%s = %s(tstate, &%s);"
                % (value_name, accessor_function_name, exception_state_name)
            )

            getErrorExitCode(
                check_name=value_name,
                emit=emit,
                context=context,
                fetched_exception=True,
            )
        else:
            accessor_function_name += "$infallible"

            emit("%s = %s(tstate);" % (value_name, accessor_function_name))

        if not isPythonWithGil():
            context.addCleanupTempName(value_name)


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
        variable_name = variable.getName()

        if python_version < 0x360:
            # Dictionary version tags (ma_version_tag, PEP 509) require Python 3.6+.
            use_caching = False
        else:
            user = context.getOwner()
            while user.isExpressionOutlineFunction():
                user = user.provider
                context = context.parent

            if user.isCompiledPythonModule():
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
            no_global_deletion=variable.isModuleVariableNoGlobalDeletion(),
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

    if (
        variable.writers
        and to_name.code_name.startswith("tmp_")
        and isObjectReferenceValue(to_name)
        and not context.needsCleanup(to_name)
    ):
        context.registerBorrowedValue(variable=variable, tmp_name=to_name)


def _getVariableCodeName(in_context, variable):
    if in_context:
        return "closure_" + variable.getVariableCodeName()
    elif variable.isParameterVariable():
        return "par_" + variable.getVariableCodeName()
    elif variable.isTempVariable():
        return "tmp_" + variable.getVariableCodeName()
    else:
        return "var_" + variable.getVariableCodeName()


if python_version >= 0x360:

    def _pickCellCType(variable):
        if variable.getName() == "__class__":
            return CTypePyCellObject

        if variable.needsPyCell():
            return CTypePyCellObject

        return CTypeCellObject

else:

    def _pickCellCType(variable):
        # pylint: disable=unused-argument
        return CTypeCellObject


def getPickedCType(variable, context):
    user = context.getEntryPoint()
    owner = variable.getEntryPoint()

    if owner is user:
        if variable.isSharedTechnically():
            # TODO: That need not really be an impediment, we could share pointers to
            # everything.
            return _pickCellCType(variable)
        else:
            shapes = variable.getTypeShapes()

            if len(shapes) != 1:
                result = CTypePyObjectPtr
            else:
                result = shapes.pop().getCType()

    elif context.isForDirectCall():
        if variable.isSharedTechnically():
            return _pickCellCType(variable)
        else:
            result = CTypePyObjectPtrPtr
    else:
        return _pickCellCType(variable)

    return result


def decideLocalVariableCodeType(context, variable):
    # pylint: disable=too-many-branches

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


def getClosureCopyCode(closure_variables, context):
    """Return '(closure_name, closure_copy_lines)' for 'closure_variables'."""
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


def getVariableAssignmentCode(
    context, emit, variable, variable_trace, tmp_name, needs_release, inplace
):
    checkDeferredReleaseUse(
        usage="assignment",
        tmp_name=tmp_name,
        context=context,
        detail=variable.getName(),
    )

    if not inplace:
        promoteBorrowedValuesForVariable(variable=variable, emit=emit, context=context)

    if context.needsCleanup(tmp_name):
        ref_count = 1
    else:
        ref_count = 0

    if variable.isModuleVariable():
        variable_declaration = VariableDeclaration(
            c_type="module_var",
            code_name=variable.getName(),
            init_value=None,
            heap_name=None,
            struct_name=None,
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


def _getVariableDelCode(
    variable, variable_trace, previous_trace, tolerant, needs_check, emit, context
):
    if variable.isModuleVariable():
        variable_declaration_old = VariableDeclaration(
            c_type="module_var",
            code_name=variable.getName(),
            init_value=None,
            heap_name=None,
            struct_name=None,
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

    promoteBorrowedValuesForVariable(variable=variable, emit=emit, context=context)

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
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
