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
""" Built-in iterator nodes.

These play a role in for loops, and in unpacking. They can something be
predicted to succeed or fail, in which case, code can become less complex.

The length of things is an important optimization issue for these to be
good.
"""

from nuitka.optimizations import BuiltinOptimization

from .ExpressionBases import ExpressionBuiltinSingleArgBase
from .shapes.BuiltinTypeShapes import ShapeTypeIntOrLong


class ExpressionBuiltinLen(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_BUILTIN_LEN"

    builtin_spec = BuiltinOptimization.builtin_len_spec

    def getIntegerValue(self):
        value = self.getValue()

        if value.hasShapeSlotLen():
            return value.getIterationLength()
        else:
            return None

    def computeExpression(self, trace_collection):
        return self.getValue().computeExpressionLen(
            len_node         = self,
            trace_collection = trace_collection
        )

    def getTypeShape(self):
        return ShapeTypeIntOrLong

    def mayRaiseException(self, exception_type):
        value = self.getValue()

        if value.mayRaiseException(exception_type):
            return True

        return not value.getTypeShape().hasShapeSlotLen()
