#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit patches or make the software available to licensors of
#     this software in either form, you automatically them grant them a
#     license for your part of the code under "Apache License 2.0" unless you
#     choose to remove this notice.
#
#     Kay Hayen uses the right to license his code under only GPL version 3,
#     to discourage a fork of Nuitka before it is "finished". He will later
#     make a new "Nuitka" release fully under "Apache License 2.0".
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
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

            while not search.isStatementForLoop() and not search.isStatementWhileLoop():
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


        if node.isAssignTargetVariable():
            # TODO: Looks like a getParentStatement is missing.
            parent = node

            while not parent.isStatement():
                parent = parent.getParent()

            if parent.isStatementDel():
                node.getTargetVariableRef().getVariable().setHasDelIndicator()

        if node.isStatementTryExcept():
            parent = node.getParentVariableProvider()

            parent.markAsTryExceptContaining()

        if node.isStatementExec() or node.isExpressionBuiltinExec():
            parent = node.getParentVariableProvider()

            if parent.isExpressionFunctionBody():
                parent.markAsExecContaining()

        if node.isExpressionBuiltinImport() and not Options.getShallFollowExtra():
            warning( """\
Unresolved '__import__' call at '%s' may require use of '--recurse-directory'.""" % (
                    node.getSourceReference().getAsString()
                )
            )
