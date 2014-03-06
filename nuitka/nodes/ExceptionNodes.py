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
""" Nodes related to raising and making exceptions.

"""

from .NodeBases import (
    ExpressionChildrenHavingBase,
    StatementChildrenHavingBase,
    ExpressionMixin,
    NodeBase
)

class StatementRaiseException(StatementChildrenHavingBase):
    kind = "STATEMENT_RAISE_EXCEPTION"

    named_children = (
        "exception_type",
        "exception_value",
        "exception_trace",
        "exception_cause"
    )

    def __init__(self, exception_type, exception_value, exception_trace,
                 exception_cause, source_ref):
        if exception_type is None:
            assert exception_value is None

        if exception_value is None:
            assert exception_trace is None

        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "exception_type"  : exception_type,
                "exception_value" : exception_value,
                "exception_trace" : exception_trace,
                "exception_cause" : exception_cause
            },
            source_ref = source_ref
        )

        self.reraise_local = False
        self.reraise_finally = False

    getExceptionType = StatementChildrenHavingBase.childGetter(
        "exception_type"
    )
    getExceptionValue = StatementChildrenHavingBase.childGetter(
        "exception_value"
    )
    getExceptionTrace = StatementChildrenHavingBase.childGetter(
        "exception_trace"
    )
    getExceptionCause = StatementChildrenHavingBase.childGetter(
        "exception_cause"
    )

    def isReraiseException(self):
        return self.getExceptionType() is None

    def isReraiseExceptionLocal(self):
        assert self.isReraiseException()

        return self.reraise_local

    def isReraiseExceptionFinally(self):
        assert self.isReraiseException()

        return self.reraise_finally

    def markAsReraiseLocal(self):
        self.reraise_local = True

    def markAsReraiseFinally(self):
        self.reraise_finally = True

    def isStatementAborting(self):
        return True

    def needsLineNumber(self):
        return not self.isReraiseException()

    def isImplicit(self):
        return False

    def computeStatement(self, constraint_collection):
        constraint_collection.onExpression(
            expression = self.getExceptionType(),
            allow_none = True
        )
        exception_type = self.getExceptionType()

        if exception_type is not None and \
           exception_type.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

            result = makeStatementExpressionOnlyReplacementNode(
                expression = exception_type,
                node       = self
            )

            return result, "new_raise", """\
Explicit raise already raises implicitely building exception type."""

        constraint_collection.onExpression(
            expression = self.getExceptionValue(),
            allow_none = True
        )
        exception_value = self.getExceptionValue()

        if exception_value is not None and exception_value.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    exception_type,
                    exception_value
                )
            )

            return result, "new_node", """\
Explicit raise already raises implicitely building exception value."""

        constraint_collection.onExpression(
            expression = self.getExceptionTrace(),
            allow_none = True
        )
        exception_trace = self.getExceptionTrace()

        if exception_trace is not None and \
           exception_trace.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    exception_type,
                    exception_value,
                    exception_trace
                )
            )

            return result, "new_raise", """\
Explicit raise already raises implicitely building exception traceback."""

        constraint_collection.onExpression(
            expression = self.getExceptionCause(),
            allow_none = True
        )
        exception_cause = self.getExceptionCause()

        if exception_cause is not None and \
           exception_cause.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    exception_type,
                    exception_cause,
                )
            )

            return result, "new_raise", """
Explicit raise already raises implicitely building exception cause."""

        return self, None, None


class StatementRaiseExceptionImplicit(StatementRaiseException):
    kind = "STATEMENT_RAISE_EXCEPTION_IMPLICIT"

    def isStatementRaiseException(self):
        return True

    def isImplicit(self):
        return True


class ExpressionRaiseException(ExpressionChildrenHavingBase):
    """ This node type is only produced via optimization.

    CPython only knows exception raising as a statement, but often the raising
    of exceptions can be predicted to occur as part of an expression, which it
    replaces then.
    """

    kind = "EXPRESSION_RAISE_EXCEPTION"

    named_children = ( "exception_type", "exception_value" )

    def __init__(self, exception_type, exception_value, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "exception_type"  : exception_type,
                "exception_value" : exception_value
            },
            source_ref = source_ref
        )

    def willRaiseException(self, exception_type):
        # Virtual method, pylint: disable=R0201,W0613

        # One thing is clear, it will raise. TODO: Match exception_type more
        # closely if it is predictable.
        if exception_type is BaseException:
            return True
        else:
            return False


    getExceptionType = ExpressionChildrenHavingBase.childGetter(
        "exception_type"
    )
    getExceptionValue = ExpressionChildrenHavingBase.childGetter(
        "exception_value"
    )

    def mayProvideReference(self):
        return False

    def computeExpression(self, constraint_collection):
        return self, None, None

    def computeExpressionDrop(self, statement, constraint_collection):
        from .ExceptionNodes import StatementRaiseExceptionImplicit

        result = StatementRaiseExceptionImplicit(
            exception_type  = self.getExceptionType(),
            exception_value = self.getExceptionValue(),
            exception_trace = None,
            exception_cause = None,
            source_ref      = self.getSourceReference()
        )

        return result, "new_raise", """\
Propgated implict raise expression to raise statement."""


class ExpressionBuiltinMakeException(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_MAKE_EXCEPTION"

    named_children = ( "args", )

    def __init__(self, exception_name, args, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "args" : tuple( args ),
            },
            source_ref = source_ref
        )

        self.exception_name = exception_name

    def getDetails(self):
        return { "exception_name" : self.exception_name }

    def getExceptionName(self):
        return self.exception_name

    getArgs = ExpressionChildrenHavingBase.childGetter( "args" )

    def computeExpression(self, constraint_collection):
        return self, None, None


class ExpressionCaughtExceptionTypeRef(NodeBase, ExpressionMixin):
    kind = "EXPRESSION_CAUGHT_EXCEPTION_TYPE_REF"

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


class ExpressionCaughtExceptionValueRef(NodeBase, ExpressionMixin):
    kind = "EXPRESSION_CAUGHT_EXCEPTION_VALUE_REF"

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

    def makeCloneAt(self, source_ref):
        return ExpressionCaughtExceptionValueRef(
            source_ref = source_ref
        )


class ExpressionCaughtExceptionTracebackRef(NodeBase, ExpressionMixin):
    kind = "EXPRESSION_CAUGHT_EXCEPTION_TRACEBACK_REF"

    def __init__(self, source_ref):
        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

    def computeExpression(self, constraint_collection):
        return self, None, None

    def mayHaveSideEffects(self):
        # Referencing the expression type has no side effect
        return False
