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

from .NodeBases import StatementChildHavingBase
from .NodeMakingHelpers import (
    makeStatementExpressionOnlyReplacementNode,
    makeStatementsSequenceReplacementNode,
)
from .shapes.StandardShapes import tshape_unknown
from .VariableDelNodes import makeStatementDelVariable


class StatementAssignmentVariable(StatementChildHavingBase):
    """Assignment to a variable from an expression.

    All assignment forms that are not to attributes, slices, subscripts
    use this.

    The source might be a complex expression. The target can be any kind
    of variable, temporary, local, global, etc.

    Assigning a variable is something we trace in a new version, this is
    hidden behind target variable reference, which has this version once
    it can be determined.
    """

    kind = "STATEMENT_ASSIGNMENT_VARIABLE"

    named_child = "source"
    nice_child = "assignment source"

    __slots__ = (
        "subnode_source",
        "variable",
        "variable_version",
        "variable_trace",
        "inplace_suspect",
    )

    def __init__(self, source, variable, source_ref, version=None):
        assert source is not None, source_ref

        if version is None:
            version = variable.allocateTargetNumber()

        self.variable = variable
        self.variable_version = version

        StatementChildHavingBase.__init__(self, value=source, source_ref=source_ref)

        self.variable_trace = None
        self.inplace_suspect = None

    def finalize(self):
        StatementChildHavingBase.finalize(self)

        del self.variable
        del self.variable_trace

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
        assert cls is StatementAssignmentVariable, cls

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
        if self.variable is not None:
            version = self.variable.allocateTargetNumber()
        else:
            version = None

        return StatementAssignmentVariable(
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

    def unmarkAsInplaceSuspect(self):
        self.inplace_suspect = False

    def mayRaiseException(self, exception_type):
        return self.subnode_source.mayRaiseException(exception_type)

    def computeStatement(self, trace_collection):
        # This is very complex stuff, pylint: disable=too-many-branches,too-many-return-statements

        # TODO: Way too ugly to have global trace kinds just here, and needs to
        # be abstracted somehow. But for now we let it live here.
        source = self.subnode_source

        if source.isExpressionSideEffects():
            # If the assignment source has side effects, we can put them into a
            # sequence and compute that instead.
            statements = [
                makeStatementExpressionOnlyReplacementNode(side_effect, self)
                for side_effect in source.subnode_side_effects
            ]

            statements.append(self)

            # Remember out parent, we will assign it for the sequence to use.
            parent = self.parent

            # Need to update ourselves to no longer reference the side effects,
            # but go to the wrapped thing.
            self.setChild("source", source.subnode_expression)

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

        variable = self.variable

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

        provider = trace_collection.getOwner()

        if variable.hasAccessesOutsideOf(provider) is False:
            last_trace = variable.getMatchingAssignTrace(self)

            if last_trace is not None and not last_trace.getMergeOrNameUsageCount():
                if source.isCompileTimeConstant():
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
                        if not source.isMutable():
                            self.variable_trace.setReplacementNode(
                                lambda _usage: source.makeClone()
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
                elif source.isExpressionFunctionCreation():
                    # TODO: Prepare for inlining.
                    pass
                else:
                    # More cases thinkable.
                    pass

        return self, None, None

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
