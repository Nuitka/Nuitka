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
""" Nodes that build dictionaries.

The "pair" is a sub-structure of the dictionary, representing a key/value pair
that is the child of the dictionary creation.

"""


from nuitka import Constants
from nuitka.Builtins import calledWithBuiltinArgumentNamesDecorator
from nuitka.PythonVersions import python_version

from .AttributeNodes import ExpressionAttributeLookup
from .BuiltinHashNodes import ExpressionBuiltinHash
from .ExpressionBases import ExpressionChildrenHavingBase
from .NodeBases import SideEffectsFromChildrenMixin, StatementChildrenHavingBase
from .NodeMakingHelpers import (
    makeConstantReplacementNode,
    makeRaiseExceptionExpressionFromTemplate,
    makeStatementOnlyNodesFromExpressions,
    wrapExpressionWithSideEffects,
)
from .TypeNodes import ExpressionBuiltinType1


class ExpressionKeyValuePair(
    SideEffectsFromChildrenMixin, ExpressionChildrenHavingBase
):
    kind = "EXPRESSION_KEY_VALUE_PAIR"

    if python_version < 350:
        named_children = ("value", "key")
    else:
        named_children = ("key", "value")

    def __init__(self, key, value, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self, values={"key": key, "value": value}, source_ref=source_ref
        )

    getKey = ExpressionChildrenHavingBase.childGetter("key")
    getValue = ExpressionChildrenHavingBase.childGetter("value")

    def computeExpression(self, trace_collection):
        key = self.getKey()

        hashable = key.isKnownToBeHashable()

        # If not known to be hashable, that can raise an exception.
        if not hashable:
            trace_collection.onExceptionRaiseExit(TypeError)

        if hashable is False:
            # TODO: If it's not hashable, we should turn it into a raise, it's
            # just difficult to predict the exception value precisely, as it
            # could be e.g. (2, []), and should then complain about the list.
            pass

        return self, None, None

    def mayRaiseException(self, exception_type):
        key = self.getKey()

        return (
            key.mayRaiseException(exception_type)
            or key.isKnownToBeHashable() is not True
            or self.getValue().mayRaiseException(exception_type)
        )

    def extractSideEffects(self):
        if self.subnode_key.isKnownToBeHashable() is True:
            key_part = self.subnode_key.extractSideEffects()
        else:
            key_part = (
                ExpressionBuiltinHash(
                    value=self.subnode_key, source_ref=self.subnode_key.source_ref
                ),
            )

        if python_version < 350:
            return self.subnode_value.extractSideEffects() + key_part
        else:
            return key_part + self.subnode_value.extractSideEffects()


class ExpressionMakeDict(SideEffectsFromChildrenMixin, ExpressionChildrenHavingBase):
    kind = "EXPRESSION_MAKE_DICT"

    named_children = ("pairs",)

    def __init__(self, pairs, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self, values={"pairs": tuple(pairs)}, source_ref=source_ref
        )

    getPairs = ExpressionChildrenHavingBase.childGetter("pairs")

    def computeExpression(self, trace_collection):
        pairs = self.getPairs()

        is_constant = True

        for pair in pairs:
            key = pair.getKey()

            if key.isKnownToBeHashable() is False:
                side_effects = []

                for pair2 in pairs:
                    side_effects.extend(pair2.extractSideEffects())

                    if pair2 is pair:
                        break

                result = makeRaiseExceptionExpressionFromTemplate(
                    exception_type="TypeError",
                    template="unhashable type: '%s'",
                    template_args=ExpressionAttributeLookup(
                        source=ExpressionBuiltinType1(
                            value=key.extractUnhashableNode(), source_ref=key.source_ref
                        ),
                        attribute_name="__name__",
                        source_ref=key.source_ref,
                    ),
                    source_ref=key.source_ref,
                )
                result = wrapExpressionWithSideEffects(
                    side_effects=side_effects, old_node=key, new_node=result
                )

                return (
                    result,
                    "new_raise",
                    "Dictionary key is known to not be hashable.",
                )

            if is_constant:
                if not key.isExpressionConstantRef():
                    is_constant = False
                else:
                    value = pair.getValue()

                    if not value.isExpressionConstantRef():
                        is_constant = False

        if not is_constant:
            return self, None, None

        constant_value = Constants.createConstantDict(
            keys=[pair.getKey().getConstant() for pair in pairs],
            values=[pair.getValue().getConstant() for pair in pairs],
        )

        new_node = makeConstantReplacementNode(constant=constant_value, node=self)

        return (
            new_node,
            "new_constant",
            """\
Created dictionary found to be constant.""",
        )

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
        pair_count = len(self.getPairs())

        # Hashing may consume elements.
        if pair_count >= 2:
            return None
        else:
            return pair_count

    def getIterationMinLength(self):
        pair_count = len(self.getPairs())

        if pair_count == 0:
            return 0
        else:
            return 1

    def getIterationMaxLength(self):
        return len(self.getPairs())

    def canPredictIterationValues(self):
        # Dictionaries are fully predictable, pylint: disable=no-self-use

        # TODO: For some things, that may not be true, when key collisions
        # happen for example. We will have to check that then.
        return True

    def getIterationValue(self, count):
        return self.getPairs()[count].getKey()

    def getTruthValue(self):
        return self.getIterationLength() > 0

    def isMapping(self):
        # Dictionaries are always mappings, but this is a virtual method,
        # pylint: disable=no-self-use
        return True

    def isMappingWithConstantStringKeys(self):
        for pair in self.getPairs():
            key = pair.getKey()

            if not key.isExpressionConstantRef() or not key.isStringConstant():
                return False
        return True

    def getMappingStringKeyPairs(self):
        return [
            (pair.getKey().getConstant(), pair.getValue()) for pair in self.getPairs()
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

    def computeExpressionDrop(self, statement, trace_collection):
        expressions = []

        for pair in self.getPairs():
            expressions.extend(pair.extractSideEffects())

        result = makeStatementOnlyNodesFromExpressions(expressions=expressions)

        del self.parent

        return (
            result,
            "new_statements",
            """\
Removed sequence creation for unused sequence.""",
        )

    def computeExpressionIter1(self, iter_node, trace_collection):
        return iter_node, None, None

    def hasShapeDictionaryExact(self):
        return True


class StatementDictOperationSet(StatementChildrenHavingBase):
    kind = "STATEMENT_DICT_OPERATION_SET"

    named_children = ("value", "dict", "key")

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, dict_arg, key, value, source_ref):
        assert dict_arg is not None
        assert key is not None
        assert value is not None

        StatementChildrenHavingBase.__init__(
            self,
            values={"dict": dict_arg, "key": key, "value": value},
            source_ref=source_ref,
        )

    getDict = StatementChildrenHavingBase.childGetter("dict")
    getKey = StatementChildrenHavingBase.childGetter("key")
    getValue = StatementChildrenHavingBase.childGetter("value")

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        key = self.getKey()

        if not key.isKnownToBeHashable():
            # Any exception may be raised.
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        key = self.getKey()

        if not key.isKnownToBeHashable():
            return True

        if key.mayRaiseException(exception_type):
            return True

        value = self.getValue()

        if value.mayRaiseException(exception_type):
            return True

        return False


class StatementDictOperationRemove(StatementChildrenHavingBase):
    kind = "STATEMENT_DICT_OPERATION_REMOVE"

    named_children = ("dict", "key")

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, dict_arg, key, source_ref):
        assert dict_arg is not None
        assert key is not None

        StatementChildrenHavingBase.__init__(
            self, values={"dict": dict_arg, "key": key}, source_ref=source_ref
        )

    getDict = StatementChildrenHavingBase.childGetter("dict")
    getKey = StatementChildrenHavingBase.childGetter("key")

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        key = self.getKey()

        if not key.isKnownToBeHashable():
            return True

        if key.mayRaiseException(exception_type):
            return True

        # TODO: Could check dict for knowledge about keys.
        return True


class ExpressionDictOperationGet(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_DICT_OPERATION_GET"

    named_children = ("dict", "key")

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, dict_arg, key, source_ref):
        assert dict_arg is not None
        assert key is not None

        ExpressionChildrenHavingBase.__init__(
            self, values={"dict": dict_arg, "key": key}, source_ref=source_ref
        )

    getDict = ExpressionChildrenHavingBase.childGetter("dict")
    getKey = ExpressionChildrenHavingBase.childGetter("key")

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class StatementDictOperationUpdate(StatementChildrenHavingBase):
    """ Update dict value.

        This is mainly used for re-formulations, where a dictionary
        update will be performed on what is known not to be a
        general mapping.
    """

    kind = "STATEMENT_DICT_OPERATION_UPDATE"

    named_children = ("dict", "value")

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, dict_arg, value, source_ref):
        assert dict_arg is not None
        assert value is not None

        StatementChildrenHavingBase.__init__(
            self, values={"dict": dict_arg, "value": value}, source_ref=source_ref
        )

    getDict = StatementChildrenHavingBase.childGetter("dict")
    getValue = StatementChildrenHavingBase.childGetter("value")

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionDictOperationIn(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_DICT_OPERATION_IN"

    # Follow the reversed nature of "in", with the dictionary on the right
    # side of things.
    named_children = ("key", "dict")

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, key, dict_arg, source_ref):
        assert dict_arg is not None
        assert key is not None

        ExpressionChildrenHavingBase.__init__(
            self, values={"dict": dict_arg, "key": key}, source_ref=source_ref
        )

    getDict = ExpressionChildrenHavingBase.childGetter("dict")
    getKey = ExpressionChildrenHavingBase.childGetter("key")

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionDictOperationNOTIn(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_DICT_OPERATION_NOT_IN"

    # Follow the reversed nature of "in", with the dictionary on the right
    # side of things.
    named_children = ("key", "dict")

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, key, dict_arg, source_ref):
        assert dict_arg is not None
        assert key is not None

        ExpressionChildrenHavingBase.__init__(
            self, values={"dict": dict_arg, "key": key}, source_ref=source_ref
        )

    getDict = ExpressionChildrenHavingBase.childGetter("dict")
    getKey = ExpressionChildrenHavingBase.childGetter("key")

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None
