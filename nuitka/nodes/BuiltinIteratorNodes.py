#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.PythonVersions import python_version

from .ExpressionBases import (
    ExpressionBuiltinSingleArgBase,
    ExpressionChildrenHavingBase,
)
from .NodeBases import StatementChildHavingBase
from .NodeMakingHelpers import (
    makeRaiseExceptionReplacementStatement,
    wrapExpressionWithSideEffects,
)
from .shapes.StandardShapes import tshape_iterator


class ExpressionBuiltinIter1(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_BUILTIN_ITER1"

    simulator = iter

    def computeExpression(self, trace_collection):
        trace_collection.initIteratorValue(self)

        value = self.subnode_value
        return value.computeExpressionIter1(
            iter_node=self, trace_collection=trace_collection
        )

    def computeExpressionIter1(self, iter_node, trace_collection):
        # Iteration over an iterator is that iterator.

        return self, "new_builtin", "Eliminated useless iterator creation."

    def getTypeShape(self):
        return self.subnode_value.getTypeShape().getShapeIter()

    def computeExpressionNext1(self, next_node, trace_collection):
        value = self.subnode_value

        if value.isKnownToBeIterableAtMin(1) and value.canPredictIterationValues():
            result = wrapExpressionWithSideEffects(
                new_node=value.getIterationValue(0),
                old_node=value,
                side_effects=value.getIterationValueRange(1, None),
            )

            return False, (
                result,
                "new_expression",
                "Predicted 'next' value from iteration.",
            )

        # TODO: This is only true for a few value types, use type shape to tell if
        # it might escape or raise.
        self.onContentEscapes(trace_collection)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return True, (next_node, None, None)

    def isKnownToBeIterable(self, count):
        if count is None:
            return True

        iter_length = self.subnode_value.getIterationLength()
        return iter_length == count

    def isKnownToBeIterableAtMin(self, count):
        assert type(count) is int

        iter_length = self.subnode_value.getIterationMinLength()
        return iter_length is not None and count <= iter_length

    def getIterationLength(self):
        return self.subnode_value.getIterationLength()

    def canPredictIterationValues(self):
        return self.subnode_value.canPredictIterationValues()

    def getIterationValue(self, element_index):
        return self.subnode_value.getIterationValue(element_index)

    def getIterationHandle(self):
        return self.subnode_value.getIterationHandle()

    def extractSideEffects(self):
        # Iterator making is the side effect itself.
        value = self.subnode_value

        if value.isCompileTimeConstant() and value.isKnownToBeIterable(None):
            return ()
        else:
            return (self,)

    def mayHaveSideEffects(self):
        value = self.subnode_value

        if value.isCompileTimeConstant():
            return not value.isKnownToBeIterable(None)

        return True

    def mayRaiseException(self, exception_type):
        value = self.subnode_value

        if value.mayRaiseException(exception_type):
            return True

        if value.isKnownToBeIterable(None):
            return False

        return True

    def mayRaiseExceptionOperation(self):
        value = self.subnode_value

        return value.isKnownToBeIterable(None) is not True

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
                "cannot unpack non-iterable %s object" % (type(value).__name__)
            )


class StatementSpecialUnpackCheck(StatementChildHavingBase):
    kind = "STATEMENT_SPECIAL_UNPACK_CHECK"

    named_child = "iterator"

    __slots__ = ("count",)

    def __init__(self, iterator, count, source_ref):
        StatementChildHavingBase.__init__(self, value=iterator, source_ref=source_ref)

        self.count = int(count)

    def getDetails(self):
        return {"count": self.getCount()}

    def getCount(self):
        return self.count

    def computeStatement(self, trace_collection):
        iterator = trace_collection.onExpression(self.subnode_iterator)

        if iterator.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        if iterator.willRaiseException(BaseException):
            from .NodeMakingHelpers import (
                makeStatementExpressionOnlyReplacementNode,
            )

            result = makeStatementExpressionOnlyReplacementNode(
                expression=iterator, node=self
            )

            return (
                result,
                "new_raise",
                """\
Explicit raise already raises implicitly building exception type.""",
            )

        if (
            iterator.isExpressionTempVariableRef()
            and iterator.variable_trace.isAssignTrace()
        ):

            iterator = iterator.variable_trace.getAssignNode().subnode_source

            current_index = trace_collection.getIteratorNextCount(iterator)
        else:
            current_index = None

        if current_index is not None:
            iter_length = iterator.getIterationLength()

            if iter_length is not None:
                # Remove the check if it can be decided at compile time.
                if current_index == iter_length:
                    return (
                        None,
                        "new_statements",
                        """\
Determined iteration end check to be always true.""",
                    )
                else:
                    result = makeRaiseExceptionReplacementStatement(
                        statement=self,
                        exception_type="ValueError",
                        exception_value="too many values to unpack"
                        if python_version < 0x300
                        else "too many values to unpack (expected %d)"
                        % self.getCount(),
                    )

                    trace_collection.onExceptionRaiseExit(TypeError)

                    return (
                        result,
                        "new_raise",
                        """\
Determined iteration end check to always raise.""",
                    )

        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def getStatementNiceName():
        return "iteration check statement"


class ExpressionBuiltinIter2(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_ITER2"

    named_children = ("callable_arg", "sentinel")

    def __init__(self, callable_arg, sentinel, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values={"callable_arg": callable_arg, "sentinel": sentinel},
            source_ref=source_ref,
        )

    @staticmethod
    def getTypeShape():
        # TODO: This could be more specific.
        return tshape_iterator

    def computeExpression(self, trace_collection):
        # TODO: The "callable" should be investigated here, maybe it is not
        # really callable, or raises an exception.

        return self, None, None

    def computeExpressionIter1(self, iter_node, trace_collection):
        return self, "new_builtin", "Eliminated useless iterator creation."


class ExpressionAsyncIter(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_ASYNC_ITER"

    def computeExpression(self, trace_collection):
        value = self.subnode_value

        return value.computeExpressionAsyncIter(
            iter_node=self, trace_collection=trace_collection
        )

    def isKnownToBeIterable(self, count):
        if count is None:
            return True

        # TODO: Should ask value if it is.
        return None

    def getIterationLength(self):
        return self.subnode_value.getIterationLength()

    def extractSideEffects(self):
        # Iterator making is the side effect itself.
        if self.subnode_value.isCompileTimeConstant():
            return ()
        else:
            return (self,)

    def mayHaveSideEffects(self):
        if self.subnode_value.isCompileTimeConstant():
            return self.subnode_value.isKnownToBeIterable(None)

        return True

    def mayRaiseException(self, exception_type):
        value = self.subnode_value

        if value.mayRaiseException(exception_type):
            return True

        if value.isKnownToBeIterable(None):
            return False

        return True

    def isKnownToBeIterableAtMin(self, count):
        assert type(count) is int

        iter_length = self.subnode_value.getIterationMinLength()
        return iter_length is not None and iter_length < count

    def onRelease(self, trace_collection):
        # print "onRelease", self
        pass


class ExpressionAsyncNext(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_ASYNC_NEXT"

    def __init__(self, value, source_ref):
        ExpressionBuiltinSingleArgBase.__init__(
            self, value=value, source_ref=source_ref
        )

    def computeExpression(self, trace_collection):
        # TODO: Predict iteration result if possible via SSA variable trace of
        # the iterator state.

        # Assume exception is possible. TODO: We might query the next from the
        # source with a computeExpressionAsyncNext slot, but we delay that.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None
