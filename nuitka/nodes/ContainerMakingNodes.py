#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka import Constants

class ExpressionMakeSequenceBase(SideEffectsFromChildrenMixin,
                                ExpressionChildrenHavingBase):
    named_children = ("elements",)

    def __init__(self, sequence_kind, elements, source_ref):
        assert sequence_kind in ( "TUPLE", "LIST", "SET" ), sequence_kind

        for element in elements:
            assert element.isExpression(), element

        self.sequence_kind = sequence_kind.lower()

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "elements" : tuple( elements ),
            },
            source_ref = source_ref

        )

    def isExpressionMakeSequence(self):
        return True

    def getSequenceKind(self):
        return self.sequence_kind

    getElements = ExpressionChildrenHavingBase.childGetter( "elements" )

    def getSimulator(self):
        # Abstract method, pylint: disable=R0201,W0613
        return None

    def computeExpression(self, constraint_collection):
        # Children can tell all we need to know, pylint: disable=W0613

        elements = self.getElements()

        for count, element in enumerate( elements ):
            if element.willRaiseException( BaseException ):
                from .NodeMakingHelpers import wrapExpressionWithSideEffects

                result = wrapExpressionWithSideEffects(
                    side_effects = elements[ : count ],
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

        from .NodeMakingHelpers import getComputationResult

        # The simulator is in fact callable if not None, pylint: disable=E1102
        return getComputationResult(
            node        = self,
            computation = lambda : simulator(
                element.getConstant()
                for element in
                self.getElements()
            ),
            description = "%s with constant arguments." % simulator
        )

    def mayHaveSideEffectsBool(self):
        return False

    def isKnownToBeIterable(self, count):
        return count is None or count == len( self.getElements() )

    def getIterationValue(self, count):
        return self.getElements()[ count ]

    def getIterationLength(self):
        return len( self.getElements() )

    def canPredictIterationValues(self):
        return True

    def getIterationValues(self):
        return self.getElements()

    def getTruthValue(self):
        return self.getIterationLength() > 0

    def computeExpressionDrop(self, statement, constraint_collection):
        from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

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

    def computeExpressionIter1(self, iter_node, constraint_collection):
        result = ExpressionMakeTuple(
            elements   = self.getElements(),
            source_ref = self.source_ref
        )

        self.replaceWith(result)

        return iter_node, "new_expression", """\
Iteration of list reduced to tuple."""


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

    def computeExpressionIter1(self, iter_node, constraint_collection):
        result = ExpressionMakeTuple(
            elements   = self.getElements(),
            source_ref = self.source_ref
        )

        self.replaceWith(result)

        return iter_node, "new_expression", """\
Iteration of set reduced to tuple."""


class ExpressionKeyValuePair(SideEffectsFromChildrenMixin,
                            ExpressionChildrenHavingBase):
    kind = "EXPRESSION_KEY_VALUE_PAIR"

    named_children = ( "key", "value" )

    def __init__(self, key, value, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "key"   : key,
                "value" : value
            },
            source_ref = source_ref
        )

    getKey = ExpressionChildrenHavingBase.childGetter( "key" )
    getValue = ExpressionChildrenHavingBase.childGetter( "value" )

    def computeExpression(self, constraint_collection):
        # Children can tell all we need to know, pylint: disable=W0613
        key = self.getKey()

        if key.willRaiseException(BaseException):
            return key, "new_raise", "Dictionary key raises exception"

        value = self.getValue()

        if value.willRaiseException(BaseException):
            from .NodeMakingHelpers import wrapExpressionWithNodeSideEffects

            result = wrapExpressionWithNodeSideEffects(
                new_node = value,
                old_node = key
            )

            return result, "new_raise", "Dictionary value raises exception"

        return self, None, None


class ExpressionMakeDict(SideEffectsFromChildrenMixin,
                         ExpressionChildrenHavingBase):
    kind = "EXPRESSION_MAKE_DICT"

    named_children = ( "pairs", )

    def __init__(self, pairs, lazy_order, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "pairs" : tuple( pairs ),
            },
            source_ref = source_ref
        )

        self.lazy_order = lazy_order

    getPairs = ExpressionChildrenHavingBase.childGetter( "pairs" )

    def computeExpression(self, constraint_collection):
        # Children can tell all we need to know, pylint: disable=W0613
        pairs = self.getPairs()

        for count, pair in enumerate( pairs ):
            if pair.willRaiseException( BaseException ):
                from .NodeMakingHelpers import wrapExpressionWithSideEffects

                result = wrapExpressionWithSideEffects(
                    side_effects = pairs[ : count ],
                    new_node     = pair,
                    old_node     = self
                )

                return result, "new_raise", "Dict creation raises exception"

        for pair in pairs:
            key = pair.getKey()

            # TODO: Mutable key should cause something problematic.
            if not key.isExpressionConstantRef() or key.isMutable():
                return self, None, None

            value = pair.getValue()

            if not value.isExpressionConstantRef():
                return self, None, None

        constant_value = Constants.createConstantDict(
            keys       = [
                pair.getKey().getConstant()
                for pair in
                pairs
            ],
            values     = [
                pair.getValue().getConstant()
                for pair in
                pairs
            ],
            lazy_order = self.lazy_order
        )

        from .NodeMakingHelpers import makeConstantReplacementNode

        new_node = makeConstantReplacementNode(
            constant = constant_value,
            node     = self
        )

        return new_node, "new_constant", """\
Created dictionary found to be constant."""

    def mayHaveSideEffectsBool(self):
        return False

    def isKnownToBeIterable(self, count):
        return count is None or count == len( self.getPairs() )

    def getIterationLength(self):
        return len( self.getPairs() )

    def canPredictIterationValues(self):
        # Dictionaries are fully predictable, pylint: disable=R0201
        return True

    def getIterationValue(self, count):
        return self.getPairs()[ count ].getKey()

    def getTruthValue(self):
        return self.getIterationLength() > 0

    def isMapping(self):
        # Dictionaries are always mappings, but this is a virtual method,
        # pylint: disable=R0201
        return True

    def isMappingWithConstantStringKeys(self):
        for pair in self.getPairs():
            key = pair.getKey()

            if not key.isExpressionConstantRef() or not key.isStringConstant():
                return False
        else:
            return True

    def getMappingStringKeyPairs(self):
        return [
            (
                pair.getKey().getConstant(),
                pair.getValue()
            )
            for pair in
            self.getPairs()
        ]

    def getMappingPairs(self):
        return self.getPairs()

    # TODO: Missing computeExpressionIter1 here. For now it would require us to
    # add lots of temporary variables for keys, which then becomes the tuple,
    # but for as long as we don't have efficient forward propagation of these,
    # we won't do that. Otherwise we loose execution order of values with them
    # remaining as side effects. We could limit ourselves to cases where
    # isMappingWithConstantStringKeys is true, or keys had no side effects, but
    # that feels wasted effort as we are going to have full propagation.

    def computeExpressionDrop(self, statement, constraint_collection):
        from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

        expressions = []

        for pair in self.getPairs():
            expressions.append(pair.getValue())
            expressions.append(pair.getKey())

        result = makeStatementOnlyNodesFromExpressions(
            expressions = expressions
        )

        return result, "new_statements", """\
Removed sequence creation for unused sequence."""
