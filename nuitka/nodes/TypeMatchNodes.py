#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
"""Dedicated nodes used for the 3.10 matching

Not usable with older Python as it depends on type flags not present.
"""

from .ExpressionBases import ExpressionChildHavingBase
from .ExpressionShapeMixins import ExpressionBoolShapeExactMixin
from .NodeBases import SideEffectsFromChildrenMixin


class ExpressionMatchTypeCheckBase(
    ExpressionBoolShapeExactMixin,
    SideEffectsFromChildrenMixin,
    ExpressionChildHavingBase,
):
    named_child = "value"

    def __init__(self, value, source_ref):
        ExpressionChildHavingBase.__init__(
            self,
            value=value,
            source_ref=source_ref,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_value.mayRaiseException(exception_type)


class ExpressionMatchTypeCheckSequence(ExpressionMatchTypeCheckBase):
    kind = "EXPRESSION_MATCH_TYPE_CHECK_SEQUENCE"

    def computeExpression(self, trace_collection):
        # TODO: Quite some cases should be possible to predict, based on argument
        # shape, this could evaluate to statically True/False and then will allow
        # optimization into match branches.
        return self, None, None


class ExpressionMatchTypeCheckMapping(ExpressionMatchTypeCheckBase):
    kind = "EXPRESSION_MATCH_TYPE_CHECK_MAPPING"

    def computeExpression(self, trace_collection):
        # TODO: Quite some cases should be possible to predict, based on argument
        # shape, this could evaluate to statically True/False and then will allow
        # optimization into match branches.
        return self, None, None
