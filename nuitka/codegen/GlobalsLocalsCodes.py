#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Code generation for locals and globals handling.

This also includes writing back to locals for exec statements.
"""

from nuitka.PythonVersions import python_version

from .ConstantCodes import getConstantCode
from .ErrorCodes import getErrorExitBoolCode
from .Helpers import generateExpressionCode
from .ModuleCodes import getModuleAccessCode
from .PythonAPICodes import generateCAPIObjectCode
from .templates.CodeTemplatesVariables import (
    template_set_locals_dict_value,
    template_set_locals_mapping_value,
    template_update_locals_dict_value,
    template_update_locals_mapping_value
)
from .VariableCodes import (
    getLocalVariableObjectAccessCode,
    getVariableAssignmentCode
)


def generateBuiltinLocalsCode(to_name, expression, emit, context):
    provider = expression.getParentVariableProvider()

    getLoadLocalsCode(
        to_name  = to_name,
        provider = provider,
        mode     = provider.getLocalsMode(),
        emit     = emit,
        context  = context
    )


def generateBuiltinGlobalsCode(to_name, expression, emit, context):
    # Functions used for generation all accept expression, but this one does
    # not use it. pylint: disable=W0613

    getLoadGlobalsCode(
        to_name = to_name,
        emit    = emit,
        context = context
    )


def getLoadGlobalsCode(to_name, emit, context):
    assert type(to_name) is str

    emit(
        "%(to_name)s = ((PyModuleObject *)%(module_identifier)s)->md_dict;" % {
            "to_name"           : to_name,
            "module_identifier" : getModuleAccessCode(context)
        },
    )


def _getLocalVariableList(provider):
    if provider.isExpressionFunctionBody():
        include_closure = not provider.isUnoptimized()
    elif provider.isExpressionClassBody():
        include_closure = False
    else:
        include_closure = True

    return [
        variable
        for variable in
        provider.getVariables()
        if not variable.isModuleVariable()
        if not variable.isMaybeLocalVariable()
        if (include_closure or variable.getOwner() is provider)
    ]


def _getVariableDictUpdateCode(target_name, variable, initial, is_dict, emit, context):
    # TODO: Variable could known to be set here, get a hand at that
    # information.

    access_code = getLocalVariableObjectAccessCode(
        variable = variable,
        context  = context
    )

    if is_dict:
        if initial:
            template = template_set_locals_dict_value
        else:
            template = template_update_locals_dict_value

        emit(
             template % {
                "dict_name"   : target_name,
                "var_name"    : getConstantCode(
                    constant = variable.getName(),
                    context  = context
                ),
                "access_code" : access_code,
            }
        )
    else:
        if initial:
            template = template_set_locals_mapping_value
        else:
            template = template_update_locals_mapping_value

        res_name = context.getBoolResName()

        emit(
            template % {
                "mapping_name" : target_name,
                "var_name"     : getConstantCode(
                    constant = variable.getName(),
                    context  = context
                ),
                "access_code"  : access_code,
                "tmp_name"     : res_name
            }
        )

        getErrorExitBoolCode(
            condition = "%s == false" % res_name,
            emit      = emit,
            context   = context
        )


def getLoadLocalsCode(to_name, provider, mode, emit, context):
    if provider.isCompiledPythonModule():
        # Optimization will have made this "globals".
        assert False, provider
    elif not context.hasLocalsDict():
        local_list = _getLocalVariableList(
            provider = provider,
        )

        # TODO: Use DictCodes ?
        emit(
            "%s = PyDict_New();" % (
                to_name,
            )
        )

        context.addCleanupTempName(to_name)

        for local_var in local_list:
            _getVariableDictUpdateCode(
                target_name = to_name,
                variable    = local_var,
                is_dict     = True,
                initial     = True,
                emit        = emit,
                context     = context
            )
    else:
        if mode == "copy":
            emit(
                "%s = PyDict_Copy( locals_dict );" % (
                    to_name,
                )
            )

            context.addCleanupTempName(to_name)
        elif mode == "updated":
            local_list = _getLocalVariableList(
                provider = provider
            )

            emit(
                """\
%s = locals_dict;
Py_INCREF( locals_dict );""" % (
                    to_name
                )
            )

            for local_var in local_list:
                _getVariableDictUpdateCode(
                    target_name = to_name,
                    variable    = local_var,
                    is_dict     = python_version < 300 or \
                                  not context.getFunction().isExpressionClassBody(),
                    initial     = False,
                    emit        = emit,
                    context     = context
                )

            context.addCleanupTempName(to_name)
        else:
            assert False


def generateSetLocalsCode(statement, emit, context):
    new_locals_name = context.allocateTempName("set_locals", unique = True)

    generateExpressionCode(
        to_name    = new_locals_name,
        expression = statement.getNewLocals(),
        emit       = emit,
        context    = context
    )

    ref_count = context.needsCleanup(new_locals_name)

    emit(
        """\
Py_DECREF(locals_dict);
locals_dict = %s;""" % (
            new_locals_name
        )
    )

    if not ref_count:
        emit(
            "Py_INCREF(locals_dict);"
        )

    if ref_count:
        context.removeCleanupTempName(new_locals_name)


def getStoreLocalsCode(locals_name, provider, emit, context):
    assert not provider.isCompiledPythonModule()

    for variable in provider.getVariables():
        if not variable.isModuleVariable() and \
           not variable.isMaybeLocalVariable():
            key_name = getConstantCode(
                context  = context,
                constant = variable.getName()
            )

            value_name = context.allocateTempName("locals_value", unique = True)

            # This should really be a template.
            emit(
               "%s = PyObject_GetItem( %s, %s );" % (
                   value_name,
                   locals_name,
                   key_name,
                )
            )

            getErrorExitBoolCode(
                condition = """\
%s == NULL && !EXCEPTION_MATCH_BOOL_SINGLE( GET_ERROR_OCCURRED(), PyExc_KeyError )""" % value_name,
                emit      = emit,
                context   = context
            )

            emit("CLEAR_ERROR_OCCURRED();")
            emit("if ( %s != NULL )" % value_name)
            emit('{')

            context.addCleanupTempName(value_name)
            getVariableAssignmentCode(
                variable      = variable,
                tmp_name      = value_name,
                needs_release = None, # TODO: Could be known maybe.
                in_place      = False,
                emit          = emit,
                context       = context
            )

            emit('}')


def generateBuiltinDir1Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "PyObject_Dir",
        arg_desc   = (
            ("dir_arg", expression.getValue()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )


def generateBuiltinVarsCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "LOOKUP_VARS",
        arg_desc   = (
            ("vars_arg", expression.getSource()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )
