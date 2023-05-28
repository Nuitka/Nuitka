#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Nodes for variable deletion

These refer to resolved variable objects.

"""

from abc import abstractmethod

from nuitka.ModuleRegistry import getOwnerFromCodeName
from nuitka.Options import isExperimental
from nuitka.PythonVersions import getUnboundLocalErrorErrorTemplate

from .NodeBases import StatementBase
from .NodeMakingHelpers import makeRaiseExceptionReplacementStatement
from .VariableReleaseNodes import makeStatementReleaseVariable


class StatementDelVariableBase(StatementBase):
    """Deleting a variable.

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

    __slots__ = (
        "variable",
        "variable_version",
        "variable_trace",
        "previous_trace",
    )

    def __init__(self, variable, version, source_ref):
        if variable is not None:
            if version is None:
                version = variable.allocateTargetNumber()

        StatementBase.__init__(self, source_ref=source_ref)

        self.variable = variable
        self.variable_version = version

        self.variable_trace = None
        self.previous_trace = None

    @staticmethod
    def isStatementDelVariable():
        return True

    def finalize(self):
        del self.parent
        del self.variable
        del self.variable_trace
        del self.previous_trace

    def getDetails(self):
        return {
            "variable": self.variable,
            "version": self.variable_version,
        }

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
                args["variable_name"], temp_type=args["var_type"]
            )
        else:
            variable = owner.getProvidedVariable(args["variable_name"])

        del args["is_temp"]
        del args["var_type"]
        del args["owner"]

        version = variable.allocateTargetNumber()
        variable.version_number = max(variable.version_number, version)

        return cls(variable=variable, source_ref=source_ref, **args)

    def makeClone(self):
        if self.variable is not None:
            version = self.variable.allocateTargetNumber()
        else:
            version = None

        return self.__class__(
            variable=self.variable,
            version=version,
            source_ref=self.source_ref,
        )

    def getVariableName(self):
        return self.variable.getName()

    def getVariableTrace(self):
        return self.variable_trace

    def getPreviousVariableTrace(self):
        return self.previous_trace

    def getVariable(self):
        return self.variable

    def setVariable(self, variable):
        self.variable = variable
        self.variable_version = variable.allocateTargetNumber()

    @abstractmethod
    def _computeDelWithoutValue(self, trace_collection):
        """For overload, produce result if deleted variable is found known unset."""

    def computeStatement(self, trace_collection):
        variable = self.variable

        # Special case, boolean temp variables need no "del".
        # TODO: Later, these might not exist, if we forward propagate them not as "del"
        # at all
        if variable.isTempVariableBool():
            return (
                None,
                "new_statements",
                "Removed 'del' statement of boolean '%s' without effect."
                % (self.getVariableName(),),
            )

        self.previous_trace = trace_collection.getVariableCurrentTrace(variable)

        # First eliminate us entirely if we can.
        if self.previous_trace.mustNotHaveValue():
            return self._computeDelWithoutValue(trace_collection)

        if not self.is_tolerant:
            self.previous_trace.addNameUsage()

        # TODO: Why doesn't this module variable check not follow from other checks done here, e.g. name usages.
        # TODO: This currently cannot be done as releases do not create successor traces yet, although they
        # probably should.
        if isExperimental("del_optimization") and not variable.isModuleVariable():
            provider = trace_collection.getOwner()

            if variable.hasAccessesOutsideOf(provider) is False:
                last_trace = variable.getMatchingDelTrace(self)

                if last_trace is not None and not last_trace.getMergeOrNameUsageCount():
                    if not last_trace.getUsageCount():
                        result = makeStatementReleaseVariable(
                            variable=variable, source_ref=self.source_ref
                        )

                        return trace_collection.computedStatementResult(
                            result,
                            "new_statements",
                            "Changed del to release for variable '%s' not used afterwards."
                            % variable.getName(),
                        )

        # If not tolerant, we may exception exit now during the __del__
        if not self.is_tolerant and not self.previous_trace.mustHaveValue():
            trace_collection.onExceptionRaiseExit(BaseException)

        # Record the deletion, needs to start a new version then.
        self.variable_trace = trace_collection.onVariableDel(
            variable=variable, version=self.variable_version, del_node=self
        )

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        return self, None, None

    def collectVariableAccesses(self, emit_read, emit_write):
        emit_write(self.variable)


class StatementDelVariableTolerant(StatementDelVariableBase):
    """Deleting a variable.

    All del forms that are not to attributes, slices, subscripts
    use this.

    The target can be any kind of variable, temporary, local, global, etc.

    Deleting a variable is something we trace in a new version, this is
    hidden behind target variable reference, which has this version once
    it can be determined.

    Tolerance means that the value might be unset. That can happen with
    re-formulation of ours, and Python3 exception variables.
    """

    kind = "STATEMENT_DEL_VARIABLE_TOLERANT"

    is_tolerant = True

    def getDetailsForDisplay(self):
        return {
            "variable_name": self.getVariableName(),
            "is_temp": self.variable.isTempVariable(),
            "var_type": self.variable.getVariableType(),
            "owner": self.variable.getOwner().getCodeName(),
        }

    def _computeDelWithoutValue(self, trace_collection):
        return (
            None,
            "new_statements",
            "Removed tolerant 'del' statement of '%s' without effect."
            % (self.getVariableName(),),
        )

    @staticmethod
    def mayRaiseException(exception_type):
        return False


class StatementDelVariableIntolerant(StatementDelVariableBase):
    """Deleting a variable.

    All del forms that are not to attributes, slices, subscripts
    use this.

    The target can be any kind of variable, temporary, local, global, etc.

    Deleting a variable is something we trace in a new version, this is
    hidden behind target variable reference, which has this version once
    it can be determined.

    Tolerance means that the value might be unset. That can happen with
    re-formulation of ours, and Python3 exception variables.
    """

    kind = "STATEMENT_DEL_VARIABLE_INTOLERANT"

    is_tolerant = False

    def _computeDelWithoutValue(self, trace_collection):
        if self.variable.isLocalVariable():
            result = makeRaiseExceptionReplacementStatement(
                statement=self,
                exception_type="UnboundLocalError",
                exception_value=getUnboundLocalErrorErrorTemplate()
                % self.variable.getName(),
            )
        else:
            result = makeRaiseExceptionReplacementStatement(
                statement=self,
                exception_type="NameError",
                exception_value="""name '%s' is not defined"""
                % self.variable.getName(),
            )

        return trace_collection.computedStatementResult(
            result,
            "new_raise",
            "Variable del of not initialized variable '%s'" % self.variable.getName(),
        )

    def mayRaiseException(self, exception_type):
        if self.variable_trace is not None:
            # Temporary variables deletions won't raise, just because we
            # don't create them that way. We can avoid going through SSA in
            # these cases.
            if self.variable.isTempVariable():
                return False

            # If SSA knows, that's fine.
            if self.previous_trace is not None and self.previous_trace.mustHaveValue():
                return False

        return True


def makeStatementDelVariable(variable, tolerant, source_ref, version=None):
    if tolerant:
        return StatementDelVariableTolerant(
            variable=variable, version=version, source_ref=source_ref
        )
    else:
        return StatementDelVariableIntolerant(
            variable=variable, version=version, source_ref=source_ref
        )
