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
""" Friends of values represent complete or partial knowledge about data flow.

The friends are used during optimization of the tree to express the more or less
concrete knowledge about an expressions value.
"""

class ValueFriendBase( object ):
    def __init__( self ):
        pass

    def isNode( self ):
        # Virtual method, pylint: disable=R0201

        # ValueFriends are not nodes, this function exists in nodes too and is used only
        # to make this difference.
        return False

    def __eq__( self, other ):
        raise AssertionError( self, other )

    def isKnownToBeIterable( self, count ):
        # Virtual method, pylint: disable=R0201,W0613
        return None

    def isBuiltinNameRef( self ):
        # Virtual method, pylint: disable=R0201
        return False


class ValueFriendChooseOne( ValueFriendBase ):
    def __init__( self, *choices ):
        assert choices
        assert type( choices ) is tuple

        self.choices = choices

        ValueFriendBase.__init__( self )

    def mayHaveSideEffects( self ):
        for choice in self.choices:
            if choice.mayHaveSideEffects():
                return True
        else:
            return False

    def makeCloneAt( self, source_ref ):
        choices = tuple(
            choice.makeCloneAt( source_ref )
            for choice in
            self.choices
        )

        return self.__class__( *choices ) # That is the interface, pylint: disable=W0142

    def __repr__( self ):
        return "<%s instance of choices '%r'>" % (
            self.__class__.__name__,
            self.choices
        )

    def __eq__( self, other ):
        for choice in self.choices:
            if choice != other:
                return False
        else:
            return True


current_constraint_collection = None

def mergeBranchFriendValues( a, b ):
    # The real quick path
    if a is b:
        return a

    # The somewhat slower path, compare a and b, if equal, we can pick one.
    if a == b:
        return a

    # Otherwise represent the choosing of one branch in a value friend.
    return ValueFriendChooseOne( a, b )
