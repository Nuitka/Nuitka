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
""" Base for all optimization modules

Provides a class that all optimization visitors should inherit from.
"""

# Pylint fails to find this, somewhat, at least it reports wrong about this.
from .. import TreeOperations

# pylint: disable=W0611
# These are here for easier import by the optimization steps.

from nuitka.nodes.NodeMakingHelpers import (
    makeRaiseExceptionReplacementExpressionFromInstance,
    makeRaiseExceptionReplacementStatement,
    makeBuiltinExceptionRefReplacementNode,
    makeBuiltinRefReplacementNode,
    makeConstantReplacementNode,
)

from logging import warning, debug, info
# pylint: enable=W0611


class OptimizationVisitorBase( TreeOperations.VisitorNoopMixin ):
    on_signal = None

    # Type of visit, by default all the tree is visited, but can also visit scopes only or
    # only nodes of given "kinds"
    visit_type = "tree"

    # Override this with the kind of nodes to be visited
    visit_kinds = None

    def signalChange( self, tags, source_ref, message ):
        """ Indicate a change to the optimization framework.

        """
        debug( "%s : %s : %s" % ( source_ref.getAsString(), tags, message ) )

        if self.on_signal is not None:
            self.on_signal( tags )

    def execute( self, tree, on_signal = None ):
        self.on_signal = on_signal

        if self.visit_type == "tree":
            TreeOperations.visitTree(
                tree    = tree,
                visitor = self
            )
        elif self.visit_type == "scopes":
            TreeOperations.visitScopes(
                tree    = tree,
                visitor = self
            )
        else:
            raise AssertionError( self, self.visit_type )

    def replaceWithComputationResult( self, node, computation, description ):
        # Try and turn raised exceptions into static raises. pylint: disable=W0703

        try:
            result = computation()
        except Exception as e:
            new_node = makeRaiseExceptionReplacementExpressionFromInstance(
                expression = node,
                exception  = e
            )

            self.signalChange(
                "new_raise",
                node.getSourceReference(),
                description + " was predicted to raise an exception."
            )
        else:
            new_node = makeConstantReplacementNode(
                constant = result,
                node     = node
            )

            self.signalChange(
                "new_constant",
                node.getSourceReference(),
                description + " was predicted to constant result."
            )

        node.replaceWith( new_node )

class OptimizationDispatchingVisitorBase( OptimizationVisitorBase ):
    def __init__( self, dispatch_dict ):
        self.dispatch_dict = dispatch_dict

    def onEnterNode( self, node ):
        key = self.getKey( node )

        if key in self.dispatch_dict:
            new_node = self.dispatch_dict[ key ]( node )

            return new_node


    def getKey( self, node ):
        # Abstract method, pylint: disable=R0201,W0613
        assert False

class OptimizationVisitorScopedBase( OptimizationVisitorBase ):
    visit_type = "scopes"


def areConstants( expressions ):
    """ Check if all the expressions are in fact constants.

        This is a frequent pre-condition for optimizations.
    """

    for expression in expressions:
        if not expression.isExpressionConstantRef():
            return False
    else:
        return True
