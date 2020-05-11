#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.optimizations.TraceCollections import TraceCollectionBranch
from nuitka.tree.Extractions import getVariablesWritten

from .Checkers import checkStatementsSequenceOrNone
from .NodeBases import StatementBase, StatementChildHavingBase


class StatementLoop(StatementChildHavingBase):
    kind = "STATEMENT_LOOP"

    named_child = "body"
    getLoopBody = StatementChildHavingBase.childGetter("body")
    setLoopBody = StatementChildHavingBase.childSetter("body")

    checker = checkStatementsSequenceOrNone

    __slots__ = ("loop_variables", "loop_start", "loop_end", "loop_previous_end")

    def __init__(self, body, source_ref):
        StatementChildHavingBase.__init__(self, value=body, source_ref=source_ref)

        self.loop_variables = None

        # Shapes of the variable at the start.
        self.loop_start = {}
        self.loop_end = {}
        self.loop_previous_end = {}

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

    def _computeLoopBody(self, trace_collection):
        # Rather complex stuff, pylint: disable=too-many-branches,too-many-locals

        loop_body = self.getLoopBody()
        if loop_body is None:
            return None, None, None

        # Track if we got incomplete knowledge due to loop. If so, we are not done, even
        # if no was optimization done, once we are complete, they can come.
        has_incomplete = False

        # Look ahead. what will be written and degrade to initial loop
        # traces about that if we are in the first iteration, later we
        # will have more precise knowledge.

        if self.loop_variables is None:
            self.loop_variables = getVariablesWritten(loop_body)

            # Only important to mark these states as different, so we start with
            # initial loop traces.
            for loop_variable in self.loop_variables:
                self.loop_start[loop_variable] = None

                self.loop_previous_end[loop_variable] = None
                self.loop_end[loop_variable] = set()

            first_pass = True
        else:
            first_pass = False

        # Mark all variables as loop wrap around that are written in the loop and
        # hit a 'continue' and make them become loop merges. We will strive to
        # reduce self.loop_variables if we find ones that have no change in all
        # 'continue' exits.
        loop_entry_traces = set()
        for loop_variable in self.loop_variables:
            current = trace_collection.getVariableCurrentTrace(loop_variable)

            if first_pass:
                incomplete = True
                has_incomplete = True
            else:
                incomplete = (
                    self.loop_start[loop_variable].getLoopTypeShapes()
                    != current.getLoopTypeShapes()
                    or self.loop_end[loop_variable]
                    != self.loop_previous_end[loop_variable]
                )

                if incomplete:
                    has_incomplete = True

            # TODO: We should be able to avoid these, but it breaks assumptions for assertions
            # of asssigned and deleted values in the loop.
            # if (
            #     incomplete
            #     and not current.isUninitTrace()
            #     or self.loop_end[loop_variable]
            # ):
            loop_entry_traces.add(
                (
                    loop_variable,
                    trace_collection.markActiveVariableAsLoopMerge(
                        variable=loop_variable,
                        shapes=self.loop_end[loop_variable],
                        incomplete=incomplete,
                        first_pass=first_pass,
                    ),
                )
            )

            # Remember what we started with, so we can detect changes from outside the
            # loop and make them restart the collection process.
            self.loop_start[loop_variable] = current

        abort_context = trace_collection.makeAbortStackContext(
            catch_breaks=True,
            catch_continues=True,
            catch_returns=False,
            catch_exceptions=False,
        )

        with abort_context:
            # Forget all iterator and other value status. TODO: These should be using
            # more proper tracing to benefit.
            trace_collection.resetValueStates()

            result = loop_body.computeStatementsSequence(
                trace_collection=trace_collection
            )

            # Might be changed.
            if result is not loop_body:
                self.setLoopBody(result)
                loop_body = result

            if loop_body is not None:
                # Emulate terminal continue if not aborting.
                if not loop_body.isStatementAborting():
                    trace_collection.onLoopContinue()

            continue_collections = trace_collection.getLoopContinueCollections()

            # Rebuild this with only the ones that actually changed in the loop.
            self.loop_variables = set()

            for loop_variable, loop_entry_trace in loop_entry_traces:
                loop_end_traces = set()

                if not first_pass:
                    self.loop_previous_end[loop_variable] = self.loop_end[loop_variable]
                    self.loop_end[loop_variable] = set()

                for continue_collection in continue_collections:
                    loop_end_trace = continue_collection.getVariableCurrentTrace(
                        loop_variable
                    )

                    if loop_end_trace is not loop_entry_trace:
                        if not first_pass:
                            loop_end_trace.getTypeShape().emitAlternatives(
                                self.loop_end[loop_variable].add
                            )

                        loop_end_traces.add(loop_end_trace)

                if loop_end_traces:
                    loop_entry_trace.addLoopContinueTraces(loop_end_traces)
                    self.loop_variables.add(loop_variable)

            # If we break, the outer collections becomes a merge of all those breaks
            # or just the one, if there is only one.
            break_collections = trace_collection.getLoopBreakCollections()

        if has_incomplete:
            trace_collection.signalChange(
                "new_expression", self.source_ref, "Loop has incomplete variable types."
            )

        return loop_body, break_collections, continue_collections

    def computeStatement(self, trace_collection):
        outer_trace_collection = trace_collection
        trace_collection = TraceCollectionBranch(parent=trace_collection, name="loop")

        loop_body, break_collections, continue_collections = self._computeLoopBody(
            trace_collection
        )

        if break_collections:
            outer_trace_collection.mergeMultipleBranches(break_collections)

        # Consider trailing "continue" statements, these have no effect, so we
        # can remove them.
        if loop_body is not None:
            assert loop_body.isStatementsSequence()

            statements = loop_body.getStatements()
            assert statements  # Cannot be empty

            # If the last statement is a "continue" statement, it can simply
            # be discarded.
            last_statement = statements[-1]
            if last_statement.isStatementLoopContinue():
                if len(statements) == 1:
                    self.subnode_body.finalize()

                    self.setLoopBody(None)
                    loop_body = None
                else:
                    last_statement.parent.replaceChild(last_statement, None)
                    last_statement.finalize()

                trace_collection.signalChange(
                    "new_statements",
                    last_statement.getSourceReference(),
                    """\
Removed useless terminal 'continue' as last statement of loop.""",
                )
            elif last_statement.isStatementLoopBreak():
                if not continue_collections and len(break_collections) == 1:
                    loop_body = loop_body.removeStatement(last_statement)

                    return (
                        loop_body,
                        "new_statements",
                        "Removed useless loop with only a break at the end.",
                    )

        # Consider leading "break" statements, they should be the only, and
        # should lead to removing the whole loop statement. Trailing "break"
        # statements could also be handled, but that would need to consider if
        # there are other "break" statements too. Numbering loop exits is
        # nothing we have yet.
        if loop_body is not None:
            assert loop_body.isStatementsSequence()

            statements = loop_body.getStatements()
            assert statements  # Cannot be empty

            if len(statements) == 1 and statements[-1].isStatementLoopBreak():
                # TODO: Should be dead code now, due to the optimization above.
                assert False

                return (
                    None,
                    "new_statements",
                    """\
Removed useless loop with immediate 'break' statement.""",
                )

        # Also consider the threading intermission. TODO: We ought to make it
        # explicit, so we can see it potentially disrupting and changing the
        # global variables. It may also raise.
        outer_trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def getStatementNiceName(self):
        return "loop statement"


class StatementLoopContinue(StatementBase):
    kind = "STATEMENT_LOOP_CONTINUE"

    def __init__(self, source_ref):
        StatementBase.__init__(self, source_ref=source_ref)

    def finalize(self):
        del self.parent

    def isStatementAborting(self):
        return True

    def mayRaiseException(self, exception_type):
        return False

    def mayContinue(self):
        return True

    def computeStatement(self, trace_collection):
        # This statement being aborting, will already tell everything.
        trace_collection.onLoopContinue()

        return self, None, None

    def getStatementNiceName(self):
        return "loop continue statement"


class StatementLoopBreak(StatementBase):
    kind = "STATEMENT_LOOP_BREAK"

    def __init__(self, source_ref):
        StatementBase.__init__(self, source_ref=source_ref)

    def finalize(self):
        del self.parent

    def isStatementAborting(self):
        return True

    def mayRaiseException(self, exception_type):
        return False

    def mayBreak(self):
        return True

    def computeStatement(self, trace_collection):
        # This statement being aborting, will already tell everything.
        trace_collection.onLoopBreak()

        return self, None, None

    def getStatementNiceName(self):
        return "loop break statement"
