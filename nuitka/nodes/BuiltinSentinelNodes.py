#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Node for calls to the 'sentinel' built-in."""

from .ExpressionBases import ExpressionBase
from .ExpressionBasesGenerated import (
    ChildrenHavingNameReprValueAutoNoneOperationMixin,
)
from .ExpressionShapeMixins import ExpressionSentinelShapeExactMixin


class ExpressionBuiltinSentinelCall(
    ExpressionSentinelShapeExactMixin,
    ChildrenHavingNameReprValueAutoNoneOperationMixin,
    ExpressionBase,
):
    kind = "EXPRESSION_BUILTIN_SENTINEL_CALL"

    named_children = ("name", "repr_value|auto_none")
    auto_compute_handling = "operation"

    @staticmethod
    def isExpressionBuiltinCall():
        return True

    def __init__(self, name, repr_value, source_ref):
        ChildrenHavingNameReprValueAutoNoneOperationMixin.__init__(
            self, name=name, repr_value=repr_value
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseExceptionOperation(self):
        # The sentinel constructor only rejects a non-string name or a repr
        # that is neither str nor None. Allocation failures are not tracked
        # here, matching the other built-in constructor nodes.
        if not self.subnode_name.hasShapeStrExact():
            return True

        repr_node = self.subnode_repr_value

        if repr_node is None:
            return False

        return not repr_node.hasShapeStrExact()

    def getKnownAttributeValue(self, attribute_name):
        if attribute_name == "__name__" and self.subnode_name.isCompileTimeConstant():
            return self.subnode_name.getCompileTimeConstant()

        return ExpressionSentinelShapeExactMixin.getKnownAttributeValue(attribute_name)


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
