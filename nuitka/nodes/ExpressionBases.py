#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Expression base classes.

These classes provide the generic base classes available for
expressions. They have a richer interface, mostly related to
abstract execution, and different from statements.

"""

from abc import abstractmethod

from nuitka import Options
from nuitka.__past__ import long

# TODO: Probably should separate building reports out.
from nuitka.code_generation.Reports import onMissingOverload
from nuitka.Constants import isCompileTimeConstantValue
from nuitka.PythonVersions import python_version

from .ChildrenHavingMixins import ChildHavingValueMixin
from .NodeBases import NodeBase
from .NodeMakingHelpers import (
    makeConstantReplacementNode,
    makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue,
    wrapExpressionWithNodeSideEffects,
)
from .shapes.BuiltinTypeShapes import (
    tshape_bool,
    tshape_bytes,
    tshape_dict,
    tshape_list,
    tshape_str,
    tshape_type,
    tshape_unicode,
)
from .shapes.StandardShapes import tshape_unknown


class ExpressionBase(NodeBase):
    # TODO: Maybe we can do this only for debug mode.
    __slots__ = ("code_generated",)

    @staticmethod
    def getTypeShape():
        return tshape_unknown

    def getValueShape(self):
        return self

    @staticmethod
    def isCompileTimeConstant():
        """Has a value that we can use at compile time.

        Yes or no. If it has such a value, simulations can be applied at
        compile time and e.g. operations or conditions, or even calls may
        be executed against it.
        """
        return False

    @staticmethod
    def getTruthValue():
        """Return known truth value. The "None" value indicates unknown."""

        return None

    @staticmethod
    def getComparisonValue():
        """Return known value used for compile time comparison. The "None" value indicates unknown."""

        return False, None

    @staticmethod
    def isMappingWithConstantStringKeys():
        """Is this a mapping with constant string keys. Used for call optimization."""
        return False

    @staticmethod
    def isKnownToBeIterable(count):
        """Can be iterated at all (count is None) or exactly count times.

        Yes or no. If it can be iterated a known number of times, it may
        be asked to unpack itself.
        """

        # Virtual method, pylint: disable=unused-argument
        return False

    @staticmethod
    def isKnownToBeIterableAtMin(count):
        # Virtual method, pylint: disable=unused-argument
        return False

    def getIterationLength(self):
        """Value that "len" or "PyObject_Size" would give, if known.

        Otherwise it is "None" to indicate unknown.
        """

        # Virtual method, pylint: disable=no-self-use
        return None

    def getIterationMinLength(self):
        """Value that "len" or "PyObject_Size" would give at minimum, if known.

        Otherwise it is "None" to indicate unknown.
        """

        return self.getIterationLength()

    @staticmethod
    def getStringValue():
        """Node as string value, if possible."""
        return None

    def getStrValue(self):
        """Value that "str" or "PyObject_Str" would give, if known.

        Otherwise it is "None" to indicate unknown. Users must not
        forget to take side effects into account, when replacing a
        node with its string value.
        """
        string_value = self.getStringValue()

        if string_value is not None:
            # Those that are user provided, need to overload this.
            return makeConstantReplacementNode(
                node=self, constant=string_value, user_provided=False
            )

        return None

    def getTypeValue(self):
        """Type of the node."""

        from .TypeNodes import ExpressionBuiltinType1

        return ExpressionBuiltinType1(
            value=self.makeClone(), source_ref=self.source_ref
        )

    def getIterationHandle(self):
        # Virtual method, pylint: disable=no-self-use
        return None

    @staticmethod
    def isKnownToBeHashable():
        """Is the value hashable, i.e. suitable for dictionary/set key usage."""

        # Unknown by default.
        return None

    @staticmethod
    def extractUnhashableNodeType():
        """Return the value type that is not hashable, if isKnowtoBeHashable() returns False."""

        # Not available by default.
        return None

    def onRelease(self, trace_collection):
        # print "onRelease", self
        pass

    def isKnownToHaveAttribute(self, attribute_name):
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return None

    @abstractmethod
    def computeExpressionRaw(self, trace_collection):
        """Abstract execution of the node.

        Returns:
            tuple(node, tags, description)

            The return value can be node itself.

        Notes:
            Replaces a node with computation result. This is the low level
            form for the few cases, where the children are not simply all
            evaluated first, but this allows e.g. to deal with branches, do
            not overload this unless necessary.
        """

    def computeExpressionAttribute(self, lookup_node, attribute_name, trace_collection):
        # By default, an attribute lookup may change everything about the lookup
        # source.
        # trace_collection.onValueEscapeAttributeLookup(self, attribute_name)

        if self.mayRaiseExceptionAttributeLookup(BaseException, attribute_name):
            trace_collection.onExceptionRaiseExit(BaseException)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        return lookup_node, None, None

    def computeExpressionAttributeSpecial(
        self, lookup_node, attribute_name, trace_collection
    ):
        # By default, an attribute lookup may change everything about the lookup
        # source. Virtual method, pylint: disable=unused-argument
        # trace_collection.onValueEscapeAttributeLookup(self, attribute_name)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        trace_collection.onExceptionRaiseExit(BaseException)

        return lookup_node, None, None

    def computeExpressionImportName(self, import_node, import_name, trace_collection):
        if self.mayRaiseExceptionImportName(BaseException, import_name):
            trace_collection.onExceptionRaiseExit(BaseException)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        return import_node, None, None

    def computeExpressionSetAttribute(
        self, set_node, attribute_name, value_node, trace_collection
    ):
        # Virtual method, pylint: disable=unused-argument

        # By default, an attribute lookup may change everything about the lookup
        # source and any code could run.
        trace_collection.removeKnowledge(self)
        trace_collection.removeKnowledge(value_node)
        trace_collection.onControlFlowEscape(self)

        trace_collection.onExceptionRaiseExit(BaseException)

        # Better mechanics?
        return set_node, None, None

    def computeExpressionDelAttribute(self, set_node, attribute_name, trace_collection):
        # By default, an attribute lookup may change everything about the lookup
        # source. Virtual method, pylint: disable=unused-argument
        # trace_collection.removeKnowledge(self)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        trace_collection.onExceptionRaiseExit(BaseException)

        # Better mechanics?
        return set_node, None, None

    def computeExpressionSubscript(self, lookup_node, subscript, trace_collection):
        # By default, an subscript can execute any code and change all values
        # that escaped. This is a virtual method that may consider the subscript
        # but generally we don't know what to do. pylint: disable=unused-argument
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return lookup_node, None, None

    def computeExpressionSetSubscript(
        self, set_node, subscript, value_node, trace_collection
    ):
        # By default, an subscript can execute any code and change all values
        # that escaped. This is a virtual method that may consider the subscript
        # but generally we don't know what to do.
        trace_collection.removeKnowledge(value_node)
        trace_collection.removeKnowledge(subscript)
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return set_node, None, None

    def computeExpressionDelSubscript(self, del_node, subscript, trace_collection):
        # By default, an subscript can execute any code and change all values
        # that escaped. This is a virtual method that may consider the subscript
        # but generally we don't know what to do. pylint: disable=unused-argument
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return del_node, None, None

    def computeExpressionSlice(self, lookup_node, lower, upper, trace_collection):
        # pylint: disable=unused-argument

        # By default, a slicing may change everything about the lookup source.
        # trace_collection.removeKnowledge(self)
        # trace_collection.onValueEscapeSliceOperation(self, lower, upper)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return lookup_node, None, None

    def computeExpressionSetSlice(
        self, set_node, lower, upper, value_node, trace_collection
    ):
        # pylint: disable=unused-argument

        # By default, an subscript may change everything about the lookup
        # source and the value is escaped.
        trace_collection.removeKnowledge(value_node)
        trace_collection.removeKnowledge(self)
        trace_collection.onControlFlowEscape(self)

        # trace_collection.onValueEscapeSliceArguments(self, lower, upper)

        # trace_collection.onValueEscapeSliceSetSource(self, lower, upper)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return set_node, None, None

    def computeExpressionDelSlice(self, set_node, lower, upper, trace_collection):
        # pylint: disable=unused-argument

        # By default, an subscript may change everything about the lookup
        # source.
        trace_collection.removeKnowledge(self)
        trace_collection.onControlFlowEscape(self)

        # trace_collection.onValueEscapeSliceArguments(self, lower, upper)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return set_node, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Virtual method, pylint: disable=unused-argument

        # The called and the arguments escape for good.
        call_node.onContentEscapes(trace_collection)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return call_node, None, None

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        # Virtual method, pylint: disable=unused-argument

        # The called and the arguments escape for good.
        self.onContentEscapes(trace_collection)
        if call_args is not None:
            call_args.onContentEscapes(trace_collection)
        if call_kw is not None:
            call_kw.onContentEscapes(trace_collection)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return call_node, None, None

    def computeExpressionLen(self, len_node, trace_collection):
        shape = self.getValueShape()

        has_len = shape.hasShapeSlotLen()

        if has_len is False:
            # An exception may be raised.
            trace_collection.onExceptionRaiseExit(BaseException)

            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                template="object of type '%s' has no len()",
                operation="len",
                original_node=len_node,
                value_node=self,
            )
        elif has_len is True:
            iter_length = self.getIterationLength()

            if iter_length is not None:
                from .ConstantRefNodes import makeConstantRefNode

                result = makeConstantRefNode(
                    constant=int(iter_length),  # make sure to downcast long
                    source_ref=len_node.getSourceReference(),
                )

                result = wrapExpressionWithNodeSideEffects(
                    new_node=result, old_node=self
                )

                return (
                    result,
                    "new_constant",
                    "Predicted 'len' result from value shape.",
                )

        self.onContentEscapes(trace_collection)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return len_node, None, None

    def computeExpressionAbs(self, abs_node, trace_collection):
        shape = self.getTypeShape()

        if shape.hasShapeSlotAbs() is False:
            # Any exception may be raised.
            trace_collection.onExceptionRaiseExit(BaseException)

            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                template="bad operand type for abs(): '%s'",
                operation="abs",
                original_node=abs_node,
                value_node=self,
            )

        self.onContentEscapes(trace_collection)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return abs_node, None, None

    def computeExpressionInt(self, int_node, trace_collection):
        shape = self.getTypeShape()

        if shape.hasShapeSlotInt() is False:
            # Any exception may be raised.
            trace_collection.onExceptionRaiseExit(BaseException)

            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                template=(
                    "int() argument must be a string or a number, not '%s'"
                    if python_version < 0x300
                    else "int() argument must be a string, a bytes-like object or a number, not '%s'"
                ),
                operation="int",
                original_node=int_node,
                value_node=self,
            )

        self.onContentEscapes(trace_collection)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return int_node, None, None

    def computeExpressionLong(self, long_node, trace_collection):
        shape = self.getTypeShape()

        if shape.hasShapeSlotLong() is False:
            # Any exception may be raised.
            trace_collection.onExceptionRaiseExit(BaseException)

            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                template="long() argument must be a string or a number, not '%s'",
                operation="long",
                original_node=long_node,
                value_node=self,
            )

        self.onContentEscapes(trace_collection)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return long_node, None, None

    def computeExpressionFloat(self, float_node, trace_collection):
        shape = self.getTypeShape()

        if shape.hasShapeSlotFloat() is False:
            # Any exception may be raised.
            trace_collection.onExceptionRaiseExit(BaseException)

            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                (
                    "float() argument must be a string or a number"
                    if Options.is_full_compat and python_version < 0x300
                    else "float() argument must be a string or a number, not '%s'"
                ),
                operation="long",
                original_node=float_node,
                value_node=self,
            )

        self.onContentEscapes(trace_collection)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return float_node, None, None

    def computeExpressionBytes(self, bytes_node, trace_collection):
        shape = self.getTypeShape()

        if (
            shape.hasShapeSlotBytes() is False
            and shape.hasShapeSlotInt() is False
            and shape.hasShapeSlotIter() is False
        ):
            # An exception is raised.
            trace_collection.onExceptionRaiseExit(BaseException)

            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                "'%s' object is not iterable",
                operation="bytes",
                original_node=bytes_node,
                value_node=self,
            )

        self.onContentEscapes(trace_collection)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return bytes_node, None, None

    def computeExpressionComplex(self, complex_node, trace_collection):
        shape = self.getTypeShape()

        if shape.hasShapeSlotComplex() is False:
            # Any exception may be raised.
            trace_collection.onExceptionRaiseExit(BaseException)

            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                (
                    "complex() argument must be a string or a number"
                    if Options.is_full_compat and python_version < 0x300
                    else "complex() argument must be a string or a number, not '%s'"
                ),
                operation="complex",
                original_node=complex_node,
                value_node=self,
            )

        self.onContentEscapes(trace_collection)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return complex_node, None, None

    def computeExpressionIter1(self, iter_node, trace_collection):
        shape = self.getTypeShape()

        if shape.hasShapeSlotIter() is False:
            # An exception may be raised.
            trace_collection.onExceptionRaiseExit(BaseException)

            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                template="'%s' object is not iterable",
                operation="iter",
                original_node=iter_node,
                value_node=self,
            )

        self.onContentEscapes(trace_collection)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return iter_node, None, None

    def computeExpressionNext1(self, next_node, trace_collection):
        # TODO: This is only true for a few value types, use type shape to tell if
        # it might escape or raise.

        self.onContentEscapes(trace_collection)

        # Any code could be run, note that.
        if self.mayHaveSideEffectsNext():
            trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return True, (next_node, None, None)

    def computeExpressionAsyncIter(self, iter_node, trace_collection):
        self.onContentEscapes(trace_collection)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return iter_node, None, None

    def computeExpressionOperationNot(self, not_node, trace_collection):
        # Virtual method, pylint: disable=no-self-use

        # The value of that node escapes and could change its contents.
        # trace_collection.onValueEscapeNot(self)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(not_node)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return not_node, None, None

    def computeExpressionOperationRepr(self, repr_node, trace_collection):
        type_shape = self.getTypeShape()

        escape_desc = type_shape.getOperationUnaryReprEscape()

        # Annotate if exceptions might be raised.
        exception_raise_exit = escape_desc.getExceptionExit()
        if exception_raise_exit is not None:
            trace_collection.onExceptionRaiseExit(exception_raise_exit)

        if escape_desc.isValueEscaping():
            # The value of that node escapes and could change its contents during repr
            # only, which might be more limited.
            # trace_collection.onValueEscapeRepr(self)
            trace_collection.removeKnowledge(self)

        if escape_desc.isControlFlowEscape():
            # Any code could be run, note that.
            trace_collection.onControlFlowEscape(self)

        return (repr_node, None, None), escape_desc

    def computeExpressionComparisonIn(self, in_node, value_node, trace_collection):
        # Virtual method, pylint: disable=unused-argument

        shape = self.getTypeShape()

        assert shape is not None, self

        if shape.hasShapeSlotContains() is False:
            # An exception may be raised.
            trace_collection.onExceptionRaiseExit(BaseException)

            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                template="argument of type '%s' object is not iterable",
                operation="in",
                original_node=in_node,
                value_node=self,
            )

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(in_node)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return in_node, None, None

    def computeExpressionDrop(self, statement, trace_collection):
        if not self.mayHaveSideEffects():
            return (
                None,
                "new_statements",
                lambda: "Removed %s without effect." % self.getDescription(),
            )

        return statement, None, None

    def computeExpressionBool(self, trace_collection):
        if not self.mayRaiseException(BaseException) and self.mayRaiseExceptionBool(
            BaseException
        ):
            trace_collection.onExceptionRaiseExit(BaseException)

        # None indicates no replacement action.
        return None, None, None

    @staticmethod
    def onContentEscapes(trace_collection):
        pass

    @staticmethod
    def onContentIteratedEscapes(trace_collection):
        pass

    @staticmethod
    def mayRaiseExceptionBool(exception_type):
        """Unless we are told otherwise, everything may raise being checked."""
        # Virtual method, pylint: disable=unused-argument
        return True

    @staticmethod
    def mayRaiseExceptionAbs(exception_type):
        """Unless we are told otherwise, everything may raise in 'abs'."""
        # Virtual method, pylint: disable=unused-argument

        return True

    @staticmethod
    def mayRaiseExceptionInt(exception_type):
        """Unless we are told otherwise, everything may raise in __int__."""
        # Virtual method, pylint: disable=unused-argument

        return True

    @staticmethod
    def mayRaiseExceptionLong(exception_type):
        """Unless we are told otherwise, everything may raise in __long__."""
        # Virtual method, pylint: disable=unused-argument

        return True

    @staticmethod
    def mayRaiseExceptionFloat(exception_type):
        """Unless we are told otherwise, everything may raise in __float__."""
        # Virtual method, pylint: disable=unused-argument

        return True

    @staticmethod
    def mayRaiseExceptionBytes(exception_type):
        """Unless we are told otherwise, everything may raise in __bytes__."""
        # Virtual method, pylint: disable=unused-argument

        return True

    @staticmethod
    def mayRaiseExceptionIn(exception_type, checked_value):
        """Unless we are told otherwise, everything may raise being iterated."""
        # Virtual method, pylint: disable=unused-argument

        return True

    @staticmethod
    def mayRaiseExceptionAttributeLookup(exception_type, attribute_name):
        """Unless we are told otherwise, everything may raise for attribute access."""
        # Virtual method, pylint: disable=unused-argument

        return True

    @staticmethod
    def mayRaiseExceptionAttributeLookupSpecial(exception_type, attribute_name):
        """Unless we are told otherwise, everything may raise for attribute access."""
        # Virtual method, pylint: disable=unused-argument

        return True

    @staticmethod
    def mayRaiseExceptionAttributeLookupObject(exception_type, attribute):
        """Unless we are told otherwise, everything may raise for attribute access."""
        # Virtual method, pylint: disable=unused-argument

        return True

    @staticmethod
    def mayRaiseExceptionImportName(exception_type, import_name):
        """Unless we are told otherwise, everything may raise for name import."""
        # Virtual method, pylint: disable=unused-argument
        return True

    @staticmethod
    def mayHaveSideEffectsBool():
        """Unless we are told otherwise, everything may have a side effect for bool check."""

        return True

    @staticmethod
    def mayHaveSideEffectsAbs():
        """Unless we are told otherwise, everything may have a side effect for abs check."""

        # TODO: Bonus points for check type shapes that will be good
        # for abs, i.e. number shapes like Int, Long, Float, Complex.

        return True

    def mayHaveSideEffectsNext(self):
        """The type shape tells us, if "next" may execute code."""

        return self.getTypeShape().hasShapeSlotNextCode()

    def hasShapeSlotLen(self):
        """The type shape tells us, if "len" is available."""
        return self.getTypeShape().hasShapeSlotLen()

    def hasShapeSlotIter(self):
        """The type shape tells us, if "iter" is available."""
        return self.getTypeShape().hasShapeSlotIter()

    def hasShapeSlotNext(self):
        """The type shape tells us, if "next" is available."""
        return self.getTypeShape().hasShapeSlotNext()

    # TODO: Maybe this is a shape slot thing.
    @staticmethod
    def isIndexable():
        """Unless we are told otherwise, it's not indexable."""

        return False

    # TODO: There ought to be a type shape check for that too.
    @staticmethod
    def getIntegerValue():
        """Node as integer value, if possible."""

        return None

    # TODO: There ought to be a type shape check for that too.
    @staticmethod
    def getIndexValue():
        """Node as index value, if possible.

        This should only work for int, bool, and long values, but e.g. not floats.
        """

        return None

    @staticmethod
    def getIntValue():
        """Value that "int" or "PyNumber_Int" (sp) would give, if known.

        Otherwise it is "None" to indicate unknown. Users must not
        forget to take side effects into account, when replacing a
        node with its string value.
        """
        return None

    def getExpressionDictInConstant(self, value):
        """Value that the dict "in" operation would give, if known.

        This is only called for values with known dict type shape. And those
        nodes who are known to do it, have to overload it.
        """

        # Virtual method, pylint: disable=unused-argument

        # We want to have them all overloaded, so lets report cases where that
        # has not been happening.
        if Options.is_debug:
            onMissingOverload(method_name="getExpressionDictInConstant", node=self)

        return None

    def hasShapeTrustedAttributes(self):
        return self.getTypeShape().hasShapeTrustedAttributes()

    def hasShapeTypeExact(self):
        """Does a node have exactly a 'type' shape."""

        return self.getTypeShape() is tshape_type

    def hasShapeListExact(self):
        """Does a node have exactly a list shape."""

        return self.getTypeShape() is tshape_list

    def hasShapeDictionaryExact(self):
        """Does a node have exactly a dictionary shape."""

        return self.getTypeShape() is tshape_dict

    def hasShapeStrExact(self):
        """Does an expression have exactly a string shape."""
        return self.getTypeShape() is tshape_str

    def hasShapeUnicodeExact(self):
        """Does an expression have exactly a unicode shape."""
        return self.getTypeShape() is tshape_unicode

    if str is bytes:

        def hasShapeStrOrUnicodeExact(self):
            return self.getTypeShape() in (tshape_str, tshape_unicode)

    else:

        def hasShapeStrOrUnicodeExact(self):
            return self.getTypeShape() is tshape_str

    def hasShapeBytesExact(self):
        """Does an expression have exactly a bytes shape."""
        return self.getTypeShape() is tshape_bytes

    def hasShapeBoolExact(self):
        """Does an expression have exactly a bool shape."""
        return self.getTypeShape() is tshape_bool

    @staticmethod
    def hasVeryTrustedValue():
        """Trust that value will not be overwritten from the outside."""
        return False


class ExpressionNoSideEffectsMixin(object):
    __slots__ = ()

    @staticmethod
    def mayHaveSideEffects():
        # Virtual method overload
        return False

    @staticmethod
    def extractSideEffects():
        # Virtual method overload, we said we have no effects.
        return ()

    def computeExpressionDrop(self, statement, trace_collection):
        # Virtual method overload, pylint: disable=unused-argument
        #
        # We said we have no effects, so we can be removed.
        return (
            None,
            "new_statements",
            lambda: "Removed %s that never has an effect." % self.getDescription(),
        )

    @staticmethod
    def mayRaiseException(exception_type):
        # Virtual method overload, pylint: disable=unused-argument

        # An exception would be considered a side effect too.
        return False


class CompileTimeConstantExpressionBase(ExpressionNoSideEffectsMixin, ExpressionBase):
    # TODO: Do this for all computations, do this in the base class of all
    # nodes.
    __slots__ = ("computed_attribute",)

    def __init__(self, source_ref):
        ExpressionBase.__init__(self, source_ref)

        self.computed_attribute = None

    @staticmethod
    def isCompileTimeConstant():
        """Has a value that we can use at compile time.

        Yes or no. If it has such a value, simulations can be applied at
        compile time and e.g. operations or conditions, or even calls may
        be executed against it.
        """
        return True

    def getTruthValue(self):
        return bool(self.getCompileTimeConstant())

    def getComparisonValue(self):
        return True, self.getCompileTimeConstant()

    @abstractmethod
    def getCompileTimeConstant(self):
        """Return compile time constant.

        Notes: Only available after passing "isCompileTimeConstant()".

        """

    @staticmethod
    def isMutable():
        """Return if compile time constant is mutable.

        Notes: Only useful after passing "isCompileTimeConstant()".
        """
        return False

    @staticmethod
    def hasShapeTrustedAttributes():
        # All compile time constants must be fixed for attributes.
        return True

    @staticmethod
    def mayHaveSideEffectsBool():
        # Virtual method overload
        return False

    @staticmethod
    def mayRaiseExceptionBool(exception_type):
        return False

    def mayRaiseExceptionAttributeLookup(self, exception_type, attribute_name):
        # We remember it from our computation.
        return not self.computed_attribute

    def mayRaiseExceptionAttributeLookupSpecial(self, exception_type, attribute_name):
        # We remember it from our computation.
        return not self.computed_attribute

    def computeExpressionOperationNot(self, not_node, trace_collection):
        return trace_collection.getCompileTimeComputationResult(
            node=not_node,
            computation=lambda: not self.getCompileTimeConstant(),
            description="""\
Compile time constant negation truth value pre-computed.""",
        )

    def computeExpressionOperationRepr(self, repr_node, trace_collection):
        return (
            trace_collection.getCompileTimeComputationResult(
                node=repr_node,
                computation=lambda: repr(self.getCompileTimeConstant()),
                description="""\
Compile time constant repr value pre-computed.""",
            ),
            None,
        )

    def computeExpressionLen(self, len_node, trace_collection):
        return trace_collection.getCompileTimeComputationResult(
            node=len_node,
            computation=lambda: len(self.getCompileTimeConstant()),
            description="""\
Compile time constant len value pre-computed.""",
        )

    def computeExpressionAbs(self, abs_node, trace_collection):
        return trace_collection.getCompileTimeComputationResult(
            node=abs_node,
            computation=lambda: abs(self.getCompileTimeConstant()),
            description="""\
Compile time constant abs value pre-computed.""",
        )

    def computeExpressionInt(self, int_node, trace_collection):
        return trace_collection.getCompileTimeComputationResult(
            node=int_node,
            computation=lambda: int(self.getCompileTimeConstant()),
            description="""\
Compile time constant int value pre-computed.""",
        )

    def computeExpressionLong(self, long_node, trace_collection):
        return trace_collection.getCompileTimeComputationResult(
            node=long_node,
            computation=lambda: long(self.getCompileTimeConstant()),
            description="""\
Compile time constant long value pre-computed.""",
        )

    def computeExpressionFloat(self, float_node, trace_collection):
        return trace_collection.getCompileTimeComputationResult(
            node=float_node,
            computation=lambda: float(self.getCompileTimeConstant()),
            description="""\
Compile time constant float value pre-computed.""",
        )

    def computeExpressionBytes(self, bytes_node, trace_collection):
        constant_value = self.getCompileTimeConstant()

        if type(constant_value) in (int, long):
            if constant_value > 1000:
                return bytes_node, None, None

        return trace_collection.getCompileTimeComputationResult(
            node=bytes_node,
            computation=lambda: bytes(constant_value),
            description="""\
Compile time constant bytes value pre-computed.""",
        )

    def isKnownToHaveAttribute(self, attribute_name):
        if self.computed_attribute is None:
            self.computed_attribute = hasattr(
                self.getCompileTimeConstant(), attribute_name
            )

        return self.computed_attribute

    def getKnownAttributeValue(self, attribute_name):
        return getattr(self.getCompileTimeConstant(), attribute_name)

    def computeExpressionAttribute(self, lookup_node, attribute_name, trace_collection):
        value = self.getCompileTimeConstant()

        if self.computed_attribute is None:
            self.computed_attribute = hasattr(value, attribute_name)

        # If it raises, or the attribute itself is a compile time constant,
        # then do execute it.
        if not self.computed_attribute or isCompileTimeConstantValue(
            getattr(value, attribute_name, None)
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=lookup_node,
                computation=lambda: getattr(value, attribute_name),
                description="Attribute '%s' pre-computed." % (attribute_name),
            )

        return lookup_node, None, None

    def computeExpressionSubscript(self, lookup_node, subscript, trace_collection):
        if subscript.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=lookup_node,
                computation=lambda: self.getCompileTimeConstant()[
                    subscript.getCompileTimeConstant()
                ],
                description="Subscript of constant with constant value.",
            )

        # TODO: Look-up of subscript to index may happen.
        # Any code could be run due to that, note that.
        trace_collection.onControlFlowEscape(self)

        trace_collection.onExceptionRaiseExit(BaseException)

        return lookup_node, None, None

    def computeExpressionSlice(self, lookup_node, lower, upper, trace_collection):
        # TODO: Could be happy with predictable index values and not require
        # constants.
        if lower is not None:
            if upper is not None:
                if lower.isCompileTimeConstant() and upper.isCompileTimeConstant():
                    return trace_collection.getCompileTimeComputationResult(
                        node=lookup_node,
                        computation=lambda: self.getCompileTimeConstant()[
                            lower.getCompileTimeConstant() : upper.getCompileTimeConstant()
                        ],
                        description="Slicing of constant with constant indexes.",
                        user_provided=False,
                    )
            else:
                if lower.isCompileTimeConstant():
                    return trace_collection.getCompileTimeComputationResult(
                        node=lookup_node,
                        computation=lambda: self.getCompileTimeConstant()[
                            lower.getCompileTimeConstant() :
                        ],
                        description="Slicing of constant with constant lower index only.",
                        user_provided=False,
                    )
        else:
            if upper is not None:
                if upper.isCompileTimeConstant():
                    return trace_collection.getCompileTimeComputationResult(
                        node=lookup_node,
                        computation=lambda: self.getCompileTimeConstant()[
                            : upper.getCompileTimeConstant()
                        ],
                        description="Slicing of constant with constant upper index only.",
                        user_provided=False,
                    )
            else:
                return trace_collection.getCompileTimeComputationResult(
                    node=lookup_node,
                    computation=lambda: self.getCompileTimeConstant()[:],
                    description="Slicing of constant with no indexes.",
                    user_provided=False,
                )

        # Any exception might be raised, although it's not likely.
        trace_collection.onExceptionRaiseExit(BaseException)

        return lookup_node, None, None

    def computeExpressionComparisonIn(self, in_node, value_node, trace_collection):
        if value_node.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=in_node,
                computation=lambda: in_node.getSimulator()(
                    value_node.getCompileTimeConstant(), self.getCompileTimeConstant()
                ),
                description="""\
Predicted '%s' on compiled time constant values."""
                % in_node.comparator,
                user_provided=False,
            )

        # Look-up of __contains__ on compile time constants does mostly nothing.
        trace_collection.onExceptionRaiseExit(BaseException)

        return in_node, None, None

    def computeExpressionBool(self, trace_collection):
        constant = self.getCompileTimeConstant()

        # Dealt with through dedicated nodes.
        assert type(constant) is not bool
        truth_value = bool(constant)

        result = makeConstantReplacementNode(
            constant=truth_value, node=self, user_provided=False
        )

        return truth_value, result, "Predicted compile time constant truth value."


class ExpressionSpecBasedComputationMixin(object):
    # Mixins are not allowed to specify slots.
    __slots__ = ()

    builtin_spec = None

    def computeBuiltinSpec(self, trace_collection, given_values):
        assert self.builtin_spec is not None, self

        if not self.builtin_spec.isCompileTimeComputable(given_values):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        return trace_collection.getCompileTimeComputationResult(
            node=self,
            computation=lambda: self.builtin_spec.simulateCall(given_values),
            description="Built-in call to '%s' pre-computed."
            % (self.builtin_spec.getName()),
            user_provided=self.builtin_spec.isUserProvided(given_values),
        )


class ExpressionSpecBasedComputationNoRaiseMixin(object):
    # Mixins are not allowed to specify slots.
    __slots__ = ()

    builtin_spec = None

    def computeBuiltinSpec(self, trace_collection, given_values):
        assert self.builtin_spec is not None, self

        if not self.builtin_spec.isCompileTimeComputable(given_values):
            return self, None, None

        return trace_collection.getCompileTimeComputationResult(
            node=self,
            computation=lambda: self.builtin_spec.simulateCall(given_values),
            description="Built-in call to '%s' pre-computed."
            % (self.builtin_spec.getName()),
        )


class ExpressionBuiltinSingleArgBase(
    ExpressionSpecBasedComputationMixin, ChildHavingValueMixin, ExpressionBase
):
    named_children = ("value",)

    def __init__(self, value, source_ref):
        ChildHavingValueMixin.__init__(self, value=value)

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        value = self.subnode_value

        # TODO: Can this happen, where, and can we have a different base class then.
        assert value is not None

        if value is None:
            return self.computeBuiltinSpec(
                trace_collection=trace_collection, given_values=()
            )
        else:
            return self.computeBuiltinSpec(
                trace_collection=trace_collection, given_values=(value,)
            )


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
