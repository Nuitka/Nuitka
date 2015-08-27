#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Nodes that build dictionaries.

The "pair" is a sub-structure of the dictionary, representing a key/value pair
that is the child of the dictionary creation.

"""


from nuitka import Constants
from nuitka.PythonVersions import python_version

from .NodeBases import (
    ExpressionChildrenHavingBase,
    SideEffectsFromChildrenMixin
)
from .NodeMakingHelpers import (
    makeConstantReplacementNode,
    makeStatementOnlyNodesFromExpressions,
    wrapExpressionWithNodeSideEffects,
    wrapExpressionWithSideEffects
)


class ExpressionKeyValuePair(SideEffectsFromChildrenMixin,
                             ExpressionChildrenHavingBase):
    kind = "EXPRESSION_KEY_VALUE_PAIR"

    if python_version < 350:
        named_children = (
            "key",
            "value"
        )
    else:
        named_children = (
            "key",
            "value"
        )


    def __init__(self, key, value, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "key"   : key,
                "value" : value
            },
            source_ref = source_ref
        )

    getKey = ExpressionChildrenHavingBase.childGetter("key")
    getValue = ExpressionChildrenHavingBase.childGetter("value")

    def computeExpression(self, constraint_collection):
        sub_expressions = self.getVisitableNodes()

        if sub_expressions[0].willRaiseException(BaseException):
            child_name = sub_expressions[0].getChildName()

            return sub_expressions[0], "new_raise", "Dictionary %s raises exception" % child_name

        if sub_expressions[1].willRaiseException(BaseException):
            child_name = sub_expressions[1].getChildName()

            result = wrapExpressionWithNodeSideEffects(
                new_node = sub_expressions[1],
                old_node = sub_expressions[0]
            )

            return result, "new_raise", "Dictionary %s raises exception" % child_name

        return self, None, None

    def mayRaiseException(self, exception_type):
        key = self.getKey()

        return key.mayRaiseException(exception_type) or \
               key.isKnownToBeHashable() is not True or \
               self.getValue().mayRaiseException(exception_type)


class ExpressionMakeDict(SideEffectsFromChildrenMixin,
                         ExpressionChildrenHavingBase):
    kind = "EXPRESSION_MAKE_DICT"

    named_children = (
        "pairs",
    )

    def __init__(self, pairs, lazy_order, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "pairs" : tuple(pairs),
            },
            source_ref = source_ref
        )

        self.lazy_order = lazy_order

    def getDetails(self):
        return {
            "lazy_order" : self.lazy_order
        }

    getPairs = ExpressionChildrenHavingBase.childGetter("pairs")

    def computeExpression(self, constraint_collection):
        pairs = self.getPairs()

        for count, pair in enumerate(pairs):
            if pair.willRaiseException(BaseException):
                # Later elements have no side effects after the element that
                # raised the exception.
                result = wrapExpressionWithSideEffects(
                    side_effects = pairs[:count],
                    new_node     = pair,
                    old_node     = self
                )

                return result, "new_raise", "Dict creation raises exception"

        for pair in pairs:
            key = pair.getKey()

            # TODO: Mutable key should cause an exception raise to be produced.
            if not key.isExpressionConstantRef() or not key.isKnownToBeHashable():
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

        new_node = makeConstantReplacementNode(
            constant = constant_value,
            node     = self
        )

        return new_node, "new_constant", """\
Created dictionary found to be constant."""

    def mayRaiseException(self, exception_type):
        for pair in self.getPairs():
            if pair.mayRaiseException(exception_type):
                return True

        return False

    def mayHaveSideEffectsBool(self):
        return False

    def isKnownToBeIterable(self, count):
        return count is None or count == len(self.getPairs())

    def getIterationLength(self):
        return len(self.getPairs())

    def canPredictIterationValues(self):
        # Dictionaries are fully predictable, pylint: disable=R0201
        return True

    def getIterationValue(self, count):
        return self.getPairs()[ count ].getKey()

    def getTruthValue(self):
        return self.getIterationLength() > 0

    def mayBeNone(self):
        return False

    def isMapping(self):
        # Dictionaries are always mappings, but this is a virtual method,
        # pylint: disable=R0201
        return True

    def isMappingWithConstantStringKeys(self):
        for pair in self.getPairs():
            key = pair.getKey()

            if not key.isExpressionConstantRef() or not key.isStringConstant():
                return False
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
        expressions = []

        for pair in self.getPairs():
            expressions.extend(pair.extractSideEffects())

        result = makeStatementOnlyNodesFromExpressions(
            expressions = expressions
        )

        return result, "new_statements", """\
Removed sequence creation for unused sequence."""

    def computeExpressionIter1(self, iter_node, constraint_collection):
        return self, None, None

        # TODO: This ought to be possible. Only difficulty is to
        # preserve order of evaluation, by making values a side
        # effect of the keys.
        # return iter_node, "new_expression", """\
# Iteration over dict reduced to tuple."""
