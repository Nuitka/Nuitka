#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Finalize the markups

Set flags on functions and classes to indicate if a locals dict is really
needed.

Set a flag on loops if they really need to catch Continue and Break exceptions
or if it can be more simple code.

Set a flag on return statements and functions that require the use of
"ReturnValue" exceptions, or if it can be more simple code.

Set a flag on re-raises of exceptions if they can be simple throws or if they
are in another context.

"""

from logging import warning

from nuitka import Importing, Options, Utils

from .FinalizeBase import FinalizationVisitorBase


def isWhiteListedImport(node):
    module = node.getParentModule()

    return Importing.isStandardLibraryPath(module.getFilename())

class FinalizeMarkups(FinalizationVisitorBase):
    def onEnterNode(self, node):
        # This has many different things it deals with, so there need to be a
        # lot of branches and statements, pylint: disable=R0912,R0915
        if node.isExpressionFunctionBody():
            if node.isUnoptimized():
                node.markAsLocalsDict()

        if node.needsLocalsDict():
            provider = node.getParentVariableProvider()

            if provider.isExpressionFunctionBody():
                provider.markAsLocalsDict()

        if node.isStatementBreakLoop():
            search = node

            # Search up to the containing loop.
            while not search.isStatementLoop():
                last_search = search
                search = search.getParent()

                if search.isStatementTryFinally() and \
                   last_search == search.getBlockTry():
                    search.markAsNeedsBreakHandling()

        if node.isStatementContinueLoop():
            search = node

            # Search up to the containing loop.
            while not search.isStatementLoop():
                last_search = search
                search = search.getParent()

                if search.isStatementTryFinally() and \
                   last_search == search.getBlockTry():
                    search.markAsNeedsContinueHandling()

        if Utils.python_version >= 300:
            if node.isExpressionYield() or node.isExpressionYieldFrom():
                search = node.getParent()

                while not search.isExpressionFunctionBody():
                    last_search = search
                    search = search.getParent()

                    if search.isStatementTryFinally() and \
                       last_search == search.getBlockTry() and \
                       search.needsExceptionPublish():
                        node.markAsExceptionPreserving()
                        break

                    if search.isStatementTryExcept() and \
                       search.getExceptionHandling() is last_search and \
                       search.needsExceptionPublish():
                        node.markAsExceptionPreserving()
                        break

        if node.isStatementReturn() or node.isStatementGeneratorReturn():
            search = node

            # Search up to the containing function, and check for a try/finally
            # containing the "return" statement.
            while not search.isExpressionFunctionBody():
                last_search = search
                search = search.getParent()

                if search.isStatementTryFinally():
                    if last_search == search.getBlockTry():
                        search.markAsNeedsReturnHandling(1)

                        provider = search.getParentVariableProvider()
                        if provider.isGenerator():
                            provider.markAsNeedsGeneratorReturnHandling(2)

                    if last_search == search.getBlockFinal():
                        if search.needsReturnHandling():
                            search.markAsNeedsReturnHandling(2)

            if search.isGenerator():
                search.markAsNeedsGeneratorReturnHandling(1)

        if node.isStatementTryExcept():
            if node.public_exc:
                parent_frame = node.getParentStatementsFrame()
                assert parent_frame, node

                parent_frame.markAsFrameExceptionPreserving()

        if node.isStatementTryFinally():
            if Utils.python_version >= 300 and node.public_exc:
                parent_frame = node.getParentStatementsFrame()
                parent_frame.markAsFrameExceptionPreserving()

        if node.isExpressionBuiltinImport() and \
           not Options.getShallFollowExtra() and \
           not Options.getShallFollowExtraFilePatterns() and \
           not Options.shallFollowNoImports() and \
           not isWhiteListedImport(node):
            warning("""Unresolved '__import__' call at '%s' may require use \
of '--recurse-directory'.""" % (
                    node.getSourceReference().getAsString()
                )
            )

        if node.isExpressionFunctionCreation():
            if not node.getParent().isExpressionFunctionCall():
                node.getFunctionRef().getFunctionBody().markAsNeedsCreation()

        if node.isExpressionFunctionCall():
            node.getFunction().getFunctionRef().getFunctionBody().\
              markAsDirectlyCalled()

        if node.isExpressionFunctionRef():
            function_body = node.getFunctionBody()
            parent_module = function_body.getParentModule()

            node_module = node.getParentModule()
            if node_module is not parent_module:
                function_body.markAsCrossModuleUsed()

                node_module.addCrossUsedFunction(function_body)

        if node.isStatementAssignmentVariable():
            target_var = node.getTargetVariableRef().getVariable()
            assign_source = node.getAssignSource()

            if assign_source.isExpressionOperationBinary():
                left_arg = assign_source.getLeft()

                if left_arg.isExpressionVariableRef():
                    if assign_source.getLeft().getVariable() is target_var:
                        assign_source.markAsInplaceSuspect()
                        node.markAsInplaceSuspect()
