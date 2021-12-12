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
    ExpressionBoolShapeExactMixin,
    ExpressionBytesShapeExactMixin,
    ExpressionIntShapeExactMixin,
    ExpressionListShapeExactMixin,
    ExpressionStrOrUnicodeExactMixin,
    ExpressionStrShapeExactMixin,
    ExpressionTupleShapeExactMixin,
)
from .NodeBases import SideEffectsFromChildrenMixin
from .NodeMetaClasses import NodeCheckMetaClass


def getStrOperationClasses():
    """Return all str operation nodes, for use by code generation."""
    return (
        cls
        for kind, cls in NodeCheckMetaClass.kinds.items()
        if kind.startswith("EXPRESSION_STR_OPERATION")
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
                description="Built-in 'str.join' with constant values.",
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
                description="Built-in 'str.partition' with constant values.",
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
                description="Built-in 'str.rpartition' with constant values.",
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
    def getSimulator(self):
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
            simulator = self.getSimulator()

            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: simulator(
                    str_arg.getCompileTimeConstant(),
                    chars.getCompileTimeConstant(),
                ),
                description="Built-in 'str.strip' with constant values.",
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
    def getSimulator():
        """Compile time simulation"""

        return str.strip


class ExpressionStrOperationLstrip2(ExpressionStrOperationStrip2Base):
    """This operation represents s.lstrip(chars)."""

    kind = "EXPRESSION_STR_OPERATION_LSTRIP2"

    @staticmethod
    def getSimulator():
        """Compile time simulation"""

        return str.lstrip


class ExpressionStrOperationRstrip2(ExpressionStrOperationStrip2Base):
    """This operation represents s.rstrip(chars)."""

    kind = "EXPRESSION_STR_OPERATION_RSTRIP2"

    @staticmethod
    def getSimulator():
        """Compile time simulation"""

        return str.rstrip


class ExpressionStrOperationSingleArgBase(
    SideEffectsFromChildrenMixin, ExpressionChildHavingBase
):
    named_child = "str_arg"

    @abstractmethod
    def getSimulator(self):
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
            simulator = self.getSimulator()

            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: simulator(
                    str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.%s' on constant value." % simulator.__name__,
                user_provided=str_arg.user_provided,
            )

        return self, None, None

    def mayRaiseException(self, exception_type):
        return self.subnode_str_arg.mayRaiseException(exception_type)


class ExpressionStrOperationStrip1Base(  # Base classes can be abstract, pylint: disable=abstract-method
    ExpressionStrShapeExactMixin,
    ExpressionStrOperationSingleArgBase,
):
    """Base class for use by str.strip(), str.lstrip() and str.rstrip()"""


class ExpressionStrOperationStrip1(ExpressionStrOperationStrip1Base):
    """This operation represents s.strip()."""

    kind = "EXPRESSION_STR_OPERATION_STRIP1"

    @staticmethod
    def getSimulator():
        """Compile time simulation."""

        return str.strip


class ExpressionStrOperationLstrip1(ExpressionStrOperationStrip1Base):
    """This operation represents s.lstrip(chars)."""

    kind = "EXPRESSION_STR_OPERATION_LSTRIP1"

    @staticmethod
    def getSimulator():
        """Compile time simulation."""

        return str.lstrip


class ExpressionStrOperationRstrip1(ExpressionStrOperationStrip1Base):
    """This operation represents s.rstrip()."""

    kind = "EXPRESSION_STR_OPERATION_RSTRIP1"

    @staticmethod
    def getSimulator():
        """Compile time simulation."""

        return str.rstrip


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
            simulator = self.getSimulator()

            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: simulator(
                    str_arg.getCompileTimeConstant(), sub.getCompileTimeConstant()
                ),
                description="Built-in 'str.find' with constant values.",
                user_provided=str_arg.user_provided,
            )

        # TODO: Only if the sub is not a string
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrFindMixin(object):
    __slots__ = ()

    @staticmethod
    def getSimulator():
        """Compile time simulation"""

        return str.find


class ExpressionStrRfindMixin(object):
    __slots__ = ()

    @staticmethod
    def getSimulator():
        """Compile time simulation"""

        return str.rfind


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
            simulator = self.getSimulator()

            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: simulator(
                    str_arg.getCompileTimeConstant(),
                    sub.getCompileTimeConstant(),
                    start.getCompileTimeConstant(),
                ),
                description="Built-in 'str.find' with constant values.",
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
            simulator = self.getSimulator()

            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: simulator(
                    str_arg.getCompileTimeConstant(),
                    sub.getCompileTimeConstant(),
                    start.getCompileTimeConstant(),
                    end.getCompileTimeConstant(),
                ),
                description="Built-in 'str.find' with constant values.",
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


class ExpressionStrOperationIndexMixin(object):
    __slots__ = ()

    @staticmethod
    def mayRaiseException(exception_type):
        # It will return ValueError if not finding it, pylint: disable=unused-argument
        return True

    @staticmethod
    def getSimulator():
        """Compile time simulation"""

        return str.index


class ExpressionStrOperationRindexMixin(ExpressionStrOperationIndexMixin):
    __slots__ = ()

    @staticmethod
    def getSimulator():
        """Compile time simulation"""

        return str.rindex


class ExpressionStrOperationIndex2(
    ExpressionStrOperationIndexMixin, ExpressionStrOperationFind2Base
):
    """This operation represents s.index(sub)."""

    kind = "EXPRESSION_STR_OPERATION_INDEX2"


class ExpressionStrOperationIndex3(
    ExpressionStrOperationIndexMixin, ExpressionStrOperationFind3Base
):
    """This operation represents s.index(sub, start)."""

    kind = "EXPRESSION_STR_OPERATION_INDEX3"


class ExpressionStrOperationIndex4(
    ExpressionStrOperationIndexMixin, ExpressionStrOperationFind4Base
):
    """This operation represents s.index(sub, start, end)."""

    kind = "EXPRESSION_STR_OPERATION_INDEX4"


class ExpressionStrOperationRindex2(
    ExpressionStrOperationRindexMixin, ExpressionStrOperationFind2Base
):
    """This operation represents s.rindex(sub)."""

    kind = "EXPRESSION_STR_OPERATION_RINDEX2"


class ExpressionStrOperationRindex3(
    ExpressionStrOperationRindexMixin, ExpressionStrOperationFind3Base
):
    """This operation represents s.rindex(sub, start)."""

    kind = "EXPRESSION_STR_OPERATION_RINDEX3"


class ExpressionStrOperationRindex4(
    ExpressionStrOperationRindexMixin, ExpressionStrOperationFind4Base
):
    """This operation represents s.rindex(sub, start, end)."""

    kind = "EXPRESSION_STR_OPERATION_RINDEX4"


class ExpressionStrOperationCapitalize(
    ExpressionStrShapeExactMixin, ExpressionStrOperationSingleArgBase
):
    """This operation represents s.capitalize()."""

    kind = "EXPRESSION_STR_OPERATION_CAPITALIZE"

    @staticmethod
    def getSimulator():
        """Compile time simulation."""

        return str.capitalize


class ExpressionStrOperationUpper(
    ExpressionStrShapeExactMixin, ExpressionStrOperationSingleArgBase
):
    """This operation represents s.upper()."""

    kind = "EXPRESSION_STR_OPERATION_UPPER"

    @staticmethod
    def getSimulator():
        """Compile time simulation."""

        return str.upper


class ExpressionStrOperationLower(
    ExpressionStrShapeExactMixin, ExpressionStrOperationSingleArgBase
):
    """This operation represents s.lower()."""

    kind = "EXPRESSION_STR_OPERATION_LOWER"

    @staticmethod
    def getSimulator():
        """Compile time simulation."""

        return str.lower


class ExpressionStrOperationSwapcase(
    ExpressionStrShapeExactMixin, ExpressionStrOperationSingleArgBase
):
    """This operation represents s.swapcase()."""

    kind = "EXPRESSION_STR_OPERATION_SWAPCASE"

    @staticmethod
    def getSimulator():
        """Compile time simulation."""

        return str.swapcase


class ExpressionStrOperationTitle(
    ExpressionStrShapeExactMixin, ExpressionStrOperationSingleArgBase
):
    """This operation represents s.title()."""

    kind = "EXPRESSION_STR_OPERATION_TITLE"

    @staticmethod
    def getSimulator():
        """Compile time simulation."""

        return str.title


class ExpressionStrOperationIsalnum(
    ExpressionBoolShapeExactMixin, ExpressionStrOperationSingleArgBase
):
    """This operation represents s.isalnum()."""

    kind = "EXPRESSION_STR_OPERATION_ISALNUM"

    @staticmethod
    def getSimulator():
        """Compile time simulation."""

        return str.isalnum


class ExpressionStrOperationIsalpha(
    ExpressionBoolShapeExactMixin, ExpressionStrOperationSingleArgBase
):
    """This operation represents s.isalpha()."""

    kind = "EXPRESSION_STR_OPERATION_ISALPHA"

    @staticmethod
    def getSimulator():
        """Compile time simulation."""

        return str.isalpha


class ExpressionStrOperationIsdigit(
    ExpressionBoolShapeExactMixin, ExpressionStrOperationSingleArgBase
):
    """This operation represents s.isdigit()."""

    kind = "EXPRESSION_STR_OPERATION_ISDIGIT"

    @staticmethod
    def getSimulator():
        """Compile time simulation."""

        return str.isdigit


class ExpressionStrOperationIslower(
    ExpressionBoolShapeExactMixin, ExpressionStrOperationSingleArgBase
):
    """This operation represents s.islower()."""

    kind = "EXPRESSION_STR_OPERATION_ISLOWER"

    @staticmethod
    def getSimulator():
        """Compile time simulation."""

        return str.islower


class ExpressionStrOperationIsupper(
    ExpressionBoolShapeExactMixin, ExpressionStrOperationSingleArgBase
):
    """This operation represents s.isupper()."""

    kind = "EXPRESSION_STR_OPERATION_ISUPPER"

    @staticmethod
    def getSimulator():
        """Compile time simulation."""

        return str.isupper


class ExpressionStrOperationIsspace(
    ExpressionBoolShapeExactMixin, ExpressionStrOperationSingleArgBase
):
    """This operation represents s.isspace()."""

    kind = "EXPRESSION_STR_OPERATION_ISSPACE"

    @staticmethod
    def getSimulator():
        """Compile time simulation."""

        return str.isspace


class ExpressionStrOperationIstitle(
    ExpressionBoolShapeExactMixin, ExpressionStrOperationSingleArgBase
):
    """This operation represents s.istitle()."""

    kind = "EXPRESSION_STR_OPERATION_ISTITLE"

    @staticmethod
    def getSimulator():
        """Compile time simulation."""

        return str.istitle


class ExpressionStrSplitMixin(object):
    __slots__ = ()

    @staticmethod
    def getSimulator():
        """Compile time simulation."""

        return str.split


class ExpressionStrRsplitMixin(object):
    __slots__ = ()

    @staticmethod
    def getSimulator():
        """Compile time simulation."""

        return str.rsplit


class ExpressionStrOperationSplit1Base(  # Base classes can be abstract, pylint: disable=abstract-method
    ExpressionListShapeExactMixin,
    ExpressionStrOperationSingleArgBase,
):
    """Base class for use by str.split(), str.lsplit() and str.rsplit()"""


class ExpressionStrOperationSplit1(
    ExpressionStrSplitMixin, ExpressionStrOperationSplit1Base
):
    """This operation represents s.split()."""

    kind = "EXPRESSION_STR_OPERATION_SPLIT1"


# TODO: This one could be eliminated in factor of simpleExpressionStrOperationSplit1
# since without an argument, there is no difference.
class ExpressionStrOperationRsplit1(
    ExpressionStrRsplitMixin, ExpressionStrOperationSplit1Base
):
    """This operation represents s.rsplit()."""

    kind = "EXPRESSION_STR_OPERATION_RSPLIT1"


class ExpressionStrOperationSplit2Base(
    ExpressionListShapeExactMixin, ExpressionChildrenHavingBase
):
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
            simulator = self.getSimulator()

            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: simulator(
                    str_arg.getCompileTimeConstant(), sep.getCompileTimeConstant()
                ),
                description="Built-in 'str.split' with constant values.",
                user_provided=str_arg.user_provided,
            )

        # TODO: Only if the sep is not a string
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrOperationSplit2(
    ExpressionStrSplitMixin, ExpressionStrOperationSplit2Base
):
    """This operation represents s.split(sep)."""

    kind = "EXPRESSION_STR_OPERATION_SPLIT2"


class ExpressionStrOperationRsplit2(
    ExpressionStrRsplitMixin, ExpressionStrOperationSplit2Base
):
    """This operation represents s.rsplit(sep)."""

    kind = "EXPRESSION_STR_OPERATION_RSPLIT2"


class ExpressionStrOperationSplit3Base(
    ExpressionListShapeExactMixin, ExpressionChildrenHavingBase
):
    named_children = ("str_arg", "sep", "maxsplit")

    def __init__(self, str_arg, sep, maxsplit, source_ref):
        assert str_arg is not None
        assert sep is not None
        assert maxsplit is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values={"str_arg": str_arg, "sep": sep, "maxsplit": maxsplit},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        str_arg = self.subnode_str_arg
        sep = self.subnode_sep
        maxsplit = self.subnode_maxsplit

        if (
            str_arg.isCompileTimeConstant()
            and sep.isCompileTimeConstant()
            and maxsplit.isCompileTimeConstant()
        ):
            simulator = self.getSimulator()

            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: simulator(
                    str_arg.getCompileTimeConstant(),
                    sep.getCompileTimeConstant(),
                    maxsplit.getCompileTimeConstant(),
                ),
                description="Built-in 'str.split' with constant values.",
                user_provided=str_arg.user_provided,
            )

        # TODO: Only if the seo is not a string or maxsplit not a number
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrOperationSplit3(
    ExpressionStrSplitMixin, ExpressionStrOperationSplit3Base
):
    """This operation represents s.split(sep, maxsplit)."""

    kind = "EXPRESSION_STR_OPERATION_SPLIT3"


class ExpressionStrOperationRsplit3(
    ExpressionStrRsplitMixin, ExpressionStrOperationSplit3Base
):
    """This operation represents s.rsplit(sep, maxsplit)."""

    kind = "EXPRESSION_STR_OPERATION_RSPLIT3"


class ExpressionStrOperationEndswithBase(
    ExpressionBoolShapeExactMixin, ExpressionChildrenHavingBase
):
    @staticmethod
    def getSimulator():
        """Compile time simulation"""

        return str.endswith


class ExpressionStrOperationEndswith2(ExpressionStrOperationEndswithBase):
    kind = "EXPRESSION_STR_OPERATION_ENDSWITH2"

    named_children = ("str_arg", "suffix")

    def __init__(self, str_arg, suffix, source_ref):
        assert str_arg is not None
        assert suffix is not None

        ExpressionStrOperationEndswithBase.__init__(
            self,
            values={"str_arg": str_arg, "suffix": suffix},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        str_arg = self.subnode_str_arg
        suffix = self.subnode_suffix

        if str_arg.isCompileTimeConstant() and suffix.isCompileTimeConstant():
            simulator = self.getSimulator()

            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: simulator(
                    str_arg.getCompileTimeConstant(), suffix.getCompileTimeConstant()
                ),
                description="Built-in 'str.endswith' with constant values.",
                user_provided=str_arg.user_provided,
            )

        # TODO: Only if the suffix is not a string
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrOperationEndswith3(ExpressionStrOperationEndswithBase):
    kind = "EXPRESSION_STR_OPERATION_ENDSWITH3"

    named_children = ("str_arg", "suffix", "start")

    def __init__(self, str_arg, suffix, start, source_ref):
        assert str_arg is not None
        assert suffix is not None
        assert start is not None

        ExpressionStrOperationEndswithBase.__init__(
            self,
            values={"str_arg": str_arg, "suffix": suffix, "start": start},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        str_arg = self.subnode_str_arg
        suffix = self.subnode_suffix
        start = self.subnode_start

        if (
            str_arg.isCompileTimeConstant()
            and suffix.isCompileTimeConstant()
            and start.isCompileTimeConstant()
        ):
            simulator = self.getSimulator()

            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: simulator(
                    str_arg.getCompileTimeConstant(),
                    suffix.getCompileTimeConstant(),
                    start.getCompileTimeConstant(),
                ),
                description="Built-in 'str.endswith' with constant values.",
                user_provided=str_arg.user_provided,
            )

        # TODO: Only if the suffix is not a string
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrOperationEndswith4(ExpressionStrOperationEndswithBase):
    kind = "EXPRESSION_STR_OPERATION_ENDSWITH4"

    named_children = ("str_arg", "suffix", "start", "end")

    def __init__(self, str_arg, suffix, start, end, source_ref):
        assert str_arg is not None
        assert suffix is not None
        assert start is not None
        assert end is not None

        ExpressionStrOperationEndswithBase.__init__(
            self,
            values={"str_arg": str_arg, "suffix": suffix, "start": start, "end": end},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        str_arg = self.subnode_str_arg
        suffix = self.subnode_suffix
        start = self.subnode_start
        end = self.subnode_end

        if (
            str_arg.isCompileTimeConstant()
            and suffix.isCompileTimeConstant()
            and start.isCompileTimeConstant()
            and end.isCompileTimeConstant()
        ):
            simulator = self.getSimulator()

            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: simulator(
                    str_arg.getCompileTimeConstant(),
                    suffix.getCompileTimeConstant(),
                    start.getCompileTimeConstant(),
                    end.getCompileTimeConstant(),
                ),
                description="Built-in 'str.endswith' with constant values.",
                user_provided=str_arg.user_provided,
            )

        # TODO: Only if the suffix is not a string
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrOperationStartswithBase(
    ExpressionBoolShapeExactMixin, ExpressionChildrenHavingBase
):
    @staticmethod
    def getSimulator():
        """Compile time simulation"""

        return str.startswith


class ExpressionStrOperationStartswith2(ExpressionStrOperationStartswithBase):
    kind = "EXPRESSION_STR_OPERATION_STARTSWITH2"

    named_children = ("str_arg", "prefix")

    def __init__(self, str_arg, prefix, source_ref):
        assert str_arg is not None
        assert prefix is not None

        ExpressionStrOperationStartswithBase.__init__(
            self,
            values={"str_arg": str_arg, "prefix": prefix},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        str_arg = self.subnode_str_arg
        prefix = self.subnode_prefix

        if str_arg.isCompileTimeConstant() and prefix.isCompileTimeConstant():
            simulator = self.getSimulator()

            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: simulator(
                    str_arg.getCompileTimeConstant(), prefix.getCompileTimeConstant()
                ),
                description="Built-in 'str.startswith' with constant values.",
                user_provided=str_arg.user_provided,
            )

        # TODO: Only if the prefix is not a string
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrOperationStartswith3(ExpressionStrOperationStartswithBase):
    kind = "EXPRESSION_STR_OPERATION_STARTSWITH3"

    named_children = ("str_arg", "prefix", "start")

    def __init__(self, str_arg, prefix, start, source_ref):
        assert str_arg is not None
        assert prefix is not None
        assert start is not None

        ExpressionStrOperationStartswithBase.__init__(
            self,
            values={"str_arg": str_arg, "prefix": prefix, "start": start},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        str_arg = self.subnode_str_arg
        prefix = self.subnode_prefix
        start = self.subnode_start

        if (
            str_arg.isCompileTimeConstant()
            and prefix.isCompileTimeConstant()
            and start.isCompileTimeConstant()
        ):
            simulator = self.getSimulator()

            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: simulator(
                    str_arg.getCompileTimeConstant(),
                    prefix.getCompileTimeConstant(),
                    start.getCompileTimeConstant(),
                ),
                description="Built-in 'str.startswith' with constant values.",
                user_provided=str_arg.user_provided,
            )

        # TODO: Only if the prefix is not a string
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrOperationStartswith4(ExpressionStrOperationStartswithBase):
    kind = "EXPRESSION_STR_OPERATION_STARTSWITH4"

    named_children = ("str_arg", "prefix", "start", "end")

    def __init__(self, str_arg, prefix, start, end, source_ref):
        assert str_arg is not None
        assert prefix is not None
        assert start is not None
        assert end is not None

        ExpressionStrOperationStartswithBase.__init__(
            self,
            values={"str_arg": str_arg, "prefix": prefix, "start": start, "end": end},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        str_arg = self.subnode_str_arg
        prefix = self.subnode_prefix
        start = self.subnode_start
        end = self.subnode_end

        if (
            str_arg.isCompileTimeConstant()
            and prefix.isCompileTimeConstant()
            and start.isCompileTimeConstant()
            and end.isCompileTimeConstant()
        ):
            simulator = self.getSimulator()

            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: simulator(
                    str_arg.getCompileTimeConstant(),
                    prefix.getCompileTimeConstant(),
                    start.getCompileTimeConstant(),
                    end.getCompileTimeConstant(),
                ),
                description="Built-in 'str.startswith' with constant values.",
                user_provided=str_arg.user_provided,
            )

        # TODO: Only if the prefix is not a string
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrOperationReplaceBase(
    ExpressionStrOrUnicodeExactMixin, ExpressionChildrenHavingBase
):
    @staticmethod
    def getSimulator():
        """Compile time simulation"""

        return str.replace


class ExpressionStrOperationReplace3(ExpressionStrOperationReplaceBase):
    kind = "EXPRESSION_STR_OPERATION_REPLACE3"

    named_children = ("str_arg", "old", "new")

    def __init__(self, str_arg, old, new, source_ref):
        assert str_arg is not None
        assert old is not None
        assert new is not None

        ExpressionStrOperationReplaceBase.__init__(
            self,
            values={"str_arg": str_arg, "old": old, "new": new},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        str_arg = self.subnode_str_arg
        old = self.subnode_old
        new = self.subnode_new

        if (
            str_arg.isCompileTimeConstant()
            and old.isCompileTimeConstant()
            and new.isCompileTimeConstant()
        ):
            simulator = self.getSimulator()

            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: simulator(
                    str_arg.getCompileTimeConstant(),
                    old.getCompileTimeConstant(),
                    new.getCompileTimeConstant(),
                ),
                description="Built-in 'str.replace' with constant values.",
                user_provided=str_arg.user_provided,
            )

        # TODO: Only if the old/new are not strings
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrOperationReplace4(ExpressionStrOperationReplaceBase):
    kind = "EXPRESSION_STR_OPERATION_REPLACE4"

    named_children = ("str_arg", "old", "new", "count")

    def __init__(self, str_arg, old, new, count, source_ref):
        assert str_arg is not None
        assert old is not None
        assert new is not None
        assert count is not None

        ExpressionStrOperationReplaceBase.__init__(
            self,
            values={"str_arg": str_arg, "old": old, "new": new, "count": count},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        str_arg = self.subnode_str_arg
        old = self.subnode_old
        new = self.subnode_new
        count = self.subnode_count

        if (
            str_arg.isCompileTimeConstant()
            and old.isCompileTimeConstant()
            and new.isCompileTimeConstant()
            and count.isCompileTimeConstant()
        ):
            simulator = self.getSimulator()

            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: simulator(
                    str_arg.getCompileTimeConstant(),
                    old.getCompileTimeConstant(),
                    new.getCompileTimeConstant(),
                    count.getCompileTimeConstant(),
                ),
                description="Built-in 'str.replace' with constant values.",
                user_provided=str_arg.user_provided,
            )

        # TODO: Only if the old/new are not strings
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrOperationEncodeMixin(
    ExpressionBytesShapeExactMixin if str is not bytes else ExpressionStrShapeExactMixin
):
    __slots__ = ()

    # TODO: Encodings might be registered and influence things at runtime, disabled
    # until we researched that.
    @staticmethod
    def getSimulator():
        """Compile time simulation"""

        return str.encode


class ExpressionStrOperationEncode1(
    ExpressionStrOperationEncodeMixin, ExpressionChildHavingBase
):
    kind = "EXPRESSION_STR_OPERATION_ENCODE1"

    named_child = "str_arg"

    def __init__(self, str_arg, source_ref):
        assert str_arg is not None

        ExpressionChildHavingBase.__init__(
            self,
            value=str_arg,
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):

        # TODO: Only if the string cannot be encoded.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrOperationEncode2(
    ExpressionStrOperationEncodeMixin, ExpressionChildrenHavingBase
):
    kind = "EXPRESSION_STR_OPERATION_ENCODE2"

    named_children = "str_arg", "encoding"

    def __init__(self, str_arg, encoding, source_ref):
        assert str_arg is not None
        assert encoding is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values={"str_arg": str_arg, "encoding": encoding},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        # TODO: Only if the string cannot be encoded to the given encoding
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrOperationEncode3(
    ExpressionStrOperationEncodeMixin, ExpressionChildrenHavingBase
):
    kind = "EXPRESSION_STR_OPERATION_ENCODE3"

    named_children = "str_arg", "encoding", "errors"

    def __init__(self, str_arg, encoding, errors, source_ref):
        assert str_arg is not None
        assert encoding is not None
        assert errors is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values={"str_arg": str_arg, "encoding": encoding, "errors": errors},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        # TODO: Only if the string cannot be encoded to the given encoding, and errors
        # is not ignore.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrOperationDecodeMixin(ExpressionStrOrUnicodeExactMixin):
    __slots__ = ()

    # TODO: Encodings might be registered and influence things at runtime, disabled
    # until we researched that.
    @staticmethod
    def getSimulator():
        """Compile time simulation"""

        return str.decode


class ExpressionStrOperationDecode1(
    ExpressionStrOperationDecodeMixin, ExpressionChildHavingBase
):
    kind = "EXPRESSION_STR_OPERATION_DECODE1"

    named_child = "str_arg"

    def __init__(self, str_arg, source_ref):
        assert str_arg is not None

        ExpressionChildHavingBase.__init__(
            self,
            value=str_arg,
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        # TODO: Only if the string cannot be decoded.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrOperationDecode2(
    ExpressionStrOperationDecodeMixin, ExpressionChildrenHavingBase
):
    kind = "EXPRESSION_STR_OPERATION_DECODE2"

    named_children = "str_arg", "encoding"

    def __init__(self, str_arg, encoding, source_ref):
        assert str_arg is not None
        assert encoding is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values={"str_arg": str_arg, "encoding": encoding},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        # TODO: Only if the string cannot be decoded to the given encoding
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrOperationDecode3(
    ExpressionStrOperationDecodeMixin, ExpressionChildrenHavingBase
):
    kind = "EXPRESSION_STR_OPERATION_DECODE3"

    named_children = "str_arg", "encoding", "errors"

    def __init__(self, str_arg, encoding, errors, source_ref):
        assert str_arg is not None
        assert encoding is not None
        assert errors is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values={"str_arg": str_arg, "encoding": encoding, "errors": errors},
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        # TODO: Only if the string cannot be decoded to the given encoding, and errors
        # is not ignore.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None
