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

def visitScope( tree, visitor ):
    try:
        _visitScope( tree, visitor )
    except ExitVisit:
        pass
    except RestartVisit:
        visitTree( tree, visitor )


class _TreeVisitorAssignParent:
    def __call__( self, node ):
        for child in node.getVisitableNodes():
            if child is None:
                raise AssertionError( "none child encountered", node, node.source_ref )

            try:
                child.parent = node
            except AttributeError:
                raise AssertionError( "strange child encountered", node, node.source_ref, child )

def assignParent( tree ):
    visitTree( tree, _TreeVisitorAssignParent() )
