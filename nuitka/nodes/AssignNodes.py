#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .NodeBases import NodeBase, StatementChildrenHavingBase
from .NodeMakingHelpers import (
    makeStatementExpressionOnlyReplacementNode,
    makeStatementsSequenceReplacementNode
)


class StatementAssignmentVariableName(StatementChildrenHavingBase):
    """ Precursor of StatementAssignmentVariable used during tree building phase

    """

    kind = "STATEMENT_ASSIGNMENT_VARIABLE_NAME"

    named_children = (
        "source",
    )

    def __init__(self, provider, variable_name, source, source_ref):
        assert source is not None, source_ref

        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "source"       : source,
            },
            source_ref = source_ref
        )

        self.variable_name = variable_name
        self.provider = provider

        assert not provider.isExpressionOutlineBody(), source_ref

    def getDetails(self):
        return {
            "variable_name" : self.variable_name,
            "provider" : self.provider
        }

    def getVariableName(self):
        return self.variable_name

    def computeStatement(self, trace_collection):
        # Only for abc, pylint: disable=no-self-use
        assert False

    getAssignSource = StatementChildrenHavingBase.childGetter(
        "source"
    )


class StatementDelVariableName(NodeBase):
    """ Precursor of StatementDelVariable used during tree building phase

    """

    kind = "STATEMENT_DEL_VARIABLE_NAME"

    __slots__ = "variable_name", "provider", "tolerant"

    def __init__(self, provider, variable_name, tolerant, source_ref):
        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

        self.variable_name = variable_name
        self.provider = provider

        self.tolerant = tolerant

    def getDetails(self):
        return {
            "variable_name" : self.variable_name,
            "provider" : self.provider,
            "tolerant" : self.tolerant
        }

    def getVariableName(self):
        return self.variable_name

    def computeStatement(self, trace_collection):
        # Only for abc, pylint: disable=no-self-use
        assert False


class StatementAssignmentVariable(StatementChildrenHavingBase):
    """ Assignment to a variable from an expression.

        All assignment forms that are not to attributes, slices, subscripts
        use this.

        The source might be a complex expression. The target can be any kind
        of variable, temporary, local, global, etc.

        Assigning a variable is something we trace in a new version, this is
        hidden behind target variable reference, which has this version once
        it can be determined.
    """

    kind = "STATEMENT_ASSIGNMENT_VARIABLE"

    named_children = (
        "source",
    )

    inplace_suspect = None

    def __init__(self, source, variable, source_ref, version = None):
        assert source is not None, source_ref

        if variable is not None:
            if version is None:
                version = variable.allocateTargetNumber()

        self.variable = variable
        self.variable_version = version

        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "source"       : source,
            },
            source_ref = source_ref
        )

        self.variable_trace = None

    def getDetail(self):
        if self.variable is not None:
            return "to variable %s" % self.variable
        else:
            return "to variable %s" % self.variable_name

    def getDetails(self):
        return {
            "variable"      : self.variable,
        }

    def getDetailsForDisplay(self):
        return {
            "variable_name" : self.getVariableName(),
            "is_temp"       : self.variable.isTempVariable(),
            "owner"         : self.variable.getOwner().getCodeName(),
        }

    @classmethod
    def fromXML(cls, provider, source_ref, **args):
        assert cls is StatementAssignmentVariable, cls

        owner = getOwnerFromCodeName(args["owner"])

        if args["is_temp"] == "True":
            variable = owner.createTempVariable(args["variable_name"])
        else:
            variable = owner.getProvidedVariable(args["variable_name"])

        del args["is_temp"]
        del args["owner"]

        version = variable.allocateTargetNumber()

        return cls(
            variable   = variable,
            version    = version,
            source_ref = source_ref,
            **args
        )

    def makeClone(self):
        if self.variable is not None:
            version = self.variable.allocateTargetNumber()
        else:
            version = None

        return StatementAssignmentVariable(
            source     = self.getAssignSource().makeClone(),
            variable   = self.variable,
            version    = version,
            source_ref = self.source_ref
        )

    getAssignSource = StatementChildrenHavingBase.childGetter(
        "source"
    )
    setAssignSource = StatementChildrenHavingBase.childSetter(
        "source"
    )

    def getVariableName(self):
        return self.variable.getName()

    def getVariable(self):
        return self.variable

    def setVariable(self, variable):
        self.variable = variable
        self.variable_version = variable.allocateTargetNumber()

    def getVariableVersion(self):
        return self.variable_version

    def markAsInplaceSuspect(self):
        self.inplace_suspect = True

    def isInplaceSuspect(self):
        return self.inplace_suspect

    def mayRaiseException(self, exception_type):
        return self.getAssignSource().mayRaiseException(exception_type)

    def computeStatement(self, trace_collection):
        # This is very complex stuff, pylint: disable=too-many-branches

        # TODO: Way too ugly to have global trace kinds just here, and needs to
        # be abstracted somehow. But for now we let it live here.
        source = self.getAssignSource()

        if source.isExpressionSideEffects():
            # If the assignment source has side effects, we can put them into a
            # sequence and compute that instead.
            statements = [
                makeStatementExpressionOnlyReplacementNode(
                    side_effect,
                    self
                )
                for side_effect in
                source.getSideEffects()
            ]

            statements.append(self)

            # Remember out parent, we will assign it for the sequence to use.
            parent = self.parent

            # Need to update ourselves to no longer reference the side effects,
            # but go to the wrapped thing.
            self.setAssignSource(source.getExpression())

            result = makeStatementsSequenceReplacementNode(
                statements = statements,
                node       = self,
            )
            result.parent = parent

            return (
                result.computeStatementsSequence(trace_collection),
                "new_statements",
"""\
Side effects of assignments promoted to statements."""
            )

        # Let assignment source may re-compute first.
        trace_collection.onExpression(self.getAssignSource())
        source = self.getAssignSource()

        # No assignment will occur, if the assignment source raises, so give up
        # on this, and return it as the only side effect.
        if source.willRaiseException(BaseException):
            result = makeStatementExpressionOnlyReplacementNode(
                expression = source,
                node       = self
            )

            return result, "new_raise", """\
Assignment raises exception in assigned value, removed assignment."""

        variable = self.variable

        # Not allowed anymore at this point.
        assert variable is not None

        # Assigning from and to the same variable, can be optimized away
        # immediately, there is no point in doing it. Exceptions are of course
        # module variables that collide with built-in names.

        # TODO: The variable type checks ought to become unnecessary, as they
        # are to be a feature of the trace. Assigning from known assigned is
        # supposed to be possible to eliminate. If we get that wrong, we are
        # doing it wrong.
        if not variable.isModuleVariable() and \
           source.isExpressionVariableRef() and \
           source.getVariable() is variable:

            # A variable access that has a side effect, must be preserved,
            # so it can e.g. raise an exception, otherwise we can be fully
            # removed.
            if source.mayHaveSideEffects():
                result = makeStatementExpressionOnlyReplacementNode(
                    expression = source,
                    node       = self
                )

                return result, "new_statements", """\
Reduced assignment of %s from itself to mere access of it.""" % variable.getDescription()
            else:
                return None, "new_statements", """\
Removed assignment of %s from itself which is known to be defined.""" % variable.getDescription()



        # Set-up the trace to the trace collection, so future references will
        # find this assignment.
        self.variable_trace = trace_collection.onVariableSet(
            assign_node = self
        )

        provider = self.getParentVariableProvider()

        if variable.hasAccessesOutsideOf(provider) is False:
            last_trace = variable.getMatchingAssignTrace(self)

            if last_trace is not None:
                if source.isCompileTimeConstant():
                    # Can safely forward propagate only non-mutable constants.
                    if not source.isMutable():
                        if not last_trace.getNameUsageCount():
                            self.variable_trace.setReplacementNode(
                                lambda _usage : source.makeClone()
                            )

                            propagated = True
                        else:
                            propagated = False

                        if not variable.isModuleVariable():
                            if not last_trace.hasPotentialUsages() and not last_trace.getNameUsageCount():
                                if not last_trace.getPrevious().isUninitTrace():
                                    # TODO: We could well decide, if that's even necessary, but for now
                                    # the "StatementDelVariable" is tasked with that.
                                    result = StatementDelVariable(
                                        variable   = self.variable,
                                        version    = self.variable_version,
                                        tolerant   = True,
                                        source_ref = self.getSourceReference()
                                    )
                                else:
                                    result = None

                                return (
                                    result,
                                    "new_statements",
                                    "Dropped %s assignment statement to '%s'." % (
                                       "propagated" if propagated else "dead",
                                       self.getVariableName()
                                    )
                                )
                    else:
                        # Something might be possible still.

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


class StatementDelVariable(NodeBase):
    """ Deleting a variable.

        All del forms that are not to attributes, slices, subscripts
        use this.

        The target can be any kind of variable, temporary, local, global, etc.

        Deleting a variable is something we trace in a new version, this is
        hidden behind target variable reference, which has this version once
        it can be determined.

        Tolerance means that the value might be unset. That can happen with
        re-formulation of ours, and Python3 exception variables.
    """
    kind = "STATEMENT_DEL_VARIABLE"

    __slots__ = "variable", "variable_version", "variable_trace", "previous_trace", "tolerant"

    def __init__(self, tolerant, source_ref, variable, version = None):
        if type(tolerant) is str:
            tolerant = tolerant == "True"

        assert tolerant is True or tolerant is False, repr(tolerant)

        if variable is not None:
            if version is None:
                version = variable.allocateTargetNumber()

        self.variable = variable
        self.variable_version = version

        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

        self.variable_trace = None
        self.previous_trace = None

        self.tolerant = tolerant

    def getDetail(self):
        if self.variable is not None:
            return "to variable %s" % self.variable
        else:
            return "to variable %s" % self.variable_name

    def getDetails(self):
        return {
            "variable" : self.variable,
            "version"  : self.variable_version,
            "tolerant" : self.tolerant
        }

    def getDetailsForDisplay(self):
        return {
            "variable_name" : self.getVariableName(),
            "is_temp"       : self.variable.isTempVariable(),
            "owner"         : self.variable.getOwner().getCodeName(),
            "tolerant"      : self.tolerant
        }

    @classmethod
    def fromXML(cls, provider, source_ref, **args):
        assert cls is StatementDelVariable, cls

        owner = getOwnerFromCodeName(args["owner"])

        if args["is_temp"] == "True":
            variable = owner.createTempVariable(args["variable_name"])
        else:
            variable = owner.getProvidedVariable(args["variable_name"])

        del args["is_temp"]
        del args["owner"]

        version = variable.allocateTargetNumber()
        variable.version_number = max(variable.version_number, version)

        return cls(
            variable   = variable,
            source_ref = source_ref,
            **args
        )

    def makeClone(self):
        if self.variable is not None:
            version = self.variable.allocateTargetNumber()
        else:
            version = None

        return StatementDelVariable(
            variable   = self.variable,
            version    = version,
            tolerant   = self.tolerant,
            source_ref = self.source_ref
        )

    # TODO: Value propagation needs to make a difference based on this.
    def isTolerant(self):
        return self.tolerant

    def getVariableName(self):
        return self.variable.getName()

    def getVariable(self):
        return self.variable

    def setVariable(self, variable):
        assert self.variable_version is None

        self.variable = variable
        self.variable_version = variable.allocateTargetNumber()

    def getVariableVersion(self):
        return self.variable_version

    def computeStatement(self, trace_collection):
        variable = self.variable

        self.previous_trace = trace_collection.getVariableCurrentTrace(variable)

        # First eliminate us entirely if we can.
        if self.tolerant and self.previous_trace.isUninitTrace():
            return (
                None,
                "new_statements",
                "Removed tolerant 'del' statement of '%s' without effect." % (
                    self.getVariableName(),
                )
            )

        # The "del" is a potential use of a value. TODO: This could be made more
        # beautiful indication, as it's not any kind of usage.
        self.previous_trace.addPotentialUsage()

        # If not tolerant, we may exception exit now during the __del__
        if not self.tolerant and not self.previous_trace.mustHaveValue():
            trace_collection.onExceptionRaiseExit(BaseException)

        # Record the deletion, needs to start a new version then.
        trace_collection.onVariableDel(
            variable = variable,
            version  = self.variable_version
        )

        trace_collection.onVariableContentEscapes(variable)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Need to fetch the potentially invalidated variable. A "del" on a
        # or shared value, may easily assign the global variable in "__del__".
        self.variable_trace = trace_collection.getVariableCurrentTrace(variable)

        return self, None, None

    def mayHaveSideEffects(self):
        return True

    def mayRaiseException(self, exception_type):
        if self.tolerant:
            return False
        else:
            if self.variable_trace is not None:
                variable = self.getVariable()

                # Temporary variables deletions won't raise, just because we
                # don't create them that way. We can avoid going through SSA in
                # these cases.
                if variable.isTempVariable():
                    return False

                # If SSA knows, that's fine.
                if self.previous_trace is not None and \
                   self.previous_trace.mustHaveValue():
                    return False

            return True


class StatementReleaseVariable(NodeBase):
    """ Releasing a variable.

        Just release the value, which of course is not to be used afterwards.

        Typical code: Function exit, try/finally release of temporary
        variables.
    """

    kind = "STATEMENT_RELEASE_VARIABLE"

    __slots__ = "variable", "variable_trace"

    def __init__(self, variable, source_ref):
        assert variable is not None, source_ref

        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

        self.variable = variable

        self.variable_trace = None

    def getDetail(self):
        return "of variable %s" % self.variable

    def getDetails(self):
        return {
            "variable" : self.variable
        }

    def getDetailsForDisplay(self):
        return {
            "variable_name" : self.variable.getName(),
            "owner"    : self.variable.getOwner().getCodeName()
        }

    @classmethod
    def fromXML(cls, provider, source_ref, **args):
        assert cls is StatementReleaseVariable, cls

        owner = getOwnerFromCodeName(args["owner"])
        assert owner is not None, args["owner"]

        variable = owner.getProvidedVariable(args["variable_name"])

        return cls(
            variable   = variable,
            source_ref = source_ref
        )

    def getVariable(self):
        return self.variable

    def getVariableVersion(self):
        return self.variable_trace.getVersion()

    def setVariable(self, variable):
        self.variable = variable

    def computeStatement(self, trace_collection):
        self.variable_trace = trace_collection.getVariableCurrentTrace(self.variable)

        if self.variable_trace.isUninitTrace():
            return (
                None,
                "new_statements",
                "Uninitialized %s is not released." % (
                    self.variable.getDescription()
                )
            )

        trace_collection.onVariableContentEscapes(self.variable)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # TODO: We might be able to remove ourselves based on the trace
        # we belong to.

        return self, None, None

    def mayHaveSideEffects(self):
        # May execute __del__ code, it would be sweet to be able to predict
        # that another reference will still be active for a value though.
        return True

    def mayRaiseException(self, exception_type):
        # By default, __del__ is not allowed to raise an exception.
        return False
