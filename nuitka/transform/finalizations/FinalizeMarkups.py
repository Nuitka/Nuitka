#
#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at a later time to
#     the PSF. With this version of Nuitka, using it for a Closed Source and
#     distributing the binary only is not allowed.
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

from .FinalizeBase import FinalizationVisitorBase

class FinalizeMarkups( FinalizationVisitorBase ):
    def __call__( self, node ):
        if node.isExpressionFunctionBody() or node.isExpressionClassBody():
            if OverflowCheck.check( node.getBody() ):
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

            if parent.isStatementAssignment() and parent.getSource() is None:
                node.getTargetVariableRef().getVariable().setHasDelIndicator()

        if node.isStatementTryExcept():
            parent = node.getParentVariableProvider()

            parent.markAsTryExceptContaining()
