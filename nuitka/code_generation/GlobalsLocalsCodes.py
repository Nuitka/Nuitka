#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .CodeHelpers import (
    decideConversionCheckNeeded,
    withObjectCodeTemporaryAssignment,
)
from .Emission import SourceCodeCollector
from .ErrorCodes import getErrorExitBoolCode
from .Indentation import indented
from .PythonAPICodes import generateCAPIObjectCode
from .templates.CodeTemplatesVariables import (
    template_set_locals_dict_value,
    template_set_locals_mapping_value,
    template_update_locals_dict_value,
    template_update_locals_mapping_value,
)
from .VariableCodes import (
    getLocalVariableDeclaration,
    getVariableReferenceCode,
)
from .VariableDeclarations import VariableDeclaration


def generateBuiltinLocalsRefCode(to_name, expression, emit, context):
    locals_scope = expression.getLocalsScope()

    locals_declaration = context.addLocalsDictName(locals_scope.getCodeName())

    with withObjectCodeTemporaryAssignment(
        to_name, "locals_ref_value", expression, emit, context
    ) as value_name:

        emit("%s = %s;" % (value_name, locals_declaration))


def generateBuiltinLocalsCode(to_name, expression, emit, context):
    variable_traces = expression.getVariableTraces()
    updated = expression.isExpressionBuiltinLocalsUpdated()
    locals_scope = expression.getLocalsScope()

    # Locals is sorted of course.
    def _sorted(variables):
        variable_order = tuple(locals_scope.getProvidedVariables())

        return sorted(
            variables, key=lambda variable_desc: variable_order.index(variable_desc[0])
        )

    with withObjectCodeTemporaryAssignment(
        to_name, "locals_ref_value", expression, emit, context
    ) as value_name:

        if updated:
            locals_declaration = context.addLocalsDictName(locals_scope.getCodeName())
            is_dict = locals_scope.hasShapeDictionaryExact()
            # For Python3 it may really not be a dictionary.

            # TODO: Creation is not needed for classes.
            emit(
                """\
if (%(locals_dict)s == NULL) %(locals_dict)s = PyDict_New();
%(to_name)s = %(locals_dict)s;
Py_INCREF(%(to_name)s);"""
                % {"to_name": value_name, "locals_dict": locals_declaration}
            )
            context.addCleanupTempName(value_name)

            initial = False
        else:
            emit("%s = PyDict_New();" % (to_name,))

            context.addCleanupTempName(value_name)

            initial = True
            is_dict = True

        for local_var, variable_trace in _sorted(variable_traces):
            _getVariableDictUpdateCode(
                target_name=value_name,
                variable=local_var,
                variable_trace=variable_trace,
                is_dict=is_dict,
                initial=initial,
                emit=emit,
                context=context,
            )


def generateBuiltinGlobalsCode(to_name, expression, emit, context):
    with withObjectCodeTemporaryAssignment(
        to_name, "globals_value", expression, emit, context
    ) as value_name:
        emit(
            "%(to_name)s = (PyObject *)moduledict_%(module_identifier)s;"
            % {"to_name": value_name, "module_identifier": context.getModuleCodeName()}
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
        for variable in provider.getProvidedVariables()
        if not variable.isModuleVariable()
        if (include_closure or variable.getOwner() is provider)
    ]


def _getVariableDictUpdateCode(
    target_name, variable, variable_trace, initial, is_dict, emit, context
):
    # TODO: Variable could known to be set here, get a hand at that
    # information.

    variable_declaration = getLocalVariableDeclaration(
        context, variable, variable_trace
    )

    variable_c_type = variable_declaration.getCType()

    test_code = variable_c_type.getInitTestConditionCode(
        value_name=variable_declaration, inverted=False
    )

    access_code = SourceCodeCollector()

    getVariableReferenceCode(
        to_name=VariableDeclaration("PyObject *", "value", None, None),
        variable=variable,
        variable_trace=variable_trace,
        needs_check=False,
        conversion_check=True,
        emit=access_code,
        context=context,
    )

    if is_dict:
        if initial:
            template = template_set_locals_dict_value
        else:
            template = template_update_locals_dict_value

        emit(
            template
            % {
                "dict_name": target_name,
                "var_name": context.getConstantCode(constant=variable.getName()),
                "test_code": test_code,
                "access_code": indented(access_code.codes),
            }
        )
    else:
        if initial:
            template = template_set_locals_mapping_value
        else:
            template = template_update_locals_mapping_value

        res_name = context.getBoolResName()

        emit(
            template
            % {
                "mapping_name": target_name,
                "var_name": context.getConstantCode(constant=variable.getName()),
                "test_code": test_code,
                "access_code": access_code,
                "tmp_name": res_name,
            }
        )

        getErrorExitBoolCode(
            condition="%s == false" % res_name, emit=emit, context=context
        )


def generateBuiltinDir1Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="PyObject_Dir",
        arg_desc=(("dir_arg", expression.subnode_value),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinVarsCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="LOOKUP_VARS",
        arg_desc=(("vars_arg", expression.subnode_source),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )
