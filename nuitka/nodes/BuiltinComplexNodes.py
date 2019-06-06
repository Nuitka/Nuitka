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
""" Node for the calls to the 'complex' built-in.

"""
from nuitka.specs import BuiltinParameterSpecs

from .ExpressionBases import (
    ExpressionChildrenHavingBase,
    ExpressionSpecBasedComputationBase,
)
from .shapes.BuiltinTypeShapes import ShapeTypeComplex


class ExpressionBuiltinComplex1(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_COMPLEX1"

    named_children = ("value",)

    def __init__(self, value, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self, values={"value": value}, source_ref=source_ref
        )

    def getTypeShape(self):
        # Note: The complex built-in will convert overloads from __complex__
        # slot and create a new one instead.
        return ShapeTypeComplex

    def computeExpression(self, trace_collection):
        value = self.getValue()

        return value.computeExpressionComplex(
            complex_node=self, trace_collection=trace_collection
        )

    getValue = ExpressionChildrenHavingBase.childGetter("value")


class ExpressionBuiltinComplex2(ExpressionSpecBasedComputationBase):
    kind = "EXPRESSION_BUILTIN_COMPLEX2"

    named_children = ("real", "imag")

    builtin_spec = BuiltinParameterSpecs.builtin_complex_spec

    def __init__(self, real, imag, source_ref):
        ExpressionSpecBasedComputationBase.__init__(
            self, values={"real": real, "imag": imag}, source_ref=source_ref
        )

    getReal = ExpressionSpecBasedComputationBase.childGetter("real")
    getImag = ExpressionSpecBasedComputationBase.childGetter("imag")

    def computeExpression(self, trace_collection):
        given_values = self.subnode_real, self.subnode_imag

        return self.computeBuiltinSpec(
            trace_collection=trace_collection, given_values=given_values
        )

    def getTypeShape(self):
        return ShapeTypeComplex
