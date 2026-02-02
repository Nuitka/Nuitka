#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Trace collection (also often still referred to as constraint collection).

At the core of value propagation there is the collection of constraints that
allow to propagate knowledge forward or not.

This is about collecting these constraints and to manage them.
"""

import contextlib
from collections import defaultdict
from contextlib import contextmanager

from nuitka.__past__ import iterItems  # Python3 compatibility.
from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.ModuleRegistry import addUsedModule
from nuitka.nodes.NodeMakingHelpers import getComputationResult
from nuitka.nodes.shapes.StandardShapes import tshape_uninitialized
from nuitka.States import states
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
    ValueTraceLoopComplete,
    ValueTraceLoopIncomplete,
    ValueTraceMerge,
    ValueTraceStartInit,
    ValueTraceStartInitStarArgs,
    ValueTraceStartInitStarDict,
    ValueTraceStartUninitialized,
    ValueTraceStartUnknown,
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

    def getVariableTracesAll(self):
        return self.variable_traces

    def addVariableMergeMultipleTrace(self, variable, traces):
        trace_merge = ValueTraceMerge(traces)

        version = variable.allocateTargetNumber()

        self.variable_traces[variable][version] = trace_merge

        return version


class CollectionStartPointMixin(CollectionUpdateMixin):
    """Mixin to use in start points of collections.

    These are modules, functions, etc. typically entry points.
    """

    # Many things are traced, pylint: disable=too-many-instance-attributes

    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    def __init__(self):
        # Variable assignments performed in here, last issued number, only used
        # to determine the next number that should be used for a new assignment.
        self.variable_versions = {}

        # The full trace of a variable with a version for the function or module
        # this is.
        self.variable_traces = defaultdict(dict)

        self.break_collections = None
        self.continue_collections = None
        self.return_collections = None
        self.exception_collections = None

        self.outline_functions = None

        # What loop variables were there, them going away is something we want
        # to know.
        self.loop_variables = set()

        self.delayed_work = []

    def getLoopBreakCollections(self):
        return self.break_collections

    def onLoopBreak(self, collection):
        self.break_collections.append(
            TraceCollectionSnapshot(parent=collection, name="loop break")
        )

    def getLoopContinueCollections(self):
        return self.continue_collections

    def onLoopContinue(self, collection):
        self.continue_collections.append(
            TraceCollectionSnapshot(parent=collection, name="loop continue")
        )

    def onFunctionReturn(self, collection):
        if self.return_collections is not None:
            self.return_collections.append(
                TraceCollectionSnapshot(parent=collection, name="return")
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

            if not self.exception_collections or (
                self.exception_collections[-1].variable_actives
                is not collection.variable_actives
            ):
                self.exception_collections.append(
                    TraceCollectionSnapshot(parent=collection, name="exception")
                )

    def getFunctionReturnCollections(self):
        return self.return_collections

    def getExceptionRaiseCollections(self):
        return self.exception_collections

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

    def onDelayedWork(self, node, function, old_desc, describe_new_node):
        self.delayed_work.append((node, function, old_desc, describe_new_node))

    def performDelayedWork(self):
        for node, delayed_function, old_desc, describe_new_node in self.delayed_work:
            # We might point to a node that has been removed.
            if not node.isConnected():
                if states.is_debug:
                    # Might be normal though, but we will aim at avoiding the
                    # necessity of encountering this where possible.
                    assert False, "Node %s is not connected" % node
                continue

            new_node = delayed_function(node)
            if new_node is not node:
                node.getParent().replaceChild(node, new_node)

                tags, new_node_description = describe_new_node(new_node)
                self.signalChange(
                    tags=tags,
                    message="Replaced %s with %s." % (old_desc, new_node_description),
                    source_ref=node.getSourceReference(),
                )

        # Surely do this only once.
        del self.delayed_work

    def updateVeryTrustedModuleVariable(self, variable, old_node, new_node):
        """Update a very trusted module variable assignment if necessary."""
        if self.very_trusted_module_variables.get(variable, None) is old_node:
            self.very_trusted_module_variables[variable] = new_node


class TraceCollectionBase(object):
    """This contains for logic for maintaining active traces.

    They are kept for "variable" and versions.
    """

    __slots__ = (
        "owner",
        "parent",
        "name",
        "variable_actives",
        "variable_actives_needs_copy",
        "has_unescaped_variables",
        "variable_escapable",
    )

    if isCountingInstances():
        __del__ = counted_del()

    @counted_init
    def __init__(self, owner, name, parent):
        self.owner = owner
        self.parent = parent
        self.name = name

        # Currently active values in the tracing.
        self.variable_actives = {}
        self.variable_actives_needs_copy = True

        # Even though it's empty, we set it, because init of variables won't do it.
        self.has_unescaped_variables = True

        self.variable_escapable = set()

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

        return self.variable_traces[variable][self.variable_actives[variable]]

    def hasVariableCurrentTrace(self, variable):
        return variable in self.variable_actives

    def markCurrentVariableTrace(self, variable, version):
        if self.variable_actives_needs_copy:
            self.variable_actives = self.variable_actives.copy()
            self.variable_actives_needs_copy = False

        self.variable_actives[variable] = version
        self.has_unescaped_variables = True

    def removeCurrentVariableTrace(self, variable):
        if self.variable_actives_needs_copy:
            self.variable_actives = self.variable_actives.copy()
            self.variable_actives_needs_copy = False

        del self.variable_actives[variable]

    def initVariableLate(self, variable):
        if self.variable_actives_needs_copy:
            self.variable_actives = self.variable_actives.copy()
            self.variable_actives_needs_copy = False

        variable.initVariableLate(self)

    def markActiveVariableAsEscaped(self, variable):
        version = self.variable_actives[variable]
        variable_traces = self.variable_traces[variable]
        current = variable_traces[version]

        if current.isTraceThatNeedsEscape():
            # Escape traces are div 3 rem 1.
            version = version // 3 * 3 + 1

            if version not in variable_traces:
                variable_traces[version] = ValueTraceEscaped(self.owner, current)

            self.markCurrentVariableTrace(variable, version)

    def markClosureVariableAsUnknown(self, variable):
        version = self.variable_actives[variable]
        variable_traces = self.variable_traces[variable]
        current = variable_traces[version]

        if not current.isUnknownTrace():
            # Unknown traces are div 3 rem 2.
            version = version // 3 * 3 + 2

            if version not in variable_traces:
                variable_traces[version] = ValueTraceUnknown(self.owner, current)

            self.markCurrentVariableTrace(variable, version)

    def markActiveVariableAsUnknown(self, variable):
        version = self.variable_actives[variable]

        if version % 3 != 2:
            variable_traces = self.variable_traces[variable]
            current = variable_traces[version]

            if not current.isUnknownOrVeryTrustedTrace():
                # Unknown traces are div 3 rem 2.
                version = version // 3 * 3 + 2

                if version not in variable_traces:
                    variable_traces[version] = ValueTraceUnknown(self.owner, current)

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
        self.variable_traces[variable][version] = result

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

        if self.has_unescaped_variables:
            #            print("Control flow escape in", self.name, self.variable_escapable)
            for variable in self.variable_escapable:
                if variable in self.variable_actives:
                    variable.onControlFlowEscape(self)

            self.has_unescaped_variables = False

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
            self.owner,
            assign_node,
            self.getVariableCurrentTrace(variable),
        )

        self.variable_traces[variable][version] = variable_trace

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
            self.owner,
            assign_node,
            self.getVariableCurrentTrace(variable),
        )

        self.variable_traces[variable][version] = variable_trace

        # Make references point to it.
        self.markCurrentVariableTrace(variable, version)

        return variable_trace

    def onVariableSetToVeryTrustedValue(self, variable, version, assign_node):
        variable_trace = ValueTraceAssignVeryTrusted(
            self.owner,
            assign_node,
            self.getVariableCurrentTrace(variable),
        )

        self.variable_traces[variable][version] = variable_trace

        # Make references point to it.
        self.markCurrentVariableTrace(variable, version)

        return variable_trace

    def onVariableSetToUnescapablePropagatedValue(
        self, variable, version, assign_node, replacement
    ):
        variable_trace = ValueTraceAssignUnescapablePropagated(
            self.owner,
            assign_node,
            self.getVariableCurrentTrace(variable),
            replacement,
        )

        self.variable_traces[variable][version] = variable_trace

        # Make references point to it.
        self.markCurrentVariableTrace(variable, version)

        return variable_trace

    def onVariableDel(self, variable, version, del_node):
        # Add a new trace, allocating a new version for the variable, and
        # remember the delete of the current
        old_trace = self.getVariableCurrentTrace(variable)

        # TODO: Annotate value content as escaped.

        variable_trace = ValueTraceDeleted(
            self.owner,
            old_trace,
            del_node,
        )

        # Assign to not initialized again.
        self.variable_traces[variable][version] = variable_trace

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

                # Nothing to do here, self is unchanged.
                if collection1.variable_actives is collection2.variable_actives:
                    return
            else:
                # Refuse to do stupid work
                return
        elif collection_no is None:
            # Handle one branch case, we need to merge versions backwards as
            # they may make themselves obsolete.
            collection1 = self
            collection2 = collection_yes

            # Nothing to do here, self is unchanged.
            if collection1.variable_actives is collection2.variable_actives:
                return

        else:
            # Handle two branch case, they may or may not do the same things.
            collection1 = collection_yes
            collection2 = collection_no

            # Both branches being unchanged, means no merge is needed
            if collection1.variable_actives == collection2.variable_actives:
                self.replaceBranch(collection1)

                return

        _merge_counts[2] += 1

        if states.is_debug:
            # They must have the same content only or else some bug occurred.
            if len(collection1.variable_actives) != len(collection2.variable_actives):
                for variable, version in iterItems(collection1.variable_actives):
                    if variable not in collection2.variable_actives:
                        print("Only in collection1", variable, version)

                for variable, version in iterItems(collection2.variable_actives):
                    if variable not in collection1.variable_actives:
                        print("Only in collection2", variable, version)

                assert False

        has_unescaped_variables = (
            collection1.has_unescaped_variables or collection2.has_unescaped_variables
        )
        new_actives = {}
        for variable, version in iterItems(collection1.variable_actives):
            other_version = collection2.variable_actives[variable]

            if version != other_version:
                variable_traces = self.variable_traces[variable]

                trace1 = variable_traces[version]
                trace2 = variable_traces[other_version]

                if version % 3 == 1 and trace1.previous is trace2:
                    pass
                elif other_version % 3 == 1 and trace2.previous is trace1:
                    version = other_version
                else:
                    version = self.addVariableMergeMultipleTrace(
                        variable,
                        (
                            trace1,
                            trace2,
                        ),
                    )

                    has_unescaped_variables = True

            new_actives[variable] = version

        self.variable_actives = new_actives
        self.variable_actives_needs_copy = False

        # TODO: This could be avoided, if we detect no actual changes being present, but it might
        # be more costly.
        self.has_unescaped_variables = has_unescaped_variables

    def mergeMultipleBranches(self, collections):
        # Optimize for length 1, which is trivial merge and needs not a
        # lot of work, and length 2 has dedicated code as it's so frequent.

        # collection_levels = set()
        # new_collections = []

        # for collection in collections:
        #     if collection.variable_actives_level not in collection_levels:
        #         collection_levels.add(collection.variable_actives_level)
        #         new_collections.append(collection)

        # collections = new_collections

        # if len(collections) != len(new_collections):
        #     print("Reduced multi %d to %d for %s" % (len(collections), len(new_collections), self))
        #     assert False

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
            include_sleep_time=False,
            use_perf_counters=False,
        ):
            new_actives = {}

            has_unescaped_variables = any(
                collection.has_unescaped_variables for collection in collections
            )

            for variable in collections[0].variable_actives:
                versions = set(
                    collection.variable_actives[variable] for collection in collections
                )

                if len(versions) == 1:
                    (version,) = versions
                else:
                    traces = []
                    escaped = []
                    winner_version = None

                    variable_traces = self.variable_traces[variable]

                    for version in sorted(versions):
                        trace = variable_traces[version]

                        if version % 3 == 1:
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
                            variable,
                            traces,
                        )

                        has_unescaped_variables = True

                new_actives[variable] = version

            self.variable_actives = new_actives
            self.variable_actives_needs_copy = False

            # TODO: This could be avoided, if we detect no actual changes being present, but it might
            # be more costly.
            self.has_unescaped_variables = has_unescaped_variables

    def replaceBranch(self, collection_replace):
        self.variable_actives = collection_replace.variable_actives
        self.has_unescaped_variables = collection_replace.has_unescaped_variables

        # Make the old one unusable.
        collection_replace.variable_actives = None

        _merge_counts[1] += 1

    def onLoopBreak(self, collection):
        return self.parent.onLoopBreak(collection)

    def onLoopContinue(self, collection):
        return self.parent.onLoopContinue(collection)

    def onFunctionReturn(self, collection):
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

    def updateVeryTrustedModuleVariable(self, variable, old_node, new_node):
        return self.parent.updateVeryTrustedModuleVariable(variable, old_node, new_node)

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

    def initVariableUnknown(self, variable, old_collection):
        # TODO: Making these really reusable by removing their state for each of
        # these cases. pylint: disable=unused-argument
        # if old_collection is not None:
        #     trace = old_collection.variable_traces[variable][-1]
        # else:
        trace = ValueTraceStartUnknown(self.owner)

        # Unknown traces are div 3 rem 2.
        self.variable_traces[variable][-1] = trace
        self.variable_actives[variable] = -1

        return trace

    def initVariableModule(self, variable, old_collection):
        # TODO: Making these really reusable by removing their state for each of
        # these cases. pylint: disable=unused-argument
        # if old_collection is not None:
        #     trace = old_collection.variable_traces[variable][-1]
        # else:
        trace = ValueTraceStartUnknown(self.owner)

        # Unknown traces are div 3 rem 2.
        self.variable_traces[variable][-1] = trace
        self.variable_actives[variable] = -1

        return trace

    def initVariableInit(self, variable, old_collection):
        # TODO: Making these really reusable by removing their state for each of
        # these cases. pylint: disable=unused-argument
        # if old_collection is not None:
        #     trace = old_collection.variable_traces[variable][0]
        # else:
        trace = ValueTraceStartInit(self.owner)

        self.variable_traces[variable][0] = trace
        self.variable_actives[variable] = 0

        return trace

    def initVariableInitStarArgs(self, variable, old_collection):
        # TODO: Making these really reusable by removing their state for each of
        # these cases. pylint: disable=unused-argument
        # if old_collection is not None:
        #     trace = old_collection.variable_traces[variable][0]
        # else:
        trace = ValueTraceStartInitStarArgs(self.owner)

        self.variable_traces[variable][0] = trace
        self.variable_actives[variable] = 0

        return trace

    def initVariableInitStarDict(self, variable, old_collection):
        # TODO: Making these really reusable by removing their state for each of
        # these cases. pylint: disable=unused-argument
        # if old_collection is not None:
        #     trace = old_collection.variable_traces[variable][0]
        # else:
        trace = ValueTraceStartInitStarDict(self.owner)

        self.variable_traces[variable][0] = trace
        self.variable_actives[variable] = 0

        return trace

    def initVariableUninitialized(self, variable, old_collection):
        # TODO: Making these really reusable by removing their state for each of
        # these cases. pylint: disable=unused-argument
        # if old_collection is not None:
        #     trace = old_collection.variable_traces[variable][0]
        # else:
        trace = ValueTraceStartUninitialized(self.owner)

        self.variable_traces[variable][0] = trace
        self.variable_actives[variable] = 0

        return trace

    def initVariableUninitializedLate(self, variable):
        trace = ValueTraceStartUninitialized(self.owner)

        self.variable_traces[variable][0] = trace
        variable.setTracesForUserFirst(self.owner, self.variable_traces[variable])

        return trace

    def onDelayedWork(self, node, function, old_desc, describe_new_node):
        self.parent.onDelayedWork(node, function, old_desc, describe_new_node)


class TraceCollectionBranch(CollectionUpdateMixin, TraceCollectionBase):
    __slots__ = (
        "variable_traces",
        "loop_variables",
    )

    def __init__(self, name, parent):
        TraceCollectionBase.__init__(
            self,
            owner=parent.owner,
            name=name,
            parent=parent,
        )

        # If it gets modified, it will copy the snapshot state for us, so this
        # stays in tact.
        self.variable_actives = parent.variable_actives
        parent.variable_actives_needs_copy = True

        self.variable_escapable = parent.variable_escapable
        self.has_unescaped_variables = parent.has_unescaped_variables

        # For quick access without going to parent.
        self.variable_traces = parent.variable_traces
        self.loop_variables = parent.loop_variables

    def computeBranch(self, branch):
        result = branch.computeStatementsSequence(self)

        if result is not branch:
            branch.parent.replaceChild(branch, result)

        return result


class TraceCollectionSnapshot(CollectionUpdateMixin, TraceCollectionBase):
    __slots__ = (
        "variable_traces",
        "loop_variables",
    )

    def __init__(self, name, parent):
        TraceCollectionBase.__init__(
            self,
            owner=parent.owner,
            name=name,
            parent=parent,
        )

        # If it gets modified, it will copy the snapshot state for us, so this
        # stays in tact.
        self.variable_actives = parent.variable_actives
        parent.variable_actives_needs_copy = True

        self.variable_escapable = parent.variable_escapable
        self.has_unescaped_variables = parent.has_unescaped_variables

        # For quick access without going to parent.
        self.variable_traces = parent.variable_traces
        self.loop_variables = parent.loop_variables


class TraceCollectionFunction(CollectionStartPointMixin, TraceCollectionBase):
    __slots__ = (
        "variable_versions",
        "variable_traces",
        "loop_variables",
        "break_collections",
        "continue_collections",
        "return_collections",
        "exception_collections",
        "outline_functions",
        "very_trusted_module_variables",
        "delayed_work",
    )

    def __init__(self, parent, old_collection, function_body):
        # Many kinds of variables to setup, pylint: disable=too-many-branches

        # assert (
        #     function_body.isExpressionFunctionBody()
        #     or function_body.isExpressionGeneratorObjectBody()
        #     or function_body.isExpressionCoroutineObjectBody()
        #     or function_body.isExpressionAsyncgenObjectBody()
        # ), function_body

        CollectionStartPointMixin.__init__(self)

        TraceCollectionBase.__init__(
            self,
            owner=function_body,
            name=function_body.getCodeName(),
            parent=parent,
        )

        if parent is not None:
            self.very_trusted_module_variables = parent.getVeryTrustedModuleVariables()
        else:
            self.very_trusted_module_variables = ()

        if function_body.isExpressionFunctionBody():
            parameters = function_body.getParameters()

            for parameter_variable in parameters.getTopLevelVariables():
                self.initVariableInit(parameter_variable, old_collection)
                self.variable_escapable.add(parameter_variable)

            list_star_variable = parameters.getListStarArgVariable()
            if list_star_variable is not None:
                self.initVariableInitStarArgs(list_star_variable, old_collection)
                self.variable_escapable.add(list_star_variable)

            dict_star_variable = parameters.getDictStarArgVariable()
            if dict_star_variable is not None:
                self.initVariableInitStarDict(dict_star_variable, old_collection)
                self.variable_escapable.add(dict_star_variable)

        for closure_variable in function_body.getClosureVariables():
            if closure_variable not in self.variable_actives:
                self.initVariableUnknown(closure_variable, old_collection)

                if closure_variable.isLocalVariable():
                    self.variable_escapable.add(closure_variable)

        for local_variable in function_body.getLocalVariables():
            if local_variable not in self.variable_actives:
                self.initVariableUninitialized(local_variable, old_collection)
                self.variable_escapable.add(local_variable)

        for module_variable in function_body.getModuleVariables():
            self.initVariableModule(module_variable, old_collection)
            self.variable_escapable.add(module_variable)

        for temp_variable in function_body.getTempVariables(outline=None):
            self.initVariableUninitialized(temp_variable, old_collection)

        # TODO: Have special function type for exec functions stuff.
        locals_scope = function_body.getLocalsScope()

        if locals_scope is not None:
            if not locals_scope.isMarkedForPropagation():
                for locals_dict_variable in locals_scope.variables.values():
                    self.initVariableUninitialized(locals_dict_variable, old_collection)
            else:
                function_body.locals_scope = None

        self.has_unescaped_variables = True

    def initVariableModule(self, variable, old_collection):
        # print("initVariableModule", variable, self)
        trusted_node = self.very_trusted_module_variables.get(variable)

        if trusted_node is None:
            return TraceCollectionBase.initVariableModule(
                self, variable, old_collection
            )

        assign_trace = ValueTraceAssignVeryTrusted(
            self.owner,
            trusted_node.getParent(),
            None,
        )

        # TODO: Make very trusted assign traces also div recognized by expanding
        # to div 4.
        self.variable_traces[variable][0] = assign_trace
        self.variable_actives[variable] = 0

        return assign_trace


class TraceCollectionPureFunction(TraceCollectionFunction):
    """Pure functions don't feed their parent."""

    __slots__ = ("used_functions",)

    def __init__(self, old_collection, function_body):
        TraceCollectionFunction.__init__(
            self,
            parent=None,
            old_collection=old_collection,
            function_body=function_body,
        )

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
        "loop_variables",
        "break_collections",
        "continue_collections",
        "return_collections",
        "exception_collections",
        "outline_functions",
        "very_trusted_module_variables",
        "module_usage_attempts",
        "distribution_names",
        "delayed_work",
    )

    def __init__(self, module, very_trusted_module_variables, old_collection):
        assert module.isCompiledPythonModule(), module

        CollectionStartPointMixin.__init__(self)

        TraceCollectionBase.__init__(
            self,
            owner=module,
            name=module.getFullName(),
            parent=None,
        )

        self.very_trusted_module_variables = very_trusted_module_variables

        # Attempts to use a module in this module.
        self.module_usage_attempts = OrderedSet()

        # Attempts to use a distribution in this module.
        self.distribution_names = OrderedDict()

        for module_variable in module.locals_scope.getLocalsRelevantVariables():
            self.initVariableModule(module_variable, old_collection)
            self.variable_escapable.add(module_variable)

        for temp_variable in module.getTempVariables(outline=None):
            self.initVariableUninitialized(temp_variable, old_collection)

        self.has_unescaped_variables = True

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


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
