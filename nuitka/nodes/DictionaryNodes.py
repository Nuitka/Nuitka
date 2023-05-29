#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Nodes that build and operate on dictionaries.

The "pair" is a sub-structure of the dictionary, representing a key/value pair
that is the child of the dictionary creation.

"""


from nuitka import Constants
from nuitka.specs.BuiltinDictOperationSpecs import dict_fromkeys_spec
from nuitka.specs.BuiltinParameterSpecs import extractBuiltinArgs

from .AttributeNodes import makeExpressionAttributeLookup
from .BuiltinOperationNodeBasesGenerated import (
    ExpressionDictOperationClearBase,
    ExpressionDictOperationCopyBase,
    ExpressionDictOperationFromkeys2Base,
    ExpressionDictOperationFromkeys3Base,
    ExpressionDictOperationGet2Base,
    ExpressionDictOperationGet3Base,
    ExpressionDictOperationHaskeyBase,
    ExpressionDictOperationItemsBase,
    ExpressionDictOperationIteritemsBase,
    ExpressionDictOperationIterkeysBase,
    ExpressionDictOperationItervaluesBase,
    ExpressionDictOperationKeysBase,
    ExpressionDictOperationPop2Base,
    ExpressionDictOperationPop3Base,
    ExpressionDictOperationPopitemBase,
    ExpressionDictOperationSetdefault2Base,
    ExpressionDictOperationSetdefault3Base,
    ExpressionDictOperationUpdate2Base,
    ExpressionDictOperationUpdate3Base,
    ExpressionDictOperationValuesBase,
    ExpressionDictOperationViewitemsBase,
    ExpressionDictOperationViewkeysBase,
    ExpressionDictOperationViewvaluesBase,
)
from .ChildrenHavingMixins import (
    ChildrenExpressionDictOperationItemMixin,
    ChildrenExpressionDictOperationUpdatePairsMixin,
    ChildrenExpressionMakeDictMixin,
    ChildrenHavingKeyDictArgMixin,
)
from .ConstantRefNodes import (
    ExpressionConstantDictEmptyRef,
    makeConstantRefNode,
)
from .ExpressionBases import ExpressionBase, ExpressionNoSideEffectsMixin
from .ExpressionShapeMixins import (
    ExpressionBoolShapeExactMixin,
    ExpressionDictShapeExactMixin,
)
from .NodeBases import SideEffectsFromChildrenMixin
from .NodeMakingHelpers import (
    makeConstantReplacementNode,
    makeRaiseExceptionExpressionFromTemplate,
    makeRaiseExceptionReplacementExpression,
    makeStatementOnlyNodesFromExpressions,
    wrapExpressionWithSideEffects,
)
from .shapes.StandardShapes import tshape_iterator
from .StatementBasesGenerated import (
    StatementDictOperationRemoveBase,
    StatementDictOperationSetBase,
    StatementDictOperationSetKeyValueBase,
    StatementDictOperationUpdateBase,
)


def makeExpressionMakeDict(pairs, source_ref):
    if pairs:
        return ExpressionMakeDict(pairs, source_ref)
    else:
        # TODO: Get rid of user provided for empty dict refs, makes no sense.
        return ExpressionConstantDictEmptyRef(
            user_provided=False, source_ref=source_ref
        )


def makeExpressionMakeDictOrConstant(pairs, user_provided, source_ref):
    # Create dictionary node or constant value if possible.

    for pair in pairs:
        if (
            not pair.isCompileTimeConstant()
            or pair.isKeyKnownToBeHashable() is not True
        ):
            result = makeExpressionMakeDict(pairs, source_ref)
            break
    else:
        # Unless told otherwise, create the dictionary in its full size, so
        # that no growing occurs and the constant becomes as similar as possible
        # before being marshaled.
        result = makeConstantRefNode(
            constant=Constants.createConstantDict(
                keys=[pair.getKeyCompileTimeConstant() for pair in pairs],
                values=[pair.getValueCompileTimeConstant() for pair in pairs],
            ),
            user_provided=user_provided,
            source_ref=source_ref,
        )

    if pairs:
        result.setCompatibleSourceReference(
            source_ref=pairs[-1].getCompatibleSourceReference()
        )

    return result


class ExpressionMakeDictMixin(object):
    __slots__ = ()

    def mayRaiseException(self, exception_type):
        for pair in self.subnode_pairs:
            if pair.mayRaiseException(exception_type):
                return True

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

    @staticmethod
    def canPredictIterationValues():
        # Dictionaries are assumed to be fully predictable

        # TODO: For some things, that may not be true, when key collisions
        # happen for example. We will have to check that then.
        return True

    def getIterationValue(self, count):
        return self.subnode_pairs[count].getKeyNode()

    def isMappingWithConstantStringKeys(self):
        return all(pair.isKeyExpressionConstantStrRef() for pair in self.subnode_pairs)

    def getMappingStringKeyPairs(self):
        return [
            (pair.getKeyCompileTimeConstant(), pair.getValueNode())
            for pair in self.subnode_pairs
        ]

    # TODO: Make this happen from auto-compute, children only side effects
    def computeExpressionDrop(self, statement, trace_collection):
        # Virtual method overload, pylint: disable=unused-argument
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

    # TODO: Missing computeExpressionIter1 here. For now it would require us to
    # add lots of temporary variables for keys, which then becomes the tuple,
    # but for as long as we don't have efficient forward propagation of these,
    # we won't do that. Otherwise we loose execution order of values with them
    # remaining as side effects. We could limit ourselves to cases where
    # isMappingWithConstantStringKeys is true, or keys had no side effects, but
    # that feels wasted effort as we are going to have full propagation.

    @staticmethod
    def computeExpressionIter1(iter_node, trace_collection):
        return iter_node, None, None

    def onContentEscapes(self, trace_collection):
        for pair in self.subnode_pairs:
            pair.onContentEscapes(trace_collection)


class ExpressionMakeDict(
    ExpressionDictShapeExactMixin,
    SideEffectsFromChildrenMixin,
    ExpressionMakeDictMixin,
    ChildrenExpressionMakeDictMixin,
    ExpressionBase,
):
    kind = "EXPRESSION_MAKE_DICT"

    named_children = ("pairs|tuple",)

    def __init__(self, pairs, source_ref):
        assert pairs

        ChildrenExpressionMakeDictMixin.__init__(
            self,
            pairs=pairs,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        pairs = self.subnode_pairs

        is_constant = True

        for pair in pairs:
            if pair.isKeyKnownToBeHashable() is False:
                # The ones with constant keys are hashable.
                key = pair.subnode_key

                side_effects = []

                for pair2 in pairs:
                    side_effects.extend(pair2.extractSideEffects())

                    if pair2 is pair:
                        break

                result = makeRaiseExceptionExpressionFromTemplate(
                    exception_type="TypeError",
                    template="unhashable type: '%s'",
                    template_args=makeExpressionAttributeLookup(
                        expression=key.extractUnhashableNodeType(),
                        attribute_name="__name__",
                        source_ref=key.source_ref,
                    ),
                    source_ref=key.source_ref,
                )
                result = wrapExpressionWithSideEffects(
                    side_effects=side_effects,
                    old_node=key,
                    new_node=result,
                )

                return (
                    result,
                    "new_raise",
                    "Dictionary key is known to not be hashable.",
                )

            if is_constant:
                if not pair.isCompileTimeConstant():
                    is_constant = False

        if not is_constant:
            return self, None, None

        constant_value = Constants.createConstantDict(
            keys=[pair.getKeyCompileTimeConstant() for pair in pairs],
            values=[pair.getValueCompileTimeConstant() for pair in pairs],
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

    @staticmethod
    def getTruthValue():
        # Cannot be empty
        return True


class StatementDictOperationSetMixin(object):
    __slots__ = ()

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


class StatementDictOperationSet(
    StatementDictOperationSetMixin, StatementDictOperationSetBase
):
    kind = "STATEMENT_DICT_OPERATION_SET"

    named_children = ("value", "dict_arg", "key")
    auto_compute_handling = "operation"


class StatementDictOperationSetKeyValue(
    StatementDictOperationSetMixin, StatementDictOperationSetKeyValueBase
):
    kind = "STATEMENT_DICT_OPERATION_SET_KEY_VALUE"

    named_children = ("value", "dict_arg", "key")
    auto_compute_handling = "operation"


class StatementDictOperationRemove(StatementDictOperationRemoveBase):
    kind = "STATEMENT_DICT_OPERATION_REMOVE"

    named_children = ("dict_arg", "key")
    auto_compute_handling = "operation"

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


class ExpressionDictOperationPop2(ExpressionDictOperationPop2Base):
    """This operation represents d.pop(key), i.e. default None."""

    kind = "EXPRESSION_DICT_OPERATION_POP2"

    __slots__ = ("known_hashable_key",)

    def __init__(self, dict_arg, key, source_ref):
        ExpressionDictOperationPop2Base.__init__(
            self,
            dict_arg=dict_arg,
            key=key,
            source_ref=source_ref,
        )

        self.known_hashable_key = None

    def computeExpression(self, trace_collection):
        dict_arg = self.subnode_dict_arg
        key = self.subnode_key

        if self.known_hashable_key is None:
            self.known_hashable_key = key.isKnownToBeHashable()

            if self.known_hashable_key is False:
                trace_collection.onExceptionRaiseExit(BaseException)

                return makeUnhashableExceptionReplacementExpression(
                    node=self,
                    key=key,
                    operation="dict.pop",
                    side_effects=(dict_arg, key),
                )

        # TODO: Check if dict_arg has key.

        # TODO: Until we have proper dictionary tracing, do this.
        trace_collection.removeKnowledge(dict_arg)

        # TODO: Until we can know KeyError won't happen, but then we should change into
        # something else.
        trace_collection.onExceptionRaiseExit(BaseException)

        # TODO: Check for "None" default and demote to ExpressionDictOperationSetdefault3 in
        # that case.
        return self, None, None

    # TODO: These turn this into dictionary item removals, as value is unused.
    # def computeExpressionDrop(self, statement, trace_collection):

    # TODO: Might raise KeyError depending on dictionary.
    @staticmethod
    def mayRaiseException(exception_type):
        return True

        # if self.known_hashable_key is None:
        #     return True
        # else:
        #     return self.subnode_dict_arg.mayRaiseException(
        #         exception_type
        #     ) or self.subnode_key.mayRaiseException(exception_type)


class ExpressionDictOperationPop3(ExpressionDictOperationPop3Base):
    """This operation represents d.pop(key, default)."""

    kind = "EXPRESSION_DICT_OPERATION_POP3"

    __slots__ = ("known_hashable_key",)

    def __init__(self, dict_arg, key, default, source_ref):
        ExpressionDictOperationPop3Base.__init__(
            self,
            dict_arg=dict_arg,
            key=key,
            default=default,
            source_ref=source_ref,
        )

        self.known_hashable_key = None

    def computeExpression(self, trace_collection):
        dict_arg = self.subnode_dict_arg
        key = self.subnode_key

        if self.known_hashable_key is None:
            self.known_hashable_key = key.isKnownToBeHashable()

            if self.known_hashable_key is False:
                trace_collection.onExceptionRaiseExit(BaseException)

                return makeUnhashableExceptionReplacementExpression(
                    node=self,
                    key=key,
                    operation="dict.pop",
                    side_effects=(dict_arg, key, self.subnode_default),
                )

        # TODO: Check if dict_arg has key

        # TODO: Until we have proper dictionary tracing, do this.
        trace_collection.removeKnowledge(dict_arg)

        # TODO: Check for "None" default and demote to ExpressionDictOperationSetdefault3 in
        # that case.
        return self, None, None

    # TODO: These turn this into dictionary item removals, as value is unused.
    # def computeExpressionDrop(self, statement, trace_collection):

    def mayRaiseException(self, exception_type):
        if self.known_hashable_key is None:
            return True
        else:
            return (
                self.subnode_dict_arg.mayRaiseException(exception_type)
                or self.subnode_key.mayRaiseException(exception_type)
                or self.subnode_default.mayRaiseException(exception_type)
            )


class ExpressionDictOperationPopitem(ExpressionDictOperationPopitemBase):
    """This operation represents d.popitem()."""

    kind = "EXPRESSION_DICT_OPERATION_POPITEM"

    def computeExpression(self, trace_collection):
        dict_arg = self.subnode_dict_arg

        # TODO: Check if dict_arg is not empty.

        # TODO: Until we have proper dictionary tracing, do this.
        trace_collection.removeKnowledge(dict_arg)

        # TODO: Until we can know KeyError won't happen, but then we should change into
        # something else.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    # TODO: These turn this into dictionary item removal, as value is unused.
    # def computeExpressionDrop(self, statement, trace_collection):

    # TODO: Might raise KeyError depending on dictionary.
    @staticmethod
    def mayRaiseException(exception_type):
        return True


class ExpressionDictOperationSetdefault2(ExpressionDictOperationSetdefault2Base):
    """This operation represents d.setdefault(key), i.e. default None."""

    kind = "EXPRESSION_DICT_OPERATION_SETDEFAULT2"

    __slots__ = ("known_hashable_key",)

    def __init__(self, dict_arg, key, source_ref):
        ExpressionDictOperationSetdefault2Base.__init__(
            self,
            dict_arg=dict_arg,
            key=key,
            source_ref=source_ref,
        )

        self.known_hashable_key = None

    def computeExpression(self, trace_collection):
        dict_arg = self.subnode_dict_arg
        key = self.subnode_key

        if self.known_hashable_key is None:
            self.known_hashable_key = key.isKnownToBeHashable()

            if self.known_hashable_key is False:
                trace_collection.onExceptionRaiseExit(BaseException)

                return makeUnhashableExceptionReplacementExpression(
                    node=self,
                    key=key,
                    operation="dict.setdefault",
                    side_effects=(dict_arg, key),
                )

        # TODO: Check if dict_arg has key, and eliminate this node entirely
        # if that's the case with hashing of the key as a remaining side effect
        # though.

        # TODO: Until we have proper dictionary tracing, do this.
        trace_collection.removeKnowledge(dict_arg)

        # TODO: Check for "None" default and demote to ExpressionDictOperationSetdefault3 in
        # that case.
        return self, None, None

    def mayRaiseException(self, exception_type):
        if self.known_hashable_key is not True:
            return True
        else:
            return self.subnode_dict_arg.mayRaiseException(
                exception_type
            ) or self.subnode_key.mayRaiseException(exception_type)


class ExpressionDictOperationSetdefault3(ExpressionDictOperationSetdefault3Base):
    """This operation represents d.setdefault(key, default)."""

    kind = "EXPRESSION_DICT_OPERATION_SETDEFAULT3"

    __slots__ = ("known_hashable_key",)

    def __init__(self, dict_arg, key, default, source_ref):
        ExpressionDictOperationSetdefault3Base.__init__(
            self,
            dict_arg=dict_arg,
            key=key,
            default=default,
            source_ref=source_ref,
        )

        # TODO: Slots could be part of base class generation too.
        self.known_hashable_key = None

    def computeExpression(self, trace_collection):
        dict_arg = self.subnode_dict_arg
        key = self.subnode_key

        if self.known_hashable_key is None:
            self.known_hashable_key = key.isKnownToBeHashable()

            if self.known_hashable_key is False:
                trace_collection.onExceptionRaiseExit(BaseException)

                return makeUnhashableExceptionReplacementExpression(
                    node=self,
                    key=key,
                    operation="dict.setdefault",
                    side_effects=(dict_arg, key, self.subnode_default),
                )

        # TODO: Check if dict_arg has key, and eliminate this node entirely
        # if that's the case with hashing of the key as a remaining side effect
        # though.

        # TODO: Until we have proper dictionary tracing, do this.
        trace_collection.removeKnowledge(dict_arg)

        # TODO: Check for "None" default and demote to ExpressionDictOperationSetdefault3 in
        # that case.
        return self, None, None

    def mayRaiseException(self, exception_type):
        if self.known_hashable_key is not True:
            return True
        else:
            return (
                self.subnode_dict_arg.mayRaiseException(exception_type)
                or self.subnode_key.mayRaiseException(exception_type)
                or self.subnode_default.mayRaiseException(exception_type)
            )


class ExpressionDictOperationItem(
    ChildrenExpressionDictOperationItemMixin, ExpressionBase
):
    """This operation represents d[key] with an exception for missing key."""

    kind = "EXPRESSION_DICT_OPERATION_ITEM"

    named_children = ("dict_arg", "key")

    def __init__(self, dict_arg, key, source_ref):
        ChildrenExpressionDictOperationItemMixin.__init__(
            self, dict_arg=dict_arg, key=key
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        dict_arg = self.subnode_dict_arg
        key = self.subnode_key

        if dict_arg.isCompileTimeConstant() and key.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: self.getCompileTimeConstant()[
                    dict_arg.getCompileTimeConstant()[key.getCompileTimeConstant()]
                ],
                user_provided=dict_arg.user_provided,
                description="Dictionary item lookup with constant key.",
            )

        # TODO: Only if the key is not hashable.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionDictOperationGet2(ExpressionDictOperationGet2Base):
    """This operation represents d.get(key) with no exception for missing key but None default."""

    kind = "EXPRESSION_DICT_OPERATION_GET2"

    named_children = ("dict_arg", "key")

    __slots__ = ("known_hashable_key",)

    def __init__(self, dict_arg, key, source_ref):
        ExpressionDictOperationGet2Base.__init__(
            self, dict_arg=dict_arg, key=key, source_ref=source_ref
        )

        self.known_hashable_key = None

    def computeExpression(self, trace_collection):
        dict_arg = self.subnode_dict_arg
        key = self.subnode_key

        if self.known_hashable_key is None:
            self.known_hashable_key = self.subnode_key.isKnownToBeHashable()

            if self.known_hashable_key is False:
                trace_collection.onExceptionRaiseExit(BaseException)

                return makeUnhashableExceptionReplacementExpression(
                    node=self,
                    key=key,
                    operation="dict.get",
                    side_effects=(dict_arg, key),
                )

        if dict_arg.isCompileTimeConstant() and key.isCompileTimeConstant():
            result = wrapExpressionWithSideEffects(
                new_node=makeConstantReplacementNode(
                    constant=dict_arg.getCompileTimeConstant().get(
                        key.getCompileTimeConstant()
                    ),
                    node=self,
                    user_provided=dict_arg.user_provided,
                ),
                old_node=self,
                side_effects=(dict_arg, key),
            )

            return (
                result,
                "new_expression",
                "Compile time computed 'dict.get' on constant argument.",
            )

        if self.known_hashable_key is None:
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        if self.known_hashable_key is None:
            return True
        else:
            return self.subnode_dict_arg.mayRaiseException(
                exception_type
            ) or self.subnode_key.mayRaiseException(exception_type)

    def mayHaveSideEffects(self):
        if self.known_hashable_key is None:
            return True
        else:
            return (
                self.subnode_dict_arg.mayHaveSideEffects()
                or self.subnode_key.mayHaveSideEffects()
            )

    def extractSideEffects(self):
        if self.known_hashable_key is None:
            return (self,)
        else:
            return (
                self.subnode_dict_arg.extractSideEffects()
                + self.subnode_key.extractSideEffects()
            )


class ExpressionDictOperationGet3(ExpressionDictOperationGet3Base):
    """This operation represents d.get(key, default) with no exception for missing key but default value."""

    kind = "EXPRESSION_DICT_OPERATION_GET3"

    named_children = ("dict_arg", "key", "default")

    __slots__ = ("known_hashable_key",)

    def __init__(self, dict_arg, key, default, source_ref):
        ExpressionDictOperationGet3Base.__init__(
            self, dict_arg=dict_arg, key=key, default=default, source_ref=source_ref
        )

        self.known_hashable_key = None

    def computeExpression(self, trace_collection):
        dict_arg = self.subnode_dict_arg
        key = self.subnode_key

        if self.known_hashable_key is None:
            self.known_hashable_key = key.isKnownToBeHashable()

            if self.known_hashable_key is False:
                trace_collection.onExceptionRaiseExit(BaseException)

                return makeUnhashableExceptionReplacementExpression(
                    node=self,
                    key=key,
                    operation="dict.get",
                    side_effects=(dict_arg, key, self.subnode_default),
                )

        # TODO: With dictionary tracing, this could become more transparent.
        if dict_arg.isCompileTimeConstant() and key.isCompileTimeConstant():
            dict_value = dict_arg.getCompileTimeConstant()
            key_value = key.getCompileTimeConstant()

            if key_value in dict_value:
                # Side effects of args must be retained, but it's not used.
                result = wrapExpressionWithSideEffects(
                    new_node=makeConstantReplacementNode(
                        constant=dict_value[key_value],
                        node=self,
                        user_provided=dict_arg.user_provided,
                    ),
                    old_node=self,
                    side_effects=(
                        dict_arg,
                        key,
                        self.subnode_default,
                    ),
                )

                description = "Compile time computed 'dict.get' on constant argument to not use default."
            else:
                # Side effects of dict and key must be retained, but it's not used.
                result = wrapExpressionWithSideEffects(
                    new_node=self.subnode_default,
                    old_node=self,
                    side_effects=(dict_arg, key),
                )

                description = "Compile time computed 'dict.get' on constant argument to use default."

            return (result, "new_expression", description)

        if self.known_hashable_key is None:
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        if self.known_hashable_key is None:
            return True
        else:
            return (
                self.subnode_dict_arg.mayRaiseException(exception_type)
                or self.subnode_key.mayRaiseException(exception_type)
                or self.subnode_default.mayRaiseException(exception_type)
            )

    def mayHaveSideEffects(self):
        if self.known_hashable_key is None:
            return True
        else:
            return (
                self.subnode_dict_arg.mayHaveSideEffects()
                or self.subnode_key.mayHaveSideEffects()
                or self.subnode_default.mayHaveSideEffects()
            )

    def extractSideEffects(self):
        if self.known_hashable_key is None:
            return (self,)
        else:
            return (
                self.subnode_dict_arg.extractSideEffects()
                + self.subnode_key.extractSideEffects()
                + self.subnode_defaults.extractSideEffects()
            )


class ExpressionDictOperationCopy(
    SideEffectsFromChildrenMixin,
    ExpressionDictOperationCopyBase,
):
    kind = "EXPRESSION_DICT_OPERATION_COPY"

    def computeExpression(self, trace_collection):
        dict_arg = self.subnode_dict_arg

        if dict_arg.isCompileTimeConstant():
            result = makeConstantReplacementNode(
                constant=dict_arg.getCompileTimeConstant().copy(),
                node=self,
                user_provided=dict_arg.user_provided,
            )

            return (
                result,
                "new_expression",
                "Compile time computed 'dict.copy' on constant argument.",
            )

        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return self.subnode_dict_arg.mayRaiseException(exception_type)


class ExpressionDictOperationClear(ExpressionDictOperationClearBase):
    kind = "EXPRESSION_DICT_OPERATION_CLEAR"

    def computeExpression(self, trace_collection):
        # Once we do dictionary tracing, we should tell it, we know its new value
        # perfectly, and that we have no use for previous value.
        # trace_collection.onDictionaryReplaceValueWithKnownValue(self.subnode_dict_arg, {})

        return self, None, None

    def mayRaiseException(self, exception_type):
        return self.subnode_dict_arg.mayRaiseException(exception_type)


class ExpressionDictOperationKeys(
    SideEffectsFromChildrenMixin,
    ExpressionDictOperationKeysBase,
):
    kind = "EXPRESSION_DICT_OPERATION_KEYS"

    def computeExpression(self, trace_collection):
        dict_arg = self.subnode_dict_arg

        if dict_arg.isCompileTimeConstant():
            result = makeConstantReplacementNode(
                constant=dict_arg.getCompileTimeConstant().keys(),
                node=self,
                user_provided=dict_arg.user_provided,
            )

            return (
                result,
                "new_expression",
                "Compile time computed 'dict.keys' on constant argument.",
            )

        return self, None, None

    def mayRaiseException(self, exception_type):
        return self.subnode_dict_arg.mayRaiseException(exception_type)


class ExpressionDictOperationViewkeys(
    SideEffectsFromChildrenMixin, ExpressionDictOperationViewkeysBase
):
    kind = "EXPRESSION_DICT_OPERATION_VIEWKEYS"

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def getTypeShape():
        # TODO: Actually iterator that yields key values
        return tshape_iterator

    def mayRaiseException(self, exception_type):
        return self.subnode_dict_arg.mayRaiseException(exception_type)


class ExpressionDictOperationIterkeys(
    SideEffectsFromChildrenMixin, ExpressionDictOperationIterkeysBase
):
    kind = "EXPRESSION_DICT_OPERATION_ITERKEYS"

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def getTypeShape():
        # TODO: Actually iterator yield keys
        return tshape_iterator

    def mayRaiseException(self, exception_type):
        return self.subnode_dict_arg.mayRaiseException(exception_type)


class ExpressionDictOperationValues(
    SideEffectsFromChildrenMixin,
    ExpressionDictOperationValuesBase,
):
    kind = "EXPRESSION_DICT_OPERATION_VALUES"

    def computeExpression(self, trace_collection):
        dict_arg = self.subnode_dict_arg

        if dict_arg.isCompileTimeConstant():
            result = makeConstantReplacementNode(
                constant=dict_arg.getCompileTimeConstant().values(),
                node=self,
                user_provided=dict_arg.user_provided,
            )

            return (
                result,
                "new_expression",
                "Compile time computed 'dict.values' on constant argument.",
            )

        return self, None, None

    def mayRaiseException(self, exception_type):
        return self.subnode_dict_arg.mayRaiseException(exception_type)


class ExpressionDictOperationViewvalues(
    SideEffectsFromChildrenMixin, ExpressionDictOperationViewvaluesBase
):
    kind = "EXPRESSION_DICT_OPERATION_VIEWVALUES"

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def getTypeShape():
        # TODO: Actually iterator that yields key values
        return tshape_iterator

    def mayRaiseException(self, exception_type):
        return self.subnode_dict_arg.mayRaiseException(exception_type)


class ExpressionDictOperationItervalues(
    SideEffectsFromChildrenMixin, ExpressionDictOperationItervaluesBase
):
    kind = "EXPRESSION_DICT_OPERATION_ITERVALUES"

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def getTypeShape():
        # TODO: Actually the iterator yield values.
        return tshape_iterator

    def mayRaiseException(self, exception_type):
        return self.subnode_dict_arg.mayRaiseException(exception_type)


class ExpressionDictOperationItems(
    SideEffectsFromChildrenMixin,
    ExpressionDictOperationItemsBase,
):
    kind = "EXPRESSION_DICT_OPERATION_ITEMS"

    def computeExpression(self, trace_collection):
        dict_arg = self.subnode_dict_arg

        if dict_arg.isCompileTimeConstant():
            result = makeConstantReplacementNode(
                constant=dict_arg.getCompileTimeConstant().items(),
                node=self,
                user_provided=dict_arg.user_provided,
            )

            return (
                result,
                "new_expression",
                "Compile time computed 'dict.items' on constant argument.",
            )

        return self, None, None

    def mayRaiseException(self, exception_type):
        return self.subnode_dict_arg.mayRaiseException(exception_type)


class ExpressionDictOperationIteritems(
    SideEffectsFromChildrenMixin, ExpressionDictOperationIteritemsBase
):
    kind = "EXPRESSION_DICT_OPERATION_ITERITEMS"

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def getTypeShape():
        # TODO: Actually iterator that yields 2 element tuples, add shapes
        # for that too.
        return tshape_iterator

    def mayRaiseException(self, exception_type):
        return self.subnode_dict_arg.mayRaiseException(exception_type)


class ExpressionDictOperationViewitems(
    SideEffectsFromChildrenMixin, ExpressionDictOperationViewitemsBase
):
    kind = "EXPRESSION_DICT_OPERATION_VIEWITEMS"

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def getTypeShape():
        # TODO: Actually iterator that yields key values
        return tshape_iterator

    def mayRaiseException(self, exception_type):
        return self.subnode_dict_arg.mayRaiseException(exception_type)


class ExpressionDictOperationUpdate2(ExpressionDictOperationUpdate2Base):
    """This operation represents d.update(iterable)."""

    kind = "EXPRESSION_DICT_OPERATION_UPDATE2"

    def __init__(self, dict_arg, iterable, source_ref):
        # TODO: Change generation of attribute nodes to pass it like this already.
        if type(iterable) is tuple:
            (iterable,) = iterable

        ExpressionDictOperationUpdate2Base.__init__(
            self,
            dict_arg=dict_arg,
            iterable=iterable,
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        # TODO: Until we have proper dictionary tracing, do this.
        trace_collection.removeKnowledge(self.subnode_dict_arg)
        # TODO: Using it might change it, unfortunately
        trace_collection.removeKnowledge(self.subnode_iterable)

        # TODO: Until we can know iteration error won't happen, but then we should change into
        # something else.
        trace_collection.onExceptionRaiseExit(BaseException)

        # TODO: Check empty, and remove itself if that's the case.
        return self, None, None

    # TODO: Might raise non-iterable depending on value shape, or not hashable from content.
    @staticmethod
    def mayRaiseException(exception_type):
        return True


def makeExpressionDictOperationUpdate3(dict_arg, iterable, pairs, source_ref):
    # Artefact of star argument parsing iterable, where it is also optional
    # revolved on the outside here
    if type(iterable) is tuple:
        if not iterable:
            iterable = None
        else:
            (iterable,) = iterable

    if iterable is not None:
        return ExpressionDictOperationUpdate3(dict_arg, iterable, pairs, source_ref)
    else:
        return ExpressionDictOperationUpdatePairs(dict_arg, pairs, source_ref)


class ExpressionDictOperationUpdate3(ExpressionDictOperationUpdate3Base):
    """This operation represents d.update(iterable, **pairs)."""

    kind = "EXPRESSION_DICT_OPERATION_UPDATE3"

    def __init__(self, dict_arg, iterable, pairs, source_ref):
        ExpressionDictOperationUpdate3Base.__init__(
            self,
            dict_arg=dict_arg,
            iterable=iterable,
            pairs=pairs,
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        # TODO: Until we have proper dictionary tracing, do this.
        trace_collection.removeKnowledge(self.subnode_dict_arg)
        # TODO: Using it might change it, unfortunately
        # TODO: When iterable is empty, this should be specialized further to
        # ExpressionDictOperationUpdatePairs
        trace_collection.removeKnowledge(self.subnode_iterable)

        for pair in self.subnode_pairs:
            trace_collection.removeKnowledge(pair)

        # TODO: Until we can know iteration error won't happen, but then we should change into
        # something else.
        trace_collection.onExceptionRaiseExit(BaseException)

        # TODO: Check empty, and remove itself if that's the case.
        return self, None, None

    # TODO: Might raise non-iterable depending on value shape, or not hashable from content.
    @staticmethod
    def mayRaiseException(exception_type):
        return True


class ExpressionDictOperationUpdatePairs(
    ChildrenExpressionDictOperationUpdatePairsMixin, ExpressionBase
):
    """This operation represents d.update(iterable, **pairs)."""

    kind = "EXPRESSION_DICT_OPERATION_UPDATE_PAIRS"

    named_children = ("dict_arg", "pairs|tuple")

    def __init__(self, dict_arg, pairs, source_ref):
        ChildrenExpressionDictOperationUpdatePairsMixin.__init__(
            self,
            dict_arg=dict_arg,
            pairs=pairs,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        # TODO: Until we have proper dictionary tracing, do this.
        trace_collection.removeKnowledge(self.subnode_dict_arg)
        # TODO: Using it might change it, unfortunately
        # TODO: When iterable is empty, this should be specialized further.

        for pair in self.subnode_pairs:
            trace_collection.removeKnowledge(pair)

        # TODO: Until we can know KeyError won't happen, but then we should change into
        # something else.
        trace_collection.onExceptionRaiseExit(BaseException)

        # TODO: Check empty, and remove itself if that's the case.
        return self, None, None

    # TODO: Might raise non-iterable depending on value shape, or not hashable from content.
    @staticmethod
    def mayRaiseException(exception_type):
        return True


class StatementDictOperationUpdate(StatementDictOperationUpdateBase):
    """Update dict value.

    This is mainly used for re-formulations, where a dictionary
    update will be performed on what is known not to be a
    general mapping.
    """

    kind = "STATEMENT_DICT_OPERATION_UPDATE"

    named_children = ("dict_arg", "value")
    auto_compute_handling = "operation"

    def computeStatementOperation(self, trace_collection):
        # TODO: Until we have proper dictionary tracing, do this.
        trace_collection.removeKnowledge(self.subnode_dict_arg)
        # TODO: Using it might change it, unfortunately
        trace_collection.removeKnowledge(self.subnode_value)

        # TODO: Until we can know iteration error won't happen, but then we should change into
        # something else.
        trace_collection.onExceptionRaiseExit(BaseException)

        # TODO: Check empty, and remove itself if that's the case.
        return self, None, None


def makeUnhashableExceptionReplacementExpression(node, key, side_effects, operation):
    unhashable_type_name = (
        key.extractUnhashableNodeType().getCompileTimeConstant().__name__
    )
    result = makeRaiseExceptionReplacementExpression(
        expression=node,
        exception_type="TypeError",
        exception_value="unhashable type: '%s'" % unhashable_type_name,
    )
    result = wrapExpressionWithSideEffects(
        side_effects=side_effects,
        old_node=node,
        new_node=result,
    )

    return (
        result,
        "new_raise",
        "Dictionary operation '%s' with key of type '%s' that is known to not be hashable."
        % (operation, unhashable_type_name),
    )


class ExpressionDictOperationInNotInUncertainMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    def computeExpression(self, trace_collection):
        if self.known_hashable_key is None:
            self.known_hashable_key = self.subnode_key.isKnownToBeHashable()

            if self.known_hashable_key is False:
                trace_collection.onExceptionRaiseExit(BaseException)

                return makeUnhashableExceptionReplacementExpression(
                    node=self,
                    key=self.subnode_key,
                    operation="in (dict)",
                    side_effects=self.getVisitableNodes(),
                )

        if self.known_hashable_key is None:
            trace_collection.onExceptionRaiseExit(BaseException)

        if self.subnode_key.isCompileTimeConstant():
            truth_value = self.subnode_dict_arg.getExpressionDictInConstant(
                self.subnode_key.getCompileTimeConstant()
            )

            if truth_value is not None:
                # TODO: Ugly that this code is not drawing from derived class methods.
                if "NOT" in self.kind:
                    truth_value = not truth_value

                result = wrapExpressionWithSideEffects(
                    new_node=makeConstantReplacementNode(
                        constant=truth_value, node=self, user_provided=True
                    ),
                    old_node=self,
                    side_effects=self.getVisitableNodes(),
                )

                return result, "new_constant", "Predicted dict 'in' truth value"

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
            # No side effects at all but from the children.
            result = []

            # The order of evaluation is different for "in" and "has_key", so we go
            # through visitable nodes.
            for child in self.getVisitableNodes():
                result.extend(child.extractSideEffects())

            return tuple(result)


class ExpressionDictOperationInNotInUncertainBase(
    ExpressionDictOperationInNotInUncertainMixin,
    ExpressionBoolShapeExactMixin,
    ChildrenHavingKeyDictArgMixin,
    ExpressionBase,
):
    # Follows the reversed nature of "in", with the dictionary on the right
    # side of things.
    named_children = ("key", "dict_arg")

    __slots__ = ("known_hashable_key",)

    def __init__(self, key, dict_arg, source_ref):
        ChildrenHavingKeyDictArgMixin.__init__(
            self,
            key=key,
            dict_arg=dict_arg,
        )

        ExpressionBase.__init__(self, source_ref)

        self.known_hashable_key = None


class ExpressionDictOperationIn(ExpressionDictOperationInNotInUncertainBase):
    kind = "EXPRESSION_DICT_OPERATION_IN"


class ExpressionDictOperationNotIn(ExpressionDictOperationInNotInUncertainBase):
    kind = "EXPRESSION_DICT_OPERATION_NOT_IN"


class ExpressionDictOperationHaskey(
    ExpressionDictOperationInNotInUncertainMixin,
    ExpressionDictOperationHaskeyBase,
):
    kind = "EXPRESSION_DICT_OPERATION_HASKEY"

    # Different order of arguments.
    named_children = ("dict_arg", "key")

    __slots__ = ("known_hashable_key",)

    def __init__(self, key, dict_arg, source_ref):
        ExpressionDictOperationHaskeyBase.__init__(
            self, key=key, dict_arg=dict_arg, source_ref=source_ref
        )

        self.known_hashable_key = None


class ExpressionDictOperationFromkeys2(ExpressionDictOperationFromkeys2Base):
    kind = "EXPRESSION_DICT_OPERATION_FROMKEYS2"

    def computeExpression(self, trace_collection):
        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        if self.subnode_iterable.isCompileTimeConstant():
            # TODO: Could be assert against it being None with a compile time constant,
            # we will usually be able to tell?
            # This is actually OK to use like this, pylint: disable=bad-chained-comparison
            if None is not self.subnode_iterable.getIterationLength() < 256:
                return trace_collection.getCompileTimeComputationResult(
                    node=self,
                    computation=lambda: dict.fromkeys(
                        self.subnode_iterable.getCompileTimeConstant()
                    ),
                    description="Computed 'dict.fromkeys' with constant value.",
                )

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_iterable.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    def mayRaiseExceptionOperation(self):
        # This is actually OK to use like this, pylint: disable=bad-chained-comparison
        return None is not self.subnode_iterable.getIterationLength() < 256


class ExpressionDictOperationFromkeys3(ExpressionDictOperationFromkeys3Base):
    kind = "EXPRESSION_DICT_OPERATION_FROMKEYS3"

    def computeExpression(self, trace_collection):
        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        if (
            self.subnode_iterable.isCompileTimeConstant()
            and self.subnode_value.isCompileTimeConstant()
        ):
            # TODO: Could be assert against it being None with a compile time constant,
            # we will usually be able to tell?
            # This is actually OK to use like this, pylint: disable=bad-chained-comparison
            if None is not self.subnode_iterable.getIterationLength() < 256:
                return trace_collection.getCompileTimeComputationResult(
                    node=self,
                    computation=lambda: dict.fromkeys(
                        self.subnode_iterable.getCompileTimeConstant(),
                        self.subnode_value.getCompileTimeConstant(),
                    ),
                    description="Computed 'dict.fromkeys' with constant values.",
                )

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_iterable.mayRaiseException(exception_type)
            or self.subnode_value.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    def mayRaiseExceptionOperation(self):
        # This is actually OK to use like this, pylint: disable=bad-chained-comparison
        return None is not self.subnode_iterable.getIterationLength() < 256


class ExpressionDictOperationFromkeysRef(ExpressionNoSideEffectsMixin, ExpressionBase):
    kind = "EXPRESSION_DICT_OPERATION_FROMKEYS_REF"

    def finalize(self):
        del self.parent

    def computeExpressionRaw(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        def wrapExpressionDictOperationFromkeys(iterable, value, source_ref):
            if value is None:
                return ExpressionDictOperationFromkeys2(
                    iterable=iterable, source_ref=source_ref
                )
            else:
                return ExpressionDictOperationFromkeys3(
                    iterable=iterable, value=value, source_ref=source_ref
                )

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationFromkeys,
            builtin_spec=dict_fromkeys_spec,
        )

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Call to 'dict.fromkeys' recognized.",
        )
