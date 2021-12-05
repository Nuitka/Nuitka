#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
from nuitka.tree.Extractions import getVariablesWrittenOrRead

from .Checkers import checkStatementsSequenceOrNone
from .NodeBases import StatementBase, StatementChildHavingBase
from .shapes.StandardShapes import tshape_unknown, tshape_unknown_loop

tshape_unknown_set = frozenset([tshape_unknown])


def minimizeShapes(shapes):
    # Merge some shapes automatically, no need to give a set.
    if tshape_unknown in shapes:
        return tshape_unknown_set

    return shapes


class StatementLoop(StatementChildHavingBase):
    kind = "STATEMENT_LOOP"

    named_child = "loop_body"

    checker = checkStatementsSequenceOrNone

    __slots__ = (
        "loop_variables",
        "loop_start",
        "loop_resume",
        "loop_previous_resume",
        "incomplete_count",
    )

    def __init__(self, loop_body, source_ref):
        StatementChildHavingBase.__init__(self, value=loop_body, source_ref=source_ref)

        self.loop_variables = None

        # Traces of the variable at the start of loop, to detect changes and make
        # those restart optimization.
        self.loop_start = {}

        # Shapes currently known to be present when the loop is started or resumed
        # with continue statements.
        self.loop_resume = {}

        # Shapes from last time around, to detect the when it becomes complete, i.e.
        # we have seen it all.
        self.loop_previous_resume = {}

        # To allow an upper limit in case it doesn't terminate.
        self.incomplete_count = 0

    def mayReturn(self):
        loop_body = self.subnode_loop_body

        if loop_body is not None and loop_body.mayReturn():
            return True

        return False

    @staticmethod
    def mayBreak():
        # The loop itself may never break another loop.
        return False

    @staticmethod
    def mayContinue():
        # The loop itself may never continue another loop.
        return False

    def isStatementAborting(self):
        loop_body = self.subnode_loop_body

        if loop_body is None:
            return True
        else:
            return not loop_body.mayBreak()

    @staticmethod
    def mayRaiseException(exception_type):
        # Loops can only raise, if their body does, but they also issue the
        # async exceptions, so we must make them do it all the time.
        return True
        # loop_body = self.subnode_loop_body
        #  return loop_body is not None and \
        #         self.subnode_loop_body.mayRaiseException(exception_type)

    def _computeLoopBody(self, trace_collection):
        # Rather complex stuff, pylint: disable=too-many-branches,too-many-locals,too-many-statements
        # print("Enter loop body", self.source_ref)

        loop_body = self.subnode_loop_body
        if loop_body is None:
            return None, None, None

        # Look ahead. what will be written and degrade to initial loop traces
        # about that if we are in the first iteration, later we # will have more
        # precise knowledge.
        if self.loop_variables is None:
            self.loop_variables = getVariablesWrittenOrRead(loop_body)

            all_first_pass = True
        else:
            all_first_pass = False

        # Track if we got incomplete knowledge due to loop. If so, we are not done, even
        # if no was optimization done, once we are complete, they can come.
        incomplete_variables = None

        # Mark all variables as loop wrap around that are written in the loop and
        # hit a 'continue' and make them become loop merges. We will strive to
        # reduce self.loop_variables if we find ones that have no change in all
        # 'continue' exits.
        loop_entry_traces = set()
        for loop_variable in self.loop_variables:
            current = trace_collection.getVariableCurrentTrace(loop_variable)

            if all_first_pass:
                first_pass = True

                # Remember what we started with, so we can detect changes from outside the
                # loop and make them restart the collection process, if the pre-conditions
                # got better.
                self.loop_start[loop_variable] = current
            else:
                if not self.loop_start[loop_variable].compareValueTrace(current):
                    first_pass = True
                    self.loop_start[loop_variable] = current
                else:
                    first_pass = False

            if first_pass:
                incomplete = True

                self.loop_previous_resume[loop_variable] = None

                # Don't forget to initialize the loop resume traces with the starting point. We use
                # a special trace class that will not take the list too serious though.
                self.loop_resume[loop_variable] = set()
                current.getTypeShape().emitAlternatives(
                    self.loop_resume[loop_variable].add
                )
            else:
                if (
                    self.loop_resume[loop_variable]
                    != self.loop_previous_resume[loop_variable]
                ):
                    # print("incomplete", self.source_ref, loop_variable, ":",
                    # self.loop_previous_resume[loop_variable], "<->", self.loop_resume[loop_variable])

                    incomplete = True

                    if incomplete_variables is None:
                        incomplete_variables = set()

                    incomplete_variables.add(loop_variable)
                else:
                    # print("complete", self.source_ref, loop_variable, ":",
                    # self.loop_previous_resume[loop_variable], "<->", self.loop_resume[loop_variable])
                    incomplete = False

            # Mark the variable as loop usage before executing it.
            loop_entry_traces.add(
                (
                    loop_variable,
                    trace_collection.markActiveVariableAsLoopMerge(
                        loop_node=self,
                        current=current,
                        variable=loop_variable,
                        shapes=self.loop_resume[loop_variable],
                        incomplete=incomplete,
                    ),
                )
            )

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
                self.setChild("loop_body", result)
                loop_body = result

            if loop_body is not None:
                # Emulate terminal continue if not aborting.
                if not loop_body.isStatementAborting():
                    trace_collection.onLoopContinue()

            continue_collections = trace_collection.getLoopContinueCollections()

            # Rebuild this with only the ones that actually changed in the loop.
            self.loop_variables = []

            for loop_variable, loop_entry_trace in loop_entry_traces:

                # Giving up
                if self.incomplete_count >= 20:
                    self.loop_previous_resume[loop_variable] = self.loop_resume[
                        loop_variable
                    ] = set((tshape_unknown_loop,))
                    continue

                # Remember what it was at the start, to be able to tell if it changed.
                self.loop_previous_resume[loop_variable] = self.loop_resume[
                    loop_variable
                ]
                self.loop_resume[loop_variable] = set()

                loop_resume_traces = set(
                    continue_collection.getVariableCurrentTrace(loop_variable)
                    for continue_collection in continue_collections
                )

                # Only if the variable is re-entering the loop, annotate that.
                if not loop_resume_traces or (
                    len(loop_resume_traces) == 1
                    and loop_entry_trace.compareValueTrace(
                        next(iter(loop_resume_traces))
                    )
                ):
                    # Remove the variable, need not consider it
                    # ever again.
                    del self.loop_resume[loop_variable]
                    del self.loop_previous_resume[loop_variable]
                    del self.loop_start[loop_variable]

                    continue

                # Keep this as a loop variable
                self.loop_variables.append(loop_variable)

                # Tell the loop trace about the continue traces.
                loop_entry_trace.addLoopContinueTraces(loop_resume_traces)

                # Also consider the entry trace before loop from here on.
                loop_resume_traces.add(self.loop_start[loop_variable])

                shapes = set()

                for loop_resume_trace in loop_resume_traces:
                    loop_resume_trace.getTypeShape().emitAlternatives(shapes.add)

                self.loop_resume[loop_variable] = minimizeShapes(shapes)

            # If we break, the outer collections becomes a merge of all those breaks
            # or just the one, if there is only one.
            break_collections = trace_collection.getLoopBreakCollections()

        if incomplete_variables:
            self.incomplete_count += 1

            trace_collection.signalChange(
                "loop_analysis",
                self.source_ref,
                lambda: "Loop has incomplete variable types after %d attempts for '%s'."
                % (
                    self.incomplete_count,
                    ",".join(variable.getName() for variable in incomplete_variables),
                ),
            )
        else:
            if self.incomplete_count:
                trace_collection.signalChange(
                    "loop_analysis",
                    self.source_ref,
                    lambda: "Loop has complete variable types after %d attempts."
                    % self.incomplete_count,
                )

                self.incomplete_count = 0

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

            statements = loop_body.subnode_statements
            assert statements  # Cannot be empty

            # If the last statement is a "continue" statement, it can simply
            # be discarded.
            last_statement = statements[-1]
            if last_statement.isStatementLoopContinue():
                if len(statements) == 1:
                    self.subnode_body.finalize()

                    self.clearChild("loop_body")
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

            statements = loop_body.subnode_statements
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

    @staticmethod
    def getStatementNiceName():
        return "loop statement"


class StatementLoopContinue(StatementBase):
    kind = "STATEMENT_LOOP_CONTINUE"

    def __init__(self, source_ref):
        StatementBase.__init__(self, source_ref=source_ref)

    def finalize(self):
        del self.parent

    @staticmethod
    def isStatementAborting():
        return True

    @staticmethod
    def mayRaiseException(exception_type):
        return False

    @staticmethod
    def mayContinue():
        return True

    def computeStatement(self, trace_collection):
        # This statement being aborting, will already tell everything.
        trace_collection.onLoopContinue()

        return self, None, None

    @staticmethod
    def getStatementNiceName():
        return "loop continue statement"


class StatementLoopBreak(StatementBase):
    kind = "STATEMENT_LOOP_BREAK"

    def __init__(self, source_ref):
        StatementBase.__init__(self, source_ref=source_ref)

    def finalize(self):
        del self.parent

    @staticmethod
    def isStatementAborting():
        return True

    @staticmethod
    def mayRaiseException(exception_type):
        return False

    @staticmethod
    def mayBreak():
        return True

    def computeStatement(self, trace_collection):
        # This statement being aborting, will already tell everything.
        trace_collection.onLoopBreak()

        return self, None, None

    @staticmethod
    def getStatementNiceName():
        return "loop break statement"
