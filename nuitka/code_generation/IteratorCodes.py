#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Iteration related codes.

Next variants and unpacking with related checks.
"""

from nuitka.PythonVersions import python_version

from .CodeHelpers import (
    decideConversionCheckNeeded,
    generateChildExpressionsCode,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import (
    getErrorExitCode,
    getErrorExitReleaseCode,
    getReleaseCode,
)
from .LineNumberCodes import getErrorLineNumberUpdateCode
from .PythonAPICodes import (
    CArg,
    TupleArg,
    generateCAPIBoolCode,
    generateCAPIErrorCode,
    generateCAPIObjectCode,
    makeArgDescFromExpression,
)
from .templates.CodeTemplatesIterators import template_loop_break_next


def _emitIteratorNextCode(expression, to_name, value, emit):
    if expression.getTypeShape().isShapeIterator():
        emit("%s = ITERATOR_NEXT_ITERATOR(%s);" % (to_name, value))
    else:
        emit("%s = ITERATOR_NEXT(%s);" % (to_name, value))


def generateBuiltinNext1Code(to_name, expression, emit, context):
    (value_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    (
        exception_state_name,
        _exception_lineno,
    ) = context.getExceptionVariableDescriptions()

    with withObjectCodeTemporaryAssignment(
        to_name, "next_value", expression, emit, context
    ) as result_name:
        _emitIteratorNextCode(
            expression=expression.subnode_value,
            to_name=result_name,
            value=value_name,
            emit=emit,
        )

        emit(
            """\
if (%(to_name)s == NULL) {
    FETCH_ERROR_OCCURRED_STATE(tstate, &%(exception_state_name)s);

    if (!HAS_EXCEPTION_STATE(&%(exception_state_name)s)) {
        SET_EXCEPTION_PRESERVATION_STATE_STOP_ITERATION_EMPTY(tstate, &%(exception_state_name)s);
    }
}
"""
            % {
                "to_name": result_name,
                "exception_state_name": exception_state_name,
            }
        )

        getErrorExitCode(
            check_name=result_name,
            release_name=value_name,
            fetched_exception=True,
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(result_name)


def generateBuiltinEnumerate1Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_ENUMERATE1",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinEnumerate2Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_ENUMERATE2",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinZipCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_ZIP",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinZip310Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_ZIP310",
        tstate=True,
        arg_desc=(
            TupleArg("zip_iterables", expression.subnode_values),
            ("zip_strict", expression.subnode_strict),
        ),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def getBuiltinLoopBreakNextCode(expression, to_name, value, emit, context):
    _emitIteratorNextCode(
        expression=expression,
        to_name=to_name,
        value=value,
        emit=emit,
    )

    getReleaseCode(release_name=value, emit=emit, context=context)

    break_target = context.getLoopBreakTarget()
    if type(break_target) is tuple:
        break_indicator_code = "%s = true;" % break_target[1]
        break_target = break_target[0]
    else:
        break_indicator_code = ""

    (
        exception_state_name,
        _exception_lineno,
    ) = context.getExceptionVariableDescriptions()

    emit(
        template_loop_break_next
        % {
            "to_name": to_name,
            "break_indicator_code": break_indicator_code,
            "break_target": break_target,
            "release_temps": getErrorExitReleaseCode(context),
            "line_number_code": getErrorLineNumberUpdateCode(context),
            "exception_target": context.getExceptionEscape(),
            "exception_state_name": exception_state_name,
        }
    )

    context.addCleanupTempName(to_name)


def generateSpecialUnpackCode(to_name, expression, emit, context):
    may_raise = expression.mayRaiseExceptionOperation()

    if not may_raise:
        capi = "UNPACK_NEXT_INFALLIBLE"
        tstate = False
        arg_desc = makeArgDescFromExpression(expression)
    elif python_version < 0x350:
        capi = "UNPACK_NEXT"
        tstate = True
        arg_desc = makeArgDescFromExpression(expression) + (
            CArg(expression.getCount() - 1),
        )
    else:
        capi = "UNPACK_NEXT_STARRED" if expression.getStarred() else "UNPACK_NEXT"
        tstate = True
        arg_desc = makeArgDescFromExpression(expression) + (
            CArg(expression.getCount() - 1),
            CArg(expression.getExpected()),
        )

    generateCAPIObjectCode(
        to_name=to_name,
        capi=capi,
        tstate=tstate,
        arg_desc=arg_desc,
        may_raise=may_raise,
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        fetched_exception=True,
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateUnpackCheckCode(statement, emit, context):
    generateCAPIErrorCode(
        capi="UNPACK_ITERATOR_CHECK",
        tstate=True,
        arg_desc=makeArgDescFromExpression(statement) + (CArg(statement.getCount()),),
        may_raise=statement.mayRaiseExceptionOperation(),
        fetched_exception=True,
        source_ref=statement.getSourceReference(),
        emit=emit,
        context=context,
    )


def generateUnpackCheckFromIteratedCode(statement, emit, context):
    generateCAPIErrorCode(
        capi="UNPACK_ITERATED_CHECK",
        tstate=True,
        arg_desc=makeArgDescFromExpression(statement) + (CArg(statement.getCount()),),
        may_raise=statement.mayRaiseExceptionOperation(),
        fetched_exception=True,
        source_ref=statement.getSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinNext2Code(to_name, expression, emit, context):
    if expression.subnode_iterator.getTypeShape().isShapeIterator():
        capi = "BUILTIN_NEXT2_ITERATOR"
    else:
        capi = "BUILTIN_NEXT2"

    generateCAPIObjectCode(
        to_name=to_name,
        capi=capi,
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateIsIterableCode(to_name, expression, emit, context):
    generateCAPIBoolCode(
        to_name=to_name,
        capi="IS_ITERABLE",
        tstate=False,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        res_type="bool",
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinIter1Code(to_name, expression, emit, context):
    may_raise = expression.mayRaiseExceptionOperation()

    generateCAPIObjectCode(
        to_name=to_name,
        capi="MAKE_ITERATOR" if may_raise else "MAKE_ITERATOR_INFALLIBLE",
        tstate=may_raise,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=may_raise,
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinIterForUnpackCode(to_name, expression, emit, context):
    may_raise = expression.mayRaiseExceptionOperation()

    generateCAPIObjectCode(
        to_name=to_name,
        capi="MAKE_UNPACK_ITERATOR" if may_raise else "MAKE_ITERATOR_INFALLIBLE",
        tstate=False,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=may_raise,
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinIter2Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_ITER2",
        tstate=False,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinLenCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_LEN",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinAnyCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_ANY",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinAllCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_ALL",
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
