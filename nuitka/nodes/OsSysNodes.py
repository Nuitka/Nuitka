#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Nodes the represent ways to access os and sys functions. """


from .ExpressionBases import ExpressionNoSideEffectsMixin
from .HardImportNodesGenerated import (
    ExpressionOsPathExistsCallBase,
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
