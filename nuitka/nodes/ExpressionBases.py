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
""" Expression base classes.

These classes provide the generic base classes available for
expressions. They have a richer interface, mostly related to
abstract execution, and different from statements.

"""

from abc import abstractmethod

from nuitka.__past__ import long  # pylint: disable=I0021,redefined-builtin
from nuitka.Constants import isCompileTimeConstantValue
from nuitka.Options import isFullCompat
from nuitka.PythonVersions import python_version

from .NodeBases import ChildrenHavingMixin, NodeBase
from .NodeMakingHelpers import (
    getComputationResult,
    makeConstantReplacementNode,
    makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue,
    wrapExpressionWithNodeSideEffects,
    wrapExpressionWithSideEffects
)
from .shapes.BuiltinTypeShapes import (
    ShapeTypeDict,
    ShapeTypeStr,
    ShapeTypeUnicode
)
from .shapes.StandardShapes import ShapeUnknown


class ExpressionBase(NodeBase):
    # TODO: Maybe we can do this only for debug mode.
    __slots__ = ("code_generated",)

    def getTypeShape(self):
        # Virtual method, pylint: disable=no-self-use
        return ShapeUnknown

    def getValueShape(self):
        return self

    def isCompileTimeConstant(self):
        """ Has a value that we can use at compile time.

            Yes or no. If it has such a value, simulations can be applied at
            compile time and e.g. operations or conditions, or even calls may
            be executed against it.
        """
        # Virtual method, pylint: disable=no-self-use
        return False

    def getTruthValue(self):
        """ Return known truth value. The "None" value indicates unknown. """

        if self.isCompileTimeConstant():
            return bool(self.getCompileTimeConstant())
        else:
            return None

    def isKnownToBeIterable(self, count):
        """ Can be iterated at all (count is None) or exactly count times.

            Yes or no. If it can be iterated a known number of times, it may
            be asked to unpack itself.
        """

        # Virtual method, pylint: disable=no-self-use,unused-argument
        return False

    def isKnownToBeIterableAtMin(self, count):
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return False

    def isKnownToBeIterableAtMax(self, count):
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return False

    def getIterationLength(self):
        """ Value that "len" or "PyObject_Size" would give, if known.

            Otherwise it is "None" to indicate unknown.
        """

        # Virtual method, pylint: disable=no-self-use
        return None

    def getIterationMinLength(self):
        """ Value that "len" or "PyObject_Size" would give at minimum, if known.

            Otherwise it is "None" to indicate unknown.
        """

        return self.getIterationLength()

    def getIterationMaxLength(self):
        """ Value that "len" or "PyObject_Size" would give at maximum, if known.

            Otherwise it is "None" to indicate unknown.
        """

        return self.getIterationLength()

    def getStringValue(self):
        """ Node as string value, if possible."""
        # Virtual method, pylint: disable=no-self-use
        return None

    def getStrValue(self):
        """ Value that "str" or "PyObject_Str" would give, if known.

            Otherwise it is "None" to indicate unknown. Users must not
            forget to take side effects into account, when replacing a
            node with its string value.
        """
        string_value = self.getStringValue()

        if string_value is not None:
            return makeConstantReplacementNode(
                node     = self,
                constant = string_value
            )

        return None

    def getTypeValue(self):
        """ Type of the node.

        """

        from .TypeNodes import ExpressionBuiltinType1

        return ExpressionBuiltinType1(
            value      = self.makeClone(),
            source_ref = self.getSourceReference()
        )

    def isKnownToBeHashable(self):
        """ Is the value hashable, i.e. suitable for dictionary/set keying."""

        # Virtual method, pylint: disable=no-self-use
        # Unknown by default.
        return None

    def extractUnhashableNode(self):
        # Virtual method, pylint: disable=no-self-use
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
        """ Replace this node with computation result. """

    def computeExpressionAttribute(self, lookup_node, attribute_name,
                                   trace_collection):
        # By default, an attribute lookup may change everything about the lookup
        # source.
        trace_collection.removeKnowledge(self)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        if not self.isKnownToHaveAttribute(attribute_name):
            trace_collection.onExceptionRaiseExit(BaseException)

        return lookup_node, None, None

    def computeExpressionAttributeSpecial(self, lookup_node, attribute_name,
                                          trace_collection):
        # By default, an attribute lookup may change everything about the lookup
        # source. Virtual method, pylint: disable=unused-argument
        trace_collection.removeKnowledge(lookup_node)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        trace_collection.onExceptionRaiseExit(BaseException)

        return lookup_node, None, None

    def computeExpressionImportName(self, import_node, import_name,
                                    trace_collection):
        if self.mayRaiseExceptionImportName(BaseException, import_name):
            trace_collection.onExceptionRaiseExit(BaseException)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        return import_node, None, None

    def computeExpressionSetAttribute(self, set_node, attribute_name,
                                      value_node, trace_collection):

        # By default, an attribute lookup may change everything about the lookup
        # source. Virtual method, pylint: disable=unused-argument
        trace_collection.removeKnowledge(self)
        trace_collection.removeKnowledge(value_node)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        trace_collection.onExceptionRaiseExit(BaseException)

        # Better mechanics?
        return set_node, None, None

    def computeExpressionDelAttribute(self, set_node, attribute_name,
                                      trace_collection):

        # By default, an attribute lookup may change everything about the lookup
        # source. Virtual method, pylint: disable=unused-argument
        trace_collection.removeKnowledge(self)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        trace_collection.onExceptionRaiseExit(BaseException)

        # Better mechanics?
        return set_node, None, None

    def computeExpressionSubscript(self, lookup_node, subscript,
                                   trace_collection):
        # By default, an subscript can execute any code and change all values
        # that escaped. This is a virtual method that may consider the subscript
        # but generally we don't know what to do. pylint: disable=unused-argument
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return lookup_node, None, None

    def computeExpressionSetSubscript(self, set_node, subscript, value_node,
                                      trace_collection):
        # By default, an subscript can execute any code and change all values
        # that escaped. This is a virtual method that may consider the subscript
        # but generally we don't know what to do. pylint: disable=unused-argument
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return set_node, None, None

    def computeExpressionDelSubscript(self, del_node, subscript,
                                      trace_collection):
        # By default, an subscript can execute any code and change all values
        # that escaped. This is a virtual method that may consider the subscript
        # but generally we don't know what to do. pylint: disable=unused-argument
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return del_node, None, None

    def computeExpressionSlice(self, lookup_node, lower, upper,
                               trace_collection):
        # By default, a slicing may change everything about the lookup source.
        trace_collection.removeKnowledge(self)
        trace_collection.removeKnowledge(lower)
        trace_collection.removeKnowledge(upper)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return lookup_node, None, None

    def computeExpressionSetSlice(self, set_node, lower, upper, value_node,
                                      trace_collection):
        # By default, an subscript may change everything about the lookup
        # source.
        trace_collection.removeKnowledge(self)
        trace_collection.removeKnowledge(lower)
        trace_collection.removeKnowledge(upper)
        trace_collection.removeKnowledge(value_node)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return set_node, None, None

    def computeExpressionDelSlice(self, set_node, lower, upper,
                                  trace_collection):
        # By default, an subscript may change everything about the lookup
        # source.
        trace_collection.removeKnowledge(self)
        trace_collection.removeKnowledge(lower)
        trace_collection.removeKnowledge(upper)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return set_node, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw,
                              trace_collection):
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
            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                template      = "object of type '%s' has no len()",
                operation     = "len",
                original_node = len_node,
                value_node    = self
            )
        elif has_len is True:
            iter_length = self.getIterationLength()

            if iter_length is not None:
                from .ConstantRefNodes import makeConstantRefNode

                result = makeConstantRefNode(
                    constant   = int(iter_length), # make sure to downcast long
                    source_ref = len_node.getSourceReference()
                )

                result = wrapExpressionWithNodeSideEffects(
                    new_node = result,
                    old_node = self
                )

                return result, "new_constant", "Predicted 'len' result from value shape."

        self.onContentEscapes(trace_collection)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return len_node, None, None

    def computeExpressionInt(self, int_node, trace_collection):
        shape = self.getTypeShape()

        if shape.hasShapeSlotInt() is False:
            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                template      =
                    "int() argument must be a string or a number, not '%s'"
                      if python_version < 300 else
                    "int() argument must be a string, a bytes-like object or a number, not '%s'",
                operation     = "int",
                original_node = int_node,
                value_node    = self
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
            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                template      = "long() argument must be a string or a number, not '%s'",
                operation     = "long",
                original_node = long_node,
                value_node    = self
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
            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                    "float() argument must be a string or a number"
                      if isFullCompat() and python_version < 300 else
                    "float() argument must be a string or a number, not '%s'",
                operation     = "long",
                original_node = float_node,
                value_node    = self
            )

        self.onContentEscapes(trace_collection)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return float_node, None, None

    def computeExpressionBytes(self, bytes_node, trace_collection):
        shape = self.getTypeShape()

        if shape.hasShapeSlotBytes() is False and \
           shape.hasShapeSlotInt() is False and \
           shape.hasShapeSlotIter() is False:
            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                "'%s' object is not iterable",
                operation     = "bytes",
                original_node = bytes_node,
                value_node    = self
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
            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                    "complex() argument must be a string or a number"
                      if isFullCompat() and python_version < 300 else
                    "complex() argument must be a string or a number, not '%s'",
                operation     = "complex",
                original_node = complex_node,
                value_node    = self
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
            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                template      = "'%s' object is not iterable",
                operation     = "iter",
                original_node = iter_node,
                value_node    = self
            )

        self.onContentEscapes(trace_collection)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return iter_node, None, None

    def computeExpressionNext1(self, next_node, trace_collection):
        self.onContentEscapes(trace_collection)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return next_node, None, None

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
        trace_collection.removeKnowledge(not_node)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(not_node)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return not_node, None, None

    def computeExpressionComparisonIn(self, in_node, value_node, trace_collection):
        # Virtual method, pylint: disable=unused-argument

        shape = self.getTypeShape()

        assert shape is not None, self

        if shape.hasShapeSlotContains() is False:
            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                template      = "argument of type '%s' object is not iterable",
                operation     = "in",
                original_node = in_node,
                value_node    = self
            )

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(in_node)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return in_node, None, None

    def computeExpressionDrop(self, statement, trace_collection):
        if not self.mayHaveSideEffects():
            return None, "new_statements", lambda : "Removed %s without effect." % self.getDescription()

        return statement, None, None

    def onContentEscapes(self, trace_collection):
        pass

    def mayRaiseExceptionBool(self, exception_type):
        """ Unless we are told otherwise, everything may raise being checked. """
        # Virtual method, pylint: disable=no-self-use,unused-argument

        return True

    def mayRaiseExceptionInt(self, exception_type):
        """ Unless we are told otherwise, everything may raise in __int__. """
        # Virtual method, pylint: disable=no-self-use,unused-argument

        return True

    def mayRaiseExceptionLong(self, exception_type):
        """ Unless we are told otherwise, everything may raise in __long__. """
        # Virtual method, pylint: disable=no-self-use,unused-argument

        return True

    def mayRaiseExceptionFloat(self, exception_type):
        """ Unless we are told otherwise, everything may raise in __float__. """
        # Virtual method, pylint: disable=no-self-use,unused-argument

        return True

    def mayRaiseExceptionBytes(self, exception_type):
        """ Unless we are told otherwise, everything may raise in __bytes__. """
        # Virtual method, pylint: disable=no-self-use,unused-argument

        return True

    def mayRaiseExceptionIn(self, exception_type, checked_value):
        """ Unless we are told otherwise, everything may raise being iterated. """
        # Virtual method, pylint: disable=no-self-use,unused-argument

        return True

    def mayRaiseExceptionAttributeLookup(self, exception_type, attribute_name):
        """ Unless we are told otherwise, everything may raise for attribute access. """
        # Virtual method, pylint: disable=no-self-use,unused-argument

        return True

    def mayRaiseExceptionAttributeLookupSpecial(self, exception_type, attribute_name):
        """ Unless we are told otherwise, everything may raise for attribute access. """
        # Virtual method, pylint: disable=no-self-use,unused-argument

        return True

    def mayRaiseExceptionAttributeLookupObject(self, exception_type, attribute):
        """ Unless we are told otherwise, everything may raise for attribute access. """
        # Virtual method, pylint: disable=no-self-use,unused-argument

        return True

    def mayRaiseExceptionAttributeCheck(self, exception_type, attribute_name):
        """ Unless we are told otherwise, everything may raise for attribute check. """
        # Virtual method, pylint: disable=no-self-use,unused-argument

        return True

    def mayRaiseExceptionAttributeCheckObject(self, exception_type, attribute):
        """ Unless we are told otherwise, everything may raise for attribute check. """
        # Virtual method, pylint: disable=no-self-use,unused-argument

        return True

    def mayRaiseExceptionImportName(self, exception_type, import_name):
        """ Unless we are told otherwise, everything may raise for name import. """
        # Virtual method, pylint: disable=no-self-use,unused-argument
        return True

    def mayHaveSideEffectsBool(self):
        """ Unless we are told otherwise, everything may have a side effect for bool check. """
        # Virtual method, pylint: disable=no-self-use

        return True

    def hasShapeSlotLen(self):
        """ The type shape tells us, if "len" is available.

        """
        return self.getTypeShape().hasShapeSlotLen()

    def hasShapeSlotIter(self):
        """ The type shape tells us, if "iter" is available.

        """
        return self.getTypeShape().hasShapeSlotIter()

    def hasShapeSlotNext(self):
        """ The type shape tells us, if "next" is available.

        """
        return self.getTypeShape().hasShapeSlotNext()


    # TODO: Maybe this is a shape slot thing.
    def isIndexable(self):
        """ Unless we are told otherwise, it's not indexable. """
        # Virtual method, pylint: disable=no-self-use

        return False

    # TODO: The ought to be a type shape check for that too.
    def getIntegerValue(self):
        """ Node as integer value, if possible."""
        # Virtual method, pylint: disable=no-self-use
        return None

    def getIntValue(self):
        """ Value that "int" or "PyNumber_Int" (sp) would give, if known.

            Otherwise it is "None" to indicate unknown. Users must not
            forget to take side effects into account, when replacing a
            node with its string value.
        """
        # Virtual method, pylint: disable=no-self-use
        return None

    def hasShapeDictionaryExact(self):
        """ Does a node have exactly a dictionary shape.

        """

        return self.getTypeShape() is ShapeTypeDict

    def hasShapeStrExact(self):
        """ Does an expression have exactly a string shape.

        """
        return self.getTypeShape() is ShapeTypeStr

    def hasShapeUnicodeExact(self):
        """ Does an expression have exactly a unicode shape.

        """
        return self.getTypeShape() is ShapeTypeUnicode





class CompileTimeConstantExpressionBase(ExpressionBase):
    # Base classes can be abstract, pylint: disable=abstract-method

    # TODO: Do this for all computations, do this in the base class of all
    # nodes.
    __slots__ = ("computed_attribute",)

    def __init__(self, source_ref):
        ExpressionBase.__init__(
            self,
            source_ref = source_ref
        )

        self.computed_attribute = None

    def isCompileTimeConstant(self):
        """ Has a value that we can use at compile time.

            Yes or no. If it has such a value, simulations can be applied at
            compile time and e.g. operations or conditions, or even calls may
            be executed against it.
        """
        return True

    def isMutable(self):
        # Virtual method, pylint: disable=no-self-use
        return False

    def mayHaveSideEffects(self):
        # Virtual method overload
        return False

    def mayHaveSideEffectsBool(self):
        # Virtual method overload
        return False

    def mayRaiseException(self, exception_type):
        # Virtual method overload
        return False

    def mayRaiseExceptionBool(self, exception_type):
        # Virtual method overload
        return False

    def mayRaiseExceptionAttributeLookup(self, exception_type, attribute_name):
        # Virtual method overload

        # We remember it from our computation.
        return not self.computed_attribute

    def mayRaiseExceptionAttributeLookupSpecial(self, exception_type, attribute_name):
        # Virtual method overload

        # We remember it from our computation.
        return not self.computed_attribute

    def mayRaiseExceptionAttributeCheck(self, exception_type, attribute_name):
        # Virtual method overload

        # Checking attributes of compile time constants never raises.
        return False

    def computeExpressionOperationNot(self, not_node, trace_collection):
        return trace_collection.getCompileTimeComputationResult(
            node        = not_node,
            computation = lambda : not self.getCompileTimeConstant(),
            description = """\
Compile time constant negation truth value pre-computed."""
        )

    def computeExpressionLen(self, len_node, trace_collection):
        return trace_collection.getCompileTimeComputationResult(
            node        = len_node,
            computation = lambda : len(self.getCompileTimeConstant()),
            description = """\
Compile time constant len value pre-computed."""
        )

    def computeExpressionInt(self, int_node, trace_collection):
        return trace_collection.getCompileTimeComputationResult(
            node        = int_node,
            computation = lambda : int(self.getCompileTimeConstant()),
            description = """\
Compile time constant int value pre-computed."""
        )

    def computeExpressionLong(self, long_node, trace_collection):
        return trace_collection.getCompileTimeComputationResult(
            node        = long_node,
            computation = lambda : long(self.getCompileTimeConstant()),
            description = """\
Compile time constant long value pre-computed."""
        )

    def computeExpressionFloat(self, float_node, trace_collection):
        return trace_collection.getCompileTimeComputationResult(
            node        = float_node,
            computation = lambda : float(self.getCompileTimeConstant()),
            description = """\
Compile time constant float value pre-computed."""
        )

    def computeExpressionBytes(self, bytes_node, trace_collection):
        constant_value = self.getCompileTimeConstant()

        if type(constant_value) in (int, long):
            if constant_value > 1000:
                return bytes_node, None, None

        return trace_collection.getCompileTimeComputationResult(
            node        = bytes_node,
            computation = lambda : bytes(constant_value),
            description = """\
Compile time constant bytes value pre-computed."""
        )

    def isKnownToHaveAttribute(self, attribute_name):
        if self.computed_attribute is None:
            self.computed_attribute = hasattr(self.getCompileTimeConstant(), attribute_name)

        return self.computed_attribute

    def computeExpressionAttribute(self, lookup_node, attribute_name, trace_collection):
        value = self.getCompileTimeConstant()

        if self.computed_attribute is None:
            self.computed_attribute = hasattr(value, attribute_name)

        # If it raises, or the attribute itself is a compile time constant,
        # then do execute it.
        if not self.computed_attribute or \
           isCompileTimeConstantValue(getattr(value, attribute_name)):

            return trace_collection.getCompileTimeComputationResult(
                node        = lookup_node,
                computation = lambda : getattr(value, attribute_name),
                description = "Attribute '%s' pre-computed." % (
                    attribute_name
                )
            )

        return lookup_node, None, None

    def computeExpressionSubscript(self, lookup_node, subscript, trace_collection):
        if subscript.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node        = lookup_node,
                computation = lambda : self.getCompileTimeConstant()[
                    subscript.getCompileTimeConstant()
                ],
                description = "Subscript of constant with constant value."
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

                    return getComputationResult(
                        node        = lookup_node,
                        computation = lambda : self.getCompileTimeConstant()[
                            lower.getCompileTimeConstant() : upper.getCompileTimeConstant()
                        ],
                        description = """\
Slicing of constant with constant indexes."""
                    )
            else:
                if lower.isCompileTimeConstant():
                    return getComputationResult(
                        node        = lookup_node,
                        computation = lambda : self.getCompileTimeConstant()[
                            lower.getCompileTimeConstant() :
                        ],
                        description = """\
Slicing of constant with constant lower index only."""
                    )
        else:
            if upper is not None:
                if upper.isCompileTimeConstant():
                    return getComputationResult(
                        node        = lookup_node,
                        computation = lambda : self.getCompileTimeConstant()[
                            : upper.getCompileTimeConstant()
                        ],
                        description = """\
Slicing of constant with constant upper index only."""
                    )
            else:
                return getComputationResult(
                    node        = lookup_node,
                    computation = lambda : self.getCompileTimeConstant()[ : ],
                    description = "Slicing of constant with no indexes."
                )

        return lookup_node, None, None

    def computeExpressionComparisonIn(self, in_node, value_node, trace_collection):
        if value_node.isCompileTimeConstant():
            return getComputationResult(
                node        = in_node,
                computation = lambda : in_node.getSimulator()(
                    value_node.getCompileTimeConstant(),
                    self.getCompileTimeConstant()
                ),
                description = """\
Predicted '%s' on compiled time constant values.""" % in_node.comparator
            )

        # Look-up of __contains__ on compile time constants does mostly nothing.
        trace_collection.onExceptionRaiseExit(BaseException)

        return in_node, None, None


class ExpressionChildrenHavingBase(ChildrenHavingMixin, ExpressionBase):
    def __init__(self, values, source_ref):
        ExpressionBase.__init__(
            self,
            source_ref = source_ref
        )

        ChildrenHavingMixin.__init__(
            self,
            values = values
        )

    def computeExpressionRaw(self, trace_collection):
        """ Compute an expression.

            Default behavior is to just visit the child expressions first, and
            then the node "computeExpression". For a few cases this needs to
            be overloaded, e.g. conditional expressions.
        """
        # First apply the sub-expressions, as they are evaluated before
        # the actual operation.
        for count, sub_expression in enumerate(self.getVisitableNodes()):
            expression = trace_collection.onExpression(sub_expression)

            if expression.willRaiseException(BaseException):
                sub_expressions = self.getVisitableNodes()

                wrapped_expression = wrapExpressionWithSideEffects(
                    side_effects = sub_expressions[:count],
                    old_node     = sub_expression,
                    new_node     = expression
                )

                return (
                    wrapped_expression,
                    "new_raise",
                    lambda : "For '%s' the child expression '%s' will raise." % (
                        self.getChildNameNice(),
                        expression.getChildNameNice()
                    )
                )

        # Then ask ourselves to work on it.
        return self.computeExpression(
            trace_collection = trace_collection
        )


class ExpressionChildHavingBase(ExpressionBase):
    checker = None

    def __init__(self, value, source_ref):
        ExpressionBase.__init__(
            self,
            source_ref = source_ref
        )

        assert type(self.named_child) is str and self.named_child

        if self.checker is not None:
            value = self.checker(value) # False alarm, pylint: disable=not-callable

        assert type(value) is not list, self.named_child

        if type(value) is tuple:
            assert None not in value, self.named_child

            for val in value:
                val.parent = self
        elif value is not None:
            value.parent = self
        elif value is None:
            pass
        else:
            assert False, type(value)

        attr_name = "subnode_" + self.named_child
        setattr(self, attr_name, value)

    def finalize(self):
        del self.parent

        for c in self.getVisitableNodes():
            c.finalize()

    # TODO: De-duplicate this with multiple child variant.
    def computeExpressionRaw(self, trace_collection):
        """ Compute an expression.

            Default behavior is to just visit the child expressions first, and
            then the node "computeExpression". For a few cases this needs to
            be overloaded, e.g. conditional expressions.
        """
        # First apply the sub-expressions, as they are evaluated before.
        sub_expressions = self.getVisitableNodes()

        for count, sub_expression in enumerate(sub_expressions):
            assert sub_expression.isExpression(), (self, sub_expression)

            expression = trace_collection.onExpression(
                expression = sub_expression
            )

            if expression.willRaiseException(BaseException):
                wrapped_expression = wrapExpressionWithSideEffects(
                    side_effects = sub_expressions[:count],
                    old_node     = sub_expression,
                    new_node     = expression
                )

                return (
                    wrapped_expression,
                    "new_raise",
                    lambda : "For '%s' the child expression '%s' will raise." % (
                        self.getChildNameNice(),
                        expression.getChildNameNice()
                    )
                )

        # Then ask ourselves to work on it.
        return self.computeExpression(
            trace_collection = trace_collection
        )

    def setChild(self, name, value):
        """ Set a child value.

            Do not overload, provider self.checkers instead.
        """
        # Only accept legal child names
        assert name  == self.named_child, name

        # Lists as inputs are OK, but turn them into tuples.
        if type(value) is list:
            value = tuple(value)

        if self.checker is not None:
            value = self.checker(value) # False alarm, pylint: disable=not-callable
        # Re-parent value to us.
        if type(value) is tuple:
            for val in value:
                val.parent = self
        elif value is not None:
            value.parent = self

        attr_name = "subnode_" + name

        # Determine old value, and inform it about loosing its parent.
        old_value = getattr(self, attr_name)

        assert old_value is not value, value

        setattr(self, attr_name, value)

    def getChild(self, name):
        # Only accept legal child names
        attr_name = "subnode_" + name
        return getattr(self, attr_name)

    @staticmethod
    def childGetter(name):
        attr_name = "subnode_" + name

        def getter(self):
            return getattr(self, attr_name)

        return getter

    @staticmethod
    def childSetter(name):
        def setter(self, value):
            self.setChild(name, value)

        return setter

    def getVisitableNodes(self):
        # TODO: Consider if a generator would be faster.
        attr_name = "subnode_" + self.named_child
        value = getattr(self, attr_name)

        if value is None:
            return ()
        elif type(value) is tuple:
            return value
        elif isinstance(value, NodeBase):
            return (value,)
        else:
            raise AssertionError(
                self,
                "has illegal child", value, value.__class__
            )

    def getVisitableNodesNamed(self):
        """ Named children dictionary.

            For use in debugging and XML output.
        """
        attr_name = "subnode_" + self.named_child
        value = getattr(self, attr_name)

        yield self.named_child, value

    def replaceChild(self, old_node, new_node):
        if new_node is not None and not isinstance(new_node, NodeBase):
            raise AssertionError(
                "Cannot replace with", new_node, "old", old_node, "in", self
            )

        # Find the replaced node, as an added difficulty, what might be
        # happening, is that the old node is an element of a tuple, in which we
        # may also remove that element, by setting it to None.
        key = self.named_child
        value = self.getChild(key)

        if value is None:
            pass
        elif type(value) is tuple:
            if old_node in value:
                if new_node is not None:
                    self.setChild(
                        key,
                        tuple(
                            (val if val is not old_node else new_node)
                            for val in
                            value
                        )
                    )
                else:
                    self.setChild(
                        key,
                        tuple(
                            val
                            for val in
                            value
                            if val is not old_node
                        )
                    )

                return key
        elif isinstance(value, NodeBase):
            if old_node is value:
                self.setChild(key, new_node)

                return key
        else:
            assert False, (key, value, value.__class__)

        raise AssertionError(
            "Didn't find child",
            old_node,
            "in",
            self
        )

    def getCloneArgs(self):
        # Make clones of child nodes too.
        values = {}
        key = self.named_child

        value = self.getChild(key)

        assert type(value) is not list, key

        if value is None:
            values[key] = None
        elif type(value) is tuple:
            values[key] = tuple(
                v.makeClone()
                for v in
                value
            )
        else:
            values[key] = value.makeClone()

        values.update(
            self.getDetails()
        )

        return values



class ExpressionSpecBasedComputationBase(ExpressionChildrenHavingBase):
    builtin_spec = None

    def computeBuiltinSpec(self, trace_collection, given_values):
        assert self.builtin_spec is not None, self

        for value in given_values:
            if value is not None and not value.isCompileTimeConstant():
                trace_collection.onExceptionRaiseExit(BaseException)

                return self, None, None

        if not self.builtin_spec.isCompileTimeComputable(given_values):
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

        return trace_collection.getCompileTimeComputationResult(
            node        = self,
            computation = lambda : self.builtin_spec.simulateCall(given_values),
            description = "Built-in call to '%s' pre-computed." % (
                self.builtin_spec.getName()
            )
        )


class ExpressionBuiltinSingleArgBase(ExpressionSpecBasedComputationBase):
    named_children = (
        "value",
    )

    def __init__(self, value, source_ref):
        ExpressionSpecBasedComputationBase.__init__(
            self,
            values     = {
                "value" : value,
            },
            source_ref = source_ref
        )

    getValue = ExpressionChildrenHavingBase.childGetter(
        "value"
    )

    def computeExpression(self, trace_collection):
        value = self.getValue()

        if value is None:
            return self.computeBuiltinSpec(
                trace_collection = trace_collection,
                given_values     = ()
            )
        else:
            return self.computeBuiltinSpec(
                trace_collection = trace_collection,
                given_values     = (value,)
            )
