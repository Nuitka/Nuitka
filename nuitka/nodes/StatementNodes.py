#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Nodes for statements.

"""

from .NodeBases import StatementBase, StatementChildHavingBase


def checkStatements(value):
    """ Check that statements list value property.

    Must not be None, must not contain None, and of course only statements,
    may be empty.
    """

    assert value is not None
    assert None not in value

    for statement in value:
        assert statement.isStatement() or statement.isStatementsFrame(), \
          statement.asXmlText()

    return tuple(value)


class StatementsSequence(StatementChildHavingBase):
    kind = "STATEMENTS_SEQUENCE"

    named_child = "statements"

    checker = checkStatements

    def __init__(self, statements, source_ref):
        StatementChildHavingBase.__init__(
            self,
            value      = tuple(statements),
            source_ref = source_ref
        )

    getStatements = StatementChildHavingBase.childGetter("statements")
    setStatements = StatementChildHavingBase.childSetter("statements")

    def finalize(self):
        del self.parent

        for s in self.getStatements():
            s.finalize()

    # Overloading name based automatic check, so that derived ones know it too.
    def isStatementsSequence(self):
        # Virtual method, pylint: disable=no-self-use

        return True

    def trimStatements(self, statement):
        assert statement.parent is self

        old_statements = list(self.getStatements())
        assert statement in old_statements, \
          (statement, self)

        new_statements = old_statements[ : old_statements.index(statement)+1 ]

        self.setChild("statements", new_statements)

    def removeStatement(self, statement):
        assert statement.parent is self

        statements = list(self.getStatements())
        statements.remove(statement)

        self.setChild("statements", statements)

    def mergeStatementsSequence(self, statement_sequence):
        assert statement_sequence.parent is self

        old_statements = list(self.getStatements())
        assert statement_sequence in old_statements, \
          (statement_sequence, self)

        merge_index =  old_statements.index(statement_sequence)

        new_statements = tuple(old_statements[ : merge_index ])     + \
                         statement_sequence.getStatements()         + \
                         tuple(old_statements[ merge_index+1 : ])

        self.setChild("statements", new_statements)

    def mayHaveSideEffects(self):
        # Statement sequences have a side effect if one of the statements does.
        for statement in self.getStatements():
            if statement.mayHaveSideEffects():
                return True
        return False

    def mayRaiseException(self, exception_type):
        for statement in self.getStatements():
            if statement.mayRaiseException(exception_type):
                return True
        return False

    def needsFrame(self):
        for statement in self.getStatements():
            if statement.needsFrame():
                return True
        return False

    def mayReturn(self):
        for statement in self.getStatements():
            if statement.mayReturn():
                return True
        return False

    def mayBreak(self):
        for statement in self.getStatements():
            if statement.mayBreak():
                return True
        return False

    def mayContinue(self):
        for statement in self.getStatements():
            if statement.mayContinue():
                return True
        return False

    def mayRaiseExceptionOrAbort(self, exception_type):
        return self.mayRaiseException(exception_type) or \
               self.mayReturn() or \
               self.mayBreak() or \
               self.mayContinue()

    def isStatementAborting(self):
        return self.getStatements()[-1].isStatementAborting()

    def computeStatement(self, trace_collection):
        # Don't want to be called like this.
        assert False, self

    def computeStatementsSequence(self, trace_collection):
        new_statements = []

        statements = self.getStatements()
        assert statements, self

        for count, statement in enumerate(statements):
            # May be frames embedded.
            if statement.isStatementsFrame():
                new_statement = statement.computeStatementsSequence(
                    trace_collection
                )
            else:
                new_statement = trace_collection.onStatement(
                    statement = statement
                )

            if new_statement is not None:
                if new_statement.isStatementsSequence() and \
                   not new_statement.isStatementsFrame():
                    new_statements.extend(
                        new_statement.getStatements()
                    )
                else:
                    new_statements.append(
                        new_statement
                    )

                if statement is not statements[-1] and \
                   new_statement.isStatementAborting():
                    trace_collection.signalChange(
                        "new_statements",
                        statements[count+1].getSourceReference(),
                        "Removed dead statements."
                    )

                    for s in statements[statements.index(statement)+1:]:
                        s.finalize()

                    break

        if statements != new_statements:
            if new_statements:
                self.setStatements(new_statements)

                return self
            else:
                return None
        else:
            return self

    def getStatementNiceName(self):
        return "statements sequence"


class StatementExpressionOnly(StatementChildHavingBase):
    kind = "STATEMENT_EXPRESSION_ONLY"

    named_child = "expression"

    def __init__(self, expression, source_ref):
        assert expression.isExpression()

        StatementChildHavingBase.__init__(
            self,
            value      = expression,
            source_ref = source_ref
        )

    def getDetail(self):
        return "expression %s" % self.getExpression()

    def mayHaveSideEffects(self):
        return self.getExpression().mayHaveSideEffects()

    def mayRaiseException(self, exception_type):
        return self.getExpression().mayRaiseException(exception_type)

    getExpression = StatementChildHavingBase.childGetter("expression")

    def computeStatement(self, trace_collection):
        trace_collection.onExpression(
            expression = self.getExpression()
        )
        expression = self.getExpression()

        if expression.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        result, change_tags, change_desc = expression.computeExpressionDrop(
            statement        = self,
            trace_collection = trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self, None, None

    def getStatementNiceName(self):
        return "expression only statement"


class StatementPreserveFrameException(StatementBase):
    kind = "STATEMENT_PRESERVE_FRAME_EXCEPTION"

    __slots__ = ("preserver_id",)

    def __init__(self, preserver_id, source_ref):
        StatementBase.__init__(
            self,
            source_ref = source_ref
        )

        self.preserver_id = preserver_id

    def finalize(self):
        del self.parent

    def getDetails(self):
        return {
            "preserver_id" : self.preserver_id
        }

    def getPreserverId(self):
        return self.preserver_id

    def computeStatement(self, trace_collection):
        # For Python2 generators, it's not necessary to preserve, the frame
        # decides it. TODO: This check makes only sense once.

        if self.getParentStatementsFrame().needsExceptionFramePreservation():
            return self, None, None
        else:
            return (
                None,
                "new_statements",
                "Removed frame preservation for generators."
            )

    def mayRaiseException(self, exception_type):
        return False

    def needsFrame(self):
        return True


class StatementRestoreFrameException(StatementBase):
    kind = "STATEMENT_RESTORE_FRAME_EXCEPTION"

    __slots__ = ("preserver_id",)

    def __init__(self, preserver_id, source_ref):
        StatementBase.__init__(
            self,
            source_ref = source_ref
        )

        self.preserver_id = preserver_id

    def finalize(self):
        del self.parent

    def getDetails(self):
        return {
            "preserver_id" : self.preserver_id
        }

    def getPreserverId(self):
        return self.preserver_id

    def computeStatement(self, trace_collection):
        return self, None, None

    def mayRaiseException(self, exception_type):
        return False


class StatementPublishException(StatementBase):
    kind = "STATEMENT_PUBLISH_EXCEPTION"

    def __init__(self, source_ref):
        StatementBase.__init__(
            self,
            source_ref = source_ref
        )

    def finalize(self):
        del self.parent

    def computeStatement(self, trace_collection):
        # TODO: Determine the need for it.
        return self, None, None

    def mayRaiseException(self, exception_type):
        return False
