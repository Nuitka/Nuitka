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


class ExpressionBuiltinAny(ExpressionBuiltinSingleArgBase):
    """ Builtin Any Node class.

    Args:
        ExpressionBase: 'any - expression'

    Returns:
        Node that represents built-in 'any' call.

    """

    kind = "EXPRESSION_BUILTIN_ANY"

    builtin_spec = BuiltinParameterSpecs.builtin_any_spec

    def computeExpression(self, trace_collection):
        return self.getValue().computeExpressionAny(
            any_node=self, trace_collection=trace_collection
        )

    def getTypeShape(self):
        """ returns type shape of the 'any' node

        """
        return ShapeTypeBool

    def mayRaiseException(self, exception_type):
        """ returns boolean True if try/except/finally is needed else False

        """
        value = self.getValue()

        if value.mayRaiseException(exception_type):
            return True

        return not value.getTypeShape().hasShapeSlotIter()
