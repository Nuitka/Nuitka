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
""" Code generation for sets.

Right now only the creation, and set add code is done here. But more should be
added later on.
"""

from .ErrorCodes import getErrorExitBoolCode, getReleaseCodes
from .Helpers import generateChildExpressionsCode, generateExpressionCode
from .PythonAPICodes import generateCAPIObjectCode


def generateSetCreationCode(to_name, expression, emit, context):
    emit(
        "%s = PySet_New( NULL );" % (
            to_name,
        )
    )

    context.addCleanupTempName(to_name)

    element_name = context.allocateTempName("set_element")

    for element in expression.getElements():
        generateExpressionCode(
            to_name    = element_name,
            expression = element,
            emit       = emit,
            context    = context
        )

        if element.isKnownToBeHashable():
            emit(
                "PySet_Add( %s, %s );" % (
                    to_name,
                    element_name
                )
            )
        else:
            res_name = context.getIntResName()

            emit(
                "%s = PySet_Add( %s, %s );" % (
                    res_name,
                    to_name,
                    element_name
                )
            )

            getErrorExitBoolCode(
                condition = "%s != 0" % res_name,
                emit      = emit,
                context   = context
            )

        if context.needsCleanup(element_name):
            emit("Py_DECREF( %s );" % element_name)
            context.removeCleanupTempName(element_name)


def generateSetOperationAddCode(statement, emit, context):
    set_arg_name = context.allocateTempName("append_list")
    generateExpressionCode(
        to_name    = set_arg_name,
        expression = statement.getSet(),
        emit       = emit,
        context    = context
    )

    value_arg_name = context.allocateTempName("append_value")
    generateExpressionCode(
        to_name    = value_arg_name,
        expression = statement.getValue(),
        emit       = emit,
        context    = context
    )

    context.setCurrentSourceCodeReference(statement.getSourceReference())

    res_name = context.getIntResName()

    emit("assert( PySet_Check( %s ) );" % set_arg_name)
    emit(
        "%s = PySet_Add( %s, %s );" % (
            res_name,
            set_arg_name,
            value_arg_name
        )
    )

    getReleaseCodes(
        release_names = (set_arg_name, value_arg_name),
        emit          = emit,
        context       = context
    )

    getErrorExitBoolCode(
        condition = "%s == -1" % res_name,
        emit      = emit,
        context   = context
    )


def generateSetOperationUpdateCode(to_name, expression, emit, context):
    res_name = context.getIntResName()

    set_arg_name, value_arg_name = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    emit("assert( PySet_Check( %s ) );" % set_arg_name)
    emit(
        "%s = _PySet_Update( %s, %s );" % (
            res_name,
            set_arg_name,
            value_arg_name
        )
    )

    getReleaseCodes(
        release_names = (set_arg_name, value_arg_name),
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


def generateBuiltinSetCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "PySet_New",
        arg_desc   = (
            ("set_arg", expression.getValue()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )
