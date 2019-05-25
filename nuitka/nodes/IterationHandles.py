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

from nuitka.__past__ import getMetaClassBase


class IterationHandleBase(getMetaClassBase("IterationHandle")):
    """Base class for Iteration Handles."""

    @abstractmethod
    def __repr__(self):
        """Returns a printable representation of the IterationHandle
        and it's children object."""
        pass

    @abstractmethod
    def getNextValueExpression(self):
        """Abstract method to get next iteration value."""
        pass

    @abstractmethod
    def getIterationValueWithIndex(self, value_index):
        """Abstract method for random access of the expression."""
        pass

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
        """Return the next iteration value or StopIteration exception
        if the iteration has reached the end
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

    def __init__(self, constant_node):
        assert type(constant_node) in (list, tuple)
        self.constant_node = constant_node
        self.iter = iter(constant_node)

    def __repr__(self):
        return "<%s of %r>" % (self.__class__.__name__, self.constant_node)

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
            return self.constant_node[value_index]
        except IndexError:
            return None

    def getNextValueTruth(self):
        """Return the boolean value of the next iteration handle."""
        try:
            iteration_value = next(self.iter)
        except StopIteration:
            return StopIteration
        return bool(iteration_value)
