#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Outline nodes.

We use them for re-formulations and for in-lining of code. They are expressions
that get their value from return statements in their code body. They do not
own anything by themselves. It's just a way of having try/finally for the
expressions, or multiple returns, without running in a too different context.
"""

from nuitka.ModuleRegistry import addUsedModule
from nuitka.tree.Extractions import (
    getClonedProvider,
    updateVariableUsage,
    withClonedProvider,
)

from .ChildrenHavingMixins import ChildHavingBodyOptionalMixin
from .ConstantRefNodes import makeConstantRefNode
from .ExceptionNodes import ExpressionRaiseException
from .ExpressionBases import ExpressionBase
from .FunctionNodes import (
    ExpressionFunctionBodyBase,
    updateFunctionBodyReferences,
)
from .LocalsScopes import getLocalsDictHandle


class ExpressionOutlineMixin(object):
    # pylint: disable=assigning-non-slot
    __slots__ = ()

    def getDetails(self):
        return {"provider": self.provider, "name": self.name}

    def getDetailsForDisplay(self):
        return {"name": self.name, "provider": self.provider.getCodeName()}

    def getEntryPoint(self):
        """Entry point for code.

        Normally ourselves. Only outlines will refer to their parent which
        technically owns them.

        """

        return self.provider.getEntryPoint()

    def needsReturnExit(self):
        """Does a return of the outline body need an exit point.

        This is not the case if no return can complete, e.g. when all of them
        are contained in a 'finally' block that raises.

        Returns:
            bool
        """

        body = self.subnode_body

        return body is not None and body.mayReturn()

    def getOutlineTempScope(self):
        if self.temp_scope is None:
            self.temp_scope = self.provider.allocateTempScope(self.name)

        return self.temp_scope

    def allocateTempScope(self, name):
        return self.provider.allocateTempScope(name=self.name + "$" + name)

    def allocateTempVariable(self, temp_scope, name, temp_type, late=False):
        if temp_scope is None:
            temp_scope = self.getOutlineTempScope()

        entry_point = self.getEntryPoint()

        return entry_point.allocateTempVariable(
            temp_scope=temp_scope,
            name=name,
            temp_type=temp_type,
            late=late,
            outline=self,
        )

    def _cloneTempVariables(self, result):
        old_entry_point = self.getEntryPoint()
        new_entry_point = result.getEntryPoint()

        assert new_entry_point.trace_collection is None, new_entry_point

        variable_translations = {}

        for temp_variable in old_entry_point.getTempVariables(self):
            new_temp_name = temp_variable.getName()

            if new_entry_point.hasTempVariable(new_temp_name):
                clone_number = 1

                while True:
                    clone_suffix = (
                        "_clone" if clone_number == 1 else "_clone_%d" % clone_number
                    )
                    candidate_name = new_temp_name + clone_suffix

                    if not new_entry_point.hasTempVariable(candidate_name):
                        new_temp_name = candidate_name
                        break

                    clone_number += 1

            # Make the clone own separate temporary variables; cloning only
            # happens before trace collection starts.
            new_temp_variable = new_entry_point.createTempVariable(
                temp_name=new_temp_name,
                temp_type=temp_variable.getVariableType(),
                outline=result,
            )

            variable_translations[temp_variable] = new_temp_variable

        return variable_translations

    def _computeOutlineBody(self, trace_collection, need_removal, outline_description):
        catch_exceptions = (
            need_removal and trace_collection.getExceptionRaiseCollections() is not None
        )

        abort_context = trace_collection.makeAbortStackContext(
            catch_breaks=False,
            catch_continues=False,
            catch_returns=True,
            catch_exceptions=catch_exceptions,
        )

        with abort_context:
            body = self.subnode_body

            result = body.computeStatementsSequence(trace_collection=trace_collection)

            if result is not body:
                self.setChildBody(result)
                body = result

            return_collections = trace_collection.getFunctionReturnCollections()
            exception_collections = trace_collection.getExceptionRaiseCollections()

            for variable in need_removal:
                for return_collection in return_collections:
                    return_collection.removeCurrentVariableTrace(variable)

                if catch_exceptions:
                    for exception_collection in exception_collections:
                        exception_collection.removeCurrentVariableTrace(variable)

                trace_collection.removeCurrentVariableTrace(variable)

        if catch_exceptions:
            for exception_collection in exception_collections:
                trace_collection.onExceptionRaiseExit(None, exception_collection)

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
                "%s '%s' is now simple return, use directly."
                % (outline_description, self.name),
            )

        if first_statement.isStatementReturn():
            return (
                first_statement.subnode_expression,
                "new_expression",
                "%s '%s' is now simple return, use directly."
                % (outline_description, self.name),
            )

        if first_statement.isStatementRaiseException():
            assert first_statement.subnode_exception_value is None, first_statement
            result = ExpressionRaiseException(
                exception_type=first_statement.subnode_exception_type,
                source_ref=first_statement.getSourceReference(),
            )

            return (
                result,
                "new_expression",
                "%s is now exception raise, use directly." % outline_description,
            )

        # TODO: Function outline may become too trivial to outline and return
        # collections may tell us something.
        return self, None, None

    def mayRaiseException(self, exception_type):
        return self.subnode_body.mayRaiseException(exception_type)

    def willRaiseAnyException(self):
        return self.subnode_body.willRaiseAnyException()


class ExpressionOutlineBody(
    ExpressionOutlineMixin, ChildHavingBodyOptionalMixin, ExpressionBase
):
    """Outlined expression code.

    Executes a statement sequence inline within the calling provider's
    context and produces its expression value via return statements.
    """

    kind = "EXPRESSION_OUTLINE_BODY"

    named_children = ("body|optional+setter",)

    __slots__ = ("provider", "name", "temp_scope")

    @staticmethod
    def isExpressionOutlineBody():
        return True

    def __init__(self, provider, name, source_ref, body=None):
        assert name != ""

        ChildHavingBodyOptionalMixin.__init__(self, body=body)

        ExpressionBase.__init__(self, source_ref)

        self.provider = provider
        self.name = name

        self.temp_scope = None

        # Hack: This allows some APIs to work although this is not yet
        # officially a child yet. Important during building.
        self.parent = provider

    def getContainingClassDictCreation(self):
        return self.getParentVariableProvider().getContainingClassDictCreation()

    def makeClone(self):
        result = self.__class__(
            provider=getClonedProvider(self.provider),
            name=self.name,
            body=None,
            source_ref=self.source_ref,
        )

        effective_source_ref = self.getCompatibleSourceReference()
        if effective_source_ref is not self.source_ref:
            result.setCompatibleSourceReference(effective_source_ref)

        if self.subnode_body is not None:
            with withClonedProvider(self, result):
                result.setChildBody(self.subnode_body.makeClone())

        variable_translations = self._cloneTempVariables(result)

        if variable_translations:
            updateVariableUsage(
                provider=result,
                old_locals_scope=None,
                new_locals_scope=None,
                variable_translations=variable_translations,
            )

            updateFunctionBodyReferences(
                provider=result,
                old_provider=self,
                variable_translations=variable_translations,
                code_name_translations={},
            )

        return result

    def computeExpressionRaw(self, trace_collection):
        owning_module = self.getParentModule()

        # Make sure the owning module is added to the used set. This is most
        # important for helper functions, or modules, which otherwise have
        # become unused.
        addUsedModule(
            module=owning_module,
            using_module=None,
            usage_tag="outline",
            reason="Owning module",
            source_ref=self.source_ref,
        )

        # The outline body executes inline within the calling context, and the
        # expression it returns can reference its temporary variables, so those
        # cannot be removed from the trace collection after the body was computed.
        return self._computeOutlineBody(
            trace_collection=trace_collection,
            need_removal=(),
            outline_description="Outline",
        )

    def collectVariableAccesses(self, emit_variable):
        local_temp_variables = self.getEntryPoint().getTempVariables(self)

        def local_emit(variable):
            if variable not in local_temp_variables:
                emit_variable(variable)

        self.subnode_body.collectVariableAccesses(local_emit)


class ExpressionOutlineFunctionBase(ExpressionOutlineMixin, ExpressionFunctionBodyBase):
    """Outlined function code.

    This is for a call to a function to be called in-line to be executed
    in a specific context. It contains an exclusively owned function body,
    that has no other references, and can be considered part of the calling
    context.

    As normal function it must return a value, to use as expression value,
    but we know we only exist once.

    Once this has no frame, it can be changed to a mere outline expression.
    """

    __slots__ = ("temp_scope",)

    def __init__(self, provider, name, body, code_prefix, source_ref, flags=None):
        ExpressionFunctionBodyBase.__init__(
            self,
            provider=provider,
            name=name,
            body=body,
            code_prefix=code_prefix,
            flags=flags,
            source_ref=source_ref,
        )

        self.temp_scope = None

    @staticmethod
    def isExpressionOutlineFunctionBase():
        return True

    @staticmethod
    def willRaiseAnyException():
        # The outline function as an expression only creates the function
        # object, and it does not execute its body as part of that, so it
        # cannot raise by itself.
        return False

    def _getCloneDetails(self):
        result = self.getDetails()
        result["provider"] = getClonedProvider(result["provider"])
        result["name"] += "_clone"

        return result

    def makeClone(self):
        result = self.__class__(
            source_ref=self.source_ref, body=None, **self._getCloneDetails()
        )

        effective_source_ref = self.getCompatibleSourceReference()
        if effective_source_ref is not self.source_ref:
            result.setCompatibleSourceReference(effective_source_ref)

        if self.subnode_body is not None:
            with withClonedProvider(self, result):
                result.setChildBody(self.subnode_body.makeClone())

        # pylint: disable=assigning-non-slot
        result.locals_scope, variable_translations = self.locals_scope.makeClone(
            new_owner=result
        )

        variable_translations.update(self._cloneTempVariables(result))

        # Taken variables are not owned by the outline either, replicate
        # them for the clone, translating the temporary variables, which
        # are cloned above, but keeping e.g. module variables as they are.
        for taken_variable in self.taken:
            result.taken.add(variable_translations.get(taken_variable, taken_variable))

        updateVariableUsage(
            provider=result,
            old_locals_scope=self.locals_scope,
            new_locals_scope=result.locals_scope,
            variable_translations=variable_translations,
        )

        updateFunctionBodyReferences(
            provider=result,
            old_provider=self,
            variable_translations=variable_translations,
            code_name_translations={self.getCodeName(): result.getCodeName()},
        )

        if self.isExpressionClassBodyBase():
            self._copyClassBodyCloneState(
                result=result, variable_translations=variable_translations
            )

        return result

    def computeExpressionRaw(self, trace_collection):
        need_removal = set()

        for variable in self.locals_scope.variables.values():
            assert variable not in trace_collection.variable_actives, variable

            trace_collection.initVariableLate(variable)
            need_removal.add(variable)

        for variable in self.locals_scope.local_variables.values():
            assert variable not in trace_collection.variable_actives, variable

            trace_collection.initVariableLate(variable)
            need_removal.add(variable)

        for variable in self.taken:
            if variable not in trace_collection.variable_actives:
                trace_collection.initVariableLate(variable)
                need_removal.add(variable)

        for variable in self.getEntryPoint().getTempVariables(self):
            if variable not in trace_collection.variable_actives:
                trace_collection.initVariableLate(variable)
                need_removal.add(variable)

        trace_collection.addOutlineFunction(self)

        return self._computeOutlineBody(
            trace_collection=trace_collection,
            need_removal=need_removal,
            outline_description="Outline function",
        )

    def collectVariableAccesses(self, emit_variable):
        local_variable_values = self.getLocalsScope().local_variables.values()
        local_temp_variables = self.getEntryPoint().getTempVariables(self)

        def local_emit(variable):
            if (
                variable not in local_variable_values
                and variable not in local_temp_variables
            ):
                emit_variable(variable)

        self.subnode_body.collectVariableAccesses(local_emit)

    def getTraceCollection(self):
        return self.provider.getTraceCollection()

    def getClosureVariable(self, variable_name):
        return self.provider.getVariableForReference(variable_name=variable_name)

    def getLocalsScope(self):
        # TODO: Make this abstract and static for ones that do not
        # have a locals scope.
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

    def getChildQualname(self, function_name):
        return self.provider.getChildQualname(function_name)


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
