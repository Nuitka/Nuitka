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

WARNING, this code is GENERATED. Modify the template AttributeNodeFixed.py.j2 instead!
"""

from nuitka.specs.BuiltinParameterSpecs import extractBuiltinArgs

from .AttributeLookupNodes import ExpressionAttributeLookupFixedBase
from .NodeBases import SideEffectsFromChildrenMixin

attribute_classes = {}
attribute_typed_classes = set()


class ExpressionAttributeLookupFixedCapitalize(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'capitalize' of an object.

    Typically code like: source.capitalize
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_CAPITALIZE"
    attribute_name = "capitalize"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrCapitalize(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'capitalize' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="capitalize",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="capitalize"
        )


attribute_classes["capitalize"] = ExpressionAttributeLookupFixedCapitalize


from nuitka.specs.BuiltinStrOperationSpecs import str_capitalize_spec


class ExpressionAttributeLookupStrCapitalize(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedCapitalize
):
    """Attribute Capitalize lookup on a str.

    Typically code like: some_str.capitalize
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_CAPITALIZE"
    attribute_name = "capitalize"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationCapitalize(source_ref):
            from .StrNodes import ExpressionStrOperationCapitalize

            return ExpressionStrOperationCapitalize(
                str_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationCapitalize,
            builtin_spec=str_capitalize_spec,
        )

        return result, "new_expression", "Call to 'capitalize' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrCapitalize)


class ExpressionAttributeLookupFixedCasefold(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'casefold' of an object.

    Typically code like: source.casefold
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_CASEFOLD"
    attribute_name = "casefold"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is not bytes and subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrCasefold(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'casefold' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="casefold",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="casefold"
        )


attribute_classes["casefold"] = ExpressionAttributeLookupFixedCasefold


class ExpressionAttributeLookupStrCasefold(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedCasefold
):
    """Attribute Casefold lookup on a str.

    Typically code like: some_str.casefold
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_CASEFOLD"
    attribute_name = "casefold"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as str operation ExpressionStrOperationCasefold is not yet implemented


attribute_typed_classes.add(ExpressionAttributeLookupStrCasefold)


class ExpressionAttributeLookupFixedCenter(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'center' of an object.

    Typically code like: source.center
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_CENTER"
    attribute_name = "center"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrCenter(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'center' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="center",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="center"
        )


attribute_classes["center"] = ExpressionAttributeLookupFixedCenter


class ExpressionAttributeLookupStrCenter(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedCenter
):
    """Attribute Center lookup on a str.

    Typically code like: some_str.center
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_CENTER"
    attribute_name = "center"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as str operation ExpressionStrOperationCenter is not yet implemented


attribute_typed_classes.add(ExpressionAttributeLookupStrCenter)


class ExpressionAttributeLookupFixedClear(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'clear' of an object.

    Typically code like: source.clear
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_CLEAR"
    attribute_name = "clear"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            return trace_collection.computedExpressionResult(
                expression=ExpressionAttributeLookupDictClear(
                    expression=subnode_expression, source_ref=self.source_ref
                ),
                change_tags="new_expression",
                change_desc="Attribute lookup 'clear' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="clear",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="clear"
        )


attribute_classes["clear"] = ExpressionAttributeLookupFixedClear


from nuitka.specs.BuiltinDictOperationSpecs import dict_clear_spec


class ExpressionAttributeLookupDictClear(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedClear
):
    """Attribute Clear lookup on a dict.

    Typically code like: some_dict.clear
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_CLEAR"
    attribute_name = "clear"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationClear(source_ref):
            from .DictionaryNodes import ExpressionDictOperationClear

            return ExpressionDictOperationClear(
                dict_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationClear,
            builtin_spec=dict_clear_spec,
        )

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Call to 'clear' of dictionary recognized.",
        )


attribute_typed_classes.add(ExpressionAttributeLookupDictClear)


class ExpressionAttributeLookupFixedCopy(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'copy' of an object.

    Typically code like: source.copy
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_COPY"
    attribute_name = "copy"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            return trace_collection.computedExpressionResult(
                expression=ExpressionAttributeLookupDictCopy(
                    expression=subnode_expression, source_ref=self.source_ref
                ),
                change_tags="new_expression",
                change_desc="Attribute lookup 'copy' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="copy",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="copy"
        )


attribute_classes["copy"] = ExpressionAttributeLookupFixedCopy


from nuitka.specs.BuiltinDictOperationSpecs import dict_copy_spec


class ExpressionAttributeLookupDictCopy(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedCopy
):
    """Attribute Copy lookup on a dict.

    Typically code like: some_dict.copy
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_COPY"
    attribute_name = "copy"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationCopy(source_ref):
            from .DictionaryNodes import ExpressionDictOperationCopy

            return ExpressionDictOperationCopy(
                dict_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationCopy,
            builtin_spec=dict_copy_spec,
        )

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Call to 'copy' of dictionary recognized.",
        )


attribute_typed_classes.add(ExpressionAttributeLookupDictCopy)


class ExpressionAttributeLookupFixedCount(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'count' of an object.

    Typically code like: source.count
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_COUNT"
    attribute_name = "count"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrCount(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'count' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="count",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="count"
        )


attribute_classes["count"] = ExpressionAttributeLookupFixedCount


class ExpressionAttributeLookupStrCount(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedCount
):
    """Attribute Count lookup on a str.

    Typically code like: some_str.count
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_COUNT"
    attribute_name = "count"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as str operation ExpressionStrOperationCount is not yet implemented


attribute_typed_classes.add(ExpressionAttributeLookupStrCount)


class ExpressionAttributeLookupFixedDecode(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'decode' of an object.

    Typically code like: source.decode
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_DECODE"
    attribute_name = "decode"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is bytes and subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrDecode(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'decode' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="decode",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="decode"
        )


attribute_classes["decode"] = ExpressionAttributeLookupFixedDecode


from nuitka.specs.BuiltinStrOperationSpecs import str_decode_spec


class ExpressionAttributeLookupStrDecode(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedDecode
):
    """Attribute Decode lookup on a str.

    Typically code like: some_str.decode
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_DECODE"
    attribute_name = "decode"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationDecode(encoding, errors, source_ref):
            if errors is not None:
                from .StrNodes import ExpressionStrOperationDecode3

                return ExpressionStrOperationDecode3(
                    str_arg=self.subnode_expression,
                    encoding=encoding,
                    errors=errors,
                    source_ref=source_ref,
                )
            elif encoding is not None:
                from .StrNodes import ExpressionStrOperationDecode2

                return ExpressionStrOperationDecode2(
                    str_arg=self.subnode_expression,
                    encoding=encoding,
                    source_ref=source_ref,
                )
            else:
                from .StrNodes import ExpressionStrOperationDecode1

                return ExpressionStrOperationDecode1(
                    str_arg=self.subnode_expression, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationDecode,
            builtin_spec=str_decode_spec,
        )

        return result, "new_expression", "Call to 'decode' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrDecode)


class ExpressionAttributeLookupFixedEncode(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'encode' of an object.

    Typically code like: source.encode
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ENCODE"
    attribute_name = "encode"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrEncode(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'encode' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="encode",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="encode"
        )


attribute_classes["encode"] = ExpressionAttributeLookupFixedEncode


from nuitka.specs.BuiltinStrOperationSpecs import str_encode_spec


class ExpressionAttributeLookupStrEncode(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedEncode
):
    """Attribute Encode lookup on a str.

    Typically code like: some_str.encode
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ENCODE"
    attribute_name = "encode"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationEncode(encoding, errors, source_ref):
            if errors is not None:
                from .StrNodes import ExpressionStrOperationEncode3

                return ExpressionStrOperationEncode3(
                    str_arg=self.subnode_expression,
                    encoding=encoding,
                    errors=errors,
                    source_ref=source_ref,
                )
            elif encoding is not None:
                from .StrNodes import ExpressionStrOperationEncode2

                return ExpressionStrOperationEncode2(
                    str_arg=self.subnode_expression,
                    encoding=encoding,
                    source_ref=source_ref,
                )
            else:
                from .StrNodes import ExpressionStrOperationEncode1

                return ExpressionStrOperationEncode1(
                    str_arg=self.subnode_expression, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationEncode,
            builtin_spec=str_encode_spec,
        )

        return result, "new_expression", "Call to 'encode' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrEncode)


class ExpressionAttributeLookupFixedEndswith(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'endswith' of an object.

    Typically code like: source.endswith
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ENDSWITH"
    attribute_name = "endswith"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrEndswith(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'endswith' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="endswith",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="endswith"
        )


attribute_classes["endswith"] = ExpressionAttributeLookupFixedEndswith


from nuitka.specs.BuiltinStrOperationSpecs import str_endswith_spec


class ExpressionAttributeLookupStrEndswith(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedEndswith
):
    """Attribute Endswith lookup on a str.

    Typically code like: some_str.endswith
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ENDSWITH"
    attribute_name = "endswith"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationEndswith(suffix, start, end, source_ref):
            if end is not None:
                from .StrNodes import ExpressionStrOperationEndswith4

                return ExpressionStrOperationEndswith4(
                    str_arg=self.subnode_expression,
                    suffix=suffix,
                    start=start,
                    end=end,
                    source_ref=source_ref,
                )
            elif start is not None:
                from .StrNodes import ExpressionStrOperationEndswith3

                return ExpressionStrOperationEndswith3(
                    str_arg=self.subnode_expression,
                    suffix=suffix,
                    start=start,
                    source_ref=source_ref,
                )
            else:
                from .StrNodes import ExpressionStrOperationEndswith2

                return ExpressionStrOperationEndswith2(
                    str_arg=self.subnode_expression,
                    suffix=suffix,
                    source_ref=source_ref,
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationEndswith,
            builtin_spec=str_endswith_spec,
        )

        return result, "new_expression", "Call to 'endswith' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrEndswith)


class ExpressionAttributeLookupFixedExpandtabs(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'expandtabs' of an object.

    Typically code like: source.expandtabs
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_EXPANDTABS"
    attribute_name = "expandtabs"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrExpandtabs(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'expandtabs' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="expandtabs",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="expandtabs"
        )


attribute_classes["expandtabs"] = ExpressionAttributeLookupFixedExpandtabs


class ExpressionAttributeLookupStrExpandtabs(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedExpandtabs
):
    """Attribute Expandtabs lookup on a str.

    Typically code like: some_str.expandtabs
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_EXPANDTABS"
    attribute_name = "expandtabs"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as str operation ExpressionStrOperationExpandtabs is not yet implemented


attribute_typed_classes.add(ExpressionAttributeLookupStrExpandtabs)


class ExpressionAttributeLookupFixedFind(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'find' of an object.

    Typically code like: source.find
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_FIND"
    attribute_name = "find"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrFind(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'find' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="find",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="find"
        )


attribute_classes["find"] = ExpressionAttributeLookupFixedFind


from nuitka.specs.BuiltinStrOperationSpecs import str_find_spec


class ExpressionAttributeLookupStrFind(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedFind
):
    """Attribute Find lookup on a str.

    Typically code like: some_str.find
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_FIND"
    attribute_name = "find"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationFind(sub, start, end, source_ref):
            if end is not None:
                from .StrNodes import ExpressionStrOperationFind4

                return ExpressionStrOperationFind4(
                    str_arg=self.subnode_expression,
                    sub=sub,
                    start=start,
                    end=end,
                    source_ref=source_ref,
                )
            elif start is not None:
                from .StrNodes import ExpressionStrOperationFind3

                return ExpressionStrOperationFind3(
                    str_arg=self.subnode_expression,
                    sub=sub,
                    start=start,
                    source_ref=source_ref,
                )
            else:
                from .StrNodes import ExpressionStrOperationFind2

                return ExpressionStrOperationFind2(
                    str_arg=self.subnode_expression, sub=sub, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationFind,
            builtin_spec=str_find_spec,
        )

        return result, "new_expression", "Call to 'find' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrFind)


class ExpressionAttributeLookupFixedFormat(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'format' of an object.

    Typically code like: source.format
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_FORMAT"
    attribute_name = "format"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrFormat(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'format' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="format",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="format"
        )


attribute_classes["format"] = ExpressionAttributeLookupFixedFormat


class ExpressionAttributeLookupStrFormat(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedFormat
):
    """Attribute Format lookup on a str.

    Typically code like: some_str.format
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_FORMAT"
    attribute_name = "format"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as str operation ExpressionStrOperationFormat is not yet implemented


attribute_typed_classes.add(ExpressionAttributeLookupStrFormat)


class ExpressionAttributeLookupFixedFormatmap(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'format_map' of an object.

    Typically code like: source.format_map
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_FORMATMAP"
    attribute_name = "format_map"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is not bytes and subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrFormatmap(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'format_map' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="format_map",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="format_map"
        )


attribute_classes["format_map"] = ExpressionAttributeLookupFixedFormatmap


class ExpressionAttributeLookupStrFormatmap(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedFormatmap
):
    """Attribute Formatmap lookup on a str.

    Typically code like: some_str.format_map
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_FORMATMAP"
    attribute_name = "format_map"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as str operation ExpressionStrOperationFormatmap is not yet implemented


attribute_typed_classes.add(ExpressionAttributeLookupStrFormatmap)


class ExpressionAttributeLookupFixedFromkeys(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'fromkeys' of an object.

    Typically code like: source.fromkeys
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_FROMKEYS"
    attribute_name = "fromkeys"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            return trace_collection.computedExpressionResult(
                expression=ExpressionAttributeLookupDictFromkeys(
                    expression=subnode_expression, source_ref=self.source_ref
                ),
                change_tags="new_expression",
                change_desc="Attribute lookup 'fromkeys' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="fromkeys",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="fromkeys"
        )


attribute_classes["fromkeys"] = ExpressionAttributeLookupFixedFromkeys


class ExpressionAttributeLookupDictFromkeys(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedFromkeys
):
    """Attribute Fromkeys lookup on a dict.

    Typically code like: some_dict.fromkeys
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_FROMKEYS"
    attribute_name = "fromkeys"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as dict operation ExpressionDictOperationFromkeys is not yet implemented


attribute_typed_classes.add(ExpressionAttributeLookupDictFromkeys)


class ExpressionAttributeLookupFixedGet(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'get' of an object.

    Typically code like: source.get
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_GET"
    attribute_name = "get"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            return trace_collection.computedExpressionResult(
                expression=ExpressionAttributeLookupDictGet(
                    expression=subnode_expression, source_ref=self.source_ref
                ),
                change_tags="new_expression",
                change_desc="Attribute lookup 'get' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="get",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="get"
        )


attribute_classes["get"] = ExpressionAttributeLookupFixedGet


from nuitka.specs.BuiltinDictOperationSpecs import dict_get_spec


class ExpressionAttributeLookupDictGet(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedGet
):
    """Attribute Get lookup on a dict.

    Typically code like: some_dict.get
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_GET"
    attribute_name = "get"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationGet(key, default, source_ref):
            if default is not None:
                from .DictionaryNodes import ExpressionDictOperationGet3

                return ExpressionDictOperationGet3(
                    dict_arg=self.subnode_expression,
                    key=key,
                    default=default,
                    source_ref=source_ref,
                )
            else:
                from .DictionaryNodes import ExpressionDictOperationGet2

                return ExpressionDictOperationGet2(
                    dict_arg=self.subnode_expression, key=key, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationGet,
            builtin_spec=dict_get_spec,
        )

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Call to 'get' of dictionary recognized.",
        )


attribute_typed_classes.add(ExpressionAttributeLookupDictGet)


class ExpressionAttributeLookupFixedHaskey(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'has_key' of an object.

    Typically code like: source.has_key
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_HASKEY"
    attribute_name = "has_key"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is bytes and subnode_expression.hasShapeDictionaryExact():
            return trace_collection.computedExpressionResult(
                expression=ExpressionAttributeLookupDictHaskey(
                    expression=subnode_expression, source_ref=self.source_ref
                ),
                change_tags="new_expression",
                change_desc="Attribute lookup 'has_key' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="has_key",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="has_key"
        )


attribute_classes["has_key"] = ExpressionAttributeLookupFixedHaskey


from nuitka.specs.BuiltinDictOperationSpecs import dict_has_key_spec


class ExpressionAttributeLookupDictHaskey(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedHaskey
):
    """Attribute Haskey lookup on a dict.

    Typically code like: some_dict.has_key
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_HASKEY"
    attribute_name = "has_key"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationHaskey(key, source_ref):
            from .DictionaryNodes import ExpressionDictOperationHaskey

            return ExpressionDictOperationHaskey(
                dict_arg=self.subnode_expression, key=key, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationHaskey,
            builtin_spec=dict_has_key_spec,
        )

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Call to 'has_key' of dictionary recognized.",
        )


attribute_typed_classes.add(ExpressionAttributeLookupDictHaskey)


class ExpressionAttributeLookupFixedIndex(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'index' of an object.

    Typically code like: source.index
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_INDEX"
    attribute_name = "index"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrIndex(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'index' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="index",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="index"
        )


attribute_classes["index"] = ExpressionAttributeLookupFixedIndex


from nuitka.specs.BuiltinStrOperationSpecs import str_index_spec


class ExpressionAttributeLookupStrIndex(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIndex
):
    """Attribute Index lookup on a str.

    Typically code like: some_str.index
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_INDEX"
    attribute_name = "index"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationIndex(sub, start, end, source_ref):
            if end is not None:
                from .StrNodes import ExpressionStrOperationIndex4

                return ExpressionStrOperationIndex4(
                    str_arg=self.subnode_expression,
                    sub=sub,
                    start=start,
                    end=end,
                    source_ref=source_ref,
                )
            elif start is not None:
                from .StrNodes import ExpressionStrOperationIndex3

                return ExpressionStrOperationIndex3(
                    str_arg=self.subnode_expression,
                    sub=sub,
                    start=start,
                    source_ref=source_ref,
                )
            else:
                from .StrNodes import ExpressionStrOperationIndex2

                return ExpressionStrOperationIndex2(
                    str_arg=self.subnode_expression, sub=sub, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationIndex,
            builtin_spec=str_index_spec,
        )

        return result, "new_expression", "Call to 'index' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrIndex)


class ExpressionAttributeLookupFixedIsalnum(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'isalnum' of an object.

    Typically code like: source.isalnum
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ISALNUM"
    attribute_name = "isalnum"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrIsalnum(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'isalnum' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="isalnum",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="isalnum"
        )


attribute_classes["isalnum"] = ExpressionAttributeLookupFixedIsalnum


from nuitka.specs.BuiltinStrOperationSpecs import str_isalnum_spec


class ExpressionAttributeLookupStrIsalnum(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIsalnum
):
    """Attribute Isalnum lookup on a str.

    Typically code like: some_str.isalnum
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISALNUM"
    attribute_name = "isalnum"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationIsalnum(source_ref):
            from .StrNodes import ExpressionStrOperationIsalnum

            return ExpressionStrOperationIsalnum(
                str_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationIsalnum,
            builtin_spec=str_isalnum_spec,
        )

        return result, "new_expression", "Call to 'isalnum' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrIsalnum)


class ExpressionAttributeLookupFixedIsalpha(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'isalpha' of an object.

    Typically code like: source.isalpha
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ISALPHA"
    attribute_name = "isalpha"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrIsalpha(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'isalpha' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="isalpha",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="isalpha"
        )


attribute_classes["isalpha"] = ExpressionAttributeLookupFixedIsalpha


from nuitka.specs.BuiltinStrOperationSpecs import str_isalpha_spec


class ExpressionAttributeLookupStrIsalpha(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIsalpha
):
    """Attribute Isalpha lookup on a str.

    Typically code like: some_str.isalpha
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISALPHA"
    attribute_name = "isalpha"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationIsalpha(source_ref):
            from .StrNodes import ExpressionStrOperationIsalpha

            return ExpressionStrOperationIsalpha(
                str_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationIsalpha,
            builtin_spec=str_isalpha_spec,
        )

        return result, "new_expression", "Call to 'isalpha' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrIsalpha)


class ExpressionAttributeLookupFixedIsascii(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'isascii' of an object.

    Typically code like: source.isascii
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ISASCII"
    attribute_name = "isascii"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is not bytes and subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrIsascii(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'isascii' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="isascii",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="isascii"
        )


attribute_classes["isascii"] = ExpressionAttributeLookupFixedIsascii


class ExpressionAttributeLookupStrIsascii(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIsascii
):
    """Attribute Isascii lookup on a str.

    Typically code like: some_str.isascii
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISASCII"
    attribute_name = "isascii"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as str operation ExpressionStrOperationIsascii is not yet implemented


attribute_typed_classes.add(ExpressionAttributeLookupStrIsascii)


class ExpressionAttributeLookupFixedIsdecimal(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'isdecimal' of an object.

    Typically code like: source.isdecimal
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ISDECIMAL"
    attribute_name = "isdecimal"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is not bytes and subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrIsdecimal(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'isdecimal' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="isdecimal",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="isdecimal"
        )


attribute_classes["isdecimal"] = ExpressionAttributeLookupFixedIsdecimal


class ExpressionAttributeLookupStrIsdecimal(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIsdecimal
):
    """Attribute Isdecimal lookup on a str.

    Typically code like: some_str.isdecimal
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISDECIMAL"
    attribute_name = "isdecimal"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as str operation ExpressionStrOperationIsdecimal is not yet implemented


attribute_typed_classes.add(ExpressionAttributeLookupStrIsdecimal)


class ExpressionAttributeLookupFixedIsdigit(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'isdigit' of an object.

    Typically code like: source.isdigit
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ISDIGIT"
    attribute_name = "isdigit"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrIsdigit(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'isdigit' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="isdigit",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="isdigit"
        )


attribute_classes["isdigit"] = ExpressionAttributeLookupFixedIsdigit


from nuitka.specs.BuiltinStrOperationSpecs import str_isdigit_spec


class ExpressionAttributeLookupStrIsdigit(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIsdigit
):
    """Attribute Isdigit lookup on a str.

    Typically code like: some_str.isdigit
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISDIGIT"
    attribute_name = "isdigit"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationIsdigit(source_ref):
            from .StrNodes import ExpressionStrOperationIsdigit

            return ExpressionStrOperationIsdigit(
                str_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationIsdigit,
            builtin_spec=str_isdigit_spec,
        )

        return result, "new_expression", "Call to 'isdigit' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrIsdigit)


class ExpressionAttributeLookupFixedIsidentifier(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'isidentifier' of an object.

    Typically code like: source.isidentifier
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ISIDENTIFIER"
    attribute_name = "isidentifier"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is not bytes and subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrIsidentifier(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'isidentifier' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="isidentifier",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="isidentifier"
        )


attribute_classes["isidentifier"] = ExpressionAttributeLookupFixedIsidentifier


class ExpressionAttributeLookupStrIsidentifier(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIsidentifier
):
    """Attribute Isidentifier lookup on a str.

    Typically code like: some_str.isidentifier
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISIDENTIFIER"
    attribute_name = "isidentifier"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as str operation ExpressionStrOperationIsidentifier is not yet implemented


attribute_typed_classes.add(ExpressionAttributeLookupStrIsidentifier)


class ExpressionAttributeLookupFixedIslower(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'islower' of an object.

    Typically code like: source.islower
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ISLOWER"
    attribute_name = "islower"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrIslower(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'islower' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="islower",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="islower"
        )


attribute_classes["islower"] = ExpressionAttributeLookupFixedIslower


from nuitka.specs.BuiltinStrOperationSpecs import str_islower_spec


class ExpressionAttributeLookupStrIslower(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIslower
):
    """Attribute Islower lookup on a str.

    Typically code like: some_str.islower
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISLOWER"
    attribute_name = "islower"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationIslower(source_ref):
            from .StrNodes import ExpressionStrOperationIslower

            return ExpressionStrOperationIslower(
                str_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationIslower,
            builtin_spec=str_islower_spec,
        )

        return result, "new_expression", "Call to 'islower' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrIslower)


class ExpressionAttributeLookupFixedIsnumeric(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'isnumeric' of an object.

    Typically code like: source.isnumeric
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ISNUMERIC"
    attribute_name = "isnumeric"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is not bytes and subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrIsnumeric(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'isnumeric' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="isnumeric",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="isnumeric"
        )


attribute_classes["isnumeric"] = ExpressionAttributeLookupFixedIsnumeric


class ExpressionAttributeLookupStrIsnumeric(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIsnumeric
):
    """Attribute Isnumeric lookup on a str.

    Typically code like: some_str.isnumeric
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISNUMERIC"
    attribute_name = "isnumeric"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as str operation ExpressionStrOperationIsnumeric is not yet implemented


attribute_typed_classes.add(ExpressionAttributeLookupStrIsnumeric)


class ExpressionAttributeLookupFixedIsprintable(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'isprintable' of an object.

    Typically code like: source.isprintable
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ISPRINTABLE"
    attribute_name = "isprintable"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is not bytes and subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrIsprintable(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'isprintable' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="isprintable",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="isprintable"
        )


attribute_classes["isprintable"] = ExpressionAttributeLookupFixedIsprintable


class ExpressionAttributeLookupStrIsprintable(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIsprintable
):
    """Attribute Isprintable lookup on a str.

    Typically code like: some_str.isprintable
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISPRINTABLE"
    attribute_name = "isprintable"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as str operation ExpressionStrOperationIsprintable is not yet implemented


attribute_typed_classes.add(ExpressionAttributeLookupStrIsprintable)


class ExpressionAttributeLookupFixedIsspace(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'isspace' of an object.

    Typically code like: source.isspace
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ISSPACE"
    attribute_name = "isspace"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrIsspace(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'isspace' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="isspace",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="isspace"
        )


attribute_classes["isspace"] = ExpressionAttributeLookupFixedIsspace


from nuitka.specs.BuiltinStrOperationSpecs import str_isspace_spec


class ExpressionAttributeLookupStrIsspace(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIsspace
):
    """Attribute Isspace lookup on a str.

    Typically code like: some_str.isspace
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISSPACE"
    attribute_name = "isspace"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationIsspace(source_ref):
            from .StrNodes import ExpressionStrOperationIsspace

            return ExpressionStrOperationIsspace(
                str_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationIsspace,
            builtin_spec=str_isspace_spec,
        )

        return result, "new_expression", "Call to 'isspace' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrIsspace)


class ExpressionAttributeLookupFixedIstitle(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'istitle' of an object.

    Typically code like: source.istitle
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ISTITLE"
    attribute_name = "istitle"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrIstitle(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'istitle' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="istitle",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="istitle"
        )


attribute_classes["istitle"] = ExpressionAttributeLookupFixedIstitle


from nuitka.specs.BuiltinStrOperationSpecs import str_istitle_spec


class ExpressionAttributeLookupStrIstitle(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIstitle
):
    """Attribute Istitle lookup on a str.

    Typically code like: some_str.istitle
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISTITLE"
    attribute_name = "istitle"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationIstitle(source_ref):
            from .StrNodes import ExpressionStrOperationIstitle

            return ExpressionStrOperationIstitle(
                str_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationIstitle,
            builtin_spec=str_istitle_spec,
        )

        return result, "new_expression", "Call to 'istitle' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrIstitle)


class ExpressionAttributeLookupFixedIsupper(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'isupper' of an object.

    Typically code like: source.isupper
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ISUPPER"
    attribute_name = "isupper"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrIsupper(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'isupper' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="isupper",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="isupper"
        )


attribute_classes["isupper"] = ExpressionAttributeLookupFixedIsupper


from nuitka.specs.BuiltinStrOperationSpecs import str_isupper_spec


class ExpressionAttributeLookupStrIsupper(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIsupper
):
    """Attribute Isupper lookup on a str.

    Typically code like: some_str.isupper
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISUPPER"
    attribute_name = "isupper"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationIsupper(source_ref):
            from .StrNodes import ExpressionStrOperationIsupper

            return ExpressionStrOperationIsupper(
                str_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationIsupper,
            builtin_spec=str_isupper_spec,
        )

        return result, "new_expression", "Call to 'isupper' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrIsupper)


class ExpressionAttributeLookupFixedItems(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'items' of an object.

    Typically code like: source.items
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ITEMS"
    attribute_name = "items"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            return trace_collection.computedExpressionResult(
                expression=ExpressionAttributeLookupDictItems(
                    expression=subnode_expression, source_ref=self.source_ref
                ),
                change_tags="new_expression",
                change_desc="Attribute lookup 'items' on dict shape resolved.",
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

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationItems,
            builtin_spec=dict_items_spec,
        )

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Call to 'items' of dictionary recognized.",
        )


attribute_typed_classes.add(ExpressionAttributeLookupDictItems)


class ExpressionAttributeLookupFixedIteritems(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'iteritems' of an object.

    Typically code like: source.iteritems
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ITERITEMS"
    attribute_name = "iteritems"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is bytes and subnode_expression.hasShapeDictionaryExact():
            return trace_collection.computedExpressionResult(
                expression=ExpressionAttributeLookupDictIteritems(
                    expression=subnode_expression, source_ref=self.source_ref
                ),
                change_tags="new_expression",
                change_desc="Attribute lookup 'iteritems' on dict shape resolved.",
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

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationIteritems,
            builtin_spec=dict_iteritems_spec,
        )

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Call to 'iteritems' of dictionary recognized.",
        )


attribute_typed_classes.add(ExpressionAttributeLookupDictIteritems)


class ExpressionAttributeLookupFixedIterkeys(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'iterkeys' of an object.

    Typically code like: source.iterkeys
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ITERKEYS"
    attribute_name = "iterkeys"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is bytes and subnode_expression.hasShapeDictionaryExact():
            return trace_collection.computedExpressionResult(
                expression=ExpressionAttributeLookupDictIterkeys(
                    expression=subnode_expression, source_ref=self.source_ref
                ),
                change_tags="new_expression",
                change_desc="Attribute lookup 'iterkeys' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="iterkeys",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="iterkeys"
        )


attribute_classes["iterkeys"] = ExpressionAttributeLookupFixedIterkeys


from nuitka.specs.BuiltinDictOperationSpecs import dict_iterkeys_spec


class ExpressionAttributeLookupDictIterkeys(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIterkeys
):
    """Attribute Iterkeys lookup on a dict.

    Typically code like: some_dict.iterkeys
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_ITERKEYS"
    attribute_name = "iterkeys"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationIterkeys(source_ref):
            from .DictionaryNodes import ExpressionDictOperationIterkeys

            return ExpressionDictOperationIterkeys(
                dict_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationIterkeys,
            builtin_spec=dict_iterkeys_spec,
        )

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Call to 'iterkeys' of dictionary recognized.",
        )


attribute_typed_classes.add(ExpressionAttributeLookupDictIterkeys)


class ExpressionAttributeLookupFixedItervalues(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'itervalues' of an object.

    Typically code like: source.itervalues
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ITERVALUES"
    attribute_name = "itervalues"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is bytes and subnode_expression.hasShapeDictionaryExact():
            return trace_collection.computedExpressionResult(
                expression=ExpressionAttributeLookupDictItervalues(
                    expression=subnode_expression, source_ref=self.source_ref
                ),
                change_tags="new_expression",
                change_desc="Attribute lookup 'itervalues' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="itervalues",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="itervalues"
        )


attribute_classes["itervalues"] = ExpressionAttributeLookupFixedItervalues


from nuitka.specs.BuiltinDictOperationSpecs import dict_itervalues_spec


class ExpressionAttributeLookupDictItervalues(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedItervalues
):
    """Attribute Itervalues lookup on a dict.

    Typically code like: some_dict.itervalues
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_ITERVALUES"
    attribute_name = "itervalues"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationItervalues(source_ref):
            from .DictionaryNodes import ExpressionDictOperationItervalues

            return ExpressionDictOperationItervalues(
                dict_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationItervalues,
            builtin_spec=dict_itervalues_spec,
        )

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Call to 'itervalues' of dictionary recognized.",
        )


attribute_typed_classes.add(ExpressionAttributeLookupDictItervalues)


class ExpressionAttributeLookupFixedJoin(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'join' of an object.

    Typically code like: source.join
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_JOIN"
    attribute_name = "join"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrJoin(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'join' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="join",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="join"
        )


attribute_classes["join"] = ExpressionAttributeLookupFixedJoin


from nuitka.specs.BuiltinStrOperationSpecs import str_join_spec


class ExpressionAttributeLookupStrJoin(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedJoin
):
    """Attribute Join lookup on a str.

    Typically code like: some_str.join
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_JOIN"
    attribute_name = "join"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationJoin(iterable, source_ref):
            from .StrNodes import ExpressionStrOperationJoin

            return ExpressionStrOperationJoin(
                str_arg=self.subnode_expression,
                iterable=iterable,
                source_ref=source_ref,
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationJoin,
            builtin_spec=str_join_spec,
        )

        return result, "new_expression", "Call to 'join' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrJoin)


class ExpressionAttributeLookupFixedKeys(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'keys' of an object.

    Typically code like: source.keys
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_KEYS"
    attribute_name = "keys"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            return trace_collection.computedExpressionResult(
                expression=ExpressionAttributeLookupDictKeys(
                    expression=subnode_expression, source_ref=self.source_ref
                ),
                change_tags="new_expression",
                change_desc="Attribute lookup 'keys' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="keys",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="keys"
        )


attribute_classes["keys"] = ExpressionAttributeLookupFixedKeys


from nuitka.specs.BuiltinDictOperationSpecs import dict_keys_spec


class ExpressionAttributeLookupDictKeys(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedKeys
):
    """Attribute Keys lookup on a dict.

    Typically code like: some_dict.keys
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_KEYS"
    attribute_name = "keys"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationKeys(source_ref):
            if str is bytes:
                from .DictionaryNodes import ExpressionDictOperationKeys

                return ExpressionDictOperationKeys(
                    dict_arg=self.subnode_expression, source_ref=source_ref
                )
            else:
                from .DictionaryNodes import ExpressionDictOperationIterkeys

                return ExpressionDictOperationIterkeys(
                    dict_arg=self.subnode_expression, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationKeys,
            builtin_spec=dict_keys_spec,
        )

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Call to 'keys' of dictionary recognized.",
        )


attribute_typed_classes.add(ExpressionAttributeLookupDictKeys)


class ExpressionAttributeLookupFixedLjust(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'ljust' of an object.

    Typically code like: source.ljust
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_LJUST"
    attribute_name = "ljust"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrLjust(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'ljust' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="ljust",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="ljust"
        )


attribute_classes["ljust"] = ExpressionAttributeLookupFixedLjust


class ExpressionAttributeLookupStrLjust(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedLjust
):
    """Attribute Ljust lookup on a str.

    Typically code like: some_str.ljust
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_LJUST"
    attribute_name = "ljust"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as str operation ExpressionStrOperationLjust is not yet implemented


attribute_typed_classes.add(ExpressionAttributeLookupStrLjust)


class ExpressionAttributeLookupFixedLower(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'lower' of an object.

    Typically code like: source.lower
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_LOWER"
    attribute_name = "lower"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrLower(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'lower' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="lower",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="lower"
        )


attribute_classes["lower"] = ExpressionAttributeLookupFixedLower


from nuitka.specs.BuiltinStrOperationSpecs import str_lower_spec


class ExpressionAttributeLookupStrLower(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedLower
):
    """Attribute Lower lookup on a str.

    Typically code like: some_str.lower
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_LOWER"
    attribute_name = "lower"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationLower(source_ref):
            from .StrNodes import ExpressionStrOperationLower

            return ExpressionStrOperationLower(
                str_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationLower,
            builtin_spec=str_lower_spec,
        )

        return result, "new_expression", "Call to 'lower' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrLower)


class ExpressionAttributeLookupFixedLstrip(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'lstrip' of an object.

    Typically code like: source.lstrip
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_LSTRIP"
    attribute_name = "lstrip"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrLstrip(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'lstrip' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="lstrip",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="lstrip"
        )


attribute_classes["lstrip"] = ExpressionAttributeLookupFixedLstrip


from nuitka.specs.BuiltinStrOperationSpecs import str_lstrip_spec


class ExpressionAttributeLookupStrLstrip(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedLstrip
):
    """Attribute Lstrip lookup on a str.

    Typically code like: some_str.lstrip
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_LSTRIP"
    attribute_name = "lstrip"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationLstrip(chars, source_ref):
            if chars is not None:
                from .StrNodes import ExpressionStrOperationLstrip2

                return ExpressionStrOperationLstrip2(
                    str_arg=self.subnode_expression, chars=chars, source_ref=source_ref
                )
            else:
                from .StrNodes import ExpressionStrOperationLstrip1

                return ExpressionStrOperationLstrip1(
                    str_arg=self.subnode_expression, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationLstrip,
            builtin_spec=str_lstrip_spec,
        )

        return result, "new_expression", "Call to 'lstrip' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrLstrip)


class ExpressionAttributeLookupFixedMaketrans(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'maketrans' of an object.

    Typically code like: source.maketrans
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_MAKETRANS"
    attribute_name = "maketrans"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is not bytes and subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrMaketrans(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'maketrans' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="maketrans",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="maketrans"
        )


attribute_classes["maketrans"] = ExpressionAttributeLookupFixedMaketrans


class ExpressionAttributeLookupStrMaketrans(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedMaketrans
):
    """Attribute Maketrans lookup on a str.

    Typically code like: some_str.maketrans
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_MAKETRANS"
    attribute_name = "maketrans"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as str operation ExpressionStrOperationMaketrans is not yet implemented


attribute_typed_classes.add(ExpressionAttributeLookupStrMaketrans)


class ExpressionAttributeLookupFixedPartition(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'partition' of an object.

    Typically code like: source.partition
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_PARTITION"
    attribute_name = "partition"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrPartition(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'partition' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="partition",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="partition"
        )


attribute_classes["partition"] = ExpressionAttributeLookupFixedPartition


from nuitka.specs.BuiltinStrOperationSpecs import str_partition_spec


class ExpressionAttributeLookupStrPartition(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedPartition
):
    """Attribute Partition lookup on a str.

    Typically code like: some_str.partition
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_PARTITION"
    attribute_name = "partition"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationPartition(sep, source_ref):
            from .StrNodes import ExpressionStrOperationPartition

            return ExpressionStrOperationPartition(
                str_arg=self.subnode_expression, sep=sep, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationPartition,
            builtin_spec=str_partition_spec,
        )

        return result, "new_expression", "Call to 'partition' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrPartition)


class ExpressionAttributeLookupFixedPop(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'pop' of an object.

    Typically code like: source.pop
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_POP"
    attribute_name = "pop"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            return trace_collection.computedExpressionResult(
                expression=ExpressionAttributeLookupDictPop(
                    expression=subnode_expression, source_ref=self.source_ref
                ),
                change_tags="new_expression",
                change_desc="Attribute lookup 'pop' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="pop",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="pop"
        )


attribute_classes["pop"] = ExpressionAttributeLookupFixedPop


from nuitka.specs.BuiltinDictOperationSpecs import dict_pop_spec


class ExpressionAttributeLookupDictPop(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedPop
):
    """Attribute Pop lookup on a dict.

    Typically code like: some_dict.pop
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_POP"
    attribute_name = "pop"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationPop(key, default, source_ref):
            if default is not None:
                from .DictionaryNodes import ExpressionDictOperationPop3

                return ExpressionDictOperationPop3(
                    dict_arg=self.subnode_expression,
                    key=key,
                    default=default,
                    source_ref=source_ref,
                )
            else:
                from .DictionaryNodes import ExpressionDictOperationPop2

                return ExpressionDictOperationPop2(
                    dict_arg=self.subnode_expression, key=key, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationPop,
            builtin_spec=dict_pop_spec,
        )

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Call to 'pop' of dictionary recognized.",
        )


attribute_typed_classes.add(ExpressionAttributeLookupDictPop)


class ExpressionAttributeLookupFixedPopitem(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'popitem' of an object.

    Typically code like: source.popitem
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_POPITEM"
    attribute_name = "popitem"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            return trace_collection.computedExpressionResult(
                expression=ExpressionAttributeLookupDictPopitem(
                    expression=subnode_expression, source_ref=self.source_ref
                ),
                change_tags="new_expression",
                change_desc="Attribute lookup 'popitem' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="popitem",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="popitem"
        )


attribute_classes["popitem"] = ExpressionAttributeLookupFixedPopitem


class ExpressionAttributeLookupDictPopitem(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedPopitem
):
    """Attribute Popitem lookup on a dict.

    Typically code like: some_dict.popitem
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_POPITEM"
    attribute_name = "popitem"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as dict operation ExpressionDictOperationPopitem is not yet implemented


attribute_typed_classes.add(ExpressionAttributeLookupDictPopitem)


class ExpressionAttributeLookupFixedReplace(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'replace' of an object.

    Typically code like: source.replace
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_REPLACE"
    attribute_name = "replace"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrReplace(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'replace' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="replace",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="replace"
        )


attribute_classes["replace"] = ExpressionAttributeLookupFixedReplace


from nuitka.specs.BuiltinStrOperationSpecs import str_replace_spec


class ExpressionAttributeLookupStrReplace(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedReplace
):
    """Attribute Replace lookup on a str.

    Typically code like: some_str.replace
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_REPLACE"
    attribute_name = "replace"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationReplace(old, new, count, source_ref):
            if count is not None:
                from .StrNodes import ExpressionStrOperationReplace4

                return ExpressionStrOperationReplace4(
                    str_arg=self.subnode_expression,
                    old=old,
                    new=new,
                    count=count,
                    source_ref=source_ref,
                )
            else:
                from .StrNodes import ExpressionStrOperationReplace3

                return ExpressionStrOperationReplace3(
                    str_arg=self.subnode_expression,
                    old=old,
                    new=new,
                    source_ref=source_ref,
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationReplace,
            builtin_spec=str_replace_spec,
        )

        return result, "new_expression", "Call to 'replace' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrReplace)


class ExpressionAttributeLookupFixedRfind(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'rfind' of an object.

    Typically code like: source.rfind
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_RFIND"
    attribute_name = "rfind"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrRfind(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'rfind' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="rfind",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="rfind"
        )


attribute_classes["rfind"] = ExpressionAttributeLookupFixedRfind


from nuitka.specs.BuiltinStrOperationSpecs import str_rfind_spec


class ExpressionAttributeLookupStrRfind(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedRfind
):
    """Attribute Rfind lookup on a str.

    Typically code like: some_str.rfind
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_RFIND"
    attribute_name = "rfind"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationRfind(sub, start, end, source_ref):
            if end is not None:
                from .StrNodes import ExpressionStrOperationRfind4

                return ExpressionStrOperationRfind4(
                    str_arg=self.subnode_expression,
                    sub=sub,
                    start=start,
                    end=end,
                    source_ref=source_ref,
                )
            elif start is not None:
                from .StrNodes import ExpressionStrOperationRfind3

                return ExpressionStrOperationRfind3(
                    str_arg=self.subnode_expression,
                    sub=sub,
                    start=start,
                    source_ref=source_ref,
                )
            else:
                from .StrNodes import ExpressionStrOperationRfind2

                return ExpressionStrOperationRfind2(
                    str_arg=self.subnode_expression, sub=sub, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationRfind,
            builtin_spec=str_rfind_spec,
        )

        return result, "new_expression", "Call to 'rfind' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrRfind)


class ExpressionAttributeLookupFixedRindex(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'rindex' of an object.

    Typically code like: source.rindex
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_RINDEX"
    attribute_name = "rindex"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrRindex(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'rindex' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="rindex",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="rindex"
        )


attribute_classes["rindex"] = ExpressionAttributeLookupFixedRindex


from nuitka.specs.BuiltinStrOperationSpecs import str_rindex_spec


class ExpressionAttributeLookupStrRindex(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedRindex
):
    """Attribute Rindex lookup on a str.

    Typically code like: some_str.rindex
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_RINDEX"
    attribute_name = "rindex"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationRindex(sub, start, end, source_ref):
            if end is not None:
                from .StrNodes import ExpressionStrOperationRindex4

                return ExpressionStrOperationRindex4(
                    str_arg=self.subnode_expression,
                    sub=sub,
                    start=start,
                    end=end,
                    source_ref=source_ref,
                )
            elif start is not None:
                from .StrNodes import ExpressionStrOperationRindex3

                return ExpressionStrOperationRindex3(
                    str_arg=self.subnode_expression,
                    sub=sub,
                    start=start,
                    source_ref=source_ref,
                )
            else:
                from .StrNodes import ExpressionStrOperationRindex2

                return ExpressionStrOperationRindex2(
                    str_arg=self.subnode_expression, sub=sub, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationRindex,
            builtin_spec=str_rindex_spec,
        )

        return result, "new_expression", "Call to 'rindex' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrRindex)


class ExpressionAttributeLookupFixedRjust(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'rjust' of an object.

    Typically code like: source.rjust
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_RJUST"
    attribute_name = "rjust"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrRjust(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'rjust' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="rjust",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="rjust"
        )


attribute_classes["rjust"] = ExpressionAttributeLookupFixedRjust


class ExpressionAttributeLookupStrRjust(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedRjust
):
    """Attribute Rjust lookup on a str.

    Typically code like: some_str.rjust
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_RJUST"
    attribute_name = "rjust"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as str operation ExpressionStrOperationRjust is not yet implemented


attribute_typed_classes.add(ExpressionAttributeLookupStrRjust)


class ExpressionAttributeLookupFixedRpartition(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'rpartition' of an object.

    Typically code like: source.rpartition
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_RPARTITION"
    attribute_name = "rpartition"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrRpartition(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'rpartition' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="rpartition",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="rpartition"
        )


attribute_classes["rpartition"] = ExpressionAttributeLookupFixedRpartition


from nuitka.specs.BuiltinStrOperationSpecs import str_rpartition_spec


class ExpressionAttributeLookupStrRpartition(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedRpartition
):
    """Attribute Rpartition lookup on a str.

    Typically code like: some_str.rpartition
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_RPARTITION"
    attribute_name = "rpartition"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationRpartition(sep, source_ref):
            from .StrNodes import ExpressionStrOperationRpartition

            return ExpressionStrOperationRpartition(
                str_arg=self.subnode_expression, sep=sep, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationRpartition,
            builtin_spec=str_rpartition_spec,
        )

        return result, "new_expression", "Call to 'rpartition' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrRpartition)


class ExpressionAttributeLookupFixedRsplit(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'rsplit' of an object.

    Typically code like: source.rsplit
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_RSPLIT"
    attribute_name = "rsplit"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrRsplit(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'rsplit' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="rsplit",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="rsplit"
        )


attribute_classes["rsplit"] = ExpressionAttributeLookupFixedRsplit


from nuitka.specs.BuiltinStrOperationSpecs import str_rsplit_spec


class ExpressionAttributeLookupStrRsplit(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedRsplit
):
    """Attribute Rsplit lookup on a str.

    Typically code like: some_str.rsplit
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_RSPLIT"
    attribute_name = "rsplit"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationRsplit(sep, maxsplit, source_ref):
            if maxsplit is not None:
                from .StrNodes import ExpressionStrOperationRsplit3

                return ExpressionStrOperationRsplit3(
                    str_arg=self.subnode_expression,
                    sep=sep,
                    maxsplit=maxsplit,
                    source_ref=source_ref,
                )
            elif sep is not None:
                from .StrNodes import ExpressionStrOperationRsplit2

                return ExpressionStrOperationRsplit2(
                    str_arg=self.subnode_expression, sep=sep, source_ref=source_ref
                )
            else:
                from .StrNodes import ExpressionStrOperationRsplit1

                return ExpressionStrOperationRsplit1(
                    str_arg=self.subnode_expression, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationRsplit,
            builtin_spec=str_rsplit_spec,
        )

        return result, "new_expression", "Call to 'rsplit' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrRsplit)


class ExpressionAttributeLookupFixedRstrip(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'rstrip' of an object.

    Typically code like: source.rstrip
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_RSTRIP"
    attribute_name = "rstrip"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrRstrip(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'rstrip' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="rstrip",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="rstrip"
        )


attribute_classes["rstrip"] = ExpressionAttributeLookupFixedRstrip


from nuitka.specs.BuiltinStrOperationSpecs import str_rstrip_spec


class ExpressionAttributeLookupStrRstrip(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedRstrip
):
    """Attribute Rstrip lookup on a str.

    Typically code like: some_str.rstrip
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_RSTRIP"
    attribute_name = "rstrip"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationRstrip(chars, source_ref):
            if chars is not None:
                from .StrNodes import ExpressionStrOperationRstrip2

                return ExpressionStrOperationRstrip2(
                    str_arg=self.subnode_expression, chars=chars, source_ref=source_ref
                )
            else:
                from .StrNodes import ExpressionStrOperationRstrip1

                return ExpressionStrOperationRstrip1(
                    str_arg=self.subnode_expression, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationRstrip,
            builtin_spec=str_rstrip_spec,
        )

        return result, "new_expression", "Call to 'rstrip' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrRstrip)


class ExpressionAttributeLookupFixedSetdefault(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'setdefault' of an object.

    Typically code like: source.setdefault
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_SETDEFAULT"
    attribute_name = "setdefault"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            return trace_collection.computedExpressionResult(
                expression=ExpressionAttributeLookupDictSetdefault(
                    expression=subnode_expression, source_ref=self.source_ref
                ),
                change_tags="new_expression",
                change_desc="Attribute lookup 'setdefault' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="setdefault",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="setdefault"
        )


attribute_classes["setdefault"] = ExpressionAttributeLookupFixedSetdefault


from nuitka.specs.BuiltinDictOperationSpecs import dict_setdefault_spec


class ExpressionAttributeLookupDictSetdefault(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedSetdefault
):
    """Attribute Setdefault lookup on a dict.

    Typically code like: some_dict.setdefault
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_SETDEFAULT"
    attribute_name = "setdefault"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationSetdefault(key, default, source_ref):
            if default is not None:
                from .DictionaryNodes import ExpressionDictOperationSetdefault3

                return ExpressionDictOperationSetdefault3(
                    dict_arg=self.subnode_expression,
                    key=key,
                    default=default,
                    source_ref=source_ref,
                )
            else:
                from .DictionaryNodes import ExpressionDictOperationSetdefault2

                return ExpressionDictOperationSetdefault2(
                    dict_arg=self.subnode_expression, key=key, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationSetdefault,
            builtin_spec=dict_setdefault_spec,
        )

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Call to 'setdefault' of dictionary recognized.",
        )


attribute_typed_classes.add(ExpressionAttributeLookupDictSetdefault)


class ExpressionAttributeLookupFixedSplit(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'split' of an object.

    Typically code like: source.split
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_SPLIT"
    attribute_name = "split"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrSplit(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'split' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="split",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="split"
        )


attribute_classes["split"] = ExpressionAttributeLookupFixedSplit


from nuitka.specs.BuiltinStrOperationSpecs import str_split_spec


class ExpressionAttributeLookupStrSplit(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedSplit
):
    """Attribute Split lookup on a str.

    Typically code like: some_str.split
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_SPLIT"
    attribute_name = "split"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationSplit(sep, maxsplit, source_ref):
            if maxsplit is not None:
                from .StrNodes import ExpressionStrOperationSplit3

                return ExpressionStrOperationSplit3(
                    str_arg=self.subnode_expression,
                    sep=sep,
                    maxsplit=maxsplit,
                    source_ref=source_ref,
                )
            elif sep is not None:
                from .StrNodes import ExpressionStrOperationSplit2

                return ExpressionStrOperationSplit2(
                    str_arg=self.subnode_expression, sep=sep, source_ref=source_ref
                )
            else:
                from .StrNodes import ExpressionStrOperationSplit1

                return ExpressionStrOperationSplit1(
                    str_arg=self.subnode_expression, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationSplit,
            builtin_spec=str_split_spec,
        )

        return result, "new_expression", "Call to 'split' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrSplit)


class ExpressionAttributeLookupFixedSplitlines(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'splitlines' of an object.

    Typically code like: source.splitlines
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_SPLITLINES"
    attribute_name = "splitlines"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrSplitlines(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'splitlines' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="splitlines",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="splitlines"
        )


attribute_classes["splitlines"] = ExpressionAttributeLookupFixedSplitlines


class ExpressionAttributeLookupStrSplitlines(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedSplitlines
):
    """Attribute Splitlines lookup on a str.

    Typically code like: some_str.splitlines
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_SPLITLINES"
    attribute_name = "splitlines"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as str operation ExpressionStrOperationSplitlines is not yet implemented


attribute_typed_classes.add(ExpressionAttributeLookupStrSplitlines)


class ExpressionAttributeLookupFixedStartswith(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'startswith' of an object.

    Typically code like: source.startswith
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_STARTSWITH"
    attribute_name = "startswith"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrStartswith(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'startswith' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="startswith",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="startswith"
        )


attribute_classes["startswith"] = ExpressionAttributeLookupFixedStartswith


from nuitka.specs.BuiltinStrOperationSpecs import str_startswith_spec


class ExpressionAttributeLookupStrStartswith(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedStartswith
):
    """Attribute Startswith lookup on a str.

    Typically code like: some_str.startswith
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_STARTSWITH"
    attribute_name = "startswith"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationStartswith(prefix, start, end, source_ref):
            if end is not None:
                from .StrNodes import ExpressionStrOperationStartswith4

                return ExpressionStrOperationStartswith4(
                    str_arg=self.subnode_expression,
                    prefix=prefix,
                    start=start,
                    end=end,
                    source_ref=source_ref,
                )
            elif start is not None:
                from .StrNodes import ExpressionStrOperationStartswith3

                return ExpressionStrOperationStartswith3(
                    str_arg=self.subnode_expression,
                    prefix=prefix,
                    start=start,
                    source_ref=source_ref,
                )
            else:
                from .StrNodes import ExpressionStrOperationStartswith2

                return ExpressionStrOperationStartswith2(
                    str_arg=self.subnode_expression,
                    prefix=prefix,
                    source_ref=source_ref,
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationStartswith,
            builtin_spec=str_startswith_spec,
        )

        return result, "new_expression", "Call to 'startswith' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrStartswith)


class ExpressionAttributeLookupFixedStrip(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'strip' of an object.

    Typically code like: source.strip
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_STRIP"
    attribute_name = "strip"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrStrip(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'strip' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="strip",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="strip"
        )


attribute_classes["strip"] = ExpressionAttributeLookupFixedStrip


from nuitka.specs.BuiltinStrOperationSpecs import str_strip_spec


class ExpressionAttributeLookupStrStrip(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedStrip
):
    """Attribute Strip lookup on a str.

    Typically code like: some_str.strip
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_STRIP"
    attribute_name = "strip"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationStrip(chars, source_ref):
            if chars is not None:
                from .StrNodes import ExpressionStrOperationStrip2

                return ExpressionStrOperationStrip2(
                    str_arg=self.subnode_expression, chars=chars, source_ref=source_ref
                )
            else:
                from .StrNodes import ExpressionStrOperationStrip1

                return ExpressionStrOperationStrip1(
                    str_arg=self.subnode_expression, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationStrip,
            builtin_spec=str_strip_spec,
        )

        return result, "new_expression", "Call to 'strip' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrStrip)


class ExpressionAttributeLookupFixedSwapcase(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'swapcase' of an object.

    Typically code like: source.swapcase
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_SWAPCASE"
    attribute_name = "swapcase"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrSwapcase(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'swapcase' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="swapcase",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="swapcase"
        )


attribute_classes["swapcase"] = ExpressionAttributeLookupFixedSwapcase


from nuitka.specs.BuiltinStrOperationSpecs import str_swapcase_spec


class ExpressionAttributeLookupStrSwapcase(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedSwapcase
):
    """Attribute Swapcase lookup on a str.

    Typically code like: some_str.swapcase
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_SWAPCASE"
    attribute_name = "swapcase"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationSwapcase(source_ref):
            from .StrNodes import ExpressionStrOperationSwapcase

            return ExpressionStrOperationSwapcase(
                str_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationSwapcase,
            builtin_spec=str_swapcase_spec,
        )

        return result, "new_expression", "Call to 'swapcase' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrSwapcase)


class ExpressionAttributeLookupFixedTitle(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'title' of an object.

    Typically code like: source.title
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_TITLE"
    attribute_name = "title"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrTitle(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'title' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="title",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="title"
        )


attribute_classes["title"] = ExpressionAttributeLookupFixedTitle


from nuitka.specs.BuiltinStrOperationSpecs import str_title_spec


class ExpressionAttributeLookupStrTitle(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedTitle
):
    """Attribute Title lookup on a str.

    Typically code like: some_str.title
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_TITLE"
    attribute_name = "title"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationTitle(source_ref):
            from .StrNodes import ExpressionStrOperationTitle

            return ExpressionStrOperationTitle(
                str_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationTitle,
            builtin_spec=str_title_spec,
        )

        return result, "new_expression", "Call to 'title' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrTitle)


class ExpressionAttributeLookupFixedTranslate(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'translate' of an object.

    Typically code like: source.translate
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_TRANSLATE"
    attribute_name = "translate"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrTranslate(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'translate' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="translate",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="translate"
        )


attribute_classes["translate"] = ExpressionAttributeLookupFixedTranslate


class ExpressionAttributeLookupStrTranslate(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedTranslate
):
    """Attribute Translate lookup on a str.

    Typically code like: some_str.translate
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_TRANSLATE"
    attribute_name = "translate"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as str operation ExpressionStrOperationTranslate is not yet implemented


attribute_typed_classes.add(ExpressionAttributeLookupStrTranslate)


class ExpressionAttributeLookupFixedUpdate(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'update' of an object.

    Typically code like: source.update
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_UPDATE"
    attribute_name = "update"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            return trace_collection.computedExpressionResult(
                expression=ExpressionAttributeLookupDictUpdate(
                    expression=subnode_expression, source_ref=self.source_ref
                ),
                change_tags="new_expression",
                change_desc="Attribute lookup 'update' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="update",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="update"
        )


attribute_classes["update"] = ExpressionAttributeLookupFixedUpdate


from nuitka.specs.BuiltinDictOperationSpecs import dict_update_spec


class ExpressionAttributeLookupDictUpdate(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedUpdate
):
    """Attribute Update lookup on a dict.

    Typically code like: some_dict.update
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_UPDATE"
    attribute_name = "update"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationUpdate(list_args, kw_args, source_ref):
            if kw_args is not None:
                from .DictionaryNodes import ExpressionDictOperationUpdate3

                return ExpressionDictOperationUpdate3(
                    dict_arg=self.subnode_expression,
                    iterable=list_args,
                    pairs=kw_args,
                    source_ref=source_ref,
                )
            else:
                from .DictionaryNodes import ExpressionDictOperationUpdate2

                return ExpressionDictOperationUpdate2(
                    dict_arg=self.subnode_expression,
                    iterable=list_args,
                    source_ref=source_ref,
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationUpdate,
            builtin_spec=dict_update_spec,
        )

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Call to 'update' of dictionary recognized.",
        )


attribute_typed_classes.add(ExpressionAttributeLookupDictUpdate)


class ExpressionAttributeLookupFixedUpper(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'upper' of an object.

    Typically code like: source.upper
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_UPPER"
    attribute_name = "upper"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrUpper(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'upper' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="upper",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="upper"
        )


attribute_classes["upper"] = ExpressionAttributeLookupFixedUpper


from nuitka.specs.BuiltinStrOperationSpecs import str_upper_spec


class ExpressionAttributeLookupStrUpper(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedUpper
):
    """Attribute Upper lookup on a str.

    Typically code like: some_str.upper
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_UPPER"
    attribute_name = "upper"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionStrOperationUpper(source_ref):
            from .StrNodes import ExpressionStrOperationUpper

            return ExpressionStrOperationUpper(
                str_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationUpper,
            builtin_spec=str_upper_spec,
        )

        return result, "new_expression", "Call to 'upper' of str recognized."


attribute_typed_classes.add(ExpressionAttributeLookupStrUpper)


class ExpressionAttributeLookupFixedValues(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'values' of an object.

    Typically code like: source.values
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_VALUES"
    attribute_name = "values"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            return trace_collection.computedExpressionResult(
                expression=ExpressionAttributeLookupDictValues(
                    expression=subnode_expression, source_ref=self.source_ref
                ),
                change_tags="new_expression",
                change_desc="Attribute lookup 'values' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="values",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="values"
        )


attribute_classes["values"] = ExpressionAttributeLookupFixedValues


from nuitka.specs.BuiltinDictOperationSpecs import dict_values_spec


class ExpressionAttributeLookupDictValues(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedValues
):
    """Attribute Values lookup on a dict.

    Typically code like: some_dict.values
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_VALUES"
    attribute_name = "values"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationValues(source_ref):
            if str is bytes:
                from .DictionaryNodes import ExpressionDictOperationValues

                return ExpressionDictOperationValues(
                    dict_arg=self.subnode_expression, source_ref=source_ref
                )
            else:
                from .DictionaryNodes import ExpressionDictOperationItervalues

                return ExpressionDictOperationItervalues(
                    dict_arg=self.subnode_expression, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationValues,
            builtin_spec=dict_values_spec,
        )

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Call to 'values' of dictionary recognized.",
        )


attribute_typed_classes.add(ExpressionAttributeLookupDictValues)


class ExpressionAttributeLookupFixedViewitems(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'viewitems' of an object.

    Typically code like: source.viewitems
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_VIEWITEMS"
    attribute_name = "viewitems"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is bytes and subnode_expression.hasShapeDictionaryExact():
            return trace_collection.computedExpressionResult(
                expression=ExpressionAttributeLookupDictViewitems(
                    expression=subnode_expression, source_ref=self.source_ref
                ),
                change_tags="new_expression",
                change_desc="Attribute lookup 'viewitems' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="viewitems",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="viewitems"
        )


attribute_classes["viewitems"] = ExpressionAttributeLookupFixedViewitems


from nuitka.specs.BuiltinDictOperationSpecs import dict_viewitems_spec


class ExpressionAttributeLookupDictViewitems(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedViewitems
):
    """Attribute Viewitems lookup on a dict.

    Typically code like: some_dict.viewitems
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_VIEWITEMS"
    attribute_name = "viewitems"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationViewitems(source_ref):
            from .DictionaryNodes import ExpressionDictOperationViewitems

            return ExpressionDictOperationViewitems(
                dict_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationViewitems,
            builtin_spec=dict_viewitems_spec,
        )

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Call to 'viewitems' of dictionary recognized.",
        )


attribute_typed_classes.add(ExpressionAttributeLookupDictViewitems)


class ExpressionAttributeLookupFixedViewkeys(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'viewkeys' of an object.

    Typically code like: source.viewkeys
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_VIEWKEYS"
    attribute_name = "viewkeys"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is bytes and subnode_expression.hasShapeDictionaryExact():
            return trace_collection.computedExpressionResult(
                expression=ExpressionAttributeLookupDictViewkeys(
                    expression=subnode_expression, source_ref=self.source_ref
                ),
                change_tags="new_expression",
                change_desc="Attribute lookup 'viewkeys' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="viewkeys",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="viewkeys"
        )


attribute_classes["viewkeys"] = ExpressionAttributeLookupFixedViewkeys


from nuitka.specs.BuiltinDictOperationSpecs import dict_viewkeys_spec


class ExpressionAttributeLookupDictViewkeys(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedViewkeys
):
    """Attribute Viewkeys lookup on a dict.

    Typically code like: some_dict.viewkeys
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_VIEWKEYS"
    attribute_name = "viewkeys"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationViewkeys(source_ref):
            from .DictionaryNodes import ExpressionDictOperationViewkeys

            return ExpressionDictOperationViewkeys(
                dict_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationViewkeys,
            builtin_spec=dict_viewkeys_spec,
        )

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Call to 'viewkeys' of dictionary recognized.",
        )


attribute_typed_classes.add(ExpressionAttributeLookupDictViewkeys)


class ExpressionAttributeLookupFixedViewvalues(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'viewvalues' of an object.

    Typically code like: source.viewvalues
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_VIEWVALUES"
    attribute_name = "viewvalues"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is bytes and subnode_expression.hasShapeDictionaryExact():
            return trace_collection.computedExpressionResult(
                expression=ExpressionAttributeLookupDictViewvalues(
                    expression=subnode_expression, source_ref=self.source_ref
                ),
                change_tags="new_expression",
                change_desc="Attribute lookup 'viewvalues' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="viewvalues",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="viewvalues"
        )


attribute_classes["viewvalues"] = ExpressionAttributeLookupFixedViewvalues


from nuitka.specs.BuiltinDictOperationSpecs import dict_viewvalues_spec


class ExpressionAttributeLookupDictViewvalues(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedViewvalues
):
    """Attribute Viewvalues lookup on a dict.

    Typically code like: some_dict.viewvalues
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_VIEWVALUES"
    attribute_name = "viewvalues"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationViewvalues(source_ref):
            from .DictionaryNodes import ExpressionDictOperationViewvalues

            return ExpressionDictOperationViewvalues(
                dict_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationViewvalues,
            builtin_spec=dict_viewvalues_spec,
        )

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Call to 'viewvalues' of dictionary recognized.",
        )


attribute_typed_classes.add(ExpressionAttributeLookupDictViewvalues)


class ExpressionAttributeLookupFixedZfill(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'zfill' of an object.

    Typically code like: source.zfill
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ZFILL"
    attribute_name = "zfill"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeStrExact():
            result = ExpressionAttributeLookupStrZfill(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'zfill' on str shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="zfill",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="zfill"
        )


attribute_classes["zfill"] = ExpressionAttributeLookupFixedZfill


class ExpressionAttributeLookupStrZfill(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedZfill
):
    """Attribute Zfill lookup on a str.

    Typically code like: some_str.zfill
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ZFILL"
    attribute_name = "zfill"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as str operation ExpressionStrOperationZfill is not yet implemented


attribute_typed_classes.add(ExpressionAttributeLookupStrZfill)
