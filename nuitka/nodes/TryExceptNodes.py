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

from .NodeBases import StatementChildrenHavingBase


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
