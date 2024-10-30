#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Iteration related codes.

Next variants and unpacking with related checks.
"""

from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.PythonVersions import python_version

from .CodeHelpers import (
    decideConversionCheckNeeded,
    generateChildExpressionsCode,
    generateExpressionCode,
    withObjectCodeTemporaryAssignment,
)
from .ComparisonCodes import getRichComparisonCode
from .ErrorCodes import (
    getErrorExitBoolCode,
    getErrorExitCode,
    getErrorExitReleaseCode,
    getFrameVariableTypeDescriptionCode,
    getReleaseCode,
)
from .Indentation import indented
from .LineNumberCodes import getErrorLineNumberUpdateCode
from .PythonAPICodes import generateCAPIObjectCode
from .templates.CodeTemplatesIterators import template_loop_break_next


def generateBuiltinNext1Code(to_name, expression, emit, context):
    (value_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    (
        exception_state_name,
        _exception_lineno,
    ) = context.variable_storage.getExceptionVariableDescriptions()

    with withObjectCodeTemporaryAssignment(
        to_name, "next_value", expression, emit, context
    ) as result_name:
        # TODO: Make use of "ITERATOR_NEXT_ITERATOR" in case of known type shape
        # iterator.
        emit(
            """\
%(to_name)s = ITERATOR_NEXT(%(iterator_name)s);
if (%(to_name)s == NULL) {
    FETCH_ERROR_OCCURRED_STATE(tstate, &%(exception_state_name)s);

    if (!HAS_EXCEPTION_STATE(&%(exception_state_name)s)) {
        SET_EXCEPTION_PRESERVATION_STATE_STOP_ITERATION_EMPTY(tstate, &%(exception_state_name)s);
    }
}
"""
            % {
                "to_name": result_name,
                "iterator_name": value_name,
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


def getBuiltinLoopBreakNextCode(expression, to_name, value, emit, context):
    if expression.getTypeShape().isShapeIterator():
        emit("%s = %s;" % (to_name, "ITERATOR_NEXT_ITERATOR(%s)" % value))
    else:
        emit("%s = %s;" % (to_name, "ITERATOR_NEXT(%s)" % value))

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
    ) = context.variable_storage.getExceptionVariableDescriptions()

    emit(
        template_loop_break_next
        % {
            "to_name": to_name,
            "break_indicator_code": break_indicator_code,
            "break_target": break_target,
            "release_temps": indented(getErrorExitReleaseCode(context), 8),
            "var_description_code": indented(
                getFrameVariableTypeDescriptionCode(context), 8
            ),
            "line_number_code": indented(getErrorLineNumberUpdateCode(context), 8),
            "exception_target": context.getExceptionEscape(),
            "exception_state_name": exception_state_name,
        }
    )

    context.addCleanupTempName(to_name)


def generateSpecialUnpackCode(to_name, expression, emit, context):
    value_name = context.allocateTempName("unpack")

    generateExpressionCode(
        to_name=value_name,
        expression=expression.subnode_value,
        emit=emit,
        context=context,
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "unpack_value", expression, emit, context
    ) as result_name:
        needs_check = expression.mayRaiseExceptionOperation()

        if not needs_check:
            emit("%s = UNPACK_NEXT_INFALLIBLE(%s);" % (result_name, value_name))
        elif python_version < 0x350:
            (
                exception_state_name,
                _exception_lineno,
            ) = context.variable_storage.getExceptionVariableDescriptions()

            emit(
                "%s = UNPACK_NEXT(tstate, &%s, %s, %s);"
                % (
                    result_name,
                    exception_state_name,
                    value_name,
                    expression.getCount() - 1,
                )
            )
        else:
            starred = expression.getStarred()
            expected = expression.getExpected()

            (
                exception_state_name,
                _exception_lineno,
            ) = context.variable_storage.getExceptionVariableDescriptions()

            emit(
                "%s = UNPACK_NEXT%s(tstate, &%s, %s, %s, %s);"
                % (
                    result_name,
                    "_STARRED" if starred else "",
                    exception_state_name,
                    value_name,
                    expression.getCount() - 1,
                    expected,
                )
            )

        getErrorExitCode(
            check_name=result_name,
            release_name=value_name,
            needs_check=needs_check,
            fetched_exception=True,
            emit=emit,
            context=context,
        )

    context.addCleanupTempName(to_name)


def generateUnpackCheckCode(statement, emit, context):
    iterator_name = context.allocateTempName("iterator_name")

    generateExpressionCode(
        to_name=iterator_name,
        expression=statement.subnode_iterator,
        emit=emit,
        context=context,
    )

    with context.withCurrentSourceCodeReference(statement.getSourceReference()):
        (
            exception_state_name,
            _exception_lineno,
        ) = context.variable_storage.getExceptionVariableDescriptions()

        res_name = context.getBoolResName()

        emit(
            "%s = UNPACK_ITERATOR_CHECK(tstate, &%s, %s, %d);"
            % (res_name, exception_state_name, iterator_name, statement.getCount())
        )

        getErrorExitBoolCode(
            condition="%s == false" % res_name,
            fetched_exception=True,
            emit=emit,
            context=context,
        )


def generateUnpackCheckFromIteratedCode(statement, emit, context):
    iteration_length_name = context.allocateTempName("iteration_length", unique=True)

    generateExpressionCode(
        to_name=iteration_length_name,
        expression=statement.subnode_iterated_length,
        emit=emit,
        context=context,
    )

    to_name = context.getBoolResName()

    getRichComparisonCode(
        to_name=to_name,
        comparator="Gt",
        left=statement.subnode_iterated_length,
        # Creating a temporary node on the fly, knowing it's not used for many
        # things. TODO: Once we have value shapes, we ought to use those.
        right=makeConstantRefNode(
            constant=statement.count,
            source_ref=statement.source_ref,
            user_provided=True,
        ),
        # We know that cannot fail.
        needs_check=False,
        source_ref=statement.source_ref,
        emit=emit,
        context=context,
    )

    # TODO: Why is this necessary, to_name doesn't allow storage.
    context.removeCleanupTempName(to_name)

    # TODO: This exception ought to have a creator function.
    emit(
        """
if (%(to_name)s) {
    PyErr_Format(PyExc_ValueError, "too many values to unpack");
}
"""
        % {"to_name": to_name}
    )

    getErrorExitBoolCode(condition=str(to_name), emit=emit, context=context)


def generateBuiltinNext2Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_NEXT2",
        tstate=True,
        arg_desc=(
            ("next_arg", expression.subnode_iterator),
            ("next_default", expression.subnode_default),
        ),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
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
        arg_desc=(("iter_arg", expression.subnode_value),),
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
        arg_desc=(("iter_arg", expression.subnode_value),),
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
        arg_desc=(
            ("iter_callable", expression.subnode_callable_arg),
            ("iter_sentinel", expression.subnode_sentinel),
        ),
        may_raise=expression.mayRaiseException(BaseException),
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
        arg_desc=(("len_arg", expression.subnode_value),),
        may_raise=expression.mayRaiseException(BaseException),
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
        arg_desc=(("any_arg", expression.subnode_value),),
        may_raise=expression.mayRaiseException(BaseException),
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
        arg_desc=(("all_arg", expression.subnode_value),),
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
