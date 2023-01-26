#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Node the calls to the 'range' built-in.

This is a rather complex beast as it has many cases, is difficult to know if
it's sizable enough to compute, and there are complex cases, where the bad
result of it can be predicted still, and these are interesting for warnings.

"""

import math

from nuitka.PythonVersions import python_version
from nuitka.specs import BuiltinParameterSpecs

from .ChildrenHavingMixins import (
    ChildHavingLowMixin,
    ChildrenHavingLowHighMixin,
    ChildrenHavingLowHighStepMixin,
)
from .ExpressionBases import ExpressionBase
from .ExpressionShapeMixins import ExpressionListShapeExactMixin
from .IterationHandles import (
    IterationHandleRange1,
    IterationHandleRange2,
    IterationHandleRange3,
)
from .NodeMakingHelpers import makeConstantReplacementNode
from .shapes.BuiltinTypeShapes import tshape_xrange


class ExpressionBuiltinRangeMixin(ExpressionListShapeExactMixin):
    """Mixin class for range nodes with 1/2/3 arguments."""

    # Mixins are required to slots
    __slots__ = ()

    builtin_spec = BuiltinParameterSpecs.builtin_range_spec

    def getTruthValue(self):
        length = self.getIterationLength()

        if length is None:
            return None
        else:
            return length > 0

    def mayHaveSideEffects(self):
        for child in self.getVisitableNodes():
            if child.mayHaveSideEffects():
                return True

            if child.getIntegerValue() is None:
                return True

            if python_version >= 0x270 and child.isExpressionConstantFloatRef():
                return True

        return False

    def mayRaiseException(self, exception_type):
        for child in self.getVisitableNodes():
            if child.mayRaiseException(exception_type):
                return True

            # TODO: Should take exception_type value into account here.
            if child.getIntegerValue() is None:
                return True

            if python_version >= 0x270 and child.isExpressionConstantFloatRef():
                return True

        step = self.subnode_step

        # A step of 0 will raise.
        if step is not None and step.getIntegerValue() == 0:
            return True

        return False

    def computeBuiltinSpec(self, trace_collection, given_values):
        assert self.builtin_spec is not None, self

        if not self.builtin_spec.isCompileTimeComputable(given_values):
            trace_collection.onExceptionRaiseExit(BaseException)

            # TODO: Raise exception known step 0.

            return self, None, None

        return trace_collection.getCompileTimeComputationResult(
            node=self,
            computation=lambda: self.builtin_spec.simulateCall(given_values),
            description="Built-in call to '%s' computed."
            % (self.builtin_spec.getName()),
        )

    def computeExpressionIter1(self, iter_node, trace_collection):
        assert python_version < 0x300

        # TODO: The xrange is always faster and more memory usage than range, so this makes no sense, to
        # use it as a source for any iteration, esp. as xrange is the Python3 only type that will be
        # best optimized.
        result = makeExpressionBuiltinXrange(
            low=self.subnode_low,
            high=self.subnode_high,
            step=self.subnode_step,
            source_ref=self.source_ref,
        )

        self.parent.replaceChild(self, result)
        del self.parent

        return (
            iter_node,
            "new_expression",
            "Replaced 'range' with 'xrange' built-in call for iteration.",
        )

    def canPredictIterationValues(self):
        return self.getIterationLength() is not None


class ExpressionBuiltinRange1(
    ExpressionBuiltinRangeMixin, ChildHavingLowMixin, ExpressionBase
):
    kind = "EXPRESSION_BUILTIN_RANGE1"

    python_version_spec = "< 0x300"

    named_children = ("low",)

    subnode_high = None
    subnode_step = None

    def __init__(self, low, source_ref):
        ChildHavingLowMixin.__init__(self, low=low)

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        low = self.subnode_low

        return self.computeBuiltinSpec(
            trace_collection=trace_collection, given_values=(low,)
        )

    def getIterationLength(self):
        low = self.subnode_low.getIntegerValue()

        if low is None:
            return None

        return max(0, low)

    def getIterationHandle(self):
        low = self.subnode_low.getIntegerValue()
        if low is None:
            return None

        return IterationHandleRange1(low, self.source_ref)

    def getIterationValue(self, element_index):
        length = self.getIterationLength()

        if length is None:
            return None

        if element_index > length:
            return None

        # TODO: Make sure to cast element_index to what CPython will give, for
        # now a downcast will do.
        return makeConstantReplacementNode(
            constant=int(element_index), node=self, user_provided=False
        )

    def isKnownToBeIterable(self, count):
        return count is None or count == self.getIterationLength()


class ExpressionBuiltinRange2(
    ExpressionBuiltinRangeMixin, ChildrenHavingLowHighMixin, ExpressionBase
):
    kind = "EXPRESSION_BUILTIN_RANGE2"

    python_version_spec = "< 0x300"

    named_children = ("low", "high")

    # For the mixing to work generically
    subnode_step = None

    def __init__(self, low, high, source_ref):
        ChildrenHavingLowHighMixin.__init__(
            self,
            low=low,
            high=high,
        )

        ExpressionBase.__init__(self, source_ref)

    builtin_spec = BuiltinParameterSpecs.builtin_range_spec

    def computeExpression(self, trace_collection):
        assert python_version < 0x300

        low = self.subnode_low
        high = self.subnode_high

        return self.computeBuiltinSpec(
            trace_collection=trace_collection, given_values=(low, high)
        )

    def getIterationLength(self):
        low = self.subnode_low
        high = self.subnode_high

        low = low.getIntegerValue()

        if low is None:
            return None

        high = high.getIntegerValue()

        if high is None:
            return None

        return max(0, high - low)

    def getIterationHandle(self):
        low = self.subnode_low.getIntegerValue()
        if low is None:
            return None

        high = self.subnode_high.getIntegerValue()
        if high is None:
            return None

        return IterationHandleRange2(low, high, self.source_ref)

    def getIterationValue(self, element_index):
        low = self.subnode_low
        high = self.subnode_high

        low = low.getIntegerValue()

        if low is None:
            return None

        high = high.getIntegerValue()

        if high is None:
            return None

        result = low + element_index

        if result >= high:
            return None
        else:
            return makeConstantReplacementNode(
                constant=result, node=self, user_provided=False
            )

    def isKnownToBeIterable(self, count):
        return count is None or count == self.getIterationLength()


class ExpressionBuiltinRange3(
    ExpressionBuiltinRangeMixin, ChildrenHavingLowHighStepMixin, ExpressionBase
):
    kind = "EXPRESSION_BUILTIN_RANGE3"

    python_version_spec = "< 0x300"

    named_children = ("low", "high", "step")

    def __init__(self, low, high, step, source_ref):
        ChildrenHavingLowHighStepMixin.__init__(
            self,
            low=low,
            high=high,
            step=step,
        )

        ExpressionBase.__init__(self, source_ref)

    builtin_spec = BuiltinParameterSpecs.builtin_range_spec

    def computeExpression(self, trace_collection):
        low = self.subnode_low
        high = self.subnode_high
        step = self.subnode_step

        return self.computeBuiltinSpec(
            trace_collection=trace_collection, given_values=(low, high, step)
        )

    def getIterationLength(self):
        low = self.subnode_low
        high = self.subnode_high
        step = self.subnode_step

        low = low.getIntegerValue()

        if low is None:
            return None

        high = high.getIntegerValue()

        if high is None:
            return None

        step = step.getIntegerValue()

        if step is None:
            return None

        # Give up on this, will raise ValueError.
        if step == 0:
            return None

        if low < high:
            if step < 0:
                estimate = 0
            else:
                estimate = math.ceil(float(high - low) / step)
        else:
            if step > 0:
                estimate = 0
            else:
                estimate = math.ceil(float(high - low) / step)

        estimate = round(estimate)

        assert estimate >= 0

        return int(estimate)

    def canPredictIterationValues(self):
        return self.getIterationLength() is not None

    def getIterationHandle(self):
        low = self.subnode_low.getIntegerValue()
        if low is None:
            return None

        high = self.subnode_high.getIntegerValue()
        if high is None:
            return None

        step = self.subnode_step.getIntegerValue()
        if step is None:
            return None

        # Give up on this, will raise ValueError.
        if step == 0:
            return None

        return IterationHandleRange3(low, high, step, self.source_ref)

    def getIterationValue(self, element_index):
        low = self.subnode_low.getIntegerValue()

        if low is None:
            return None

        high = self.subnode_high.getIntegerValue()

        if high is None:
            return None

        step = self.subnode_step.getIntegerValue()

        result = low + step * element_index

        if result >= high:
            return None
        else:
            return makeConstantReplacementNode(
                constant=result, node=self, user_provided=False
            )

    def isKnownToBeIterable(self, count):
        return count is None or count == self.getIterationLength()


class ExpressionBuiltinXrangeMixin(object):
    """Mixin class for xrange nodes with 1/2/3 arguments."""

    # Mixins are required to slots
    __slots__ = ()

    builtin_spec = BuiltinParameterSpecs.builtin_xrange_spec

    @staticmethod
    def getTypeShape():
        return tshape_xrange

    def canPredictIterationValues(self):
        return self.getIterationLength() is not None

    def getTruthValue(self):
        length = self.getIterationLength()

        if length is None:
            return None
        else:
            return length > 0

    def mayHaveSideEffects(self):
        for child in self.getVisitableNodes():
            if child.mayHaveSideEffects():
                return True

            if child.getIntegerValue() is None:
                return True

        return False

    def mayRaiseException(self, exception_type):
        for child in self.getVisitableNodes():
            if child.mayRaiseException(exception_type):
                return True

            # TODO: Should take exception_type value into account here.
            if child.getIntegerValue() is None:
                return True

        step = self.subnode_step

        # A step of 0 will raise.
        if step is not None and step.getIntegerValue() == 0:
            return True

        return False

    def computeBuiltinSpec(self, trace_collection, given_values):
        assert self.builtin_spec is not None, self

        if not self.builtin_spec.isCompileTimeComputable(given_values):
            trace_collection.onExceptionRaiseExit(BaseException)

            # TODO: Raise exception known step 0.

            return self, None, None

        return trace_collection.getCompileTimeComputationResult(
            node=self,
            computation=lambda: self.builtin_spec.simulateCall(given_values),
            description="Built-in call to '%s' computed."
            % (self.builtin_spec.getName()),
        )

    def computeExpressionIter1(self, iter_node, trace_collection):
        # No exception will be raised on xrange iteration, but there is nothing to
        # lower for, virtual method: pylint: disable=no-self-use

        return iter_node, None, None


class ExpressionBuiltinXrange1(
    ExpressionBuiltinXrangeMixin, ChildHavingLowMixin, ExpressionBase
):
    kind = "EXPRESSION_BUILTIN_XRANGE1"

    named_children = ("low",)

    subnode_high = None
    subnode_step = None

    def __init__(self, low, source_ref):
        ChildHavingLowMixin.__init__(self, low=low)

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        low = self.subnode_low

        # TODO: Optimize this if self.subnode_low.getIntegerValue() is Not None
        return self.computeBuiltinSpec(
            trace_collection=trace_collection, given_values=(low,)
        )

    def getIterationLength(self):
        low = self.subnode_low.getIntegerValue()

        if low is None:
            return None

        return max(0, low)

    def getIterationValue(self, element_index):
        length = self.getIterationLength()

        if length is None:
            return None

        if element_index > length:
            return None

        # TODO: Make sure to cast element_index to what CPython will give, for
        # now a downcast will do.
        return makeConstantReplacementNode(
            constant=int(element_index), node=self, user_provided=False
        )


class ExpressionBuiltinXrange2(
    ExpressionBuiltinXrangeMixin, ChildrenHavingLowHighMixin, ExpressionBase
):
    kind = "EXPRESSION_BUILTIN_XRANGE2"

    named_children = ("low", "high")

    subnode_step = None

    def __init__(self, low, high, source_ref):
        ChildrenHavingLowHighMixin.__init__(
            self,
            low=low,
            high=high,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        low = self.subnode_low
        high = self.subnode_high

        return self.computeBuiltinSpec(
            trace_collection=trace_collection, given_values=(low, high)
        )

    def getIterationLength(self):
        low = self.subnode_low
        high = self.subnode_high

        low = low.getIntegerValue()

        if low is None:
            return None

        high = high.getIntegerValue()

        if high is None:
            return None

        return max(0, high - low)

    def getIterationValue(self, element_index):
        low = self.subnode_low
        high = self.subnode_high

        low = low.getIntegerValue()

        if low is None:
            return None

        high = high.getIntegerValue()

        if high is None:
            return None

        result = low + element_index

        if result >= high:
            return None
        else:
            return makeConstantReplacementNode(
                constant=result, node=self, user_provided=False
            )


class ExpressionBuiltinXrange3(
    ExpressionBuiltinXrangeMixin, ChildrenHavingLowHighStepMixin, ExpressionBase
):
    kind = "EXPRESSION_BUILTIN_XRANGE3"

    named_children = ("low", "high", "step")

    def __init__(self, low, high, step, source_ref):
        ChildrenHavingLowHighStepMixin.__init__(
            self,
            low=low,
            high=high,
            step=step,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        low = self.subnode_low
        high = self.subnode_high
        step = self.subnode_step

        return self.computeBuiltinSpec(
            trace_collection=trace_collection, given_values=(low, high, step)
        )

    def getIterationLength(self):
        low = self.subnode_low
        high = self.subnode_high
        step = self.subnode_step

        low = low.getIntegerValue()

        if low is None:
            return None

        high = high.getIntegerValue()

        if high is None:
            return None

        step = step.getIntegerValue()

        if step is None:
            return None

        # Give up on this, will raise ValueError.
        if step == 0:
            return None

        if low < high:
            if step < 0:
                estimate = 0
            else:
                estimate = math.ceil(float(high - low) / step)
        else:
            if step > 0:
                estimate = 0
            else:
                estimate = math.ceil(float(high - low) / step)

        estimate = round(estimate)

        assert estimate >= 0

        return int(estimate)

    def getIterationValue(self, element_index):
        low = self.subnode_low.getIntegerValue()

        if low is None:
            return None

        high = self.subnode_high.getIntegerValue()

        if high is None:
            return None

        step = self.subnode_step.getIntegerValue()

        result = low + step * element_index

        if result >= high:
            return None
        else:
            return makeConstantReplacementNode(
                constant=result, node=self, user_provided=False
            )


def makeExpressionBuiltinXrange(low, high, step, source_ref):
    if high is None:
        return ExpressionBuiltinXrange1(low=low, source_ref=source_ref)
    elif step is None:
        return ExpressionBuiltinXrange2(low=low, high=high, source_ref=source_ref)
    else:
        return ExpressionBuiltinXrange3(
            low=low, high=high, step=step, source_ref=source_ref
        )
