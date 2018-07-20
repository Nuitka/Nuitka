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
""" Code generation for locals and globals handling.

This also includes writing back to locals for exec statements.
"""

from nuitka.nodes.shapes.BuiltinTypeShapes import ShapeTypeDict

from .ErrorCodes import getErrorExitBoolCode
from .PythonAPICodes import generateCAPIObjectCode
from .templates.CodeTemplatesVariables import (
    template_set_locals_dict_value,
    template_set_locals_mapping_value,
    template_update_locals_dict_value,
    template_update_locals_mapping_value
)
from .VariableCodes import getLocalVariableCodeType


def generateBuiltinLocalsRefCode(to_name, expression, emit, context):
    # The locals scope is the context needed, pylint: disable=unused-argument

    emit(
        """\
%s = %s;""" % (
            to_name,
            expression.getLocalsScope().getCodeName(),
        )
    )


def generateBuiltinLocalsCode(to_name, expression, emit, context):
    provider = expression.getParentVariableProvider()

    variable_traces = expression.getVariableTraces()
    updated   = expression.isExpressionBuiltinLocalsUpdated()

    # Locals is sorted of course.
    def _sorted(variables):
        locals_owner = context.getOwner()

        if locals_owner.isExpressionOutlineBody():
            locals_owner = locals_owner.getParentVariableProvider()

        variable_order = locals_owner.getProvidedVariableOrder()

        return sorted(
            variables,
            key = lambda variable_desc: variable_order.index(variable_desc[0].getName()),
        )

    # Optimization will have made this "globals", and it wouldn't be
    # about local variables at all.
    assert not provider.isCompiledPythonModule(), provider

    if updated:
        locals_scope = expression.getLocalsScope()

        locals_dict_name = locals_scope.getCodeName()
        is_dict = locals_scope.getTypeShape() is ShapeTypeDict
        # For Python3 it may really not be a dictionary.

        # TODO: Creation is not needed for classes.
        emit(
            """\
if (%(locals_dict)s == NULL) %(locals_dict)s = PyDict_New();
%(to_name)s = %(locals_dict)s;
Py_INCREF( %(to_name)s );""" % {
                "to_name" : to_name ,
                "locals_dict" : locals_dict_name,
            }
        )
        context.addCleanupTempName(to_name)

        context.addLocalsDictName(locals_dict_name)

        initial = False
    else:
        emit(
            "%s = PyDict_New();" % (
                to_name,
            )
        )

        context.addCleanupTempName(to_name)

        initial = True
        is_dict = True

    for local_var, variable_trace in _sorted(variable_traces):
        _getVariableDictUpdateCode(
            target_name    = to_name,
            variable       = local_var,
            variable_trace = variable_trace,
            is_dict        = is_dict,
            initial        = initial,
            emit           = emit,
            context        = context
        )


def generateBuiltinGlobalsCode(to_name, expression, emit, context):
    # Functions used for generation all accept expression, but this one does
    # not use it. pylint: disable=unused-argument

    getLoadGlobalsCode(
        to_name = to_name,
        emit    = emit,
        context = context
    )


def getLoadGlobalsCode(to_name, emit, context):
    assert type(to_name) is str

    emit(
        "%(to_name)s = (PyObject *)moduledict_%(module_identifier)s;" % {
            "to_name"           : to_name,
            "module_identifier" : context.getModuleCodeName()
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
        if (include_closure or variable.getOwner() is provider)
    ]


def _getVariableDictUpdateCode(target_name, variable, variable_trace, initial,
                               is_dict, emit, context):
    # TODO: Variable could known to be set here, get a hand at that
    # information.

    variable_code_name, variable_c_type = getLocalVariableCodeType(context, variable, variable_trace)

    test_code = variable_c_type.getLocalVariableInitTestCode(variable_code_name)
    access_code = variable_c_type.getLocalVariableObjectAccessCode(variable_code_name)

    if is_dict:
        if initial:
            template = template_set_locals_dict_value
        else:
            template = template_update_locals_dict_value

        emit(
             template % {
                "dict_name"   : target_name,
                "var_name"    : context.getConstantCode(
                    constant = variable.getName()
                ),
                "test_code"   : test_code,
                "access_code" : access_code
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
                "var_name"     : context.getConstantCode(
                    constant = variable.getName()
                ),
                "test_code"    : test_code,
                "access_code"  : access_code,
                "tmp_name"     : res_name
            }
        )

        getErrorExitBoolCode(
            condition = "%s == false" % res_name,
            emit      = emit,
            context   = context
        )


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
