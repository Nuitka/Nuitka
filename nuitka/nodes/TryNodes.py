#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .NodeBases import ExpressionChildrenHavingBase, StatementChildrenHavingBase


class ReturnBreakContinueHandlingMixin:
    def __init__(self):
        self.needs_return_handling = 0
        self.needs_continue_handling = False
        self.needs_break_handling = False

    def markAsNeedsReturnHandling(self, value):
        self.needs_return_handling = value

    def needsReturnHandling(self):
        return self.needs_return_handling > 0

    def needsReturnValueRelease(self):
        return self.needs_return_handling == 2

    def markAsNeedsContinueHandling(self):
        self.needs_continue_handling = True

    def needsContinueHandling(self):
        return self.needs_continue_handling

    def markAsNeedsBreakHandling(self):
        self.needs_break_handling = True

    def needsBreakHandling(self):
        return self.needs_break_handling


class StatementTryFinally(StatementChildrenHavingBase,
                          ReturnBreakContinueHandlingMixin):
    kind = "STATEMENT_TRY_FINALLY"

    named_children = (
        "tried",
        "final"
    )

    def __init__(self, tried, final, public_exc, source_ref):
        assert tried is None or tried.isStatementsSequence()
        assert final is None or final.isStatementsSequence()

        self.public_exc = public_exc

        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "tried" : tried,
                "final" : final
            },
            source_ref = source_ref
        )

        ReturnBreakContinueHandlingMixin.__init__(self)


    getBlockTry = StatementChildrenHavingBase.childGetter(
        "tried"
    )
    setBlockTry = StatementChildrenHavingBase.childSetter(
        "tried"
    )

    getBlockFinal = StatementChildrenHavingBase.childGetter(
        "final"
    )
    setBlockFinal = StatementChildrenHavingBase.childSetter(
        "final"
    )

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

    def mayRaiseException(self, exception_type):
        return self.getBlockTry().mayRaiseException(exception_type) or \
               self.getBlockFinal().mayRaiseException(exception_type)

    def mayReturn(self):
        return self.getBlockTry().mayReturn() or \
               self.getBlockFinal().mayReturn()

    def mayBreak(self):
        return self.getBlockTry().mayBreak() or \
               self.getBlockFinal().mayBreak()

    def mayContinue(self):
        return self.getBlockTry().mayContinue() or \
               self.getBlockFinal().mayContinue()

    def needsFrame(self):
        return self.getBlockTry().needsFrame() or \
               self.getBlockFinal().needsFrame()

    def needsExceptionPublish(self):
        return self.public_exc

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
                self.setBlockTry(result)
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
        elif not tried_statement_sequence.mayRaiseExceptionOrAbort(
                BaseException
            ):
            tried_statement_sequence.setChild(
                "statements",
                tried_statement_sequence.getStatements() +
                final_statement_sequence.getStatements()
            )

            return tried_statement_sequence, "new_statements", """\
Removed try/finally with try block that cannot raise."""
        else:
            # TODO: Can't really merge it yet.
            constraint_collection.removeAllKnowledge()

            # Otherwise keep it as it.
            return self, None, None


class ExpressionTryFinally(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_TRY_FINALLY"

    named_children = (
        "tried",
        "expression",
        "final"
    )

    def __init__(self, tried, expression, final, source_ref):
        assert final is not None or tried is not None
        assert tried is None or tried.isStatementsSequence()
        assert final is None or final.isStatementsSequence()

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "tried"      : tried,
                "expression" : expression,
                "final"      : final
            },
            source_ref = source_ref
        )

    getBlockTry = ExpressionChildrenHavingBase.childGetter(
        "tried"
    )
    setBlockTry = ExpressionChildrenHavingBase.childSetter(
        "tried"
    )

    getBlockFinal = ExpressionChildrenHavingBase.childGetter(
        "final"
    )
    setBlockFinal = ExpressionChildrenHavingBase.childSetter(
        "final"
    )

    getExpression = ExpressionChildrenHavingBase.childGetter(
        "expression"
    )
    setExpression = ExpressionChildrenHavingBase.childSetter(
        "expression"
    )

    def needsReturnHandling(self):
        # This is an overload, pylint: disable=R0201
        return False

    def needsReturnValueRelease(self):
        # This is an overload, pylint: disable=R0201
        return False

    def needsContinueHandling(self):
        # This is an overload, pylint: disable=R0201
        return False

    def needsBreakHandling(self):
        # This is an overload, pylint: disable=R0201
        return False

    def needsExceptionPublish(self):
        # This is an overload, pylint: disable=R0201
        return False

    def mayRaiseException(self, exception_type):
        tried_block = self.getBlockTry()

        if tried_block is not None and \
           tried_block.mayRaiseException(exception_type):
            return True

        if self.getExpression().mayRaiseException(exception_type):
            return True

        final_block = self.getBlockFinal()

        if final_block is not None and \
           final_block.mayRaiseException(exception_type):
            return True

        return False

    def computeExpressionRaw(self, constraint_collection):
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
                self.setBlockTry(result)
                tried_statement_sequence = result

        # The main expression itself.
        constraint_collection.onExpression(self.getExpression())

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

        if tried_statement_sequence is None and \
           final_statement_sequence is None:
            # If the tried and final block is empty, go to the expression
            # directly.
            return self.getExpression(), "new_expression", """\
Removed try/finally expression with empty tried and final block."""
        else:
            # TODO: Can't really merge it yet.
            constraint_collection.removeAllKnowledge()

            # Otherwise keep it as it.
            return self, None, None

    def computeExpressionDrop(self, statement, constraint_collection):
        from .NodeMakingHelpers import (
          makeStatementExpressionOnlyReplacementNode,
          makeStatementsSequenceReplacementNode
        )

        tried = self.getBlockTry()

        if tried is None:
            statements = ()
        else:
            statements = tried.getStatements()

        statements += (
            makeStatementExpressionOnlyReplacementNode(
                expression = self.getExpression(),
                node       = self.getExpression()
            ),
        )

        tried = makeStatementsSequenceReplacementNode(
            statements = statements,
            node       = self
        )

        result = StatementTryFinally(
            tried      = tried,
            final      = self.getBlockFinal(),
            public_exc = self.needsExceptionPublish(),
            source_ref = self.getSourceReference()
        )

        return result, "new_statements", """\
Replaced try/finally expression with try/finally statement."""


    def canPredictIterationValues(self):
        # pylint: disable=R0201

        return False

        # TODO: Users should not rely on this to be able to directly extract
        # values, but preserve our side effects.
        # return self.getExpression().canPredictIterationValues()

    def getIterationValues(self):
        return self.getExpression().getIterationValues()

    def isMappingWithConstantStringKeys(self):
        # pylint: disable=R0201
        return False

        # TODO: Uses should not depend on this to mean there is no side effects,
        # then we could delegate.


class StatementTryExcept(StatementChildrenHavingBase):
    kind = "STATEMENT_TRY_EXCEPT"

    named_children = (
        "tried",
        "handling"
    )

    def __init__(self, tried, handling, public_exc, source_ref):
        self.public_exc = public_exc

        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "tried"    : tried,
                "handling" : handling
            },
            source_ref = source_ref
        )

        assert type(public_exc) is bool

    getBlockTry = StatementChildrenHavingBase.childGetter(
        "tried"
    )
    setBlockTry = StatementChildrenHavingBase.childSetter(
        "tried"
    )

    getExceptionHandling = StatementChildrenHavingBase.childGetter(
        "handling"
    )

    def isStatementAborting(self):
        tried_block = self.getBlockTry()
        handling = self.getExceptionHandling()

        if tried_block is not None and tried_block.isStatementAborting() and \
           handling is not None and handling.isStatementAborting():
            return True

        return False

    def mayRaiseException(self, exception_type):
        tried = self.getBlockTry()

        if tried is None:
            return False

        handling = self.getExceptionHandling()

        if handling is None:
            return False

        return handling.mayRaiseException(exception_type) and \
               tried.mayRaiseException(exception_type)

    def mayReturn(self):
        handling = self.getExceptionHandling()

        if handling is not None and handling.mayReturn():
            return True

        tried = self.getBlockTry()

        if tried is not None and tried.mayReturn():
            return True

        return False

    def mayBreak(self):
        handling = self.getExceptionHandling()

        if handling is not None and handling.mayBreak():
            return True

        tried = self.getBlockTry()

        if tried is not None and tried.mayBreak():
            return True

        return False

    def mayContinue(self):
        handling = self.getExceptionHandling()

        if handling is not None and handling.mayContinue():
            return True

        tried = self.getBlockTry()

        if tried is not None and tried.mayContinue():
            return True

        return False

    def needsFrame(self):
        return True

    def needsExceptionPublish(self):
        return self.public_exc

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

        # TODO: Need not to remove all knowledge, but only the parts that were
        # touched.
        constraint_collection.removeAllKnowledge()

        if self.getExceptionHandling() is not None:
            from nuitka.optimizations.ConstraintCollections import \
              ConstraintCollectionBranch

            _collection_exception_handling = ConstraintCollectionBranch(
                parent = constraint_collection,
                branch = self.getExceptionHandling()
            )

        # Without exception handlers remaining, nothing else to do. They may
        # e.g. be removed as only re-raising.
        if self.getExceptionHandling() and \
           self.getExceptionHandling().getStatements()[0].\
             isStatementReraiseException():
            return tried_statement_sequence, "new_statements", """\
Removed try/except without any remaing handlers."""

        # Remove exception handling, if it cannot happen.
        if not tried_statement_sequence.mayRaiseException(BaseException):
            return tried_statement_sequence, "new_statements", """\
Removed try/except with tried block that cannot raise."""

        # Give up, merging this is too hard for now, any amount of the tried
        # sequence may have executed together with one of the handlers, or all
        # of tried and no handlers. TODO: improve this to an actual merge, even
        # if a pessimistic one.
        constraint_collection.removeAllKnowledge()

        return self, None, None
