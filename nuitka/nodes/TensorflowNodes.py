#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Nodes that represent tensorflow functions

"""

from nuitka.HardImportRegistry import addModuleDynamicHard

from .HardImportNodesGenerated import ExpressionTensorflowFunctionCallBase

addModuleDynamicHard(module_name="tensorflow")


class ExpressionTensorflowFunctionCall(ExpressionTensorflowFunctionCallBase):
    kind = "EXPRESSION_TENSORFLOW_FUNCTION_CALL"

    def replaceWithCompileTimeValue(self, trace_collection):
        # TODO: The node generation should allow for this to not be necessary
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


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
