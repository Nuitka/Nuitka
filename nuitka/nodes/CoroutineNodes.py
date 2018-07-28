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
""" Nodes for coroutine objects and their creations.

Coroutines are turned into normal functions that create generator objects,
whose implementation lives here. The creation itself also lives here.

"""

from .ExpressionBases import ExpressionChildrenHavingBase
from .FunctionNodes import ExpressionFunctionEntryPointBase


class ExpressionMakeCoroutineObject(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_MAKE_COROUTINE_OBJECT"

    named_children = (
        "coroutine_ref",
    )

    getCoroutineRef = ExpressionChildrenHavingBase.childGetter("coroutine_ref")

    def __init__(self, coroutine_ref, code_object, source_ref):
        assert coroutine_ref.getFunctionBody().isExpressionCoroutineObjectBody()

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "coroutine_ref" : coroutine_ref,
            },
            source_ref = source_ref
        )

        self.code_object = code_object

        self.variable_closure_traces = None

    def getDetails(self):
        return {
            "code_object" : self.code_object
        }

    def getCodeObject(self):
        return self.code_object

    def getDetailsForDisplay(self):
        return {
            "coroutine" : self.getCoroutineRef().getFunctionBody().getCodeName()
        }

    def computeExpression(self, trace_collection):
        self.variable_closure_traces = []

        for closure_variable in self.getCoroutineRef().getFunctionBody().getClosureVariables():
            trace = trace_collection.getVariableCurrentTrace(closure_variable)
            trace.addClosureUsage()

            self.variable_closure_traces.append(
                (closure_variable, trace)
            )

        # TODO: Coroutine body may know something too.
        return self, None, None

    def mayRaiseException(self, exception_type):
        return False

    def mayHaveSideEffects(self):
        return False

    def getClosureVariableVersions(self):
        return self.variable_closure_traces


class ExpressionCoroutineObjectBody(ExpressionFunctionEntryPointBase):
    kind = "EXPRESSION_COROUTINE_OBJECT_BODY"

    qualname_setup = None

    def __init__(self, provider, name, flags, source_ref):
        ExpressionFunctionEntryPointBase.__init__(
            self,
            provider    = provider,
            name        = name,
            code_prefix = "coroutine",
            flags       = flags,
            source_ref  = source_ref
        )

        self.needs_generator_return_exit = False

    def getFunctionName(self):
        return self.name

    def markAsNeedsGeneratorReturnHandling(self, value):
        self.needs_generator_return_exit = max(
            self.needs_generator_return_exit,
            value
        )

    def needsGeneratorReturnHandling(self):
        return self.needs_generator_return_exit == 2

    def needsGeneratorReturnExit(self):
        return bool(self.needs_generator_return_exit)

    @staticmethod
    def needsCreation():
        return False

    @staticmethod
    def isUnoptimized():
        return False


class ExpressionAsyncWait(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_ASYNC_WAIT"

    named_children = ("expression",)

    def __init__(self, expression, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "expression" : expression
            },
            source_ref = source_ref
        )

        self.exception_preserving = False

    @staticmethod
    def isExpressionAsyncWait():
        return True

    def markAsExceptionPreserving(self):
        self.exception_preserving = True

    def isExceptionPreserving(self):
        return self.exception_preserving

    def computeExpression(self, trace_collection):
        # TODO: Might be predictable based awaitable analysis or for constants.
        return self, None, None

    getValue = ExpressionChildrenHavingBase.childGetter("expression")


class ExpressionAsyncWaitEnter(ExpressionAsyncWait):
    kind = "EXPRESSION_ASYNC_WAIT_ENTER"


class ExpressionAsyncWaitExit(ExpressionAsyncWait):
    kind = "EXPRESSION_ASYNC_WAIT_EXIT"
