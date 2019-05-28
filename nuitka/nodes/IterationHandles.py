#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

from abc import abstractmethod

from nuitka.__past__ import (  # pylint: disable=I0021,redefined-builtin
    getMetaClassBase,
    xrange,
)


class IterationHandleBase(getMetaClassBase("IterationHandle")):
    """Base class for Iteration Handles."""

    @abstractmethod
    def __repr__(self):
        """Returns a printable representation of the IterationHandle
        and it's children object."""

    @abstractmethod
    def getNextValueExpression(self):
        """Abstract method to get next iteration value."""

    @abstractmethod
    def getIterationValueWithIndex(self, value_index):
        """Abstract method for random access of the expression."""

    def getNextValueTruth(self):
        """Returns truth value of the next expression or Stops the
        iteration handle if end is reached.
        """
        iteration_value = self.getNextValueExpression()
        if iteration_value is None:
            return StopIteration
        return iteration_value.getTruthValue()


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
        self.constant = constant_node.constant
        self.constant_node = constant_node
        self.iter = iter(self.constant)

    def __repr__(self):
        return "<%s of %r>" % (self.__class__.__name__, self.constant_node)

    def getNextValueExpression(self):
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
        """Return the boolean value of the next iteration handle."""
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
        assert type(self.constant) not in (set, dict)

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
                constant=self.constant[value_index],
                source_ref=self.constant_node.source_ref,
            )
        except IndexError:
            return None


class ConstantSetAndDictIterationHandle(ConstantIterationHandleBase):
    """Class for the set and dictionary constants.
    """

    def __init__(self, constant_node):
        ConstantIterationHandleBase.__init__(self, constant_node)
        assert type(self.constant) in (set, dict)


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

    def __init__(self, constant_list):
        assert type(constant_list) in (list, tuple)
        self.constant_list = constant_list
        self.iter = iter(self.constant_list)

    def __repr__(self):
        return "<%s of %r>" % (self.__class__.__name__, self.constant_list)

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
            return self.constant_list[value_index]
        except IndexError:
            return None


class ConstantRangeIterationHandleBase(IterationHandleBase):
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

    def __init__(self, constant_value):
        self.constant_value = constant_value

    def __repr__(self):
        return "<%s of %r>" % (self.__class__.__name__, self.constant_value.getLow())

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
        if value_index < self.constant_value.getIterationLength():
            return value_index
        else:
            return IndexError

    def getNextValueTruth(self):
        """Return the boolean value of the next iteration handle."""
        try:
            iteration_value = next(self.iter)
        except StopIteration:
            return StopIteration
        return bool(iteration_value)


class ConstantIterationHandleRange1(ConstantRangeIterationHandleBase):
    """Iteration handle for range(low,)"""

    def __init__(self, constant_value):
        ConstantRangeIterationHandleBase.__init__(self, constant_value)
        assert self.constant_value.isExpressionBuiltinRange1()
        if self.constant_value.getLow().getIntegerValue() is not None:
            self.low = self.constant_value.getLow().getIntegerValue()
        self.constant = xrange(self.low)
        self.iter = iter(self.constant)


class ConstantIterationHandleRange2(ConstantRangeIterationHandleBase):
    """Iteration handle for ranges(low, high)"""

    def __init__(self, constant_value):
        ConstantRangeIterationHandleBase.__init__(self, constant_value)
        assert self.constant_value.isExpressionBuiltinRange2()
        if self.constant_value.getLow().getIntegerValue() is not None:
            self.low = self.constant_value.getLow().getIntegerValue()
        if self.constant_value.getHigh().getIntegerValue() is not None:
            self.high = self.constant_value.getHigh().getIntegerValue()
        self.constant = xrange(self.low, self.high)
        self.iter = iter(self.constant)


class ConstantIterationHandleRange3(ConstantRangeIterationHandleBase):
    """Iteration handle for ranges(low, high, step)"""

    def __init__(self, constant_value):
        ConstantRangeIterationHandleBase.__init__(self, constant_value)
        assert self.constant_value.isExpressionBuiltinRange3()
        if self.constant_value.getLow().getIntegerValue() is not None:
            self.low = self.constant_value.getLow().getIntegerValue()
        if self.constant_value.getHigh().getIntegerValue() is not None:
            self.high = self.constant_value.getHigh().getIntegerValue()
        if self.constant_value.getStep().getIntegerValue() is not None:
            self.step = self.constant_value.getStep().getIntegerValue()
        self.constant = xrange(self.low, self.high, self.step)
        self.iter = iter(self.constant)

    def getIterationValueWithIndex(self, value_index):
        """Tries to return constant value at the given index.

        Parameters
        ----------
        value_index : int
            Index value of the element to be returned
        """
        index_value = value_index * self.step
        if index_value < self.constant_value.getIterationLength():
            return index_value
        else:
            return IndexError
