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

from nuitka import Options, Variables
from nuitka.PythonVersions import python_version

from .Emission import SourceCodeCollector
from .ErrorCodes import (
    getAssertionCode,
    getErrorFormatExitBoolCode,
    getErrorFormatExitCode
)
from .Helpers import generateExpressionCode
from .Indentation import indented
from .templates.CodeTemplatesVariables import (
    template_del_global_unclear,
    template_del_local_intolerant,
    template_del_local_known,
    template_del_local_tolerant,
    template_del_shared_intolerant,
    template_del_shared_known,
    template_del_shared_tolerant,
    template_read_local,
    template_read_maybe_local_unclear,
    template_read_mvar_unclear,
    template_read_shared_known,
    template_read_shared_unclear,
    template_release_clear,
    template_release_unclear,
    template_write_local_clear_ref0,
    template_write_local_clear_ref1,
    template_write_local_empty_ref0,
    template_write_local_empty_ref1,
    template_write_local_inplace,
    template_write_local_unclear_ref0,
    template_write_local_unclear_ref1,
    template_write_shared_clear_ref0,
    template_write_shared_clear_ref1,
    template_write_shared_inplace,
    template_write_shared_unclear_ref0,
    template_write_shared_unclear_ref1
)


def generateAssignmentVariableCode(statement, emit, context):
    variable_ref  = statement.getTargetVariableRef()
    value         = statement.getAssignSource()

    tmp_name = context.allocateTempName("assign_source")

    generateExpressionCode(
        expression = value,
        to_name    = tmp_name,
        emit       = emit,
        context    = context
    )

    getVariableAssignmentCode(
        tmp_name      = tmp_name,
        variable      = variable_ref.getVariable(),
        version       = variable_ref.getVariableVersion(),
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
        variable    = statement.getTargetVariableRef().getVariable(),
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

    variable_trace = user.trace_collection.getVariableTrace(variable, version)

    c_type = variable_trace.getPickedCType(context)

    if owner is user:
        result = getVariableCodeName(
            in_context = False,
            variable   = variable
        )
    elif context.isForDirectCall():

        if user.isExpressionGeneratorObjectBody():
            closure_index = user.getClosureVariables().index(variable)

            result = "generator->m_closure[%d]" % closure_index
        elif user.isExpressionCoroutineObjectBody():
            closure_index = user.getClosureVariables().index(variable)

            result = "coroutine->m_closure[%d]" % closure_index
        elif user.isExpressionAsyncgenObjectBody():
            closure_index = user.getClosureVariables().index(variable)

            result = "asyncgen->m_closure[%d]" % closure_index
        else:
            result = getVariableCodeName(
                in_context = True,
                variable   = variable
            )
    else:
        closure_index = user.getClosureVariables().index(variable)

        if user.isExpressionGeneratorObjectBody():
            result = "generator->m_closure[%d]" % closure_index
        elif user.isExpressionCoroutineObjectBody():
            result = "coroutine->m_closure[%d]" % closure_index
        elif user.isExpressionAsyncgenObjectBody():
            result = "asyncgen->m_closure[%d]" % closure_index
        else:
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


def getLocalVariableObjectAccessCode(context, variable, version):
    variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, version)

    if variable_c_type == "struct Nuitka_CellObject *":
        # TODO: Why not use PyCell_GET for readability.
        return variable_code_name + "->ob_ref"
    elif variable_c_type == "PyObject **":
        return '*' + variable_code_name
    elif variable_c_type == "PyObject *":
        return variable_code_name
    else:
        assert False, variable_c_type


def getLocalVariableInitCode(context, variable, version, init_from = None):
    assert not variable.isModuleVariable()

    variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, version)

    if variable_c_type == "struct Nuitka_CellObject *":
        # TODO: Single out "init_from" only user, so it becomes sure that we
        # get a reference transferred here in these cases.
        if init_from is not None:
            init_value = "PyCell_NEW1( %s )" % init_from
        else:
            init_value = "PyCell_EMPTY()"
    elif variable_c_type == "PyObject *":
        if init_from is None:
            init_from = "NULL"

        init_value = "%s" % init_from
    else:
        assert False, variable

    if variable.isLocalVariable():
        context.setVariableType(variable, variable_code_name, variable_c_type)

    return "%s%s%s = %s;" % (
        variable_c_type,
        ' ' if variable_c_type[-1] not in "*&" else "",
        variable_code_name,
        init_value
    )


def getVariableAssignmentCode(context, emit, variable, version,
                              tmp_name, needs_release, in_place):
    # Many different cases, as this must be, pylint: disable=too-many-branches,too-many-statements

    assert isinstance(variable, Variables.Variable), variable

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
    elif variable.isLocalVariable():
        variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, version)

        context.setVariableType(variable, variable_code_name, variable_c_type)

        if in_place:
            # Releasing is not an issue here, local variable reference never
            # gave a reference, and the in-place code deals with possible
            # replacement/release.
            if variable_c_type == "struct Nuitka_CellObject *":
                template = template_write_shared_inplace
            else:
                template = template_write_local_inplace

        elif variable_c_type == "struct Nuitka_CellObject *":
            if ref_count:
                if needs_release is False:
                    template = template_write_shared_clear_ref0
                else:
                    template = template_write_shared_unclear_ref0
            else:
                if needs_release is False:
                    template = template_write_shared_clear_ref1
                else:
                    template = template_write_shared_unclear_ref1
        else:
            assert variable_c_type == "PyObject *", variable_c_type

            if ref_count:
                if needs_release is False:
                    template = template_write_local_empty_ref0
                elif needs_release is True:
                    template = template_write_local_clear_ref0
                else:
                    template = template_write_local_unclear_ref0
            else:
                if needs_release is False:
                    template = template_write_local_empty_ref1
                elif needs_release is True:
                    template = template_write_local_clear_ref1
                else:
                    template = template_write_local_unclear_ref1

        emit(
            template % {
                "identifier" : variable_code_name,
                "tmp_name"   : tmp_name
            }
        )

        if ref_count:
            context.removeCleanupTempName(tmp_name)
    elif variable.isTempVariable():
        variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, version)

        if variable_c_type == "struct Nuitka_CellObject *":
            if ref_count:
                template = template_write_shared_unclear_ref0
            else:
                template = template_write_shared_unclear_ref1
        elif variable_c_type in ("PyObject *", "PyObject **"):
            if ref_count:
                if needs_release is False:
                    template = template_write_local_empty_ref0
                elif needs_release is True:
                    template = template_write_local_clear_ref0
                else:
                    template = template_write_local_unclear_ref0
            else:
                if needs_release is False:
                    template = template_write_local_empty_ref1
                elif needs_release is True:
                    template = template_write_local_clear_ref1
                else:
                    template = template_write_local_unclear_ref1
        else:
            assert False, variable_c_type

        emit(
            template % {
                "identifier" : getLocalVariableObjectAccessCode(context, variable, version),
                "tmp_name"   : tmp_name
            }
        )

        if ref_count:
            context.removeCleanupTempName(tmp_name)
    else:
        assert False, variable


def _generateModuleVariableAccessCode(to_name, variable_name, needs_check, emit, context):
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
        if python_version < 340 and \
           not context.isCompiledPythonModule() and \
           not context.getOwner().isExpressionClassBody():
            error_message = "global name '%s' is not defined"
        else:
            error_message = "name '%s' is not defined"

        getErrorFormatExitCode(
            check_name = to_name,
            exception  = "PyExc_NameError",
            args       = (
                error_message,
                variable_name
            ),
            emit       = emit,
            context    = context
        )
    elif Options.isDebug():
        emit("CHECK_OBJECT( %s );" % to_name)


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
            "locals_dict" : "locals_dict",
            "fallback"    : indented(fallback_emit.codes),
            "tmp_name"    : to_name,
            "var_name"    : context.getConstantCode(
                constant = variable_name
            )
        }
    )


def getVariableAccessCode(to_name, variable, version, needs_check, emit, context):
    # Many different cases, as this must be, pylint: disable=too-many-branches

    assert isinstance(variable, Variables.Variable), variable

    if variable.isModuleVariable():
        _generateModuleVariableAccessCode(
            to_name       = to_name,
            variable_name = variable.getName(),
            needs_check   = needs_check,
            emit          = emit,
            context       = context
        )

        return
    elif variable.isLocalVariable():
        variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, version)

        if variable_c_type == "struct Nuitka_CellObject *":
            if not needs_check:
                template = template_read_shared_unclear
            else:
                template = template_read_shared_known

            emit(
                template % {
                    "tmp_name"   : to_name,
                    "identifier" : variable_code_name
                }
            )
        else:
            template = template_read_local

            emit(
                template % {
                    "tmp_name"   : to_name,
                    "identifier" : getLocalVariableObjectAccessCode(context, variable, version)
                }
            )

        if needs_check:
            if variable.getOwner() is not context.getOwner():
                getErrorFormatExitCode(
                    check_name = to_name,
                    exception  = "PyExc_NameError",
                    args       = (
                        """\
free variable '%s' referenced before assignment in enclosing scope""",
                        variable.getName()
                    ),
                    emit       = emit,
                    context    = context
                )
            else:
                getErrorFormatExitCode(
                    check_name = to_name,
                    exception  = "PyExc_UnboundLocalError",
                    args       = (
                        """\
local variable '%s' referenced before assignment""",
                        variable.getName()
                    ),
                    emit       = emit,
                    context    = context
                )
        elif Options.isDebug():
            emit("CHECK_OBJECT( %s );" % to_name)

        return
    elif variable.isTempVariable():
        variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, version)

        if variable_c_type == "struct Nuitka_CellObject *":
            template = template_read_shared_unclear

            emit(
                template % {
                    "tmp_name"   : to_name,
                    "identifier" : variable_code_name
                }
            )

            if needs_check:
                getErrorFormatExitCode(
                    check_name = to_name,
                    exception  = "PyExc_NameError",
                    args       = (
                        """\
free variable '%s' referenced before assignment in enclosing scope""",
                        variable.getName()
                    ),
                    emit       = emit,
                    context    = context
                )
            elif Options.isDebug():
                emit("CHECK_OBJECT( %s );" % to_name)

            return
        elif variable_c_type in ("PyObject *", "PyObject **"):
            template = template_read_local

            emit(
                template % {
                    "tmp_name"   : to_name,
                    "identifier" : getLocalVariableObjectAccessCode(context, variable, version)
                }
            )

            if needs_check:
                getErrorFormatExitCode(
                    check_name = to_name,
                    exception  = "PyExc_UnboundLocalError",
                    args       = (
                        """\
local variable '%s' referenced before assignment""",
                        variable.getName()
                    ),
                    emit       = emit,
                    context    = context
                )
            elif Options.isDebug():
                emit("CHECK_OBJECT( %s );" % to_name)

            return
        else:
            assert False, variable_c_type

    assert False, variable


def getVariableDelCode(variable, old_version, new_version, tolerant,
                       needs_check, emit, context):
    # Many different cases, as this must be, pylint: disable=too-many-branches,too-many-statements
    assert isinstance(variable, Variables.Variable), variable

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
            getErrorFormatExitBoolCode(
                condition = "%s == -1" % res_name,
                exception = "PyExc_NameError",
                args      = (
                    "%sname '%s' is not defined" % (
                        "global " if not context.isCompiledPythonModule() else "",
                        variable.getName()
                    ),
                ),
                emit      = emit,
                context   = context
            )
    elif variable.isLocalVariable():
        variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, old_version)
        variable_code_name_new, variable_c_new_type = getLocalVariableCodeType(context, variable, new_version)

        # TODO: We need to split this operation in two parts. Release and init
        # are not one thing.
        assert variable_c_type == variable_c_new_type

        context.setVariableType(variable, variable_code_name_new, variable_c_new_type)

        if not needs_check:
            if variable_c_type == "struct Nuitka_CellObject *":
                template = template_del_shared_known
            else:
                template = template_del_local_known

            emit(
                template % {
                    "identifier" : variable_code_name
                }
            )

        elif tolerant:
            if variable_c_type == "struct Nuitka_CellObject *":
                template = template_del_shared_tolerant
            else:
                template = template_del_local_tolerant

            emit(
                template % {
                    "identifier" : variable_code_name
                }
            )
        else:
            res_name = context.getBoolResName()

            if variable_c_type == "struct Nuitka_CellObject *":
                template = template_del_shared_intolerant
            else:
                template = template_del_local_intolerant

            emit(
                template % {
                    "identifier" : variable_code_name,
                    "result"     : res_name
                }
            )

            if variable.getOwner() is context.getOwner():
                getErrorFormatExitBoolCode(
                    condition = "%s == false" % res_name,
                    exception = "PyExc_UnboundLocalError",
                    args      = ("""\
local variable '%s' referenced before assignment""" % (
                           variable.getName()
                        ),
                    ),
                    emit      = emit,
                    context   = context
                )
            else:
                getErrorFormatExitBoolCode(
                    condition = "%s == false" % res_name,
                    exception = "PyExc_NameError",
                    args      = ("""\
free variable '%s' referenced before assignment in enclosing scope""" % (
                            variable.getName()
                        ),
                    ),
                    emit      = emit,
                    context   = context
                )
    elif variable.isTempVariable():
        variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, old_version)
        _variable_code_name, variable_c_new_type = getLocalVariableCodeType(context, variable, new_version)

        # TODO: We need to split this operation in two parts. Release and init
        # are not one thing.
        assert variable_c_type == variable_c_new_type

        if tolerant:
            # Temp variables use similar classes, can use same templates.

            if variable_c_type == "struct Nuitka_CellObject *":
                template = template_del_shared_tolerant
            elif variable_c_type == "PyObject *":
                template = template_del_local_tolerant
            else:
                assert False, variable_c_type

            emit(
                template % {
                    "identifier" : variable_code_name
                }
            )
        else:
            res_name = context.getBoolResName()

            if variable_c_type == "struct Nuitka_CellObject *":
                template = template_del_shared_tolerant
            elif variable_c_type == "PyObject *":
                template = template_del_local_tolerant
            else:
                assert False, variable_c_type

            emit(
                template % {
                    "identifier" : variable_code_name,
                    "result"     : res_name
                }
            )

            getAssertionCode(
                check = "%s != false" % res_name,
                emit  = emit
            )
    else:
        assert False, variable


def getVariableReleaseCode(variable, version, needs_check, emit, context):
    assert isinstance(variable, Variables.Variable), variable

    assert not variable.isModuleVariable()

    # TODO: We could know, if we could loop, and only set the
    # variable to NULL then, using a different template.

    if needs_check:
        template = template_release_unclear
    else:
        template = template_release_clear

    emit(
        template % {
            "identifier" : getVariableCode(
                variable = variable,
                version  = version,
                context  = context
            )
        }
    )
