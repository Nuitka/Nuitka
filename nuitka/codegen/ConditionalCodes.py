#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

from . import Generator


def generateConditionCode(condition, emit, context):
    # The complexity is needed to avoid unnecessary complex generated C++
    # pylint: disable=R0915,R0914

    # TODO: This will move to Helper module
    from .CodeGeneration import generateExpressionCode

    if condition.isExpressionConstantRef():
        # TODO: Must not happen, optimization catches this.
        assert False

        value = condition.getConstant()

        if value:
            Generator.getGotoCode(context.getTrueBranchTarget(), emit)
        else:
            Generator.getGotoCode(context.getFalseBranchTarget(), emit)
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
        Generator.getComparisonExpressionBoolCode(
            comparator = condition.getComparator(),
            left_name  = left_name,
            right_name = right_name,
            emit       = emit,
            context    = context
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

        Generator.getLabelCode(select_true,emit)
        generateConditionCode(
            condition = expression_yes,
            emit      = emit,
            context   = context,
        )
        Generator.getGotoCode(select_end, emit)
        Generator.getLabelCode(select_false,emit)
        generateConditionCode(
            condition = expression_no,
            emit      = emit,
            context   = context,
        )
        Generator.getLabelCode(select_end,emit)
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

        Generator.getAttributeCheckBoolCode(
            source_name = source_name,
            attr_name   = attr_name,
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

        Generator.getBuiltinIsinstanceBoolCode(
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

        Generator.getConditionCheckTrueCode(
            to_name    = truth_name,
            value_name = condition_name,
            emit       = emit
        )

        old_source_ref = context.setCurrentSourceCodeReference(condition.getSourceReference())

        Generator.getErrorExitBoolCode(
            condition = "%s == -1" % truth_name,
            emit      = emit,
            context   = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)

        Generator.getReleaseCode(
            release_name = condition_name,
            emit         = emit,
            context      = context
        )

        Generator.getBranchingCode(
            condition = "%s == 1" % truth_name,
            emit      = emit,
            context   = context
        )
