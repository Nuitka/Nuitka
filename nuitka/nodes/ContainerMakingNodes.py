#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .NodeBases import (
    ExpressionChildrenHavingBase,
    SideEffectsFromChildrenMixin
)
from .NodeMakingHelpers import (
    getComputationResult,
    makeStatementOnlyNodesFromExpressions,
    wrapExpressionWithSideEffects
)


class ExpressionMakeSequenceBase(SideEffectsFromChildrenMixin,
                                 ExpressionChildrenHavingBase):
    named_children = (
        "elements",
    )

    def __init__(self, sequence_kind, elements, source_ref):
        assert sequence_kind in ("TUPLE", "LIST", "SET"), sequence_kind

        for element in elements:
            assert element.isExpression(), element

        self.sequence_kind = sequence_kind.lower()

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "elements" : tuple(elements),
            },
            source_ref = source_ref

        )

    def isExpressionMakeSequence(self):
        return True

    def getSequenceKind(self):
        return self.sequence_kind

    getElements = ExpressionChildrenHavingBase.childGetter("elements")

    def getSimulator(self):
        # Abstract method, pylint: disable=R0201
        return None

    def computeExpression(self, constraint_collection):
        elements = self.getElements()

        for count, element in enumerate(elements):
            if element.willRaiseException(BaseException):
                result = wrapExpressionWithSideEffects(
                    side_effects = elements[:count],
                    new_node     = element,
                    old_node     = self
                )

                return result, "new_raise", "Sequence creation raises exception"

        # TODO: CompileTimeConstant should be good enough.
        for element in elements:
            if not element.isExpressionConstantRef():
                return self, None, None

        simulator = self.getSimulator()
        assert simulator is not None

        # The simulator is in fact callable if not None, pylint: disable=E1102
        return getComputationResult(
            node        = self,
            computation = lambda : simulator(
                element.getConstant()
                for element in
                self.getElements()
            ),
            description = "%s with constant arguments." % simulator.__name__.title()
        )

    def mayHaveSideEffectsBool(self):
        return False

    def isKnownToBeIterable(self, count):
        return count is None or count == len(self.getElements())

    def getIterationValue(self, count):
        return self.getElements()[count]

    @staticmethod
    def canPredictIterationValues():
        return True

    def getIterationValues(self):
        return self.getElements()

    def getTruthValue(self):
        return self.getIterationLength() > 0

    def mayRaiseException(self, exception_type):
        for element in self.getElements():
            if element.mayRaiseException(exception_type):
                return True

        return False

    def mayBeNone(self):
        return False

    def computeExpressionDrop(self, statement, constraint_collection):
        result = makeStatementOnlyNodesFromExpressions(
            expressions = self.getElements()
        )

        return result, "new_statements", """\
Removed sequence creation for unused sequence."""


class ExpressionMakeTuple(ExpressionMakeSequenceBase):
    kind = "EXPRESSION_MAKE_TUPLE"

    def __init__(self, elements, source_ref):
        ExpressionMakeSequenceBase.__init__(
            self,
            sequence_kind = "TUPLE",
            elements      = elements,
            source_ref    = source_ref
        )

    def getSimulator(self):
        return tuple

    def getIterationLength(self):
        return len(self.getElements())


class ExpressionMakeList(ExpressionMakeSequenceBase):
    kind = "EXPRESSION_MAKE_LIST"

    def __init__(self, elements, source_ref):
        ExpressionMakeSequenceBase.__init__(
            self,
            sequence_kind = "LIST",
            elements      = elements,
            source_ref    = source_ref
        )

    def getSimulator(self):
        return list

    def getIterationLength(self):
        return len(self.getElements())

    def computeExpressionIter1(self, iter_node, constraint_collection):
        result = ExpressionMakeTuple(
            elements   = self.getElements(),
            source_ref = self.source_ref
        )

        self.replaceWith(result)

        return iter_node, "new_expression", """\
Iteration over list reduced to tuple."""


class ExpressionMakeSet(ExpressionMakeSequenceBase):
    kind = "EXPRESSION_MAKE_SET"

    def __init__(self, elements, source_ref):
        ExpressionMakeSequenceBase.__init__(
            self,
            sequence_kind = "SET",
            elements      = elements,
            source_ref    = source_ref
        )

    def getSimulator(self):
        return set

    def getIterationLength(self):
        element_count = len(self.getElements())

        # Hashing may consume elements.
        if element_count >= 2:
            return None
        else:
            return element_count

    def getIterationMinLength(self):
        element_count = len(self.getElements())

        if element_count == 0:
            return 0
        else:
            return 1

    def getIterationMaxLength(self):
        return len(self.getElements())

    def mayRaiseException(self, exception_type):
        for element in self.getElements():
            if not element.isKnownToBeHashable():
                return True

            if element.mayRaiseException(exception_type):
                return True

        return False

    def computeExpressionIter1(self, iter_node, constraint_collection):
        result = ExpressionMakeTuple(
            elements   = self.getElements(),
            source_ref = self.source_ref
        )

        self.replaceWith(result)

        return iter_node, "new_expression", """\
Iteration over set reduced to tuple."""
