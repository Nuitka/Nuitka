#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
from logging import debug

from nuitka import Options, Tracing
from nuitka.__past__ import iterItems
from nuitka.nodes.AssignNodes import StatementDelVariable
from nuitka.nodes.NodeMakingHelpers import (
    makeStatementExpressionOnlyReplacementNode,
    makeStatementsSequenceReplacementNode
)

from .VariableTraces import (
    VariableAssignTrace,
    VariableMergeTrace,
    VariableUninitTrace,
    VariableUnknownTrace
)


# TODO: This will be removed, to be replaced by variable trace information.
class VariableUsageProfile:
    def __init__(self, variable):
        self.variable = variable

        self.written_to = False

    def markAsWrittenTo(self, assign_source):
        self.written_to = True

    def isReadOnly(self):
        return not self.written_to


class VariableUsageTrackingMixin:
    def __init__(self):
        self.variable_usages = {}

    # TODO: This will be removed, to be replaced by variable trace information.
    def _getVariableUsage(self, variable):
        if variable in self.variable_usages:
            return self.variable_usages[ variable ]
        else:
            self.variable_usages[ variable ] = VariableUsageProfile( variable )

            return self.variable_usages[ variable ]

    def setIndications(self):
        pass

    def setupVariableTraces(self, owner):
        for variable in owner.getVariables():
            # print owner.isPythonModule(), variable

            if variable.isParameterVariable():
                self.initVariableUnknown( variable )
            elif variable.isLocalVariable():
                self.initVariableUninit( variable )
            elif variable.isMaybeLocalVariable():
                self.initVariableUnknown( variable )
            elif variable.isModuleVariableReference():
                pass
            elif variable.isModuleVariable():
                self.initVariableUnknown( variable.makeReference( owner ) )
            elif variable.isClosureReference():
                pass
            else:
                assert False, variable

        for variable in owner.getTempVariables():
            self.initVariableUninit(variable.makeReference(owner))

        if owner.isExpressionFunctionBody():
            for variable in owner.taken:
                self.initVariableUnknown(variable)

    def _makeVariableTraceOptimization(self, owner, variable_trace):
        variable = variable_trace.getVariable()

        if variable.isTempVariableReference():
            referenced_variable = variable.getReferenced()

            if referenced_variable.isTempVariable():
                if referenced_variable.getOwner() is owner:

                    if variable_trace.isUninitTrace() and \
                       variable_trace.getVersion() == 0:
                        if self.getVariableCurrentTrace( variable ) is variable_trace:
                            # TODO: Removing them now breaks merging, could be
                            # done not at all before code generation.
                            # owner.removeTempVariable( variable )
                            pass

                    # TODO: Something wrong here, disabled it for now.
                    if False and \
                        variable_trace.isAssignTrace() and \
                       not variable_trace.getAssignNode().getAssignSource().\
                         mayHaveSideEffects() and \
                       not variable_trace.getPotentialUsages():
                        variable_trace.getAssignNode().replaceWith(None)


    def makeVariableTraceOptimizations(self, owner):
        # Reliable trace based optimization goes here:
        for variable_trace in self.variable_traces.values():
            try:
                self._makeVariableTraceOptimization(
                    owner          = owner,
                    variable_trace = variable_trace
                )
            except:
                print( "Problem with", variable_trace, "in", owner )
                raise


class CollectionTracingMixin:
    def __init__(self):
        # For functions, when we are in here, the currently active one,
        self.variable_actives = {}

    def getVariableCurrentTrace(self, variable):
        return self.getVariableTrace(
            variable = variable,
            version  = self.getCurrentVariableVersion( variable )
        )

    def markCurrentVariableTrace(self, variable, version):
        assert not variable.isModuleVariable() or variable.isReference(), \
           variable

        self.variable_actives[ variable ] = version

    def getCurrentVariableVersion(self, variable):
        assert variable in self.variable_actives, ( variable, self )
        return self.variable_actives[ variable ]

    def getActiveVariables(self):
        return tuple( self.variable_actives.keys() )

    def markActiveVariableAsUnknown(self, variable):
        current = self.getVariableCurrentTrace(
            variable = variable,
        )

        if not current.isUnknownTrace():
            version = variable.allocateTargetNumber()

            self.addVariableTrace(
                variable = variable,
                version  = version,
                trace    = VariableUnknownTrace(
                    variable = variable,
                    version  = version
                )
            )

            self.markCurrentVariableTrace( variable, version )

    def markActiveVariablesAsUnknown(self):
        for variable in self.getActiveVariables():
            self.markActiveVariableAsUnknown( variable )


class CollectionStartpointMixin:
    def __init__(self):
        # Variable assignments performed in here, last issued number, only used
        # to determine the next number that should be used for a new assignment.
        self.variable_versions = {}

        # The full trace of a variable with a version for the function or module
        # this is.
        self.variable_traces = {}

        # Cannot mess with local variables that much, as "locals" and "eval"
        # calls may not yet be known.
        self.unclear_locals = False

    def getVariableTrace(self, variable, version):
        return self.variable_traces[ ( variable, version ) ]

    def getVariableTraces(self, variable):
        result = []

        for key, variable_trace in iterItems( self.variable_traces ):
            candidate = key[0]
            candidate = candidate.getReferenced()

            if variable is candidate:
                result.append( variable_trace )

        return result

    def addVariableTrace(self, variable, version, trace):
        key = variable, version

        assert key not in self.variable_traces, ( key, self )
        self.variable_traces[ key ] = trace

    def addVariableMergeTrace(self, variable, trace_yes, trace_no):
        version = variable.allocateTargetNumber()
        trace_merge = VariableMergeTrace(
            variable     = variable,
            version      = version,
            trace_yes    = trace_yes,
            trace_no     = trace_no
        )

        self.addVariableTrace(variable, version, trace_merge)

        # Merging is using, might imply releasing.
        trace_yes.addUsage(trace_merge)
        trace_no.addUsage(trace_merge)

        return version

    def dumpTraces(self):
        debug("Constraint collection state: %s", self)
        for _variable_desc, variable_trace in sorted(iterItems(self.variable_traces)):

            # debug( "%r: %r", variable_trace )
            variable_trace.dump()

    def initVariableUnknown(self, variable):
        self.addVariableTrace(
            variable = variable,
            version  = 0,
            trace    = VariableUnknownTrace(
                variable = variable,
                version  = 0
            )
        )

        self.markCurrentVariableTrace( variable, 0 )

    def initVariableUninit(self, variable):
        self.addVariableTrace(
            variable = variable,
            version  = 0,
            trace    = VariableUninitTrace(
                variable = variable,
                version  = 0
            )
        )

        self.markCurrentVariableTrace( variable, 0 )

    def assumeUnclearLocals(self, source_ref):
        if not self.unclear_locals:
            self.signalChange(
                "new_expression",
                source_ref,
                "Unclear module variable delays processing."
            )

        self.unclear_locals = True


# TODO: This code is only here while staging it, will live in a dedicated module
# later on
class ConstraintCollectionBase(CollectionTracingMixin):
    def __init__(self, parent, signal_change = None):
        CollectionTracingMixin.__init__( self )

        assert signal_change is None or parent is None

        if signal_change is not None:
            self.signalChange = signal_change
        else:
            self.signalChange = parent.signalChange

        self.parent = parent

        # Trust variable_traces, should go away later on, for now we use it to
        # disable optimization.
        self.removes_knowledge = False

    def mustAlias(self, a, b):
        if a.isExpressionVariableRef() and b.isExpressionVariableRef():
            return a.getVariable() is b.getVariable()

        return False

    def mustNotAlias(self, a, b):
        return False

    def removeKnowledge(self, node):
        assert node.isNode()

    def removeAllKnowledge(self):
        # Temporary, we don't have to have this anyway, this will just disable
        # all uses of variable traces for optimization.
        self.removes_knowledge = True

        self.markActiveVariablesAsUnknown()

    def assumeUnclearLocals(self, source_ref):
        self.parent.assumeUnclearLocals(source_ref)

    def getVariableTrace(self, variable, version):
        return self.parent.getVariableTrace( variable, version )

    def addVariableTrace(self, variable, version, trace):
        assert self.parent is not None, self

        self.parent.addVariableTrace( variable, version, trace )

    def addVariableMergeTrace(self, variable, trace_yes, trace_no):
        assert self.parent is not None, self

        return self.parent.addVariableMergeTrace(variable, trace_yes, trace_no)

    def onVariableSet(self, assign_node):
        if assign_node.isStatementAssignmentVariable():
            target_node = assign_node.getTargetVariableRef()
        else:
            target_node = assign_node

        # Add a new trace, using the version allocated for the variable, and
        # remember the value friend.
        variable = target_node.getVariable()

        assert not variable.isModuleVariable() or variable.isReference(), \
            variable

        # print "SET", target_node, target_node.getVariableVersion()
        version = target_node.getVariableVersion()

        self.addVariableTrace(
            variable = variable,
            version  = version,
            trace    = VariableAssignTrace(
                assign_node = assign_node,
                variable    = variable,
                version     = version
            )
        )

        # Make references point to it.
        self.markCurrentVariableTrace(variable, version)

    def onVariableDel(self, target_node):
        # Add a new trace, allocating a new version for the variable, and
        # remember the delete of the current
        variable = target_node.getVariable()

        current = self.getVariableCurrentTrace( variable )
        current.addRelease( target_node )

        version = target_node.getVariableVersion()

        # Assign to uninit again.
        self.addVariableTrace(
            variable = variable,
            version  = version,
            trace    = VariableUninitTrace(
                variable = variable,
                version  = version
            )
        )

        # Make references point to it.
        self.markCurrentVariableTrace( variable, version )

    def onVariableUsage(self, ref_node):
        variable = ref_node.getVariable()

        self.getVariableCurrentTrace( variable ).addUsage( ref_node )

    def onVariableContentEscapes(self, variable):
        self.getVariableCurrentTrace( variable ).onValueEscape()

    def onExpression(self, expression, allow_none = False):
        if expression is None and allow_none:
            return

        assert expression.isExpression(), expression
        assert expression.parent, expression

        # Now compute this expression, allowing it to replace itself with
        # something else as part of a local peephole optimization.
        r = expression.computeExpressionRaw(
            constraint_collection = self
        )
        assert type(r) is tuple, expression

        new_node, change_tags, change_desc = r

        if change_tags is not None:
            # This is mostly for tracing and indication that a change occured
            # and it may be interesting to look again.
            self.signalChange(
                change_tags,
                expression.getSourceReference(),
                change_desc
            )

        if new_node is not expression:
            expression.replaceWith(new_node)

        if new_node.isExpressionVariableRef():
            # Remember this for constraint collection. Any variable that we
            # access has a version already that we can query. TODO: May do this
            # as a "computeReference".

            self.onVariableUsage( new_node )

        return new_node

    def onModuleVariableAssigned(self, variable, assign_source):
        self.parent.onModuleVariableAssigned( variable, assign_source )

    def onLocalVariableAssigned(self, variable, assign_source):
        self.parent.onLocalVariableAssigned( variable, assign_source )

    def onTempVariableAssigned(self, variable, assign_source):
        self.parent.onTempVariableAssigned( variable, assign_source )

    def _onStatementAssignmentVariable(self, statement):
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

        if variable.isModuleVariableReference():
            self.onModuleVariableAssigned( variable, source )
        elif variable.isLocalVariable():
            self.onLocalVariableAssigned( variable, source )
        elif variable.isTempVariableReference():
            self.onTempVariableAssigned( variable, source )

        return result

    def onStatement(self, statement):
        try:
            assert statement.isStatement(), statement

            new_statement, change_tags, change_desc = \
              statement.computeStatement(self)

            # print new_statement, change_tags, change_desc
            if new_statement is not statement:
                self.signalChange(
                    change_tags,
                    statement.getSourceReference(),
                    change_desc
                )

            return new_statement
        except Exception:
            Tracing.printError(
                "Problem with statement at %s:" %
                statement.getSourceReference().getAsString()
            )
            raise

    def mergeBranches(self, collection_yes, collection_no):
        # Refuse to do stupid work
        if collection_yes is None and collection_no is None:
            pass
        elif collection_yes is None or collection_no is None:
            # Handle one branch case, we need to merge versions backwards as
            # they may make themselves obsolete.
            collection = collection_yes or collection_no

            for variable in collection.getActiveVariables():
                # print "ACTIVE", variable, self.getCurrentVariableVersion( variable )

                trace_old = self.getVariableCurrentTrace(variable)
                trace_new = collection.getVariableCurrentTrace(variable)

                assert trace_old is not None
                assert trace_new is not None

                if trace_old is not trace_new:
                    version = self.addVariableMergeTrace(
                        variable  = variable,
                        trace_yes = trace_new,
                        trace_no  = trace_old
                    )

                    self.markCurrentVariableTrace(variable, version)

            return
        else:
            for variable in collection_yes.getActiveVariables():
                trace_yes = collection_yes.getVariableCurrentTrace(variable)
                trace_no = collection_no.getVariableCurrentTrace(variable)

                if trace_yes is not trace_no:
                    version = self.addVariableMergeTrace(
                        variable  = variable,
                        trace_yes = trace_yes,
                        trace_no  = trace_no
                    )

                    self.markCurrentVariableTrace(variable, version)


class ConstraintCollectionBranch(ConstraintCollectionBase):
    def __init__(self, parent, branch):
        ConstraintCollectionBase.__init__(
            self,
            parent = parent
        )

        self.variable_actives = dict(parent.variable_actives)

        if branch.isStatementsSequence():
            result = branch.computeStatementsSequence(
                constraint_collection = self
            )

            if result is not branch:
                branch.replaceWith(result)
        else:
            self.onExpression(
                expression = branch
            )


    def mergeBranches(self, collection_yes, collection_no):
        # Branches in branches, should ask parent about merging them.
        return self.parent.mergeBranches( collection_yes, collection_no )

    # TODO: This make go away once we have keeper variables better covered.
    def initVariableUninit(self, variable):
        self.parent.initVariableUninit( variable )

        self.markCurrentVariableTrace( variable, 0 )


class ConstraintCollectionFunction(CollectionStartpointMixin,
                                   ConstraintCollectionBase,
                                   VariableUsageTrackingMixin):
    def __init__(self, parent, function_body):
        assert function_body.isExpressionFunctionBody(), function_body

        CollectionStartpointMixin.__init__(self)

        ConstraintCollectionBase.__init__(
            self,
            parent = parent
        )

        VariableUsageTrackingMixin.__init__(self)

        self.function_body = function_body

        statements_sequence = function_body.getBody()

        if statements_sequence is not None and \
           not statements_sequence.getStatements():
            function_body.setStatements( None )
            statements_sequence = None

        self.setupVariableTraces(function_body)

        if statements_sequence is not None:
            result = statements_sequence.computeStatementsSequence(
                constraint_collection = self
            )

            if result is not statements_sequence:
                function_body.setBody(result)

        # TODO: Should become trace based as well.
        self.setIndications()
        # self.dumpTraces()

        self.makeVariableTraceOptimizations(function_body)

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

            if variable.isLocalVariable() and not variable.isSharedLogically():
                if variable_trace.isAssignTrace():
                    assign_node = variable_trace.getAssignNode()

                    if not assign_node.getAssignSource().mayHaveSideEffects():

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


    def __repr__(self):
        return "<ConstraintCollectionFunction for %s>" % self.function_body

    def onLocalVariableAssigned(self, variable, assign_source):
        self._getVariableUsage( variable ).markAsWrittenTo( assign_source )

    def onTempVariableAssigned(self, variable, assign_source):
        variable = variable.getReferenced()
        # assert variable.getOwner() is self.function_body

        self._getVariableUsage(variable).markAsWrittenTo(assign_source)


class ConstraintCollectionModule(CollectionStartpointMixin,
                                 ConstraintCollectionBase,
                                 VariableUsageTrackingMixin):
    def __init__(self, signal_change, module):
        assert module.isPythonModule()

        CollectionStartpointMixin.__init__( self )

        ConstraintCollectionBase.__init__(
            self,
            None,
            signal_change = signal_change
        )

        VariableUsageTrackingMixin.__init__( self )

        self.module = module

        self.setupVariableTraces( module )

        module_body = module.getBody()

        if module_body is not None:
            result = module_body.computeStatementsSequence(
                constraint_collection = self
            )

            if result is not module_body:
                module.setBody(result)

        self.setIndications()

        self.makeVariableTraceOptimizations( module )

    def onModuleVariableAssigned(self, variable, assign_source):
        while variable.isModuleVariableReference():
            variable = variable.getReferenced()

        self._getVariableUsage( variable ).markAsWrittenTo( assign_source )

    def onTempVariableAssigned(self, variable, assign_source):
        variable = variable.getReferenced()

        self._getVariableUsage( variable ).markAsWrittenTo(assign_source)

    def getWrittenVariables(self):
        return [
            variable
            for variable, usage in iterItems(self.variable_usages)
            if not usage.isReadOnly()
        ]
