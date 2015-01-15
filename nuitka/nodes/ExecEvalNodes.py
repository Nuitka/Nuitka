#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka import Utils

from .NodeBases import ExpressionChildrenHavingBase, StatementChildrenHavingBase


class ExpressionBuiltinEval(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_EVAL"

    named_children = (
        "source",
        "globals",
        "locals"
    )

    def __init__(self, source_code, globals_arg, locals_arg, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "source"  : source_code,
                "globals" : globals_arg,
                "locals"  : locals_arg,
            },
            source_ref = source_ref
        )

    getSourceCode = ExpressionChildrenHavingBase.childGetter("source")
    getGlobals = ExpressionChildrenHavingBase.childGetter("globals")
    getLocals = ExpressionChildrenHavingBase.childGetter("locals")

    def computeExpression(self, constraint_collection):
        # TODO: Attempt for constant values to do it.
        return self, None, None


# Note: Python3 only so far.
if Utils.python_version >= 300:
    class ExpressionBuiltinExec(ExpressionBuiltinEval):
        kind = "EXPRESSION_BUILTIN_EXEC"

        def __init__(self, source_code, globals_arg, locals_arg, source_ref):
            ExpressionBuiltinEval.__init__(
                self,
                source_code = source_code,
                globals_arg = globals_arg,
                locals_arg  = locals_arg,
                source_ref  = source_ref
            )

        def needsLocalsDict(self):
            return False

        def computeExpression(self, constraint_collection):
            # TODO: Attempt for constant values to do it.
            return self, None, None

        def computeExpressionDrop(self, statement, constraint_collection):
            if self.getParentVariableProvider().isEarlyClosure():
                result = StatementExec(
                    source_code = self.getSourceCode(),
                    globals_arg = self.getGlobals(),
                    locals_arg  = self.getLocals(),
                    source_ref  = self.getSourceReference()
                )

                return result, "new_statements", """\
Replaced builtin exec call to exec statement in early closure context."""
            else:
                return statement, None, None


# Note: Python2 only
if Utils.python_version < 300:
    class ExpressionBuiltinExecfile(ExpressionBuiltinEval):
        kind = "EXPRESSION_BUILTIN_EXECFILE"

        named_children = ("source", "globals", "locals")

        def __init__(self, source_code, globals_arg, locals_arg, source_ref):
            ExpressionBuiltinEval.__init__(
                self,
                source_code = source_code,
                globals_arg = globals_arg,
                locals_arg  = locals_arg,
                source_ref  = source_ref
            )

        def needsLocalsDict(self):
            return True

        def computeExpressionDrop(self, statement, constraint_collection):
            # In this case, the copy-back must be done and will only be done
            # correctly by the code for exec statements.
            provider = self.getParentVariableProvider()

            if provider.isExpressionFunctionBody() and \
               provider.isClassDictCreation():
                result = StatementExec(
                    source_code = self.getSourceCode(),
                    globals_arg = self.getGlobals(),
                    locals_arg  = self.getLocals(),
                    source_ref  = self.getSourceReference()
                )

                return result, "new_statements", """\
Changed execfile to exec on class level."""
            else:
                return statement, None, None


class StatementExec(StatementChildrenHavingBase):
    kind = "STATEMENT_EXEC"

    named_children = (
        "source",
        "globals",
        "locals"
    )

    def __init__(self, source_code, globals_arg, locals_arg, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "globals" : globals_arg,
                "locals"  : locals_arg,
                "source"  : source_code
            },
            source_ref = source_ref,
        )

    def setChild(self, name, value):
        if name in ("globals", "locals"):
            from .NodeMakingHelpers import convertNoneConstantToNone

            value = convertNoneConstantToNone(value)

        return StatementChildrenHavingBase.setChild(self, name, value)

    getSourceCode = StatementChildrenHavingBase.childGetter("source")
    getGlobals = StatementChildrenHavingBase.childGetter("globals")
    getLocals = StatementChildrenHavingBase.childGetter("locals")

    def needsLocalsDict(self):
        return self.getLocals().mayBeNone()

    def computeStatement(self, constraint_collection):
        constraint_collection.onExpression(
            expression = self.getSourceCode()
        )
        source_code = self.getSourceCode()

        if source_code.willRaiseException(BaseException):
            result = source_code

            return (
                result,
                "new_raise",
                """\
Exec statement raises implicitly when determining source code argument."""
            )

        constraint_collection.onExpression(
            expression = self.getGlobals(),
            allow_none = True
        )
        globals_arg = self.getGlobals()

        if globals_arg is not None and \
           globals_arg.willRaiseException(BaseException):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    source_code,
                    globals_arg
                )
            )

            return (
                result,
                "new_raise",
                """\
Exec statement raises implicitly when determining globals argument."""
            )

        constraint_collection.onExpression(
            expression = self.getLocals(),
            allow_none = True
        )
        locals_arg = self.getLocals()

        if locals_arg is not None and \
           locals_arg.willRaiseException(BaseException):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    source_code,
                    globals_arg,
                    locals_arg
                )
            )

            return (
                result,
                "new_raise",
                """\
Exec statement raises implicitly when determining locals argument."""
            )

        str_value = self.getSourceCode().getStrValue()

        if False and str_value is not None:
            # TODO: Don't forget to consider side effects of source code.

            # TODO: This needs to be re-done.
            exec_body = None

            return (
                exec_body,
                "new_statements",
                "In-lined constant exec statement."
            )

        return self, None, None


class StatementLocalsDictSync(StatementChildrenHavingBase):
    kind = "STATEMENT_LOCALS_DICT_SYNC"

    named_children = (
        "locals",
    )

    def __init__(self, locals_arg, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "locals"  : locals_arg,
            },
            source_ref = source_ref,
        )

    def computeStatement(self, constraint_collection):
        if self.getParentVariableProvider().isPythonModule():
            return None, "new_statements", "Removed sync back to locals without locals."

        constraint_collection.removeAllKnowledge()

        return self, None, None

    getLocals = ExpressionChildrenHavingBase.childGetter("locals")

    def mayRaiseException(self, exception_type):
        return False


class ExpressionBuiltinCompile(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_COMPILE"

    named_children = (
        "source",
        "filename",
        "mode",
        "flags",
        "dont_inherit",
        "optimize"
    )

    def __init__(self, source_code, filename, mode, flags, dont_inherit,
                 optimize, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "source"       : source_code,
                "filename"     : filename,
                "mode"         : mode,
                "flags"        : flags,
                "dont_inherit" : dont_inherit,
                "optimize"     : optimize
            },
            source_ref = source_ref
        )

    getSourceCode = ExpressionChildrenHavingBase.childGetter("source")
    getFilename = ExpressionChildrenHavingBase.childGetter("filename")
    getMode = ExpressionChildrenHavingBase.childGetter("mode")
    getFlags = ExpressionChildrenHavingBase.childGetter("flags")
    getDontInherit = ExpressionChildrenHavingBase.childGetter("dont_inherit")
    getOptimize = ExpressionChildrenHavingBase.childGetter("optimize")

    def computeExpression(self, constraint_collection):
        # TODO: Attempt for constant values to do it.
        return self, None, None
