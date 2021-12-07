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
"""Mixins for expressions that have specific shapes.

Providing derived implementation, such that e.g. for a given shape, shortcuts
are automatically implemented.
"""

from abc import abstractmethod

from nuitka.Constants import (
    the_empty_bytearray,
    the_empty_dict,
    the_empty_frozenset,
    the_empty_list,
    the_empty_set,
    the_empty_slice,
    the_empty_tuple,
)

from .NodeMakingHelpers import (
    makeConstantReplacementNode,
    makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue,
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
    tshape_int_or_long,
    tshape_list,
    tshape_long,
    tshape_none,
    tshape_set,
    tshape_slice,
    tshape_str,
    tshape_str_derived,
    tshape_str_or_unicode,
    tshape_str_or_unicode_derived,
    tshape_tuple,
    tshape_unicode,
    tshape_unicode_derived,
)


class ExpressionSpecificDerivedMixinBase(object):
    """Mixin that provides all shapes exactly false overloads.

    This is to be used as a base class for specific or derived shape
    mixins, such that they automatically provide false for all other exact
    shape checks except the one they care about.
    """

    __slots__ = ()

    @staticmethod
    def hasShapeNoneExact():
        return False

    @staticmethod
    def hasShapeBoolExact():
        return False

    @staticmethod
    def hasShapeDictionaryExact():
        return False

    @staticmethod
    def hasShapeListExact():
        return False

    @staticmethod
    def hasShapeSetExact():
        return False

    @staticmethod
    def hasShapeFrozesetExact():
        return False

    @staticmethod
    def hasShapeTupleExact():
        return False

    @staticmethod
    def hasShapeStrExact():
        return False

    @staticmethod
    def hasShapeUnicodeExact():
        return False

    @staticmethod
    def hasShapeStrOrUnicodeExact():
        return False

    @staticmethod
    def hasShapeBytesExact():
        return False

    @staticmethod
    def hasShapeBytearrayExact():
        return False

    @staticmethod
    def hasShapeFloatExact():
        return False

    @staticmethod
    def hasShapeComplexExact():
        return False

    @staticmethod
    def hasShapeIntExact():
        return False

    @staticmethod
    def hasShapeLongExact():
        return False

    @staticmethod
    def hasShapeSliceExact():
        return False


class ExpressionSpecificExactMixinBase(ExpressionSpecificDerivedMixinBase):
    """Mixin that provides attribute knowledge for exact type shapes.

    This is to be used as a base class for specific shape mixins,
    such that they automatically provide false for all other exact
    shape checks except the one they care about.
    """

    __slots__ = ()

    @staticmethod
    def hasShapeTrustedAttributes():
        return True

    @abstractmethod
    def isKnownToHaveAttribute(self, attribute_name):
        return True

    @abstractmethod
    def getKnownAttributeValue(self, attribute_name):
        """Can be used as isKnownToHaveAttribute is True"""

    def mayRaiseExceptionAttributeLookup(self, exception_type, attribute_name):
        # TODO: The exception_type is not checked, pylint: disable=unused-argument
        return not self.isKnownToHaveAttribute(attribute_name)

    @staticmethod
    def mayRaiseExceptionBool(exception_type):
        # We cannot raise anything, pylint: disable=unused-argument
        return False

    @staticmethod
    def mayHaveSideEffectsBool():
        return False


class ExpressionNonIterableTypeShapeMixin(object):
    """Mixin for nodes known to not be iterable."""

    __slots__ = ()

    @staticmethod
    def getIterationLength():
        return None

    @staticmethod
    def isKnownToBeIterable(count):
        # virtual method overload, pylint: disable=unused-argument
        return False

    @staticmethod
    def isKnownToBeIterableAtMin(count):
        # virtual method overload, pylint: disable=unused-argument
        return False

    @staticmethod
    def canPredictIterationValues():
        return False

    def computeExpressionIter1(self, iter_node, trace_collection):
        shape = self.getTypeShape()

        assert shape.hasShapeSlotIter() is False

        # An exception will be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
            template="'%s' object is not iterable",
            operation="iter",
            original_node=iter_node,
            value_node=self,
        )


class ExpressionIterableTypeShapeMixin(object):
    """Mixin for nodes known to not be iterable."""

    __slots__ = ()

    # Bad Implementation that the node can use, based on getIterationLength, which
    def isKnownToBeIterable(self, count):
        return count is None or self.getIterationLength() == count

    def isKnownToBeIterableAtMin(self, count):
        length = self.getIterationLength()

        return length is not None and length >= count

    def canPredictIterationValues(self):
        return self.isKnownToBeIterable(None)


class ExpressionDictShapeExactMixin(
    ExpressionIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    """Mixin for nodes with exact dictionary shape."""

    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_dict

    @staticmethod
    def hasShapeDictionaryExact():
        return True

    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        return hasattr(the_empty_dict, attribute_name)

    @staticmethod
    def getKnownAttributeValue(attribute_name):
        return getattr(the_empty_dict, attribute_name)

    @staticmethod
    def isKnownToBeHashable():
        return False

    def extractUnhashableNodeType(self):
        return makeConstantReplacementNode(
            constant=dict, node=self, user_provided=False
        )


class ExpressionListShapeExactMixin(
    ExpressionIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    """Mixin for nodes with exact list shape."""

    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_list

    @staticmethod
    def hasShapeListExact():
        return True

    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        return hasattr(the_empty_list, attribute_name)

    @staticmethod
    def getKnownAttributeValue(attribute_name):
        return getattr(the_empty_list, attribute_name)

    @staticmethod
    def isKnownToBeHashable():
        return False

    def extractUnhashableNodeType(self):
        return makeConstantReplacementNode(
            constant=list, node=self, user_provided=False
        )


class ExpressionFrozensetShapeExactMixin(
    ExpressionIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    """Mixin for nodes with exact frozenset shape."""

    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_frozenset

    @staticmethod
    def hasShapeListExact():
        return True

    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        return hasattr(the_empty_frozenset, attribute_name)

    @staticmethod
    def getKnownAttributeValue(attribute_name):
        return getattr(the_empty_frozenset, attribute_name)

    @staticmethod
    def isKnownToBeHashable():
        return True


class ExpressionSetShapeExactMixin(
    ExpressionIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    """Mixin for nodes with exact set shape."""

    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_set

    @staticmethod
    def hasShapeSetExact():
        return True

    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        return hasattr(the_empty_set, attribute_name)

    @staticmethod
    def getKnownAttributeValue(attribute_name):
        return getattr(the_empty_set, attribute_name)

    @staticmethod
    def isKnownToBeHashable():
        return False

    def extractUnhashableNodeType(self):
        return makeConstantReplacementNode(constant=set, node=self, user_provided=False)


class ExpressionTupleShapeExactMixin(
    ExpressionIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    """Mixin for nodes with exact tuple shape."""

    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_tuple

    @staticmethod
    def hasShapeSetExact():
        return True

    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        return hasattr(the_empty_tuple, attribute_name)

    @staticmethod
    def getKnownAttributeValue(attribute_name):
        return getattr(the_empty_tuple, attribute_name)

    @staticmethod
    def isKnownToBeHashable():
        return None


class ExpressionBoolShapeExactMixin(
    ExpressionNonIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    """Mixin for nodes with exact bool shape."""

    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_bool

    @staticmethod
    def hasShapeBoolExact():
        return True

    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        return hasattr(False, attribute_name)

    @staticmethod
    def getKnownAttributeValue(attribute_name):
        return getattr(False, attribute_name)

    @staticmethod
    def isKnownToBeHashable():
        return True


class ExpressionStrShapeExactMixin(
    ExpressionIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    """Mixin for nodes with exact str shape."""

    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_str

    @staticmethod
    def hasShapeStrExact():
        return True

    @staticmethod
    def hasShapeStrOrUnicodeExact():
        return True

    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        return hasattr("", attribute_name)

    @staticmethod
    def getKnownAttributeValue(attribute_name):
        return getattr("", attribute_name)

    @staticmethod
    def isKnownToBeHashable():
        return True


class ExpressionBytesShapeExactMixin(
    ExpressionIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    """Mixin for nodes with exact bytes shape."""

    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_bytes

    @staticmethod
    def hasShapeBytesExact():
        return True

    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        return hasattr(b"", attribute_name)

    @staticmethod
    def getKnownAttributeValue(attribute_name):
        return getattr(b"", attribute_name)

    @staticmethod
    def isKnownToBeHashable():
        return True


class ExpressionBytearrayShapeExactMixin(
    ExpressionIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    """Mixin for nodes with exact bytearray shape."""

    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_bytearray

    @staticmethod
    def hasShapeBytearrayExact():
        return True

    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        return hasattr(the_empty_bytearray, attribute_name)

    @staticmethod
    def getKnownAttributeValue(attribute_name):
        return getattr(the_empty_bytearray, attribute_name)

    @staticmethod
    def isKnownToBeHashable():
        return False

    def extractUnhashableNodeType(self):
        return makeConstantReplacementNode(
            constant=bytearray, node=self, user_provided=False
        )


class ExpressionUnicodeShapeExactMixin(
    ExpressionIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    """Mixin for nodes with exact unicode shape."""

    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_unicode

    @staticmethod
    def hasShapeUnicodeExact():
        return True

    @staticmethod
    def hasShapeStrOrUnicodeExact():
        return True

    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        return hasattr(u"", attribute_name)

    @staticmethod
    def getKnownAttributeValue(attribute_name):
        return getattr(u"", attribute_name)

    @staticmethod
    def isKnownToBeHashable():
        return True


if str is not bytes:
    ExpressionStrOrUnicodeExactMixin = ExpressionStrShapeExactMixin
else:

    class ExpressionStrOrUnicodeExactMixin(
        ExpressionIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
    ):
        """Mixin for nodes with str_or_unicode shape."""

        __slots__ = ()

        @staticmethod
        def getTypeShape():
            return tshape_str_or_unicode

        @staticmethod
        def hasShapeStrOrUnicodeExact():
            return True

        @staticmethod
        def isKnownToHaveAttribute(attribute_name):
            return hasattr(u"", attribute_name) and hasattr("", attribute_name)

        @staticmethod
        def getKnownAttributeValue(attribute_name):
            return getattr("", attribute_name)

        @staticmethod
        def isKnownToBeHashable():
            return True


class ExpressionFloatShapeExactMixin(
    ExpressionNonIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    """Mixin for nodes with exact float shape."""

    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_float

    @staticmethod
    def hasShapeFloatExact():
        return True

    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        return hasattr(0.0, attribute_name)

    @staticmethod
    def getKnownAttributeValue(attribute_name):
        return getattr(0.0, attribute_name)

    @staticmethod
    def isKnownToBeHashable():
        return True


class ExpressionIntShapeExactMixin(
    ExpressionNonIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    """Mixin for nodes with exact int shape."""

    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_int

    @staticmethod
    def hasShapeIntExact():
        return True

    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        return hasattr(0, attribute_name)

    @staticmethod
    def getKnownAttributeValue(attribute_name):
        return getattr(0, attribute_name)

    @staticmethod
    def isKnownToBeHashable():
        return True


class ExpressionLongShapeExactMixin(
    ExpressionNonIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    """Mixin for nodes with exact long shape."""

    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_long

    @staticmethod
    def hasShapeLongExact():
        return True

    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        return hasattr(tshape_long.typical_value, attribute_name)

    @staticmethod
    def getKnownAttributeValue(attribute_name):
        return getattr(tshape_long.typical_value, attribute_name)

    @staticmethod
    def isKnownToBeHashable():
        return True


if str is not bytes:
    ExpressionIntOrLongExactMixin = ExpressionIntShapeExactMixin
else:

    class ExpressionIntOrLongExactMixin(
        ExpressionNonIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
    ):
        """Mixin for nodes with int_or_long shape."""

        __slots__ = ()

        @staticmethod
        def getTypeShape():
            return tshape_int_or_long

        @staticmethod
        def isKnownToHaveAttribute(attribute_name):
            return hasattr(0, attribute_name) and hasattr(
                tshape_long.typical_value, attribute_name
            )

        @staticmethod
        def getKnownAttributeValue(attribute_name):
            return getattr(0, attribute_name)

        @staticmethod
        def isKnownToBeHashable():
            return True


class ExpressionEllipsisShapeExactMixin(
    ExpressionNonIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    """Mixin for nodes with exact ellipsis shape."""

    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_ellipsis

    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        return hasattr(Ellipsis, attribute_name)

    @staticmethod
    def getKnownAttributeValue(attribute_name):
        return getattr(Ellipsis, attribute_name)

    @staticmethod
    def isKnownToBeHashable():
        return True

    @staticmethod
    def getTruthValue():
        """Return known truth value."""

        return True


class ExpressionNoneShapeExactMixin(
    ExpressionNonIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    """Mixin for nodes with exact None shape."""

    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_none

    @staticmethod
    def hasShapeNoneExact():
        return True

    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        return hasattr(None, attribute_name)

    @staticmethod
    def getKnownAttributeValue(attribute_name):
        return getattr(None, attribute_name)

    @staticmethod
    def isKnownToBeHashable():
        return True

    @staticmethod
    def getTruthValue():
        """Return known truth value."""

        return False


class ExpressionComplexShapeExactMixin(
    ExpressionNonIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    """Mixin for nodes with exact complex shape."""

    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_complex

    @staticmethod
    def hasShapeComplexExact():
        return True

    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        # These vary with instances, constant values should not enter here.
        if attribute_name in ("imag", "real"):
            return False

        return hasattr(0j, attribute_name)

    @staticmethod
    def getKnownAttributeValue(attribute_name):
        return getattr(0j, attribute_name)

    @staticmethod
    def isKnownToBeHashable():
        return True


class ExpressionSliceShapeExactMixin(
    ExpressionNonIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    """Mixin for nodes with exact complex shape."""

    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_slice

    @staticmethod
    def hasShapeSliceExact():
        return True

    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        return hasattr(the_empty_slice, attribute_name)

    @staticmethod
    def getKnownAttributeValue(attribute_name):
        return getattr(the_empty_slice, attribute_name)

    @staticmethod
    def isKnownToBeHashable():
        return False


class ExpressionStrDerivedShapeMixin(ExpressionSpecificDerivedMixinBase):
    """Mixin for nodes with str derived shape."""

    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_str_derived


class ExpressionUnicodeDerivedShapeMixin(ExpressionSpecificDerivedMixinBase):
    """Mixin for nodes with unicode derived shape."""

    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_unicode_derived


if str is not bytes:
    ExpressionStrOrUnicodeDerivedShapeMixin = ExpressionUnicodeDerivedShapeMixin
else:

    class ExpressionStrOrUnicodeDerivedShapeMixin(ExpressionSpecificDerivedMixinBase):
        """Mixin for nodes with str or unicode derived shape."""

        __slots__ = ()

        @staticmethod
        def getTypeShape():
            return tshape_str_or_unicode_derived
