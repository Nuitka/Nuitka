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
""" Return node

This one exits functions. The only other exit is the default exit of functions with 'None'
value, if no return is done.
"""

from .NodeBases import StatementChildrenHavingBase


class StatementReturn(StatementChildrenHavingBase):
    kind = "STATEMENT_RETURN"

    named_children = ( "expression", )

    def __init__(self, expression, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "expression" : expression
            },
            source_ref = source_ref
        )

        self.exception_driven = None

    getExpression = StatementChildrenHavingBase.childGetter( "expression" )

    def isStatementAborting(self):
        return True

    def mayRaiseException(self, exception_type):
        return self.getExpression().mayRaiseException( exception_type )

    def setExceptionDriven(self, value):
        self.exception_driven = value

    def isExceptionDriven(self):
        assert self.exception_driven is not None

        return self.exception_driven

    def computeStatement(self, constraint_collection):
        constraint_collection.onExpression( self.getExpression() )
        expression = self.getExpression()

        if expression.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

            result = makeStatementExpressionOnlyReplacementNode(
                expression = expression,
                node       = self
            )

            return result, "new_raise", "Return statement raises in returned expression, removed return"

        return self, None, None


class StatementGeneratorReturn(StatementReturn):
    kind = "STATEMENT_GENERATOR_RETURN"

    def __init__(self, expression, source_ref):
        StatementReturn.__init__(
            self,
            expression = expression,
            source_ref = source_ref
        )
