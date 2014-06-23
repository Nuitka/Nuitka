#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .NodeBases import StatementChildrenHavingBase
from .NodeMakingHelpers import (
    makeConstantReplacementNode,
    makeStatementExpressionOnlyReplacementNode,
    makeStatementsSequenceReplacementNode,
    wrapStatementWithSideEffects
)


class StatementPrintValue(StatementChildrenHavingBase):
    kind = "STATEMENT_PRINT_VALUE"

    named_children = (
        "dest",
        "value"
    )

    def __init__(self, dest, value, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "value" : value,
                "dest"  : dest
            },
            source_ref = source_ref
        )

    getDestination = StatementChildrenHavingBase.childGetter(
        "dest"
    )

    getValue = StatementChildrenHavingBase.childGetter(
        "value"
    )
    setValue = StatementChildrenHavingBase.childSetter(
        "value"
    )

    def computeStatement(self, constraint_collection):
        constraint_collection.onExpression(
            expression = self.getDestination(),
            allow_none = True
        )
        dest = self.getDestination()

        if dest is not None and dest.willRaiseException(BaseException):
            result = makeStatementExpressionOnlyReplacementNode(
                expression = dest,
                node       = self
            )

            return result, "new_raise", """\
Known exception raise in print statement destination converted to explicit \
raise."""

        constraint_collection.onExpression(
            expression = self.getValue()
        )
        value = self.getValue()

        if value.willRaiseException(BaseException):
            if dest is not None:
                result = wrapStatementWithSideEffects(
                    new_node = makeStatementExpressionOnlyReplacementNode(
                        expression = value,
                        node       = self
                    ),
                    old_node = dest
                )
            else:
                result = makeStatementExpressionOnlyReplacementNode(
                    expression = value,
                    node       = self
                )

            return result, "new_raise", """\
Known exception raise in print statement arguments converted to explicit \
raise."""

        return self, None, None

        # TODO: Restore this

        printeds = self.getValues()

        for count in range( len( printeds ) - 1 ):
            if printeds[ count ].isExpressionConstantRef():
                new_value = printeds[ count ].getConstant()

                # Above code should have replaced this already.
                assert type( new_value ) is str, self

                stop_count = count + 1

                while True:
                    candidate = printeds[ stop_count ]

                    if candidate.isExpressionConstantRef() and \
                       candidate.isStringConstant():
                        if not new_value.endswith( "\t" ):
                            new_value += " "

                        new_value += candidate.getConstant()

                        stop_count += 1

                        if stop_count >= len( printeds ):
                            break

                    else:
                        break

                if stop_count != count + 1:
                    new_node = makeConstantReplacementNode(
                        constant = new_value,
                        node     = printeds[ count ]
                    )

                    new_printeds = printeds[ : count ] + \
                                   ( new_node, ) + \
                                   printeds[ stop_count: ]

                    self.setValues( new_printeds )

                    constraint_collection.signalChange(
                        "new_expression",
                        printeds[ count ].getSourceReference(),
                        "Combined print string arguments at compile time"
                    )

                    break

        if dest is None:
            values = self.getValues()

            if values:
                if values[0].isExpressionSideEffects():
                    statements = [
                        makeStatementExpressionOnlyReplacementNode(
                            side_effect,
                            self
                        )
                        for side_effect in
                        values[0].getSideEffects()
                    ]

                    statements.append( self )

                    self.setValues(
                        ( values[0].getExpression(), ) + values[ 1: ]
                    )

                    result = makeStatementsSequenceReplacementNode(
                        statements = statements,
                        node       = self,
                    )

                    return result, "new_statements", """\
Side effects first printed item promoted to statements."""

        return self, None, None


class StatementPrintNewline(StatementChildrenHavingBase):
    kind = "STATEMENT_PRINT_NEWLINE"

    named_children = (
        "dest",
    )

    def __init__(self, dest, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "dest" : dest
            },
            source_ref = source_ref
        )

    getDestination = StatementChildrenHavingBase.childGetter(
        "dest"
    )

    def computeStatement(self, constraint_collection):
        # TODO: Reactivate below optimizations for prints.
        constraint_collection.onExpression(
            expression = self.getDestination(),
            allow_none = True
        )
        dest = self.getDestination()

        if dest is not None and dest.willRaiseException(BaseException):
            result = makeStatementExpressionOnlyReplacementNode(
                expression = dest,
                node       = self
            )

            return result, "new_raise", """\
Known exception raise in print statement destination converted to explicit \
raise."""

        return self, None, None
