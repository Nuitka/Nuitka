#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Nodes that build and operate on str."""

from .BuiltinOperationNodeBasesGenerated import (
    ExpressionStrOperationCapitalizeBase,
    ExpressionStrOperationCasefoldBase,
    ExpressionStrOperationCenter2Base,
    ExpressionStrOperationCenter3Base,
    ExpressionStrOperationCount2Base,
    ExpressionStrOperationCount3Base,
    ExpressionStrOperationCount4Base,
    ExpressionStrOperationDecode1Base,
    ExpressionStrOperationDecode2Base,
    ExpressionStrOperationDecode3Base,
    ExpressionStrOperationEncode1Base,
    ExpressionStrOperationEncode2Base,
    ExpressionStrOperationEncode3Base,
    ExpressionStrOperationEndswith2Base,
    ExpressionStrOperationEndswith3Base,
    ExpressionStrOperationEndswith4Base,
    ExpressionStrOperationExpandtabs1Base,
    ExpressionStrOperationExpandtabs2Base,
    ExpressionStrOperationFind2Base,
    ExpressionStrOperationFind3Base,
    ExpressionStrOperationFind4Base,
    ExpressionStrOperationFormatBase,
    ExpressionStrOperationIndex2Base,
    ExpressionStrOperationIndex3Base,
    ExpressionStrOperationIndex4Base,
    ExpressionStrOperationIsalnumBase,
    ExpressionStrOperationIsalphaBase,
    ExpressionStrOperationIsasciiBase,
    ExpressionStrOperationIsdecimalBase,
    ExpressionStrOperationIsdigitBase,
    ExpressionStrOperationIsidentifierBase,
    ExpressionStrOperationIslowerBase,
    ExpressionStrOperationIsnumericBase,
    ExpressionStrOperationIsprintableBase,
    ExpressionStrOperationIsspaceBase,
    ExpressionStrOperationIstitleBase,
    ExpressionStrOperationIsupperBase,
    ExpressionStrOperationJoinBase,
    ExpressionStrOperationLjust2Base,
    ExpressionStrOperationLjust3Base,
    ExpressionStrOperationLowerBase,
    ExpressionStrOperationLstrip1Base,
    ExpressionStrOperationLstrip2Base,
    ExpressionStrOperationPartitionBase,
    ExpressionStrOperationReplace3Base,
    ExpressionStrOperationReplace4Base,
    ExpressionStrOperationRfind2Base,
    ExpressionStrOperationRfind3Base,
    ExpressionStrOperationRfind4Base,
    ExpressionStrOperationRindex2Base,
    ExpressionStrOperationRindex3Base,
    ExpressionStrOperationRindex4Base,
    ExpressionStrOperationRjust2Base,
    ExpressionStrOperationRjust3Base,
    ExpressionStrOperationRpartitionBase,
    ExpressionStrOperationRsplit1Base,
    ExpressionStrOperationRsplit2Base,
    ExpressionStrOperationRsplit3Base,
    ExpressionStrOperationRstrip1Base,
    ExpressionStrOperationRstrip2Base,
    ExpressionStrOperationSplit1Base,
    ExpressionStrOperationSplit2Base,
    ExpressionStrOperationSplit3Base,
    ExpressionStrOperationSplitlines1Base,
    ExpressionStrOperationSplitlines2Base,
    ExpressionStrOperationStartswith2Base,
    ExpressionStrOperationStartswith3Base,
    ExpressionStrOperationStartswith4Base,
    ExpressionStrOperationStrip1Base,
    ExpressionStrOperationStrip2Base,
    ExpressionStrOperationSwapcaseBase,
    ExpressionStrOperationTitleBase,
    ExpressionStrOperationTranslate2Base,
    ExpressionStrOperationTranslate3Base,
    ExpressionStrOperationUpperBase,
    ExpressionStrOperationZfillBase,
)
from .ConstantRefNodes import makeConstantRefNode
from .ExpressionShapeMixins import (
    ExpressionBytesShapeExactMixin,
    ExpressionStrOrUnicodeExactMixin,
    ExpressionStrShapeExactMixin,
)
from .NodeMetaClasses import NodeCheckMetaClass


def getStrOperationClasses():
    return (
        cls
        for kind, cls in NodeCheckMetaClass.kinds.items()
        if kind.startswith("EXPRESSION_STR_OPERATION_")
    )


class ExpressionStrOperationJoin(ExpressionStrOperationJoinBase):
    kind = "EXPRESSION_STR_OPERATION_JOIN"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationPartition(ExpressionStrOperationPartitionBase):
    kind = "EXPRESSION_STR_OPERATION_PARTITION"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True

    @staticmethod
    def getIterationLength():
        return 3


class ExpressionStrOperationRpartition(ExpressionStrOperationRpartitionBase):
    kind = "EXPRESSION_STR_OPERATION_RPARTITION"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True

    @staticmethod
    def getIterationLength():
        return 3


class ExpressionStrOperationStrip1(ExpressionStrOperationStrip1Base):
    kind = "EXPRESSION_STR_OPERATION_STRIP1"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationStrip2(ExpressionStrOperationStrip2Base):
    kind = "EXPRESSION_STR_OPERATION_STRIP2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationLstrip1(ExpressionStrOperationLstrip1Base):
    kind = "EXPRESSION_STR_OPERATION_LSTRIP1"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationLstrip2(ExpressionStrOperationLstrip2Base):
    kind = "EXPRESSION_STR_OPERATION_LSTRIP2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationRstrip1(ExpressionStrOperationRstrip1Base):
    kind = "EXPRESSION_STR_OPERATION_RSTRIP1"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationRstrip2(ExpressionStrOperationRstrip2Base):
    kind = "EXPRESSION_STR_OPERATION_RSTRIP2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationFind2(ExpressionStrOperationFind2Base):
    kind = "EXPRESSION_STR_OPERATION_FIND2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationFind3(ExpressionStrOperationFind3Base):
    kind = "EXPRESSION_STR_OPERATION_FIND3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationFind4(ExpressionStrOperationFind4Base):
    kind = "EXPRESSION_STR_OPERATION_FIND4"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationRfind2(ExpressionStrOperationRfind2Base):
    kind = "EXPRESSION_STR_OPERATION_RFIND2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationRfind3(ExpressionStrOperationRfind3Base):
    kind = "EXPRESSION_STR_OPERATION_RFIND3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationRfind4(ExpressionStrOperationRfind4Base):
    kind = "EXPRESSION_STR_OPERATION_RFIND4"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationIndex2(ExpressionStrOperationIndex2Base):
    kind = "EXPRESSION_STR_OPERATION_INDEX2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationIndex3(ExpressionStrOperationIndex3Base):
    kind = "EXPRESSION_STR_OPERATION_INDEX3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationIndex4(ExpressionStrOperationIndex4Base):
    kind = "EXPRESSION_STR_OPERATION_INDEX4"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationRindex2(ExpressionStrOperationRindex2Base):
    kind = "EXPRESSION_STR_OPERATION_RINDEX2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationRindex3(ExpressionStrOperationRindex3Base):
    kind = "EXPRESSION_STR_OPERATION_RINDEX3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationRindex4(ExpressionStrOperationRindex4Base):
    kind = "EXPRESSION_STR_OPERATION_RINDEX4"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationCapitalize(ExpressionStrOperationCapitalizeBase):
    kind = "EXPRESSION_STR_OPERATION_CAPITALIZE"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationCasefold(ExpressionStrOperationCasefoldBase):
    kind = "EXPRESSION_STR_OPERATION_CASEFOLD"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationUpper(ExpressionStrOperationUpperBase):
    kind = "EXPRESSION_STR_OPERATION_UPPER"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationLower(ExpressionStrOperationLowerBase):
    kind = "EXPRESSION_STR_OPERATION_LOWER"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationSwapcase(ExpressionStrOperationSwapcaseBase):
    kind = "EXPRESSION_STR_OPERATION_SWAPCASE"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationTitle(ExpressionStrOperationTitleBase):
    kind = "EXPRESSION_STR_OPERATION_TITLE"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationIsalnum(ExpressionStrOperationIsalnumBase):
    kind = "EXPRESSION_STR_OPERATION_ISALNUM"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationIsalpha(ExpressionStrOperationIsalphaBase):
    kind = "EXPRESSION_STR_OPERATION_ISALPHA"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationIsascii(ExpressionStrOperationIsasciiBase):
    kind = "EXPRESSION_STR_OPERATION_ISASCII"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationIsdigit(ExpressionStrOperationIsdigitBase):
    kind = "EXPRESSION_STR_OPERATION_ISDIGIT"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationIsdecimal(ExpressionStrOperationIsdecimalBase):
    kind = "EXPRESSION_STR_OPERATION_ISDECIMAL"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationIsidentifier(ExpressionStrOperationIsidentifierBase):
    kind = "EXPRESSION_STR_OPERATION_ISIDENTIFIER"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationIslower(ExpressionStrOperationIslowerBase):
    kind = "EXPRESSION_STR_OPERATION_ISLOWER"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationIsnumeric(ExpressionStrOperationIsnumericBase):
    kind = "EXPRESSION_STR_OPERATION_ISNUMERIC"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationIsprintable(ExpressionStrOperationIsprintableBase):
    kind = "EXPRESSION_STR_OPERATION_ISPRINTABLE"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationIsupper(ExpressionStrOperationIsupperBase):
    kind = "EXPRESSION_STR_OPERATION_ISUPPER"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationIsspace(ExpressionStrOperationIsspaceBase):
    kind = "EXPRESSION_STR_OPERATION_ISSPACE"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationIstitle(ExpressionStrOperationIstitleBase):
    kind = "EXPRESSION_STR_OPERATION_ISTITLE"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationSplit1(ExpressionStrOperationSplit1Base):
    kind = "EXPRESSION_STR_OPERATION_SPLIT1"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationSplit2(ExpressionStrOperationSplit2Base):
    kind = "EXPRESSION_STR_OPERATION_SPLIT2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


def makeExpressionStrOperationSplit3(str_arg, sep, maxsplit, source_ref):
    if sep is None:
        sep = makeConstantRefNode(constant=None, source_ref=source_ref)

    return ExpressionStrOperationSplit3(
        str_arg=str_arg,
        sep=sep,
        maxsplit=maxsplit,
        source_ref=source_ref,
    )


class ExpressionStrOperationSplit3(ExpressionStrOperationSplit3Base):
    kind = "EXPRESSION_STR_OPERATION_SPLIT3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


# TODO: This one could be eliminated in favor of simple ExpressionStrOperationSplit1
# since without an argument, there is no difference.
class ExpressionStrOperationRsplit1(ExpressionStrOperationRsplit1Base):
    kind = "EXPRESSION_STR_OPERATION_RSPLIT1"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationRsplit2(ExpressionStrOperationRsplit2Base):
    kind = "EXPRESSION_STR_OPERATION_RSPLIT2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


def makeExpressionStrOperationRsplit3(str_arg, sep, maxsplit, source_ref):
    if sep is None:
        sep = makeConstantRefNode(constant=None, source_ref=source_ref)

    return ExpressionStrOperationRsplit3(
        str_arg=str_arg,
        sep=sep,
        maxsplit=maxsplit,
        source_ref=source_ref,
    )


class ExpressionStrOperationRsplit3(ExpressionStrOperationRsplit3Base):
    kind = "EXPRESSION_STR_OPERATION_RSPLIT3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationEndswith2(ExpressionStrOperationEndswith2Base):
    kind = "EXPRESSION_STR_OPERATION_ENDSWITH2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationEndswith3(ExpressionStrOperationEndswith3Base):
    kind = "EXPRESSION_STR_OPERATION_ENDSWITH3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationEndswith4(ExpressionStrOperationEndswith4Base):
    kind = "EXPRESSION_STR_OPERATION_ENDSWITH4"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationStartswith2(ExpressionStrOperationStartswith2Base):
    kind = "EXPRESSION_STR_OPERATION_STARTSWITH2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationStartswith3(ExpressionStrOperationStartswith3Base):
    kind = "EXPRESSION_STR_OPERATION_STARTSWITH3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationStartswith4(ExpressionStrOperationStartswith4Base):
    kind = "EXPRESSION_STR_OPERATION_STARTSWITH4"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationReplace3(ExpressionStrOperationReplace3Base):
    kind = "EXPRESSION_STR_OPERATION_REPLACE3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationReplace4(ExpressionStrOperationReplace4Base):
    kind = "EXPRESSION_STR_OPERATION_REPLACE4"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


# TODO: Cannot yet do this with static code generation in the base class.
class ExpressionStrOperationEncodeMixin(
    ExpressionBytesShapeExactMixin if str is not bytes else ExpressionStrShapeExactMixin
):
    __slots__ = ()

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments cannot be encoded
        return True


class ExpressionStrOperationEncode1(
    ExpressionStrOperationEncodeMixin, ExpressionStrOperationEncode1Base
):
    kind = "EXPRESSION_STR_OPERATION_ENCODE1"


class ExpressionStrOperationEncode2(
    ExpressionStrOperationEncodeMixin, ExpressionStrOperationEncode2Base
):
    kind = "EXPRESSION_STR_OPERATION_ENCODE2"

    def computeExpression(self, trace_collection):
        # TODO: Maybe demote for default values of encodings, e.g. UTF8, ASCII
        #
        # We cannot know what error handlers or encodings got registered.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


def makeExpressionStrOperationEncode3(str_arg, encoding, errors, source_ref):
    if encoding is None:
        encoding = makeConstantRefNode(constant="utf-8", source_ref=source_ref)

    return ExpressionStrOperationEncode3(
        str_arg=str_arg, encoding=encoding, errors=errors, source_ref=source_ref
    )


class ExpressionStrOperationEncode3(
    ExpressionStrOperationEncodeMixin, ExpressionStrOperationEncode3Base
):
    kind = "EXPRESSION_STR_OPERATION_ENCODE3"

    def computeExpression(self, trace_collection):
        # We cannot know what error handlers or encodings got registered.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


# TODO: Cannot yet do this with static code generation in the base class.
class ExpressionStrOperationDecodeMixin(ExpressionStrOrUnicodeExactMixin):
    __slots__ = ()

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments cannot be decoded
        return True


class ExpressionStrOperationDecode1(
    ExpressionStrOperationDecodeMixin, ExpressionStrOperationDecode1Base
):
    kind = "EXPRESSION_STR_OPERATION_DECODE1"


class ExpressionStrOperationDecode2(
    ExpressionStrOperationDecodeMixin, ExpressionStrOperationDecode2Base
):
    kind = "EXPRESSION_STR_OPERATION_DECODE2"

    def computeExpression(self, trace_collection):
        # TODO: Maybe demote for default values of encodings, e.g. UTF8, ASCII

        # We cannot know what error handlers or encodings got registered.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrOperationDecode3(
    ExpressionStrOperationDecodeMixin, ExpressionStrOperationDecode3Base
):
    kind = "EXPRESSION_STR_OPERATION_DECODE3"

    def computeExpression(self, trace_collection):
        # We cannot know what error handlers or encodings got registered.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionStrOperationCount2(ExpressionStrOperationCount2Base):
    kind = "EXPRESSION_STR_OPERATION_COUNT2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationCount3(ExpressionStrOperationCount3Base):
    kind = "EXPRESSION_STR_OPERATION_COUNT3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationCount4(ExpressionStrOperationCount4Base):
    kind = "EXPRESSION_STR_OPERATION_COUNT4"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationFormat(ExpressionStrOperationFormatBase):
    named_children = ("str_arg", "args|tuple", "pairs|tuple")

    kind = "EXPRESSION_STR_OPERATION_FORMAT"

    def computeExpression(self, trace_collection):
        str_arg = self.subnode_str_arg
        args = self.subnode_args
        pairs = self.subnode_pairs

        # TODO: Partially constant could also be propagated into there.

        if (
            str_arg.isCompileTimeConstant()
            and all(arg.isCompileTimeConstant() for arg in args)
            and all(pair.isCompileTimeConstant() for pair in pairs)
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.format(
                    str_arg.getCompileTimeConstant(),
                    *(arg.getCompileTimeConstant() for arg in args),
                    **dict(
                        (
                            pair.getKeyCompileTimeConstant(),
                            pair.getValueCompileTimeConstant(),
                        )
                        for pair in pairs
                    )
                ),
                description="Built-in 'str.format' with constant values.",
                user_provided=str_arg.user_provided,
            )

        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    # TODO: Format strings are not yet looked at
    @staticmethod
    def mayRaiseException(exception_type):
        return True

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationExpandtabs1(ExpressionStrOperationExpandtabs1Base):
    kind = "EXPRESSION_STR_OPERATION_EXPANDTABS1"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionStrOperationExpandtabs2(ExpressionStrOperationExpandtabs2Base):
    kind = "EXPRESSION_STR_OPERATION_EXPANDTABS2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationTranslate2(ExpressionStrOperationTranslate2Base):
    kind = "EXPRESSION_STR_OPERATION_TRANSLATE2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationTranslate3(ExpressionStrOperationTranslate3Base):
    kind = "EXPRESSION_STR_OPERATION_TRANSLATE3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationZfill(ExpressionStrOperationZfillBase):
    kind = "EXPRESSION_STR_OPERATION_ZFILL"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationCenter2(ExpressionStrOperationCenter2Base):
    kind = "EXPRESSION_STR_OPERATION_CENTER2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationCenter3(ExpressionStrOperationCenter3Base):
    kind = "EXPRESSION_STR_OPERATION_CENTER3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationLjust2(ExpressionStrOperationLjust2Base):
    kind = "EXPRESSION_STR_OPERATION_LJUST2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationLjust3(ExpressionStrOperationLjust3Base):
    kind = "EXPRESSION_STR_OPERATION_LJUST3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationRjust2(ExpressionStrOperationRjust2Base):
    kind = "EXPRESSION_STR_OPERATION_RJUST2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationRjust3(ExpressionStrOperationRjust3Base):
    kind = "EXPRESSION_STR_OPERATION_RJUST3"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


class ExpressionStrOperationSplitlines1(ExpressionStrOperationSplitlines1Base):
    kind = "EXPRESSION_STR_OPERATION_SPLITLINES1"

    @staticmethod
    def mayRaiseExceptionOperation():
        # We do not count MemoryError
        return False


class ExpressionStrOperationSplitlines2(ExpressionStrOperationSplitlines2Base):
    kind = "EXPRESSION_STR_OPERATION_SPLITLINES2"

    @staticmethod
    def mayRaiseExceptionOperation():
        # TODO: Only if the arguments have wrong shapes, code generation needs to use this too.
        return True


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
