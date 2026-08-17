#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Built-in iterator nodes.

These play a role in for loops, and in unpacking. They can something be
predicted to succeed or fail, in which case, code can become less complex.

The length of things is an important optimization issue for these to be
good.
"""

from nuitka.PythonVersions import python_version
from nuitka.specs import BuiltinParameterSpecs

from .BuiltinLenNodes import ExpressionBuiltinLen
from .ChildrenHavingMixins import (
    ChildHavingSequenceMixin,
    ChildHavingValuesTupleMixin,
    ChildrenHavingSequenceStartMixin,
    ChildrenHavingStrictOptionalValuesTupleMixin,
)
from .ExpressionBases import ExpressionBase, ExpressionBuiltinSingleArgBase
from .ExpressionBasesGenerated import ExpressionBuiltinIter2Base
from .NodeMakingHelpers import (
    makeRaiseExceptionReplacementStatement,
    makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue,
    wrapExpressionWithSideEffects,
)
from .shapes.BuiltinTypeShapes import tshape_list
from .shapes.IteratorShapes import tshape_iterator
from .StatementBasesGenerated import (
    StatementSpecialUnpackCheckBase,
    StatementSpecialUnpackCheckFromIteratedBase,
)
from .VariableRefNodes import ExpressionTempVariableRef


class ExpressionBuiltinIter1(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_BUILTIN_ITER1"

    simulator = iter

    @staticmethod
    def isExpressionBuiltinIter1():
        return True

    def computeExpression(self, trace_collection):
        return self.subnode_value.computeExpressionIter1(
            iter_node=self, trace_collection=trace_collection
        )

    def computeExpressionIter1(self, iter_node, trace_collection):
        # Iteration over an iterator is that iterator.

        return self, "new_builtin", "Eliminated useless iterator creation."

    def getTypeShape(self):
        result = self.subnode_value.getTypeShape().getShapeIter()

        if result is None:
            return tshape_iterator

        return result

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

        # TODO: This is only relevant for a few value types, use type shape to tell if
        # it might escape or raise.
        self.onContentEscapes(trace_collection)

        if value.mayHaveSideEffectsNext():
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


class ExpressionBuiltinEnumerateMixin(object):
    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_iterator

    def computeExpression(self, trace_collection):
        self.onContentEscapes(trace_collection)

        trace_collection.onControlFlowEscape(self)
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def isKnownToBeIterable(self, count):
        if count is None:
            return self.subnode_sequence.getTypeShape().hasShapeSlotIter()

        return self.subnode_sequence.isKnownToBeIterable(count)

    def isKnownToBeIterableAtMin(self, count):
        return self.subnode_sequence.isKnownToBeIterableAtMin(count)

    def getIterationLength(self):
        return self.subnode_sequence.getIterationLength()

    def mayRaiseException(self, exception_type):
        sequence = self.subnode_sequence

        if sequence.mayRaiseException(exception_type):
            return True

        if not sequence.getTypeShape().hasShapeSlotIter():
            return True

        return False


class ExpressionBuiltinEnumerate1(
    ExpressionBuiltinEnumerateMixin, ChildHavingSequenceMixin, ExpressionBase
):
    kind = "EXPRESSION_BUILTIN_ENUMERATE1"

    named_children = ("sequence",)

    def __init__(self, sequence, source_ref):
        ChildHavingSequenceMixin.__init__(self, sequence=sequence)

        ExpressionBase.__init__(self, source_ref)


class ExpressionBuiltinEnumerate2(
    ExpressionBuiltinEnumerateMixin, ChildrenHavingSequenceStartMixin, ExpressionBase
):
    kind = "EXPRESSION_BUILTIN_ENUMERATE2"

    named_children = ("sequence", "start")

    def __init__(self, sequence, start, source_ref):
        ChildrenHavingSequenceStartMixin.__init__(
            self,
            sequence=sequence,
            start=start,
        )

        ExpressionBase.__init__(self, source_ref)

    def mayRaiseException(self, exception_type):
        if ExpressionBuiltinEnumerateMixin.mayRaiseException(self, exception_type):
            return True

        if self.subnode_start.mayRaiseException(exception_type):
            return True

        return False


class ExpressionBuiltinZipMixin(object):
    __slots__ = ()

    if str is bytes:

        @staticmethod
        def getTypeShape():
            return tshape_list

    else:

        @staticmethod
        def getTypeShape():
            return tshape_iterator

    def computeExpression(self, trace_collection):
        self.onContentEscapes(trace_collection)

        trace_collection.onControlFlowEscape(self)
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def isKnownToBeIterable(self, count):
        if count is None:
            for value in self.subnode_values:
                if value.getTypeShape().hasShapeSlotIter() is False:
                    return False

            return True

        return self.isKnownToBeIterableAtMin(count)

    def isKnownToBeIterableAtMin(self, count):
        if not self.subnode_values:
            return count == 0

        for value in self.subnode_values:
            if not value.isKnownToBeIterableAtMin(count):
                return False

        return True

    def getIterationLength(self):
        lengths = []

        for value in self.subnode_values:
            iteration_length = value.getIterationLength()

            if iteration_length is None:
                return None

            lengths.append(iteration_length)

        if not lengths:
            return 0

        return min(lengths)

    def mayRaiseException(self, exception_type):
        for value in self.subnode_values:
            if value.mayRaiseException(exception_type):
                return True

            if value.getTypeShape().hasShapeSlotIter() is not True:
                return True

        return False


class ExpressionBuiltinZip(
    ExpressionBuiltinZipMixin, ChildHavingValuesTupleMixin, ExpressionBase
):
    kind = "EXPRESSION_BUILTIN_ZIP"

    named_children = ("values|tuple",)

    builtin_spec = BuiltinParameterSpecs.builtin_zip_spec

    def __init__(self, values, source_ref):
        ChildHavingValuesTupleMixin.__init__(self, values=values)

        ExpressionBase.__init__(self, source_ref)


class ExpressionBuiltinZip310(
    ExpressionBuiltinZipMixin,
    ChildrenHavingStrictOptionalValuesTupleMixin,
    ExpressionBase,
):
    kind = "EXPRESSION_BUILTIN_ZIP310"

    named_children = ("strict|optional", "values|tuple")

    python_version_spec = ">= 0x3A0"

    builtin_spec = BuiltinParameterSpecs.builtin_zip310_spec

    def __init__(self, strict, values, source_ref):
        ChildrenHavingStrictOptionalValuesTupleMixin.__init__(
            self,
            strict=strict,
            values=values,
        )

        ExpressionBase.__init__(self, source_ref)

    def mayRaiseException(self, exception_type):
        strict = self.subnode_strict

        if strict is not None and strict.mayRaiseException(exception_type):
            return True

        return ExpressionBuiltinZipMixin.mayRaiseException(self, exception_type)


class ExpressionBuiltinIterForUnpack(ExpressionBuiltinIter1):
    kind = "EXPRESSION_BUILTIN_ITER_FOR_UNPACK"

    def computeExpression(self, trace_collection):
        result = self.subnode_value.computeExpressionIter1(
            iter_node=self, trace_collection=trace_collection
        )

        result_node = result[0]

        # Rewrite exceptions to correct message.
        if (
            result_node.isExpressionRaiseException()
            and result_node.subnode_exception_type.isExpressionBuiltinMakeException()
            and result_node.subnode_exception_type.getExceptionName() == "TypeError"
        ):
            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                template="cannot unpack non-iterable %s object",
                operation="iter",
                original_node=self,
                value_node=self.subnode_value,
            )

        return result

    @staticmethod
    def simulator(value):
        try:
            return iter(value)
        except TypeError:
            raise TypeError(
                "cannot unpack non-iterable %s object" % (type(value).__name__)
            )


class StatementSpecialUnpackCheckFromIterated(
    StatementSpecialUnpackCheckFromIteratedBase
):
    kind = "STATEMENT_SPECIAL_UNPACK_CHECK_FROM_ITERATED"

    named_children = ("iterated_length",)
    node_attributes = ("count",)
    auto_compute_handling = "operation"

    def computeStatementOperation(self, trace_collection):
        if self.subnode_iterated_length.isCompileTimeConstant():
            iterated_length_value = (
                self.subnode_iterated_length.getCompileTimeConstant()
            )

            if iterated_length_value <= self.count:
                return (
                    None,
                    "new_statements",
                    lambda: "Determined iteration length check to be always true, because %d <= %d."
                    % (iterated_length_value, self.count),
                )
            else:
                result = makeRaiseExceptionReplacementStatement(
                    statement=self,
                    exception_type="ValueError",
                    exception_value=(
                        "too many values to unpack"
                        if python_version < 0x300
                        else "too many values to unpack (expected %d)" % self.count
                    ),
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


def makeStatementSpecialUnpackCheckFromIterated(
    tmp_iterated_variable, count, source_ref
):
    return StatementSpecialUnpackCheckFromIterated(
        iterated_length=ExpressionBuiltinLen(
            ExpressionTempVariableRef(
                variable=tmp_iterated_variable, source_ref=source_ref
            ),
            source_ref=source_ref,
        ),
        count=count,
        source_ref=source_ref,
    )


class StatementSpecialUnpackCheck(StatementSpecialUnpackCheckBase):
    kind = "STATEMENT_SPECIAL_UNPACK_CHECK"

    named_children = ("iterator",)
    node_attributes = ("count",)
    auto_compute_handling = "operation"

    def getCount(self):
        return self.count

    def computeStatementOperation(self, trace_collection):
        iterator = self.subnode_iterator

        if iterator.isExpressionTempVariableRef():
            iteration_source_node = iterator.variable_trace.getIterationSourceNode()

            if iteration_source_node is not None:
                if iteration_source_node.parent.isStatementAssignmentVariableIterator():
                    iterator_assign_node = iteration_source_node.parent

                    if iterator_assign_node.tmp_iterated_variable is not None:
                        result = makeStatementSpecialUnpackCheckFromIterated(
                            tmp_iterated_variable=iterator_assign_node.tmp_iterated_variable,
                            count=self.count,
                            source_ref=self.source_ref,
                        )

                        return trace_collection.computedStatementResult(
                            result,
                            change_tags="new_statements",
                            change_desc=lambda: "Iterator check of changed to iterated size check using '%s'."
                            % iterator_assign_node.tmp_iterated_variable.getName(),
                        )

        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def getStatementNiceName():
        return "iteration check statement"


class ExpressionBuiltinIter2(ExpressionBuiltinIter2Base):
    kind = "EXPRESSION_BUILTIN_ITER2"

    named_children = ("callable_arg", "sentinel")

    auto_compute_handling = "final"

    # TODO: The "callable" be investigated in a non-final
    # "auto_compute_handling" here, as maybe it is not really callable.

    @staticmethod
    def getTypeShape():
        # TODO: This could be more specific, this one is a fixed well known thing!
        return tshape_iterator

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


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
