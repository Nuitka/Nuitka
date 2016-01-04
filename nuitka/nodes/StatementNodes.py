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
""" Nodes for statements.

"""

from .NodeBases import NodeBase, StatementChildrenHavingBase


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


class StatementsSequence(StatementChildrenHavingBase):
    kind = "STATEMENTS_SEQUENCE"

    named_children = (
        "statements",
    )

    checkers = {
        "statements" : checkStatements
    }

    def __init__(self, statements, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "statements" : statements
            },
            source_ref = source_ref
        )

    getStatements = StatementChildrenHavingBase.childGetter("statements")
    setStatements = StatementChildrenHavingBase.childSetter("statements")

    def getDetailsForDisplay(self):
        if self.getStatements():
            return {
                "statement_count" : len(self.getStatements())
            }
        else:
            return {
                "statement_count" : 0
            }

    # Overloading name based automatic check, so that derived ones know it too.
    def isStatementsSequence(self):
        # Virtual method, pylint: disable=R0201

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

    def computeStatement(self, constraint_collection):
        # Don't want to be called like this.
        assert False, self

    def computeStatementsSequence(self, constraint_collection):
        new_statements = []

        statements = self.getStatements()
        assert statements, self

        for count, statement in enumerate(statements):
            # May be frames embedded.
            if statement.isStatementsFrame():
                new_statement = statement.computeStatementsSequence(
                    constraint_collection
                )
            else:
                new_statement = constraint_collection.onStatement(
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
                    constraint_collection.signalChange(
                        "new_statements",
                        statements[count+1].getSourceReference(),
                        "Removed dead statements."
                    )

                    break

        if statements != new_statements:
            if new_statements:
                self.setStatements(new_statements)

                return self
            else:
                return None
        else:
            return self



class StatementExpressionOnly(StatementChildrenHavingBase):
    kind = "STATEMENT_EXPRESSION_ONLY"

    named_children = (
        "expression",
    )

    def __init__(self, expression, source_ref):
        assert expression.isExpression()

        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "expression" : expression
            },
            source_ref = source_ref
        )

    def getDetail(self):
        return "expression %s" % self.getExpression()

    def mayHaveSideEffects(self):
        return self.getExpression().mayHaveSideEffects()

    def mayRaiseException(self, exception_type):
        return self.getExpression().mayRaiseException(exception_type)

    getExpression = StatementChildrenHavingBase.childGetter(
        "expression"
    )

    def computeStatement(self, constraint_collection):
        constraint_collection.onExpression(
            expression = self.getExpression()
        )
        expression = self.getExpression()

        if expression.mayRaiseException(BaseException):
            constraint_collection.onExceptionRaiseExit(BaseException)

        result, change_tags, change_desc = expression.computeExpressionDrop(
            statement             = self,
            constraint_collection = constraint_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self, None, None


class StatementGeneratorEntry(NodeBase):
    kind = "STATEMENT_GENERATOR_ENTRY"

    def __init__(self, source_ref):
        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

    def mayRaiseException(self, exception_type):
        # Anything might be thrown into a generator, representing that is the
        # whole point of this statement.
        return True

    def computeStatement(self, constraint_collection):
        constraint_collection.onExceptionRaiseExit(BaseException)

        # Nothing we can about it.
        return self, None, None


class StatementPreserveFrameException(NodeBase):
    kind = "STATEMENT_PRESERVE_FRAME_EXCEPTION"

    def __init__(self, preserver_id, source_ref):
        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

        self.preserver_id = preserver_id

    def getDetails(self):
        return {
            "preserver_id" : self.preserver_id
        }

    def getPreserverId(self):
        return self.preserver_id

    def computeStatement(self, constraint_collection):
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


class StatementRestoreFrameException(NodeBase):
    kind = "STATEMENT_RESTORE_FRAME_EXCEPTION"

    def __init__(self, preserver_id, source_ref):
        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

        self.preserver_id = preserver_id

    def getDetails(self):
        return {
            "preserver_id" : self.preserver_id
        }

    def getPreserverId(self):
        return self.preserver_id

    def computeStatement(self, constraint_collection):
        return self, None, None

    def mayRaiseException(self, exception_type):
        return False


class StatementPublishException(NodeBase):
    kind = "STATEMENT_PUBLISH_EXCEPTION"

    def __init__(self, source_ref):
        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

    def computeStatement(self, constraint_collection):
        # TODO: Determine the need for it.
        return self, None, None

    def mayRaiseException(self, exception_type):
        return False
