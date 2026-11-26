#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Finalize markups on the node tree ahead of code generation.

Marks module value setters, function creation/direct-call/cross-module flags,
in-place assignment suspects, and frame/yield exception preservation, and
decides which function bodies need C code.
"""

from nuitka import Tracing
from nuitka.code_generation.AnnotateFunctionCodes import (
    checkAnnotateFunction,
    isBytecodeBackedFunction,
)
from nuitka.code_generation.PythonSourceCodeGeneration import (
    PythonSourceGenerationError,
)
from nuitka.ModuleRegistry import getModuleByName
from nuitka.options.Options import shallNotFallbackBytecodeToCompiled
from nuitka.PythonVersions import python_version
from nuitka.Tracing import code_generation_logger
from nuitka.tree.Operations import VisitorNoopMixin


class FinalizeMarkups(VisitorNoopMixin):
    def __init__(self, module):
        self.module = module

    def onEnterNode(self, node):
        try:
            self._onEnterNode(node)
        except Exception:
            Tracing.printError(
                "Problem with %r at %s"
                % (node, node.getSourceReference().getAsString())
            )
            raise

    def _onEnterNode(self, node):
        # pylint: disable=too-many-branches

        module_name = node.needsModuleValueSetter()

        if module_name is not None:
            module = getModuleByName(module_name)

            if module is not None:
                module.markModuleValueSetterNeeded()

        if node.isExpressionFunctionCreation() and (
            not node.getParent().isExpressionFunctionCall()
            or node.getParent().subnode_function is not node
        ):
            node.subnode_function_ref.getFunctionBody().markAsNeedsCreation()

        if node.isExpressionFunctionCall():
            node.subnode_function.subnode_function_ref.getFunctionBody().markAsDirectlyCalled()

        if node.isExpressionFunctionRef():
            function_body = node.getFunctionBody()
            parent_module = function_body.getParentModule()

            if self.module is not parent_module:
                function_body.markAsCrossModuleUsed()

                self.module.addCrossUsedFunction(function_body)

        if node.isStatementAssignmentVariable():
            target_var = node.getVariable()
            assign_source = node.subnode_source

            if assign_source.isExpressionOperationBinary():
                left_arg = assign_source.subnode_left

                if (
                    left_arg.isExpressionVariableRefOrTempVariableRef()
                    and assign_source.subnode_left.getVariable() is target_var
                    and assign_source.isInplaceSuspect()
                ):
                    node.markAsInplaceSuspect()
                elif left_arg.isExpressionLocalsVariableRefOrFallback():
                    assign_source.removeMarkAsInplaceSuspect()

        if python_version < 0x300 and node.isStatementPublishException():
            node.getParentStatementsFrame().markAsFrameExceptionPreserving()

        if python_version >= 0x300 and (
            node.isExpressionYield()
            or node.isExpressionYieldFrom()
            or node.isExpressionYieldFromAwaitable()
        ):
            search = node.getParent()

            # TODO: This is best achieved by having different yield nodes
            # depending on containing function kind to begin with and should
            # be discovered during the build.

            while (
                not search.isExpressionGeneratorObjectBody()
                and not search.isExpressionCoroutineObjectBody()
                and not search.isExpressionAsyncgenObjectBody()
            ):
                last_search = search
                search = search.getParent()

                if (
                    search.isStatementTry()
                    and last_search == search.subnode_except_handler
                ):
                    node.markAsExceptionPreserving()
                    break


def decideAnnotateFunctionFallbacks(module):
    """Decide which Python source backed annotate functions must use C code."""
    module_name = module.getFullName()

    for function_body in module.getUsedFunctions():
        if not isBytecodeBackedFunction(function_body):
            continue

        try:
            checkAnnotateFunction(function_body)
        except PythonSourceGenerationError as e:
            function_qualname = function_body.getFunctionQualname()
            source_ref = function_body.getSourceReference()

            if shallNotFallbackBytecodeToCompiled(
                module_name=module_name,
                function_qualname=function_qualname,
                source_ref=source_ref,
            ):
                return code_generation_logger.sysexit(
                    """\
Error, bytecode-to-compiled fallback is disallowed for annotate function '%s' at %s: %s"""
                    % (function_qualname, source_ref.getAsString(), e)
                )

            function_body.addFlag("force_c")


def markFunctionsNeededForCCode(module):
    """Mark function bodies that are created or called from compiled C code.

    Notes:
        Function creations inside Python source backed function bodies are not
        part of the C code and are therefore not followed.
    """
    stack = [module.subnode_body]

    while stack:
        node = stack.pop()

        if node is None:
            continue

        if node.isExpressionFunctionRef():
            function_body = node.getFunctionBody()

            if not function_body.needsCCode() and not isBytecodeBackedFunction(
                function_body
            ):
                function_body.markAsNeedsCCode()
                stack.append(function_body.subnode_body)

            continue

        stack.extend(node.getVisitableNodes())


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
