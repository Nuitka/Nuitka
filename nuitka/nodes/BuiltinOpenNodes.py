#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Node the calls to the 'open' built-in.

This is a rather two sided beast, as it may be read or write. And we would like to be able
to track it, so we can include files into the executable, or write more efficiently.
"""

from .BuiltinRefNodes import ExpressionBuiltinPatchableTypeRef
from .ChildrenHavingMixins import (
    ChildrenExpressionBuiltinOpenP2Mixin,
    ChildrenExpressionBuiltinOpenP3Mixin,
)
from .ExpressionBases import ExpressionBase
from .shapes.BuiltinTypeShapes import tshape_file


class ExpressionBuiltinOpenMixin(object):
    # Mixins are required to define empty slots
    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_file

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        # Note: Quite impossible to predict without further assumptions, but we could look
        # at the arguments at least.
        return self, None, None


class ExpressionBuiltinOpenP2(
    ExpressionBuiltinOpenMixin,
    ChildrenExpressionBuiltinOpenP2Mixin,
    ExpressionBase,
):
    kind = "EXPRESSION_BUILTIN_OPEN_P2"

    python_version_spec = "< 0x300"

    named_children = ("filename", "mode|optional", "buffering|optional")

    def __init__(self, filename, mode, buffering, source_ref):
        ChildrenExpressionBuiltinOpenP2Mixin.__init__(
            self,
            filename=filename,
            mode=mode,
            buffering=buffering,
        )

        ExpressionBase.__init__(self, source_ref)


class ExpressionBuiltinOpenP3(
    ExpressionBuiltinOpenMixin,
    ChildrenExpressionBuiltinOpenP3Mixin,
    ExpressionBase,
):
    kind = "EXPRESSION_BUILTIN_OPEN_P3"

    python_version_spec = ">= 0x300"

    named_children = (
        "filename",
        "mode|optional",
        "buffering|optional",
        "encoding|optional",
        "errors|optional",
        "newline|optional",
        "closefd|optional",
        "opener|optional",
    )

    def __init__(
        self,
        filename,
        mode,
        buffering,
        encoding,
        errors,
        newline,
        closefd,
        opener,
        source_ref,
    ):
        ChildrenExpressionBuiltinOpenP3Mixin.__init__(
            self,
            filename=filename,
            mode=mode,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
            closefd=closefd,
            opener=opener,
        )

        ExpressionBase.__init__(self, source_ref)


def makeExpressionBuiltinsOpenCall(
    filename,
    mode,
    buffering,
    encoding,
    errors,
    newline,
    closefd,
    opener,
    source_ref,
):
    """Function reference ctypes.CDLL"""

    assert str is not bytes
    return ExpressionBuiltinOpenP3(
        filename=filename,
        mode=mode,
        buffering=buffering,
        encoding=encoding,
        errors=errors,
        newline=newline,
        closefd=closefd,
        opener=opener,
        source_ref=source_ref,
    )


def makeBuiltinOpenRefNode(source_ref):
    return ExpressionBuiltinPatchableTypeRef(builtin_name="open", source_ref=source_ref)


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
