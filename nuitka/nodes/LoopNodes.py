#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.optimizations.TraceCollections import ConstraintCollectionBranch
from nuitka.tree.Extractions import getVariablesWritten

from .Checkers import checkStatementsSequenceOrNone
from .NodeBases import NodeBase, StatementChildrenHavingBase


class StatementLoop(StatementChildrenHavingBase):
    kind = "STATEMENT_LOOP"

    named_children = (
        "body",
    )

    checkers = {
        "body" : checkStatementsSequenceOrNone
    }

    def __init__(self, body, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "body" : body
            },
            source_ref = source_ref
        )

        self.loop_variables = None

    getLoopBody = StatementChildrenHavingBase.childGetter("body")
    setLoopBody = StatementChildrenHavingBase.childSetter("body")

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

        if loop_body is None:
            return True
        else:
            return not loop_body.mayBreak()

    def mayRaiseException(self, exception_type):
        # Loops can only raise, if their body does, but they also issue the
        # async exceptions, so we must make them do it all the time.
        return True
        # loop_body = self.getLoopBody()
        #  return loop_body is not None and \
        #         self.getLoopBody().mayRaiseException(exception_type)

    def computeLoopBody(self, constraint_collection):
        abort_context = constraint_collection.makeAbortStackContext(
            catch_breaks     = True,
            catch_continues  = True,
            catch_returns    = False,
            catch_exceptions = False,
        )

        with abort_context:
            loop_body = self.getLoopBody()

            if loop_body is not None:
                # Look ahead. what will be written and degrade about that if we
                # are in the first iteration, later we will have more precise
                # knowledge.
                if self.loop_variables is None:
                    self.loop_variables = getVariablesWritten(
                        loop_body
                    )

                loop_entry_traces = set()

                # Mark all variables as loop wrap around that are written in
                # the loop and hit a 'continue'.
                for variable in self.loop_variables:
                    loop_entry_traces.add(
                        constraint_collection.markActiveVariableAsLoopMerge(
                            variable = variable
                        )
                    )


                result = loop_body.computeStatementsSequence(
                    constraint_collection = constraint_collection
                )

                # Might be changed.
                if result is not loop_body:
                    self.setLoopBody(result)
                    loop_body = result

                if loop_body is not None:
                    # Emulate terminal continue if not aborting.
                    if not loop_body.isStatementAborting():
                        constraint_collection.onLoopContinue()

                continue_collections = constraint_collection.getLoopContinueCollections()

                self.loop_variables = set()

                for loop_entry_trace in loop_entry_traces:
                    variable = loop_entry_trace.getVariable()

                    loop_end_traces = set()

                    for continue_collection in continue_collections:
                        loop_end_trace = continue_collection.getVariableCurrentTrace(variable)

                        if loop_end_trace is not loop_entry_trace:
                            loop_end_traces.add(loop_end_trace)

                    if loop_end_traces:
                        loop_entry_trace.addLoopContinueTraces(loop_end_traces)
                        self.loop_variables.add(variable)

            # If we break, the outer collections becomes a merge of all those breaks
            # or just the one, if there is only one.
            break_collections = constraint_collection.getLoopBreakCollections()

        return loop_body, break_collections

    def computeStatement(self, constraint_collection):
        outer_constraint_collection = constraint_collection
        constraint_collection = ConstraintCollectionBranch(
            parent = constraint_collection,
            name   = "loop"
        )

        loop_body, break_collections = self.computeLoopBody(constraint_collection)

        # Consider trailing "continue" statements, these have no effect, so we
        # can remove them.
        if loop_body is not None:
            assert loop_body.isStatementsSequence()

            statements = loop_body.getStatements()
            assert statements # Cannot be empty

            # If the last statement is a "continue" statement, it can simply
            # be discarded.
            last_statement = statements[-1]
            if last_statement.isStatementLoopContinue():
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

        if break_collections:
            outer_constraint_collection.mergeMultipleBranches(break_collections)

        # Consider leading "break" statements, they should be the only, and
        # should lead to removing the whole loop statement. Trailing "break"
        # statements could also be handled, but that would need to consider if
        # there are other "break" statements too. Numbering loop exits is
        # nothing we have yet.
        if loop_body is not None:
            assert loop_body.isStatementsSequence()

            statements = loop_body.getStatements()
            assert statements # Cannot be empty

            if len(statements) == 1 and statements[-1].isStatementLoopBreak():
                return None, "new_statements", """\
Removed useless loop with immediate 'break' statement."""

        # Also consider the threading intermission. TODO: We ought to make it
        # explicit, so we can see it potentially disrupting and changing the
        # global variables. It may also raise.
        outer_constraint_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class StatementLoopContinue(NodeBase):
    kind = "STATEMENT_LOOP_CONTINUE"

    def __init__(self, source_ref):
        NodeBase.__init__(self, source_ref = source_ref)

    def isStatementAborting(self):
        return True

    def mayRaiseException(self, exception_type):
        return False

    def mayContinue(self):
        return True

    def computeStatement(self, constraint_collection):
        # This statement being aborting, will already tell everything.
        constraint_collection.onLoopContinue()

        return self, None, None


class StatementLoopBreak(NodeBase):
    kind = "STATEMENT_LOOP_BREAK"

    def __init__(self, source_ref):
        NodeBase.__init__(self, source_ref = source_ref)

    def isStatementAborting(self):
        return True

    def mayRaiseException(self, exception_type):
        return False

    def mayBreak(self):
        return True

    def computeStatement(self, constraint_collection):
        # This statement being aborting, will already tell everything.
        constraint_collection.onLoopBreak()

        return self, None, None
