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
""" Builtin iterator nodes.

These play a role in for loops, and in unpacking. They can something be predicted to
succeed or fail, in which case, code can become less complex. The length of things is an
important optimization issue.
"""

from .NodeBases import (
    CPythonExpressionBuiltinSingleArgBase,
    CPythonExpressionChildrenHavingBase,
    CPythonChildrenHaving,
    CPythonNodeBase
)

from .NodeMakingHelpers import makeConstantReplacementNode

from nuitka.transform.optimizations import BuiltinOptimization

class CPythonExpressionBuiltinLen( CPythonExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_LEN"

    builtin_spec = BuiltinOptimization.builtin_len_spec

    def computeNode( self, constraint_collection ):
        new_node, change_tags, change_desc = CPythonExpressionBuiltinSingleArgBase.computeNode(
            self,
            constraint_collection = constraint_collection
        )

        if new_node is self:
            arg_length = self.getValue().getIterationLength( constraint_collection )

            if arg_length is not None:
                # TODO: Need to ask it to preserve side-effects, from e.g. a function
                # call.
                new_node = makeConstantReplacementNode( arg_length, self )
                change_tags = "new_constant"
                change_desc = "Predicted len argument"


        return new_node, change_tags, change_desc



class CPythonExpressionBuiltinIter1( CPythonExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_ITER1"

    def computeNode( self, constraint_collection ):
        value = self.getValue()

        if value.isIteratorMaking():
            return value, "new_builtin", "Eliminated useless iterator creation"
        else:
            return self, None, None

    def isIteratorMaking( self ):
        return True

    def isKnownToBeIterable( self, count ):
        if count is None:
            return True

        # TODO: Should ask value if it is.
        return None

    def getIterationLength( self, constraint_collection ):
        return self.getValue().getIterationLength( constraint_collection )


class CPythonExpressionBuiltinNext1( CPythonExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_NEXT1"

    def computeNode( self, constraint_collection ):
        return self, None, None


class CPythonExpressionSpecialUnpack( CPythonExpressionBuiltinNext1 ):
    kind = "EXPRESSION_SPECIAL_UNPACK"

    def __init__( self, value, count, source_ref ):
        CPythonExpressionBuiltinNext1.__init__(
            self,
            value      = value,
            source_ref = source_ref
        )

        self.count = count

    def getDetails( self ):
        return {
            "count" : self.getCount(),
        }

    def getCount( self ):
        return self.count


class CPythonStatementSpecialUnpackCheck( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_SPECIAL_UNPACK_CHECK"

    named_children = ( "iterator", )

    def __init__( self, iterator, count, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "iterator" : iterator
            }
        )

        self.count = count

    def getDetails( self ):
        return {
            "count" : self.getCount(),
        }

    def getCount( self ):
        return self.count

    getIterator = CPythonExpressionChildrenHavingBase.childGetter( "iterator" )

class CPythonExpressionBuiltinIter2( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_BUILTIN_ITER2"

    named_children = ( "callable", "sentinel", )

    def __init__( self, call_able, sentinel, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values = {
                "callable" : call_able,
                "sentinel" : sentinel,
            },
            source_ref = source_ref
        )

    getCallable = CPythonExpressionChildrenHavingBase.childGetter( "callable" )
    getSentinel = CPythonExpressionChildrenHavingBase.childGetter( "sentinel" )

    def computeNode( self, constraint_collection ):
        return self, None, None

    def isIteratorMaking( self ):
        return True


class CPythonExpressionBuiltinNext2( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_BUILTIN_NEXT2"

    named_children = ( "iterator", "default", )

    def __init__( self, iterator, default, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values = {
                "iterator" : iterator,
                "default"  : default,
            },
            source_ref = source_ref
        )

    getIterator = CPythonExpressionChildrenHavingBase.childGetter( "iterator" )
    getDefault = CPythonExpressionChildrenHavingBase.childGetter( "default" )

    def computeNode( self, constraint_collection ):
        return self, None, None
