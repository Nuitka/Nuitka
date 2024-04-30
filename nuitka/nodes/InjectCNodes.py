#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Nodes to inject C code into generated code. """

from .NodeBases import StatementBase


class StatementInjectCBase(StatementBase):
    __slots__ = ("c_code",)

    def __init__(self, c_code, source_ref):
        StatementBase.__init__(self, source_ref=source_ref)

        self.c_code = c_code

    def finalize(self):
        del self.c_code

    def computeStatement(self, trace_collection):
        return self, None, None

    @staticmethod
    def mayRaiseException(exception_type):
        return False


class StatementInjectCCode(StatementInjectCBase):
    kind = "STATEMENT_INJECT_C_CODE"


class StatementInjectCDecl(StatementInjectCBase):
    kind = "STATEMENT_INJECT_C_DECL"

    __slots__ = ("c_code",)


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
