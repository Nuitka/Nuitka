#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Assignment related nodes.

The most simple assignment statement ``a = b`` is what we have here. All others
are either re-formulated using temporary variables, e.g. ``a, b = c`` or are
attribute, slice, subscript assignments.

The deletion is a separate node unlike in CPython where assigning to ``NULL`` is
internally what deletion is. But deleting is something entirely different to us
during code generation, which is why we keep them separate.

Tracing assignments in SSA form is the core of optimization for which we use
the traces.

"""

from abc import abstractmethod

from nuitka.ModuleRegistry import getOwnerFromCodeName
from nuitka.Options import isExperimental

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
from .shapes.StandardShapes import tshape_iterator, tshape_unknown
from .StatementBasesGenerated import (
    StatementAssignmentVariableConstantImmutableBase,
    StatementAssignmentVariableConstantMutableBase,
    StatementAssignmentVariableFromTempVariableBase,
    StatementAssignmentVariableFromVariableBase,
    StatementAssignmentVariableGenericBase,
    StatementAssignmentVariableHardValueBase,
    StatementAssignmentVariableIteratorBase,
)
from .VariableDelNodes import makeStatementDelVariable
from .VariableRefNodes import ExpressionTempVariableRef


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

    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    @staticmethod
    def isStatementAssignmentVariable():
        return True

    def finalize(self):
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
        # Virtual method overload, pylint: disable=unused-argument
        owner = getOwnerFromCodeName(args["owner"])

        if args["is_temp"] == "True":
            variable = owner.createTempVariable(
                args["variable_name"], temp_type=["var_type"]
            )
        else:
            variable = owner.getProvidedVariable(args["variable_name"])

        del args["is_temp"]
        del args["var_type"]
        del args["owner"]

        version = variable.allocateTargetNumber()

        return cls(variable=variable, version=version, source_ref=source_ref, **args)

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
        previous = self.variable_trace.getPrevious()

        if previous.mustNotHaveValue():
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
                "Assignment source is now known to be hard import.",
            )

        return self, None, None

    def collectVariableAccesses(self, emit_read, emit_write):
        emit_write(self.variable)
        self.subnode_source.collectVariableAccesses(emit_read, emit_write)

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

    # False alarm due to post_init, pylint: disable=attribute-defined-outside-init

    # TODO: Add parsing of node_attributes for init values, so we can avoid these too
    def postInitNode(self):
        self.variable_trace = None
        self.inplace_suspect = None

    @staticmethod
    def getReleaseEscape():
        return ControlFlowDescriptionFullEscape

    def computeStatement(self, trace_collection):
        # TODO: Way too ugly to have global trace kinds just here, and needs to
        # be abstracted somehow. But for now we let it live here.
        old_source = self.subnode_source
        variable = self.variable

        if old_source.isExpressionSideEffects():
            # If the assignment source has side effects, we can put them into a
            # sequence and compute that instead.
            statements = [
                makeStatementExpressionOnlyReplacementNode(side_effect, self)
                for side_effect in old_source.subnode_side_effects
            ]

            statements.append(self)

            # Remember out parent, we will assign it for the sequence to use.
            parent = self.parent

            # Need to update ourselves to no longer reference the side effects,
            # but go to the wrapped thing.
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

        # Let assignment source may re-compute first.
        source = trace_collection.onExpression(self.subnode_source)

        # No assignment will occur, if the assignment source raises, so give up
        # on this, and return it as the only side effect.
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

        # Assigning from and to the same variable, can be optimized away
        # immediately, there is no point in doing it. Exceptions are of course
        # module variables that collide with built-in names.

        # TODO: The variable type checks ought to become unnecessary, as they
        # are to be a feature of the trace. Assigning from known assigned is
        # supposed to be possible to eliminate. If we get that wrong, we are
        # doing it wrong.
        if (
            not variable.isModuleVariable()
            and source.isExpressionVariableRef()
            and source.getVariable() is variable
        ):
            # A variable access that has a side effect, must be preserved,
            # so it can e.g. raise an exception, otherwise we can be fully
            # removed.
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
        # Set-up the trace to the trace collection, so future references will
        # find this assignment.
        self.variable_trace = trace_collection.onVariableSet(
            variable=self.variable, version=self.variable_version, assign_node=self
        )

        # TODO: Determine from future use of assigned variable, if this is needed at all.
        trace_collection.removeKnowledge(source)

    def hasVeryTrustedValue(self):
        """Does this assignment node have a very trusted value."""
        return self.subnode_source.hasVeryTrustedValue()


class StatementAssignmentVariableIterator(
    StatementAssignmentVariableMixin, StatementAssignmentVariableIteratorBase
):
    # Carries state for propagating iterators potentially.

    # TODO: Maybe have a namedtuple with these intended for index replacement,
    # they form once set of things pylint: disable=too-many-instance-attributes

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
        "temp_scope",
        "tmp_iterated_variable",
        "tmp_iteration_count_variable",
        "tmp_iteration_next_variable",
        "is_indexable",
    )

    # False alarm due to post_init, pylint: disable=attribute-defined-outside-init

    # TODO: Add parsing of node_attributes for init values, so we can avoid these too
    def postInitNode(self):
        self.variable_trace = None
        self.inplace_suspect = None

        # Have a valid start value, later this will become more specific.
        self.type_shape = tshape_iterator

        # For replacing with indexing potentially.
        self.temp_scope = None
        self.tmp_iterated_variable = None
        self.tmp_iteration_count_variable = None
        self.tmp_iteration_next_variable = None

        # When found non-indexable, we do not try again.
        self.is_indexable = None

    def getTypeShape(self):
        return self.type_shape

    @staticmethod
    def getReleaseEscape():
        # TODO: For iteration over constants that wouldn't be necessary,
        # but if we know the iteration well enough, it's supposed to be
        # converted to something else anyway.
        return ControlFlowDescriptionElementBasedEscape

    def getIterationIndexDesc(self):
        """For use in optimization outputs only, here and using nodes."""
        return "'%s[%s]'" % (
            self.tmp_iterated_variable.getName(),
            self.tmp_iteration_count_variable.getName(),
        )

    def _replaceWithDirectAccess(self, trace_collection, provider):
        self.temp_scope = provider.allocateTempScope("iterator_access")

        self.tmp_iterated_variable = provider.allocateTempVariable(
            temp_scope=self.temp_scope, name="iterated_value", temp_type="object"
        )

        reference_iterated = ExpressionTempVariableRef(
            variable=self.tmp_iterated_variable,
            source_ref=self.subnode_source.source_ref,
        )

        iterated_value = self.subnode_source.subnode_value

        assign_iterated = makeStatementAssignmentVariable(
            source=iterated_value,
            variable=self.tmp_iterated_variable,
            source_ref=iterated_value.source_ref,
        )

        self.tmp_iteration_count_variable = provider.allocateTempVariable(
            temp_scope=self.temp_scope, name="iteration_count", temp_type="object"
        )

        assign_iteration_count = makeStatementAssignmentVariable(
            source=makeConstantRefNode(constant=0, source_ref=self.source_ref),
            variable=self.tmp_iteration_count_variable,
            source_ref=iterated_value.source_ref,
        )

        # TODO: Unclear what node this really is right now, need to try out.
        self.subnode_source.setChildValue(reference_iterated)

        # Make sure variable trace is computed.
        assign_iterated.computeStatement(trace_collection)
        assign_iteration_count.computeStatement(trace_collection)
        reference_iterated.computeExpressionRaw(trace_collection)

        self.variable_trace = trace_collection.onVariableSet(
            variable=self.variable,
            version=self.variable_version,
            assign_node=self,
        )

        # For use when the "next" is replaced.
        self.tmp_iteration_next_variable = provider.allocateTempVariable(
            temp_scope=self.temp_scope, name="next_value", temp_type="object"
        )

        result = makeStatementsSequenceReplacementNode(
            (assign_iteration_count, assign_iterated, self), self
        )

        return (
            result,
            "new_statements",
            lambda: "Enabling indexing of iterated value through %s."
            % self.getIterationIndexDesc(),
        )

    def computeStatement(self, trace_collection):
        # TODO: Way too ugly to have global trace kinds just here, and needs to
        # be abstracted somehow. But for now we let it live here.
        source = self.subnode_source
        variable = self.variable

        provider = trace_collection.getOwner()

        # Let assignment source may re-compute first.
        source = trace_collection.onExpression(self.subnode_source)

        if (
            self.tmp_iterated_variable is None
            and self.is_indexable is None
            and source.isExpressionBuiltinIterForUnpack()
            and isExperimental("iterator-optimization")
        ):
            if variable.hasAccessesOutsideOf(provider) is False:
                last_trace = variable.getMatchingUnescapedAssignTrace(self)

                if last_trace is not None:
                    # Might not be allowed, remember if it's not allowed, otherwise retry.
                    self.is_indexable = (
                        source.subnode_value.getTypeShape().hasShapeIndexLookup()
                    )

                    if self.is_indexable:
                        return self._replaceWithDirectAccess(
                            trace_collection=trace_collection, provider=provider
                        )

        # No assignment will occur, if the assignment source raises, so give up
        # on this, and return it as the only side effect.
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

        self.type_shape = source.getTypeShape()

        # Set-up the trace to the trace collection, so future references will
        # find this assignment.
        # Note: Keep this aligned with computeStatementAssignmentTraceUpdate
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
        """Does this assignment node have a very trusted value."""
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

    # False alarm due to post_init, pylint: disable=attribute-defined-outside-init

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

        # Set-up the trace to the trace collection, so future references will
        # find this assignment.
        # Note: Keep this aligned with computeStatementAssignmentTraceUpdate
        self.variable_trace = trace_collection.onVariableSet(
            variable=variable, version=self.variable_version, assign_node=self
        )

        provider = trace_collection.getOwner()

        if variable.hasAccessesOutsideOf(provider) is False:
            last_trace = variable.getMatchingAssignTrace(self)

            if last_trace is not None and not last_trace.getMergeOrNameUsageCount():
                if (
                    variable.isModuleVariable()
                    or variable.owner.locals_scope.isUnoptimizedFunctionScope()
                ):
                    # TODO: We do not trust these yet a lot, but more might be
                    pass
                else:
                    # Unused constants can be eliminated in any case.
                    if not last_trace.getUsageCount():
                        if not last_trace.getPrevious().isUnassignedTrace():
                            result = makeStatementDelVariable(
                                variable=self.variable,
                                version=self.variable_version,
                                tolerant=True,
                                source_ref=self.source_ref,
                            )
                        else:
                            result = None

                        return (
                            result,
                            "new_statements",
                            "Dropped dead assignment statement to '%s'."
                            % (self.getVariableName()),
                        )

                    # Can safely forward propagate only non-mutable constants.

        return self, None, None

    def computeStatementAssignmentTraceUpdate(self, trace_collection, source):
        self.variable_trace = trace_collection.onVariableSet(
            variable=self.variable, version=self.variable_version, assign_node=self
        )

    @staticmethod
    def hasVeryTrustedValue():
        """Does this assignment node have a very trusted value."""
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

    # False alarm due to post_init, pylint: disable=attribute-defined-outside-init

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

        # Set-up the trace to the trace collection, so future references will
        # find this assignment.
        provider = trace_collection.getOwner()

        if variable.hasAccessesOutsideOf(provider) is False:
            last_trace = variable.getMatchingAssignTrace(self)

            if last_trace is not None and not last_trace.getMergeOrNameUsageCount():
                if (
                    variable.isModuleVariable()
                    or variable.owner.locals_scope.isUnoptimizedFunctionScope()
                ):
                    # TODO: We do not trust these yet a lot, but more might be
                    pass
                else:
                    # Unused constants can be eliminated in any case.
                    if not last_trace.getUsageCount():
                        if not last_trace.getPrevious().isUnassignedTrace():
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
                        else:
                            return (
                                None,
                                "new_statements",
                                "Dropped dead assignment statement to '%s'."
                                % (self.getVariableName()),
                            )

                    # Still trace or assignment, for the last time. TODO: Maybe this can be
                    # used for the keeping of the "replacement node" as well.
                    self.variable_trace = trace_collection.onVariableSetToUnescapablePropagatedValue(
                        variable=variable,
                        version=self.variable_version,
                        assign_node=self,
                        replacement=lambda _replaced_node: self.subnode_source.makeClone(),
                    )

                    if not last_trace.getPrevious().isUnassignedTrace():
                        result = makeStatementDelVariable(
                            variable=self.variable,
                            version=self.variable_version,
                            tolerant=True,
                            source_ref=self.source_ref,
                        )
                    else:
                        result = None

                    return (
                        result,
                        "new_statements",
                        "Dropped propagated assignment statement to '%s'."
                        % self.getVariableName(),
                    )

        # Note: Keep this aligned with computeStatementAssignmentTraceUpdate
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
        """Does this assignment node have a very trusted value."""
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

    # False alarm due to post_init, pylint: disable=attribute-defined-outside-init

    # TODO: Add parsing of node_attributes for init values, so we can avoid these too
    def postInitNode(self):
        self.variable_trace = None
        self.inplace_suspect = None

    @staticmethod
    def getReleaseEscape():
        return ControlFlowDescriptionNoEscape

    def computeStatement(self, trace_collection):
        # TODO: Way too ugly to have global trace kinds just here, and needs to
        # be abstracted somehow. But for now we let it live here.
        variable = self.variable

        # Let assignment source may re-compute first.
        source = trace_collection.onExpression(self.subnode_source)

        # No assignment will occur, if the assignment source raises, so give up
        # on this, and return it as the only side effect.
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

        # Note: Keep this aligned with computeStatementAssignmentTraceUpdate
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
        """Does this assignment node have a very trusted value."""
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

    # False alarm due to post_init, pylint: disable=attribute-defined-outside-init

    # TODO: Add parsing of node_attributes for init values, so we can avoid these too
    def postInitNode(self):
        self.variable_trace = None
        self.inplace_suspect = None

    @staticmethod
    def getReleaseEscape():
        # TODO: Variable type may know better.
        return ControlFlowDescriptionFullEscape

    def computeStatement(self, trace_collection):
        # TODO: Way too ugly to have global trace kinds just here, and needs to
        # be abstracted somehow. But for now we let it live here.
        old_source = self.subnode_source
        variable = self.variable

        # Assigning from and to the same variable, can be optimized away
        # immediately, there is no point in doing it. Exceptions are of course
        # module variables that collide with built-in names. TODO: In
        # specialization this could be considered right away as its own node
        # type, waiting for it to compute like this.
        if not variable.isModuleVariable() and old_source.getVariable() is variable:
            # A variable access that has a side effect, must be preserved,
            # so it can e.g. raise an exception, otherwise we can be fully
            # removed.
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

        # Let assignment source may re-compute first.
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
            # Set-up the trace to the trace collection, so future references will
            # find this assignment. TODO: We should for non-variables make sure we do
            # always specialize, since this is no longer a variable once it was
            # resolved.
            self.variable_trace = trace_collection.onVariableSet(
                variable=self.variable, version=self.variable_version, assign_node=self
            )

            # TODO: Determine from future use of assigned variable, if this is needed at all.
            trace_collection.removeKnowledge(source)

    @staticmethod
    def hasVeryTrustedValue():
        """Does this assignment node have a very trusted value."""
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

    # False alarm due to post_init, pylint: disable=attribute-defined-outside-init

    # TODO: Add parsing of node_attributes for init values, so we can avoid these too
    def postInitNode(self):
        self.variable_trace = None
        self.inplace_suspect = None

    @staticmethod
    def getReleaseEscape():
        # TODO: Variable type may know better.
        return ControlFlowDescriptionFullEscape

    def computeStatement(self, trace_collection):
        # TODO: Way too ugly to have global trace kinds just here, and needs to
        # be abstracted somehow. But for now we let it live here.
        old_source = self.subnode_source
        variable = self.variable

        # Assigning from and to the same variable, can be optimized away
        # immediately, there is no point in doing it. Exceptions are of course
        # module variables that collide with built-in names.
        if old_source.getVariable() is variable:
            return (
                None,
                "new_statements",
                """\
Removed assignment of %s from itself which is known to be defined."""
                % variable.getDescription(),
            )

        # Let assignment source may re-compute first.
        source = trace_collection.onExpression(self.subnode_source)

        if source is old_source:
            result = self, None, None
        else:
            result = self._considerSpecialization(old_source, source)
            result[0].parent = self.parent

        result[0].computeStatementAssignmentTraceUpdate(trace_collection, source)

        return result

    def computeStatementAssignmentTraceUpdate(self, trace_collection, source):
        # Set-up the trace to the trace collection, so future references will
        # find this assignment.
        self.variable_trace = trace_collection.onVariableSet(
            variable=self.variable, version=self.variable_version, assign_node=self
        )

        # TODO: Determine from future use of assigned variable, if this is needed at all.
        trace_collection.removeKnowledge(source)

    @staticmethod
    def hasVeryTrustedValue():
        """Does this assignment node have a very trusted value."""
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
    elif source.getTypeShape().isShapeIterator():
        return StatementAssignmentVariableIterator(
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
