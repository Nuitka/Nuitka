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
""" Nodes for try/except and try/finally

The try/except needs handlers, and these blocks are complex control flow.

"""

from .NodeBases import StatementChildrenHavingBase


class StatementTryFinally(StatementChildrenHavingBase):
    kind = "STATEMENT_TRY_FINALLY"

    named_children = ( "tried", "final" )

    def __init__(self, tried, final, source_ref):
        assert tried is None or tried.isStatementsSequence()
        assert final is None or final.isStatementsSequence()

        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "tried" : tried,
                "final" : final
            },
            source_ref = source_ref
        )

        self.break_exception = False
        self.continue_exception = False
        self.return_value_exception_catch = False
        self.return_value_exception_reraise = False

    getBlockTry = StatementChildrenHavingBase.childGetter( "tried" )
    setBlockTry = StatementChildrenHavingBase.childSetter( "tried" )
    getBlockFinal = StatementChildrenHavingBase.childGetter( "final" )
    setBlockFinal = StatementChildrenHavingBase.childSetter( "final" )

    def isStatementAborting(self):
        # In try/finally there are two chances to raise or return a value, so we
        # need to "or" the both branches. One of them will do.

        tried_block = self.getBlockTry()

        if tried_block is not None and tried_block.isStatementAborting():
            return True

        final_block = self.getBlockFinal()

        if final_block is not None and final_block.isStatementAborting():
            return True

        return False

    def markAsExceptionContinue(self):
        self.continue_exception = True

    def markAsExceptionBreak(self):
        self.break_exception = True

    def markAsExceptionReturnValueCatch(self):
        self.return_value_exception_catch = True

    def markAsExceptionReturnValueReraise(self):
        self.return_value_exception_reraise = True

    def needsExceptionContinue(self):
        return self.continue_exception

    def needsExceptionBreak(self):
        return self.break_exception

    def needsExceptionReturnValueCatcher(self):
        return self.return_value_exception_catch

    def needsExceptionReturnValueReraiser(self):
        return self.return_value_exception_reraise

    def computeStatement(self, constraint_collection):
        # The tried block must be considered as a branch, if it is not empty
        # already.
        tried_statement_sequence = self.getBlockTry()

        # May be "None" from the outset, so guard against that, later in this
        # function we are going to remove it.
        if tried_statement_sequence is not None:
            result = tried_statement_sequence.computeStatementsSequence(
                constraint_collection = constraint_collection
            )

            # Might be changed.
            if result is not tried_statement_sequence:
                tried_statement_sequence.replaceWith( result )
                tried_statement_sequence = result

        final_statement_sequence = self.getBlockFinal()

        # TODO: The final must not assume that all of tried was executed,
        # instead it may have aborted after any part of it, which is a rather
        # complex definition.

        if final_statement_sequence is not None:
            if tried_statement_sequence is not None:
                from nuitka.tree.Extractions import getVariablesWritten

                variable_writes = getVariablesWritten(
                    tried_statement_sequence
                )


                # Mark all variables as unknown that are written in the tried
                # block, so it destroys the assumptions for loop turn around.
                for variable, _variable_version in variable_writes:
                    constraint_collection.markActiveVariableAsUnknown(
                        variable = variable
                    )


            # Then assuming no exception, the no raise block if present.
            result = final_statement_sequence.computeStatementsSequence(
                constraint_collection = constraint_collection
            )

            if result is not final_statement_sequence:
                self.setBlockFinal(result)

                final_statement_sequence = result

        # Note: Need to query again, because the object may have changed in the
        # "computeStatementsSequence" calls.

        if tried_statement_sequence is None:
            # If the tried block is empty, go to the final block directly, if
            # any.
            return final_statement_sequence, "new_statements", """\
Removed try/finally with empty tried block."""
        elif final_statement_sequence is None:
            # If the final block is empty, just need to execute the tried block
            # then.
            return tried_statement_sequence, "new_statements", """\
Removed try/finally with empty final block."""
        else:
            # TODO: Can't really merge it yet.
            constraint_collection.removeAllKnowledge()

            # Otherwise keep it as it.
            return self, None, None


class StatementExceptHandler(StatementChildrenHavingBase):
    kind = "STATEMENT_EXCEPT_HANDLER"

    named_children = (
        "exception_types",
        "body"
    )

    def __init__(self, exception_types, body, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "exception_types" : tuple( exception_types ),
                "body"            : body,
            },
            source_ref = source_ref
        )

    getExceptionTypes  = StatementChildrenHavingBase.childGetter(
        "exception_types"
    )
    getExceptionBranch = StatementChildrenHavingBase.childGetter(
        "body"
    )
    setExceptionBranch = StatementChildrenHavingBase.childSetter(
        "body"
    )


class StatementTryExcept(StatementChildrenHavingBase):
    kind = "STATEMENT_TRY_EXCEPT"

    named_children = ( "tried", "handlers" )

    def __init__(self, tried, handlers, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "tried"    : tried,
                "handlers" : tuple( handlers )
            },
            source_ref = source_ref
        )

    getBlockTry = StatementChildrenHavingBase.childGetter(
        "tried"
    )
    setBlockTry = StatementChildrenHavingBase.childSetter(
        "tried"
    )

    getExceptionHandlers = StatementChildrenHavingBase.childGetter(
        "handlers"
    )

    def isStatementAborting(self):
        tried_block = self.getBlockTry()

        # Happens during tree building only.
        if tried_block is None:
            return False

        if not tried_block.isStatementAborting():
            return False

        for handler in self.getExceptionHandlers():
            if not handler.isStatementAborting():
                return False

        return True

    def isStatementTryExceptOptimized(self):
        tried_block = self.getBlockTry()

        tried_statements = tried_block.getStatements()

        if len( tried_statements ) == 1:
            tried_statement = tried_statements[0]

            if tried_statement.isStatementAssignmentVariable():
                source = tried_statement.getAssignSource()

                if source.isExpressionBuiltinNext1():
                    if not source.getValue().mayRaiseException( BaseException ):
                        # Note: Now we know the source lookup is the only thing
                        # that may raise.

                        handlers = self.getExceptionHandlers()

                        if len( handlers ) == 1:
                            catched_types = handlers[0].getExceptionTypes()

                            if len( catched_types ) == 1:
                                catched_type = catched_types[0]

                                if catched_type.isExpressionBuiltinExceptionRef():
                                    if catched_type.getExceptionName() == "StopIteration":
                                        if handlers[0].getExceptionBranch().isStatementAborting():
                                            return True

        return False


    def computeStatement(self, constraint_collection):
        # The tried block can be processed normally.
        tried_statement_sequence = self.getBlockTry()

        # May be "None" from the outset, so guard against that, later we are
        # going to remove it.
        if tried_statement_sequence is not None:
            result = tried_statement_sequence.computeStatementsSequence(
                constraint_collection = constraint_collection
            )

            if result is not tried_statement_sequence:
                self.setBlockTry(result)

                tried_statement_sequence = result

        if tried_statement_sequence is None:
            return None, "new_statements", """\
Removed try/except with empty tried block."""

        from nuitka.optimizations.ConstraintCollections import \
            ConstraintCollectionHandler
        # The exception branches triggers in unknown state, any amount of tried
        # code may have happened. A similar approach to loops should be taken to
        # invalidate the state before.
        for handler in self.getExceptionHandlers():
            collection_exception_branch = ConstraintCollectionHandler(
                parent  = constraint_collection,
                handler = handler
            )

        # Without exception handlers remaining, nothing else to do. They may
        # e.g. be removed as only re-raising.
        if not self.getExceptionHandlers():
            return tried_statement_sequence, "new_statements", """\
Removed try/except without any remaing handlers."""

        # Give up, merging this is too hard for now, any amount of the tried
        # sequence may have executed together with one of the handlers, or all
        # of tried and no handlers. TODO: improve this to an actual merge, even
        # if a pessimistic one.
        constraint_collection.removeAllKnowledge()

        return self, None, None
