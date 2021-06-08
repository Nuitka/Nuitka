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
""" Subscript node.

Subscripts are important when working with lists and dictionaries. Tracking
them can allow to achieve more compact code, or predict results at compile time.

There is be a method "computeExpressionSubscript" to aid predicting them in the
other nodes.
"""

from .ExpressionBases import ExpressionChildrenHavingBase
from .NodeBases import StatementChildrenHavingBase


class StatementAssignmentSubscript(StatementChildrenHavingBase):
    kind = "STATEMENT_ASSIGNMENT_SUBSCRIPT"

    named_children = ("source", "subscribed", "subscript")

    def __init__(self, subscribed, subscript, source, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values={"source": source, "subscribed": subscribed, "subscript": subscript},
            source_ref=source_ref,
        )

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.subnode_subscribed.computeExpressionSetSubscript(
            set_node=self,
            subscript=self.subnode_subscript,
            value_node=self.subnode_source,
            trace_collection=trace_collection,
        )

    @staticmethod
    def getStatementNiceName():
        return "subscript assignment statement"


class StatementDelSubscript(StatementChildrenHavingBase):
    kind = "STATEMENT_DEL_SUBSCRIPT"

    named_children = ("subscribed", "subscript")

    def __init__(self, subscribed, subscript, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values={"subscribed": subscribed, "subscript": subscript},
            source_ref=source_ref,
        )

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.subnode_subscribed.computeExpressionDelSubscript(
            del_node=self,
            subscript=self.subnode_subscript,
            trace_collection=trace_collection,
        )

    @staticmethod
    def getStatementNiceName():
        return "subscript del statement"


class ExpressionSubscriptLookup(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_SUBSCRIPT_LOOKUP"

    named_children = ("expression", "subscript")

    def __init__(self, expression, subscript, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values={"expression": expression, "subscript": subscript},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        return self.subnode_expression.computeExpressionSubscript(
            lookup_node=self,
            subscript=self.subnode_subscript,
            trace_collection=trace_collection,
        )

    @staticmethod
    def isKnownToBeIterable(count):
        return None
