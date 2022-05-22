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
""" Dictionary pairs, for use in dictionary building, calls, etc.

"""

from nuitka.PythonVersions import python_version

from .BuiltinHashNodes import ExpressionBuiltinHash
from .ConstantRefNodes import makeConstantRefNode
from .ExpressionBases import (
    ExpressionChildHavingBase,
    ExpressionChildrenHavingBase,
)
from .NodeBases import SideEffectsFromChildrenMixin


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

    def isCompileTimeConstant(self):
        # Note: Values are more often not constant, short circuits faster this way around
        return (
            self.subnode_value.isCompileTimeConstant()
            and self.subnode_key.isCompileTimeConstant()
        )


class ExpressionKeyValuePairConstantKey(
    SideEffectsFromChildrenMixin, ExpressionChildHavingBase
):
    kind = "EXPRESSION_KEY_VALUE_PAIR_CONSTANT_KEY"

    named_child = "value"

    def __init__(self, key, value, source_ref):
        ExpressionChildHavingBase.__init__(self, value=value, source_ref=source_ref)

        self.key = key

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


def makeExpressionPairs(keys, values):
    assert len(keys) == len(values)

    return tuple(
        ExpressionKeyValuePair(
            key=key, value=value, source_ref=key.getSourceReference()
        )
        for key, value in zip(keys, values)
    )


def makeExpressionKeyValuePair(key, value):
    # TODO: Detect constant key value
    return ExpressionKeyValuePair(
        key=key,
        value=value,
        source_ref=value.getSourceReference(),
    )


def makeExpressionKeyValuePairConstantKey(key, value):
    # TODO: Make use of ExpressionKeyValuePairConstantKey
    return ExpressionKeyValuePair(
        key=makeConstantRefNode(
            constant=key, source_ref=value.getSourceReference(), user_provided=True
        ),
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
