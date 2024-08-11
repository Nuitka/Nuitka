#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Nodes for coroutine objects and their creations.

Coroutines are turned into normal functions that create generator objects,
whose implementation lives here. The creation itself also lives here.

"""

from .ChildrenHavingMixins import (
    ChildHavingCoroutineRefMixin,
    ChildHavingExpressionMixin,
)
from .ExpressionBases import ExpressionBase, ExpressionNoSideEffectsMixin
from .FunctionNodes import ExpressionFunctionEntryPointBase


class ExpressionMakeCoroutineObject(
    ExpressionNoSideEffectsMixin, ChildHavingCoroutineRefMixin, ExpressionBase
):
    kind = "EXPRESSION_MAKE_COROUTINE_OBJECT"

    named_children = ("coroutine_ref",)

    __slots__ = ("variable_closure_traces",)

    def __init__(self, coroutine_ref, source_ref):
        assert coroutine_ref.getFunctionBody().isExpressionCoroutineObjectBody()

        ChildHavingCoroutineRefMixin.__init__(self, coroutine_ref=coroutine_ref)

        ExpressionBase.__init__(self, source_ref)

        self.variable_closure_traces = None

    def getDetailsForDisplay(self):
        return {"coroutine": self.subnode_coroutine_ref.getFunctionBody().getCodeName()}

    def computeExpression(self, trace_collection):
        self.variable_closure_traces = []

        for (
            closure_variable
        ) in self.subnode_coroutine_ref.getFunctionBody().getClosureVariables():
            trace = trace_collection.getVariableCurrentTrace(closure_variable)
            trace.addNameUsage()

            self.variable_closure_traces.append((closure_variable, trace))

        # TODO: Coroutine body may know something too.
        return self, None, None

    def getClosureVariableVersions(self):
        return self.variable_closure_traces


class ExpressionCoroutineObjectBody(ExpressionFunctionEntryPointBase):
    kind = "EXPRESSION_COROUTINE_OBJECT_BODY"

    __slots__ = ("qualname_setup", "needs_generator_return_exit")

    def __init__(self, provider, name, code_object, flags, auto_release, source_ref):
        ExpressionFunctionEntryPointBase.__init__(
            self,
            provider=provider,
            name=name,
            code_object=code_object,
            code_prefix="coroutine",
            flags=flags,
            auto_release=auto_release,
            source_ref=source_ref,
        )

        self.needs_generator_return_exit = False

        self.qualname_setup = None

    def getFunctionName(self):
        return self.name

    def markAsNeedsGeneratorReturnHandling(self):
        self.needs_generator_return_exit = True

    def needsGeneratorReturnExit(self):
        return self.needs_generator_return_exit

    @staticmethod
    def needsCreation():
        return False

    @staticmethod
    def isUnoptimized():
        return False


class ExpressionAsyncWait(ChildHavingExpressionMixin, ExpressionBase):
    kind = "EXPRESSION_ASYNC_WAIT"

    named_children = ("expression",)

    __slots__ = ("exception_preserving",)

    def __init__(self, expression, source_ref):
        ChildHavingExpressionMixin.__init__(self, expression=expression)

        ExpressionBase.__init__(self, source_ref)

        self.exception_preserving = False

    @staticmethod
    def isExpressionAsyncWait():
        return True

    def computeExpression(self, trace_collection):
        # TODO: Might be predictable based awaitable analysis or for constants.

        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


class ExpressionAsyncWaitEnter(ExpressionAsyncWait):
    kind = "EXPRESSION_ASYNC_WAIT_ENTER"


class ExpressionAsyncWaitExit(ExpressionAsyncWait):
    kind = "EXPRESSION_ASYNC_WAIT_EXIT"


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
