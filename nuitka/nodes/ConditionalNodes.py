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
""" Conditional nodes.

These is the conditional expression '(a if b else c)' and the conditional
statement, 'if a: ... else: ...' and there is no 'elif', because that is
expressed via nesting of conditional statements.
"""

from nuitka.optimizations.TraceCollections import TraceCollectionBranch

from .BuiltinTypeNodes import ExpressionBuiltinBool
from .Checkers import checkStatementsSequenceOrNone
from .ChildrenHavingMixins import (
    ChildrenHavingConditionExpressionYesExpressionNoMixin,
    ChildrenHavingLeftRightMixin,
)
from .ExpressionBases import ExpressionBase
from .NodeMakingHelpers import (
    makeConstantReplacementNode,
    makeStatementExpressionOnlyReplacementNode,
    wrapExpressionWithNodeSideEffects,
    wrapExpressionWithSideEffects,
    wrapStatementWithSideEffects,
)
from .OperatorNodesUnary import ExpressionOperationNot
from .shapes.BuiltinTypeShapes import tshape_bool, tshape_unknown
from .StatementBasesGenerated import StatementConditionalBase
from .StatementNodes import StatementsSequence


class ConditionalValueComputeMixin(object):
    __slots__ = ()

    def _computeConditionTruthValue(self, trace_collection):
        condition = self.subnode_condition

        truth_value, replacement, message = condition.computeExpressionBool(
            trace_collection
        )
        if replacement is not None:
            assert replacement.isExpression()

            self.replaceChild(condition, replacement)

            trace_collection.signalChange(
                tags="new_constant", source_ref=self.source_ref, message=message
            )

            return truth_value, replacement
        else:
            # Query the truth value after the expression is evaluated, once it is
            # evaluated in onExpression, it is known.
            return condition.getTruthValue(), condition


class ExpressionConditional(
    ConditionalValueComputeMixin,
    ChildrenHavingConditionExpressionYesExpressionNoMixin,
    ExpressionBase,
):
    kind = "EXPRESSION_CONDITIONAL"

    named_children = ("condition", "expression_yes", "expression_no")

    def __init__(self, condition, expression_yes, expression_no, source_ref):
        ChildrenHavingConditionExpressionYesExpressionNoMixin.__init__(
            self,
            condition=condition,
            expression_yes=expression_yes,
            expression_no=expression_no,
        )

        ExpressionBase.__init__(self, source_ref)

    def getTypeShape(self):
        yes_shape = self.subnode_expression_yes.getTypeShape()

        if yes_shape is tshape_unknown:
            return tshape_unknown
        else:
            no_shape = self.subnode_expression_no.getTypeShape()

            if no_shape is yes_shape:
                return no_shape
            else:
                return tshape_unknown

    def getBranches(self):
        return (self.subnode_expression_yes, self.subnode_expression_no)

    def computeExpressionRaw(self, trace_collection):
        # This is rather complex stuff, pylint: disable=too-many-branches

        # Query the truth value after the expression is evaluated, once it is
        # evaluated in onExpression, it is known.
        condition = trace_collection.onExpression(self.subnode_condition)

        # No need to look any further, if the condition raises, the branches do
        # not matter at all.
        if condition.willRaiseAnyException():
            return (
                condition,
                "new_raise",
                """\
Conditional expression already raises implicitly in condition, removing \
branches.""",
            )

        # Tell it we are evaluation it for boolean value only, it may demote
        # itself possibly.
        truth_value, condition = self._computeConditionTruthValue(trace_collection)

        # TODO: We now know that condition evaluates to true for the yes branch
        # and to not true for no branch, the branch should know that.
        yes_branch = self.subnode_expression_yes

        # Continue to execute for yes branch unless we know it's not going to be
        # relevant.
        if truth_value is not False:
            branch_yes_collection = TraceCollectionBranch(
                parent=trace_collection, name="conditional expression yes branch"
            )

            yes_branch = branch_yes_collection.onExpression(yes_branch)

            # If it's aborting, it doesn't contribute to merging.
            if truth_value is not True and yes_branch.willRaiseAnyException():
                branch_yes_collection = None
        else:
            branch_yes_collection = None

        no_branch = self.subnode_expression_no

        # Continue to execute for yes branch.
        if truth_value is not True:
            branch_no_collection = TraceCollectionBranch(
                parent=trace_collection, name="conditional expression no branch"
            )

            no_branch = branch_no_collection.onExpression(no_branch)

            # If it's aborting, it doesn't contribute to merging.
            if truth_value is not False and no_branch.willRaiseAnyException():
                branch_no_collection = None
        else:
            branch_no_collection = None

        if truth_value is True:
            trace_collection.replaceBranch(branch_yes_collection)
        elif truth_value is False:
            trace_collection.replaceBranch(branch_no_collection)
        else:
            # Merge into parent execution.
            trace_collection.mergeBranches(branch_yes_collection, branch_no_collection)

        if truth_value is True:
            return (
                wrapExpressionWithNodeSideEffects(
                    new_node=self.subnode_expression_yes, old_node=condition
                ),
                "new_expression",
                "Conditional expression predicted to 'yes' case.",
            )
        elif truth_value is False:
            return (
                wrapExpressionWithNodeSideEffects(
                    new_node=self.subnode_expression_no, old_node=condition
                ),
                "new_expression",
                "Conditional expression predicted to 'no' case.",
            )
        else:
            return self, None, None

    def computeExpressionDrop(self, statement, trace_collection):
        result = makeStatementConditional(
            condition=self.subnode_condition,
            yes_branch=makeStatementExpressionOnlyReplacementNode(
                expression=self.subnode_expression_yes, node=self.subnode_expression_yes
            ),
            no_branch=makeStatementExpressionOnlyReplacementNode(
                expression=self.subnode_expression_no, node=self.subnode_expression_no
            ),
            source_ref=self.source_ref,
        )

        del self.parent

        return (
            result,
            "new_statements",
            """\
Convert conditional expression with unused result into conditional statement.""",
        )

    def mayHaveSideEffectsBool(self):
        # The bool will me made on either side.
        if self.subnode_expression_yes.mayHaveSideEffectsBool():
            return True

        if self.subnode_expression_no.mayHaveSideEffectsBool():
            return True

        return False

    def mayRaiseException(self, exception_type):
        condition = self.subnode_condition

        if condition.mayRaiseException(exception_type):
            return True

        if condition.mayRaiseExceptionBool(exception_type):
            return True

        yes_branch = self.subnode_expression_yes

        # Handle branches that became empty behind our back
        if yes_branch is not None and yes_branch.mayRaiseException(exception_type):
            return True

        no_branch = self.subnode_expression_no

        # Handle branches that became empty behind our back
        if no_branch is not None and no_branch.mayRaiseException(exception_type):
            return True

        return False

    def mayRaiseExceptionBool(self, exception_type):
        if self.subnode_condition.mayRaiseExceptionBool(exception_type):
            return True

        if self.subnode_expression_yes.mayRaiseExceptionBool(exception_type):
            return True

        if self.subnode_expression_no.mayRaiseExceptionBool(exception_type):
            return True

        return False

    def getIntegerValue(self):
        result_yes = self.subnode_expression_yes.getIntegerValue()
        result_no = self.subnode_expression_no.getIntegerValue()

        if result_yes == result_no:
            return result_yes
        else:
            return None

    def getExpressionDictInConstant(self, value):
        result_yes = self.subnode_expression_yes.getExpressionDictInConstant(value)
        result_no = self.subnode_expression_no.getExpressionDictInConstant(value)

        if result_yes == result_no:
            return result_yes
        else:
            return None


class ExpressionConditionalBoolBase(ChildrenHavingLeftRightMixin, ExpressionBase):
    named_children = ("left", "right")

    def __init__(self, left, right, source_ref):
        ChildrenHavingLeftRightMixin.__init__(self, left=left, right=right)

        ExpressionBase.__init__(self, source_ref)

    def computeExpressionRaw(self, trace_collection):
        # Query the truth value after the expression is evaluated, once it is
        # evaluated in onExpression, it is known.
        left = trace_collection.onExpression(self.subnode_left)

        # No need to look any further, if the condition raises, the branches do
        # not matter at all.
        if left.willRaiseAnyException():
            return (
                left,
                "new_raise",
                """\
Conditional %s statements already raises implicitly in condition, removing \
branches."""
                % self.conditional_kind,
            )

        if not left.mayRaiseException(BaseException) and left.mayRaiseExceptionBool(
            BaseException
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

        # Decide this based on truth value of condition.
        truth_value = left.getTruthValue()

        truth_value_use_left = self.conditional_kind == "or"
        truth_value_use_right = not truth_value_use_left

        right = self.subnode_right

        # Continue to execute for yes branch unless we know it's not going to be
        # relevant.
        if truth_value is not truth_value_use_left:
            # TODO: We now know that left evaluates and we should tell the
            # branch that.
            branch_yes_collection = TraceCollectionBranch(
                parent=trace_collection,
                name="boolean %s right branch" % self.conditional_kind,
            )

            right = branch_yes_collection.onExpression(right)

            # If it's aborting, it doesn't contribute to merging.
            if right.willRaiseAnyException():
                branch_yes_collection = None
        else:
            branch_yes_collection = None

        if branch_yes_collection:
            # Merge into parent execution.
            trace_collection.mergeBranches(branch_yes_collection, None)

        if truth_value is truth_value_use_left:
            return (
                left,
                "new_expression",
                "Conditional '%s' expression predicted to left value."
                % self.conditional_kind,
            )
        elif truth_value is truth_value_use_right:
            return (
                wrapExpressionWithNodeSideEffects(new_node=right, old_node=left),
                "new_expression",
                "Conditional '%s' expression predicted right value."
                % self.conditional_kind,
            )
        else:
            return self, None, None

    def mayRaiseException(self, exception_type):
        left = self.subnode_left

        if left.mayRaiseException(exception_type):
            return True

        if left.mayRaiseExceptionBool(exception_type):
            return True

        right = self.subnode_right

        if right.mayRaiseException(exception_type):
            return True

        return False

    def computeExpressionBool(self, trace_collection):
        truth_value = self.subnode_right.getTruthValue()

        if not self.mayRaiseException(BaseException) and self.mayRaiseExceptionBool(
            BaseException
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

        if truth_value is None:
            # No action
            pass
        elif truth_value is True:
            if self.isExpressionConditionalOr():
                result = wrapExpressionWithSideEffects(
                    new_node=makeConstantReplacementNode(
                        constant=True, node=self.subnode_right, user_provided=False
                    ),
                    old_node=self,
                    side_effects=(
                        ExpressionBuiltinBool(
                            value=self.subnode_left, source_ref=self.source_ref
                        ),
                    ),
                )

                return True, result, "Predicted right hand side of 'or' to be true."
            else:
                # TODO: There are no side effects after something else, which
                # would be needed, but for constant values, this works well.
                if not self.subnode_right.mayHaveSideEffects():
                    return (
                        self.subnode_left.getTruthValue(),
                        self.subnode_left,
                        "Predicted right hand side of 'and' to be true.",
                    )
        elif truth_value is False:
            if self.isExpressionConditionalAnd():
                result = wrapExpressionWithSideEffects(
                    new_node=makeConstantReplacementNode(
                        constant=False, node=self.subnode_right, user_provided=False
                    ),
                    old_node=self,
                    side_effects=(
                        ExpressionBuiltinBool(
                            value=self.subnode_left, source_ref=self.source_ref
                        ),
                    ),
                )

                return False, result, "Predicted right hand side of 'and' to be false."
            else:
                # TODO: There are no side effects after something else, which
                # would be needed, but for constant values, this works well.
                if not self.subnode_right.mayHaveSideEffects():
                    return (
                        self.subnode_left.getTruthValue(),
                        self.subnode_left,
                        "Predicted right hand side of 'or' to be false.",
                    )
                else:
                    truth_value = self.subnode_left.getTruthValue()

        return truth_value, None, None

    def mayRaiseExceptionBool(self, exception_type):
        # The and/or bool will be working on either side.
        if self.subnode_left.mayRaiseExceptionBool(exception_type):
            return True

        if self.subnode_right.mayRaiseExceptionBool(exception_type):
            return True

        return False

    def mayHaveSideEffectsBool(self):
        if self.subnode_left.mayHaveSideEffectsBool():
            return True

        if self.subnode_right.mayHaveSideEffectsBool():
            return True

        return False


class ExpressionConditionalOr(ExpressionConditionalBoolBase):
    kind = "EXPRESSION_CONDITIONAL_OR"

    conditional_kind = "or"

    def __init__(self, left, right, source_ref):
        ExpressionConditionalBoolBase.__init__(
            self, left=left, right=right, source_ref=source_ref
        )

    def computeExpressionDrop(self, statement, trace_collection):
        result = makeStatementConditional(
            condition=self.subnode_left,
            yes_branch=None,
            no_branch=makeStatementExpressionOnlyReplacementNode(
                expression=self.subnode_right, node=self.subnode_right
            ),
            source_ref=self.source_ref,
        )

        del self.parent

        return (
            result,
            "new_statements",
            """\
Convert conditional 'or' expression with unused result into conditional statement.""",
        )


class ExpressionConditionalAnd(ExpressionConditionalBoolBase):
    kind = "EXPRESSION_CONDITIONAL_AND"

    conditional_kind = "and"

    def __init__(self, left, right, source_ref):
        ExpressionConditionalBoolBase.__init__(
            self, left=left, right=right, source_ref=source_ref
        )

    def computeExpressionDrop(self, statement, trace_collection):
        result = makeStatementConditional(
            condition=self.subnode_left,
            no_branch=None,
            yes_branch=makeStatementExpressionOnlyReplacementNode(
                expression=self.subnode_right, node=self.subnode_right
            ),
            source_ref=self.source_ref,
        )

        del self.parent

        return (
            result,
            "new_statements",
            """\
Convert conditional 'and' expression with unused result into conditional statement.""",
        )


class StatementConditional(ConditionalValueComputeMixin, StatementConditionalBase):
    kind = "STATEMENT_CONDITIONAL"

    named_children = (
        "condition",
        "yes_branch|statements_or_none+setter",
        "no_branch|statements_or_none+setter",
    )

    checkers = {
        "yes_branch": checkStatementsSequenceOrNone,
        "no_branch": checkStatementsSequenceOrNone,
    }

    def isStatementAborting(self):
        yes_branch = self.subnode_yes_branch

        if yes_branch is not None:
            if yes_branch.isStatementAborting():
                no_branch = self.subnode_no_branch

                if no_branch is not None:
                    return no_branch.isStatementAborting()
                else:
                    return False
            else:
                return False
        else:
            return False

    def mayRaiseException(self, exception_type):
        condition = self.subnode_condition

        if condition.mayRaiseException(exception_type):
            return True

        if condition.mayRaiseExceptionBool(exception_type):
            return True

        yes_branch = self.subnode_yes_branch

        # Handle branches that became empty behind our back
        if yes_branch is not None and yes_branch.mayRaiseException(exception_type):
            return True

        no_branch = self.subnode_no_branch

        # Handle branches that became empty behind our back
        if no_branch is not None and no_branch.mayRaiseException(exception_type):
            return True

        return False

    def needsFrame(self):
        condition = self.subnode_condition

        if condition.mayRaiseException(BaseException):
            return True

        if condition.mayRaiseExceptionBool(BaseException):
            return True

        yes_branch = self.subnode_yes_branch

        # Handle branches that became empty behind our back
        if yes_branch is not None and yes_branch.needsFrame():
            return True

        no_branch = self.subnode_no_branch

        # Handle branches that became empty behind our back
        if no_branch is not None and no_branch.needsFrame():
            return True

        return False

    def computeStatement(self, trace_collection):
        # This is rather complex stuff, pylint: disable=too-many-branches,too-many-statements

        condition = trace_collection.onExpression(self.subnode_condition)

        # No need to look any further, if the condition raises, the branches do
        # not matter at all.
        if condition.willRaiseAnyException():
            result = makeStatementExpressionOnlyReplacementNode(
                expression=condition, node=self
            )

            return (
                result,
                "new_raise",
                """\
Conditional statements already raises implicitly in condition, removing \
branches.""",
            )

        # Tell it we are evaluation it for boolean value only, it may demote
        # itself possibly.
        truth_value, condition = self._computeConditionTruthValue(trace_collection)

        # TODO: We now know that condition evaluates to true for the yes branch
        # and to not true for no branch, the branch collection should know that.
        yes_branch = self.subnode_yes_branch
        no_branch = self.subnode_no_branch

        # Handle branches that became empty behind our back.
        if yes_branch is not None:
            if not yes_branch.subnode_statements:
                yes_branch.finalize()
                yes_branch = None

                self.setChildYesBranch(None)

        if no_branch is not None:
            if not no_branch.subnode_statements:
                no_branch.finalize()
                no_branch = None

                self.setChildNoBranch(None)

        # Consider to not remove branches that we know won't be taken.
        if yes_branch is not None and truth_value is False:
            trace_collection.signalChange(
                tags="new_statements",
                source_ref=yes_branch.source_ref,
                message="Removed conditional branch that cannot be taken due to false condition value.",
            )

            yes_branch.finalize()
            yes_branch = None

            self.setChildYesBranch(None)

        if no_branch is not None and truth_value is True:
            trace_collection.signalChange(
                tags="new_statements",
                source_ref=no_branch.source_ref,
                message="Removed 'else' branch that cannot be taken due to true condition value.",
            )

            no_branch.finalize()
            no_branch = None

            self.setChildNoBranch(None)

        # Do we need to merge branches
        needs_merge = True

        # Continue to execute for yes branch unless we know it's not going to be
        # relevant.
        if yes_branch is not None:
            branch_yes_collection = TraceCollectionBranch(
                parent=trace_collection, name="conditional yes branch"
            )

            yes_branch = branch_yes_collection.computeBranch(branch=yes_branch)

            # If it's aborting, it doesn't contribute to merging.
            if yes_branch is None:
                branch_yes_collection = None
            elif yes_branch.isStatementAborting():
                branch_yes_collection = None
                needs_merge = False
        else:
            branch_yes_collection = None

        # Continue to execute for yes branch.
        if no_branch is not None:
            branch_no_collection = TraceCollectionBranch(
                parent=trace_collection, name="conditional no branch"
            )

            no_branch = branch_no_collection.computeBranch(branch=no_branch)

            # If it's aborting, it doesn't contribute to merging.
            if no_branch is None:
                branch_no_collection = None
            elif no_branch.isStatementAborting():
                branch_no_collection = None
                needs_merge = False
        else:
            branch_no_collection = None

        if truth_value is True:
            if branch_yes_collection is not None:
                trace_collection.replaceBranch(branch_yes_collection)
        elif truth_value is False:
            if branch_no_collection is not None:
                trace_collection.replaceBranch(branch_no_collection)
        else:
            if needs_merge:
                trace_collection.mergeBranches(
                    branch_yes_collection, branch_no_collection
                )
            else:
                if branch_yes_collection is not None:
                    trace_collection.replaceBranch(branch_yes_collection)
                elif branch_no_collection is not None:
                    trace_collection.replaceBranch(branch_no_collection)

        # Both branches may have become empty, which case, the statement needs
        # not remain.
        if yes_branch is None and no_branch is None:
            # Need to keep the boolean check.
            if truth_value is None:
                condition = ExpressionBuiltinBool(
                    value=condition, source_ref=condition.getSourceReference()
                )

            if condition.mayHaveSideEffects():
                # With both branches eliminated, the condition remains as a side
                # effect.
                result = makeStatementExpressionOnlyReplacementNode(
                    expression=condition, node=self
                )

                del self.parent

                return (
                    result,
                    "new_statements",
                    """\
Both branches have no effect, reduced to evaluate condition.""",
                )
            else:
                self.finalize()

                return (
                    None,
                    "new_statements",
                    """\
Removed conditional statement without effect.""",
                )

        # Note: Checking the condition late, so that the surviving branch got
        # processed already. Returning without doing that, will corrupt the SSA
        # results. TODO: Could pretend the other branch didn't exist to save
        # complexity the merging of processing.
        if truth_value is not None:
            if truth_value is True:
                choice = "true"

                new_statement = yes_branch
                if no_branch is not None:
                    no_branch.finalize()
            else:
                choice = "false"

                new_statement = no_branch
                if yes_branch is not None:
                    yes_branch.finalize()

            new_statement = wrapStatementWithSideEffects(
                new_node=new_statement,
                old_node=condition,
                allow_none=True,  # surviving branch may empty
            )

            del self.parent

            return (
                new_statement,
                "new_statements",
                """\
Condition for branch statement was predicted to be always %s."""
                % choice,
            )

        # If there is no "yes" branch, remove that. Maybe a bad idea though.
        if yes_branch is None:
            # Would be eliminated already, if there wasn't any "no" branch
            # either.
            assert no_branch is not None

            new_statement = makeStatementConditional(
                condition=ExpressionOperationNot(
                    operand=condition, source_ref=condition.getSourceReference()
                ),
                yes_branch=no_branch,
                no_branch=None,
                source_ref=self.source_ref,
            )

            del self.parent

            return (
                new_statement,
                "new_statements",
                """\
Empty 'yes' branch for conditional statement treated with inverted condition check.""",
            )

        return self, None, None

    def mayReturn(self):
        yes_branch = self.subnode_yes_branch

        if yes_branch is not None and yes_branch.mayReturn():
            return True

        no_branch = self.subnode_no_branch

        if no_branch is not None and no_branch.mayReturn():
            return True

        return False

    def mayBreak(self):
        yes_branch = self.subnode_yes_branch

        if yes_branch is not None and yes_branch.mayBreak():
            return True

        no_branch = self.subnode_no_branch

        if no_branch is not None and no_branch.mayBreak():
            return True

        return False

    def mayContinue(self):
        yes_branch = self.subnode_yes_branch

        if yes_branch is not None and yes_branch.mayContinue():
            return True

        no_branch = self.subnode_no_branch

        if no_branch is not None and no_branch.mayContinue():
            return True

        return False

    @staticmethod
    def getStatementNiceName():
        return "branch statement"


def makeNotExpression(expression):
    # These are invertible with bool type shape.
    if expression.isExpressionComparison() and expression.getTypeShape() is tshape_bool:
        return expression.makeInverseComparison()
    else:
        return ExpressionOperationNot(
            operand=expression, source_ref=expression.getSourceReference()
        )


def makeStatementConditional(condition, yes_branch, no_branch, source_ref):
    """Create conditional statement, with yes_branch not being empty.

    May have to invert condition to achieve that.
    """

    if yes_branch is None:
        condition = makeNotExpression(expression=condition)

        yes_branch, no_branch = no_branch, yes_branch

    if yes_branch is not None and not yes_branch.isStatementsSequence():
        yes_branch = StatementsSequence(
            statements=(yes_branch,), source_ref=yes_branch.source_ref
        )

    if no_branch is not None and not no_branch.isStatementsSequence():
        no_branch = StatementsSequence(
            statements=(no_branch,), source_ref=no_branch.source_ref
        )

    return StatementConditional(
        condition=condition,
        yes_branch=yes_branch,
        no_branch=no_branch,
        source_ref=source_ref,
    )
