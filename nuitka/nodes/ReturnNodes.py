#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Return node

This one exits functions. The only other exit is the default exit of functions with 'None' value, if no return is done.
"""

from .NodeBases import ExpressionMixin, NodeBase, StatementChildrenHavingBase


class StatementReturn(StatementChildrenHavingBase):
    kind = "STATEMENT_RETURN"

    named_children = ("expression",)
    nice_children = ("return value",)

    def __init__(self, expression, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "expression" : expression
            },
            source_ref = source_ref
        )

    getExpression = StatementChildrenHavingBase.childGetter(
        "expression"
    )

    def isStatementAborting(self):
        return True

    def mayRaiseException(self, exception_type):
        return self.getExpression().mayRaiseException(exception_type)

    def computeStatement(self, constraint_collection):
        constraint_collection.onExpression(self.getExpression())
        expression = self.getExpression()

        if expression.mayRaiseException(BaseException):
            constraint_collection.onExceptionRaiseExit(BaseException)

        if expression.willRaiseException(BaseException):
            from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

            result = makeStatementExpressionOnlyReplacementNode(
                expression = expression,
                node       = self
            )

            return result, "new_raise", """\
Return statement raises in returned expression, removed return."""

        constraint_collection.onFunctionReturn()

        return self, None, None


class ExpressionReturnedValueRef(NodeBase, ExpressionMixin):
    kind = "EXPRESSION_RETURNED_VALUE_REF"

    def __init__(self, source_ref):
        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

    def computeExpression(self, constraint_collection):
        # TODO: Might be predictable based on the exception handler this is in.
        return self, None, None

    def mayHaveSideEffects(self):
        # Referencing the expression type has no side effect
        return False

    def mayRaiseException(self, exception_type):
        return False
