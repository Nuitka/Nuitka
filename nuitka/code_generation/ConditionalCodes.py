#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Conditional statements related codes.

Branches, conditions, truth checks.
"""

from .CodeHelpers import (
    decideConversionCheckNeeded,
    generateExpressionCode,
    promoteBorrowedValuesForExpressionWrites,
)
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
    # pylint: disable=too-many-locals,too-many-statements
    promoteBorrowedValuesForExpressionWrites(
        expression=expression, emit=emit, context=context
    )

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

    # The borrowed association is not moved to the result yet, because the
    # right value may overwrite the variable the left value came from.
    if not needs_ref1:
        left_borrowed_values = context.getBorrowedValues(left_name)
    else:
        left_borrowed_values = ()

    getReleaseCode(release_name=left_name, emit=emit, context=context)

    right_value = expression.subnode_right

    generateExpressionCode(
        to_name=right_name, expression=right_value, emit=emit, context=context
    )

    needs_ref2 = context.needsCleanup(right_name)

    if needs_ref2:
        context.removeCleanupTempName(right_name)

    if not needs_ref2 and needs_ref1:
        getTakeReferenceCode(right_name, emit)
        context.unregisterBorrowedValue(right_name)

    to_name.getCType().emitAssignConversionCode(
        to_name=to_name,
        value_name=right_name,
        needs_check=decideConversionCheckNeeded(to_name, right_value),
        emit=emit,
        context=context,
    )

    if not needs_ref2 and not needs_ref1:
        context.transferBorrowedValue(right_name, to_name)
        context.addBorrowedValues(to_name, left_borrowed_values)

    getGotoCode(end_target, emit)

    getLabelCode(true_target, emit)

    if not needs_ref1 and needs_ref2:
        getTakeReferenceCode(left_name, emit)
        context.unregisterBorrowedValue(to_name)

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
    promoteBorrowedValuesForExpressionWrites(
        expression=expression, emit=emit, context=context
    )

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

    if needs_ref1:
        context.removeCleanupTempName(to_name)
        yes_borrowed_values = ()
    else:
        yes_borrowed_values = context.getBorrowedValues(to_name)

    context.unregisterBorrowedValue(to_name)

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

        real_emit.extend(emit)
        emit = real_emit

        getTakeReferenceCode(to_name, emit)
        context.addCleanupTempName(to_name)
        context.unregisterBorrowedValue(to_name)
    elif not needs_ref1 and needs_ref2:
        getTakeReferenceCode(to_name, real_emit)
        context.unregisterBorrowedValue(to_name)

        getGotoCode(end_target, real_emit)
        getLabelCode(false_target, real_emit)

        real_emit.extend(emit)
        emit = real_emit
    else:
        if not needs_ref1:
            # The result is borrowed, and both branches may have contributed
            # a different variable for it.
            context.addBorrowedValues(to_name, yes_borrowed_values)
        else:
            context.unregisterBorrowedValue(to_name)

        getGotoCode(end_target, real_emit)
        getLabelCode(false_target, real_emit)

        real_emit.extend(emit)
        emit = real_emit

    getLabelCode(end_target, emit)

    context.setTrueBranchTarget(old_true_target)
    context.setFalseBranchTarget(old_false_target)


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
