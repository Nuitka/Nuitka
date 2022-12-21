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
""" Nodes for all things "ctypes" stdlib module.

"""


from .HardImportNodesGenerated import (
    ExpressionCtypesCdllBefore38CallBase,
    ExpressionCtypesCdllSince38CallBase,
)


class ExpressionCtypesCdllSince38Call(ExpressionCtypesCdllSince38CallBase):
    """Function reference ctypes.CDLL"""

    kind = "EXPRESSION_CTYPES_CDLL_SINCE38_CALL"

    def replaceWithCompileTimeValue(self, trace_collection):
        # TODO: Locate DLLs and report to freezer
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionCtypesCdllBefore38Call(ExpressionCtypesCdllBefore38CallBase):
    """Function reference ctypes.CDLL"""

    kind = "EXPRESSION_CTYPES_CDLL_BEFORE38_CALL"

    def replaceWithCompileTimeValue(self, trace_collection):
        # TODO: Locate DLLs and report to freezer
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None
