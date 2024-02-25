#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Slice nodes.

Slices are important when working with lists. Tracking them can allow to
achieve more compact code, or predict results at compile time.

There will be a method "computeExpressionSlice" to aid predicting them.
"""

from nuitka.specs import BuiltinParameterSpecs

from .ChildrenHavingMixins import (
    ChildHavingStopMixin,
    ChildrenHavingExpressionLowerAutoNoneUpperAutoNoneMixin,
    ChildrenHavingStartStopMixin,
    ChildrenHavingStartStopStepMixin,
)
from .ConstantRefNodes import ExpressionConstantNoneRef, makeConstantRefNode
from .ExpressionBases import (
    ExpressionBase,
    ExpressionSpecBasedComputationNoRaiseMixin,
)
from .ExpressionShapeMixins import ExpressionSliceShapeExactMixin
from .NodeBases import SideEffectsFromChildrenMixin
from .NodeMakingHelpers import (
    makeStatementExpressionOnlyReplacementNode,
    makeStatementOnlyNodesFromExpressions,
    wrapExpressionWithSideEffects,
)
from .StatementBasesGenerated import (
    StatementAssignmentSliceBase,
    StatementDelSliceBase,
)


class StatementAssignmentSlice(StatementAssignmentSliceBase):
    kind = "STATEMENT_ASSIGNMENT_SLICE"

    named_children = ("source", "expression", "lower|optional", "upper|optional")

    python_version_spec = "< 0x300"

    def computeStatement(self, trace_collection):
        source = trace_collection.onExpression(self.subnode_source)

        # No assignment will occur, if the assignment source raises, so strip it
        # away.
        if source.willRaiseAnyException():
            result = makeStatementExpressionOnlyReplacementNode(
                expression=source, node=self
            )

            return (
                result,
                "new_raise",
                """\
Slice assignment raises exception in assigned value, removed assignment.""",
            )

        lookup_source = trace_collection.onExpression(self.subnode_expression)

        if lookup_source.willRaiseAnyException():
            result = makeStatementOnlyNodesFromExpressions(
                expressions=(source, lookup_source)
            )

            return (
                result,
                "new_raise",
                """\
Slice assignment raises exception in sliced value, removed assignment.""",
            )

        lower = trace_collection.onExpression(self.subnode_lower, allow_none=True)

        if lower is not None and lower.willRaiseAnyException():
            result = makeStatementOnlyNodesFromExpressions(
                expressions=(source, lookup_source, lower)
            )

            return (
                result,
                "new_raise",
                """\
Slice assignment raises exception in lower slice boundary value, removed \
assignment.""",
            )

        upper = trace_collection.onExpression(self.subnode_upper, allow_none=True)

        if upper is not None and upper.willRaiseAnyException():
            result = makeStatementOnlyNodesFromExpressions(
                expressions=(source, lookup_source, lower, upper)
            )

            return (
                result,
                "new_raise",
                """\
Slice assignment raises exception in upper slice boundary value, removed \
assignment.""",
            )

        return lookup_source.computeExpressionSetSlice(
            set_node=self,
            lower=lower,
            upper=upper,
            value_node=source,
            trace_collection=trace_collection,
        )


class StatementDelSlice(StatementDelSliceBase):
    kind = "STATEMENT_DEL_SLICE"

    named_children = ("expression", "lower|optional", "upper|optional")

    def computeStatement(self, trace_collection):
        lookup_source = trace_collection.onExpression(self.subnode_expression)

        if lookup_source.willRaiseAnyException():
            result = makeStatementExpressionOnlyReplacementNode(
                expression=lookup_source, node=self
            )

            return (
                result,
                "new_raise",
                """\
Slice del raises exception in sliced value, removed del""",
            )

        lower = trace_collection.onExpression(self.subnode_lower, allow_none=True)

        if lower is not None and lower.willRaiseAnyException():
            result = makeStatementOnlyNodesFromExpressions(
                expressions=(lookup_source, lower)
            )

            return (
                result,
                "new_raise",
                """
Slice del raises exception in lower slice boundary value, removed del""",
            )

        trace_collection.onExpression(self.subnode_upper, allow_none=True)
        upper = self.subnode_upper

        if upper is not None and upper.willRaiseAnyException():
            result = makeStatementOnlyNodesFromExpressions(
                expressions=(lookup_source, lower, upper)
            )

            return (
                result,
                "new_raise",
                """
Slice del raises exception in upper slice boundary value, removed del""",
            )

        return lookup_source.computeExpressionDelSlice(
            set_node=self, lower=lower, upper=upper, trace_collection=trace_collection
        )


class ExpressionSliceLookup(
    ChildrenHavingExpressionLowerAutoNoneUpperAutoNoneMixin, ExpressionBase
):
    kind = "EXPRESSION_SLICE_LOOKUP"

    python_version_spec = "< 0x300"

    named_children = ("expression", "lower|auto_none", "upper|auto_none")

    def __init__(self, expression, lower, upper, source_ref):
        ChildrenHavingExpressionLowerAutoNoneUpperAutoNoneMixin.__init__(
            self,
            expression=expression,
            lower=lower,
            upper=upper,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        lookup_source = self.subnode_expression

        return lookup_source.computeExpressionSlice(
            lookup_node=self,
            lower=self.subnode_lower,
            upper=self.subnode_upper,
            trace_collection=trace_collection,
        )

    @staticmethod
    def isKnownToBeIterable(count):
        # TODO: Should ask SliceRegistry
        return None


def makeExpressionBuiltinSlice(start, stop, step, source_ref):
    if (
        (start is None or start.isCompileTimeConstant())
        and (stop is None or stop.isCompileTimeConstant())
        and (step is None or step.isCompileTimeConstant())
    ):
        # Avoid going slices for what is effectively constant.

        start_value = None if start is None else start.getCompileTimeConstant()
        stop_value = None if stop is None else stop.getCompileTimeConstant()
        step_value = None if step is None else step.getCompileTimeConstant()

        return makeConstantRefNode(
            constant=slice(start_value, stop_value, step_value), source_ref=source_ref
        )

    if start is None and step is None:
        return ExpressionBuiltinSlice1(stop=stop, source_ref=source_ref)

    if start is None:
        start = ExpressionConstantNoneRef(source_ref=source_ref)
    if stop is None:
        stop = ExpressionConstantNoneRef(source_ref=source_ref)

    if step is None:
        return ExpressionBuiltinSlice2(start=start, stop=stop, source_ref=source_ref)

    return ExpressionBuiltinSlice3(
        start=start, stop=stop, step=step, source_ref=source_ref
    )


class ExpressionBuiltinSliceMixin(
    ExpressionSliceShapeExactMixin, SideEffectsFromChildrenMixin
):
    # Mixins are required to define empty slots
    __slots__ = ()

    builtin_spec = BuiltinParameterSpecs.builtin_slice_spec

    # We use SideEffectsFromChildrenMixin for the other things.
    def mayHaveSideEffects(self):
        return self.mayRaiseException(BaseException)


class ExpressionBuiltinSlice3(
    ExpressionBuiltinSliceMixin,
    ExpressionSpecBasedComputationNoRaiseMixin,
    ChildrenHavingStartStopStepMixin,
    ExpressionBase,
):
    kind = "EXPRESSION_BUILTIN_SLICE3"

    named_children = ("start", "stop", "step")

    def __init__(self, start, stop, step, source_ref):
        ChildrenHavingStartStopStepMixin.__init__(
            self,
            start=start,
            stop=stop,
            step=step,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_step.isExpressionConstantNoneRef()
            or self.subnode_step.getIndexValue() == 1
        ):
            return trace_collection.computedExpressionResult(
                wrapExpressionWithSideEffects(
                    old_node=self,
                    new_node=ExpressionBuiltinSlice2(
                        start=self.subnode_start,
                        stop=self.subnode_stop,
                        source_ref=self.source_ref,
                    ),
                    side_effects=self.subnode_step.extractSideEffects(),
                ),
                "new_expression",
                "Reduce 3 argument slice object creation to two argument form.",
            )

        return self.computeBuiltinSpec(
            trace_collection=trace_collection,
            given_values=(self.subnode_start, self.subnode_stop, self.subnode_step),
        )

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_start.mayRaiseException(exception_type)
            or self.subnode_stop.mayRaiseException(exception_type)
            or self.subnode_step.mayRaiseException(exception_type)
        )


class ExpressionBuiltinSlice2(
    ExpressionBuiltinSliceMixin,
    ExpressionSpecBasedComputationNoRaiseMixin,
    ChildrenHavingStartStopMixin,
    ExpressionBase,
):
    kind = "EXPRESSION_BUILTIN_SLICE2"

    named_children = ("start", "stop")

    def __init__(self, start, stop, source_ref):
        ChildrenHavingStartStopMixin.__init__(
            self,
            start=start,
            stop=stop,
        )

        ExpressionBase.__init__(
            self,
            source_ref,
        )

    def computeExpression(self, trace_collection):
        if self.subnode_start.isExpressionConstantNoneRef():
            return trace_collection.computedExpressionResult(
                wrapExpressionWithSideEffects(
                    old_node=self,
                    new_node=ExpressionBuiltinSlice1(
                        stop=self.subnode_stop, source_ref=self.source_ref
                    ),
                    side_effects=self.subnode_start.extractSideEffects(),
                ),
                "new_expression",
                "Reduce 2 argument slice object creation to single argument form.",
            )

        return self.computeBuiltinSpec(
            trace_collection=trace_collection,
            given_values=(self.subnode_start, self.subnode_stop),
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_start.mayRaiseException(
            exception_type
        ) or self.subnode_stop.mayRaiseException(exception_type)


class ExpressionBuiltinSlice1(
    ExpressionBuiltinSliceMixin,
    ExpressionSpecBasedComputationNoRaiseMixin,
    ChildHavingStopMixin,
    ExpressionBase,
):
    kind = "EXPRESSION_BUILTIN_SLICE1"

    named_children = ("stop",)

    def __init__(self, stop, source_ref):
        ChildHavingStopMixin.__init__(self, stop=stop)

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        return self.computeBuiltinSpec(
            trace_collection=trace_collection,
            given_values=(self.subnode_stop,),
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_stop.mayRaiseException(exception_type)


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
