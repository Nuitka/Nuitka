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
# We are not avoiding these in generated code at all
# pylint: disable=I0021,too-many-lines
# pylint: disable=I0021,line-too-long
# pylint: disable=I0021,too-many-instance-attributes
# pylint: disable=I0021,too-many-return-statements


"""Specialized attribute nodes

WARNING, this code is GENERATED. Modify the template AttributeNodeFixed.py.j2 instead!

spell-checker: ignore append capitalize casefold center clear copy count decode encode endswith expandtabs extend find format formatmap fromkeys get haskey index insert isalnum isalpha isascii isdecimal isdigit isidentifier islower isnumeric isprintable isspace istitle isupper items iteritems iterkeys itervalues join keys ljust lower lstrip maketrans partition pop popitem prepare remove replace reverse rfind rindex rjust rpartition rsplit rstrip setdefault sort split splitlines startswith strip swapcase title translate update upper values viewitems viewkeys viewvalues zfill
spell-checker: ignore args chars count default delete encoding end errors fillchar index item iterable keepends key kwargs maxsplit new old pairs prefix sep start stop sub suffix table tabsize value width
"""


from nuitka.specs.BuiltinBytesOperationSpecs import (
    bytes_capitalize_spec,
    bytes_center_spec,
    bytes_count_spec,
    bytes_decode_spec,
    bytes_endswith_spec,
    bytes_expandtabs_spec,
    bytes_find_spec,
    bytes_index_spec,
    bytes_isalnum_spec,
    bytes_isalpha_spec,
    bytes_isdigit_spec,
    bytes_islower_spec,
    bytes_isspace_spec,
    bytes_istitle_spec,
    bytes_isupper_spec,
    bytes_join_spec,
    bytes_ljust_spec,
    bytes_lower_spec,
    bytes_lstrip_spec,
    bytes_partition_spec,
    bytes_replace_spec,
    bytes_rfind_spec,
    bytes_rindex_spec,
    bytes_rjust_spec,
    bytes_rpartition_spec,
    bytes_rsplit_spec,
    bytes_rstrip_spec,
    bytes_split_spec,
    bytes_splitlines_spec,
    bytes_startswith_spec,
    bytes_strip_spec,
    bytes_swapcase_spec,
    bytes_title_spec,
    bytes_translate_spec,
    bytes_upper_spec,
    bytes_zfill_spec,
)
from nuitka.specs.BuiltinDictOperationSpecs import (
    dict_clear_spec,
    dict_copy_spec,
    dict_fromkeys_spec,
    dict_get_spec,
    dict_has_key_spec,
    dict_items_spec,
    dict_iteritems_spec,
    dict_iterkeys_spec,
    dict_itervalues_spec,
    dict_keys_spec,
    dict_pop_spec,
    dict_popitem_spec,
    dict_setdefault_spec,
    dict_update_spec,
    dict_values_spec,
    dict_viewitems_spec,
    dict_viewkeys_spec,
    dict_viewvalues_spec,
)
from nuitka.specs.BuiltinListOperationSpecs import (
    list_append_spec,
    list_clear_spec,
    list_copy_spec,
    list_count_spec,
    list_extend_spec,
    list_index_spec,
    list_insert_spec,
    list_pop_spec,
    list_remove_spec,
    list_reverse_spec,
)
from nuitka.specs.BuiltinParameterSpecs import extractBuiltinArgs
from nuitka.specs.BuiltinStrOperationSpecs import (
    str_capitalize_spec,
    str_center_spec,
    str_count_spec,
    str_decode_spec,
    str_encode_spec,
    str_endswith_spec,
    str_expandtabs_spec,
    str_find_spec,
    str_format_spec,
    str_index_spec,
    str_isalnum_spec,
    str_isalpha_spec,
    str_isdigit_spec,
    str_islower_spec,
    str_isspace_spec,
    str_istitle_spec,
    str_isupper_spec,
    str_join_spec,
    str_ljust_spec,
    str_lower_spec,
    str_lstrip_spec,
    str_partition_spec,
    str_replace_spec,
    str_rfind_spec,
    str_rindex_spec,
    str_rjust_spec,
    str_rpartition_spec,
    str_rsplit_spec,
    str_rstrip_spec,
    str_split_spec,
    str_splitlines_spec,
    str_startswith_spec,
    str_strip_spec,
    str_swapcase_spec,
    str_title_spec,
    str_translate_spec,
    str_upper_spec,
    str_zfill_spec,
)
from nuitka.specs.BuiltinTypeOperationSpecs import type___prepare___spec

from .AttributeLookupNodes import ExpressionAttributeLookupFixedBase
from .AttributeNodes import makeExpressionAttributeLookup
from .BuiltinTypeNodes import ExpressionTypeOperationPrepare
from .BytesNodes import (
    ExpressionBytesOperationCapitalize,
    ExpressionBytesOperationCenter2,
    ExpressionBytesOperationCenter3,
    ExpressionBytesOperationCount2,
    ExpressionBytesOperationCount3,
    ExpressionBytesOperationCount4,
    ExpressionBytesOperationDecode1,
    ExpressionBytesOperationDecode2,
    ExpressionBytesOperationEndswith2,
    ExpressionBytesOperationEndswith3,
    ExpressionBytesOperationEndswith4,
    ExpressionBytesOperationExpandtabs1,
    ExpressionBytesOperationExpandtabs2,
    ExpressionBytesOperationFind2,
    ExpressionBytesOperationFind3,
    ExpressionBytesOperationFind4,
    ExpressionBytesOperationIndex2,
    ExpressionBytesOperationIndex3,
    ExpressionBytesOperationIndex4,
    ExpressionBytesOperationIsalnum,
    ExpressionBytesOperationIsalpha,
    ExpressionBytesOperationIsdigit,
    ExpressionBytesOperationIslower,
    ExpressionBytesOperationIsspace,
    ExpressionBytesOperationIstitle,
    ExpressionBytesOperationIsupper,
    ExpressionBytesOperationJoin,
    ExpressionBytesOperationLjust2,
    ExpressionBytesOperationLjust3,
    ExpressionBytesOperationLower,
    ExpressionBytesOperationLstrip1,
    ExpressionBytesOperationLstrip2,
    ExpressionBytesOperationPartition,
    ExpressionBytesOperationReplace3,
    ExpressionBytesOperationReplace4,
    ExpressionBytesOperationRfind2,
    ExpressionBytesOperationRfind3,
    ExpressionBytesOperationRfind4,
    ExpressionBytesOperationRindex2,
    ExpressionBytesOperationRindex3,
    ExpressionBytesOperationRindex4,
    ExpressionBytesOperationRjust2,
    ExpressionBytesOperationRjust3,
    ExpressionBytesOperationRpartition,
    ExpressionBytesOperationRsplit1,
    ExpressionBytesOperationRsplit2,
    ExpressionBytesOperationRstrip1,
    ExpressionBytesOperationRstrip2,
    ExpressionBytesOperationSplit1,
    ExpressionBytesOperationSplit2,
    ExpressionBytesOperationSplitlines1,
    ExpressionBytesOperationSplitlines2,
    ExpressionBytesOperationStartswith2,
    ExpressionBytesOperationStartswith3,
    ExpressionBytesOperationStartswith4,
    ExpressionBytesOperationStrip1,
    ExpressionBytesOperationStrip2,
    ExpressionBytesOperationSwapcase,
    ExpressionBytesOperationTitle,
    ExpressionBytesOperationTranslate2,
    ExpressionBytesOperationTranslate3,
    ExpressionBytesOperationUpper,
    ExpressionBytesOperationZfill,
    makeExpressionBytesOperationDecode3,
    makeExpressionBytesOperationRsplit3,
    makeExpressionBytesOperationSplit3,
)
from .ConstantRefNodes import makeConstantRefNode
from .DictionaryNodes import (
    ExpressionDictOperationClear,
    ExpressionDictOperationCopy,
    ExpressionDictOperationFromkeys2,
    ExpressionDictOperationFromkeys3,
    ExpressionDictOperationFromkeysRef,
    ExpressionDictOperationGet2,
    ExpressionDictOperationGet3,
    ExpressionDictOperationHaskey,
    ExpressionDictOperationItems,
    ExpressionDictOperationIteritems,
    ExpressionDictOperationIterkeys,
    ExpressionDictOperationItervalues,
    ExpressionDictOperationKeys,
    ExpressionDictOperationPop2,
    ExpressionDictOperationPop3,
    ExpressionDictOperationPopitem,
    ExpressionDictOperationSetdefault2,
    ExpressionDictOperationSetdefault3,
    ExpressionDictOperationUpdate2,
    ExpressionDictOperationValues,
    ExpressionDictOperationViewitems,
    ExpressionDictOperationViewkeys,
    ExpressionDictOperationViewvalues,
    makeExpressionDictOperationUpdate3,
)
from .KeyValuePairNodes import makeKeyValuePairExpressionsFromKwArgs
from .ListOperationNodes import (
    ExpressionListOperationAppend,
    ExpressionListOperationClear,
    ExpressionListOperationCopy,
    ExpressionListOperationCount,
    ExpressionListOperationExtend,
    ExpressionListOperationIndex2,
    ExpressionListOperationIndex3,
    ExpressionListOperationIndex4,
    ExpressionListOperationInsert,
    ExpressionListOperationPop1,
    ExpressionListOperationPop2,
    ExpressionListOperationRemove,
    ExpressionListOperationReverse,
)
from .NodeBases import SideEffectsFromChildrenMixin
from .NodeMakingHelpers import wrapExpressionWithNodeSideEffects
from .StrNodes import (
    ExpressionStrOperationCapitalize,
    ExpressionStrOperationCenter2,
    ExpressionStrOperationCenter3,
    ExpressionStrOperationCount2,
    ExpressionStrOperationCount3,
    ExpressionStrOperationCount4,
    ExpressionStrOperationDecode1,
    ExpressionStrOperationDecode2,
    ExpressionStrOperationDecode3,
    ExpressionStrOperationEncode1,
    ExpressionStrOperationEncode2,
    ExpressionStrOperationEndswith2,
    ExpressionStrOperationEndswith3,
    ExpressionStrOperationEndswith4,
    ExpressionStrOperationExpandtabs1,
    ExpressionStrOperationExpandtabs2,
    ExpressionStrOperationFind2,
    ExpressionStrOperationFind3,
    ExpressionStrOperationFind4,
    ExpressionStrOperationFormat,
    ExpressionStrOperationIndex2,
    ExpressionStrOperationIndex3,
    ExpressionStrOperationIndex4,
    ExpressionStrOperationIsalnum,
    ExpressionStrOperationIsalpha,
    ExpressionStrOperationIsdigit,
    ExpressionStrOperationIslower,
    ExpressionStrOperationIsspace,
    ExpressionStrOperationIstitle,
    ExpressionStrOperationIsupper,
    ExpressionStrOperationJoin,
    ExpressionStrOperationLjust2,
    ExpressionStrOperationLjust3,
    ExpressionStrOperationLower,
    ExpressionStrOperationLstrip1,
    ExpressionStrOperationLstrip2,
    ExpressionStrOperationPartition,
    ExpressionStrOperationReplace3,
    ExpressionStrOperationReplace4,
    ExpressionStrOperationRfind2,
    ExpressionStrOperationRfind3,
    ExpressionStrOperationRfind4,
    ExpressionStrOperationRindex2,
    ExpressionStrOperationRindex3,
    ExpressionStrOperationRindex4,
    ExpressionStrOperationRjust2,
    ExpressionStrOperationRjust3,
    ExpressionStrOperationRpartition,
    ExpressionStrOperationRsplit1,
    ExpressionStrOperationRsplit2,
    ExpressionStrOperationRstrip1,
    ExpressionStrOperationRstrip2,
    ExpressionStrOperationSplit1,
    ExpressionStrOperationSplit2,
    ExpressionStrOperationSplitlines1,
    ExpressionStrOperationSplitlines2,
    ExpressionStrOperationStartswith2,
    ExpressionStrOperationStartswith3,
    ExpressionStrOperationStartswith4,
    ExpressionStrOperationStrip1,
    ExpressionStrOperationStrip2,
    ExpressionStrOperationSwapcase,
    ExpressionStrOperationTitle,
    ExpressionStrOperationTranslate,
    ExpressionStrOperationUpper,
    ExpressionStrOperationZfill,
    makeExpressionStrOperationEncode3,
    makeExpressionStrOperationRsplit3,
    makeExpressionStrOperationSplit3,
)

attribute_classes = {}
attribute_typed_classes = set()


class ExpressionAttributeLookupFixedPrepare(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value '__prepare__' of an object.

    Typically code like: source.__prepare__
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_PREPARE"
    attribute_name = "__prepare__"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is not bytes and subnode_expression.hasShapeTypeExact():
            result = ExpressionAttributeLookupTypePrepare(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup '__prepare__' on type shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="__prepare__",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="__prepare__"
        )


attribute_classes["__prepare__"] = ExpressionAttributeLookupFixedPrepare


class ExpressionAttributeLookupTypePrepare(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedPrepare
):
    """Attribute '__prepare__' lookup on a type value.

    Typically code like: some_type.__prepare__
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_TYPE_PREPARE"
    attribute_name = "__prepare__"

    # There is nothing to compute for it as a value.
    # TODO: Enable this once we can also say removal of knowable for an argument.
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        # Cannot be used to modify the type.
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, type_arg, trace_collection):
        def wrapExpressionTypeOperationPrepare(args, kwargs, source_ref):
            return ExpressionTypeOperationPrepare(
                type_arg=type_arg, args=args, kwargs=kwargs, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionTypeOperationPrepare,
            builtin_spec=type___prepare___spec,
        )

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Call to '__prepare__' of type recognized.",
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        type_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, type_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupTypePrepare)


class ExpressionAttributeLookupFixedAppend(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'append' of an object.

    Typically code like: source.append
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_APPEND"
    attribute_name = "append"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeListExact():
            result = ExpressionAttributeLookupListAppend(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'append' on list shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="append",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="append"
        )

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["append"] = ExpressionAttributeLookupFixedAppend


class ExpressionAttributeLookupListAppend(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedAppend
):
    """Attribute append lookup on a list value.

    Typically code like: some_list.append
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_LIST_APPEND"
    attribute_name = "append"

    def computeExpression(self, trace_collection):
        # Might be used to modify the list.
        trace_collection.removeKnowledge(self.subnode_expression)

        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, list_arg, trace_collection):
        def wrapExpressionListOperationAppend(item, source_ref):
            return ExpressionListOperationAppend(
                list_arg=list_arg, item=item, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionListOperationAppend,
            builtin_spec=list_append_spec,
        )

        return result, "new_expression", "Call to 'append' of list recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        list_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, list_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupListAppend)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'capitalize' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesCapitalize(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'capitalize' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrCapitalize(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedCapitalize
):
    """Attribute 'capitalize' lookup on a str value.

    Typically code like: some_str.capitalize
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_CAPITALIZE"
    attribute_name = "capitalize"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationCapitalize(source_ref):
            return ExpressionStrOperationCapitalize(
                str_arg=str_arg, source_ref=source_ref
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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrCapitalize)


class ExpressionAttributeLookupBytesCapitalize(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedCapitalize
):
    """Attribute 'capitalize' lookup on a bytes value.

    Typically code like: some_bytes.capitalize
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_CAPITALIZE"
    attribute_name = "capitalize"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationCapitalize(source_ref):
            return ExpressionBytesOperationCapitalize(
                bytes_arg=bytes_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationCapitalize,
            builtin_spec=bytes_capitalize_spec,
        )

        return result, "new_expression", "Call to 'capitalize' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesCapitalize)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'casefold' on str shape resolved.",
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
    """Attribute 'casefold' lookup on a str value.

    Typically code like: some_str.casefold
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_CASEFOLD"
    attribute_name = "casefold"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'center' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesCenter(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'center' on bytes shape resolved.",
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
    """Attribute 'center' lookup on a str value.

    Typically code like: some_str.center
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_CENTER"
    attribute_name = "center"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationCenter(width, fillchar, source_ref):
            if fillchar is not None:
                return ExpressionStrOperationCenter3(
                    str_arg=str_arg,
                    width=width,
                    fillchar=fillchar,
                    source_ref=source_ref,
                )
            else:
                return ExpressionStrOperationCenter2(
                    str_arg=str_arg, width=width, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationCenter,
            builtin_spec=str_center_spec,
        )

        return result, "new_expression", "Call to 'center' of str recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrCenter)


class ExpressionAttributeLookupBytesCenter(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedCenter
):
    """Attribute 'center' lookup on a bytes value.

    Typically code like: some_bytes.center
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_CENTER"
    attribute_name = "center"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationCenter(width, fillchar, source_ref):
            if fillchar is not None:
                return ExpressionBytesOperationCenter3(
                    bytes_arg=bytes_arg,
                    width=width,
                    fillchar=fillchar,
                    source_ref=source_ref,
                )
            else:
                return ExpressionBytesOperationCenter2(
                    bytes_arg=bytes_arg, width=width, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationCenter,
            builtin_spec=bytes_center_spec,
        )

        return result, "new_expression", "Call to 'center' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesCenter)


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
        if str is not bytes and subnode_expression.hasShapeListExact():
            result = ExpressionAttributeLookupListClear(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'clear' on list shape resolved.",
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

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["clear"] = ExpressionAttributeLookupFixedClear


class ExpressionAttributeLookupDictClear(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedClear
):
    """Attribute 'clear' lookup on a dict value.

    Typically code like: some_dict.clear
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_CLEAR"
    attribute_name = "clear"

    # There is nothing to compute for it as a value.
    # TODO: Enable this once we can also say removal of knowable for an argument.
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        # Might be used to modify the dict.
        trace_collection.removeKnowledge(self.subnode_expression)

        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, dict_arg, trace_collection):
        def wrapExpressionDictOperationClear(source_ref):
            return ExpressionDictOperationClear(
                dict_arg=dict_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        dict_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, dict_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupDictClear)


class ExpressionAttributeLookupListClear(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedClear
):
    """Attribute clear lookup on a list value.

    Typically code like: some_list.clear
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_LIST_CLEAR"
    attribute_name = "clear"

    def computeExpression(self, trace_collection):
        # Might be used to modify the list.
        trace_collection.removeKnowledge(self.subnode_expression)

        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, list_arg, trace_collection):
        def wrapExpressionListOperationClear(source_ref):
            return ExpressionListOperationClear(
                list_arg=list_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionListOperationClear,
            builtin_spec=list_clear_spec,
        )

        return result, "new_expression", "Call to 'clear' of list recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        list_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, list_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupListClear)


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
        if str is not bytes and subnode_expression.hasShapeListExact():
            result = ExpressionAttributeLookupListCopy(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'copy' on list shape resolved.",
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

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["copy"] = ExpressionAttributeLookupFixedCopy


class ExpressionAttributeLookupDictCopy(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedCopy
):
    """Attribute 'copy' lookup on a dict value.

    Typically code like: some_dict.copy
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_COPY"
    attribute_name = "copy"

    # There is nothing to compute for it as a value.
    # TODO: Enable this once we can also say removal of knowable for an argument.
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        # Might be used to modify the dict.
        trace_collection.removeKnowledge(self.subnode_expression)

        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, dict_arg, trace_collection):
        def wrapExpressionDictOperationCopy(source_ref):
            return ExpressionDictOperationCopy(dict_arg=dict_arg, source_ref=source_ref)

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        dict_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, dict_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupDictCopy)


class ExpressionAttributeLookupListCopy(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedCopy
):
    """Attribute copy lookup on a list value.

    Typically code like: some_list.copy
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_LIST_COPY"
    attribute_name = "copy"

    def computeExpression(self, trace_collection):
        # Might be used to modify the list.
        trace_collection.removeKnowledge(self.subnode_expression)

        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, list_arg, trace_collection):
        def wrapExpressionListOperationCopy(source_ref):
            return ExpressionListOperationCopy(list_arg=list_arg, source_ref=source_ref)

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionListOperationCopy,
            builtin_spec=list_copy_spec,
        )

        return result, "new_expression", "Call to 'copy' of list recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        list_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, list_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupListCopy)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'count' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesCount(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'count' on bytes shape resolved.",
            )
        if subnode_expression.hasShapeListExact():
            result = ExpressionAttributeLookupListCount(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'count' on list shape resolved.",
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

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["count"] = ExpressionAttributeLookupFixedCount


class ExpressionAttributeLookupStrCount(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedCount
):
    """Attribute 'count' lookup on a str value.

    Typically code like: some_str.count
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_COUNT"
    attribute_name = "count"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationCount(sub, start, end, source_ref):
            if end is not None:
                return ExpressionStrOperationCount4(
                    str_arg=str_arg,
                    sub=sub,
                    start=start,
                    end=end,
                    source_ref=source_ref,
                )
            elif start is not None:
                return ExpressionStrOperationCount3(
                    str_arg=str_arg, sub=sub, start=start, source_ref=source_ref
                )
            else:
                return ExpressionStrOperationCount2(
                    str_arg=str_arg, sub=sub, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationCount,
            builtin_spec=str_count_spec,
        )

        return result, "new_expression", "Call to 'count' of str recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrCount)


class ExpressionAttributeLookupBytesCount(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedCount
):
    """Attribute 'count' lookup on a bytes value.

    Typically code like: some_bytes.count
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_COUNT"
    attribute_name = "count"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationCount(sub, start, end, source_ref):
            if end is not None:
                return ExpressionBytesOperationCount4(
                    bytes_arg=bytes_arg,
                    sub=sub,
                    start=start,
                    end=end,
                    source_ref=source_ref,
                )
            elif start is not None:
                return ExpressionBytesOperationCount3(
                    bytes_arg=bytes_arg, sub=sub, start=start, source_ref=source_ref
                )
            else:
                return ExpressionBytesOperationCount2(
                    bytes_arg=bytes_arg, sub=sub, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationCount,
            builtin_spec=bytes_count_spec,
        )

        return result, "new_expression", "Call to 'count' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesCount)


class ExpressionAttributeLookupListCount(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedCount
):
    """Attribute count lookup on a list value.

    Typically code like: some_list.count
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_LIST_COUNT"
    attribute_name = "count"

    def computeExpression(self, trace_collection):
        # Cannot be used to modify the list.
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, list_arg, trace_collection):
        def wrapExpressionListOperationCount(value, source_ref):
            return ExpressionListOperationCount(
                list_arg=list_arg, value=value, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionListOperationCount,
            builtin_spec=list_count_spec,
        )

        return result, "new_expression", "Call to 'count' of list recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        list_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, list_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupListCount)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'decode' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesDecode(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'decode' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrDecode(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedDecode
):
    """Attribute 'decode' lookup on a str value.

    Typically code like: some_str.decode
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_DECODE"
    attribute_name = "decode"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationDecode(encoding, errors, source_ref):
            if errors is not None:
                return ExpressionStrOperationDecode3(
                    str_arg=str_arg,
                    encoding=encoding,
                    errors=errors,
                    source_ref=source_ref,
                )
            elif encoding is not None:
                return ExpressionStrOperationDecode2(
                    str_arg=str_arg, encoding=encoding, source_ref=source_ref
                )
            else:
                return ExpressionStrOperationDecode1(
                    str_arg=str_arg, source_ref=source_ref
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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrDecode)


class ExpressionAttributeLookupBytesDecode(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedDecode
):
    """Attribute 'decode' lookup on a bytes value.

    Typically code like: some_bytes.decode
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_DECODE"
    attribute_name = "decode"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationDecode(encoding, errors, source_ref):
            if errors is not None:
                return makeExpressionBytesOperationDecode3(
                    bytes_arg=bytes_arg,
                    encoding=encoding,
                    errors=errors,
                    source_ref=source_ref,
                )
            elif encoding is not None:
                return ExpressionBytesOperationDecode2(
                    bytes_arg=bytes_arg, encoding=encoding, source_ref=source_ref
                )
            else:
                return ExpressionBytesOperationDecode1(
                    bytes_arg=bytes_arg, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationDecode,
            builtin_spec=bytes_decode_spec,
        )

        return result, "new_expression", "Call to 'decode' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesDecode)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'encode' on str shape resolved.",
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


class ExpressionAttributeLookupStrEncode(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedEncode
):
    """Attribute 'encode' lookup on a str value.

    Typically code like: some_str.encode
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ENCODE"
    attribute_name = "encode"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationEncode(encoding, errors, source_ref):
            if errors is not None:
                return makeExpressionStrOperationEncode3(
                    str_arg=str_arg,
                    encoding=encoding,
                    errors=errors,
                    source_ref=source_ref,
                )
            elif encoding is not None:
                return ExpressionStrOperationEncode2(
                    str_arg=str_arg, encoding=encoding, source_ref=source_ref
                )
            else:
                return ExpressionStrOperationEncode1(
                    str_arg=str_arg, source_ref=source_ref
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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'endswith' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesEndswith(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'endswith' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrEndswith(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedEndswith
):
    """Attribute 'endswith' lookup on a str value.

    Typically code like: some_str.endswith
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ENDSWITH"
    attribute_name = "endswith"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationEndswith(suffix, start, end, source_ref):
            if end is not None:
                return ExpressionStrOperationEndswith4(
                    str_arg=str_arg,
                    suffix=suffix,
                    start=start,
                    end=end,
                    source_ref=source_ref,
                )
            elif start is not None:
                return ExpressionStrOperationEndswith3(
                    str_arg=str_arg, suffix=suffix, start=start, source_ref=source_ref
                )
            else:
                return ExpressionStrOperationEndswith2(
                    str_arg=str_arg, suffix=suffix, source_ref=source_ref
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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrEndswith)


class ExpressionAttributeLookupBytesEndswith(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedEndswith
):
    """Attribute 'endswith' lookup on a bytes value.

    Typically code like: some_bytes.endswith
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_ENDSWITH"
    attribute_name = "endswith"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationEndswith(suffix, start, end, source_ref):
            if end is not None:
                return ExpressionBytesOperationEndswith4(
                    bytes_arg=bytes_arg,
                    suffix=suffix,
                    start=start,
                    end=end,
                    source_ref=source_ref,
                )
            elif start is not None:
                return ExpressionBytesOperationEndswith3(
                    bytes_arg=bytes_arg,
                    suffix=suffix,
                    start=start,
                    source_ref=source_ref,
                )
            else:
                return ExpressionBytesOperationEndswith2(
                    bytes_arg=bytes_arg, suffix=suffix, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationEndswith,
            builtin_spec=bytes_endswith_spec,
        )

        return result, "new_expression", "Call to 'endswith' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesEndswith)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'expandtabs' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesExpandtabs(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'expandtabs' on bytes shape resolved.",
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
    """Attribute 'expandtabs' lookup on a str value.

    Typically code like: some_str.expandtabs
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_EXPANDTABS"
    attribute_name = "expandtabs"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationExpandtabs(tabsize, source_ref):
            if tabsize is not None:
                return ExpressionStrOperationExpandtabs2(
                    str_arg=str_arg, tabsize=tabsize, source_ref=source_ref
                )
            else:
                return ExpressionStrOperationExpandtabs1(
                    str_arg=str_arg, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationExpandtabs,
            builtin_spec=str_expandtabs_spec,
        )

        return result, "new_expression", "Call to 'expandtabs' of str recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrExpandtabs)


class ExpressionAttributeLookupBytesExpandtabs(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedExpandtabs
):
    """Attribute 'expandtabs' lookup on a bytes value.

    Typically code like: some_bytes.expandtabs
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_EXPANDTABS"
    attribute_name = "expandtabs"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationExpandtabs(tabsize, source_ref):
            if tabsize is not None:
                return ExpressionBytesOperationExpandtabs2(
                    bytes_arg=bytes_arg, tabsize=tabsize, source_ref=source_ref
                )
            else:
                return ExpressionBytesOperationExpandtabs1(
                    bytes_arg=bytes_arg, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationExpandtabs,
            builtin_spec=bytes_expandtabs_spec,
        )

        return result, "new_expression", "Call to 'expandtabs' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesExpandtabs)


class ExpressionAttributeLookupFixedExtend(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'extend' of an object.

    Typically code like: source.extend
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_EXTEND"
    attribute_name = "extend"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeListExact():
            result = ExpressionAttributeLookupListExtend(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'extend' on list shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="extend",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="extend"
        )

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["extend"] = ExpressionAttributeLookupFixedExtend


class ExpressionAttributeLookupListExtend(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedExtend
):
    """Attribute extend lookup on a list value.

    Typically code like: some_list.extend
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_LIST_EXTEND"
    attribute_name = "extend"

    def computeExpression(self, trace_collection):
        # Might be used to modify the list.
        trace_collection.removeKnowledge(self.subnode_expression)

        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, list_arg, trace_collection):
        def wrapExpressionListOperationExtend(value, source_ref):
            return ExpressionListOperationExtend(
                list_arg=list_arg, value=value, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionListOperationExtend,
            builtin_spec=list_extend_spec,
        )

        return result, "new_expression", "Call to 'extend' of list recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        list_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, list_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupListExtend)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'find' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesFind(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'find' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrFind(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedFind
):
    """Attribute 'find' lookup on a str value.

    Typically code like: some_str.find
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_FIND"
    attribute_name = "find"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationFind(sub, start, end, source_ref):
            if end is not None:
                return ExpressionStrOperationFind4(
                    str_arg=str_arg,
                    sub=sub,
                    start=start,
                    end=end,
                    source_ref=source_ref,
                )
            elif start is not None:
                return ExpressionStrOperationFind3(
                    str_arg=str_arg, sub=sub, start=start, source_ref=source_ref
                )
            else:
                return ExpressionStrOperationFind2(
                    str_arg=str_arg, sub=sub, source_ref=source_ref
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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrFind)


class ExpressionAttributeLookupBytesFind(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedFind
):
    """Attribute 'find' lookup on a bytes value.

    Typically code like: some_bytes.find
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_FIND"
    attribute_name = "find"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationFind(sub, start, end, source_ref):
            if end is not None:
                return ExpressionBytesOperationFind4(
                    bytes_arg=bytes_arg,
                    sub=sub,
                    start=start,
                    end=end,
                    source_ref=source_ref,
                )
            elif start is not None:
                return ExpressionBytesOperationFind3(
                    bytes_arg=bytes_arg, sub=sub, start=start, source_ref=source_ref
                )
            else:
                return ExpressionBytesOperationFind2(
                    bytes_arg=bytes_arg, sub=sub, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationFind,
            builtin_spec=bytes_find_spec,
        )

        return result, "new_expression", "Call to 'find' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesFind)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'format' on str shape resolved.",
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
    """Attribute 'format' lookup on a str value.

    Typically code like: some_str.format
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_FORMAT"
    attribute_name = "format"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationFormat(args, pairs, source_ref):
            return ExpressionStrOperationFormat(
                str_arg=str_arg,
                args=args,
                pairs=makeKeyValuePairExpressionsFromKwArgs(pairs),
                source_ref=source_ref,
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationFormat,
            builtin_spec=str_format_spec,
        )

        return result, "new_expression", "Call to 'format' of str recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'format_map' on str shape resolved.",
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
    """Attribute 'format_map' lookup on a str value.

    Typically code like: some_str.format_map
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_FORMATMAP"
    attribute_name = "format_map"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

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

        if subnode_expression.isExpressionConstantTypeDictRef():
            return (
                ExpressionDictOperationFromkeysRef(source_ref=self.source_ref),
                "new_expression",
                "Reference to 'dict.fromkeys' resolved.",
            )
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

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["fromkeys"] = ExpressionAttributeLookupFixedFromkeys


class ExpressionAttributeLookupDictFromkeys(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedFromkeys
):
    """Attribute 'fromkeys' lookup on a dict value.

    Typically code like: some_dict.fromkeys
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_FROMKEYS"
    attribute_name = "fromkeys"

    # There is nothing to compute for it as a value.
    # TODO: Enable this once we can also say removal of knowable for an argument.
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        # Cannot be used to modify the dict.
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, dict_arg, trace_collection):
        def wrapExpressionDictOperationFromkeys(iterable, value, source_ref):
            if value is not None:
                return ExpressionDictOperationFromkeys3(
                    iterable=iterable, value=value, source_ref=source_ref
                )
            else:
                return ExpressionDictOperationFromkeys2(
                    iterable=iterable, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationFromkeys,
            builtin_spec=dict_fromkeys_spec,
        )

        result = wrapExpressionWithNodeSideEffects(old_node=dict_arg, new_node=result)

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Call to 'fromkeys' of dictionary recognized.",
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        dict_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, dict_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


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

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["get"] = ExpressionAttributeLookupFixedGet


class ExpressionAttributeLookupDictGet(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedGet
):
    """Attribute 'get' lookup on a dict value.

    Typically code like: some_dict.get
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_GET"
    attribute_name = "get"

    # There is nothing to compute for it as a value.
    # TODO: Enable this once we can also say removal of knowable for an argument.
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        # Cannot be used to modify the dict.
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, dict_arg, trace_collection):
        def wrapExpressionDictOperationGet(key, default, source_ref):
            if default is not None:
                return ExpressionDictOperationGet3(
                    dict_arg=dict_arg, key=key, default=default, source_ref=source_ref
                )
            else:
                return ExpressionDictOperationGet2(
                    dict_arg=dict_arg, key=key, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        dict_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, dict_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


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

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["has_key"] = ExpressionAttributeLookupFixedHaskey


class ExpressionAttributeLookupDictHaskey(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedHaskey
):
    """Attribute 'has_key' lookup on a dict value.

    Typically code like: some_dict.has_key
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_HASKEY"
    attribute_name = "has_key"

    # There is nothing to compute for it as a value.
    # TODO: Enable this once we can also say removal of knowable for an argument.
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        # Cannot be used to modify the dict.
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, dict_arg, trace_collection):
        def wrapExpressionDictOperationHaskey(key, source_ref):
            return ExpressionDictOperationHaskey(
                dict_arg=dict_arg, key=key, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        dict_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, dict_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'index' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesIndex(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'index' on bytes shape resolved.",
            )
        if subnode_expression.hasShapeListExact():
            result = ExpressionAttributeLookupListIndex(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'index' on list shape resolved.",
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

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["index"] = ExpressionAttributeLookupFixedIndex


class ExpressionAttributeLookupStrIndex(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIndex
):
    """Attribute 'index' lookup on a str value.

    Typically code like: some_str.index
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_INDEX"
    attribute_name = "index"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationIndex(sub, start, end, source_ref):
            if end is not None:
                return ExpressionStrOperationIndex4(
                    str_arg=str_arg,
                    sub=sub,
                    start=start,
                    end=end,
                    source_ref=source_ref,
                )
            elif start is not None:
                return ExpressionStrOperationIndex3(
                    str_arg=str_arg, sub=sub, start=start, source_ref=source_ref
                )
            else:
                return ExpressionStrOperationIndex2(
                    str_arg=str_arg, sub=sub, source_ref=source_ref
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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrIndex)


class ExpressionAttributeLookupBytesIndex(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIndex
):
    """Attribute 'index' lookup on a bytes value.

    Typically code like: some_bytes.index
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_INDEX"
    attribute_name = "index"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationIndex(sub, start, end, source_ref):
            if end is not None:
                return ExpressionBytesOperationIndex4(
                    bytes_arg=bytes_arg,
                    sub=sub,
                    start=start,
                    end=end,
                    source_ref=source_ref,
                )
            elif start is not None:
                return ExpressionBytesOperationIndex3(
                    bytes_arg=bytes_arg, sub=sub, start=start, source_ref=source_ref
                )
            else:
                return ExpressionBytesOperationIndex2(
                    bytes_arg=bytes_arg, sub=sub, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationIndex,
            builtin_spec=bytes_index_spec,
        )

        return result, "new_expression", "Call to 'index' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesIndex)


class ExpressionAttributeLookupListIndex(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIndex
):
    """Attribute index lookup on a list value.

    Typically code like: some_list.index
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_LIST_INDEX"
    attribute_name = "index"

    def computeExpression(self, trace_collection):
        # Cannot be used to modify the list.
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, list_arg, trace_collection):
        def wrapExpressionListOperationIndex(value, start, stop, source_ref):
            if stop is not None:
                return ExpressionListOperationIndex4(
                    list_arg=list_arg,
                    value=value,
                    start=start,
                    stop=stop,
                    source_ref=source_ref,
                )
            elif start is not None:
                return ExpressionListOperationIndex3(
                    list_arg=list_arg, value=value, start=start, source_ref=source_ref
                )
            else:
                return ExpressionListOperationIndex2(
                    list_arg=list_arg, value=value, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionListOperationIndex,
            builtin_spec=list_index_spec,
        )

        return result, "new_expression", "Call to 'index' of list recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        list_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, list_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupListIndex)


class ExpressionAttributeLookupFixedInsert(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'insert' of an object.

    Typically code like: source.insert
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_INSERT"
    attribute_name = "insert"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeListExact():
            result = ExpressionAttributeLookupListInsert(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'insert' on list shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="insert",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="insert"
        )

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["insert"] = ExpressionAttributeLookupFixedInsert


class ExpressionAttributeLookupListInsert(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedInsert
):
    """Attribute insert lookup on a list value.

    Typically code like: some_list.insert
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_LIST_INSERT"
    attribute_name = "insert"

    def computeExpression(self, trace_collection):
        # Might be used to modify the list.
        trace_collection.removeKnowledge(self.subnode_expression)

        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, list_arg, trace_collection):
        def wrapExpressionListOperationInsert(index, item, source_ref):
            return ExpressionListOperationInsert(
                list_arg=list_arg, index=index, item=item, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionListOperationInsert,
            builtin_spec=list_insert_spec,
        )

        return result, "new_expression", "Call to 'insert' of list recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        list_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, list_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupListInsert)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'isalnum' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesIsalnum(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'isalnum' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrIsalnum(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIsalnum
):
    """Attribute 'isalnum' lookup on a str value.

    Typically code like: some_str.isalnum
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISALNUM"
    attribute_name = "isalnum"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationIsalnum(source_ref):
            return ExpressionStrOperationIsalnum(str_arg=str_arg, source_ref=source_ref)

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationIsalnum,
            builtin_spec=str_isalnum_spec,
        )

        return result, "new_expression", "Call to 'isalnum' of str recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrIsalnum)


class ExpressionAttributeLookupBytesIsalnum(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIsalnum
):
    """Attribute 'isalnum' lookup on a bytes value.

    Typically code like: some_bytes.isalnum
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_ISALNUM"
    attribute_name = "isalnum"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationIsalnum(source_ref):
            return ExpressionBytesOperationIsalnum(
                bytes_arg=bytes_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationIsalnum,
            builtin_spec=bytes_isalnum_spec,
        )

        return result, "new_expression", "Call to 'isalnum' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesIsalnum)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'isalpha' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesIsalpha(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'isalpha' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrIsalpha(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIsalpha
):
    """Attribute 'isalpha' lookup on a str value.

    Typically code like: some_str.isalpha
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISALPHA"
    attribute_name = "isalpha"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationIsalpha(source_ref):
            return ExpressionStrOperationIsalpha(str_arg=str_arg, source_ref=source_ref)

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationIsalpha,
            builtin_spec=str_isalpha_spec,
        )

        return result, "new_expression", "Call to 'isalpha' of str recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrIsalpha)


class ExpressionAttributeLookupBytesIsalpha(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIsalpha
):
    """Attribute 'isalpha' lookup on a bytes value.

    Typically code like: some_bytes.isalpha
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_ISALPHA"
    attribute_name = "isalpha"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationIsalpha(source_ref):
            return ExpressionBytesOperationIsalpha(
                bytes_arg=bytes_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationIsalpha,
            builtin_spec=bytes_isalpha_spec,
        )

        return result, "new_expression", "Call to 'isalpha' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesIsalpha)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'isascii' on str shape resolved.",
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
    """Attribute 'isascii' lookup on a str value.

    Typically code like: some_str.isascii
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISASCII"
    attribute_name = "isascii"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'isdecimal' on str shape resolved.",
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
    """Attribute 'isdecimal' lookup on a str value.

    Typically code like: some_str.isdecimal
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISDECIMAL"
    attribute_name = "isdecimal"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'isdigit' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesIsdigit(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'isdigit' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrIsdigit(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIsdigit
):
    """Attribute 'isdigit' lookup on a str value.

    Typically code like: some_str.isdigit
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISDIGIT"
    attribute_name = "isdigit"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationIsdigit(source_ref):
            return ExpressionStrOperationIsdigit(str_arg=str_arg, source_ref=source_ref)

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationIsdigit,
            builtin_spec=str_isdigit_spec,
        )

        return result, "new_expression", "Call to 'isdigit' of str recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrIsdigit)


class ExpressionAttributeLookupBytesIsdigit(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIsdigit
):
    """Attribute 'isdigit' lookup on a bytes value.

    Typically code like: some_bytes.isdigit
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_ISDIGIT"
    attribute_name = "isdigit"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationIsdigit(source_ref):
            return ExpressionBytesOperationIsdigit(
                bytes_arg=bytes_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationIsdigit,
            builtin_spec=bytes_isdigit_spec,
        )

        return result, "new_expression", "Call to 'isdigit' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesIsdigit)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'isidentifier' on str shape resolved.",
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
    """Attribute 'isidentifier' lookup on a str value.

    Typically code like: some_str.isidentifier
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISIDENTIFIER"
    attribute_name = "isidentifier"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'islower' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesIslower(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'islower' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrIslower(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIslower
):
    """Attribute 'islower' lookup on a str value.

    Typically code like: some_str.islower
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISLOWER"
    attribute_name = "islower"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationIslower(source_ref):
            return ExpressionStrOperationIslower(str_arg=str_arg, source_ref=source_ref)

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationIslower,
            builtin_spec=str_islower_spec,
        )

        return result, "new_expression", "Call to 'islower' of str recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrIslower)


class ExpressionAttributeLookupBytesIslower(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIslower
):
    """Attribute 'islower' lookup on a bytes value.

    Typically code like: some_bytes.islower
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_ISLOWER"
    attribute_name = "islower"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationIslower(source_ref):
            return ExpressionBytesOperationIslower(
                bytes_arg=bytes_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationIslower,
            builtin_spec=bytes_islower_spec,
        )

        return result, "new_expression", "Call to 'islower' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesIslower)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'isnumeric' on str shape resolved.",
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
    """Attribute 'isnumeric' lookup on a str value.

    Typically code like: some_str.isnumeric
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISNUMERIC"
    attribute_name = "isnumeric"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'isprintable' on str shape resolved.",
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
    """Attribute 'isprintable' lookup on a str value.

    Typically code like: some_str.isprintable
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISPRINTABLE"
    attribute_name = "isprintable"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'isspace' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesIsspace(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'isspace' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrIsspace(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIsspace
):
    """Attribute 'isspace' lookup on a str value.

    Typically code like: some_str.isspace
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISSPACE"
    attribute_name = "isspace"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationIsspace(source_ref):
            return ExpressionStrOperationIsspace(str_arg=str_arg, source_ref=source_ref)

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationIsspace,
            builtin_spec=str_isspace_spec,
        )

        return result, "new_expression", "Call to 'isspace' of str recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrIsspace)


class ExpressionAttributeLookupBytesIsspace(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIsspace
):
    """Attribute 'isspace' lookup on a bytes value.

    Typically code like: some_bytes.isspace
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_ISSPACE"
    attribute_name = "isspace"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationIsspace(source_ref):
            return ExpressionBytesOperationIsspace(
                bytes_arg=bytes_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationIsspace,
            builtin_spec=bytes_isspace_spec,
        )

        return result, "new_expression", "Call to 'isspace' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesIsspace)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'istitle' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesIstitle(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'istitle' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrIstitle(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIstitle
):
    """Attribute 'istitle' lookup on a str value.

    Typically code like: some_str.istitle
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISTITLE"
    attribute_name = "istitle"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationIstitle(source_ref):
            return ExpressionStrOperationIstitle(str_arg=str_arg, source_ref=source_ref)

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationIstitle,
            builtin_spec=str_istitle_spec,
        )

        return result, "new_expression", "Call to 'istitle' of str recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrIstitle)


class ExpressionAttributeLookupBytesIstitle(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIstitle
):
    """Attribute 'istitle' lookup on a bytes value.

    Typically code like: some_bytes.istitle
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_ISTITLE"
    attribute_name = "istitle"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationIstitle(source_ref):
            return ExpressionBytesOperationIstitle(
                bytes_arg=bytes_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationIstitle,
            builtin_spec=bytes_istitle_spec,
        )

        return result, "new_expression", "Call to 'istitle' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesIstitle)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'isupper' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesIsupper(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'isupper' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrIsupper(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIsupper
):
    """Attribute 'isupper' lookup on a str value.

    Typically code like: some_str.isupper
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ISUPPER"
    attribute_name = "isupper"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationIsupper(source_ref):
            return ExpressionStrOperationIsupper(str_arg=str_arg, source_ref=source_ref)

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationIsupper,
            builtin_spec=str_isupper_spec,
        )

        return result, "new_expression", "Call to 'isupper' of str recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrIsupper)


class ExpressionAttributeLookupBytesIsupper(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIsupper
):
    """Attribute 'isupper' lookup on a bytes value.

    Typically code like: some_bytes.isupper
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_ISUPPER"
    attribute_name = "isupper"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationIsupper(source_ref):
            return ExpressionBytesOperationIsupper(
                bytes_arg=bytes_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationIsupper,
            builtin_spec=bytes_isupper_spec,
        )

        return result, "new_expression", "Call to 'isupper' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesIsupper)


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

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["items"] = ExpressionAttributeLookupFixedItems


class ExpressionAttributeLookupDictItems(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedItems
):
    """Attribute 'items' lookup on a dict value.

    Typically code like: some_dict.items
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_ITEMS"
    attribute_name = "items"

    # There is nothing to compute for it as a value.
    # TODO: Enable this once we can also say removal of knowable for an argument.
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        # Cannot be used to modify the dict.
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, dict_arg, trace_collection):
        def wrapExpressionDictOperationItems(source_ref):
            if str is bytes:
                return ExpressionDictOperationItems(
                    dict_arg=dict_arg, source_ref=source_ref
                )
            else:
                return ExpressionDictOperationIteritems(
                    dict_arg=dict_arg, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        dict_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, dict_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


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

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["iteritems"] = ExpressionAttributeLookupFixedIteritems


class ExpressionAttributeLookupDictIteritems(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIteritems
):
    """Attribute 'iteritems' lookup on a dict value.

    Typically code like: some_dict.iteritems
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_ITERITEMS"
    attribute_name = "iteritems"

    # There is nothing to compute for it as a value.
    # TODO: Enable this once we can also say removal of knowable for an argument.
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        # Cannot be used to modify the dict.
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, dict_arg, trace_collection):
        def wrapExpressionDictOperationIteritems(source_ref):
            return ExpressionDictOperationIteritems(
                dict_arg=dict_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        dict_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, dict_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


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

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["iterkeys"] = ExpressionAttributeLookupFixedIterkeys


class ExpressionAttributeLookupDictIterkeys(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIterkeys
):
    """Attribute 'iterkeys' lookup on a dict value.

    Typically code like: some_dict.iterkeys
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_ITERKEYS"
    attribute_name = "iterkeys"

    # There is nothing to compute for it as a value.
    # TODO: Enable this once we can also say removal of knowable for an argument.
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        # Cannot be used to modify the dict.
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, dict_arg, trace_collection):
        def wrapExpressionDictOperationIterkeys(source_ref):
            return ExpressionDictOperationIterkeys(
                dict_arg=dict_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        dict_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, dict_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


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

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["itervalues"] = ExpressionAttributeLookupFixedItervalues


class ExpressionAttributeLookupDictItervalues(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedItervalues
):
    """Attribute 'itervalues' lookup on a dict value.

    Typically code like: some_dict.itervalues
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_ITERVALUES"
    attribute_name = "itervalues"

    # There is nothing to compute for it as a value.
    # TODO: Enable this once we can also say removal of knowable for an argument.
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        # Cannot be used to modify the dict.
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, dict_arg, trace_collection):
        def wrapExpressionDictOperationItervalues(source_ref):
            return ExpressionDictOperationItervalues(
                dict_arg=dict_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        dict_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, dict_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'join' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesJoin(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'join' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrJoin(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedJoin
):
    """Attribute 'join' lookup on a str value.

    Typically code like: some_str.join
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_JOIN"
    attribute_name = "join"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationJoin(iterable, source_ref):
            return ExpressionStrOperationJoin(
                str_arg=str_arg, iterable=iterable, source_ref=source_ref
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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrJoin)


class ExpressionAttributeLookupBytesJoin(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedJoin
):
    """Attribute 'join' lookup on a bytes value.

    Typically code like: some_bytes.join
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_JOIN"
    attribute_name = "join"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationJoin(iterable, source_ref):
            return ExpressionBytesOperationJoin(
                bytes_arg=bytes_arg, iterable=iterable, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationJoin,
            builtin_spec=bytes_join_spec,
        )

        return result, "new_expression", "Call to 'join' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesJoin)


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

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["keys"] = ExpressionAttributeLookupFixedKeys


class ExpressionAttributeLookupDictKeys(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedKeys
):
    """Attribute 'keys' lookup on a dict value.

    Typically code like: some_dict.keys
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_KEYS"
    attribute_name = "keys"

    # There is nothing to compute for it as a value.
    # TODO: Enable this once we can also say removal of knowable for an argument.
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        # Cannot be used to modify the dict.
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, dict_arg, trace_collection):
        def wrapExpressionDictOperationKeys(source_ref):
            if str is bytes:
                return ExpressionDictOperationKeys(
                    dict_arg=dict_arg, source_ref=source_ref
                )
            else:
                return ExpressionDictOperationIterkeys(
                    dict_arg=dict_arg, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        dict_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, dict_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'ljust' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesLjust(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'ljust' on bytes shape resolved.",
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
    """Attribute 'ljust' lookup on a str value.

    Typically code like: some_str.ljust
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_LJUST"
    attribute_name = "ljust"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationLjust(width, fillchar, source_ref):
            if fillchar is not None:
                return ExpressionStrOperationLjust3(
                    str_arg=str_arg,
                    width=width,
                    fillchar=fillchar,
                    source_ref=source_ref,
                )
            else:
                return ExpressionStrOperationLjust2(
                    str_arg=str_arg, width=width, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationLjust,
            builtin_spec=str_ljust_spec,
        )

        return result, "new_expression", "Call to 'ljust' of str recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrLjust)


class ExpressionAttributeLookupBytesLjust(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedLjust
):
    """Attribute 'ljust' lookup on a bytes value.

    Typically code like: some_bytes.ljust
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_LJUST"
    attribute_name = "ljust"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationLjust(width, fillchar, source_ref):
            if fillchar is not None:
                return ExpressionBytesOperationLjust3(
                    bytes_arg=bytes_arg,
                    width=width,
                    fillchar=fillchar,
                    source_ref=source_ref,
                )
            else:
                return ExpressionBytesOperationLjust2(
                    bytes_arg=bytes_arg, width=width, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationLjust,
            builtin_spec=bytes_ljust_spec,
        )

        return result, "new_expression", "Call to 'ljust' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesLjust)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'lower' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesLower(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'lower' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrLower(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedLower
):
    """Attribute 'lower' lookup on a str value.

    Typically code like: some_str.lower
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_LOWER"
    attribute_name = "lower"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationLower(source_ref):
            return ExpressionStrOperationLower(str_arg=str_arg, source_ref=source_ref)

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationLower,
            builtin_spec=str_lower_spec,
        )

        return result, "new_expression", "Call to 'lower' of str recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrLower)


class ExpressionAttributeLookupBytesLower(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedLower
):
    """Attribute 'lower' lookup on a bytes value.

    Typically code like: some_bytes.lower
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_LOWER"
    attribute_name = "lower"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationLower(source_ref):
            return ExpressionBytesOperationLower(
                bytes_arg=bytes_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationLower,
            builtin_spec=bytes_lower_spec,
        )

        return result, "new_expression", "Call to 'lower' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesLower)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'lstrip' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesLstrip(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'lstrip' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrLstrip(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedLstrip
):
    """Attribute 'lstrip' lookup on a str value.

    Typically code like: some_str.lstrip
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_LSTRIP"
    attribute_name = "lstrip"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationLstrip(chars, source_ref):
            if chars is not None:
                return ExpressionStrOperationLstrip2(
                    str_arg=str_arg, chars=chars, source_ref=source_ref
                )
            else:
                return ExpressionStrOperationLstrip1(
                    str_arg=str_arg, source_ref=source_ref
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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrLstrip)


class ExpressionAttributeLookupBytesLstrip(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedLstrip
):
    """Attribute 'lstrip' lookup on a bytes value.

    Typically code like: some_bytes.lstrip
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_LSTRIP"
    attribute_name = "lstrip"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationLstrip(chars, source_ref):
            if chars is not None:
                return ExpressionBytesOperationLstrip2(
                    bytes_arg=bytes_arg, chars=chars, source_ref=source_ref
                )
            else:
                return ExpressionBytesOperationLstrip1(
                    bytes_arg=bytes_arg, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationLstrip,
            builtin_spec=bytes_lstrip_spec,
        )

        return result, "new_expression", "Call to 'lstrip' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesLstrip)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'maketrans' on str shape resolved.",
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
    """Attribute 'maketrans' lookup on a str value.

    Typically code like: some_str.maketrans
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_MAKETRANS"
    attribute_name = "maketrans"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'partition' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesPartition(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'partition' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrPartition(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedPartition
):
    """Attribute 'partition' lookup on a str value.

    Typically code like: some_str.partition
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_PARTITION"
    attribute_name = "partition"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationPartition(sep, source_ref):
            return ExpressionStrOperationPartition(
                str_arg=str_arg, sep=sep, source_ref=source_ref
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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrPartition)


class ExpressionAttributeLookupBytesPartition(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedPartition
):
    """Attribute 'partition' lookup on a bytes value.

    Typically code like: some_bytes.partition
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_PARTITION"
    attribute_name = "partition"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationPartition(sep, source_ref):
            return ExpressionBytesOperationPartition(
                bytes_arg=bytes_arg, sep=sep, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationPartition,
            builtin_spec=bytes_partition_spec,
        )

        return result, "new_expression", "Call to 'partition' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesPartition)


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
        if subnode_expression.hasShapeListExact():
            result = ExpressionAttributeLookupListPop(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'pop' on list shape resolved.",
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

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["pop"] = ExpressionAttributeLookupFixedPop


class ExpressionAttributeLookupDictPop(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedPop
):
    """Attribute 'pop' lookup on a dict value.

    Typically code like: some_dict.pop
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_POP"
    attribute_name = "pop"

    # There is nothing to compute for it as a value.
    # TODO: Enable this once we can also say removal of knowable for an argument.
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        # Might be used to modify the dict.
        trace_collection.removeKnowledge(self.subnode_expression)

        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, dict_arg, trace_collection):
        def wrapExpressionDictOperationPop(key, default, source_ref):
            if default is not None:
                return ExpressionDictOperationPop3(
                    dict_arg=dict_arg, key=key, default=default, source_ref=source_ref
                )
            else:
                return ExpressionDictOperationPop2(
                    dict_arg=dict_arg, key=key, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        dict_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, dict_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupDictPop)


class ExpressionAttributeLookupListPop(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedPop
):
    """Attribute pop lookup on a list value.

    Typically code like: some_list.pop
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_LIST_POP"
    attribute_name = "pop"

    def computeExpression(self, trace_collection):
        # Might be used to modify the list.
        trace_collection.removeKnowledge(self.subnode_expression)

        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, list_arg, trace_collection):
        def wrapExpressionListOperationPop(index, source_ref):
            if index is not None:
                return ExpressionListOperationPop2(
                    list_arg=list_arg, index=index, source_ref=source_ref
                )
            else:
                return ExpressionListOperationPop1(
                    list_arg=list_arg, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionListOperationPop,
            builtin_spec=list_pop_spec,
        )

        return result, "new_expression", "Call to 'pop' of list recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        list_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, list_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupListPop)


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

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["popitem"] = ExpressionAttributeLookupFixedPopitem


class ExpressionAttributeLookupDictPopitem(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedPopitem
):
    """Attribute 'popitem' lookup on a dict value.

    Typically code like: some_dict.popitem
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_POPITEM"
    attribute_name = "popitem"

    # There is nothing to compute for it as a value.
    # TODO: Enable this once we can also say removal of knowable for an argument.
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        # Might be used to modify the dict.
        trace_collection.removeKnowledge(self.subnode_expression)

        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, dict_arg, trace_collection):
        def wrapExpressionDictOperationPopitem(source_ref):
            return ExpressionDictOperationPopitem(
                dict_arg=dict_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationPopitem,
            builtin_spec=dict_popitem_spec,
        )

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Call to 'popitem' of dictionary recognized.",
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        dict_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, dict_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupDictPopitem)


class ExpressionAttributeLookupFixedRemove(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'remove' of an object.

    Typically code like: source.remove
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_REMOVE"
    attribute_name = "remove"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeListExact():
            result = ExpressionAttributeLookupListRemove(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'remove' on list shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="remove",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="remove"
        )

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["remove"] = ExpressionAttributeLookupFixedRemove


class ExpressionAttributeLookupListRemove(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedRemove
):
    """Attribute remove lookup on a list value.

    Typically code like: some_list.remove
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_LIST_REMOVE"
    attribute_name = "remove"

    def computeExpression(self, trace_collection):
        # Might be used to modify the list.
        trace_collection.removeKnowledge(self.subnode_expression)

        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, list_arg, trace_collection):
        def wrapExpressionListOperationRemove(value, source_ref):
            return ExpressionListOperationRemove(
                list_arg=list_arg, value=value, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionListOperationRemove,
            builtin_spec=list_remove_spec,
        )

        return result, "new_expression", "Call to 'remove' of list recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        list_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, list_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupListRemove)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'replace' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesReplace(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'replace' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrReplace(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedReplace
):
    """Attribute 'replace' lookup on a str value.

    Typically code like: some_str.replace
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_REPLACE"
    attribute_name = "replace"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationReplace(old, new, count, source_ref):
            if count is not None:
                return ExpressionStrOperationReplace4(
                    str_arg=str_arg,
                    old=old,
                    new=new,
                    count=count,
                    source_ref=source_ref,
                )
            else:
                return ExpressionStrOperationReplace3(
                    str_arg=str_arg, old=old, new=new, source_ref=source_ref
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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrReplace)


class ExpressionAttributeLookupBytesReplace(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedReplace
):
    """Attribute 'replace' lookup on a bytes value.

    Typically code like: some_bytes.replace
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_REPLACE"
    attribute_name = "replace"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationReplace(old, new, count, source_ref):
            if count is not None:
                return ExpressionBytesOperationReplace4(
                    bytes_arg=bytes_arg,
                    old=old,
                    new=new,
                    count=count,
                    source_ref=source_ref,
                )
            else:
                return ExpressionBytesOperationReplace3(
                    bytes_arg=bytes_arg, old=old, new=new, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationReplace,
            builtin_spec=bytes_replace_spec,
        )

        return result, "new_expression", "Call to 'replace' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesReplace)


class ExpressionAttributeLookupFixedReverse(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'reverse' of an object.

    Typically code like: source.reverse
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_REVERSE"
    attribute_name = "reverse"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeListExact():
            result = ExpressionAttributeLookupListReverse(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'reverse' on list shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="reverse",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="reverse"
        )

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["reverse"] = ExpressionAttributeLookupFixedReverse


class ExpressionAttributeLookupListReverse(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedReverse
):
    """Attribute reverse lookup on a list value.

    Typically code like: some_list.reverse
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_LIST_REVERSE"
    attribute_name = "reverse"

    def computeExpression(self, trace_collection):
        # Might be used to modify the list.
        trace_collection.removeKnowledge(self.subnode_expression)

        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, list_arg, trace_collection):
        def wrapExpressionListOperationReverse(source_ref):
            return ExpressionListOperationReverse(
                list_arg=list_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionListOperationReverse,
            builtin_spec=list_reverse_spec,
        )

        return result, "new_expression", "Call to 'reverse' of list recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        list_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, list_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupListReverse)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'rfind' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesRfind(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'rfind' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrRfind(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedRfind
):
    """Attribute 'rfind' lookup on a str value.

    Typically code like: some_str.rfind
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_RFIND"
    attribute_name = "rfind"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationRfind(sub, start, end, source_ref):
            if end is not None:
                return ExpressionStrOperationRfind4(
                    str_arg=str_arg,
                    sub=sub,
                    start=start,
                    end=end,
                    source_ref=source_ref,
                )
            elif start is not None:
                return ExpressionStrOperationRfind3(
                    str_arg=str_arg, sub=sub, start=start, source_ref=source_ref
                )
            else:
                return ExpressionStrOperationRfind2(
                    str_arg=str_arg, sub=sub, source_ref=source_ref
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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrRfind)


class ExpressionAttributeLookupBytesRfind(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedRfind
):
    """Attribute 'rfind' lookup on a bytes value.

    Typically code like: some_bytes.rfind
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_RFIND"
    attribute_name = "rfind"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationRfind(sub, start, end, source_ref):
            if end is not None:
                return ExpressionBytesOperationRfind4(
                    bytes_arg=bytes_arg,
                    sub=sub,
                    start=start,
                    end=end,
                    source_ref=source_ref,
                )
            elif start is not None:
                return ExpressionBytesOperationRfind3(
                    bytes_arg=bytes_arg, sub=sub, start=start, source_ref=source_ref
                )
            else:
                return ExpressionBytesOperationRfind2(
                    bytes_arg=bytes_arg, sub=sub, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationRfind,
            builtin_spec=bytes_rfind_spec,
        )

        return result, "new_expression", "Call to 'rfind' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesRfind)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'rindex' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesRindex(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'rindex' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrRindex(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedRindex
):
    """Attribute 'rindex' lookup on a str value.

    Typically code like: some_str.rindex
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_RINDEX"
    attribute_name = "rindex"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationRindex(sub, start, end, source_ref):
            if end is not None:
                return ExpressionStrOperationRindex4(
                    str_arg=str_arg,
                    sub=sub,
                    start=start,
                    end=end,
                    source_ref=source_ref,
                )
            elif start is not None:
                return ExpressionStrOperationRindex3(
                    str_arg=str_arg, sub=sub, start=start, source_ref=source_ref
                )
            else:
                return ExpressionStrOperationRindex2(
                    str_arg=str_arg, sub=sub, source_ref=source_ref
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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrRindex)


class ExpressionAttributeLookupBytesRindex(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedRindex
):
    """Attribute 'rindex' lookup on a bytes value.

    Typically code like: some_bytes.rindex
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_RINDEX"
    attribute_name = "rindex"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationRindex(sub, start, end, source_ref):
            if end is not None:
                return ExpressionBytesOperationRindex4(
                    bytes_arg=bytes_arg,
                    sub=sub,
                    start=start,
                    end=end,
                    source_ref=source_ref,
                )
            elif start is not None:
                return ExpressionBytesOperationRindex3(
                    bytes_arg=bytes_arg, sub=sub, start=start, source_ref=source_ref
                )
            else:
                return ExpressionBytesOperationRindex2(
                    bytes_arg=bytes_arg, sub=sub, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationRindex,
            builtin_spec=bytes_rindex_spec,
        )

        return result, "new_expression", "Call to 'rindex' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesRindex)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'rjust' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesRjust(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'rjust' on bytes shape resolved.",
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
    """Attribute 'rjust' lookup on a str value.

    Typically code like: some_str.rjust
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_RJUST"
    attribute_name = "rjust"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationRjust(width, fillchar, source_ref):
            if fillchar is not None:
                return ExpressionStrOperationRjust3(
                    str_arg=str_arg,
                    width=width,
                    fillchar=fillchar,
                    source_ref=source_ref,
                )
            else:
                return ExpressionStrOperationRjust2(
                    str_arg=str_arg, width=width, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationRjust,
            builtin_spec=str_rjust_spec,
        )

        return result, "new_expression", "Call to 'rjust' of str recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrRjust)


class ExpressionAttributeLookupBytesRjust(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedRjust
):
    """Attribute 'rjust' lookup on a bytes value.

    Typically code like: some_bytes.rjust
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_RJUST"
    attribute_name = "rjust"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationRjust(width, fillchar, source_ref):
            if fillchar is not None:
                return ExpressionBytesOperationRjust3(
                    bytes_arg=bytes_arg,
                    width=width,
                    fillchar=fillchar,
                    source_ref=source_ref,
                )
            else:
                return ExpressionBytesOperationRjust2(
                    bytes_arg=bytes_arg, width=width, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationRjust,
            builtin_spec=bytes_rjust_spec,
        )

        return result, "new_expression", "Call to 'rjust' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesRjust)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'rpartition' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesRpartition(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'rpartition' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrRpartition(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedRpartition
):
    """Attribute 'rpartition' lookup on a str value.

    Typically code like: some_str.rpartition
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_RPARTITION"
    attribute_name = "rpartition"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationRpartition(sep, source_ref):
            return ExpressionStrOperationRpartition(
                str_arg=str_arg, sep=sep, source_ref=source_ref
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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrRpartition)


class ExpressionAttributeLookupBytesRpartition(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedRpartition
):
    """Attribute 'rpartition' lookup on a bytes value.

    Typically code like: some_bytes.rpartition
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_RPARTITION"
    attribute_name = "rpartition"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationRpartition(sep, source_ref):
            return ExpressionBytesOperationRpartition(
                bytes_arg=bytes_arg, sep=sep, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationRpartition,
            builtin_spec=bytes_rpartition_spec,
        )

        return result, "new_expression", "Call to 'rpartition' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesRpartition)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'rsplit' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesRsplit(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'rsplit' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrRsplit(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedRsplit
):
    """Attribute 'rsplit' lookup on a str value.

    Typically code like: some_str.rsplit
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_RSPLIT"
    attribute_name = "rsplit"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationRsplit(sep, maxsplit, source_ref):
            if maxsplit is not None:
                return makeExpressionStrOperationRsplit3(
                    str_arg=str_arg, sep=sep, maxsplit=maxsplit, source_ref=source_ref
                )
            elif sep is not None:
                return ExpressionStrOperationRsplit2(
                    str_arg=str_arg, sep=sep, source_ref=source_ref
                )
            else:
                return ExpressionStrOperationRsplit1(
                    str_arg=str_arg, source_ref=source_ref
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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrRsplit)


class ExpressionAttributeLookupBytesRsplit(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedRsplit
):
    """Attribute 'rsplit' lookup on a bytes value.

    Typically code like: some_bytes.rsplit
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_RSPLIT"
    attribute_name = "rsplit"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationRsplit(sep, maxsplit, source_ref):
            if maxsplit is not None:
                return makeExpressionBytesOperationRsplit3(
                    bytes_arg=bytes_arg,
                    sep=sep,
                    maxsplit=maxsplit,
                    source_ref=source_ref,
                )
            elif sep is not None:
                return ExpressionBytesOperationRsplit2(
                    bytes_arg=bytes_arg, sep=sep, source_ref=source_ref
                )
            else:
                return ExpressionBytesOperationRsplit1(
                    bytes_arg=bytes_arg, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationRsplit,
            builtin_spec=bytes_rsplit_spec,
        )

        return result, "new_expression", "Call to 'rsplit' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesRsplit)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'rstrip' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesRstrip(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'rstrip' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrRstrip(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedRstrip
):
    """Attribute 'rstrip' lookup on a str value.

    Typically code like: some_str.rstrip
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_RSTRIP"
    attribute_name = "rstrip"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationRstrip(chars, source_ref):
            if chars is not None:
                return ExpressionStrOperationRstrip2(
                    str_arg=str_arg, chars=chars, source_ref=source_ref
                )
            else:
                return ExpressionStrOperationRstrip1(
                    str_arg=str_arg, source_ref=source_ref
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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrRstrip)


class ExpressionAttributeLookupBytesRstrip(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedRstrip
):
    """Attribute 'rstrip' lookup on a bytes value.

    Typically code like: some_bytes.rstrip
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_RSTRIP"
    attribute_name = "rstrip"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationRstrip(chars, source_ref):
            if chars is not None:
                return ExpressionBytesOperationRstrip2(
                    bytes_arg=bytes_arg, chars=chars, source_ref=source_ref
                )
            else:
                return ExpressionBytesOperationRstrip1(
                    bytes_arg=bytes_arg, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationRstrip,
            builtin_spec=bytes_rstrip_spec,
        )

        return result, "new_expression", "Call to 'rstrip' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesRstrip)


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

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["setdefault"] = ExpressionAttributeLookupFixedSetdefault


class ExpressionAttributeLookupDictSetdefault(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedSetdefault
):
    """Attribute 'setdefault' lookup on a dict value.

    Typically code like: some_dict.setdefault
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_SETDEFAULT"
    attribute_name = "setdefault"

    # There is nothing to compute for it as a value.
    # TODO: Enable this once we can also say removal of knowable for an argument.
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        # Might be used to modify the dict.
        trace_collection.removeKnowledge(self.subnode_expression)

        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, dict_arg, trace_collection):
        def wrapExpressionDictOperationSetdefault(key, default, source_ref):
            if default is not None:
                return ExpressionDictOperationSetdefault3(
                    dict_arg=dict_arg, key=key, default=default, source_ref=source_ref
                )
            else:
                return ExpressionDictOperationSetdefault2(
                    dict_arg=dict_arg, key=key, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        dict_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, dict_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupDictSetdefault)


class ExpressionAttributeLookupFixedSort(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value 'sort' of an object.

    Typically code like: source.sort
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_SORT"
    attribute_name = "sort"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeListExact():
            result = ExpressionAttributeLookupListSort(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'sort' on list shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="sort",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="sort"
        )

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["sort"] = ExpressionAttributeLookupFixedSort


class ExpressionAttributeLookupListSort(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedSort
):
    """Attribute sort lookup on a list value.

    Typically code like: some_list.sort
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_LIST_SORT"
    attribute_name = "sort"

    def computeExpression(self, trace_collection):
        # Might be used to modify the list.
        trace_collection.removeKnowledge(self.subnode_expression)

        return self, None, None

    # No computeExpressionCall as list operation ExpressionListOperationSort is not yet implemented


attribute_typed_classes.add(ExpressionAttributeLookupListSort)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'split' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesSplit(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'split' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrSplit(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedSplit
):
    """Attribute 'split' lookup on a str value.

    Typically code like: some_str.split
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_SPLIT"
    attribute_name = "split"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationSplit(sep, maxsplit, source_ref):
            if maxsplit is not None:
                return makeExpressionStrOperationSplit3(
                    str_arg=str_arg, sep=sep, maxsplit=maxsplit, source_ref=source_ref
                )
            elif sep is not None:
                return ExpressionStrOperationSplit2(
                    str_arg=str_arg, sep=sep, source_ref=source_ref
                )
            else:
                return ExpressionStrOperationSplit1(
                    str_arg=str_arg, source_ref=source_ref
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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrSplit)


class ExpressionAttributeLookupBytesSplit(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedSplit
):
    """Attribute 'split' lookup on a bytes value.

    Typically code like: some_bytes.split
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_SPLIT"
    attribute_name = "split"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationSplit(sep, maxsplit, source_ref):
            if maxsplit is not None:
                return makeExpressionBytesOperationSplit3(
                    bytes_arg=bytes_arg,
                    sep=sep,
                    maxsplit=maxsplit,
                    source_ref=source_ref,
                )
            elif sep is not None:
                return ExpressionBytesOperationSplit2(
                    bytes_arg=bytes_arg, sep=sep, source_ref=source_ref
                )
            else:
                return ExpressionBytesOperationSplit1(
                    bytes_arg=bytes_arg, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationSplit,
            builtin_spec=bytes_split_spec,
        )

        return result, "new_expression", "Call to 'split' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesSplit)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'splitlines' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesSplitlines(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'splitlines' on bytes shape resolved.",
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
    """Attribute 'splitlines' lookup on a str value.

    Typically code like: some_str.splitlines
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_SPLITLINES"
    attribute_name = "splitlines"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationSplitlines(keepends, source_ref):
            if keepends is not None:
                return ExpressionStrOperationSplitlines2(
                    str_arg=str_arg, keepends=keepends, source_ref=source_ref
                )
            else:
                return ExpressionStrOperationSplitlines1(
                    str_arg=str_arg, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationSplitlines,
            builtin_spec=str_splitlines_spec,
        )

        return result, "new_expression", "Call to 'splitlines' of str recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrSplitlines)


class ExpressionAttributeLookupBytesSplitlines(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedSplitlines
):
    """Attribute 'splitlines' lookup on a bytes value.

    Typically code like: some_bytes.splitlines
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_SPLITLINES"
    attribute_name = "splitlines"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationSplitlines(keepends, source_ref):
            if keepends is not None:
                return ExpressionBytesOperationSplitlines2(
                    bytes_arg=bytes_arg, keepends=keepends, source_ref=source_ref
                )
            else:
                return ExpressionBytesOperationSplitlines1(
                    bytes_arg=bytes_arg, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationSplitlines,
            builtin_spec=bytes_splitlines_spec,
        )

        return result, "new_expression", "Call to 'splitlines' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesSplitlines)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'startswith' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesStartswith(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'startswith' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrStartswith(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedStartswith
):
    """Attribute 'startswith' lookup on a str value.

    Typically code like: some_str.startswith
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_STARTSWITH"
    attribute_name = "startswith"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationStartswith(prefix, start, end, source_ref):
            if end is not None:
                return ExpressionStrOperationStartswith4(
                    str_arg=str_arg,
                    prefix=prefix,
                    start=start,
                    end=end,
                    source_ref=source_ref,
                )
            elif start is not None:
                return ExpressionStrOperationStartswith3(
                    str_arg=str_arg, prefix=prefix, start=start, source_ref=source_ref
                )
            else:
                return ExpressionStrOperationStartswith2(
                    str_arg=str_arg, prefix=prefix, source_ref=source_ref
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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrStartswith)


class ExpressionAttributeLookupBytesStartswith(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedStartswith
):
    """Attribute 'startswith' lookup on a bytes value.

    Typically code like: some_bytes.startswith
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_STARTSWITH"
    attribute_name = "startswith"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationStartswith(prefix, start, end, source_ref):
            if end is not None:
                return ExpressionBytesOperationStartswith4(
                    bytes_arg=bytes_arg,
                    prefix=prefix,
                    start=start,
                    end=end,
                    source_ref=source_ref,
                )
            elif start is not None:
                return ExpressionBytesOperationStartswith3(
                    bytes_arg=bytes_arg,
                    prefix=prefix,
                    start=start,
                    source_ref=source_ref,
                )
            else:
                return ExpressionBytesOperationStartswith2(
                    bytes_arg=bytes_arg, prefix=prefix, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationStartswith,
            builtin_spec=bytes_startswith_spec,
        )

        return result, "new_expression", "Call to 'startswith' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesStartswith)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'strip' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesStrip(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'strip' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrStrip(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedStrip
):
    """Attribute 'strip' lookup on a str value.

    Typically code like: some_str.strip
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_STRIP"
    attribute_name = "strip"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationStrip(chars, source_ref):
            if chars is not None:
                return ExpressionStrOperationStrip2(
                    str_arg=str_arg, chars=chars, source_ref=source_ref
                )
            else:
                return ExpressionStrOperationStrip1(
                    str_arg=str_arg, source_ref=source_ref
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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrStrip)


class ExpressionAttributeLookupBytesStrip(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedStrip
):
    """Attribute 'strip' lookup on a bytes value.

    Typically code like: some_bytes.strip
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_STRIP"
    attribute_name = "strip"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationStrip(chars, source_ref):
            if chars is not None:
                return ExpressionBytesOperationStrip2(
                    bytes_arg=bytes_arg, chars=chars, source_ref=source_ref
                )
            else:
                return ExpressionBytesOperationStrip1(
                    bytes_arg=bytes_arg, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationStrip,
            builtin_spec=bytes_strip_spec,
        )

        return result, "new_expression", "Call to 'strip' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesStrip)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'swapcase' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesSwapcase(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'swapcase' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrSwapcase(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedSwapcase
):
    """Attribute 'swapcase' lookup on a str value.

    Typically code like: some_str.swapcase
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_SWAPCASE"
    attribute_name = "swapcase"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationSwapcase(source_ref):
            return ExpressionStrOperationSwapcase(
                str_arg=str_arg, source_ref=source_ref
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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrSwapcase)


class ExpressionAttributeLookupBytesSwapcase(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedSwapcase
):
    """Attribute 'swapcase' lookup on a bytes value.

    Typically code like: some_bytes.swapcase
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_SWAPCASE"
    attribute_name = "swapcase"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationSwapcase(source_ref):
            return ExpressionBytesOperationSwapcase(
                bytes_arg=bytes_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationSwapcase,
            builtin_spec=bytes_swapcase_spec,
        )

        return result, "new_expression", "Call to 'swapcase' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesSwapcase)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'title' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesTitle(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'title' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrTitle(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedTitle
):
    """Attribute 'title' lookup on a str value.

    Typically code like: some_str.title
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_TITLE"
    attribute_name = "title"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationTitle(source_ref):
            return ExpressionStrOperationTitle(str_arg=str_arg, source_ref=source_ref)

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationTitle,
            builtin_spec=str_title_spec,
        )

        return result, "new_expression", "Call to 'title' of str recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrTitle)


class ExpressionAttributeLookupBytesTitle(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedTitle
):
    """Attribute 'title' lookup on a bytes value.

    Typically code like: some_bytes.title
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_TITLE"
    attribute_name = "title"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationTitle(source_ref):
            return ExpressionBytesOperationTitle(
                bytes_arg=bytes_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationTitle,
            builtin_spec=bytes_title_spec,
        )

        return result, "new_expression", "Call to 'title' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesTitle)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'translate' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesTranslate(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'translate' on bytes shape resolved.",
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
    """Attribute 'translate' lookup on a str value.

    Typically code like: some_str.translate
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_TRANSLATE"
    attribute_name = "translate"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationTranslate(table, source_ref):
            return ExpressionStrOperationTranslate(
                str_arg=str_arg, table=table, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationTranslate,
            builtin_spec=str_translate_spec,
        )

        return result, "new_expression", "Call to 'translate' of str recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrTranslate)


class ExpressionAttributeLookupBytesTranslate(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedTranslate
):
    """Attribute 'translate' lookup on a bytes value.

    Typically code like: some_bytes.translate
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_TRANSLATE"
    attribute_name = "translate"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationTranslate(table, delete, source_ref):
            if delete is not None:
                return ExpressionBytesOperationTranslate3(
                    bytes_arg=bytes_arg,
                    table=table,
                    delete=delete,
                    source_ref=source_ref,
                )
            else:
                return ExpressionBytesOperationTranslate2(
                    bytes_arg=bytes_arg, table=table, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationTranslate,
            builtin_spec=bytes_translate_spec,
        )

        return result, "new_expression", "Call to 'translate' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesTranslate)


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

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["update"] = ExpressionAttributeLookupFixedUpdate


class ExpressionAttributeLookupDictUpdate(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedUpdate
):
    """Attribute 'update' lookup on a dict value.

    Typically code like: some_dict.update
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_UPDATE"
    attribute_name = "update"

    # There is nothing to compute for it as a value.
    # TODO: Enable this once we can also say removal of knowable for an argument.
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        # Might be used to modify the dict.
        trace_collection.removeKnowledge(self.subnode_expression)

        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, dict_arg, trace_collection):
        def wrapExpressionDictOperationUpdate(iterable, pairs, source_ref):
            if pairs:
                return makeExpressionDictOperationUpdate3(
                    dict_arg=dict_arg,
                    iterable=iterable,
                    pairs=makeKeyValuePairExpressionsFromKwArgs(pairs),
                    source_ref=source_ref,
                )
            else:
                return ExpressionDictOperationUpdate2(
                    dict_arg=dict_arg, iterable=iterable, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationUpdate,
            builtin_spec=dict_update_spec,
            empty_special_class=lambda source_ref: wrapExpressionWithNodeSideEffects(
                new_node=makeConstantRefNode(constant=None, source_ref=source_ref),
                old_node=dict_arg,
            ),
        )

        return trace_collection.computedExpressionResult(
            expression=result,
            change_tags="new_expression",
            change_desc="Call to 'update' of dictionary recognized.",
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        dict_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, dict_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'upper' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesUpper(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'upper' on bytes shape resolved.",
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


class ExpressionAttributeLookupStrUpper(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedUpper
):
    """Attribute 'upper' lookup on a str value.

    Typically code like: some_str.upper
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_UPPER"
    attribute_name = "upper"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationUpper(source_ref):
            return ExpressionStrOperationUpper(str_arg=str_arg, source_ref=source_ref)

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationUpper,
            builtin_spec=str_upper_spec,
        )

        return result, "new_expression", "Call to 'upper' of str recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrUpper)


class ExpressionAttributeLookupBytesUpper(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedUpper
):
    """Attribute 'upper' lookup on a bytes value.

    Typically code like: some_bytes.upper
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_UPPER"
    attribute_name = "upper"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationUpper(source_ref):
            return ExpressionBytesOperationUpper(
                bytes_arg=bytes_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationUpper,
            builtin_spec=bytes_upper_spec,
        )

        return result, "new_expression", "Call to 'upper' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesUpper)


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

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["values"] = ExpressionAttributeLookupFixedValues


class ExpressionAttributeLookupDictValues(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedValues
):
    """Attribute 'values' lookup on a dict value.

    Typically code like: some_dict.values
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_VALUES"
    attribute_name = "values"

    # There is nothing to compute for it as a value.
    # TODO: Enable this once we can also say removal of knowable for an argument.
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        # Cannot be used to modify the dict.
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, dict_arg, trace_collection):
        def wrapExpressionDictOperationValues(source_ref):
            if str is bytes:
                return ExpressionDictOperationValues(
                    dict_arg=dict_arg, source_ref=source_ref
                )
            else:
                return ExpressionDictOperationItervalues(
                    dict_arg=dict_arg, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        dict_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, dict_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


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

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["viewitems"] = ExpressionAttributeLookupFixedViewitems


class ExpressionAttributeLookupDictViewitems(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedViewitems
):
    """Attribute 'viewitems' lookup on a dict value.

    Typically code like: some_dict.viewitems
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_VIEWITEMS"
    attribute_name = "viewitems"

    # There is nothing to compute for it as a value.
    # TODO: Enable this once we can also say removal of knowable for an argument.
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        # Cannot be used to modify the dict.
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, dict_arg, trace_collection):
        def wrapExpressionDictOperationViewitems(source_ref):
            return ExpressionDictOperationViewitems(
                dict_arg=dict_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        dict_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, dict_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


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

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["viewkeys"] = ExpressionAttributeLookupFixedViewkeys


class ExpressionAttributeLookupDictViewkeys(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedViewkeys
):
    """Attribute 'viewkeys' lookup on a dict value.

    Typically code like: some_dict.viewkeys
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_VIEWKEYS"
    attribute_name = "viewkeys"

    # There is nothing to compute for it as a value.
    # TODO: Enable this once we can also say removal of knowable for an argument.
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        # Cannot be used to modify the dict.
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, dict_arg, trace_collection):
        def wrapExpressionDictOperationViewkeys(source_ref):
            return ExpressionDictOperationViewkeys(
                dict_arg=dict_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        dict_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, dict_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


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

    def onContentEscapes(self, trace_collection):
        self.subnode_expression.onContentEscapes(trace_collection)


attribute_classes["viewvalues"] = ExpressionAttributeLookupFixedViewvalues


class ExpressionAttributeLookupDictViewvalues(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedViewvalues
):
    """Attribute 'viewvalues' lookup on a dict value.

    Typically code like: some_dict.viewvalues
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_VIEWVALUES"
    attribute_name = "viewvalues"

    # There is nothing to compute for it as a value.
    # TODO: Enable this once we can also say removal of knowable for an argument.
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        # Cannot be used to modify the dict.
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, dict_arg, trace_collection):
        def wrapExpressionDictOperationViewvalues(source_ref):
            return ExpressionDictOperationViewvalues(
                dict_arg=dict_arg, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Make sure we wait with knowing if the content is safe to use until its time.
        call_node.onContentEscapes(trace_collection)

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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        dict_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, dict_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


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

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'zfill' on str shape resolved.",
            )
        if str is not bytes and subnode_expression.hasShapeBytesExact():
            result = ExpressionAttributeLookupBytesZfill(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return trace_collection.computedExpressionResult(
                expression=result,
                change_tags="new_expression",
                change_desc="Attribute lookup 'zfill' on bytes shape resolved.",
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
    """Attribute 'zfill' lookup on a str value.

    Typically code like: some_str.zfill
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_STR_ZFILL"
    attribute_name = "zfill"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, str_arg, trace_collection):
        def wrapExpressionStrOperationZfill(width, source_ref):
            return ExpressionStrOperationZfill(
                str_arg=str_arg, width=width, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionStrOperationZfill,
            builtin_spec=str_zfill_spec,
        )

        return result, "new_expression", "Call to 'zfill' of str recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        str_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, str_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupStrZfill)


class ExpressionAttributeLookupBytesZfill(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedZfill
):
    """Attribute 'zfill' lookup on a bytes value.

    Typically code like: some_bytes.zfill
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_BYTES_ZFILL"
    attribute_name = "zfill"

    # There is nothing to compute for it as a value.
    # TODO: Enable this
    # auto_compute_handling = "final,no_raise"

    def computeExpression(self, trace_collection):
        return self, None, None

    @staticmethod
    def _computeExpressionCall(call_node, bytes_arg, trace_collection):
        def wrapExpressionBytesOperationZfill(width, source_ref):
            return ExpressionBytesOperationZfill(
                bytes_arg=bytes_arg, width=width, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionBytesOperationZfill,
            builtin_spec=bytes_zfill_spec,
        )

        return result, "new_expression", "Call to 'zfill' of bytes recognized."

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        return self._computeExpressionCall(
            call_node, self.subnode_expression, trace_collection
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        bytes_node = makeExpressionAttributeLookup(
            expression=variable_ref_node,
            attribute_name="__self__",
            # TODO: Would be nice to have the real source reference here, but it feels
            # a bit expensive.
            source_ref=variable_ref_node.source_ref,
        )

        return self._computeExpressionCall(call_node, bytes_node, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)


attribute_typed_classes.add(ExpressionAttributeLookupBytesZfill)
