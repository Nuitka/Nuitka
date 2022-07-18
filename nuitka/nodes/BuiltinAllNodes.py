#     Copyright 2022, Batakrishna Sahu, mailto:<Batakrishna.Sahu@suiit.ac.in>
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
""" Node for the calls to the 'all' built-in.

"""

from nuitka.specs import BuiltinParameterSpecs

from .ExpressionBases import ExpressionBuiltinSingleArgBase
from .ExpressionShapeMixins import ExpressionBoolShapeExactMixin
from .NodeMakingHelpers import (
    makeConstantReplacementNode,
    makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue,
    wrapExpressionWithNodeSideEffects,
)
from .shapes.BuiltinTypeShapes import tshape_str, tshape_unicode


class ExpressionBuiltinAll(
    ExpressionBoolShapeExactMixin, ExpressionBuiltinSingleArgBase
):
    """Builtin All Node class.

    Args:
        ExpressionBase: 'all - expression'

    Returns:
        Node that represents built-in 'all' call.

    """

    kind = "EXPRESSION_BUILTIN_ALL"

    builtin_spec = BuiltinParameterSpecs.builtin_all_spec

    def computeExpression(self, trace_collection):
        value = self.subnode_value
        shape = value.getTypeShape()
        if shape.hasShapeSlotIter() is False:
            # An exception is raised.
            trace_collection.onExceptionRaiseExit(BaseException)

            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                template="'%s' object is not iterable",
                operation="all",
                original_node=value,
                value_node=value,
            )

        if shape in (tshape_str, tshape_unicode):
            return (
                wrapExpressionWithNodeSideEffects(
                    new_node=makeConstantReplacementNode(
                        constant=True, node=self, user_provided=False
                    ),
                    old_node=value,
                ),
                "new_constant",
                "Predicted truth value of built-in 'all' string type argument",
            )

        iteration_handle = value.getIterationHandle()

        if iteration_handle is not None:
            all_true = iteration_handle.getAllElementTruthValue()

            if all_true is not None:
                result = wrapExpressionWithNodeSideEffects(
                    new_node=makeConstantReplacementNode(
                        constant=all_true, node=self, user_provided=False
                    ),
                    old_node=value,
                )

                return (
                    result,
                    "new_constant",
                    "Predicted truth value of built-in 'all' argument",
                )

        self.onContentEscapes(trace_collection)

        # All code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # All exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        """returns boolean True if try/except/finally is needed else False"""
        value = self.subnode_value

        if value.mayRaiseException(exception_type):
            return True

        return not value.getTypeShape().hasShapeSlotIter()
