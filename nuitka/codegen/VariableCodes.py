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

from nuitka.Options import isExperimental

from .c_types.CTypePyObjectPtrs import (
    CTypeCellObject,
    CTypePyObjectPtr,
    CTypePyObjectPtrPtr
)
from .CodeHelpers import generateExpressionCode
from .ErrorCodes import getCheckObjectCode, getNameReferenceErrorCode
from .templates.CodeTemplatesVariables import (
    template_del_global_unclear,
    template_read_mvar_unclear
)


def generateAssignmentVariableCode(statement, emit, context):
    tmp_name = context.allocateTempName("assign_source")

    generateExpressionCode(
        expression = statement.getAssignSource(),
        to_name    = tmp_name,
        emit       = emit,
        context    = context
    )

    getVariableAssignmentCode(
        tmp_name       = tmp_name,
        variable       = statement.getVariable(),
        variable_trace = statement.getVariableTrace(),
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

    getVariableDelCode(
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


def generateVariableReleaseCode(statement, emit, context):
    variable = statement.getVariable()

    if variable.isSharedTechnically():
        # TODO: We might start to not allocate the cell object, then a check
        # would be due. But currently we always allocate it.
        needs_check = False
    else:
        needs_check = not statement.variable_trace.mustHaveValue()

    getVariableReleaseCode(
        variable       = statement.getVariable(),
        variable_trace = statement.getVariableTrace(),
        needs_check    = needs_check,
        emit           = emit,
        context        = context
    )


def generateVariableReferenceCode(to_name, expression, emit, context):
    getVariableAccessCode(
        to_name        = to_name,
        variable       = expression.getVariable(),
        variable_trace = expression.getVariableTrace(),
        needs_check    = expression.mayRaiseException(BaseException),
        emit           = emit,
        context        = context
    )


def getVariableCodeName(in_context, variable):
    if in_context:
        # Closure case:
        return "closure_" + variable.getCodeName()
    elif variable.isParameterVariable():
        return "par_" + variable.getCodeName()
    elif variable.isTempVariable():
        return "tmp_" + variable.getCodeName()
    else:
        return "var_" + variable.getCodeName()

enable_bool_ctype = isExperimental("enable_bool_ctype")

def getPickedCType(variable, variable_trace, context):
    """ Return type to use for specific context. """

    user = context.getEntryPoint()
    owner = variable.getEntryPoint()

    if owner is user:
        if variable.isSharedTechnically():
            result = CTypeCellObject
        else:
            if enable_bool_ctype:
                shapes = variable.getTypeShapes()

                if len(shapes) > 1:
                    return CTypePyObjectPtr
                else:
                    # We are avoiding this for now.
                    assert shapes, (variable, variable_trace)

                    return shapes.pop().getCType()
            else:
                return CTypePyObjectPtr
    elif context.isForDirectCall():
        if variable.isSharedTechnically():
            result = CTypeCellObject
        else:
            result = CTypePyObjectPtrPtr
    else:
        result = CTypeCellObject

    return result


def getLocalVariableCodeType(context, variable, variable_trace):
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
        result = getVariableCodeName(
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
            result = getVariableCodeName(
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


def getVariableCode(context, variable, variable_trace):
    # Modules are simple.
    if variable.isModuleVariable():
        return getVariableCodeName(
            in_context = False,
            variable   = variable
        )

    variable_code_name, _variable_c_type = getLocalVariableCodeType(context, variable, variable_trace)
    return variable_code_name


def getLocalVariableInitCode(context, variable, variable_trace, init_from):
    assert not variable.isModuleVariable()

    variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, variable_trace)

    if variable.isLocalVariable():
        context.setVariableType(variable, variable_code_name, variable_c_type)

    return variable_c_type.getVariableInitCode(variable_code_name, init_from)


def getVariableAssignmentCode(context, emit, variable, variable_trace,
                              tmp_name, needs_release, in_place):
    # For transfer of ownership.
    if context.needsCleanup(tmp_name):
        ref_count = 1
    else:
        ref_count = 0

    if variable.isModuleVariable():
        emit(
            "UPDATE_STRING_DICT%s( moduledict_%s, (Nuitka_StringObject *)%s, %s );" % (
                ref_count,
                context.getModuleCodeName(),
                context.getConstantCode(
                    constant = variable.getName(),
                ),
                tmp_name
            )
        )

        if ref_count:
            context.removeCleanupTempName(tmp_name)
    else:
        variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, variable_trace)

        if variable.isLocalVariable():
            context.setVariableType(variable, variable_code_name, variable_c_type)

        # TODO: this was not handled previously, do not overlook when it
        # occurs.
        assert not in_place or not variable.isTempVariable()

        emit(
            variable_c_type.getLocalVariableAssignCode(
                variable_code_name = variable_code_name,
                needs_release      = needs_release,
                tmp_name           = tmp_name,
                ref_count          = ref_count,
                in_place           = in_place
            )
        )

        if ref_count:
            context.removeCleanupTempName(tmp_name)


def generateModuleVariableAccessCode(to_name, variable_name, needs_check,
                                      emit, context):
    emit(
        template_read_mvar_unclear % {
            "module_identifier" : context.getModuleCodeName(),
            "tmp_name"          : to_name,
            "var_name"          : context.getConstantCode(
                constant = variable_name
            )
        }
    )
    if needs_check:
        getNameReferenceErrorCode(
            variable_name = variable_name,
            condition     = "%s == NULL" % to_name,
            emit          = emit,
            context       = context
        )
    else:
        getCheckObjectCode(to_name, emit)



def getVariableAccessCode(to_name, variable, variable_trace, needs_check, emit, context):
    if variable.isModuleVariable():
        generateModuleVariableAccessCode(
            to_name       = to_name,
            variable_name = variable.getName(),
            needs_check   = needs_check,
            emit          = emit,
            context       = context
        )
    else:
        variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, variable_trace)

        variable_c_type.getVariableObjectAccessCode(
            to_name            = to_name,
            variable_code_name = variable_code_name,
            variable           = variable,
            needs_check        = needs_check,
            emit               = emit,
            context            = context
        )


def getVariableDelCode(variable, variable_trace, previous_trace, tolerant,
                       needs_check, emit, context):
    if variable.isModuleVariable():
        res_name = context.getIntResName()

        emit(
            template_del_global_unclear % {
                "module_identifier" : context.getModuleCodeName(),
                "res_name"          : res_name,
                "var_name"          : context.getConstantCode(
                    constant = variable.getName()
                )
            }
        )

        if needs_check and not tolerant:
            getNameReferenceErrorCode(
                variable_name = variable.getName(),
                condition     = "%s == -1" % res_name,
                emit          = emit,
                context       = context
            )
    elif variable.isLocalVariable():
        variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, previous_trace)
        variable_code_name_new, variable_c_new_type = getLocalVariableCodeType(context, variable, variable_trace)

        # TODO: We need to split this operation in two parts. Release and init
        # are not one thing.
        assert variable_c_type == variable_c_new_type

        context.setVariableType(variable, variable_code_name_new, variable_c_new_type)

        variable_c_type.getDeleteObjectCode(
            variable_code_name = variable_code_name,
            tolerant           = tolerant,
            needs_check        = needs_check,
            variable           = variable,
            emit               = emit,
            context            = context
        )
    elif variable.isTempVariable():
        variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, previous_trace)
        _variable_code_name, variable_c_new_type = getLocalVariableCodeType(context, variable, variable_trace)

        # TODO: We need to split this operation in two parts. Release and init
        # are not one thing.
        assert variable_c_type is variable_c_new_type

        variable_c_type.getDeleteObjectCode(
            variable_code_name = variable_code_name,
            tolerant           = tolerant,
            needs_check        = needs_check,
            variable           = variable,
            emit               = emit,
            context            = context
        )

    else:
        assert False, variable


def getVariableReleaseCode(variable, variable_trace, needs_check, emit, context):
    assert not variable.isModuleVariable()

    variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, variable_trace)

    variable_c_type.getReleaseCode(
        variable_code_name = variable_code_name,
        needs_check        = needs_check,
        emit               = emit
    )
