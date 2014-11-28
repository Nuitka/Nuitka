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
""" Attribute node

Knowing attributes of an object is very important, esp. when it comes to 'self'
and objects and classes.

There will be a method "computeExpressionAttribute" to aid predicting them.
"""

from .NodeBases import ExpressionChildrenHavingBase


class ExpressionAttributeLookup(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_ATTRIBUTE_LOOKUP"

    named_children = (
        "source",
    )

    def __init__(self, source, attribute_name, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "source" : source
            },
            source_ref = source_ref
        )

        self.attribute_name = attribute_name

    def getAttributeName(self):
        return self.attribute_name

    def setAttributeName(self, attribute_name):
        self.attribute_name = attribute_name

    def getDetails(self):
        return {
            "attribute" : self.getAttributeName()
        }

    def getDetail(self):
        return "attribute %s from %s" % (
            self.getAttributeName(),
            self.getLookupSource()
        )

    getLookupSource = ExpressionChildrenHavingBase.childGetter(
        "source"
    )

    def makeCloneAt(self, source_ref):
        return ExpressionAttributeLookup(
            source         = self.getLookupSource().makeCloneAt(source_ref),
            attribute_name = self.getAttributeName(),
            source_ref     = source_ref
        )

    def computeExpression(self, constraint_collection):
        lookup_source = self.getLookupSource()

        if lookup_source.willRaiseException(BaseException):
            return lookup_source, "new_raise", "Attribute lookup source raises exception."

        return lookup_source.computeExpressionAttribute(
            lookup_node           = self,
            attribute_name        = self.getAttributeName(),
            constraint_collection = constraint_collection
        )

    def isKnownToBeIterable(self, count):
        # TODO: Could be known.
        return None


class ExpressionSpecialAttributeLookup(ExpressionAttributeLookup):
    kind = "EXPRESSION_SPECIAL_ATTRIBUTE_LOOKUP"

    # TODO: Special lookups should be treated somehow different.
    def computeExpression(self, constraint_collection):
        lookup_source = self.getLookupSource()

        if lookup_source.willRaiseException(BaseException):
            return lookup_source, "new_raise", "Special attribute lookup source raises exception."

        # TODO: Special lookups may reuse "computeExpressionAttribute"
        return self, None, None


class ExpressionBuiltinGetattr(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_GETATTR"

    named_children = ("source", "attribute", "default")

    # Need to accept 'object' keyword argument, that is just the API of getattr,
    # pylint: disable=W0622

    def __init__(self, object, name, default, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "source"    : object,
                "attribute" : name,
                "default"   : default
            },
            source_ref = source_ref
        )

    getLookupSource = ExpressionChildrenHavingBase.childGetter("source")
    getAttribute = ExpressionChildrenHavingBase.childGetter("attribute")
    getDefault = ExpressionChildrenHavingBase.childGetter("default")

    def computeExpression(self, constraint_collection):
        default = self.getDefault()

        if default is None:
            attribute = self.getAttribute()

            attribute_name = attribute.getStringValue()

            if attribute_name is not None:
                source = self.getLookupSource()
                # If source has sideeffects, it must be evaluated, before the
                # lookup, meaning, a temporary variable should be assigned. For
                # now, we give up in this case. TODO: Replace source with a
                # temporary variable assignment as a side effect.

                side_effects = source.extractSideEffects()

                if not side_effects:
                    result = ExpressionAttributeLookup(
                        expression     = source,
                        attribute_name = attribute_name,
                        source_ref     = self.source_ref
                    )

                    from .NodeMakingHelpers import wrapExpressionWithNodeSideEffects

                    result = wrapExpressionWithNodeSideEffects(
                        new_node = result,
                        old_node = attribute
                    )

                    return (
                        result,
                        "new_expression",
                        """Replaced call to built-in 'getattr' with constant \
attribute '%s' to mere attribute lookup""" % attribute_name
                    )

        return self, None, None


class ExpressionBuiltinSetattr(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_SETATTR"

    named_children = ("source", "attribute", "value")

    # Need to accept 'object' keyword argument, that is just the API of setattr,
    # pylint: disable=W0622

    def __init__(self, object, name, value, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "source"    : object,
                "attribute" : name,
                "value"     : value
            },
            source_ref = source_ref
        )

    getLookupSource = ExpressionChildrenHavingBase.childGetter("source")
    getAttribute = ExpressionChildrenHavingBase.childGetter("attribute")
    getValue = ExpressionChildrenHavingBase.childGetter("value")

    def computeExpression(self, constraint_collection):
        # Note: Might be possible to predict or downgrade to mere attribute set.
        return self, None, None


class ExpressionBuiltinHasattr(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_HASATTR"

    named_children = ("source", "attribute")

    # Need to accept object keyword argument, that is just the API of hasattr,
    # pylint: disable=W0622

    def __init__(self, object, name, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "source"    : object,
                "attribute" : name,
            },
            source_ref = source_ref
        )

    getLookupSource = ExpressionChildrenHavingBase.childGetter("source")
    getAttribute = ExpressionChildrenHavingBase.childGetter("attribute")

    def computeExpression(self, constraint_collection):
        # Note: Might be possible to predict or downgrade to mere attribute
        # check.

        return self, None, None
