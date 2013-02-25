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
""" Assignment related nodes.

All kinds of assignment targets as well as the assignment statement and expression are
located here. These are the core of value control flow.

"""

from .NodeBases import (
    ExpressionChildrenHavingBase,
    ChildrenHavingMixin,
    NodeBase
)


class StatementAssignmentVariable( ChildrenHavingMixin, NodeBase ):
    kind = "STATEMENT_ASSIGNMENT_VARIABLE"

    named_children = ( "source", "variable_ref" )

    def __init__( self, variable_ref, source, source_ref ):
        assert variable_ref is not None, source_ref
        assert source is not None, source_ref

        assert not variable_ref.isExpressionVariableRef()

        NodeBase.__init__( self, source_ref = source_ref )

        ChildrenHavingMixin.__init__(
            self,
            values = {
                "source"       : source,
                "variable_ref" : variable_ref
            }
        )

    def getDetail( self ):
        return "%s from %s" % ( self.getTargetVariableRef(), self.getAssignSource() )

    getTargetVariableRef = ChildrenHavingMixin.childGetter( "variable_ref" )
    getAssignSource = ChildrenHavingMixin.childGetter( "source" )

    def mayRaiseException( self, exception_type ):
        return self.getAssignSource().mayRaiseException( exception_type )


class StatementAssignmentAttribute( ChildrenHavingMixin, NodeBase ):
    kind = "STATEMENT_ASSIGNMENT_ATTRIBUTE"

    named_children = ( "source", "expression" )

    def __init__( self, expression, attribute_name, source, source_ref ):
        NodeBase.__init__( self, source_ref = source_ref )

        ChildrenHavingMixin.__init__(
            self,
            values = {
                "expression" : expression,
                "source"     : source,
            }
        )

        self.attribute_name = attribute_name

    def getDetails( self ):
        return { "attribute" : self.attribute_name }

    def getDetail( self ):
        return "to attribute %s" % self.attribute_name

    def getAttributeName( self ):
        return self.attribute_name

    def setAttributeName( self, attribute_name ):
        self.attribute_name = attribute_name

    getLookupSource = ExpressionChildrenHavingBase.childGetter( "expression" )
    getAssignSource = ExpressionChildrenHavingBase.childGetter( "source" )

    def computeStatement( self, constraint_collection ):
        constraint_collection.onExpression( self.getAssignSource() )
        source = self.getAssignSource()

        # No assignment will occur, if the assignment source raises, so strip it away.
        if source.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

            return makeStatementExpressionOnlyReplacementNode(
                expression = source,
                node       = self
            )

        constraint_collection.onExpression( self.getLookupSource() )
        lookup_source = self.getLookupSource()

        if lookup_source.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            return makeStatementOnlyNodesFromExpressions(
                expressions = (
                    source,
                    lookup_source
                )
            )

        return self


class StatementAssignmentSubscript( ChildrenHavingMixin, NodeBase ):
    kind = "STATEMENT_ASSIGNMENT_SUBSCRIPT"

    named_children = ( "source", "expression", "subscript" )

    def __init__( self, expression, subscript, source, source_ref ):
        NodeBase.__init__( self, source_ref = source_ref )

        ChildrenHavingMixin.__init__(
            self,
            values     = {
                "source"     : source,
                "expression" : expression,
                "subscript"  : subscript
            }
        )

    getSubscribed = ExpressionChildrenHavingBase.childGetter( "expression" )
    getSubscript = ExpressionChildrenHavingBase.childGetter( "subscript" )
    getAssignSource = ExpressionChildrenHavingBase.childGetter( "source" )

    def computeStatement( self, constraint_collection ):
        constraint_collection.onExpression( self.getAssignSource() )
        source = self.getAssignSource()

        # No assignment will occur, if the assignment source raises, so strip it away.
        if source.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

            return makeStatementExpressionOnlyReplacementNode(
                expression = source,
                node       = self
            )

        constraint_collection.onExpression( self.getSubscribed() )
        subscribed = self.getSubscribed()

        if subscribed.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            return makeStatementOnlyNodesFromExpressions(
                expressions = (
                    source,
                    subscribed
                )
            )

        constraint_collection.onExpression( self.getSubscript() )
        subscript = self.getSubscript()

        if subscript.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            return makeStatementOnlyNodesFromExpressions(
                expressions = (
                    source,
                    subscribed,
                    subscript
                )
            )

        return self


class StatementAssignmentSlice( ChildrenHavingMixin, NodeBase ):
    kind = "STATEMENT_ASSIGNMENT_SLICE"

    named_children = ( "source", "expression", "lower", "upper" )

    def __init__( self, expression, lower, upper, source, source_ref ):
        NodeBase.__init__( self, source_ref = source_ref )

        ChildrenHavingMixin.__init__(
            self,
            values     = {
                "source"     : source,
                "expression" : expression,
                "lower"      : lower,
                "upper"      : upper
            }
        )

    getLookupSource = ExpressionChildrenHavingBase.childGetter( "expression" )
    getLower = ExpressionChildrenHavingBase.childGetter( "lower" )
    getUpper = ExpressionChildrenHavingBase.childGetter( "upper" )
    getAssignSource = ExpressionChildrenHavingBase.childGetter( "source" )

    def computeStatement( self, constraint_collection ):
        constraint_collection.onExpression( self.getAssignSource() )
        source = self.getAssignSource()

        # No assignment will occur, if the assignment source raises, so strip it away.
        if source.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

            return makeStatementExpressionOnlyReplacementNode(
                expression = source,
                node       = self
            )

        constraint_collection.onExpression( self.getLookupSource() )
        lookup_source = self.getLookupSource()

        if lookup_source.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            return makeStatementOnlyNodesFromExpressions(
                expressions = (
                    source,
                    lookup_source
                )
            )

        constraint_collection.onExpression( self.getLower(), allow_none = True )
        lower = self.getLower()

        if lower is not None and lower.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            return makeStatementOnlyNodesFromExpressions(
                expressions = (
                    source,
                    lookup_source,
                    lower
                )
            )

        constraint_collection.onExpression( self.getUpper(), allow_none = True )
        upper = self.getUpper()

        if upper is not None and upper.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            return makeStatementOnlyNodesFromExpressions(
                expressions = (
                    source,
                    lookup_source,
                    lower,
                    upper
                )
            )

        return self


class StatementDelVariable( ChildrenHavingMixin, NodeBase ):
    kind = "STATEMENT_DEL_VARIABLE"

    named_children = ( "variable_ref", )

    def __init__( self, variable_ref, tolerant, source_ref ):
        assert variable_ref is not None
        assert not variable_ref.isExpressionVariableRef()
        assert tolerant is True or tolerant is False

        NodeBase.__init__( self, source_ref = source_ref )

        ChildrenHavingMixin.__init__(
            self,
            values = {
                "variable_ref" : variable_ref
            }
        )

        self.tolerant = tolerant

    def getDetail( self ):
        variable_ref = self.getTargetVariableRef()
        variable = variable_ref.getVariable()

        if variable is not None:
            return "to variable %s" % variable
        else:
            return "to variable %s" % self.getTargetVariableRef()

    # TODO: Value propagation needs to make a difference based on this.
    def isTolerant( self ):
        return self.tolerant

    getTargetVariableRef = ChildrenHavingMixin.childGetter( "variable_ref" )


class StatementDelAttribute( ChildrenHavingMixin, NodeBase ):
    kind = "STATEMENT_DEL_ATTRIBUTE"

    named_children = ( "expression", )

    def __init__( self, expression, attribute_name, source_ref ):
        NodeBase.__init__( self, source_ref = source_ref )

        ChildrenHavingMixin.__init__(
            self,
            values = {
                "expression" : expression
            }
        )

        self.attribute_name = attribute_name

    def getDetails( self ):
        return { "attribute" : self.attribute_name }

    def getDetail( self ):
        return "to attribute %s" % self.attribute_name

    def getAttributeName( self ):
        return self.attribute_name

    def setAttributeName( self, attribute_name ):
        self.attribute_name = attribute_name

    getLookupSource = ExpressionChildrenHavingBase.childGetter( "expression" )

    def computeStatement( self, constraint_collection ):
        constraint_collection.onExpression( self.getLookupSource() )
        lookup_source = self.getLookupSource()

        if lookup_source.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

            return makeStatementExpressionOnlyReplacementNode(
                expression = lookup_source,
                node       = self
            )


        return self


class StatementDelSubscript( ChildrenHavingMixin, NodeBase ):
    kind = "STATEMENT_DEL_SUBSCRIPT"

    named_children = ( "expression", "subscript" )

    def __init__( self, expression, subscript, source_ref ):
        NodeBase.__init__( self, source_ref = source_ref )

        ChildrenHavingMixin.__init__(
            self,
            values     = {
                "expression" : expression,
                "subscript"  : subscript
            }
        )

    getSubscribed = ExpressionChildrenHavingBase.childGetter( "expression" )
    getSubscript = ExpressionChildrenHavingBase.childGetter( "subscript" )

    def computeStatement( self, constraint_collection ):
        constraint_collection.onExpression( self.getSubscribed() )
        subscribed = self.getSubscribed()

        if subscribed.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

            return makeStatementExpressionOnlyReplacementNode(
                expression = subscribed,
                node       = self
            )


        constraint_collection.onExpression( self.getSubscript() )
        subscript = self.getSubscript()

        if subscript.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            return makeStatementOnlyNodesFromExpressions(
                expressions = (
                    subscribed,
                    subscript
                )
            )

        return self


class StatementDelSlice( ChildrenHavingMixin, NodeBase ):
    kind = "STATEMENT_DEL_SLICE"

    named_children = ( "expression", "lower", "upper" )

    def __init__( self, expression, lower, upper, source_ref ):
        NodeBase.__init__( self, source_ref = source_ref )

        ChildrenHavingMixin.__init__(
            self,
            values     = {
                "expression" : expression,
                "lower"      : lower,
                "upper"      : upper
            }
        )

    getLookupSource = ExpressionChildrenHavingBase.childGetter( "expression" )
    getLower = ExpressionChildrenHavingBase.childGetter( "lower" )
    getUpper = ExpressionChildrenHavingBase.childGetter( "upper" )

    def computeStatement( self, constraint_collection ):
        constraint_collection.onExpression( self.getLookupSource() )
        lookup_source = self.getLookupSource()

        if lookup_source.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

            return makeStatementExpressionOnlyReplacementNode(
                expression = lookup_source,
                node       = self
            )

        constraint_collection.onExpression( self.getLower(), allow_none = True )
        lower = self.getLower()

        if lower is not None and lower.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            return makeStatementOnlyNodesFromExpressions(
                expressions = (
                    lookup_source,
                    lower
                )
            )

        constraint_collection.onExpression( self.getUpper(), allow_none = True )
        upper = self.getUpper()

        if upper is not None and upper.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            return makeStatementOnlyNodesFromExpressions(
                expressions = (
                    lookup_source,
                    lower,
                    upper
                )
            )

        return self
