#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Nodes for comparisons.

"""

from nuitka import PythonOperators

from .ExpressionBases import ExpressionChildrenHavingBase
from .NodeMakingHelpers import (
    makeComparisonNode,
    makeConstantReplacementNode,
    wrapExpressionWithSideEffects
)


class ExpressionComparisonBase(ExpressionChildrenHavingBase):
    named_children = (
        "left",
        "right"
    )

    def __init__(self, left, right, comparator, source_ref):
        assert left.isExpression()
        assert right.isExpression()

        assert comparator in PythonOperators.all_comparison_functions, comparator

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "left"  : left,
                "right" : right
            },
            source_ref = source_ref
        )

        self.comparator = comparator

        if comparator in ("Is", "IsNot", "In", "NotIn"):
            assert self.__class__ is not ExpressionComparison

    def getOperands(self):
        return (
            self.getLeft(),
            self.getRight()
        )

    getLeft = ExpressionChildrenHavingBase.childGetter("left")
    getRight = ExpressionChildrenHavingBase.childGetter("right")

    def getComparator(self):
        return self.comparator

    def getDetails(self):
        return {
            "comparator" : self.comparator
        }

    @staticmethod
    def isExpressionComparison():
        return True

    def getSimulator(self):
        return PythonOperators.all_comparison_functions[self.comparator]

    def computeExpression(self, trace_collection):
        left = self.getLeft()
        right = self.getRight()

        if left.isCompileTimeConstant() and right.isCompileTimeConstant():
            left_value = left.getCompileTimeConstant()
            right_value = right.getCompileTimeConstant()

            return trace_collection.getCompileTimeComputationResult(
                node        = self,
                computation = lambda : self.getSimulator()(
                    left_value,
                    right_value
                ),
                description = "Comparison of constant arguments."
            )

        # The value of these nodes escaped and could change its contents.
        trace_collection.removeKnowledge(left)
        trace_collection.removeKnowledge(right)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def computeExpressionOperationNot(self, not_node, trace_collection):
        if self.comparator in PythonOperators.comparison_inversions:
            left, right = self.getOperands()

            result = makeComparisonNode(
                left       = left,
                right      = right,
                comparator = PythonOperators.comparison_inversions[
                    self.comparator
                ],
                source_ref = self.source_ref
            )

            return result, "new_expression", """\
Replaced negated comparison with inverse comparison."""

        return not_node, None, None


class ExpressionComparison(ExpressionComparisonBase):
    kind = "EXPRESSION_COMPARISON"

    def __init__(self, left, right, comparator, source_ref):
        ExpressionComparisonBase.__init__(
            self,
            left       = left,
            right      = right,
            comparator = comparator,
            source_ref = source_ref
        )


class ExpressionComparisonIsIsNotBase(ExpressionComparisonBase):
    def __init__(self, left, right, comparator, source_ref):
        ExpressionComparisonBase.__init__(
            self,
            left       = left,
            right      = right,
            comparator = comparator,
            source_ref = source_ref
        )

        assert comparator in ("Is", "IsNot")

        self.match_value = comparator == "Is"

    def getDetails(self):
        return {}

    def mayRaiseException(self, exception_type):
        return self.getLeft().mayRaiseException(exception_type) or \
               self.getRight().mayRaiseException(exception_type)

    def mayRaiseExceptionBool(self, exception_type):
        return False

    def computeExpression(self, trace_collection):
        left, right = self.getOperands()

        if trace_collection.mustAlias(left, right):
            result = makeConstantReplacementNode(
                constant = self.match_value,
                node     = self
            )

            if left.mayHaveSideEffects() or right.mayHaveSideEffects():
                result = wrapExpressionWithSideEffects(
                    side_effects = self.extractSideEffects(),
                    old_node     = self,
                    new_node     = result
                )

            return result, "new_constant", """\
Determined values to alias and therefore result of %s comparison.""" % (
                self.comparator
            )

        if trace_collection.mustNotAlias(left, right):
            result = makeConstantReplacementNode(
                constant = not self.match_value,
                node     = self
            )

            if left.mayHaveSideEffects() or right.mayHaveSideEffects():
                result = wrapExpressionWithSideEffects(
                    side_effects = self.extractSideEffects(),
                    old_node     = self,
                    new_node     = result
                )

            return result, "new_constant", """\
Determined values to not alias and therefore result of '%s' comparison.""" % (
                self.comparator
            )

        return ExpressionComparisonBase.computeExpression(
            self,
            trace_collection = trace_collection
        )

    def extractSideEffects(self):
        left, right = self.getOperands()

        return left.extractSideEffects() + right.extractSideEffects()

    def computeExpressionDrop(self, statement, trace_collection):
        from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

        result = makeStatementOnlyNodesFromExpressions(
            expressions = self.getOperands()
        )

        return result, "new_statements", """\
Removed %s comparison for unused result.""" % self.comparator


class ExpressionComparisonIs(ExpressionComparisonIsIsNotBase):
    kind = "EXPRESSION_COMPARISON_IS"

    def __init__(self, left, right, source_ref):
        ExpressionComparisonIsIsNotBase.__init__(
            self,
            left       = left,
            right      = right,
            comparator = "Is",
            source_ref = source_ref
    )


class ExpressionComparisonIsNOT(ExpressionComparisonIsIsNotBase):
    kind = "EXPRESSION_COMPARISON_IS_NOT"

    def __init__(self, left, right, source_ref):
        ExpressionComparisonIsIsNotBase.__init__(
            self,
            left       = left,
            right      = right,
            comparator = "IsNot",
            source_ref = source_ref
    )


class ExpressionComparisonExceptionMatch(ExpressionComparisonBase):
    kind = "EXPRESSION_COMPARISON_EXCEPTION_MATCH"

    def __init__(self, left, right, source_ref):
        ExpressionComparisonBase.__init__(
            self,
            left       = left,
            right      = right,
            comparator = "exception_match",
            source_ref = source_ref
        )

    def getDetails(self):
        return {}

    def getSimulator(self):
        assert False

        return PythonOperators.all_comparison_functions[self.comparator]


class ExpressionComparisonInNotInBase(ExpressionComparisonBase):
    def __init__(self, left, right, comparator, source_ref):
        ExpressionComparisonBase.__init__(
            self,
            left       = left,
            right      = right,
            comparator = comparator,
            source_ref = source_ref
        )

        assert comparator in ("In", "NotIn")

    def getDetails(self):
        return {}

    def mayRaiseException(self, exception_type):
        left = self.getLeft()

        if left.mayRaiseException(exception_type):
            return True

        right = self.getRight()

        if right.mayRaiseException(exception_type):
            return True

        return right.mayRaiseExceptionIn(exception_type, left)

    def mayRaiseExceptionBool(self, exception_type):
        return False

    def computeExpression(self, trace_collection):
        return self.getRight().computeExpressionComparisonIn(
            in_node          = self,
            value_node       = self.getLeft(),
            trace_collection = trace_collection
        )


class ExpressionComparisonIn(ExpressionComparisonInNotInBase):
    kind = "EXPRESSION_COMPARISON_IN"

    def __init__(self, left, right, source_ref):
        ExpressionComparisonInNotInBase.__init__(
            self,
            left       = left,
            right      = right,
            comparator = "In",
            source_ref = source_ref
        )


class ExpressionComparisonNOTIn(ExpressionComparisonInNotInBase):
    kind = "EXPRESSION_COMPARISON_NOT_IN"

    def __init__(self, left, right, source_ref):
        ExpressionComparisonInNotInBase.__init__(
            self,
            left       = left,
            right      = right,
            comparator = "NotIn",
            source_ref = source_ref
        )
