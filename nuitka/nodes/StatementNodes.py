#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Nodes for statements.

"""

from nuitka.PythonVersions import python_version

from .NodeBases import StatementBase
from .StatementBasesGenerated import (
    StatementExpressionOnlyBase,
    StatementsSequenceBase,
)


class StatementsSequenceMixin(object):
    __slots__ = ()

    def finalize(self):
        del self.parent

        for s in self.subnode_statements:
            s.finalize()

    @staticmethod
    def isStatementsSequence():
        return True

    def computeStatement(self, trace_collection):
        # Don't want to be called like this.
        assert False, self

    def trimStatements(self, statement):
        assert statement.parent is self

        old_statements = list(self.subnode_statements)
        assert statement in old_statements, (statement, self)

        new_statements = old_statements[: old_statements.index(statement) + 1]

        self.setChildStatements(new_statements)

    def removeStatement(self, statement):
        assert statement.parent is self

        statements = list(self.subnode_statements)
        statements.remove(statement)
        self.setChildStatements(tuple(statements))

        if statements:
            return self
        else:
            return None

    def replaceStatement(self, statement, statements):
        old_statements = list(self.subnode_statements)

        merge_index = old_statements.index(statement)

        new_statements = (
            tuple(old_statements[:merge_index])
            + tuple(statements)
            + tuple(old_statements[merge_index + 1 :])
        )

        self.setChildStatements(new_statements)

    def mayHaveSideEffects(self):
        # Statement sequences have a side effect if one of the statements does.
        for statement in self.subnode_statements:
            if statement.mayHaveSideEffects():
                return True
        return False

    def mayRaiseException(self, exception_type):
        for statement in self.subnode_statements:
            if statement.mayRaiseException(exception_type):
                return True
        return False

    def needsFrame(self):
        for statement in self.subnode_statements:
            if statement.needsFrame():
                return True
        return False

    def mayReturn(self):
        for statement in self.subnode_statements:
            if statement.mayReturn():
                return True
        return False

    def mayBreak(self):
        for statement in self.subnode_statements:
            if statement.mayBreak():
                return True
        return False

    def mayContinue(self):
        for statement in self.subnode_statements:
            if statement.mayContinue():
                return True
        return False

    def mayRaiseExceptionOrAbort(self, exception_type):
        return (
            self.mayRaiseException(exception_type)
            or self.mayReturn()
            or self.mayBreak()
            or self.mayContinue()
        )

    def isStatementAborting(self):
        return self.subnode_statements[-1].isStatementAborting()

    def willRaiseAnyException(self):
        return self.subnode_statements[-1].willRaiseAnyException()


class StatementsSequence(StatementsSequenceMixin, StatementsSequenceBase):
    kind = "STATEMENTS_SEQUENCE"

    named_children = ("statements|tuple+setter",)

    @staticmethod
    def isStatementsSequenceButNotFrame():
        return True

    def computeStatementsSequence(self, trace_collection):
        new_statements = []

        statements = self.subnode_statements
        assert statements, self

        for count, statement in enumerate(statements):
            # May be frames embedded.
            if statement.isStatementsFrame():
                new_statement = statement.computeStatementsSequence(trace_collection)
            else:
                new_statement = trace_collection.onStatement(statement=statement)

            if new_statement is not None:
                if new_statement.isStatementsSequenceButNotFrame():
                    new_statements.extend(new_statement.subnode_statements)
                else:
                    new_statements.append(new_statement)

                if (
                    statement is not statements[-1]
                    and new_statement.isStatementAborting()
                ):
                    trace_collection.signalChange(
                        "new_statements",
                        statements[count + 1].getSourceReference(),
                        "Removed dead statements.",
                    )

                    for s in statements[statements.index(statement) + 1 :]:
                        s.finalize()

                    break

        new_statements = tuple(new_statements)
        if statements != new_statements:
            if new_statements:
                self.setChildStatements(new_statements)

                return self
            else:
                return None
        else:
            return self

    @staticmethod
    def getStatementNiceName():
        return "statements sequence"


class StatementExpressionOnly(StatementExpressionOnlyBase):
    kind = "STATEMENT_EXPRESSION_ONLY"

    named_children = ("expression",)

    def mayHaveSideEffects(self):
        return self.subnode_expression.mayHaveSideEffects()

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseException(exception_type)

    def computeStatement(self, trace_collection):
        # TODO: Maybe also have a variant that will not attempt dropping anymore, for nodes
        # that are known to not do it anymore, or wait for a node change, or make it part of
        # the expression interface to be used in statement form as well.

        expression = trace_collection.onExpression(self.subnode_expression)

        return expression.computeExpressionDrop(
            statement=self, trace_collection=trace_collection
        )

    @staticmethod
    def getStatementNiceName():
        return "expression only statement"

    def getDetailsForDisplay(self):
        return {"expression": self.subnode_expression.kind}


class StatementPreserveFrameException(StatementBase):
    kind = "STATEMENT_PRESERVE_FRAME_EXCEPTION"

    __slots__ = ("preserver_id",)

    def __init__(self, preserver_id, source_ref):
        StatementBase.__init__(self, source_ref=source_ref)

        self.preserver_id = preserver_id

    def finalize(self):
        del self.parent

    def getDetails(self):
        return {"preserver_id": self.preserver_id}

    def getPreserverId(self):
        return self.preserver_id

    if python_version < 0x300:

        def computeStatement(self, trace_collection):
            # For Python2 generators, it's not necessary to preserve, the frame
            # decides it. TODO: This check makes only sense once.

            if self.getParentStatementsFrame().needsExceptionFramePreservation():
                return self, None, None
            else:
                return (
                    None,
                    "new_statements",
                    "Removed frame preservation for generators.",
                )

    else:

        def computeStatement(self, trace_collection):
            return self, None, None

    @staticmethod
    def mayRaiseException(exception_type):
        return False

    @staticmethod
    def needsFrame():
        return True


class StatementRestoreFrameException(StatementBase):
    kind = "STATEMENT_RESTORE_FRAME_EXCEPTION"

    __slots__ = ("preserver_id",)

    def __init__(self, preserver_id, source_ref):
        StatementBase.__init__(self, source_ref=source_ref)

        self.preserver_id = preserver_id

    def finalize(self):
        del self.parent

    def getDetails(self):
        return {"preserver_id": self.preserver_id}

    def getPreserverId(self):
        return self.preserver_id

    def computeStatement(self, trace_collection):
        return self, None, None

    @staticmethod
    def mayRaiseException(exception_type):
        return False


class StatementPublishException(StatementBase):
    kind = "STATEMENT_PUBLISH_EXCEPTION"

    def __init__(self, source_ref):
        StatementBase.__init__(self, source_ref=source_ref)

    def finalize(self):
        del self.parent

    def computeStatement(self, trace_collection):
        # TODO: Determine the need for it.
        return self, None, None

    @staticmethod
    def mayRaiseException(exception_type):
        return False


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
