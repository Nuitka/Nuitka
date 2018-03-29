#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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

from abc import abstractmethod

from .ExpressionBases import ExpressionBase
from .NodeBases import NodeBase, StatementChildrenHavingBase
from .NodeMakingHelpers import makeConstantReplacementNode


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

    def computeStatement(self, trace_collection):
        trace_collection.onExpression(self.getExpression())
        expression = self.getExpression()

        if expression.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        if expression.willRaiseException(BaseException):
            from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

            result = makeStatementExpressionOnlyReplacementNode(
                expression = expression,
                node       = self
            )

            return result, "new_raise", """\
Return statement raises in returned expression, removed return."""

        trace_collection.onFunctionReturn()

        if expression.isExpressionConstantRef():
            result = makeStatementReturnConstant(
                constant   = expression.getCompileTimeConstant(),
                source_ref = self.source_ref
            )

            return result, "new_statements", """\
Return value is always constant."""

        return self, None, None


class StatementReturnConstantBase(NodeBase):
    __slots__ = ()

    def __init__(self, source_ref):
        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

    @staticmethod
    def isStatementReturn():
        return True

    def isStatementAborting(self):
        return True

    def mayRaiseException(self, exception_type):
        return False

    def computeStatement(self, trace_collection):
        trace_collection.onFunctionReturn()

        return self, None, None

    @abstractmethod
    def getConstant(self):
        """ The returned constant value.

        """

    def getExpression(self):
        return makeConstantReplacementNode(
            node     = self,
            constant = self.getConstant()
        )


class StatementReturnNone(StatementReturnConstantBase):
    kind = "STATEMENT_RETURN_NONE"

    __slots__ = ()

    def __init__(self, source_ref):
        StatementReturnConstantBase.__init__(
            self,
            source_ref = source_ref
        )

    def getConstant(self):
        return None


class StatementReturnFalse(StatementReturnConstantBase):
    kind = "STATEMENT_RETURN_FALSE"

    __slots__ = ()

    def __init__(self, source_ref):
        StatementReturnConstantBase.__init__(
            self,
            source_ref = source_ref
        )

    def getConstant(self):
        return False


class StatementReturnTrue(StatementReturnConstantBase):
    kind = "STATEMENT_RETURN_TRUE"

    __slots__ = ()

    def __init__(self, source_ref):
        StatementReturnConstantBase.__init__(
            self,
            source_ref = source_ref
        )

    def getConstant(self):
        return True


class StatementReturnConstant(StatementReturnConstantBase):
    kind = "STATEMENT_RETURN_CONSTANT"

    __slots__ = ("constant",)

    def __init__(self, constant, source_ref):
        StatementReturnConstantBase.__init__(
            self,
            source_ref = source_ref
        )

        self.constant = constant

    def getConstant(self):
        return self.constant

    def getDetails(self):
        return {
            "constant" : self.constant
        }


def makeStatementReturnConstant(constant, source_ref):
    if constant is None:
        return StatementReturnNone(
            source_ref = source_ref
        )
    elif constant is True:
        return StatementReturnTrue(
            source_ref = source_ref
        )
    elif constant is False:
        return StatementReturnFalse(
            source_ref = source_ref
        )
    else:
        return StatementReturnConstant(
            constant   = constant,
            source_ref = source_ref
        )


class ExpressionReturnedValueRef(ExpressionBase):
    kind = "EXPRESSION_RETURNED_VALUE_REF"

    def __init__(self, source_ref):
        ExpressionBase.__init__(
            self,
            source_ref = source_ref
        )

    def computeExpressionRaw(self, trace_collection):
        # TODO: Might be predictable based on the exception handler this is in.
        return self, None, None

    def mayHaveSideEffects(self):
        # Referencing the expression type has no side effect
        return False

    def mayRaiseException(self, exception_type):
        return False
