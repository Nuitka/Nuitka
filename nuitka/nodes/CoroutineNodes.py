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
from nuitka.utils import Utils

from .Checkers import checkStatementsSequenceOrNone
from .FunctionNodes import ExpressionFunctionBodyBase
from .NodeBases import ChildrenHavingMixin, ExpressionMixin, NodeBase
from .IndicatorMixins import (
    MarkLocalsDictIndicator,
    MarkUnoptimizedFunctionIndicator
)


class ExpressionCoroutineCreation(NodeBase, ExpressionMixin):
    kind = "EXPRESSION_COROUTINE_CREATION"

    def __init__(self, coroutine_body, source_ref):
        assert coroutine_body.isExpressionCoroutineBody()

        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

        self.coroutine_body = coroutine_body

    def getName(self):
        return self.coroutine_body.getName()

    def getDetails(self):
        return {
            "coroutine_body" : self.coroutine_body
        }

    def getDetailsForDisplay(self):
        return {
            "coroutine" : self.coroutine_body.getCodeName()
        }

    def getCoroutineBody(self):
        return self.coroutine_body

    def computeExpressionRaw(self, constraint_collection):
        function_body = self.getCoroutineBody()

        owning_module = function_body.getParentModule()

        # Make sure the owning module is added to the used set. This is most
        # important for helper functions, or modules, which otherwise have
        # become unused.
        from nuitka.ModuleRegistry import addUsedModule
        addUsedModule(owning_module)

        owning_module.addUsedFunction(function_body)

        from nuitka.optimizations.TraceCollections import \
            ConstraintCollectionFunction

        # TODO: Doesn't this mean, we can do this multiple times by doing it
        # in the reference. We should do it in the body, and there we should
        # limit us to only doing it once per module run, e.g. being based on
        # presence in used functions of the module already.
        old_collection = function_body.constraint_collection

        function_body.constraint_collection = ConstraintCollectionFunction(
            parent        = constraint_collection,
            function_body = function_body
        )

        statements_sequence = function_body.getBody()

        if statements_sequence is not None and \
           not statements_sequence.getStatements():
            function_body.setStatements(None)
            statements_sequence = None

        if statements_sequence is not None:
            result = statements_sequence.computeStatementsSequence(
                constraint_collection = function_body.constraint_collection
            )

            if result is not statements_sequence:
                function_body.setBody(result)

        function_body.constraint_collection.updateFromCollection(old_collection)

        # TODO: Function collection may now know something.
        return self, None, None

    def mayRaiseException(self, exception_type):
        return False

    def mayHaveSideEffects(self):
        return False


class ExpressionCoroutineBody(ExpressionFunctionBodyBase,
                              MarkLocalsDictIndicator,
                              MarkUnoptimizedFunctionIndicator):
    kind = "EXPRESSION_COROUTINE_BODY"

    named_children = (
        "body",
    )

    checkers = {
        # TODO: Is "None" really an allowed value.
        "body" : checkStatementsSequenceOrNone
    }

    if Utils.python_version >= 340:
        qualname_setup = None

    def __init__(self, provider, name, source_ref):
        while provider.isExpressionOutlineBody():
            provider = provider.getParentVariableProvider()

        ExpressionFunctionBodyBase.__init__(
            self,
            provider    = provider,
            name        = name,
            code_prefix = "coroutine",
            is_class    = False,
            source_ref  = source_ref
        )

        MarkLocalsDictIndicator.__init__(self)

        MarkUnoptimizedFunctionIndicator.__init__(self)

    def getFunctionName(self):
        return self.name

    def getFunctionQualname(self):
        return self.getParentVariableProvider().getFunctionQualname()

    @staticmethod
    def isExpressionFunctionBody():
        return True

    @staticmethod
    def needsCreation():
        return False

    getBody = ChildrenHavingMixin.childGetter("body")
    setBody = ChildrenHavingMixin.childSetter("body")
