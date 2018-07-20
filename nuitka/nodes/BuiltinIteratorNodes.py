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
""" Built-in iterator nodes.

These play a role in for loops, and in unpacking. They can something be
predicted to succeed or fail, in which case, code can become less complex.

The length of things is an important optimization issue for these to be
good.
"""

from nuitka.Builtins import calledWithBuiltinArgumentNamesDecorator
from nuitka.PythonVersions import python_version

from .ExpressionBases import (
    ExpressionBuiltinSingleArgBase,
    ExpressionChildrenHavingBase
)
from .NodeBases import StatementChildHavingBase
from .NodeMakingHelpers import (
    makeRaiseExceptionReplacementStatement,
    wrapExpressionWithSideEffects
)
from .shapes.StandardShapes import ShapeIterator


class ExpressionBuiltinIter1(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_BUILTIN_ITER1"

    simulator = iter

    def computeExpression(self, trace_collection):
        trace_collection.initIteratorValue(self)
        value = self.getValue()

        return value.computeExpressionIter1(
            iter_node        = self,
            trace_collection = trace_collection
        )

    def computeExpressionIter1(self, iter_node, trace_collection):
        # Iteration over an iterator is that iterator.

        return (
            self,
            "new_builtin",
            "Eliminated useless iterator creation."
        )

    def getTypeShape(self):
        return self.getValue().getTypeShape().getShapeIter()

    def computeExpressionNext1(self, next_node, trace_collection):
        value = self.getValue()

        if value.isKnownToBeIterableAtMin(1) and \
           value.canPredictIterationValues():
            result = wrapExpressionWithSideEffects(
                new_node     = value.getIterationValue(0),
                old_node     = value,
                side_effects = value.getIterationValueRange(1,None)
            )

            return result, "new_expression", "Pridicted 'next' value from iteration."

        self.onContentEscapes(trace_collection)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return next_node, None, None

    def isKnownToBeIterable(self, count):
        if count is None:
            return True

        iter_length = self.getValue().getIterationLength()
        return iter_length == count

    def isKnownToBeIterableAtMin(self, count):
        assert type(count) is int

        iter_length = self.getValue().getIterationMinLength()
        return iter_length is not None and count <= iter_length

    def isKnownToBeIterableAtMax(self, count):
        assert type(count) is int

        iter_length = self.getValue().getIterationMaxLength()
        return iter_length is not None and count <= iter_length

    def getIterationLength(self):
        return self.getValue().getIterationLength()

    def canPredictIterationValues(self):
        return self.getValue().canPredictIterationValues()

    def getIterationValue(self, element_index):
        return self.getValue().getIterationValue(element_index)

    def extractSideEffects(self):
        # Iterator making is the side effect itself.
        value = self.getValue()

        if value.isCompileTimeConstant() and value.isKnownToBeIterable(None):
            return ()
        else:
            return (self,)

    def mayHaveSideEffects(self):
        if self.getValue().isCompileTimeConstant():
            return not self.getValue().isKnownToBeIterable(None)

        return True

    def mayRaiseException(self, exception_type):
        value = self.getValue()

        if value.mayRaiseException(exception_type):
            return True

        if value.isKnownToBeIterable(None):
            return False

        return True

    def onRelease(self, trace_collection):
        # print "onRelease", self
        pass


class ExpressionBuiltinIterForUnpack(ExpressionBuiltinIter1):
    kind = "EXPRESSION_BUILTIN_ITER_FOR_UNPACK"

    @staticmethod
    def simulator(value):
        try:
            return iter(value)
        except TypeError:
            raise TypeError(
                "cannot unpack non-iterable %s object" % (
                    type(value).__name__
                )
            )


class StatementSpecialUnpackCheck(StatementChildHavingBase):
    kind = "STATEMENT_SPECIAL_UNPACK_CHECK"

    named_child = "iterator"

    __slots__ = ("count",)

    def __init__(self, iterator, count, source_ref):
        StatementChildHavingBase.__init__(
            self,
            value      = iterator,
            source_ref = source_ref
        )

        self.count = int(count)

    def getDetails(self):
        return {
            "count" : self.getCount(),
        }

    def getCount(self):
        return self.count

    getIterator = StatementChildHavingBase.childGetter("iterator")

    def computeStatement(self, trace_collection):
        trace_collection.onExpression(self.getIterator())
        iterator = self.getIterator()

        if iterator.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(
                BaseException
            )

        if iterator.willRaiseException(BaseException):
            from .NodeMakingHelpers import \
              makeStatementExpressionOnlyReplacementNode

            result = makeStatementExpressionOnlyReplacementNode(
                expression = iterator,
                node       = self
            )

            return result, "new_raise", """\
Explicit raise already raises implicitly building exception type."""

        if iterator.isExpressionTempVariableRef() and \
           iterator.variable_trace.isAssignTrace():

            iterator = iterator.variable_trace.getAssignNode().getAssignSource()

            current_index = trace_collection.getIteratorNextCount(iterator)
        else:
            current_index = None

        if current_index is not None:
            iter_length = iterator.getIterationLength()

            if iter_length is not None:
                # Remove the check if it can be decided at compile time.
                if current_index == iter_length:
                    return None, "new_statements", """\
Determined iteration end check to be always true."""
                else:
                    result = makeRaiseExceptionReplacementStatement(
                        statement       = self,
                        exception_type  = "ValueError",
                        exception_value = "too many values to unpack"
                                            if python_version < 300 else
                                          "too many values to unpack (expected %d)" % self.getCount()
                    )

                    trace_collection.onExceptionRaiseExit(
                        TypeError
                    )

                    return result, "new_raise", """\
Determined iteration end check to always raise."""

        trace_collection.onExceptionRaiseExit(
            BaseException
        )

        return self, None, None

    def getStatementNiceName(self):
        return "iteration check statement"


class ExpressionBuiltinIter2(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_ITER2"

    named_children = (
        "callable",
        "sentinel",
    )

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, callable_arg, sentinel, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "callable" : callable_arg,
                "sentinel" : sentinel,
            },
            source_ref = source_ref
        )

    getCallable = ExpressionChildrenHavingBase.childGetter("callable")
    getSentinel = ExpressionChildrenHavingBase.childGetter("sentinel")

    def getTypeShape(self):
        # TODO: This could be more specific.
        return ShapeIterator

    def computeExpression(self, trace_collection):
        # TODO: The "callable" should be investigated here, maybe it is not
        # really callable, or raises an exception.

        return self, None, None

    def computeExpressionIter1(self, iter_node, trace_collection):
        return self, "new_builtin", "Eliminated useless iterator creation."



class ExpressionAsyncIter(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_ASYNC_ITER"

    def computeExpression(self, trace_collection):
        value = self.getValue()

        return value.computeExpressionAsyncIter(
            iter_node        = self,
            trace_collection = trace_collection
        )

    def isKnownToBeIterable(self, count):
        if count is None:
            return True

        # TODO: Should ask value if it is.
        return None

    def getIterationLength(self):
        return self.getValue().getIterationLength()

    def extractSideEffects(self):
        # Iterator making is the side effect itself.
        if self.getValue().isCompileTimeConstant():
            return ()
        else:
            return (self,)

    def mayHaveSideEffects(self):
        if self.getValue().isCompileTimeConstant():
            return self.getValue().isKnownToBeIterable(None)

        return True

    def mayRaiseException(self, exception_type):
        value = self.getValue()

        if value.mayRaiseException(exception_type):
            return True

        if value.isKnownToBeIterable(None):
            return False

        return True

    def isKnownToBeIterableAtMin(self, count):
        assert type(count) is int

        iter_length = self.getValue().getIterationMinLength()
        return iter_length is not None and iter_length < count

    def isKnownToBeIterableAtMax(self, count):
        assert type(count) is int

        iter_length = self.getValue().getIterationMaxLength()

        return iter_length is not None and count <= iter_length

    def onRelease(self, trace_collection):
        # print "onRelease", self
        pass


class ExpressionAsyncNext(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_ASYNC_NEXT"

    def __init__(self, value, source_ref):
        ExpressionBuiltinSingleArgBase.__init__(
            self,
            value      = value,
            source_ref = source_ref
        )

    def computeExpression(self, trace_collection):
        # TODO: Predict iteration result if possible via SSA variable trace of
        # the iterator state.

        # Assume exception is possible. TODO: We might query the next from the
        # source with a computeExpressionAsyncNext slot, but we delay that.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None
