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

from .ValueFriends import ValueFriendBase

from .SideEffectNode import CPythonExpressionSideEffects

from nuitka.transform.optimizations import BuiltinOptimization

from nuitka import Options


class CPythonExpressionBuiltinLen( CPythonExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_LEN"

    builtin_spec = BuiltinOptimization.builtin_len_spec

    def getIntegerValue( self, constraint_collection ):
        return self.getValue().getIterationLength( constraint_collection )

    def computeNode( self, constraint_collection ):
        from .NodeMakingHelpers import makeConstantReplacementNode, wrapExpressionWithSideEffects

        new_node, change_tags, change_desc = CPythonExpressionBuiltinSingleArgBase.computeNode(
            self,
            constraint_collection = constraint_collection
        )

        if new_node is self:
            arg_length = self.getIntegerValue( constraint_collection )

            if arg_length is not None:
                change_tags = "new_constant"
                change_desc = "Predicted len argument"

                new_node = wrapExpressionWithSideEffects(
                    new_node = makeConstantReplacementNode( arg_length, self ),
                    old_node = self.getValue()

                )

                if new_node.isExpressionSideEffects(): # false alarm pylint: disable=E1101
                    change_desc += " maintaining side effects"

        return new_node, change_tags, change_desc


class ValueFriendBuiltinIter1( ValueFriendBase ):
    def __init__( self, iterated ):
        ValueFriendBase.__init__( self )

        self.iterated = iterated
        self.iter_length = None
        self.consumed = 0

        self.used = False

    def __eq__( self, other ):
        if self.__class__ is not other.__class__:
            return False

        return self.iterated == other.iterated and self.consumed == other.consumed

    def mayProvideReference( self ):
        return True

    def isKnownToBeIterableAtMin( self, count, constraint_collection ):
        if self.iter_length is None:
            self.iter_length = self.iterated.getIterationLength(
                constraint_collection = constraint_collection
            )

        return self.iter_length is not None and self.iter_length - self.consumed >= count

    def isKnownToBeIterableAtMax( self, count, constraint_collection ):
        if self.iter_length is None:
            self.iter_length = self.iterated.getIterationLength(
                constraint_collection = constraint_collection
            )

        return self.iter_length is not None and self.iter_length - self.consumed <= count

    def getIterationNext( self, constraint_collection ):
        # print self.iterated, self.consumed, self.iterated.getVisitableNodes()

        if self.iterated.canPredictIterationValues( constraint_collection ):
            result = self.iterated.getIterationValue( self.consumed, constraint_collection )
        else:
            result = None

        self.consumed += 1

        return result

    def markAsUsed( self ):
        self.used = True

    def onRelease( self, constraint_collection ):
        # print "onRelease", self
        pass


class CPythonExpressionBuiltinIter1( CPythonExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_ITER1"

    def getValueFriend( self, constraint_collection ):
        return ValueFriendBuiltinIter1( self.getValue().getValueFriend( constraint_collection ) )

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

    def extractSideEffects( self ):
        # Iterator making is the side effect itself.
        if self.getValue().isCompileTimeConstant():
            return ()
        else:
            return ( self, )


    def mayHaveSideEffects( self, constraint_collection ):
        if self.getValue().isCompileTimeConstant():
            return self.getValue().isKnownToBeIterable( None )

        return None


class CPythonExpressionBuiltinNext1( CPythonExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_NEXT1"

    def getDetails( self ):
        return {
            "iter" : self.getValue()
        }

    def makeCloneAt( self, source_ref ):
        return self.__class__(
            value      = self.getValue(),
            source_ref = source_ref
        )

    def computeNode( self, constraint_collection ):
        if not Options.isExperimental():
            return self, None, None

        target = self.getValue().getValueFriend( constraint_collection )

        if target.isKnownToBeIterableAtMin( 1, constraint_collection ):
            value = target.getIterationNext( constraint_collection )

            if value is not None:
                if value.isNode() and not self.parent.isStatementExpressionOnly():
                    # As a side effect, keep the iteration, later checks may depend on it,
                    # or if absent, optimizations will remove it.
                    if not self.parent.isExpressionSideEffects():
                        value = CPythonExpressionSideEffects(
                            expression   = value.makeCloneAt(
                                source_ref = self.getSourceReference()
                            ),
                            side_effects = (
                                self.makeCloneAt(
                                    source_ref = self.getSourceReference()
                                ),
                            ),
                            source_ref   = self.getSourceReference()
                        )

                    return value, "new_expression", "Predicted next iteration result"
            else:
                assert False, target

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

    def makeCloneAt( self, source_ref ):
        return self.__class__(
            value      = self.getValue(),
            count      = self.getCount(),
            source_ref = source_ref
        )

    def getDetails( self ):
        result = CPythonExpressionBuiltinNext1.getDetails( self )
        result[ "element_index" ] = self.getCount()

        return result

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
