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
""" Low level variable code generation.

"""

from nuitka.nodes.shapes.BuiltinTypeShapes import ShapeTypeBool

from .c_types.CTypePyObjectPtrs import (
    CTypeCellObject,
    CTypePyObjectPtr,
    CTypePyObjectPtrPtr
)
from .CodeHelpers import decideConversionCheckNeeded, generateExpressionCode
from .ErrorCodes import (
    getAssertionCode,
    getLocalVariableReferenceErrorCode,
    getNameReferenceErrorCode
)
from .VariableDeclarations import VariableDeclaration


def generateAssignmentVariableCode(statement, emit, context):
    assign_source = statement.getAssignSource()

    variable = statement.getVariable()
    variable_trace = statement.getVariableTrace()

    if variable.isModuleVariable():
        # Use "object" for module variables.
        tmp_name = context.allocateTempName("assign_source")
    else:
        source_shape = assign_source.getTypeShape()

        variable_declaration = getLocalVariableDeclaration(context, variable, variable_trace)

        if source_shape is ShapeTypeBool and \
           variable_declaration.c_type == "nuitka_bool":
            tmp_name = context.allocateTempName("assign_source", "nuitka_bool")
        else:
            tmp_name = context.allocateTempName("assign_source")

    generateExpressionCode(
        expression = assign_source,
        to_name    = tmp_name,
        emit       = emit,
        context    = context
    )

    getVariableAssignmentCode(
        tmp_name       = tmp_name,
        variable       = variable,
        variable_trace = variable_trace,
        needs_release  = statement.needsReleasePreviousValue(),
        in_place       = statement.inplace_suspect,
        emit           = emit,
        context        = context
    )

    # Ownership of that reference must have been transfered.
    assert not context.needsCleanup(tmp_name)


def generateDelVariableCode(statement, emit, context):
    old_source_ref = context.setCurrentSourceCodeReference(
        statement.getSourceReference()
    )

    _getVariableDelCode(
        variable       = statement.getVariable(),
        variable_trace = statement.variable_trace,
        previous_trace = statement.previous_trace,
        tolerant       = statement.isTolerant(),
        needs_check    = statement.isTolerant() or \
                         statement.mayRaiseException(BaseException),
        emit           = emit,
        context        = context
    )

    context.setCurrentSourceCodeReference(old_source_ref)




def getVariableReferenceCode(to_name, variable, variable_trace, needs_check,
                             conversion_check, emit, context):
    if variable.isModuleVariable():
        variable_declaration = VariableDeclaration(
            "module_var",
            variable.getName(),
            None,
            None
        )
    else:
        variable_declaration = getLocalVariableDeclaration(context, variable, variable_trace)

    value_name = variable_declaration.getCType().emitValueAccessCode(
        value_name = variable_declaration,
        emit       = emit,
        context    = context
    )

    if needs_check:
        condition = value_name.getCType().getLocalVariableInitTestCode(value_name, True)

        if variable.isModuleVariable():
            getNameReferenceErrorCode(
                variable_name = variable.getName(),
                condition     = condition,
                emit          = emit,
                context       = context
            )
        else:
            getLocalVariableReferenceErrorCode(
                variable  = variable,
                condition = condition,
                emit      = emit,
                context   = context
            )
    else:
        value_name.getCType().emitValueAssertionCode(
            value_name = value_name,
            emit       = emit,
            context    = context
        )

    to_name.getCType().emitAssignConversionCode(
        to_name     = to_name,
        value_name  = value_name,
        needs_check = conversion_check,
        emit        = emit,
        context     = context
    )


def generateVariableReferenceCode(to_name, expression, emit, context):
    variable       = expression.getVariable()
    variable_trace = expression.getVariableTrace()

    needs_check    = expression.mayRaiseException(BaseException)

    getVariableReferenceCode(
        to_name          = to_name,
        variable         = variable,
        variable_trace   = variable_trace,
        needs_check      = needs_check,
        conversion_check = decideConversionCheckNeeded(to_name, expression),
        emit             = emit,
        context          = context
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


def getPickedCType(variable, variable_trace, context):
    """ Return type to use for specific context. """

    user = context.getEntryPoint()
    owner = variable.getEntryPoint()

    if owner is user:
        if variable.isSharedTechnically():
            result = CTypeCellObject
        else:
            shapes = variable.getTypeShapes()

            if len(shapes) > 1:
                return CTypePyObjectPtr
            else:
                # We are avoiding this for now.
                assert shapes, (variable, variable_trace)

                return shapes.pop().getCType()
    elif context.isForDirectCall():
        if variable.isSharedTechnically():
            result = CTypeCellObject
        else:
            result = CTypePyObjectPtrPtr
    else:
        result = CTypeCellObject

    return result


def decideLocalVariableCodeType(context, variable, variable_trace):
    # Now must be local or temporary variable.

    user = context.getOwner()
    owner = variable.getOwner()

    user = user.getEntryPoint()

    prefix = ""

    if owner.isExpressionOutlineFunction() or owner.isExpressionClassBody():
        entry_point = owner.getEntryPoint()

        prefix = "outline_%d_" % entry_point.getTraceCollection().getOutlineFunctions().index(owner)
        owner = entry_point

    c_type = getPickedCType(variable, variable_trace, context)

    if owner is user:
        result = _getVariableCodeName(
            in_context = False,
            variable   = variable
        )

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
            result = _getVariableCodeName(
                in_context = True,
                variable   = variable
            )

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

    if owner.isExpressionOutlineFunction() or owner.isExpressionClassBody():
        entry_point = owner.getEntryPoint()

        prefix = "outline_%d_" % entry_point.getTraceCollection().getOutlineFunctions().index(owner)
        owner = entry_point

    if owner is user:
        result = _getVariableCodeName(
            in_context = False,
            variable   = variable
        )

        result = prefix + result

        result = context.variable_storage.getVariableDeclarationTop(result)

        assert result is not None, variable

        return result
    else:
        closure_index = user.getClosureVariableIndex(variable)

        return context.variable_storage.getVariableDeclarationClosure(closure_index)


def getVariableAssignmentCode(context, emit, variable, variable_trace,
                              tmp_name, needs_release, in_place):
    # For transfer of ownership.
    if context.needsCleanup(tmp_name):
        ref_count = 1
    else:
        ref_count = 0

    if variable.isModuleVariable():
        variable_declaration = VariableDeclaration(
            "module_var",
            variable.getName(),
            None,
            None
        )
    else:
        variable_declaration = getLocalVariableDeclaration(context, variable, variable_trace)

        assert variable_declaration, (variable, context)

        if variable.isLocalVariable():
            context.setVariableType(variable, variable_declaration)

        # TODO: If this was not handled previously, do not overlook when it
        # occurs.
        assert not in_place or not variable.isTempVariable()

    variable_declaration.getCType().emitVariableAssignCode(
        value_name    = variable_declaration,
        needs_release = needs_release,
        tmp_name      = tmp_name,
        ref_count     = ref_count,
        in_place      = in_place,
        emit          = emit,
        context       = context
    )

    if ref_count:
        context.removeCleanupTempName(tmp_name)


def _getVariableDelCode(variable, variable_trace, previous_trace, tolerant,
                        needs_check, emit, context):
    if variable.isModuleVariable():
        variable_declaration_old = VariableDeclaration(
            "module_var",
            variable.getName(),
            None,
            None
        )
        variable_declaration_new = variable_declaration_old
    else:
        variable_declaration_old = getLocalVariableDeclaration(context, variable, previous_trace)
        variable_declaration_new = getLocalVariableDeclaration(context, variable, variable_trace)

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
        to_name     = to_name,
        value_name  = variable_declaration_old,
        tolerant    = tolerant,
        needs_check = needs_check,
        emit        = emit,
        context     = context
    )

    if needs_check and not tolerant:
        if variable.isModuleVariable():
            getNameReferenceErrorCode(
                variable_name = variable.getName(),
                condition     = "%s == false" % to_name,
                emit          = emit,
                context       = context
            )
        elif variable.isLocalVariable():
            getLocalVariableReferenceErrorCode(
                variable  = variable,
                condition = "%s == false" % to_name,
                emit      = emit,
                context   = context
            )
        else:
            getAssertionCode(
                check = "%s != false" % to_name,
                emit  = emit
            )


def generateVariableReleaseCode(statement, emit, context):
    variable = statement.getVariable()

    if variable.isSharedTechnically():
        # TODO: We might start to not allocate the cell object, then a check
        # would be due. But currently we always allocate it.
        needs_check = False
    else:
        needs_check = not statement.variable_trace.mustHaveValue()

    _getVariableReleaseCode(
        variable       = statement.getVariable(),
        variable_trace = statement.getVariableTrace(),
        needs_check    = needs_check,
        emit           = emit,
        context        = context
    )


def _getVariableReleaseCode(variable, variable_trace, needs_check, emit, context):
    assert not variable.isModuleVariable()

    variable_declaration = getLocalVariableDeclaration(context, variable, variable_trace)

    variable_declaration.getCType().getReleaseCode(
        variable_code_name = variable_declaration,
        needs_check        = needs_check,
        emit               = emit
    )
