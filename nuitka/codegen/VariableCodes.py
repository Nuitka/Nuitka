#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka import Variables

from . import CodeTemplates
from .ConstantCodes import getConstantCode
from .ErrorCodes import (
    getErrorExitBoolCode,
    getErrorExitCode,
    getErrorFormatExitBoolCode,
    getErrorFormatExitCode
)


def _getContextAccess(context, force_closure = False):
    # Context access is variant depending on if that's a created function or
    # not. For generators, they even share closure variables in the common
    # context.
    if context.isPythonModule():
        return ""
    else:
        function = context.getFunction()

        if function.needsCreation():
            if function.isGenerator():
                if force_closure:
                    return "_python_context->common_context->"
                else:
                    return "_python_context->"
            else:
                if force_closure:
                    return "_python_context->"
                else:
                    return ""
        else:
            if function.isGenerator():
                return "_python_context->"
            else:
                return ""


def getVariableCode(context, variable):
    from_context = _getContextAccess(
        context       = context,
        force_closure = variable.isClosureReference()
    )

    return from_context + variable.getCodeName()


def getLocalVariableInitCode(context, variable, init_from = None,
                             in_context = False):
    # This has many cases to deal with, so there need to be a lot of branches.
    # pylint: disable=R0912

    assert not variable.isModuleVariable()

    result = variable.getDeclarationTypeCode(in_context)

    # For pointer types, we don't have to separate with spaces.
    if not result.endswith( "*" ):
        result += " "

    store_name = variable.getMangledName()

    result += variable.getCodeName()

    if not in_context:
        if variable.isTempVariable():
            assert init_from is None

            if variable.isSharedTechnically():
                result += "( NULL )"
        else:
            if init_from is not None:
                result += "( %s )" % init_from

    result += ";"

    return result


def getVariableAssignmentCode(context, emit, variable, tmp_name):
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
        if variable.isSharedTechnically():
            if ref_count:
                template = CodeTemplates.template_write_shared_unclear_ref0
            else:
                template = CodeTemplates.template_write_shared_unclear_ref1
        else:
            if ref_count:
                template = CodeTemplates.template_write_local_unclear_ref0
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
    elif variable.isClosureReference() or variable.isTempVariableReference():
        if variable.getReferenced().isSharedTechnically():
            if ref_count:
                template = CodeTemplates.template_write_shared_unclear_ref0
            else:
                template = CodeTemplates.template_write_shared_unclear_ref1
        else:
            if ref_count:
                template = CodeTemplates.template_write_local_unclear_ref0
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


def getVariableAccessCode(to_name, variable, emit, context):
    assert isinstance(variable, Variables.Variable), variable

    if variable.isModuleVariable():
        # TODO: use SSA to determine
        needs_check = True

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
            getErrorFormatExitCode(
                check_name = to_name,
                exception  = "PyExc_NameError",
                args       = (
                    '''%sname '%s' is not defined''' % (
                       "global " if not context.isPythonModule() else "",
                       variable.getName()
                    ),
                ),
                emit       = emit,
                context    = context
            )

        return
    elif variable.isMaybeLocalVariable():
        # TODO: use SSA to determine
        needs_check = True

        emit(
            CodeTemplates.template_read_maybe_local_unclear % {
                "locals_dict"       : "locals_dict",
                "module_identifier" : context.getModuleCodeName(),
                "tmp_name"          : to_name,
                "var_name"          : getConstantCode(
                    context  = context,
                    constant = variable.getName()
                )
            }
        )

        if needs_check:
            getErrorFormatExitCode(
                check_name = to_name,
                exception  = "PyExc_NameError",
                args       = (
                    '''name '%s' is not defined''' % (
                       variable.getName()
                    ),
                ),
                emit       = emit,
                context    = context
            )

        return
    elif variable.isLocalVariable():
        if variable.isSharedTechnically():
            if variable.isParameterVariable() and \
               not variable.getHasDelIndicator():
                template = CodeTemplates.template_read_shared_unclear
                needs_check = False
            else:
                template = CodeTemplates.template_read_shared_known
                needs_check = True
        else:
            template = CodeTemplates.template_read_local
            if variable.isParameterVariable() and \
               not variable.getHasDelIndicator():
                needs_check = False
            else:
                needs_check = True

        # TODO: Temporary, as DelIndicator is not based on SSA yes, we need
        # to pretend we may raise even then.
        context.markAsNeedsExceptionVariables()
        needs_check = True

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
                args       = (
'''local variable '%s' referenced before assignment''' % (
                       variable.getName()
                    ),
                ),
                emit       = emit,
                context    = context
            )

        return
    elif variable.isClosureReference() or variable.isTempVariableReference():
        if variable.getReferenced().isSharedTechnically():
            template = CodeTemplates.template_read_shared_unclear
            needs_check = True

            emit(
                template % {
                    "tmp_name"   : to_name,
                    "identifier" : getVariableCode(context, variable)
                }
            )

            if variable.isTempVariableReference():
                needs_check = False

            if needs_check:
                getErrorFormatExitCode(
                    check_name = to_name,
                    exception  = "PyExc_UnboundLocalError",
                    args       = ("""\
free variable '%s' referenced before assignment in enclosing scope""" % (
                           variable.getName()
                        ),
                    ),
                    emit       = emit,
                    context    = context
                )

            return
        else:
            template = CodeTemplates.template_read_local
            if variable.isParameterVariable() and \
               not variable.getHasDelIndicator():
                needs_check = False
            else:
                needs_check = True

            emit(
                template % {
                    "tmp_name"   : to_name,
                    "identifier" : getVariableCode(context, variable)
                }
            )

            if variable.isTempVariableReference():
                needs_check = False

            if needs_check:
                getErrorFormatExitCode(
                    check_name = to_name,
                    exception  = "PyExc_UnboundLocalError",
                    args       = (
    '''local variable '%s' referenced before assignment''' % (
                           variable.getName()
                        ),
                    ),
                    emit       = emit,
                    context    = context
                )

            return

    identifier = getVariableCode(context, variable)
    ref_count = identifier.getCheapRefCount()

    assert ref_count == 0

    assert not variable.isLocalVariable()
    assert False, variable

    emit(
        "%s = %s;" % (
            to_name,
            identifier.getCodeTemporaryRef(),
        )
    )

    if variable.isClosureReference():
        getErrorExitCode(
            check_name = to_name,
            emit       = emit,
            context    = context
        )


def getVariableDelCode(tolerant, variable, emit, context):
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

        if check:
            getErrorFormatExitBoolCode(
                condition = "%s == -1" % res_name,
                exception = "PyExc_NameError",
                args      = (
                    '''%sname '%s' is not defined''' % (
                        "global " if not context.isPythonModule() else "",
                        variable.getName()
                    ),
                ),
                emit      = emit,
                context   = context
            )
    elif variable.isLocalVariable():
        if tolerant:
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

            getErrorFormatExitBoolCode(
                condition = "%s == false" % res_name,
                exception = "PyExc_UnboundLocalError",
                args      = (
'''local variable '%s' referenced before assignment''' % (
                       variable.getName()
                    ),
                ),
                emit      = emit,
                context   = context
            )
    elif variable.isTempVariableReference():
        if tolerant:
            # Temp variables use similar classes, can use same templates.

            if variable.getReferenced().isSharedTechnically():
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
                """assert( %s != false );""" % res_name
            )
    elif variable.isClosureReference():
        if tolerant:
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

            getErrorFormatExitBoolCode(
                condition = "%s == false" % res_name,
                exception = "PyExc_UnboundLocalError",
                    args       = ("""\
free variable '%s' referenced before assignment in enclosing scope""" % (
                        variable.getName()
                    ),
                ),
                emit      = emit,
                context   = context
            )
    else:
        assert False, variable

        if tolerant:
            emit(
                "%s.del( true );" % (
                    getVariableCode(
                        variable = variable,
                        context  = context
                    ),
                )
            )
        elif variable.isTempVariableReference():
            emit(
                "%s.del( false );" % (
                    getVariableCode(
                        variable = variable,
                        context  = context
                    ),
                )
            )
        else:
            getErrorExitBoolCode(
                condition = "%s.del( false ) == false" % (
                    getVariableCode(
                        variable = variable,
                        context  = context
                    ),
                ),

                emit      = emit,
                context   = context
            )
