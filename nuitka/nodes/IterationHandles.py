#     Copyright 2022, Batakrishna Sahu, mailto:<Batakrishna.Sahu@suiit.ac.in>
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
""" Node for Iteration Handles.

"""

import math
from abc import abstractmethod

from nuitka.__past__ import getMetaClassBase, xrange


class IterationHandleBase(getMetaClassBase("IterationHandle")):
    """Base class for Iteration Handles."""

    @abstractmethod
    def getNextValueExpression(self):
        """Abstract method to get next iteration value."""

    @abstractmethod
    def getIterationValueWithIndex(self, value_index):
        # TODO: Have one doc string, and it applies to all derived methods.
        """Abstract method for random access of the expression."""

    def getNextValueTruth(self):
        """Returns truth value of the next expression or Stops the
        iteration handle if end is reached.
        """
        iteration_value = self.getNextValueExpression()
        if iteration_value is None:
            return StopIteration
        return iteration_value.getTruthValue()

    def getAllElementTruthValue(self):
        """Returns truth value for 'all' on 'lists'. It returns
        True: if all the elements of the list are True,
        False: if any element in the list is False,
        None: if number of elements in the list is greater than
        256 or any element is Unknown.
        """
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
    """Base class for the Constant Iteration Handles.

    Attributes
    ----------
    constant_node : node_object
        Instance of the calling node.

    Methods
    -------
    __repr__()
        Prints representation of the ConstantIterationHandleBase
        and it's children objects
    getNextValueExpression()
        Returns the next iteration value
    getNextValueTruth()
        Returns the boolean value of the next handle
    """

    def __init__(self, constant_node):
        assert constant_node.isIterableConstant()

        self.constant_node = constant_node
        self.iter = iter(self.constant_node.constant)

    def __repr__(self):
        return "<%s of %r>" % (self.__class__.__name__, self.constant_node)

    def getNextValueExpression(self):
        # TODO: Better doc string.
        """Returns truth value of the next expression or Stops the iteration handle
        and returns None if end is reached.
        """
        try:
            from .ConstantRefNodes import makeConstantRefNode

            return makeConstantRefNode(
                constant=next(self.iter), source_ref=self.constant_node.source_ref
            )
        except StopIteration:
            return None

    def getNextValueTruth(self):
        """Return the truth value of the next iteration value or StopIteration."""
        try:
            iteration_value = next(self.iter)
        except StopIteration:
            return StopIteration
        return bool(iteration_value)

    def getIterationValueWithIndex(self, value_index):
        return None


class ConstantIndexableIterationHandle(ConstantIterationHandleBase):
    """Class for the constants that are indexable.

    Attributes
    ----------
    constant_node : node_object
        Instance of the calling node.

    Methods
    -------
    getIterationValueWithIndex(value_index)
        Sequential access of the constants
    """

    def __init__(self, constant_node):
        ConstantIterationHandleBase.__init__(self, constant_node)

    def getIterationValueWithIndex(self, value_index):
        """Tries to return constant value at the given index.

        Parameters
        ----------
        value_index : int
            Index value of the element to be returned
        """
        try:
            from .ConstantRefNodes import makeConstantRefNode

            return makeConstantRefNode(
                constant=self.constant_node.constant[value_index],
                source_ref=self.constant_node.source_ref,
            )
        except IndexError:
            return None


class ConstantTupleIterationHandle(ConstantIndexableIterationHandle):
    pass


class ConstantListIterationHandle(ConstantIndexableIterationHandle):
    pass


class ConstantStrIterationHandle(ConstantIndexableIterationHandle):
    pass


class ConstantUnicodeIterationHandle(ConstantIndexableIterationHandle):
    pass


class ConstantBytesIterationHandle(ConstantIndexableIterationHandle):
    pass


class ConstantBytearrayIterationHandle(ConstantIndexableIterationHandle):
    pass


class ConstantRangeIterationHandle(ConstantIndexableIterationHandle):
    pass


class ConstantSetAndDictIterationHandleBase(ConstantIterationHandleBase):
    """Class for the set and dictionary constants."""

    def __init__(self, constant_node):
        ConstantIterationHandleBase.__init__(self, constant_node)


class ConstantSetIterationHandle(ConstantSetAndDictIterationHandleBase):
    pass


class ConstantFrozensetIterationHandle(ConstantSetAndDictIterationHandleBase):
    pass


class ConstantDictIterationHandle(ConstantSetAndDictIterationHandleBase):
    pass


class ListAndTupleContainerMakingIterationHandle(IterationHandleBase):
    """Class for list and tuple container making expression

    Attributes
    ----------
    constant_node : node_object
        Instance of the calling node.

    Methods
    -------
    __repr__()
        Prints representation of the ListAndTupleContainerMakingIterationHandle
        object
    getNextValueExpression()
        Returns the next iteration value
    getNextValueTruth()
        Returns the boolean value of the next handle
    getIterationValueWithIndex(value_index)
        Sequential access of the expression
    """

    def __init__(self, elements):
        self.elements = elements
        self.iter = iter(self.elements)

    def __repr__(self):
        return "<%s of %r>" % (self.__class__.__name__, self.elements)

    def getNextValueExpression(self):
        """Return the next iteration value or StopIteration exception
        if the iteration has reached the end
        """
        try:
            return next(self.iter)
        except StopIteration:
            return None

    def getIterationValueWithIndex(self, value_index):
        """Tries to return constant value at the given index.

        Parameters
        ----------
        value_index : int
            Index value of the element to be returned
        """
        try:
            return self.elements[value_index]
        except IndexError:
            return None


class RangeIterationHandleBase(IterationHandleBase):
    """Iteration handle class for range nodes

    Attributes
    ----------
    low : int
        Optional. An integer number specifying at which position to start. Default is 0
    high : int
        Optional. An integer number specifying at which position to end.
    step : int
        Optional. An integer number specifying the incrementation. Default is 1
    """

    step = 1

    def __init__(self, low_value, range_value, source_ref):
        self.low = low_value
        self.iter = iter(range_value)
        self.source_ref = source_ref

    def getNextValueExpression(self):
        """Return the next iteration value or StopIteration exception
        if the iteration has reached the end
        """
        try:
            from .ConstantRefNodes import makeConstantRefNode

            return makeConstantRefNode(
                constant=next(self.iter), source_ref=self.source_ref
            )
        except StopIteration:
            return None

    @abstractmethod
    def getIterationLength(self):
        """return length"""

    def getIterationValueWithIndex(self, value_index):
        """Tries to return constant value at the given index.

        Parameters
        ----------
        value_index : int
            Index value of the element to be returned
        """
        if value_index < self.getIterationLength():
            from .ConstantRefNodes import makeConstantRefNode

            return makeConstantRefNode(
                constant=value_index * self.step + self.low, source_ref=self.source_ref
            )
        else:
            return IndexError

    def getNextValueTruth(self):
        """Return the boolean value of the next iteration handle."""
        try:
            iteration_value = next(self.iter)
        except StopIteration:
            return StopIteration
        return bool(iteration_value)

    @staticmethod
    def getAllElementTruthValue():
        return True


class IterationHandleRange1(RangeIterationHandleBase):
    """Iteration handle for range(low,)"""

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
    """Iteration handle for ranges(low, high)"""

    def __init__(self, low_value, high_value, source_ref):
        RangeIterationHandleBase.__init__(
            self, low_value, xrange(low_value, high_value), source_ref
        )

        self.high = high_value

    def getIterationLength(self):
        return max(0, self.high - self.low)


class IterationHandleRange3(RangeIterationHandleBase):
    """Iteration handle for ranges(low, high, step)"""

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
