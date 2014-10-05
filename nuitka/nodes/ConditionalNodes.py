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
""" Conditional nodes.

These is the conditional expression '(a if b else c)' and the conditional
statement, 'if a: ... else: ...' and there is no 'elif', because that is
expressed via nesting of conditional statements.
"""

from .NodeBases import ExpressionChildrenHavingBase, StatementChildrenHavingBase


# Delayed import into multiple branches is not an issue, pylint: disable=W0404


class ExpressionConditional(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_CONDITIONAL"

    named_children = (
        "condition",
        "expression_yes",
        "expression_no"
    )

    def __init__(self, condition, yes_expression, no_expression, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "condition"      : condition,
                "expression_yes" : yes_expression,
                "expression_no"  : no_expression
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
        # Children can tell all we need to know, pylint: disable=W0613

        # Query the truth value after the expression is evaluated, once it is
        # evaluated in onExpression, it is known.
        constraint_collection.onExpression(
            expression = self.getCondition()
        )
        condition = self.getCondition()

        # No need to look any further, if the condition raises, the branches do
        # not matter at all.
        if condition.willRaiseException(BaseException):
            return condition, "new_raise", """\
Conditional statements already raises implicitely in condition, removing \
branches."""


        # If the condition raises, we let that escape.
        if condition.willRaiseException(BaseException):
            return condition, "new_raise", """\
Conditional expression raises in condition."""

        from nuitka.optimizations.ConstraintCollections import \
            ConstraintCollectionBranch

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
            from .NodeMakingHelpers import wrapExpressionWithNodeSideEffects

            return (
                wrapExpressionWithNodeSideEffects(
                    new_node = self.getExpressionYes(),
                    old_node = condition
                ),
                "new_expression",
                "Conditional expression predicted to yes case"
            )
        elif truth_value is False:
            from .NodeMakingHelpers import wrapExpressionWithNodeSideEffects

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
        condition = self.getCondition()

        if condition.mayHaveSideEffectsBool():
            return True

        if self.getExpressionYes().mayHaveSideEffectsBool():
            return True

        if self.getExpressionNo().mayHaveSideEffectsBool():
            return True

        return False


class StatementConditional(StatementChildrenHavingBase):
    kind = "STATEMENT_CONDITIONAL"

    named_children = (
        "condition",
        "yes_branch",
        "no_branch"
    )

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

    getCondition = StatementChildrenHavingBase.childGetter( "condition" )
    getBranchYes = StatementChildrenHavingBase.childGetter( "yes_branch" )
    setBranchYes = StatementChildrenHavingBase.childSetter( "yes_branch" )
    getBranchNo = StatementChildrenHavingBase.childGetter( "no_branch" )
    setBranchNo = StatementChildrenHavingBase.childSetter( "no_branch" )

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
        # This is rather complex stuff, pylint: disable=R0912

        # Query the truth value after the expression is evaluated, once it is
        # evaluated in onExpression, it is known.
        constraint_collection.onExpression(
            expression = self.getCondition()
        )
        condition = self.getCondition()

        # No need to look any further, if the condition raises, the branches do
        # not matter at all.
        if condition.willRaiseException(BaseException):
            from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

            result = makeStatementExpressionOnlyReplacementNode(
                expression = condition,
                node       = self
            )

            return result, "new_raise", """\
Conditional statements already raises implicitely in condition, removing \
branches."""

        from nuitka.optimizations.ConstraintCollections import \
            ConstraintCollectionBranch

        # Consider to not execute branches that we know to be true, but execute
        # the ones that may be true, potentially both.
        truth_value = condition.getTruthValue()

        # TODO: We now know that condition evaluates to true for the yes branch
        # and to not true for no branch, the branch collection should know that.
        yes_branch = self.getBranchYes()

        # Handle branches that became empty behind our back.
        if yes_branch is not None:
            if not yes_branch.getStatements():
                yes_branch = None

        # Continue to execute for yes branch unless we know it's not going to be
        # relevant.
        if yes_branch is not None and truth_value is not False:
            branch_yes_collection = ConstraintCollectionBranch(
                parent = constraint_collection,
                branch = yes_branch
            )

            # May have just gone away, so fetch it again.
            yes_branch = self.getBranchYes()

            # If it's aborting, it doesn't contribute to merging.
            if yes_branch is None or yes_branch.isStatementAborting():
                branch_yes_collection = None
        else:
            branch_yes_collection = None

        no_branch = self.getBranchNo()

        # Handle branches that became empty behind our back
        if no_branch is not None:
            if not no_branch.getStatements():
                no_branch = None

        # Continue to execute for yes branch.
        if no_branch is not None and truth_value is not True:
            branch_no_collection = ConstraintCollectionBranch(
                parent = constraint_collection,
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

        # Both branches may have become empty.
        if yes_branch is None and no_branch is None:
            from .NodeMakingHelpers import \
                makeStatementExpressionOnlyReplacementNode

            # With both branches eliminated, the condition remains as a side
            # effect.
            result = makeStatementExpressionOnlyReplacementNode(
                expression = condition,
                node       = self
            )

            return result, "new_statements", """\
Both branches have no effect, reduced to evaluate condition."""

        if yes_branch is None:
            # Would be eliminated already, if there wasn't any "no" branch
            # either.
            assert no_branch is not None

            from .OperatorNodes import ExpressionOperationNOT

            new_statement = StatementConditional(
                condition = ExpressionOperationNOT(
                    operand    = condition,
                    source_ref = condition.getSourceReference()
                ),
                yes_branch = no_branch,
                no_branch  = None,
                source_ref = self.getSourceReference()
            )

            return new_statement, "new_statements", """\
Empty 'yes' branch for condition was replaced with inverted condition check."""

        # Note: Checking the condition late, so that the surviving branch got
        # processed already. Returning without doing that, will corrupt the SSA
        # results. TODO: Could pretend the other branch didn't exist to save
        # complexity the merging of processing.
        if truth_value is not None:
            from .NodeMakingHelpers import wrapStatementWithSideEffects

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
