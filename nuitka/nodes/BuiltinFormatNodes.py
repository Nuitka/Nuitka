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
""" Format related nodes format/bin/oct/hex/ascii.

These will most often be used for outputs, and the hope is, the type prediction or the
result prediction will help to be smarter, but generally these should not be that much
about performance critical.

"""
from nuitka.PythonVersions import python_version
from nuitka.specs import BuiltinParameterSpecs

from .ChildrenHavingMixins import (
    ChildrenHavingValueFormatSpecOptionalAutoNoneEmptyStrMixin,
)
from .ExpressionBases import ExpressionBase, ExpressionBuiltinSingleArgBase
from .ExpressionShapeMixins import (
    ExpressionIntOrLongExactMixin,
    ExpressionStrOrUnicodeExactMixin,
    ExpressionStrShapeExactMixin,
)
from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode


class ExpressionBuiltinFormat(
    ExpressionStrOrUnicodeExactMixin,
    ChildrenHavingValueFormatSpecOptionalAutoNoneEmptyStrMixin,
    ExpressionBase,
):
    kind = "EXPRESSION_BUILTIN_FORMAT"

    named_children = ("value", "format_spec|auto_none_empty_str")

    def __init__(self, value, format_spec, source_ref):
        ChildrenHavingValueFormatSpecOptionalAutoNoneEmptyStrMixin.__init__(
            self,
            value=value,
            format_spec=format_spec,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        # TODO: Can use the format built-in on compile time constants at least.

        value = self.subnode_value
        format_spec = self.subnode_format_spec

        # TODO: Provide "__format__" slot based handling.

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        # Strings format themselves as what they are.
        if format_spec is None:
            if value.hasShapeStrOrUnicodeExact():
                return (
                    value,
                    "new_expression",
                    """\
Removed useless 'format' on '%s' value."""
                    % value.getTypeShape().getTypeName(),
                )

        return self, None, None


class ExpressionBuiltinAscii(
    ExpressionStrShapeExactMixin, ExpressionBuiltinSingleArgBase
):
    kind = "EXPRESSION_BUILTIN_ASCII"

    if python_version >= 0x300:
        builtin_spec = BuiltinParameterSpecs.builtin_ascii_spec


class ExpressionBuiltinBin(
    ExpressionStrShapeExactMixin, ExpressionBuiltinSingleArgBase
):
    kind = "EXPRESSION_BUILTIN_BIN"

    builtin_spec = BuiltinParameterSpecs.builtin_bin_spec


class ExpressionBuiltinOct(
    ExpressionStrShapeExactMixin, ExpressionBuiltinSingleArgBase
):
    kind = "EXPRESSION_BUILTIN_OCT"

    builtin_spec = BuiltinParameterSpecs.builtin_oct_spec


class ExpressionBuiltinHex(
    ExpressionStrShapeExactMixin, ExpressionBuiltinSingleArgBase
):
    kind = "EXPRESSION_BUILTIN_HEX"

    builtin_spec = BuiltinParameterSpecs.builtin_hex_spec


class ExpressionBuiltinId(
    ExpressionIntOrLongExactMixin, ExpressionBuiltinSingleArgBase
):
    kind = "EXPRESSION_BUILTIN_ID"

    builtin_spec = BuiltinParameterSpecs.builtin_id_spec

    def computeExpression(self, trace_collection):
        # Note: Quite impossible to predict the pointer value or anything, but
        # we know the result will be a long.
        return self, None, None

    def mayRaiseException(self, exception_type):
        return self.subnode_value.mayRaiseException(exception_type)

    def getIntValue(self):
        return self

    # TODO: Make use SideEffectsFromChildrenMixin in form of a SideEffectsFromChildMixin
    def computeExpressionDrop(self, statement, trace_collection):
        result = makeStatementExpressionOnlyReplacementNode(
            expression=self.subnode_value, node=self
        )

        del self.parent

        return (
            result,
            "new_statements",
            """\
Removed id taking for unused result.""",
        )

    def mayHaveSideEffects(self):
        return self.subnode_value.mayHaveSideEffects()

    def extractSideEffects(self):
        return self.subnode_value.extractSideEffects()
