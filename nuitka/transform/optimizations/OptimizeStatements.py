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
""" Merge nested statement sequences into one and removes useless try/finally/except

This undoes the effect of inlined exec or statements replaced with statement sequences and
also removes useless try/except or try/finally statements.

"""

from .OptimizeBase import OptimizationVisitorBase, TreeOperations

from nuitka.nodes import Nodes

from logging import warning

class StatementSequencesCleanupVisitor( OptimizationVisitorBase ):
    def __call__( self, node ):
        if node.isStatementsSequence():
            parent = node.getParent()

            if parent.isStatementsSequence():
                parent.mergeStatementsSequence( node )

                raise TreeOperations.RestartVisit
        elif node.isStatementExpressionOnly():
            if node.getExpression().isExpressionConstantRef():
                new_node = Nodes.CPythonStatementPass(
                    source_ref = node.getSourceReference()
                )

                node.replaceWith( new_node )
        elif node.isStatementPass():
            parent = node.getParent()

            statements = parent.getStatements()

            if len( statements ) == 1:
                owner = parent.getParent()

                # TODO: Make use of tag to be added "empty_body"
                if owner.isStatementConditional():
                    parent.replaceWith( None )
                elif owner.isStatementForLoop():
                    parent.replaceWith( None )
                elif owner.isStatementWhileLoop():
                    parent.replaceWith( None )
                elif owner.isStatementWith():
                    parent.replaceWith( None )
                elif owner.isStatementTryExcept():
                    parent.replaceWith( None )
                elif owner.isStatementTryFinally():
                    parent.replaceWith( None )
                elif owner.isStatementExceptHandler():
                    parent.replaceWith( None )
                elif owner.isExpressionFunctionBody():
                    parent.replaceWith( None )
                elif owner.isExpressionClassBody():
                    parent.replaceWith( None )
                elif owner.isModule():
                    parent.replaceWith( None )
                else:
                    warning( "Discovered pass statement %s owned by %s", node, owner )
            else:
                parent.removeStatement( node )

                # TODO: Should only re-visit this node.
                raise TreeOperations.RestartVisit
        elif node.isStatementTryExcept():
            if node.getBlockTry() is None:
                new_node = node.getBlockNoRaise()

                if new_node is None:
                    new_node = Nodes.CPythonStatementPass(
                        source_ref = node.getSourceReference()
                    )

                node.replaceWith( new_node )

                self.signalChange(
                    "new_statements",
                    node.getSourceReference(),
                    "Try/except was predicted to never raise, removing exception handling and guard."
                )
        elif node.isStatementTryFinally():
            if node.getBlockTry() is None:
                new_node = node.getBlockFinal()

                if new_node is None:
                    new_node = Nodes.CPythonStatementPass(
                        source_ref = node.getSourceReference()
                    )

                node.replaceWith( new_node )

                self.signalChange(
                    "new_statements",
                    node.getSourceReference(),
                    "Try/finally was predicted to never raise, removing 'final' nature of the block."
                )
            elif node.getBlockFinal() is None:
                new_node = node.getBlockTry()


                node.replaceWith( new_node )
