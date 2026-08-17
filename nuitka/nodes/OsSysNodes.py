#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Nodes the represent ways to access os and sys functions."""

import os

from .ConstantRefNodes import makeConstantRefNode
from .ExceptionNodes import (
    ExpressionRaiseException,
    makeBuiltinMakeExceptionNode,
)
from .ExpressionBases import ExpressionNoSideEffectsMixin
from .HardImportNodesGenerated import (
    ExpressionOsListdirCallBase,
    ExpressionOsLstatCallBase,
    ExpressionOsPathAbspathCallBase,
    ExpressionOsPathBasenameCallBase,
    ExpressionOsPathExistsCallBase,
    ExpressionOsPathIsabsCallBase,
    ExpressionOsPathIsdirCallBase,
    ExpressionOsPathIsfileCallBase,
    ExpressionOsStatCallBase,
    ExpressionOsUnameCallBase,
)


class ExpressionOsUnameCall(
    # TODO: Needs a tshape_namedtuple_alike shape, as opposed to
    # tshape_namedtuple_derived, since posix.uname_result is a C-level tuple
    # subclass with named fields, not a collections.namedtuple.
    ExpressionNoSideEffectsMixin,
    ExpressionOsUnameCallBase,
):
    kind = "EXPRESSION_OS_UNAME_CALL"

    @staticmethod
    def getIterationLength():
        return 5

    def isKnownToBeIterable(self, count):
        return count is None or count == 5

    def isKnownToBeIterableAtMin(self, count):
        return count <= 5

    @staticmethod
    def canPredictIterationValues():
        return False

    @staticmethod
    def isKnownToBeIndexable():
        return True

    @staticmethod
    def mayRaiseExceptionOperation():
        return False

    def computeExpressionSubscript(self, lookup_node, subscript, trace_collection):
        if subscript.isIndexConstant() and subscript.getIntegerValue() == 0:
            return (
                makeConstantRefNode(constant=os.uname()[0], source_ref=self.source_ref),
                "new_constant",
                "Subscript of 'os.uname' at index 0 is platform constant.",
            )

        trace_collection.onExceptionRaiseExit(BaseException)

        return lookup_node, None, None

    def replaceWithCompileTimeValue(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionOsPathExistsCall(ExpressionOsPathExistsCallBase):
    kind = "EXPRESSION_OS_PATH_EXISTS_CALL"

    def replaceWithCompileTimeValue(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionOsPathIsfileCall(ExpressionOsPathIsfileCallBase):
    kind = "EXPRESSION_OS_PATH_ISFILE_CALL"

    def replaceWithCompileTimeValue(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionOsPathIsdirCall(ExpressionOsPathIsdirCallBase):
    kind = "EXPRESSION_OS_PATH_ISDIR_CALL"

    def replaceWithCompileTimeValue(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionOsPathBasenameCall(ExpressionOsPathBasenameCallBase):
    kind = "EXPRESSION_OS_PATH_BASENAME_CALL"

    def replaceWithCompileTimeValue(self, trace_collection):
        result = makeConstantRefNode(
            constant=os.path.basename(self.subnode_p.getCompileTimeConstant()),
            source_ref=self.source_ref,
        )

        return (
            result,
            "new_expression",
            "Compile time resolved 'os.path.basename' call.",
        )


class ExpressionOsPathDirnameCall(ExpressionOsPathBasenameCallBase):
    kind = "EXPRESSION_OS_PATH_DIRNAME_CALL"

    def replaceWithCompileTimeValue(self, trace_collection):
        result = makeConstantRefNode(
            constant=os.path.dirname(self.subnode_p.getCompileTimeConstant()),
            source_ref=self.source_ref,
        )

        return (
            result,
            "new_expression",
            "Compile time resolved 'os.path.dirname' call.",
        )


class ExpressionOsPathAbspathCall(ExpressionOsPathAbspathCallBase):
    kind = "EXPRESSION_OS_PATH_ABSPATH_CALL"

    def replaceWithCompileTimeValue(self, trace_collection):
        # Nothing we can do really

        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionOsPathNormpathCall(ExpressionOsPathAbspathCallBase):
    kind = "EXPRESSION_OS_PATH_NORMPATH_CALL"

    def replaceWithCompileTimeValue(self, trace_collection):
        result = makeConstantRefNode(
            constant=os.path.normpath(self.subnode_path.getCompileTimeConstant()),
            source_ref=self.source_ref,
        )

        return (
            result,
            "new_expression",
            "Compile time resolved 'os.path.normpath' call.",
        )


class ExpressionOsPathIsabsCall(ExpressionOsPathIsabsCallBase):
    kind = "EXPRESSION_OS_PATH_ISABS_CALL"

    def replaceWithCompileTimeValue(self, trace_collection):
        result = makeConstantRefNode(
            constant=os.path.isabs(self.subnode_s.getCompileTimeConstant()),
            source_ref=self.source_ref,
        )

        return (
            result,
            "new_expression",
            "Compile time resolved 'os.path.isabs' call.",
        )


class ExpressionOsListdirCall(ExpressionOsListdirCallBase):
    kind = "EXPRESSION_OS_LISTDIR_CALL"

    def replaceWithCompileTimeValue(self, trace_collection):
        # Nothing we can do really

        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionOsStatCall(ExpressionOsStatCallBase):
    kind = "EXPRESSION_OS_STAT_CALL"

    def replaceWithCompileTimeValue(self, trace_collection):
        # Nothing we can do really

        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionOsLstatCall(ExpressionOsLstatCallBase):
    kind = "EXPRESSION_OS_LSTAT_CALL"

    def replaceWithCompileTimeValue(self, trace_collection):
        # Nothing we can do really

        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


def makeExpressionSysExitCall(exit_code, source_ref):

    if exit_code is None:
        args = ()
    else:
        args = (exit_code,)

    return ExpressionRaiseException(
        exception_type=makeBuiltinMakeExceptionNode(
            exception_name="SystemExit",
            args=args,
            for_raise=True,
            source_ref=source_ref,
        ),
        source_ref=source_ref,
    )


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
