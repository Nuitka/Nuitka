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
""" Operations on the tree.

This is mostly for the different kinds of visits that the node tree can have. You
can visit a scope, a tree (module), every scope of a tree (module) and the whole
forest of modules.

"""

class ExitNodeVisit( BaseException ):
    pass

class ExitVisit( BaseException ):
    pass

class RestartVisit( BaseException ):
    pass

def _visitTree( tree, visitor, limit_tag ):
    try:
        visitor.onEnterNode( tree )

        visit_children = True
    except ExitNodeVisit:
        visit_children = False

    if visit_children:
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


def visitScopes( tree, visitor ):
    class VisitEverything( VisitorNoopMixin ):
        def onEnterNode( self, node ):
            if node.hasTag( "closure_taker" ):
                visitor.onEnterScope( node )
                visitTree( node, visitor, "closure_taker" )
                visitor.onLeaveScope( node )

    _visitTree( tree, VisitEverything(), None )

def visitTagHaving( tree, visitor, tag ):
    class VisitEverything( VisitorNoopMixin ):
        def onEnterNode( self, node ):
            if node.hasTag( tag ):
                visitor.onEnterNode( node )

    _visitTree( tree, VisitEverything(), None )


class VisitorNoopMixin:
    def onEnterNode( self, node ):
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
