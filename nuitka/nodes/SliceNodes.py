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
""" Slice nodes.

Slices are important when working with lists. Tracking them can allow to
achieve more compact code, or predict results at compile time.

There will be a method "computeExpressionSlice" to aid predicting them.
"""

from nuitka.utils import Utils

from .NodeBases import ExpressionChildrenHavingBase, StatementChildrenHavingBase
from .NodeMakingHelpers import (
    convertNoneConstantToNone,
    getComputationResult,
    makeStatementExpressionOnlyReplacementNode,
    makeStatementOnlyNodesFromExpressions
)


class StatementAssignmentSlice(StatementChildrenHavingBase):
    kind = "STATEMENT_ASSIGNMENT_SLICE"

    named_children = (
        "source",
        "expression",
        "lower",
        "upper"
    )

    def __init__(self, expression, lower, upper, source, source_ref):
        assert Utils.python_version < 300

        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "source"     : source,
                "expression" : expression,
                "lower"      : lower,
                "upper"      : upper
            },
            source_ref = source_ref
        )

    getLookupSource = StatementChildrenHavingBase.childGetter("expression")
    getLower = StatementChildrenHavingBase.childGetter("lower")
    getUpper = StatementChildrenHavingBase.childGetter("upper")
    getAssignSource = StatementChildrenHavingBase.childGetter("source")

    def computeStatement(self, constraint_collection):
        constraint_collection.onExpression(self.getAssignSource())
        source = self.getAssignSource()

        # No assignment will occur, if the assignment source raises, so strip it
        # away.
        if source.willRaiseException(BaseException):
            result = makeStatementExpressionOnlyReplacementNode(
                expression = source,
                node       = self
            )

            return result, "new_raise", """\
Slice assignment raises exception in assigned value, removed assignment."""

        constraint_collection.onExpression(self.getLookupSource())
        lookup_source = self.getLookupSource()

        if lookup_source.willRaiseException(BaseException):
            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    source,
                    lookup_source
                )
            )

            return result, "new_raise", """\
Slice assignment raises exception in sliced value, removed assignment."""

        constraint_collection.onExpression(self.getLower(), allow_none = True)
        lower = self.getLower()

        if lower is not None and lower.willRaiseException(BaseException):
            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    source,
                    lookup_source,
                    lower
                )
            )

            return result, "new_raise", """\
Slice assignment raises exception in lower slice boundary value, removed \
assignment."""

        constraint_collection.onExpression(self.getUpper(), allow_none = True)
        upper = self.getUpper()

        if upper is not None and upper.willRaiseException(BaseException):
            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    source,
                    lookup_source,
                    lower,
                    upper
                )
            )

            return result, "new_raise", """\
Slice assignment raises exception in upper slice boundary value, removed \
assignment."""

        return lookup_source.computeExpressionSetSlice(
            set_node              = self,
            lower                 = lower,
            upper                 = upper,
            value_node            = source,
            constraint_collection = constraint_collection
        )


class StatementDelSlice(StatementChildrenHavingBase):
    kind = "STATEMENT_DEL_SLICE"

    named_children = (
        "expression",
        "lower",
        "upper"
    )

    def __init__(self, expression, lower, upper, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "expression" : expression,
                "lower"      : lower,
                "upper"      : upper
            },
            source_ref = source_ref
        )

    getLookupSource = StatementChildrenHavingBase.childGetter("expression")
    getLower = StatementChildrenHavingBase.childGetter("lower")
    getUpper = StatementChildrenHavingBase.childGetter("upper")

    def computeStatement(self, constraint_collection):
        constraint_collection.onExpression(self.getLookupSource())
        lookup_source = self.getLookupSource()

        if lookup_source.willRaiseException(BaseException):
            result = makeStatementExpressionOnlyReplacementNode(
                expression = lookup_source,
                node       = self
            )

            return result, "new_raise", """\
Slice del raises exception in sliced value, removed del"""


        constraint_collection.onExpression(self.getLower(), allow_none = True)
        lower = self.getLower()

        if lower is not None and lower.willRaiseException(BaseException):
            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    lookup_source,
                    lower
                )
            )

            return result, "new_raise", """
Slice del raises exception in lower slice boundary value, removed del"""

        constraint_collection.onExpression(self.getUpper(), allow_none = True)
        upper = self.getUpper()

        if upper is not None and upper.willRaiseException(BaseException):
            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    lookup_source,
                    lower,
                    upper
                )
            )

            return result, "new_raise", """
Slice del raises exception in upper slice boundary value, removed del"""

        return lookup_source.computeExpressionDelSlice(
            set_node              = self,
            lower                 = lower,
            upper                 = upper,
            constraint_collection = constraint_collection
        )


class ExpressionSliceLookup(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_SLICE_LOOKUP"

    named_children = (
        "expression",
        "lower",
        "upper"
    )

    checkers   = {
        "upper" : convertNoneConstantToNone,
        "lower" : convertNoneConstantToNone
    }

    def __init__(self, expression, lower, upper, source_ref):
        assert Utils.python_version < 300

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "expression" : expression,
                "upper"      : upper,
                "lower"      : lower
            },
            source_ref = source_ref
        )

    getLookupSource = ExpressionChildrenHavingBase.childGetter("expression")

    getLower = ExpressionChildrenHavingBase.childGetter("lower")
    setLower = ExpressionChildrenHavingBase.childSetter("lower")

    getUpper = ExpressionChildrenHavingBase.childGetter("upper")
    setUpper = ExpressionChildrenHavingBase.childSetter("upper")

    def computeExpression(self, constraint_collection):
        lookup_source = self.getLookupSource()

        return lookup_source.computeExpressionSlice(
            lookup_node           = self,
            lower                 = self.getLower(),
            upper                 = self.getUpper(),
            constraint_collection = constraint_collection
        )

    def isKnownToBeIterable(self, count):
        # TODO: Should ask SliceRegistry
        return None


class ExpressionSliceObject(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_SLICE_OBJECT"

    named_children = (
        "lower",
        "upper",
        "step"
    )

    def __init__(self, lower, upper, step, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "upper" : upper,
                "lower" : lower,
                "step"  : step
            },
            source_ref = source_ref
        )

    getLower = ExpressionChildrenHavingBase.childGetter("lower")
    getUpper = ExpressionChildrenHavingBase.childGetter("upper")
    getStep  = ExpressionChildrenHavingBase.childGetter("step")

    def computeExpression(self, constraint_collection):
        lower = self.getLower()

        if lower is not None and not lower.isCompileTimeConstant():
            return self, None, None

        upper = self.getUpper()

        if upper is not None and not upper.isCompileTimeConstant():
            return self, None, None

        step = self.getStep()

        if step is not None and not step.isCompileTimeConstant():
            return self, None, None

        return getComputationResult(
            node        = self,
            computation = lambda : slice(
                lower.getCompileTimeConstant() if lower is not None else None,
                upper.getCompileTimeConstant() if upper is not None else None,
                step.getCompileTimeConstant()  if step is not None else None
            ),
            description = "Built-in call to 'slice' computed."
        )
