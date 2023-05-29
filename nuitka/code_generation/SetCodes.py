#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.PythonVersions import needsSetLiteralReverseInsertion

from .CodeHelpers import (
    assignConstantNoneResult,
    decideConversionCheckNeeded,
    generateChildExpressionsCode,
    generateExpressionCode,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getAssertionCode, getErrorExitBoolCode
from .PythonAPICodes import generateCAPIObjectCode


def generateSetCreationCode(to_name, expression, emit, context):
    element_name = context.allocateTempName("set_element")

    elements = expression.subnode_elements

    # Supposed to optimize empty set to constant value.
    assert elements, expression

    with withObjectCodeTemporaryAssignment(
        to_name, "set_result", expression, emit, context
    ) as result_name:

        for count, element in enumerate(elements):
            generateExpressionCode(
                to_name=element_name, expression=element, emit=emit, context=context
            )

            if count == 0:
                emit("%s = PySet_New(NULL);" % (result_name,))
                getAssertionCode(result_name, emit)

                context.addCleanupTempName(to_name)

            res_name = context.getIntResName()

            emit("%s = PySet_Add(%s, %s);" % (res_name, to_name, element_name))

            getErrorExitBoolCode(
                condition="%s != 0" % res_name,
                needs_check=not element.isKnownToBeHashable(),
                emit=emit,
                context=context,
            )

            if context.needsCleanup(element_name):
                emit("Py_DECREF(%s);" % element_name)
                context.removeCleanupTempName(element_name)


def generateSetLiteralCreationCode(to_name, expression, emit, context):
    if not needsSetLiteralReverseInsertion():
        return generateSetCreationCode(to_name, expression, emit, context)

    with withObjectCodeTemporaryAssignment(
        to_name, "set_result", expression, emit, context
    ) as result_name:

        emit("%s = PySet_New(NULL);" % (result_name,))

        context.addCleanupTempName(result_name)

        elements = expression.subnode_elements

        element_names = []

        for count, element in enumerate(elements, 1):
            element_name = context.allocateTempName("set_element_%d" % count)
            element_names.append(element_name)

            generateExpressionCode(
                to_name=element_name, expression=element, emit=emit, context=context
            )

        for count, element in enumerate(elements):
            element_name = element_names[len(elements) - count - 1]

            if element.isKnownToBeHashable():
                emit("PySet_Add(%s, %s);" % (result_name, element_name))
            else:
                res_name = context.getIntResName()

                emit("%s = PySet_Add(%s, %s);" % (res_name, result_name, element_name))

                getErrorExitBoolCode(
                    condition="%s != 0" % res_name, emit=emit, context=context
                )

            if context.needsCleanup(element_name):
                emit("Py_DECREF(%s);" % element_name)
                context.removeCleanupTempName(element_name)


def generateSetOperationAddCode(statement, emit, context):

    set_arg_name = context.allocateTempName("add_set")
    generateExpressionCode(
        to_name=set_arg_name,
        expression=statement.subnode_set_arg,
        emit=emit,
        context=context,
    )

    value_arg_name = context.allocateTempName("add_value")
    generateExpressionCode(
        to_name=value_arg_name,
        expression=statement.subnode_value,
        emit=emit,
        context=context,
    )

    context.setCurrentSourceCodeReference(statement.getSourceReference())

    res_name = context.getIntResName()

    emit("assert(PySet_Check(%s));" % set_arg_name)
    emit("%s = PySet_Add(%s, %s);" % (res_name, set_arg_name, value_arg_name))

    getErrorExitBoolCode(
        condition="%s == -1" % res_name,
        release_names=(set_arg_name, value_arg_name),
        emit=emit,
        context=context,
    )


def generateSetOperationUpdateCode(to_name, expression, emit, context):
    res_name = context.getIntResName()

    set_arg_name, value_arg_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    emit("assert(PySet_Check(%s));" % set_arg_name)
    emit("%s = _PySet_Update(%s, %s);" % (res_name, set_arg_name, value_arg_name))

    getErrorExitBoolCode(
        condition="%s == -1" % res_name,
        release_names=(set_arg_name, value_arg_name),
        emit=emit,
        context=context,
    )

    assignConstantNoneResult(to_name, emit, context)


def generateBuiltinSetCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="PySet_New",
        arg_desc=(("set_arg", expression.subnode_value),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinFrozensetCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="PyFrozenSet_New",
        arg_desc=(("frozenset_arg", expression.subnode_value),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )
