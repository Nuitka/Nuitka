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
""" Nodes that build and operate on str.

"""

from .ExpressionBases import ExpressionChildrenHavingBase
from .ExpressionShapeMixins import (
    ExpressionStrShapeExactMixin,
    ExpressionTupleShapeExactMixin,
)


class ExpressionStrOperationJoin(
    ExpressionStrShapeExactMixin, ExpressionChildrenHavingBase
):
    """This operation represents s.join(iterable)."""

    kind = "EXPRESSION_STR_OPERATION_JOIN"

    named_children = ("str_arg", "iterable")

    def __init__(self, str_arg, iterable, source_ref):
        assert str_arg is not None
        assert iterable is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values={"str_arg": str_arg, "iterable": iterable},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        str_arg = self.subnode_str_arg
        iterable = self.subnode_iterable

        if str_arg.isCompileTimeConstant() and iterable.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str_arg.getCompileTimeConstant().join(
                    iterable.getCompileTimeConstant()
                ),
                description="Str join with constant values.",
                user_provided=str_arg.user_provided,
            )

        # TODO: Only if the iterables contains a non-string.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrOperationPartition(
    ExpressionTupleShapeExactMixin, ExpressionChildrenHavingBase
):
    """This operation represents s.partition(sep)."""

    kind = "EXPRESSION_STR_OPERATION_PARTITION"

    named_children = ("str_arg", "sep")

    def __init__(self, str_arg, sep, source_ref):
        assert str_arg is not None
        assert sep is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values={"str_arg": str_arg, "sep": sep},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        str_arg = self.subnode_str_arg
        sep = self.subnode_sep

        if str_arg.isCompileTimeConstant() and sep.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: self.getCompileTimeConstant()[
                    str_arg.getCompileTimeConstant().partition(
                        sep.getCompileTimeConstant()
                    )
                ],
                description="Str partition with constant values.",
                user_provided=str_arg.user_provided,
            )

        # TODO: Only if the sep is not a string
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def getIterationLength():
        return 3


class ExpressionStrOperationRpartition(
    ExpressionTupleShapeExactMixin, ExpressionChildrenHavingBase
):
    """This operation represents s.rpartition(sep)."""

    kind = "EXPRESSION_STR_OPERATION_RPARTITION"

    named_children = ("str_arg", "sep")

    def __init__(self, str_arg, sep, source_ref):
        assert str_arg is not None
        assert sep is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values={"str_arg": str_arg, "sep": sep},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        str_arg = self.subnode_str_arg
        sep = self.subnode_sep

        if str_arg.isCompileTimeConstant() and sep.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: self.getCompileTimeConstant()[
                    str_arg.getCompileTimeConstant().rpartition(
                        sep.getCompileTimeConstant()
                    )
                ],
                description="Str rpartition with constant values.",
                user_provided=str_arg.user_provided,
            )

        # TODO: Only if the sep is not a string
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def getIterationLength():
        return 3
