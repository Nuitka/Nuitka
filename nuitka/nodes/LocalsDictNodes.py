#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Nodes that deal with locals, as dict or mapping.

The mapping types can be optimized into dict types, and the ones with
fallback can be optimized to no fallback variants.

"""

from nuitka.optimizations.TraceCollections import TraceCollectionBranch
from nuitka.PythonVersions import python_version
from nuitka.tree.TreeHelpers import makeStatementsSequence

from .ChildrenHavingMixins import ChildHavingFallbackMixin
from .ConditionalNodes import ExpressionConditional
from .ExpressionBases import ExpressionBase
from .NodeBases import StatementBase
from .StatementBasesGenerated import (
    StatementLocalsDictOperationSetBase,
    StatementSetLocalsBase,
    StatementSetLocalsDictionaryBase,
)
from .VariableAssignNodes import makeStatementAssignmentVariable
from .VariableDelNodes import makeStatementDelVariable
from .VariableRefNodes import ExpressionTempVariableRef
from .VariableReleaseNodes import makeStatementReleaseVariable


class ExpressionLocalsVariableRefOrFallback(ChildHavingFallbackMixin, ExpressionBase):
    kind = "EXPRESSION_LOCALS_VARIABLE_REF_OR_FALLBACK"

    named_children = ("fallback",)

    __slots__ = ("locals_scope", "variable", "variable_trace")

    def __init__(self, locals_scope, variable_name, fallback, source_ref):
        assert locals_scope is not None

        ChildHavingFallbackMixin.__init__(self, fallback=fallback)

        ExpressionBase.__init__(self, source_ref)

        self.locals_scope = locals_scope
        self.variable = locals_scope.getLocalsDictVariable(variable_name)

        self.variable_trace = None

    def getDetails(self):
        return {
            "locals_scope": self.locals_scope,
            "variable_name": self.getVariableName(),
        }

    def getVariableName(self):
        return self.variable.getName()

    def getLocalsDictScope(self):
        return self.locals_scope

    def computeExpressionRaw(self, trace_collection):
        self.variable_trace = trace_collection.getVariableCurrentTrace(
            variable=self.variable
        )

        replacement = self.variable_trace.getReplacementNode(self)

        if replacement is not None:
            trace_collection.signalChange(
                "new_expression",
                self.source_ref,
                "Value propagated for '%s' from '%s'."
                % (
                    self.variable.getName(),
                    replacement.getSourceReference().getAsString(),
                ),
            )

            # Need to compute the replacement still.
            return replacement.computeExpressionRaw(trace_collection)

        # TODO: Split exec locals variable references out to distinct node type.
        no_exec = not self.locals_scope.isUnoptimizedFunctionScope()

        # if we can be sure if doesn't have a value set, go to the fallback directly.
        if no_exec and self.variable_trace.mustNotHaveValue():
            return trace_collection.computedExpressionResultRaw(
                self.subnode_fallback,
                "new_expression",
                "Name '%s' cannot be in locals dict." % self.variable.getName(),
            )

        # If we cannot be sure if the value is set, then we need the fallback,
        # otherwise we could remove it simply.
        if no_exec and self.variable_trace.mustHaveValue():
            trace_collection.signalChange(
                "new_expression",
                self.source_ref,
                "Name '%s' must be in locals dict." % self.variable.getName(),
            )

            result = ExpressionLocalsVariableRef(
                locals_scope=self.locals_scope,
                variable_name=self.variable.getName(),
                source_ref=self.source_ref,
            )

            # Need to compute the replacement still.
            return result.computeExpressionRaw(trace_collection)

        trace_collection.onExceptionRaiseExit(BaseException)

        branch_fallback = TraceCollectionBranch(
            parent=trace_collection, name="fallback node usage"
        )

        if (
            self.variable_trace.isUnknownTrace()
            and self.subnode_fallback.isExpressionVariableRef()
        ):
            fallback_variable_trace = self.subnode_fallback.variable_trace

            if fallback_variable_trace is not None:
                trusted_node = (
                    self.subnode_fallback.variable_trace.getAttributeNodeVeryTrusted()
                )

                if trusted_node is not None:
                    return trace_collection.computedExpressionResultRaw(
                        expression=self.subnode_fallback,
                        change_tags="var_usage",
                        change_desc="Hard value referenced in class not considering class dictionary.",
                    )

        branch_fallback.onExpression(self.subnode_fallback)
        trace_collection.mergeBranches(branch_fallback, None)

        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        trace_collection.onControlFlowEscape(self)

        if (
            self.variable.getName()
            in ("dir", "eval", "exec", "execfile", "locals", "vars")
            and self.subnode_fallback.isExpressionVariableRef()
            and self.subnode_fallback.getVariable().isIncompleteModuleVariable()
        ):
            # Just inform the collection that all escaped.
            trace_collection.onLocalsUsage(self.getLocalsDictScope())

        if (
            self.subnode_fallback.isExpressionBuiltinRef()
            or self.subnode_fallback.isExpressionConstantTypeRef()
        ):
            variable_name = self.variable.getName()

            # Create a cloned node with the locals variable.
            call_node_clone = call_node.makeClone()
            call_node_clone.setChildCalled(
                ExpressionLocalsVariableRef(
                    locals_scope=self.locals_scope,
                    variable_name=variable_name,
                    source_ref=self.source_ref,
                )
            )

            # Make the original one for the fallback
            call_node = call_node.makeCloneShallow()
            call_node.setChildCalled(self.subnode_fallback)

            result = ExpressionConditional(
                condition=ExpressionLocalsVariableCheck(
                    locals_scope=self.locals_scope,
                    variable_name=variable_name,
                    source_ref=self.source_ref,
                ),
                expression_yes=call_node_clone,
                expression_no=call_node,
                source_ref=self.source_ref,
            )

            return (
                result,
                "new_expression",
                "Moved call of uncertain dict variable '%s' to inside." % variable_name,
            )

        return call_node, None, None

    # TODO: Specialize for Python3 maybe to save attribute for Python2.
    may_raise_access = python_version >= 0x300

    def mayRaiseException(self, exception_type):
        if self.may_raise_access and self.locals_scope.hasShapeDictionaryExact():
            return True

        return self.subnode_fallback.mayRaiseException(exception_type)


# TODO: Why is this unused.
class ExpressionLocalsMappingVariableRefOrFallback(
    ExpressionLocalsVariableRefOrFallback
):
    kind = "EXPRESSION_LOCALS_MAPPING_VARIABLE_REF_OR_FALLBACK"


class ExpressionLocalsVariableRef(ExpressionBase):
    kind = "EXPRESSION_LOCALS_VARIABLE_REF"

    __slots__ = "variable", "locals_scope", "variable_trace"

    def __init__(self, locals_scope, variable_name, source_ref):

        ExpressionBase.__init__(self, source_ref)

        self.locals_scope = locals_scope
        self.variable = locals_scope.getLocalsDictVariable(variable_name)

        self.variable_trace = None

    def finalize(self):
        del self.parent
        del self.locals_scope
        del self.variable

    def getDetails(self):
        return {
            "variable_name": self.getVariableName(),
            "locals_scope": self.locals_scope,
        }

    def getDetailsForDisplay(self):
        return {"variable_name": self.getVariableName()}

    def getVariableName(self):
        return self.variable.getName()

    def getLocalsDictScope(self):
        return self.locals_scope

    def computeExpressionRaw(self, trace_collection):
        if self.locals_scope.isMarkedForPropagation():
            variable_name = self.getVariableName()

            variable = self.locals_scope.allocateTempReplacementVariable(
                trace_collection=trace_collection, variable_name=variable_name
            )

            result = ExpressionTempVariableRef(
                variable=variable, source_ref=self.source_ref
            )
            result.parent = self.parent

            self.finalize()

            new_result = result.computeExpressionRaw(trace_collection)

            if new_result[0] is not result:
                assert False, (new_result, result)

            return (
                result,
                "new_expression",
                "Replaced dictionary ref with temporary variable.",
            )

        self.variable_trace = trace_collection.getVariableCurrentTrace(
            variable=self.variable
        )

        replacement = self.variable_trace.getReplacementNode(self)

        if replacement is not None:
            trace_collection.signalChange(
                "new_expression",
                self.source_ref,
                "Value propagated for '%s' from '%s'."
                % (
                    self.variable.getName(),
                    replacement.getSourceReference().getAsString(),
                ),
            )

            # Need to compute the replacement still.
            return replacement.computeExpressionRaw(trace_collection)

        if not self.variable_trace.mustHaveValue():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        trace_collection.onControlFlowEscape(self)
        return call_node, None, None

    def mayRaiseException(self, exception_type):
        return self.variable_trace is None or not self.variable_trace.mustHaveValue()


class ExpressionLocalsVariableCheck(ExpressionBase):
    kind = "EXPRESSION_LOCALS_VARIABLE_CHECK"

    __slots__ = "variable_name", "locals_scope"

    def __init__(self, locals_scope, variable_name, source_ref):
        self.variable_name = variable_name

        ExpressionBase.__init__(self, source_ref)

        self.locals_scope = locals_scope

    def finalize(self):
        del self.parent
        del self.locals_scope

    def getDetails(self):
        return {"locals_scope": self.locals_scope, "variable_name": self.variable_name}

    def getVariableName(self):
        return self.variable_name

    def getLocalsDictScope(self):
        return self.locals_scope

    def computeExpressionRaw(self, trace_collection):
        assert not self.locals_scope.isMarkedForPropagation()
        return self, None, None


class StatementLocalsDictOperationSet(StatementLocalsDictOperationSetBase):
    kind = "STATEMENT_LOCALS_DICT_OPERATION_SET"

    named_children = ("source",)
    node_attributes = ("locals_scope", "variable_name")
    auto_compute_handling = "post_init"

    __slots__ = ("variable", "variable_version", "variable_trace")

    # TODO: Specialize for Python3 maybe to save attribute for Python2.
    may_raise_set = python_version >= 0x300

    # false alarm due to post_init, pylint: disable=attribute-defined-outside-init

    def postInitNode(self):
        self.variable = self.locals_scope.getLocalsDictVariable(
            variable_name=self.variable_name
        )
        self.variable_version = self.variable.allocateTargetNumber()
        self.variable_trace = None

    def finalize(self):
        del self.parent
        del self.locals_scope
        del self.variable_trace

    def getDetails(self):
        return {
            "locals_scope": self.locals_scope,
            "variable_name": self.getVariableName(),
        }

    def getVariableName(self):
        return self.variable.getName()

    def getLocalsDictScope(self):
        return self.locals_scope

    def getTypeShape(self):
        return self.locals_scope.getMappingValueShape(self.variable)

    def computeStatement(self, trace_collection):
        if self.locals_scope.isMarkedForPropagation():
            variable = self.locals_scope.allocateTempReplacementVariable(
                trace_collection=trace_collection, variable_name=self.variable_name
            )

            result = makeStatementAssignmentVariable(
                source=self.subnode_source,
                variable=variable,
                source_ref=self.source_ref,
            )
            result.parent = self.parent

            new_result = result.computeStatement(trace_collection)
            result = new_result[0]

            assert result.isStatementAssignmentVariable(), new_result

            self.finalize()
            return (
                result,
                "new_statements",
                "Replaced dictionary assignment with temporary variable assignment.",
            )

        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        self.variable_trace = trace_collection.onVariableSet(
            variable=self.variable, version=self.variable_version, assign_node=self
        )

        if self.may_raise_set:
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return self.may_raise_set or self.subnode_source.mayRaiseException(
            exception_type
        )

    @staticmethod
    def getStatementNiceName():
        return "locals dictionary value set statement"


class StatementLocalsDictOperationDel(StatementBase):
    kind = "STATEMENT_LOCALS_DICT_OPERATION_DEL"

    __slots__ = (
        "variable",
        "variable_version",
        "previous_trace",
        "locals_scope",
        "tolerant",
    )

    # TODO: Specialize for Python3 maybe to save attribute for Python2.
    may_raise_del = python_version >= 0x300

    def __init__(self, locals_scope, variable_name, tolerant, source_ref):
        assert type(variable_name) is str

        StatementBase.__init__(self, source_ref=source_ref)

        assert locals_scope is not None

        self.locals_scope = locals_scope

        self.variable = locals_scope.getLocalsDictVariable(variable_name)
        self.variable_version = self.variable.allocateTargetNumber()

        self.tolerant = tolerant

        self.previous_trace = None

    def finalize(self):
        del self.parent
        del self.locals_scope
        del self.variable
        del self.previous_trace

    def getDetails(self):
        return {
            "variable_name": self.getVariableName(),
            "locals_scope": self.locals_scope,
        }

    def getVariableName(self):
        return self.variable.getName()

    def getLocalsDictScope(self):
        return self.locals_scope

    def computeStatement(self, trace_collection):
        # Conversion from dictionary to normal nodes is done here.
        if self.locals_scope.isMarkedForPropagation():
            variable_name = self.getVariableName()

            variable = self.locals_scope.allocateTempReplacementVariable(
                trace_collection=trace_collection, variable_name=variable_name
            )

            result = makeStatementDelVariable(
                variable=variable, tolerant=False, source_ref=self.source_ref
            )
            result.parent = self.parent

            new_result = result.computeStatement(trace_collection)
            result = new_result[0]

            assert result.isStatementDelVariable(), new_result

            return (
                new_result,
                "new_statements",
                "Replaced dictionary del with temporary variable.",
            )

        self.previous_trace = trace_collection.getVariableCurrentTrace(self.variable)

        # Deleting is usage of the value, and may call code on it. This is to inhibit
        # just removing it.
        self.previous_trace.addUsage()

        # We may not exception exit now during the __del__ unless there is no value.
        # TODO: In which case, there is doing to be a NameError or UnboundLocalError.
        if not self.previous_trace.mustHaveValue():
            trace_collection.onExceptionRaiseExit(BaseException)

        # Record the deletion, needs to start a new version then.
        _variable_trace = trace_collection.onVariableDel(
            variable=self.variable, version=self.variable_version, del_node=self
        )

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return self.may_raise_del and not self.tolerant

    @staticmethod
    def getStatementNiceName():
        return "locals dictionary value del statement"


class StatementSetLocalsMixin(object):
    __slots__ = ()

    def getDetailsForDisplay(self):
        return {"locals_scope": self.locals_scope.getCodeName()}

    def getLocalsScope(self):
        return self.locals_scope


class StatementSetLocals(StatementSetLocalsMixin, StatementSetLocalsBase):
    kind = "STATEMENT_SET_LOCALS"

    named_children = ("new_locals",)
    node_attributes = ("locals_scope",)
    auto_compute_handling = "operation"

    # TODO: Convert to StatementSetLocals if known to be constant dictionary.

    def getDetailsForDisplay(self):
        return {"locals_scope": self.locals_scope.getCodeName()}

    def getLocalsScope(self):
        return self.locals_scope

    def mayRaiseException(self, exception_type):
        return self.subnode_new_locals.mayRaiseException(exception_type)

    def computeStatementOperation(self, trace_collection):
        if self.locals_scope.isMarkedForPropagation():
            self.finalize()

            return (
                None,
                "new_statements",
                """\
Forward propagating locals.""",
            )

        if self.subnode_new_locals.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def getStatementNiceName():
        return "locals mapping init statement"


class StatementSetLocalsDictionary(
    StatementSetLocalsMixin, StatementSetLocalsDictionaryBase
):
    kind = "STATEMENT_SET_LOCALS_DICTIONARY"

    node_attributes = ("locals_scope",)

    def computeStatement(self, trace_collection):
        if self.locals_scope.isMarkedForPropagation():
            self.finalize()

            return (
                None,
                "new_statements",
                """\
Forward propagating locals.""",
            )

        return self, None, None

    @staticmethod
    def mayRaiseException(exception_type):
        return False

    @staticmethod
    def getStatementNiceName():
        return "locals dictionary init statement"


class StatementReleaseLocals(StatementBase):
    kind = "STATEMENT_RELEASE_LOCALS"

    __slots__ = ("locals_scope",)

    def __init__(self, locals_scope, source_ref):
        StatementBase.__init__(self, source_ref=source_ref)

        self.locals_scope = locals_scope

    def finalize(self):
        del self.parent
        del self.locals_scope

    def computeStatement(self, trace_collection):
        if self.locals_scope.isMarkedForPropagation():
            statements = [
                makeStatementReleaseVariable(
                    variable=variable, source_ref=self.source_ref
                )
                for variable in self.locals_scope.getPropagationVariables().values()
            ]

            result = makeStatementsSequence(
                statements=statements, allow_none=False, source_ref=self.source_ref
            )

            self.finalize()

            return (
                result,
                "new_statements",
                "Releasing temp variables instead of locals dict.",
            )

        return self, None, None

    def getDetails(self):
        return {"locals_scope": self.locals_scope}

    def getLocalsScope(self):
        return self.locals_scope

    @staticmethod
    def mayRaiseException(exception_type):
        return False

    @staticmethod
    def getStatementNiceName():
        return "locals dictionary release statement"
