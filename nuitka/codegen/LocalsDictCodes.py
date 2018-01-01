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
""" Code generation for locals dict handling.

These are variable handling for classes and partially also Python2 exec
statements.
"""

from nuitka.nodes.shapes.BuiltinTypeShapes import ShapeTypeDict

from .CodeHelpers import generateExpressionCode
from .Emission import SourceCodeCollector
from .ErrorCodes import getErrorExitBoolCode, getReleaseCodes
from .Indentation import indented
from .PythonAPICodes import getReferenceExportCode
from .templates.CodeTemplatesVariables import (
    template_read_locals_dict_with_fallback,
    template_read_locals_mapping_with_fallback
)


def generateSetLocalsDictCode(statement, emit, context):
    new_locals_name = context.allocateTempName("set_locals", unique = True)

    generateExpressionCode(
        to_name    = new_locals_name,
        expression = statement.getNewLocals(),
        emit       = emit,
        context    = context
    )

    locals_dict_name = statement.getLocalsScope().getCodeName()
    context.addLocalsDictName(locals_dict_name)

    emit(
        """\
%(locals_dict)s = %(locals_value)s;""" % {
            "locals_dict"  : locals_dict_name,
            "locals_value" : new_locals_name
        }
    )


    getReferenceExportCode(new_locals_name, emit, context)

    if context.needsCleanup(new_locals_name):
        context.removeCleanupTempName(new_locals_name)


def generateReleaseLocalsDictCode(statement, emit, context):
    # The statement has it all, pylint: disable=unused-argument

    locals_dict_name = statement.getLocalsScope().getCodeName()

    emit(
        """\
Py_DECREF( %(locals_dict)s );
%(locals_dict)s = NULL;""" % {
            "locals_dict"  : locals_dict_name,
        }
    )


def generateLocalsDictSetCode(statement, emit, context):
    value_arg_name = context.allocateTempName("dictset_value", unique = True)
    generateExpressionCode(
        to_name    = value_arg_name,
        expression = statement.subnode_value,
        emit       = emit,
        context    = context
    )

    context.setCurrentSourceCodeReference(statement.getSourceReference())

    locals_scope = statement.getLocalsDictScope()

    dict_arg_name = locals_scope.getCodeName()
    is_dict = locals_scope.getTypeShape() is ShapeTypeDict

    res_name = context.getIntResName()

    if is_dict:
        emit(
            "%s = PyDict_SetItem( %s, %s, %s );" % (
                res_name,
                dict_arg_name,
                context.getConstantCode(statement.getVariableName()),
                value_arg_name
            )
        )
    else:
        emit(
            "%s = PyObject_SetItem( %s, %s, %s );" % (
                res_name,
                dict_arg_name,
                context.getConstantCode(statement.getVariableName()),
                value_arg_name
            )
        )

    getReleaseCodes(
        release_names = (value_arg_name, dict_arg_name),
        emit          = emit,
        context       = context
    )

    getErrorExitBoolCode(
        condition   = "%s != 0" % res_name,
        emit        = emit,
        needs_check = statement.mayRaiseException(BaseException),
        context     = context
    )


def generateLocalsDictDelCode(statement, emit, context):
    locals_scope = statement.getLocalsDictScope()

    dict_arg_name = locals_scope.getCodeName()
    is_dict = locals_scope.getTypeShape() is ShapeTypeDict

    context.setCurrentSourceCodeReference(statement.getSourceReference())

    if is_dict:
        res_name = context.getBoolResName()

        emit(
            "%s = DICT_REMOVE_ITEM( %s, %s );" % (
                res_name,
                dict_arg_name,
                context.getConstantCode(statement.getVariableName())
            )
        )

        getErrorExitBoolCode(
            condition   = "%s == false" % res_name,
            needs_check = statement.mayRaiseException(BaseException),
            emit        = emit,
            context     = context
        )
    else:
        res_name = context.getIntResName()

        emit(
            "%s = PyObject_DelItem( %s, %s );" % (
                res_name,
                dict_arg_name,
                context.getConstantCode(statement.getVariableName())
            )
        )

        getErrorExitBoolCode(
            condition   = "%s == -1" % res_name,
            needs_check = statement.mayRaiseException(BaseException),
            emit        = emit,
            context     = context
        )


def generateLocalsDictVariableRefOrFallbackCode(to_name, expression, emit, context):
    variable_name = expression.getVariableName()

    fallback_emit = SourceCodeCollector()

    generateExpressionCode(
        to_name    = to_name,
        expression = expression.subnode_fallback,
        emit       = fallback_emit,
        context    = context
    )

    locals_scope = expression.getLocalsDictScope()

    dict_arg_name = locals_scope.getCodeName()
    is_dict = locals_scope.getTypeShape() is ShapeTypeDict

    if is_dict:
        template = template_read_locals_dict_with_fallback
    else:
        template = template_read_locals_mapping_with_fallback

    emit(
        template % {
            "to_name"     : to_name,
            "locals_dict" : dict_arg_name,
            "fallback"    : indented(fallback_emit.codes),
            "var_name"    : context.getConstantCode(
                constant = variable_name
            )
        }
    )


def generateLocalsDictVariableRefCode(to_name, expression, emit, context):
    variable_name = expression.getVariableName()

    locals_scope = expression.getLocalsDictScope()

    dict_arg_name = locals_scope.getCodeName()
    is_dict = locals_scope.getTypeShape() is ShapeTypeDict

    # TODO: Be more special.
    if is_dict:
        template = template_read_locals_dict_with_fallback
    else:
        template = template_read_locals_mapping_with_fallback

    emit(
        template % {
            "to_name"     : to_name,
            "locals_dict" : dict_arg_name,
            "fallback"    : indented(""),
            "var_name"    : context.getConstantCode(
                constant = variable_name
            )
        }
    )


def generateLocalsDictVariableCheckCode(to_name, expression, emit, context):
    variable_name = expression.getVariableName()

    is_dict = expression.getLocalsDictScope().getTypeShape() is ShapeTypeDict

    if is_dict:
        template = """\
%(to_name)s = PyDict_GetItem( %(locals_dict)s, %(var_name)s );

%(to_name)s = BOOL_FROM( %(to_name)s != NULL );
"""
        emit(
            template % {
                "locals_dict" : expression.getLocalsDictScope().getCodeName(),
                "var_name"    : context.getConstantCode(
                    constant = variable_name
                ),
                "to_name"     : to_name
            }
        )
    else:
        tmp_name = context.getIntResName()

        template = """\
%(tmp_name)s = MAPPING_HAS_ITEM( %(locals_dict)s, %(var_name)s );
"""

        emit(
            template % {
                "locals_dict" : expression.getLocalsDictScope().getCodeName(),
                "var_name"    : context.getConstantCode(
                    constant = variable_name
                ),
                "tmp_name"     : tmp_name
            }
        )

        getErrorExitBoolCode(
            condition   = "%s == -1" % tmp_name,
            needs_check = expression.mayRaiseException(BaseException),
            emit        = emit,
            context     = context
        )

        emit(
            """\
%(to_name)s = BOOL_FROM( %(tmp_name)s == 1 );
""" % {
                "to_name"  : to_name,
                "tmp_name" : tmp_name

            }
        )
