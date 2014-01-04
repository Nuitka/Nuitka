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

Right now there is only the print statement, but in principle, there should also be the
print function here. These perform output, which can be combined if possible, and could be
detected to fail, which would be perfect.

Predicting the behavior of 'print' is not trivial at all, due to many special cases.
"""

from .NodeBases import StatementChildrenHavingBase

# Delayed import into multiple branches is not an issue, pylint: disable=W0404

class StatementPrint(StatementChildrenHavingBase):
    kind = "STATEMENT_PRINT"

    named_children = ( "dest", "values" )

    def __init__(self, dest, values, newline, source_ref):
        assert values or newline

        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "values" : tuple( values ),
                "dest"   : dest
            },
            source_ref = source_ref
        )

        self.newline = newline

    def isNewlinePrint(self):
        return self.newline

    def removeNewlinePrint(self):
        self.newline = False

    getDestination = StatementChildrenHavingBase.childGetter( "dest" )
    getValues = StatementChildrenHavingBase.childGetter( "values" )
    setValues = StatementChildrenHavingBase.childSetter( "values" )

    def computeStatement(self, constraint_collection):
        constraint_collection.onExpression( self.getDestination(), allow_none = True )
        dest = self.getDestination()

        if dest is not None and dest.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

            result = makeStatementExpressionOnlyReplacementNode(
                expression = dest,
                node       = self
            )

            return result, "new_raise", """\
Known exception raise in print statement destination converted to explicit raise."""

        for count, value in enumerate( self.getValues() ):
            constraint_collection.onExpression( value )
            value = self.getValues()[ count ]

            if value.willRaiseException( BaseException ):
                # Trim to values up to this from this statement.
                values = self.getValues()
                values = list( values )[ : values.index( value ) ]

                from .NodeMakingHelpers import (
                    makeStatementExpressionOnlyReplacementNode,
                    makeStatementsSequenceReplacementNode
                )

                if values:
                    result = makeStatementsSequenceReplacementNode(
                        statements = (
                            StatementPrint(
                                dest       = self.getDestination(),
                                values     = values,
                                newline    = False,
                                source_ref = self.source_ref
                            ),
                            makeStatementExpressionOnlyReplacementNode(
                                expression = value,
                                node       = self
                            )
                        ),
                        node       = self
                    )
                else:
                    result = makeStatementExpressionOnlyReplacementNode(
                        expression = value,
                        node       = self
                    )

                return result, "new_raise", """\
Known exception raise in print statement arguments converted to explicit raise."""

        printeds = self.getValues()

        for count in range( len( printeds ) - 1 ):
            if printeds[ count ].isExpressionConstantRef():
                new_value = printeds[ count ].getConstant()

                # Above code should have replaced this already.
                assert type( new_value ) is str, self

                stop_count = count + 1

                while True:
                    candidate = printeds[ stop_count ]

                    if candidate.isExpressionConstantRef() and candidate.isStringConstant():
                        if not new_value.endswith( "\t" ):
                            new_value += " "

                        new_value += candidate.getConstant()

                        stop_count += 1

                        if stop_count >= len( printeds ):
                            break

                    else:
                        break

                if stop_count != count + 1:
                    from .NodeMakingHelpers import makeConstantReplacementNode

                    new_node = makeConstantReplacementNode(
                        constant = new_value,
                        node     = printeds[ count ]
                    )

                    new_printeds = printeds[ : count ] + ( new_node, ) + printeds[ stop_count: ]

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
                    from .NodeMakingHelpers import (
                        makeStatementExpressionOnlyReplacementNode,
                        makeStatementsSequenceReplacementNode
                    )

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
