#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka import Options, Utils, Importing

from .FinalizeBase import FinalizationVisitorBase

from logging import warning

def isWhileListedImport(node):
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
            search = node.getParent()

            # Search up to the containing loop.
            while not search.isStatementLoop():
                last_search = search
                search = search.getParent()

                if search.isStatementTryFinally() and last_search == search.getBlockTry():
                    search.markAsExceptionBreak()
                    node.markAsExceptionDriven()

            if node.isExceptionDriven():
                search.markAsExceptionBreak()

        if node.isStatementContinueLoop():
            search = node.getParent()

            # Search up to the containing loop.
            while not search.isStatementLoop():
                last_search = search
                search = search.getParent()

                if search.isStatementTryFinally() and \
                   last_search == search.getBlockTry():
                    search.markAsExceptionContinue()
                    node.markAsExceptionDriven()

            if node.isExceptionDriven():
                search.markAsExceptionContinue()

        if node.isExpressionYield() or node.isExpressionYieldFrom():
            search = node.getParent()

            while not search.isExpressionFunctionBody():
                last_search = search
                search = search.getParent()

                if Utils.python_version >= 300 and \
                   search.isStatementTryFinally() and \
                   last_search == search.getBlockTry():
                    node.markAsExceptionPreserving()
                    break

                if search.isStatementExceptHandler():
                    node.markAsExceptionPreserving()
                    break

        if node.isStatementReturn() or node.isStatementGeneratorReturn():
            search = node.getParent()

            exception_driven = False
            last_found = None

            # Search up to the containing function, and check for a try/finally
            # containing the "return" statement.
            while not search.isExpressionFunctionBody():
                last_search = search
                search = search.getParent()

                if search.isStatementTryFinally() and \
                   last_search == search.getBlockTry():
                    search.markAsExceptionReturnValueCatch()

                    exception_driven = True

                    if last_found is not None:
                        last_found.markAsExceptionReturnValueReraise()

                    last_found = search

            if exception_driven:
                search.markAsExceptionReturnValue()

            node.setExceptionDriven( exception_driven )

        if node.isStatementRaiseException() and node.isReraiseException():
            search = node.getParent()

            # Check if it's in a try/except block.
            while not search.isParentVariableProvider():
                if search.isStatementsSequence():
                    if search.getParent().isStatementExceptHandler():
                        node.markAsReraiseLocal()
                        break

                    if search.getParent().isStatementTryFinally() and \
                       Utils.python_version >= 300:
                        node.markAsReraiseFinally()

                search = search.getParent()

            search = node.getParent()

        if node.isStatementDelVariable():
            variable = node.getTargetVariableRef().getVariable()

            while variable.isReference():
                variable = variable.getReferenced()

            variable.setHasDelIndicator()

        if node.isStatementTryExcept():
            provider = node.getParentVariableProvider()
            provider.markAsTryExceptContaining()

            if not node.isStatementTryExceptOptimized():
                parent_frame = node.getParentStatementsFrame()
                parent_frame.markAsFrameExceptionPreserving()

        if node.isStatementTryFinally():
            provider = node.getParentVariableProvider()
            provider.markAsTryFinallyContaining()

            if Utils.python_version >= 300:
                parent_frame = node.getParentStatementsFrame()
                parent_frame.markAsFrameExceptionPreserving()

        if node.isStatementRaiseException():
            provider = node.getParentVariableProvider()
            provider.markAsRaiseContaining()

        if node.isExpressionBuiltinImport() and \
           not Options.getShallFollowExtra() and \
           not isWhileListedImport(node):
            warning( """Unresolved '__import__' call at '%s' may require use \
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
            parent_module = node.getFunctionBody().getParentModule()

            if node.getParentModule() is not parent_module:
                node.getFunctionBody().markAsCrossModuleUsed()
