#     Copyright 2022, Cjw, mailto:cjw@ŧhedeadfly.com
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
""" Nodes that build and operate on lists."""


from abc import abstractmethod

from .ConstantRefNodes import makeConstantRefNode
from .ExpressionBases import (
    ExpressionChildHavingBase,
    ExpressionChildrenHavingBase,
)
from .ExpressionShapeMixins import (
    ExpressionBoolShapeExactMixin,
    ExpressionBytesShapeExactMixin,
    ExpressionIntShapeExactMixin,
    ExpressionListShapeExactMixin,
    ExpressionStrOrUnicodeExactMixin,
    ExpressionStrShapeExactMixin,
    ExpressionTupleShapeExactMixin,
)
from .NodeBases import SideEffectsFromChildrenMixin
from .NodeMetaClasses import NodeCheckMetaClass


class ExpressionListOperationAppend(
    ExpressionListShapeExactMixin, ExpressionChildHavingBase
):
    """This operation represents l.append(object)."""

    kind = "EXPRESSION_LIST_OPERATION_APPEND"

    name_children = ('list_arg', 'item')

    def __init__(self, list_arg, item, source_ref):
        assert list_arg is not None
        assert item is not None

        ExpressionChildHavingBase.__init__(
            self,
            value={'list_arg': list_arg, 'item': item},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        list_arg = self.subnode_list_arg
        item = self.subnode_item

        # the state of the object changes
        trace_collection.removeKnowledge(list_arg)

        # exposing the variable content
        item.onContentEscapes(trace_collection)

        return self, None, None


class ExpressionListOperationClear(
    ExpressionListShapeExactMixin, ExpressionChildHavingBase
):
    """This operation represents l.clear()."""

    kind = "EXPRESSION_LIST_OPERATION_CLEAR"

    name_children = ('list_arg',)

    def __init__(self, list_arg, source_ref):
        assert list_arg is not None

        ExpressionChildHavingBase.__init__(
            self,
            value=list_arg,
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        list_arg = self.subnode_list_arg

        # only the state of object changes
        trace_collection.removeKnowledge(list_arg)

        return self, None, None


class ExpressionListOperationCopy(
    SideEffectsFromChildrenMixin, ExpressionChildHavingBase
):
    """This operation represents l.copy()."""

    kind = "EXPRESSION_LIST_OPERATION_COPY"

    name_children = ('list_arg',)

    def __init__(self, list_arg, source_ref):
        assert list_arg is not None

        ExpressionChildHavingBase.__init__(
            self,
            value=list_arg,
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        list_arg = self.subnode_list_arg

        list_arg.onContentEscapes(trace_collection)
        return self, None, None


class ExpressionListOperationExtend(
    ExpressionListShapeExactMixin, ExpressionChildHavingBase
):
    """This operation represents l.extend(iterable)."""

    kind = "EXPRESSION_LIST_OPERATION_EXTEND"
    name_children = ('list_arg', 'value')

    def __init__(self, list_arg, value, source_ref):
        assert list_arg is not None
        assert value is not None

        ExpressionChildHavingBase.__init__(
            self,
            value={'list_arg': list_arg, 'value': value},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        list_arg = self.subnode_list_arg
        value = self.subnode_value

        # the content of the list changes
        trace_collection.removeKnowledge(list_arg)

        # expose the input value
        value.onContentEscapes(trace_collection)

        # if the argument is no iterable
        trace_collection.onExceptionRaiseExit(BaseException)
        return self, None, None


class ExpressionListOperationIndex(
    ExpressionListShapeExactMixin, ExpressionChildHavingBase
):
    """This operation represents l.index(value, start, stop)."""

    kind = "EXPRESSION_LIST_OPERATION_INDEX"
    name_children = ('list_arg', 'value', 'start', 'stop')

    def __init__(self, list_arg, value, start, stop, source_ref):
        assert list_arg is not None
        assert value is not None
        # start and stop can be omitted

        ExpressionChildHavingBase.__init__(
            self,
            value={'list_arg': list_arg, 'value': value, 'start': start, 'stop': stop},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        list_arg = self.subnode_list_arg
        value = self.subnode_value

        value.onContentEscapes(trace_collection)

        # raises ValueError when the value is not found
        trace_collection.onExceptionRaiseExit(BaseException)
        return self, None, None


class ExpressionListOperationInsert(
    ExpressionListShapeExactMixin, ExpressionChildHavingBase
):
    """This operation represents l.insert(index, item)."""

    kind = "EXPRESSION_LIST_OPERATION_INSERT"
    name_children = ('list_arg', 'index', 'item')

    def __init__(self, list_arg, index, item, source_ref):
        assert list_arg is not None
        assert index is not None
        assert item is not None

        ExpressionChildHavingBase.__init__(
            self,
            value={'list_arg': list_arg, 'index': index, 'item': item},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        list_arg = self.subnode_list_arg
        item = self.subnode_item

        # expose the item
        item.onContentEscapes(trace_collection)
        trace_collection.removeKnowledge(list_arg)
        # it raises no index error

        return self, None, None


class ExpressionListOperationPop(
    ExpressionListShapeExactMixin, ExpressionChildHavingBase
):
    """This operation represents l.pop(index)."""

    kind = "EXPRESSION_LIST_OPERATION_POP"
    name_children = ('list_arg', 'index')

    def __init__(self, list_arg, index, source_ref):
        assert list_arg is not None
        # index can be omitted

        ExpressionChildHavingBase.__init__(
            self,
            value={'list_arg': list_arg, 'index': index},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        list_arg = self.subnode_list_arg

        trace_collection.removeKnowledge(list_arg)

        # raises index error
        trace_collection.onExceptionRaiseExit(BaseException)
        return self, None, None


class ExpressionListOperationRemove(
    ExpressionListShapeExactMixin, ExpressionChildHavingBase
):
    """This operation represents l.remove(value)."""

    kind = "EXPRESSION_LIST_OPERATION_REMOVE"
    name_children = ('list_arg', 'value')

    def __init__(self, list_arg, value, source_ref):
        assert list_arg is not None
        assert value is not None

        ExpressionChildHavingBase.__init__(
            self,
            value={'list_arg': list_arg, 'value': value},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        list_arg = self.subnode_list_arg
        value = self.subnode_value

        # TODO: do i need to call onContentEscapes?
        trace_collection.removeKnowledge(list_arg)

        # raises ValuerError if the value is not found
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionListOperationReverse(
    ExpressionListShapeExactMixin, ExpressionChildHavingBase
):
    """This operation represents l.reverse()."""

    kind = "EXPRESSION_LIST_OPERATION_REVERSE"

    name_children = ('list_arg',)

    def __init__(self, list_arg, source_ref):
        assert list_arg is not None

        ExpressionChildHavingBase.__init__(
            self,
            value=list_arg,
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        list_arg = self.subnode_list_arg

        trace_collection.removeKnowledge(list_arg)
        return self, None, None


class ExpressionListOperationSort(
    ExpressionListShapeExactMixin, ExpressionChildHavingBase
):
    """This operation represents l.sort()."""

    kind = "EXPRESSION_LIST_OPERATION_SORT"

    name_children = ('list_arg',)

    def __init__(self, list_arg, source_ref):
        assert list_arg is not None

        ExpressionChildHavingBase.__init__(
            self,
            value=list_arg,
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        list_arg = self.subnode_list_arg

        trace_collection.removeKnowledge(list_arg)
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None
