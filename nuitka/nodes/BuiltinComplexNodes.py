#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Node for the calls to the 'complex' built-in.

"""
from nuitka.specs import BuiltinParameterSpecs

from .ChildrenHavingMixins import (
    ChildHavingValueMixin,
    ChildrenHavingRealOptionalImagMixin,
)
from .ExpressionBases import (
    ExpressionBase,
    ExpressionSpecBasedComputationMixin,
)
from .ExpressionShapeMixins import ExpressionComplexShapeExactMixin


class ExpressionBuiltinComplex1(
    ExpressionComplexShapeExactMixin, ChildHavingValueMixin, ExpressionBase
):
    kind = "EXPRESSION_BUILTIN_COMPLEX1"

    named_children = ("value",)

    def __init__(self, value, source_ref):
        ChildHavingValueMixin.__init__(self, value=value)

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        value = self.subnode_value

        return value.computeExpressionComplex(
            complex_node=self, trace_collection=trace_collection
        )


class ExpressionBuiltinComplex2(
    ExpressionSpecBasedComputationMixin,
    ExpressionComplexShapeExactMixin,
    ChildrenHavingRealOptionalImagMixin,
    ExpressionBase,
):
    kind = "EXPRESSION_BUILTIN_COMPLEX2"

    named_children = ("real|optional", "imag")

    builtin_spec = BuiltinParameterSpecs.builtin_complex_spec

    def __init__(self, real, imag, source_ref):
        ChildrenHavingRealOptionalImagMixin.__init__(
            self,
            real=real,
            imag=imag,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        given_values = self.subnode_real, self.subnode_imag

        return self.computeBuiltinSpec(
            trace_collection=trace_collection, given_values=given_values
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
