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
""" Code generation for lists.

Right now only the creation is done here. But more should be added later on.
"""

from .CodeHelpers import (
    assignConstantNoneResult,
    decideConversionCheckNeeded,
    generateChildExpressionsCode,
    generateExpressionCode,
    withCleanupFinally,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getErrorExitBoolCode, getErrorExitCode
from .PythonAPICodes import generateCAPIObjectCode


def generateListCreationCode(to_name, expression, emit, context):
    elements = expression.subnode_elements
    assert elements

    with withObjectCodeTemporaryAssignment(
        to_name, "list_result", expression, emit, context
    ) as result_name:
        element_name = context.allocateTempName("list_element")

        def generateElementCode(element):
            generateExpressionCode(
                to_name=element_name, expression=element, emit=emit, context=context
            )

            # Use helper that makes sure we provide a reference.
            if context.needsCleanup(element_name):
                context.removeCleanupTempName(element_name)
                helper_code = "PyList_SET_ITEM"
            else:
                helper_code = "PyList_SET_ITEM0"

            return helper_code

        helper_code = generateElementCode(elements[0])

        emit("%s = PyList_New(%d);" % (result_name, len(elements)))

        needs_exception_exit = any(
            element.mayRaiseException(BaseException) for element in elements[1:]
        )

        with withCleanupFinally(
            "list_build", result_name, needs_exception_exit, emit, context
        ) as guarded_emit:
            emit = guarded_emit.emit

            for count, element in enumerate(elements):
                if count > 0:
                    helper_code = generateElementCode(element)

                emit(
                    "%s(%s, %d, %s);" % (helper_code, result_name, count, element_name)
                )


def generateListOperationAppendCode(statement, emit, context):
    list_arg_name = context.allocateTempName("append_list")
    generateExpressionCode(
        to_name=list_arg_name,
        expression=statement.subnode_list_arg,
        emit=emit,
        context=context,
    )

    value_arg_name = context.allocateTempName("append_value")
    generateExpressionCode(
        to_name=value_arg_name,
        expression=statement.subnode_value,
        emit=emit,
        context=context,
    )

    context.setCurrentSourceCodeReference(statement.getSourceReference())

    res_name = context.getBoolResName()

    emit("assert(PyList_Check(%s));" % list_arg_name)

    if context.needsCleanup(value_arg_name):
        emit("%s = LIST_APPEND1(%s, %s);" % (res_name, list_arg_name, value_arg_name))
        context.removeCleanupTempName(value_arg_name)
    else:
        emit("%s = LIST_APPEND0(%s, %s);" % (res_name, list_arg_name, value_arg_name))

    # TODO: Only really MemoryError, which we often ignore.
    getErrorExitBoolCode(
        condition="%s == false" % res_name,
        release_names=(list_arg_name, value_arg_name),
        emit=emit,
        context=context,
    )


def generateListOperationExtendCode(to_name, expression, emit, context):
    list_arg_name, value_arg_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    emit("assert(PyList_Check(%s));" % list_arg_name)

    # These give different error messages.
    is_unpack = expression.isExpressionListOperationExtendForUnpack()

    res_name = context.getBoolResName()

    emit(
        "%s = %s(%s, %s);"
        % (
            res_name,
            "LIST_EXTEND_FOR_UNPACK" if is_unpack else "LIST_EXTEND",
            list_arg_name,
            value_arg_name,
        )
    )

    getErrorExitBoolCode(
        condition="%s == false" % res_name,
        release_names=(list_arg_name, value_arg_name),
        emit=emit,
        context=context,
    )

    assignConstantNoneResult(to_name, emit, context)


def generateListOperationPopCode(to_name, expression, emit, context):
    (list_arg_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    emit("assert(PyList_Check(%s));" % list_arg_name)

    with withObjectCodeTemporaryAssignment(
        to_name, "list_pop_result", expression, emit, context
    ) as result_name:

        # TODO: Have a dedicated helper instead, this could be more efficient.
        emit(
            '%s = PyObject_CallMethod(%s, (char *)"pop", NULL);'
            % (result_name, list_arg_name)
        )

        getErrorExitCode(
            check_name=result_name,
            release_name=list_arg_name,
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(result_name)


def generateBuiltinListCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="MAKE_LIST",
        arg_desc=(("list_arg", expression.subnode_value),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )
