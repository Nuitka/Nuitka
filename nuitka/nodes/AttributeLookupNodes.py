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
""" Attribute lookup nodes, generic one and base for generated ones.

See AttributeNodes otherwise.
"""

from .ExpressionBases import ExpressionChildHavingBase


class ExpressionAttributeLookup(ExpressionChildHavingBase):
    """Looking up an attribute of an object.

    Typically code like: source.attribute_name
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP"

    named_child = "expression"
    __slots__ = ("attribute_name",)

    def __init__(self, expression, attribute_name, source_ref):
        ExpressionChildHavingBase.__init__(
            self, value=expression, source_ref=source_ref
        )

        self.attribute_name = attribute_name

    def getAttributeName(self):
        return self.attribute_name

    def getDetails(self):
        return {"attribute_name": self.attribute_name}

    def computeExpression(self, trace_collection):
        return self.subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name=self.attribute_name,
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(
            exception_type
        ) or self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name=self.attribute_name
        )

    @staticmethod
    def isKnownToBeIterable(count):
        # TODO: Could be known. We would need for computeExpressionAttribute to
        # either return a new node, or a decision maker.
        return None


class ExpressionAttributeLookupFixedBase(ExpressionChildHavingBase):
    """Looking up an attribute of an object.

    Typically code like: source.attribute_name
    """

    attribute_name = None

    named_child = "expression"

    def __init__(self, expression, source_ref):
        ExpressionChildHavingBase.__init__(
            self, value=expression, source_ref=source_ref
        )

    def getAttributeName(self):
        return self.attribute_name

    @staticmethod
    def getDetails():
        return {}

    def computeExpression(self, trace_collection):
        return self.subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name=self.attribute_name,
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(
            exception_type
        ) or self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name=self.attribute_name
        )

    @staticmethod
    def isKnownToBeIterable(count):
        # TODO: Could be known. We would need for computeExpressionAttribute to
        # either return a new node, or a decision maker.
        return None
