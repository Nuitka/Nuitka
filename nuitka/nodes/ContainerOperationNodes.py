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
""" Operations on Containers.

"""

from .ChildrenHavingMixins import ChildrenExpressionSetOperationUpdateMixin
from .ExpressionBases import ExpressionBase
from .StatementBasesGenerated import (
    StatementListOperationAppendBase,
    StatementSetOperationAddBase,
)


class StatementListOperationAppend(StatementListOperationAppendBase):
    kind = "STATEMENT_LIST_OPERATION_APPEND"

    named_children = ("list_arg", "value")
    auto_compute_handling = "operation"

    def computeStatementOperation(self, trace_collection):
        # TODO: Until we have proper list tracing.
        trace_collection.removeKnowledge(self.subnode_list_arg)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return self.subnode_list_arg.mayRaiseException(
            exception_type
        ) or self.subnode_value.mayRaiseException(exception_type)


class StatementSetOperationAdd(StatementSetOperationAddBase):
    kind = "STATEMENT_SET_OPERATION_ADD"

    named_children = ("set_arg", "value")
    auto_compute_handling = "operation"

    def computeStatementOperation(self, trace_collection):
        # TODO: Until we have proper set tracing.
        trace_collection.removeKnowledge(self.subnode_set_arg)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return self.subnode_set_arg.mayRaiseException(
            exception_type
        ) or self.subnode_value.mayRaiseException(exception_type)


class ExpressionSetOperationUpdate(
    ChildrenExpressionSetOperationUpdateMixin, ExpressionBase
):
    kind = "EXPRESSION_SET_OPERATION_UPDATE"

    named_children = ("set_arg", "value")

    def __init__(self, set_arg, value, source_ref):
        ChildrenExpressionSetOperationUpdateMixin.__init__(
            self,
            set_arg=set_arg,
            value=value,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        trace_collection.removeKnowledge(self.subnode_set_arg)

        return self, None, None
