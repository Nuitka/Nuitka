#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Trace collection (also often still referred to as constraint collection).

At the core of value propagation there is the collection of constraints that
allow to propagate knowledge forward or not.

This is about collecting these constraints and to manage them.
"""

import contextlib
from collections import defaultdict
from contextlib import contextmanager

from nuitka import Variables
from nuitka.__past__ import iterItems  # Python3 compatibility.
from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.ModuleRegistry import addUsedModule
from nuitka.nodes.NodeMakingHelpers import getComputationResult
from nuitka.nodes.shapes.StandardShapes import tshape_uninitialized
from nuitka.Tracing import (
    inclusion_logger,
    printError,
    printLine,
    printSeparator,
)
from nuitka.tree.SourceHandling import readSourceLine
from nuitka.utils.InstanceCounters import (
    counted_del,
    counted_init,
    isCountingInstances,
)
from nuitka.utils.Timing import TimerReport

from .ValueTraces import (
    ValueTraceAssign,
    ValueTraceAssignUnescapable,
    ValueTraceAssignUnescapablePropagated,
    ValueTraceAssignVeryTrusted,
    ValueTraceDeleted,
    ValueTraceEscaped,
    ValueTraceInit,
    ValueTraceInitStarArgs,
    ValueTraceInitStarDict,
    ValueTraceLoopComplete,
    ValueTraceLoopIncomplete,
    ValueTraceMerge,
    ValueTraceUninitialized,
    ValueTraceUnknown,
)

# Keeping trace of how often branches are merged between calls
_merge_counts = defaultdict(int)


def fetchMergeCounts():
    result = dict(_merge_counts)
    _merge_counts.clear()
    return result


signalChange = None


@contextmanager
def withChangeIndicationsTo(signal_change):
    """Decide where change indications should go to."""

    global signalChange  # Singleton, pylint: disable=global-statement

    old = signalChange
    signalChange = signal_change
    yield
    signalChange = old


class CollectionUpdateMixin(object):
    """Mixin to use in every collection to add traces."""

    # Mixins are not allowed to specify slots.
    __slots__ = ()

    def hasVariableTrace(self, variable, version):
        return (variable, version) in self.variable_traces

    def getVariableTrace(self, variable, version):
        return self.variable_traces[(variable, version)]

    def getVariableTraces(self, variable):
        result = []

        for key, variable_trace in iterItems(self.variable_traces):
            candidate = key[0]

            if variable is candidate:
                result.append(variable_trace)

        return result

    def getVariableTracesAll(self):
        return self.variable_traces

    def addVariableTrace(self, variable, version, trace):
        key = variable, version

        assert key not in self.variable_traces, (key, self)
        self.variable_traces[key] = trace

    def addVariableMergeMultipleTrace(self, variable, traces):
        version = variable.allocateTargetNumber()

        trace_merge = ValueTraceMerge(traces)

        self.addVariableTrace(variable, version, trace_merge)

        return version


class CollectionStartPointMixin(CollectionUpdateMixin):
    """Mixin to use in start points of collections.

    These are modules, functions, etc. typically entry points.
    """

    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # Many things are traced

    def __init__(self):
        # Variable assignments performed in here, last issued number, only used
        # to determine the next number that should be used for a new assignment.
        self.variable_versions = {}

        # The full trace of a variable with a version for the function or module
        # this is.
        self.variable_traces = {}

        self.break_collections = None
        self.continue_collections = None
        self.return_collections = None
        self.exception_collections = None

        self.outline_functions = None

    def getLoopBreakCollections(self):
        return self.break_collections

    def onLoopBreak(self, collection=None):
        if collection is None:
            collection = self

        self.break_collections.append(
            TraceCollectionBranch(parent=collection, name="loop break")
        )

    def getLoopContinueCollections(self):
        return self.continue_collections

    def onLoopContinue(self, collection=None):
        if collection is None:
            collection = self

        self.continue_collections.append(
            TraceCollectionBranch(parent=collection, name="loop continue")
        )

    def onFunctionReturn(self, collection=None):
        if collection is None:
            collection = self

        if self.return_collections is not None:
            self.return_collections.append(
                TraceCollectionBranch(parent=collection, name="return")
            )

    def onExceptionRaiseExit(self, raisable_exceptions, collection=None):
        """Indicate to the trace collection what exceptions may have occurred.

        Args:
            raisable_exception: Currently ignored, one or more exceptions that
            could occur, e.g. "BaseException".
            collection: To pass the collection that will be the parent
        Notes:
            Currently this is unused. Passing "collection" as an argument, so
            we know the original collection to attach the branch to, is maybe
            not the most clever way to do this

            We also might want to specialize functions for specific exceptions,
            there is little point in providing BaseException as an argument in
            so many places.

            The actual storage of the exceptions that can occur is currently
            missing entirely. We just use this to detect "any exception" by
            not being empty.
        """

        # TODO: We might want to track per exception, pylint: disable=unused-argument

        if self.exception_collections is not None:
            if collection is None:
                collection = self

            self.exception_collections.append(
                TraceCollectionBranch(parent=collection, name="exception")
            )

    def getFunctionReturnCollections(self):
        return self.return_collections

    def getExceptionRaiseCollections(self):
        return self.exception_collections

    def hasEmptyTraces(self, variable):
        # TODO: Combine these steps into one for performance gains.
        traces = self.getVariableTraces(variable)
        return areEmptyTraces(traces)

    def hasReadOnlyTraces(self, variable):
        # TODO: Combine these steps into one for performance gains.
        traces = self.getVariableTraces(variable)
        return areReadOnlyTraces(traces)

    def initVariableUnknown(self, variable):
        trace = ValueTraceUnknown(owner=self.owner, previous=None)

        self.addVariableTrace(variable, 0, trace)

        return trace

    def initVariableModule(self, variable):
        trace = ValueTraceUnknown(owner=self.owner, previous=None)

        self.addVariableTrace(variable, 0, trace)

        return trace

    def initVariableInit(self, variable):
        trace = ValueTraceInit(self.owner)

        self.addVariableTrace(variable, 0, trace)

        return trace

    def initVariableInitStarArgs(self, variable):
        trace = ValueTraceInitStarArgs(self.owner)

        self.addVariableTrace(variable, 0, trace)

        return trace

    def initVariableInitStarDict(self, variable):
        trace = ValueTraceInitStarDict(self.owner)

        self.addVariableTrace(variable, 0, trace)

        return trace

    def initVariableUninitialized(self, variable):
        trace = ValueTraceUninitialized(owner=self.owner, previous=None)

        self.addVariableTrace(variable, 0, trace)

        return trace

    def updateVariablesFromCollection(self, old_collection, source_ref):
        Variables.updateVariablesFromCollection(old_collection, self, source_ref)

    @contextlib.contextmanager
    def makeAbortStackContext(
        self, catch_breaks, catch_continues, catch_returns, catch_exceptions
    ):
        if catch_breaks:
            old_break_collections = self.break_collections
            self.break_collections = []
        if catch_continues:
            old_continue_collections = self.continue_collections
            self.continue_collections = []
        if catch_returns:
            old_return_collections = self.return_collections
            self.return_collections = []
        if catch_exceptions:
            old_exception_collections = self.exception_collections
            self.exception_collections = []

        yield

        if catch_breaks:
            self.break_collections = old_break_collections
        if catch_continues:
            self.continue_collections = old_continue_collections
        if catch_returns:
            self.return_collections = old_return_collections
        if catch_exceptions:
            self.exception_collections = old_exception_collections

    def initVariable(self, variable):
        return variable.initVariable(self)

    def addOutlineFunction(self, outline):
        if self.outline_functions is None:
            self.outline_functions = [outline]
        else:
            self.outline_functions.append(outline)

    def getOutlineFunctions(self):
        return self.outline_functions

    def onLocalsDictEscaped(self, locals_scope):
        locals_scope.preventLocalsDictPropagation()

        for variable in locals_scope.variables.values():
            self.markActiveVariableAsEscaped(variable)

        # TODO: Limit to the scope.
        # TODO: Does the above code not do that already?
        for variable in self.variable_actives:
            if variable.isTempVariable() or variable.isModuleVariable():
                continue

            self.markActiveVariableAsEscaped(variable)

    def onUsedFunction(self, function_body):
        owning_module = function_body.getParentModule()

        # Make sure the owning module is added to the used set. This is most
        # important for helper functions, or modules, which otherwise have
        # become unused.
        addUsedModule(
            module=owning_module,
            using_module=None,
            usage_tag="function",
            reason="Function %s" % self.name,
            source_ref=owning_module.source_ref,
        )

        needs_visit = owning_module.addUsedFunction(function_body)

        if needs_visit or function_body.isExpressionFunctionPureBody():
            function_body.computeFunctionRaw(self)


class TraceCollectionBase(object):
    """This contains for logic for maintaining active traces.

    They are kept for "variable" and versions.
    """

    __slots__ = ("owner", "parent", "name", "variable_actives")

    if isCountingInstances():
        __del__ = counted_del()

    @counted_init
    def __init__(self, owner, name, parent):
        self.owner = owner
        self.parent = parent
        self.name = name

        # Currently active values in the tracing.
        self.variable_actives = {}

    def __repr__(self):
        return "<%s for %s at 0x%x>" % (self.__class__.__name__, self.name, id(self))

    def getOwner(self):
        return self.owner

    def dumpActiveTraces(self, indent=""):
        printSeparator()
        printLine("Active are:")
        for variable, version in sorted(
            self.variable_actives.items(), key=lambda var: var[0].variable_name
        ):
            printLine("%s %s:" % (variable, version))
            self.getVariableCurrentTrace(variable).dump(indent)

        printSeparator()

    def getVariableCurrentTrace(self, variable):
        """Get the current value trace associated to this variable

        It is also created on the fly if necessary. We create them
        lazy so to keep the tracing branches minimal where possible.
        """

        return self.getVariableTrace(
            variable=variable, version=self._getCurrentVariableVersion(variable)
        )

    def markCurrentVariableTrace(self, variable, version):
        self.variable_actives[variable] = version

    def _getCurrentVariableVersion(self, variable):
        try:
            return self.variable_actives[variable]
        except KeyError:
            # Initialize variables on the fly.
            if not self.hasVariableTrace(variable, 0):
                self.initVariable(variable)

            self.markCurrentVariableTrace(variable, 0)

            return self.variable_actives[variable]

    def markActiveVariableAsEscaped(self, variable):
        current = self.getVariableCurrentTrace(variable)

        if current.isTraceThatNeedsEscape():
            version = variable.allocateTargetNumber()

            self.addVariableTrace(
                variable,
                version,
                ValueTraceEscaped(owner=self.owner, previous=current),
            )

            self.markCurrentVariableTrace(variable, version)

    def markClosureVariableAsUnknown(self, variable):
        current = self.getVariableCurrentTrace(variable)

        if not current.isUnknownTrace():
            version = variable.allocateTargetNumber()

            self.addVariableTrace(
                variable,
                version,
                ValueTraceUnknown(owner=self.owner, previous=current),
            )

            self.markCurrentVariableTrace(variable, version)

    def markActiveVariableAsUnknown(self, variable):
        current = self.getVariableCurrentTrace(variable)

        if not current.isUnknownOrVeryTrustedTrace():
            version = variable.allocateTargetNumber()

            self.addVariableTrace(
                variable,
                version,
                ValueTraceUnknown(owner=self.owner, previous=current),
            )

            self.markCurrentVariableTrace(variable, version)

    def markActiveVariableAsLoopMerge(
        self, loop_node, current, variable, shapes, incomplete
    ):
        if incomplete:
            result = ValueTraceLoopIncomplete(loop_node, current, shapes)
        else:
            # TODO: Empty is a missing optimization somewhere, but it also happens that
            # a variable is getting released in a loop.
            # assert shapes, (variable, current)

            if not shapes:
                shapes.add(tshape_uninitialized)

            result = ValueTraceLoopComplete(loop_node, current, shapes)

        version = variable.allocateTargetNumber()
        self.addVariableTrace(variable, version, result)

        self.markCurrentVariableTrace(variable, version)

        return result

    @staticmethod
    def signalChange(tags, source_ref, message):
        # This is monkey patched from another module. pylint: disable=I0021,not-callable
        signalChange(tags, source_ref, message)

    @staticmethod
    def mustAlias(a, b):
        if a.isExpressionVariableRef() and b.isExpressionVariableRef():
            return a.getVariable() is b.getVariable()

        return False

    @staticmethod
    def mustNotAlias(a, b):
        # TODO: not yet really implemented
        if a.isExpressionConstantRef() and b.isExpressionConstantRef():
            if a.isMutable() or b.isMutable():
                return True

        return False

    def onControlFlowEscape(self, node):
        # TODO: One day, we should trace which nodes exactly cause a variable
        # to be considered escaped, pylint: disable=unused-argument
        for variable in self.variable_actives:
            variable.onControlFlowEscape(self)

    def removeKnowledge(self, node):
        if node.isExpressionVariableRef():
            node.variable.removeKnowledge(self)

    def onValueEscapeStr(self, node):
        # TODO: We can ignore these for now.
        pass

    def removeAllKnowledge(self):
        for variable in self.variable_actives:
            variable.removeAllKnowledge(self)

    def onVariableSet(self, variable, version, assign_node):
        variable_trace = ValueTraceAssign(
            owner=self.owner,
            assign_node=assign_node,
            previous=self.getVariableCurrentTrace(variable),
        )

        self.addVariableTrace(variable, version, variable_trace)

        # Make references point to it.
        self.markCurrentVariableTrace(variable, version)

        return variable_trace

    def onVariableSetAliasing(self, variable, version, assign_node, source):
        other_variable_trace = source.variable_trace

        if other_variable_trace.__class__ is ValueTraceAssignUnescapable:
            return self.onVariableSetToUnescapableValue(
                variable=variable, version=version, assign_node=assign_node
            )
        elif other_variable_trace.__class__ is ValueTraceAssignVeryTrusted:
            return self.onVariableSetToVeryTrustedValue(
                variable=variable, version=version, assign_node=assign_node
            )
        else:
            result = self.onVariableSet(
                variable=variable, version=version, assign_node=assign_node
            )

            self.removeKnowledge(source)

            return result

    def onVariableSetToUnescapableValue(self, variable, version, assign_node):
        variable_trace = ValueTraceAssignUnescapable(
            owner=self.owner,
            assign_node=assign_node,
            previous=self.getVariableCurrentTrace(variable),
        )

        self.addVariableTrace(variable, version, variable_trace)

        # Make references point to it.
        self.markCurrentVariableTrace(variable, version)

        return variable_trace

    def onVariableSetToVeryTrustedValue(self, variable, version, assign_node):
        variable_trace = ValueTraceAssignVeryTrusted(
            owner=self.owner,
            assign_node=assign_node,
            previous=self.getVariableCurrentTrace(variable),
        )

        self.addVariableTrace(variable, version, variable_trace)

        # Make references point to it.
        self.markCurrentVariableTrace(variable, version)

        return variable_trace

    def onVariableSetToUnescapablePropagatedValue(
        self, variable, version, assign_node, replacement
    ):
        variable_trace = ValueTraceAssignUnescapablePropagated(
            owner=self.owner,
            assign_node=assign_node,
            previous=self.getVariableCurrentTrace(variable),
            replacement=replacement,
        )

        self.addVariableTrace(variable, version, variable_trace)

        # Make references point to it.
        self.markCurrentVariableTrace(variable, version)

        return variable_trace

    def onVariableDel(self, variable, version, del_node):
        # Add a new trace, allocating a new version for the variable, and
        # remember the delete of the current
        old_trace = self.getVariableCurrentTrace(variable)

        # TODO: Annotate value content as escaped.

        variable_trace = ValueTraceDeleted(
            owner=self.owner, del_node=del_node, previous=old_trace
        )

        # Assign to not initialized again.
        self.addVariableTrace(variable, version, variable_trace)

        # Make references point to it.
        self.markCurrentVariableTrace(variable, version)

        return variable_trace

    def onLocalsUsage(self, locals_scope):
        self.onLocalsDictEscaped(locals_scope)

        result = []

        scope_locals_variables = locals_scope.getLocalsRelevantVariables()

        for variable in self.variable_actives:
            if variable.isLocalVariable() and variable in scope_locals_variables:
                variable_trace = self.getVariableCurrentTrace(variable)

                variable_trace.addNameUsage()
                result.append((variable, variable_trace))

        return result

    def onVariableContentEscapes(self, variable):
        self.markActiveVariableAsEscaped(variable)

    def onExpression(self, expression, allow_none=False):
        if expression is None and allow_none:
            return None

        parent = expression.parent
        assert parent, expression

        # Now compute this expression, allowing it to replace itself with
        # something else as part of a local peep hole optimization.
        new_node, change_tags, change_desc = expression.computeExpressionRaw(self)

        if change_tags is not None:
            # This is mostly for tracing and indication that a change occurred
            # and it may be interesting to look again.
            self.signalChange(change_tags, expression.getSourceReference(), change_desc)

        if new_node is not expression:
            parent.replaceChild(expression, new_node)

        return new_node

    def onStatement(self, statement):
        try:
            new_statement, change_tags, change_desc = statement.computeStatement(self)

            # print new_statement, change_tags, change_desc
            if new_statement is not statement:
                self.signalChange(
                    change_tags, statement.getSourceReference(), change_desc
                )

            return new_statement
        except Exception:
            printError(
                "Problem with statement at %s:\n-> %s"
                % (
                    statement.source_ref.getAsString(),
                    readSourceLine(statement.source_ref),
                )
            )
            raise

    def computedStatementResult(self, statement, change_tags, change_desc):
        """Make sure the replacement statement is computed.

        Use this when a replacement expression needs to be seen by the trace
        collection and be computed, without causing any duplication, but where
        otherwise there would be loss of annotated effects.

        This may e.g. be true for nodes that need an initial run to know their
        exception result and type shape.
        """
        # Need to compute the replacement still.
        new_statement = statement.computeStatement(self)

        if new_statement[0] is not statement:
            # Signal intermediate result as well.
            self.signalChange(change_tags, statement.getSourceReference(), change_desc)

            return new_statement
        else:
            return statement, change_tags, change_desc

    def computedExpressionResult(self, expression, change_tags, change_desc):
        """Make sure the replacement expression is computed.

        Use this when a replacement expression needs to be seen by the trace
        collection and be computed, without causing any duplication, but where
        otherwise there would be loss of annotated effects.

        This may e.g. be true for nodes that need an initial run to know their
        exception result and type shape.
        """

        # Need to compute the replacement still.
        new_expression = expression.computeExpression(self)

        if new_expression[0] is not expression:
            # Signal intermediate result as well.
            self.signalChange(change_tags, expression.getSourceReference(), change_desc)

            return new_expression
        else:
            return expression, change_tags, change_desc

    def computedExpressionResultRaw(self, expression, change_tags, change_desc):
        """Make sure the replacement expression is computed.

        Use this when a replacement expression needs to be seen by the trace
        collection and be computed, without causing any duplication, but where
        otherwise there would be loss of annotated effects.

        This may e.g. be true for nodes that need an initial run to know their
        exception result and type shape.

        This is for raw, i.e. subnodes are not yet computed automatically.
        """

        # Need to compute the replacement still.
        new_expression = expression.computeExpressionRaw(self)

        if new_expression[0] is not expression:
            # Signal intermediate result as well.
            self.signalChange(change_tags, expression.getSourceReference(), change_desc)

            return new_expression
        else:
            return expression, change_tags, change_desc

    def mergeBranches(self, collection_yes, collection_no):
        """Merge two alternative branches into this trace.

        This is mostly for merging conditional branches, or other ways
        of having alternative control flow. This deals with up to two
        alternative branches to both change this collection.
        """

        # Many branches due to inlining the actual merge and preparing it
        # pylint: disable=too-many-branches

        if collection_yes is None:
            if collection_no is not None:
                # Handle one branch case, we need to merge versions backwards as
                # they may make themselves obsolete.
                collection1 = self
                collection2 = collection_no
            else:
                # Refuse to do stupid work
                return
        elif collection_no is None:
            # Handle one branch case, we need to merge versions backwards as
            # they may make themselves obsolete.
            collection1 = self
            collection2 = collection_yes
        else:
            # Handle two branch case, they may or may not do the same things.
            collection1 = collection_yes
            collection2 = collection_no

        _merge_counts[2] += 1

        variable_versions = {}

        for variable, version in iterItems(collection1.variable_actives):
            variable_versions[variable] = version

        for variable, version in iterItems(collection2.variable_actives):
            if variable not in variable_versions:
                if version != 0:
                    variable_versions[variable] = 0, version
                else:
                    variable_versions[variable] = 0
            else:
                other = variable_versions[variable]

                if other != version:
                    variable_versions[variable] = other, version

        # That would not be fast, pylint: disable=consider-using-dict-items
        for variable in variable_versions:
            if variable not in collection2.variable_actives:
                if variable_versions[variable] != 0:
                    variable_versions[variable] = variable_versions[variable], 0

        self.variable_actives = {}

        for variable, versions in iterItems(variable_versions):
            if type(versions) is tuple:
                trace1 = self.getVariableTrace(variable, versions[0])
                trace2 = self.getVariableTrace(variable, versions[1])

                if trace1.isEscapeTrace() and trace1.previous is trace2:
                    version = versions[0]
                elif trace2.isEscapeTrace() and trace2.previous is trace1:
                    version = versions[1]
                else:
                    version = self.addVariableMergeMultipleTrace(
                        variable=variable,
                        traces=(
                            trace1,
                            trace2,
                        ),
                    )
            else:
                version = versions

            self.markCurrentVariableTrace(variable, version)

    def mergeMultipleBranches(self, collections):
        # This one is really complex, pylint: disable=too-many-branches

        assert collections

        # Optimize for length 1, which is trivial merge and needs not a
        # lot of work, and length 2 has dedicated code as it's so frequent.
        merge_size = len(collections)

        if merge_size == 1:
            self.replaceBranch(collections[0])
            return
        elif merge_size == 2:
            return self.mergeBranches(*collections)

        _merge_counts[len(collections)] += 1

        with TimerReport(
            message="Running merge for %s took %%.2f seconds" % collections,
            decider=False,
        ):
            variable_versions = defaultdict(OrderedSet)

            for collection in collections:
                for variable, version in iterItems(collection.variable_actives):
                    variable_versions[variable].add(version)

            for collection in collections:
                for variable, versions in iterItems(variable_versions):
                    if variable not in collection.variable_actives:
                        versions.add(0)

            self.variable_actives = {}

            for variable, versions in iterItems(variable_versions):
                if len(versions) == 1:
                    (version,) = versions
                else:
                    traces = []
                    escaped = []
                    winner_version = None

                    for version in versions:
                        trace = self.getVariableTrace(variable, version)

                        if trace.isEscapeTrace():
                            winner_version = version
                            escaped_trace = trace.previous

                            if escaped_trace in traces:
                                traces.remove(trace.previous)

                            escaped.append(escaped)
                            traces.append(trace)
                        else:
                            if trace not in escaped:
                                traces.append(trace)

                    if len(traces) == 1:
                        version = winner_version
                        assert winner_version is not None
                    else:
                        version = self.addVariableMergeMultipleTrace(
                            variable=variable, traces=tuple(traces)
                        )

                self.markCurrentVariableTrace(variable, version)

            # print("Leave mergeMultipleBranches", len(collections))

    def replaceBranch(self, collection_replace):
        self.variable_actives.update(collection_replace.variable_actives)
        collection_replace.variable_actives = None

        _merge_counts[1] += 1

    def onLoopBreak(self, collection=None):
        if collection is None:
            collection = self

        return self.parent.onLoopBreak(collection)

    def onLoopContinue(self, collection=None):
        if collection is None:
            collection = self

        return self.parent.onLoopContinue(collection)

    def onFunctionReturn(self, collection=None):
        if collection is None:
            collection = self

        return self.parent.onFunctionReturn(collection)

    def onExceptionRaiseExit(self, raisable_exceptions, collection=None):
        if collection is None:
            collection = self

        return self.parent.onExceptionRaiseExit(raisable_exceptions, collection)

    def getLoopBreakCollections(self):
        return self.parent.getLoopBreakCollections()

    def getLoopContinueCollections(self):
        return self.parent.getLoopContinueCollections()

    def getFunctionReturnCollections(self):
        return self.parent.getFunctionReturnCollections()

    def getExceptionRaiseCollections(self):
        return self.parent.getExceptionRaiseCollections()

    def makeAbortStackContext(
        self, catch_breaks, catch_continues, catch_returns, catch_exceptions
    ):
        return self.parent.makeAbortStackContext(
            catch_breaks=catch_breaks,
            catch_continues=catch_continues,
            catch_returns=catch_returns,
            catch_exceptions=catch_exceptions,
        )

    def onLocalsDictEscaped(self, locals_scope):
        self.parent.onLocalsDictEscaped(locals_scope)

    def getCompileTimeComputationResult(
        self, node, computation, description, user_provided=False
    ):
        new_node, change_tags, message = getComputationResult(
            node=node,
            computation=computation,
            description=description,
            user_provided=user_provided,
        )

        if change_tags == "new_raise":
            self.onExceptionRaiseExit(BaseException)

        return new_node, change_tags, message

    def addOutlineFunction(self, outline):
        self.parent.addOutlineFunction(outline)

    def getVeryTrustedModuleVariables(self):
        return self.parent.getVeryTrustedModuleVariables()

    def onUsedFunction(self, function_body):
        return self.parent.onUsedFunction(function_body)

    def onModuleUsageAttempts(self, module_usage_attempts):
        self.parent.onModuleUsageAttempts(module_usage_attempts)

    def onModuleUsageAttempt(self, module_usage_attempt):
        self.parent.onModuleUsageAttempt(module_usage_attempt)

    def onDistributionUsed(self, distribution_name, node, success):
        self.parent.onDistributionUsed(
            distribution_name=distribution_name, node=node, success=success
        )


class TraceCollectionBranch(CollectionUpdateMixin, TraceCollectionBase):
    __slots__ = ("variable_traces",)

    def __init__(self, name, parent):
        TraceCollectionBase.__init__(self, owner=parent.owner, name=name, parent=parent)

        # Detach from others
        self.variable_actives = dict(parent.variable_actives)

        # For quick access without going to parent.
        self.variable_traces = parent.variable_traces

    def computeBranch(self, branch):
        assert branch.isStatementsSequence()

        result = branch.computeStatementsSequence(self)

        if result is not branch:
            branch.parent.replaceChild(branch, result)

        return result

    def initVariable(self, variable):
        variable_trace = self.parent.initVariable(variable)

        self.variable_actives[variable] = 0

        return variable_trace


class TraceCollectionFunction(CollectionStartPointMixin, TraceCollectionBase):
    __slots__ = (
        "variable_versions",
        "variable_traces",
        "break_collections",
        "continue_collections",
        "return_collections",
        "exception_collections",
        "outline_functions",
        "very_trusted_module_variables",
    )

    def __init__(self, parent, function_body):
        assert (
            function_body.isExpressionFunctionBody()
            or function_body.isExpressionGeneratorObjectBody()
            or function_body.isExpressionCoroutineObjectBody()
            or function_body.isExpressionAsyncgenObjectBody()
        ), function_body

        CollectionStartPointMixin.__init__(self)

        TraceCollectionBase.__init__(
            self,
            owner=function_body,
            name="collection_" + function_body.getCodeName(),
            parent=parent,
        )

        if parent is not None:
            self.very_trusted_module_variables = parent.getVeryTrustedModuleVariables()
        else:
            self.very_trusted_module_variables = ()

        if function_body.isExpressionFunctionBody():
            parameters = function_body.getParameters()

            for parameter_variable in parameters.getTopLevelVariables():
                self.initVariableInit(parameter_variable)
                self.variable_actives[parameter_variable] = 0

            list_star_variable = parameters.getListStarArgVariable()
            if list_star_variable is not None:
                self.initVariableInitStarArgs(list_star_variable)
                self.variable_actives[list_star_variable] = 0

            dict_star_variable = parameters.getDictStarArgVariable()
            if dict_star_variable is not None:
                self.initVariableInitStarDict(dict_star_variable)
                self.variable_actives[dict_star_variable] = 0

        for closure_variable in function_body.getClosureVariables():
            self.initVariableUnknown(closure_variable)
            self.variable_actives[closure_variable] = 0

        # TODO: Have special function type for exec functions stuff.
        locals_scope = function_body.getLocalsScope()

        if locals_scope is not None:
            if not locals_scope.isMarkedForPropagation():
                for locals_dict_variable in locals_scope.variables.values():
                    self.initVariableUninitialized(locals_dict_variable)
            else:
                function_body.locals_scope = None

    def initVariableModule(self, variable):
        trusted_node = self.very_trusted_module_variables.get(variable)

        if trusted_node is None:
            return CollectionStartPointMixin.initVariableModule(self, variable)

        assign_trace = ValueTraceAssignVeryTrusted(
            self.owner, assign_node=trusted_node.getParent(), previous=None
        )

        # This is rare enough to not need a more optimized code.
        self.addVariableTrace(variable, 0, assign_trace)
        self.markActiveVariableAsEscaped(variable)

        return self.getVariableCurrentTrace(variable)


class TraceCollectionPureFunction(TraceCollectionFunction):
    """Pure functions don't feed their parent."""

    __slots__ = ("used_functions",)

    def __init__(self, function_body):
        TraceCollectionFunction.__init__(self, parent=None, function_body=function_body)

        self.used_functions = OrderedSet()

    def getUsedFunctions(self):
        return self.used_functions

    def onUsedFunction(self, function_body):
        self.used_functions.add(function_body)

        TraceCollectionFunction.onUsedFunction(self, function_body=function_body)


class TraceCollectionModule(CollectionStartPointMixin, TraceCollectionBase):
    __slots__ = (
        "variable_versions",
        "variable_traces",
        "break_collections",
        "continue_collections",
        "return_collections",
        "exception_collections",
        "outline_functions",
        "very_trusted_module_variables",
        "module_usage_attempts",
        "distribution_names",
    )

    def __init__(self, module, very_trusted_module_variables):
        assert module.isCompiledPythonModule(), module

        CollectionStartPointMixin.__init__(self)

        TraceCollectionBase.__init__(
            self, owner=module, name="module:" + module.getFullName(), parent=None
        )

        self.very_trusted_module_variables = very_trusted_module_variables

        # Attempts to use a module in this module.
        self.module_usage_attempts = OrderedSet()

        # Attempts to use a distribution in this module.
        self.distribution_names = OrderedDict()

    def getVeryTrustedModuleVariables(self):
        return self.very_trusted_module_variables

    def updateVeryTrustedModuleVariables(self, very_trusted_module_variables):
        result = self.very_trusted_module_variables != very_trusted_module_variables

        self.very_trusted_module_variables = very_trusted_module_variables

        return result

    def getModuleUsageAttempts(self):
        return self.module_usage_attempts

    def onModuleUsageAttempts(self, module_usage_attempts):
        self.module_usage_attempts.update(module_usage_attempts)

    def onModuleUsageAttempt(self, module_usage_attempt):
        self.module_usage_attempts.add(module_usage_attempt)

    def getUsedDistributions(self):
        return self.distribution_names

    def onDistributionUsed(self, distribution_name, node, success):
        inclusion_logger.info_to_file_only(
            "Cannot find distribution '%s' at '%s', expect potential run time problem, unless this is unused code."
            % (distribution_name, node.source_ref.getAsString())
        )

        self.distribution_names[distribution_name] = success


# TODO: This should not exist, but be part of decision at the time these are collected.
def areEmptyTraces(variable_traces):
    """Do these traces contain any writes or accesses."""
    # Many cases immediately return, that is how we do it here,
    # pylint: disable=too-many-branches,too-many-return-statements

    for variable_trace in variable_traces:
        if variable_trace.isAssignTrace():
            return False
        elif variable_trace.isInitTrace():
            return False
        elif variable_trace.isDeletedTrace():
            # A "del" statement can do this, and needs to prevent variable
            # from being removed.

            return False
        elif variable_trace.isUninitializedTrace():
            if variable_trace.getUsageCount():
                # Checking definite is enough, the merges, we shall see
                # them as well.
                return False
        elif variable_trace.isUnknownTrace():
            if variable_trace.getUsageCount():
                # Checking definite is enough, the merges, we shall see
                # them as well.
                return False
        elif variable_trace.isEscapeTrace():
            if variable_trace.getUsageCount():
                # Checking definite is enough, the merges, we shall see
                # them as well.
                return False
        elif variable_trace.isMergeTrace():
            if variable_trace.getUsageCount():
                # Checking definite is enough, the merges, we shall see
                # them as well.
                return False
        elif variable_trace.isLoopTrace():
            return False
        else:
            assert False, variable_trace

    return True


def areReadOnlyTraces(variable_traces):
    """Do these traces contain any writes."""

    # Many cases immediately return, that is how we do it here,
    for variable_trace in variable_traces:
        if variable_trace.isAssignTrace():
            return False
        elif variable_trace.isInitTrace():
            pass
        elif variable_trace.isDeletedTrace():
            # A "del" statement can do this, and needs to prevent variable
            # from being not released.

            return False
        elif variable_trace.isUninitializedTrace():
            pass
        elif variable_trace.isUnknownTrace():
            return False
        elif variable_trace.isEscapeTrace():
            pass
        elif variable_trace.isMergeTrace():
            pass
        elif variable_trace.isLoopTrace():
            pass
        else:
            assert False, variable_trace

    return True


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
