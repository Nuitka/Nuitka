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
""" Code generation for lists.

Right now only the creation is done here. But more should be added later on.
"""

from .ErrorCodes import (
    getErrorExitBoolCode,
    getErrorExitCode,
    getReleaseCode,
    getReleaseCodes
)
from .Helpers import generateChildExpressionsCode


def generateListCreationCode(to_name, elements, emit, context):
    emit(
        "%s = PyList_New( %d );" % (
            to_name,
            len(elements)
        )
    )

    from .CodeGeneration import generateExpressionCode

    context.addCleanupTempName(to_name)

    element_name = context.allocateTempName("list_element")

    for count, element in enumerate(elements):
        generateExpressionCode(
            to_name    = element_name,
            expression = element,
            emit       = emit,
            context    = context
        )

        if not context.needsCleanup(element_name):
            emit("Py_INCREF( %s );" % element_name)
        else:
            context.removeCleanupTempName(element_name)

        emit(
            "PyList_SET_ITEM( %s, %d, %s );" % (
                to_name,
                count,
                element_name
            )
        )


def generateListOperationAppendCode(to_name, expression, emit, context):
    res_name = context.getIntResName()

    list_arg_name, value_arg_name = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )


    emit("assert( PyList_Check( %s ) );" % list_arg_name)
    emit(
        "%s = PyList_Append( %s, %s );" % (
            res_name,
            list_arg_name,
            value_arg_name
        )
    )

    getReleaseCodes(
        release_names = (list_arg_name, value_arg_name),
        emit          = emit,
        context       = context
    )

    getErrorExitBoolCode(
        condition = "%s == -1" % res_name,
        emit      = emit,
        context   = context
    )

    # Only assign if necessary.
    if context.isUsed(to_name):
        emit(
            "%s = Py_None;" % to_name
        )
    else:
        context.forgetTempName(to_name)


def generateListOperationExtendCode(to_name, expression, emit, context):
    list_arg_name, value_arg_name = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    emit("assert( PyList_Check( %s ) );" % list_arg_name)
    emit(
        "%s = _PyList_Extend( (PyListObject *)%s, %s );" % (
            to_name,
            list_arg_name,
            value_arg_name
        )
    )

    getReleaseCodes(
        release_names = (list_arg_name, value_arg_name),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def generateListOperationPopCode(to_name, expression, emit, context):
    list_arg_name, = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    # TODO: Have a dedicated helper instead, this could be more efficient.
    emit("assert( PyList_Check( %s ) );" % list_arg_name)
    emit(
        '%s = PyObject_CallMethod(  %s, (char *)"pop", NULL );' % (
            to_name,
            list_arg_name
        )
    )

    getReleaseCode(
        release_name = list_arg_name,
        emit         = emit,
        context      = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)
