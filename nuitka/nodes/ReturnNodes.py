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
""" Return node

This one exits functions. The only other exit is the default exit of functions with 'None' value, if no return is done.
"""

from abc import abstractmethod

from .NodeBases import StatementBase, StatementChildHavingBase


class StatementReturn(StatementChildHavingBase):
    kind = "STATEMENT_RETURN"

    named_child = "expression"
    nice_child = "return value"

    def __init__(self, expression, source_ref):
        assert expression
        StatementChildHavingBase.__init__(self, value=expression, source_ref=source_ref)

    @staticmethod
    def mayReturn():
        return True

    @staticmethod
    def isStatementAborting():
        return True

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)

    def computeStatement(self, trace_collection):
        expression = trace_collection.onExpression(self.subnode_expression)

        if expression.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        if expression.willRaiseException(BaseException):
            from .NodeMakingHelpers import (
                makeStatementExpressionOnlyReplacementNode,
            )

            result = makeStatementExpressionOnlyReplacementNode(
                expression=expression, node=self
            )

            return (
                result,
                "new_raise",
                """\
Return statement raises in returned expression, removed return.""",
            )

        trace_collection.onFunctionReturn()

        if expression.isExpressionConstantRef():
            result = makeStatementReturnConstant(
                constant=expression.getCompileTimeConstant(), source_ref=self.source_ref
            )

            del self.parent

            return (
                result,
                "new_statements",
                """\
Return value is constant.""",
            )

        return self, None, None


class StatementReturnConstantBase(StatementBase):
    __slots__ = ()

    def __init__(self, source_ref):
        StatementBase.__init__(self, source_ref=source_ref)

    @staticmethod
    def isStatementReturn():
        return True

    @staticmethod
    def isStatementReturnConstant():
        return True

    @staticmethod
    def isStatementAborting():
        return True

    @staticmethod
    def mayReturn():
        return True

    @staticmethod
    def mayRaiseException(exception_type):
        return False

    def computeStatement(self, trace_collection):
        trace_collection.onFunctionReturn()

        return self, None, None

    @abstractmethod
    def getConstant(self):
        """The returned constant value."""

    @staticmethod
    def getStatementNiceName():
        return "return statement"


class StatementReturnNone(StatementReturnConstantBase):
    kind = "STATEMENT_RETURN_NONE"

    __slots__ = ()

    def __init__(self, source_ref):
        StatementReturnConstantBase.__init__(self, source_ref=source_ref)

    def finalize(self):
        del self.parent

    def getConstant(self):
        return None


class StatementReturnFalse(StatementReturnConstantBase):
    kind = "STATEMENT_RETURN_FALSE"

    __slots__ = ()

    def __init__(self, source_ref):
        StatementReturnConstantBase.__init__(self, source_ref=source_ref)

    def finalize(self):
        del self.parent

    def getConstant(self):
        return False


class StatementReturnTrue(StatementReturnConstantBase):
    kind = "STATEMENT_RETURN_TRUE"

    __slots__ = ()

    def __init__(self, source_ref):
        StatementReturnConstantBase.__init__(self, source_ref=source_ref)

    def finalize(self):
        del self.parent

    def getConstant(self):
        return True


class StatementReturnConstant(StatementReturnConstantBase):
    kind = "STATEMENT_RETURN_CONSTANT"

    __slots__ = ("constant",)

    def __init__(self, constant, source_ref):
        StatementReturnConstantBase.__init__(self, source_ref=source_ref)

        self.constant = constant

    def finalize(self):
        del self.parent
        del self.constant

    def getConstant(self):
        return self.constant

    def getDetails(self):
        return {"constant": self.constant}


class StatementReturnReturnedValue(StatementBase):
    kind = "STATEMENT_RETURN_RETURNED_VALUE"

    __slots__ = ()

    def __init__(self, source_ref):
        StatementBase.__init__(self, source_ref=source_ref)

    def finalize(self):
        del self.parent

    @staticmethod
    def isStatementReturnReturnedValue():
        return True

    @staticmethod
    def isStatementReturn():
        return True

    @staticmethod
    def isStatementAborting():
        return True

    @staticmethod
    def mayReturn():
        return True

    @staticmethod
    def mayRaiseException(exception_type):
        return False

    def computeStatement(self, trace_collection):
        trace_collection.onFunctionReturn()

        return self, None, None

    @staticmethod
    def getStatementNiceName():
        return "rereturn statement"


def makeStatementReturnConstant(constant, source_ref):
    if constant is None:
        return StatementReturnNone(source_ref=source_ref)
    elif constant is True:
        return StatementReturnTrue(source_ref=source_ref)
    elif constant is False:
        return StatementReturnFalse(source_ref=source_ref)
    else:
        return StatementReturnConstant(constant=constant, source_ref=source_ref)


def makeStatementReturn(expression, source_ref):
    """Create the best return statement variant."""

    if expression is None:
        return StatementReturnNone(source_ref=source_ref)
    elif expression.isCompileTimeConstant():
        return makeStatementReturnConstant(
            constant=expression.getCompileTimeConstant(), source_ref=source_ref
        )
    else:
        return StatementReturn(expression=expression, source_ref=source_ref)
