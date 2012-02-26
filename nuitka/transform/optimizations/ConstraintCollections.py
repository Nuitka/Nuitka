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

from nuitka.nodes.NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

from nuitka import Options, Utils, TreeRecursion, Importing

from logging import debug

# TODO: This is code duplication, assignments should have a helper module do deal with a
# list of targets and/or generally the value of getTargets() should be able to do a few
# things.
def _isComplexAssignmentTarget( targets ):
    if type( targets ) not in ( tuple, list ) and targets.isAssignTargetSomething():
        targets = [ targets ]

    return len( targets ) > 1 or targets[0].isAssignTargetTuple()

# TODO: This code is only here while staging it, will live in a dedicated module later on
class ConstraintCollection:
    def __init__( self, signal_change, copy_of = None ):
        self.signalChange = signal_change

        if copy_of is None:
            self.variables = {}
        else:
            assert copy_of.__class__ is ConstraintCollection

            self.variables = dict( copy_of.variables )

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

    def onAssigmentToTargetFromValueFriend( self, target, value_friend ):
        if target.isAssignTargetVariable():
            if value_friend is None:
                self.onAssignmentOfTargetFromUnknown( target )
            else:
                self.variables[ target.getTargetVariableRef().getVariable() ] = value_friend
        elif target.isAssignTargetSubscript():
            # TODO: We don't yet track subscripts, as those.
            # TODO: onExpression should rather be "onTarget()" which should do less.
            self.onTarget( target.getSubscribed() )
            self.onExpression( target.getSubscript() )
        elif target.isAssignTargetAttribute():
            # TODO: We don't yet track attributes, as those.
            self.onTarget( target.getLookupSource() )
        elif target.isAssignTargetSlice():
            # TODO: We don't yet track slices, as those.
            self.onTarget( target.getLookupSource() )

            if target.getLower() is not None:
                self.onExpression( target.getLower() )
            if target.getUpper() is not None:
                self.onExpression( target.getUpper() )
        elif target.isAssignTargetTuple():
            self.onAssignmentToTargetsFromSource(
                targets = target.getElements(),
                source  = value_friend
            )
        else:
            assert False, target

    def onAssignmentOfTargetFromUnknown( self, target ):
        if target.isAssignTargetVariable():
            variable = target.getTargetVariableRef().getVariable()

            if variable in self.variables:
                del self.variables[ variable ]


    def onClosureTaker( self, closure_taker ):
        if closure_taker.isExpressionFunctionBody():
            collector = ConstraintCollectionFunction( self.signalChange )
        elif closure_taker.isExpressionClassBody():
            collector = ConstraintCollectionClass( self.signalChange )
        elif closure_taker.isExpressionListContractionBody():
            collector = ConstraintCollectionContraction( self.signalChange )
        elif closure_taker.isExpressionDictContractionBody():
            collector = ConstraintCollectionContraction( self.signalChange )
        elif closure_taker.isExpressionSetContractionBody():
            collector = ConstraintCollectionContraction( self.signalChange )
        elif closure_taker.isExpressionGeneratorBody():
            collector = ConstraintCollectionContraction( self.signalChange )
        else:
            assert False, closure_taker

        collector.process( closure_taker )

    def onStatementsSequence( self, statements_sequence ):
        assert statements_sequence.isStatementsSequence()

        new_statements = []

        statements = statements_sequence.getStatements()
        assert statements, statements_sequence

        for statement in statements_sequence.getStatements():
            new_statement = self.onStatement( statement )

            if new_statement is not None:
                if new_statement.isStatementsSequence():
                    new_statements.extend( new_statement.getStatements() )
                else:
                    new_statements.append( new_statement )

        if statements != new_statements:
            # print statements, new_statements

            if new_statements:
                statements_sequence.setStatements( new_statements )
            else:
                statements_sequence.replaceWith( None )


    def onAssignmentToTargetFromSource( self, target, source ):
        self.onAssignmentToTargetsFromSource(
            targets = ( target, ),
            source  = source
        )

    def onAssignmentToTargetsFromSource( self, targets, source ):
        assert type( targets ) is tuple
        for target in targets:
            assert target.isAssignTargetSomething()

        assert source.isExpression()

        # Ask the source about iself, what does it give.
        source_friend = source.getValueFriend()

        assert source_friend is not None, source

        if _isComplexAssignmentTarget( targets ):
            if source_friend.isKnownToBeIterable( len( targets ) ):
                unpack_friends = source_friend.getUnpacked( len( targets ) )

                for target, unpack_friend in zip( targets, unpack_friends ):
                    self.onAssigmentToTargetFromValueFriend(
                        target       = target,
                        value_friend = unpack_friend
                    )
            else:
                for target in targets:
                    self.onAssignmentOfTargetFromUnknown(
                        target = target
                    )
        else:
            self.onAssigmentToTargetFromValueFriend(
                target       = targets[0],
                value_friend = source_friend
            )

    def onDeleteTarget( self, target ):
        if target.isAssignTargetVariable():
            variable = target.getTargetVariableRef().getVariable()

            if variable in self.variables:
                del self.variables[ variable ]
        elif target.isAssignTargetSlice():
            # TODO: Handle it.
            pass
        elif target.isAssignTargetSubscript():
            # TODO: Handle it.
            pass
        elif target.isAssignTargetAttribute():
            # TODO: Handle it.
            pass
        else:
            assert False, target

    def onStatementAssignment( self, statement ):
        source = statement.getSource()

        self.onExpression( source )

        # Note: The source may no longer be valid, can't use it anymore.
        del source

        targets = statement.getTargets()

        self.onAssignmentToTargetsFromSource(
            targets = targets,
            source  = statement.getSource()
        )

        return statement

    def onStatementDel( self, statement ):
        self.onDeleteTarget( statement.getTarget() )

        return statement

    def onTarget( self, target ):
        if target.isAssignTargetVariable():
            # Should invalidate it
            pass
        elif target.isAssignTargetTuple():
            for sub_target in target.getElements():
                self.onTarget( sub_target )
        elif target.isAssignTargetAttribute():
            # Should invalidate it via attribute registry.
            pass
        elif target.isAssignTargetSubscript():
            # Should invalidate it via subscript registry and wholly.
            pass
        elif target.isAssignTargetSomething():
            assert False, target
        elif target.isExpression():
            self.onExpression( target )
        else:
            assert False, target


    def onExpression( self, expression ):
        assert expression.isExpression(), expression

        # print( "CONSIDER", expression )

        self.onSubExpressions( expression )

        new_node, change_tags, change_desc = expression.computeNode()

        if new_node is not expression:
            expression.replaceWith( new_node )

            self.signalChange(
                change_tags,
                expression.getSourceReference(),
                change_desc
            )
        elif expression.isExpressionVariableRef() and False: # TODO: Not safe yet, disabled
            assert not new_node.getParent().isAssignTargetSomething(), new_node.getParent()

            variable = expression.getVariable()

            friend = self.getVariableValueFriend( variable )

            if friend is not None and not friend.mayHaveSideEffects() and friend.isNode():
                new_node = friend.makeCloneAt(
                    source_ref = expression.getSourceReference(),
                )

                expression.replaceWith( new_node )

                self.signalChange(
                    "new_constant",
                    expression.getSourceReference(),
                    "Assignment source of '%s' propagated, as it has no side effects." % variable.getName()
                )

        return new_node

    def onStatementUsingChildExpressions( self, statement ):
        self.onSubExpressions( statement )

        return statement

    def onSubExpressions( self, owner ):
        if owner.isExpressionAssignment():
            self.onTarget( owner.getTarget() )
            self.onExpression( owner.getSource() )
        elif not owner.hasTag( "closure_taker" ):
            sub_expressions = owner.getVisitableNodes()

            for sub_expression in sub_expressions:
                self.onExpression( sub_expression )
        else:
            self.onClosureTaker( owner )

    def _onStatementConditional( self, statement ):
        no_branch = statement.getBranchNo()

        if no_branch is not None and not no_branch.mayHaveSideEffects():
            self.signalChange(
                "new_statements",
                no_branch.getSourceReference(),
                "Removed else branch without side effects."
            )

            statement.setBranchNo( None )

            no_branch = None

        yes_branch = statement.getBranchYes()

        if yes_branch is not None and not yes_branch.mayHaveSideEffects():
            statement.setBranchYes( None )

            self.signalChange(
                "new_statements",
                yes_branch.getSourceReference(),
                "Removed else branch without side effects."
            )

            yes_branch = None

        self.onExpression( statement.getCondition() )

        condition = statement.getCondition()

        if condition.isExpressionConstantRef():
            if condition.getConstant():
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

        if no_branch is None and yes_branch is None:
            new_statement = makeStatementExpressionOnlyReplacementNode(
                expression = condition,
                node       = statement
            )

            self.signalChange(
                "new_statements",
                statement.getSourceReference(),
                "Both branches have no effect, drop branch nature, only evaluate condition."
            )

            return new_statement

        # TODO: We now know that condition evaluates to true for the yes branch
        # and to not true for no branch

        branch_yes_collection = ConstraintCollectionBranch( self.signalChange )

        if yes_branch is not None:
            branch_yes_collection.process( self, yes_branch )

        if no_branch is not None:
            branch_no_collection = ConstraintCollectionBranch( self.signalChange )

            branch_no_collection.process( self, statement.getBranchNo() )

            self.variables = self.mergeBranchVariables(
                branch_yes_collection.variables,
                branch_no_collection.variables
            )
        else:
            self.mergeBranch( branch_yes_collection )

        return statement

    def onStatement( self, statement ):
        assert statement.isStatement(), statement

        if statement.isStatementAssignment():
            return self.onStatementAssignment( statement )
        elif statement.isStatementDel():
            return self.onStatementDel( statement )
        elif statement.isStatementExpressionOnly():
            expression = statement.getExpression()

            # Workaround for possibilty of generating a statement here.
            if expression.isStatement():
                return self.onStatement( expression )
            else:
                self.onExpression( expression )

                if statement.mayHaveSideEffects():
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
        elif statement.isStatementForLoop():
            # The iterator making is evaluated in any case here.
            self.onExpression( statement.getIterator() )

            # Note: Fetching again, my be replaced meanwhile.
            iterator = statement.getIterator()

            if iterator.isIteratorMaking():
                pass

            if False: # TODO: Must be done
                # Do not accept any change signals, in the first run of the loop, we only want
                # to collect knowledge about what we cannot trust from the start state.
                def disallow_changes():
                    assert False

                first_loop_run = ConstraintCollectionLoopFirst( disallow_changes )
                first_loop_run.process( self, statement )

            other_loop_run = ConstraintCollectionLoopOther( self.signalChange )
            other_loop_run.process( self, statement )

            self.mergeBranch(
                other_loop_run
            )

            return statement
        elif statement.isStatementWhileLoop():
            self.onExpression( statement.getCondition() )

            other_loop_run = ConstraintCollectionLoopOther( self.signalChange )
            other_loop_run.process( self, statement )

            self.mergeBranch(
                other_loop_run
            )

            return statement
        elif statement.isStatementTryFinally():
            # The tried block can be processed normally.
            tried_statement_sequence = statement.getBlockTry()

            if tried_statement_sequence is not None:
                self.onStatementsSequence( tried_statement_sequence )

            if statement.getBlockTry() is None:
                result = statement.getBlockFinal()
            else:
                result = statement

            if statement.getBlockFinal() is not None:
                # Then assuming no exception, the no raise block if present.
                self.onStatementsSequence( statement.getBlockFinal() )
            else:
                result = statement.getBlockTry()

            return result
        elif statement.isStatementTryExcept():
            # The tried block can be processed normally.
            tried_statement_sequence = statement.getBlockTry()

            if tried_statement_sequence is None:
                return statement.getBlockNoRaise()

            self.onStatementsSequence( tried_statement_sequence )

            if statement.getBlockNoRaise() is not None:
                # Then assuming no exception, the no raise block if present.
                self.onStatementsSequence( statement.getBlockNoRaise() )

            # The exception branches triggers in unknown state, any amount of tried code
            # may have happened. A similar approach to loops should be taken to invalidate
            # the state before.
            for handler in statement.getExceptionHandlers():
                exception_branch = ConstraintCollectionHandler( self.signalChange )
                exception_branch.process( handler )

            # Give up, merging this is too hard for now.
            self.variables = {}

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
        elif statement.isStatementWith():
            if statement.getTarget() is not None:
                self.onTarget( statement.getTarget() )
            self.onExpression( statement.getExpression() )

            with_body = statement.getWithBody()

            if with_body is not None:
                self.onStatementsSequence( with_body )

            return statement
        elif statement.isStatementTempBlock():
            self.onStatementsSequence( statement.getBody() )

            return statement
        else:
            assert False, statement


class ConstraintCollectionHandler( ConstraintCollection ):
    def process( self, handler ):
        assert handler.isStatementExceptHandler()

        # TODO: The exception type and name could be assigned.
        branch = handler.getExceptionBranch()

        if branch is not None:
            self.onStatementsSequence( branch )

class ConstraintCollectionBranch( ConstraintCollection ):
    def process( self, start_state, branch ):
        assert branch.isStatementsSequence()

        self.onStatementsSequence( branch )


class ConstraintCollectionFunction( ConstraintCollection ):
    def process( self, function_body ):
        assert function_body.isExpressionFunctionBody()

        statements_sequence = function_body.getBody()

        if statements_sequence is not None:
            self.onStatementsSequence( statements_sequence )


class ConstraintCollectionClass( ConstraintCollection ):
    def process( self, class_body ):
        assert class_body.isExpressionClassBody()

        statements_sequence = class_body.getBody()

        if statements_sequence is not None:
            self.onStatementsSequence( statements_sequence )


class ConstraintCollectionContraction( ConstraintCollection ):
    def process( self, contraction_body ):
        # TODO: Contractions don't work at all in this structure.
        for source in contraction_body.getSources():
            self.onExpression( source )

        for condition in contraction_body.getConditions():
            self.onExpression( condition )

        for target in contraction_body.getTargets():
            self.onTarget( target )

        # TODO: Do not call this body, it's the expression generated.
        self.onExpression( contraction_body.getBody() )


class ConstraintCollectionModule( ConstraintCollection ):
    def process( self, module ):
        assert module.isModule()

        module_body = module.getBody()

        if module_body is not None:
            self.onStatementsSequence( module_body )

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


class ConstraintCollectionLoopOther( ConstraintCollection ):
    def process( self, start_state, loop ):
        # TODO: Somehow should copy that start state over, assuming nothing won't be wrong
        # for a start.
        self.start_state = start_state

        if loop.isStatementForLoop():
            # TODO: This should really be done from a next.
            if False:
                self.onAssignmentToTargetFromSource(
                    source = loop.getIterator(),
                    target = loop.getLoopVariableAssignment()
                )
        elif loop.isStatementWhileLoop():
            pass
        else:
            assert False, loop

        loop_body = loop.getLoopBody()

        if loop_body is not None:
            self.onStatementsSequence( loop_body )


class ConstraintCollectionLoopFirst( ConstraintCollection ):
    def process( self, start_state, loop ):
        # TODO: Somehow should copy that start state over, assuming nothing won't be wrong
        # for a start.
        self.start_state = start_state

        assert loop.isStatementForLoop()

        if loop.isStatementForLoop():
            # TODO: This should really be done from a next.
            if False:
                self.onAssignmentToTargetFromSource(
                    source = loop.getIterator(),
                    target = loop.getLoopVariableAssignment()
                )


        self.onStatementsSequence( loop.getBody() )
