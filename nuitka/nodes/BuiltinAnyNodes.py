#     Copyright 2023, Batakrishna Sahu, mailto:<Batakrishna.Sahu@suiit.ac.in>
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
from .ExpressionShapeMixins import ExpressionBoolShapeExactMixin
from .NodeMakingHelpers import (
    makeConstantReplacementNode,
    makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue,
    wrapExpressionWithNodeSideEffects,
)


class ExpressionBuiltinAny(
    ExpressionBoolShapeExactMixin, ExpressionBuiltinSingleArgBase
):
    """Builtin Any Node class.

    Node that represents built-in 'any' call.

    """

    kind = "EXPRESSION_BUILTIN_ANY"

    builtin_spec = BuiltinParameterSpecs.builtin_any_spec

    def computeExpression(self, trace_collection):
        value = self.subnode_value
        shape = value.getTypeShape()
        if shape.hasShapeSlotIter() is False:
            # An exception is raised.
            trace_collection.onExceptionRaiseExit(BaseException)

            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                template="'%s' object is not iterable",
                operation="any",
                original_node=value,
                value_node=value,
            )

        iteration_handle = value.getIterationHandle()

        if iteration_handle is not None:
            all_false = True
            count = 0
            while True:
                truth_value = iteration_handle.getNextValueTruth()
                if truth_value is StopIteration:
                    break
                if count > 256:
                    all_false = False
                    break

                if truth_value is True:
                    result = wrapExpressionWithNodeSideEffects(
                        new_node=makeConstantReplacementNode(
                            constant=True, node=self, user_provided=False
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

                count += 1

            if all_false is True:
                result = wrapExpressionWithNodeSideEffects(
                    new_node=makeConstantReplacementNode(
                        constant=False, node=self, user_provided=False
                    ),
                    old_node=value,
                )

                return (
                    result,
                    "new_constant",
                    "Predicted truth value of built-in any argument",
                )

        self.onContentEscapes(trace_collection)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        """returns boolean True if exception is raised else False"""
        value = self.subnode_value

        if value.mayRaiseException(exception_type):
            return True

        return not value.getTypeShape().hasShapeSlotIter()
