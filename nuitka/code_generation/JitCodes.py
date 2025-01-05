#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Code generation for JIT specific stuff, preserving source code for runtime. """

from nuitka.Options import isStandaloneMode


def addUncompiledFunctionSourceDict(func_value, context):
    if (
        isStandaloneMode()
        and func_value is not None
        and func_value.isExpressionFunctionCreation()
    ):
        function_ref = func_value.subnode_function_ref

        function_super_qualified_name = function_ref.getFunctionSuperQualifiedName()
        function_source_code = function_ref.getFunctionSourceCode()

        context.addModuleInitCode(
            """\
SET_UNCOMPILED_FUNCTION_SOURCE_DICT(%s, %s);
"""
            % (
                context.getConstantCode(function_super_qualified_name),
                context.getConstantCode(function_source_code),
            )
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
