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
    @abstractmethod
    def getNextValueExpression(self):
        pass

    @abstractmethod
    def getIterationValueWithIndex(self, value_index):
        pass

    def getNextValueTruth(self):
        iteration_value = self.getNextValueExpression()
        if iteration_value is None:
            return StopIteration
        return iteration_value.getTruthValue()


class ConstantIterationHandleBase(IterationHandleBase):
    def __init__(self, constant_node):
        assert constant_node.isIterableConstant()
        self.constant = constant_node.constant
        self.constant_node = constant_node
        self.iter = iter(self.constant)

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
    def __init__(self, constant_node):
        ConstantIterationHandleBase.__init__(self, constant_node)
        assert type(self.constant) not in (set, dict)

    def getIterationValueWithIndex(self, value_index):
        try:
            from .ConstantRefNodes import makeConstantRefNode

            return makeConstantRefNode(
                constant=self.constant[value_index],
                source_ref=self.constant_node.source_ref,
            )
        except IndexError:
            return None


class ConstantSetAndDictIterationHandle(ConstantIterationHandleBase):
    def __init__(self, constant_node):
        ConstantIterationHandleBase.__init__(self, constant_node)
        assert type(self.constant) in (set, dict)
