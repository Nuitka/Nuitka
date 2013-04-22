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

    def onRelease( self, constraint_collection ):
        # print "onRelease", self
        pass

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
