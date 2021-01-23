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
""" Nodes concern with exec and eval builtins.

These are the dynamic codes, and as such rather difficult. We would like
to eliminate or limit their impact as much as possible, but it's difficult
to do.
"""

from nuitka.PythonVersions import python_version

from .ExpressionBases import ExpressionChildrenHavingBase
from .NodeBases import StatementChildHavingBase, StatementChildrenHavingBase
from .NodeMakingHelpers import (
    convertNoneConstantToNone,
    makeStatementOnlyNodesFromExpressions,
)


class ExpressionBuiltinEval(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_EVAL"

    named_children = ("source", "globals_arg", "locals_arg")

    def __init__(self, source_code, globals_arg, locals_arg, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values={
                "source": source_code,
                "globals_arg": globals_arg,
                "locals_arg": locals_arg,
            },
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        # TODO: Attempt for constant values to do it.
        return self, None, None


# Note: Python3 only so far.
if python_version >= 0x300:

    class ExpressionBuiltinExec(ExpressionBuiltinEval):
        kind = "EXPRESSION_BUILTIN_EXEC"

        def __init__(self, source_code, globals_arg, locals_arg, source_ref):
            ExpressionBuiltinEval.__init__(
                self,
                source_code=source_code,
                globals_arg=globals_arg,
                locals_arg=locals_arg,
                source_ref=source_ref,
            )

        def computeExpression(self, trace_collection):
            # TODO: Attempt for constant values to do it.
            return self, None, None

        def computeExpressionDrop(self, statement, trace_collection):
            if self.getParentVariableProvider().isEarlyClosure():
                result = StatementExec(
                    source_code=self.subnode_source,
                    globals_arg=self.subnode_globals_arg,
                    locals_arg=self.subnode_locals_arg,
                    source_ref=self.source_ref,
                )

                del self.parent

                return (
                    result,
                    "new_statements",
                    """\
Replaced built-in exec call to exec statement in early closure context.""",
                )
            else:
                return statement, None, None


# Note: Python2 only
if python_version < 0x300:

    class ExpressionBuiltinExecfile(ExpressionBuiltinEval):
        kind = "EXPRESSION_BUILTIN_EXECFILE"

        named_children = ("source", "globals_arg", "locals_arg")

        def __init__(self, source_code, globals_arg, locals_arg, source_ref):
            ExpressionBuiltinEval.__init__(
                self,
                source_code=source_code,
                globals_arg=globals_arg,
                locals_arg=locals_arg,
                source_ref=source_ref,
            )

        def computeExpressionDrop(self, statement, trace_collection):
            # In this case, the copy-back must be done and will only be done
            # correctly by the code for exec statements.
            provider = self.getParentVariableProvider()

            if provider.isExpressionClassBody():
                result = StatementExec(
                    source_code=self.subnode_source,
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


class StatementExec(StatementChildrenHavingBase):
    kind = "STATEMENT_EXEC"

    named_children = ("source", "globals_arg", "locals_arg")

    def __init__(self, source_code, globals_arg, locals_arg, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values={
                "globals_arg": globals_arg,
                "locals_arg": locals_arg,
                "source": source_code,
            },
            source_ref=source_ref,
        )

    def setChild(self, name, value):
        if name in ("globals_arg", "locals_arg"):
            value = convertNoneConstantToNone(value)

        return StatementChildrenHavingBase.setChild(self, name, value)

    def computeStatement(self, trace_collection):
        source_code = trace_collection.onExpression(expression=self.subnode_source)

        if source_code.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        if source_code.willRaiseException(BaseException):
            result = source_code

            return (
                result,
                "new_raise",
                """\
Exec statement raises implicitly when determining source code argument.""",
            )

        globals_arg = trace_collection.onExpression(
            expression=self.subnode_globals_arg, allow_none=True
        )

        if globals_arg is not None and globals_arg.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        if globals_arg is not None and globals_arg.willRaiseException(BaseException):
            result = makeStatementOnlyNodesFromExpressions(
                expressions=(source_code, globals_arg)
            )

            return (
                result,
                "new_raise",
                """\
Exec statement raises implicitly when determining globals argument.""",
            )

        locals_arg = trace_collection.onExpression(
            expression=self.subnode_locals_arg, allow_none=True
        )

        if locals_arg is not None and locals_arg.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        if locals_arg is not None and locals_arg.willRaiseException(BaseException):
            result = makeStatementOnlyNodesFromExpressions(
                expressions=(source_code, globals_arg, locals_arg)
            )

            return (
                result,
                "new_raise",
                """\
Exec statement raises implicitly when determining locals argument.""",
            )

        trace_collection.onExceptionRaiseExit(BaseException)

        str_value = self.subnode_source.getStrValue()

        if False and str_value is not None:
            # TODO: Don't forget to consider side effects of source code,
            # locals_arg, and globals_arg.

            # TODO: This needs to be re-done.
            exec_body = None

            return (exec_body, "new_statements", "In-lined constant exec statement.")

        return self, None, None


class StatementLocalsDictSync(StatementChildHavingBase):
    kind = "STATEMENT_LOCALS_DICT_SYNC"

    named_child = "locals_arg"

    __slots__ = ("locals_scope", "previous_traces", "variable_traces")

    def __init__(self, locals_scope, locals_arg, source_ref):
        StatementChildHavingBase.__init__(self, value=locals_arg, source_ref=source_ref)

        self.previous_traces = None
        self.variable_traces = None

        self.locals_scope = locals_scope

    def getDetails(self):
        return {"locals_scope": self.locals_scope}

    def getPreviousVariablesTraces(self):
        return self.previous_traces

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

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


class ExpressionBuiltinCompile(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_COMPILE"

    named_children = ("source", "filename", "mode", "flags", "dont_inherit", "optimize")

    def __init__(
        self, source_code, filename, mode, flags, dont_inherit, optimize, source_ref
    ):
        ExpressionChildrenHavingBase.__init__(
            self,
            values={
                "source": source_code,
                "filename": filename,
                "mode": mode,
                "flags": flags,
                "dont_inherit": dont_inherit,
                "optimize": optimize,
            },
            source_ref=source_ref,
        )

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        # TODO: Attempt for constant values to do it.
        return self, None, None
