#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Nodes concern with exec and eval builtins.

These are the dynamic codes, and as such rather difficult. We would like
to eliminate or limit their impact as much as possible, but it's difficult
to do.
"""

from .ChildrenHavingMixins import (
    ChildrenExpressionBuiltinCompileMixin,
    ChildrenExpressionBuiltinEvalMixin,
    ChildrenExpressionBuiltinExecfileMixin,
    ChildrenExpressionBuiltinExecMixin,
)
from .ExpressionBases import ExpressionBase
from .StatementBasesGenerated import (
    StatementExecBase,
    StatementLocalsDictSyncBase,
)


class ExpressionBuiltinEval(ChildrenExpressionBuiltinEvalMixin, ExpressionBase):
    kind = "EXPRESSION_BUILTIN_EVAL"

    named_children = ("source_code", "globals_arg", "locals_arg")

    def __init__(self, source_code, globals_arg, locals_arg, source_ref):
        ChildrenExpressionBuiltinEvalMixin.__init__(
            self,
            source_code=source_code,
            globals_arg=globals_arg,
            locals_arg=locals_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        # TODO: Attempt for constant values to do it.
        return self, None, None


class ExpressionBuiltinExec(ChildrenExpressionBuiltinExecMixin, ExpressionBase):
    kind = "EXPRESSION_BUILTIN_EXEC"

    python_version_spec = ">= 0x300"

    named_children = ("source_code", "globals_arg", "locals_arg")

    def __init__(self, source_code, globals_arg, locals_arg, source_ref):
        ChildrenExpressionBuiltinExecMixin.__init__(
            self,
            source_code=source_code,
            globals_arg=globals_arg,
            locals_arg=locals_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        # TODO: Attempt for constant values to do it.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def computeExpressionDrop(self, statement, trace_collection):
        return statement, None, None


class ExpressionBuiltinExecfile(ChildrenExpressionBuiltinExecfileMixin, ExpressionBase):
    kind = "EXPRESSION_BUILTIN_EXECFILE"

    python_version_spec = "< 0x300"

    named_children = ("source_code", "globals_arg", "locals_arg")

    __slots__ = ("in_class_body",)

    def __init__(self, in_class_body, source_code, globals_arg, locals_arg, source_ref):
        ChildrenExpressionBuiltinExecfileMixin.__init__(
            self,
            source_code=source_code,
            globals_arg=globals_arg,
            locals_arg=locals_arg,
        )

        ExpressionBase.__init__(self, source_ref)

        self.in_class_body = in_class_body

    def getDetails(self):
        return {"in_class_body": self.in_class_body}

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        # Nothing can be done for it really.
        return self, None, None

    def computeExpressionDrop(self, statement, trace_collection):
        # In this case, the copy-back must be done and will only be done
        # correctly by the code for exec statements.

        if self.in_class_body:
            result = StatementExec(
                source_code=self.subnode_source_code,
                globals_arg=self.subnode_globals_arg,
                locals_arg=self.subnode_locals_arg,
                source_ref=self.source_ref,
            )

            del self.parent

            return (
                result,
                "new_statements",
                """\
Changed 'execfile' with unused result to 'exec' on class level.""",
            )
        else:
            return statement, None, None


class StatementExec(StatementExecBase):
    kind = "STATEMENT_EXEC"

    named_children = ("source_code", "globals_arg|auto_none", "locals_arg|auto_none")
    auto_compute_handling = "operation"

    python_version_spec = "< 0x300"

    def computeStatementOperation(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        # TODO: Optimize strings for exec expression and statement again.
        # str_value = self.subnode_source_code.getStrValue()

        return self, None, None


class StatementLocalsDictSync(StatementLocalsDictSyncBase):
    kind = "STATEMENT_LOCALS_DICT_SYNC"

    named_children = ("locals_arg",)
    node_attributes = ("locals_scope",)
    auto_compute_handling = "operation,post_init"

    __slots__ = ("previous_traces", "variable_traces")

    # false alarm due to post_init, pylint: disable=attribute-defined-outside-init

    def postInitNode(self):
        self.previous_traces = None
        self.variable_traces = None

    def getPreviousVariablesTraces(self):
        return self.previous_traces

    def computeStatementOperation(self, trace_collection):
        # TODO: Derive this from the locals scope instead, otherwise this is
        # costly and a potentially wrong decision.
        provider = self.getParentVariableProvider()
        if provider.isCompiledPythonModule():
            return None, "new_statements", "Removed sync back to locals without locals."

        self.previous_traces = trace_collection.onLocalsUsage(self.locals_scope)
        if not self.previous_traces:
            return None, "new_statements", "Removed sync back to locals without locals."

        trace_collection.removeAllKnowledge()
        self.variable_traces = trace_collection.onLocalsUsage(self.locals_scope)

        return self, None, None

    @staticmethod
    def mayRaiseException(exception_type):
        return False


class ExpressionBuiltinCompile(ChildrenExpressionBuiltinCompileMixin, ExpressionBase):
    kind = "EXPRESSION_BUILTIN_COMPILE"

    named_children = (
        "source",
        "filename",
        "mode",
        "flags|optional",
        "dont_inherit|optional",
        "optimize|optional",
    )

    def __init__(
        self, source_code, filename, mode, flags, dont_inherit, optimize, source_ref
    ):
        ChildrenExpressionBuiltinCompileMixin.__init__(
            self,
            source=source_code,
            filename=filename,
            mode=mode,
            flags=flags,
            dont_inherit=dont_inherit,
            optimize=optimize,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        # TODO: Attempt for constant values to do it.
        return self, None, None
