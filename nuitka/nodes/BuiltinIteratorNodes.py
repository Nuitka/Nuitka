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
    ExpressionBuiltinSingleArgBase,
    ExpressionChildrenHavingBase,
    StatementChildrenHavingBase
)

from .ValueFriends import ValueFriendBase

from .SideEffectNodes import ExpressionSideEffects

from nuitka.optimizations import BuiltinOptimization

from nuitka import Options


class ExpressionBuiltinLen( ExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_LEN"

    builtin_spec = BuiltinOptimization.builtin_len_spec

    def getIntegerValue( self ):
        return self.getValue().getIterationLength()

    def computeExpression( self, constraint_collection ):
        from .NodeMakingHelpers import makeConstantReplacementNode, wrapExpressionWithNodeSideEffects

        new_node, change_tags, change_desc = ExpressionBuiltinSingleArgBase.computeExpression(
            self,
            constraint_collection = constraint_collection
        )

        if new_node is self:
            arg_length = self.getIntegerValue()

            if arg_length is not None:
                change_tags = "new_constant"
                change_desc = "Predicted len argument"

                new_node = wrapExpressionWithNodeSideEffects(
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
        # Virtual method overload, where it's fixed by type, pylint: disable=R0201
        return True

    def isKnownToBeIterableAtMin( self, count ):
        if self.iter_length is None:
            self.iter_length = self.iterated.getIterationLength()

        return self.iter_length is not None and self.iter_length - self.consumed >= count

    def isKnownToBeIterableAtMax( self, count ):
        if self.iter_length is None:
            self.iter_length = self.iterated.getIterationLength()

        return self.iter_length is not None and self.iter_length - self.consumed <= count

    def getIterationNext( self ):
        # print self.iterated, self.consumed, self.iterated.getVisitableNodes()

        if self.iterated.canPredictIterationValues():
            result = self.iterated.getIterationValue( self.consumed )
        else:
            result = None

        self.consumed += 1

        return result

    def markAsUsed( self ):
        self.used = True

    def onRelease( self, constraint_collection ):
        # print "onRelease", self
        pass


class ExpressionBuiltinIter1( ExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_ITER1"

    def getValueFriend( self, constraint_collection ):
        return ValueFriendBuiltinIter1( self.getValue().getValueFriend( constraint_collection ) )

    def computeExpression( self, constraint_collection ):
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

    def getIterationLength( self ):
        return self.getValue().getIterationLength()

    def extractSideEffects( self ):
        # Iterator making is the side effect itself.
        if self.getValue().isCompileTimeConstant():
            return ()
        else:
            return ( self, )


    def mayHaveSideEffects( self ):
        if self.getValue().isCompileTimeConstant():
            return self.getValue().isKnownToBeIterable( None )

        return True


class ExpressionBuiltinNext1( ExpressionBuiltinSingleArgBase ):
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

    def computeExpression( self, constraint_collection ):
        # TODO: Enable below code once safer.
        if True or not Options.isExperimental():
            return self, None, None

        target = self.getValue().getValueFriend( constraint_collection )

        if target.isKnownToBeIterableAtMin( 1 ):
            value = target.getIterationNext()

            if value is not None:
                if value.isNode() and not self.parent.isStatementExpressionOnly():
                    # As a side effect, keep the iteration, later checks may depend on it,
                    # or if absent, optimizations will remove it.
                    if not self.parent.isExpressionSideEffects():
                        value = ExpressionSideEffects(
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


class ExpressionSpecialUnpack( ExpressionBuiltinNext1 ):
    kind = "EXPRESSION_SPECIAL_UNPACK"

    def __init__( self, value, count, source_ref ):
        ExpressionBuiltinNext1.__init__(
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
        result = ExpressionBuiltinNext1.getDetails( self )
        result[ "element_index" ] = self.getCount()

        return result

    def getCount( self ):
        return self.count


class StatementSpecialUnpackCheck( StatementChildrenHavingBase ):
    kind = "STATEMENT_SPECIAL_UNPACK_CHECK"

    named_children = ( "iterator", )

    def __init__( self, iterator, count, source_ref ):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "iterator" : iterator
            },
            source_ref = source_ref
        )

        self.count = count

    def getDetails( self ):
        return {
            "count" : self.getCount(),
        }

    def getCount( self ):
        return self.count

    getIterator = StatementChildrenHavingBase.childGetter( "iterator" )

    def computeStatement( self, constraint_collection ):
        constraint_collection.onExpression( self.getIterator() )
        iterator = self.getIterator()

        if iterator.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

            result = makeStatementExpressionOnlyReplacementNode(
                expression = iterator,
                node       = self
            )

            return result, "new_raise", "Explicit raise already raises implicitely building exception type"

        # Remove the check if it can be decided at compile time.
        if iterator.isKnownToBeIterableAtMax( 0 ):
            return None, "new_statements", "Determined iteration end check to be always true."

        return self, None, None


class ExpressionBuiltinIter2( ExpressionChildrenHavingBase ):
    kind = "EXPRESSION_BUILTIN_ITER2"

    named_children = ( "callable", "sentinel", )

    # Need to accept 'callable' keyword argument, that is just the API of iter,
    # pylint: disable=W0622

    def __init__( self, callable, sentinel, source_ref ):
        ExpressionChildrenHavingBase.__init__(
            self,
            values = {
                "callable" : callable,
                "sentinel" : sentinel,
            },
            source_ref = source_ref
        )

    getCallable = ExpressionChildrenHavingBase.childGetter( "callable" )
    getSentinel = ExpressionChildrenHavingBase.childGetter( "sentinel" )

    def computeExpression( self, constraint_collection ):
        # TODO: The "callable" should be investigated here, pylint: disable=W0613

        return self, None, None

    def isIteratorMaking( self ):
        return True


class ExpressionBuiltinNext2( ExpressionChildrenHavingBase ):
    kind = "EXPRESSION_BUILTIN_NEXT2"

    named_children = ( "iterator", "default", )

    def __init__( self, iterator, default, source_ref ):
        ExpressionChildrenHavingBase.__init__(
            self,
            values = {
                "iterator" : iterator,
                "default"  : default,
            },
            source_ref = source_ref
        )

    getIterator = ExpressionChildrenHavingBase.childGetter( "iterator" )
    getDefault = ExpressionChildrenHavingBase.childGetter( "default" )

    def computeExpression( self, constraint_collection ):
        # TODO: The "iterator" should be investigated here, pylint: disable=W0613

        return self, None, None
