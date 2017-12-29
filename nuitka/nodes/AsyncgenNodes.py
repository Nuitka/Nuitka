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
""" Nodes for async generator objects and their creations.

Async generator are turned into normal functions that create generator objects,
whose implementation lives here. The creation itself also lives here.

"""

from .Checkers import checkStatementsSequenceOrNone
from .ExpressionBases import ExpressionChildrenHavingBase
from .FunctionNodes import ExpressionFunctionEntryPointBase


class ExpressionMakeAsyncgenObject(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_MAKE_ASYNCGEN_OBJECT"

    named_children = (
        "asyncgen_ref",
    )

    getAsyncgenRef = ExpressionChildrenHavingBase.childGetter("asyncgen_ref")

    def __init__(self, asyncgen_ref, code_object, source_ref):
        assert asyncgen_ref.getFunctionBody().isExpressionAsyncgenObjectBody()

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "asyncgen_ref" : asyncgen_ref,
            },
            source_ref = source_ref
        )

        self.code_object = code_object

        self.variable_closure_traces = []

    def getDetails(self):
        return {
            "code_object" : self.code_object
        }

    def getCodeObject(self):
        return self.code_object

    def getDetailsForDisplay(self):
        return {
            "asyncgen" : self.getAsyncgenRef().getFunctionBody().getCodeName()
        }

    def computeExpression(self, trace_collection):
        self.variable_closure_traces = []

        for closure_variable in self.getAsyncgenRef().getFunctionBody().getClosureVariables():
            trace = trace_collection.getVariableCurrentTrace(closure_variable)
            trace.addClosureUsage()

            self.variable_closure_traces.append(trace)

        # TODO: Asyncgen body may know something too.
        return self, None, None

    def mayRaiseException(self, exception_type):
        return False

    def mayHaveSideEffects(self):
        return False

    def getClosureVariableVersions(self):
        return [
            (trace.getVariable(), trace.getVersion())
            for trace in self.variable_closure_traces
        ]


class ExpressionAsyncgenObjectBody(ExpressionFunctionEntryPointBase):
    kind = "EXPRESSION_ASYNCGEN_OBJECT_BODY"

    named_children = (
        "body",
    )

    checkers = {
        # TODO: Is "None" really an allowed value.
        "body" : checkStatementsSequenceOrNone
    }

    qualname_setup = None

    def __init__(self, provider, name, flags, source_ref):
        ExpressionFunctionEntryPointBase.__init__(
            self,
            provider    = provider,
            name        = name,
            code_prefix = "asyncgen",
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
