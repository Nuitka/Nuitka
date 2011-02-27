#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
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
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
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

# pylint: disable=E0611
# Pylint fails to find this, somewhat, at least it reports wrong about this.
from .. import TreeOperations

from nuitka import Nodes

# pylint: disable=W0611
# These are here for easier import by the optimization steps.
from logging import warning, debug, info

class OptimizationVisitorBase:
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
        elif self.visit_type == "kinds":
            TreeOperations.visitKinds(
                tree    = tree,
                visitor = self,
                kinds   = self.visit_kinds
            )
        elif self.visit_type == "scopes":
            TreeOperations.visitScopes(
                tree    = tree,
                visitor = self
            )
        else:
            assert False

class OptimizationDispatchingVisitorBase( OptimizationVisitorBase ):
    def __init__( self, dispatch_dict ):
        self.dispatch_dict = dispatch_dict

    def __call__( self, node ):
        key = self.getKey( node )

        if key in self.dispatch_dict:
            new_node = self.dispatch_dict[ key ]( node )

            if new_node is not None:
                node.replaceWith( new_node = new_node )

                if new_node.isStatement() and node.parent.isStatementExpression():
                    node.parent.replaceWith( new_node )

                TreeOperations.assignParent( node.parent )

                if new_node.isConstantReference():
                    self.signalChange(
                        "new_constant",
                        node.getSourceReference(),
                        message = "Replaced %s with constant result." % node.kind
                    )
                elif new_node.isBuiltin():
                    self.signalChange(
                        "new_builtin",
                        node.getSourceReference(),
                        message = "Replaced call to builtin %s with builtin call." % new_node.kind
                    )
                elif new_node.isExpressionRaiseException():
                    self.signalChange(
                        "new_code",
                        node.getSourceReference(),
                        message = "Replaced call to builtin %s with predictable exception raise." % new_node.kind
                    )


                self.onNodeWasReplaced(
                    old_node = node
                )

    def onNodeWasReplaced( self, old_node ):
        pass

    def getKey( self, node ):
        # Abstract method, pylint: disable=R0201,W0613
        assert False


def areConstants( expressions ):
    """ Check if all the expressions are in fact constants.

        This is a frequent pre-condition for optimizations.
    """

    for expression in expressions:
        if not expression.isConstantReference():
            return False
    else:
        return True

def makeRaiseExceptionReplacementStatement( statement, exception_type, exception_value ):
    source_ref = statement.getSourceReference()

    assert type( exception_type ) is str

    result = Nodes.CPythonStatementRaiseException(
        exception_type = Nodes.CPythonExpressionVariableRef(
            variable_name = exception_type,
            source_ref    = source_ref
        ),
        exception_value = Nodes.makeConstantReplacementNode(
            constant = exception_value,
            node     = statement
        ),
        exception_trace = None,
        source_ref = source_ref
    )

    TreeOperations.assignParent( result )

    return result

def makeRaiseExceptionReplacementExpression( expression, exception_type, exception_value ):
    source_ref = expression.getSourceReference()

    assert type( exception_type ) is str

    result = Nodes.CPythonExpressionRaiseException(
        exception_type = Nodes.CPythonExpressionVariableRef(
            variable_name = exception_type,
            source_ref    = source_ref
        ),
        exception_value = Nodes.makeConstantReplacementNode(
            constant = exception_value,
            node     = expression
        ),
        source_ref = source_ref
    )

    TreeOperations.assignParent( result )

    return result

# Ignore a deprecation warning of Python 2.6 that seemingly went away with Python 2.7, so
# I am assuming the attribute will be there forever in Python 2.x, and it's safe to use.
import warnings
warnings.filterwarnings( "ignore", "BaseException.message has been deprecated" )

def makeRaiseExceptionReplacementExpressionFromInstance( expression, exception ):
    assert isinstance( exception, Exception )

    return makeRaiseExceptionReplacementExpression(
        expression      = expression,
        exception_type  = exception.__class__.__name__,
        exception_value = exception.message
    )

def getConstantComputationReplacementNode( expression, computation ):
    # Try and turn raised exceptions into static raises. pylint: disable=W0703

    try:
        result = computation()
    except Exception as e:
        return makeRaiseExceptionReplacementExpressionFromInstance(
            expression = expression,
            exception  = e
        )
    else:
        return Nodes.makeConstantReplacementNode(
            constant = result,
            node     = expression
        )
