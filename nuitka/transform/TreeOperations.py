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
""" Operations on the tree.

This is mostly for the different kinds of visits that the node tree can have. You
can visit a scope, a tree (module), every scope of a tree (module) and the whole
forest of modules.

"""

class ExitVisit( BaseException ):
    pass

class RestartVisit( BaseException ):
    pass

def _visitTree( tree, visitor, limit_tag ):
    visitor( tree )

    for visitable in tree.getChildNodesNotTagged( limit_tag ):
        if visitable is None:
            raise AssertionError( "'None' child encountered", tree, tree.source_ref )

        _visitTree( visitable, visitor, limit_tag )

    visitor.onLeaveNode( tree )

def visitTree( tree, visitor, limit_tag = None ):
    try:
        _visitTree( tree, visitor, limit_tag )
    except ExitVisit:
        pass
    except RestartVisit:
        visitTree( tree, visitor, limit_tag )

def visitScope( tree, visitor ):
    visitTree( tree, visitor, "closure_taker" )

def visitExecution( tree, visitor ):
    visitTree( tree, visitor, "execution_border" )

def visitScopes( tree, visitor ):
    def visitEverything( node ):
        if node.hasTag( "closure_taker" ):
            visitor.onEnterScope( node )
            visitTree( node, visitor, "closure_taker" )
            visitor.onLeaveScope( node )

    visitEverything.onLeaveNode = lambda tree: None

    _visitTree( tree, visitEverything, None )

def visitExecutions( tree, visitor ):
    def visitEverything( node ):
        if node.hasTag( "closure_taker" ):
            visitor.onEnterScope( node )
            visitTree( tree, visitor, "execution_border" )
            visitor.onLeaveScope( node )
        elif node.hasTag( "execution_border" ):
            visitor.onEnterExecutionBorder( node )
            visitTree( tree, visitor, "execution_border" )
            visitor.onLeaveExecutionBorder( node )

    visitEverything.onLeaveNode = lambda tree: None

    _visitTree( tree, visitEverything, None )

def visitTagHaving( tree, visitor, tag ):
    def visitEverything( node ):
        if node.hasTag( tag ):
            visitor( node )

    visitEverything.onLeaveNode = lambda tree: None

    _visitTree( tree, visitEverything, None )


class VisitorNoopMixin:
    # TODO: Rename this one day to onEnterNode, the functor approach makes no sense really.
    def __call__( self, node ):
        """ To be optionally overloaded for operation before the node children were done. """
        pass

    def onLeaveNode( self, node ):
        """ To be optionally overloaded for operation after the node children were done. """
        pass

    # Only for "scope" and "execution" visits.
    def onEnterScope( self, tree ):
        """ To be optionally overloaded for per-scope entry tasks. """
        pass

    def onLeaveScope( self, tree ):
        """ To be optionally overloaded for per-scope exit tasks. """
        pass
