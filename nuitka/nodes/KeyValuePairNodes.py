#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Dictionary pairs, for use in dictionary building, calls, etc.

These represent the a=b part, as they occur in calls, and dictionary
values, but they do not form a dictionary. As a sequence, they can
have order.

"""

from abc import abstractmethod

from nuitka.PythonVersions import python_version

from .BuiltinHashNodes import ExpressionBuiltinHash
from .ChildrenHavingMixins import (
    ChildHavingValueMixin,
    ChildrenHavingKeyValueMixin,
    ChildrenHavingValueKeyMixin,
)
from .ConstantRefNodes import makeConstantRefNode
from .ExpressionBases import ExpressionBase, ExpressionNoSideEffectsMixin
from .NodeBases import SideEffectsFromChildrenMixin


class ExpressionKeyValuePairMixin(object):
    __slots__ = ()

    @staticmethod
    def isExpressionKeyValuePair():
        return True

    @abstractmethod
    def mayKeyRaiseException(self, exception_type):
        pass

    @abstractmethod
    def mayValueRaiseException(self, exception_type):
        pass

    @abstractmethod
    def getKeyNode(self):
        pass

    @abstractmethod
    def getValueNode(self):
        pass


class ExpressionKeyValuePairNonConstantMixin(ExpressionKeyValuePairMixin):
    __slots__ = ()

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

    def isKeyKnownToBeHashable(self):
        return self.subnode_key.isKnownToBeHashable()

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

    def isCompileTimeConstant(self):
        # Note: Values are more often not constant, short circuits faster this way around
        return (
            self.subnode_value.isCompileTimeConstant()
            and self.subnode_key.isCompileTimeConstant()
        )

    def isKeyExpressionConstantStrRef(self):
        return self.subnode_key.isKeyExpressionConstantStrRef()

    def getKeyCompileTimeConstant(self):
        return self.subnode_key.getCompileTimeConstant()

    def getValueCompileTimeConstant(self):
        return self.subnode_value.getCompileTimeConstant()

    def mayKeyRaiseException(self, exception_type):
        return self.subnode_key.mayRaiseException(exception_type)

    def mayValueRaiseException(self, exception_type):
        return self.subnode_value.mayRaiseException(exception_type)

    def getKeyNode(self):
        return self.subnode_key

    def getValueNode(self):
        return self.subnode_value

    def getCompatibleSourceReference(self):
        return self.subnode_value.getCompatibleSourceReference()


class ExpressionKeyValuePairOld(
    ExpressionKeyValuePairNonConstantMixin,
    SideEffectsFromChildrenMixin,
    ChildrenHavingValueKeyMixin,
    ExpressionBase,
):
    kind = "EXPRESSION_KEY_VALUE_PAIR_OLD"

    python_version_spec = "< 0x350"

    # They changed the order of evaluation only with Python >=3.5 to what you normally would expect.
    named_children = ("value", "key")

    def __init__(self, value, key, source_ref):
        ChildrenHavingValueKeyMixin.__init__(
            self,
            value=value,
            key=key,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionKeyValuePairNew(
    ExpressionKeyValuePairNonConstantMixin,
    SideEffectsFromChildrenMixin,
    ChildrenHavingKeyValueMixin,
    ExpressionBase,
):
    kind = "EXPRESSION_KEY_VALUE_PAIR_NEW"

    python_version_spec = ">= 0x350"

    # They changed the order of evaluation with 3.5 to what you normally would expect.
    named_children = ("key", "value")

    def __init__(self, key, value, source_ref):
        ChildrenHavingKeyValueMixin.__init__(
            self,
            key=key,
            value=value,
        )

        ExpressionBase.__init__(self, source_ref)


# Allow other code to forget about it.
if python_version < 0x350:
    ExpressionKeyValuePair = ExpressionKeyValuePairOld
else:
    ExpressionKeyValuePair = ExpressionKeyValuePairNew


class ExpressionKeyValuePairConstantKey(
    ExpressionKeyValuePairMixin,
    SideEffectsFromChildrenMixin,
    ChildHavingValueMixin,
    ExpressionBase,
):
    kind = "EXPRESSION_KEY_VALUE_PAIR_CONSTANT_KEY"

    named_children = ("value",)

    __slots__ = ("key",)

    def __init__(self, key, value, source_ref):
        ChildHavingValueMixin.__init__(self, value=value)

        ExpressionBase.__init__(self, source_ref)

        self.key = key

    def getDetails(self):
        return {"key": self.key}

    @staticmethod
    def isKeyKnownToBeHashable():
        return True

    def computeExpression(self, trace_collection):
        # Nothing to do, we are hashable and everything.
        return self, None, None

    def mayRaiseException(self, exception_type):
        return self.subnode_value.mayRaiseException(exception_type)

    def extractSideEffects(self):
        return self.subnode_value.extractSideEffects()

    def onContentEscapes(self, trace_collection):
        self.subnode_value.onContentEscapes(trace_collection)

    def isCompileTimeConstant(self):
        return self.subnode_value.isCompileTimeConstant()

    def isKeyExpressionConstantStrRef(self):
        return type(self.key) is str

    def getKeyCompileTimeConstant(self):
        return self.key

    def getValueCompileTimeConstant(self):
        return self.subnode_value.getCompileTimeConstant()

    @staticmethod
    def mayKeyRaiseException(exception_type):
        # pylint: disable
        return False

    def mayValueRaiseException(self, exception_type):
        return self.subnode_value.mayRaiseException(exception_type)

    def getKeyNode(self):
        return makeConstantRefNode(constant=self.key, source_ref=self.source_ref)

    def getValueNode(self):
        return self.subnode_value

    def getCompatibleSourceReference(self):
        return self.subnode_value.getCompatibleSourceReference()


class ExpressionKeyValuePairConstantKeyValue(
    ExpressionKeyValuePairMixin, ExpressionNoSideEffectsMixin, ExpressionBase
):
    kind = "EXPRESSION_KEY_VALUE_PAIR_CONSTANT_KEY_VALUE"

    __slots__ = ("key", "value")

    def __init__(self, key, value, source_ref):
        self.key = key
        self.value = value

        ExpressionBase.__init__(self, source_ref)

    def finalize(self):
        del self.key
        del self.value

    def getDetails(self):
        return {"key": self.key, "value": self.value}

    @staticmethod
    def isKeyKnownToBeHashable():
        return True

    def computeExpressionRaw(self, trace_collection):
        # Nothing to do, we are hashable and everything.
        return self, None, None

    @staticmethod
    def isCompileTimeConstant():
        return True

    def isKeyExpressionConstantStrRef(self):
        return type(self.key) is str

    def getKeyCompileTimeConstant(self):
        return self.key

    def getValueCompileTimeConstant(self):
        return self.value

    @staticmethod
    def mayKeyRaiseException(exception_type):
        return False

    def mayValueRaiseException(self, exception_type):
        return self.subnode_value.mayRaiseException(exception_type)

    def getKeyNode(self):
        return makeConstantRefNode(
            constant=self.key, source_ref=self.source_ref, user_provided=True
        )

    def getValueNode(self):
        # TODO: Actually trace user provided for the key/value too, but
        # it seems excessive now.
        return makeConstantRefNode(
            constant=self.value, source_ref=self.source_ref, user_provided=True
        )


def makeExpressionPairs(keys, values):
    assert len(keys) == len(values)

    return tuple(
        makeExpressionKeyValuePair(key=key, value=value)
        for key, value in zip(keys, values)
    )


def makeExpressionKeyValuePair(key, value):
    # Detect constant key value that is hashable and use preferred node type for that.
    if key.isCompileTimeConstant() and key.isKnownToBeHashable():
        return makeExpressionKeyValuePairConstantKey(
            key=key.getCompileTimeConstant(), value=value
        )
    else:
        return ExpressionKeyValuePair(
            key=key,
            value=value,
            source_ref=value.getSourceReference(),
        )


def makeExpressionKeyValuePairConstantKey(key, value):
    if value.isCompileTimeConstant():
        return ExpressionKeyValuePairConstantKeyValue(
            key=key,
            value=value.getCompileTimeConstant(),
            source_ref=value.getSourceReference(),
        )
    else:
        return ExpressionKeyValuePairConstantKey(
            key=key,
            value=value,
            source_ref=value.getSourceReference(),
        )


def makeKeyValuePairExpressionsFromKwArgs(pairs):
    return tuple(
        makeExpressionKeyValuePairConstantKey(
            key=key,
            value=value,
        )
        for key, value in pairs
    )


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
