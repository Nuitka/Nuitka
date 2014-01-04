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
""" Nodes for statements.

"""

from .NodeBases import StatementChildrenHavingBase

from nuitka.Utils import python_version


def checkStatements(value):
    """ Check that statements list value propert.

    Must not be None, must not contain None, and of course only statements,
    may be empty.
    """

    assert value is not None
    assert None not in value

    for statement in value:
        assert statement.isStatement() or statement.isStatementsFrame(), \
          statement

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

    def getDetails(self):
        if self.getStatements():
            return {
                "statement_count" : len( self.getStatements() )
            }
        else:
            return {
                "statement_count" : 0
            }

    # Overloading name based automatic check, so that derived ones know it too.
    def isStatementsSequence(self):
        # Virtual method, pylint: disable=R0201,W0613

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
        else:
            return False

    def isStatementAborting(self):
        return self.getStatements()[-1].isStatementAborting()

    def computeStatement(self, constraint_collection):
        # Don't want to be called like this.
        assert False

    def computeStatementsSequence(self, constraint_collection):
        # Expect to be overloaded.
        assert not self.isStatementsFrame(), self

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
                        statements[count + 1].getSourceReference(),
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


def checkFrameStatements(value):
    """ Check that frames statements list value proper.

    Must not be None, must not contain None, and of course only statements
    sequences, or statements, may be empty.
    """

    assert value is not None
    assert None not in value

    for statement in value:
        assert statement.isStatement() or statement.isStatementsFrame(), \
          statement

    return tuple(value)


class StatementsFrame(StatementsSequence):
    kind = "STATEMENTS_FRAME"

    checkers = {
        "statements" : checkFrameStatements
    }

    def __init__(self, statements, guard_mode, code_name, var_names, arg_count,
                kw_only_count, has_starlist, has_stardict, source_ref):
        StatementsSequence.__init__(
            self,
            statements = statements,
            source_ref = source_ref
        )

        self.var_names = tuple( var_names )
        self.code_name = code_name

        self.kw_only_count = kw_only_count
        self.arg_count = arg_count

        self.guard_mode = guard_mode

        self.has_starlist = has_starlist
        self.has_stardict = has_stardict

        self.needs_frame_exception_preserve = False

    def getDetails(self):
        result = {
            "code_name"  : self.code_name,
            "var_names"  : ", ".join( self.var_names ),
            "guard_mode" : self.guard_mode
        }

        if python_version >= 300:
            result["kw_only_count"] = self.kw_only_count

        result.update(StatementsSequence.getDetails(self))

        return result

    def needsLineNumber(self):
        return False

    def getGuardMode(self):
        return self.guard_mode

    def getVarNames(self):
        return self.var_names

    def getCodeObjectName(self):
        return self.code_name

    def getKwOnlyParameterCount(self):
        return self.kw_only_count

    def getArgumentCount(self):
        return self.arg_count

    def makeCloneAt(self, source_ref):
        assert False

    def markAsFrameExceptionPreserving(self):
        self.needs_frame_exception_preserve = True

    def needsFrameExceptionPreversing(self):
        return self.needs_frame_exception_preserve

    def getCodeObjectHandle(self, context):
        provider = self.getParentVariableProvider()

        # TODO: Why do this accessing a node, do this outside.
        from nuitka.codegen.CodeObjectCodes import getCodeObjectHandle

        return getCodeObjectHandle(
            context       = context,
            filename      = self.source_ref.getFilename(),
            var_names     = self.getVarNames(),
            arg_count     = self.getArgumentCount(),
            kw_only_count = self.getKwOnlyParameterCount(),
            line_number   = 0
                              if provider.isPythonModule() else
                            self.source_ref.getLineNumber(),
            code_name     = self.getCodeObjectName(),
            is_generator  = provider.isExpressionFunctionBody() and \
                            provider.isGenerator(),
            is_optimized  = not provider.isPythonModule() and \
                            not provider.isClassDictCreation() and \
                            not context.hasLocalsDict(),
            has_starlist  = self.has_starlist,
            has_stardict  = self.has_stardict
        )

    def computeStatementsSequence(self, constraint_collection):
        new_statements = []

        statements = self.getStatements()

        for count, statement in enumerate(statements):
            # May be frames embedded.
            if statement.isStatementsFrame():
                new_statement = statement.computeStatementsSequence(
                    constraint_collection = constraint_collection
                )
            else:
                new_statement = constraint_collection.onStatement(
                    statement = statement
                )

            if new_statement is not None:
                if new_statement.isStatementsSequence() and \
                   not new_statement.isStatementsFrame():
                    new_statements.extend(new_statement.getStatements())
                else:
                    new_statements.append(new_statement)

                if statement is not statements[-1] and \
                   new_statement.isStatementAborting():
                    constraint_collection.signalChange(
                        "new_statements",
                        statements[count+1].getSourceReference(),
                        "Removed dead statements."
                    )

                    break

        if not new_statements:
            return None

        # Determine statements inside the frame, that need not be in a frame,
        # because they wouldn't raise an exception.
        outside_pre = []
        while new_statements and \
              not new_statements[0].mayRaiseException(BaseException):
            outside_pre.append(new_statements[0])
            del new_statements[0]

        outside_post = []
        while new_statements and \
              not new_statements[-1].mayRaiseException(BaseException):
            outside_post.insert(0, new_statements[-1])
            del new_statements[-1]

        if outside_pre or outside_post:
            from .NodeMakingHelpers import makeStatementsSequenceReplacementNode

            if new_statements:
                self.setStatements(new_statements)

                return makeStatementsSequenceReplacementNode(
                    statements = outside_pre + [self] + \
                                 outside_post,
                    node       = self
                )
            else:
                return makeStatementsSequenceReplacementNode(
                    statements = outside_pre + outside_post,
                    node       = self
                )
        else:
            if statements != new_statements:
                self.setStatements(new_statements)

            return self


class StatementExpressionOnly(StatementChildrenHavingBase):
    kind = "STATEMENT_EXPRESSION_ONLY"

    named_children = ("expression",)

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

    getExpression = StatementChildrenHavingBase.childGetter(
        "expression"
    )

    def computeStatement(self, constraint_collection):
        constraint_collection.onExpression(
            expression = self.getExpression()
        )
        expression = self.getExpression()

        return expression.computeExpressionDrop(
            statement             = self,
            constraint_collection = constraint_collection
        )
