#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Built-in type nodes tuple/list/set/float/str/unicode etc.

These are all very simple and have predictable properties, because we know their type and
that should allow some important optimizations.
"""

from nuitka.specs import BuiltinParameterSpecs

from .ChildrenHavingMixins import (
    ChildHavingValueMixin,
    ChildrenExpressionBuiltinBytearray3Mixin,
    ChildrenExpressionTypeOperationPrepareMixin,
    ChildrenHavingValueOptionalEncodingOptionalErrorsOptionalMixin,
)
from .ConstantRefNodes import makeConstantRefNode
from .ExpressionBases import (
    CompileTimeConstantExpressionBase,
    ExpressionBase,
    ExpressionBuiltinSingleArgBase,
    ExpressionSpecBasedComputationMixin,
)
from .ExpressionShapeMixins import (
    ExpressionBoolShapeExactMixin,
    ExpressionBytearrayShapeExactMixin,
    ExpressionBytesShapeExactMixin,
    ExpressionFrozensetShapeExactMixin,
    ExpressionListShapeExactMixin,
    ExpressionSetShapeExactMixin,
    ExpressionStrDerivedShapeMixin,
    ExpressionStrOrUnicodeDerivedShapeMixin,
    ExpressionTupleShapeExactMixin,
)
from .NodeMakingHelpers import (
    makeConstantReplacementNode,
    wrapExpressionWithNodeSideEffects,
)
from .shapes.BuiltinTypeShapes import (
    tshape_bytes_derived,
    tshape_float_derived,
    tshape_str_derived,
    tshape_unicode_derived,
)


class ExpressionBuiltinTypeBase(ExpressionBuiltinSingleArgBase):
    pass


class ExpressionBuiltinContainerBase(
    ExpressionSpecBasedComputationMixin, ChildHavingValueMixin, ExpressionBase
):
    # For overload.
    builtin_spec = None

    named_children = ("value",)

    def __init__(self, value, source_ref):
        ChildHavingValueMixin.__init__(self, value=value)

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        value = self.subnode_value

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
            # They take over the variable content, exposing it to currently untraced usages.
            value.onContentEscapes(trace_collection)

            return self.computeBuiltinSpec(
                trace_collection=trace_collection, given_values=(value,)
            )


class ExpressionBuiltinTuple(
    ExpressionTupleShapeExactMixin, ExpressionBuiltinContainerBase
):
    kind = "EXPRESSION_BUILTIN_TUPLE"

    builtin_spec = BuiltinParameterSpecs.builtin_tuple_spec


class ExpressionBuiltinList(
    ExpressionListShapeExactMixin, ExpressionBuiltinContainerBase
):
    kind = "EXPRESSION_BUILTIN_LIST"

    builtin_spec = BuiltinParameterSpecs.builtin_list_spec


class ExpressionBuiltinSet(
    ExpressionSetShapeExactMixin, ExpressionBuiltinContainerBase
):
    kind = "EXPRESSION_BUILTIN_SET"

    builtin_spec = BuiltinParameterSpecs.builtin_set_spec


class ExpressionBuiltinFrozenset(
    ExpressionFrozensetShapeExactMixin, ExpressionBuiltinContainerBase
):
    kind = "EXPRESSION_BUILTIN_FROZENSET"

    builtin_spec = BuiltinParameterSpecs.builtin_frozenset_spec


class ExpressionBuiltinFloat(ChildHavingValueMixin, ExpressionBase):
    kind = "EXPRESSION_BUILTIN_FLOAT"

    named_children = ("value",)

    def __init__(self, value, source_ref):
        ChildHavingValueMixin.__init__(self, value=value)

        ExpressionBase.__init__(self, source_ref)

    @staticmethod
    def getTypeShape():
        # TODO: Depending on input type shape, we should improve this.
        return tshape_float_derived

    def computeExpression(self, trace_collection):
        return self.subnode_value.computeExpressionFloat(
            float_node=self, trace_collection=trace_collection
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_value.mayRaiseExceptionFloat(exception_type)


class ExpressionBuiltinBool(ExpressionBoolShapeExactMixin, ExpressionBuiltinTypeBase):
    kind = "EXPRESSION_BUILTIN_BOOL"

    builtin_spec = BuiltinParameterSpecs.builtin_bool_spec

    def computeExpression(self, trace_collection):
        value = self.subnode_value

        truth_value = value.getTruthValue()

        if truth_value is not None:
            result = wrapExpressionWithNodeSideEffects(
                new_node=makeConstantReplacementNode(
                    constant=truth_value, node=self, user_provided=False
                ),
                old_node=value,
            )

            return (
                result,
                "new_constant",
                "Predicted truth value of built-in bool argument",
            )

        if value.hasShapeBoolExact():
            return (
                value,
                "new_expression",
                "Eliminated boolean conversion of boolean value.",
            )

        return ExpressionBuiltinTypeBase.computeExpression(self, trace_collection)

    def mayRaiseException(self, exception_type):
        return self.subnode_value.mayRaiseException(
            exception_type
        ) or self.subnode_value.mayRaiseExceptionBool(exception_type)


class ExpressionBuiltinUnicodeBase(
    ExpressionSpecBasedComputationMixin,
    ChildrenHavingValueOptionalEncodingOptionalErrorsOptionalMixin,
    ExpressionBase,
):
    named_children = ("value|optional", "encoding|optional", "errors|optional")

    def __init__(self, value, encoding, errors, source_ref):
        ChildrenHavingValueOptionalEncodingOptionalErrorsOptionalMixin.__init__(
            self,
            value=value,
            encoding=encoding,
            errors=errors,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        args = [self.subnode_value, self.subnode_encoding, self.subnode_errors]

        while args and args[-1] is None:
            del args[-1]

        # The value of that node escapes and could change its contents.
        if self.subnode_value is not None:
            trace_collection.onValueEscapeStr(self.subnode_value)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        return self.computeBuiltinSpec(
            trace_collection=trace_collection, given_values=tuple(args)
        )


class ExpressionBuiltinStrP2(
    ExpressionStrOrUnicodeDerivedShapeMixin, ExpressionBuiltinTypeBase
):
    """Python2 built-in str call."""

    kind = "EXPRESSION_BUILTIN_STR_P2"

    builtin_spec = BuiltinParameterSpecs.builtin_str_spec

    def computeExpression(self, trace_collection):
        (
            new_node,
            change_tags,
            change_desc,
        ) = ExpressionBuiltinTypeBase.computeExpression(self, trace_collection)

        if new_node is self:
            str_value = self.subnode_value.getStrValue()

            if str_value is not None:
                new_node = wrapExpressionWithNodeSideEffects(
                    new_node=str_value, old_node=self.subnode_value
                )

                change_tags = "new_expression"
                change_desc = "Predicted 'str' built-in result"

        return new_node, change_tags, change_desc

    @staticmethod
    def getTypeShape():
        return tshape_str_derived


class ExpressionBuiltinUnicodeP2(ExpressionBuiltinUnicodeBase):
    """Python2 built-in unicode call."""

    kind = "EXPRESSION_BUILTIN_UNICODE_P2"

    builtin_spec = BuiltinParameterSpecs.builtin_unicode_p2_spec

    @staticmethod
    def getTypeShape():
        return tshape_unicode_derived


class ExpressionBuiltinStrP3(
    ExpressionStrDerivedShapeMixin, ExpressionBuiltinUnicodeBase
):
    """Python3 built-in str call."""

    kind = "EXPRESSION_BUILTIN_STR_P3"

    builtin_spec = BuiltinParameterSpecs.builtin_str_spec

    @staticmethod
    def getTypeShape():
        return tshape_str_derived


class ExpressionBuiltinBytes3(
    ExpressionBytesShapeExactMixin, ExpressionBuiltinUnicodeBase
):
    kind = "EXPRESSION_BUILTIN_BYTES3"

    builtin_spec = BuiltinParameterSpecs.builtin_bytes_p3_spec


class ExpressionBuiltinBytes1(ChildHavingValueMixin, ExpressionBase):
    kind = "EXPRESSION_BUILTIN_BYTES1"

    named_children = ("value",)

    def __init__(self, value, source_ref):
        ChildHavingValueMixin.__init__(self, value=value)

        ExpressionBase.__init__(self, source_ref)

    @staticmethod
    def getTypeShape():
        # TODO: Depending on input type shape, we should improve this.
        return tshape_bytes_derived

    def computeExpression(self, trace_collection):
        return self.subnode_value.computeExpressionBytes(
            bytes_node=self, trace_collection=trace_collection
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_value.mayRaiseExceptionBytes(exception_type)


class ExpressionBuiltinBytearray1(
    ExpressionBytearrayShapeExactMixin, ExpressionBuiltinTypeBase
):
    kind = "EXPRESSION_BUILTIN_BYTEARRAY1"

    builtin_spec = BuiltinParameterSpecs.builtin_bytearray_spec

    def __init__(self, value, source_ref):
        ExpressionBuiltinTypeBase.__init__(self, value=value, source_ref=source_ref)


class ExpressionBuiltinBytearray3(
    ExpressionBytearrayShapeExactMixin,
    ChildrenExpressionBuiltinBytearray3Mixin,
    ExpressionBase,
):
    kind = "EXPRESSION_BUILTIN_BYTEARRAY3"

    named_children = ("string", "encoding|optional", "errors|optional")

    builtin_spec = BuiltinParameterSpecs.builtin_bytearray_spec

    def __init__(self, string, encoding, errors, source_ref):
        ChildrenExpressionBuiltinBytearray3Mixin.__init__(
            self,
            string=string,
            encoding=encoding,
            errors=errors,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionConstantGenericAlias(CompileTimeConstantExpressionBase):
    kind = "EXPRESSION_CONSTANT_GENERIC_ALIAS"

    __slots__ = ("generic_alias",)

    def __init__(self, generic_alias, source_ref):
        CompileTimeConstantExpressionBase.__init__(self, source_ref)

        self.generic_alias = generic_alias

    def finalize(self):
        del self.parent

    def getDetails(self):
        return {"generic_alias": self.generic_alias}

    def getCompileTimeConstant(self):
        return self.generic_alias

    def getStrValue(self):
        return makeConstantRefNode(
            constant=str(self.getCompileTimeConstant()),
            user_provided=True,
            source_ref=self.source_ref,
        )

    def computeExpressionRaw(self, trace_collection):
        # Nothing much to do.
        return self, None, None


class ExpressionConstantUnionType(CompileTimeConstantExpressionBase):
    kind = "EXPRESSION_CONSTANT_UNION_TYPE"

    __slots__ = ("union_type",)

    def __init__(self, union_type, source_ref):
        CompileTimeConstantExpressionBase.__init__(self, source_ref)

        self.union_type = union_type

    def finalize(self):
        del self.parent

    def getDetails(self):
        return {"union_type": self.union_type}

    def getCompileTimeConstant(self):
        return self.union_type

    def getStrValue(self):
        return makeConstantRefNode(
            constant=str(self.getCompileTimeConstant()),
            user_provided=True,
            source_ref=self.source_ref,
        )

    def computeExpressionRaw(self, trace_collection):
        # Nothing much to do.
        return self, None, None


class ExpressionTypeOperationPrepare(
    ChildrenExpressionTypeOperationPrepareMixin, ExpressionBase
):
    kind = "EXPRESSION_TYPE_OPERATION_PREPARE"

    named_children = ("type_arg", "args|optional", "kwargs|optional")

    def __init__(self, type_arg, args, kwargs, source_ref):
        ChildrenExpressionTypeOperationPrepareMixin.__init__(
            self, type_arg=type_arg, args=args, kwargs=kwargs
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_type_arg.isExpressionConstantTypeTypeRef():
            result = makeConstantReplacementNode(
                constant={}, node=self, user_provided=False
            )

            return (
                result,
                "new_constant",
                "Predicted result 'type.__prepare__' as empty dict.",
            )

        return self, None, None


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
