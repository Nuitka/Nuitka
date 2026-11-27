#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code generation for lists."""

from .CodeHelpers import (
    assignConstantNoneResult,
    decideConversionCheckNeeded,
    generateChildExpressionCode,
    generateChildExpressionsCode,
    generateExpressionCode,
    promoteBorrowedValue,
    withBorrowedValueScope,
    withCleanupFinally,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getReleaseCodes
from .PythonAPICodes import (
    generateCAPIErrorCode,
    generateCAPIObjectCode,
    generateCAPIObjectCode0,
    getCAPIErrorCode,
    makeArgDescFromExpression,
)


def generateListCreationCode(to_name, expression, emit, context):
    with withBorrowedValueScope(context):
        _generateListCreationCode(
            to_name=to_name, expression=expression, emit=emit, context=context
        )


def _generateListCreationCode(to_name, expression, emit, context):
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
            emit = guarded_emit

            for count, element in enumerate(elements):
                if count > 0:
                    helper_code = generateElementCode(element)

                emit(
                    "%s(%s, %d, %s);" % (helper_code, result_name, count, element_name)
                )

                context.unregisterBorrowedValue(element_name)


def generateListOperationAppendCode(statement, emit, context):
    list_arg_name, value_arg_name = generateChildExpressionsCode(
        expression=statement, emit=emit, context=context
    )

    with context.withCurrentSourceCodeReference(statement.getSourceReference()):
        if context.needsCleanup(value_arg_name):
            capi = "LIST_APPEND1"
            context.removeCleanupTempName(value_arg_name)
        else:
            capi = "LIST_APPEND0"

        getCAPIErrorCode(
            capi=capi,
            arg_names=(list_arg_name, value_arg_name),
            may_raise=statement.mayRaiseExceptionOperation(),
            release_names=(list_arg_name, value_arg_name),
            emit=emit,
            context=context,
        )


def generateListOperationAppendCode2(to_name, expression, emit, context):
    list_arg_name, value_arg_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    with context.withCurrentSourceCodeReference(expression.getSourceReference()):
        if context.needsCleanup(value_arg_name):
            capi = "LIST_APPEND1"
            context.removeCleanupTempName(value_arg_name)
        else:
            capi = "LIST_APPEND0"

        getCAPIErrorCode(
            capi=capi,
            arg_names=(list_arg_name, value_arg_name),
            may_raise=expression.mayRaiseExceptionOperation(),
            release_names=(list_arg_name, value_arg_name),
            emit=emit,
            context=context,
        )

    assignConstantNoneResult(to_name, emit, context)


def generateListOperationExtendCode(to_name, expression, emit, context):
    generateCAPIErrorCode(
        capi=(
            "LIST_EXTEND_FOR_UNPACK"
            if expression.isExpressionListOperationExtendForUnpack()
            else "LIST_EXTEND_FROM_ITERABLE"
        ),
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )

    assignConstantNoneResult(to_name, emit, context)


def generateListOperationClearCode(to_name, expression, emit, context):
    generateCAPIObjectCode0(
        to_name=None,
        capi="LIST_CLEAR",
        tstate=False,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )

    assignConstantNoneResult(to_name, emit, context)


def generateListOperationCopyCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="LIST_COPY",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateListOperationReverseCode(to_name, expression, emit, context):
    generateCAPIObjectCode0(
        to_name=None,
        capi="LIST_REVERSE",
        tstate=False,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )

    assignConstantNoneResult(to_name, emit, context)


def generateListOperationIndex2Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="LIST_INDEX2",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateListOperationIndex3Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="LIST_INDEX3",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateListOperationIndex4Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="LIST_INDEX4",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateListOperationInsertCode(to_name, expression, emit, context):
    is_integer_index = expression.subnode_index.isExpressionIntegerSubscript()

    if is_integer_index:
        list_arg_name = generateChildExpressionCode(
            expression=expression.subnode_list_arg, emit=emit, context=context
        )
        promoteBorrowedValue(
            value_name=list_arg_name,
            later_expressions=(expression.subnode_item,),
            emit=emit,
            context=context,
        )

        item_arg_name = generateChildExpressionCode(
            expression=expression.subnode_item, emit=emit, context=context
        )
    else:
        list_arg_name, index_arg_name, item_arg_name = generateChildExpressionsCode(
            expression=expression, emit=emit, context=context
        )

    if is_integer_index:
        index_constant = expression.subnode_index.getIndexValue()

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
        getCAPIErrorCode(
            capi="LIST_INSERT",
            arg_names=("tstate", list_arg_name, index_arg_name, item_arg_name),
            may_raise=expression.mayRaiseExceptionOperation(),
            release_names=(
                list_arg_name,
                index_arg_name,
                item_arg_name,
            ),
            emit=emit,
            context=context,
        )

    assignConstantNoneResult(to_name, emit, context)


def generateListOperationCountCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="LIST_COUNT",
        tstate=False,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


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
    generateCAPIErrorCode(
        capi="LIST_REMOVE",
        tstate=False,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        source_ref=expression.getCompatibleSourceReference(),
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
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
