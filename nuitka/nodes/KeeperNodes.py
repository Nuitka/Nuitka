#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Keeper nodes.

We need keeper nodes for comparison chains to hold the previous value during the
evaluation of an expression. They are otherwise not used and should be avoided,
all other constructs use real temporary variables.

"""

from .NodeBases import (
    ExpressionChildrenHavingBase,
    ExpressionMixin,
    NodeBase
)


class ExpressionAssignmentTempKeeper(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_ASSIGNMENT_TEMP_KEEPER"

    named_children = ( "source", )

    def __init__(self, variable, source, source_ref):
        assert source is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "source" : source,
            },
            source_ref = source_ref
        )

        self.variable = variable
        self.variable_version = variable.allocateTargetNumber()

        assert self.variable_version != 0

    def getDetail(self):
        return "%s from %s" % (
            self.getVariableName(),
            self.getAssignSource()
        )

    def getDetails(self):
        return {
            "name" : self.getVariableName()
        }

    def getVariable(self):
        return self.variable

    def getVariableName(self):
        return self.variable.getName()

    def getVariableVersion(self):
        return self.variable_version

    getAssignSource = ExpressionChildrenHavingBase.childGetter(
        "source"
    )

    def computeExpression(self, constraint_collection):
        source = self.getAssignSource()

        if source.willRaiseException(BaseException):
            return source, "new_raise", "Temp keeper assignment source raises."

        constraint_collection.onVariableSet(
            assign_node = self
        )

        return self, None, None

    def mayRaiseException(self, exception_type):
        return self.getAssignSource().mayRaiseException(
            exception_type = exception_type
        )

    def willRaiseException(self, exception_type):
        return self.getAssignSource().willRaiseException(
            exception_type = exception_type
        )

    def getTruthValue(self):
        return self.getAssignSource().getTruthValue()


class ExpressionTempKeeperRef(NodeBase, ExpressionMixin):
    kind = "EXPRESSION_TEMP_KEEPER_REF"

    def __init__(self, variable, source_ref):
        NodeBase.__init__( self, source_ref = source_ref )

        self.variable = variable

    def getDetails(self):
        return {
            "name" : self.getVariableName()
        }

    def getDetail(self):
        return self.getVariableName()

    def getVariable(self):
        return self.variable

    def getVariableName(self):
        return self.variable.getName()

    def computeExpression(self, constraint_collection):
        variable_trace = constraint_collection.getVariableCurrentTrace(
            variable = self.variable
        )

        if variable_trace.isAssignTrace():
            assign_source = variable_trace.getAssignNode().getAssignSource()

            if not assign_source.mayHaveSideEffects():
                return (
                    assign_source.makeCloneAt( self.getSourceReference() ),
                    "new_expression", """\
Replaced keeper variable usage for no side effects value."""
                )

        return self, None, None

    def mayRaiseException(self, exception_type):
        # Can't happen
        return False

    def mayHaveSideEffects(self):
        return False

    def isOrderRelevant(self):
        return True

    def mayProvideReference(self):
        return self.variable.getReferenced().getNeedsFree()
