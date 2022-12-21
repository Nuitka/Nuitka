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
""" Node for constant expressions. Can be all common built-in types.

"""

import sys
from abc import abstractmethod

from nuitka import Options
from nuitka.__past__ import (
    GenericAlias,
    UnionType,
    iterItems,
    long,
    unicode,
    xrange,
)
from nuitka.Builtins import (
    builtin_anon_values,
    builtin_exception_values_list,
    builtin_named_values,
)
from nuitka.Constants import (
    getUnhashableConstant,
    isConstant,
    isHashable,
    isMutable,
    the_empty_dict,
    the_empty_frozenset,
    the_empty_list,
    the_empty_set,
    the_empty_tuple,
    the_empty_unicode,
)
from nuitka.PythonVersions import python_version
from nuitka.Tracing import optimization_logger

from .ExpressionBases import CompileTimeConstantExpressionBase
from .ExpressionShapeMixins import (
    ExpressionBoolShapeExactMixin,
    ExpressionBytearrayShapeExactMixin,
    ExpressionBytesShapeExactMixin,
    ExpressionComplexShapeExactMixin,
    ExpressionDictShapeExactMixin,
    ExpressionEllipsisShapeExactMixin,
    ExpressionFloatShapeExactMixin,
    ExpressionFrozensetShapeExactMixin,
    ExpressionIntShapeExactMixin,
    ExpressionListShapeExactMixin,
    ExpressionLongShapeExactMixin,
    ExpressionNoneShapeExactMixin,
    ExpressionSetShapeExactMixin,
    ExpressionSliceShapeExactMixin,
    ExpressionStrShapeExactMixin,
    ExpressionTupleShapeExactMixin,
    ExpressionUnicodeShapeExactMixin,
)
from .IterationHandles import (
    ConstantBytearrayIterationHandle,
    ConstantBytesIterationHandle,
    ConstantDictIterationHandle,
    ConstantFrozensetIterationHandle,
    ConstantListIterationHandle,
    ConstantRangeIterationHandle,
    ConstantSetIterationHandle,
    ConstantStrIterationHandle,
    ConstantTupleIterationHandle,
    ConstantUnicodeIterationHandle,
)
from .NodeMakingHelpers import (
    makeRaiseExceptionReplacementExpression,
    wrapExpressionWithSideEffects,
)
from .shapes.BuiltinTypeShapes import (
    tshape_namedtuple,
    tshape_type,
    tshape_xrange,
)


class ExpressionConstantUntrackedRefBase(CompileTimeConstantExpressionBase):
    __slots__ = ("constant",)

    def __init__(self, constant, source_ref):
        CompileTimeConstantExpressionBase.__init__(self, source_ref)

        self.constant = constant

    def finalize(self):
        del self.parent
        del self.constant

    def __repr__(self):
        return "<Node %s value %r at %s>" % (
            self.kind,
            self.constant,
            self.source_ref.getAsString(),
        )

    def getDetails(self):
        return {"constant": self.constant}

    def getDetailsForDisplay(self):
        result = self.getDetails()

        if "constant" in result:
            result["constant"] = repr(result["constant"])

        return result

    @staticmethod
    def isExpressionConstantRef():
        return True

    def computeExpressionRaw(self, trace_collection):
        # Cannot compute any further, this is already the best.
        return self, None, None

    # Note: For computedExpressionResult to work, TODO: needed more generally?
    def computeExpression(self, trace_collection):
        # Cannot compute any further, this is already the best.
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        trace_collection.onExceptionRaiseExit(TypeError)

        # The arguments don't matter. All constant values cannot be called, and
        # we just need to make and error out of that.
        new_node = wrapExpressionWithSideEffects(
            new_node=makeRaiseExceptionReplacementExpression(
                expression=self,
                exception_type="TypeError",
                exception_value="'%s' object is not callable"
                % type(self.constant).__name__,
            ),
            old_node=call_node,
            side_effects=call_node.extractSideEffectsPreCall(),
        )

        return (
            new_node,
            "new_raise",
            "Predicted call of constant %s value to exception raise."
            % type(self.constant),
        )

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        return self.computeExpressionCall(
            call_node=call_node,
            call_args=call_args,
            call_kw=call_kw,
            trace_collection=trace_collection,
        )

    def getCompileTimeConstant(self):
        return self.constant

    # TODO: Push this to singletons for being static functions
    def getComparisonValue(self):
        return True, self.constant

    @staticmethod
    def getIterationHandle():
        return None

    def isMutable(self):
        # This is expected to be overloaded by child classes.
        assert False, self

    def isKnownToBeHashable(self):
        # This is expected to be overloaded by child classes.
        assert False, self

    def extractUnhashableNodeType(self):
        value = getUnhashableConstant(self.constant)

        if value is not None:
            return makeConstantRefNode(constant=type(value), source_ref=self.source_ref)

    @staticmethod
    def isNumberConstant():
        # This is expected to be overloaded by child classes that disagree, bool, int, long and float
        return False

    @staticmethod
    def isIndexConstant():
        # This is expected to be overloaded by child classes that disagree, bool, int, long and float
        return False

    def isIndexable(self):
        # TODO: Suspiciously this doesn't use isIndexConstant, which includes float, bug?
        return self.constant is None or self.isNumberConstant()

    def isKnownToBeIterable(self, count):
        if self.isIterableConstant():
            return count is None or len(self.constant) == count
        else:
            return False

    def isKnownToBeIterableAtMin(self, count):
        length = self.getIterationLength()

        return length is not None and length >= count

    def canPredictIterationValues(self):
        return self.isKnownToBeIterable(None)

    def getIterationValue(self, count):
        assert count < len(self.constant)

        return makeConstantRefNode(
            constant=self.constant[count], source_ref=self.source_ref
        )

    def getIterationValueRange(self, start, stop):
        return [
            makeConstantRefNode(constant=value, source_ref=self.source_ref)
            for value in self.constant[start:stop]
        ]

    def getIterationValues(self):
        source_ref = self.source_ref

        return tuple(
            makeConstantRefNode(
                constant=value, source_ref=source_ref, user_provided=self.user_provided
            )
            for value in self.constant
        )

    def getIntegerValue(self):
        if self.isNumberConstant():
            return int(self.constant)
        else:
            return None

    @abstractmethod
    def isIterableConstant(self):
        """Is the constant type iterable."""
        # This is expected to be overloaded by child classes, but it's actually wasteful
        # to use it, we should have overloads of using methods too.

    def getIterationLength(self):
        # This is expected to be overloaded by child classes if they are iterable
        assert not self.isIterableConstant(), self

        return None

    def getStrValue(self):
        return makeConstantRefNode(
            constant=str(self.constant),
            user_provided=False,
            source_ref=self.source_ref,
        )

    def computeExpressionIter1(self, iter_node, trace_collection):
        # Note, this is overloaded for all the others.
        assert not self.isIterableConstant()

        # TODO: Raise static exception.

        return iter_node, None, None


class ExpressionConstantRefBase(ExpressionConstantUntrackedRefBase):
    """Constants reference base class.

    Use this for cases, for which it makes sense to track origin, e.g.
    large lists are from computation or from user literals.
    """

    # Base classes can be abstract, pylint: disable=I0021,abstract-method

    __slots__ = ("user_provided",)

    def __init__(self, constant, user_provided, source_ref):
        ExpressionConstantUntrackedRefBase.__init__(
            self, constant=constant, source_ref=source_ref
        )

        self.user_provided = user_provided

        if not user_provided and Options.is_debug:
            try:
                if type(constant) in (str, unicode, bytes):
                    max_size = 1000
                elif type(constant) is xrange:
                    max_size = None
                else:
                    max_size = 256

                if max_size is not None and len(constant) > max_size:
                    optimization_logger.warning(
                        "Too large constant (%s %d) encountered at %s."
                        % (
                            type(constant),
                            len(constant),
                            source_ref.getAsString(),
                        )
                    )
            except TypeError:
                pass

    def getDetails(self):
        return {"constant": self.constant, "user_provided": self.user_provided}

    def __repr__(self):
        return "<Node %s value %r at %s %s>" % (
            self.kind,
            self.constant,
            self.source_ref.getAsString(),
            self.user_provided,
        )

    def getStrValue(self):
        try:
            return makeConstantRefNode(
                constant=str(self.constant),
                user_provided=self.user_provided,
                source_ref=self.source_ref,
            )
        except UnicodeEncodeError:
            # Unicode constants may not be possible to encode.
            return None


class ExpressionConstantNoneRef(
    ExpressionNoneShapeExactMixin, ExpressionConstantUntrackedRefBase
):
    kind = "EXPRESSION_CONSTANT_NONE_REF"

    __slots__ = ()

    def __init__(self, source_ref):
        ExpressionConstantUntrackedRefBase.__init__(
            self, constant=None, source_ref=source_ref
        )

    @staticmethod
    def getDetails():
        return {}

    @staticmethod
    def isMutable():
        return False

    @staticmethod
    def isIterableConstant():
        return False


class ExpressionConstantBoolRefBase(
    ExpressionBoolShapeExactMixin, ExpressionConstantUntrackedRefBase
):
    @staticmethod
    def isExpressionConstantBoolRef():
        return True

    @staticmethod
    def computeExpressionBool(trace_collection):
        # Best case already, None indicated no action.
        return None, None, None

    @staticmethod
    def getDetails():
        return {}

    @staticmethod
    def isMutable():
        return False

    @staticmethod
    def isKnownToBeHashable():
        return True

    @staticmethod
    def isNumberConstant():
        return True

    @staticmethod
    def isIndexConstant():
        return True

    @staticmethod
    def isIterableConstant():
        return False


class ExpressionConstantTrueRef(ExpressionConstantBoolRefBase):
    kind = "EXPRESSION_CONSTANT_TRUE_REF"

    __slots__ = ()

    def __init__(self, source_ref):
        ExpressionConstantBoolRefBase.__init__(
            self, constant=True, source_ref=source_ref
        )

    @staticmethod
    def getTruthValue():
        """Return known truth value."""

        return True

    @staticmethod
    def getIndexValue():
        return 1


class ExpressionConstantFalseRef(ExpressionConstantBoolRefBase):
    kind = "EXPRESSION_CONSTANT_FALSE_REF"

    __slots__ = ()

    def __init__(self, source_ref):
        ExpressionConstantBoolRefBase.__init__(
            self, constant=False, source_ref=source_ref
        )

    @staticmethod
    def getTruthValue():
        """Return known truth value."""

        return False

    @staticmethod
    def getIndexValue():
        return 0


class ExpressionConstantEllipsisRef(
    ExpressionEllipsisShapeExactMixin, ExpressionConstantUntrackedRefBase
):
    kind = "EXPRESSION_CONSTANT_ELLIPSIS_REF"

    __slots__ = ()

    def __init__(self, source_ref):
        ExpressionConstantUntrackedRefBase.__init__(
            self, constant=Ellipsis, source_ref=source_ref
        )

    @staticmethod
    def getDetails():
        return {}

    @staticmethod
    def isMutable():
        return False

    @staticmethod
    def isIterableConstant():
        return False


class ExpressionConstantDictRef(
    ExpressionDictShapeExactMixin, ExpressionConstantRefBase
):
    kind = "EXPRESSION_CONSTANT_DICT_REF"

    def __init__(self, constant, user_provided, source_ref):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantDictRef():
        return True

    @staticmethod
    def isMutable():
        return True

    @staticmethod
    def isKnownToBeHashable():
        return False

    @staticmethod
    def isIterableConstant():
        return True

    def getIterationHandle(self):
        return ConstantDictIterationHandle(self)

    def getIterationLength(self):
        return len(self.constant)

    def computeExpressionIter1(self, iter_node, trace_collection):
        result = makeConstantRefNode(
            constant=tuple(self.constant),
            user_provided=self.user_provided,
            source_ref=self.source_ref,
        )

        self.parent.replaceChild(self, result)
        self.finalize()

        return (
            iter_node,
            "new_constant",
            """Iteration over constant dict lowered to tuple.""",
        )

    def isMappingWithConstantStringKeys(self):
        return all(type(key) in (str, unicode) for key in self.constant)

    def getMappingStringKeyPairs(self):
        pairs = []

        for key, value in iterItems(self.constant):
            pairs.append(
                (
                    key,
                    makeConstantRefNode(
                        constant=value,
                        user_provided=self.user_provided,
                        source_ref=self.source_ref,
                    ),
                )
            )

        return pairs

    @staticmethod
    def getTruthValue():
        """Return known truth value.

        The empty dict is not allowed here, so we can hardcode it.
        """

        return True


class EmptyContainerMixin(object):
    __slots__ = ()

    def getDetails(self):
        return {"user_provided": self.user_provided}

    @staticmethod
    def getIterationLength():
        return 0

    @staticmethod
    def getTruthValue():
        """Return known truth value.

        The empty container is false, so we can hardcode it.
        """

        return False


class ExpressionConstantDictEmptyRef(EmptyContainerMixin, ExpressionConstantDictRef):
    kind = "EXPRESSION_CONSTANT_DICT_EMPTY_REF"

    __slots__ = ()

    def __init__(self, user_provided, source_ref):
        ExpressionConstantDictRef.__init__(
            self,
            constant=the_empty_dict,
            user_provided=user_provided,
            source_ref=source_ref,
        )


class ExpressionConstantTupleRef(
    ExpressionTupleShapeExactMixin, ExpressionConstantRefBase
):
    kind = "EXPRESSION_CONSTANT_TUPLE_REF"

    __slots__ = ()

    def __init__(self, constant, user_provided, source_ref):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantTupleRef():
        return True

    @staticmethod
    def isMutable():
        return False

    def isKnownToBeHashable(self):
        # There are a few exceptions, where non-mutable can be non-hashable, e.g. slice.
        return isHashable(self.constant)

    @staticmethod
    def isIterableConstant():
        return True

    def getIterationHandle(self):
        return ConstantTupleIterationHandle(self)

    def getIterationLength(self):
        return len(self.constant)

    def computeExpressionIter1(self, iter_node, trace_collection):
        # Note: Tuples are as good as it gets.
        return iter_node, None, None

    @staticmethod
    def getTruthValue():
        """Return known truth value.

        The empty dict is not allowed here, so we can hardcode it.
        """

        return True


class ExpressionConstantTupleMutableRef(ExpressionConstantTupleRef):
    kind = "EXPRESSION_CONSTANT_TUPLE_MUTABLE_REF"

    __slots__ = ()

    @staticmethod
    def isMutable():
        return True

    @staticmethod
    def isKnownToBeHashable():
        return False


class ExpressionConstantTupleEmptyRef(EmptyContainerMixin, ExpressionConstantTupleRef):
    kind = "EXPRESSION_CONSTANT_TUPLE_EMPTY_REF"

    __slots__ = ()

    def __init__(self, user_provided, source_ref):
        ExpressionConstantTupleRef.__init__(
            self,
            constant=the_empty_tuple,
            user_provided=user_provided,
            source_ref=source_ref,
        )


class ExpressionConstantListRef(
    ExpressionListShapeExactMixin, ExpressionConstantRefBase
):
    kind = "EXPRESSION_CONSTANT_LIST_REF"

    __slots__ = ()

    def __init__(self, constant, user_provided, source_ref):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantListRef():
        return True

    @staticmethod
    def isMutable():
        return True

    @staticmethod
    def isIterableConstant():
        return True

    def getIterationHandle(self):
        return ConstantListIterationHandle(self)

    def getIterationLength(self):
        return len(self.constant)

    def computeExpressionIter1(self, iter_node, trace_collection):
        result = makeConstantRefNode(
            constant=tuple(self.constant),
            user_provided=self.user_provided,
            source_ref=self.source_ref,
        )

        self.parent.replaceChild(self, result)
        self.finalize()

        return (
            iter_node,
            "new_constant",
            """Iteration over constant list lowered to tuple.""",
        )


class ExpressionConstantListEmptyRef(EmptyContainerMixin, ExpressionConstantListRef):
    kind = "EXPRESSION_CONSTANT_LIST_EMPTY_REF"

    __slots__ = ()

    def __init__(self, user_provided, source_ref):
        ExpressionConstantListRef.__init__(
            self,
            constant=the_empty_list,
            user_provided=user_provided,
            source_ref=source_ref,
        )


class ExpressionConstantSetRef(ExpressionSetShapeExactMixin, ExpressionConstantRefBase):
    kind = "EXPRESSION_CONSTANT_SET_REF"

    __slots__ = ()

    def __init__(self, constant, user_provided, source_ref):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantSetRef():
        return True

    @staticmethod
    def isMutable():
        return True

    @staticmethod
    def isKnownToBeHashable():
        return False

    @staticmethod
    def isIterableConstant():
        return True

    def getIterationHandle(self):
        return ConstantSetIterationHandle(self)

    def getIterationLength(self):
        return len(self.constant)

    def computeExpressionIter1(self, iter_node, trace_collection):
        result = makeConstantRefNode(
            constant=tuple(self.constant),
            user_provided=self.user_provided,
            source_ref=self.source_ref,
        )

        self.parent.replaceChild(self, result)
        self.finalize()

        return (
            iter_node,
            "new_constant",
            """Iteration over constant set lowered to tuple.""",
        )


class ExpressionConstantSetEmptyRef(EmptyContainerMixin, ExpressionConstantSetRef):
    kind = "EXPRESSION_CONSTANT_SET_EMPTY_REF"

    __slots__ = ()

    def __init__(self, user_provided, source_ref):
        ExpressionConstantSetRef.__init__(
            self,
            constant=the_empty_set,
            user_provided=user_provided,
            source_ref=source_ref,
        )


class ExpressionConstantFrozensetRef(
    ExpressionFrozensetShapeExactMixin, ExpressionConstantRefBase
):
    kind = "EXPRESSION_CONSTANT_FROZENSET_REF"

    __slots__ = ()

    def __init__(self, constant, user_provided, source_ref):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantFrozensetRef():
        return True

    @staticmethod
    def isMutable():
        return False

    @staticmethod
    def isIterableConstant():
        return True

    def getIterationHandle(self):
        return ConstantFrozensetIterationHandle(self)

    def getIterationLength(self):
        return len(self.constant)

    def computeExpressionIter1(self, iter_node, trace_collection):
        result = makeConstantRefNode(
            constant=tuple(self.constant),
            user_provided=self.user_provided,
            source_ref=self.source_ref,
        )

        self.parent.replaceChild(self, result)
        self.finalize()

        return (
            iter_node,
            "new_constant",
            """Iteration over constant frozenset lowered to tuple.""",
        )


class ExpressionConstantFrozensetEmptyRef(
    EmptyContainerMixin, ExpressionConstantFrozensetRef
):
    kind = "EXPRESSION_CONSTANT_FROZENSET_EMPTY_REF"

    __slots__ = ()

    def __init__(self, user_provided, source_ref):
        ExpressionConstantFrozensetRef.__init__(
            self,
            constant=the_empty_frozenset,
            user_provided=user_provided,
            source_ref=source_ref,
        )


class ExpressionConstantIntRef(
    ExpressionIntShapeExactMixin, ExpressionConstantUntrackedRefBase
):
    kind = "EXPRESSION_CONSTANT_INT_REF"

    __slots__ = ()

    def __init__(self, constant, source_ref):
        ExpressionConstantUntrackedRefBase.__init__(
            self, constant=constant, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantIntRef():
        return True

    @staticmethod
    def isMutable():
        return False

    @staticmethod
    def isNumberConstant():
        return True

    @staticmethod
    def isIndexConstant():
        return True

    def getIndexValue(self):
        return self.constant

    @staticmethod
    def isIterableConstant():
        return False


class ExpressionConstantLongRef(
    ExpressionLongShapeExactMixin, ExpressionConstantRefBase
):
    kind = "EXPRESSION_CONSTANT_LONG_REF"

    __slots__ = ()

    def __init__(self, constant, user_provided, source_ref):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantLongRef():
        return True

    @staticmethod
    def isMutable():
        return False

    @staticmethod
    def isNumberConstant():
        return True

    @staticmethod
    def isIndexConstant():
        return True

    def getIndexValue(self):
        # Use the int value if possible, otherwise that remains a long, which is
        # also OK, but often unnecessary.
        return int(self.constant)

    @staticmethod
    def isIterableConstant():
        return False


class ExpressionConstantStrRef(ExpressionStrShapeExactMixin, ExpressionConstantRefBase):
    kind = "EXPRESSION_CONSTANT_STR_REF"

    __slots__ = ()

    def __init__(self, constant, user_provided, source_ref):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantStrRef():
        return True

    @staticmethod
    def isMutable():
        return False

    @staticmethod
    def isIterableConstant():
        return True

    def getIterationHandle(self):
        return ConstantStrIterationHandle(self)

    def getIterationLength(self):
        return len(self.constant)

    def getStrValue(self):
        return self

    def getStringValue(self):
        return self.constant

    def computeExpressionIter1(self, iter_node, trace_collection):
        # Note: str are as good as it gets.
        return iter_node, None, None


class ExpressionConstantStrEmptyRef(EmptyContainerMixin, ExpressionConstantStrRef):
    kind = "EXPRESSION_CONSTANT_STR_EMPTY_REF"

    __slots__ = ()

    def __init__(self, user_provided, source_ref):
        ExpressionConstantStrRef.__init__(
            self,
            constant="",
            user_provided=user_provided,
            source_ref=source_ref,
        )


class ExpressionConstantUnicodeRef(
    ExpressionUnicodeShapeExactMixin, ExpressionConstantRefBase
):
    kind = "EXPRESSION_CONSTANT_UNICODE_REF"

    __slots__ = ()

    def __init__(self, constant, user_provided, source_ref):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantUnicodeRef():
        return True

    @staticmethod
    def isMutable():
        return False

    @staticmethod
    def isIterableConstant():
        return True

    def getIterationHandle(self):
        return ConstantUnicodeIterationHandle(self)

    def getIterationLength(self):
        return len(self.constant)

    def computeExpressionIter1(self, iter_node, trace_collection):
        # Note: unicode are as good as it gets
        return iter_node, None, None


class ExpressionConstantUnicodeEmptyRef(
    EmptyContainerMixin, ExpressionConstantUnicodeRef
):
    kind = "EXPRESSION_CONSTANT_UNICODE_EMPTY_REF"

    __slots__ = ()

    def __init__(self, user_provided, source_ref):
        ExpressionConstantUnicodeRef.__init__(
            self,
            constant=the_empty_unicode,
            user_provided=user_provided,
            source_ref=source_ref,
        )


class ExpressionConstantBytesRef(
    ExpressionBytesShapeExactMixin, ExpressionConstantRefBase
):
    kind = "EXPRESSION_CONSTANT_BYTES_REF"

    def __init__(self, constant, user_provided, source_ref):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantBytesRef():
        return True

    @staticmethod
    def isMutable():
        return False

    @staticmethod
    def isIterableConstant():
        return True

    def getIterationHandle(self):
        return ConstantBytesIterationHandle(self)

    def getIterationLength(self):
        return len(self.constant)

    def computeExpressionIter1(self, iter_node, trace_collection):
        # Note: bytes are as good as it gets
        return iter_node, None, None


class ExpressionConstantBytesEmptyRef(EmptyContainerMixin, ExpressionConstantBytesRef):
    kind = "EXPRESSION_CONSTANT_BYTES_EMPTY_REF"

    __slots__ = ()

    def __init__(self, user_provided, source_ref):
        ExpressionConstantBytesRef.__init__(
            self,
            constant=b"",
            user_provided=user_provided,
            source_ref=source_ref,
        )


class ExpressionConstantBytearrayRef(
    ExpressionBytearrayShapeExactMixin, ExpressionConstantRefBase
):
    kind = "EXPRESSION_CONSTANT_BYTEARRAY_REF"

    def __init__(self, constant, user_provided, source_ref):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantBytearrayRef():
        return True

    @staticmethod
    def isMutable():
        return True

    @staticmethod
    def isIterableConstant():
        return True

    def getIterationHandle(self):
        return ConstantBytearrayIterationHandle(self)

    def getIterationLength(self):
        return len(self.constant)

    def computeExpressionIter1(self, iter_node, trace_collection):
        result = makeConstantRefNode(
            constant=bytes(self.constant),
            user_provided=self.user_provided,
            source_ref=self.source_ref,
        )

        self.parent.replaceChild(self, result)
        self.finalize()

        return (
            iter_node,
            "new_constant",
            """Iteration over constant bytearray lowered to bytes.""",
        )


class ExpressionConstantFloatRef(
    ExpressionFloatShapeExactMixin, ExpressionConstantUntrackedRefBase
):
    kind = "EXPRESSION_CONSTANT_FLOAT_REF"

    __slots__ = ()

    def __init__(self, constant, source_ref):
        ExpressionConstantUntrackedRefBase.__init__(
            self, constant=constant, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantFloatRef():
        return True

    @staticmethod
    def isMutable():
        return False

    @staticmethod
    def isNumberConstant():
        return True

    @staticmethod
    def isIterableConstant():
        return False


class ExpressionConstantComplexRef(
    ExpressionComplexShapeExactMixin, ExpressionConstantUntrackedRefBase
):
    kind = "EXPRESSION_CONSTANT_COMPLEX_REF"

    __slots__ = ()

    def __init__(self, constant, source_ref):
        ExpressionConstantUntrackedRefBase.__init__(
            self, constant=constant, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantComplexRef():
        return True

    @staticmethod
    def isMutable():
        return False

    @staticmethod
    def isIterableConstant():
        return False

    # Overload what ExpressionComplexShapeExactMixin says, for a given instance we know all.
    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        return hasattr(0j, attribute_name)


class ExpressionConstantSliceRef(
    ExpressionSliceShapeExactMixin, ExpressionConstantUntrackedRefBase
):
    kind = "EXPRESSION_CONSTANT_SLICE_REF"

    __slots__ = ()

    def __init__(self, constant, source_ref):
        ExpressionConstantUntrackedRefBase.__init__(
            self, constant=constant, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantSliceRef():
        return True

    @staticmethod
    def isMutable():
        return False

    @staticmethod
    def isIterableConstant():
        return False


class ExpressionConstantXrangeRef(ExpressionConstantUntrackedRefBase):
    kind = "EXPRESSION_CONSTANT_XRANGE_REF"

    __slots__ = ()

    def __init__(self, constant, source_ref):
        ExpressionConstantUntrackedRefBase.__init__(
            self, constant=constant, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantXrangeRef():
        return True

    @staticmethod
    def getTypeShape():
        return tshape_xrange

    @staticmethod
    def isMutable():
        return False

    @staticmethod
    def isKnownToBeHashable():
        return True

    @staticmethod
    def isIterableConstant():
        return True

    def getIterationHandle(self):
        return ConstantRangeIterationHandle(self)

    def getIterationLength(self):
        return len(self.constant)

    def computeExpressionIter1(self, iter_node, trace_collection):
        # Note: xrange are as good as it gets.
        return iter_node, None, None


class ExpressionConstantTypeRef(ExpressionConstantUntrackedRefBase):
    kind = "EXPRESSION_CONSTANT_TYPE_REF"

    __slots__ = ()

    @staticmethod
    def isExpressionConstantTypeRef():
        return True

    @staticmethod
    def getTypeShape():
        return tshape_type

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        from nuitka.optimizations.OptimizeBuiltinCalls import (
            computeBuiltinCall,
        )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        new_node, tags, message = computeBuiltinCall(
            builtin_name=self.constant.__name__, call_node=call_node
        )

        return new_node, tags, message

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        return self.computeExpressionCall(
            call_node=call_node,
            call_args=call_args,
            call_kw=call_kw,
            trace_collection=trace_collection,
        )

    @staticmethod
    def isMutable():
        return False

    @staticmethod
    def isKnownToBeHashable():
        return True

    @staticmethod
    def isIterableConstant():
        return False

    @staticmethod
    def getTruthValue():
        return True


class ExpressionConstantTypeSubscriptableRef(ExpressionConstantTypeRef):
    kind = "EXPRESSION_CONSTANT_TYPE_SUBSCRIPTABLE_REF"

    __slots__ = ()

    def computeExpressionSubscript(self, lookup_node, subscript, trace_collection):
        if subscript.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=lookup_node,
                computation=lambda: self.getCompileTimeConstant()[
                    subscript.getCompileTimeConstant()
                ],
                description="Subscript of subscriptable type with constant value.",
            )

        # TODO: Not true, in fact these should become GenericAlias always.
        trace_collection.onExceptionRaiseExit(BaseException)

        return lookup_node, None, None


def makeConstantRefNode(constant, source_ref, user_provided=False):
    # This is dispatching per constant value and types, every case
    # to be a return statement, pylint: disable=too-many-branches,too-many-return-statements,too-many-statements

    # Dispatch based on constants first.
    if constant is None:
        return ExpressionConstantNoneRef(source_ref=source_ref)
    elif constant is True:
        return ExpressionConstantTrueRef(source_ref=source_ref)
    elif constant is False:
        return ExpressionConstantFalseRef(source_ref=source_ref)
    elif constant is Ellipsis:
        return ExpressionConstantEllipsisRef(source_ref=source_ref)

    # Next, dispatch based on type.
    constant_type = type(constant)

    if constant_type is int:
        return ExpressionConstantIntRef(constant=constant, source_ref=source_ref)
    elif constant_type is str:
        if constant:
            return ExpressionConstantStrRef(
                constant=constant,
                user_provided=user_provided,
                source_ref=source_ref,
            )
        else:
            return ExpressionConstantStrEmptyRef(
                user_provided=user_provided,
                source_ref=source_ref,
            )
    elif constant_type is float:
        return ExpressionConstantFloatRef(constant=constant, source_ref=source_ref)
    elif constant_type is long:
        return ExpressionConstantLongRef(
            constant=constant,
            user_provided=user_provided,
            source_ref=source_ref,
        )
    elif constant_type is unicode:
        if constant:
            return ExpressionConstantUnicodeRef(
                constant=constant,
                user_provided=user_provided,
                source_ref=source_ref,
            )
        else:
            return ExpressionConstantUnicodeEmptyRef(
                user_provided=user_provided,
                source_ref=source_ref,
            )
    elif constant_type is bytes:
        if constant:
            return ExpressionConstantBytesRef(
                constant=constant,
                user_provided=user_provided,
                source_ref=source_ref,
            )
        else:
            return ExpressionConstantBytesEmptyRef(
                user_provided=user_provided,
                source_ref=source_ref,
            )
    elif constant_type is dict:
        if constant:
            assert isConstant(constant), repr(constant)

            return ExpressionConstantDictRef(
                constant=constant,
                user_provided=user_provided,
                source_ref=source_ref,
            )
        else:
            return ExpressionConstantDictEmptyRef(
                user_provided=user_provided,
                source_ref=source_ref,
            )
    elif constant_type is tuple:
        if constant:
            assert isConstant(constant), repr(constant)

            if isMutable(constant):
                return ExpressionConstantTupleMutableRef(
                    constant=constant,
                    user_provided=user_provided,
                    source_ref=source_ref,
                )
            else:
                return ExpressionConstantTupleRef(
                    constant=constant,
                    user_provided=user_provided,
                    source_ref=source_ref,
                )
        else:
            return ExpressionConstantTupleEmptyRef(
                user_provided=user_provided,
                source_ref=source_ref,
            )
    elif constant_type is list:
        if constant:
            assert isConstant(constant), repr(constant)

            return ExpressionConstantListRef(
                constant=constant,
                user_provided=user_provided,
                source_ref=source_ref,
            )
        else:
            return ExpressionConstantListEmptyRef(
                user_provided=user_provided,
                source_ref=source_ref,
            )
    elif constant_type is set:
        if constant:
            assert isConstant(constant), repr(constant)

            return ExpressionConstantSetRef(
                constant=constant,
                user_provided=user_provided,
                source_ref=source_ref,
            )
        else:
            return ExpressionConstantSetEmptyRef(
                user_provided=user_provided,
                source_ref=source_ref,
            )
    elif constant_type is frozenset:
        if constant:
            assert isConstant(constant), repr(constant)

            return ExpressionConstantFrozensetRef(
                constant=constant,
                user_provided=user_provided,
                source_ref=source_ref,
            )
        else:
            return ExpressionConstantFrozensetEmptyRef(
                user_provided=user_provided,
                source_ref=source_ref,
            )
    elif constant_type is complex:
        return ExpressionConstantComplexRef(
            constant=constant,
            source_ref=source_ref,
        )
    elif constant_type is slice:
        return ExpressionConstantSliceRef(
            constant=constant,
            source_ref=source_ref,
        )
    elif constant_type is type:
        if python_version >= 0x390 and constant in (
            set,
            frozenset,
            tuple,
            list,
            dict,
        ):
            return ExpressionConstantTypeSubscriptableRef(
                constant=constant, source_ref=source_ref
            )

        return ExpressionConstantTypeRef(constant=constant, source_ref=source_ref)
    elif constant_type is xrange:
        return ExpressionConstantXrangeRef(
            constant=constant,
            source_ref=source_ref,
        )
    elif constant_type is bytearray:
        return ExpressionConstantBytearrayRef(
            constant=constant,
            user_provided=user_provided,
            source_ref=source_ref,
        )
    elif constant_type is GenericAlias:
        from .BuiltinTypeNodes import ExpressionConstantGenericAlias

        return ExpressionConstantGenericAlias(
            generic_alias=constant, source_ref=source_ref
        )
    elif constant_type is UnionType:
        from .BuiltinTypeNodes import ExpressionConstantUnionType

        return ExpressionConstantUnionType(union_type=constant, source_ref=source_ref)
    elif constant is sys.version_info:
        return ExpressionConstantSysVersionInfoRef(source_ref=source_ref)
    elif constant in builtin_anon_values:
        from .BuiltinRefNodes import ExpressionBuiltinAnonymousRef

        return ExpressionBuiltinAnonymousRef(
            builtin_name=builtin_anon_values[constant],
            source_ref=source_ref,
        )
    elif constant in builtin_named_values:
        from .BuiltinRefNodes import ExpressionBuiltinRef

        return ExpressionBuiltinRef(
            builtin_name=builtin_named_values[constant], source_ref=source_ref
        )
    elif constant in builtin_exception_values_list:
        from .BuiltinRefNodes import ExpressionBuiltinExceptionRef

        if constant is NotImplemented:
            exception_name = "NotImplemented"
        else:
            exception_name = constant.__name__

        return ExpressionBuiltinExceptionRef(
            exception_name=exception_name, source_ref=source_ref
        )
    else:
        # Missing constant type, ought to not happen, please report.
        assert False, (constant, constant_type)


class ExpressionConstantSysVersionInfoRef(ExpressionConstantUntrackedRefBase):
    kind = "EXPRESSION_CONSTANT_SYS_VERSION_INFO_REF"

    __slots__ = ()

    def __init__(self, source_ref):
        ExpressionConstantUntrackedRefBase.__init__(
            self, constant=sys.version_info, source_ref=source_ref
        )

    @staticmethod
    def getDetails():
        return {}

    @staticmethod
    def getTypeShape():
        return tshape_namedtuple

    @staticmethod
    def isMutable():
        return False

    @staticmethod
    def isKnownToBeHashable():
        return True

    @staticmethod
    def isIterableConstant():
        return True

    def getIterationHandle(self):
        return ConstantTupleIterationHandle(self)

    def getIterationLength(self):
        return len(self.constant)

    def computeExpressionIter1(self, iter_node, trace_collection):
        # For iteration, we are just a normal tuple.
        result = makeConstantRefNode(
            constant=tuple(self.constant),
            user_provided=True,
            source_ref=self.source_ref,
        )

        self.parent.replaceChild(self, result)
        self.finalize()

        return (
            iter_node,
            "new_constant",
            """Iteration over constant 'sys.version_info' lowered to tuple.""",
        )

    @staticmethod
    def getTruthValue():
        return True
