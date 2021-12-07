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

from abc import abstractmethod

from .ExpressionBases import (
    ExpressionChildHavingBase,
    ExpressionChildrenHavingBase,
)
from .ExpressionShapeMixins import (
    ExpressionIntShapeExactMixin,
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
                computation=lambda: str_arg.getCompileTimeConstant().partition(
                    sep.getCompileTimeConstant()
                ),
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
                computation=lambda: str_arg.getCompileTimeConstant().rpartition(
                    sep.getCompileTimeConstant()
                ),
                description="Str rpartition with constant values.",
                user_provided=str_arg.user_provided,
            )

        # TODO: Only if the sep is not a string
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def getIterationLength():
        return 3


class ExpressionStrOperationStrip2Base(
    ExpressionStrShapeExactMixin, ExpressionChildrenHavingBase
):

    named_children = ("str_arg", "chars")

    @abstractmethod
    def simulator(self, str_value, chars_value):
        """Compile time simulation"""

    def __init__(self, str_arg, chars, source_ref):
        assert str_arg is not None
        assert chars is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values={"str_arg": str_arg, "chars": chars},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        str_arg = self.subnode_str_arg
        chars = self.subnode_chars

        if str_arg.isCompileTimeConstant() and chars.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: self.simulator(
                    str_value=str_arg.getCompileTimeConstant(),
                    chars_value=chars.getCompileTimeConstant(),
                ),
                description="Str strip with constant values.",
                user_provided=str_arg.user_provided,
            )

        # TODO: Only if the sep is not a string
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        # TODO: Only if chars is not correct shape
        return True


class ExpressionStrOperationStrip2(ExpressionStrOperationStrip2Base):
    """This operation represents s.strip(chars)."""

    kind = "EXPRESSION_STR_OPERATION_STRIP2"

    @staticmethod
    def simulator(str_value, chars_value):
        return str_value.strip(chars_value)


class ExpressionStrOperationLstrip2(ExpressionStrOperationStrip2Base):
    """This operation represents s.lstrip(chars)."""

    kind = "EXPRESSION_STR_OPERATION_LSTRIP2"

    @staticmethod
    def simulator(str_value, chars_value):
        return str_value.lstrip(chars_value)


class ExpressionStrOperationRstrip2(ExpressionStrOperationStrip2Base):
    """This operation represents s.rstrip(chars)."""

    kind = "EXPRESSION_STR_OPERATION_RSTRIP2"

    @staticmethod
    def simulator(str_value, chars_value):
        return str_value.rstrip(chars_value)


class ExpressionStrOperationStrip1Base(
    ExpressionStrShapeExactMixin, ExpressionChildHavingBase
):
    named_child = "str_arg"

    @abstractmethod
    def simulator(self, str_value):
        """Compile time simulation."""

    def __init__(self, str_arg, source_ref):
        assert str_arg is not None

        ExpressionChildHavingBase.__init__(
            self,
            value=str_arg,
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        str_arg = self.subnode_str_arg

        if str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: self.simulator(
                    str_value=str_arg.getCompileTimeConstant(),
                ),
                description="Str strip with constant value.",
                user_provided=str_arg.user_provided,
            )

        # TODO: Only if the sep is not a string
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        # TODO: Only if chars is not correct shape
        return True


class ExpressionStrOperationStrip1(ExpressionStrOperationStrip1Base):
    """This operation represents s.strip()."""

    kind = "EXPRESSION_STR_OPERATION_STRIP1"

    @staticmethod
    def simulator(str_value):
        return str_value.strip()


class ExpressionStrOperationLstrip1(ExpressionStrOperationStrip1Base):
    """This operation represents s.lstrip(chars)."""

    kind = "EXPRESSION_STR_OPERATION_LSTRIP1"

    @staticmethod
    def simulator(str_value):
        return str_value.lstrip()


class ExpressionStrOperationRstrip1(ExpressionStrOperationStrip1Base):
    """This operation represents s.rstrip()."""

    kind = "EXPRESSION_STR_OPERATION_RSTRIP1"

    @staticmethod
    def simulator(str_value):
        return str_value.rstrip()


class ExpressionStrOperationFind2Base(
    ExpressionIntShapeExactMixin, ExpressionChildrenHavingBase
):
    named_children = ("str_arg", "sub")

    def __init__(self, str_arg, sub, source_ref):
        assert str_arg is not None
        assert sub is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values={"str_arg": str_arg, "sub": sub},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        str_arg = self.subnode_str_arg
        sub = self.subnode_sub

        if str_arg.isCompileTimeConstant() and sub.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: self.simulator(
                    str_arg.getCompileTimeConstant(), sub.getCompileTimeConstant()
                ),
                description="Str find with constant values.",
                user_provided=str_arg.user_provided,
            )

        # TODO: Only if the sub is not a string
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrFindMixin(object):
    __slots__ = ()

    @staticmethod
    def simulator(*args):
        return str.find(*args)


class ExpressionStrRfindMixin(object):
    __slots__ = ()

    @staticmethod
    def simulator(*args):
        return str.rfind(*args)


class ExpressionStrOperationFind2(
    ExpressionStrFindMixin, ExpressionStrOperationFind2Base
):
    """This operation represents s.find(sub)."""

    kind = "EXPRESSION_STR_OPERATION_FIND2"


class ExpressionStrOperationRfind2(
    ExpressionStrRfindMixin, ExpressionStrOperationFind2Base
):
    """This operation represents s.rfind(sub)."""

    kind = "EXPRESSION_STR_OPERATION_RFIND2"


class ExpressionStrOperationFind3Base(
    ExpressionIntShapeExactMixin, ExpressionChildrenHavingBase
):
    """This operation represents s.find(sub)."""

    kind = "EXPRESSION_STR_OPERATION_FIND3"

    named_children = ("str_arg", "sub", "start")

    def __init__(self, str_arg, sub, start, source_ref):
        assert str_arg is not None
        assert sub is not None
        assert start is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values={"str_arg": str_arg, "sub": sub, "start": start},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        str_arg = self.subnode_str_arg
        sub = self.subnode_sub
        start = self.subnode_start

        if (
            str_arg.isCompileTimeConstant()
            and sub.isCompileTimeConstant()
            and start.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: self.simulator(
                    str_arg.getCompileTimeConstant(),
                    sub.getCompileTimeConstant(),
                    start.getCompileTimeConstant(),
                ),
                description="Str find with constant values.",
                user_provided=str_arg.user_provided,
            )

        # TODO: Only if the sub is not a string or start is not an int
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrOperationFind3(
    ExpressionStrFindMixin, ExpressionStrOperationFind3Base
):
    """This operation represents s.find(sub, start)."""

    kind = "EXPRESSION_STR_OPERATION_FIND3"


class ExpressionStrOperationRfind3(
    ExpressionStrRfindMixin, ExpressionStrOperationFind3Base
):
    """This operation represents s.rfind(sub, start)."""

    kind = "EXPRESSION_STR_OPERATION_RFIND3"


class ExpressionStrOperationFind4Base(
    ExpressionIntShapeExactMixin, ExpressionChildrenHavingBase
):
    """This operation represents s.find(sub)."""

    kind = "EXPRESSION_STR_OPERATION_FIND4"

    named_children = ("str_arg", "sub", "start", "end")

    def __init__(self, str_arg, sub, start, end, source_ref):
        assert str_arg is not None
        assert sub is not None
        assert start is not None
        assert end is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values={"str_arg": str_arg, "sub": sub, "start": start, "end": end},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        str_arg = self.subnode_str_arg
        sub = self.subnode_sub
        start = self.subnode_start
        end = self.subnode_end

        if (
            str_arg.isCompileTimeConstant()
            and sub.isCompileTimeConstant()
            and start.isCompileTimeConstant()
            and end.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: self.simulator(
                    str_arg.getCompileTimeConstant(),
                    sub.getCompileTimeConstant(),
                    start.getCompileTimeConstant(),
                    end.getCompileTimeConstant(),
                ),
                description="Str find with constant values.",
                user_provided=str_arg.user_provided,
            )

        # TODO: Only if the sub is not a string or start and end are not int
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrOperationFind4(
    ExpressionStrFindMixin, ExpressionStrOperationFind4Base
):
    """This operation represents s.find(sub, start, end)."""

    kind = "EXPRESSION_STR_OPERATION_FIND4"


class ExpressionStrOperationRfind4(
    ExpressionStrRfindMixin, ExpressionStrOperationFind4Base
):
    """This operation represents s.rfind(sub, start, end)."""

    kind = "EXPRESSION_STR_OPERATION_RFIND4"
