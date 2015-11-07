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
""" Operations on Containers.

"""

from nuitka.Builtins import calledWithBuiltinArgumentNamesDecorator

from .NodeBases import ExpressionChildrenHavingBase, StatementChildrenHavingBase


class ExpressionListOperationAppend(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_LIST_OPERATION_APPEND"

    named_children = (
        "list",
        "value"
    )

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, list_arg, value, source_ref):
        assert list_arg is not None
        assert value is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "list"  : list_arg,
                "value" : value
            },
            source_ref = source_ref
        )

    getList = ExpressionChildrenHavingBase.childGetter("list")
    getValue = ExpressionChildrenHavingBase.childGetter("value")

    def computeExpression(self, constraint_collection):
        constraint_collection.removeKnowledge(self.getList())

        return self, None, None


class ExpressionListOperationExtend(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_LIST_OPERATION_EXTEND"

    named_children = (
        "list",
        "value"
    )

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, list_arg, value, source_ref):
        assert list_arg is not None
        assert value is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "list"  : list_arg,
                "value" : value
            },
            source_ref = source_ref
        )

    getList = ExpressionChildrenHavingBase.childGetter("list")
    getValue = ExpressionChildrenHavingBase.childGetter("value")

    def computeExpression(self, constraint_collection):
        constraint_collection.removeKnowledge(self.getList())

        return self, None, None


class ExpressionListOperationPop(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_LIST_OPERATION_POP"

    named_children = (
        "list",
    )

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, list_arg, source_ref):
        assert list_arg is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "list"  : list_arg,
            },
            source_ref = source_ref
        )

    getList = ExpressionChildrenHavingBase.childGetter("list")

    def computeExpression(self, constraint_collection):
        # We might be able to tell that element, or know that it cannot exist
        # and raise an exception instead.
        constraint_collection.removeKnowledge(self.getList())

        return self, None, None


class ExpressionSetOperationAdd(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_SET_OPERATION_ADD"

    named_children = (
        "set",
        "value"
    )

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, set_arg, value, source_ref):
        assert set_arg is not None
        assert value is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "set"   : set_arg,
                "value" : value
            },
            source_ref = source_ref
        )

    getSet = ExpressionChildrenHavingBase.childGetter(
        "set"
    )
    getValue = ExpressionChildrenHavingBase.childGetter(
        "value"
    )

    def computeExpression(self, constraint_collection):
        constraint_collection.removeKnowledge(self.getSet())

        return self, None, None


class ExpressionSetOperationUpdate(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_SET_OPERATION_UPDATE"

    named_children = (
        "set",
        "value"
    )

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, set_arg, value, source_ref):
        assert set_arg is not None
        assert value is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "set"  : set_arg,
                "value" : value
            },
            source_ref = source_ref
        )

    getSet = ExpressionChildrenHavingBase.childGetter(
        "set"
    )
    getValue = ExpressionChildrenHavingBase.childGetter(
        "value"
    )

    def computeExpression(self, constraint_collection):
        constraint_collection.removeKnowledge(self.getSet())

        return self, None, None


class ExpressionDictOperationSet(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_DICT_OPERATION_SET"

    named_children = (
        "dict",
        "key",
        "value"
    )

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, dict_arg, key, value, source_ref):
        assert dict_arg is not None
        assert key is not None
        assert value is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "dict"  : dict_arg,
                "key"   : key,
                "value" : value
            },
            source_ref = source_ref
        )

    getDict = ExpressionChildrenHavingBase.childGetter("dict")
    getKey = ExpressionChildrenHavingBase.childGetter("key")
    getValue = ExpressionChildrenHavingBase.childGetter("value")

    def computeExpression(self, constraint_collection):
        constraint_collection.removeKnowledge(self.getDict())

        return self, None, None


class StatementDictOperationRemove(StatementChildrenHavingBase):
    kind = "STATEMENT_DICT_OPERATION_REMOVE"

    named_children = (
        "dict",
        "key"
    )

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, dict_arg, key, source_ref):
        assert dict_arg is not None
        assert key is not None

        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "dict"    : dict_arg,
                "key"     : key,
            },
            source_ref = source_ref
        )

    getDict = StatementChildrenHavingBase.childGetter("dict")
    getKey = StatementChildrenHavingBase.childGetter("key")

    def computeStatement(self, constraint_collection):
        constraint_collection.onExpression(self.getDict())
        dicte = self.getDict()

        if dicte.willRaiseException(BaseException):
            from .NodeMakingHelpers import \
              makeStatementExpressionOnlyReplacementNode

            result = makeStatementExpressionOnlyReplacementNode(
                expression = dicte,
                node       = self
            )

            return result, "new_raise", """\
Dictionary remove already raises implicitly accessing dictionary."""

        constraint_collection.onExpression(self.getKey())
        key = self.getKey()

        if key.willRaiseException(BaseException):
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            result = makeStatementOnlyNodesFromExpressions(
                expressions = (
                    dicte,
                    key
                )
            )

            return result, "new_raise", """
Dictionary remove already raises implicitly building key."""

        # TODO: Be less lossy about it.
        constraint_collection.removeKnowledge(dicte)

        return self, None, None


class ExpressionDictOperationGet(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_DICT_OPERATION_GET"

    named_children = (
        "dict",
        "key"
    )

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, dict_arg, key, source_ref):
        assert dict_arg is not None
        assert key is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "dict" : dict_arg,
                "key"  : key,
            },
            source_ref = source_ref
        )

    getDict = ExpressionChildrenHavingBase.childGetter("dict")
    getKey = ExpressionChildrenHavingBase.childGetter("key")

    def computeExpression(self, constraint_collection):
        return self, None, None


class ExpressionDictOperationUpdate(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_DICT_OPERATION_UPDATE"

    named_children = (
        "dict",
        "value"
    )

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, dict_arg, value, source_ref):
        assert dict_arg is not None
        assert value is not None

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "dict"  : dict_arg,
                "value" : value
            },
            source_ref = source_ref
        )

    getSet = ExpressionChildrenHavingBase.childGetter(
        "dict"
    )
    getValue = ExpressionChildrenHavingBase.childGetter(
        "value"
    )

    def computeExpression(self, constraint_collection):
        constraint_collection.removeKnowledge(self.getSet())

        return self, None, None
