#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .NodeBases import ChildrenHavingMixin, ExpressionChildrenHavingBase


class ExpressionOutlineBody(ExpressionChildrenHavingBase):
    """ Outlined code.

        This is for a call to a piece of code to be executed in a specific
        context. It contains an exclusively owned function body, that has
        no other references, and can be considered part of the calling
        context.

        It must return a value, to use as expression value.
    """

    kind = "EXPRESSION_OUTLINE_BODY"

    named_children = (
        "body",
    )

    def __init__(self, provider, name, source_ref, body = None):
        assert name != ""

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "body" : body
            },
            source_ref = source_ref
        )

        self.provider = provider
        self.name = name

        self.temp_scope = None

        # Hack: This allows some APIs to work although this is not yet
        # officially a child yet. Important during building.
        self.parent = provider

    def getDetails(self):
        return {
            "provider" : self.provider,
            "name"     : self.name
        }

    getBody = ChildrenHavingMixin.childGetter("body")
    setBody = ChildrenHavingMixin.childSetter("body")

    def getOutlineTempScope(self):
        # We use our own name as a temp_scope, cached from the parent, if the
        # scope is None.
        if self.temp_scope is None:
            self.temp_scope = self.provider.allocateTempScope(self.name)

        return self.temp_scope

    def allocateTempVariable(self, temp_scope, name):
        if temp_scope is None:
            temp_scope = self.getOutlineTempScope()

        return self.provider.allocateTempVariable(
            temp_scope = temp_scope,
            name       = name
        )

    def allocateTempScope(self, name):

        # Let's scope the temporary scopes by the outline they come from.
        return self.provider.allocateTempScope(
            name = self.name + '$' + name
        )

    def getContainingClassDictCreation(self):
        return self.getParentVariableProvider().getContainingClassDictCreation()

    def computeExpressionRaw(self, constraint_collection):
        owning_module = self.getParentModule()

        # Make sure the owning module is added to the used set. This is most
        # important for helper functions, or modules, which otherwise have
        # become unused.
        from nuitka.ModuleRegistry import addUsedModule
        addUsedModule(owning_module)

        abort_context = constraint_collection.makeAbortStackContext(
            catch_breaks     = False,
            catch_continues  = False,
            catch_returns    = True,
            catch_exceptions = False
        )

        with abort_context:
            body = self.getBody()

            result = body.computeStatementsSequence(
                constraint_collection = constraint_collection
            )

            if result is not body:
                self.setBody(result)
                body = result

            return_collections = constraint_collection.getFunctionReturnCollections()

        constraint_collection.mergeMultipleBranches(return_collections)

        if body.getStatements()[0].isStatementReturn():
            return (
                body.getStatements()[0].getExpression(),
                "new_expression",
                "Outline is now simple expression, use directly."
            )

        # TODO: Function outline may become too trivial to outline and return
        # collections may tell us something.
        return self, None, None
