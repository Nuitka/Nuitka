#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Nodes for match statement for Python3.10+ """

from .ExpressionBases import ExpressionChildHavingBase
from .ExpressionShapeMixins import ExpressionTupleShapeExactMixin


class ExpressionMatchArgs(ExpressionTupleShapeExactMixin, ExpressionChildHavingBase):
    kind = "EXPRESSION_MATCH_ARGS"

    named_child = "expression"

    __slots__ = ("max_allowed",)

    def __init__(self, expression, max_allowed, source_ref):

        ExpressionChildHavingBase.__init__(
            self, value=expression, source_ref=source_ref
        )

        self.max_allowed = max_allowed

    def computeExpression(self, trace_collection):
        # TODO: May know that match args doesn't raise from the shape of
        # the matches expression, most don't.

        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None
