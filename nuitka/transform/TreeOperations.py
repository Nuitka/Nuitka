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

def _visitTree( tree, visitor ):
    visitor( tree )

    for visitable in tree.getVisitableNodes():
        if visitable is None:
            raise AssertionError( "none child encountered", tree, tree.source_ref )

        _visitTree( visitable, visitor )

def visitTree( tree, visitor ):
    try:
        _visitTree( tree, visitor )
    except ExitVisit:
        pass
    except RestartVisit:
        visitTree( tree, visitor )


def _visitScope( tree, visitor ):
    visitor( tree )

    for visitable in tree.getSameScopeNodes():
        if visitable is None:
            raise AssertionError( "none child encountered", tree, tree.source_ref )

        _visitScope( visitable, visitor )

    visitor.leaveNode( tree )

def visitScope( tree, visitor ):
    visitor.enterScope( tree )

    try:
        _visitScope( tree, visitor )
    except ExitVisit:
        pass
    except RestartVisit:
        visitScope( tree, visitor )

    visitor.leaveScope( tree )


def visitKinds( tree, kinds, visitor ):
    def visitMatchingKinds( node ):
        if node.kind in kinds:
            visitor( node )

    _visitTree( tree, visitMatchingKinds )

def visitScopes( tree, visitor ):
    def visitEverything( node ):
        if node.isClosureVariableTaker():
            visitScope( node, visitor )

    _visitTree( tree, visitEverything )

class ScopeVisitorNoopMixin:
    def enterScope( self, tree ):
        """ To be optionally overloaded for per-scope entry tasks. """
        pass

    def leaveScope( self, tree ):
        """ To be optionally overloaded for per-scope exit tasks. """
        pass

    # TODO: Rename this one day, the functor approach makes
    def __call__( self, node ):
        """ To be optionally overloaded for operation before the node children were done. """
        pass

    def leaveNode( self, node ):
        """ To be optionally overloaded for operation after the node children were done. """
        pass
