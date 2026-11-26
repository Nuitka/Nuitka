#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Mixins for expressions that have specific shapes.

Providing derived implementation, such that e.g. for a given shape, shortcuts
are automatically implemented.
"""

from abc import abstractmethod

from nuitka.__past__ import sentinel
from nuitka.Constants import (
    the_empty_bytearray,
    the_empty_dict,
    the_empty_frozendict,
    the_empty_frozenset,
    the_empty_list,
    the_empty_sentinel,
    the_empty_set,
    the_empty_slice,
    the_empty_tuple,
    the_empty_unicode,
)
from nuitka.PythonVersions import python_version

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
    tshape_frozendict,
    tshape_frozenset,
    tshape_int,
    tshape_int_or_long,
    tshape_list,
    tshape_long,
    tshape_none,
    tshape_sentinel,
    tshape_set,
    tshape_slice,
    tshape_str,
    tshape_str_derived,
    tshape_str_or_unicode,
    tshape_str_or_unicode_derived,
    tshape_tuple,
    tshape_type,
    tshape_unicode,
    tshape_unicode_derived,
)


class ExpressionSpecificDerivedMixinBase(object):
    """Base mixin returning 'False' for all exact shape checks."""

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
    def hasShapeFrozensetExact():
        return False

    @staticmethod
    def hasShapeFrozendictExact():
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

    @staticmethod
    def hasShapeTypeExact():
        return False


class ExpressionSpecificExactMixinBase(ExpressionSpecificDerivedMixinBase):
    """Base mixin providing attribute knowledge for exact type shapes."""

    __slots__ = ()

    @staticmethod
    def hasShapeTrustedAttributes():
        return True

    @abstractmethod
    def isKnownToHaveAttribute(self, attribute_name):
        return True

    @abstractmethod
    def getKnownAttributeValue(self, attribute_name):
        """Return known attribute value when 'isKnownToHaveAttribute' is 'True'."""

    def mayRaiseExceptionAttributeLookup(self, exception_type, attribute_name):
        # TODO: The exception_type is not checked, pylint: disable=unused-argument
        return not self.isKnownToHaveAttribute(attribute_name)

    @staticmethod
    def mayRaiseExceptionBool(exception_type):
        # pylint: disable=unused-argument
        return False

    @staticmethod
    def mayHaveSideEffectsBool():
        return False


class ExpressionNonIterableTypeShapeMixin(object):
    __slots__ = ()

    @staticmethod
    def getIterationLength():
        return None

    @staticmethod
    def isKnownToBeIterable(count):
        # pylint: disable=unused-argument
        return False

    @staticmethod
    def isKnownToBeIterableAtMin(count):
        # pylint: disable=unused-argument
        return False

    @staticmethod
    def canPredictIterationValues():
        return False

    def computeExpressionIter1(self, iter_node, trace_collection):
        shape = self.getTypeShape()

        assert shape.hasShapeSlotIter() is False

        trace_collection.onExceptionRaiseExit(BaseException)

        return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
            template="'%s' object is not iterable",
            operation="iter",
            original_node=iter_node,
            value_node=self,
        )


class ExpressionIterableTypeShapeMixin(object):
    __slots__ = ()

    @staticmethod
    def mayRaiseExceptionIter(exception_type):
        # pylint: disable=unused-argument
        return False

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

    # TODO: Make it really abstract to force all to take benefit of it.
    @staticmethod
    def getExpressionDictInConstant(value):
        # pylint: disable=unused-argument
        return None


class ExpressionListShapeExactMixin(
    ExpressionIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
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

    @staticmethod
    def isKnownToBeIndexable():
        return True

    def extractUnhashableNodeType(self):
        return makeConstantReplacementNode(
            constant=list, node=self, user_provided=False
        )


class ExpressionFrozensetShapeExactMixin(
    ExpressionIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_frozenset

    @staticmethod
    def hasShapeFrozensetExact():
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


class ExpressionFrozendictShapeExactMixin(
    ExpressionIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_frozendict

    @staticmethod
    def hasShapeFrozendictExact():
        return True

    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        return hasattr(the_empty_frozendict, attribute_name)

    @staticmethod
    def getKnownAttributeValue(attribute_name):
        return getattr(the_empty_frozendict, attribute_name)


class ExpressionSentinelShapeExactMixin(
    ExpressionNonIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_sentinel

    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        return hasattr(the_empty_sentinel, attribute_name)

    @staticmethod
    def getKnownAttributeValue(attribute_name):
        # Sentinel names and modules are instance-specific, so only expose
        # type-level values here.
        if attribute_name == "__class__":
            return sentinel

        return None

    @staticmethod
    def isKnownToBeHashable():
        return True

    @staticmethod
    def getTruthValue():
        return True


class ExpressionSetShapeExactMixin(
    ExpressionIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
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
    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_tuple

    @staticmethod
    def hasShapeTupleExact():
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

    @staticmethod
    def isKnownToBeIndexable():
        return True


class ExpressionBoolShapeExactMixin(
    ExpressionNonIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
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

    @staticmethod
    def isKnownToBeIndexable():
        return True


class ExpressionBytesShapeExactMixin(
    ExpressionIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
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

    @staticmethod
    def isKnownToBeIndexable():
        return True


class ExpressionBytearrayShapeExactMixin(
    ExpressionIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
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

    @staticmethod
    def isKnownToBeIndexable():
        return True

    def extractUnhashableNodeType(self):
        return makeConstantReplacementNode(
            constant=bytearray, node=self, user_provided=False
        )


class ExpressionUnicodeShapeExactMixin(
    ExpressionIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
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
        return hasattr(the_empty_unicode, attribute_name)

    @staticmethod
    def getKnownAttributeValue(attribute_name):
        return getattr(the_empty_unicode, attribute_name)

    @staticmethod
    def isKnownToBeHashable():
        return True

    @staticmethod
    def isKnownToBeIndexable():
        return True


if str is not bytes:
    ExpressionStrOrUnicodeExactMixin = ExpressionStrShapeExactMixin
else:

    class ExpressionStrOrUnicodeExactMixin(
        ExpressionIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
    ):
        __slots__ = ()

        @staticmethod
        def getTypeShape():
            return tshape_str_or_unicode

        @staticmethod
        def hasShapeStrOrUnicodeExact():
            return True

        @staticmethod
        def isKnownToHaveAttribute(attribute_name):
            return hasattr("", attribute_name) and hasattr(
                the_empty_unicode, attribute_name
            )

        @staticmethod
        def getKnownAttributeValue(attribute_name):
            return getattr("", attribute_name)

        @staticmethod
        def isKnownToBeHashable():
            return True

        @staticmethod
        def isKnownToBeIndexable():
            return True


class ExpressionFloatShapeExactMixin(
    ExpressionNonIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
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
        return True


class ExpressionNoneShapeExactMixin(
    ExpressionNonIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
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
        return False


class ExpressionComplexShapeExactMixin(
    ExpressionNonIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_complex

    @staticmethod
    def hasShapeComplexExact():
        return True

    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        # Real and imaginary parts are instance-specific.
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

    if python_version < 0x3C0:

        @staticmethod
        def isKnownToBeHashable():
            return False

        def extractUnhashableNodeType(self):
            return makeConstantReplacementNode(
                constant=slice, node=self, user_provided=False
            )


class ExpressionTypeShapeExactMixin(
    ExpressionNonIterableTypeShapeMixin, ExpressionSpecificExactMixinBase
):
    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_type

    @staticmethod
    def hasShapeTypeExact():
        return True

    @staticmethod
    def isKnownToHaveAttribute(attribute_name):
        return hasattr(type, attribute_name)

    @staticmethod
    def getKnownAttributeValue(attribute_name):
        return getattr(type, attribute_name)

    @staticmethod
    def isKnownToBeHashable():
        return True


class ExpressionStrDerivedShapeMixin(ExpressionSpecificDerivedMixinBase):
    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_str_derived

    @staticmethod
    def isKnownToBeIndexable():
        return True


class ExpressionUnicodeDerivedShapeMixin(ExpressionSpecificDerivedMixinBase):
    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_unicode_derived

    @staticmethod
    def isKnownToBeIndexable():
        return True


if str is not bytes:
    ExpressionStrOrUnicodeDerivedShapeMixin = ExpressionUnicodeDerivedShapeMixin
else:

    class ExpressionStrOrUnicodeDerivedShapeMixin(ExpressionSpecificDerivedMixinBase):
        __slots__ = ()

        @staticmethod
        def getTypeShape():
            return tshape_str_or_unicode_derived

        @staticmethod
        def isKnownToBeIndexable():
            return True


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
