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
""" Globals/locals/singe arg dir nodes

These nodes give access to variables, highly problematic, because using them,
the code may change or access anything about them, so nothing can be trusted
anymore, if we start to not know where their value goes.

The "dir()" call without arguments is reformulated to locals or globals calls.
"""

from .ConstantRefNodes import makeConstantRefNode
from .DictionaryNodes import ExpressionKeyValuePair, ExpressionMakeDict
from .ExpressionBases import ExpressionBase, ExpressionBuiltinSingleArgBase
from .VariableRefNodes import ExpressionTempVariableRef, ExpressionVariableRef


class ExpressionBuiltinGlobals(ExpressionBase):
    kind = "EXPRESSION_BUILTIN_GLOBALS"

    def __init__(self, source_ref):
        ExpressionBase.__init__(self, source_ref=source_ref)

    def finalize(self):
        del self.parent

    def computeExpressionRaw(self, trace_collection):
        return self, None, None

    def mayHaveSideEffects(self):
        return False

    def mayRaiseException(self, exception_type):
        return False


class ExpressionBuiltinLocalsBase(ExpressionBase):
    # Base classes can be abstract, pylint: disable=abstract-method

    __slots__ = ("variable_traces", "locals_scope")

    def __init__(self, locals_scope, source_ref):
        ExpressionBase.__init__(self, source_ref=source_ref)

        self.variable_traces = None
        self.locals_scope = locals_scope

    def finalize(self):
        del self.locals_scope
        del self.variable_traces

    def mayHaveSideEffects(self):
        return False

    def mayRaiseException(self, exception_type):
        return False

    def getVariableTraces(self):
        return self.variable_traces


class ExpressionBuiltinLocalsUpdated(ExpressionBuiltinLocalsBase):
    kind = "EXPRESSION_BUILTIN_LOCALS_UPDATED"

    def __init__(self, locals_scope, source_ref):
        ExpressionBuiltinLocalsBase.__init__(
            self, locals_scope=locals_scope, source_ref=source_ref
        )

        assert locals_scope is not None

    def getLocalsScope(self):
        return self.locals_scope

    def computeExpressionRaw(self, trace_collection):
        # Just inform the collection that all escaped.
        self.variable_traces = trace_collection.onLocalsUsage(
            self.getParentVariableProvider()
        )

        trace_collection.onLocalsDictEscaped(self.locals_scope)

        return self, None, None


class ExpressionBuiltinLocalsRef(ExpressionBuiltinLocalsBase):
    kind = "EXPRESSION_BUILTIN_LOCALS_REF"

    def __init__(self, locals_scope, source_ref):
        ExpressionBuiltinLocalsBase.__init__(
            self, locals_scope=locals_scope, source_ref=source_ref
        )

    def getLocalsScope(self):
        return self.locals_scope

    def computeExpressionRaw(self, trace_collection):
        if self.locals_scope.isMarkedForPropagation():
            result = ExpressionMakeDict(
                pairs=(
                    ExpressionKeyValuePair(
                        key=makeConstantRefNode(
                            constant=variable_name, source_ref=self.source_ref
                        ),
                        value=ExpressionTempVariableRef(
                            variable=variable, source_ref=self.source_ref
                        ),
                        source_ref=self.source_ref,
                    )
                    for variable_name, variable in self.locals_scope.getPropagationVariables().items()
                ),
                source_ref=self.source_ref,
            )

            new_result = result.computeExpressionRaw(trace_collection)

            assert new_result[0] is result

            self.finalize()

            return result, "new_expression", "Propagated locals dictionary reference."

        # Just inform the collection that all escaped unless it is abortative.
        if not self.getParent().isStatementReturn():
            trace_collection.onLocalsUsage(self.getParentVariableProvider())

        return self, None, None


class ExpressionBuiltinLocalsCopy(ExpressionBuiltinLocalsBase):
    kind = "EXPRESSION_BUILTIN_LOCALS_COPY"

    def computeExpressionRaw(self, trace_collection):
        # Just inform the collection that all escaped.

        self.variable_traces = trace_collection.onLocalsUsage(
            self.getParentVariableProvider()
        )

        for variable, variable_trace in self.variable_traces:
            if (
                not variable_trace.mustHaveValue()
                and not variable_trace.mustNotHaveValue()
            ):
                return self, None, None

            # Other locals elsewhere.
            if variable_trace.getNameUsageCount() > 1:
                return self, None, None

        pairs = []
        for variable, variable_trace in self.variable_traces:
            if variable_trace.mustHaveValue():
                pairs.append(
                    ExpressionKeyValuePair(
                        key=makeConstantRefNode(
                            constant=variable.getName(),
                            user_provided=True,
                            source_ref=self.source_ref,
                        ),
                        value=ExpressionVariableRef(
                            variable=variable, source_ref=self.source_ref
                        ),
                        source_ref=self.source_ref,
                    )
                )

        # Locals is sorted of course.
        def _sorted(pairs):
            names = self.getParentVariableProvider().getLocalVariableNames()

            return sorted(
                pairs,
                key=lambda pair: names.index(pair.getKey().getCompileTimeConstant()),
            )

        result = ExpressionMakeDict(pairs=_sorted(pairs), source_ref=self.source_ref)

        return result, "new_expression", "Statically predicted locals dictionary."


class ExpressionBuiltinDir1(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_BUILTIN_DIR1"

    def computeExpression(self, trace_collection):
        # TODO: Quite some cases should be possible to predict and this
        # should be using a slot, with "__dir__" being overloaded or not.

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Any exception may be raised.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None
