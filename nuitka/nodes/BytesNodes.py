#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Nodes that build and operate on bytes (Python3).

"""

from .BuiltinOperationNodeBasesGenerated import (
    ExpressionBytesOperationCapitalizeBase,
    ExpressionBytesOperationCenter2Base,
    ExpressionBytesOperationCenter3Base,
    ExpressionBytesOperationCount2Base,
    ExpressionBytesOperationCount3Base,
    ExpressionBytesOperationCount4Base,
    ExpressionBytesOperationDecode1Base,
    ExpressionBytesOperationDecode2Base,
    ExpressionBytesOperationDecode3Base,
    ExpressionBytesOperationEndswith2Base,
    ExpressionBytesOperationEndswith3Base,
    ExpressionBytesOperationEndswith4Base,
    ExpressionBytesOperationExpandtabs1Base,
    ExpressionBytesOperationExpandtabs2Base,
    ExpressionBytesOperationFind2Base,
    ExpressionBytesOperationFind3Base,
    ExpressionBytesOperationFind4Base,
    ExpressionBytesOperationIndex2Base,
    ExpressionBytesOperationIndex3Base,
    ExpressionBytesOperationIndex4Base,
    ExpressionBytesOperationIsalnumBase,
    ExpressionBytesOperationIsalphaBase,
    ExpressionBytesOperationIsdigitBase,
    ExpressionBytesOperationIslowerBase,
    ExpressionBytesOperationIsspaceBase,
    ExpressionBytesOperationIstitleBase,
    ExpressionBytesOperationIsupperBase,
    ExpressionBytesOperationJoinBase,
    ExpressionBytesOperationLjust2Base,
    ExpressionBytesOperationLjust3Base,
    ExpressionBytesOperationLowerBase,
    ExpressionBytesOperationLstrip1Base,
    ExpressionBytesOperationLstrip2Base,
    ExpressionBytesOperationPartitionBase,
    ExpressionBytesOperationReplace3Base,
    ExpressionBytesOperationReplace4Base,
    ExpressionBytesOperationRfind2Base,
    ExpressionBytesOperationRfind3Base,
    ExpressionBytesOperationRfind4Base,
    ExpressionBytesOperationRindex2Base,
    ExpressionBytesOperationRindex3Base,
    ExpressionBytesOperationRindex4Base,
    ExpressionBytesOperationRjust2Base,
    ExpressionBytesOperationRjust3Base,
    ExpressionBytesOperationRpartitionBase,
    ExpressionBytesOperationRsplit1Base,
    ExpressionBytesOperationRsplit2Base,
    ExpressionBytesOperationRsplit3Base,
    ExpressionBytesOperationRstrip1Base,
    ExpressionBytesOperationRstrip2Base,
    ExpressionBytesOperationSplit1Base,
    ExpressionBytesOperationSplit2Base,
    ExpressionBytesOperationSplit3Base,
    ExpressionBytesOperationSplitlines1Base,
    ExpressionBytesOperationSplitlines2Base,
    ExpressionBytesOperationStartswith2Base,
    ExpressionBytesOperationStartswith3Base,
    ExpressionBytesOperationStartswith4Base,
    ExpressionBytesOperationStrip1Base,
    ExpressionBytesOperationStrip2Base,
    ExpressionBytesOperationSwapcaseBase,
    ExpressionBytesOperationTitleBase,
    ExpressionBytesOperationTranslate2Base,
    ExpressionBytesOperationTranslate3Base,
    ExpressionBytesOperationUpperBase,
    ExpressionBytesOperationZfillBase,
)
from .ConstantRefNodes import makeConstantRefNode
from .ExpressionShapeMixins import ExpressionStrOrUnicodeExactMixin
from .NodeMetaClasses import NodeCheckMetaClass


def getBytesOperationClasses():
    """Return all bytes operation nodes, for use by code generation."""
    return (
        cls
        for kind, cls in NodeCheckMetaClass.kinds.items()
        if kind.startswith("EXPRESSION_BYTES_OPERATION_")
    )


class ExpressionBytesOperationJoin(ExpressionBytesOperationJoinBase):
    """This operation represents b.join(iterable)."""

    kind = "EXPRESSION_BYTES_OPERATION_JOIN"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationPartition(ExpressionBytesOperationPartitionBase):
    """This operation represents b.partition(sep)."""

    kind = "EXPRESSION_BYTES_OPERATION_PARTITION"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True

    @staticmethod
    def getIterationLength():
        return 3


class ExpressionBytesOperationRpartition(ExpressionBytesOperationRpartitionBase):
    """This operation represents b.rpartition(sep)."""

    kind = "EXPRESSION_BYTES_OPERATION_RPARTITION"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True

    @staticmethod
    def getIterationLength():
        return 3


class ExpressionBytesOperationStrip1(ExpressionBytesOperationStrip1Base):
    """This operation represents b.strip()."""

    kind = "EXPRESSION_BYTES_OPERATION_STRIP1"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionBytesOperationStrip2(ExpressionBytesOperationStrip2Base):
    """This operation represents b.strip(chars)."""

    kind = "EXPRESSION_BYTES_OPERATION_STRIP2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationLstrip1(ExpressionBytesOperationLstrip1Base):
    """This operation represents b.lstrip(chars)."""

    kind = "EXPRESSION_BYTES_OPERATION_LSTRIP1"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionBytesOperationLstrip2(ExpressionBytesOperationLstrip2Base):
    """This operation represents b.lstrip(chars)."""

    kind = "EXPRESSION_BYTES_OPERATION_LSTRIP2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationRstrip1(ExpressionBytesOperationRstrip1Base):
    """This operation represents b.rstrip()."""

    kind = "EXPRESSION_BYTES_OPERATION_RSTRIP1"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionBytesOperationRstrip2(ExpressionBytesOperationRstrip2Base):
    """This operation represents b.rstrip(chars)."""

    kind = "EXPRESSION_BYTES_OPERATION_RSTRIP2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationFind2(ExpressionBytesOperationFind2Base):
    """This operation represents b.find(sub)."""

    kind = "EXPRESSION_BYTES_OPERATION_FIND2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationFind3(ExpressionBytesOperationFind3Base):
    """This operation represents b.find(sub, start)."""

    kind = "EXPRESSION_BYTES_OPERATION_FIND3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationFind4(ExpressionBytesOperationFind4Base):
    """This operation represents b.find(sub, start, end)."""

    kind = "EXPRESSION_BYTES_OPERATION_FIND4"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationRfind2(ExpressionBytesOperationRfind2Base):
    """This operation represents b.rfind(sub)."""

    kind = "EXPRESSION_BYTES_OPERATION_RFIND2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationRfind3(ExpressionBytesOperationRfind3Base):
    """This operation represents b.rfind(sub, start)."""

    kind = "EXPRESSION_BYTES_OPERATION_RFIND3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationRfind4(ExpressionBytesOperationRfind4Base):
    """This operation represents b.rfind(sub, start, end)."""

    kind = "EXPRESSION_BYTES_OPERATION_RFIND4"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationIndex2(ExpressionBytesOperationIndex2Base):
    """This operation represents b.index(sub)."""

    kind = "EXPRESSION_BYTES_OPERATION_INDEX2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationIndex3(ExpressionBytesOperationIndex3Base):
    """This operation represents b.index(sub, start)."""

    kind = "EXPRESSION_BYTES_OPERATION_INDEX3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationIndex4(ExpressionBytesOperationIndex4Base):
    """This operation represents b.index(sub, start, end)."""

    kind = "EXPRESSION_BYTES_OPERATION_INDEX4"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationRindex2(ExpressionBytesOperationRindex2Base):
    """This operation represents b.rindex(sub)."""

    kind = "EXPRESSION_BYTES_OPERATION_RINDEX2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationRindex3(ExpressionBytesOperationRindex3Base):
    """This operation represents b.rindex(sub, start)."""

    kind = "EXPRESSION_BYTES_OPERATION_RINDEX3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationRindex4(ExpressionBytesOperationRindex4Base):
    """This operation represents b.rindex(sub, start, end)."""

    kind = "EXPRESSION_BYTES_OPERATION_RINDEX4"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationCapitalize(ExpressionBytesOperationCapitalizeBase):
    """This operation represents b.capitalize()."""

    kind = "EXPRESSION_BYTES_OPERATION_CAPITALIZE"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionBytesOperationUpper(ExpressionBytesOperationUpperBase):
    """This operation represents b.upper()."""

    kind = "EXPRESSION_BYTES_OPERATION_UPPER"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionBytesOperationLower(ExpressionBytesOperationLowerBase):
    """This operation represents b.lower()."""

    kind = "EXPRESSION_BYTES_OPERATION_LOWER"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionBytesOperationSwapcase(ExpressionBytesOperationSwapcaseBase):
    """This operation represents b.swapcase()."""

    kind = "EXPRESSION_BYTES_OPERATION_SWAPCASE"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionBytesOperationTitle(ExpressionBytesOperationTitleBase):
    """This operation represents b.title()."""

    kind = "EXPRESSION_BYTES_OPERATION_TITLE"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionBytesOperationIsalnum(ExpressionBytesOperationIsalnumBase):
    """This operation represents b.isalnum()."""

    kind = "EXPRESSION_BYTES_OPERATION_ISALNUM"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionBytesOperationIsalpha(ExpressionBytesOperationIsalphaBase):
    """This operation represents b.isalpha()."""

    kind = "EXPRESSION_BYTES_OPERATION_ISALPHA"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionBytesOperationIsdigit(ExpressionBytesOperationIsdigitBase):
    """This operation represents b.isdigit()."""

    kind = "EXPRESSION_BYTES_OPERATION_ISDIGIT"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionBytesOperationIslower(ExpressionBytesOperationIslowerBase):
    """This operation represents b.islower()."""

    kind = "EXPRESSION_BYTES_OPERATION_ISLOWER"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionBytesOperationIsupper(ExpressionBytesOperationIsupperBase):
    """This operation represents b.isupper()."""

    kind = "EXPRESSION_BYTES_OPERATION_ISUPPER"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionBytesOperationIsspace(ExpressionBytesOperationIsspaceBase):
    """This operation represents b.isspace()."""

    kind = "EXPRESSION_BYTES_OPERATION_ISSPACE"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionBytesOperationIstitle(ExpressionBytesOperationIstitleBase):
    """This operation represents b.istitle()."""

    kind = "EXPRESSION_BYTES_OPERATION_ISTITLE"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionBytesOperationSplit1(ExpressionBytesOperationSplit1Base):
    """This operation represents b.split()."""

    kind = "EXPRESSION_BYTES_OPERATION_SPLIT1"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionBytesOperationSplit2(ExpressionBytesOperationSplit2Base):
    """This operation represents b.split(sep)."""

    kind = "EXPRESSION_BYTES_OPERATION_SPLIT2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


def makeExpressionBytesOperationSplit3(bytes_arg, sep, maxsplit, source_ref):
    if sep is None:
        sep = makeConstantRefNode(constant=None, source_ref=source_ref)

    return ExpressionBytesOperationSplit3(
        bytes_arg=bytes_arg,
        sep=sep,
        maxsplit=maxsplit,
        source_ref=source_ref,
    )


class ExpressionBytesOperationSplit3(ExpressionBytesOperationSplit3Base):
    """This operation represents b.split(sep, maxsplit)."""

    kind = "EXPRESSION_BYTES_OPERATION_SPLIT3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


# TODO: This one could be eliminated in favor of simple ExpressionBytesOperationSplit1
# since without an argument, there is no difference.
class ExpressionBytesOperationRsplit1(ExpressionBytesOperationRsplit1Base):
    """This operation represents b.rsplit()."""

    kind = "EXPRESSION_BYTES_OPERATION_RSPLIT1"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionBytesOperationRsplit2(ExpressionBytesOperationRsplit2Base):
    """This operation represents b.rsplit(sep)."""

    kind = "EXPRESSION_BYTES_OPERATION_RSPLIT2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


def makeExpressionBytesOperationRsplit3(bytes_arg, sep, maxsplit, source_ref):
    if sep is None:
        sep = makeConstantRefNode(constant=None, source_ref=source_ref)

    return ExpressionBytesOperationRsplit3(
        bytes_arg=bytes_arg,
        sep=sep,
        maxsplit=maxsplit,
        source_ref=source_ref,
    )


class ExpressionBytesOperationRsplit3(ExpressionBytesOperationRsplit3Base):
    """This operation represents b.rsplit(sep, maxsplit)."""

    kind = "EXPRESSION_BYTES_OPERATION_RSPLIT3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationEndswith2(ExpressionBytesOperationEndswith2Base):
    kind = "EXPRESSION_BYTES_OPERATION_ENDSWITH2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationEndswith3(ExpressionBytesOperationEndswith3Base):
    kind = "EXPRESSION_BYTES_OPERATION_ENDSWITH3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationEndswith4(ExpressionBytesOperationEndswith4Base):
    kind = "EXPRESSION_BYTES_OPERATION_ENDSWITH4"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationStartswith2(ExpressionBytesOperationStartswith2Base):
    kind = "EXPRESSION_BYTES_OPERATION_STARTSWITH2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationStartswith3(ExpressionBytesOperationStartswith3Base):
    kind = "EXPRESSION_BYTES_OPERATION_STARTSWITH3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationStartswith4(ExpressionBytesOperationStartswith4Base):
    kind = "EXPRESSION_BYTES_OPERATION_STARTSWITH4"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationReplace3(ExpressionBytesOperationReplace3Base):
    kind = "EXPRESSION_BYTES_OPERATION_REPLACE3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationReplace4(ExpressionBytesOperationReplace4Base):
    kind = "EXPRESSION_BYTES_OPERATION_REPLACE4"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationDecodeMixin(ExpressionStrOrUnicodeExactMixin):
    __slots__ = ()

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments cannot be decoded
        return True


class ExpressionBytesOperationDecode1(
    ExpressionBytesOperationDecodeMixin, ExpressionBytesOperationDecode1Base
):
    kind = "EXPRESSION_BYTES_OPERATION_DECODE1"


class ExpressionBytesOperationDecode2(
    ExpressionBytesOperationDecodeMixin, ExpressionBytesOperationDecode2Base
):
    kind = "EXPRESSION_BYTES_OPERATION_DECODE2"

    def computeExpression(self, trace_collection):
        # TODO: Maybe demote for default values of encodings, e.g. UTF8, ASCII

        # We cannot know what error handlers or encodings got registered.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


def makeExpressionBytesOperationDecode3(bytes_arg, encoding, errors, source_ref):
    if encoding is None:
        encoding = makeConstantRefNode(constant="utf-8", source_ref=source_ref)

    return ExpressionBytesOperationDecode3(
        bytes_arg=bytes_arg,
        encoding=encoding,
        errors=errors,
        source_ref=source_ref,
    )


class ExpressionBytesOperationDecode3(
    ExpressionBytesOperationDecodeMixin, ExpressionBytesOperationDecode3Base
):
    kind = "EXPRESSION_BYTES_OPERATION_DECODE3"

    def computeExpression(self, trace_collection):
        # We cannot know what error handlers or encodings got registered.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionBytesOperationCount2(ExpressionBytesOperationCount2Base):
    kind = "EXPRESSION_BYTES_OPERATION_COUNT2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationCount3(ExpressionBytesOperationCount3Base):
    kind = "EXPRESSION_BYTES_OPERATION_COUNT3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationCount4(ExpressionBytesOperationCount4Base):
    kind = "EXPRESSION_BYTES_OPERATION_COUNT4"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationExpandtabs1(ExpressionBytesOperationExpandtabs1Base):
    """This operation represents b.expandtabs()."""

    kind = "EXPRESSION_BYTES_OPERATION_EXPANDTABS1"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionBytesOperationExpandtabs2(ExpressionBytesOperationExpandtabs2Base):
    kind = "EXPRESSION_BYTES_OPERATION_EXPANDTABS2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationTranslate2(ExpressionBytesOperationTranslate2Base):
    """This operation represents b.translate(table)."""

    kind = "EXPRESSION_BYTES_OPERATION_TRANSLATE2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationTranslate3(ExpressionBytesOperationTranslate3Base):
    """This operation represents b.translate(table, delete)."""

    kind = "EXPRESSION_BYTES_OPERATION_TRANSLATE3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationZfill(ExpressionBytesOperationZfillBase):
    """This operation represents b.zfill(width)."""

    kind = "EXPRESSION_BYTES_OPERATION_ZFILL"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationCenter2(ExpressionBytesOperationCenter2Base):
    kind = "EXPRESSION_BYTES_OPERATION_CENTER2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationCenter3(ExpressionBytesOperationCenter3Base):
    kind = "EXPRESSION_BYTES_OPERATION_CENTER3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationLjust2(ExpressionBytesOperationLjust2Base):
    kind = "EXPRESSION_BYTES_OPERATION_LJUST2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationLjust3(ExpressionBytesOperationLjust3Base):
    kind = "EXPRESSION_BYTES_OPERATION_LJUST3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationRjust2(ExpressionBytesOperationRjust2Base):
    kind = "EXPRESSION_BYTES_OPERATION_RJUST2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationRjust3(ExpressionBytesOperationRjust3Base):
    kind = "EXPRESSION_BYTES_OPERATION_RJUST3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionBytesOperationSplitlines1(ExpressionBytesOperationSplitlines1Base):
    """This operation represents b.splitlines()."""

    kind = "EXPRESSION_BYTES_OPERATION_SPLITLINES1"

    @staticmethod
    def mayRaiseExceptionOperation():
        # We do not count MemoryError
        return False


class ExpressionBytesOperationSplitlines2(ExpressionBytesOperationSplitlines2Base):
    """This operation represents b.splitlines(keepends)."""

    kind = "EXPRESSION_BYTES_OPERATION_SPLITLINES2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


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
