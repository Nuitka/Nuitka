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

At the core of value propagation there is the collection of constraints that
allow to propagate knowledge forward or not.

This is about collecting these constraints and to manage them.
"""

# Python3 compatibility.
from nuitka.__past__ import iterItems

from nuitka.nodes import ValueFriends

from nuitka.nodes.NodeMakingHelpers import (
    makeStatementExpressionOnlyReplacementNode,
    makeStatementsSequenceReplacementNode,
)

from nuitka.nodes.AssignNodes import StatementDelVariable

from nuitka import Options, Utils, Importing
from nuitka.tree import Recursion

from logging import debug, warning


class VariableTraceBase:
    def __init__( self, variable, version ):
        self.variable     = variable
        self.version      = version

        # List of references.
        self.usages = []

        # List of releases of the node.
        self.releases = []

        # If not None, this indicates the last usage, where the value was not
        # yet escaped. If it is 0, it escaped immediately. Escaping is a one
        # time action.
        self.escaped_at = None

    def getVariable( self ):
        return self.variable

    def getVersion( self ):
        return self.version

    def addUsage( self, ref_node ):
        self.usages.append( ref_node )

    def addRelease( self, release_node ):
        self.releases.append( release_node )

    def onValueEscape( self ):
        self.escaped_at = len( self.usages )

    def isEscaped( self ):
        return self.escaped_at is not None

    def getPotentialUsages( self ):
        return self.usages

    def getDefiniteUsages( self ):
        return self.usages

    def isAssignTrace( self ):
        return False

    def isUninitTrace( self ):
        return False

    def isMergeTrace( self ):
        return False


class VariableUninitTrace( VariableTraceBase ):
    def __init__( self, variable, version ):
        VariableTraceBase.__init__(
            self,
            variable = variable,
            version  = version
        )

    def isUninitTrace( self ):
        return True

    def dump( self ):
        debug( "Trace of %s %d:", self.variable, self.version )
        debug( "  Starts out uninitialized" )

        for count, usage in enumerate( self.usages ):
            if count == self.escaped_at:
                debug( "  Escaped value" )

            debug( "  Used at %s", usage )


class VariableUnknownTrace( VariableTraceBase ):
    def __init__( self, variable, version ):
        VariableTraceBase.__init__(
            self,
            variable = variable,
            version  = version
        )

    def dump( self ):
        debug( "Trace of %s %d:", self.variable, self.version )
        debug( "  Starts unknown" )

        for count, usage in enumerate( self.usages ):
            if count == self.escaped_at:
                debug( "  Escaped value" )

            debug( "  Used at %s", usage )


class VariableAssignTrace( VariableTraceBase ):
    def __init__( self, target_node, variable, version, value_friend ):
        VariableTraceBase.__init__(
            self,
            variable = variable,
            version  = version
        )

        self.target_node = target_node
        self.value_friend = value_friend

    def __repr__( self ):
        return "<VariableAssignTrace %s %d>" % (
            self.variable,
            self.version
        )

    def dump( self ):
        debug( "Trace of %s %d:", self.variable, self.version )
        debug( "  Assigned from %s", self.value_friend )

        for count, usage in enumerate( self.usages ):
            if count == self.escaped_at:
                debug( "  Escaped value" )

            debug( "  Used at %s", usage )

    def isAssignTrace( self ):
        return True

    def getAssignNode( self ):
        return self.target_node


class VariableMergeTrace( VariableTraceBase ):
    def __init__( self, variable, version, trace_yes, trace_no ):
        assert trace_no is not trace_yes, ( variable, version, trace_no )

        VariableTraceBase.__init__(
            self,
            variable = variable,
            version  = version
        )

        self.trace_yes = trace_yes
        self.trace_no = trace_no

        self.forwarded = True

    def isMergeTrace( self ):
        return True

    def addUsage( self, ref_node ):
        if not self.usages:
            # Merging is usage.
            self.trace_yes.addUsage( self )
            if self.trace_no is not None:
                self.trace_no.addUsage( self )

        VariableTraceBase.addUsage( self, ref_node )


    def getPotentialUsages( self ):
        assert False

    def dump( self ):
        debug( "Trace of %s %d:", self.variable, self.version )
        debug( "  Merge of %s <-> %s", self.trace_yes, self.trace_no )


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


class CollectionTracingMixin:
    def __init__( self ):
        # For functions, when we are in here, the currently active one,
        self.variable_actives = {}

    def getVariableCurrentTrace( self, variable ):
        return self.getVariableTrace(
            variable = variable,
            version  = self.getCurrentVariableVersion( variable )
        )

    def markCurrentVariableTrace( self, variable, version ):
        assert not variable.isModuleVariable() or variable.isReference(), variable

        self.variable_actives[ variable ] = version

    def getCurrentVariableVersion( self, variable ):
        assert variable in self.variable_actives, ( variable, self )
        return self.variable_actives[ variable ]

    def getActiveVariables( self ):
        return list( self.variable_actives.keys() )


class CollectionStartpointMixin:
    def __init__( self ):
        # Variable assignments performed in here, last issued number, only used
        # to determine the next number that should be used for a new assignment.
        self.variable_versions = {}

        # The full trace of a variable with a version for the function or module
        # this is.
        self.variable_traces = {}

        # Cannot mess with local variables that much, as "locals" and "eval"
        # calls may not yet be known.
        self.unclear_locals = False

    def getVariableTrace( self, variable, version ):
        return self.variable_traces[ ( variable, version ) ]

    def addVariableTrace( self, variable, version, trace ):
        key = variable, version

        assert key not in self.variable_traces, key
        self.variable_traces[ key ] = trace

    def dumpTrace( self ):
        debug( "Constraint collection state:" )
        for variable_desc, variable_trace in iterItems( self.variable_traces ):
            debug( "%r: %r", variable_desc, variable_trace )
            variable_trace.dump()

    def initVariableUnknown( self, variable ):
        self.addVariableTrace(
            variable = variable,
            version  = 0,
            trace    = VariableUnknownTrace(
                variable = variable,
                version  = 0
            )
        )

        self.markCurrentVariableTrace( variable, 0 )

    def initVariableUninit( self, variable ):
        self.addVariableTrace(
            variable = variable,
            version  = 0,
            trace    = VariableUninitTrace(
                variable = variable,
                version  = 0
            )
        )

        self.markCurrentVariableTrace( variable, 0 )

    def assumeUnclearLocals( self ):
        self.unclear_locals = True


# TODO: This code is only here while staging it, will live in a dedicated module
# later on
class ConstraintCollectionBase( CollectionTracingMixin ):
    def __init__( self, parent, signal_change = None ):
        CollectionTracingMixin.__init__( self )

        assert signal_change is None or parent is None

        if signal_change is not None:
            self.signalChange = signal_change
        else:
            self.signalChange = parent.signalChange

        self.parent = parent

        self.variables = {}

        # Trust variable_traces, should go away later on, for now we use it to
        # disable optimization.
        self.removes_knowledge = False

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

        # Temporary, we don't have to have this anyway, this will just disable
        # all uses of variable traces for optimization.
        self.removes_knowledge = True

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

    def _onStatementsFrame( self, statements_sequence ):
        assert statements_sequence.isStatementsFrame()

        new_statements = []

        statements = statements_sequence.getStatements()
#        assert statements, statements_sequence

        for count, statement in enumerate( statements ):
            # May be frames embedded.
            if statement.isStatementsFrame():
                new_statement = self.onStatementsSequence( statement )
            else:
                new_statement = self.onStatement( statement )

            if new_statement is not None:
                if new_statement.isStatementsSequence() and \
                   not new_statement.isStatementsFrame():
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
            if not new_statements:
                return None

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
                if new_statement.isStatementsSequence() and \
                   not new_statement.isStatementsFrame():
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

    def assumeUnclearLocals( self ):
        self.parent.assumeUnclearLocals()

    def getVariableTrace( self, variable, version ):
        return self.parent.getVariableTrace( variable, version )

    def addVariableTrace( self, variable, version, trace ):
        assert self.parent is not None, self

        self.parent.addVariableTrace( variable, version, trace )

    def onVariableSet( self, target_node, value_friend ):
        # Add a new trace, using the version allocated for the variable, and
        # remember the value friend.
        variable = target_node.getVariable()

        assert not variable.isModuleVariable() or variable.isReference(), variable

        # print "SET", target_node, target_node.getVariableVersion()
        version = target_node.getVariableVersion()

        self.addVariableTrace(
            variable = variable,
            version  = version,
            trace    = VariableAssignTrace(
                target_node  = target_node,
                variable     = variable,
                version      = version,
                value_friend = value_friend
            )
        )

        # Make references point to it.
        self.markCurrentVariableTrace( variable, version )

    def onVariableDel( self, del_node ):
        # Add a new trace, allocating a new version for the variable, and
        # remember the delete of the current
        target_node = del_node.getTargetVariableRef()
        variable = target_node.getVariable()

        current = self.getVariableCurrentTrace( variable )
        current.addRelease( del_node )

        version = target_node.getVariableVersion()

        # Assign to uninit again.
        self.addVariableTrace(
            variable = variable,
            version  = version,
            trace    = VariableUninitTrace(
                variable     = variable,
                version      = version
            )
        )

        # Make references point to it.
        self.markCurrentVariableTrace( variable, version )

    def onVariableUsage( self, ref_node ):
        variable = ref_node.getVariable()
        # while variable.isReference():
        #    variable = variable.getReferenced()

        self.getVariableCurrentTrace( variable ).addUsage( ref_node )

    def onLocalsAccess( self, locals_node ):
        for variable in self.getActiveVariables():
            # print "LOCALS", variable
            self.getVariableCurrentTrace( variable ).addUsage( locals_node )

    def onVariableContentEscapes( self, variable ):
        self.getVariableCurrentTrace( variable ).onValueEscape()

    def onExpression( self, expression, allow_none = False ):
        if expression is None and allow_none:
            return

        assert expression.isExpression(), expression

        # Now compute this expression, allowing it to replace itself with
        # something else as part of a local peephole optimization.
        r = expression.computeExpressionRaw( self )
        assert type(r) is tuple, expression

        new_node, change_tags, change_desc = r

        if new_node is not expression:
            expression.replaceWith( new_node )

            # This is mostly for tracing and indication that a change occured
            # and it may be interesting to look again.
            self.signalChange(
                change_tags,
                expression.getSourceReference(),
                change_desc
            )

        if new_node.isExpressionVariableRef():
            # OLD:
            if not new_node.getVariable().isModuleVariableReference():
                self.onLocalVariableRead( new_node.getVariable() )

            # Remember this for constraint collection. Any variable that we
            # access has a version already that we can query. TODO: May do this
            # as a "computeReference".

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

        # Assigning from and to the same variable, can be optimized away
        # immediately, there is no point in doing it. Exceptions are of course
        # module variables that collide with builtin names.
        if not variable.isModuleVariableReference() and \
             source.isExpressionVariableRef() and \
             source.getVariable() == variable:
            if source.mayHaveSideEffects():
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
        # Refuse to do stupid work
        if collection_yes is None and collection_no is None:
            pass
        elif collection_yes is None or collection_no is None:
            # Handle one branch case, we need to merge versions backwards as
            # they may make themselves obsolete.
            collection = collection_yes or collection_no

            for variable in collection.getActiveVariables():
                # print "ACTIVE", variable, self.getCurrentVariableVersion( variable )

                trace_old = self.getVariableCurrentTrace( variable )
                trace_new = collection.getVariableCurrentTrace( variable )

                if trace_old is not trace_new:
                    version = variable.allocateTargetNumber()

                    # print "Allocated", variable, version

                    trace_merge = VariableMergeTrace(
                        variable     = variable,
                        version      = version,
                        trace_yes    = trace_new,
                        trace_no     = trace_old
                    )

                    self.addVariableTrace(
                        variable = variable,
                        version  = version,
                        trace    = trace_merge
                    )

                    # Merging is releasing.
                    trace_old.addUsage( trace_merge )
                    trace_new.addUsage( trace_merge )

            return
        else:
            for variable in collection_yes.getActiveVariables():
                trace_yes = collection_yes.getVariableCurrentTrace( variable )
                trace_no = collection_no.getVariableCurrentTrace( variable )

                if trace_yes is not trace_no:
                    version = variable.allocateTargetNumber()
                    trace_merge = VariableMergeTrace(
                        variable     = variable,
                        version      = version,
                        trace_yes    = trace_yes,
                        trace_no     = trace_no
                    )

                    self.addVariableTrace(
                        variable = variable,
                        version  = version,
                        trace    = trace_merge
                    )

                    # Merging is releasing.
                    trace_yes.addUsage( trace_merge )
                    trace_no.addUsage( trace_merge )


class ConstraintCollectionHandler( ConstraintCollectionBase ):
    def __init__( self, parent ):
        ConstraintCollectionBase.__init__(
            self,
            parent = parent
        )

        self.variable_actives = dict( parent.variable_actives )

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

        self.variable_actives = dict( parent.variable_actives )

    def process( self, branch ):
        assert branch.isStatementsSequence(), branch

        result = self.onStatementsSequence( branch )

        if result is not branch:
            branch.replaceWith( result )

    def mergeBranches( self, collection_yes, collection_no ):
        # Branches in branches, should ask parent about merging them.
        return self.parent.mergeBranches( collection_yes, collection_no )


class ConstraintCollectionFunction( CollectionStartpointMixin,
                                    ConstraintCollectionBase,
                                    VariableUsageTrackingMixin,
                                     ):
    def __init__( self, parent ):
        CollectionStartpointMixin.__init__( self )

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

        if statements_sequence is not None and \
           not statements_sequence.getStatements():
            function_body.setStatements( None )
            statements_sequence = None

        for variable in function_body.getVariables():
            # print function_body, variable

            if variable.isParameterVariable():
                self.initVariableUnknown( variable )
            elif variable.isLocalVariable():
                self.initVariableUninit( variable )
            elif variable.isMaybeLocalVariable():
                self.initVariableUnknown( variable )
            elif variable.isModuleVariableReference():
                pass
            elif variable.isClosureReference():
                pass
                # self.initVariableUnknown( variable )
            else:
                assert False, variable

        for variable in function_body.taken:
            # while variable.isReference():
            #    variable = variable.getReferenced()

            self.initVariableUnknown( variable )

        if statements_sequence is not None:
            result = self.onStatementsSequence( statements_sequence )

            if result is not statements_sequence:
                function_body.setBody( result )

        self.setIndications()

        if not Options.isExperimental() or self.removes_knowledge:
            return

        # self.dumpTrace()

        # Cannot mess with locals yet.
        if self.unclear_locals:
            return

        # Trace based optimization goes here:
        for variable_trace in self.variable_traces.values():
            variable = variable_trace.getVariable()

            # print variable

            if variable.isLocalVariable() and not variable.isShared():
                if variable_trace.isAssignTrace():
                    assign_node = variable_trace.getAssignNode()

                    if not assign_node.parent.getAssignSource().mayHaveSideEffects():

                        if not variable_trace.getPotentialUsages() and \
                           not variable_trace.isEscaped():
                            assign_node.parent.replaceWith(
                                StatementDelVariable(
                                    variable_ref = assign_node,
                                    tolerant     = True,
                                    source_ref   = assign_node.getSourceReference()
                                )
                            )

                            for release in variable_trace.releases:
                                if release.isStatementDelVariable():
                                    release.replaceWith(
                                        None
                                    )

                            self.signalChange(
                                "new_statements",
                                assign_node.parent.getSourceReference(),
                                "Removed assignment without effect."
                            )
                elif variable_trace.isMergeTrace():
                    # print variable_trace
                    if not variable_trace.getDefiniteUsages() and \
                       not variable_trace.isEscaped() and \
                       not variable_trace.releases:
                        pass
                        # print "HIT", variable_trace



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



class ConstraintCollectionModule( CollectionStartpointMixin,
                                  ConstraintCollectionBase,
                                  VariableUsageTrackingMixin,
                                   ):
    def __init__( self, signal_change ):
        CollectionStartpointMixin.__init__( self )

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

        for variable in module.getVariables():
            self.initVariableUnknown( variable.makeReference( module ) )

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
    def __init__( self, parent ):
        ConstraintCollectionBase.__init__(
            self,
            parent = parent
        )

        self.variable_actives = dict( parent.variable_actives )

    def process( self, loop_body ):
        result = self.onStatementsSequence( loop_body )

        if result is not loop_body:
            loop_body.replaceWith( result )


class ConstraintCollectionTempBlock( ConstraintCollectionBase ):
    def __init__( self, parent ):
        ConstraintCollectionBase.__init__(
            self,
            parent = parent
        )

        self.variable_actives = dict( parent.variable_actives )

    def process( self, temp_block ):
        old_body = temp_block.getBody()

        result = self.onStatementsSequence( old_body )

        if result is not old_body:
            temp_block.setBody( result )

        for variable in self.getActiveVariables():
            if not variable.isTempVariableReference():
                self.parent.markCurrentVariableTrace(
                    variable = variable,
                    version  = self.getCurrentVariableVersion( variable )
                )
