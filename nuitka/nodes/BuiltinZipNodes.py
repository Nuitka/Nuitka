#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
#                     Batakrishna Sahu, mailto:batakrishna.sahu@suiit.ac.in
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
""" Node for the calls to the 'zip' built-in.
"""

from nuitka.specs import BuiltinParameterSpecs

from .ExpressionBases import ExpressionChildHavingBase
from .NodeMakingHelpers import makeConstantReplacementNode


class ExpressionBuiltinZip(ExpressionChildHavingBase):
    kind = "EXPRESSION_BUILTIN_ZIP"

    # TODO: Store "values" as a named child that is a list

    builtin_spec = BuiltinParameterSpecs.builtin_zip_spec

    def computeExpression(self, trace_collection):
        # TODO: Can you tell if arguments are not iterable

        # Notice: For C side, just call zip built-in
        pass
