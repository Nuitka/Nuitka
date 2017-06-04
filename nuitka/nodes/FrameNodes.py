#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.nodes.CodeObjectSpecs import CodeObjectSpec
from nuitka.PythonVersions import python_version

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
    kind = "STATEMENTS_FRAME"

    checkers = {
        "statements" : checkFrameStatements
    }

    def __init__(self, statements, guard_mode, code_object, source_ref):
        StatementsSequence.__init__(
            self,
            statements = statements,
            source_ref = source_ref
        )

        # TODO: Why not have multiple classes for this.
        self.guard_mode = guard_mode

        self.code_object = code_object

        self.needs_frame_exception_preserve = False

    def getDetails(self):
        result = {
            "guard_mode"  : self.guard_mode,
            "code_object" : self.code_object
        }

        result.update(StatementsSequence.getDetails(self))

        return result

    def getDetailsForDisplay(self):
        result = {
            "guard_mode"  : self.guard_mode,
        }

        result.update(StatementsSequence.getDetails(self))

        result.update(self.code_object.getDetails())

        return result

    @classmethod
    def fromXML(cls, provider, source_ref, **args):
        code_object_args = {}
        other_args = {}

        for key, value in args.items():
            if key.startswith("co_"):
                code_object_args[key] = value
            else:
                other_args[key] = value

        code_object = CodeObjectSpec(**code_object_args)

        return cls(
            code_object = code_object,
            source_ref  = source_ref,
            **other_args
        )

    def getGuardMode(self):
        return self.guard_mode

    def needsExceptionFramePreservation(self):
        if python_version < 300:
            preserving = ("full", "once")
        else:
            preserving = ("full", "once", "generator")

        return self.guard_mode in preserving

    def getVarNames(self):
        return self.code_object.getVarNames()

    def updateLocalNames(self):
        """ For use during variable closure phase.

        """
        provider = self.getParentVariableProvider()

        if not provider.isCompiledPythonModule() and \
           self.code_object is not None:
            self.code_object.updateLocalNames(
                [
                    variable.getName() for
                    variable in
                    provider.getLocalVariables()
                ]
            )

    def markAsFrameExceptionPreserving(self):
        self.needs_frame_exception_preserve = True

    def needsFrameExceptionPreserving(self):
        return self.needs_frame_exception_preserve

    def getCodeObject(self):
        return self.code_object

    def getCodeObjectHandle(self, context):
        provider = self.getParentVariableProvider()

        is_optimized = not provider.isCompiledPythonModule() and \
                       not provider.isExpressionClassBody() and \
                       not provider.hasLocalsDict()

        new_locals = not provider.isCompiledPythonModule() and \
                     (python_version < 340 or (
                     not provider.isExpressionClassBody() and \
                     not provider.hasLocalsDict()))

        if provider.isCompiledPythonModule():
            line_number = 1
        else:
            line_number = self.source_ref.getLineNumber()

        if provider.isExpressionGeneratorObjectBody() or \
           provider.isExpressionCoroutineObjectBody() or \
           provider.isExpressionAsyncgenObjectBody():
            closure_provider = provider.getParentVariableProvider()
        else:
            closure_provider = provider

        parent_module = self.getParentModule()

        # TODO: Why do this accessing a node, do this outside.
        return context.getCodeObjectHandle(
            code_object  = self.code_object,
            filename     = parent_module.getRunTimeFilename(),
            line_number  = line_number,
            is_optimized = is_optimized,
            new_locals   = new_locals,
            has_closure  = closure_provider.isExpressionFunctionBody() and \
                           closure_provider.getClosureVariables() != () and \
                           not closure_provider.isExpressionClassBody(),
            future_flags = parent_module.getFutureSpec().asFlags()
        )

    def computeStatementsSequence(self, trace_collection):
        # The extraction of parts of the frame that can be moved before or after
        # the frame scope, takes it toll to complexity, pylint: disable=too-many-branches
        new_statements = []

        statements = self.getStatements()

        for count, statement in enumerate(statements):
            # May be frames embedded.
            if statement.isStatementsFrame():
                new_statement = statement.computeStatementsSequence(
                    trace_collection = trace_collection
                )
            else:
                new_statement = trace_collection.onStatement(
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
                    trace_collection.signalChange(
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
                trace_collection.signalChange(
                    "new_statements",
                    self.getSourceReference(),
                    "Removed useless frame object of '%s'." % self.code_object.getCodeObjectName()
                )

                return makeStatementsSequenceReplacementNode(
                    statements = outside_pre + outside_post,
                    node       = self
                )
        else:
            if statements != new_statements:
                self.setStatements(new_statements)

            return self
