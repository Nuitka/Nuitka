#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .AttributeNodes import ExpressionAttributeLookup
from .BuiltinHashNodes import ExpressionBuiltinHash
from .ConstantRefNodes import (
    ExpressionConstantDictEmptyRef,
    makeConstantRefNode,
)
from .ExpressionBases import (
    ExpressionChildHavingBase,
    ExpressionChildrenHavingBase,
)
from .NodeBases import (
    SideEffectsFromChildrenMixin,
    StatementChildrenHavingBase,
)
from .NodeMakingHelpers import (
    makeConstantReplacementNode,
    makeRaiseExceptionExpressionFromTemplate,
    makeStatementOnlyNodesFromExpressions,
    wrapExpressionWithSideEffects,
)
from .shapes.BuiltinTypeShapes import tshape_dict
from .TypeNodes import ExpressionBuiltinType1


def makeExpressionPairs(keys, values):
    assert len(keys) == len(values)

    return [
        ExpressionKeyValuePair(
            key=key, value=value, source_ref=key.getSourceReference()
        )
        for key, value in zip(keys, values)
    ]


class ExpressionKeyValuePair(
    SideEffectsFromChildrenMixin, ExpressionChildrenHavingBase
):
    kind = "EXPRESSION_KEY_VALUE_PAIR"

    # They changed the order of evaluation with 3.5 to what you normally would expect.
    if python_version < 0x350:
        named_children = ("value", "key")
    else:
        named_children = ("key", "value")

    def __init__(self, key, value, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self, values={"key": key, "value": value}, source_ref=source_ref
        )

    def computeExpression(self, trace_collection):
        key = self.subnode_key

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
        key = self.subnode_key

        return (
            key.mayRaiseException(exception_type)
            or key.isKnownToBeHashable() is not True
            or self.subnode_value.mayRaiseException(exception_type)
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

        if python_version < 0x350:
            return self.subnode_value.extractSideEffects() + key_part
        else:
            return key_part + self.subnode_value.extractSideEffects()

    def onContentEscapes(self, trace_collection):
        self.subnode_key.onContentEscapes(trace_collection)
        self.subnode_value.onContentEscapes(trace_collection)


def makeExpressionMakeDict(pairs, source_ref):
    if pairs:
        return ExpressionMakeDict(pairs, source_ref)
    else:
        # TODO: Get rid of user provided for empty dict refs, makes no sense.
        return ExpressionConstantDictEmptyRef(
            user_provided=False, source_ref=source_ref
        )


def makeExpressionMakeDictOrConstant(pairs, user_provided, source_ref):
    # Create dictionary node. Tries to avoid it for constant values that are not
    # mutable.

    for pair in pairs:
        # TODO: Compile time constant ought to be the criterion.
        if (
            not pair.subnode_value.isExpressionConstantRef()
            or not pair.subnode_key.isExpressionConstantRef()
        ):
            result = makeExpressionMakeDict(pairs, source_ref)
            break
    else:
        # Unless told otherwise, create the dictionary in its full size, so
        # that no growing occurs and the constant becomes as similar as possible
        # before being marshaled.
        result = makeConstantRefNode(
            constant=Constants.createConstantDict(
                keys=[pair.subnode_key.getCompileTimeConstant() for pair in pairs],
                values=[pair.subnode_value.getCompileTimeConstant() for pair in pairs],
            ),
            user_provided=user_provided,
            source_ref=source_ref,
        )

    if pairs:
        result.setCompatibleSourceReference(
            source_ref=pairs[-1].subnode_value.getCompatibleSourceReference()
        )

    return result


class ExpressionMakeDict(SideEffectsFromChildrenMixin, ExpressionChildHavingBase):
    kind = "EXPRESSION_MAKE_DICT"

    named_child = "pairs"

    def __init__(self, pairs, source_ref):
        assert pairs

        ExpressionChildHavingBase.__init__(
            self, value=tuple(pairs), source_ref=source_ref
        )

    @staticmethod
    def getTypeShape():
        return tshape_dict

    @staticmethod
    def hasShapeDictionaryExact():
        return True

    def computeExpression(self, trace_collection):
        pairs = self.subnode_pairs

        is_constant = True

        for pair in pairs:
            key = pair.subnode_key

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
                        expression=ExpressionBuiltinType1(
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
                    value = pair.subnode_value

                    if not value.isExpressionConstantRef():
                        is_constant = False

        if not is_constant:
            return self, None, None

        constant_value = Constants.createConstantDict(
            keys=[pair.subnode_key.getCompileTimeConstant() for pair in pairs],
            values=[pair.subnode_value.getCompileTimeConstant() for pair in pairs],
        )

        new_node = makeConstantReplacementNode(
            constant=constant_value, node=self, user_provided=True
        )

        return (
            new_node,
            "new_constant",
            """\
Created dictionary found to be constant.""",
        )

    def mayRaiseException(self, exception_type):
        for pair in self.subnode_pairs:
            if pair.mayRaiseException(exception_type):
                return True

        return False

    @staticmethod
    def mayHaveSideEffectsBool():
        return False

    def isKnownToBeIterable(self, count):
        return count is None or count == len(self.subnode_pairs)

    def getIterationLength(self):
        pair_count = len(self.subnode_pairs)

        # Hashing may consume elements.
        if pair_count > 1:
            return None
        else:
            return pair_count

    @staticmethod
    def getIterationMinLength():
        return 1

    def canPredictIterationValues(self):
        # Dictionaries are fully predictable, pylint: disable=no-self-use

        # TODO: For some things, that may not be true, when key collisions
        # happen for example. We will have to check that then.
        return True

    def getIterationValue(self, count):
        return self.subnode_pairs[count].subnode_key

    @staticmethod
    def getTruthValue():
        return True

    def isMappingWithConstantStringKeys(self):
        return all(
            pair.subnode_key.isExpressionConstantStrRef() for pair in self.subnode_pairs
        )

    def getMappingStringKeyPairs(self):
        return [
            (pair.subnode_key.getCompileTimeConstant(), pair.subnode_value)
            for pair in self.subnode_pairs
        ]

    # TODO: Missing computeExpressionIter1 here. For now it would require us to
    # add lots of temporary variables for keys, which then becomes the tuple,
    # but for as long as we don't have efficient forward propagation of these,
    # we won't do that. Otherwise we loose execution order of values with them
    # remaining as side effects. We could limit ourselves to cases where
    # isMappingWithConstantStringKeys is true, or keys had no side effects, but
    # that feels wasted effort as we are going to have full propagation.

    def computeExpressionDrop(self, statement, trace_collection):
        expressions = []

        for pair in self.subnode_pairs:
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

    def onContentEscapes(self, trace_collection):
        for pair in self.subnode_pairs:
            pair.onContentEscapes(trace_collection)


class StatementDictOperationSet(StatementChildrenHavingBase):
    kind = "STATEMENT_DICT_OPERATION_SET"

    named_children = ("value", "dict_arg", "key")

    def __init__(self, dict_arg, key, value, source_ref):
        assert dict_arg is not None
        assert key is not None
        assert value is not None

        StatementChildrenHavingBase.__init__(
            self,
            values={"dict_arg": dict_arg, "key": key, "value": value},
            source_ref=source_ref,
        )

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.computeStatementOperation(trace_collection)

    def computeStatementOperation(self, trace_collection):
        key = self.subnode_key

        if not key.isKnownToBeHashable():
            # Any exception may be raised.
            trace_collection.onExceptionRaiseExit(BaseException)

        # TODO: Until we have proper dictionary tracing, do this.
        trace_collection.removeKnowledge(self.subnode_dict_arg)

        return self, None, None

    def mayRaiseException(self, exception_type):
        key = self.subnode_key

        if not key.isKnownToBeHashable():
            return True

        if key.mayRaiseException(exception_type):
            return True

        value = self.subnode_value

        if value.mayRaiseException(exception_type):
            return True

        return False

    def mayRaiseExceptionOperation(self):
        return not self.subnode_key.isKnownToBeHashable()


class StatementDictOperationSetKeyValue(StatementDictOperationSet):
    kind = "STATEMENT_DICT_OPERATION_SET_KEY_VALUE"

    named_children = ("key", "value", "dict_arg")


class StatementDictOperationRemove(StatementChildrenHavingBase):
    kind = "STATEMENT_DICT_OPERATION_REMOVE"

    named_children = ("dict_arg", "key")

    def __init__(self, dict_arg, key, source_ref):
        assert dict_arg is not None
        assert key is not None

        StatementChildrenHavingBase.__init__(
            self, values={"dict_arg": dict_arg, "key": key}, source_ref=source_ref
        )

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.computeStatementOperation(trace_collection)

    def computeStatementOperation(self, trace_collection):
        # Any exception may be raised, we don't know if the key is present.
        trace_collection.onExceptionRaiseExit(BaseException)

        # TODO: Until we have proper dictionary tracing, do this.
        trace_collection.removeKnowledge(self.subnode_dict_arg)

        return self, None, None

    def mayRaiseException(self, exception_type):
        key = self.subnode_key

        if not key.isKnownToBeHashable():
            return True

        if key.mayRaiseException(exception_type):
            return True

        # TODO: Could check dict for knowledge about keys.
        return True


class ExpressionDictOperationGet(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_DICT_OPERATION_GET"

    named_children = ("dict_arg", "key")

    def __init__(self, dict_arg, key, source_ref):
        assert dict_arg is not None
        assert key is not None

        ExpressionChildrenHavingBase.__init__(
            self, values={"dict_arg": dict_arg, "key": key}, source_ref=source_ref
        )

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class StatementDictOperationUpdate(StatementChildrenHavingBase):
    """Update dict value.

    This is mainly used for re-formulations, where a dictionary
    update will be performed on what is known not to be a
    general mapping.
    """

    kind = "STATEMENT_DICT_OPERATION_UPDATE"

    named_children = ("dict_arg", "value")

    def __init__(self, dict_arg, value, source_ref):
        assert dict_arg is not None
        assert value is not None

        StatementChildrenHavingBase.__init__(
            self, values={"dict_arg": dict_arg, "value": value}, source_ref=source_ref
        )

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionDictOperationInNotInUncertainBase(ExpressionChildrenHavingBase):
    # Follows the reversed nature of "in", with the dictionary on the right
    # side of things.
    named_children = ("key", "dict_arg")

    __slots__ = ("known_hashable_key",)

    def __init__(self, key, dict_arg, source_ref):
        assert dict_arg is not None
        assert key is not None

        ExpressionChildrenHavingBase.__init__(
            self, values={"dict_arg": dict_arg, "key": key}, source_ref=source_ref
        )

        self.known_hashable_key = None

    def computeExpression(self, trace_collection):
        if self.known_hashable_key is None:
            self.known_hashable_key = self.subnode_key.isKnownToBeHashable()

            # TODO: Generate unhashable exception here.
            if self.known_hashable_key is False:
                pass

        if self.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_key.mayRaiseException(exception_type)
            or self.subnode_dict_arg.mayRaiseException(exception_type)
            or self.known_hashable_key is not True
        )

    def mayHaveSideEffects(self):
        return self.mayRaiseException(BaseException)

    def extractSideEffects(self):
        if self.known_hashable_key is not True:
            return (self,)
        else:
            return (
                self.subnode_key.extractSideEffects()
                + self.subnode_value.extractSideEffects()
            )


class ExpressionDictOperationIn(ExpressionDictOperationInNotInUncertainBase):
    kind = "EXPRESSION_DICT_OPERATION_IN"


class ExpressionDictOperationNotIn(ExpressionDictOperationInNotInUncertainBase):
    kind = "EXPRESSION_DICT_OPERATION_NOT_IN"
