#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Node for the calls to the 'int' and 'long' (Python2) built-ins.

These are divided into variants for one and two arguments and they have a
common base class, because most of the behavior is the same there. The ones
with 2 arguments only work on strings, and give errors otherwise, the ones
with one argument, use slots, "__int__" and "__long__", so what they do does
largely depend on the arguments slot.
"""

from nuitka.__past__ import long  # pylint: disable=I0021,redefined-builtin
from nuitka.PythonVersions import python_version
from nuitka.specs import BuiltinParameterSpecs

from .ConstantRefNodes import makeConstantRefNode
from .ExpressionBases import (
    ExpressionChildrenHavingBase,
    ExpressionSpecBasedComputationBase,
)
from .shapes.BuiltinTypeShapes import (
    ShapeTypeIntOrLong,
    ShapeTypeIntOrLongDerived,
    ShapeTypeLong,
    ShapeTypeLongDerived,
)


class ExpressionBuiltinInt1(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_INT1"

    named_children = ("value",)

    def __init__(self, value, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self, values={"value": value}, source_ref=source_ref
        )

    def getTypeShape(self):
        # TODO: Depending on input type shape and value, we should improve this.
        return ShapeTypeIntOrLongDerived

    def computeExpression(self, trace_collection):
        value = self.getValue()

        return value.computeExpressionInt(
            int_node=self, trace_collection=trace_collection
        )

    getValue = ExpressionChildrenHavingBase.childGetter("value")


class ExpressionBuiltinIntLong2Base(ExpressionSpecBasedComputationBase):
    named_children = ("value", "base")

    # Note: Version specific, may be allowed or not.
    try:
        int(base=2)
    except TypeError:
        base_only_value = False
    else:
        base_only_value = True

    # To be overloaded by child classes with int/long.
    builtin = int

    def __init__(self, value, base, source_ref):
        if value is None and self.base_only_value:
            value = makeConstantRefNode(
                constant="0", source_ref=source_ref, user_provided=True
            )

        ExpressionSpecBasedComputationBase.__init__(
            self, values={"value": value, "base": base}, source_ref=source_ref
        )

    getValue = ExpressionSpecBasedComputationBase.childGetter("value")
    getBase = ExpressionSpecBasedComputationBase.childGetter("base")

    def computeExpression(self, trace_collection):
        value = self.subnode_value
        base = self.subnode_base

        if value is None:
            if base is not None:
                if not self.base_only_value:
                    return trace_collection.getCompileTimeComputationResult(
                        node=self,
                        computation=lambda: self.builtin(base=2),
                        description="""\
%s built-in call with only base argument"""
                        % self.builtin.__name__,
                    )

            given_values = ()
        else:
            given_values = (value, base)

        return self.computeBuiltinSpec(
            trace_collection=trace_collection, given_values=given_values
        )


class ExpressionBuiltinInt2(ExpressionBuiltinIntLong2Base):
    kind = "EXPRESSION_BUILTIN_INT2"

    builtin_spec = BuiltinParameterSpecs.builtin_int_spec
    builtin = int

    def getTypeShape(self):
        return ShapeTypeIntOrLong


if python_version < 300:

    class ExpressionBuiltinLong1(ExpressionChildrenHavingBase):
        kind = "EXPRESSION_BUILTIN_LONG1"

        named_children = ("value",)

        def __init__(self, value, source_ref):
            ExpressionChildrenHavingBase.__init__(
                self, values={"value": value}, source_ref=source_ref
            )

        def getTypeShape(self):
            # TODO: Depending on input type shape and value, we should improve this.
            return ShapeTypeLongDerived

        def computeExpression(self, trace_collection):
            return self.subnode_value.computeExpressionLong(
                long_node=self, trace_collection=trace_collection
            )

        getValue = ExpressionChildrenHavingBase.childGetter("value")

        def mayRaiseException(self, exception_type):
            return self.subnode_value.mayRaiseExceptionLong(exception_type)

    class ExpressionBuiltinLong2(ExpressionBuiltinIntLong2Base):
        kind = "EXPRESSION_BUILTIN_LONG2"

        builtin_spec = BuiltinParameterSpecs.builtin_long_spec
        builtin = long

        def getTypeShape(self):
            return ShapeTypeLong
