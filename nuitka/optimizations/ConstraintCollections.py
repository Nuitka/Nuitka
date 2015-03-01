#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka import Options, Tracing, Utils
from nuitka.__past__ import iterItems
from nuitka.nodes.AssignNodes import StatementDelVariable
from nuitka.VariableRegistry import isSharedLogically

from .VariableTraces import (
    VariableAssignTrace,
    VariableInitTrace,
    VariableMergeTrace,
    VariableUninitTrace,
    VariableUnknownTrace
)

signalChange = None

# TODO: This will be removed, to be replaced by variable trace information.
class VariableUsageProfile:
    def __init__(self, variable):
        self.variable = variable

        self.written_to = False

    def markAsWrittenTo(self):
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
            self.variable_usages[ variable ] = VariableUsageProfile(variable)

            return self.variable_usages[ variable ]

    def _initVariable(self, variable):
        if variable.isParameterVariable():
            self._initVariableInit(variable)
        elif variable.isLocalVariable():
            self._initVariableUninit(variable)
        elif variable.isMaybeLocalVariable():
            self._initVariableUnknown(variable)
        elif variable.isModuleVariable():
            self._initVariableUnknown(variable)
        elif variable.isTempVariable():
            self._initVariableUninit(variable)
        else:
            assert False, variable


    def _makeVariableTraceOptimization(self, owner, variable_trace):
        variable = variable_trace.getVariable()

        if variable.isTempVariable():
            if variable.getOwner() is owner:

                if variable_trace.isUninitTrace() and \
                   variable_trace.getVersion() == 0:
                    if self.getVariableCurrentTrace(variable) is variable_trace:
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
                print("Problem with", variable_trace, "in", owner)
                raise


class CollectionTracingMixin:
    def __init__(self):
        # For functions, when we are in here, the currently active one,
        self.variable_actives = {}

    def getVariableCurrentTrace(self, variable):
        # Initialize variables on the fly.
        if variable not in self.variable_actives:
            self._initVariable(variable)

        return self.getVariableTrace(
            variable = variable,
            version  = self.getCurrentVariableVersion(variable)
        )

    def markCurrentVariableTrace(self, variable, version):
        self.variable_actives[variable] = version

    def getCurrentVariableVersion(self, variable):
        assert variable in self.variable_actives, (variable, self)
        return self.variable_actives[variable]

    def getActiveVariables(self):
        return tuple(self.variable_actives.keys())

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
                    version  = version,
                    previous = current
                )
            )

            self.markCurrentVariableTrace(variable, version)

    def markActiveVariablesAsUnknown(self):
        for variable in self.getActiveVariables():
            self.markActiveVariableAsUnknown(variable)


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
        return self.variable_traces[(variable, version)]

    def getVariableTraces(self, variable):
        result = []

        for key, variable_trace in iterItems(self.variable_traces):
            candidate = key[0]

            if variable is candidate:
                result.append(variable_trace)

        return result

    def addVariableTrace(self, variable, version, trace):
        key = variable, version

        assert key not in self.variable_traces, (key, self)
        self.variable_traces[key] = trace

    def addVariableMergeTrace(self, variable, trace_yes, trace_no):
        version = variable.allocateTargetNumber()
        trace_merge = VariableMergeTrace(
            variable  = variable,
            version   = version,
            trace_yes = trace_yes,
            trace_no  = trace_no
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

    def _initVariableUnknown(self, variable):
        self.addVariableTrace(
            variable = variable,
            version  = 0,
            trace    = VariableUnknownTrace(
                variable = variable,
                version  = 0,
                previous = None
            )
        )

        self.markCurrentVariableTrace(variable, 0)

    def _initVariableInit(self, variable):
        self.addVariableTrace(
            variable = variable,
            version  = 0,
            trace    = VariableInitTrace(
                variable = variable,
                version  = 0,
            )
        )

        self.markCurrentVariableTrace(variable, 0)

    def _initVariableUninit(self, variable):
        self.addVariableTrace(
            variable = variable,
            version  = 0,
            trace    = VariableUninitTrace(
                variable = variable,
                version  = 0,
                previous = None
            )
        )

        self.markCurrentVariableTrace(variable, 0)

    def assumeUnclearLocals(self, source_ref):
        if not self.unclear_locals:
            self.signalChange(
                "new_expression",
                source_ref,
                "Unclear module variable delays processing."
            )

        self.unclear_locals = True


class ConstraintCollectionBase(CollectionTracingMixin):
    def __init__(self, parent):
        CollectionTracingMixin.__init__(self)

        self.parent = parent

        # Trust variable_traces, should go away later on, for now we use it to
        # disable optimization.
        self.removes_knowledge = False

    @staticmethod
    def signalChange(tags, source_ref, message):
        # This is monkey patches from another module, pylint: disable=E1102
        signalChange(tags, source_ref, message)

    @staticmethod
    def mustAlias(a, b):
        if a.isExpressionVariableRef() and b.isExpressionVariableRef():
            return a.getVariable() is b.getVariable()

        return False

    @staticmethod
    def mustNotAlias(a, b):
        # TODO: not yet really implemented, pylint: disable=W0613
        return False

    def removeKnowledge(self, node):
        pass

    def onControlFlowEscape(self, node):
        # TODO: One day, we should trace which nodes exactly cause a variable
        # to be considered escaped, pylint: disable=W0613

        for variable in self.getActiveVariables():
            if variable.isModuleVariable():
                # print variable

                self.markActiveVariableAsUnknown(variable)

            elif Utils.python_version >= 300 or variable.isSharedTechnically():
                # print variable

                # TODO: Could be limited to shared variables that are actually
                # written to. Most of the time, that won't be the case.

                self.markActiveVariableAsUnknown(variable)


    def removeAllKnowledge(self):
        # Temporary, we don't have to have this anyway, this will just disable
        # all uses of variable traces for optimization.
        self.removes_knowledge = True

        self.markActiveVariablesAsUnknown()

    def assumeUnclearLocals(self, source_ref):
        self.parent.assumeUnclearLocals(source_ref)

    def getVariableTrace(self, variable, version):
        return self.parent.getVariableTrace(variable, version)

    def addVariableTrace(self, variable, version, trace):
        assert self.parent is not None, self

        self.parent.addVariableTrace(variable, version, trace)

    def addVariableMergeTrace(self, variable, trace_yes, trace_no):
        assert self.parent is not None, self

        return self.parent.addVariableMergeTrace(variable, trace_yes, trace_no)

    def onVariableSet(self, assign_node):
        variable_ref = assign_node.getTargetVariableRef()

        version = variable_ref.getVariableVersion()
        variable = variable_ref.getVariable()

        variable_trace = VariableAssignTrace(
            assign_node = assign_node,
            variable    = variable,
            version     = version,
            previous    = self.getVariableCurrentTrace(
                variable = variable
            )
        )

        self.addVariableTrace(
            variable = variable,
            version  = version,
            trace    = variable_trace
        )

        # Make references point to it.
        self.markCurrentVariableTrace(variable, version)

        return variable_trace


    def onVariableDel(self, del_node):
        # Add a new trace, allocating a new version for the variable, and
        # remember the delete of the current
        variable_ref = del_node.getTargetVariableRef()

        version = variable_ref.getVariableVersion()
        variable = variable_ref.getVariable()

        old_trace = self.getVariableCurrentTrace(variable)

        variable_trace = VariableUninitTrace(
            variable = variable,
            version  = version,
            previous = old_trace
        )

        # Assign to not initialized again.
        self.addVariableTrace(
            variable = variable,
            version  = version,
            trace    = variable_trace
        )

        # Make references point to it.
        self.markCurrentVariableTrace(variable, version)

        return old_trace

    def onVariableRelease(self, release_node):
        variable = release_node.getVariable()

        current = self.getVariableCurrentTrace(variable)

        # Annotate that release node. It's an unimportant usage, but one we
        # would like to be able to remove, should we remove the assignment
        # that underlies it.
        current.addRelease(release_node)

        return current


    def onVariableContentEscapes(self, variable):
        self.getVariableCurrentTrace(variable).onValueEscape()

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
            # This is mostly for tracing and indication that a change occurred
            # and it may be interesting to look again.
            self.signalChange(
                change_tags,
                expression.getSourceReference(),
                change_desc
            )

        if new_node is not expression:
            expression.replaceWith(new_node)

        # We add variable reference nodes late to their traces, only after they
        # are actually produced, and not resolved to something else, so we do
        # not have them dangling, and the code complexity inside of their own
        # "computeExpression" functions.
        if new_node.isExpressionVariableRef() or \
           new_node.isExpressionTempVariableRef():
            # Remember the reference for constraint collection.
            new_node.variable_trace.addUsage(new_node)

            if new_node.getVariable().isMaybeLocalVariable():
                variable_trace = self.getVariableCurrentTrace(
                    variable = new_node.getVariable().getMaybeVariable()
                )
                variable_trace.addUsage(new_node)

        return new_node

    def onModuleVariableAssigned(self, variable):
        self.parent.onModuleVariableAssigned(variable)

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


    def _initVariable(self, variable):
        variable_trace = self.parent.getVariableCurrentTrace(variable)

        self.variable_actives[variable] = variable_trace.getVersion()


class ConstraintCollectionFunction(CollectionStartpointMixin,
                                   ConstraintCollectionBase,
                                   VariableUsageTrackingMixin):
    def __init__(self, parent, function_body):
        # Too complex stuff here, but could be improved, just not now.
        # pylint: disable=R0912

        assert function_body.isExpressionFunctionBody(), function_body

        CollectionStartpointMixin.__init__(self)

        ConstraintCollectionBase.__init__(
            self,
            parent = parent
        )

        VariableUsageTrackingMixin.__init__(self)

        self.function_body = function_body
        function_body.constraint_collection = self

        statements_sequence = function_body.getBody()

        if statements_sequence is not None and \
           not statements_sequence.getStatements():
            function_body.setStatements(None)
            statements_sequence = None

        if statements_sequence is not None:
            result = statements_sequence.computeStatementsSequence(
                constraint_collection = self
            )

            if result is not statements_sequence:
                function_body.setBody(result)

        self.makeVariableTraceOptimizations(function_body)

        if not Options.isExperimental() or self.removes_knowledge:
            return

        # self.dumpTrace()

        # Cannot mess with locals yet.
        if self.unclear_locals:
            return

        # TODO: Merge this into makeVariableTraceOptimizations instead, could
        # check the above for these too.
        # Trace based optimization goes here:
        for variable_trace in self.variable_traces.values():
            variable = variable_trace.getVariable()

            # print variable

            if variable.isLocalVariable() and not isSharedLogically(variable):
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



class ConstraintCollectionModule(CollectionStartpointMixin,
                                 ConstraintCollectionBase,
                                 VariableUsageTrackingMixin):
    def __init__(self):
        CollectionStartpointMixin.__init__(self)

        ConstraintCollectionBase.__init__(
            self,
            parent = None
        )

        VariableUsageTrackingMixin.__init__(self)


    def onModuleVariableAssigned(self, variable):
        assert variable.isModuleVariable()

        self._getVariableUsage(variable).markAsWrittenTo()

    def getWrittenVariables(self):
        return [
            variable
            for variable, usage in iterItems(self.variable_usages)
            if not usage.isReadOnly()
        ]
