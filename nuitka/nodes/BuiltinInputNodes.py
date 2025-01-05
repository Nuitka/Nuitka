#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Node the calls to the 'input' built-in.

This has a specific result value, which can be useful to know, but mostly
we want to apply hacks for redirected error output only, and still have
the "input" function being usable.
"""

from .ExpressionBasesGenerated import ExpressionBuiltinInputBase
from .ExpressionShapeMixins import ExpressionStrShapeExactMixin


class ExpressionBuiltinInput(ExpressionStrShapeExactMixin, ExpressionBuiltinInputBase):
    kind = "EXPRESSION_BUILTIN_INPUT"

    named_children = ("prompt|optional",)
    auto_compute_handling = "final"

    @staticmethod
    def mayRaiseExceptionOperation():
        return True


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
