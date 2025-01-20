#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Nodes for variable release

These refer to resolved variable objects.

"""

from nuitka.ModuleRegistry import getOwnerFromCodeName

from .NodeBases import StatementBase


class StatementReleaseVariableBase(StatementBase):
    """Releasing a variable.

    Just release the value, which of course is not to be used afterwards.

    Typical code: Function exit user variables, try/finally release of temporary
    variables.
    """

    __slots__ = "variable", "variable_trace"

    def __init__(self, variable, source_ref):
        StatementBase.__init__(self, source_ref=source_ref)

        self.variable = variable
        self.variable_trace = None

    @staticmethod
    def isStatementReleaseVariable():
        return True

    def finalize(self):
        del self.variable
        del self.variable_trace
        del self.parent

    def getDetails(self):
        return {"variable": self.variable}

    def getDetailsForDisplay(self):
        return {
            "variable_name": self.variable.getName(),
            "owner": self.variable.getOwner().getCodeName(),
        }

    @classmethod
    def fromXML(cls, provider, source_ref, **args):
        assert cls is makeStatementReleaseVariable, cls

        owner = getOwnerFromCodeName(args["owner"])
        assert owner is not None, args["owner"]

        variable = owner.getProvidedVariable(args["variable_name"])

        return cls(variable=variable, source_ref=source_ref)

    def getVariable(self):
        return self.variable

    def getVariableTrace(self):
        return self.variable_trace

    def setVariable(self, variable):
        self.variable = variable

    def computeStatement(self, trace_collection):
        self.variable_trace = trace_collection.getVariableCurrentTrace(self.variable)

        if self.variable_trace.mustNotHaveValue():
            return (
                None,
                "new_statements",
                "Uninitialized %s is not released." % (self.variable.getDescription()),
            )

        escape_desc = self.variable_trace.getReleaseEscape()

        assert escape_desc is not None, self.variable_trace

        if escape_desc.isControlFlowEscape():
            # Any code could be run, note that.
            trace_collection.onControlFlowEscape(self)

        # TODO: We might be able to remove ourselves based on the trace
        # we belong to.

        return self, None, None

    @staticmethod
    def mayRaiseException(exception_type):
        # By default, __del__ is not allowed to raise an exception.
        return False


class StatementReleaseVariableTemp(StatementReleaseVariableBase):
    kind = "STATEMENT_RELEASE_VARIABLE_TEMP"


class StatementReleaseVariableLocal(StatementReleaseVariableBase):
    kind = "STATEMENT_RELEASE_VARIABLE_LOCAL"


class StatementReleaseVariableParameter(StatementReleaseVariableLocal):
    kind = "STATEMENT_RELEASE_VARIABLE_PARAMETER"

    def computeStatement(self, trace_collection):
        if self.variable.getOwner().isAutoReleaseVariable(self.variable):
            return (
                None,
                "new_statements",
                "Original parameter variable value of '%s' is not released."
                % self.variable.getName(),
            )

        return StatementReleaseVariableLocal.computeStatement(self, trace_collection)


def makeStatementReleaseVariable(variable, source_ref):
    if variable.isTempVariable():
        return StatementReleaseVariableTemp(variable=variable, source_ref=source_ref)
    elif variable.isParameterVariable():
        return StatementReleaseVariableParameter(
            variable=variable, source_ref=source_ref
        )
    else:
        return StatementReleaseVariableLocal(variable=variable, source_ref=source_ref)


def makeStatementsReleaseVariables(variables, source_ref):
    return tuple(
        makeStatementReleaseVariable(variable=variable, source_ref=source_ref)
        for variable in variables
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
