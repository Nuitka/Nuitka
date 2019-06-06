#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Nodes for generator objects and their creations.

Generators are turned into normal functions that create generator objects,
whose implementation lives here. The creation itself also lives here.

"""

from nuitka.PythonVersions import python_version

from .ExpressionBases import ExpressionChildrenHavingBase
from .FunctionNodes import ExpressionFunctionEntryPointBase
from .IndicatorMixins import MarkUnoptimizedFunctionIndicatorMixin
from .ReturnNodes import StatementReturn, StatementReturnNone


class ExpressionMakeGeneratorObject(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_MAKE_GENERATOR_OBJECT"

    named_children = ("generator_ref",)

    getGeneratorRef = ExpressionChildrenHavingBase.childGetter("generator_ref")

    def __init__(self, generator_ref, source_ref):
        assert (
            generator_ref.getFunctionBody().isExpressionGeneratorObjectBody()
        ), generator_ref

        ExpressionChildrenHavingBase.__init__(
            self, values={"generator_ref": generator_ref}, source_ref=source_ref
        )

        self.variable_closure_traces = None

    def getCodeObject(self):
        return self.code_object

    def computeExpression(self, trace_collection):
        self.variable_closure_traces = []

        for closure_variable in (
            self.getGeneratorRef().getFunctionBody().getClosureVariables()
        ):
            trace = trace_collection.getVariableCurrentTrace(closure_variable)
            trace.addClosureUsage()

            self.variable_closure_traces.append((closure_variable, trace))

        # TODO: Generator body may know something too.
        return self, None, None

    def mayRaiseException(self, exception_type):
        return False

    def mayHaveSideEffects(self):
        return False

    def getClosureVariableVersions(self):
        return self.variable_closure_traces


class ExpressionGeneratorObjectBody(
    MarkUnoptimizedFunctionIndicatorMixin, ExpressionFunctionEntryPointBase
):
    kind = "EXPRESSION_GENERATOR_OBJECT_BODY"

    if python_version >= 340:
        qualname_setup = None

    def __init__(self, provider, name, code_object, flags, source_ref):
        ExpressionFunctionEntryPointBase.__init__(
            self,
            provider=provider,
            name=name,
            code_object=code_object,
            code_prefix="genexpr" if name == "<genexpr>" else "genobj",
            flags=flags,
            source_ref=source_ref,
        )

        MarkUnoptimizedFunctionIndicatorMixin.__init__(self, flags)

        self.needs_generator_return_exit = False

        self.trace_collection = None

    def getFunctionName(self):
        return self.name

    def markAsNeedsGeneratorReturnHandling(self, value):
        self.needs_generator_return_exit = max(self.needs_generator_return_exit, value)

    def needsGeneratorReturnHandling(self):
        return self.needs_generator_return_exit == 2

    def needsGeneratorReturnExit(self):
        return bool(self.needs_generator_return_exit)

    @staticmethod
    def needsCreation():
        return False


class StatementGeneratorReturn(StatementReturn):
    kind = "STATEMENT_GENERATOR_RETURN"

    def __init__(self, expression, source_ref):
        StatementReturn.__init__(self, expression=expression, source_ref=source_ref)

    def computeStatement(self, trace_collection):
        trace_collection.onExpression(self.getExpression())
        expression = self.getExpression()

        if expression.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        if expression.willRaiseException(BaseException):
            from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

            result = makeStatementExpressionOnlyReplacementNode(
                expression=expression, node=self
            )

            return (
                result,
                "new_raise",
                """\
Return statement raises in returned expression, removed return.""",
            )

        trace_collection.onFunctionReturn()

        if expression.isExpressionConstantNoneRef():
            result = StatementGeneratorReturnNone(source_ref=self.source_ref)

            return (
                result,
                "new_statements",
                """\
Generator return value is always None.""",
            )

        return self, None, None

    @staticmethod
    def isStatementGeneratorReturn():
        return True

    def getStatementNiceName(self):
        return "generator return statement"


class StatementGeneratorReturnNone(StatementReturnNone):
    kind = "STATEMENT_GENERATOR_RETURN_NONE"

    __slots__ = ()

    def __init__(self, source_ref):
        StatementReturnNone.__init__(self, source_ref=source_ref)

    @staticmethod
    def isStatementGeneratorReturn():
        return True

    def getStatementNiceName(self):
        return "generator return statement"
