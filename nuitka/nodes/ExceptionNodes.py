#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Nodes related to raising and making exceptions.

"""

from nuitka.PythonVersions import python_version

from .ChildrenHavingMixins import ChildHavingExceptionTypeMixin
from .ExpressionBases import ExpressionBase, ExpressionNoSideEffectsMixin
from .ExpressionBasesGenerated import (
    ExpressionBuiltinMakeExceptionAttributeErrorBase,
    ExpressionBuiltinMakeExceptionBase,
    ExpressionBuiltinMakeExceptionImportErrorBase,
)
from .NodeBases import SideEffectsFromChildrenMixin, StatementBase
from .StatementBasesGenerated import StatementRaiseExceptionBase


class StatementRaiseExceptionMixin(object):
    # Mixins are required to also specify slots
    __slots__ = ()

    @staticmethod
    def isStatementAborting():
        return True

    @staticmethod
    def isStatementRaiseException():
        return True

    @staticmethod
    def willRaiseAnyException():
        return True


class StatementRaiseException(
    StatementRaiseExceptionMixin, StatementRaiseExceptionBase
):
    kind = "STATEMENT_RAISE_EXCEPTION"

    named_children = (
        "exception_type",
        "exception_value|optional",
        "exception_trace|optional",
        "exception_cause|optional",
    )
    auto_compute_handling = "post_init,operation"

    __slots__ = ("reraise_finally",)

    def postInitNode(self):
        self.reraise_finally = False

    def computeStatementOperation(self, trace_collection):
        # TODO: Limit by known type.
        trace_collection.onExceptionRaiseExit(BaseException)

        exception_type = self.subnode_exception_type
        if exception_type.isCompileTimeConstant():
            exception_type_value = exception_type.getCompileTimeConstant()

            if not isinstance(exception_type_value, type) or (
                not isinstance(exception_type_value, BaseException)
                and not issubclass(exception_type_value, BaseException)
            ):
                try:
                    raise exception_type_value
                except TypeError as exc:
                    from .NodeMakingHelpers import (
                        makeRaiseExceptionStatementFromInstance,
                    )

                    return (
                        makeRaiseExceptionStatementFromInstance(
                            source_ref=self.source_ref, exception=exc
                        ),
                        "new_raise",
                        "Compile time constant is known to not be an exception.",
                    )

                else:
                    # Really expecting a "TypeError" to be raised and not say
                    # an "AssertionError".
                    assert False, exception_type_value

                return

        return self, None, None

    @staticmethod
    def needsFrame():
        return True

    @staticmethod
    def getStatementNiceName():
        return "exception raise statement"


class StatementReraiseException(StatementRaiseExceptionMixin, StatementBase):
    kind = "STATEMENT_RERAISE_EXCEPTION"

    def finalize(self):
        del self.parent

    def computeStatement(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    # TODO: Not actually true, leads to wrong frame attached if there is
    # no pending exception.
    @staticmethod
    def needsFrame():
        return False

    @staticmethod
    def getStatementNiceName():
        return "exception re-raise statement"


class ExpressionRaiseException(ChildHavingExceptionTypeMixin, ExpressionBase):
    """This node type is only produced via optimization.

    CPython only knows exception raising as a statement, but often the raising
    of exceptions can be predicted to occur as part of an expression, which it
    replaces then.
    """

    kind = "EXPRESSION_RAISE_EXCEPTION"

    named_children = ("exception_type",)

    def __init__(self, exception_type, source_ref):
        ChildHavingExceptionTypeMixin.__init__(
            self,
            exception_type=exception_type,
        )

        ExpressionBase.__init__(self, source_ref)

    @staticmethod
    def willRaiseAnyException():
        return True

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def computeExpressionDrop(self, statement, trace_collection):
        result = self.asStatement()

        del self.parent

        return (
            result,
            "new_raise",
            """\
Propagated implicit raise expression to raise statement.""",
        )

    def asStatement(self):
        return StatementRaiseException(
            exception_type=self.subnode_exception_type,
            exception_value=None,
            exception_trace=None,
            exception_cause=None,
            source_ref=self.source_ref,
        )


class ExpressionBuiltinMakeException(ExpressionBuiltinMakeExceptionBase):
    kind = "EXPRESSION_BUILTIN_MAKE_EXCEPTION"

    named_children = ("args|tuple",)

    __slots__ = ("exception_name", "for_raise")

    # There is nothing to compute for it as a value.
    auto_compute_handling = "final,no_raise"

    def __init__(self, exception_name, args, for_raise, source_ref):
        ExpressionBuiltinMakeExceptionBase.__init__(self, args, source_ref=source_ref)

        self.exception_name = exception_name
        self.for_raise = for_raise

    def getDetails(self):
        return {"exception_name": self.exception_name, "for_raise": self.for_raise}

    def getExceptionName(self):
        return self.exception_name

    def computeExpression(self, trace_collection):
        return self, None, None

    def mayRaiseException(self, exception_type):
        for arg in self.subnode_args:
            if arg.mayRaiseException(exception_type):
                return True

        return False

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionBuiltinMakeExceptionImportError(
    SideEffectsFromChildrenMixin, ExpressionBuiltinMakeExceptionImportErrorBase
):
    """Python3 ImportError dedicated node with extra arguments."""

    kind = "EXPRESSION_BUILTIN_MAKE_EXCEPTION_IMPORT_ERROR"

    named_children = ("args|tuple", "name|optional", "path|optional")

    node_attributes = ("for_raise",)

    __slots__ = ()

    # There is nothing to compute for it as a value.
    auto_compute_handling = "final,no_raise"

    python_version_spec = ">= 0x300"

    @staticmethod
    def getExceptionName():
        return "ImportError"

    def computeExpression(self, trace_collection):
        return self, None, None

    def mayRaiseException(self, exception_type):
        for arg in self.subnode_args:
            if arg.mayRaiseException(exception_type):
                return True

        return False

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionBuiltinMakeExceptionModuleNotFoundError(
    ExpressionBuiltinMakeExceptionImportError
):
    kind = "EXPRESSION_BUILTIN_MAKE_EXCEPTION_MODULE_NOT_FOUND_ERROR"

    python_version_spec = ">= 0x360"

    @staticmethod
    def getExceptionName():
        return "ModuleNotFoundError"


class ExpressionBuiltinMakeExceptionAttributeError(
    SideEffectsFromChildrenMixin, ExpressionBuiltinMakeExceptionAttributeErrorBase
):
    """Python3 ImportError dedicated node with extra arguments."""

    kind = "EXPRESSION_BUILTIN_MAKE_EXCEPTION_ATTRIBUTE_ERROR"

    named_children = ("args|tuple", "name|optional", "obj|optional")

    node_attributes = ("for_raise",)

    __slots__ = ()

    # There is nothing to compute for it as a value.
    auto_compute_handling = "final,no_raise"

    python_version_spec = ">= 0x3a0"

    @staticmethod
    def getExceptionName():
        return "AttributeError"

    def computeExpression(self, trace_collection):
        return self, None, None

    def mayRaiseException(self, exception_type):
        for arg in self.subnode_args:
            if arg.mayRaiseException(exception_type):
                return True

        return False

    @staticmethod
    def mayRaiseExceptionOperation():
        return False


class ExpressionCaughtMixin(ExpressionNoSideEffectsMixin):
    """Common things for all caught exception references."""

    __slots__ = ()

    def finalize(self):
        del self.parent


class ExpressionCaughtExceptionTypeRef(ExpressionCaughtMixin, ExpressionBase):
    kind = "EXPRESSION_CAUGHT_EXCEPTION_TYPE_REF"

    def __init__(self, source_ref):
        ExpressionBase.__init__(self, source_ref)

    def computeExpressionRaw(self, trace_collection):
        # TODO: Might be predictable based on the exception handler this is in.
        return self, None, None


class ExpressionCaughtExceptionValueRef(ExpressionCaughtMixin, ExpressionBase):
    kind = "EXPRESSION_CAUGHT_EXCEPTION_VALUE_REF"

    def __init__(self, source_ref):
        ExpressionBase.__init__(self, source_ref)

    def computeExpressionRaw(self, trace_collection):
        # TODO: Might be predictable based on the exception handler this is in.
        return self, None, None


class ExpressionCaughtExceptionTracebackRef(ExpressionCaughtMixin, ExpressionBase):
    kind = "EXPRESSION_CAUGHT_EXCEPTION_TRACEBACK_REF"

    def __init__(self, source_ref):
        ExpressionBase.__init__(self, source_ref)

    def computeExpressionRaw(self, trace_collection):
        return self, None, None


def makeBuiltinMakeExceptionNode(
    exception_name, args, for_raise, name=None, path=None, obj=None, source_ref=None
):
    assert type(exception_name) is str, exception_name

    if exception_name == "ImportError" and python_version >= 0x300:
        return ExpressionBuiltinMakeExceptionImportError(
            args=args,
            name=name,
            path=path,
            for_raise=for_raise,
            source_ref=source_ref,
        )
    elif exception_name == "ModuleNotFoundError" and python_version >= 0x360:
        return ExpressionBuiltinMakeExceptionModuleNotFoundError(
            args=args,
            name=name,
            path=path,
            for_raise=for_raise,
            source_ref=source_ref,
        )
    elif exception_name == "AttributeError" and python_version >= 0x3A0:
        return ExpressionBuiltinMakeExceptionAttributeError(
            args=args,
            name=name,
            obj=obj,
            for_raise=for_raise,
            source_ref=source_ref,
        )
    else:
        # We expect to only get the star arguments for these.
        assert name is None
        assert path is None

        return ExpressionBuiltinMakeException(
            exception_name=exception_name,
            args=args,
            for_raise=for_raise,
            source_ref=source_ref,
        )


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
