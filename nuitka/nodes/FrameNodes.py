#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.PythonVersions import python_version

from .CodeObjectSpecs import CodeObjectSpec
from .FutureSpecs import fromFlags
from .StatementNodes import StatementsSequence


def checkFrameStatements(value):
    """Check that frames statements list value proper.

    Must not be None, must not contain None, and of course only statements
    sequences, or statements, may be empty.
    """

    assert value is not None
    assert None not in value

    for statement in value:
        assert statement.isStatement() or statement.isStatementsFrame(), statement

    return tuple(value)


class StatementsFrameBase(StatementsSequence):
    checkers = {"statements": checkFrameStatements}

    __slots__ = ("guard_mode", "code_object", "needs_frame_exception_preserve")

    def __init__(self, statements, guard_mode, code_object, source_ref):
        StatementsSequence.__init__(self, statements=statements, source_ref=source_ref)

        # TODO: Why not have multiple classes for this.
        self.guard_mode = guard_mode

        self.code_object = code_object

        self.needs_frame_exception_preserve = False

    def isStatementsFrame(self):
        return True

    def getDetails(self):
        result = {"code_object": self.code_object}

        result.update(StatementsSequence.getDetails(self))

        return result

    def getDetailsForDisplay(self):
        result = StatementsSequence.getDetails(self)
        result.update()

        result.update(self.code_object.getDetails())

        return result

    @classmethod
    def fromXML(cls, provider, source_ref, **args):
        code_object_args = {}
        other_args = {}

        for key, value in args.items():
            if key.startswith("co_"):
                code_object_args[key] = value
            elif key == "code_flags":
                code_object_args["future_spec"] = fromFlags(args["code_flags"])
            else:
                other_args[key] = value

        code_object = CodeObjectSpec(**code_object_args)

        return cls(code_object=code_object, source_ref=source_ref, **other_args)

    def getGuardMode(self):
        return self.guard_mode

    def needsExceptionFramePreservation(self):
        if python_version < 0x300:
            return self.guard_mode != "generator"
        else:
            return True

    def getVarNames(self):
        return self.code_object.getVarNames()

    def updateLocalNames(self):
        """For use during variable closure phase. Finalize attributes."""
        provider = self.getParentVariableProvider()

        if not provider.isCompiledPythonModule():
            if (
                provider.isExpressionGeneratorObjectBody()
                or provider.isExpressionCoroutineObjectBody()
                or provider.isExpressionAsyncgenObjectBody()
            ):
                closure_provider = provider.getParentVariableProvider()
            else:
                closure_provider = provider

            if closure_provider.isExpressionFunctionBody():
                closure_variables = closure_provider.getClosureVariables()
            else:
                closure_variables = ()

            self.code_object.updateLocalNames(
                [variable.getName() for variable in provider.getLocalVariables()],
                [
                    variable.getName()
                    for variable in closure_variables
                    if variable.getOwner() is not closure_provider
                ],
            )

        entry_point = provider.getEntryPoint()

        is_optimized = (
            not entry_point.isCompiledPythonModule()
            and not entry_point.isExpressionClassBody()
            and not entry_point.isUnoptimized()
        )

        self.code_object.setFlagIsOptimizedValue(is_optimized)

        new_locals = not provider.isCompiledPythonModule() and (
            python_version < 0x340
            or (not provider.isExpressionClassBody() and not provider.isUnoptimized())
        )

        self.code_object.setFlagNewLocalsValue(new_locals)

    def markAsFrameExceptionPreserving(self):
        self.needs_frame_exception_preserve = True

    def needsFrameExceptionPreserving(self):
        return self.needs_frame_exception_preserve

    def getCodeObject(self):
        return self.code_object

    def computeStatementsSequence(self, trace_collection):
        # The extraction of parts of the frame that can be moved before or after
        # the frame scope, takes it toll to complexity, pylint: disable=too-many-branches
        new_statements = []

        statements = self.subnode_statements

        for count, statement in enumerate(statements):
            # May be frames embedded.
            if statement.isStatementsFrame():
                new_statement = statement.computeStatementsSequence(
                    trace_collection=trace_collection
                )
            else:
                new_statement = trace_collection.onStatement(statement=statement)

            if new_statement is not None:
                if (
                    new_statement.isStatementsSequence()
                    and not new_statement.isStatementsFrame()
                ):
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

                    break

        if not new_statements:
            trace_collection.signalChange(
                "new_statements",
                self.source_ref,
                "Removed empty frame object of '%s'."
                % self.code_object.getCodeObjectName(),
            )

            return None

        # If our statements changed just now, they are not immediately usable,
        # so do this in two steps. Next time we can reduce the frame scope just
        # as well.
        if statements != tuple(new_statements):
            self.setChild("statements", new_statements)
            return self

        # Determine statements inside the frame, that need not be in a frame,
        # because they wouldn't raise an exception.
        outside_pre = []
        while new_statements and not new_statements[0].needsFrame():
            outside_pre.append(new_statements[0])
            del new_statements[0]

        outside_post = []
        while new_statements and not new_statements[-1].needsFrame():
            outside_post.insert(0, new_statements[-1])
            del new_statements[-1]

        if outside_pre or outside_post:
            from .NodeMakingHelpers import (
                makeStatementsSequenceReplacementNode,
            )

            if new_statements:
                self.setChild("statements", new_statements)

                return makeStatementsSequenceReplacementNode(
                    statements=outside_pre + [self] + outside_post, node=self
                )
            else:
                trace_collection.signalChange(
                    "new_statements",
                    self.source_ref,
                    "Removed useless frame object of '%s'."
                    % self.code_object.getCodeObjectName(),
                )

                return makeStatementsSequenceReplacementNode(
                    statements=outside_pre + outside_post, node=self
                )
        else:
            if statements != new_statements:
                self.setChild("statements", new_statements)

            return self


class StatementsFrameModule(StatementsFrameBase):
    kind = "STATEMENTS_FRAME_MODULE"

    def __init__(self, statements, code_object, source_ref):
        StatementsFrameBase.__init__(
            self,
            statements=statements,
            code_object=code_object,
            guard_mode="once",
            source_ref=source_ref,
        )

    @staticmethod
    def hasStructureMember():
        return False


class StatementsFrameFunction(StatementsFrameBase):
    kind = "STATEMENTS_FRAME_FUNCTION"

    def __init__(self, statements, code_object, source_ref):
        StatementsFrameBase.__init__(
            self,
            statements=statements,
            code_object=code_object,
            guard_mode="full",
            source_ref=source_ref,
        )

    @staticmethod
    def hasStructureMember():
        return False


class StatementsFrameGenerator(StatementsFrameBase):
    kind = "STATEMENTS_FRAME_GENERATOR"

    def __init__(self, statements, code_object, source_ref):
        StatementsFrameBase.__init__(
            self,
            statements=statements,
            code_object=code_object,
            guard_mode="generator",
            source_ref=source_ref,
        )

    @staticmethod
    def hasStructureMember():
        return True


class StatementsFrameCoroutine(StatementsFrameBase):
    kind = "STATEMENTS_FRAME_COROUTINE"

    def __init__(self, statements, code_object, source_ref):
        StatementsFrameBase.__init__(
            self,
            statements=statements,
            code_object=code_object,
            guard_mode="generator",
            source_ref=source_ref,
        )

    @staticmethod
    def hasStructureMember():
        return True


class StatementsFrameAsyncgen(StatementsFrameBase):
    kind = "STATEMENTS_FRAME_ASYNCGEN"

    def __init__(self, statements, code_object, source_ref):
        StatementsFrameBase.__init__(
            self,
            statements=statements,
            code_object=code_object,
            guard_mode="generator",
            source_ref=source_ref,
        )

    @staticmethod
    def hasStructureMember():
        return True
