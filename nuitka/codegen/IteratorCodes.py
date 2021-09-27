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
""" Iteration related codes.

Next variants and unpacking with related checks.
"""

from nuitka.PythonVersions import python_version

from .CodeHelpers import (
    decideConversionCheckNeeded,
    generateChildExpressionsCode,
    generateExpressionCode,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import (
    getErrorExitCode,
    getErrorExitReleaseCode,
    getFrameVariableTypeDescriptionCode,
    getReleaseCode,
)
from .Indentation import indented
from .LineNumberCodes import getErrorLineNumberUpdateCode
from .PythonAPICodes import generateCAPIObjectCode
from .templates.CodeTemplatesIterators import (
    template_iterator_check,
    template_loop_break_next,
)


def generateBuiltinNext1Code(to_name, expression, emit, context):
    (value_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "next_value", expression, emit, context
    ) as result_name:

        emit("%s = %s;" % (result_name, "ITERATOR_NEXT(%s)" % value_name))

        getErrorExitCode(
            check_name=result_name,
            release_name=value_name,
            quick_exception="StopIteration",
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(result_name)


def getBuiltinLoopBreakNextCode(to_name, value, emit, context):
    emit("%s = %s;" % (to_name, "ITERATOR_NEXT(%s)" % value))

    getReleaseCode(release_name=value, emit=emit, context=context)

    break_target = context.getLoopBreakTarget()
    if type(break_target) is tuple:
        break_indicator_code = "%s = true;" % break_target[1]
        break_target = break_target[0]
    else:
        break_indicator_code = ""

    (
        exception_type,
        exception_value,
        exception_tb,
        _exception_lineno,
    ) = context.variable_storage.getExceptionVariableDescriptions()

    emit(
        template_loop_break_next
        % {
            "to_name": to_name,
            "break_indicator_code": break_indicator_code,
            "break_target": break_target,
            "release_temps": indented(getErrorExitReleaseCode(context), 2),
            "var_description_code": indented(
                getFrameVariableTypeDescriptionCode(context), 2
            ),
            "line_number_code": indented(getErrorLineNumberUpdateCode(context), 2),
            "exception_target": context.getExceptionEscape(),
            "exception_type": exception_type,
            "exception_value": exception_value,
            "exception_tb": exception_tb,
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
            emit(
                "%s = UNPACK_NEXT(%s, %s);"
                % (result_name, value_name, expression.getCount() - 1)
            )
        else:
            starred = expression.getStarred()
            expected = expression.getExpected()

            emit(
                "%s = UNPACK_NEXT%s(%s, %s, %s);"
                % (
                    result_name,
                    "_STARRED" if starred else "",
                    value_name,
                    expression.getCount() - 1,
                    expected,
                )
            )

        getErrorExitCode(
            check_name=result_name,
            release_name=value_name,
            quick_exception="StopIteration",
            needs_check=needs_check,
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

    # These variable cannot collide, as it's used very locally.
    attempt_name = context.allocateTempName("iterator_attempt", unique=True)

    release_code = getErrorExitReleaseCode(context)
    var_description_code = getFrameVariableTypeDescriptionCode(context)

    with context.withCurrentSourceCodeReference(statement.getSourceReference()):

        (
            exception_type,
            exception_value,
            exception_tb,
            _exception_lineno,
        ) = context.variable_storage.getExceptionVariableDescriptions()

        emit(
            template_iterator_check
            % {
                "iterator_name": iterator_name,
                "attempt_name": attempt_name,
                "exception_exit": context.getExceptionEscape(),
                "release_temps_1": indented(release_code, 3),
                "line_number_code_1": indented(
                    getErrorLineNumberUpdateCode(context), 3
                ),
                "var_description_code_1": indented(var_description_code, 3),
                "release_temps_2": indented(release_code),
                "var_description_code_2": indented(var_description_code),
                "line_number_code_2": indented(getErrorLineNumberUpdateCode(context)),
                "exception_type": exception_type,
                "exception_value": exception_value,
                "exception_tb": exception_tb,
                "too_many_values_error": context.getConstantCode(
                    "too many values to unpack"
                    if python_version < 0x300
                    else "too many values to unpack (expected %d)"
                    % statement.getCount()
                ),
            }
        )

        getReleaseCode(release_name=iterator_name, emit=emit, context=context)


def generateBuiltinNext2Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_NEXT2",
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
        arg_desc=(("all_arg", expression.subnode_value),),
        may_raise=expression.mayRaiseException(BaseException),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )
