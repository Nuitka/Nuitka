#     Copyright 2020, Batakrishna Sahu, mailto:<Batakrishna.Sahu@suiit.ac.in> find license text at end of file


"""Node for the calls to the 'any' built-in."""

from nuitka.specs import BuiltinParameterSpecs

from .ExpressionBases import ExpressionBuiltinSingleArgBase
from .ExpressionShapeMixins import ExpressionBoolShapeExactMixin
from .NodeMakingHelpers import (
    makeConstantReplacementNode,
    makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue,
    wrapExpressionWithNodeSideEffects,
)
from .shapes.BuiltinTypeShapes import (
    tshape_bytearray,
    tshape_bytes,
    tshape_str,
    tshape_str_or_unicode,
    tshape_unicode,
    tshape_xrange,
)

# Exact built-in sequences whose iteration and element truth checks cannot
# execute user code or raise exceptions.
_non_raising_truth_iterable_shapes = (
    tshape_str,
    tshape_unicode,
    tshape_str_or_unicode,
    tshape_bytes,
    tshape_bytearray,
    tshape_xrange,
)


class ExpressionBuiltinAny(
    ExpressionBoolShapeExactMixin, ExpressionBuiltinSingleArgBase
):
    kind = "EXPRESSION_BUILTIN_ANY"

    builtin_spec = BuiltinParameterSpecs.builtin_any_spec

    def computeExpression(self, trace_collection):
        value = self.subnode_value
        shape = value.getTypeShape()
        if shape.hasShapeSlotIter() is False:
            trace_collection.onExceptionRaiseExit(BaseException)

            return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                template="'%s' object is not iterable",
                operation="any",
                original_node=value,
                value_node=value,
            )

        iteration_handle = value.getIterationHandle()

        if iteration_handle is not None:
            any_true = iteration_handle.getAnyElementTruthValue()

            if any_true is not None:
                result = wrapExpressionWithNodeSideEffects(
                    new_node=makeConstantReplacementNode(
                        constant=any_true, node=self, user_provided=False
                    ),
                    old_node=value,
                )

                return (
                    result,
                    "new_constant",
                    "Predicted truth value of built-in any argument",
                )

        if shape not in _non_raising_truth_iterable_shapes:
            self.onContentEscapes(trace_collection)
            trace_collection.onControlFlowEscape(self)
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseExceptionOperation(self):
        return (
            self.subnode_value.getTypeShape() not in _non_raising_truth_iterable_shapes
        )

    def mayRaiseException(self, exception_type):
        value = self.subnode_value

        if value.mayRaiseException(exception_type):
            return True

        return self.mayRaiseExceptionOperation()


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
