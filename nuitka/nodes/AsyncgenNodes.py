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
""" Nodes for async generator objects and their creations.

Async generator are turned into normal functions that create generator objects,
whose implementation lives here. The creation itself also lives here.

"""

from .ExpressionBases import (
    ExpressionChildHavingBase,
    ExpressionNoSideEffectsMixin,
)
from .FunctionNodes import ExpressionFunctionEntryPointBase


class ExpressionMakeAsyncgenObject(
    ExpressionNoSideEffectsMixin, ExpressionChildHavingBase
):
    kind = "EXPRESSION_MAKE_ASYNCGEN_OBJECT"

    named_child = "asyncgen_ref"

    __slots__ = ("variable_closure_traces",)

    def __init__(self, asyncgen_ref, source_ref):
        assert asyncgen_ref.getFunctionBody().isExpressionAsyncgenObjectBody()

        ExpressionChildHavingBase.__init__(
            self, value=asyncgen_ref, source_ref=source_ref
        )

        self.variable_closure_traces = []

    def getDetailsForDisplay(self):
        return {"asyncgen": self.subnode_asyncgen_ref.getFunctionBody().getCodeName()}

    def computeExpression(self, trace_collection):
        self.variable_closure_traces = []

        for (
            closure_variable
        ) in self.subnode_asyncgen_ref.getFunctionBody().getClosureVariables():
            trace = trace_collection.getVariableCurrentTrace(closure_variable)
            trace.addNameUsage()

            self.variable_closure_traces.append((closure_variable, trace))

        # TODO: Asyncgen body may know something too.
        return self, None, None

    def getClosureVariableVersions(self):
        return self.variable_closure_traces


class ExpressionAsyncgenObjectBody(ExpressionFunctionEntryPointBase):
    kind = "EXPRESSION_ASYNCGEN_OBJECT_BODY"

    __slots__ = ("qualname_setup", "needs_generator_return_exit")

    def __init__(self, provider, name, code_object, flags, auto_release, source_ref):
        ExpressionFunctionEntryPointBase.__init__(
            self,
            provider=provider,
            name=name,
            code_object=code_object,
            code_prefix="asyncgen",
            flags=flags,
            auto_release=auto_release,
            source_ref=source_ref,
        )

        self.needs_generator_return_exit = False

        self.qualname_setup = None

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

    @staticmethod
    def isUnoptimized():
        return False
