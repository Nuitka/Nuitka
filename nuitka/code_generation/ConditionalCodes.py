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
""" Conditional statements related codes.

Branches, conditions, truth checks.
"""

from .CodeHelpers import decideConversionCheckNeeded, generateExpressionCode
from .Emission import SourceCodeCollector
from .ErrorCodes import (
    getErrorExitBoolCode,
    getReleaseCode,
    getTakeReferenceCode,
)
from .LabelCodes import getBranchingCode, getGotoCode, getLabelCode


def generateConditionCode(condition, emit, context):
    if condition.mayRaiseExceptionBool(BaseException):
        compare_name = context.allocateTempName("condition_result", "nuitka_bool")
    else:
        compare_name = context.allocateTempName("condition_result", "bool")

    generateExpressionCode(
        to_name=compare_name, expression=condition, emit=emit, context=context
    )

    getBranchingCode(
        condition=compare_name.getCType().getTruthCheckCode(compare_name),
        emit=emit,
        context=context,
    )

    getReleaseCode(compare_name, emit, context)


def generateConditionalAndOrCode(to_name, expression, emit, context):
    # This is a complex beast, handling both "or" and "and" expressions,
    # and it needs to micro manage details.
    # pylint: disable=too-many-locals
    if expression.isExpressionConditionalOr():
        prefix = "or_"
    else:
        prefix = "and_"

    true_target = context.allocateLabel(prefix + "left")
    false_target = context.allocateLabel(prefix + "right")
    end_target = context.allocateLabel(prefix + "end")

    old_true_target = context.getTrueBranchTarget()
    old_false_target = context.getFalseBranchTarget()

    truth_name = context.allocateTempName(prefix + "left_truth", "int")

    left_name = context.allocateTempName(prefix + "left_value", to_name.c_type)
    right_name = context.allocateTempName(prefix + "right_value", to_name.c_type)

    left_value = expression.subnode_left

    generateExpressionCode(
        to_name=left_name, expression=left_value, emit=emit, context=context
    )

    # We need to treat this mostly manually here. We remember to release
    # this, and we better do this manually later.
    needs_ref1 = context.needsCleanup(left_name)

    if expression.isExpressionConditionalOr():
        context.setTrueBranchTarget(true_target)
        context.setFalseBranchTarget(false_target)
    else:
        context.setTrueBranchTarget(false_target)
        context.setFalseBranchTarget(true_target)

    left_name.getCType().emitTruthCheckCode(
        to_name=truth_name,
        value_name=left_name,
        emit=emit,
    )

    needs_check = left_value.mayRaiseExceptionBool(BaseException)

    if needs_check:
        getErrorExitBoolCode(
            condition="%s == -1" % truth_name,
            needs_check=True,
            emit=emit,
            context=context,
        )

    getBranchingCode(condition="%s == 1" % truth_name, emit=emit, context=context)

    getLabelCode(false_target, emit)

    # So it's not the left value, then lets release that one right away, it
    # is not needed, but we remember if it should be added above.
    getReleaseCode(release_name=left_name, emit=emit, context=context)

    right_value = expression.subnode_right

    # Evaluate the "right" value then.
    generateExpressionCode(
        to_name=right_name, expression=right_value, emit=emit, context=context
    )

    # Again, remember the reference count to manage it manually.
    needs_ref2 = context.needsCleanup(right_name)

    if needs_ref2:
        context.removeCleanupTempName(right_name)

    if not needs_ref2 and needs_ref1:
        getTakeReferenceCode(right_name, emit)

    to_name.getCType().emitAssignConversionCode(
        to_name=to_name,
        value_name=right_name,
        needs_check=decideConversionCheckNeeded(to_name, right_value),
        emit=emit,
        context=context,
    )

    getGotoCode(end_target, emit)

    getLabelCode(true_target, emit)

    if not needs_ref1 and needs_ref2:
        getTakeReferenceCode(left_name, emit)

    to_name.getCType().emitAssignConversionCode(
        to_name=to_name,
        value_name=left_name,
        needs_check=decideConversionCheckNeeded(to_name, left_value),
        emit=emit,
        context=context,
    )

    getLabelCode(end_target, emit)

    if needs_ref1 or needs_ref2:
        context.addCleanupTempName(to_name)

    context.setTrueBranchTarget(old_true_target)
    context.setFalseBranchTarget(old_false_target)


def generateConditionalCode(to_name, expression, emit, context):
    true_target = context.allocateLabel("condexpr_true")
    false_target = context.allocateLabel("condexpr_false")
    end_target = context.allocateLabel("condexpr_end")

    old_true_target = context.getTrueBranchTarget()
    old_false_target = context.getFalseBranchTarget()

    context.setTrueBranchTarget(true_target)
    context.setFalseBranchTarget(false_target)

    generateConditionCode(
        condition=expression.subnode_condition, emit=emit, context=context
    )

    getLabelCode(true_target, emit)
    generateExpressionCode(
        to_name=to_name,
        expression=expression.subnode_expression_yes,
        emit=emit,
        context=context,
    )
    needs_ref1 = context.needsCleanup(to_name)

    # Must not clean this up in other expression.
    if needs_ref1:
        context.removeCleanupTempName(to_name)

    real_emit = emit
    emit = SourceCodeCollector()

    generateExpressionCode(
        to_name=to_name,
        expression=expression.subnode_expression_no,
        emit=emit,
        context=context,
    )

    needs_ref2 = context.needsCleanup(to_name)

    # TODO: Need to buffer generated code, so we can emit extra reference if
    # not same.
    if needs_ref1 and not needs_ref2:
        getGotoCode(end_target, real_emit)
        getLabelCode(false_target, real_emit)

        for line in emit.codes:
            real_emit(line)
        emit = real_emit

        getTakeReferenceCode(to_name, emit)
        context.addCleanupTempName(to_name)
    elif not needs_ref1 and needs_ref2:
        getTakeReferenceCode(to_name, real_emit)

        getGotoCode(end_target, real_emit)
        getLabelCode(false_target, real_emit)

        for line in emit.codes:
            real_emit(line)
        emit = real_emit
    else:
        getGotoCode(end_target, real_emit)
        getLabelCode(false_target, real_emit)

        for line in emit.codes:
            real_emit(line)
        emit = real_emit

    getLabelCode(end_target, emit)

    context.setTrueBranchTarget(old_true_target)
    context.setFalseBranchTarget(old_false_target)
