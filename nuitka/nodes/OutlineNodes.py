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
""" Outline nodes.

We use them for re-formulations and for in-lining of code. They are expressions
that get their value from return statements in their code body. They do not
own anything by themselves. It's just a way of having try/finally for the
expressions, or multiple returns, without running in a too different context.
"""

from .ConstantRefNodes import makeConstantRefNode
from .ExceptionNodes import ExpressionRaiseException
from .ExpressionBases import ExpressionChildHavingBase
from .FunctionNodes import ExpressionFunctionBodyBase
from .LocalsScopes import getLocalsDictHandle


class ExpressionOutlineBody(ExpressionChildHavingBase):
    """Outlined expression code.

    This is for a call to a piece of code to be executed in a specific
    context. It contains an exclusively owned function body, that has
    no other references, and can be considered part of the calling
    context.

    It must return a value, to use as expression value.
    """

    kind = "EXPRESSION_OUTLINE_BODY"

    named_child = "body"

    __slots__ = ("provider", "name", "temp_scope")

    @staticmethod
    def isExpressionOutlineBody():
        return True

    def __init__(self, provider, name, source_ref, body=None):
        assert name != ""

        ExpressionChildHavingBase.__init__(self, value=body, source_ref=source_ref)

        self.provider = provider
        self.name = name

        self.temp_scope = None

        # Hack: This allows some APIs to work although this is not yet
        # officially a child yet. Important during building.
        self.parent = provider

    def getDetails(self):
        return {"provider": self.provider, "name": self.name}

    def getOutlineTempScope(self):
        # We use our own name as a temp_scope, cached from the parent, if the
        # scope is None.
        if self.temp_scope is None:
            self.temp_scope = self.provider.allocateTempScope(self.name)

        return self.temp_scope

    def allocateTempVariable(self, temp_scope, name, temp_type=None):
        if temp_scope is None:
            temp_scope = self.getOutlineTempScope()

        return self.provider.allocateTempVariable(
            temp_scope=temp_scope, name=name, temp_type=temp_type
        )

    def allocateTempScope(self, name):

        # Let's scope the temporary scopes by the outline they come from.
        return self.provider.allocateTempScope(name=self.name + "$" + name)

    def getContainingClassDictCreation(self):
        return self.getParentVariableProvider().getContainingClassDictCreation()

    def computeExpressionRaw(self, trace_collection):
        owning_module = self.getParentModule()

        # Make sure the owning module is added to the used set. This is most
        # important for helper functions, or modules, which otherwise have
        # become unused.
        from nuitka.ModuleRegistry import addUsedModule

        addUsedModule(owning_module)

        abort_context = trace_collection.makeAbortStackContext(
            catch_breaks=False,
            catch_continues=False,
            catch_returns=True,
            catch_exceptions=False,
        )

        with abort_context:
            body = self.subnode_body

            result = body.computeStatementsSequence(trace_collection=trace_collection)

            if result is not body:
                self.setChild("body", result)
                body = result

            return_collections = trace_collection.getFunctionReturnCollections()

        if return_collections:
            trace_collection.mergeMultipleBranches(return_collections)

        first_statement = body.subnode_statements[0]

        if first_statement.isStatementReturnConstant():
            return (
                makeConstantRefNode(
                    constant=first_statement.getConstant(),
                    source_ref=first_statement.source_ref,
                ),
                "new_expression",
                "Outline '%s' is now simple return, use directly." % self.name,
            )

        if first_statement.isStatementReturn():
            return (
                first_statement.subnode_expression,
                "new_expression",
                "Outline '%s' is now simple return, use directly." % self.name,
            )

        if first_statement.isStatementRaiseException():
            result = ExpressionRaiseException(
                exception_type=first_statement.subnode_exception_type,
                exception_value=first_statement.subnode_exception_value,
                source_ref=first_statement.getSourceReference(),
            )

            return (
                result,
                "new_expression",
                "Outline is now exception raise, use directly.",
            )

        # TODO: Function outline may become too trivial to outline and return
        # collections may tell us something.
        return self, None, None

    def mayRaiseException(self, exception_type):
        return self.subnode_body.mayRaiseException(exception_type)

    def willRaiseException(self, exception_type):
        return self.subnode_body.willRaiseException(exception_type)

    def getEntryPoint(self):
        """Entry point for code.

        Normally ourselves. Only outlines will refer to their parent which
        technically owns them.

        """

        return self.provider.getEntryPoint()

    def getCodeName(self):
        return self.provider.getCodeName()


class ExpressionOutlineFunctionBase(ExpressionFunctionBodyBase):
    """Outlined function code.

    This is for a call to a function to be called in-line to be executed
    in a specific context. It contains an exclusively owned function body,
    that has no other references, and can be considered part of the calling
    context.

    As normal function it must return a value, to use as expression value,
    but we know we only exist once.

    Once this has no frame, it can be changed to a mere outline expression.
    """

    __slots__ = ("temp_scope", "locals_scope")

    def __init__(self, provider, name, body, code_prefix, source_ref):
        ExpressionFunctionBodyBase.__init__(
            self,
            provider=provider,
            name=name,
            body=body,
            code_prefix=code_prefix,
            flags=None,
            source_ref=source_ref,
        )

        self.temp_scope = None

        self.locals_scope = None

    @staticmethod
    def isExpressionOutlineFunctionBase():
        return True

    def getDetails(self):
        return {"name": self.name, "provider": self.provider}

    def getDetailsForDisplay(self):
        return {"name": self.name, "provider": self.provider.getCodeName()}

    def computeExpressionRaw(self, trace_collection):
        # Keep track of these, so they can provide what variables are to be
        # setup.
        trace_collection.addOutlineFunction(self)

        abort_context = trace_collection.makeAbortStackContext(
            catch_breaks=False,
            catch_continues=False,
            catch_returns=True,
            catch_exceptions=False,
        )

        with abort_context:
            body = self.subnode_body

            result = body.computeStatementsSequence(trace_collection=trace_collection)

            if result is not body:
                self.setChild("body", result)
                body = result

            return_collections = trace_collection.getFunctionReturnCollections()

        if return_collections:
            trace_collection.mergeMultipleBranches(return_collections)

        first_statement = body.subnode_statements[0]

        if first_statement.isStatementReturnConstant():
            return (
                makeConstantRefNode(
                    constant=first_statement.getConstant(),
                    source_ref=first_statement.source_ref,
                ),
                "new_expression",
                "Outline function '%s' is now simple return, use directly." % self.name,
            )

        if first_statement.isStatementReturn():
            return (
                first_statement.subnode_expression,
                "new_expression",
                "Outline function '%s' is now simple return, use directly." % self.name,
            )

        if first_statement.isStatementRaiseException():
            result = ExpressionRaiseException(
                exception_type=first_statement.subnode_exception_type,
                exception_value=first_statement.subnode_exception_value,
                source_ref=first_statement.getSourceReference(),
            )

            return (
                result,
                "new_expression",
                "Outline function is now exception raise, use directly.",
            )

        # TODO: Function outline may become too trivial to outline and return
        # collections may tell us something.
        return self, None, None

    def mayRaiseException(self, exception_type):
        return self.subnode_body.mayRaiseException(exception_type)

    def willRaiseException(self, exception_type):
        return self.subnode_body.willRaiseException(exception_type)

    def getTraceCollection(self):
        return self.provider.getTraceCollection()

    def getOutlineTempScope(self):
        # We use our own name as a temp_scope, cached from the parent, if the
        # scope is None.
        if self.temp_scope is None:
            self.temp_scope = self.provider.allocateTempScope(self.name)

        return self.temp_scope

    def allocateTempVariable(self, temp_scope, name, temp_type=None):
        if temp_scope is None:
            temp_scope = self.getOutlineTempScope()

        return self.provider.allocateTempVariable(
            temp_scope=temp_scope, name=name, temp_type=None
        )

    def allocateTempScope(self, name):

        # Let's scope the temporary scopes by the outline they come from.
        return self.provider.allocateTempScope(name=self.name + "$" + name)

    def getEntryPoint(self):
        """Entry point for code.

        Normally ourselves. Only outlines will refer to their parent which
        technically owns them.

        """

        return self.provider.getEntryPoint()

    def getClosureVariable(self, variable_name):
        # Simply try and get from our parent.
        return self.provider.getVariableForReference(variable_name=variable_name)

    def getLocalsScope(self):
        return self.locals_scope

    def isEarlyClosure(self):
        return self.provider.isEarlyClosure()

    def isUnoptimized(self):
        return self.provider.isUnoptimized()


class ExpressionOutlineFunction(ExpressionOutlineFunctionBase):
    kind = "EXPRESSION_OUTLINE_FUNCTION"

    __slots__ = ("locals_scope",)

    def __init__(self, provider, name, source_ref, body=None):
        ExpressionOutlineFunctionBase.__init__(
            self,
            provider=provider,
            name=name,
            code_prefix="outline",
            body=body,
            source_ref=source_ref,
        )

        self.locals_scope = getLocalsDictHandle(
            "locals_%s" % self.getCodeName(), "python_function", self
        )
