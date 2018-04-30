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
""" Globals/locals/dir1 nodes

These nodes give access to variables, highly problematic, because using them,
the code may change or access anything about them, so nothing can be trusted
anymore, if we start to not know where their value goes.

The "dir()" call without arguments is reformulated to locals or globals calls.
"""

from nuitka.PythonVersions import python_version

from .ConstantRefNodes import makeConstantRefNode
from .DictionaryNodes import ExpressionKeyValuePair, ExpressionMakeDict
from .ExpressionBases import ExpressionBase, ExpressionBuiltinSingleArgBase
from .VariableRefNodes import ExpressionVariableRef


class ExpressionBuiltinGlobals(ExpressionBase):
    kind = "EXPRESSION_BUILTIN_GLOBALS"

    def __init__(self, source_ref):
        ExpressionBase.__init__(
            self,
            source_ref = source_ref
        )

    def computeExpressionRaw(self, trace_collection):
        return self, None, None

    def mayHaveSideEffects(self):
        return False

    def mayRaiseException(self, exception_type):
        return False


class ExpressionBuiltinLocalsBase(ExpressionBase):
    # Base classes can be abstract, pylint: disable=abstract-method

    __slots__ = ("variable_versions",)

    def __init__(self, source_ref):
        ExpressionBase.__init__(
            self,
            source_ref = source_ref
        )

        self.variable_versions = None

    def mayHaveSideEffects(self):
        if python_version < 300:
            return False

        provider = self.getParentVariableProvider()

        assert not provider.isCompiledPythonModule()

        # TODO: That's not true.
        return self.getParentVariableProvider().isExpressionClassBody()

    def mayRaiseException(self, exception_type):
        return self.mayHaveSideEffects()

    def getVariableVersions(self):
        return self.variable_versions


class ExpressionBuiltinLocalsUpdated(ExpressionBuiltinLocalsBase):
    kind = "EXPRESSION_BUILTIN_LOCALS_UPDATED"

    __slots__ = ("locals_scope",)

    def __init__(self, locals_scope, source_ref):
        ExpressionBuiltinLocalsBase.__init__(
            self,
            source_ref = source_ref
        )

        self.locals_scope = locals_scope

        assert locals_scope is not None

    def getLocalsScope(self):
        return self.locals_scope

    def computeExpressionRaw(self, trace_collection):
        # Just inform the collection that all escaped.
        self.variable_versions = trace_collection.onLocalsUsage(self.getParentVariableProvider())

        if self.getParent().isStatementReturn():
            result = ExpressionBuiltinLocalsCopy(
                source_ref = self.source_ref
            )

            return result, "new_expression", "Locals does not escape, no write back needed."

        trace_collection.onLocalsDictEscaped()

        return self, None, None


class ExpressionBuiltinLocalsRef(ExpressionBuiltinLocalsBase):
    kind = "EXPRESSION_BUILTIN_LOCALS_REF"

    __slots__ = ("locals_scope",)

    def __init__(self, locals_scope, source_ref):
        ExpressionBuiltinLocalsBase.__init__(
            self,
            source_ref = source_ref
        )

        self.locals_scope = locals_scope

    def getLocalsScope(self):
        return self.locals_scope

    def computeExpressionRaw(self, trace_collection):
        # Just inform the collection that all escaped.

        self.variable_versions = trace_collection.onLocalsUsage(self.getParentVariableProvider())
        return self, None, None


class ExpressionBuiltinLocalsCopy(ExpressionBuiltinLocalsBase):
    kind = "EXPRESSION_BUILTIN_LOCALS_COPY"

    def computeExpressionRaw(self, trace_collection):
        # Just inform the collection that all escaped.

        self.variable_versions = trace_collection.onLocalsUsage(self.getParentVariableProvider())

        # TODO: Remove later.
        assert not self.getParentVariableProvider().isExpressionClassBody()

        for variable, version in self.variable_versions:
            trace = trace_collection.getVariableTrace(variable, version)

            if not trace.mustHaveValue() and not trace.mustNotHaveValue():
                return self, None, None

            # Other locals elsewhere.
            if trace.getNameUsageCount() > 1:
                return self, None, None

        pairs = []
        for variable, version in self.variable_versions:
            trace = trace_collection.getVariableTrace(variable, version)

            if trace.mustHaveValue():
                pairs.append(
                    ExpressionKeyValuePair(
                        key        = makeConstantRefNode(
                            constant      = variable.getName(),
                            user_provided = True,
                            source_ref    = self.source_ref
                        ),
                        value      = ExpressionVariableRef(
                            variable   = variable,
                            source_ref = self.source_ref
                        ),
                        source_ref = self.source_ref
                    )
                )

        # Locals is sorted of course.
        def _sorted(pairs):
            names = self.getParentVariableProvider().getLocalVariableNames()

            return sorted(
                pairs,
                key = lambda pair: names.index(
                    pair.getKey().getCompileTimeConstant()
                ),
            )

        result = ExpressionMakeDict(
            pairs      = _sorted(pairs),
            source_ref = self.source_ref
        )

        return result, "new_expression", "Statically predicted locals dictionary."



class ExpressionBuiltinDir1(ExpressionBuiltinSingleArgBase):
    kind = "EXPRESSION_BUILTIN_DIR1"

    def computeExpression(self, trace_collection):
        # TODO: Quite some cases should be possible to predict.
        return self, None, None
