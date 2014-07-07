#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
"isinstance" check as used in conditons.
"""

from . import OperatorCodes
from .ErrorCodes import (
    getErrorExitBoolCode,
    getErrorExitCode,
    getReleaseCode,
    getReleaseCodes
)


def getComparisonExpressionCode(to_name, comparator, left_name, right_name,
                                emit, context):
    # There is an awful lot of cases, pylint: disable=R0912

    if comparator in OperatorCodes.normal_comparison_codes:
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

        getErrorExitCode(
            check_name  = to_name,
            emit        = emit,
            context     = context
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
    elif comparator in OperatorCodes.rich_comparison_codes:
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
            check_name = to_name,
            emit       = emit,
            context    = context
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
            condition = "%s == -1" % operator_res_name,
            emit      = emit,
            context   = context
        )

        emit(
            "%s = BOOL_FROM( %s != 0 );" % (
                to_name,
                operator_res_name
            )
        )
    else:
        assert False, comparator


def getComparisonExpressionBoolCode(comparator, left_name, right_name, emit,
                                    context):
    # There is an awful lot of cases, pylint: disable=R0912

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
            condition = "%s == -1" % operator_res_name,
            emit      = emit,
            context   = context
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
            condition = "%s == -1" % operator_res_name,
            emit      = emit,
            context   = context
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
            condition = "%s == -1" % operator_res_name,
            emit      = emit,
            context   = context
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


def getBranchingCode(condition, emit, context):
    true_target = context.getTrueBranchTarget()
    false_target = context.getFalseBranchTarget()

    if true_target is not None and false_target is None:
        emit(
            "if (%s) goto %s;" % (
                condition,
                true_target
            )
        )
    elif true_target is None and false_target is not None:
        emit(
            "if (!(%s)) goto %s;" % (
                condition,
                false_target
            )
        )
    else:
        assert true_target is not None and false_target is not None

        emit(
            """\
if (%s)
{
    goto %s;
}
else
{
    goto %s;
}""" % (
                condition,
                true_target,
                false_target
            )
        )


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

    getBranchingCode("%s == 1" % res_name, emit, context)
