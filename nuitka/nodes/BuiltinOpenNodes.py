#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Node the calls to the 'open' built-in.

This is a rather two sided beast, as it may be read or write. And we would like to be able
to track it, so we can include files into the executable, or write more efficiently.
"""

from .BuiltinRefNodes import ExpressionBuiltinPatchableTypeRef
from .ExpressionBases import ExpressionBase
from .HardImportNodesGenerated import (
    ExpressionBuiltinsOpenBefore3CallBase,
    ExpressionBuiltinsOpenSince3CallBase,
)
from .shapes.BuiltinTypeShapes import tshape_file


class ExpressionBuiltinOpenMixin(object):
    # Mixins are required to define empty slots
    __slots__ = ()

    @staticmethod
    def getTypeShape():
        return tshape_file

    def replaceWithCompileTimeValue(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        # Note: Quite impossible to predict without further assumptions, but we could look
        # at the arguments at least.
        return self, None, None


class ExpressionBuiltinsOpenBefore3Call(
    ExpressionBuiltinOpenMixin,
    ExpressionBuiltinsOpenBefore3CallBase,
    ExpressionBase,
):
    kind = "EXPRESSION_BUILTINS_OPEN_BEFORE3_CALL"


class ExpressionBuiltinsOpenSince3Call(
    ExpressionBuiltinOpenMixin,
    ExpressionBuiltinsOpenSince3CallBase,
    ExpressionBase,
):
    kind = "EXPRESSION_BUILTINS_OPEN_SINCE3_CALL"


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
    if str is bytes:
        return ExpressionBuiltinsOpenBefore3Call(
            name=filename,
            mode=mode,
            buffering=buffering,
            source_ref=source_ref,
        )
    else:
        return ExpressionBuiltinsOpenSince3Call(
            file=filename,
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
