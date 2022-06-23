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
""" Nodes for named variable reference, assignment, and deletion

x = ...
del x
... = x

Variable name references might be in a class context, and then it
is unclear what this really will become. These nodes are used in
the early tree building phase, but never reach optimization phase
or even code generation.
"""

from .ExpressionBases import ExpressionBase
from .NodeBases import StatementBase, StatementChildHavingBase


class StatementAssignmentVariableName(StatementChildHavingBase):
    """Precursor of StatementAssignmentVariable used during tree building phase"""

    kind = "STATEMENT_ASSIGNMENT_VARIABLE_NAME"

    named_child = "source"
    nice_child = "assignment source"

    __slots__ = ("variable_name", "provider")

    def __init__(self, provider, variable_name, source, source_ref):
        assert source is not None, source_ref

        StatementChildHavingBase.__init__(self, value=source, source_ref=source_ref)

        self.variable_name = variable_name
        self.provider = provider

        assert not provider.isExpressionOutlineBody(), source_ref

    def getDetails(self):
        return {"variable_name": self.variable_name, "provider": self.provider}

    def getVariableName(self):
        return self.variable_name

    def computeStatement(self, trace_collection):
        # Only for abc, pylint: disable=no-self-use

        # These must not enter real optimization, they only live during the
        # tree building.
        assert False

    @staticmethod
    def getStatementNiceName():
        return "variable assignment statement"


class StatementDelVariableName(StatementBase):
    """Precursor of StatementDelVariable used during tree building phase"""

    kind = "STATEMENT_DEL_VARIABLE_NAME"

    __slots__ = "variable_name", "provider", "tolerant"

    def __init__(self, provider, variable_name, tolerant, source_ref):
        StatementBase.__init__(self, source_ref=source_ref)

        self.variable_name = variable_name
        self.provider = provider

        self.tolerant = tolerant

    def finalize(self):
        del self.parent
        del self.provider

    def getDetails(self):
        return {
            "variable_name": self.variable_name,
            "provider": self.provider,
            "tolerant": self.tolerant,
        }

    def getVariableName(self):
        return self.variable_name

    def computeStatement(self, trace_collection):
        # Only for abc, pylint: disable=no-self-use

        # These must not enter real optimization, they only live during the
        # tree building.
        assert False


class ExpressionVariableNameRef(ExpressionBase):
    """These are used before the actual variable object is known from VariableClosure."""

    kind = "EXPRESSION_VARIABLE_NAME_REF"

    __slots__ = "variable_name", "provider"

    def __init__(self, provider, variable_name, source_ref):
        assert not provider.isExpressionOutlineBody(), source_ref

        ExpressionBase.__init__(self, source_ref=source_ref)

        self.variable_name = variable_name

        self.provider = provider

    def finalize(self):
        del self.parent
        del self.provider

    @staticmethod
    def isExpressionVariableNameRef():
        return True

    def getDetails(self):
        return {"variable_name": self.variable_name, "provider": self.provider}

    def getVariableName(self):
        return self.variable_name

    def computeExpressionRaw(self, trace_collection):
        return self, None, None

    @staticmethod
    def needsFallback():
        return True


class ExpressionVariableLocalNameRef(ExpressionVariableNameRef):
    """These are used before the actual variable object is known from VariableClosure.

    The special thing about this as opposed to ExpressionVariableNameRef is that
    these must remain local names and cannot fallback to outside scopes. This is
    used for "__annotations__".

    """

    kind = "EXPRESSION_VARIABLE_LOCAL_NAME_REF"

    @staticmethod
    def needsFallback():
        return False
