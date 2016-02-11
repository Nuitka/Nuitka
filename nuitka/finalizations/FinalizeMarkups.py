#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka import Options, Tracing
from nuitka.importing import StandardLibrary
from nuitka.plugins.Plugins import Plugins
from nuitka.PythonVersions import python_version

from .FinalizeBase import FinalizationVisitorBase


def isWhiteListedImport(node):
    module = node.getParentModule()

    return StandardLibrary.isStandardLibraryPath(module.getFilename())

class FinalizeMarkups(FinalizationVisitorBase):
    def onEnterNode(self, node):
        try:
            self._onEnterNode(node)
        except Exception:
            Tracing.printError(
                "Problem with %r at %s" % (
                    node,
                    node.getSourceReference().getAsString()
                )
            )
            raise

    def _onEnterNode(self, node):
        # This has many different things it deals with, so there need to be a
        # lot of branches and statements, pylint: disable=R0912,R0915

        # Also all self specific things have been done on the outside,
        # pylint: disable=R0201

        # Find nodes with only compile time constant children, these are
        # missing some obvious optimization potentially.
        if False: # For searching only, pylint: disable=W0125
            if not node.isStatementReturn() and \
               not node.isExpressionYield() and \
               not node.isStatementRaiseException() and \
               not node.isExpressionCall() and \
               not node.isExpressionBuiltinIter1():

                children = node.getVisitableNodes()

                if children:
                    for child in children:
                        if child.isStatement() or child.isStatementsSequence():
                            break

                        if not child.isCompileTimeConstant():
                            break
                    else:
                        assert False, (node, node.parent, children)

        if node.isExpressionFunctionBody():
            if node.isUnoptimized():
                node.markAsLocalsDict()

        if node.needsLocalsDict():
            provider = node.getParentVariableProvider()

            if not provider.isCompiledPythonModule():
                provider.markAsLocalsDict()

        if node.isStatementReturn() or node.isStatementGeneratorReturn():
            search = node

            in_tried_block = False

            # Search up to the containing function, and check for a try/finally
            # containing the "return" statement.
            search = search.getParentReturnConsumer()

            if search.isExpressionGeneratorObjectBody() or \
               search.isExpressionCoroutineObjectBody():
                if in_tried_block:
                    search.markAsNeedsGeneratorReturnHandling(2)
                else:
                    search.markAsNeedsGeneratorReturnHandling(1)

        if node.isExpressionBuiltinImport() and \
           not Options.getShallFollowExtra() and \
           not Options.getShallFollowExtraFilePatterns() and \
           not Options.shallFollowNoImports() and \
           not isWhiteListedImport(node) and \
           not Plugins.suppressBuiltinImportWarning(node.getParentModule(), node.getSourceReference()):
            warning("""Unresolved '__import__' call at '%s' may require use \
of '--recurse-directory'.""" % (
                    node.getSourceReference().getAsString()
                )
            )

        if node.isExpressionFunctionCreation():
            if not node.getParent().isExpressionFunctionCall() or \
               node.getParent().getFunction() is not node:
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
                    if assign_source.getLeft().getVariable().isModuleVariable():
                        assign_source.unmarkAsInplaceSuspect()
                    elif assign_source.getLeft().getVariable() is target_var:
                        if assign_source.isInplaceSuspect():
                            node.markAsInplaceSuspect()

        if node.isStatementPublishException():
            node.getParentStatementsFrame().markAsFrameExceptionPreserving()

        if python_version >= 300:
            if node.isExpressionYield() or node.isExpressionYieldFrom():
                search = node.getParent()

                while not search.isExpressionGeneratorObjectBody():
                    last_search = search
                    search = search.getParent()

                    if search.isStatementTry() and \
                       last_search == search.getBlockExceptHandler():
                        node.markAsExceptionPreserving()
                        break
