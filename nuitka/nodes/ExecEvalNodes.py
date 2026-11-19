#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Nodes concerned with exec, eval, and compile built-ins."""

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

    @staticmethod
    def isExpressionBuiltinCall():
        return True

    def __init__(self, source_code, globals_arg, locals_arg, source_ref):
        ChildrenExpressionBuiltinEvalMixin.__init__(
            self,
            source_code=source_code,
            globals_arg=globals_arg,
            locals_arg=locals_arg,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        return self, None, None


class ExpressionBuiltinExec(ChildrenExpressionBuiltinExecMixin, ExpressionBase):
    kind = "EXPRESSION_BUILTIN_EXEC"

    python_version_spec = ">= 0x300"

    named_children = ("source_code", "globals_arg", "locals_arg", "closure|optional")

    @staticmethod
    def isExpressionBuiltinCall():
        return True

    def __init__(self, source_code, globals_arg, locals_arg, closure, source_ref):
        ChildrenExpressionBuiltinExecMixin.__init__(
            self,
            source_code=source_code,
            globals_arg=globals_arg,
            locals_arg=locals_arg,
            closure=closure,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def computeExpressionDrop(self, statement, trace_collection):
        return statement, None, None


class ExpressionBuiltinExecfile(ChildrenExpressionBuiltinExecfileMixin, ExpressionBase):
    kind = "EXPRESSION_BUILTIN_EXECFILE"

    python_version_spec = "< 0x300"

    named_children = ("source_code", "globals_arg", "locals_arg")

    @staticmethod
    def isExpressionBuiltinCall():
        return True

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

        return self, None, None

    def computeExpressionDrop(self, statement, trace_collection):
        # In a Python 2 class body, locals copy-back is only performed by the
        # 'exec' statement implementation.
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
        return self, None, None


class StatementLocalsDictSync(StatementLocalsDictSyncBase):
    kind = "STATEMENT_LOCALS_DICT_SYNC"

    named_children = ("locals_arg",)
    node_attributes = ("locals_scope",)
    auto_compute_handling = "operation,post_init"

    __slots__ = ("previous_traces", "variable_traces")

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

    @staticmethod
    def isExpressionBuiltinCall():
        return True

    def __init__(
        self, source, filename, mode, flags, dont_inherit, optimize, source_ref
    ):
        ChildrenExpressionBuiltinCompileMixin.__init__(
            self,
            source=source,
            filename=filename,
            mode=mode,
            flags=flags,
            dont_inherit=dont_inherit,
            optimize=optimize,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
