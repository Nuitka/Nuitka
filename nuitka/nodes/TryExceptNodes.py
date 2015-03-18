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
""" Nodes for try/except

The try/except is re-formulated to only one handler. The different catches
are conditional statements and not the issue anymore.

"""

from nuitka.optimizations.TraceCollections import ConstraintCollectionBranch

from .NodeBases import (
    StatementChildrenHavingBase,
    checkStatementsSequenceOrNone
)


class StatementTryExcept(StatementChildrenHavingBase):
    kind = "STATEMENT_TRY_EXCEPT"

    named_children = (
        "tried",
        "handling"
    )

    checkers = {
        "tried"    : checkStatementsSequenceOrNone,
        "handling" : checkStatementsSequenceOrNone
    }

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


        collection_exception_handling = ConstraintCollectionBranch(
            parent = constraint_collection,
        )

        collection_exception_handling.degradePartiallyFromCode(tried_statement_sequence)

        if self.getExceptionHandling() is not None:
            collection_exception_handling.computeBranch(
                branch = self.getExceptionHandling()
            )


        # Merge only, if the exception handling itself does exit.
        if self.getExceptionHandling() is None or \
           not self.getExceptionHandling().isStatementAborting():

            constraint_collection.mergeBranches(
                collection_yes = collection_exception_handling,
                collection_no  = None
            )

        # Without exception handlers remaining, nothing else to do. They may
        # e.g. be removed as only re-raising.
        if self.getExceptionHandling() and \
           self.getExceptionHandling().getStatements()[0].\
             isStatementReraiseException():
            return tried_statement_sequence, "new_statements", """\
Removed try/except without any remaining handlers."""

        # Remove exception handling, if it cannot happen.
        if not tried_statement_sequence.mayRaiseException(BaseException):
            return tried_statement_sequence, "new_statements", """\
Removed try/except with tried block that cannot raise."""

        new_statements = tried_statement_sequence.getStatements()
        # Determine statements inside the exception guard, that need not be in
        # a handler, because they wouldn't raise an exception. TODO: This
        # actual exception being watched for should be considered, by look
        # for any now.
        outside_pre = []
        while new_statements and \
              not new_statements[0].mayRaiseException(BaseException):
            outside_pre.append(new_statements[0])
            new_statements = list(new_statements)[1:]

        outside_post = []
        if self.getExceptionHandling() is not None and \
           self.getExceptionHandling().isStatementAborting():
            while new_statements and \
                  not new_statements[-1].mayRaiseException(BaseException):
                outside_post.insert(0, new_statements[-1])
                new_statements = list(new_statements)[:-1]

        if outside_pre or outside_post:
            tried_statement_sequence.setStatements(new_statements)

            from .NodeMakingHelpers import makeStatementsSequenceReplacementNode

            result = makeStatementsSequenceReplacementNode(
                statements = outside_pre + [self] + outside_post,
                node       = self
            )

            return result, "new_statements", """\
Moved statements of tried block that cannot raise."""

        return self, None, None
