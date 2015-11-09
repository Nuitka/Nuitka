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
""" Frame nodes.

The frame attaches name and other frame properties to a scope, where it is
optional. For use in tracebacks, their created frame objects, potentially
cached are essential.

Otherwise, they are similar to statement sequences, so they inherit from
them.

"""

from nuitka.utils.Utils import python_version

from .StatementNodes import StatementsSequence


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
    # Frames got many details to store, pylint: disable=R0902

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

        self.var_names = tuple(var_names)
        self.code_name = code_name

        self.kw_only_count = kw_only_count
        self.arg_count = arg_count

        self.guard_mode = guard_mode

        self.has_starlist = has_starlist
        self.has_stardict = has_stardict

        self.needs_frame_exception_preserve = False

    def getDetails(self):
        result = {
            "guard_mode" : self.guard_mode,
            "code_name"  : self.code_name,
            "var_names"  : self.var_names,
            "arg_count"  : self.arg_count,
            "kw_only_count" : self.kw_only_count,
            "has_starlist" : self.has_starlist,
            "has_stardict" : self.has_stardict,
        }

        if python_version >= 300:
            result["kw_only_count"] = self.kw_only_count

        result.update(StatementsSequence.getDetails(self))

        return result

    def getGuardMode(self):
        return self.guard_mode

    def needsExceptionFramePreservation(self):
        if python_version < 300:
            preserving = ("full", "once")
        else:
            preserving = ("full", "once", "generator")

        return self.guard_mode in preserving

    def getVarNames(self):
        return self.var_names

    def updateVarNames(self):
        """ For use during variable closure phase.

        """
        provider = self.getParentVariableProvider()

        # TODO: Bad for in-lining of these.
        if provider.isExpressionFunctionBody():
            var_names = provider.getParameters().getCoArgNames()

            # Add names of local variables too.
            var_names += [
                local_variable.getName()
                for local_variable in
                provider.getLocalVariables()
                if not local_variable.isParameterVariable()
            ]

            self.var_names = tuple(var_names)

    def getCodeObjectName(self):
        return self.code_name

    def getKwOnlyParameterCount(self):
        return self.kw_only_count

    def getArgumentCount(self):
        return self.arg_count

    def markAsFrameExceptionPreserving(self):
        self.needs_frame_exception_preserve = True

    def needsFrameExceptionPreserving(self):
        return self.needs_frame_exception_preserve

    def getCodeObjectHandle(self, context):
        provider = self.getParentVariableProvider()

        # TODO: Why do this accessing a node, do this outside.
        return context.getCodeObjectHandle(
            filename      = self.getParentModule().getRunTimeFilename(),
            var_names     = self.getVarNames(),
            arg_count     = self.getArgumentCount(),
            kw_only_count = self.getKwOnlyParameterCount(),
            line_number   = 0
                              if provider.isCompiledPythonModule() else
                            self.source_ref.getLineNumber(),
            code_name     = self.getCodeObjectName(),
            is_generator  = provider.isExpressionFunctionBody() and \
                            provider.isGenerator(),
            is_optimized  = not provider.isCompiledPythonModule() and \
                            not provider.isExpressionClassBody() and \
                            not provider.hasLocalsDict(),
            has_starlist  = self.has_starlist,
            has_stardict  = self.has_stardict,
            has_closure   = provider.isExpressionFunctionBody() and \
                            provider.getClosureVariables() != () and \
                            not provider.isExpressionClassBody(),
            future_flags  = provider.getSourceReference().getFutureSpec().\
                              asFlags()
        )

    def computeStatementsSequence(self, constraint_collection):
        # The extraction of parts of the frame that can be moved before or after
        # the frame scope, takes it toll to complexity, pylint: disable=R0912
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

        # If our statements changed just now, they are not immediately usable,
        # so do this in two steps. Next time we can reduce the frame scope just
        # as well.
        if statements != tuple(new_statements):
            self.setStatements(new_statements)
            return self

        # Determine statements inside the frame, that need not be in a frame,
        # because they wouldn't raise an exception.
        outside_pre = []
        while new_statements and \
              not new_statements[0].needsFrame():
            outside_pre.append(new_statements[0])
            del new_statements[0]

        outside_post = []
        while new_statements and \
              not new_statements[-1].needsFrame():
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
                constraint_collection.signalChange(
                    "new_statements",
                    self.getSourceReference(),
                    "Removed useless frame object of '%s'." % self.getCodeObjectName()
                )

                return makeStatementsSequenceReplacementNode(
                    statements = outside_pre + outside_post,
                    node       = self
                )
        else:
            if statements != new_statements:
                self.setStatements(new_statements)

            return self
