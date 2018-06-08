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
""" Nodes that deal with locals, as dict or mapping.

The mapping types can be optimized into dict types, and the ones with
fallback can be optimized to no fallback variants.

"""



from nuitka import Variables
from nuitka.optimizations.TraceCollections import TraceCollectionBranch
from nuitka.PythonVersions import python_version

from .CallNodes import ExpressionCallEmpty
from .ConditionalNodes import ExpressionConditional
from .ConstantRefNodes import ExpressionConstantDictEmptyRef
from .ExpressionBases import ExpressionBase, ExpressionChildrenHavingBase
from .NodeBases import NodeBase, StatementChildrenHavingBase


class ExpressionLocalsVariableRefORFallback(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_LOCALS_VARIABLE_REF_OR_FALLBACK"

    named_children = ("fallback",)

    def __init__(self, locals_scope, variable_name, fallback_node, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "fallback" : fallback_node
            },
            source_ref = source_ref
        )

        assert locals_scope is not None

        self.locals_scope = locals_scope
        self.variable = locals_scope.getLocalsDictVariable(variable_name)

        self.variable_trace = None

    def getDetails(self):
        return {
            "variable_name" : self.getVariableName(),
        }

    def getVariableName(self):
        return self.variable.getName()

    def getLocalsDictScope(self):
        return self.locals_scope

    def computeExpressionRaw(self, trace_collection):
        self.variable_trace = trace_collection.getVariableCurrentTrace(
            variable = self.variable
        )

        replacement = self.variable_trace.getReplacementNode(self)

        if replacement is not None:
            trace_collection.signalChange(
                "new_expression",
                self.source_ref,
                "Value propagated for '%s' from '%s'." % (
                    self.variable.getName(),
                    replacement.getSourceReference().getAsString()
                )
            )

            # Need to compute the replacement still.
            return replacement.computeExpressionRaw(trace_collection)

        # If we cannot be sure if the value is set, then we need the fallback,
        # otherwise we could remove it simply.
        if self.variable_trace.mustHaveValue():
            trace_collection.signalChange(
                "new_expression",
                self.source_ref,
                "Name '%s' must be in locals dict." % self.variable.getName()
            )

            result = ExpressionLocalsVariableRef(
                locals_scope  = self.locals_scope,
                variable_name = self.variable.getName(),
                source_ref    = self.source_ref
            )

            # Need to compute the replacement still.
            return result.computeExpressionRaw(trace_collection)
        else:
            trace_collection.onExceptionRaiseExit(BaseException)

            branch_fallback = TraceCollectionBranch(
                parent = trace_collection,
                name   = "fallback node usage"
            )

            branch_fallback.computeBranch(self.subnode_fallback)

            trace_collection.mergeBranches(
                branch_fallback,
                None
            )

        # if we can be sure if doesn't have a value set, go to the fallback directly.
        if self.variable_trace.mustNotHaveValue():
            return (
                self.subnode_fallback,
                "new_expression",
                "Name '%s' cannot be in locals dict." % self.variable.getName()
            )
        else:
            return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw,
                              trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        trace_collection.onControlFlowEscape(self)

        if not Variables.complete and \
           self.variable.getName() in ("dir", "eval", "exec", "execfile", "locals", "vars") and \
           self.subnode_fallback.isExpressionVariableRef() and \
           self.subnode_fallback.getVariable().isModuleVariable():
            # Just inform the collection that all escaped.
            trace_collection.onLocalsUsage(self.getParentVariableProvider())

        if self.subnode_fallback.isExpressionBuiltinRef() or \
           self.subnode_fallback.isExpressionConstantTypeRef():
            if call_node.isExpressionCallEmpty():
                variable_name = self.variable.getName()

                result = ExpressionConditional(
                    condition      = ExpressionLocalsVariableCheck(
                        locals_scope  = self.locals_scope,
                        variable_name = variable_name,
                        source_ref    = self.source_ref

                    ),
                    expression_yes = ExpressionCallEmpty(
                        called     = ExpressionLocalsVariableRef(
                            locals_scope  = self.locals_scope,
                            variable_name = variable_name,
                            source_ref    = self.source_ref
                        ),
                        source_ref = call_node.source_ref
                    ),
                    expression_no  = ExpressionCallEmpty(
                        called     = self.subnode_fallback,
                        source_ref = call_node.source_ref
                    ),
                    source_ref     = self.source_ref
                )

                return result, "new_expression", "Moved empty call of uncertain dict variable to inside."

        return call_node, None, None

    def mayRaiseException(self, exception_type):
        return python_version >= 300 or \
               self.subnode_fallback.mayRaiseException(exception_type)


class ExpressionLocalsMappingVariableRefORFallback(ExpressionLocalsVariableRefORFallback):
    kind = "EXPRESSION_LOCALS_MAPPING_VARIABLE_REF_OR_FALLBACK"


class ExpressionLocalsVariableRef(ExpressionBase):
    kind = "EXPRESSION_LOCALS_VARIABLE_REF"

    __slots__ = "variable", "locals_scope", "variable_trace"

    def __init__(self, locals_scope, variable_name, source_ref):

        ExpressionBase.__init__(
            self,
            source_ref = source_ref
        )

        self.locals_scope = locals_scope
        self.variable = locals_scope.getLocalsDictVariable(variable_name)

        self.variable_trace = None

    def getDetails(self):
        return {
            "variable_name" : self.getVariableName(),
            "locals_scope"  : self.locals_scope
        }

    def getDetailsForDisplay(self):
        return {
            "variable_name" : self.getVariableName(),
        }

    def getVariableName(self):
        return self.variable.getName()

    def getLocalsDictScope(self):
        return self.locals_scope

    def computeExpressionRaw(self, trace_collection):
        self.variable_trace = trace_collection.getVariableCurrentTrace(
            variable = self.variable
        )

        replacement = self.variable_trace.getReplacementNode(self)

        if replacement is not None:
            trace_collection.signalChange(
                "new_expression",
                self.source_ref,
                "Value propagated for '%s' from '%s'." % (
                    self.variable.getName(),
                    replacement.getSourceReference().getAsString()
                )
            )

            # Need to compute the replacement still.
            return replacement.computeExpressionRaw(trace_collection)

        if not self.variable_trace.mustHaveValue():
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


    def computeExpressionCall(self, call_node, call_args, call_kw,
                              trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        trace_collection.onControlFlowEscape(self)
        return call_node, None, None

    def mayRaiseException(self, exception_type):
        return self.variable_trace is None or \
               not self.variable_trace.mustHaveValue()


class ExpressionLocalsVariableCheck(ExpressionBase):
    kind = "EXPRESSION_LOCALS_VARIABLE_CHECK"

    __slots__ = "variable_name", "locals_scope"

    def __init__(self, locals_scope, variable_name, source_ref):
        self.variable_name = variable_name

        ExpressionBase.__init__(
            self,
            source_ref = source_ref
        )

        self.locals_scope = locals_scope

    def getDetails(self):
        return {
            "variable_name" : self.variable_name,
        }

    def getVariableName(self):
        return self.variable_name

    def getLocalsDictScope(self):
        return self.locals_scope

    def computeExpressionRaw(self, trace_collection):
        return self, None, None


class StatementLocalsDictOperationSet(StatementChildrenHavingBase):
    kind = "STATEMENT_LOCALS_DICT_OPERATION_SET"

    named_children = (
        "value",
    )

    # TODO: Specialize for Python3 maybe to save attribute for Python2.
    may_raise_set = python_version >= 300

    def __init__(self, locals_scope, variable_name, value, source_ref):
        assert type(variable_name) is str
        assert value is not None

        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "value" : value
            },
            source_ref = source_ref
        )

        assert locals_scope is not None

        self.variable = locals_scope.getLocalsDictVariable(
            variable_name = variable_name
        )

        self.variable_version = self.variable.allocateTargetNumber()
        self.variable_trace = None

        self.locals_scope = locals_scope


    def getDetails(self):
        return {
            "variable_name" : self.getVariableName()
        }

    def getVariableName(self):
        return self.variable.getName()

    def getLocalsDictScope(self):
        return self.locals_scope

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection = trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        self.variable_trace = trace_collection.onVariableSet(
            variable    = self.variable,
            version     = self.variable_version,
            assign_node = self
        )

        if self.may_raise_set:
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return self.may_raise_set or self.subnode_value.mayRaiseException(exception_type)


class StatementLocalsDictOperationDel(NodeBase):
    kind = "STATEMENT_LOCALS_DICT_OPERATION_DEL"

    __slots__ = "variable", "variable_version", "previous_trace", "locals_scope"

    # TODO: Specialize for Python3 maybe to save attribute for Python2.
    may_raise_del = python_version >= 300


    def __init__(self, locals_scope, variable_name, source_ref):
        assert type(variable_name) is str

        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

        assert locals_scope is not None

        self.locals_scope = locals_scope

        self.variable = locals_scope.getLocalsDictVariable(variable_name)
        self.variable_version = self.variable.allocateTargetNumber()

        self.previous_trace = None

    def getDetails(self):
        return {
            "variable_name" : self.getVariableName(),
            "locals_scope"  : self.locals_scope
        }

    def getVariableName(self):
        return self.variable.getName()

    def getLocalsDictScope(self):
        return self.locals_scope

    def computeStatement(self, trace_collection):
        self.previous_trace = trace_collection.getVariableCurrentTrace(self.variable)

        # The "del" is a potential use of a value. TODO: This could be made more
        # beautiful indication, as it's not any kind of usage.
        self.previous_trace.addPotentialUsage()

        # We may not exception exit now during the __del__ unless there is no value.
        if not self.previous_trace.mustHaveValue():
            trace_collection.onExceptionRaiseExit(BaseException)

        # Record the deletion, needs to start a new version then.
        _variable_trace = trace_collection.onVariableDel(
            variable = self.variable,
            version  = self.variable_version
        )

        trace_collection.onVariableContentEscapes(self.variable)

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        return self, None, None

    def mayRaiseException(self, exception_type):
        return self.may_raise_del



class StatementSetLocals(StatementChildrenHavingBase):
    kind = "STATEMENT_SET_LOCALS"

    named_children = (
        "new_locals",
    )

    def __init__(self, locals_scope, new_locals, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "new_locals" : new_locals,
            },
            source_ref = source_ref
        )

        self.locals_scope = locals_scope

    def getDetailsForDisplay(self):
        return {
            "locals_scope" : self.locals_scope.getCodeName()
        }

    def getDetails(self):
        return {
            "locals_scope" : self.locals_scope
        }

    def getLocalsScope(self):
        return self.locals_scope

    def mayRaiseException(self, exception_type):
        return self.getNewLocals().mayRaiseException(exception_type)

    getNewLocals = StatementChildrenHavingBase.childGetter("new_locals")

    def computeStatement(self, trace_collection):
        trace_collection.onExpression(self.getNewLocals())
        new_locals = self.getNewLocals()

        if new_locals.willRaiseException(BaseException):
            from .NodeMakingHelpers import \
               makeStatementExpressionOnlyReplacementNode

            result = makeStatementExpressionOnlyReplacementNode(
                expression = new_locals,
                node       = self
            )

            return result, "new_raise", """\
Setting locals already raises implicitly building new locals."""

        return self, None, None


class StatementSetLocalsDictionary(StatementSetLocals):
    kind = "STATEMENT_SET_LOCALS_DICTIONARY"

    def __init__(self, locals_scope, source_ref):
        StatementSetLocals.__init__(
            self,
            locals_scope = locals_scope,
            new_locals   = ExpressionConstantDictEmptyRef(
                source_ref = source_ref
            ),
            source_ref   = source_ref
        )

    def mayRaiseException(self, exception_type):
        return False


class StatementReleaseLocals(NodeBase):
    kind = "STATEMENT_RELEASE_LOCALS"

    __slots__ = ("locals_scope",)

    def __init__(self, locals_scope, source_ref):
        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

        self.locals_scope = locals_scope

    def computeStatement(self, trace_collection):
        return self, None, None

    def getDetails(self):
        return {
            "locals_scope": self.locals_scope
        }

    def getLocalsScope(self):
        return self.locals_scope

    def mayRaiseException(self, exception_type):
        return False
