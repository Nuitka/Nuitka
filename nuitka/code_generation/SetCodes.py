#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code generation for set creation and operations."""

from nuitka.PythonVersions import needsSetLiteralReverseInsertion

from .CodeHelpers import (
    assignConstantNoneResult,
    decideConversionCheckNeeded,
    generateChildExpressionsCode,
    generateExpressionCode,
    promoteBorrowedValue,
    withBorrowedValueScope,
    withCleanupFinally,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getAssertionCode, getErrorExitBoolCode
from .PythonAPICodes import (
    generateCAPIObjectCode,
    getCAPIErrorCode,
    makeArgDescFromExpression,
)


def generateSetCreationCode(to_name, expression, emit, context):
    with withBorrowedValueScope(context):
        _generateSetCreationCode(
            to_name=to_name, expression=expression, emit=emit, context=context
        )


def _generateSetCreationCode(to_name, expression, emit, context):
    element_name = context.allocateTempName("set_element")

    elements = expression.subnode_elements

    assert elements, expression

    with withObjectCodeTemporaryAssignment(
        to_name, "set_result", expression, emit, context
    ) as result_name:
        generateExpressionCode(
            to_name=element_name, expression=elements[0], emit=emit, context=context
        )

        first_element_needs_release = context.needsCleanup(element_name)
        if first_element_needs_release:
            context.removeCleanupTempName(element_name)

        emit("%s = PySet_New(NULL);" % (result_name,))
        getAssertionCode(result_name, emit)

        needs_exception_exit = any(
            element.mayRaiseException(BaseException) for element in elements[1:]
        ) or any(not element.isKnownToBeHashable() for element in elements)

        with withCleanupFinally(
            "set_build", result_name, needs_exception_exit, emit, context
        ) as guarded_emit:
            emit = guarded_emit

            if first_element_needs_release:
                context.addCleanupTempName(element_name)

            for count, element in enumerate(elements):
                if count > 0:
                    generateExpressionCode(
                        to_name=element_name,
                        expression=element,
                        emit=emit,
                        context=context,
                    )

                res_name = context.getIntResName()

                emit("%s = PySet_Add(%s, %s);" % (res_name, result_name, element_name))

                getErrorExitBoolCode(
                    condition="%s != 0" % res_name,
                    needs_check=not element.isKnownToBeHashable(),
                    emit=emit,
                    context=context,
                )

                if context.needsCleanup(element_name):
                    emit("Py_DECREF(%s);" % element_name)
                    context.removeCleanupTempName(element_name)

                context.unregisterBorrowedValue(element_name)


def generateSetLiteralCreationCode(to_name, expression, emit, context):
    with withBorrowedValueScope(context):
        _generateSetLiteralCreationCode(
            to_name=to_name, expression=expression, emit=emit, context=context
        )


def _generateSetLiteralCreationCode(to_name, expression, emit, context):
    if not needsSetLiteralReverseInsertion():
        return generateSetCreationCode(to_name, expression, emit, context)

    with withObjectCodeTemporaryAssignment(
        to_name, "set_result", expression, emit, context
    ) as result_name:
        emit("%s = PySet_New(NULL);" % (result_name,))
        getAssertionCode(result_name, emit)

        elements = expression.subnode_elements

        needs_exception_exit = any(
            element.mayRaiseException(BaseException) for element in elements
        ) or any(not element.isKnownToBeHashable() for element in elements)

        with withCleanupFinally(
            "set_literal_build", result_name, needs_exception_exit, emit, context
        ) as guarded_emit:
            emit = guarded_emit

            element_names = []

            for count, element in enumerate(elements, 1):
                element_name = context.allocateTempName("set_element_%d" % count)
                element_names.append(element_name)

                generateExpressionCode(
                    to_name=element_name, expression=element, emit=emit, context=context
                )
                if count < len(elements):
                    promoteBorrowedValue(
                        value_name=element_name,
                        later_expressions=elements[count:],
                        emit=emit,
                        context=context,
                    )

            for count, element in enumerate(elements):
                element_name = element_names[len(elements) - count - 1]

                if element.isKnownToBeHashable():
                    emit("PySet_Add(%s, %s);" % (result_name, element_name))
                else:
                    res_name = context.getIntResName()

                    emit(
                        "%s = PySet_Add(%s, %s);"
                        % (res_name, result_name, element_name)
                    )

                    getErrorExitBoolCode(
                        condition="%s != 0" % res_name, emit=emit, context=context
                    )

                if context.needsCleanup(element_name):
                    emit("Py_DECREF(%s);" % element_name)
                    context.removeCleanupTempName(element_name)

                context.unregisterBorrowedValue(element_name)


def generateSetOperationAddCode(statement, emit, context):
    set_arg_name, value_arg_name = generateChildExpressionsCode(
        expression=statement, emit=emit, context=context
    )

    with context.withCurrentSourceCodeReference(statement.getSourceReference()):
        emit("assert(PySet_Check(%s));" % set_arg_name)
        getCAPIErrorCode(
            capi="PySet_Add",
            arg_names=(set_arg_name, value_arg_name),
            may_raise=statement.mayRaiseExceptionOperation(),
            release_names=(set_arg_name, value_arg_name),
            res_type="int_neg1",
            emit=emit,
            context=context,
        )


def generateSetOperationUpdateCode(to_name, expression, emit, context):
    set_arg_name, value_arg_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    emit("assert(PySet_Check(%s));" % set_arg_name)
    getCAPIErrorCode(
        capi="_PySet_Update",
        arg_names=(set_arg_name, value_arg_name),
        may_raise=expression.mayRaiseExceptionOperation(),
        release_names=(set_arg_name, value_arg_name),
        res_type="int_neg1",
        emit=emit,
        context=context,
    )

    assignConstantNoneResult(to_name, emit, context)


def generateBuiltinSetCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="PySet_New",
        tstate=False,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinFrozensetCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="PyFrozenSet_New",
        tstate=False,
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
