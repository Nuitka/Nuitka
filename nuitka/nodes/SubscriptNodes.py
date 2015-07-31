#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

There will be a method "computeExpressionSubscript" to aid predicting them.
"""

from .NodeBases import ExpressionChildrenHavingBase, StatementChildrenHavingBase
from .NodeMakingHelpers import (
    makeStatementExpressionOnlyReplacementNode,
    makeStatementOnlyNodesFromExpressions
)


class StatementAssignmentSubscript(StatementChildrenHavingBase):
    kind = "STATEMENT_ASSIGNMENT_SUBSCRIPT"

    named_children = (
        "source",
        "expression",
        "subscript"
    )

    def __init__(self, expression, subscript, source, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "source"     : source,
                "expression" : expression,
                "subscript"  : subscript
            },
            source_ref = source_ref
        )

    getSubscribed = StatementChildrenHavingBase.childGetter("expression")
    getSubscript = StatementChildrenHavingBase.childGetter("subscript")
    getAssignSource = StatementChildrenHavingBase.childGetter("source")

    def computeStatement(self, constraint_collection):
        constraint_collection.onExpression(
            expression = self.getAssignSource()
        )
        source = self.getAssignSource()

        # No assignment will occur, if the assignment source raises, so strip it
        # away.
        if source.willRaiseException(BaseException):
            result = makeStatementExpressionOnlyReplacementNode(
                expression = source,
                node       = self
            )

            return result, "new_raise", """\
Subscript assignment raises exception in assigned value, removed assignment."""

        constraint_collection.onExpression(self.getSubscribed())
        subscribed = self.getSubscribed()

        if subscribed.willRaiseException(BaseException):
            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    source,
                    subscribed
                )
            )

            return result, "new_raise", """\
Subscript assignment raises exception in subscribed, removed assignment."""

        constraint_collection.onExpression(
            self.getSubscript()
        )
        subscript = self.getSubscript()

        if subscript.willRaiseException(BaseException):
            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    source,
                    subscribed,
                    subscript
                )
            )

            return result, "new_raise", """
Subscript assignment raises exception in subscript value, removed \
assignment."""

        return subscribed.computeExpressionSetSubscript(
            set_node              = self,
            subscript             = subscript,
            value_node            = source,
            constraint_collection = constraint_collection
        )


class StatementDelSubscript(StatementChildrenHavingBase):
    kind = "STATEMENT_DEL_SUBSCRIPT"

    named_children = (
        "expression",
        "subscript"
    )

    def __init__(self, expression, subscript, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "expression" : expression,
                "subscript"  : subscript
            },
            source_ref = source_ref
        )

    getSubscribed = StatementChildrenHavingBase.childGetter("expression")
    getSubscript = StatementChildrenHavingBase.childGetter("subscript")

    def computeStatement(self, constraint_collection):
        constraint_collection.onExpression(self.getSubscribed())
        subscribed = self.getSubscribed()

        if subscribed.willRaiseException(BaseException):
            result = makeStatementExpressionOnlyReplacementNode(
                expression = subscribed,
                node       = self
            )

            return result, "new_raise", """\
Subscript 'del' raises exception in subscribed value, removed del."""

        constraint_collection.onExpression(self.getSubscript())
        subscript = self.getSubscript()

        if subscript.willRaiseException(BaseException):
            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    subscribed,
                    subscript
                )
            )

            return result, "new_raise", """\
Subscript 'del' raises exception in subscript value, removed del."""

        return subscribed.computeExpressionDelSubscript(
            set_node              = self,
            subscript             = subscript,
            constraint_collection = constraint_collection
        )


class ExpressionSubscriptLookup(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_SUBSCRIPT_LOOKUP"

    named_children = (
        "subscribed",
        "subscript"
    )

    def __init__(self, subscribed, subscript, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "subscribed" : subscribed,
                "subscript"  : subscript
            },
            source_ref = source_ref
        )

    getLookupSource = ExpressionChildrenHavingBase.childGetter("subscribed")
    getSubscript = ExpressionChildrenHavingBase.childGetter("subscript")

    def computeExpression(self, constraint_collection):
        return self.getLookupSource().computeExpressionSubscript(
            lookup_node           = self,
            subscript             = self.getSubscript(),
            constraint_collection = constraint_collection
        )

    def isKnownToBeIterable(self, count):
        return None
