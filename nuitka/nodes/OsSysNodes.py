#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Nodes the represent ways to access os and sys functions. """


import os

from .BuiltinRefNodes import ExpressionBuiltinExceptionRef
from .ConstantRefNodes import makeConstantRefNode
from .ExceptionNodes import ExpressionRaiseException
from .ExpressionBases import ExpressionNoSideEffectsMixin
from .HardImportNodesGenerated import (
    ExpressionOsListdirCallBase,
    ExpressionOsPathAbspathCallBase,
    ExpressionOsPathBasenameCallBase,
    ExpressionOsPathExistsCallBase,
    ExpressionOsPathIsabsCallBase,
    ExpressionOsPathIsdirCallBase,
    ExpressionOsPathIsfileCallBase,
    ExpressionOsUnameCallBase,
)


class ExpressionOsUnameCall(
    # TODO: We don*t have this
    # ExpressionTupleShapeDerivedMixin,
    ExpressionNoSideEffectsMixin,
    ExpressionOsUnameCallBase,
):
    kind = "EXPRESSION_OS_UNAME_CALL"

    @staticmethod
    def mayRaiseExceptionOperation():
        return False

    def replaceWithCompileTimeValue(self, trace_collection):
        # TODO: The value should be its own runtime constant value type which
        # supports indexing.

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


def makeExpressionSysExitCall(exit_code, source_ref):
    if exit_code is None:
        exit_code = makeConstantRefNode(constant=None, source_ref=source_ref)

    return ExpressionRaiseException(
        exception_type=ExpressionBuiltinExceptionRef(
            exception_name="SystemExit", source_ref=source_ref
        ),
        exception_value=exit_code,
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
