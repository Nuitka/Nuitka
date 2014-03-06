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
""" Loop nodes.

There are for and loop nodes, but both are reduced to loops with break/continue
statements for it. These reformulations require that optimization of loops has
to be very general, yet the node type for loop, becomes very simple.
"""

from .NodeBases import (
    StatementChildrenHavingBase,
    NodeBase
)
from nuitka.tree.Extractions import getVariablesWritten


class StatementLoop(StatementChildrenHavingBase):
    kind = "STATEMENT_LOOP"

    named_children = (
        "frame",
    )

    def __init__(self, body, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "frame" : body
            },
            source_ref = source_ref
        )

        self.break_exception = False
        self.continue_exception = False

    getLoopBody = StatementChildrenHavingBase.childGetter("frame")

    def markAsExceptionContinue(self):
        self.continue_exception = True

    def markAsExceptionBreak(self):
        self.break_exception = True

    def needsExceptionContinue(self):
        return self.continue_exception

    def needsExceptionBreak(self):
        return self.break_exception

    def computeStatement(self, constraint_collection):
        loop_body = self.getLoopBody()

        if loop_body is not None:
            # Look ahead. what will be written.
            variable_writes = getVariablesWritten( loop_body )

            # Mark all variables as unknown that are written in the loop body,
            # so it destroys the assumptions for loop turn around.
            for variable, _variable_version in variable_writes:
                constraint_collection.markActiveVariableAsUnknown(
                    variable = variable
                )

            result = loop_body.computeStatementsSequence(
                constraint_collection = constraint_collection
            )

            # Might be changed.
            if result is not loop_body:
                loop_body.replaceWith( result )
                loop_body = result

        # Consider trailing "continue" statements, these have no effect, so we
        # can remove them.
        if loop_body is not None:
            assert loop_body.isStatementsSequence()

            statements = loop_body.getStatements()
            assert statements # Cannot be empty

            last_statement = statements[-1]
            if last_statement.isStatementContinueLoop():
                loop_body.removeStatement( last_statement )
                statements = loop_body.getStatements()

                if not statements:
                    loop_body.replaceWith( None )
                    loop_body = None

                constraint_collection.signalChange(
                    "new_statements",
                    last_statement.getSourceReference(),
                    "Removed continue as last statement of loop."
                )

        # Consider leading "break" statements, they should be the only, and
        # should lead to removing the whole loop statement. Trailing "break"
        # statements could also be handled, but that would need to consider if
        # there are other "break" statements too. Numbering loop exits is
        # nothing we have yet.
        if loop_body is not None:
            assert loop_body.isStatementsSequence()

            statements = loop_body.getStatements()
            assert statements # Cannot be empty

            if len( statements ) == 1 and statements[-1].isStatementBreakLoop():
                return None, "new_statements", """\
Removed loop immediately broken."""

        return self, None, None

    def needsLineNumber(self):
        # The loop itself cannot fail, the first statement will set the line
        # number if necessary.
        return False


class StatementContinueLoop(NodeBase):
    kind = "STATEMENT_CONTINUE_LOOP"

    def __init__(self, source_ref):
        NodeBase.__init__( self, source_ref = source_ref )

        self.exception_driven = False

    def isStatementAborting(self):
        return True

    def markAsExceptionDriven(self):
        self.exception_driven = True

    def isExceptionDriven(self):
        return self.exception_driven

    def computeStatement(self, constraint_collection):
        # This statement being aborting, will already tell everything. TODO: The
        # fine difference that this jumps to loop start for sure, should be
        # represented somehow one day.
        return self, None, None


class StatementBreakLoop(NodeBase):
    kind = "STATEMENT_BREAK_LOOP"

    def __init__(self, source_ref):
        NodeBase.__init__( self, source_ref = source_ref )

        self.exception_driven = False

    def isStatementAborting(self):
        return True

    def markAsExceptionDriven(self):
        self.exception_driven = True

    def isExceptionDriven(self):
        return self.exception_driven

    def computeStatement(self, constraint_collection):
        # This statement being aborting, will already tell everything. TODO: The
        # fine difference that this exits the loop for sure, should be
        # represented somehow one day.
        return self, None, None
