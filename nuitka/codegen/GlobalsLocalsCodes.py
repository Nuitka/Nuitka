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

from nuitka import Utils

from .ConstantCodes import getConstantCode
from .ErrorCodes import getErrorExitBoolCode
from .ModuleCodes import getModuleAccessCode
from .VariableCodes import getVariableAssignmentCode, getVariableCode


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
        # Sort parameter variables of functions to the end.

        start_part = []
        end_part = []

        for variable in provider.getVariables():
            if variable.isParameterVariable():
                end_part.append(variable )
            else:
                start_part.append(variable)

        variables = start_part + end_part

        include_closure = not provider.isUnoptimized() and \
                          not provider.isClassDictCreation()
    else:
        variables = provider.getVariables()

        include_closure = True

    return [
        variable
        for variable in
        variables
        if not variable.isModuleVariable()
        if not variable.isMaybeLocalVariable()
        if ( not variable.isClosureReference() or include_closure )
    ]


def _getVariableDictUpdateCode(dict_name, variable, emit, context):
    # TODO: Variable could known to be set here, get a hand at that
    # information.
    emit(
        "if (%s.isInitialized())\n{" % getVariableCode(
            variable = variable,
            context  = context
        )
    )

    # TODO: For Python3 classes, we need to allow non-dicts, and we ought to
    # check their errors. Often we know it as fresh dict, so this could be
    # optimized.
    access_code = getVariableCode(
        variable = variable,
        context  = context
    )

    if variable.isLocalVariable():
        if variable.isSharedTechnically():
            access_code += ".storage->object"
        else:
            access_code += ".object"
    else:
        if variable.getReferenced().isSharedTechnically():
            access_code += ".storage->object"
        else:
            access_code += ".object"


    emit(
        """\
    %s(
        %s,
        %s,
        %s
    );
""" % (
            "PyDict_SetItem"
              if Utils.python_version < 300 else
            "PyObject_SetItem",
            dict_name,
            getConstantCode(
                constant = variable.getMangledName(),
                context  = context
            ),
            access_code
        )
    )

    # TODO: Use branch C codes to achieve proper indentation
    emit(
        "}"
    )


def getLoadLocalsCode(to_name, provider, mode, emit, context):
    if provider.isPythonModule():
        # TODO: Should not happen in the normal case, make this assertable.
        getLoadGlobalsCode(to_name, emit, context)
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
                dict_name = to_name,
                variable  = local_var,
                emit      = emit,
                context   = context
            )
    else:
        if mode == "copy":
            assert False

            emit(
                "%s = PyDict_Copy( locals_dict )" % (
                    to_name,
                )
            )

            context.addCleanupTempName(to_name)
        elif mode == "updated":
            local_list = _getLocalVariableList(
                provider = provider
            )

            emit(
                "%s = INCREASE_REFCOUNT( locals_dict );" % (
                    to_name
                )
            )

            for local_var in local_list:
                _getVariableDictUpdateCode(
                    dict_name = to_name,
                    variable  = local_var,
                    emit      = emit,
                    context   = context
                )

            context.addCleanupTempName(to_name)
        else:
            assert False


def getSetLocalsCode(new_locals_name, emit, context):
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
    assert not provider.isPythonModule()

    for variable in provider.getVariables():
        if not variable.isModuleVariable() and \
           not variable.isMaybeLocalVariable():
            key_name = getConstantCode(
                context  = context,
                constant = variable.getName()
            )

            value_name = context.allocateTempName("locals_value", unique = True)

            emit(
               "%s = PyObject_GetItem( %s, %s );" % (
                   value_name,
                   locals_name,
                   key_name,
                )
            )

            getErrorExitBoolCode(
                condition = """\
%s == NULL && !PyErr_ExceptionMatches( PyExc_KeyError )""" % value_name,
                emit      = emit,
                context   = context
            )

            emit("PyErr_Clear();")
            emit("if (%s != NULL)" % value_name)
            emit("{")

            context.addCleanupTempName(value_name)
            getVariableAssignmentCode(
                variable   = variable,
                tmp_name   = value_name,
                emit       = emit,
                context    = context
            )

            emit("}")
