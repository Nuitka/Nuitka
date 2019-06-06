#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.Builtins import calledWithBuiltinArgumentNamesDecorator

from .ExpressionBases import ExpressionChildrenHavingBase
from .NodeBases import StatementChildrenHavingBase


class StatementListOperationAppend(StatementChildrenHavingBase):
    kind = "STATEMENT_LIST_OPERATION_APPEND"

    named_children = ("list", "value")

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, list_arg, value, source_ref):
        assert list_arg is not None
        assert value is not None

        StatementChildrenHavingBase.__init__(
            self, values={"list": list_arg, "value": value}, source_ref=source_ref
        )

    getList = StatementChildrenHavingBase.childGetter("list")
    getValue = StatementChildrenHavingBase.childGetter("value")

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        trace_collection.removeKnowledge(self.getList())

        return self, None, None


class ExpressionListOperationExtend(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_LIST_OPERATION_EXTEND"

    named_children = ("list", "value")

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, list_arg, value, source_ref):
        assert list_arg is not None
        assert value is not None

        ExpressionChildrenHavingBase.__init__(
            self, values={"list": list_arg, "value": value}, source_ref=source_ref
        )

    getList = ExpressionChildrenHavingBase.childGetter("list")
    getValue = ExpressionChildrenHavingBase.childGetter("value")

    def computeExpression(self, trace_collection):
        trace_collection.removeKnowledge(self.getList())

        return self, None, None


class ExpressionListOperationPop(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_LIST_OPERATION_POP"

    named_children = ("list",)

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, list_arg, source_ref):
        assert list_arg is not None

        ExpressionChildrenHavingBase.__init__(
            self, values={"list": list_arg}, source_ref=source_ref
        )

    getList = ExpressionChildrenHavingBase.childGetter("list")

    def computeExpression(self, trace_collection):
        # We might be able to tell that element, or know that it cannot exist
        # and raise an exception instead.
        trace_collection.removeKnowledge(self.getList())

        return self, None, None


class StatementSetOperationAdd(StatementChildrenHavingBase):
    kind = "STATEMENT_SET_OPERATION_ADD"

    named_children = ("set", "value")

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, set_arg, value, source_ref):
        assert set_arg is not None
        assert value is not None

        StatementChildrenHavingBase.__init__(
            self, values={"set": set_arg, "value": value}, source_ref=source_ref
        )

    getSet = StatementChildrenHavingBase.childGetter("set")
    getValue = StatementChildrenHavingBase.childGetter("value")

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        trace_collection.removeKnowledge(self.getSet())

        return self, None, None


class ExpressionSetOperationUpdate(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_SET_OPERATION_UPDATE"

    named_children = ("set", "value")

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, set_arg, value, source_ref):
        assert set_arg is not None
        assert value is not None

        ExpressionChildrenHavingBase.__init__(
            self, values={"set": set_arg, "value": value}, source_ref=source_ref
        )

    getSet = ExpressionChildrenHavingBase.childGetter("set")
    getValue = ExpressionChildrenHavingBase.childGetter("value")

    def computeExpression(self, trace_collection):
        trace_collection.removeKnowledge(self.getSet())

        return self, None, None
