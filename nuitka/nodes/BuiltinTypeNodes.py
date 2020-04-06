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
""" Built-in type nodes tuple/list/set/float/str/unicode etc.

These are all very simple and have predictable properties, because we know their type and
that should allow some important optimizations.
"""

from nuitka.PythonVersions import python_version
from nuitka.specs import BuiltinParameterSpecs

from .ExpressionBases import (
    ExpressionBuiltinSingleArgBase,
    ExpressionChildHavingBase,
    ExpressionChildrenHavingBase,
    ExpressionSpecBasedComputationMixin,
)
from .NodeMakingHelpers import (
    makeConstantReplacementNode,
    wrapExpressionWithNodeSideEffects,
)
from .shapes.BuiltinTypeShapes import (
    tshape_bool,
    tshape_bytearray,
    tshape_bytes,
    tshape_bytes_derived,
    tshape_float_derived,
    tshape_frozenset,
    tshape_list,
    tshape_set,
    tshape_str_derived,
    tshape_tuple,
    tshape_unicode_derived,
)


class ExpressionBuiltinTypeBase(ExpressionBuiltinSingleArgBase):
    pass


class ExpressionBuiltinContainerBase(
    ExpressionSpecBasedComputationMixin, ExpressionChildHavingBase
):

    builtin_spec = None

    named_child = "value"
    getValue = ExpressionChildHavingBase.childGetter("value")

    def __init__(self, value, source_ref):
        ExpressionChildHavingBase.__init__(self, value=value, source_ref=source_ref)

    def computeExpression(self, trace_collection):
        value = self.getValue()

        if value is None:
            return self.computeBuiltinSpec(
                trace_collection=trace_collection, given_values=()
            )
        elif value.isExpressionConstantXrangeRef():
            if value.getIterationLength() <= 256:
                return self.computeBuiltinSpec(
                    trace_collection=trace_collection, given_values=(value,)
                )
            else:
                return self, None, None
        else:
            return self.computeBuiltinSpec(
                trace_collection=trace_collection, given_values=(value,)
            )


class ExpressionBuiltinTuple(ExpressionBuiltinContainerBase):
    kind = "EXPRESSION_BUILTIN_TUPLE"

    builtin_spec = BuiltinParameterSpecs.builtin_tuple_spec

    def getTypeShape(self):
        return tshape_tuple


class ExpressionBuiltinList(ExpressionBuiltinContainerBase):
    kind = "EXPRESSION_BUILTIN_LIST"

    builtin_spec = BuiltinParameterSpecs.builtin_list_spec

    def getTypeShape(self):
        return tshape_list


class ExpressionBuiltinSet(ExpressionBuiltinContainerBase):
    kind = "EXPRESSION_BUILTIN_SET"

    builtin_spec = BuiltinParameterSpecs.builtin_set_spec

    def getTypeShape(self):
        return tshape_set


class ExpressionBuiltinFrozenset(ExpressionBuiltinContainerBase):
    kind = "EXPRESSION_BUILTIN_FROZENSET"

    builtin_spec = BuiltinParameterSpecs.builtin_frozenset_spec

    def getTypeShape(self):
        return tshape_frozenset


class ExpressionBuiltinFloat(ExpressionChildHavingBase):
    kind = "EXPRESSION_BUILTIN_FLOAT"

    named_child = "value"
    getValue = ExpressionChildHavingBase.childGetter("value")

    def __init__(self, value, source_ref):
        ExpressionChildHavingBase.__init__(self, value=value, source_ref=source_ref)

    def getTypeShape(self):
        # TODO: Depending on input type shape, we should improve this.
        return tshape_float_derived

    def computeExpression(self, trace_collection):
        return self.subnode_value.computeExpressionFloat(
            float_node=self, trace_collection=trace_collection
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_value.mayRaiseExceptionFloat(exception_type)


class ExpressionBuiltinBool(ExpressionBuiltinTypeBase):
    kind = "EXPRESSION_BUILTIN_BOOL"

    builtin_spec = BuiltinParameterSpecs.builtin_bool_spec

    def computeExpression(self, trace_collection):
        value = self.getValue()

        if value is not None:
            truth_value = self.getValue().getTruthValue()

            if truth_value is not None:
                result = wrapExpressionWithNodeSideEffects(
                    new_node=makeConstantReplacementNode(
                        constant=truth_value, node=self
                    ),
                    old_node=self.getValue(),
                )

                return (
                    result,
                    "new_constant",
                    "Predicted truth value of built-in bool argument",
                )

        return ExpressionBuiltinTypeBase.computeExpression(self, trace_collection)

    def getTypeShape(self):
        # Note: Not allowed to subclass bool.
        return tshape_bool


class ExpressionBuiltinUnicodeBase(
    ExpressionSpecBasedComputationMixin, ExpressionChildrenHavingBase
):
    named_children = ("value", "encoding", "errors")
    getValue = ExpressionChildrenHavingBase.childGetter("value")
    getEncoding = ExpressionChildrenHavingBase.childGetter("encoding")
    getErrors = ExpressionChildrenHavingBase.childGetter("errors")

    def __init__(self, value, encoding, errors, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values={"value": value, "encoding": encoding, "errors": errors},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        args = [self.getValue(), self.getEncoding(), self.getErrors()]

        while args and args[-1] is None:
            del args[-1]

        for arg in args:
            # The value of that node escapes and could change its contents.
            trace_collection.removeKnowledge(arg)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        return self.computeBuiltinSpec(
            trace_collection=trace_collection, given_values=tuple(args)
        )


if python_version < 300:

    class ExpressionBuiltinStr(ExpressionBuiltinTypeBase):
        kind = "EXPRESSION_BUILTIN_STR"

        builtin_spec = BuiltinParameterSpecs.builtin_str_spec

        def computeExpression(self, trace_collection):
            new_node, change_tags, change_desc = ExpressionBuiltinTypeBase.computeExpression(
                self, trace_collection
            )

            if new_node is self:
                str_value = self.getValue().getStrValue()

                if str_value is not None:
                    new_node = wrapExpressionWithNodeSideEffects(
                        new_node=str_value, old_node=self.getValue()
                    )

                    change_tags = "new_expression"
                    change_desc = "Predicted 'str' built-in result"

            return new_node, change_tags, change_desc

        def getTypeShape(self):
            return tshape_str_derived

    class ExpressionBuiltinUnicode(ExpressionBuiltinUnicodeBase):
        kind = "EXPRESSION_BUILTIN_UNICODE"

        builtin_spec = BuiltinParameterSpecs.builtin_unicode_spec

        def getTypeShape(self):
            return tshape_unicode_derived


else:

    class ExpressionBuiltinStr(ExpressionBuiltinUnicodeBase):
        kind = "EXPRESSION_BUILTIN_STR"

        builtin_spec = BuiltinParameterSpecs.builtin_str_spec

        def getTypeShape(self):
            return tshape_str_derived

    class ExpressionBuiltinBytes3(ExpressionBuiltinUnicodeBase):
        kind = "EXPRESSION_BUILTIN_BYTES3"

        builtin_spec = BuiltinParameterSpecs.builtin_bytes_spec

        def getTypeShape(self):
            return tshape_bytes

    class ExpressionBuiltinBytes1(ExpressionChildHavingBase):
        kind = "EXPRESSION_BUILTIN_BYTES1"

        named_child = "value"
        getValue = ExpressionChildHavingBase.childGetter("value")

        def __init__(self, value, source_ref):
            ExpressionChildHavingBase.__init__(self, value=value, source_ref=source_ref)

        def getTypeShape(self):
            # TODO: Depending on input type shape, we should improve this.
            return tshape_bytes_derived

        def computeExpression(self, trace_collection):
            return self.subnode_value.computeExpressionBytes(
                bytes_node=self, trace_collection=trace_collection
            )

        def mayRaiseException(self, exception_type):
            return self.subnode_value.mayRaiseExceptionBytes(exception_type)


class ExpressionBuiltinBytearray1(ExpressionBuiltinTypeBase):
    kind = "EXPRESSION_BUILTIN_BYTEARRAY1"

    builtin_spec = BuiltinParameterSpecs.builtin_bytearray_spec

    def __init__(self, value, source_ref):
        ExpressionBuiltinTypeBase.__init__(self, value=value, source_ref=source_ref)

    def getTypeShape(self):
        return tshape_bytearray


class ExpressionBuiltinBytearray3(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_BYTEARRAY3"

    named_children = ("string", "encoding", "errors")
    getStringArg = ExpressionChildrenHavingBase.childGetter("string")
    getEncoding = ExpressionChildrenHavingBase.childGetter("encoding")
    getErrors = ExpressionChildrenHavingBase.childGetter("errors")

    builtin_spec = BuiltinParameterSpecs.builtin_bytearray_spec

    def __init__(self, string, encoding, errors, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values={"string": string, "encoding": encoding, "errors": errors},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def getTypeShape(self):
        return tshape_bytearray
