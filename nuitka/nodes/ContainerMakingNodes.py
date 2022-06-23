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
""" Nodes that build containers.

"""

import functools
from abc import abstractmethod

from nuitka.PythonVersions import needsSetLiteralReverseInsertion

from .ConstantRefNodes import (
    ExpressionConstantListEmptyRef,
    ExpressionConstantSetEmptyRef,
    ExpressionConstantTupleEmptyRef,
    makeConstantRefNode,
)
from .ExpressionBases import ExpressionChildTupleHavingBase
from .ExpressionShapeMixins import (
    ExpressionListShapeExactMixin,
    ExpressionSetShapeExactMixin,
    ExpressionTupleShapeExactMixin,
)
from .IterationHandles import ListAndTupleContainerMakingIterationHandle
from .NodeBases import SideEffectsFromChildrenMixin
from .NodeMakingHelpers import (
    makeStatementOnlyNodesFromExpressions,
    wrapExpressionWithSideEffects,
)


class ExpressionMakeSequenceBase(
    SideEffectsFromChildrenMixin, ExpressionChildTupleHavingBase
):
    __slots__ = ("sequence_kind",)

    named_child = "elements"

    def __init__(self, sequence_kind, elements, source_ref):
        assert elements

        for element in elements:
            assert element.isExpression(), element

        self.sequence_kind = sequence_kind.lower()

        ExpressionChildTupleHavingBase.__init__(
            self, value=tuple(elements), source_ref=source_ref
        )

    @staticmethod
    def isExpressionMakeSequence():
        return True

    @abstractmethod
    def getSimulator(self):
        """The simulator for the container making, for overload."""

    def computeExpression(self, trace_collection):
        elements = self.subnode_elements

        are_constants = True

        for count, element in enumerate(elements):
            if element.willRaiseException(BaseException):
                result = wrapExpressionWithSideEffects(
                    side_effects=elements[:count], new_node=element, old_node=self
                )

                return result, "new_raise", "Sequence creation raises exception"

            if are_constants and not element.isCompileTimeConstant():
                are_constants = False

        if are_constants is False:
            return self, None, None

        simulator = self.getSimulator()
        assert simulator is not None

        return trace_collection.getCompileTimeComputationResult(
            node=self,
            computation=lambda: simulator(
                element.getCompileTimeConstant() for element in elements
            ),
            description="%s with constant arguments." % simulator.__name__.capitalize(),
            user_provided=True,
        )

    def isKnownToBeIterable(self, count):
        return count is None or count == len(self.subnode_elements)

    def isKnownToBeIterableAtMin(self, count):
        return count <= len(self.subnode_elements)

    def getIterationValue(self, count):
        return self.subnode_elements[count]

    def getIterationValueRange(self, start, stop):
        return self.subnode_elements[start:stop]

    @staticmethod
    def canPredictIterationValues():
        return True

    def getIterationValues(self):
        return self.subnode_elements

    def getIterationHandle(self):
        return ListAndTupleContainerMakingIterationHandle(self.subnode_elements)

    @staticmethod
    def getTruthValue():
        return True

    def mayRaiseException(self, exception_type):
        for element in self.subnode_elements:
            if element.mayRaiseException(exception_type):
                return True

        return False

    def computeExpressionDrop(self, statement, trace_collection):
        result = makeStatementOnlyNodesFromExpressions(
            expressions=self.subnode_elements
        )

        del self.parent

        return (
            result,
            "new_statements",
            """\
Removed sequence creation for unused sequence.""",
        )

    def onContentEscapes(self, trace_collection):
        for element in self.subnode_elements:
            element.onContentEscapes(trace_collection)


def makeExpressionMakeTuple(elements, source_ref):
    if elements:
        return ExpressionMakeTuple(elements, source_ref)
    else:
        # TODO: Get rid of user provided for empty tuple refs, makes no sense.
        return ExpressionConstantTupleEmptyRef(
            user_provided=False, source_ref=source_ref
        )


def makeExpressionMakeTupleOrConstant(elements, user_provided, source_ref):
    for element in elements:
        # TODO: Compile time constant ought to be the criterion.
        if not element.isExpressionConstantRef():
            result = makeExpressionMakeTuple(elements, source_ref)
            break
    else:
        result = makeConstantRefNode(
            constant=tuple(element.getCompileTimeConstant() for element in elements),
            user_provided=user_provided,
            source_ref=source_ref,
        )

    if elements:
        result.setCompatibleSourceReference(
            source_ref=elements[-1].getCompatibleSourceReference()
        )

    return result


class ExpressionMakeTuple(ExpressionTupleShapeExactMixin, ExpressionMakeSequenceBase):
    kind = "EXPRESSION_MAKE_TUPLE"

    def __init__(self, elements, source_ref):
        ExpressionMakeSequenceBase.__init__(
            self, sequence_kind="TUPLE", elements=elements, source_ref=source_ref
        )

    @staticmethod
    def getSimulator():
        return tuple

    def getIterationLength(self):
        return len(self.subnode_elements)


def makeExpressionMakeList(elements, source_ref):
    if elements:
        return ExpressionMakeList(elements, source_ref)
    else:
        # TODO: Get rid of user provided for empty list refs, makes no sense.
        return ExpressionConstantListEmptyRef(
            user_provided=False, source_ref=source_ref
        )


def makeExpressionMakeListOrConstant(elements, user_provided, source_ref):
    assert type(elements) is list

    for element in elements:
        # TODO: Compile time constant ought to be the criterion.
        if not element.isExpressionConstantRef():
            result = makeExpressionMakeList(elements, source_ref)
            break
    else:
        result = makeConstantRefNode(
            constant=[element.getCompileTimeConstant() for element in elements],
            user_provided=user_provided,
            source_ref=source_ref,
        )

    if elements:
        result.setCompatibleSourceReference(
            source_ref=elements[-1].getCompatibleSourceReference()
        )

    return result


class ExpressionMakeList(ExpressionListShapeExactMixin, ExpressionMakeSequenceBase):
    kind = "EXPRESSION_MAKE_LIST"

    def __init__(self, elements, source_ref):
        ExpressionMakeSequenceBase.__init__(
            self, sequence_kind="LIST", elements=elements, source_ref=source_ref
        )

    @staticmethod
    def getSimulator():
        return list

    def getIterationLength(self):
        return len(self.subnode_elements)

    def computeExpressionIter1(self, iter_node, trace_collection):
        result = ExpressionMakeTuple(
            elements=self.subnode_elements, source_ref=self.source_ref
        )

        self.parent.replaceChild(self, result)
        del self.parent

        return (
            iter_node,
            "new_expression",
            """\
Iteration over list lowered to iteration over tuple.""",
        )


class ExpressionMakeSet(ExpressionSetShapeExactMixin, ExpressionMakeSequenceBase):
    kind = "EXPRESSION_MAKE_SET"

    def __init__(self, elements, source_ref):
        ExpressionMakeSequenceBase.__init__(
            self, sequence_kind="SET", elements=elements, source_ref=source_ref
        )

    @staticmethod
    def getSimulator():
        return set

    def getIterationLength(self):
        element_count = len(self.subnode_elements)

        # Hashing and equality may consume elements of the produced set.
        if element_count >= 2:
            return None
        else:
            return element_count

    @staticmethod
    def getIterationMinLength():
        # Hashing and equality may consume elements of the produced set.
        return 1

    def computeExpression(self, trace_collection):
        # For sets, we need to consider

        elements = self.subnode_elements

        are_constants = True
        are_hashable = True

        for count, element in enumerate(elements):
            if element.willRaiseException(BaseException):
                result = wrapExpressionWithSideEffects(
                    side_effects=elements[:count], new_node=element, old_node=self
                )

                return result, "new_raise", "Sequence creation raises exception"

            if are_constants and not element.isCompileTimeConstant():
                are_constants = False

            if are_hashable and not element.isKnownToBeHashable():
                are_hashable = False

            if not are_hashable and not are_constants:
                break

        if not are_constants:
            if not are_hashable:
                trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        simulator = self.getSimulator()
        assert simulator is not None

        return trace_collection.getCompileTimeComputationResult(
            node=self,
            computation=lambda: simulator(
                element.getCompileTimeConstant() for element in elements
            ),
            description="%s with constant arguments." % simulator.__name__.capitalize(),
            user_provided=True,
        )

    def mayRaiseException(self, exception_type):
        for element in self.subnode_elements:
            if not element.isKnownToBeHashable():
                return True

            if element.mayRaiseException(exception_type):
                return True

        return False

    def computeExpressionIter1(self, iter_node, trace_collection):
        result = ExpressionMakeTuple(
            elements=self.subnode_elements, source_ref=self.source_ref
        )

        self.parent.replaceChild(self, result)
        del self.parent

        return (
            iter_node,
            "new_expression",
            """\
Iteration over set lowered to iteration over tuple.""",
        )


needs_set_literal_reverse = needsSetLiteralReverseInsertion()


def makeExpressionMakeSetLiteral(elements, source_ref):
    if elements:
        if needs_set_literal_reverse:
            return ExpressionMakeSetLiteral(elements, source_ref)
        else:
            return ExpressionMakeSet(elements, source_ref)
    else:
        # TODO: Get rid of user provided for empty set refs, makes no sense.
        return ExpressionConstantSetEmptyRef(user_provided=False, source_ref=source_ref)


@functools.wraps(set)
def reversed_set(value):
    return set(reversed(tuple(value)))


def makeExpressionMakeSetLiteralOrConstant(elements, user_provided, source_ref):
    for element in elements:
        # TODO: Compile time constant ought to be the criterion.
        if not element.isExpressionConstantRef():
            result = makeExpressionMakeSetLiteral(elements, source_ref)
            break
    else:
        # Need to reverse now if needed.
        if needs_set_literal_reverse:
            elements = tuple(reversed(elements))

        result = makeConstantRefNode(
            constant=set(element.getCompileTimeConstant() for element in elements),
            user_provided=user_provided,
            source_ref=source_ref,
        )

    if elements:
        result.setCompatibleSourceReference(
            source_ref=elements[-1].getCompatibleSourceReference()
        )

    return result


class ExpressionMakeSetLiteral(ExpressionMakeSet):
    kind = "EXPRESSION_MAKE_SET_LITERAL"

    @staticmethod
    def getSimulator():
        return reversed_set
