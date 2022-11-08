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
""" Nodes for try/except/finally handling.

This is the unified low level solution to trying a block, and executing code
when it returns, break, continues, or raises an exception. See Developer
Manual for how this maps to try/finally and try/except as in Python.
"""

from nuitka.Errors import NuitkaOptimizationError
from nuitka.optimizations.TraceCollections import TraceCollectionBranch

from .Checkers import checkStatementsSequence, checkStatementsSequenceOrNone
from .NodeBases import StatementChildrenHavingBase
from .StatementNodes import StatementsSequence


class StatementTry(StatementChildrenHavingBase):
    kind = "STATEMENT_TRY"

    named_children = (
        "tried",
        "except_handler",
        "break_handler",
        "continue_handler",
        "return_handler",
    )

    checkers = {
        "tried": checkStatementsSequence,
        "except_handler": checkStatementsSequenceOrNone,
        "break_handler": checkStatementsSequenceOrNone,
        "continue_handler": checkStatementsSequenceOrNone,
        "return_handler": checkStatementsSequenceOrNone,
    }

    __slots__ = ("tried_may_raise",)

    def __init__(
        self,
        tried,
        except_handler,
        break_handler,
        continue_handler,
        return_handler,
        source_ref,
    ):
        StatementChildrenHavingBase.__init__(
            self,
            values={
                "tried": tried,
                "except_handler": except_handler,
                "break_handler": break_handler,
                "continue_handler": continue_handler,
                "return_handler": return_handler,
            },
            source_ref=source_ref,
        )

        self.tried_may_raise = None

    def getDetailsForDisplay(self):
        return {"aborting": self.isStatementAborting()}

    def computeStatement(self, trace_collection):
        # This node has many children to handle, pylint: disable=I0021,too-many-branches,too-many-locals,too-many-statements
        tried = self.subnode_tried

        except_handler = self.subnode_except_handler
        break_handler = self.subnode_break_handler
        continue_handler = self.subnode_continue_handler
        return_handler = self.subnode_return_handler

        # The tried block must be considered as a branch, if it is not empty
        # already.
        collection_start = TraceCollectionBranch(
            parent=trace_collection, name="try start"
        )

        abort_context = trace_collection.makeAbortStackContext(
            catch_breaks=break_handler is not None,
            catch_continues=continue_handler is not None,
            catch_returns=return_handler is not None,
            catch_exceptions=True,
        )

        with abort_context:
            # As a branch point for the many types of handlers.

            result = tried.computeStatementsSequence(trace_collection=trace_collection)

            # We might be done entirely already.
            if result is None:
                return None, "new_statements", "Removed now empty try statement."

            # Might be changed.
            if result is not tried:
                self.setChild("tried", result)
                tried = result

            break_collections = trace_collection.getLoopBreakCollections()
            continue_collections = trace_collection.getLoopContinueCollections()
            return_collections = trace_collection.getFunctionReturnCollections()
            exception_collections = trace_collection.getExceptionRaiseCollections()

        # Not raising never turns into raising, but None (never calculated) and True
        # may no longer be true, but not raising never becomes raising.
        if self.tried_may_raise is not False:
            self.tried_may_raise = tried.mayRaiseException(BaseException)

        # Exception handling is useless if no exception is to be raised.
        if not self.tried_may_raise:
            if except_handler is not None:
                except_handler.finalize()

                self.clearChild("except_handler")
                trace_collection.signalChange(
                    tags="new_statements",
                    message="Removed useless exception handler.",
                    source_ref=except_handler.source_ref,
                )

                except_handler = None

        # If tried may raise, even empty exception handler has a meaning to
        # ignore that exception.
        if self.tried_may_raise:
            collection_exception_handling = TraceCollectionBranch(
                parent=collection_start, name="except handler"
            )

            # When no exception exits are there, this is a problem, we just
            # found an inconsistency that is a bug.
            if not exception_collections:
                for statement in tried.subnode_statements:
                    if statement.mayRaiseException(BaseException):
                        raise NuitkaOptimizationError(
                            "This statement does raise but didn't annotate an exception exit.",
                            statement,
                        )

                raise NuitkaOptimizationError(
                    "Falsely assuming tried block may raise, but no statement says so.",
                    tried,
                )

            collection_exception_handling.mergeMultipleBranches(exception_collections)

            if except_handler is not None:
                result = except_handler.computeStatementsSequence(
                    trace_collection=collection_exception_handling
                )

                # Might be changed.
                if result is not except_handler:
                    self.setChild("except_handler", result)
                    except_handler = result

        if break_handler is not None:
            if not tried.mayBreak():
                break_handler.finalize()

                self.clearChild("break_handler")
                break_handler = None

        if break_handler is not None:
            collection_break = TraceCollectionBranch(
                parent=collection_start, name="break handler"
            )

            collection_break.mergeMultipleBranches(break_collections)

            result = break_handler.computeStatementsSequence(
                trace_collection=collection_break
            )

            # Might be changed.
            if result is not break_handler:
                self.setChild("break_handler", result)
                break_handler = result

        if continue_handler is not None:
            if not tried.mayContinue():
                continue_handler.finalize()

                self.clearChild("continue_handler")
                continue_handler = None

        if continue_handler is not None:
            collection_continue = TraceCollectionBranch(
                parent=collection_start, name="continue handler"
            )

            collection_continue.mergeMultipleBranches(continue_collections)

            result = continue_handler.computeStatementsSequence(
                trace_collection=collection_continue
            )

            # Might be changed.
            if result is not continue_handler:
                self.setChild("continue_handler", result)
                continue_handler = result

        if return_handler is not None:
            if not tried.mayReturn():
                return_handler.finalize()

                self.clearChild("return_handler")
                return_handler = None

        if return_handler is not None:
            collection_return = TraceCollectionBranch(
                parent=collection_start, name="return handler"
            )

            collection_return.mergeMultipleBranches(return_collections)

            result = return_handler.computeStatementsSequence(
                trace_collection=collection_return
            )

            # Might be changed.
            if result is not return_handler:
                self.setChild("return_handler", result)
                return_handler = result

        # Check for trivial return handlers that immediately return, they can
        # just be removed.
        if return_handler is not None:
            if return_handler.subnode_statements[0].isStatementReturnReturnedValue():
                return_handler.finalize()

                self.clearChild("return_handler")
                return_handler = None

        # Merge exception handler only if it is used. Empty means it is not
        # aborting, as it swallows the exception.
        if self.tried_may_raise and (
            except_handler is None or not except_handler.isStatementAborting()
        ):
            if tried.isStatementAborting():
                trace_collection.variable_actives = (
                    collection_exception_handling.variable_actives
                )
            else:
                trace_collection.mergeBranches(
                    collection_yes=collection_exception_handling, collection_no=None
                )

        # An empty exception handler means we have to swallow exception.
        if (
            (
                not self.tried_may_raise
                or (
                    except_handler is not None
                    and except_handler.subnode_statements[
                        0
                    ].isStatementReraiseException()
                )
            )
            and break_handler is None
            and continue_handler is None
            and return_handler is None
        ):
            return (
                tried,
                "new_statements",
                "Removed useless try, all handlers became empty.",
            )

        tried_statements = tried.subnode_statements

        pre_statements = []

        while tried_statements:
            tried_statement = tried_statements[0]

            if tried_statement.mayRaiseException(BaseException):
                break

            if break_handler is not None and tried_statement.mayBreak():
                break

            if continue_handler is not None and tried_statement.mayContinue():
                break

            if return_handler is not None and tried_statement.mayReturn():
                break

            pre_statements.append(tried_statement)
            tried_statements = list(tried_statements)

            del tried_statements[0]

        post_statements = []

        if except_handler is not None and except_handler.isStatementAborting():
            while tried_statements:
                tried_statement = tried_statements[-1]

                if tried_statement.mayRaiseException(BaseException):
                    break

                if break_handler is not None and tried_statement.mayBreak():
                    break

                if continue_handler is not None and tried_statement.mayContinue():
                    break

                if return_handler is not None and tried_statement.mayReturn():
                    break

                post_statements.insert(0, tried_statement)
                tried_statements = list(tried_statements)

                del tried_statements[-1]

        if pre_statements or post_statements:
            assert tried_statements  # Should be dealt with already

            tried.setChild("statements", tried_statements)

            result = StatementsSequence(
                statements=pre_statements + [self] + post_statements,
                source_ref=self.source_ref,
            )

            def explain():
                # TODO: We probably don't want to say this for re-formulation ones.
                result = "Reduced scope of tried block."

                if pre_statements:
                    result += " Leading statements at %s." % (
                        ",".join(
                            x.getSourceReference().getAsString() + "/" + str(x)
                            for x in pre_statements
                        )
                    )

                if post_statements:
                    result += " Trailing statements at %s." % (
                        ",".join(
                            x.getSourceReference().getAsString() + "/" + str(x)
                            for x in post_statements
                        )
                    )

                return result

            return (result, "new_statements", explain)

        return self, None, None

    def mayReturn(self):
        # TODO: If we optimized return handler away, this would be not needed
        # or even non-optimal.
        if self.subnode_tried.mayReturn():
            return True

        if self.tried_may_raise is not False:
            except_handler = self.subnode_except_handler

            if except_handler is not None and except_handler.mayReturn():
                return True

        break_handler = self.subnode_break_handler

        if break_handler is not None and break_handler.mayReturn():
            return True

        continue_handler = self.subnode_continue_handler

        if continue_handler is not None and continue_handler.mayReturn():
            return True

        return_handler = self.subnode_return_handler

        if return_handler is not None and return_handler.mayReturn():
            return True

        return False

    def mayBreak(self):
        # TODO: If we optimized return handler away, this would be not needed
        # or even non-optimal.
        if self.subnode_tried.mayBreak():
            return True

        if self.tried_may_raise is not False:
            except_handler = self.subnode_except_handler

            if except_handler is not None and except_handler.mayBreak():
                return True

        break_handler = self.subnode_break_handler

        if break_handler is not None and break_handler.mayBreak():
            return True

        continue_handler = self.subnode_continue_handler

        if continue_handler is not None and continue_handler.mayBreak():
            return True

        return_handler = self.subnode_return_handler

        if return_handler is not None and return_handler.mayBreak():
            return True

        return False

    def mayContinue(self):
        # TODO: If we optimized return handler away, this would be not needed
        # or even non-optimal.
        if self.subnode_tried.mayContinue():
            return True

        if self.tried_may_raise is not False:
            except_handler = self.subnode_except_handler

            if except_handler is not None and except_handler.mayContinue():
                return True

        break_handler = self.subnode_break_handler

        if break_handler is not None and break_handler.mayContinue():
            return True

        continue_handler = self.subnode_continue_handler

        if continue_handler is not None and continue_handler.mayContinue():
            return True

        return_handler = self.subnode_return_handler

        if return_handler is not None and return_handler.mayContinue():
            return True

        return False

    def isStatementAborting(self):
        if self.tried_may_raise is not False:
            except_handler = self.subnode_except_handler

            if except_handler is None or not except_handler.isStatementAborting():
                return False

        break_handler = self.subnode_break_handler

        if break_handler is not None and not break_handler.isStatementAborting():
            return False

        continue_handler = self.subnode_continue_handler

        if continue_handler is not None and not continue_handler.isStatementAborting():
            return False

        return_handler = self.subnode_return_handler

        if return_handler is not None and not return_handler.isStatementAborting():
            return False

        return self.subnode_tried.isStatementAborting()

    def mayRaiseException(self, exception_type):
        if self.tried_may_raise is not False:
            except_handler = self.subnode_except_handler

            if except_handler is not None and except_handler.mayRaiseException(
                exception_type
            ):
                return True

        break_handler = self.subnode_break_handler

        if break_handler is not None and break_handler.mayRaiseException(
            exception_type
        ):
            return True

        continue_handler = self.subnode_continue_handler

        if continue_handler is not None and continue_handler.mayRaiseException(
            exception_type
        ):
            return True

        return_handler = self.subnode_return_handler

        if return_handler is not None and return_handler.mayRaiseException(
            exception_type
        ):
            return True

        return False

    def needsFrame(self):
        if self.tried_may_raise is not False:
            except_handler = self.subnode_except_handler

            if except_handler is not None and except_handler.needsFrame():
                return True

        break_handler = self.subnode_break_handler

        if break_handler is not None and break_handler.needsFrame():
            return True

        continue_handler = self.subnode_continue_handler

        if continue_handler is not None and continue_handler.needsFrame():
            return True

        return_handler = self.subnode_return_handler

        if return_handler is not None and return_handler.needsFrame():
            return True

        return self.subnode_tried.needsFrame()

    @staticmethod
    def getStatementNiceName():
        return "tried block statement"
