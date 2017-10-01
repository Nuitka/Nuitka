#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .CodeHelpers import generateExpressionCode
from .Emission import SourceCodeCollector
from .ErrorCodes import getCheckObjectCode, getNameReferenceErrorCode
from .Indentation import indented
from .templates.CodeTemplatesVariables import (
    template_del_global_unclear,
    template_read_maybe_local_unclear,
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
        tmp_name      = tmp_name,
        variable      = statement.getVariable(),
        version       = statement.getVariableVersion(),
        needs_release = statement.needsReleasePreviousValue(),
        in_place      = statement.inplace_suspect,
        emit          = emit,
        context       = context
    )

    # Ownership of that reference must have been transfered.
    assert not context.needsCleanup(tmp_name)


def generateDelVariableCode(statement, emit, context):
    old_source_ref = context.setCurrentSourceCodeReference(
        statement.getSourceReference()
    )

    getVariableDelCode(
        variable    = statement.getVariable(),
        new_version = statement.variable_trace.getVersion(),
        old_version = statement.previous_trace.getVersion(),
        tolerant    = statement.isTolerant(),
        needs_check = statement.isTolerant() or \
                      statement.mayRaiseException(BaseException),
        emit        = emit,
        context     = context
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
        variable    = statement.getVariable(),
        version     = statement.getVariableVersion(),
        needs_check = needs_check,
        emit        = emit,
        context     = context
    )


def generateVariableReferenceCode(to_name, expression, emit, context):
    getVariableAccessCode(
        to_name     = to_name,
        variable    = expression.getVariable(),
        version     = expression.getVariableVersion(),
        needs_check = expression.mayRaiseException(BaseException),
        emit        = emit,
        context     = context
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


def getLocalVariableCodeType(context, variable, version):
    # Now must be local or temporary variable.

    user = context.getOwner()
    owner = variable.getOwner()

    user = user.getEntryPoint()

    prefix = ""

    if owner.isExpressionOutlineFunction() or owner.isExpressionClassBody():
        entry_point = owner.getEntryPoint()

        prefix = "outline_%d_" % entry_point.getTraceCollection().getOutlineFunctions().index(owner)
        owner = entry_point

    variable_trace = user.getTraceCollection().getVariableTrace(variable, version)

    c_type = variable_trace.getPickedCType(context)

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


def getVariableCode(context, variable, version):
    # Modules are simple.
    if variable.isModuleVariable():
        return getVariableCodeName(
            in_context = False,
            variable   = variable
        )

    variable_code_name, _variable_c_type = getLocalVariableCodeType(context, variable, version)
    return variable_code_name


def getLocalVariableInitCode(context, variable, version, init_from):
    assert not variable.isModuleVariable()

    variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, version)

    if variable.isLocalVariable():
        context.setVariableType(variable, variable_code_name, variable_c_type)

    return variable_c_type.getVariableInitCode(variable_code_name, init_from)


def getVariableAssignmentCode(context, emit, variable, version,
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
        variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, version)

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


def _generateModuleVariableAccessCode(to_name, variable_name, needs_check,
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


def generateLocalsDictVariableRefCode(to_name, expression, emit, context):
    variable_name = expression.getVariableName()

    fallback_emit = SourceCodeCollector()

    getVariableAccessCode(
        to_name     = to_name,
        variable    = expression.getFallbackVariable(),
        version     = expression.getFallbackVariableVersion(),
        needs_check = True,
        emit        = fallback_emit,
        context     = context
    )


    emit(
        template_read_maybe_local_unclear % {
            "locals_dict" : context.getLocalsDictName(),
            "fallback"    : indented(fallback_emit.codes),
            "tmp_name"    : to_name,
            "var_name"    : context.getConstantCode(
                constant = variable_name
            )
        }
    )


def getVariableAccessCode(to_name, variable, version, needs_check, emit, context):
    if variable.isModuleVariable():
        _generateModuleVariableAccessCode(
            to_name       = to_name,
            variable_name = variable.getName(),
            needs_check   = needs_check,
            emit          = emit,
            context       = context
        )
    else:
        variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, version)

        variable_c_type.getVariableObjectAccessCode(
            to_name            = to_name,
            variable_code_name = variable_code_name,
            variable           = variable,
            needs_check        = needs_check,
            emit               = emit,
            context            = context
        )


def getVariableDelCode(variable, old_version, new_version, tolerant,
                       needs_check, emit, context):
    if variable.isModuleVariable():
        check = not tolerant

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

        # TODO: Apply needs_check for module variables too.
        if check:
            getNameReferenceErrorCode(
                variable_name = variable.getName(),
                condition     = "%s == -1" % res_name,
                emit          = emit,
                context       = context
            )
    elif variable.isLocalVariable():
        variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, old_version)
        variable_code_name_new, variable_c_new_type = getLocalVariableCodeType(context, variable, new_version)

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
        variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, old_version)
        _variable_code_name, variable_c_new_type = getLocalVariableCodeType(context, variable, new_version)

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


def getVariableReleaseCode(variable, version, needs_check, emit, context):
    assert not variable.isModuleVariable()

    variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, version)

    variable_c_type.getReleaseCode(
        variable_code_name = variable_code_name,
        needs_check        = needs_check,
        emit               = emit
    )
