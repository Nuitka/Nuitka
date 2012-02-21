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
""" Merge nested statement sequences into one and removes useless try/finally/except

This undoes the effect of inlined exec or statements replaced with statement sequences and
also removes useless try/except or try/finally statements.

"""

from .OptimizeBase import OptimizationVisitorBase, TreeOperations

from nuitka.nodes.NodeMakingHelpers import (
    makeStatementExpressionOnlyReplacementNode
)

from logging import warning

class StatementSequencesCleanupVisitor( OptimizationVisitorBase ):
    def _optimizeConstantConditionalOperation( self, node ):
        condition = node.getCondition()

        if condition.isExpressionConstantRef():
            if condition.getConstant():
                choice = "true"

                new_node = node.getBranchYes()
            else:
                choice = "false"

                new_node = node.getBranchNo()

            if new_node is None:
                if len( node.getParent().getStatements() ) == 1:
                    node.getParent().replaceWith( None )
                else:
                    node.getParent().removeStatement( node )
            else:
                node.replaceWith( new_node )

            self.signalChange(
                "new_statements",
                node.getSourceReference(),
                "Condition for branch was predicted to be always %s." % choice
            )

            raise TreeOperations.ExitNodeVisit
        else:
            no_branch = node.getBranchNo()

            if no_branch is not None and not no_branch.mayHaveSideEffects():
                no_branch = None

                node.setBranchNo( None )

            yes_branch = node.getBranchYes()

            if yes_branch is not None and not yes_branch.mayHaveSideEffects():
                yes_branch = None

                node.setBranchYes( None )

            if no_branch is None and yes_branch is None:
                new_node = makeStatementExpressionOnlyReplacementNode(
                    expression = node.getCondition(),
                    node       = node
                )

                node.replaceWith( new_node )

                self.signalChange(
                    "new_statements",
                    node.getSourceReference(),
                    "Both branches have no effect, drop conditional."
                )

                raise TreeOperations.ExitNodeVisit

    def _optimizeForLoop( self, node ):
        no_break = node.getNoBreak()

        if no_break is not None and not no_break.mayHaveSideEffects():
            no_break = None

            node.setNoBreak( None )

        body = node.getLoopBody()

        if body is not None and not body.mayHaveSideEffects():
            body = None

            node.setLoopBody( None )

        # TODO: Optimize away the for loop if possible, if e.g. the iteration has no side
        # effects, it's result is predictable etc.

    def onEnterNode( self, node ):
        if node.isStatementsSequence():
            parent = node.getParent()

            if parent.isStatementsSequence():
                assert False, node

                parent.mergeStatementsSequence( node )

                raise TreeOperations.RestartVisit
        elif node.isStatementExpressionOnly():
            if node.getExpression().isExpressionConstantRef():
                parent = node.getParent()

                if len( parent.getStatements() ) == 1:
                    parent.replaceWith( None )
                else:
                    parent.removeStatement( node )
        elif node.isStatementConditional():
            self._optimizeConstantConditionalOperation(
                node = node
            )
        elif node.isStatementForLoop():
            self._optimizeForLoop(
                node = node
            )
        elif node.isStatementTryExcept():
            if node.getBlockTry() is None:
                new_node = node.getBlockNoRaise()

                if new_node is None:
                    if len( node.getParent().getStatements() ) == 1:
                        node.getParent().replaceWith( None )
                    else:
                        node.getParent().removeStatement( node )
                else:
                    node.replaceWith( new_node )

                self.signalChange(
                    "new_statements",
                    node.getSourceReference(),
                    "Try/except was predicted to never raise, removing exception handling and guard."
                )

                raise TreeOperations.RestartVisit
        elif node.isStatementTryFinally():
            if node.getBlockTry() is None:
                new_node = node.getBlockFinal()

                if new_node is None:
                    if len( node.getParent().getStatements() ) == 1:
                        node.getParent().replaceWith( None )
                    else:
                        node.getParent().removeStatement( node )
                else:
                    node.replaceWith( new_node )

                self.signalChange(
                    "new_statements",
                    node.getSourceReference(),
                    "Try/finally was predicted to never raise, removing 'final' nature of the block."
                )

                raise TreeOperations.RestartVisit
            elif node.getBlockFinal() is None:
                new_node = node.getBlockTry()

                self.signalChange(
                    "new_statements",
                    node.getSourceReference(),
                    "Finally was predicted to not do anything, removing 'final' nature of the block."
                )

                node.replaceWith( new_node )

                raise TreeOperations.RestartVisit
