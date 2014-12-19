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
statements for it. These re-formulations require that optimization of loops has
to be very general, yet the node type for loop, becomes very simple.
"""

from nuitka.tree.Extractions import getVariablesWritten

from .NodeBases import NodeBase, StatementChildrenHavingBase


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

        # For code generation, so it knows if an exit target is needed.
        self.has_break = False

    getLoopBody = StatementChildrenHavingBase.childGetter("frame")
    setLoopBody = StatementChildrenHavingBase.childSetter("frame")

    def mayReturn(self):
        loop_body = self.getLoopBody()

        if loop_body is not None and loop_body.mayReturn():
            return True

        return False

    def mayBreak(self):
        # The loop itself may never break another loop.
        return False

    def mayContinue(self):
        # The loop itself may never continue another loop.
        return False

    def isStatementAborting(self):
        loop_body = self.getLoopBody()

        if loop_body is not None:
            return not loop_body.mayBreak()
        else:
            return True

    def computeStatement(self, constraint_collection):
        loop_body = self.getLoopBody()

        if loop_body is not None:
            # Look ahead. what will be written.
            variable_writes = getVariablesWritten(loop_body)

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
                self.setLoopBody(result)
                loop_body = result

        # Consider trailing "continue" statements, these have no effect, so we
        # can remove them.
        if loop_body is not None:
            assert loop_body.isStatementsSequence()

            statements = loop_body.getStatements()
            assert statements # Cannot be empty

            # If the last statement is a "continue" statement, it can simply
            # be discarded.
            last_statement = statements[-1]
            if last_statement.isStatementContinueLoop():
                if len(statements) == 1:
                    self.setLoopBody(None)
                    loop_body = None
                else:
                    last_statement.replaceWith(None)

                constraint_collection.signalChange(
                    "new_statements",
                    last_statement.getSourceReference(),
                    """\
Removed useless terminal 'continue' as last statement of loop."""
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

            if len(statements) == 1 and statements[-1].isStatementBreakLoop():
                return None, "new_statements", """\
Removed useless loop with immediate 'break' statement."""

        return self, None, None


class StatementContinueLoop(NodeBase):
    kind = "STATEMENT_CONTINUE_LOOP"

    def __init__(self, source_ref):
        NodeBase.__init__(self, source_ref = source_ref)

    def isStatementAborting(self):
        return True

    def computeStatement(self, constraint_collection):
        # This statement being aborting, will already tell everything. TODO: The
        # fine difference that this jumps to loop start for sure, should be
        # represented somehow one day.
        return self, None, None

    def mayRaiseException(self, exception_type):
        return False

    def mayContinue(self):
        return True


class StatementBreakLoop(NodeBase):
    kind = "STATEMENT_BREAK_LOOP"

    def __init__(self, source_ref):
        NodeBase.__init__(self, source_ref = source_ref)

    def isStatementAborting(self):
        return True

    def mayRaiseException(self, exception_type):
        return False

    def mayBreak(self):
        return True

    def computeStatement(self, constraint_collection):
        # This statement being aborting, will already tell everything. TODO: The
        # fine difference that this exits the loop for sure, should be
        # represented somehow one day.
        return self, None, None
