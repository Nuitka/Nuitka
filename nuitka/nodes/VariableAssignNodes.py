#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.ModuleRegistry import getOwnerFromCodeName
from nuitka.Options import isExperimental

from .ConstantRefNodes import makeConstantRefNode
from .NodeBases import StatementChildHavingBase
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
from .VariableDelNodes import makeStatementDelVariable
from .VariableRefNodes import ExpressionTempVariableRef


class StatementAssignmentVariableBase(StatementChildHavingBase):
    """Assignment to a variable from an expression.

    All assignment forms that are not to attributes, slices, subscripts
    use this.

    The source might be a complex expression. The target can be any kind
    of variable, temporary, local, global, etc.

    Assigning a variable is something we trace in a new version, this is
    hidden behind target variable reference, which has this version once
    it can be determined.
    """

    named_child = "source"
    nice_child = "assignment source"

    __slots__ = (
        "subnode_source",
        "variable",
        "variable_version",
        "variable_trace",
        "inplace_suspect",
    )

    def __init__(self, source, variable, version, source_ref):
        assert version is not None, source_ref

        self.variable = variable
        self.variable_version = version

        StatementChildHavingBase.__init__(self, value=source, source_ref=source_ref)

        self.variable_trace = None
        self.inplace_suspect = None

    @staticmethod
    def isStatementAssignmentVariable():
        return True

    def finalize(self):
        del self.variable
        del self.variable_trace
        self.subnode_source.finalize()
        del self.subnode_source

    def getDetails(self):
        return {"variable": self.variable}

    def getDetailsForDisplay(self):
        return {
            "variable_name": self.getVariableName(),
            "is_temp": self.variable.isTempVariable(),
            "var_type": self.variable.getVariableType(),
            "owner": self.variable.getOwner().getCodeName(),
        }

    @classmethod
    def fromXML(cls, provider, source_ref, **args):
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
            version=version,
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

    def _transferState(self, result):
        self.variable_trace.assign_node = result
        result.variable_trace = self.variable_trace
        self.variable_trace = None

    def _considerSpecialization(self, old_source):
        # Specialize if possible, might have become that way only recently.
        # return driven, pylint: disable=too-many-return-statements
        source = self.subnode_source

        if source is old_source:
            return self, None, None

        if source.isCompileTimeConstant():
            result = makeStatementAssignmentVariableConstant(
                source=source,
                variable=self.variable,
                version=self.variable_version,
                source_ref=self.source_ref,
            )

            self._transferState(result)

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
                version=self.variable_version,
                source_ref=self.source_ref,
            )

            self._transferState(result)

            return (
                result,
                "new_statements",
                "Assignment source is now variable reference.",
            )

        if source.isExpressionTempVariableRef():
            result = StatementAssignmentVariableFromTempVariable(
                source=source,
                variable=self.variable,
                version=self.variable_version,
                source_ref=self.source_ref,
            )

            self._transferState(result)

            return (
                result,
                "new_statements",
                "Assignment source is now temp variable reference.",
            )

        if source.getTypeShape().isShapeIterator():
            result = StatementAssignmentVariableIterator(
                source=source,
                variable=self.variable,
                version=self.variable_version,
                source_ref=self.source_ref,
            )

            self._transferState(result)

            return (
                result,
                "new_statements",
                "Assignment source is now known to be iterator.",
            )

        if source.hasVeryTrustedValue():
            result = StatementAssignmentVariableHardValue(
                source=source,
                variable=self.variable,
                version=self.variable_version,
                source_ref=self.source_ref,
            )

            self._transferState(result)

            return (
                result,
                "new_statements",
                "Assignment source is now known to be hard import.",
            )

        return self, None, None


class StatementAssignmentVariableGeneric(StatementAssignmentVariableBase):
    kind = "STATEMENT_ASSIGNMENT_VARIABLE_GENERIC"

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
            self.setChild("source", old_source.subnode_expression)

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
        if source.willRaiseException(BaseException):
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

        # Set-up the trace to the trace collection, so future references will
        # find this assignment.
        self.variable_trace = trace_collection.onVariableSet(
            variable=variable, version=self.variable_version, assign_node=self
        )

        # TODO: Determine from future use of assigned variable, if this is needed at all.
        trace_collection.removeKnowledge(source)

        return self._considerSpecialization(old_source)


class StatementAssignmentVariableIterator(StatementAssignmentVariableBase):
    # Carries a lot of state for propagating iterators potentially.
    # pylint: disable=too-many-instance-attributes

    kind = "STATEMENT_ASSIGNMENT_VARIABLE_ITERATOR"

    __slots__ = (
        "type_shape",
        "temp_scope",
        "tmp_iterated_variable",
        "tmp_iteration_count_variable",
        "tmp_iteration_next_variable",
        "is_indexable",
    )

    def __init__(self, source, variable, version, source_ref):
        StatementAssignmentVariableBase.__init__(
            self,
            source=source,
            variable=variable,
            version=version,
            source_ref=source_ref,
        )

        self.type_shape = tshape_iterator

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
            temp_scope=self.temp_scope, name="iterated_value"
        )

        reference_iterated = ExpressionTempVariableRef(
            variable=self.tmp_iterated_variable,
            source_ref=self.subnode_source.source_ref,
        )

        iterated_value = self.subnode_source.subnode_value

        assign_iterated = makeStatementAssignmentVariable(
            source=iterated_value,
            variable=self.tmp_iterated_variable,
            version=None,
            source_ref=iterated_value.source_ref,
        )

        self.tmp_iteration_count_variable = provider.allocateTempVariable(
            temp_scope=self.temp_scope, name="iteration_count"
        )

        assign_iteration_count = makeStatementAssignmentVariable(
            source=makeConstantRefNode(constant=0, source_ref=self.source_ref),
            variable=self.tmp_iteration_count_variable,
            version=None,
            source_ref=iterated_value.source_ref,
        )

        self.subnode_source.setChild("value", reference_iterated)

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
            temp_scope=self.temp_scope, name="next_value"
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
        if source.willRaiseException(BaseException):
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
        self.variable_trace = trace_collection.onVariableSet(
            variable=variable, version=self.variable_version, assign_node=self
        )

        return self, None, None


class StatementAssignmentVariableConstantMutable(StatementAssignmentVariableBase):
    kind = "STATEMENT_ASSIGNMENT_VARIABLE_CONSTANT_MUTABLE"

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


class StatementAssignmentVariableConstantImmutable(StatementAssignmentVariableBase):
    kind = "STATEMENT_ASSIGNMENT_VARIABLE_CONSTANT_IMMUTABLE"

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

        self.variable_trace = trace_collection.onVariableSetToUnescapableValue(
            variable=variable, version=self.variable_version, assign_node=self
        )

        return self, None, None


class StatementAssignmentVariableHardValue(StatementAssignmentVariableBase):
    kind = "STATEMENT_ASSIGNMENT_VARIABLE_HARD_VALUE"

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
        if source.willRaiseException(BaseException):
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

        self.variable_trace = trace_collection.onVariableSetToVeryTrustedValue(
            variable=variable, version=self.variable_version, assign_node=self
        )

        return self, None, None


class StatementAssignmentVariableFromVariable(StatementAssignmentVariableBase):
    kind = "STATEMENT_ASSIGNMENT_VARIABLE_FROM_VARIABLE"

    @staticmethod
    def getReleaseEscape():
        # TODO: Variable type may know better.
        return ControlFlowDescriptionFullEscape

    def computeStatement(self, trace_collection):
        # TODO: Way too ugly to have global trace kinds just here, and needs to
        # be abstracted somehow. But for now we let it live here.
        old_source = self.subnode_source
        variable = self.variable

        if not variable.isModuleVariable() and old_source.getVariable() is variable:
            # A variable access that has a side effect, must be preserved,
            # so it can e.g. raise an exception, otherwise we can be fully
            # removed.
            if old_source.mayHaveSideEffects():
                result = makeStatementExpressionOnlyReplacementNode(
                    expression=old_source, node=self
                )

                return (
                    result.computeStatementsSequence(trace_collection),
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

        # Assigning from and to the same variable, can be optimized away
        # immediately, there is no point in doing it. Exceptions are of course
        # module variables that collide with built-in names.

        # Set-up the trace to the trace collection, so future references will
        # find this assignment.
        self.variable_trace = trace_collection.onVariableSet(
            variable=variable, version=self.variable_version, assign_node=self
        )

        # TODO: Determine from future use of assigned variable, if this is needed at all.
        trace_collection.removeKnowledge(source)

        return self._considerSpecialization(old_source)


class StatementAssignmentVariableFromTempVariable(StatementAssignmentVariableBase):
    kind = "STATEMENT_ASSIGNMENT_VARIABLE_FROM_TEMP_VARIABLE"

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

        # Set-up the trace to the trace collection, so future references will
        # find this assignment.
        self.variable_trace = trace_collection.onVariableSet(
            variable=variable, version=self.variable_version, assign_node=self
        )

        # TODO: Determine from future use of assigned variable, if this is needed at all.
        trace_collection.removeKnowledge(source)

        return self._considerSpecialization(old_source)


def makeStatementAssignmentVariableConstant(source, variable, version, source_ref):
    if source.isMutable():
        return StatementAssignmentVariableConstantMutable(
            source=source, variable=variable, source_ref=source_ref, version=version
        )
    else:
        return StatementAssignmentVariableConstantImmutable(
            source=source, variable=variable, source_ref=source_ref, version=version
        )


def makeStatementAssignmentVariable(source, variable, source_ref, version=None):
    assert source is not None, source_ref

    if version is None:
        version = variable.allocateTargetNumber()

    if source.isCompileTimeConstant():
        return makeStatementAssignmentVariableConstant(
            source=source, variable=variable, version=version, source_ref=source_ref
        )
    elif source.isExpressionVariableRef():
        return StatementAssignmentVariableFromVariable(
            source=source, variable=variable, version=version, source_ref=source_ref
        )
    elif source.isExpressionTempVariableRef():
        return StatementAssignmentVariableFromTempVariable(
            source=source, variable=variable, version=version, source_ref=source_ref
        )
    elif source.getTypeShape().isShapeIterator():
        return StatementAssignmentVariableIterator(
            source=source, variable=variable, version=version, source_ref=source_ref
        )
    elif source.hasVeryTrustedValue():
        return StatementAssignmentVariableHardValue(
            source=source, variable=variable, version=version, source_ref=source_ref
        )
    else:
        return StatementAssignmentVariableGeneric(
            source=source, variable=variable, source_ref=source_ref, version=version
        )
