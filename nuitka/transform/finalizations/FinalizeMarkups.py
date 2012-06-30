#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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

Set flags on functions and classes to indicate if a locals dict is really needed.

Set a flag on loops if they really need to catch Continue and Break exceptions or
if it can be more simple code.

Set a flag on re-raises of exceptions if they can be simple throws or if they are
in another context.

"""
from nuitka.nodes import OverflowCheck
from nuitka import Options

from .FinalizeBase import FinalizationVisitorBase

from logging import warning

class FinalizeMarkups( FinalizationVisitorBase ):
    def onEnterNode( self, node ):
        # This has many different things it deals with, so there need to be a lot of
        # branches. pylint: disable=R0912

        # Record if a function or class has an overflow. TODO: The Overflow check
        # module and this should be united in a per tag finalization check on say
        # "callable_body" tag
        if node.isExpressionFunctionBody() or node.isExpressionClassBody():
            body = node.getBody()

            if body is not None and OverflowCheck.check( body ):
                node.markAsLocalsDict()

        if node.isStatementBreakLoop() or node.isStatementContinueLoop():
            search = node.getParent()

            crossed_try = False

            # Search up to the containing loop.
            while not search.isStatementLoop():
                last_search = search
                search = search.getParent()

                if search.isStatementTryFinally() and last_search == search.getBlockTry():
                    crossed_try = True

            if crossed_try:
                search.markAsExceptionBreakContinue()
                node.markAsExceptionBreakContinue()

        if node.isStatementRaiseException() and node.isReraiseException():
            search = node.getParent()

            crossed_except = False

            while not search.isParentVariableProvider():
                if search.isStatementsSequence():
                    if search.getParent().isStatementExceptHandler():
                        crossed_except = True
                        break

                search = search.getParent()

            if crossed_except:
                node.markAsReraiseLocal()

        if node.isStatementDelVariable():
            node.getTargetVariableRef().getVariable().setHasDelIndicator()

        if node.isStatementTryExcept():
            parent = node.getParentVariableProvider()

            parent.markAsTryExceptContaining()

        if node.isExpressionBuiltinImport() and not Options.getShallFollowExtra():
            warning( """\
Unresolved '__import__' call at '%s' may require use of '--recurse-directory'.""" % (
                    node.getSourceReference().getAsString()
                )
            )
