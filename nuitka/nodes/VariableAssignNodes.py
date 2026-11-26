#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Assignment related nodes.

The most simple assignment statement 'a = b' is what we have here. All others
are either re-formulated using temporary variables, e.g. 'a, b = c' or are
attribute, slice, subscript assignments.

The deletion is a separate node unlike in CPython where assigning to 'NULL' is
internally what deletion is. But deleting is something entirely different to us
during code generation, which is why we keep them separate.

Tracing assignments in SSA form is the core of optimization for which we use
the traces.
"""

from abc import abstractmethod

from nuitka.__past__ import iterItems
from nuitka.ModuleRegistry import getOwnerFromCodeName
from nuitka.States import states

from .BuiltinIteratorNodes import makeStatementSpecialUnpackCheckFromIterated
from .ConstantRefNodes import makeConstantRefNode
from .NodeMakingHelpers import (
    makeStatementExpressionOnlyReplacementNode,
    makeStatementsSequenceReplacementNode,
)
from .shapes.ControlFlowDescriptions import (
    ControlFlowDescriptionElementBasedEscape,
    ControlFlowDescriptionFullEscape,
    ControlFlowDescriptionNoEscape,
)
from .shapes.IteratorShapes import tshape_iterator
from .shapes.StandardShapes import tshape_unknown
from .StatementBasesGenerated import (
    StatementAssignmentVariableConstantImmutableBase,
    StatementAssignmentVariableConstantMutableBase,
    StatementAssignmentVariableFromTempVariableBase,
    StatementAssignmentVariableFromVariableBase,
    StatementAssignmentVariableGenericBase,
    StatementAssignmentVariableHardValueBase,
    StatementAssignmentVariableIteratorBase,
)
from .SubscriptNodes import ExpressionSubscriptLookupForUnpack
from .VariableDelNodes import makeStatementDelVariable
from .VariableRefNodes import ExpressionTempVariableRef
from .VariableReleaseNodes import makeStatementReleaseVariable


class StatementAssignmentVariableMixin(object):
    """Assignment to a variable from an expression.

    All assignment forms that are not to attributes, slices, subscripts
    use this.

    The source might be a complex expression. The target can be any kind
    of variable, temporary, local, global, etc.

    Assigning a variable is something we trace in a new version, this is
    hidden behind target variable reference, which has this version once
    it can be determined.
    """

    # pylint: disable=assigning-non-slot
    __slots__ = ()

    @staticmethod
    def isStatementAssignmentVariable():
        return True

    def finalize(self):
        del self.parent
        del self.variable
        del self.variable_trace
        self.subnode_source.finalize()
        del self.subnode_source

    def getDetailsForDisplay(self):
        return {
            "variable_name": self.getVariableName(),
            "is_temp": self.variable.isTempVariable(),
            "var_type": self.variable.getVariableType(),
            "owner": self.variable.getOwner().getCodeName(),
        }

    @classmethod
    def fromXML(cls, provider, source_ref, **args):
        # pylint: disable=unused-argument
        owner = getOwnerFromCodeName(args["owner"])

        # TODO: Need to also provide "outline" for best effect
        if args["is_temp"] == "True":
            variable = owner.createTempVariable(
                args["variable_name"], temp_type=args["var_type"], outline=None
            )
        else:
            variable = owner.getProvidedVariable(args["variable_name"])

        del args["variable_name"]
        del args["is_temp"]
        del args["var_type"]
        del args["owner"]

        version = variable.allocateTargetNumber()

        return cls(
            variable=variable, variable_version=version, source_ref=source_ref, **args
        )

    def makeClone(self):
        version = self.variable.allocateTargetNumber()

        return self.__class__(
            source=self.subnode_source.makeClone(),
            variable=self.variable,
            variable_version=version,
            source_ref=self.source_ref,
        )

    def getVariableName(self):
        return self.variable.getName()

    def getVariable(self):
        return self.variable

    def setVariable(self, variable):
        self.variable = variable
        self.variable_version = variable.allocateTargetNumber()

    def getVariableTrace(self):
        return self.variable_trace

    def markAsInplaceSuspect(self):
        self.inplace_suspect = True

    def isInplaceSuspect(self):
        return self.inplace_suspect

    def removeMarkAsInplaceSuspect(self):
        self.inplace_suspect = False

    def mayRaiseException(self, exception_type):
        return self.subnode_source.mayRaiseException(exception_type)

    def needsReleasePreviousValue(self):
        previous = self.variable_trace.previous

        if previous.mustNotHaveValue():
            # Loop re-entry can give this assignment a previous value even if the
            # last trace collection run fell back to the uninitialized start trace.
            if self.getContainingLoopNode() is not None:
                return None

            return False
        elif previous.mustHaveValue():
            return True
        else:
            return None

    @staticmethod
    def getStatementNiceName():
        return "variable assignment statement"

    def getTypeShape(self):
        # Might be finalized, e.g. due to being dead code.
        try:
            source = self.subnode_source
        except AttributeError:
            return tshape_unknown

        return source.getTypeShape()

    @staticmethod
    def mayHaveSideEffects():
        # TODO: May execute "__del__" code, it would be sweet to be able to predict
        # if another reference will still be active for a value though, or if there
        # is such a code for the type shape.
        return True

    def _considerSpecialization(self, old_source, source):
        if source.isCompileTimeConstant():
            result = makeStatementAssignmentVariableConstant(
                source=source,
                variable=self.variable,
                variable_version=self.variable_version,
                very_trusted=old_source.isExpressionImportName(),
                source_ref=self.source_ref,
            )

            return (
                result,
                "new_statements",
                "Assignment source of '%s' is now compile time constant."
                % self.getVariableName(),
            )

        if source.isExpressionVariableRef():
            result = StatementAssignmentVariableFromVariable(
                source=source,
                variable=self.variable,
                variable_version=self.variable_version,
                source_ref=self.source_ref,
            )

            return (
                result,
                "new_statements",
                "Assignment source is now variable reference.",
            )

        if source.isExpressionTempVariableRef():
            result = StatementAssignmentVariableFromTempVariable(
                source=source,
                variable=self.variable,
                variable_version=self.variable_version,
                source_ref=self.source_ref,
            )

            return (
                result,
                "new_statements",
                "Assignment source is now temp variable reference.",
            )

        if source.getTypeShape().isShapeIterator():
            result = StatementAssignmentVariableIterator(
                source=source,
                variable=self.variable,
                variable_version=self.variable_version,
                source_ref=self.source_ref,
            )

            return (
                result,
                "new_statements",
                "Assignment source is now known to be iterator.",
            )

        if source.hasVeryTrustedValue():
            result = StatementAssignmentVariableHardValue(
                source=source,
                variable=self.variable,
                variable_version=self.variable_version,
                source_ref=self.source_ref,
            )

            return (
                result,
                "new_statements",
                "Assignment source is now known to be hard value.",
            )

        return self, None, None

    def collectVariableAccesses(self, emit_variable):
        emit_variable(self.variable)
        self.subnode_source.collectVariableAccesses(emit_variable)

    @abstractmethod
    def hasVeryTrustedValue(self):
        """Does this assignment node have a very trusted value."""

    @abstractmethod
    def computeStatementAssignmentTraceUpdate(self, trace_collection, source):
        """Set the value trace for the assignment form."""


class StatementAssignmentVariableGeneric(
    StatementAssignmentVariableMixin, StatementAssignmentVariableGenericBase
):
    kind = "STATEMENT_ASSIGNMENT_VARIABLE_GENERIC"

    named_children = ("source|setter",)
    nice_children = ("assignment source",)
    node_attributes = ("variable", "variable_version")
    auto_compute_handling = "post_init"

    __slots__ = (
        "variable_trace",
        # TODO: Does every variant have to care here
        "inplace_suspect",
    )

    # TODO: Add parsing of node_attributes for init values, so we can avoid these too
    def postInitNode(self):
        self.variable_trace = None
        self.inplace_suspect = None

    @staticmethod
    def getReleaseEscape():
        return ControlFlowDescriptionFullEscape

    def computeStatement(self, trace_collection):
        old_source = self.subnode_source
        variable = self.variable

        if old_source.isExpressionSideEffects():
            statements = [
                makeStatementExpressionOnlyReplacementNode(side_effect, self)
                for side_effect in old_source.subnode_side_effects
            ]

            statements.append(self)

            parent = self.parent

            self.setChildSource(old_source.subnode_expression)

            result = makeStatementsSequenceReplacementNode(
                statements=statements, node=self
            )
            result.parent = parent

            return (
                result.computeStatementsSequence(trace_collection),
                "new_statements",
                """\
Side effects of assignments promoted to statements.""",
            )

        source = trace_collection.onExpression(self.subnode_source)

        if source.willRaiseAnyException():
            result = makeStatementExpressionOnlyReplacementNode(
                expression=source, node=self
            )

            del self.parent

            return (
                result,
                "new_raise",
                """\
Assignment raises exception in assigned value, removed assignment.""",
            )

        # Module variables may shadow built-in names, so 'x = x' is not a no-op for them.
        # TODO: The variable type checks ought to become unnecessary, as they
        # are to be a feature of the trace. Assigning from known assigned is
        # supposed to be possible to eliminate.
        if (
            not variable.isModuleVariable()
            and source.isExpressionVariableRef()
            and source.getVariable() is variable
        ):
            if source.mayHaveSideEffects():
                result = makeStatementExpressionOnlyReplacementNode(
                    expression=source, node=self
                )

                return (
                    result,
                    "new_statements",
                    """\
Lowered assignment of %s from itself to mere access of it."""
                    % variable.getDescription(),
                )
            else:
                return (
                    None,
                    "new_statements",
                    """\
Removed assignment of %s from itself which is known to be defined."""
                    % variable.getDescription(),
                )

        if source is old_source:
            result = self, None, None
        else:
            result = self._considerSpecialization(old_source, source)
            result[0].parent = self.parent

        result[0].computeStatementAssignmentTraceUpdate(trace_collection, source)

        return result

    def computeStatementAssignmentTraceUpdate(self, trace_collection, source):
        self.variable_trace = trace_collection.onVariableSet(
            variable=self.variable, version=self.variable_version, assign_node=self
        )

        # TODO: Determine from future use of assigned variable, if this is needed at all.
        trace_collection.removeKnowledge(source)

    def undoVariableTracing(self, trace_collection):
        # The value trace replacement is undone by restoring the previous
        # active version of the variable, but only if the variable is still
        # active, which is not the case for variables local to a removed
        # outline.
        if self.variable_trace is not None:
            variable = self.variable

            if variable in trace_collection.variable_actives:
                previous = self.variable_trace.previous

                for version, trace in iterItems(
                    trace_collection.variable_traces[variable]
                ):
                    if trace is previous:
                        trace_collection.markCurrentVariableTrace(variable, version)
                        break

    def hasVeryTrustedValue(self):
        return self.subnode_source.hasVeryTrustedValue()


class StatementAssignmentVariableIterator(
    StatementAssignmentVariableMixin, StatementAssignmentVariableIteratorBase
):
    kind = "STATEMENT_ASSIGNMENT_VARIABLE_ITERATOR"

    named_children = ("source",)
    nice_children = ("assignment source",)
    node_attributes = ("variable", "variable_version")
    auto_compute_handling = "post_init"

    __slots__ = (
        "variable_trace",
        # TODO: Does every variant have to care here
        "inplace_suspect",
        "type_shape",
    )

    # TODO: Add parsing of node_attributes for init values, so we can avoid these too
    def postInitNode(self):
        self.variable_trace = None
        self.inplace_suspect = None
        self.type_shape = tshape_iterator

    def getTypeShape(self):
        return self.type_shape

    @staticmethod
    def getReleaseEscape():
        # TODO: For iteration over constants that wouldn't be necessary,
        # but if we know the iteration well enough, it's supposed to be
        # converted to something else anyway.
        return ControlFlowDescriptionElementBasedEscape

    @staticmethod
    def _collectConnectedNodes(nodes, description):
        result = []

        for node in nodes:
            if not node.isConnected():
                if states.is_debug:
                    assert False, "Iterator %s %s is not connected" % (
                        description,
                        node,
                    )
                continue

            result.append(node)

        return result

    def _collectDirectAccessTargets(self, assign_trace, usages, releases, dels):
        unpack_nodes = []
        unpack_check_nodes = []

        for usage in self._collectConnectedNodes(usages, "usage"):
            usage_parent = usage.getParent()

            if (
                usage_parent.isExpressionSpecialUnpack()
                and usage_parent.subnode_value is usage
            ):
                unpack_nodes.append((usage_parent, usage))
            elif (
                usage_parent.isStatementSpecialUnpackCheck()
                and usage_parent.subnode_iterator is usage
            ):
                unpack_check_nodes.append(usage_parent)
            else:
                return None

        if len(unpack_nodes) + len(unpack_check_nodes) != assign_trace.getUsageCount():
            if states.is_debug:
                assert False, (
                    self,
                    len(unpack_nodes) + len(unpack_check_nodes),
                    assign_trace.getUsageCount(),
                )
            return None

        release_nodes = self._collectConnectedNodes(releases, "release")
        del_nodes = self._collectConnectedNodes(dels, "del")

        return unpack_nodes, unpack_check_nodes, release_nodes, del_nodes

    @staticmethod
    def _applyDirectAccessReplacements(
        tmp_iterated_variable,
        unpack_nodes,
        unpack_check_nodes,
        release_nodes,
        del_nodes,
    ):
        for unpack_node, usage in unpack_nodes:
            replacement = ExpressionSubscriptLookupForUnpack(
                expression=ExpressionTempVariableRef(
                    variable=tmp_iterated_variable,
                    source_ref=usage.source_ref,
                ),
                subscript=makeConstantRefNode(
                    constant=unpack_node.getCount() - 1,
                    source_ref=usage.source_ref,
                ),
                expected=unpack_node.getExpected(),
                source_ref=usage.source_ref,
            )
            unpack_node.getParent().replaceChild(unpack_node, replacement)

        for check_node in unpack_check_nodes:
            replacement = makeStatementSpecialUnpackCheckFromIterated(
                tmp_iterated_variable=tmp_iterated_variable,
                count=check_node.getCount(),
                source_ref=check_node.source_ref,
            )
            check_node.getParent().replaceChild(check_node, replacement)

        for release_node in release_nodes:
            replacement = makeStatementReleaseVariable(
                variable=tmp_iterated_variable,
                source_ref=release_node.source_ref,
            )
            release_node.getParent().replaceChild(release_node, replacement)

        for del_node in del_nodes:
            replacement = makeStatementDelVariable(
                variable=tmp_iterated_variable,
                tolerant=del_node.is_tolerant,
                source_ref=del_node.source_ref,
            )
            del_node.getParent().replaceChild(del_node, replacement)

    def _replaceWithDirectAccess(self, node):
        """Replace iterator assignment and recorded accesses with direct access.

        Executed as delayed work at the end of a trace collection pass, when no
        trace collection walk is active. All accesses recorded on the tracked
        trace during the pass are rewritten to target the newly allocated temp
        variable, and the iterated value is reparented directly without cloning.
        """
        assert node is self

        assign_trace = self.variable_trace

        if assign_trace is None:
            return self

        usages = assign_trace.usages
        releases = assign_trace.releases
        dels = assign_trace.dels
        assign_trace.clearTrackedNodes()

        if (
            usages is None
            or not assign_trace.hasNoMergeOrNameUsage()
            or not self.subnode_source.isExpressionBuiltinIterForUnpack()
        ):
            return self

        iterated_value = self.subnode_source.subnode_value
        provider = self.getParentVariableProvider()
        entry_point = provider.getEntryPoint()

        # Escape traces are at version + 1 (div 3 rem 1); do not replace if
        # this assignment was escaped during the finishing pass.
        if (
            not iterated_value.isKnownToBeIndexable()
            or self.variable_version + 1
            in entry_point.trace_collection.variable_traces[self.variable]
        ):
            return self

        targets = self._collectDirectAccessTargets(assign_trace, usages, releases, dels)

        if targets is None:
            return self

        temp_scope = provider.allocateTempScope("unpack")
        tmp_iterated_variable = provider.allocateTempVariable(
            temp_scope=temp_scope,
            name="iterated_value",
            temp_type="object",
            late=True,
        )

        self._applyDirectAccessReplacements(tmp_iterated_variable, *targets)

        return makeStatementAssignmentVariable(
            source=iterated_value,
            variable=tmp_iterated_variable,
            source_ref=iterated_value.source_ref,
        )

    def computeStatement(self, trace_collection):
        variable = self.variable
        provider = trace_collection.getOwner()

        source = trace_collection.onExpression(self.subnode_source)

        if source.willRaiseAnyException():
            result = makeStatementExpressionOnlyReplacementNode(
                expression=source, node=self
            )

            del self.parent

            return (
                result,
                "new_raise",
                """\
Assignment raises exception in assigned value, removed assignment.""",
            )

        needs_delayed_direct_access = False

        if (
            self.variable_trace is not None
            and source.isExpressionBuiltinIterForUnpack()
            and source.subnode_value.isKnownToBeIndexable()
            and variable.hasAccessesOutsideOf(provider) is False
        ):
            # TODO: Ought to become able to check if the self.variable_trace
            # is escaped by annotating that upwards, so a search is not
            # needed at all.
            last_trace = variable.getMatchingUnescapedAssignTrace(self)

            if last_trace is not None:
                needs_delayed_direct_access = True

                trace_collection.onDelayedWork(
                    node=self,
                    function=self._replaceWithDirectAccess,
                    old_desc="assignment to '%s' from iter()" % variable.getName(),
                    describe_new_node=lambda new_node: (
                        "new_statements",
                        "direct access assignment to '%s'" % new_node.getVariableName(),
                    ),
                )

        self.type_shape = source.getTypeShape()

        if needs_delayed_direct_access:
            self.variable_trace = trace_collection.onVariableSetTracked(
                variable=variable, version=self.variable_version, assign_node=self
            )
        else:
            self.variable_trace = trace_collection.onVariableSet(
                variable=variable, version=self.variable_version, assign_node=self
            )

        return self, None, None

    def computeStatementAssignmentTraceUpdate(self, trace_collection, source):
        self.variable_trace = trace_collection.onVariableSet(
            variable=self.variable, version=self.variable_version, assign_node=self
        )

    @staticmethod
    def hasVeryTrustedValue():
        return False


class StatementAssignmentVariableConstantMutable(
    StatementAssignmentVariableMixin, StatementAssignmentVariableConstantMutableBase
):
    kind = "STATEMENT_ASSIGNMENT_VARIABLE_CONSTANT_MUTABLE"

    named_children = ("source",)
    nice_children = ("assignment source",)
    node_attributes = ("variable", "variable_version")
    auto_compute_handling = "post_init"

    __slots__ = (
        "variable_trace",
        # TODO: Does every variant have to care here
        "inplace_suspect",
    )

    # TODO: Add parsing of node_attributes for init values, so we can avoid these too
    def postInitNode(self):
        self.variable_trace = None
        self.inplace_suspect = None

    @staticmethod
    def mayRaiseException(exception_type):
        return False

    @staticmethod
    def getReleaseEscape():
        return ControlFlowDescriptionNoEscape

    def computeStatement(self, trace_collection):
        variable = self.variable
        last_trace = self.variable_trace

        provider = trace_collection.getOwner()

        if (
            last_trace is not None
            and last_trace.hasNoMergeOrNameUsage()
            and variable.hasAccessesOutsideOf(provider) is False
        ):
            if (
                variable.isModuleVariable()
                or variable.owner.locals_scope.isUnoptimizedFunctionScope()
                or trace_collection.needsFrameLocalsProxy()
            ):
                # TODO: We do not trust these yet a lot, but more might be
                pass
            else:
                if not last_trace.getUsageCount():
                    if last_trace.previous.isUnassignedTrace():
                        return (
                            None,
                            "new_statements",
                            "Dropped dead assignment statement to '%s'."
                            % (self.getVariableName()),
                        )
                    else:
                        return trace_collection.computedStatementResult(
                            statement=makeStatementDelVariable(
                                variable=self.variable,
                                version=self.variable_version,
                                tolerant=True,
                                source_ref=self.source_ref,
                            ),
                            change_tags="new_statements",
                            change_desc="Lowered dead assignment statement to '%s' to previous value 'del'."
                            % self.getVariableName(),
                        )

        # Can safely forward propagate only non-mutable constants.
        self.variable_trace = trace_collection.onVariableSet(
            variable=variable, version=self.variable_version, assign_node=self
        )

        return self, None, None

    def computeStatementAssignmentTraceUpdate(self, trace_collection, source):
        self.variable_trace = trace_collection.onVariableSet(
            variable=self.variable, version=self.variable_version, assign_node=self
        )

    @staticmethod
    def hasVeryTrustedValue():
        return False


class StatementAssignmentVariableConstantImmutable(
    StatementAssignmentVariableMixin, StatementAssignmentVariableConstantImmutableBase
):
    kind = "STATEMENT_ASSIGNMENT_VARIABLE_CONSTANT_IMMUTABLE"

    named_children = ("source",)
    nice_children = ("assignment source",)
    node_attributes = ("variable", "variable_version")
    auto_compute_handling = "post_init"

    __slots__ = (
        "variable_trace",
        # TODO: Does every variant have to care here
        "inplace_suspect",
    )

    # TODO: Add parsing of node_attributes for init values, so we can avoid these too
    def postInitNode(self):
        self.variable_trace = None
        self.inplace_suspect = None

    @staticmethod
    def mayRaiseException(exception_type):
        return False

    @staticmethod
    def getReleaseEscape():
        return ControlFlowDescriptionNoEscape

    def computeStatement(self, trace_collection):
        variable = self.variable
        last_trace = self.variable_trace

        provider = trace_collection.getOwner()

        if (
            last_trace is not None
            and last_trace.hasNoMergeOrNameUsage()
            and variable.hasAccessesOutsideOf(provider) is False
        ):
            if (
                variable.isModuleVariable()
                or variable.owner.locals_scope.isUnoptimizedFunctionScope()
                or trace_collection.needsFrameLocalsProxy()
            ):
                # TODO: We do not trust these yet a lot, but more might be
                pass
            else:
                if not last_trace.getUsageCount():
                    if last_trace.previous.isUnassignedTrace():
                        return (
                            None,
                            "new_statements",
                            "Dropped dead assignment statement to '%s'."
                            % (self.getVariableName()),
                        )
                    else:
                        return trace_collection.computedStatementResult(
                            statement=makeStatementDelVariable(
                                variable=self.variable,
                                version=self.variable_version,
                                tolerant=True,
                                source_ref=self.source_ref,
                            ),
                            change_tags="new_statements",
                            change_desc="Lowered dead assignment statement to '%s' to previous value 'del'."
                            % self.getVariableName(),
                        )

                # TODO: Maybe this can be used for keeping the replacement node as well.
                self.variable_trace = trace_collection.onVariableSetToUnescapablePropagatedValue(
                    variable=variable,
                    version=self.variable_version,
                    assign_node=self,
                    replacement=lambda _replaced_node: self.subnode_source.makeClone(),
                )

                if last_trace.previous.isUnassignedTrace():
                    result = None
                else:
                    result = makeStatementDelVariable(
                        variable=self.variable,
                        version=self.variable_version,
                        tolerant=True,
                        source_ref=self.source_ref,
                    )

                return (
                    result,
                    "new_statements",
                    "Dropped propagated assignment statement to '%s'."
                    % self.getVariableName(),
                )

        self.variable_trace = trace_collection.onVariableSetToUnescapableValue(
            variable=variable, version=self.variable_version, assign_node=self
        )

        return self, None, None

    def computeStatementAssignmentTraceUpdate(self, trace_collection, source):
        self.variable_trace = trace_collection.onVariableSetToUnescapableValue(
            variable=self.variable, version=self.variable_version, assign_node=self
        )

    @staticmethod
    def hasVeryTrustedValue():
        return False


class StatementAssignmentVariableConstantMutableTrusted(
    StatementAssignmentVariableConstantImmutable
):
    kind = "STATEMENT_ASSIGNMENT_VARIABLE_CONSTANT_MUTABLE_TRUSTED"

    @staticmethod
    def hasVeryTrustedValue():
        return False


class StatementAssignmentVariableConstantImmutableTrusted(
    StatementAssignmentVariableConstantImmutable
):
    kind = "STATEMENT_ASSIGNMENT_VARIABLE_CONSTANT_IMMUTABLE_TRUSTED"

    @staticmethod
    def hasVeryTrustedValue():
        return True


class StatementAssignmentVariableHardValue(
    StatementAssignmentVariableMixin, StatementAssignmentVariableHardValueBase
):
    kind = "STATEMENT_ASSIGNMENT_VARIABLE_HARD_VALUE"

    named_children = ("source",)
    nice_children = ("assignment source",)
    node_attributes = ("variable", "variable_version")
    auto_compute_handling = "post_init"

    __slots__ = (
        "variable_trace",
        # TODO: Does every variant have to care here
        "inplace_suspect",
    )

    # TODO: Add parsing of node_attributes for init values, so we can avoid these too
    def postInitNode(self):
        self.variable_trace = None
        self.inplace_suspect = None

    @staticmethod
    def getReleaseEscape():
        return ControlFlowDescriptionNoEscape

    def computeStatement(self, trace_collection):
        variable = self.variable

        source = trace_collection.onExpression(self.subnode_source)

        if source.willRaiseAnyException():
            result = makeStatementExpressionOnlyReplacementNode(
                expression=source, node=self
            )

            del self.parent

            return (
                result,
                "new_raise",
                """\
Assignment raises exception in assigned value, removed assignment.""",
            )

        current_trace = trace_collection.getVariableCurrentTrace(variable)

        if current_trace.isAssignTraceVeryTrusted() and (
            source.isExpressionImportModuleHard()
            or source.isExpressionImportModuleFixed()
        ):
            prev_assign_node = current_trace.getAssignNode()
            prev_source = prev_assign_node.subnode_source

            assert (
                prev_source.isExpressionImportModuleHard()
                or prev_source.isExpressionImportModuleFixed()
                or prev_source.isExpressionImportModuleNameHard()
            ), prev_source

            if prev_source.getValueName() == source.getValueName():
                trace_collection.updateVeryTrustedModuleVariable(
                    variable,
                    old_node=source,
                    new_node=prev_source,
                )

                return (
                    makeStatementExpressionOnlyReplacementNode(
                        expression=source, node=self
                    ),
                    "new_statements",
                    "Removed assignment of %s from itself which is known to be defined."
                    % variable.getDescription(),
                )

        self.variable_trace = trace_collection.onVariableSetToVeryTrustedValue(
            variable=variable, version=self.variable_version, assign_node=self
        )

        return self, None, None

    def computeStatementAssignmentTraceUpdate(self, trace_collection, source):
        self.variable_trace = trace_collection.onVariableSetToVeryTrustedValue(
            variable=self.variable, version=self.variable_version, assign_node=self
        )

    @staticmethod
    def hasVeryTrustedValue():
        return True


class StatementAssignmentVariableFromVariable(
    StatementAssignmentVariableMixin, StatementAssignmentVariableFromVariableBase
):
    kind = "STATEMENT_ASSIGNMENT_VARIABLE_FROM_VARIABLE"

    named_children = ("source",)
    nice_children = ("assignment source",)
    node_attributes = ("variable", "variable_version")
    auto_compute_handling = "post_init"

    __slots__ = (
        "variable_trace",
        # TODO: Does every variant have to care here
        "inplace_suspect",
    )

    # TODO: Add parsing of node_attributes for init values, so we can avoid these too
    def postInitNode(self):
        self.variable_trace = None
        self.inplace_suspect = None

    @staticmethod
    def getReleaseEscape():
        # TODO: Variable type may know better.
        return ControlFlowDescriptionFullEscape

    def computeStatement(self, trace_collection):
        old_source = self.subnode_source
        variable = self.variable

        # Module variables may shadow built-in names, so 'x = x' is not a no-op for them.
        # TODO: Specialize self-assignment directly into its own node type.
        if (
            not variable.isModuleVariable()
            and old_source.isExpressionVariableRefOrTempVariableRef()
            and old_source.getVariable() is variable
        ):
            if old_source.mayHaveSideEffects():
                result = makeStatementExpressionOnlyReplacementNode(
                    expression=old_source, node=self
                )

                result = trace_collection.onStatement(result)

                return (
                    result,
                    "new_statements",
                    """\
Lowered assignment of %s from itself to mere access of it."""
                    % variable.getDescription(),
                )
            else:
                return (
                    None,
                    "new_statements",
                    """\
Removed assignment of %s from itself which is known to be defined."""
                    % variable.getDescription(),
                )

        source = trace_collection.onExpression(self.subnode_source)

        if source is old_source:
            result = self, None, None
        else:
            if source.willRaiseAnyException():
                result = makeStatementExpressionOnlyReplacementNode(
                    expression=source, node=self
                )

                return (
                    result,
                    "new_raise",
                    """\
Assignment raises exception in assigned variable access, removed assignment.""",
                )

            result = self._considerSpecialization(old_source, source)

            if result[0] is self and not source.isExpressionVariableRef():
                result = (
                    StatementAssignmentVariableGeneric(
                        source=source,
                        variable=self.variable,
                        variable_version=self.variable_version,
                        source_ref=self.source_ref,
                    ),
                    "new_statements",
                    "Assignment source is no longer a variable reference.",
                )

            result[0].parent = self.parent

        result[0].computeStatementAssignmentTraceUpdate(trace_collection, source)

        return result

    def computeStatementAssignmentTraceUpdate(self, trace_collection, source):
        if source.isExpressionVariableRef():
            self.variable_trace = trace_collection.onVariableSetAliasing(
                variable=self.variable,
                version=self.variable_version,
                assign_node=self,
                source=source,
            )
        else:
            # Non-variable sources are converted to generic assignments in
            # 'computeStatement', but restored or cloned trees may still get
            # here, where the trace must not assume a variable source.
            self.variable_trace = trace_collection.onVariableSet(
                variable=self.variable, version=self.variable_version, assign_node=self
            )

            # TODO: Determine from future use of assigned variable, if this is needed at all.
            trace_collection.removeKnowledge(source)

    @staticmethod
    def hasVeryTrustedValue():
        return False


class StatementAssignmentVariableFromTempVariable(
    StatementAssignmentVariableMixin, StatementAssignmentVariableFromTempVariableBase
):
    kind = "STATEMENT_ASSIGNMENT_VARIABLE_FROM_TEMP_VARIABLE"

    named_children = ("source",)
    nice_children = ("assignment source",)
    node_attributes = ("variable", "variable_version")
    auto_compute_handling = "post_init"

    __slots__ = (
        "variable_trace",
        # TODO: Does every variant have to care here
        "inplace_suspect",
    )

    # TODO: Add parsing of node_attributes for init values, so we can avoid these too
    def postInitNode(self):
        self.variable_trace = None
        self.inplace_suspect = None

    @staticmethod
    def getReleaseEscape():
        # TODO: Variable type may know better.
        return ControlFlowDescriptionFullEscape

    def computeStatement(self, trace_collection):
        old_source = self.subnode_source
        variable = self.variable

        if (
            old_source.isExpressionVariableRefOrTempVariableRef()
            and old_source.getVariable() is variable
        ):
            return (
                None,
                "new_statements",
                """\
Removed assignment of %s from itself which is known to be defined."""
                % variable.getDescription(),
            )

        source = trace_collection.onExpression(self.subnode_source)

        if source is old_source:
            result = self, None, None
        else:
            result = self._considerSpecialization(old_source, source)

            if result[0] is self and not source.isExpressionTempVariableRef():
                result = (
                    StatementAssignmentVariableGeneric(
                        source=source,
                        variable=self.variable,
                        variable_version=self.variable_version,
                        source_ref=self.source_ref,
                    ),
                    "new_statements",
                    "Assignment source is no longer a temporary variable reference.",
                )

            result[0].parent = self.parent

        result[0].computeStatementAssignmentTraceUpdate(trace_collection, source)

        return result

    def computeStatementAssignmentTraceUpdate(self, trace_collection, source):
        self.variable_trace = trace_collection.onVariableSet(
            variable=self.variable, version=self.variable_version, assign_node=self
        )

        # TODO: Determine from future use of assigned variable, if this is needed at all.
        trace_collection.removeKnowledge(source)

    @staticmethod
    def hasVeryTrustedValue():
        return False


def makeStatementAssignmentVariableConstant(
    source, variable, variable_version, very_trusted, source_ref
):
    if source.isMutable():
        if very_trusted:
            return StatementAssignmentVariableConstantMutableTrusted(
                source=source,
                variable=variable,
                source_ref=source_ref,
                variable_version=variable_version,
            )
        else:
            return StatementAssignmentVariableConstantMutable(
                source=source,
                variable=variable,
                source_ref=source_ref,
                variable_version=variable_version,
            )
    else:
        if very_trusted:
            return StatementAssignmentVariableConstantImmutableTrusted(
                source=source,
                variable=variable,
                source_ref=source_ref,
                variable_version=variable_version,
            )
        else:
            return StatementAssignmentVariableConstantImmutable(
                source=source,
                variable=variable,
                source_ref=source_ref,
                variable_version=variable_version,
            )


def makeStatementAssignmentVariable(
    source, variable, source_ref, variable_version=None
):
    assert source is not None, source_ref

    if variable_version is None:
        variable_version = variable.allocateTargetNumber()

    if source.isCompileTimeConstant():
        return makeStatementAssignmentVariableConstant(
            source=source,
            variable=variable,
            variable_version=variable_version,
            very_trusted=False,
            source_ref=source_ref,
        )
    elif source.isExpressionVariableRef():
        return StatementAssignmentVariableFromVariable(
            source=source,
            variable=variable,
            variable_version=variable_version,
            source_ref=source_ref,
        )
    elif source.isExpressionTempVariableRef():
        return StatementAssignmentVariableFromTempVariable(
            source=source,
            variable=variable,
            variable_version=variable_version,
            source_ref=source_ref,
        )
    elif source.hasVeryTrustedValue():
        return StatementAssignmentVariableHardValue(
            source=source,
            variable=variable,
            variable_version=variable_version,
            source_ref=source_ref,
        )
    elif source.getTypeShape().isShapeIterator():
        return StatementAssignmentVariableIterator(
            source=source,
            variable=variable,
            variable_version=variable_version,
            source_ref=source_ref,
        )
    else:
        return StatementAssignmentVariableGeneric(
            source=source,
            variable=variable,
            variable_version=variable_version,
            source_ref=source_ref,
        )


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
