#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
# We are not avoiding these in generated code at all
# pylint: disable=I0021,too-many-lines
# pylint: disable=I0021,line-too-long
# pylint: disable=I0021,too-many-instance-attributes
# pylint: disable=I0021,too-many-return-statements


"""Children having expression bases

WARNING, this code is GENERATED. Modify the template ChildrenHavingMixin.py.j2 instead!

spell-checker: ignore append capitalize casefold center clear copy count decode encode endswith expandtabs extend find format formatmap get haskey index insert isalnum isalpha isascii isdecimal isdigit isidentifier islower isnumeric isprintable isspace istitle isupper items iteritems iterkeys itervalues join keys ljust lower lstrip maketrans partition pop popitem remove replace reverse rfind rindex rjust rpartition rsplit rstrip setdefault sort split splitlines startswith strip swapcase title translate update upper values viewitems viewkeys viewvalues zfill
spell-checker: ignore args chars count default delete encoding end errors fillchar index item iterable keepends key maxsplit new old pairs prefix sep start stop sub suffix table tabsize value width
"""


# Loop unrolling over child names, pylint: disable=too-many-branches

from abc import abstractmethod

from .ExpressionBases import ExpressionBase
from .NodeMakingHelpers import wrapExpressionWithSideEffects


class NoChildHavingFinalNoRaiseMixin(ExpressionBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionImportlibMetadataBackportEntryPointValueRef
    #   ExpressionImportlibMetadataEntryPointValueRef

    def finalize(self):
        del self.parent

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        return self, None, None

    @staticmethod
    def mayRaiseExceptionOperation():
        return False

    @staticmethod
    def mayRaiseException(exception_type):
        return False


# Assign the names that are easier to import with a stable name.
ExpressionImportlibMetadataBackportEntryPointValueRefBase = (
    NoChildHavingFinalNoRaiseMixin
)
ExpressionImportlibMetadataEntryPointValueRefBase = NoChildHavingFinalNoRaiseMixin


class ChildHavingArgsTupleFinalNoRaiseMixin(ExpressionBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinMakeException

    def __init__(self, args, source_ref):
        assert type(args) is tuple

        for val in args:
            val.parent = self

        self.subnode_args = args

        ExpressionBase.__init__(self, source_ref)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return self.subnode_args

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("args", self.subnode_args),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_args
        if old_node in value:
            if new_node is not None:
                new_node.parent = self

                self.subnode_args = tuple(
                    (val if val is not old_node else new_node) for val in value
                )
            else:
                self.subnode_args = tuple(val for val in value if val is not old_node)

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "args": tuple(v.makeClone() for v in self.subnode_args),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        for c in self.subnode_args:
            c.finalize()
        del self.subnode_args

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expressions, as they are evaluated before
        # the actual operation.
        old_subnode_args = self.subnode_args

        for sub_expression in old_subnode_args:
            expression = trace_collection.onExpression(sub_expression)

            if expression.willRaiseAnyException():
                wrapped_expression = wrapExpressionWithSideEffects(
                    side_effects=self.subnode_args[
                        : old_subnode_args.index(sub_expression)
                    ],
                    old_node=sub_expression,
                    new_node=expression,
                )

                return (
                    wrapped_expression,
                    "new_raise",
                    lambda: "For '%s' the child expression '%s' will raise."
                    % (self.getChildNameNice(), expression.getChildNameNice()),
                )

        return self, None, None

    @staticmethod
    def mayRaiseExceptionOperation():
        return False

    def mayRaiseException(self, exception_type):
        return any(
            value.mayRaiseException(exception_type) for value in self.subnode_args
        )


# Assign the names that are easier to import with a stable name.
ExpressionBuiltinMakeExceptionBase = ChildHavingArgsTupleFinalNoRaiseMixin


class ChildrenHavingArgsTupleNameOptionalPathOptionalFinalNoRaiseMixin(ExpressionBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinMakeExceptionImportError

    def __init__(self, args, name, path, source_ref):
        assert type(args) is tuple

        for val in args:
            val.parent = self

        self.subnode_args = args

        if name is not None:
            name.parent = self

        self.subnode_name = name

        if path is not None:
            path.parent = self

        self.subnode_path = path

        ExpressionBase.__init__(self, source_ref)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.extend(self.subnode_args)
        value = self.subnode_name
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_path
        if value is None:
            pass
        else:
            result.append(value)
        return tuple(result)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("args", self.subnode_args),
            ("name", self.subnode_name),
            ("path", self.subnode_path),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_args
        if old_node in value:
            if new_node is not None:
                new_node.parent = self

                self.subnode_args = tuple(
                    (val if val is not old_node else new_node) for val in value
                )
            else:
                self.subnode_args = tuple(val for val in value if val is not old_node)

            return

        value = self.subnode_name
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_name = new_node

            return

        value = self.subnode_path
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_path = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "args": tuple(v.makeClone() for v in self.subnode_args),
            "name": self.subnode_name.makeClone()
            if self.subnode_name is not None
            else None,
            "path": self.subnode_path.makeClone()
            if self.subnode_path is not None
            else None,
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        for c in self.subnode_args:
            c.finalize()
        del self.subnode_args
        if self.subnode_name is not None:
            self.subnode_name.finalize()
        del self.subnode_name
        if self.subnode_path is not None:
            self.subnode_path.finalize()
        del self.subnode_path

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expressions, as they are evaluated before
        # the actual operation.
        for count, sub_expression in enumerate(self.getVisitableNodes()):
            expression = trace_collection.onExpression(sub_expression)

            if expression.willRaiseAnyException():
                sub_expressions = self.getVisitableNodes()

                wrapped_expression = wrapExpressionWithSideEffects(
                    side_effects=sub_expressions[:count],
                    old_node=sub_expression,
                    new_node=expression,
                )

                return (
                    wrapped_expression,
                    "new_raise",
                    lambda: "For '%s' the child expression '%s' will raise."
                    % (self.getChildNameNice(), expression.getChildNameNice()),
                )

        return self, None, None

    @staticmethod
    def mayRaiseExceptionOperation():
        return False

    def mayRaiseException(self, exception_type):
        return (
            any(value.mayRaiseException(exception_type) for value in self.subnode_args)
            or (
                self.subnode_name is not None
                and self.subnode_name.mayRaiseException(exception_type)
            )
            or (
                self.subnode_path is not None
                and self.subnode_path.mayRaiseException(exception_type)
            )
        )


# Assign the names that are easier to import with a stable name.
ExpressionBuiltinMakeExceptionImportErrorBase = (
    ChildrenHavingArgsTupleNameOptionalPathOptionalFinalNoRaiseMixin
)


class ChildrenHavingCallableArgSentinelFinalMixin(ExpressionBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinIter2

    def __init__(self, callable_arg, sentinel, source_ref):
        callable_arg.parent = self

        self.subnode_callable_arg = callable_arg

        sentinel.parent = self

        self.subnode_sentinel = sentinel

        ExpressionBase.__init__(self, source_ref)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_callable_arg,
            self.subnode_sentinel,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("callable_arg", self.subnode_callable_arg),
            ("sentinel", self.subnode_sentinel),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_callable_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_callable_arg = new_node

            return

        value = self.subnode_sentinel
        if old_node is value:
            new_node.parent = self

            self.subnode_sentinel = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "callable_arg": self.subnode_callable_arg.makeClone(),
            "sentinel": self.subnode_sentinel.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_callable_arg.finalize()
        del self.subnode_callable_arg
        self.subnode_sentinel.finalize()
        del self.subnode_sentinel

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expressions, as they are evaluated before
        # the actual operation.
        for count, sub_expression in enumerate(self.getVisitableNodes()):
            expression = trace_collection.onExpression(sub_expression)

            if expression.willRaiseAnyException():
                sub_expressions = self.getVisitableNodes()

                wrapped_expression = wrapExpressionWithSideEffects(
                    side_effects=sub_expressions[:count],
                    old_node=sub_expression,
                    new_node=expression,
                )

                return (
                    wrapped_expression,
                    "new_raise",
                    lambda: "For '%s' the child expression '%s' will raise."
                    % (self.getChildNameNice(), expression.getChildNameNice()),
                )

        trace_collection.onExceptionRaiseExit(BaseException)
        return self, None, None


# Assign the names that are easier to import with a stable name.
ExpressionBuiltinIter2Base = ChildrenHavingCallableArgSentinelFinalMixin


class ChildHavingElementsTupleFinalNoRaiseMixin(ExpressionBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionImportlibMetadataBackportEntryPointsValueRef
    #   ExpressionImportlibMetadataEntryPointsValueRef

    def __init__(self, elements, source_ref):
        assert type(elements) is tuple

        for val in elements:
            val.parent = self

        self.subnode_elements = elements

        ExpressionBase.__init__(self, source_ref)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return self.subnode_elements

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("elements", self.subnode_elements),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_elements
        if old_node in value:
            if new_node is not None:
                new_node.parent = self

                self.subnode_elements = tuple(
                    (val if val is not old_node else new_node) for val in value
                )
            else:
                self.subnode_elements = tuple(
                    val for val in value if val is not old_node
                )

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "elements": tuple(v.makeClone() for v in self.subnode_elements),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        for c in self.subnode_elements:
            c.finalize()
        del self.subnode_elements

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expressions, as they are evaluated before
        # the actual operation.
        old_subnode_elements = self.subnode_elements

        for sub_expression in old_subnode_elements:
            expression = trace_collection.onExpression(sub_expression)

            if expression.willRaiseAnyException():
                wrapped_expression = wrapExpressionWithSideEffects(
                    side_effects=self.subnode_elements[
                        : old_subnode_elements.index(sub_expression)
                    ],
                    old_node=sub_expression,
                    new_node=expression,
                )

                return (
                    wrapped_expression,
                    "new_raise",
                    lambda: "For '%s' the child expression '%s' will raise."
                    % (self.getChildNameNice(), expression.getChildNameNice()),
                )

        return self, None, None

    @staticmethod
    def mayRaiseExceptionOperation():
        return False

    def mayRaiseException(self, exception_type):
        return any(
            value.mayRaiseException(exception_type) for value in self.subnode_elements
        )


# Assign the names that are easier to import with a stable name.
ExpressionImportlibMetadataBackportEntryPointsValueRefBase = (
    ChildHavingElementsTupleFinalNoRaiseMixin
)
ExpressionImportlibMetadataEntryPointsValueRefBase = (
    ChildHavingElementsTupleFinalNoRaiseMixin
)


class ChildHavingExpressionAttributeNameMixin(ExpressionBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionAttributeLookup
    #   ExpressionAttributeLookupSpecial

    def __init__(self, expression, attribute_name, source_ref):
        expression.parent = self

        self.subnode_expression = expression

        self.attribute_name = attribute_name

        ExpressionBase.__init__(self, source_ref)

    def getDetails(self):
        return {
            "attribute_name": self.attribute_name,
        }

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_expression,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("expression", self.subnode_expression),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_expression
        if old_node is value:
            new_node.parent = self

            self.subnode_expression = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "expression": self.subnode_expression.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_expression.finalize()
        del self.subnode_expression

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_expression)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    @abstractmethod
    def computeExpression(self, trace_collection):
        """Must be overloaded for non-final node."""


# Assign the names that are easier to import with a stable name.
ExpressionAttributeLookupBase = ChildHavingExpressionAttributeNameMixin
ExpressionAttributeLookupSpecialBase = ChildHavingExpressionAttributeNameMixin


class ChildHavingListArgNoRaiseMixin(ExpressionBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionListOperationClear
    #   ExpressionListOperationReverse

    def __init__(self, list_arg, source_ref):
        list_arg.parent = self

        self.subnode_list_arg = list_arg

        ExpressionBase.__init__(self, source_ref)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_list_arg,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("list_arg", self.subnode_list_arg),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_list_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_list_arg = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "list_arg": self.subnode_list_arg.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_list_arg.finalize()
        del self.subnode_list_arg

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_list_arg)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    @staticmethod
    def mayRaiseExceptionOperation():
        return False

    def mayRaiseException(self, exception_type):
        return self.subnode_list_arg.mayRaiseException(exception_type)

    @abstractmethod
    def computeExpression(self, trace_collection):
        """Must be overloaded for non-final node."""


# Assign the names that are easier to import with a stable name.
ExpressionListOperationClearBase = ChildHavingListArgNoRaiseMixin
ExpressionListOperationReverseBase = ChildHavingListArgNoRaiseMixin


class ChildrenHavingListArgItemNoRaiseMixin(ExpressionBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionListOperationAppend

    def __init__(self, list_arg, item, source_ref):
        list_arg.parent = self

        self.subnode_list_arg = list_arg

        item.parent = self

        self.subnode_item = item

        ExpressionBase.__init__(self, source_ref)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_list_arg,
            self.subnode_item,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("list_arg", self.subnode_list_arg),
            ("item", self.subnode_item),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_list_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_list_arg = new_node

            return

        value = self.subnode_item
        if old_node is value:
            new_node.parent = self

            self.subnode_item = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "list_arg": self.subnode_list_arg.makeClone(),
            "item": self.subnode_item.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_list_arg.finalize()
        del self.subnode_list_arg
        self.subnode_item.finalize()
        del self.subnode_item

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expressions, as they are evaluated before
        # the actual operation.
        for count, sub_expression in enumerate(self.getVisitableNodes()):
            expression = trace_collection.onExpression(sub_expression)

            if expression.willRaiseAnyException():
                sub_expressions = self.getVisitableNodes()

                wrapped_expression = wrapExpressionWithSideEffects(
                    side_effects=sub_expressions[:count],
                    old_node=sub_expression,
                    new_node=expression,
                )

                return (
                    wrapped_expression,
                    "new_raise",
                    lambda: "For '%s' the child expression '%s' will raise."
                    % (self.getChildNameNice(), expression.getChildNameNice()),
                )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    @staticmethod
    def mayRaiseExceptionOperation():
        return False

    def mayRaiseException(self, exception_type):
        return self.subnode_list_arg.mayRaiseException(
            exception_type
        ) or self.subnode_item.mayRaiseException(exception_type)

    @abstractmethod
    def computeExpression(self, trace_collection):
        """Must be overloaded for non-final node."""


# Assign the names that are easier to import with a stable name.
ExpressionListOperationAppendBase = ChildrenHavingListArgItemNoRaiseMixin


class ChildrenHavingListArgValueFinalNoRaiseMixin(ExpressionBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionListOperationCount

    def __init__(self, list_arg, value, source_ref):
        list_arg.parent = self

        self.subnode_list_arg = list_arg

        value.parent = self

        self.subnode_value = value

        ExpressionBase.__init__(self, source_ref)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_list_arg,
            self.subnode_value,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("list_arg", self.subnode_list_arg),
            ("value", self.subnode_value),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_list_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_list_arg = new_node

            return

        value = self.subnode_value
        if old_node is value:
            new_node.parent = self

            self.subnode_value = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "list_arg": self.subnode_list_arg.makeClone(),
            "value": self.subnode_value.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_list_arg.finalize()
        del self.subnode_list_arg
        self.subnode_value.finalize()
        del self.subnode_value

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expressions, as they are evaluated before
        # the actual operation.
        for count, sub_expression in enumerate(self.getVisitableNodes()):
            expression = trace_collection.onExpression(sub_expression)

            if expression.willRaiseAnyException():
                sub_expressions = self.getVisitableNodes()

                wrapped_expression = wrapExpressionWithSideEffects(
                    side_effects=sub_expressions[:count],
                    old_node=sub_expression,
                    new_node=expression,
                )

                return (
                    wrapped_expression,
                    "new_raise",
                    lambda: "For '%s' the child expression '%s' will raise."
                    % (self.getChildNameNice(), expression.getChildNameNice()),
                )

        return self, None, None

    @staticmethod
    def mayRaiseExceptionOperation():
        return False

    def mayRaiseException(self, exception_type):
        return self.subnode_list_arg.mayRaiseException(
            exception_type
        ) or self.subnode_value.mayRaiseException(exception_type)


# Assign the names that are easier to import with a stable name.
ExpressionListOperationCountBase = ChildrenHavingListArgValueFinalNoRaiseMixin


class ChildHavingPairsTupleFinalNoRaiseMixin(ExpressionBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionImportlibMetadataBackportSelectableGroupsValueRef
    #   ExpressionImportlibMetadataSelectableGroupsValueRef

    def __init__(self, pairs, source_ref):
        assert type(pairs) is tuple

        for val in pairs:
            val.parent = self

        self.subnode_pairs = pairs

        ExpressionBase.__init__(self, source_ref)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return self.subnode_pairs

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("pairs", self.subnode_pairs),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_pairs
        if old_node in value:
            if new_node is not None:
                new_node.parent = self

                self.subnode_pairs = tuple(
                    (val if val is not old_node else new_node) for val in value
                )
            else:
                self.subnode_pairs = tuple(val for val in value if val is not old_node)

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "pairs": tuple(v.makeClone() for v in self.subnode_pairs),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        for c in self.subnode_pairs:
            c.finalize()
        del self.subnode_pairs

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expressions, as they are evaluated before
        # the actual operation.
        old_subnode_pairs = self.subnode_pairs

        for sub_expression in old_subnode_pairs:
            expression = trace_collection.onExpression(sub_expression)

            if expression.willRaiseAnyException():
                wrapped_expression = wrapExpressionWithSideEffects(
                    side_effects=self.subnode_pairs[
                        : old_subnode_pairs.index(sub_expression)
                    ],
                    old_node=sub_expression,
                    new_node=expression,
                )

                return (
                    wrapped_expression,
                    "new_raise",
                    lambda: "For '%s' the child expression '%s' will raise."
                    % (self.getChildNameNice(), expression.getChildNameNice()),
                )

        return self, None, None

    @staticmethod
    def mayRaiseExceptionOperation():
        return False

    def mayRaiseException(self, exception_type):
        return any(
            value.mayRaiseException(exception_type) for value in self.subnode_pairs
        )


# Assign the names that are easier to import with a stable name.
ExpressionImportlibMetadataBackportSelectableGroupsValueRefBase = (
    ChildHavingPairsTupleFinalNoRaiseMixin
)
ExpressionImportlibMetadataSelectableGroupsValueRefBase = (
    ChildHavingPairsTupleFinalNoRaiseMixin
)


class ChildHavingValueFinalNoRaiseMixin(ExpressionBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinClassmethod
    #   ExpressionBuiltinStaticmethod

    def __init__(self, value, source_ref):
        value.parent = self

        self.subnode_value = value

        ExpressionBase.__init__(self, source_ref)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_value,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("value", self.subnode_value),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_value
        if old_node is value:
            new_node.parent = self

            self.subnode_value = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "value": self.subnode_value.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_value.finalize()
        del self.subnode_value

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_value)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        return self, None, None

    @staticmethod
    def mayRaiseExceptionOperation():
        return False

    def mayRaiseException(self, exception_type):
        return self.subnode_value.mayRaiseException(exception_type)


# Assign the names that are easier to import with a stable name.
ExpressionBuiltinClassmethodBase = ChildHavingValueFinalNoRaiseMixin
ExpressionBuiltinStaticmethodBase = ChildHavingValueFinalNoRaiseMixin
