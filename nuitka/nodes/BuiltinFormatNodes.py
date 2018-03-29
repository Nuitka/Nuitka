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
""" Format related nodes format/bin/oct/hex/ascii.

These will most often be used for outputs, and the hope is, the type prediction or the
result prediction will help to be smarter, but generally these should not be that much
about performance critical.

"""
from nuitka.optimizations import BuiltinOptimization
from nuitka.PythonVersions import python_version

from .ExpressionBases import (
    ExpressionBuiltinSingleArgBase,
    ExpressionChildrenHavingBase
)
from .shapes.BuiltinTypeShapes import (
    ShapeTypeIntOrLong,
    ShapeTypeStr,
    ShapeTypeStrOrUnicode
)


class ExpressionBuiltinFormat(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_FORMAT"

    named_children = (
        "value",
        "format_spec"
    )

    def __init__(self, value, format_spec, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "value"       : value,
                "format_spec" : format_spec
            },
            source_ref = source_ref
        )

    def getTypeShape(self):
        return ShapeTypeStrOrUnicode

    def computeExpression(self, trace_collection):
        # TODO: Can use the format built-in on compile time constants at least.

        value = self.getValue()
        format_spec = self.getFormatSpec()

        # Go to default way if possible.
        if format_spec is not None and \
           format_spec.isExpressionConstantStrRef() and \
           not format_spec.getCompileTimeConstant():
            self.setFormatSpec(None)
            format_spec = None

        # Strings format themselves as what they are.
        if format_spec is None:
            if value.hasShapeStrExact() or value.hasShapeUnicodeExact():
                return (
                    value,
                    "new_expression", """\
Removed useless 'format' on '%s' value.""" % value.getTypeShape().getTypeName()
                )

        return self, None, None

    getValue = ExpressionChildrenHavingBase.childGetter("value")
    getFormatSpec = ExpressionChildrenHavingBase.childGetter("format_spec")
    setFormatSpec = ExpressionChildrenHavingBase.childSetter("format_spec")


class ExpressionBuiltinAscii(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_BUILTIN_ASCII"

    if python_version >= 300:
        builtin_spec = BuiltinOptimization.builtin_ascii_spec

    def getTypeShape(self):
        return ShapeTypeStr


class ExpressionBuiltinBin(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_BUILTIN_BIN"

    builtin_spec = BuiltinOptimization.builtin_bin_spec

    def getTypeShape(self):
        return ShapeTypeStr


class ExpressionBuiltinOct(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_BUILTIN_OCT"

    builtin_spec = BuiltinOptimization.builtin_oct_spec

    def getTypeShape(self):
        return ShapeTypeStr


class ExpressionBuiltinHex(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_BUILTIN_HEX"

    builtin_spec = BuiltinOptimization.builtin_hex_spec

    def getTypeShape(self):
        return ShapeTypeStr


class ExpressionBuiltinId(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_BUILTIN_ID"

    builtin_spec = BuiltinOptimization.builtin_id_spec

    def computeExpression(self, trace_collection):
        # Note: Quite impossible to predict the pointer value or anything, but
        # we know the result will be a long.
        return self, None, None

    def getIntValue(self):
        return self

    def getTypeShape(self):
        return ShapeTypeIntOrLong
