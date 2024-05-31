#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Code generation for lists.

Right now only the creation is done here. But more should be added later on.
"""

from .CodeHelpers import (
    assignConstantNoneResult,
    decideConversionCheckNeeded,
    generateChildExpressionCode,
    generateChildExpressionsCode,
    generateExpressionCode,
    withCleanupFinally,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import (
    getErrorExitBoolCode,
    getErrorExitCode,
    getReleaseCode,
    getReleaseCodes,
)
from .PythonAPICodes import (
    generateCAPIObjectCode,
    generateCAPIObjectCode0,
    makeArgDescFromExpression,
)
from .SubscriptCodes import decideIntegerSubscript


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

        emit("%s = MAKE_LIST_EMPTY(tstate, %d);" % (result_name, len(elements)))

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


def generateListOperationAppendCode2(to_name, expression, emit, context):
    list_arg_name, value_arg_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    context.setCurrentSourceCodeReference(expression.getSourceReference())

    res_name = context.getBoolResName()

    if context.needsCleanup(value_arg_name):
        emit("%s = LIST_APPEND1(%s, %s);" % (res_name, list_arg_name, value_arg_name))
        context.removeCleanupTempName(value_arg_name)
    else:
        emit("%s = LIST_APPEND0(%s, %s);" % (res_name, list_arg_name, value_arg_name))

    # TODO: Only really MemoryError, which we often ignore.
    getErrorExitBoolCode(
        condition="%s == false" % res_name,
        release_names=(list_arg_name, value_arg_name),
        needs_check=False,
        emit=emit,
        context=context,
    )

    assignConstantNoneResult(to_name, emit, context)


def generateListOperationExtendCode(to_name, expression, emit, context):
    list_arg_name, value_arg_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    # These give different error messages.
    is_unpack = expression.isExpressionListOperationExtendForUnpack()

    res_name = context.getBoolResName()

    emit(
        "%s = %s(tstate, %s, %s);"
        % (
            res_name,
            "LIST_EXTEND_FOR_UNPACK" if is_unpack else "LIST_EXTEND_FROM_ITERABLE",
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


def generateListOperationClearCode(to_name, expression, emit, context):
    (list_arg_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    emit("LIST_CLEAR(%s);" % list_arg_name)

    getReleaseCode(release_name=list_arg_name, emit=emit, context=context)

    assignConstantNoneResult(to_name, emit, context)


def generateListOperationCopyCode(to_name, expression, emit, context):
    (list_arg_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "list_copy_result", expression, emit, context
    ) as result_name:
        emit("%s = LIST_COPY(tstate, %s);" % (result_name, list_arg_name))

        getErrorExitCode(
            check_name=result_name,
            release_name=list_arg_name,
            emit=emit,
            needs_check=False,
            context=context,
        )

        context.addCleanupTempName(result_name)


def generateListOperationReverseCode(to_name, expression, emit, context):
    (list_arg_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    emit("LIST_REVERSE(%s);" % list_arg_name)

    getReleaseCode(release_name=list_arg_name, emit=emit, context=context)

    assignConstantNoneResult(to_name, emit, context)


def generateListOperationIndex2Code(to_name, expression, emit, context):
    list_arg_name, value_arg_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "list_index_result", expression, emit, context
    ) as result_name:
        emit(
            "%s = LIST_INDEX2(tstate, %s, %s);"
            % (result_name, list_arg_name, value_arg_name)
        )

        getErrorExitCode(
            check_name=result_name,
            release_names=(list_arg_name, value_arg_name),
            needs_check=expression.mayRaiseExceptionOperation(),
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(result_name)


def generateListOperationIndex3Code(to_name, expression, emit, context):
    list_arg_name, value_arg_name, start_arg_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "list_index_result", expression, emit, context
    ) as result_name:
        emit(
            "%s = LIST_INDEX3(tstate, %s, %s, %s);"
            % (result_name, list_arg_name, value_arg_name, start_arg_name)
        )

        getErrorExitCode(
            check_name=result_name,
            release_names=(list_arg_name, value_arg_name, start_arg_name),
            needs_check=expression.mayRaiseExceptionOperation(),
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(result_name)


def generateListOperationIndex4Code(to_name, expression, emit, context):
    (
        list_arg_name,
        value_arg_name,
        start_arg_name,
        stop_arg_name,
    ) = generateChildExpressionsCode(expression=expression, emit=emit, context=context)

    with withObjectCodeTemporaryAssignment(
        to_name, "list_index_result", expression, emit, context
    ) as result_name:
        emit(
            "%s = LIST_INDEX4(tstate, %s, %s, %s, %s);"
            % (
                result_name,
                list_arg_name,
                value_arg_name,
                start_arg_name,
                stop_arg_name,
            )
        )

        getErrorExitCode(
            check_name=result_name,
            release_names=(
                list_arg_name,
                value_arg_name,
                start_arg_name,
                stop_arg_name,
            ),
            needs_check=expression.mayRaiseExceptionOperation(),
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(result_name)


def generateListOperationInsertCode(to_name, expression, emit, context):
    index_constant, is_integer_index = decideIntegerSubscript(expression.subnode_index)

    if is_integer_index:
        list_arg_name = generateChildExpressionCode(
            expression=expression.subnode_list_arg, emit=emit, context=context
        )

        item_arg_name = generateChildExpressionCode(
            expression=expression.subnode_item, emit=emit, context=context
        )
    else:
        list_arg_name, index_arg_name, item_arg_name = generateChildExpressionsCode(
            expression=expression, emit=emit, context=context
        )

    if is_integer_index:
        emit(
            "LIST_INSERT_CONST(%s, %s, %s);"
            % (
                list_arg_name,
                index_constant,
                item_arg_name,
            )
        )

        getReleaseCodes(
            release_names=(
                list_arg_name,
                item_arg_name,
            ),
            emit=emit,
            context=context,
        )
    else:
        res_name = context.getBoolResName()

        emit(
            "%s = LIST_INSERT(tstate, %s, %s, %s);"
            % (
                res_name,
                list_arg_name,
                index_arg_name,
                item_arg_name,
            )
        )

        getErrorExitBoolCode(
            condition="%s == false" % res_name,
            release_names=(
                list_arg_name,
                index_arg_name,
                item_arg_name,
            ),
            needs_check=expression.mayRaiseExceptionOperation(),
            emit=emit,
            context=context,
        )

    assignConstantNoneResult(to_name, emit, context)


def generateListOperationCountCode(to_name, expression, emit, context):
    list_arg_name, value_arg_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "list_count_result", expression, emit, context
    ) as result_name:
        emit("%s = LIST_COUNT(%s, %s);" % (result_name, list_arg_name, value_arg_name))

        getErrorExitCode(
            check_name=result_name,
            release_names=(list_arg_name, value_arg_name),
            emit=emit,
            needs_check=expression.mayRaiseExceptionOperation(),
            context=context,
        )

        context.addCleanupTempName(result_name)


def generateListOperationPop1Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="LIST_POP1",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateListOperationPop2Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="LIST_POP2",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateListOperationRemoveCode(to_name, expression, emit, context):
    (list_arg_name, value_arg_name) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    res_name = context.getBoolResName()

    emit("%s = LIST_REMOVE(%s, %s);" % (res_name, list_arg_name, value_arg_name))

    getErrorExitBoolCode(
        condition="%s == false" % res_name,
        release_names=(list_arg_name, value_arg_name),
        needs_check=expression.mayRaiseExceptionOperation(),
        emit=emit,
        context=context,
    )

    assignConstantNoneResult(to_name, emit, context)


def generateListOperationSort1Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="LIST_SORT1",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateListOperationSort2Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="LIST_SORT2",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateListOperationSort3Code(to_name, expression, emit, context):
    generateCAPIObjectCode0(
        to_name=to_name,
        capi="LIST_SORT3",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        none_null=True,
        emit=emit,
        context=context,
    )


def generateBuiltinListCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="MAKE_LIST",
        tstate=True,
        arg_desc=(("list_arg", expression.subnode_value),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


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
