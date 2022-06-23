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
""" Print nodes.

Right now there is only the print statement, but in principle, there should
also be the print function here. These perform output, which can be combined
if possible, and could be detected to fail, which would be perfect.

Predicting the behavior of 'print' is not trivial at all, due to many special
cases.
"""

from .NodeBases import StatementChildHavingBase, StatementChildrenHavingBase
from .NodeMakingHelpers import (
    makeStatementExpressionOnlyReplacementNode,
    makeStatementsSequenceReplacementNode,
    wrapStatementWithSideEffects,
)


class StatementPrintValue(StatementChildrenHavingBase):
    kind = "STATEMENT_PRINT_VALUE"

    named_children = ("dest", "value")

    def __init__(self, dest, value, source_ref):
        StatementChildrenHavingBase.__init__(
            self, values={"value": value, "dest": dest}, source_ref=source_ref
        )

        assert value is not None

    def computeStatement(self, trace_collection):
        dest = trace_collection.onExpression(
            expression=self.subnode_dest, allow_none=True
        )

        if dest is not None and dest.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        if dest is not None and dest.willRaiseException(BaseException):
            result = makeStatementExpressionOnlyReplacementNode(
                expression=dest, node=self
            )

            return (
                result,
                "new_raise",
                """\
Exception raise in 'print' statement destination converted to explicit raise.""",
            )

        value = trace_collection.onExpression(expression=self.subnode_value)

        if value.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        if value.willRaiseException(BaseException):
            if dest is not None:
                result = wrapStatementWithSideEffects(
                    new_node=makeStatementExpressionOnlyReplacementNode(
                        expression=value, node=self
                    ),
                    old_node=dest,
                )
            else:
                result = makeStatementExpressionOnlyReplacementNode(
                    expression=value, node=self
                )

            return (
                result,
                "new_raise",
                """\
Exception raise in 'print' statement arguments converted to explicit raise.""",
            )

        trace_collection.onExceptionRaiseExit(BaseException)

        if dest is None:
            if value.isExpressionSideEffects():
                self.setChild("value", value.subnode_expression)

                statements = [
                    makeStatementExpressionOnlyReplacementNode(side_effect, self)
                    for side_effect in value.subnode_side_effects
                ]

                statements.append(self)

                result = makeStatementsSequenceReplacementNode(
                    statements=statements, node=self
                )

                return (
                    result,
                    "new_statements",
                    """\
Side effects printed item promoted to statements.""",
                )

        if value.isCompileTimeConstant():
            # Avoid unicode encoding issues.
            if not value.isExpressionConstantUnicodeRef():
                new_value = value.getStrValue()
                assert new_value is not None, value

                if value is not new_value:
                    self.setChild("value", new_value)

        return self, None, None

    @staticmethod
    def mayRaiseException(exception_type):
        # Output may always fail due to external reasons.
        return True


class StatementPrintNewline(StatementChildHavingBase):
    kind = "STATEMENT_PRINT_NEWLINE"

    named_child = "dest"

    def __init__(self, dest, source_ref):
        StatementChildHavingBase.__init__(self, value=dest, source_ref=source_ref)

    def computeStatement(self, trace_collection):
        dest = trace_collection.onExpression(
            expression=self.subnode_dest, allow_none=True
        )

        if dest is not None and dest.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        if dest is not None and dest.willRaiseException(BaseException):
            result = makeStatementExpressionOnlyReplacementNode(
                expression=dest, node=self
            )

            return (
                result,
                "new_raise",
                """\
Exception raise in 'print' statement destination converted to explicit raise.""",
            )

        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def mayRaiseException(exception_type):
        # Output may always fail due to external reasons.
        return True
