#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# We are not avoiding these in generated code at all
# pylint: disable=I0021,line-too-long,too-many-instance-attributes,too-many-lines
# pylint: disable=I0021,too-many-arguments,too-many-return-statements,too-many-statements


"""Specialized attribute nodes

WARNING, this code is GENERATED. Modify the template BuiltinOperationNodeBases.py.j2 instead!

spell-checker: ignore __prepare__ append args autograph capitalize casefold center chars
spell-checker: ignore clear copy count decode default delete dist distribution_name encode
spell-checker: ignore encoding end endswith errors exit_code expandtabs
spell-checker: ignore experimental_attributes experimental_autograph_options
spell-checker: ignore experimental_compile experimental_follow_type_hints
spell-checker: ignore experimental_implements experimental_relax_shapes extend fillchar
spell-checker: ignore find format format_map formatmap fromkeys func get group handle
spell-checker: ignore has_key haskey index input_signature insert isalnum isalpha isascii
spell-checker: ignore isdecimal isdigit isidentifier islower isnumeric isprintable isspace
spell-checker: ignore istitle isupper item items iterable iteritems iterkeys itervalues
spell-checker: ignore jit_compile join keepends key keys kwargs ljust lower lstrip
spell-checker: ignore maketrans maxsplit mode name new old p package
spell-checker: ignore package_or_requirement pairs partition path pop popitem prefix
spell-checker: ignore prepare reduce_retracing remove replace resource resource_name
spell-checker: ignore reverse rfind rindex rjust rpartition rsplit rstrip s sep setdefault
spell-checker: ignore sort split splitlines start startswith stop strip sub suffix
spell-checker: ignore swapcase table tabsize title translate update upper use_errno
spell-checker: ignore use_last_error value values viewitems viewkeys viewvalues width
spell-checker: ignore winmode zfill
"""


from abc import abstractmethod

from .ChildrenHavingMixins import (
    ChildHavingBytesArgMixin,
    ChildHavingDictArgMixin,
    ChildHavingIterableMixin,
    ChildHavingStrArgMixin,
    ChildrenHavingBytesArgCharsMixin,
    ChildrenHavingBytesArgEncodingErrorsMixin,
    ChildrenHavingBytesArgEncodingMixin,
    ChildrenHavingBytesArgIterableMixin,
    ChildrenHavingBytesArgKeependsMixin,
    ChildrenHavingBytesArgOldNewCountMixin,
    ChildrenHavingBytesArgOldNewMixin,
    ChildrenHavingBytesArgPrefixMixin,
    ChildrenHavingBytesArgPrefixStartEndMixin,
    ChildrenHavingBytesArgPrefixStartMixin,
    ChildrenHavingBytesArgSepMaxsplitMixin,
    ChildrenHavingBytesArgSepMixin,
    ChildrenHavingBytesArgSubMixin,
    ChildrenHavingBytesArgSubStartEndMixin,
    ChildrenHavingBytesArgSubStartMixin,
    ChildrenHavingBytesArgSuffixMixin,
    ChildrenHavingBytesArgSuffixStartEndMixin,
    ChildrenHavingBytesArgSuffixStartMixin,
    ChildrenHavingBytesArgTableDeleteMixin,
    ChildrenHavingBytesArgTableMixin,
    ChildrenHavingBytesArgTabsizeMixin,
    ChildrenHavingBytesArgWidthFillcharMixin,
    ChildrenHavingBytesArgWidthMixin,
    ChildrenHavingDictArgIterableMixin,
    ChildrenHavingDictArgIterablePairsTupleMixin,
    ChildrenHavingDictArgKeyDefaultMixin,
    ChildrenHavingDictArgKeyMixin,
    ChildrenHavingIterableValueMixin,
    ChildrenHavingStrArgArgsTuplePairsTupleMixin,
    ChildrenHavingStrArgCharsMixin,
    ChildrenHavingStrArgEncodingErrorsMixin,
    ChildrenHavingStrArgEncodingMixin,
    ChildrenHavingStrArgIterableMixin,
    ChildrenHavingStrArgKeependsMixin,
    ChildrenHavingStrArgOldNewCountMixin,
    ChildrenHavingStrArgOldNewMixin,
    ChildrenHavingStrArgPrefixMixin,
    ChildrenHavingStrArgPrefixStartEndMixin,
    ChildrenHavingStrArgPrefixStartMixin,
    ChildrenHavingStrArgSepMaxsplitMixin,
    ChildrenHavingStrArgSepMixin,
    ChildrenHavingStrArgSubMixin,
    ChildrenHavingStrArgSubStartEndMixin,
    ChildrenHavingStrArgSubStartMixin,
    ChildrenHavingStrArgSuffixMixin,
    ChildrenHavingStrArgSuffixStartEndMixin,
    ChildrenHavingStrArgSuffixStartMixin,
    ChildrenHavingStrArgTableMixin,
    ChildrenHavingStrArgTabsizeMixin,
    ChildrenHavingStrArgWidthFillcharMixin,
    ChildrenHavingStrArgWidthMixin,
)
from .ExpressionBases import ExpressionBase
from .ExpressionShapeMixins import (
    ExpressionBoolShapeExactMixin,
    ExpressionBytesShapeExactMixin,
    ExpressionDictShapeExactMixin,
    ExpressionIntShapeExactMixin,
    ExpressionListShapeExactMixin,
    ExpressionNoneShapeExactMixin,
    ExpressionStrShapeExactMixin,
    ExpressionTupleShapeExactMixin,
)


class ExpressionStrOperationCapitalizeBase(
    ExpressionStrShapeExactMixin, ChildHavingStrArgMixin, ExpressionBase
):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.capitalize(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.capitalize' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationCapitalizeBase(
    ExpressionBytesShapeExactMixin, ChildHavingBytesArgMixin, ExpressionBase
):
    named_children = ("bytes_arg",)

    def __init__(self, bytes_arg, source_ref):
        ChildHavingBytesArgMixin.__init__(
            self,
            bytes_arg=bytes_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_bytes_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.capitalize(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.capitalize' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationCasefoldBase(ChildHavingStrArgMixin, ExpressionBase):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.casefold(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.casefold' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationCenter3Base(
    ExpressionStrShapeExactMixin, ChildrenHavingStrArgWidthFillcharMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "width",
        "fillchar",
    )

    def __init__(self, str_arg, width, fillchar, source_ref):
        ChildrenHavingStrArgWidthFillcharMixin.__init__(
            self,
            str_arg=str_arg,
            width=width,
            fillchar=fillchar,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_width.isCompileTimeConstant()
            and self.subnode_fillchar.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.center(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_width.getCompileTimeConstant(),
                    self.subnode_fillchar.getCompileTimeConstant(),
                ),
                description="Built-in 'str.center' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_width.mayRaiseException(exception_type)
            or self.subnode_fillchar.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationCenter2Base(
    ExpressionStrShapeExactMixin, ChildrenHavingStrArgWidthMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "width",
    )

    def __init__(self, str_arg, width, source_ref):
        ChildrenHavingStrArgWidthMixin.__init__(
            self,
            str_arg=str_arg,
            width=width,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_width.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.center(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_width.getCompileTimeConstant(),
                ),
                description="Built-in 'str.center' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_width.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationCenter3Base(
    ExpressionBytesShapeExactMixin,
    ChildrenHavingBytesArgWidthFillcharMixin,
    ExpressionBase,
):
    named_children = (
        "bytes_arg",
        "width",
        "fillchar",
    )

    def __init__(self, bytes_arg, width, fillchar, source_ref):
        ChildrenHavingBytesArgWidthFillcharMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            width=width,
            fillchar=fillchar,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_width.isCompileTimeConstant()
            and self.subnode_fillchar.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.center(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_width.getCompileTimeConstant(),
                    self.subnode_fillchar.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.center' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_width.mayRaiseException(exception_type)
            or self.subnode_fillchar.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationCenter2Base(
    ExpressionBytesShapeExactMixin, ChildrenHavingBytesArgWidthMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "width",
    )

    def __init__(self, bytes_arg, width, source_ref):
        ChildrenHavingBytesArgWidthMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            width=width,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_width.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.center(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_width.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.center' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_width.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionDictOperationClearBase(
    ExpressionNoneShapeExactMixin, ChildHavingDictArgMixin, ExpressionBase
):
    named_children = ("dict_arg",)

    def __init__(self, dict_arg, source_ref):
        ChildHavingDictArgMixin.__init__(
            self,
            dict_arg=dict_arg,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionDictOperationCopyBase(
    ExpressionDictShapeExactMixin, ChildHavingDictArgMixin, ExpressionBase
):
    named_children = ("dict_arg",)

    def __init__(self, dict_arg, source_ref):
        ChildHavingDictArgMixin.__init__(
            self,
            dict_arg=dict_arg,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionStrOperationCount4Base(
    ExpressionIntShapeExactMixin, ChildrenHavingStrArgSubStartEndMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "sub",
        "start",
        "end",
    )

    def __init__(self, str_arg, sub, start, end, source_ref):
        ChildrenHavingStrArgSubStartEndMixin.__init__(
            self,
            str_arg=str_arg,
            sub=sub,
            start=start,
            end=end,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
            and self.subnode_end.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.count(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                    self.subnode_end.getCompileTimeConstant(),
                ),
                description="Built-in 'str.count' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.subnode_end.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationCount3Base(
    ExpressionIntShapeExactMixin, ChildrenHavingStrArgSubStartMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "sub",
        "start",
    )

    def __init__(self, str_arg, sub, start, source_ref):
        ChildrenHavingStrArgSubStartMixin.__init__(
            self,
            str_arg=str_arg,
            sub=sub,
            start=start,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.count(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                ),
                description="Built-in 'str.count' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationCount2Base(
    ExpressionIntShapeExactMixin, ChildrenHavingStrArgSubMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "sub",
    )

    def __init__(self, str_arg, sub, source_ref):
        ChildrenHavingStrArgSubMixin.__init__(
            self,
            str_arg=str_arg,
            sub=sub,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.count(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                ),
                description="Built-in 'str.count' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationCount4Base(
    ExpressionIntShapeExactMixin, ChildrenHavingBytesArgSubStartEndMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "sub",
        "start",
        "end",
    )

    def __init__(self, bytes_arg, sub, start, end, source_ref):
        ChildrenHavingBytesArgSubStartEndMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            sub=sub,
            start=start,
            end=end,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
            and self.subnode_end.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.count(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                    self.subnode_end.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.count' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.subnode_end.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationCount3Base(
    ExpressionIntShapeExactMixin, ChildrenHavingBytesArgSubStartMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "sub",
        "start",
    )

    def __init__(self, bytes_arg, sub, start, source_ref):
        ChildrenHavingBytesArgSubStartMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            sub=sub,
            start=start,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.count(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.count' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationCount2Base(
    ExpressionIntShapeExactMixin, ChildrenHavingBytesArgSubMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "sub",
    )

    def __init__(self, bytes_arg, sub, source_ref):
        ChildrenHavingBytesArgSubMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            sub=sub,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.count(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.count' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationDecode3Base(
    ChildrenHavingStrArgEncodingErrorsMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "encoding",
        "errors",
    )

    def __init__(self, str_arg, encoding, errors, source_ref):
        ChildrenHavingStrArgEncodingErrorsMixin.__init__(
            self,
            str_arg=str_arg,
            encoding=encoding,
            errors=errors,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_encoding.isCompileTimeConstant()
            and self.subnode_errors.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.decode(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_encoding.getCompileTimeConstant(),
                    self.subnode_errors.getCompileTimeConstant(),
                ),
                description="Built-in 'str.decode' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_encoding.mayRaiseException(exception_type)
            or self.subnode_errors.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationDecode2Base(
    ChildrenHavingStrArgEncodingMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "encoding",
    )

    def __init__(self, str_arg, encoding, source_ref):
        ChildrenHavingStrArgEncodingMixin.__init__(
            self,
            str_arg=str_arg,
            encoding=encoding,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_encoding.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.decode(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_encoding.getCompileTimeConstant(),
                ),
                description="Built-in 'str.decode' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_encoding.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationDecode1Base(ChildHavingStrArgMixin, ExpressionBase):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.decode(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.decode' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationDecode3Base(
    ExpressionStrShapeExactMixin,
    ChildrenHavingBytesArgEncodingErrorsMixin,
    ExpressionBase,
):
    named_children = (
        "bytes_arg",
        "encoding",
        "errors",
    )

    def __init__(self, bytes_arg, encoding, errors, source_ref):
        ChildrenHavingBytesArgEncodingErrorsMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            encoding=encoding,
            errors=errors,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_encoding.isCompileTimeConstant()
            and self.subnode_errors.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.decode(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_encoding.getCompileTimeConstant(),
                    self.subnode_errors.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.decode' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_encoding.mayRaiseException(exception_type)
            or self.subnode_errors.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationDecode2Base(
    ExpressionStrShapeExactMixin, ChildrenHavingBytesArgEncodingMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "encoding",
    )

    def __init__(self, bytes_arg, encoding, source_ref):
        ChildrenHavingBytesArgEncodingMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            encoding=encoding,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_encoding.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.decode(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_encoding.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.decode' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_encoding.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationDecode1Base(
    ExpressionStrShapeExactMixin, ChildHavingBytesArgMixin, ExpressionBase
):
    named_children = ("bytes_arg",)

    def __init__(self, bytes_arg, source_ref):
        ChildHavingBytesArgMixin.__init__(
            self,
            bytes_arg=bytes_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_bytes_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.decode(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.decode' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationEncode3Base(
    ChildrenHavingStrArgEncodingErrorsMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "encoding",
        "errors",
    )

    def __init__(self, str_arg, encoding, errors, source_ref):
        ChildrenHavingStrArgEncodingErrorsMixin.__init__(
            self,
            str_arg=str_arg,
            encoding=encoding,
            errors=errors,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_encoding.isCompileTimeConstant()
            and self.subnode_errors.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.encode(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_encoding.getCompileTimeConstant(),
                    self.subnode_errors.getCompileTimeConstant(),
                ),
                description="Built-in 'str.encode' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_encoding.mayRaiseException(exception_type)
            or self.subnode_errors.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationEncode2Base(
    ChildrenHavingStrArgEncodingMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "encoding",
    )

    def __init__(self, str_arg, encoding, source_ref):
        ChildrenHavingStrArgEncodingMixin.__init__(
            self,
            str_arg=str_arg,
            encoding=encoding,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_encoding.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.encode(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_encoding.getCompileTimeConstant(),
                ),
                description="Built-in 'str.encode' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_encoding.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationEncode1Base(ChildHavingStrArgMixin, ExpressionBase):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.encode(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.encode' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationEndswith4Base(
    ExpressionBoolShapeExactMixin,
    ChildrenHavingStrArgSuffixStartEndMixin,
    ExpressionBase,
):
    named_children = (
        "str_arg",
        "suffix",
        "start",
        "end",
    )

    def __init__(self, str_arg, suffix, start, end, source_ref):
        ChildrenHavingStrArgSuffixStartEndMixin.__init__(
            self,
            str_arg=str_arg,
            suffix=suffix,
            start=start,
            end=end,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_suffix.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
            and self.subnode_end.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.endswith(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_suffix.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                    self.subnode_end.getCompileTimeConstant(),
                ),
                description="Built-in 'str.endswith' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_suffix.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.subnode_end.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationEndswith3Base(
    ExpressionBoolShapeExactMixin, ChildrenHavingStrArgSuffixStartMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "suffix",
        "start",
    )

    def __init__(self, str_arg, suffix, start, source_ref):
        ChildrenHavingStrArgSuffixStartMixin.__init__(
            self,
            str_arg=str_arg,
            suffix=suffix,
            start=start,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_suffix.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.endswith(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_suffix.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                ),
                description="Built-in 'str.endswith' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_suffix.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationEndswith2Base(
    ExpressionBoolShapeExactMixin, ChildrenHavingStrArgSuffixMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "suffix",
    )

    def __init__(self, str_arg, suffix, source_ref):
        ChildrenHavingStrArgSuffixMixin.__init__(
            self,
            str_arg=str_arg,
            suffix=suffix,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_suffix.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.endswith(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_suffix.getCompileTimeConstant(),
                ),
                description="Built-in 'str.endswith' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_suffix.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationEndswith4Base(
    ExpressionBoolShapeExactMixin,
    ChildrenHavingBytesArgSuffixStartEndMixin,
    ExpressionBase,
):
    named_children = (
        "bytes_arg",
        "suffix",
        "start",
        "end",
    )

    def __init__(self, bytes_arg, suffix, start, end, source_ref):
        ChildrenHavingBytesArgSuffixStartEndMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            suffix=suffix,
            start=start,
            end=end,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_suffix.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
            and self.subnode_end.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.endswith(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_suffix.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                    self.subnode_end.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.endswith' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_suffix.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.subnode_end.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationEndswith3Base(
    ExpressionBoolShapeExactMixin,
    ChildrenHavingBytesArgSuffixStartMixin,
    ExpressionBase,
):
    named_children = (
        "bytes_arg",
        "suffix",
        "start",
    )

    def __init__(self, bytes_arg, suffix, start, source_ref):
        ChildrenHavingBytesArgSuffixStartMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            suffix=suffix,
            start=start,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_suffix.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.endswith(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_suffix.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.endswith' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_suffix.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationEndswith2Base(
    ExpressionBoolShapeExactMixin, ChildrenHavingBytesArgSuffixMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "suffix",
    )

    def __init__(self, bytes_arg, suffix, source_ref):
        ChildrenHavingBytesArgSuffixMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            suffix=suffix,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_suffix.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.endswith(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_suffix.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.endswith' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_suffix.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationExpandtabs2Base(
    ExpressionStrShapeExactMixin, ChildrenHavingStrArgTabsizeMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "tabsize",
    )

    def __init__(self, str_arg, tabsize, source_ref):
        ChildrenHavingStrArgTabsizeMixin.__init__(
            self,
            str_arg=str_arg,
            tabsize=tabsize,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_tabsize.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.expandtabs(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_tabsize.getCompileTimeConstant(),
                ),
                description="Built-in 'str.expandtabs' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_tabsize.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationExpandtabs1Base(
    ExpressionStrShapeExactMixin, ChildHavingStrArgMixin, ExpressionBase
):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.expandtabs(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.expandtabs' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationExpandtabs2Base(
    ExpressionBytesShapeExactMixin, ChildrenHavingBytesArgTabsizeMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "tabsize",
    )

    def __init__(self, bytes_arg, tabsize, source_ref):
        ChildrenHavingBytesArgTabsizeMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            tabsize=tabsize,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_tabsize.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.expandtabs(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_tabsize.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.expandtabs' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_tabsize.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationExpandtabs1Base(
    ExpressionBytesShapeExactMixin, ChildHavingBytesArgMixin, ExpressionBase
):
    named_children = ("bytes_arg",)

    def __init__(self, bytes_arg, source_ref):
        ChildHavingBytesArgMixin.__init__(
            self,
            bytes_arg=bytes_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_bytes_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.expandtabs(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.expandtabs' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationFind4Base(
    ExpressionIntShapeExactMixin, ChildrenHavingStrArgSubStartEndMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "sub",
        "start",
        "end",
    )

    def __init__(self, str_arg, sub, start, end, source_ref):
        ChildrenHavingStrArgSubStartEndMixin.__init__(
            self,
            str_arg=str_arg,
            sub=sub,
            start=start,
            end=end,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
            and self.subnode_end.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.find(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                    self.subnode_end.getCompileTimeConstant(),
                ),
                description="Built-in 'str.find' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.subnode_end.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationFind3Base(
    ExpressionIntShapeExactMixin, ChildrenHavingStrArgSubStartMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "sub",
        "start",
    )

    def __init__(self, str_arg, sub, start, source_ref):
        ChildrenHavingStrArgSubStartMixin.__init__(
            self,
            str_arg=str_arg,
            sub=sub,
            start=start,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.find(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                ),
                description="Built-in 'str.find' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationFind2Base(
    ExpressionIntShapeExactMixin, ChildrenHavingStrArgSubMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "sub",
    )

    def __init__(self, str_arg, sub, source_ref):
        ChildrenHavingStrArgSubMixin.__init__(
            self,
            str_arg=str_arg,
            sub=sub,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.find(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                ),
                description="Built-in 'str.find' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationFind4Base(
    ExpressionIntShapeExactMixin, ChildrenHavingBytesArgSubStartEndMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "sub",
        "start",
        "end",
    )

    def __init__(self, bytes_arg, sub, start, end, source_ref):
        ChildrenHavingBytesArgSubStartEndMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            sub=sub,
            start=start,
            end=end,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
            and self.subnode_end.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.find(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                    self.subnode_end.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.find' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.subnode_end.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationFind3Base(
    ExpressionIntShapeExactMixin, ChildrenHavingBytesArgSubStartMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "sub",
        "start",
    )

    def __init__(self, bytes_arg, sub, start, source_ref):
        ChildrenHavingBytesArgSubStartMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            sub=sub,
            start=start,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.find(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.find' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationFind2Base(
    ExpressionIntShapeExactMixin, ChildrenHavingBytesArgSubMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "sub",
    )

    def __init__(self, bytes_arg, sub, source_ref):
        ChildrenHavingBytesArgSubMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            sub=sub,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.find(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.find' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationFormatBase(
    ExpressionStrShapeExactMixin,
    ChildrenHavingStrArgArgsTuplePairsTupleMixin,
    ExpressionBase,
):
    named_children = (
        "str_arg",
        "args|tuple",
        "pairs|tuple",
    )

    def __init__(self, str_arg, args, pairs, source_ref):
        ChildrenHavingStrArgArgsTuplePairsTupleMixin.__init__(
            self,
            str_arg=str_arg,
            args=args,
            pairs=pairs,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_args.isCompileTimeConstant()
            and self.subnode_pairs.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.format(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_args.getCompileTimeConstant(),
                    self.subnode_pairs.getCompileTimeConstant(),
                ),
                description="Built-in 'str.format' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_args.mayRaiseException(exception_type)
            or self.subnode_pairs.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationFormatmapBase(ChildHavingStrArgMixin, ExpressionBase):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.format_map(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.format_map' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionDictOperationFromkeys3Base(
    ExpressionDictShapeExactMixin, ChildrenHavingIterableValueMixin, ExpressionBase
):
    named_children = (
        "iterable",
        "value",
    )

    def __init__(self, iterable, value, source_ref):
        ChildrenHavingIterableValueMixin.__init__(
            self,
            iterable=iterable,
            value=value,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionDictOperationFromkeys2Base(
    ExpressionDictShapeExactMixin, ChildHavingIterableMixin, ExpressionBase
):
    named_children = ("iterable",)

    def __init__(self, iterable, source_ref):
        ChildHavingIterableMixin.__init__(
            self,
            iterable=iterable,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionDictOperationGet3Base(
    ChildrenHavingDictArgKeyDefaultMixin, ExpressionBase
):
    named_children = (
        "dict_arg",
        "key",
        "default",
    )

    def __init__(self, dict_arg, key, default, source_ref):
        ChildrenHavingDictArgKeyDefaultMixin.__init__(
            self,
            dict_arg=dict_arg,
            key=key,
            default=default,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionDictOperationGet2Base(ChildrenHavingDictArgKeyMixin, ExpressionBase):
    named_children = (
        "dict_arg",
        "key",
    )

    def __init__(self, dict_arg, key, source_ref):
        ChildrenHavingDictArgKeyMixin.__init__(
            self,
            dict_arg=dict_arg,
            key=key,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionDictOperationHaskeyBase(
    ExpressionBoolShapeExactMixin, ChildrenHavingDictArgKeyMixin, ExpressionBase
):
    named_children = (
        "dict_arg",
        "key",
    )

    def __init__(self, dict_arg, key, source_ref):
        ChildrenHavingDictArgKeyMixin.__init__(
            self,
            dict_arg=dict_arg,
            key=key,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionStrOperationIndex4Base(
    ExpressionIntShapeExactMixin, ChildrenHavingStrArgSubStartEndMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "sub",
        "start",
        "end",
    )

    def __init__(self, str_arg, sub, start, end, source_ref):
        ChildrenHavingStrArgSubStartEndMixin.__init__(
            self,
            str_arg=str_arg,
            sub=sub,
            start=start,
            end=end,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
            and self.subnode_end.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.index(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                    self.subnode_end.getCompileTimeConstant(),
                ),
                description="Built-in 'str.index' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.subnode_end.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationIndex3Base(
    ExpressionIntShapeExactMixin, ChildrenHavingStrArgSubStartMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "sub",
        "start",
    )

    def __init__(self, str_arg, sub, start, source_ref):
        ChildrenHavingStrArgSubStartMixin.__init__(
            self,
            str_arg=str_arg,
            sub=sub,
            start=start,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.index(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                ),
                description="Built-in 'str.index' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationIndex2Base(
    ExpressionIntShapeExactMixin, ChildrenHavingStrArgSubMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "sub",
    )

    def __init__(self, str_arg, sub, source_ref):
        ChildrenHavingStrArgSubMixin.__init__(
            self,
            str_arg=str_arg,
            sub=sub,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.index(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                ),
                description="Built-in 'str.index' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationIndex4Base(
    ExpressionIntShapeExactMixin, ChildrenHavingBytesArgSubStartEndMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "sub",
        "start",
        "end",
    )

    def __init__(self, bytes_arg, sub, start, end, source_ref):
        ChildrenHavingBytesArgSubStartEndMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            sub=sub,
            start=start,
            end=end,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
            and self.subnode_end.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.index(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                    self.subnode_end.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.index' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.subnode_end.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationIndex3Base(
    ExpressionIntShapeExactMixin, ChildrenHavingBytesArgSubStartMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "sub",
        "start",
    )

    def __init__(self, bytes_arg, sub, start, source_ref):
        ChildrenHavingBytesArgSubStartMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            sub=sub,
            start=start,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.index(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.index' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationIndex2Base(
    ExpressionIntShapeExactMixin, ChildrenHavingBytesArgSubMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "sub",
    )

    def __init__(self, bytes_arg, sub, source_ref):
        ChildrenHavingBytesArgSubMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            sub=sub,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.index(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.index' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationIsalnumBase(
    ExpressionBoolShapeExactMixin, ChildHavingStrArgMixin, ExpressionBase
):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.isalnum(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.isalnum' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationIsalnumBase(
    ExpressionBoolShapeExactMixin, ChildHavingBytesArgMixin, ExpressionBase
):
    named_children = ("bytes_arg",)

    def __init__(self, bytes_arg, source_ref):
        ChildHavingBytesArgMixin.__init__(
            self,
            bytes_arg=bytes_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_bytes_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.isalnum(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.isalnum' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationIsalphaBase(
    ExpressionBoolShapeExactMixin, ChildHavingStrArgMixin, ExpressionBase
):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.isalpha(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.isalpha' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationIsalphaBase(
    ExpressionBoolShapeExactMixin, ChildHavingBytesArgMixin, ExpressionBase
):
    named_children = ("bytes_arg",)

    def __init__(self, bytes_arg, source_ref):
        ChildHavingBytesArgMixin.__init__(
            self,
            bytes_arg=bytes_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_bytes_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.isalpha(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.isalpha' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationIsasciiBase(ChildHavingStrArgMixin, ExpressionBase):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.isascii(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.isascii' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationIsdecimalBase(ChildHavingStrArgMixin, ExpressionBase):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.isdecimal(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.isdecimal' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationIsdigitBase(
    ExpressionBoolShapeExactMixin, ChildHavingStrArgMixin, ExpressionBase
):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.isdigit(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.isdigit' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationIsdigitBase(
    ExpressionBoolShapeExactMixin, ChildHavingBytesArgMixin, ExpressionBase
):
    named_children = ("bytes_arg",)

    def __init__(self, bytes_arg, source_ref):
        ChildHavingBytesArgMixin.__init__(
            self,
            bytes_arg=bytes_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_bytes_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.isdigit(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.isdigit' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationIsidentifierBase(ChildHavingStrArgMixin, ExpressionBase):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.isidentifier(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.isidentifier' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationIslowerBase(
    ExpressionBoolShapeExactMixin, ChildHavingStrArgMixin, ExpressionBase
):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.islower(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.islower' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationIslowerBase(
    ExpressionBoolShapeExactMixin, ChildHavingBytesArgMixin, ExpressionBase
):
    named_children = ("bytes_arg",)

    def __init__(self, bytes_arg, source_ref):
        ChildHavingBytesArgMixin.__init__(
            self,
            bytes_arg=bytes_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_bytes_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.islower(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.islower' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationIsnumericBase(ChildHavingStrArgMixin, ExpressionBase):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.isnumeric(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.isnumeric' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationIsprintableBase(ChildHavingStrArgMixin, ExpressionBase):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.isprintable(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.isprintable' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationIsspaceBase(
    ExpressionBoolShapeExactMixin, ChildHavingStrArgMixin, ExpressionBase
):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.isspace(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.isspace' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationIsspaceBase(
    ExpressionBoolShapeExactMixin, ChildHavingBytesArgMixin, ExpressionBase
):
    named_children = ("bytes_arg",)

    def __init__(self, bytes_arg, source_ref):
        ChildHavingBytesArgMixin.__init__(
            self,
            bytes_arg=bytes_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_bytes_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.isspace(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.isspace' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationIstitleBase(
    ExpressionBoolShapeExactMixin, ChildHavingStrArgMixin, ExpressionBase
):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.istitle(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.istitle' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationIstitleBase(
    ExpressionBoolShapeExactMixin, ChildHavingBytesArgMixin, ExpressionBase
):
    named_children = ("bytes_arg",)

    def __init__(self, bytes_arg, source_ref):
        ChildHavingBytesArgMixin.__init__(
            self,
            bytes_arg=bytes_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_bytes_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.istitle(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.istitle' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationIsupperBase(
    ExpressionBoolShapeExactMixin, ChildHavingStrArgMixin, ExpressionBase
):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.isupper(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.isupper' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationIsupperBase(
    ExpressionBoolShapeExactMixin, ChildHavingBytesArgMixin, ExpressionBase
):
    named_children = ("bytes_arg",)

    def __init__(self, bytes_arg, source_ref):
        ChildHavingBytesArgMixin.__init__(
            self,
            bytes_arg=bytes_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_bytes_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.isupper(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.isupper' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionDictOperationItemsBase(
    ExpressionListShapeExactMixin, ChildHavingDictArgMixin, ExpressionBase
):
    named_children = ("dict_arg",)

    def __init__(self, dict_arg, source_ref):
        ChildHavingDictArgMixin.__init__(
            self,
            dict_arg=dict_arg,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionDictOperationIteritemsBase(ChildHavingDictArgMixin, ExpressionBase):
    named_children = ("dict_arg",)

    def __init__(self, dict_arg, source_ref):
        ChildHavingDictArgMixin.__init__(
            self,
            dict_arg=dict_arg,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionDictOperationIterkeysBase(ChildHavingDictArgMixin, ExpressionBase):
    named_children = ("dict_arg",)

    def __init__(self, dict_arg, source_ref):
        ChildHavingDictArgMixin.__init__(
            self,
            dict_arg=dict_arg,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionDictOperationItervaluesBase(ChildHavingDictArgMixin, ExpressionBase):
    named_children = ("dict_arg",)

    def __init__(self, dict_arg, source_ref):
        ChildHavingDictArgMixin.__init__(
            self,
            dict_arg=dict_arg,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionStrOperationJoinBase(
    ExpressionStrShapeExactMixin, ChildrenHavingStrArgIterableMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "iterable",
    )

    def __init__(self, str_arg, iterable, source_ref):
        ChildrenHavingStrArgIterableMixin.__init__(
            self,
            str_arg=str_arg,
            iterable=iterable,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_iterable.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.join(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_iterable.getCompileTimeConstant(),
                ),
                description="Built-in 'str.join' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_iterable.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationJoinBase(
    ExpressionBytesShapeExactMixin, ChildrenHavingBytesArgIterableMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "iterable",
    )

    def __init__(self, bytes_arg, iterable, source_ref):
        ChildrenHavingBytesArgIterableMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            iterable=iterable,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_iterable.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.join(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_iterable.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.join' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_iterable.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionDictOperationKeysBase(
    ExpressionListShapeExactMixin, ChildHavingDictArgMixin, ExpressionBase
):
    named_children = ("dict_arg",)

    def __init__(self, dict_arg, source_ref):
        ChildHavingDictArgMixin.__init__(
            self,
            dict_arg=dict_arg,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionStrOperationLjust3Base(
    ExpressionStrShapeExactMixin, ChildrenHavingStrArgWidthFillcharMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "width",
        "fillchar",
    )

    def __init__(self, str_arg, width, fillchar, source_ref):
        ChildrenHavingStrArgWidthFillcharMixin.__init__(
            self,
            str_arg=str_arg,
            width=width,
            fillchar=fillchar,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_width.isCompileTimeConstant()
            and self.subnode_fillchar.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.ljust(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_width.getCompileTimeConstant(),
                    self.subnode_fillchar.getCompileTimeConstant(),
                ),
                description="Built-in 'str.ljust' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_width.mayRaiseException(exception_type)
            or self.subnode_fillchar.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationLjust2Base(
    ExpressionStrShapeExactMixin, ChildrenHavingStrArgWidthMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "width",
    )

    def __init__(self, str_arg, width, source_ref):
        ChildrenHavingStrArgWidthMixin.__init__(
            self,
            str_arg=str_arg,
            width=width,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_width.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.ljust(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_width.getCompileTimeConstant(),
                ),
                description="Built-in 'str.ljust' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_width.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationLjust3Base(
    ExpressionBytesShapeExactMixin,
    ChildrenHavingBytesArgWidthFillcharMixin,
    ExpressionBase,
):
    named_children = (
        "bytes_arg",
        "width",
        "fillchar",
    )

    def __init__(self, bytes_arg, width, fillchar, source_ref):
        ChildrenHavingBytesArgWidthFillcharMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            width=width,
            fillchar=fillchar,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_width.isCompileTimeConstant()
            and self.subnode_fillchar.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.ljust(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_width.getCompileTimeConstant(),
                    self.subnode_fillchar.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.ljust' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_width.mayRaiseException(exception_type)
            or self.subnode_fillchar.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationLjust2Base(
    ExpressionBytesShapeExactMixin, ChildrenHavingBytesArgWidthMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "width",
    )

    def __init__(self, bytes_arg, width, source_ref):
        ChildrenHavingBytesArgWidthMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            width=width,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_width.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.ljust(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_width.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.ljust' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_width.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationLowerBase(
    ExpressionStrShapeExactMixin, ChildHavingStrArgMixin, ExpressionBase
):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.lower(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.lower' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationLowerBase(
    ExpressionBytesShapeExactMixin, ChildHavingBytesArgMixin, ExpressionBase
):
    named_children = ("bytes_arg",)

    def __init__(self, bytes_arg, source_ref):
        ChildHavingBytesArgMixin.__init__(
            self,
            bytes_arg=bytes_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_bytes_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.lower(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.lower' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationLstrip2Base(
    ExpressionStrShapeExactMixin, ChildrenHavingStrArgCharsMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "chars",
    )

    def __init__(self, str_arg, chars, source_ref):
        ChildrenHavingStrArgCharsMixin.__init__(
            self,
            str_arg=str_arg,
            chars=chars,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_chars.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.lstrip(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_chars.getCompileTimeConstant(),
                ),
                description="Built-in 'str.lstrip' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_chars.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationLstrip1Base(
    ExpressionStrShapeExactMixin, ChildHavingStrArgMixin, ExpressionBase
):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.lstrip(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.lstrip' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationLstrip2Base(
    ExpressionBytesShapeExactMixin, ChildrenHavingBytesArgCharsMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "chars",
    )

    def __init__(self, bytes_arg, chars, source_ref):
        ChildrenHavingBytesArgCharsMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            chars=chars,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_chars.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.lstrip(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_chars.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.lstrip' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_chars.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationLstrip1Base(
    ExpressionBytesShapeExactMixin, ChildHavingBytesArgMixin, ExpressionBase
):
    named_children = ("bytes_arg",)

    def __init__(self, bytes_arg, source_ref):
        ChildHavingBytesArgMixin.__init__(
            self,
            bytes_arg=bytes_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_bytes_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.lstrip(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.lstrip' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationMaketransBase(ChildHavingStrArgMixin, ExpressionBase):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.maketrans(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.maketrans' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationPartitionBase(
    ExpressionTupleShapeExactMixin, ChildrenHavingStrArgSepMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "sep",
    )

    def __init__(self, str_arg, sep, source_ref):
        ChildrenHavingStrArgSepMixin.__init__(
            self,
            str_arg=str_arg,
            sep=sep,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_sep.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.partition(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_sep.getCompileTimeConstant(),
                ),
                description="Built-in 'str.partition' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_sep.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationPartitionBase(
    ExpressionTupleShapeExactMixin, ChildrenHavingBytesArgSepMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "sep",
    )

    def __init__(self, bytes_arg, sep, source_ref):
        ChildrenHavingBytesArgSepMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            sep=sep,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_sep.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.partition(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_sep.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.partition' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_sep.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionDictOperationPop3Base(
    ChildrenHavingDictArgKeyDefaultMixin, ExpressionBase
):
    named_children = (
        "dict_arg",
        "key",
        "default",
    )

    def __init__(self, dict_arg, key, default, source_ref):
        ChildrenHavingDictArgKeyDefaultMixin.__init__(
            self,
            dict_arg=dict_arg,
            key=key,
            default=default,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionDictOperationPop2Base(ChildrenHavingDictArgKeyMixin, ExpressionBase):
    named_children = (
        "dict_arg",
        "key",
    )

    def __init__(self, dict_arg, key, source_ref):
        ChildrenHavingDictArgKeyMixin.__init__(
            self,
            dict_arg=dict_arg,
            key=key,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionDictOperationPopitemBase(
    ExpressionTupleShapeExactMixin, ChildHavingDictArgMixin, ExpressionBase
):
    named_children = ("dict_arg",)

    def __init__(self, dict_arg, source_ref):
        ChildHavingDictArgMixin.__init__(
            self,
            dict_arg=dict_arg,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionStrOperationReplace4Base(
    ExpressionStrShapeExactMixin, ChildrenHavingStrArgOldNewCountMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "old",
        "new",
        "count",
    )

    def __init__(self, str_arg, old, new, count, source_ref):
        ChildrenHavingStrArgOldNewCountMixin.__init__(
            self,
            str_arg=str_arg,
            old=old,
            new=new,
            count=count,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_old.isCompileTimeConstant()
            and self.subnode_new.isCompileTimeConstant()
            and self.subnode_count.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.replace(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_old.getCompileTimeConstant(),
                    self.subnode_new.getCompileTimeConstant(),
                    self.subnode_count.getCompileTimeConstant(),
                ),
                description="Built-in 'str.replace' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_old.mayRaiseException(exception_type)
            or self.subnode_new.mayRaiseException(exception_type)
            or self.subnode_count.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationReplace3Base(
    ExpressionStrShapeExactMixin, ChildrenHavingStrArgOldNewMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "old",
        "new",
    )

    def __init__(self, str_arg, old, new, source_ref):
        ChildrenHavingStrArgOldNewMixin.__init__(
            self,
            str_arg=str_arg,
            old=old,
            new=new,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_old.isCompileTimeConstant()
            and self.subnode_new.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.replace(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_old.getCompileTimeConstant(),
                    self.subnode_new.getCompileTimeConstant(),
                ),
                description="Built-in 'str.replace' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_old.mayRaiseException(exception_type)
            or self.subnode_new.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationReplace4Base(
    ExpressionBytesShapeExactMixin,
    ChildrenHavingBytesArgOldNewCountMixin,
    ExpressionBase,
):
    named_children = (
        "bytes_arg",
        "old",
        "new",
        "count",
    )

    def __init__(self, bytes_arg, old, new, count, source_ref):
        ChildrenHavingBytesArgOldNewCountMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            old=old,
            new=new,
            count=count,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_old.isCompileTimeConstant()
            and self.subnode_new.isCompileTimeConstant()
            and self.subnode_count.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.replace(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_old.getCompileTimeConstant(),
                    self.subnode_new.getCompileTimeConstant(),
                    self.subnode_count.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.replace' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_old.mayRaiseException(exception_type)
            or self.subnode_new.mayRaiseException(exception_type)
            or self.subnode_count.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationReplace3Base(
    ExpressionBytesShapeExactMixin, ChildrenHavingBytesArgOldNewMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "old",
        "new",
    )

    def __init__(self, bytes_arg, old, new, source_ref):
        ChildrenHavingBytesArgOldNewMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            old=old,
            new=new,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_old.isCompileTimeConstant()
            and self.subnode_new.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.replace(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_old.getCompileTimeConstant(),
                    self.subnode_new.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.replace' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_old.mayRaiseException(exception_type)
            or self.subnode_new.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationRfind4Base(
    ExpressionIntShapeExactMixin, ChildrenHavingStrArgSubStartEndMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "sub",
        "start",
        "end",
    )

    def __init__(self, str_arg, sub, start, end, source_ref):
        ChildrenHavingStrArgSubStartEndMixin.__init__(
            self,
            str_arg=str_arg,
            sub=sub,
            start=start,
            end=end,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
            and self.subnode_end.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.rfind(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                    self.subnode_end.getCompileTimeConstant(),
                ),
                description="Built-in 'str.rfind' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.subnode_end.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationRfind3Base(
    ExpressionIntShapeExactMixin, ChildrenHavingStrArgSubStartMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "sub",
        "start",
    )

    def __init__(self, str_arg, sub, start, source_ref):
        ChildrenHavingStrArgSubStartMixin.__init__(
            self,
            str_arg=str_arg,
            sub=sub,
            start=start,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.rfind(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                ),
                description="Built-in 'str.rfind' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationRfind2Base(
    ExpressionIntShapeExactMixin, ChildrenHavingStrArgSubMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "sub",
    )

    def __init__(self, str_arg, sub, source_ref):
        ChildrenHavingStrArgSubMixin.__init__(
            self,
            str_arg=str_arg,
            sub=sub,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.rfind(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                ),
                description="Built-in 'str.rfind' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationRfind4Base(
    ExpressionIntShapeExactMixin, ChildrenHavingBytesArgSubStartEndMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "sub",
        "start",
        "end",
    )

    def __init__(self, bytes_arg, sub, start, end, source_ref):
        ChildrenHavingBytesArgSubStartEndMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            sub=sub,
            start=start,
            end=end,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
            and self.subnode_end.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.rfind(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                    self.subnode_end.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.rfind' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.subnode_end.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationRfind3Base(
    ExpressionIntShapeExactMixin, ChildrenHavingBytesArgSubStartMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "sub",
        "start",
    )

    def __init__(self, bytes_arg, sub, start, source_ref):
        ChildrenHavingBytesArgSubStartMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            sub=sub,
            start=start,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.rfind(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.rfind' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationRfind2Base(
    ExpressionIntShapeExactMixin, ChildrenHavingBytesArgSubMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "sub",
    )

    def __init__(self, bytes_arg, sub, source_ref):
        ChildrenHavingBytesArgSubMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            sub=sub,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.rfind(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.rfind' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationRindex4Base(
    ExpressionIntShapeExactMixin, ChildrenHavingStrArgSubStartEndMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "sub",
        "start",
        "end",
    )

    def __init__(self, str_arg, sub, start, end, source_ref):
        ChildrenHavingStrArgSubStartEndMixin.__init__(
            self,
            str_arg=str_arg,
            sub=sub,
            start=start,
            end=end,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
            and self.subnode_end.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.rindex(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                    self.subnode_end.getCompileTimeConstant(),
                ),
                description="Built-in 'str.rindex' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.subnode_end.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationRindex3Base(
    ExpressionIntShapeExactMixin, ChildrenHavingStrArgSubStartMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "sub",
        "start",
    )

    def __init__(self, str_arg, sub, start, source_ref):
        ChildrenHavingStrArgSubStartMixin.__init__(
            self,
            str_arg=str_arg,
            sub=sub,
            start=start,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.rindex(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                ),
                description="Built-in 'str.rindex' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationRindex2Base(
    ExpressionIntShapeExactMixin, ChildrenHavingStrArgSubMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "sub",
    )

    def __init__(self, str_arg, sub, source_ref):
        ChildrenHavingStrArgSubMixin.__init__(
            self,
            str_arg=str_arg,
            sub=sub,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.rindex(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                ),
                description="Built-in 'str.rindex' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationRindex4Base(
    ExpressionIntShapeExactMixin, ChildrenHavingBytesArgSubStartEndMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "sub",
        "start",
        "end",
    )

    def __init__(self, bytes_arg, sub, start, end, source_ref):
        ChildrenHavingBytesArgSubStartEndMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            sub=sub,
            start=start,
            end=end,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
            and self.subnode_end.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.rindex(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                    self.subnode_end.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.rindex' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.subnode_end.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationRindex3Base(
    ExpressionIntShapeExactMixin, ChildrenHavingBytesArgSubStartMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "sub",
        "start",
    )

    def __init__(self, bytes_arg, sub, start, source_ref):
        ChildrenHavingBytesArgSubStartMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            sub=sub,
            start=start,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.rindex(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.rindex' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationRindex2Base(
    ExpressionIntShapeExactMixin, ChildrenHavingBytesArgSubMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "sub",
    )

    def __init__(self, bytes_arg, sub, source_ref):
        ChildrenHavingBytesArgSubMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            sub=sub,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_sub.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.rindex(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_sub.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.rindex' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_sub.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationRjust3Base(
    ExpressionStrShapeExactMixin, ChildrenHavingStrArgWidthFillcharMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "width",
        "fillchar",
    )

    def __init__(self, str_arg, width, fillchar, source_ref):
        ChildrenHavingStrArgWidthFillcharMixin.__init__(
            self,
            str_arg=str_arg,
            width=width,
            fillchar=fillchar,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_width.isCompileTimeConstant()
            and self.subnode_fillchar.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.rjust(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_width.getCompileTimeConstant(),
                    self.subnode_fillchar.getCompileTimeConstant(),
                ),
                description="Built-in 'str.rjust' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_width.mayRaiseException(exception_type)
            or self.subnode_fillchar.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationRjust2Base(
    ExpressionStrShapeExactMixin, ChildrenHavingStrArgWidthMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "width",
    )

    def __init__(self, str_arg, width, source_ref):
        ChildrenHavingStrArgWidthMixin.__init__(
            self,
            str_arg=str_arg,
            width=width,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_width.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.rjust(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_width.getCompileTimeConstant(),
                ),
                description="Built-in 'str.rjust' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_width.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationRjust3Base(
    ExpressionBytesShapeExactMixin,
    ChildrenHavingBytesArgWidthFillcharMixin,
    ExpressionBase,
):
    named_children = (
        "bytes_arg",
        "width",
        "fillchar",
    )

    def __init__(self, bytes_arg, width, fillchar, source_ref):
        ChildrenHavingBytesArgWidthFillcharMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            width=width,
            fillchar=fillchar,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_width.isCompileTimeConstant()
            and self.subnode_fillchar.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.rjust(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_width.getCompileTimeConstant(),
                    self.subnode_fillchar.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.rjust' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_width.mayRaiseException(exception_type)
            or self.subnode_fillchar.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationRjust2Base(
    ExpressionBytesShapeExactMixin, ChildrenHavingBytesArgWidthMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "width",
    )

    def __init__(self, bytes_arg, width, source_ref):
        ChildrenHavingBytesArgWidthMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            width=width,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_width.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.rjust(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_width.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.rjust' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_width.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationRpartitionBase(
    ExpressionTupleShapeExactMixin, ChildrenHavingStrArgSepMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "sep",
    )

    def __init__(self, str_arg, sep, source_ref):
        ChildrenHavingStrArgSepMixin.__init__(
            self,
            str_arg=str_arg,
            sep=sep,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_sep.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.rpartition(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_sep.getCompileTimeConstant(),
                ),
                description="Built-in 'str.rpartition' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_sep.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationRpartitionBase(
    ExpressionTupleShapeExactMixin, ChildrenHavingBytesArgSepMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "sep",
    )

    def __init__(self, bytes_arg, sep, source_ref):
        ChildrenHavingBytesArgSepMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            sep=sep,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_sep.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.rpartition(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_sep.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.rpartition' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_sep.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationRsplit3Base(
    ExpressionListShapeExactMixin, ChildrenHavingStrArgSepMaxsplitMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "sep",
        "maxsplit",
    )

    def __init__(self, str_arg, sep, maxsplit, source_ref):
        ChildrenHavingStrArgSepMaxsplitMixin.__init__(
            self,
            str_arg=str_arg,
            sep=sep,
            maxsplit=maxsplit,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_sep.isCompileTimeConstant()
            and self.subnode_maxsplit.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.rsplit(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_sep.getCompileTimeConstant(),
                    self.subnode_maxsplit.getCompileTimeConstant(),
                ),
                description="Built-in 'str.rsplit' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_sep.mayRaiseException(exception_type)
            or self.subnode_maxsplit.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationRsplit2Base(
    ExpressionListShapeExactMixin, ChildrenHavingStrArgSepMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "sep",
    )

    def __init__(self, str_arg, sep, source_ref):
        ChildrenHavingStrArgSepMixin.__init__(
            self,
            str_arg=str_arg,
            sep=sep,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_sep.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.rsplit(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_sep.getCompileTimeConstant(),
                ),
                description="Built-in 'str.rsplit' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_sep.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationRsplit1Base(
    ExpressionListShapeExactMixin, ChildHavingStrArgMixin, ExpressionBase
):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.rsplit(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.rsplit' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationRsplit3Base(
    ExpressionListShapeExactMixin,
    ChildrenHavingBytesArgSepMaxsplitMixin,
    ExpressionBase,
):
    named_children = (
        "bytes_arg",
        "sep",
        "maxsplit",
    )

    def __init__(self, bytes_arg, sep, maxsplit, source_ref):
        ChildrenHavingBytesArgSepMaxsplitMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            sep=sep,
            maxsplit=maxsplit,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_sep.isCompileTimeConstant()
            and self.subnode_maxsplit.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.rsplit(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_sep.getCompileTimeConstant(),
                    self.subnode_maxsplit.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.rsplit' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_sep.mayRaiseException(exception_type)
            or self.subnode_maxsplit.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationRsplit2Base(
    ExpressionListShapeExactMixin, ChildrenHavingBytesArgSepMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "sep",
    )

    def __init__(self, bytes_arg, sep, source_ref):
        ChildrenHavingBytesArgSepMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            sep=sep,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_sep.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.rsplit(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_sep.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.rsplit' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_sep.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationRsplit1Base(
    ExpressionListShapeExactMixin, ChildHavingBytesArgMixin, ExpressionBase
):
    named_children = ("bytes_arg",)

    def __init__(self, bytes_arg, source_ref):
        ChildHavingBytesArgMixin.__init__(
            self,
            bytes_arg=bytes_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_bytes_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.rsplit(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.rsplit' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationRstrip2Base(
    ExpressionStrShapeExactMixin, ChildrenHavingStrArgCharsMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "chars",
    )

    def __init__(self, str_arg, chars, source_ref):
        ChildrenHavingStrArgCharsMixin.__init__(
            self,
            str_arg=str_arg,
            chars=chars,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_chars.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.rstrip(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_chars.getCompileTimeConstant(),
                ),
                description="Built-in 'str.rstrip' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_chars.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationRstrip1Base(
    ExpressionStrShapeExactMixin, ChildHavingStrArgMixin, ExpressionBase
):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.rstrip(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.rstrip' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationRstrip2Base(
    ExpressionBytesShapeExactMixin, ChildrenHavingBytesArgCharsMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "chars",
    )

    def __init__(self, bytes_arg, chars, source_ref):
        ChildrenHavingBytesArgCharsMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            chars=chars,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_chars.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.rstrip(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_chars.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.rstrip' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_chars.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationRstrip1Base(
    ExpressionBytesShapeExactMixin, ChildHavingBytesArgMixin, ExpressionBase
):
    named_children = ("bytes_arg",)

    def __init__(self, bytes_arg, source_ref):
        ChildHavingBytesArgMixin.__init__(
            self,
            bytes_arg=bytes_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_bytes_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.rstrip(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.rstrip' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionDictOperationSetdefault3Base(
    ChildrenHavingDictArgKeyDefaultMixin, ExpressionBase
):
    named_children = (
        "dict_arg",
        "key",
        "default",
    )

    def __init__(self, dict_arg, key, default, source_ref):
        ChildrenHavingDictArgKeyDefaultMixin.__init__(
            self,
            dict_arg=dict_arg,
            key=key,
            default=default,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionDictOperationSetdefault2Base(
    ChildrenHavingDictArgKeyMixin, ExpressionBase
):
    named_children = (
        "dict_arg",
        "key",
    )

    def __init__(self, dict_arg, key, source_ref):
        ChildrenHavingDictArgKeyMixin.__init__(
            self,
            dict_arg=dict_arg,
            key=key,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionStrOperationSplit3Base(
    ExpressionListShapeExactMixin, ChildrenHavingStrArgSepMaxsplitMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "sep",
        "maxsplit",
    )

    def __init__(self, str_arg, sep, maxsplit, source_ref):
        ChildrenHavingStrArgSepMaxsplitMixin.__init__(
            self,
            str_arg=str_arg,
            sep=sep,
            maxsplit=maxsplit,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_sep.isCompileTimeConstant()
            and self.subnode_maxsplit.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.split(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_sep.getCompileTimeConstant(),
                    self.subnode_maxsplit.getCompileTimeConstant(),
                ),
                description="Built-in 'str.split' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_sep.mayRaiseException(exception_type)
            or self.subnode_maxsplit.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationSplit2Base(
    ExpressionListShapeExactMixin, ChildrenHavingStrArgSepMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "sep",
    )

    def __init__(self, str_arg, sep, source_ref):
        ChildrenHavingStrArgSepMixin.__init__(
            self,
            str_arg=str_arg,
            sep=sep,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_sep.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.split(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_sep.getCompileTimeConstant(),
                ),
                description="Built-in 'str.split' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_sep.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationSplit1Base(
    ExpressionListShapeExactMixin, ChildHavingStrArgMixin, ExpressionBase
):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.split(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.split' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationSplit3Base(
    ExpressionListShapeExactMixin,
    ChildrenHavingBytesArgSepMaxsplitMixin,
    ExpressionBase,
):
    named_children = (
        "bytes_arg",
        "sep",
        "maxsplit",
    )

    def __init__(self, bytes_arg, sep, maxsplit, source_ref):
        ChildrenHavingBytesArgSepMaxsplitMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            sep=sep,
            maxsplit=maxsplit,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_sep.isCompileTimeConstant()
            and self.subnode_maxsplit.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.split(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_sep.getCompileTimeConstant(),
                    self.subnode_maxsplit.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.split' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_sep.mayRaiseException(exception_type)
            or self.subnode_maxsplit.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationSplit2Base(
    ExpressionListShapeExactMixin, ChildrenHavingBytesArgSepMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "sep",
    )

    def __init__(self, bytes_arg, sep, source_ref):
        ChildrenHavingBytesArgSepMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            sep=sep,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_sep.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.split(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_sep.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.split' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_sep.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationSplit1Base(
    ExpressionListShapeExactMixin, ChildHavingBytesArgMixin, ExpressionBase
):
    named_children = ("bytes_arg",)

    def __init__(self, bytes_arg, source_ref):
        ChildHavingBytesArgMixin.__init__(
            self,
            bytes_arg=bytes_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_bytes_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.split(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.split' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationSplitlines2Base(
    ExpressionListShapeExactMixin, ChildrenHavingStrArgKeependsMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "keepends",
    )

    def __init__(self, str_arg, keepends, source_ref):
        ChildrenHavingStrArgKeependsMixin.__init__(
            self,
            str_arg=str_arg,
            keepends=keepends,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_keepends.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.splitlines(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_keepends.getCompileTimeConstant(),
                ),
                description="Built-in 'str.splitlines' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_keepends.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationSplitlines1Base(
    ExpressionListShapeExactMixin, ChildHavingStrArgMixin, ExpressionBase
):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.splitlines(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.splitlines' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationSplitlines2Base(
    ExpressionListShapeExactMixin, ChildrenHavingBytesArgKeependsMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "keepends",
    )

    def __init__(self, bytes_arg, keepends, source_ref):
        ChildrenHavingBytesArgKeependsMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            keepends=keepends,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_keepends.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.splitlines(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_keepends.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.splitlines' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_keepends.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationSplitlines1Base(
    ExpressionListShapeExactMixin, ChildHavingBytesArgMixin, ExpressionBase
):
    named_children = ("bytes_arg",)

    def __init__(self, bytes_arg, source_ref):
        ChildHavingBytesArgMixin.__init__(
            self,
            bytes_arg=bytes_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_bytes_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.splitlines(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.splitlines' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationStartswith4Base(
    ExpressionBoolShapeExactMixin,
    ChildrenHavingStrArgPrefixStartEndMixin,
    ExpressionBase,
):
    named_children = (
        "str_arg",
        "prefix",
        "start",
        "end",
    )

    def __init__(self, str_arg, prefix, start, end, source_ref):
        ChildrenHavingStrArgPrefixStartEndMixin.__init__(
            self,
            str_arg=str_arg,
            prefix=prefix,
            start=start,
            end=end,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_prefix.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
            and self.subnode_end.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.startswith(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_prefix.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                    self.subnode_end.getCompileTimeConstant(),
                ),
                description="Built-in 'str.startswith' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_prefix.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.subnode_end.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationStartswith3Base(
    ExpressionBoolShapeExactMixin, ChildrenHavingStrArgPrefixStartMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "prefix",
        "start",
    )

    def __init__(self, str_arg, prefix, start, source_ref):
        ChildrenHavingStrArgPrefixStartMixin.__init__(
            self,
            str_arg=str_arg,
            prefix=prefix,
            start=start,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_prefix.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.startswith(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_prefix.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                ),
                description="Built-in 'str.startswith' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_prefix.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationStartswith2Base(
    ExpressionBoolShapeExactMixin, ChildrenHavingStrArgPrefixMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "prefix",
    )

    def __init__(self, str_arg, prefix, source_ref):
        ChildrenHavingStrArgPrefixMixin.__init__(
            self,
            str_arg=str_arg,
            prefix=prefix,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_prefix.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.startswith(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_prefix.getCompileTimeConstant(),
                ),
                description="Built-in 'str.startswith' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_prefix.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationStartswith4Base(
    ExpressionBoolShapeExactMixin,
    ChildrenHavingBytesArgPrefixStartEndMixin,
    ExpressionBase,
):
    named_children = (
        "bytes_arg",
        "prefix",
        "start",
        "end",
    )

    def __init__(self, bytes_arg, prefix, start, end, source_ref):
        ChildrenHavingBytesArgPrefixStartEndMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            prefix=prefix,
            start=start,
            end=end,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_prefix.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
            and self.subnode_end.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.startswith(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_prefix.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                    self.subnode_end.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.startswith' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_prefix.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.subnode_end.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationStartswith3Base(
    ExpressionBoolShapeExactMixin,
    ChildrenHavingBytesArgPrefixStartMixin,
    ExpressionBase,
):
    named_children = (
        "bytes_arg",
        "prefix",
        "start",
    )

    def __init__(self, bytes_arg, prefix, start, source_ref):
        ChildrenHavingBytesArgPrefixStartMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            prefix=prefix,
            start=start,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_prefix.isCompileTimeConstant()
            and self.subnode_start.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.startswith(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_prefix.getCompileTimeConstant(),
                    self.subnode_start.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.startswith' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_prefix.mayRaiseException(exception_type)
            or self.subnode_start.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationStartswith2Base(
    ExpressionBoolShapeExactMixin, ChildrenHavingBytesArgPrefixMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "prefix",
    )

    def __init__(self, bytes_arg, prefix, source_ref):
        ChildrenHavingBytesArgPrefixMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            prefix=prefix,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_prefix.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.startswith(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_prefix.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.startswith' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_prefix.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationStrip2Base(
    ExpressionStrShapeExactMixin, ChildrenHavingStrArgCharsMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "chars",
    )

    def __init__(self, str_arg, chars, source_ref):
        ChildrenHavingStrArgCharsMixin.__init__(
            self,
            str_arg=str_arg,
            chars=chars,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_chars.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.strip(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_chars.getCompileTimeConstant(),
                ),
                description="Built-in 'str.strip' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_chars.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationStrip1Base(
    ExpressionStrShapeExactMixin, ChildHavingStrArgMixin, ExpressionBase
):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.strip(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.strip' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationStrip2Base(
    ExpressionBytesShapeExactMixin, ChildrenHavingBytesArgCharsMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "chars",
    )

    def __init__(self, bytes_arg, chars, source_ref):
        ChildrenHavingBytesArgCharsMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            chars=chars,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_chars.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.strip(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_chars.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.strip' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_chars.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationStrip1Base(
    ExpressionBytesShapeExactMixin, ChildHavingBytesArgMixin, ExpressionBase
):
    named_children = ("bytes_arg",)

    def __init__(self, bytes_arg, source_ref):
        ChildHavingBytesArgMixin.__init__(
            self,
            bytes_arg=bytes_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_bytes_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.strip(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.strip' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationSwapcaseBase(
    ExpressionStrShapeExactMixin, ChildHavingStrArgMixin, ExpressionBase
):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.swapcase(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.swapcase' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationSwapcaseBase(
    ExpressionBytesShapeExactMixin, ChildHavingBytesArgMixin, ExpressionBase
):
    named_children = ("bytes_arg",)

    def __init__(self, bytes_arg, source_ref):
        ChildHavingBytesArgMixin.__init__(
            self,
            bytes_arg=bytes_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_bytes_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.swapcase(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.swapcase' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationTitleBase(
    ExpressionStrShapeExactMixin, ChildHavingStrArgMixin, ExpressionBase
):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.title(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.title' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationTitleBase(
    ExpressionBytesShapeExactMixin, ChildHavingBytesArgMixin, ExpressionBase
):
    named_children = ("bytes_arg",)

    def __init__(self, bytes_arg, source_ref):
        ChildHavingBytesArgMixin.__init__(
            self,
            bytes_arg=bytes_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_bytes_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.title(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.title' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionStrOperationTranslateBase(
    ExpressionStrShapeExactMixin, ChildrenHavingStrArgTableMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "table",
    )

    def __init__(self, str_arg, table, source_ref):
        ChildrenHavingStrArgTableMixin.__init__(
            self,
            str_arg=str_arg,
            table=table,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_table.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.translate(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_table.getCompileTimeConstant(),
                ),
                description="Built-in 'str.translate' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_table.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationTranslate3Base(
    ExpressionBytesShapeExactMixin,
    ChildrenHavingBytesArgTableDeleteMixin,
    ExpressionBase,
):
    named_children = (
        "bytes_arg",
        "table",
        "delete",
    )

    def __init__(self, bytes_arg, table, delete, source_ref):
        ChildrenHavingBytesArgTableDeleteMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            table=table,
            delete=delete,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_table.isCompileTimeConstant()
            and self.subnode_delete.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.translate(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_table.getCompileTimeConstant(),
                    self.subnode_delete.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.translate' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_table.mayRaiseException(exception_type)
            or self.subnode_delete.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationTranslate2Base(
    ExpressionBytesShapeExactMixin, ChildrenHavingBytesArgTableMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "table",
    )

    def __init__(self, bytes_arg, table, source_ref):
        ChildrenHavingBytesArgTableMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            table=table,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_table.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.translate(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_table.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.translate' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_table.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionDictOperationUpdate3Base(
    ExpressionNoneShapeExactMixin,
    ChildrenHavingDictArgIterablePairsTupleMixin,
    ExpressionBase,
):
    named_children = (
        "dict_arg",
        "iterable",
        "pairs|tuple",
    )

    def __init__(self, dict_arg, iterable, pairs, source_ref):
        ChildrenHavingDictArgIterablePairsTupleMixin.__init__(
            self,
            dict_arg=dict_arg,
            iterable=iterable,
            pairs=pairs,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionDictOperationUpdate2Base(
    ExpressionNoneShapeExactMixin, ChildrenHavingDictArgIterableMixin, ExpressionBase
):
    named_children = (
        "dict_arg",
        "iterable",
    )

    def __init__(self, dict_arg, iterable, source_ref):
        ChildrenHavingDictArgIterableMixin.__init__(
            self,
            dict_arg=dict_arg,
            iterable=iterable,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionStrOperationUpperBase(
    ExpressionStrShapeExactMixin, ChildHavingStrArgMixin, ExpressionBase
):
    named_children = ("str_arg",)

    def __init__(self, str_arg, source_ref):
        ChildHavingStrArgMixin.__init__(
            self,
            str_arg=str_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_str_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.upper(
                    self.subnode_str_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'str.upper' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationUpperBase(
    ExpressionBytesShapeExactMixin, ChildHavingBytesArgMixin, ExpressionBase
):
    named_children = ("bytes_arg",)

    def __init__(self, bytes_arg, source_ref):
        ChildHavingBytesArgMixin.__init__(
            self,
            bytes_arg=bytes_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if self.subnode_bytes_arg.isCompileTimeConstant():
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.upper(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.upper' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionDictOperationValuesBase(
    ExpressionListShapeExactMixin, ChildHavingDictArgMixin, ExpressionBase
):
    named_children = ("dict_arg",)

    def __init__(self, dict_arg, source_ref):
        ChildHavingDictArgMixin.__init__(
            self,
            dict_arg=dict_arg,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionDictOperationViewitemsBase(ChildHavingDictArgMixin, ExpressionBase):
    named_children = ("dict_arg",)

    def __init__(self, dict_arg, source_ref):
        ChildHavingDictArgMixin.__init__(
            self,
            dict_arg=dict_arg,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionDictOperationViewkeysBase(ChildHavingDictArgMixin, ExpressionBase):
    named_children = ("dict_arg",)

    def __init__(self, dict_arg, source_ref):
        ChildHavingDictArgMixin.__init__(
            self,
            dict_arg=dict_arg,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionDictOperationViewvaluesBase(ChildHavingDictArgMixin, ExpressionBase):
    named_children = ("dict_arg",)

    def __init__(self, dict_arg, source_ref):
        ChildHavingDictArgMixin.__init__(
            self,
            dict_arg=dict_arg,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionStrOperationZfillBase(
    ExpressionStrShapeExactMixin, ChildrenHavingStrArgWidthMixin, ExpressionBase
):
    named_children = (
        "str_arg",
        "width",
    )

    def __init__(self, str_arg, width, source_ref):
        ChildrenHavingStrArgWidthMixin.__init__(
            self,
            str_arg=str_arg,
            width=width,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_str_arg.isCompileTimeConstant()
            and self.subnode_width.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: str.zfill(
                    self.subnode_str_arg.getCompileTimeConstant(),
                    self.subnode_width.getCompileTimeConstant(),
                ),
                description="Built-in 'str.zfill' with constant values.",
                user_provided=self.subnode_str_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_str_arg.mayRaiseException(exception_type)
            or self.subnode_width.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


class ExpressionBytesOperationZfillBase(
    ExpressionBytesShapeExactMixin, ChildrenHavingBytesArgWidthMixin, ExpressionBase
):
    named_children = (
        "bytes_arg",
        "width",
    )

    def __init__(self, bytes_arg, width, source_ref):
        ChildrenHavingBytesArgWidthMixin.__init__(
            self,
            bytes_arg=bytes_arg,
            width=width,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        if (
            self.subnode_bytes_arg.isCompileTimeConstant()
            and self.subnode_width.isCompileTimeConstant()
        ):
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: bytes.zfill(
                    self.subnode_bytes_arg.getCompileTimeConstant(),
                    self.subnode_width.getCompileTimeConstant(),
                ),
                description="Built-in 'bytes.zfill' with constant values.",
                user_provided=self.subnode_bytes_arg.user_provided,
            )

        if self.mayRaiseExceptionOperation():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_bytes_arg.mayRaiseException(exception_type)
            or self.subnode_width.mayRaiseException(exception_type)
            or self.mayRaiseExceptionOperation()
        )

    @abstractmethod
    def mayRaiseExceptionOperation(self):
        """Does the operation part raise an exception possibly."""


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
