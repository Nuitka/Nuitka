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
from nuitka.oset import OrderedSet

from nuitka.nodes import ValueFriends

from nuitka.nodes.NodeMakingHelpers import (
    makeStatementExpressionOnlyReplacementNode,
    makeStatementsSequenceReplacementNode,
)

from nuitka import Options, Utils, Importing
from nuitka.tree import Recursion

from logging import debug, warning


class VariableTrace:
    def __init__( self, variable, version ):
        self.variable     = variable
        self.version      = version

        self.usages = []

    def addUsage( self, ref_node ):
        self.usages.append( ref_node )


class VariableAssignTrace( VariableTrace ):
    def __init__( self, target_node, variable, version, value_friend ):
        VariableTrace.__init__(
            self,
            variable = variable,
            version  = version
        )

        self.target_node = target_node
        self.value_friend = value_friend

    def onValueEscape( self ):
        # TODO: Tell value friend to degrade intelligently.
        self.value_friend = None


class VariableReferenceTrace( VariableTrace ):
    def __init__( self, ref_node, variable, version ):
        VariableTrace.__init__(
            self,
            variable = variable,
            version  = version
        )

        self.ref_node = ref_node

        self.usages.append( ref_node )

    def onValueEscape( self ):
        pass


class VariableMergeTrace( VariableTrace ):
    def __init__( self, variable, version, trace_yes, trace_no ):
        VariableTrace.__init__(
            self,
            variable = variable,
            version  = version
        )

    def onValueEscape( self ):
        pass


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
    def __init__( self, parent, signal_change = None ):
        assert signal_change is None or parent is None

        if signal_change is not None:
            self.signalChange = signal_change
        else:
            self.signalChange = parent.signalChange

        self.parent = parent

        # Variable assignments performed in here.
        self.variable_versions = {}
        self.variable_traces = {}

        self.variables = {}

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


    def onVariableSet( self, target_node, value_friend ):
        # Add a new trace, allocating a new version for the variable, and remember the value
        # friend.
        variable = target_node.getVariable()

        while variable.isReference():
            variable = variable.getReferenced()

        assert not variable.isModuleVariableReference()

        version  = target_node.getVariableVersion()

        key = variable, version

        self.variable_traces[ key ] = VariableAssignTrace(
            target_node  = target_node,
            variable     = variable,
            version      = version,
            value_friend = value_friend
        )

        self.variable_versions[ variable ] = version

        return key

    def onVariableUsage( self, ref_node ):
        variable = ref_node.getVariable()

        while variable.isReference():
            variable = variable.getReferenced()

        assert not variable.isModuleVariableReference()

        version  = self.variable_versions.get( variable, 0 )

        key = variable, version

        if key in self.variable_traces:
            self.variable_traces[ key ].addUsage( ref_node )

            return None
        else:
            self.variable_traces[ key ] = VariableReferenceTrace(
                ref_node = ref_node,
                variable = variable,
                version  = version
            )

            self.variable_versions[ variable ] = version

            return key

    def onVariableContentEscapes( self, variable ):
        version = self.variable_versions.get( variable, 0 )

        key = variable, version

        if key in self.variable_traces:
            # Indicate when the variable value escaped.
            self.variable_traces[ key ].onValueEscape()

    def onExpression( self, expression, allow_none = False ):
        if expression is None and allow_none:
            return

        assert expression.isExpression(), expression

        # First apply the sub-expressions, as they are evaluated before.
        self.onSubExpressions( expression )

        # Now compute this expression, allowing it to replace itself with something else
        # as part of a local peephole optimization.
        r = expression.computeExpression( self )
        assert type(r) is tuple, expression

        new_node, change_tags, change_desc = r

        if new_node is not expression:
            expression.replaceWith( new_node )

            # This is mostly for tracing and indication that a change occured and it may
            # be interesting to look again.
            self.signalChange(
                change_tags,
                expression.getSourceReference(),
                change_desc
            )

        if new_node.isExpressionVariableRef():
            # OLD:
            if not new_node.getVariable().isModuleVariableReference():
                self.onLocalVariableRead( new_node.getVariable() )

            # Remember this for constraint collection. Any variable that we access has a
            # version already that we can query. TODO: May do this as a
            # "computeReference".

            self.onVariableUsage( new_node )
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
        # But now it cannot re-compute anymore:
        source = statement.getAssignSource()

        if source.willRaiseException( BaseException ):
            result = makeStatementExpressionOnlyReplacementNode(
                expression = source,
                node       = statement
            )

            return result, "new_raise", """\
Removed assignment that has source that will raise."""

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
                result = makeStatementExpressionOnlyReplacementNode(
                    expression = source,
                    node       = statement
                )

                return result, "new_statements", """\
Reduced assignment of variable from itself to access of it."""
            else:
                return None, "new_statements", """\
Removed assignment of variable from itself which is known to be defined."""

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

            result = result, "new_statements", """\
Side effects of assignments promoted to statements."""
        else:
            result = statement, None, None

        value_friend = source.getValueFriend( self )
        assert value_friend is not None

        old_value_friend = None

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
        try:
            assert statement.isStatement(), statement

            new_statement, change_tags, change_desc = statement.computeStatement( self )

            if new_statement is not statement:
                self.signalChange(
                    change_tags,
                    statement.getSourceReference(),
                    change_desc
                )

            return new_statement
        except Exception:
            warning( "Problem with statement at %s:", statement.getSourceReference() )
            raise

    def mergeBranches( self, collection_yes, collection_no ):
        def getParentVariableVersion( variable ):
            return self.parent.getVariableVersions().get( variable, None )

        def mergeSingleBranchChange( variable, version ):
            key = variable, variable.allocateTargetNumber()

            # Now we didn't find it in yes, so it's up to merging.
            if variable in self.variable_versions:
                trace_old = self.variable_traces[ variable, self.variable_versions[ variable ] ]
            else:
                trace_old = None

            self.variable_traces[ key ] = VariableMergeTrace(
                variable     = variable,
                version      = key[1],
                trace_yes    = self.variable_traces[ variable, version ],
                trace_no     = trace_old
            )

        if collection_yes is not None:
            added_yes = collection_yes.getBranchOnlyTraces()

            if collection_no is not None:
                added_no = collection_no.getBranchOnlyTraces()

                # Merge yes branch assignments with either existing ones from "no" branch,
                # or with the original start point.
                for yes_variable, yes_version in reversed( added_yes ):
                    key = yes_variable, yes_variable.allocateTargetNumber()

                    for no_variable, no_version in reversed( added_no ):
                        if yes_variable == no_variable:
                            self.variable_traces[ key ] = VariableMergeTrace(
                                variable     = yes_variable,
                                # TODO: Get this from ourselves.
                                version      = key[1],
                                trace_yes    = self.variable_traces[ yes_variable, yes_version ],
                                trace_no     = self.variable_traces[ no_variable, no_version ]
                            )

                            break
                    else:
                        if yes_variable in self.variable_versions:
                            trace_no = self.variable_traces[ yes_variable, self.variable_versions[ yes_variable ] ]
                        else:
                            trace_no = None

                        self.variable_traces[ key ] = VariableMergeTrace(
                            variable     = yes_variable,
                            # TODO: Get this from ourselves.
                            version      = key[1],
                            trace_yes    = self.variable_traces[ yes_variable, yes_version ],
                            trace_no     = trace_no
                        )


                # Merge no branch variables if their version is higher, meaning it's
                # actually still a newer assignment, and wasn't merged yet.
                for no_variable, no_version in reversed( added_no ):
                    for yes_variable, yes_version in reversed( added_yes ):
                        if yes_variable == no_variable:
                            break
                    else:
                        mergeSingleBranchChange( no_variable, no_version )
            else:
                for yes_variable, yes_version in reversed( added_yes ):
                    mergeSingleBranchChange( yes_variable, yes_version )
        elif collection_no is not None:
            added_no = collection_no.getBranchOnlyTraces()

            for no_variable, no_version in reversed( added_no ):
                mergeSingleBranchChange( no_variable, no_version )


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
    def __init__( self, parent ):
        ConstraintCollectionBase.__init__(
            self,
            parent = parent
        )

        self.branch_only_traces = OrderedSet()

    def process( self, branch ):
        assert branch.isStatementsSequence(), branch

        result = self.onStatementsSequence( branch )

        if result is not branch:
            branch.replaceWith( result )

    def onVariableSet( self, target_node, value_friend ):
        # Add a new trace, allocating a new version for the variable, and remember the value
        # friend.
        key = self.parent.onVariableSet(
            target_node  = target_node,
            value_friend = value_friend
        )

        # Remember the version, because it was added to this branch only, which matters
        # for merge later.
        self.branch_only_traces.add( key )

        return key

    def onVariableUsage( self, ref_node ):
        key = self.parent.onVariableUsage(
            ref_node = ref_node
        )

        if key is not None:
            self.branch_only_traces.add( key )

        return key

    def getBranchOnlyTraces( self ):
        return self.branch_only_traces

    def mergeBranches( self, collection_yes, collection_no ):
        # Branches in branches, should ask parent about merging them.
        return self.parent.mergeBranches( collection_yes, collection_no )


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

    def dumpTrace( self ):
        for i in range(5):
            print( "*" * 80 )

        for variable, traces in iterItems( self.variable_targets ):
            print( variable )
            print( "*" * 80 )
            for trace in traces:
                print( trace )
            print( "*" * 80 )

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
            signal_change = signal_change
        )

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
                    level          = 1,
                    warn           = True
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


class ConstraintCollectionLoop( ConstraintCollectionBase ):
    def process( self, loop_body ):
        result = self.onStatementsSequence( loop_body )

        if result is not loop_body:
            loop_body.replaceWith( result )
