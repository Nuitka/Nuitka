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
    makeStatementsSequenceReplacementNode
)

from nuitka import Options, Utils, TreeRecursion, Importing, Builtins

from logging import debug

class VariableUsageProfile:
    def __init__( self, variable ):
        self.variable = variable

        self.read_only = True
        self.needs_free = False

    def markAsWrittenTo( self, value_friend ):
        self.read_only = False

        # TODO: check for "may provide a reference"
        if value_friend.mayProvideReference():
            self.needs_free = True

    def isReadOnly( self ):
        return self.read_only

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

    def setTempNeedsFreeIndications( self ):
        for variable, usage in iterItems( self.variable_usages ):
            if variable.isTempVariable():
                variable.setNeedsFree( usage.getNeedsFree() )

# TODO: This code is only here while staging it, will live in a dedicated module later on
class ConstraintCollectionBase:
    def __init__( self, parent, signal_change, copy_of = None ):
        self.signalChange = signal_change
        self.parent = parent

        if copy_of is None:
            self.variables = {}
        else:
            assert copy_of.__class__ is ConstraintCollectionBase

            self.variables = dict( copy_of.variables )

    def removeKnowledge( self, value_friend ):
        to_remove = []

        for variable, value in iterItems( self.variables ):
            if value is value_friend:
                to_remove.append( variable )

        for remove in to_remove:
            self.variables[ remove ]

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

    def onClosureTaker( self, closure_taker ):
        if closure_taker.isExpressionFunctionBody():
            collector = ConstraintCollectionFunction( self, self.signalChange )
        elif closure_taker.isExpressionClassBody():
            collector = ConstraintCollectionClass( self, self.signalChange )
        else:
            assert False, closure_taker

        collector.process( closure_taker )

    def onStatementsSequence( self, statements_sequence ):
        assert statements_sequence.isStatementsSequence()

        new_statements = []

        statements = statements_sequence.getStatements()
        assert statements, statements_sequence

        for count, statement in enumerate( statements ):
            new_statement = self.onStatement( statement )

            if new_statement is not None:
                if new_statement.isStatementsSequence():
                    new_statements.extend( new_statement.getStatements() )
                else:
                    new_statements.append( new_statement )

                if statement is not statements[-1] and new_statement.isStatementAbortative():
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
            else:
                statements_sequence.replaceWith( None )

    def onExpression( self, expression, allow_none = False ):
        if expression is None and allow_none:
            return

        assert expression.isExpression(), expression

        # print( "CONSIDER expression", expression )

        self.onSubExpressions( expression )

        new_node, change_tags, change_desc = expression.computeNode( self )

        if new_node is not expression:
            expression.replaceWith( new_node )

            self.signalChange(
                change_tags,
                expression.getSourceReference(),
                change_desc
            )

        return new_node

    def onStatementUsingChildExpressions( self, statement ):
        self.onSubExpressions( statement )

        return statement

    def onSubExpressions( self, owner ):
        if not owner.hasTag( "closure_taker" ):
            sub_expressions = owner.getVisitableNodes()

            for sub_expression in sub_expressions:
                self.onExpression( sub_expression )
        else:
            self.onClosureTaker( owner )

    def _onStatementConditional( self, statement ):
        no_branch = statement.getBranchNo()

        if no_branch is not None and not no_branch.mayHaveSideEffects( None ):
            self.signalChange(
                "new_statements",
                no_branch.getSourceReference(),
                "Removed else branch without side effects."
            )

            statement.setBranchNo( None )

            no_branch = None

        yes_branch = statement.getBranchYes()

        if yes_branch is not None and not yes_branch.mayHaveSideEffects( None ):
            statement.setBranchYes( None )

            self.signalChange(
                "new_statements",
                yes_branch.getSourceReference(),
                "Removed else branch without side effects."
            )

            yes_branch = None

        self.onExpression( statement.getCondition() )

        # TODO: We now know that condition evaluates to true for the yes branch
        # and to not true for no branch

        branch_yes_collection = ConstraintCollectionBranch( self, self.signalChange )

        if yes_branch is not None:
            branch_yes_collection.process( self, yes_branch )

        if no_branch is not None:
            branch_no_collection = ConstraintCollectionBranch( self, self.signalChange )

            branch_no_collection.process( self, statement.getBranchNo() )

            self.variables = self.mergeBranchVariables(
                branch_yes_collection.variables,
                branch_no_collection.variables
            )
        else:
            self.mergeBranch( branch_yes_collection )

        if statement.getBranchNo() is None and statement.getBranchYes() is None:
            self.signalChange(
                "new_statements",
                statement.getSourceReference(),
                "Both branches have no effect, drop branch nature, only evaluate condition."
            )

            return makeStatementExpressionOnlyReplacementNode(
                expression = statement.getCondition(),
                node       = statement
            )
        elif statement.getCondition().isCompileTimeConstant():
            if statement.getCondition().getCompileTimeConstant():
                choice = "true"

                new_statement = statement.getBranchYes()
            else:
                choice = "false"

                new_statement = statement.getBranchNo()

            self.signalChange(
                "new_statements",
                statement.getSourceReference(),
                "Condition for branch was predicted to be always %s." % choice
            )

            return new_statement

        return statement

    def onModuleVariableAssigned( self, variable, value_friend ):
        self.parent.onModuleVariableAssigned( variable, value_friend )

    def onLocalVariableAssigned( self, variable, value_friend ):
        self.parent.onLocalVariableAssigned( variable, value_friend )

    def onTempVariableAssigned( self, variable, value_friend ):
        self.parent.onTempVariableAssigned( variable, value_friend )

    def onStatement( self, statement ):
        assert statement.isStatement(), statement

        if statement.isStatementAssignmentVariable():
            self.onExpression( statement.getAssignSource() )

            variable_ref = statement.getTargetVariableRef()
            variable = variable_ref.getVariable()

            # Assigning from and to the same variable, can be optimized away immediately,
            # there is no point in doing it. Exceptions are of course module variables
            # that collide with builtin names.
            if statement.getAssignSource().isExpressionVariableRef() and \
                 statement.getAssignSource().getVariable() == variable and \
                 not variable.isModuleVariableReference():
                if statement.getAssignSource().mayHaveSideEffects( self ):
                    self.signalChange(
                        "new_statements",
                        statement.getSourceReference(),
                        "Reduced assignment of variable from itself to access of it."
                    )

                    return makeStatementExpressionOnlyReplacementNode(
                        expression = statement.getAssignSource(),
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
            if statement.getAssignSource().isExpressionSideEffects():
                statements = [
                    makeStatementExpressionOnlyReplacementNode(
                        side_effect,
                        statement
                    )
                    for side_effect in
                    statement.getAssignSource().getSideEffects()
                ]

                statements.append( statement )

                result = makeStatementsSequenceReplacementNode(
                    statements = statements,
                    node       = statement,
                )

                statement.getAssignSource().replaceWith( statement.getAssignSource().getExpression() )

                self.signalChange(
                    "new_statements",
                    statement.getSourceReference(),
                    "Side effects of assignments promoted to statements."
                )
            else:
                result = statement

            value_friend = statement.getAssignSource().getValueFriend( self )
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
        elif statement.isStatementAssignmentAttribute():
            self.onExpression( statement.getAssignSource() )

            self.onExpression( statement.getLookupSource() )

            return statement
        elif statement.isStatementAssignmentSubscript():
            self.onExpression( statement.getAssignSource() )

            self.onExpression( statement.getSubscribed() )
            self.onExpression( statement.getSubscript() )

            return statement
        elif statement.isStatementAssignmentSlice():
            self.onExpression( statement.getAssignSource() )

            self.onExpression( statement.getLookupSource() )
            self.onExpression( statement.getLower(), allow_none = True )
            self.onExpression( statement.getUpper(), allow_none = True )

            return statement
        elif statement.isStatementDelVariable():
            variable = statement.getTargetVariableRef()

            if variable in self.variables:
                self.variables[ variable ].onRelease( self )

                del self.variables[ variable ]

            return statement
        elif statement.isStatementDelAttribute():
            self.onExpression( statement.getLookupSource() )

            return statement
        elif statement.isStatementDelSubscript():
            self.onExpression( statement.getSubscribed() )
            self.onExpression( statement.getSubscript() )

            return statement
        elif statement.isStatementDelSlice():
            self.onExpression( statement.getLookupSource() )
            self.onExpression( statement.getLower(), allow_none = True )
            self.onExpression( statement.getUpper(), allow_none = True )

            return statement
        elif statement.isStatementExpressionOnly():
            expression = statement.getExpression()

            # Workaround for possibilty of generating a statement here.
            if expression.isStatement():
                return self.onStatement( expression )
            elif expression.isExpressionSideEffects():
                assert False, expression
            else:
                self.onExpression( expression )

                if statement.mayHaveSideEffects( self ):
                    return statement
                else:
                    return None
        elif statement.isStatementPrint():
            return self.onStatementUsingChildExpressions( statement )
        elif statement.isStatementReturn():
            # TODO: The merging will need to consider if merged branches really can exit
            # or not.
            return self.onStatementUsingChildExpressions( statement )
        elif statement.isStatementRaiseException():
            return self.onStatementUsingChildExpressions( statement )
        elif statement.isStatementExec():
            return self.onStatementUsingChildExpressions( statement )
        elif statement.isStatementConditional():
            return self._onStatementConditional( statement )
        elif statement.isStatementLoop():
            other_loop_run = ConstraintCollectionLoopOther( self, self.signalChange )
            other_loop_run.process( self, statement )

            self.mergeBranch(
                other_loop_run
            )

            return statement
        elif statement.isStatementTryFinally():
            # The tried block can be processed normally, if it is not empty already.
            tried_statement_sequence = statement.getBlockTry()

            if tried_statement_sequence is not None:
                self.onStatementsSequence( tried_statement_sequence )

            final_statement_sequence = statement.getBlockFinal()

            # TODO: The final must not assume that all of final was executed, instead it
            # may have aborted after any part of it, which is a rather complex definition.

            if final_statement_sequence is not None:
                # Then assuming no exception, the no raise block if present.
                self.onStatementsSequence( final_statement_sequence )

            # Note: Need to query again, because the object may have changed in the
            # "onStatementsSequence" calls.

            if statement.getBlockTry() is None:
                # If the tried block is empty, go to the final block directly, if any.
                result = statement.getBlockFinal()
            elif statement.getBlockFinal() is None:
                # If the final block is empty, just need to execute the tried block then.
                result = statement.getBlockTry()
            else:
                # Otherwise keep it as it.
                result = statement

            return result
        elif statement.isStatementTryExcept():
            # The tried block can be processed normally.
            tried_statement_sequence = statement.getBlockTry()

            if tried_statement_sequence is not None:
                self.onStatementsSequence( tried_statement_sequence )

            # The exception branches triggers in unknown state, any amount of tried code
            # may have happened. A similar approach to loops should be taken to invalidate
            # the state before.
            for handler in statement.getExceptionHandlers():
                exception_branch = ConstraintCollectionHandler( self, self.signalChange )
                exception_branch.process( handler )

            # Give up, merging this is too hard for now.
            self.variables = {}

            if statement.getBlockTry() is None:
                return None
            else:
                return statement
        elif statement.isStatementImportStar():
            # TODO: Need to invalidate everything, and everything could be assigned now.
            return self.onStatementUsingChildExpressions( statement )
        elif statement.isStatementContinueLoop():
            # TODO: Not clear how to handle these, the statement sequence processing
            # should abort here.
            return statement
        elif statement.isStatementBreakLoop():
            # TODO: Not clear how to handle these, the statement sequence processing
            # should abort here.
            return statement
        elif statement.isStatementTempBlock():
            self.onStatementsSequence( statement.getBody() )

            return statement
        elif statement.isStatementSpecialUnpackCheck():
            self.onExpression( statement.getIterator() )

            # Remove the check if it can be decided at compile time.
            if statement.getIterator().isKnownToBeIterableAtMax( 0, self ):
                return None

            return statement
        else:
            assert False, statement


class ConstraintCollectionHandler( ConstraintCollectionBase ):
    def process( self, handler ):
        assert handler.isStatementExceptHandler()

        # TODO: The exception type and name could be assigned.
        branch = handler.getExceptionBranch()

        if branch is not None:
            self.onStatementsSequence( branch )

        exception_types = handler.getExceptionTypes()

        if exception_types is not None:
            for exception_type in exception_types:
                self.onExpression( exception_type )


class ConstraintCollectionBranch( ConstraintCollectionBase ):
    def process( self, start_state, branch ):
        assert branch.isStatementsSequence(), branch

        self.onStatementsSequence( branch )


class ConstraintCollectionFunction( ConstraintCollectionBase, VariableUsageTrackingMixin ):
    def __init__( self, parent, signal_change ):
        ConstraintCollectionBase.__init__(
            self,
            parent        = parent,
            signal_change = signal_change
        )

        VariableUsageTrackingMixin.__init__( self )

        self.function_body = None

    def process( self, function_body ):
        assert function_body.isExpressionFunctionBody()
        self.function_body = function_body

        statements_sequence = function_body.getBody()

        if statements_sequence is not None:
            self.onStatementsSequence( statements_sequence )

        self.setTempNeedsFreeIndications()

    def onLocalVariableAssigned( self, variable, value_friend ):
        self._getVariableUsage( variable ).markAsWrittenTo( value_friend )

    def onTempVariableAssigned( self, variable, value_friend ):
        variable = variable.getReferenced()

        assert variable.getRealOwner() is self.function_body, variable.getOwner()

        self._getVariableUsage( variable ).markAsWrittenTo( value_friend )


class ConstraintCollectionClass( ConstraintCollectionBase, VariableUsageTrackingMixin ):
    def __init__( self, parent, signal_change ):
        ConstraintCollectionBase.__init__(
            self,
            parent        = parent,
            signal_change = signal_change
        )

        VariableUsageTrackingMixin.__init__( self )

        self.class_body = None

    def process( self, class_body ):
        assert class_body.isExpressionClassBody()
        self.class_body = class_body

        statements_sequence = class_body.getBody()

        if statements_sequence is not None:
            self.onStatementsSequence( statements_sequence )

        self.setTempNeedsFreeIndications()

    def onLocalVariableAssigned( self, variable, value_friend ):
        self._getVariableUsage( variable ).markAsWrittenTo( value_friend )

    def onTempVariableAssigned( self, variable, value_friend ):
        variable = variable.getReferenced()

        assert variable.getRealOwner() is self.class_body, variable.getOwner()

        self._getVariableUsage( variable ).markAsWrittenTo( value_friend )


class ConstraintCollectionModule( ConstraintCollectionBase, VariableUsageTrackingMixin ):
    def __init__( self, signal_change ):
        ConstraintCollectionBase.__init__( self, None, signal_change )

        VariableUsageTrackingMixin.__init__( self )

        self.module = None

    def process( self, module ):
        assert module.isModule()
        self.module = module

        module_body = module.getBody()

        if module_body is not None:
            self.onStatementsSequence( module_body )

        self.setTempNeedsFreeIndications()

        self.attemptRecursion( module )

    def attemptRecursion( self, module ):
        if not Options.shallMakeModule():
            module_filename = module.getFilename()

            # Make sure, we are known to the tree recursion. TODO: Why isn't this done at
            # creation time already? This whole function should be executed at the time
            # the module came into existence, i.e. long before optimization kicks in.
            if module_filename not in TreeRecursion.imported_modules:
                if Utils.basename( module_filename ) == "__init__.py":
                    module_relpath = Utils.dirname( module_filename )
                else:
                    module_relpath = module_filename

                module_relpath = Utils.relpath( module_relpath )

                TreeRecursion.imported_modules[ Utils.relpath( module_relpath ) ] = module

            # Make sure the package is recursed to.
            module_package = module.getPackage()

            if module_package is not None:
                package_package, _package_module_name, package_filename = Importing.findModule(
                    source_ref     = module.getSourceReference(),
                    module_name    = module_package,
                    parent_package = None,
                    level          = 1
                )

                imported_module, added_flag = TreeRecursion.recurseTo(
                    module_package  = package_package,
                    module_filename = package_filename,
                    module_relpath  = Utils.relpath( package_filename )
                )

                if added_flag:
                    self.signalChange(
                        "new_module",
                        imported_module.getSourceReference(),
                        "Recursed to module."
                    )

    def onModuleVariableAssigned( self, variable, value_friend ):
        while variable.isModuleVariableReference():
            variable = variable.getReferenced()

        self._getVariableUsage( variable ).markAsWrittenTo( value_friend )

    def onTempVariableAssigned( self, variable, value_friend ):
        variable = variable.getReferenced()

        assert variable.getRealOwner() is self.module, variable.getOwner()

        self._getVariableUsage( variable ).markAsWrittenTo( value_friend )

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
            self.onStatementsSequence( loop_body )
