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
""" Comparison related codes.

Rich comparisons, "in", and "not in", also "is", and "is not", and the
"isinstance" check as used in conditions, as well as exception matching.
"""

from . import OperatorCodes
from .ErrorCodes import (
    getErrorExitBoolCode,
    getErrorExitCode,
    getReleaseCode,
    getReleaseCodes
)
from .Helpers import generateExpressionCode
from .LabelCodes import getBranchingCode


def generateComparisonExpressionCode(to_name, expression, emit, context):
    left_name = context.allocateTempName("compexpr_left")
    right_name = context.allocateTempName("compexpr_right")

    generateExpressionCode(
        to_name    = left_name,
        expression = expression.getLeft(),
        emit       = emit,
        context    = context
    )
    generateExpressionCode(
        to_name    = right_name,
        expression = expression.getRight(),
        emit       = emit,
        context    = context
    )

    comparator  = expression.getComparator()

    if comparator in OperatorCodes.normal_comparison_codes:
        needs_check = expression.getRight().mayRaiseExceptionIn(
            BaseException,
            expression.getLeft()
        )

        helper = OperatorCodes.normal_comparison_codes[ comparator ]
        assert helper.startswith("SEQUENCE_CONTAINS")

        emit(
            "%s = %s( %s, %s );" % (
                to_name,
                helper,
                left_name,
                right_name
            )
        )

        getReleaseCode(
            release_name = left_name,
            emit         = emit,
            context      = context
        )
        getReleaseCode(
            release_name = right_name,
            emit         = emit,
            context      = context
        )

        getErrorExitCode(
            check_name  = to_name,
            needs_check = needs_check,
            emit        = emit,
            context     = context
        )
    elif comparator in OperatorCodes.rich_comparison_codes:
        needs_check = expression.mayRaiseExceptionBool(BaseException)

        helper = "RICH_COMPARE_%s" % (
            OperatorCodes.rich_comparison_codes[ comparator ]
        )

        if not context.mayRecurse() and comparator == "Eq":
            helper += "_NORECURSE"

        emit(
            "%s = %s( %s, %s );" % (
                to_name,
                helper,
                left_name,
                right_name
            )
        )

        getReleaseCodes(
            release_names = (left_name, right_name),
            emit          = emit,
            context       = context
        )

        getErrorExitCode(
            check_name  = to_name,
            needs_check = needs_check,
            emit        = emit,
            context     = context
        )

        context.addCleanupTempName(to_name)
    elif comparator == "Is":
        emit(
            "%s = BOOL_FROM( %s == %s );" % (
                to_name,
                left_name,
                right_name
            )
        )

        getReleaseCodes(
            release_names = (left_name, right_name),
            emit          = emit,
            context       = context
        )
    elif comparator == "IsNot":
        emit(
            "%s = BOOL_FROM( %s != %s );" % (
                to_name,
                left_name,
                right_name
            )
        )

        getReleaseCodes(
            release_names = (left_name, right_name),
            emit          = emit,
            context       = context
        )
    elif comparator == "exception_match":
        needs_check = expression.mayRaiseExceptionBool(BaseException)

        operator_res_name = context.allocateTempName(
            "cmp_exception_match",
            "int"
        )

        emit(
             "%s = EXCEPTION_MATCH_BOOL( %s, %s );" % (
                operator_res_name,
                left_name,
                right_name
            )
        )

        getErrorExitBoolCode(
            condition   = "%s == -1" % operator_res_name,
            needs_check = needs_check,
            emit        = emit,
            context     = context
        )

        emit(
            "%s = BOOL_FROM( %s != 0 );" % (
                to_name,
                operator_res_name
            )
        )
    else:
        assert False, comparator


def getComparisonExpressionBoolCode(comparator, left_name, right_name, needs_check,
                                    emit, context):
    if comparator in OperatorCodes.normal_comparison_codes:
        operator_res_name = context.allocateTempName("cmp_" + comparator, "int")

        emit(
             "%s = PySequence_Contains( %s, %s );" % (
                operator_res_name,
                right_name, # sequence goes first.
                left_name
            )
        )

        getErrorExitBoolCode(
            condition   = "%s == -1" % operator_res_name,
            emit        = emit,
            needs_check = needs_check,
            context     = context
        )

        condition = "%s == %d" % (
            operator_res_name,
            1 if comparator == "In" else 0
        )
    elif comparator in OperatorCodes.rich_comparison_codes:
        operator_res_name = context.allocateTempName("cmp_" + comparator, "int")

        helper = OperatorCodes.rich_comparison_codes[comparator]
        if not context.mayRecurse() and comparator == "Eq":
            helper += "_NORECURSE"

        emit(
             "%s = RICH_COMPARE_BOOL_%s( %s, %s );" % (
                operator_res_name,
                helper,
                left_name,
                right_name
            )
        )

        getErrorExitBoolCode(
            condition   = "%s == -1" % operator_res_name,
            needs_check = needs_check,
            emit        = emit,
            context     = context
        )

        condition = "%s == 1" % (
            operator_res_name,
        )
    elif comparator == "Is":
        operator_res_name = context.allocateTempName("is", "bool")

        emit(
            "%s = ( %s == %s );" % (
                operator_res_name,
                left_name,
                right_name
            )
        )

        condition = operator_res_name
    elif comparator == "IsNot":
        operator_res_name = context.allocateTempName("isnot", "bool")

        emit(
            "%s = ( %s != %s );" % (
                operator_res_name,
                left_name,
                right_name
            )
        )

        condition = operator_res_name
    elif comparator == "exception_match":
        operator_res_name = context.allocateTempName("exc_match_" + comparator, "int")

        emit(
             "%s = EXCEPTION_MATCH_BOOL( %s, %s );" % (
                operator_res_name,
                left_name,
                right_name
            )
        )

        getErrorExitBoolCode(
            condition   = "%s == -1" % operator_res_name,
            needs_check = needs_check,
            emit        = emit,
            context     = context
        )

        condition = "%s == 1" % (
            operator_res_name
        )
    else:
        assert False, comparator

    getReleaseCode(
        release_name = left_name,
        emit         = emit,
        context      = context
    )
    getReleaseCode(
        release_name = right_name,
        emit         = emit,
        context      = context
    )

    getBranchingCode(condition, emit, context)


def getBuiltinIsinstanceBoolCode(inst_name, cls_name, emit, context):
    res_name = context.getIntResName()

    emit(
        "%s = Nuitka_IsInstance( %s, %s );" % (
            res_name,
            inst_name,
            cls_name
        )
    )

    getReleaseCodes(
        release_names = (inst_name, cls_name),
        emit          = emit,
        context       = context
    )

    getErrorExitBoolCode(
        condition = "%s == -1" % res_name,
        emit      = emit,
        context   = context
    )

    getBranchingCode(
        condition = "%s == 1" % res_name,
        emit      = emit,
        context   = context
    )
