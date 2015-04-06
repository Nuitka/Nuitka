#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
from nuitka.utils import Utils

from . import CodeTemplates
from .ConstantCodes import getConstantCode
from .Emission import SourceCodeCollector
from .ErrorCodes import getErrorFormatExitBoolCode, getErrorFormatExitCode
from .Indentation import indented


def generateVariableDelCode(statement, emit, context):
    old_source_ref = context.setCurrentSourceCodeReference(
        statement.getSourceReference()
    )

    getVariableDelCode(
        variable    = statement.getTargetVariableRef().getVariable(),
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
        needs_check = needs_check,
        emit        = emit,
        context     = context
    )


def generateVariableReferenceCode(to_name, expression, emit, context):
    getVariableAccessCode(
        to_name     = to_name,
        variable    = expression.getVariable(),
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


def _getLocalVariableCode(context, variable):
    # Now must be local or temporary variable. Owners of them will not use
    # context except if it's a parameter variable, which is not shared between
    # different generator instances. This is supposed to return in just about
    # every branch, pylint: disable=R0911
    user = context.getOwner()
    owner = variable.getOwner()

    if owner is user:
        result = getVariableCodeName(
            in_context = owner is not user,
            variable   = variable
        )

        # Generator objects store their parameters in a dedicate kind of
        # closure alike.
        if user.isExpressionFunctionBody() and \
           user.isGenerator() and \
           variable.isParameterVariable():
            parameter_index = user.getParameters().getVariables().index(variable)
            if variable.isSharedTechnically():
                return "((PyCellObject *)generator->m_parameters[%d])" % parameter_index, True
            else:
                return "generator->m_parameters[%d]" % parameter_index, False

        if variable.isSharedTechnically():
            return result, True
        else:
            return result, False
    elif context.isForDirectCall():
        if user.isGenerator():
            closure_index = user.getClosureVariables().index(variable)

            return "generator->m_closure[%d]" % closure_index, True
        else:
            result = getVariableCodeName(
                in_context = True,
                variable   = variable
            )

            return result, False
    else:
        closure_index = user.getClosureVariables().index(variable)

        if user.isGenerator():
            return "generator->m_closure[%d]" % closure_index, True
        else:
            return "self->m_closure[%d]" % closure_index, True

def getVariableCode(context, variable):
    # Modules are simple.
    if variable.isModuleVariable():
        return getVariableCodeName(
            in_context = False,
            variable   = variable
        )

    result, _is_cell = _getLocalVariableCode(context, variable)
    return result


def getLocalVariableObjectAccessCode(context, variable):
    assert variable.isLocalVariable()

    code, is_cell = _getLocalVariableCode(context, variable)

    if is_cell:
        return code + "->ob_ref"
    else:
        return code


def getLocalVariableInitCode(variable, init_from = None):
    assert not variable.isModuleVariable()

    type_name = variable.getDeclarationTypeCode()

    code_name = getVariableCodeName(
        in_context = False,
        variable   = variable
    )

    if variable.isSharedTechnically():
        # TODO: Single out "init_from" only user, so it becomes sure that we
        # get a reference transferred here in these cases.
        if init_from is not None:
            init_value = "PyCell_NEW1( %s )" % init_from
        else:
            init_value = "PyCell_EMPTY()"
    else:
        if init_from is None:
            init_from = "NULL"

        init_value = "%s" % init_from

    return "%s%s = %s;" % (
        type_name,
        code_name,
        init_value
    )


def getVariableAssignmentCode(context, emit, variable, tmp_name, needs_release,
                              in_place):
    # Many different cases, as this must be, pylint: disable=R0912,R0915

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
                getConstantCode(
                    constant = variable.getName(),
                    context  = context
                ),
                tmp_name
            )
        )

        if ref_count:
            context.removeCleanupTempName(tmp_name)
    elif variable.isLocalVariable():
        if in_place:
            # Releasing is not an issue here, local variable reference never
            # gave a reference, and the inplace code deals with possible
            # replacement/release.
            if variable.isSharedTechnically():
                template = CodeTemplates.template_write_shared_inplace
            else:
                template = CodeTemplates.template_write_local_inplace

        elif variable.isSharedTechnically():
            if ref_count:
                if needs_release is False:
                    template = CodeTemplates.template_write_shared_clear_ref0
                else:
                    template = CodeTemplates.template_write_shared_unclear_ref0
            else:
                if needs_release is False:
                    template = CodeTemplates.template_write_shared_clear_ref1
                else:
                    template = CodeTemplates.template_write_shared_unclear_ref1
        else:
            if ref_count:
                if needs_release is False:
                    template = CodeTemplates.template_write_local_empty_ref0
                elif needs_release is True:
                    template = CodeTemplates.template_write_local_clear_ref0
                else:
                    template = CodeTemplates.template_write_local_unclear_ref0
            else:
                if needs_release is False:
                    template = CodeTemplates.template_write_local_empty_ref1
                elif needs_release is True:
                    template = CodeTemplates.template_write_local_clear_ref1
                else:
                    template = CodeTemplates.template_write_local_unclear_ref1

        emit(
            template % {
                "identifier" : getVariableCode(context, variable),
                "tmp_name"   : tmp_name
            }
        )

        if ref_count:
            context.removeCleanupTempName(tmp_name)
    elif variable.isTempVariable():
        if variable.isSharedTechnically():
            if ref_count:
                template = CodeTemplates.template_write_shared_unclear_ref0
            else:
                template = CodeTemplates.template_write_shared_unclear_ref1
        else:
            if ref_count:
                if needs_release is False:
                    template = CodeTemplates.template_write_local_empty_ref0
                elif needs_release is True:
                    template = CodeTemplates.template_write_local_clear_ref0
                else:
                    template = CodeTemplates.template_write_local_unclear_ref0
            else:
                if needs_release is False:
                    template = CodeTemplates.template_write_local_empty_ref1
                elif needs_release is True:
                    template = CodeTemplates.template_write_local_clear_ref1
                else:
                    template = CodeTemplates.template_write_local_unclear_ref1

        emit(
            template % {
                "identifier" : getVariableCode(context, variable),
                "tmp_name"   : tmp_name
            }
        )

        if ref_count:
            context.removeCleanupTempName(tmp_name)
    else:
        assert False, variable


def getVariableAccessCode(to_name, variable, needs_check, emit, context):
    # Many different cases, as this must be, pylint: disable=R0912

    assert isinstance(variable, Variables.Variable), variable

    if variable.isModuleVariable():
        emit(
            CodeTemplates.template_read_mvar_unclear % {
                "module_identifier" : context.getModuleCodeName(),
                "tmp_name"          : to_name,
                "var_name"          : getConstantCode(
                    context  = context,
                    constant = variable.getName()
                )
            }
        )

        if needs_check:
            if Utils.python_version < 340 and not context.isPythonModule():
                error_message = "global name '%s' is not defined"
            else:
                error_message = "name '%s' is not defined"

            getErrorFormatExitCode(
                check_name = to_name,
                exception  = "PyExc_NameError",
                args       = (
                    error_message % variable.getName(),
                ),
                emit       = emit,
                context    = context
            )
        elif Options.isDebug():
            emit("CHECK_OBJECT( %s );" % to_name)

        return
    elif variable.isMaybeLocalVariable():
        fallback_emit = SourceCodeCollector()

        getVariableAccessCode(
            to_name     = to_name,
            variable    = variable.getMaybeVariable(),
            needs_check = True,
            emit        = fallback_emit,
            context     = context
        )

        emit(
            CodeTemplates.template_read_maybe_local_unclear % {
                "locals_dict" : "locals_dict",
                "fallback"    : indented(fallback_emit.codes),
                "tmp_name"    : to_name,
                "var_name"    : getConstantCode(
                    context  = context,
                    constant = variable.getName()
                )
            }
        )

        return
    elif variable.isLocalVariable():
        if variable.isSharedTechnically():
            if not needs_check:
                template = CodeTemplates.template_read_shared_unclear
            else:
                template = CodeTemplates.template_read_shared_known
        else:
            template = CodeTemplates.template_read_local

        emit(
            template % {
                "tmp_name"   : to_name,
                "identifier" : getVariableCode(context, variable)
            }
        )

        if needs_check:
            if variable.getOwner() is not context.getOwner():
                getErrorFormatExitCode(
                    check_name = to_name,
                    exception  = "PyExc_NameError",
                    args       = (
                        """\
free variable '%s' referenced before assignment in enclosing scope""" % (
                           variable.getName()
                        ),
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
local variable '%s' referenced before assignment""" % (
                           variable.getName()
                        ),
                    ),
                    emit       = emit,
                    context    = context
                )
        elif Options.isDebug():
            emit("CHECK_OBJECT( %s );" % to_name)

        return
    elif variable.isTempVariable():
        if variable.isSharedTechnically():
            template = CodeTemplates.template_read_shared_unclear

            emit(
                template % {
                    "tmp_name"   : to_name,
                    "identifier" : getVariableCode(context, variable)
                }
            )

            if needs_check:
                getErrorFormatExitCode(
                    check_name = to_name,
                    exception  = "PyExc_NameError",
                    args       = (
                        """\
free variable '%s' referenced before assignment in enclosing scope""" % (
                           variable.getName()
                        ),
                    ),
                    emit       = emit,
                    context    = context
                )
            elif Options.isDebug():
                emit("CHECK_OBJECT( %s );" % to_name)

            return
        else:
            template = CodeTemplates.template_read_local

            emit(
                template % {
                    "tmp_name"   : to_name,
                    "identifier" : getVariableCode(context, variable)
                }
            )

            if needs_check:
                getErrorFormatExitCode(
                    check_name = to_name,
                    exception  = "PyExc_UnboundLocalError",
                    args       = ("""\
local variable '%s' referenced before assignment""" % (
                           variable.getName()
                        ),
                    ),
                    emit       = emit,
                    context    = context
                )
            elif Options.isDebug():
                emit("CHECK_OBJECT( %s );" % to_name)

            return

    assert False, variable


def getVariableDelCode(variable, tolerant, needs_check, emit, context):
    # Many different cases, as this must be, pylint: disable=R0912
    assert isinstance(variable, Variables.Variable), variable

    if variable.isModuleVariable():
        check = not tolerant

        res_name = context.getIntResName()

        emit(
            CodeTemplates.template_del_global_unclear % {
                "module_identifier" : context.getModuleCodeName(),
                "res_name"          : res_name,
                "var_name"          : getConstantCode(
                    context  = context,
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
                        "global " if not context.isPythonModule() else "",
                        variable.getName()
                    ),
                ),
                emit      = emit,
                context   = context
            )
    elif variable.isLocalVariable():
        if not needs_check:
            if variable.isSharedTechnically():
                template = CodeTemplates.template_del_shared_known
            else:
                template = CodeTemplates.template_del_local_known

            emit(
                template % {
                    "identifier" : getVariableCode(
                        variable = variable,
                        context  = context
                    )
                }
            )
        elif tolerant:
            if variable.isSharedTechnically():
                template = CodeTemplates.template_del_shared_tolerant
            else:
                template = CodeTemplates.template_del_local_tolerant

            emit(
                template % {
                    "identifier" : getVariableCode(
                        variable = variable,
                        context  = context
                    )
                }
            )
        else:
            res_name = context.getBoolResName()

            if variable.isSharedTechnically():
                template = CodeTemplates.template_del_shared_intolerant
            else:
                template = CodeTemplates.template_del_local_intolerant

            emit(
                template % {
                    "identifier" : getVariableCode(
                        variable = variable,
                        context  = context
                    ),
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
        if tolerant:
            # Temp variables use similar classes, can use same templates.

            if variable.isSharedTechnically():
                template = CodeTemplates.template_del_shared_tolerant
            else:
                template = CodeTemplates.template_del_local_tolerant

            emit(
                template % {
                    "identifier" : getVariableCode(
                        variable = variable,
                        context  = context
                    )
                }
            )
        else:
            res_name = context.getBoolResName()

            if variable.isSharedTechnically():
                template = CodeTemplates.template_del_shared_intolerant
            else:
                template = CodeTemplates.template_del_local_intolerant

            emit(
                template % {
                    "identifier" : getVariableCode(
                        variable = variable,
                        context  = context
                    ),
                    "result"     : res_name
                }
            )

            emit(
                "assert( %s != false );" % res_name
            )
    else:
        assert False, variable


def getVariableReleaseCode(variable, needs_check, emit, context):
    assert isinstance(variable, Variables.Variable), variable

    assert not variable.isModuleVariable()

    # TODO: We could know, if we could loop, and only set the
    # variable to NULL then, using a different template.

    if needs_check:
        template = CodeTemplates.template_release_unclear
    else:
        template = CodeTemplates.template_release_clear

    emit(
        template % {
            "identifier" : getVariableCode(
                variable = variable,
                context  = context
            )
        }
    )


def getVariableInitializedCheckCode(variable, context):
    """ Check if a variable is initialized.

        Returns a code expression that says "true" if it is.
    """

    if variable.isLocalVariable() or variable.isTempVariable():
        if variable.isSharedTechnically():
            template = CodeTemplates.template_check_shared
        else:
            template = CodeTemplates.template_check_local

        return template % {
            "identifier" : getVariableCode(
                variable = variable,
                context  = context
            ),
        }
    else:
        assert False, variable
