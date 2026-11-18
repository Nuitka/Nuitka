#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Nodes that build and operate on lists."""

from .ChildrenHavingMixins import (
    ChildHavingListArgMixin,
    ChildrenExpressionListOperationExtendMixin,
    ChildrenHavingListArgIndexItemMixin,
    ChildrenHavingListArgIndexMixin,
    ChildrenHavingListArgKeyMixin,
    ChildrenHavingListArgKeyOptionalReverseMixin,
    ChildrenHavingListArgValueMixin,
    ChildrenHavingListArgValueStartMixin,
    ChildrenHavingListArgValueStartStopMixin,
)
from .ExpressionBases import ExpressionBase
from .ExpressionBasesGenerated import (
    ExpressionListOperationAppendBase,
    ExpressionListOperationClearBase,
    ExpressionListOperationCountBase,
    ExpressionListOperationReverseBase,
)
from .ExpressionShapeMixins import ExpressionIntOrLongExactMixin
from .NodeBases import SideEffectsFromChildrenMixin


class ExpressionListOperationAppend(ExpressionListOperationAppendBase):
    kind = "EXPRESSION_LIST_OPERATION_APPEND"

    named_children = ("list_arg", "item")
    auto_compute_handling = "no_raise"

    def computeExpression(self, trace_collection):
        # TODO: Until we have proper list tracing.
        trace_collection.removeKnowledge(self.subnode_list_arg)
        self.subnode_item.onContentEscapes(trace_collection)

        # MemoryError is ignored for list allocations.
        return self, None, None


class ExpressionListOperationClear(ExpressionListOperationClearBase):
    kind = "EXPRESSION_LIST_OPERATION_CLEAR"

    named_children = ("list_arg",)
    auto_compute_handling = "no_raise"

    def computeExpression(self, trace_collection):
        # TODO: Until we have proper list tracing.
        trace_collection.removeKnowledge(self.subnode_list_arg)

        return self, None, None


class ExpressionListOperationCopy(
    SideEffectsFromChildrenMixin, ChildHavingListArgMixin, ExpressionBase
):
    kind = "EXPRESSION_LIST_OPERATION_COPY"

    named_children = ("list_arg",)

    def __init__(self, list_arg, source_ref):
        ChildHavingListArgMixin.__init__(
            self,
            list_arg=list_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        self.subnode_list_arg.onContentEscapes(trace_collection)

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_list_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @staticmethod
    def mayRaiseExceptionOperation():
        # Code generation ignores MemoryError here.
        return False


# TODO: The generator doesn't handle int or long yet.
class ExpressionListOperationCount(
    SideEffectsFromChildrenMixin,
    ExpressionIntOrLongExactMixin,
    ExpressionListOperationCountBase,
):
    kind = "EXPRESSION_LIST_OPERATION_COUNT"

    named_children = (
        "list_arg",
        "value",
    )

    auto_compute_handling = "final,no_raise"

    # TODO: With list tracing, the size of the list should be a worthwhile first goal.
    # TODO: Is not no_raise

    def computeExpression(self, trace_collection):
        return self, None, None


class ExpressionListOperationExtend(
    ChildrenExpressionListOperationExtendMixin, ExpressionBase
):
    kind = "EXPRESSION_LIST_OPERATION_EXTEND"

    named_children = ("list_arg", "value")

    def __init__(self, list_arg, value, source_ref):
        ChildrenExpressionListOperationExtendMixin.__init__(
            self,
            list_arg=list_arg,
            value=value,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        # TODO: Until we have proper list tracing.
        trace_collection.removeKnowledge(self.subnode_list_arg)
        self.subnode_value.onContentEscapes(trace_collection)
        trace_collection.onControlFlowEscape(self)
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionListOperationExtendForUnpack(ExpressionListOperationExtend):
    kind = "EXPRESSION_LIST_OPERATION_EXTEND_FOR_UNPACK"


# TODO: The generator doesn't handle int or long yet.
class ExpressionListOperationIndex2(
    ExpressionIntOrLongExactMixin, ChildrenHavingListArgValueMixin, ExpressionBase
):
    kind = "EXPRESSION_LIST_OPERATION_INDEX2"
    named_children = ("list_arg", "value")

    def __init__(self, list_arg, value, source_ref):
        ChildrenHavingListArgValueMixin.__init__(self, list_arg=list_arg, value=value)

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        self.subnode_value.onContentEscapes(trace_collection)
        trace_collection.onControlFlowEscape(self)
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Could become more predictable, but then maybe it's optimized away too.
        return True


# TODO: The generator doesn't handle int or long yet.
class ExpressionListOperationIndex3(
    ExpressionIntOrLongExactMixin, ChildrenHavingListArgValueStartMixin, ExpressionBase
):
    kind = "EXPRESSION_LIST_OPERATION_INDEX3"
    named_children = ("list_arg", "value", "start")

    def __init__(self, list_arg, value, start, source_ref):
        ChildrenHavingListArgValueStartMixin.__init__(
            self, list_arg=list_arg, value=value, start=start
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        self.subnode_value.onContentEscapes(trace_collection)
        trace_collection.onControlFlowEscape(self)
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Could become more predictable, but then maybe it's optimized away too.
        return True


# TODO: The generator doesn't handle int or long yet.
class ExpressionListOperationIndex4(
    ExpressionIntOrLongExactMixin,
    ChildrenHavingListArgValueStartStopMixin,
    ExpressionBase,
):
    kind = "EXPRESSION_LIST_OPERATION_INDEX4"
    named_children = ("list_arg", "value", "start", "stop")

    def __init__(self, list_arg, value, start, stop, source_ref):
        ChildrenHavingListArgValueStartStopMixin.__init__(
            self,
            list_arg=list_arg,
            value=value,
            start=start,
            stop=stop,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        self.subnode_value.onContentEscapes(trace_collection)
        trace_collection.onControlFlowEscape(self)
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Could become more predictable, but then maybe it's optimized away too.
        return True


class ExpressionListOperationInsert(
    ChildrenHavingListArgIndexItemMixin, ExpressionBase
):
    kind = "EXPRESSION_LIST_OPERATION_INSERT"
    named_children = ("list_arg", "index", "item")

    def __init__(self, list_arg, index, item, source_ref):
        ChildrenHavingListArgIndexItemMixin.__init__(
            self,
            list_arg=list_arg,
            index=index,
            item=item,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        # TODO: Until we have proper list tracing.
        trace_collection.removeKnowledge(self.subnode_list_arg)
        self.subnode_item.onContentEscapes(trace_collection)

        # '__index__' or integer overflow may raise, while out-of-bounds indices clamp without IndexError.
        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_list_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
            or self.subnode_index.mayRaiseException(exception_type)
            or self.subnode_item.mayRaiseException(exception_type)
        )

    def mayRaiseExceptionOperation(self):
        return not self.subnode_index.isExpressionIntegerSubscript()


class ExpressionListOperationPop1(ChildHavingListArgMixin, ExpressionBase):
    kind = "EXPRESSION_LIST_OPERATION_POP1"
    named_children = ("list_arg",)

    def __init__(self, list_arg, source_ref):
        ChildHavingListArgMixin.__init__(
            self,
            list_arg=list_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        non_empty = self.subnode_list_arg.isKnownToBeIterableAtMin(1)

        # TODO: Until we have proper list tracing.
        trace_collection.removeKnowledge(self.subnode_list_arg)

        if not non_empty:
            trace_collection.onExceptionRaiseExit(IndexError)

        return self, None, None

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionListOperationPop2(ChildrenHavingListArgIndexMixin, ExpressionBase):
    kind = "EXPRESSION_LIST_OPERATION_POP2"
    named_children = ("list_arg", "index")

    def __init__(self, list_arg, index, source_ref):
        ChildrenHavingListArgIndexMixin.__init__(
            self,
            list_arg=list_arg,
            index=index,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        # TODO: Until we have proper list tracing.
        trace_collection.removeKnowledge(self.subnode_list_arg)
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionListOperationRemove(ChildrenHavingListArgValueMixin, ExpressionBase):
    kind = "EXPRESSION_LIST_OPERATION_REMOVE"
    named_children = ("list_arg", "value")

    def __init__(self, list_arg, value, source_ref):
        ChildrenHavingListArgValueMixin.__init__(self, list_arg=list_arg, value=value)

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        # TODO: Until we have proper list tracing.
        trace_collection.removeKnowledge(self.subnode_list_arg)
        trace_collection.onControlFlowEscape(self)
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionListOperationReverse(ExpressionListOperationReverseBase):
    kind = "EXPRESSION_LIST_OPERATION_REVERSE"

    named_children = ("list_arg",)
    auto_compute_handling = "no_raise"

    def computeExpression(self, trace_collection):
        # TODO: Until we have proper list tracing.
        trace_collection.removeKnowledge(self.subnode_list_arg)

        return self, None, None


# TODO: The sort nodes are not yet used, because of Python2/Python3 differences
# and keyword only arguments for generation of list.sort calls.


class ExpressionListOperationSort1(ChildHavingListArgMixin, ExpressionBase):
    kind = "EXPRESSION_LIST_OPERATION_SORT1"

    named_children = ("list_arg",)

    def __init__(self, list_arg, source_ref):
        ChildHavingListArgMixin.__init__(
            self,
            list_arg=list_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        # TODO: Until we have proper list tracing.
        trace_collection.removeKnowledge(self.subnode_list_arg)
        trace_collection.onControlFlowEscape(self)
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionListOperationSort2(ChildrenHavingListArgKeyMixin, ExpressionBase):
    kind = "EXPRESSION_LIST_OPERATION_SORT2"

    named_children = ("list_arg", "key")

    def __init__(self, list_arg, key, source_ref):
        ChildrenHavingListArgKeyMixin.__init__(
            self,
            list_arg=list_arg,
            key=key,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        # TODO: Until we have proper list tracing.
        trace_collection.removeKnowledge(self.subnode_list_arg)
        trace_collection.onControlFlowEscape(self)
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


class ExpressionListOperationSort3(
    ChildrenHavingListArgKeyOptionalReverseMixin, ExpressionBase
):
    kind = "EXPRESSION_LIST_OPERATION_SORT3"

    named_children = ("list_arg", "key|optional", "reverse")

    def __init__(self, list_arg, key, reverse, source_ref):
        ChildrenHavingListArgKeyOptionalReverseMixin.__init__(
            self,
            list_arg=list_arg,
            key=key,
            reverse=reverse,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        # TODO: Until we have proper list tracing.
        trace_collection.removeKnowledge(self.subnode_list_arg)
        trace_collection.onControlFlowEscape(self)
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
