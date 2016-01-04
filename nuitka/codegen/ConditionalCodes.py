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
""" Conditional statements related codes.

Branches, conditions, truth checks.
"""

from nuitka import Options

from .AttributeCodes import getAttributeCheckBoolCode
from .ComparisonCodes import (
    getBuiltinIsinstanceBoolCode,
    getComparisonExpressionBoolCode
)
from .Emission import SourceCodeCollector
from .ErrorCodes import getErrorExitBoolCode, getReleaseCode
from .Helpers import generateExpressionCode
from .LabelCodes import getBranchingCode, getGotoCode, getLabelCode


def generateConditionCode(condition, emit, context):
    # The complexity is needed to avoid unnecessary complex generated C++
    # pylint: disable=R0914,R0915

    if condition.isExpressionConstantRef():
        # TODO: Must not happen, optimization catches this.
        assert False

        value = condition.getConstant()

        if value:
            getGotoCode(context.getTrueBranchTarget(), emit)
        else:
            getGotoCode(context.getFalseBranchTarget(), emit)
    elif condition.isExpressionComparison():
        left_name = context.allocateTempName("compare_left")

        generateExpressionCode(
            to_name    = left_name,
            expression = condition.getLeft(),
            emit       = emit,
            context    = context
        )

        right_name = context.allocateTempName("compare_right")

        generateExpressionCode(
            to_name    = right_name,
            expression = condition.getRight(),
            emit       = emit,
            context    = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(condition.getSourceReference())
        getComparisonExpressionBoolCode(
            comparator  = condition.getComparator(),
            left_name   = left_name,
            right_name  = right_name,
            needs_check = condition.mayRaiseExceptionBool(BaseException),
            emit        = emit,
            context     = context
        )
        context.setCurrentSourceCodeReference(old_source_ref)
    elif condition.isExpressionOperationNOT():
        # Lets just switch the targets temporarily to get at "NOT" without
        # any effort really.
        true_target = context.getTrueBranchTarget()
        false_target = context.getFalseBranchTarget()

        context.setTrueBranchTarget(false_target)
        context.setFalseBranchTarget(true_target)

        generateConditionCode(
            condition = condition.getOperand(),
            emit      = emit,
            context   = context
        )

        context.setTrueBranchTarget(true_target)
        context.setFalseBranchTarget(false_target)
    elif condition.isExpressionConditional():
        expression_yes = condition.getExpressionYes()
        expression_no = condition.getExpressionNo()

        condition = condition.getCondition()

        old_true_target = context.getTrueBranchTarget()
        old_false_target = context.getFalseBranchTarget()

        select_true = context.allocateLabel("select_true")
        select_false = context.allocateLabel("select_false")

        # TODO: Could be avoided in some cases.
        select_end = context.allocateLabel("select_end")

        context.setTrueBranchTarget(select_true)
        context.setFalseBranchTarget(select_false)

        generateConditionCode(
            condition = condition,
            emit      = emit,
            context   = context,
        )

        context.setTrueBranchTarget(old_true_target)
        context.setFalseBranchTarget(old_false_target)

        getLabelCode(select_true,emit)
        generateConditionCode(
            condition = expression_yes,
            emit      = emit,
            context   = context,
        )
        getGotoCode(select_end, emit)
        getLabelCode(select_false,emit)
        generateConditionCode(
            condition = expression_no,
            emit      = emit,
            context   = context,
        )
        getLabelCode(select_end,emit)
    elif condition.isExpressionBuiltinHasattr():
        source_name = context.allocateTempName("hasattr_source")
        attr_name = context.allocateTempName("hasattr_attr")

        generateExpressionCode(
            to_name    = source_name,
            expression = condition.getLookupSource(),
            emit       = emit,
            context    = context
        )
        generateExpressionCode(
            to_name    = attr_name,
            expression = condition.getAttribute(),
            emit       = emit,
            context    = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(
            condition.getAttribute().getSourceReference()
               if Options.isFullCompat() else
            condition.getSourceReference()
        )

        getAttributeCheckBoolCode(
            source_name = source_name,
            attr_name   = attr_name,
            needs_check = condition.getLookupSource().mayRaiseExceptionAttributeCheckObject(
                exception_type = BaseException,
                attribute      = condition.getAttribute()
            ),
            emit        = emit,
            context     = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)
    elif condition.isExpressionBuiltinIsinstance():
        inst_name = context.allocateTempName("isinstance_inst")
        cls_name = context.allocateTempName("isinstance_cls")

        generateExpressionCode(
            to_name    = inst_name,
            expression = condition.getInstance(),
            emit       = emit,
            context    = context
        )
        generateExpressionCode(
            to_name    = cls_name,
            expression = condition.getCls(),
            emit       = emit,
            context    = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(condition.getSourceReference())

        getBuiltinIsinstanceBoolCode(
            inst_name = inst_name,
            cls_name  = cls_name,
            emit      = emit,
            context   = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)
    else:
        condition_name = context.allocateTempName("cond_value")
        truth_name = context.allocateTempName("cond_truth", "int")

        generateExpressionCode(
            to_name    = condition_name,
            expression = condition,
            emit       = emit,
            context    = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(condition.getSourceReference())

        getConditionCheckTrueCode(
            to_name     = truth_name,
            value_name  = condition_name,
            needs_check = condition.mayRaiseExceptionBool(BaseException),
            emit        = emit,
            context     = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)

        getReleaseCode(
            release_name = condition_name,
            emit         = emit,
            context      = context
        )

        getBranchingCode(
            condition = "%s == 1" % truth_name,
            emit      = emit,
            context   = context
        )


def getConditionCheckTrueCode(to_name, value_name, needs_check, emit, context):
    emit(
        "%s = CHECK_IF_TRUE( %s );" % (
            to_name,
            value_name
        )
    )

    getErrorExitBoolCode(
        condition   = "%s == -1" % to_name,
        needs_check = needs_check,
        emit        = emit,
        context     = context
    )


def generateConditionalAndOrCode(to_name, expression, emit, context):
    # This is a complex beast, handling both "or" and "and" expressions,
    # and it needs to micro manage details.
    # pylint: disable=R0914
    if expression.isExpressionConditionalOR():
        prefix = "or_"
    else:
        prefix = "and_"

    true_target = context.allocateLabel(prefix + "left")
    false_target = context.allocateLabel(prefix + "right")
    end_target = context.allocateLabel(prefix + "end")

    old_true_target = context.getTrueBranchTarget()
    old_false_target = context.getFalseBranchTarget()

    truth_name = context.allocateTempName(prefix + "left_truth", "int")

    left_name = context.allocateTempName(prefix + "left_value")
    right_name = context.allocateTempName(prefix + "right_value")

    left_value = expression.getLeft()

    generateExpressionCode(
        to_name    = left_name,
        expression = left_value,
        emit       = emit,
        context    = context
    )

    # We need to treat this mostly manually here. We remember to release
    # this, and we better do this manually later.
    needs_ref1 = context.needsCleanup(left_name)

    getConditionCheckTrueCode(
        to_name     = truth_name,
        value_name  = left_name,
        needs_check = left_value.mayRaiseExceptionBool(BaseException),
        emit        = emit,
        context     = context
    )

    if expression.isExpressionConditionalOR():
        context.setTrueBranchTarget(true_target)
        context.setFalseBranchTarget(false_target)
    else:
        context.setTrueBranchTarget(false_target)
        context.setFalseBranchTarget(true_target)

    getBranchingCode(
        condition = "%s == 1" % truth_name,
        emit      = emit,
        context   = context
    )

    getLabelCode(false_target,emit)

    # So it's not the left value, then lets release that one right away, it
    # is not needed, but we remember if it should be added above.
    getReleaseCode(
       release_name = left_name,
       emit         = emit,
       context      = context
    )

    # Evaluate the "right" value then.
    generateExpressionCode(
        to_name    = right_name,
        expression = expression.getRight(),
        emit       = emit,
        context    = context
    )

    # Again, remember the reference count to manage it manually.
    needs_ref2 = context.needsCleanup(right_name)

    if needs_ref2:
        context.removeCleanupTempName(right_name)

    if not needs_ref2 and needs_ref1:
        emit("Py_INCREF( %s );" % right_name)

    emit(
        "%s = %s;" % (
            to_name,
            right_name
        )
    )

    getGotoCode(end_target, emit)

    getLabelCode(true_target, emit)

    if not needs_ref1 and needs_ref2:
        emit("Py_INCREF( %s );" % left_name)

    emit(
        "%s = %s;" % (
            to_name,
            left_name
        )
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
        condition = expression.getCondition(),
        emit      = emit,
        context   = context
    )

    getLabelCode(true_target,emit)
    generateExpressionCode(
        to_name    = to_name,
        expression = expression.getExpressionYes(),
        emit       = emit,
        context    = context
    )
    needs_ref1 = context.needsCleanup(to_name)

    # Must not clean this up in other expression.
    if needs_ref1:
        context.removeCleanupTempName(to_name)

    real_emit = emit
    emit = SourceCodeCollector()

    generateExpressionCode(
        to_name    = to_name,
        expression = expression.getExpressionNo(),
        emit       = emit,
        context    = context
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

        emit("Py_INCREF( %s );" % to_name)
        context.addCleanupTempName(to_name)
    elif not needs_ref1 and needs_ref2:
        real_emit("Py_INCREF( %s );" % to_name)
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

    getLabelCode(end_target,emit)

    context.setTrueBranchTarget(old_true_target)
    context.setFalseBranchTarget(old_false_target)
