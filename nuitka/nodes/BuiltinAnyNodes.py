#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
#                     Batakrishna Sahu, mailto:batakrishna.sahu@suiit.ac.in
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
""" Node for the calls to the 'any' built-in.

"""

from nuitka.specs import BuiltinParameterSpecs

from .ExpressionBases import ExpressionBuiltinSingleArgBase
from .shapes.BuiltinTypeShapes import ShapeTypeBool
from .NodeMakingHelpers import wrapExpressionWithNodeSideEffects, makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue
from .NodeMakingHelpers import makeConstantReplacementNode

class ExpressionBuiltinAny(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_BUILTIN_ANY"

    builtin_spec = BuiltinParameterSpecs.builtin_any_spec

    def computeExpression(self, trace_collection):

        value = self.getValue()
        shape = value.getTypeShape()

        if shape.hasShapeSlotIter() is False:
            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                template="'%s' object is not iterable",
                operation="any",
                original_node=value,
                value_node=value,
            )

        iteration_length = value.getIterationLength()

        if iteration_length is not None and iteration_length < 256 and value.canPredictIterationValues():
            all_false = True
            for i in range(value.getIterationLength()):
                truth_value = value.getIterationValue(i).getTruthValue()

                if truth_value is True:
                    result = wrapExpressionWithNodeSideEffects(
                        new_node=makeConstantReplacementNode(
                            constant=True, node=self
                        ),
                        old_node=value,
                    )

                    return (
                        result,
                        "new_constant",
                        "Predicted truth value of built-in any argument",
                    )
                elif truth_value is None:
                    all_false = False
            if all_false is True:
                result = wrapExpressionWithNodeSideEffects(
                    new_node=makeConstantReplacementNode(
                        constant=False, node=self
                    ),
                    old_node=value,
                )

                return (
                    result,
                    "new_constant",
                    "Predicted truth value of built-in any argument",
                )
            else:
                return self, None, None

        else:
            return self, None, None


        return self.getValue().computeExpressionAny(
            any_node         = self,
            trace_collection = trace_collection
        )

    def getTypeShape(self):
        return ShapeTypeBool

    def mayRaiseException(self, exception_type):
        value = self.getValue()

        if value.mayRaiseException(exception_type):
            return True

        return not value.getTypeShape().hasShapeSlotIter()
