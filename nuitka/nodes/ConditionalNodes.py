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
""" Conditional nodes.

These is the conditional expression '(a if b else c)' and the conditional
statement, 'if a: ... else: ...' and there is no 'elif', because that is
expressed via nesting of conditional statements.
"""

from nuitka.nodes.BuiltinTypeNodes import ExpressionBuiltinBool
from nuitka.optimizations.TraceCollections import ConstraintCollectionBranch

from .Checkers import checkStatementsSequenceOrNone
from .NodeBases import (
    ExpressionChildrenHavingBase,
    StatementChildrenHavingBase
)
from .NodeMakingHelpers import (
    makeStatementExpressionOnlyReplacementNode,
    wrapExpressionWithNodeSideEffects,
    wrapStatementWithSideEffects
)


class ExpressionConditional(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_CONDITIONAL"

    named_children = (
        "condition",
        "expression_yes",
        "expression_no"
    )

    def __init__(self, condition, expression_yes, expression_no, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "condition"      : condition,
                "expression_yes" : expression_yes,
                "expression_no"  : expression_no
            },
            source_ref = source_ref
        )

    def getBranches(self):
        return (
            self.getExpressionYes(),
            self.getExpressionNo()
        )

    getExpressionYes = ExpressionChildrenHavingBase.childGetter(
        "expression_yes"
    )
    getExpressionNo = ExpressionChildrenHavingBase.childGetter(
        "expression_no"
    )

    getCondition = ExpressionChildrenHavingBase.childGetter(
        "condition"
    )

    def computeExpressionRaw(self, constraint_collection):
        # Query the truth value after the expression is evaluated, once it is
        # evaluated in onExpression, it is known.
        constraint_collection.onExpression(
            expression = self.getCondition()
        )
        condition = self.getCondition()

        condition_may_raise = condition.mayRaiseException(BaseException)

        if condition_may_raise:
            constraint_collection.onExceptionRaiseExit(
                BaseException
            )

        # No need to look any further, if the condition raises, the branches do
        # not matter at all.
        if condition.willRaiseException(BaseException):
            return condition, "new_raise", """\
Conditional expression already raises implicitly in condition, removing \
branches."""

        if not condition_may_raise and condition.mayRaiseExceptionBool(BaseException):
            constraint_collection.onExceptionRaiseExit(
                BaseException
            )

        # Decide this based on truth value of condition.
        truth_value = condition.getTruthValue()

        # TODO: We now know that condition evaluates to true for the yes branch
        # and to not true for no branch, the branch should know that.
        yes_branch = self.getExpressionYes()

        # Continue to execute for yes branch unless we know it's not going to be
        # relevant.
        if truth_value is not False:
            branch_yes_collection = ConstraintCollectionBranch(
                parent = constraint_collection,
                name   = "conditional expression yes branch"
            )

            branch_yes_collection.computeBranch(
                branch = yes_branch
            )

            # May have just gone away, so fetch it again.
            yes_branch = self.getExpressionYes()

            # If it's aborting, it doesn't contribute to merging.
            if yes_branch.willRaiseException(BaseException):
                branch_yes_collection = None
        else:
            branch_yes_collection = None

        no_branch = self.getExpressionNo()

        # Continue to execute for yes branch.
        if truth_value is not True:
            branch_no_collection = ConstraintCollectionBranch(
                parent = constraint_collection,
                name   = "conditional expression no branch"
            )

            branch_no_collection.computeBranch(
                branch = no_branch
            )

            # May have just gone away, so fetch it again.
            no_branch = self.getExpressionNo()

            # If it's aborting, it doesn't contribute to merging.
            if no_branch.willRaiseException(BaseException):
                branch_no_collection = None
        else:
            branch_no_collection = None

        # Merge into parent execution.
        constraint_collection.mergeBranches(
            branch_yes_collection,
            branch_no_collection
        )

        if truth_value is True:
            return (
                wrapExpressionWithNodeSideEffects(
                    new_node = self.getExpressionYes(),
                    old_node = condition
                ),
                "new_expression",
                "Conditional expression predicted to yes case"
            )
        elif truth_value is False:
            return (
                wrapExpressionWithNodeSideEffects(
                    new_node = self.getExpressionNo(),
                    old_node = condition
                ),
                "new_expression",
                "Conditional expression predicted to no case"
            )
        else:
            return self, None, None

    def mayHaveSideEffectsBool(self):
        if self.getCondition().mayHaveSideEffectsBool():
            return True

        if self.getExpressionYes().mayHaveSideEffectsBool():
            return True

        if self.getExpressionNo().mayHaveSideEffectsBool():
            return True

        return False

    def mayRaiseException(self, exception_type):
        condition = self.getCondition()

        if condition.mayRaiseException(exception_type):
            return True

        if condition.mayRaiseExceptionBool(exception_type):
            return True

        yes_branch = self.getExpressionYes()

        # Handle branches that became empty behind our back
        if yes_branch is not None and \
           yes_branch.mayRaiseException(exception_type):
            return True

        no_branch = self.getExpressionNo()

        # Handle branches that became empty behind our back
        if no_branch is not None and \
           no_branch.mayRaiseException(exception_type):
            return True

        return False

    def mayRaiseExceptionBool(self, exception_type):
        if self.getCondition().mayRaiseExceptionBool(exception_type):
            return True

        if self.getExpressionYes().mayRaiseExceptionBool(exception_type):
            return True

        if self.getExpressionNo().mayRaiseExceptionBool(exception_type):
            return True

        return False


class ExpressionConditionalBoolBase(ExpressionChildrenHavingBase):
    named_children = (
        "left",
        "right"
    )

    def __init__(self, left, right, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "left"  : left,
                "right" : right,
            },
            source_ref = source_ref
        )

    getLeft = ExpressionChildrenHavingBase.childGetter(
        "left"
    )
    getRight = ExpressionChildrenHavingBase.childGetter(
        "right"
    )

    def computeExpressionRaw(self, constraint_collection):
        # Query the truth value after the expression is evaluated, once it is
        # evaluated in onExpression, it is known.
        constraint_collection.onExpression(
            expression = self.getLeft()
        )
        left = self.getLeft()

        left_may_raise = left.mayRaiseException(BaseException)

        if left_may_raise:
            constraint_collection.onExceptionRaiseExit(
                BaseException
            )
        # No need to look any further, if the condition raises, the branches do
        # not matter at all.
        if left.willRaiseException(BaseException):
            return left, "new_raise", """\
Conditional %s statements already raises implicitly in condition, removing \
branches.""" % self.conditional_kind

        if not left_may_raise and left.mayRaiseExceptionBool(BaseException):
            constraint_collection.onExceptionRaiseExit(
                BaseException
            )

        # Decide this based on truth value of condition.
        truth_value = left.getTruthValue()

        truth_value_use_left = self.conditional_kind == "or"
        truth_value_use_right = not truth_value_use_left

        right = self.getRight()

        # Continue to execute for yes branch unless we know it's not going to be
        # relevant.
        if truth_value is not truth_value_use_left:
            # TODO: We now know that left evaluates and we should tell the
            # branch that.
            branch_yes_collection = ConstraintCollectionBranch(
                parent = constraint_collection,
                name   = "boolean %s right branch" % self.conditional_kind
            )

            branch_yes_collection.computeBranch(
                branch = right
            )

            # May have just gone away, so fetch it again.
            right = self.getRight()

            # If it's aborting, it doesn't contribute to merging.
            if right.willRaiseException(BaseException):
                branch_yes_collection = None
        else:
            branch_yes_collection = None


        if branch_yes_collection:
            # Merge into parent execution.
            constraint_collection.mergeBranches(
                branch_yes_collection,
                None
            )

        if truth_value is truth_value_use_left:
            return (
                left,
                "new_expression",
                "Conditional '%s' expression predicted to left value." % self.conditional_kind
            )
        elif truth_value is truth_value_use_right:
            return (
                wrapExpressionWithNodeSideEffects(
                    new_node = right,
                    old_node = left
                ),
                "new_expression",
                "Conditional '%s' expression predicted right value." % self.conditional_kind
            )
        else:
            return self, None, None

    def mayRaiseException(self, exception_type):
        left = self.getLeft()

        if left.mayRaiseException(exception_type):
            return True

        if left.mayRaiseExceptionBool(exception_type):
            return True

        right = self.getRight()

        if right.mayRaiseException(exception_type):
            return True

        return False

    def mayRaiseExceptionBool(self, exception_type):
        if self.getLeft().mayRaiseExceptionBool(exception_type):
            return True

        if self.getRight().mayRaiseExceptionBool(exception_type):
            return True

        return False

    def mayHaveSideEffectsBool(self):
        if self.getLeft().mayHaveSideEffectsBool():
            return True

        if self.getRight().mayHaveSideEffectsBool():
            return True

        return False


class ExpressionConditionalOR(ExpressionConditionalBoolBase):
    kind = "EXPRESSION_CONDITIONAL_OR"

    def __init__(self, left, right, source_ref):
        ExpressionConditionalBoolBase.__init__(
            self,
            left       = left,
            right      = right,
            source_ref = source_ref
        )

        self.conditional_kind = "or"


class ExpressionConditionalAND(ExpressionConditionalBoolBase):
    kind = "EXPRESSION_CONDITIONAL_AND"

    def __init__(self, left, right, source_ref):
        ExpressionConditionalBoolBase.__init__(
            self,
            left       = left,
            right      = right,
            source_ref = source_ref
        )

        self.conditional_kind = "and"


class StatementConditional(StatementChildrenHavingBase):
    kind = "STATEMENT_CONDITIONAL"

    named_children = (
        "condition",
        "yes_branch",
        "no_branch"
    )

    checkers = {
        "yes_branch" : checkStatementsSequenceOrNone,
        "no_branch" : checkStatementsSequenceOrNone,
    }

    def __init__(self, condition, yes_branch, no_branch, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "condition"  : condition,
                "yes_branch" : yes_branch,
                "no_branch"  : no_branch
            },
            source_ref = source_ref
        )

    getCondition = StatementChildrenHavingBase.childGetter("condition")
    getBranchYes = StatementChildrenHavingBase.childGetter("yes_branch")
    setBranchYes = StatementChildrenHavingBase.childSetter("yes_branch")
    getBranchNo = StatementChildrenHavingBase.childGetter("no_branch")
    setBranchNo = StatementChildrenHavingBase.childSetter("no_branch")

    def isStatementAborting(self):
        yes_branch = self.getBranchYes()

        if yes_branch is not None:
            if yes_branch.isStatementAborting():
                no_branch = self.getBranchNo()

                if no_branch is not None:
                    return no_branch.isStatementAborting()
                else:
                    return False
            else:
                return False
        else:
            return False

    def mayRaiseException(self, exception_type):
        condition = self.getCondition()

        if condition.mayRaiseException(exception_type):
            return True

        if condition.mayRaiseExceptionBool(exception_type):
            return True

        yes_branch = self.getBranchYes()

        # Handle branches that became empty behind our back
        if yes_branch is not None and \
           yes_branch.mayRaiseException(exception_type):
            return True

        no_branch = self.getBranchNo()

        # Handle branches that became empty behind our back
        if no_branch is not None and \
           no_branch.mayRaiseException(exception_type):
            return True

        return False

    def needsFrame(self):
        condition = self.getCondition()

        if condition.mayRaiseException(BaseException):
            return True

        if condition.mayRaiseExceptionBool(BaseException):
            return True

        yes_branch = self.getBranchYes()

        # Handle branches that became empty behind our back
        if yes_branch is not None and \
           yes_branch.needsFrame():
            return True

        no_branch = self.getBranchNo()

        # Handle branches that became empty behind our back
        if no_branch is not None and \
           no_branch.needsFrame():
            return True

        return False

    def computeStatement(self, constraint_collection):
        # This is rather complex stuff, pylint: disable=R0912,R0915

        constraint_collection.onExpression(
            expression = self.getCondition()
        )
        condition = self.getCondition()

        condition_may_raise = condition.mayRaiseException(BaseException)

        if condition_may_raise:
            constraint_collection.onExceptionRaiseExit(
                BaseException
            )

        # No need to look any further, if the condition raises, the branches do
        # not matter at all.
        if condition.willRaiseException(BaseException):
            result = makeStatementExpressionOnlyReplacementNode(
                expression = condition,
                node       = self
            )

            return result, "new_raise", """\
Conditional statements already raises implicitly in condition, removing \
branches."""

        if not condition_may_raise and condition.mayRaiseExceptionBool(BaseException):
            constraint_collection.onExceptionRaiseExit(
                BaseException
            )


        # Query the truth value after the expression is evaluated, once it is
        # evaluated in onExpression, it is known.
        truth_value = condition.getTruthValue()

        # TODO: We now know that condition evaluates to true for the yes branch
        # and to not true for no branch, the branch collection should know that.
        yes_branch = self.getBranchYes()
        no_branch = self.getBranchNo()

        # Handle branches that became empty behind our back.
        if yes_branch is not None:
            if not yes_branch.getStatements():
                yes_branch = None
        if no_branch is not None:
            if not no_branch.getStatements():
                no_branch = None

        # Consider to not remove branches that we know won't be taken.
        if yes_branch is not None and truth_value is False:
            constraint_collection.signalChange(
                tags       = "new_statements",
                source_ref = yes_branch.source_ref,
                message    = "Removed conditional branch not taken due to false condition value."
            )

            self.setBranchYes(None)
            yes_branch = None

        if no_branch is not None and truth_value is True:
            constraint_collection.signalChange(
                tags       = "new_statements",
                source_ref = no_branch.source_ref,
                message    = "Removed 'else' branch not taken due to true condition value."
            )

            self.setBranchNo(None)
            no_branch = None

        # Continue to execute for yes branch unless we know it's not going to be
        # relevant.
        if yes_branch is not None:
            branch_yes_collection = ConstraintCollectionBranch(
                parent = constraint_collection,
                name   = "conditional yes branch",
            )

            branch_yes_collection.computeBranch(
                branch = yes_branch
            )

            # May have just gone away, so fetch it again.
            yes_branch = self.getBranchYes()

            # If it's aborting, it doesn't contribute to merging.
            if yes_branch is None or yes_branch.isStatementAborting():
                branch_yes_collection = None
        else:
            branch_yes_collection = None

        # Continue to execute for yes branch.
        if no_branch is not None:
            branch_no_collection = ConstraintCollectionBranch(
                parent = constraint_collection,
                name   = "conditional no branch"
            )

            branch_no_collection.computeBranch(
                branch = no_branch
            )

            # May have just gone away, so fetch it again.
            no_branch = self.getBranchNo()

            # If it's aborting, it doesn't contribute to merging.
            if no_branch is None or no_branch.isStatementAborting():
                branch_no_collection = None
        else:
            branch_no_collection = None

        # Merge into parent execution.
        constraint_collection.mergeBranches(
            branch_yes_collection,
            branch_no_collection
        )

        # Both branches may have become empty, which case, the statement needs
        # not remain.
        if yes_branch is None and no_branch is None:
            # Need to keep the boolean check.
            if truth_value is None:
                condition = ExpressionBuiltinBool(
                    value      = condition,
                    source_ref = condition.getSourceReference()
                )

            if condition.mayHaveSideEffects():
                # With both branches eliminated, the condition remains as a side
                # effect.
                result = makeStatementExpressionOnlyReplacementNode(
                    expression = condition,
                    node       = self
                )

                return result, "new_statements", """\
Both branches have no effect, reduced to evaluate condition."""
            else:
                return None, "new_statements", """\
Removed conditional statement without effect."""

        # Note: Checking the condition late, so that the surviving branch got
        # processed already. Returning without doing that, will corrupt the SSA
        # results. TODO: Could pretend the other branch didn't exist to save
        # complexity the merging of processing.
        if truth_value is not None:
            if truth_value is True:
                choice = "true"

                new_statement = self.getBranchYes()
            else:
                choice = "false"

                new_statement = self.getBranchNo()

            new_statement = wrapStatementWithSideEffects(
                new_node   = new_statement,
                old_node   = condition,
                allow_none = True # surviving branch may empty
            )

            return new_statement, "new_statements", """\
Condition for branch was predicted to be always %s.""" % choice

        # If there is no "yes" branch, remove that. Maybe a bad idea though.
        if yes_branch is None:
            # Would be eliminated already, if there wasn't any "no" branch
            # either.
            assert no_branch is not None

            from .OperatorNodes import ExpressionOperationNOT

            new_statement = StatementConditional(
                condition  = ExpressionOperationNOT(
                    operand    = condition,
                    source_ref = condition.getSourceReference()
                ),
                yes_branch = no_branch,
                no_branch  = None,
                source_ref = self.getSourceReference()
            )

            return new_statement, "new_statements", """\
Empty 'yes' branch for conditional statement treated with inverted condition check."""

        return self, None, None

    def mayReturn(self):
        yes_branch = self.getBranchYes()

        if yes_branch is not None and yes_branch.mayReturn():
            return True

        no_branch = self.getBranchNo()

        if no_branch is not None and no_branch.mayReturn():
            return True

        return False

    def mayBreak(self):
        yes_branch = self.getBranchYes()

        if yes_branch is not None and yes_branch.mayBreak():
            return True

        no_branch = self.getBranchNo()

        if no_branch is not None and no_branch.mayBreak():
            return True

        return False


    def mayContinue(self):
        yes_branch = self.getBranchYes()

        if yes_branch is not None and yes_branch.mayContinue():
            return True

        no_branch = self.getBranchNo()

        if no_branch is not None and no_branch.mayContinue():
            return True

        return False
