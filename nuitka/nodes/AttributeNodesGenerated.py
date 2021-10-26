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
"""Specialized attribute nodes

WARNING, this code is GENERATED. Modify the template AttributeNodeFixed.py.j2 instead!"""
from nuitka.specs.BuiltinParameterSpecs import extractBuiltinArgs

from .AttributeLookupNodes import ExpressionAttributeLookupFixedBase
from .NodeBases import SideEffectsFromChildrenMixin

attribute_classes = {}


class ExpressionAttributeLookupFixedItems(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value Items of an object.

    Typically code like: source.items
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ITEMS"
    attribute_name = "items"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            result = ExpressionAttributeLookupDictItems(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'items' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="items",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="items"
        )


attribute_classes["items"] = ExpressionAttributeLookupFixedItems


from nuitka.specs.BuiltinDictOperationSpecs import dict_items_spec


class ExpressionAttributeLookupDictItems(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedItems
):
    """Attribute Items lookup on a dict.

    Typically code like: some_dict.items
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_ITEMS"
    attribute_name = "items"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationItems(source_ref):
            if str is bytes:
                from .DictionaryNodes import ExpressionDictOperationItems

                return ExpressionDictOperationItems(
                    dict_arg=self.subnode_expression, source_ref=source_ref
                )
            else:
                from .DictionaryNodes import ExpressionDictOperationIteritems

                return ExpressionDictOperationIteritems(
                    dict_arg=self.subnode_expression, source_ref=source_ref
                )

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationItems,
            builtin_spec=dict_items_spec,
        )

        return result, "new_expression", "Call to 'items' of dictionary recognized."


class ExpressionAttributeLookupFixedIteritems(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value Iteritems of an object.

    Typically code like: source.iteritems
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ITERITEMS"
    attribute_name = "iteritems"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is bytes and subnode_expression.hasShapeDictionaryExact():
            result = ExpressionAttributeLookupDictIteritems(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'iteritems' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="iteritems",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="iteritems"
        )


attribute_classes["iteritems"] = ExpressionAttributeLookupFixedIteritems


from nuitka.specs.BuiltinDictOperationSpecs import dict_iteritems_spec


class ExpressionAttributeLookupDictIteritems(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIteritems
):
    """Attribute Iteritems lookup on a dict.

    Typically code like: some_dict.iteritems
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_ITERITEMS"
    attribute_name = "iteritems"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationIteritems(source_ref):
            from .DictionaryNodes import ExpressionDictOperationIteritems

            return ExpressionDictOperationIteritems(
                dict_arg=self.subnode_expression, source_ref=source_ref
            )

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationIteritems,
            builtin_spec=dict_iteritems_spec,
        )

        return result, "new_expression", "Call to 'iteritems' of dictionary recognized."
