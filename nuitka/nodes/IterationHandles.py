#     Copyright 2020, Batakrishna Sahu, mailto:<Batakrishna.Sahu@suiit.ac.in> find license text at end of file


"""Iteration handles for compile-time sequence and range simulation."""

import math
from abc import abstractmethod

from nuitka.__past__ import xrange
from nuitka.utils.SlotMetaClasses import getMetaClassBase


class IterationHandleBase(getMetaClassBase("IterationHandle", require_slots=True)):
    __slots__ = ()

    @abstractmethod
    def getNextValueExpression(self):
        """Return the next iteration value expression, or 'None' when exhausted."""

    @abstractmethod
    def getIterationValueWithIndex(self, value_index):
        """Return the element expression at 'value_index', or 'None' if unavailable."""

    def getNextValueTruth(self):
        """Return the truth value of the next element, or 'StopIteration' when exhausted."""
        iteration_value = self.getNextValueExpression()
        if iteration_value is None:
            return StopIteration
        return iteration_value.getTruthValue()

    def getAllElementTruthValue(self):
        """Return tri-state 'all()' truth value across up to 256 elements, or 'None' if unknown."""
        all_true = True
        count = 0
        while True:
            truth_value = self.getNextValueTruth()
            if truth_value is StopIteration:
                break

            if count > 256:
                return None

            if truth_value is False:
                return False

            if truth_value is None:
                all_true = None

            count += 1

        return all_true


class ConstantIterationHandleBase(IterationHandleBase):
    __slots__ = (
        "constant_node",
        "iter",
    )

    def __init__(self, constant_node):
        assert constant_node.isIterableConstant()

        self.constant_node = constant_node
        self.iter = iter(self.constant_node.constant)

    def __repr__(self):
        return "<%s of %r>" % (self.__class__.__name__, self.constant_node)

    def getNextValueExpression(self):
        try:
            from .ConstantRefNodes import makeConstantRefNode

            return makeConstantRefNode(
                constant=next(self.iter), source_ref=self.constant_node.source_ref
            )
        except StopIteration:
            return None

    def getNextValueTruth(self):
        try:
            iteration_value = next(self.iter)
        except StopIteration:
            return StopIteration
        return bool(iteration_value)

    def getIterationValueWithIndex(self, value_index):
        return None


class ConstantIndexableIterationHandle(ConstantIterationHandleBase):
    __slots__ = ()

    def getIterationValueWithIndex(self, value_index):
        try:
            from .ConstantRefNodes import makeConstantRefNode

            return makeConstantRefNode(
                constant=self.constant_node.constant[value_index],
                source_ref=self.constant_node.source_ref,
            )
        except IndexError:
            return None


class ConstantTupleIterationHandle(ConstantIndexableIterationHandle):
    __slots__ = ()


class ConstantListIterationHandle(ConstantIndexableIterationHandle):
    __slots__ = ()


class ConstantStrIterationHandle(ConstantIndexableIterationHandle):
    __slots__ = ()


class ConstantUnicodeIterationHandle(ConstantIndexableIterationHandle):
    __slots__ = ()


class ConstantBytesIterationHandle(ConstantIndexableIterationHandle):
    __slots__ = ()


class ConstantBytearrayIterationHandle(ConstantIndexableIterationHandle):
    __slots__ = ()


class ConstantRangeIterationHandle(ConstantIndexableIterationHandle):
    __slots__ = ()


class ConstantSetAndDictIterationHandleBase(ConstantIterationHandleBase):
    __slots__ = ()


class ConstantSetIterationHandle(ConstantSetAndDictIterationHandleBase):
    __slots__ = ()


class ConstantFrozensetIterationHandle(ConstantSetAndDictIterationHandleBase):
    __slots__ = ()


class ConstantFrozendictIterationHandle(ConstantSetAndDictIterationHandleBase):
    __slots__ = ()


class ConstantDictIterationHandle(ConstantSetAndDictIterationHandleBase):
    __slots__ = ()


class ListAndTupleContainerMakingIterationHandle(IterationHandleBase):
    __slots__ = ("elements", "iter")

    def __init__(self, elements):
        self.elements = elements
        self.iter = iter(self.elements)

    def __repr__(self):
        return "<%s of %r>" % (self.__class__.__name__, self.elements)

    def getNextValueExpression(self):
        try:
            return next(self.iter)
        except StopIteration:
            return None

    def getIterationValueWithIndex(self, value_index):
        try:
            return self.elements[value_index]
        except IndexError:
            return None


class RangeIterationHandleBase(IterationHandleBase):
    step = 1

    __slots__ = ("low", "iter", "source_ref")

    def __init__(self, low_value, range_value, source_ref):
        self.low = low_value
        self.iter = iter(range_value)
        self.source_ref = source_ref

    def getNextValueExpression(self):
        try:
            from .ConstantRefNodes import makeConstantRefNode

            return makeConstantRefNode(
                constant=next(self.iter), source_ref=self.source_ref
            )
        except StopIteration:
            return None

    @abstractmethod
    def getIterationLength(self):
        pass

    def getIterationValueWithIndex(self, value_index):
        if value_index < self.getIterationLength():
            from .ConstantRefNodes import makeConstantRefNode

            return makeConstantRefNode(
                constant=value_index * self.step + self.low, source_ref=self.source_ref
            )
        else:
            return IndexError

    def getNextValueTruth(self):
        try:
            iteration_value = next(self.iter)
        except StopIteration:
            return StopIteration
        return bool(iteration_value)

    @staticmethod
    def getAllElementTruthValue():
        return True


class IterationHandleRange1(RangeIterationHandleBase):
    __slots__ = ()

    def __init__(self, low_value, source_ref):
        RangeIterationHandleBase.__init__(
            self, low_value, xrange(low_value), source_ref
        )

    def getIterationLength(self):
        return max(0, self.low)

    @staticmethod
    def getAllElementTruthValue():
        return False


class IterationHandleRange2(RangeIterationHandleBase):
    __slots__ = ("high",)

    def __init__(self, low_value, high_value, source_ref):
        RangeIterationHandleBase.__init__(
            self, low_value, xrange(low_value, high_value), source_ref
        )

        self.high = high_value

    def getIterationLength(self):
        return max(0, self.high - self.low)


class IterationHandleRange3(RangeIterationHandleBase):
    __slots__ = (
        "high",
        "step",
    )

    def __init__(self, low_value, high_value, step_value, source_ref):
        RangeIterationHandleBase.__init__(
            self, low_value, xrange(low_value, high_value, step_value), source_ref
        )
        self.high = high_value
        self.step = step_value

    def getIterationLength(self):
        if self.low < self.high:
            if self.step < 0:
                estimate = 0
            else:
                estimate = math.ceil(float(self.high - self.low) / self.step)
        else:
            if self.step > 0:
                estimate = 0
            else:
                estimate = math.ceil(float(self.high - self.low) / self.step)

        assert estimate >= 0

        return int(estimate)


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
