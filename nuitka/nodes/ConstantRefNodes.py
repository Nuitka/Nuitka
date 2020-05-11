#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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

from logging import warning

from nuitka.__past__ import (  # pylint: disable=I0021,redefined-builtin
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
    getConstantIterationLength,
    getUnhashableConstant,
    isConstant,
    isHashable,
    isIndexConstant,
    isIterableConstant,
    isMutable,
    isNumberConstant,
)
from nuitka.Options import isDebug

from .ExpressionBases import CompileTimeConstantExpressionBase
from .IterationHandles import (
    ConstantIndexableIterationHandle,
    ConstantSetAndDictIterationHandle,
)
from .NodeMakingHelpers import (
    getComputationResult,
    makeRaiseExceptionReplacementExpression,
    wrapExpressionWithSideEffects,
)
from .shapes.BuiltinTypeShapes import (
    tshape_bool,
    tshape_bytearray,
    tshape_bytes,
    tshape_complex,
    tshape_dict,
    tshape_ellipsis,
    tshape_float,
    tshape_frozenset,
    tshape_int,
    tshape_list,
    tshape_long,
    tshape_none,
    tshape_set,
    tshape_slice,
    tshape_str,
    tshape_tuple,
    tshape_type,
    tshape_unicode,
    tshape_xrange,
)


class ExpressionConstantRefBase(CompileTimeConstantExpressionBase):
    __slots__ = "constant", "user_provided"

    def __init__(self, constant, source_ref, user_provided=False):
        CompileTimeConstantExpressionBase.__init__(self, source_ref=source_ref)

        assert isConstant(constant), repr(constant)

        self.constant = constant

        # Memory saving method, have the attribute only where necessary.
        self.user_provided = user_provided

        if not user_provided and isDebug():
            try:
                if type(constant) in (str, unicode, bytes):
                    max_size = 1000
                elif type(constant) is xrange:
                    max_size = None
                else:
                    max_size = 256

                if max_size is not None and len(constant) > max_size:
                    warning(
                        "Too large constant (%s %d) encountered at %s.",
                        type(constant),
                        len(constant),
                        source_ref.getAsString(),
                    )
            except TypeError:
                pass

    def finalize(self):
        del self.parent
        del self.constant

    def __repr__(self):
        return "<Node %s value %r at %s %s>" % (
            self.kind,
            self.constant,
            self.source_ref.getAsString(),
            self.user_provided,
        )

    def getDetails(self):
        return {"constant": self.constant, "user_provided": self.user_provided}

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

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):

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

        trace_collection.onExceptionRaiseExit(TypeError)

        return (
            new_node,
            "new_raise",
            "Predicted call of constant value to exception raise.",
        )

    def getCompileTimeConstant(self):
        return self.constant

    getConstant = getCompileTimeConstant

    def getIterationHandle(self):
        if self.isIterableConstant():
            return ConstantIndexableIterationHandle(self)
        else:
            return None

    def isMutable(self):
        return isMutable(self.constant)

    def isKnownToBeHashable(self):
        return isHashable(self.constant)

    def extractUnhashableNode(self):
        value = getUnhashableConstant(self.constant)

        if value is not None:
            return makeConstantRefNode(constant=value, source_ref=self.source_ref)

    def isNumberConstant(self):
        return isNumberConstant(self.constant)

    def isIndexConstant(self):
        return isIndexConstant(self.constant)

    def isIndexable(self):
        return self.constant is None or self.isNumberConstant()

    def isKnownToBeIterable(self, count):
        if isIterableConstant(self.constant):
            return count is None or getConstantIterationLength(self.constant) == count
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
        source_ref = self.getSourceReference()

        return tuple(
            makeConstantRefNode(
                constant=value, source_ref=source_ref, user_provided=self.user_provided
            )
            for value in self.constant
        )

    def isMapping(self):
        return type(self.constant) is dict

    def isMappingWithConstantStringKeys(self):
        assert self.isMapping()

        for key in self.constant:
            if type(key) not in (str, unicode):
                return False
        return True

    def getMappingPairs(self):
        assert self.isMapping()

        pairs = []

        source_ref = self.getSourceReference()

        for key, value in iterItems(self.constant):
            pairs.append(
                makeConstantRefNode(constant=key, source_ref=source_ref),
                makeConstantRefNode(constant=value, source_ref=source_ref),
            )

        return pairs

    def getMappingStringKeyPairs(self):
        assert self.isMapping()

        pairs = []

        source_ref = self.getSourceReference()

        for key, value in iterItems(self.constant):
            pairs.append(
                (key, makeConstantRefNode(constant=value, source_ref=source_ref))
            )

        return pairs

    @staticmethod
    def isBoolConstant():
        return False

    def mayHaveSideEffects(self):
        # Constants have no side effects
        return False

    def extractSideEffects(self):
        # Constants have no side effects
        return ()

    def getIntegerValue(self):
        if self.isNumberConstant():
            return int(self.constant)
        else:
            return None

    def getIndexValue(self):
        if self.isIndexConstant():
            return int(self.constant)
        else:
            return None

    def getStringValue(self):
        if self.isStringConstant():
            return self.constant
        else:
            return None

    def getIterationLength(self):
        if isIterableConstant(self.constant):
            return getConstantIterationLength(self.constant)
        else:
            return None

    def isIterableConstant(self):
        return isIterableConstant(self.constant)

    def isUnicodeConstant(self):
        return type(self.constant) is unicode

    def isStringConstant(self):
        return type(self.constant) is str

    def getStrValue(self):
        if type(self.constant) is str:
            # Nothing to do.
            return self
        else:
            try:
                return makeConstantRefNode(
                    constant=str(self.constant),
                    user_provided=self.user_provided,
                    source_ref=self.getSourceReference(),
                )
            except UnicodeEncodeError:
                # Unicode constants may not be possible to encode.
                return None

    def computeExpressionIter1(self, iter_node, trace_collection):
        constant_type = type(self.constant)

        if constant_type in (list, set, frozenset, dict):
            result = makeConstantRefNode(
                constant=tuple(self.constant),
                user_provided=self.user_provided,
                source_ref=self.getSourceReference(),
            )

            self.parent.replaceChild(self, result)
            self.finalize()

            return (
                iter_node,
                "new_constant",
                """\
Iteration over constant %s changed to tuple."""
                % constant_type.__name__,
            )

        if not isIterableConstant(self.constant):
            # An exception may be raised.
            trace_collection.onExceptionRaiseExit(TypeError)

            return getComputationResult(
                node=iter_node,
                computation=lambda: iter_node.simulator(self.constant),
                description="Iteration of non-iterable constant.",
            )

        return iter_node, None, None


class ExpressionConstantNoneRef(ExpressionConstantRefBase):
    kind = "EXPRESSION_CONSTANT_NONE_REF"

    __slots__ = ()

    def __init__(self, source_ref, user_provided=False):
        ExpressionConstantRefBase.__init__(
            self, constant=None, user_provided=user_provided, source_ref=source_ref
        )

    def getDetails(self):
        return {}

    def getTypeShape(self):
        return tshape_none


class ExpressionConstantBoolRefBase(ExpressionConstantRefBase):
    @staticmethod
    def isBoolConstant():
        return True

    def computeExpressionBool(self, trace_collection):
        # Best case already.
        pass

    def getDetails(self):
        return {}

    def getTypeShape(self):
        return tshape_bool


class ExpressionConstantTrueRef(ExpressionConstantBoolRefBase):
    kind = "EXPRESSION_CONSTANT_TRUE_REF"

    __slots__ = ()

    def __init__(self, source_ref, user_provided=False):
        ExpressionConstantBoolRefBase.__init__(
            self, constant=True, user_provided=user_provided, source_ref=source_ref
        )


class ExpressionConstantFalseRef(ExpressionConstantBoolRefBase):
    kind = "EXPRESSION_CONSTANT_FALSE_REF"

    __slots__ = ()

    def __init__(self, source_ref, user_provided=False):
        ExpressionConstantBoolRefBase.__init__(
            self, constant=False, user_provided=user_provided, source_ref=source_ref
        )


class ExpressionConstantEllipsisRef(ExpressionConstantRefBase):
    kind = "EXPRESSION_CONSTANT_ELLIPSIS_REF"

    __slots__ = ()

    def __init__(self, source_ref, user_provided=False):
        ExpressionConstantRefBase.__init__(
            self, constant=Ellipsis, user_provided=user_provided, source_ref=source_ref
        )

    def getDetails(self):
        return {}

    def getTypeShape(self):
        return tshape_ellipsis


class ExpressionConstantDictRef(ExpressionConstantRefBase):
    kind = "EXPRESSION_CONSTANT_DICT_REF"

    def __init__(self, source_ref, constant, user_provided=False):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantDictRef():
        return True

    def getTypeShape(self):
        return tshape_dict

    def hasShapeDictionaryExact(self):
        return True

    def getIterationHandle(self):
        return ConstantSetAndDictIterationHandle(self)


class ExpressionConstantTupleRef(ExpressionConstantRefBase):
    kind = "EXPRESSION_CONSTANT_TUPLE_REF"

    __slots__ = ()

    def __init__(self, source_ref, constant, user_provided=False):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantTupleRef():
        return True

    def getTypeShape(self):
        return tshape_tuple


the_empty_tuple = ()


class ExpressionConstantTupleEmptyRef(ExpressionConstantTupleRef):
    kind = "EXPRESSION_CONSTANT_TUPLE_EMPTY_REF"

    __slots__ = ()

    def __init__(self, source_ref, user_provided=False):
        ExpressionConstantTupleRef.__init__(
            self,
            constant=the_empty_tuple,
            user_provided=user_provided,
            source_ref=source_ref,
        )

    def getDetails(self):
        return {}


class ExpressionConstantListRef(ExpressionConstantRefBase):
    kind = "EXPRESSION_CONSTANT_LIST_REF"

    __slots__ = ()

    def __init__(self, source_ref, constant, user_provided=False):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantListRef():
        return True

    def getTypeShape(self):
        return tshape_list


the_empty_list = []


class ExpressionConstantListEmptyRef(ExpressionConstantListRef):
    kind = "EXPRESSION_CONSTANT_LIST_EMPTY_REF"

    __slots__ = ()

    def __init__(self, source_ref, user_provided=False):
        ExpressionConstantListRef.__init__(
            self,
            constant=the_empty_list,
            user_provided=user_provided,
            source_ref=source_ref,
        )

    def getDetails(self):
        return {}


class ExpressionConstantSetRef(ExpressionConstantRefBase):
    kind = "EXPRESSION_CONSTANT_SET_REF"

    __slots__ = ()

    def __init__(self, source_ref, constant, user_provided=False):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantSetRef():
        return True

    def getTypeShape(self):
        return tshape_set

    def getIterationHandle(self):
        return ConstantSetAndDictIterationHandle(self)


the_empty_set = set()


class ExpressionConstantSetEmptyRef(ExpressionConstantSetRef):
    kind = "EXPRESSION_CONSTANT_SET_EMPTY_REF"

    __slots__ = ()

    def __init__(self, source_ref, user_provided=False):
        ExpressionConstantSetRef.__init__(
            self,
            constant=the_empty_set,
            user_provided=user_provided,
            source_ref=source_ref,
        )

    def getDetails(self):
        return {}


class ExpressionConstantFrozensetRef(ExpressionConstantRefBase):
    kind = "EXPRESSION_CONSTANT_FROZENSET_REF"

    __slots__ = ()

    def __init__(self, source_ref, constant, user_provided=False):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantFrozensetRef():
        return True

    def getTypeShape(self):
        return tshape_frozenset


the_empty_frozenset = frozenset()


class ExpressionConstantFrozensetEmptyRef(ExpressionConstantFrozensetRef):
    kind = "EXPRESSION_CONSTANT_FROZENSET_EMPTY_REF"

    __slots__ = ()

    def __init__(self, source_ref, user_provided=False):
        ExpressionConstantFrozensetRef.__init__(
            self,
            constant=the_empty_frozenset,
            user_provided=user_provided,
            source_ref=source_ref,
        )

    def getDetails(self):
        return {}


class ExpressionConstantIntRef(ExpressionConstantRefBase):
    kind = "EXPRESSION_CONSTANT_INT_REF"

    __slots__ = ()

    def __init__(self, source_ref, constant, user_provided=False):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantIntRef():
        return True

    def getTypeShape(self):
        return tshape_int


class ExpressionConstantLongRef(ExpressionConstantRefBase):
    kind = "EXPRESSION_CONSTANT_LONG_REF"

    __slots__ = ()

    def __init__(self, source_ref, constant, user_provided=False):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantLongRef():
        return True

    def getTypeShape(self):
        return tshape_long


class ExpressionConstantStrRef(ExpressionConstantRefBase):
    kind = "EXPRESSION_CONSTANT_STR_REF"

    __slots__ = ()

    def __init__(self, source_ref, constant, user_provided=False):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantStrRef():
        return True

    def getTypeShape(self):
        return tshape_str


class ExpressionConstantUnicodeRef(ExpressionConstantRefBase):
    kind = "EXPRESSION_CONSTANT_UNICODE_REF"

    __slots__ = ()

    def __init__(self, source_ref, constant, user_provided=False):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantUnicodeRef():
        return True

    def getTypeShape(self):
        return tshape_unicode


class ExpressionConstantBytesRef(ExpressionConstantRefBase):
    kind = "EXPRESSION_CONSTANT_BYTES_REF"

    def __init__(self, source_ref, constant, user_provided=False):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantBytesRef():
        return True

    def getTypeShape(self):
        return tshape_bytes


class ExpressionConstantBytearrayRef(ExpressionConstantRefBase):
    kind = "EXPRESSION_CONSTANT_BYTEARRAY_REF"

    def __init__(self, source_ref, constant, user_provided=False):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantBytearrayRef():
        return True

    def getTypeShape(self):
        return tshape_bytearray


class ExpressionConstantFloatRef(ExpressionConstantRefBase):
    kind = "EXPRESSION_CONSTANT_FLOAT_REF"

    __slots__ = ()

    def __init__(self, source_ref, constant, user_provided=False):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantFloatRef():
        return True

    def getTypeShape(self):
        return tshape_float


class ExpressionConstantComplexRef(ExpressionConstantRefBase):
    kind = "EXPRESSION_CONSTANT_COMPLEX_REF"

    __slots__ = ()

    def __init__(self, source_ref, constant, user_provided=False):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantComplexRef():
        return True

    def getTypeShape(self):
        return tshape_complex


class ExpressionConstantSliceRef(ExpressionConstantRefBase):
    kind = "EXPRESSION_CONSTANT_SLICE_REF"

    __slots__ = ()

    def __init__(self, source_ref, constant, user_provided=False):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantSliceRef():
        return True

    def getTypeShape(self):
        return tshape_slice


class ExpressionConstantXrangeRef(ExpressionConstantRefBase):
    kind = "EXPRESSION_CONSTANT_XRANGE_REF"

    __slots__ = ()

    def __init__(self, source_ref, constant, user_provided=False):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantXrangeRef():
        return True

    def getTypeShape(self):
        return tshape_xrange


class ExpressionConstantTypeRef(ExpressionConstantRefBase):
    kind = "EXPRESSION_CONSTANT_TYPE_REF"

    __slots__ = ()

    def __init__(self, source_ref, constant, user_provided=False):
        ExpressionConstantRefBase.__init__(
            self, constant=constant, user_provided=user_provided, source_ref=source_ref
        )

    @staticmethod
    def isExpressionConstantTypeRef():
        return True

    def getTypeShape(self):
        return tshape_type

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        from nuitka.optimizations.OptimizeBuiltinCalls import computeBuiltinCall

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        new_node, tags, message = computeBuiltinCall(
            builtin_name=self.constant.__name__, call_node=call_node
        )

        return new_node, tags, message


the_empty_dict = {}


class ExpressionConstantDictEmptyRef(ExpressionConstantDictRef):
    kind = "EXPRESSION_CONSTANT_DICT_EMPTY_REF"

    __slots__ = ()

    def __init__(self, source_ref, user_provided=False):
        ExpressionConstantDictRef.__init__(
            self,
            constant=the_empty_dict,
            user_provided=user_provided,
            source_ref=source_ref,
        )

    def getDetails(self):
        return {}


def makeConstantRefNode(constant, source_ref, user_provided=False):
    # This is dispatching per constant value and types, every case
    # to be a return statement, pylint: disable=too-many-branches,too-many-return-statements

    # Dispatch based on constants first.
    if constant is None:
        return ExpressionConstantNoneRef(
            source_ref=source_ref, user_provided=user_provided
        )
    elif constant is True:
        return ExpressionConstantTrueRef(
            source_ref=source_ref, user_provided=user_provided
        )
    elif constant is False:
        return ExpressionConstantFalseRef(
            source_ref=source_ref, user_provided=user_provided
        )
    elif constant is Ellipsis:
        return ExpressionConstantEllipsisRef(
            source_ref=source_ref, user_provided=user_provided
        )
    else:
        # Next, dispatch based on type.
        constant_type = type(constant)

        if constant_type is int:
            return ExpressionConstantIntRef(
                source_ref=source_ref, constant=constant, user_provided=user_provided
            )
        elif constant_type is str:
            return ExpressionConstantStrRef(
                source_ref=source_ref, constant=constant, user_provided=user_provided
            )
        elif constant_type is float:
            return ExpressionConstantFloatRef(
                source_ref=source_ref, constant=constant, user_provided=user_provided
            )
        elif constant_type is long:
            return ExpressionConstantLongRef(
                source_ref=source_ref, constant=constant, user_provided=user_provided
            )
        elif constant_type is unicode:
            return ExpressionConstantUnicodeRef(
                source_ref=source_ref, constant=constant, user_provided=user_provided
            )
        elif constant_type is bytes:
            return ExpressionConstantBytesRef(
                source_ref=source_ref, constant=constant, user_provided=user_provided
            )
        elif constant_type is dict:
            if constant:
                return ExpressionConstantDictRef(
                    source_ref=source_ref,
                    constant=constant,
                    user_provided=user_provided,
                )
            else:
                return ExpressionConstantDictEmptyRef(
                    source_ref=source_ref, user_provided=user_provided
                )
        elif constant_type is tuple:
            if constant:
                return ExpressionConstantTupleRef(
                    source_ref=source_ref,
                    constant=constant,
                    user_provided=user_provided,
                )
            else:
                return ExpressionConstantTupleEmptyRef(
                    source_ref=source_ref, user_provided=user_provided
                )
        elif constant_type is list:
            if constant:
                return ExpressionConstantListRef(
                    source_ref=source_ref,
                    constant=constant,
                    user_provided=user_provided,
                )
            else:
                return ExpressionConstantListEmptyRef(
                    source_ref=source_ref, user_provided=user_provided
                )
        elif constant_type is set:
            if constant:
                return ExpressionConstantSetRef(
                    source_ref=source_ref,
                    constant=constant,
                    user_provided=user_provided,
                )
            else:
                return ExpressionConstantSetEmptyRef(
                    source_ref=source_ref, user_provided=user_provided
                )
        elif constant_type is frozenset:
            if constant:
                return ExpressionConstantFrozensetRef(
                    source_ref=source_ref,
                    constant=constant,
                    user_provided=user_provided,
                )
            else:
                return ExpressionConstantFrozensetEmptyRef(
                    source_ref=source_ref, user_provided=user_provided
                )
        elif constant_type is complex:
            return ExpressionConstantComplexRef(
                source_ref=source_ref, constant=constant, user_provided=user_provided
            )
        elif constant_type is slice:
            return ExpressionConstantSliceRef(
                source_ref=source_ref, constant=constant, user_provided=user_provided
            )
        elif constant_type is type:
            return ExpressionConstantTypeRef(
                source_ref=source_ref, constant=constant, user_provided=user_provided
            )
        elif constant_type is xrange:
            return ExpressionConstantXrangeRef(
                source_ref=source_ref, constant=constant, user_provided=user_provided
            )
        elif constant_type is bytearray:
            return ExpressionConstantBytearrayRef(
                source_ref=source_ref, constant=constant, user_provided=user_provided
            )
        elif constant in builtin_anon_values:
            from .BuiltinRefNodes import ExpressionBuiltinAnonymousRef

            return ExpressionBuiltinAnonymousRef(
                source_ref=source_ref, builtin_name=builtin_anon_values[constant]
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
