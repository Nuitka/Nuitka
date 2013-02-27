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
""" Constraint collection

At the core of value propagation there is the collection of constraints that allow
to propagate knowledge forward or not. This is about collecting these constraints
and to manage them.

"""

# Python3 compatibility.
from nuitka.__past__ import iterItems

from nuitka.nodes import ValueFriends

from nuitka.nodes.NodeMakingHelpers import (
    makeStatementExpressionOnlyReplacementNode,
    makeStatementsSequenceReplacementNode,
)

from nuitka import Options, Utils, Importing
from nuitka.tree import Recursion

from logging import debug

class VariableUsageProfile:
    def __init__( self, variable ):
        self.variable = variable

        self.written_to = False
        self.read_from  = False

        # Indicator, if the variable may contain a reference.
        self.needs_free = False

    def markAsWrittenTo( self, value_friend ):
        self.written_to = True

        if value_friend.mayProvideReference():
            self.needs_free = True

    def markAsReadFrom( self ):
        self.read_from = True

    def isReadOnly( self ):
        return not self.written_to

    def isUnused( self ):
        return not self.written_to and not self.read_from

    def isWriteOnly( self ):
        return self.written_to and not self.read_from

    def setNeedsFree( self, needs_free ):
        assert needs_free is not None

        self.needs_free = needs_free

    def getNeedsFree( self ):
        return self.needs_free


class VariableUsageTrackingMixin:
    def __init__( self ):
        self.variable_usages = {}

    def _getVariableUsage( self, variable ):
        if variable in self.variable_usages:
            return self.variable_usages[ variable ]
        else:
            self.variable_usages[ variable ] = VariableUsageProfile( variable )

            return self.variable_usages[ variable ]

    def setIndications( self ):
        for variable, usage in iterItems( self.variable_usages ):
            if variable.isTempVariable():
                variable.setNeedsFree( usage.getNeedsFree() )

            if variable.isTempKeeperVariable():
                if usage.isWriteOnly():
                    variable.setWriteOnly()


# TODO: This code is only here while staging it, will live in a dedicated module later on
class ConstraintCollectionBase:
    def __init__( self, parent, signal_change = None, copy_of = None ):
        assert signal_change is None or parent is None

        if signal_change is not None:
            self.signalChange = signal_change
        else:
            self.signalChange = parent.signalChange

        self.parent = parent

        if copy_of is None:
            self.variables = {}
        else:
            assert copy_of.__class__ is ConstraintCollectionBase

            self.variables = dict( copy_of.variables )

    def mustAlias( self, a, b ):
        if a.isExpressionVariableRef() and b.isExpressionVariableRef():
            return a.getVariable() is b.getVariable()

        return False

    def mustNotAlias( self, a, b ):
        return False

    def removeKnowledge( self, value_friend ):
        to_remove = []

        for variable, value in iterItems( self.variables ):
            if value is value_friend:
                to_remove.append( variable )

        for remove in to_remove:
            del self.variables[ remove ]

    def removeAllKnowledge( self ):
        self.variables = {}

    @staticmethod
    def mergeBranchVariables( a, b ):
        result = {}

        for variable, value in iterItems( a ):
            if variable in b:
                merged = ValueFriends.mergeBranchFriendValues(
                    value,
                    b[ variable ]
                )

                if merged is not None:
                    result[ variable ] = merged
            else:
                pass

        return result

    def mergeBranch( self, other ):
        self.variables = self.mergeBranchVariables( self.variables, other.variables )

    def getVariableValueFriend( self, variable ):
        return self.variables.get( variable, None )

    def dump( self ):
        debug( "Constraint collection state:" )
        for variable_name, variable_info in sorted( iterItems( self.variables ) ):
            debug( "%r: %r", variable_name, variable_info )

    def _onStatementsFrame( self, statements_sequence ):
        assert statements_sequence.isStatementsFrame()

        new_statements = []

        statements = statements_sequence.getStatements()
        assert statements, statements_sequence

        for count, statement in enumerate( statements ):
            # May be frames embedded.
            if statement.isStatementsFrame():
                new_statement = self.onStatementsSequence( statement )
            else:
                new_statement = self.onStatement( statement )

            if new_statement is not None:
                if new_statement.isStatementsSequence() and not new_statement.isStatementsFrame():
                    new_statements.extend( new_statement.getStatements() )
                else:
                    new_statements.append( new_statement )

                if statement is not statements[-1] and new_statement.isStatementAborting():
                    self.signalChange(
                        "new_statements",
                        statements[ count + 1 ].getSourceReference(),
                        "Removed dead statements."
                    )

                    break

        if not new_statements:
            return None

        outside_pre = []

        while new_statements and not new_statements[0].mayRaiseException( BaseException ):
            outside_pre.append( new_statements[0] )
            del new_statements[0]

        outside_post = []

        while new_statements and not new_statements[-1].mayRaiseException( BaseException ):
            outside_post.insert( 0, new_statements[-1] )
            del new_statements[-1]

        if outside_pre or outside_post:
            if new_statements:
                statements_sequence.setStatements( tuple( new_statements ) )

                return makeStatementsSequenceReplacementNode(
                    statements = outside_pre + [ statements_sequence ] + outside_post,
                    node       = statements_sequence
                )
            else:
                return makeStatementsSequenceReplacementNode(
                    statements = outside_pre + outside_post,
                    node       = statements_sequence
                )
        else:
            if statements != new_statements:
                statements_sequence.setStatements( tuple( new_statements ) )

            return statements_sequence


    def onStatementsSequence( self, statements_sequence ):
        assert statements_sequence.isStatementsSequence()

        if statements_sequence.isStatementsFrame():
            return self._onStatementsFrame( statements_sequence )

        new_statements = []

        statements = statements_sequence.getStatements()
        assert statements, statements_sequence

        for count, statement in enumerate( statements ):
            # May be frames embedded.
            if statement.isStatementsFrame():
                new_statement = self.onStatementsSequence( statement )
            else:
                new_statement = self.onStatement( statement )

            if new_statement is not None:
                if new_statement.isStatementsSequence() and not new_statement.isStatementsFrame():
                    new_statements.extend( new_statement.getStatements() )
                else:
                    new_statements.append( new_statement )

                if statement is not statements[-1] and new_statement.isStatementAborting():
                    self.signalChange(
                        "new_statements",
                        statements[ count + 1 ].getSourceReference(),
                        "Removed dead statements."
                    )

                    break

        new_statements = tuple( new_statements )

        if statements != new_statements:
            if new_statements:
                statements_sequence.setStatements( new_statements )

                return statements_sequence
            else:
                return None
        else:
            return statements_sequence

    def onExpression( self, expression, allow_none = False ):
        if expression is None and allow_none:
            return

        assert expression.isExpression(), expression

        # print( "CONSIDER expression", expression )

        self.onSubExpressions( expression )

        r = expression.computeExpression( self )
        assert type(r) is tuple, expression

        new_node, change_tags, change_desc = expression.computeExpression( self )

        if new_node is not expression:
            # print expression, "->", new_node

            expression.replaceWith( new_node )

            self.signalChange(
                change_tags,
                expression.getSourceReference(),
                change_desc
            )

        if new_node.isExpressionVariableRef():
            if not new_node.getVariable().isModuleVariableReference():
                self.onLocalVariableRead( new_node.getVariable() )
        elif new_node.isExpressionAssignmentTempKeeper():
            variable = new_node.getVariable()
            assert variable is not None

            value_friend = new_node.getAssignSource().getValueFriend( self )
            assert value_friend is not None

            assert variable not in self.variables

            self.variables[ variable  ] = value_friend

            self.onTempVariableAssigned( variable, value_friend )
        elif new_node.isExpressionTempKeeperRef():
            variable = new_node.getVariable()
            assert variable is not None

            self.onTempVariableRead( variable )

        return new_node

    def onStatementUsingChildExpressions( self, statement ):
        self.onSubExpressions( statement )

        return statement

    def onSubExpressions( self, owner ):
        if owner.isExpressionFunctionRef():
            collector = ConstraintCollectionFunction( self )
            collector.process( owner.getFunctionBody() )
        elif owner.isExpressionFunctionBody():
            assert False, owner
        else:
            sub_expressions = owner.getVisitableNodes()

            for sub_expression in sub_expressions:
                self.onExpression( sub_expression )

    def onModuleVariableAssigned( self, variable, value_friend ):
        self.parent.onModuleVariableAssigned( variable, value_friend )

    def onLocalVariableAssigned( self, variable, value_friend ):
        self.parent.onLocalVariableAssigned( variable, value_friend )

    def onLocalVariableRead( self, variable ):
        self.parent.onLocalVariableRead( variable )

    def onTempVariableAssigned( self, variable, value_friend ):
        self.parent.onTempVariableAssigned( variable, value_friend )

    def onTempVariableRead( self, variable ):
        self.parent.onTempVariableRead( variable )

    def _onStatementAssignmentVariable( self, statement ):
        # Assignment source may re-compute here:
        self.onExpression( statement.getAssignSource() )

        # But now it cannot re-compute anymore:
        source = statement.getAssignSource()

        if source.willRaiseException( BaseException ):
            return makeStatementExpressionOnlyReplacementNode(
                expression = source,
                node       = statement
            )

        variable_ref = statement.getTargetVariableRef()
        variable = variable_ref.getVariable()

        assert variable is not None

        # Assigning from and to the same variable, can be optimized away immediately,
        # there is no point in doing it. Exceptions are of course module variables
        # that collide with builtin names.
        if not variable.isModuleVariableReference() and \
             source.isExpressionVariableRef() and \
             source.getVariable() == variable:
            if source.mayHaveSideEffects( self ):
                self.signalChange(
                    "new_statements",
                    statement.getSourceReference(),
                    "Reduced assignment of variable from itself to access of it."
                )

                return makeStatementExpressionOnlyReplacementNode(
                    expression = source,
                    node       = statement
                )
            else:
                self.signalChange(
                    "new_statements",
                    statement.getSourceReference(),
                    "Removed assignment of variable from itself which is known to be defined."
                )

                return None

        # If the assignment source has side effects, we can simply evaluate them
        # beforehand, we have already visited and evaluated them before.
        if source.isExpressionSideEffects():
            statements = [
                makeStatementExpressionOnlyReplacementNode(
                    side_effect,
                    statement
                )
                for side_effect in
                source.getSideEffects()
            ]

            statements.append( statement )

            result = makeStatementsSequenceReplacementNode(
                statements = statements,
                node       = statement,
            )

            source.replaceWith( source.getExpression() )

            # Need to update it.
            source = statement.getAssignSource()

            self.signalChange(
                "new_statements",
                statement.getSourceReference(),
                "Side effects of assignments promoted to statements."
            )
        else:
            result = statement

        value_friend = source.getValueFriend( self )
        assert value_friend is not None

        if variable in self.variables:
            old_value_friend = self.variables[ variable  ]
        else:
            old_value_friend = None

        self.variables[ variable  ] = value_friend

        if variable.isModuleVariableReference():
            self.onModuleVariableAssigned( variable, value_friend )
        elif variable.isLocalVariable():
            self.onLocalVariableAssigned( variable, value_friend )
        elif variable.isTempVariableReference():
            self.onTempVariableAssigned( variable, value_friend )

        if old_value_friend is not None:
            old_value_friend.onRelease( self )

        return result


    def onStatement( self, statement ):
        assert statement.isStatement(), statement

        if hasattr( statement, "computeStatement" ):
            new_statement, change_tags, change_desc = statement.computeStatement( self )

            if new_statement is not statement:
                self.signalChange(
                    change_tags,
                    statement.getSourceReference(),
                    change_desc
                )

            return new_statement

        elif statement.isStatementAssignmentVariable():
            return self._onStatementAssignmentVariable( statement )
        elif statement.isStatementDelVariable():
            variable = statement.getTargetVariableRef()

            if variable in self.variables:
                self.variables[ variable ].onRelease( self )

                del self.variables[ variable ]

            return statement
        elif statement.isStatementLoop():
            other_loop_run = ConstraintCollectionLoopOther( self )
            other_loop_run.process( self, statement )

            self.mergeBranch(
                other_loop_run
            )

            return statement
        else:
            assert False, statement


class ConstraintCollectionHandler( ConstraintCollectionBase ):
    def process( self, handler ):
        assert handler.isStatementExceptHandler()

        # TODO: The exception type and name could be assigned.
        branch = handler.getExceptionBranch()

        if branch is not None:
            result = self.onStatementsSequence( branch )

            if result is not branch:
                handler.setExceptionBranch( result )

        exception_types = handler.getExceptionTypes()

        if exception_types is not None:
            for exception_type in exception_types:
                self.onExpression( exception_type )


class ConstraintCollectionBranch( ConstraintCollectionBase ):
    def process( self, branch ):
        assert branch.isStatementsSequence(), branch

        result = self.onStatementsSequence( branch )

        if result is not branch:
            branch.replaceWith( result )


class ConstraintCollectionFunction( ConstraintCollectionBase, VariableUsageTrackingMixin ):
    def __init__( self, parent ):
        ConstraintCollectionBase.__init__(
            self,
            parent = parent
        )

        VariableUsageTrackingMixin.__init__( self )

        self.function_body = None

    def process( self, function_body ):
        assert function_body.isExpressionFunctionBody()
        self.function_body = function_body

        statements_sequence = function_body.getBody()

        if statements_sequence is not None:
            result = self.onStatementsSequence( statements_sequence )

            if result is not statements_sequence:
                function_body.setBody( result )

        self.setIndications()

    def onLocalVariableAssigned( self, variable, value_friend ):
        self._getVariableUsage( variable ).markAsWrittenTo( value_friend )

    def onLocalVariableRead( self, variable ):
        self._getVariableUsage( variable ).markAsReadFrom()

    def onTempVariableAssigned( self, variable, value_friend ):
        variable = variable.getReferenced()

        assert variable.getRealOwner() is self.function_body, variable.getOwner()

        self._getVariableUsage( variable ).markAsWrittenTo( value_friend )

    def onTempVariableRead( self, variable ):
        variable = variable.getReferenced()

        self._getVariableUsage( variable ).markAsReadFrom()



class ConstraintCollectionModule( ConstraintCollectionBase, VariableUsageTrackingMixin ):
    def __init__( self, signal_change ):
        ConstraintCollectionBase.__init__(
            self,
            None,
            signal_change = signal_change )

        VariableUsageTrackingMixin.__init__( self )

        self.module = None

    def process( self, module ):
        assert module.isPythonModule()
        self.module = module

        module_body = module.getBody()

        if module_body is not None:
            result = self.onStatementsSequence( module_body )

            if result is not module_body:
                module.setBody( result )

        self.setIndications()

        self.attemptRecursion( module )

    def attemptRecursion( self, module ):
        if not Options.shallMakeModule():
            # Make sure the package is recursed to.
            module_package = module.getPackage()

            if module_package is not None:
                package_package, _package_module_name, package_filename = Importing.findModule(
                    source_ref     = module.getSourceReference(),
                    module_name    = module_package,
                    parent_package = None,
                    level          = 1
                )

                imported_module, added_flag = Recursion.recurseTo(
                    module_package  = package_package,
                    module_filename = package_filename,
                    module_relpath  = Utils.relpath( package_filename )
                )

                if added_flag:
                    self.signalChange(
                        "new_code",
                        imported_module.getSourceReference(),
                        "Recursed to module package."
                    )

    def onModuleVariableAssigned( self, variable, value_friend ):
        while variable.isModuleVariableReference():
            variable = variable.getReferenced()

        self._getVariableUsage( variable ).markAsWrittenTo( value_friend )

    def onTempVariableAssigned( self, variable, value_friend ):
        variable = variable.getReferenced()

        assert variable.getRealOwner() is self.module, variable.getOwner()

        self._getVariableUsage( variable ).markAsWrittenTo( value_friend )

    def onTempVariableRead( self, variable ):
        variable = variable.getReferenced()

        assert variable.getRealOwner() is self.module, variable.getOwner()

        self._getVariableUsage( variable ).markAsReadFrom()


    def getWrittenVariables( self ):
        return [
            variable
            for variable, usage in iterItems( self.variable_usages )
            if not usage.isReadOnly()
        ]


class ConstraintCollectionLoopOther( ConstraintCollectionBase ):
    def process( self, start_state, loop ):
        # TODO: Somehow should copy that start state over, assuming nothing won't be wrong
        # for a start.
        self.start_state = start_state

        assert loop.isStatementLoop()

        loop_body = loop.getLoopBody()

        if loop_body is not None:
            result = self.onStatementsSequence( loop_body )

            if result is not loop_body:
                loop_body.replaceWith( result )
