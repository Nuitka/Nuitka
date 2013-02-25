#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Base for all optimization modules

Provides a class that all optimization visitors should inherit from.
"""

# Pylint fails to find this, somewhat, at least it reports wrong about this.
from nuitka.tree import Operations

# pylint: disable=W0611
# These are here for easier import by the optimization steps.

from nuitka.nodes.NodeMakingHelpers import (
    makeRaiseExceptionReplacementExpressionFromInstance,
    makeRaiseExceptionReplacementStatement,
    makeBuiltinExceptionRefReplacementNode,
    makeBuiltinRefReplacementNode,
    makeConstantReplacementNode,
)

from nuitka.tree.Operations import RestartVisit, ExitVisit

from logging import warning, debug, info
# pylint: enable=W0611


class OptimizationVisitorBase( Operations.VisitorNoopMixin ):
    on_signal = None

    def signalChange( self, tags, source_ref, message ):
        """ Indicate a change to the optimization framework.

        """
        debug( "%s : %s : %s" % ( source_ref.getAsString(), tags, message ) )

        if self.on_signal is not None:
            self.on_signal( tags )

    def execute( self, tree, on_signal = None ):
        self.on_signal = on_signal

        Operations.visitScopes(
            tree    = tree,
            visitor = self
        )

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


def areConstants( expressions ):
    """ Check if all the expressions are in fact constants.

        This is a frequent pre-condition for optimizations.
    """

    for expression in expressions:
        if not expression.isExpressionConstantRef():
            return False
    else:
        return True
