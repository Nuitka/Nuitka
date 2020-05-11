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
""" Format related nodes format/bin/oct/hex/ascii.

These will most often be used for outputs, and the hope is, the type prediction or the
result prediction will help to be smarter, but generally these should not be that much
about performance critical.

"""
from nuitka.PythonVersions import python_version
from nuitka.specs import BuiltinParameterSpecs

from .ExpressionBases import (
    ExpressionBuiltinSingleArgBase,
    ExpressionChildrenHavingBase,
)
from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode
from .shapes.BuiltinTypeShapes import (
    tshape_int_or_long,
    tshape_str,
    tshape_str_or_unicode,
)


class ExpressionBuiltinFormat(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_FORMAT"

    named_children = ("value", "format_spec")
    getValue = ExpressionChildrenHavingBase.childGetter("value")
    getFormatSpec = ExpressionChildrenHavingBase.childGetter("format_spec")
    setFormatSpec = ExpressionChildrenHavingBase.childSetter("format_spec")

    def __init__(self, value, format_spec, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values={"value": value, "format_spec": format_spec},
            source_ref=source_ref,
        )

    def getTypeShape(self):
        return tshape_str_or_unicode

    def computeExpression(self, trace_collection):
        # TODO: Can use the format built-in on compile time constants at least.

        value = self.getValue()
        format_spec = self.getFormatSpec()

        # Go to default way if possible.
        if (
            format_spec is not None
            and format_spec.isExpressionConstantStrRef()
            and not format_spec.getCompileTimeConstant()
        ):
            self.setFormatSpec(None)
            format_spec = None

        # Strings format themselves as what they are.
        if format_spec is None:
            if value.hasShapeStrExact() or value.hasShapeUnicodeExact():
                return (
                    value,
                    "new_expression",
                    """\
Removed useless 'format' on '%s' value."""
                    % value.getTypeShape().getTypeName(),
                )

        # TODO: Provide "__format__" slot based handling.

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionBuiltinAscii(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_BUILTIN_ASCII"

    if python_version >= 300:
        builtin_spec = BuiltinParameterSpecs.builtin_ascii_spec

    def getTypeShape(self):
        return tshape_str


class ExpressionBuiltinBin(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_BUILTIN_BIN"

    builtin_spec = BuiltinParameterSpecs.builtin_bin_spec

    def getTypeShape(self):
        return tshape_str


class ExpressionBuiltinOct(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_BUILTIN_OCT"

    builtin_spec = BuiltinParameterSpecs.builtin_oct_spec

    def getTypeShape(self):
        return tshape_str


class ExpressionBuiltinHex(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_BUILTIN_HEX"

    builtin_spec = BuiltinParameterSpecs.builtin_hex_spec

    def getTypeShape(self):
        return tshape_str


class ExpressionBuiltinId(ExpressionBuiltinSingleArgBase):
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

    def getTypeShape(self):
        return tshape_int_or_long

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
        return (self.subnode_value,)
