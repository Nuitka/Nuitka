#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Code generation for locals dict handling.

These are variable handling for classes and partially also Python2 exec
statements.
"""

from .CodeHelpers import (
    generateExpressionCode,
    withObjectCodeTemporaryAssignment,
)
from .Emission import SourceCodeCollector
from .ErrorCodes import (
    getErrorExitBoolCode,
    getErrorExitCode,
    getNameReferenceErrorCode,
)
from .Indentation import indented
from .PythonAPICodes import getReferenceExportCode
from .templates.CodeTemplatesVariables import (
    template_read_locals_dict_with_fallback,
    template_read_locals_dict_without_fallback,
    template_read_locals_mapping_with_fallback,
    template_read_locals_mapping_without_fallback,
)


def generateSetLocalsDictCode(statement, emit, context):
    new_locals_name = context.allocateTempName("set_locals")

    generateExpressionCode(
        to_name=new_locals_name,
        expression=statement.subnode_new_locals,
        emit=emit,
        context=context,
    )

    locals_declaration = context.addLocalsDictName(
        statement.getLocalsScope().getCodeName()
    )

    emit(
        """\
%(locals_dict)s = %(locals_value)s;"""
        % {"locals_dict": locals_declaration, "locals_value": new_locals_name}
    )

    getReferenceExportCode(new_locals_name, emit, context)

    if context.needsCleanup(new_locals_name):
        context.removeCleanupTempName(new_locals_name)


def generateReleaseLocalsDictCode(statement, emit, context):
    locals_declaration = context.addLocalsDictName(
        statement.getLocalsScope().getCodeName()
    )

    emit(
        """\
Py_DECREF(%(locals_dict)s);
%(locals_dict)s = NULL;"""
        % {"locals_dict": locals_declaration}
    )


def generateLocalsDictSetCode(statement, emit, context):
    value_arg_name = context.allocateTempName("dictset_value", unique=True)
    generateExpressionCode(
        to_name=value_arg_name,
        expression=statement.subnode_source,
        emit=emit,
        context=context,
    )

    context.setCurrentSourceCodeReference(statement.getSourceReference())

    locals_scope = statement.getLocalsDictScope()

    locals_declaration = context.addLocalsDictName(locals_scope.getCodeName())

    is_dict = locals_scope.hasShapeDictionaryExact()

    res_name = context.getIntResName()

    if is_dict:
        emit(
            "%s = PyDict_SetItem(%s, %s, %s);"
            % (
                res_name,
                locals_declaration,
                context.getConstantCode(statement.getVariableName()),
                value_arg_name,
            )
        )
    else:
        emit(
            "%s = PyObject_SetItem(%s, %s, %s);"
            % (
                res_name,
                locals_declaration,
                context.getConstantCode(statement.getVariableName()),
                value_arg_name,
            )
        )

    getErrorExitBoolCode(
        condition="%s != 0" % res_name,
        release_name=value_arg_name,
        needs_check=statement.mayRaiseException(BaseException),
        emit=emit,
        context=context,
    )


def generateLocalsDictDelCode(statement, emit, context):
    locals_scope = statement.getLocalsDictScope()

    dict_arg_name = locals_scope.getCodeName()

    is_dict = locals_scope.hasShapeDictionaryExact()

    context.setCurrentSourceCodeReference(statement.getSourceReference())

    if is_dict:
        res_name = context.getBoolResName()

        emit(
            "%s = DICT_REMOVE_ITEM(%s, %s);"
            % (
                res_name,
                dict_arg_name,
                context.getConstantCode(statement.getVariableName()),
            )
        )

        getErrorExitBoolCode(
            condition="%s == false" % res_name,
            needs_check=statement.mayRaiseException(BaseException),
            emit=emit,
            context=context,
        )
    else:
        res_name = context.getIntResName()

        emit(
            "%s = PyObject_DelItem(%s, %s);"
            % (
                res_name,
                dict_arg_name,
                context.getConstantCode(statement.getVariableName()),
            )
        )

        getErrorExitBoolCode(
            condition="%s == -1" % res_name,
            needs_check=statement.mayRaiseException(BaseException),
            emit=emit,
            context=context,
        )


def generateLocalsDictVariableRefOrFallbackCode(to_name, expression, emit, context):
    variable_name = expression.getVariableName()

    fallback_emit = SourceCodeCollector()

    with withObjectCodeTemporaryAssignment(
        to_name, "locals_lookup_value", expression, emit, context
    ) as value_name:

        generateExpressionCode(
            to_name=value_name,
            expression=expression.subnode_fallback,
            emit=fallback_emit,
            context=context,
        )

        locals_scope = expression.getLocalsDictScope()
        locals_declaration = context.addLocalsDictName(locals_scope.getCodeName())

        is_dict = locals_scope.hasShapeDictionaryExact()

        assert not context.needsCleanup(value_name)

        if is_dict:
            template = template_read_locals_dict_with_fallback
            fallback_codes = indented(fallback_emit.codes)

            emit(
                template
                % {
                    "to_name": value_name,
                    "locals_dict": locals_declaration,
                    "fallback": fallback_codes,
                    "var_name": context.getConstantCode(constant=variable_name),
                }
            )
        else:
            template = template_read_locals_mapping_with_fallback
            fallback_codes = indented(fallback_emit.codes, 2)

            emit(
                template
                % {
                    "to_name": value_name,
                    "locals_dict": locals_declaration,
                    "fallback": fallback_codes,
                    "var_name": context.getConstantCode(constant=variable_name),
                    "exception_exit": context.getExceptionEscape(),
                }
            )

            # If the fallback took no reference, then make it do it
            # anyway.
            context.addCleanupTempName(value_name)


def generateLocalsDictVariableRefCode(to_name, expression, emit, context):
    variable_name = expression.getVariableName()
    locals_scope = expression.getLocalsDictScope()

    locals_declaration = context.addLocalsDictName(locals_scope.getCodeName())

    is_dict = locals_scope.hasShapeDictionaryExact()

    if is_dict:
        template = template_read_locals_dict_without_fallback
    else:
        template = template_read_locals_mapping_without_fallback

    with withObjectCodeTemporaryAssignment(
        to_name, "locals_lookup_value", expression, emit, context
    ) as value_name:

        emit(
            template
            % {
                "to_name": value_name,
                "locals_dict": locals_declaration,
                "var_name": context.getConstantCode(constant=variable_name),
            }
        )

        getNameReferenceErrorCode(
            variable_name=variable_name,
            condition="%s == NULL && CHECK_AND_CLEAR_KEY_ERROR_OCCURRED()" % value_name,
            emit=emit,
            context=context,
        )

        getErrorExitCode(check_name=value_name, emit=emit, context=context)

        if not is_dict:
            context.addCleanupTempName(value_name)


def generateLocalsDictVariableCheckCode(to_name, expression, emit, context):
    variable_name = expression.getVariableName()

    locals_scope = expression.getLocalsDictScope()

    locals_declaration = context.addLocalsDictName(locals_scope.getCodeName())

    is_dict = locals_scope.hasShapeDictionaryExact()

    if is_dict:
        to_name.getCType().emitAssignmentCodeFromBoolCondition(
            to_name=to_name,
            condition="DICT_HAS_ITEM(%(locals_dict)s, %(var_name)s) == 1"
            % {
                "locals_dict": locals_declaration,
                "var_name": context.getConstantCode(constant=variable_name),
            },
            emit=emit,
        )
    else:
        tmp_name = context.getIntResName()

        template = """\
%(tmp_name)s = MAPPING_HAS_ITEM(%(locals_dict)s, %(var_name)s);
"""

        emit(
            template
            % {
                "locals_dict": locals_declaration,
                "var_name": context.getConstantCode(constant=variable_name),
                "tmp_name": tmp_name,
            }
        )

        getErrorExitBoolCode(
            condition="%s == -1" % tmp_name,
            needs_check=expression.mayRaiseException(BaseException),
            emit=emit,
            context=context,
        )

        to_name.getCType().emitAssignmentCodeFromBoolCondition(
            to_name=to_name, condition="%s == 1" % tmp_name, emit=emit
        )
