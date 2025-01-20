#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# We are not avoiding these in generated code at all
# pylint: disable=I0021,line-too-long,too-many-instance-attributes,too-many-lines
# pylint: disable=I0021,too-many-arguments,too-many-return-statements,too-many-statements


"""Children having expression bases

WARNING, this code is GENERATED. Modify the template ChildrenHavingMixin.py.j2 instead!

spell-checker: ignore __prepare__ append args autograph capitalize casefold center chars
spell-checker: ignore clear copy count decode default delete dist distribution_name encode
spell-checker: ignore encoding end endswith errors exit_code expandtabs
spell-checker: ignore experimental_attributes experimental_autograph_options
spell-checker: ignore experimental_compile experimental_follow_type_hints
spell-checker: ignore experimental_implements experimental_relax_shapes extend fillchar
spell-checker: ignore find format format_map formatmap fromkeys func get group handle
spell-checker: ignore has_key haskey index input_signature insert isalnum isalpha isascii
spell-checker: ignore isdecimal isdigit isidentifier islower isnumeric isprintable isspace
spell-checker: ignore istitle isupper item items iterable iteritems iterkeys itervalues
spell-checker: ignore jit_compile join keepends key keys kwargs ljust lower lstrip
spell-checker: ignore maketrans maxsplit mode name new old p package
spell-checker: ignore package_or_requirement pairs partition path pop popitem prefix
spell-checker: ignore prepare reduce_retracing remove replace resource resource_name
spell-checker: ignore reverse rfind rindex rjust rpartition rsplit rstrip s sep setdefault
spell-checker: ignore sort split splitlines start startswith stop strip sub suffix
spell-checker: ignore swapcase table tabsize title translate update upper use_errno
spell-checker: ignore use_last_error value values viewitems viewkeys viewvalues width
spell-checker: ignore winmode zfill
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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""


# Assign the names that are easier to import with a stable name.
ExpressionImportlibMetadataBackportEntryPointValueRefBase = (
    NoChildHavingFinalNoRaiseMixin
)
ExpressionImportlibMetadataEntryPointValueRefBase = NoChildHavingFinalNoRaiseMixin


class NoChildHavingFinalNoRaiseNameMixin(ExpressionBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionTypeVariable

    def __init__(self, name, source_ref):
        self.name = name

        ExpressionBase.__init__(self, source_ref)

    def getDetails(self):
        return {
            "name": self.name,
        }

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return ()

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return ()

    def replaceChild(self, old_node, new_node):
        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {}

        values.update(self.getDetails())

        return values

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""


# Assign the names that are easier to import with a stable name.
ExpressionTypeVariableBase = NoChildHavingFinalNoRaiseNameMixin


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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        for element in self.subnode_args:
            element.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ExpressionBuiltinMakeExceptionBase = ChildHavingArgsTupleFinalNoRaiseMixin


class ChildrenHavingArgsTupleNameOptionalObjOptionalFinalNoRaiseForRaiseMixin(
    ExpressionBase
):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinMakeExceptionAttributeError

    def __init__(self, args, name, obj, for_raise, source_ref):
        assert type(args) is tuple

        for val in args:
            val.parent = self

        self.subnode_args = args

        if name is not None:
            name.parent = self

        self.subnode_name = name

        if obj is not None:
            obj.parent = self

        self.subnode_obj = obj

        self.for_raise = for_raise

        ExpressionBase.__init__(self, source_ref)

    def getDetails(self):
        return {
            "for_raise": self.for_raise,
        }

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.extend(self.subnode_args)
        value = self.subnode_name
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_obj
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
            ("obj", self.subnode_obj),
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

        value = self.subnode_obj
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_obj = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "args": tuple(v.makeClone() for v in self.subnode_args),
            "name": (
                self.subnode_name.makeClone() if self.subnode_name is not None else None
            ),
            "obj": (
                self.subnode_obj.makeClone() if self.subnode_obj is not None else None
            ),
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
        if self.subnode_obj is not None:
            self.subnode_obj.finalize()
        del self.subnode_obj

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
                self.subnode_obj is not None
                and self.subnode_obj.mayRaiseException(exception_type)
            )
        )

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        for element in self.subnode_args:
            element.collectVariableAccesses(emit_read, emit_write)
        subnode_name = self.subnode_name

        if subnode_name is not None:
            self.subnode_name.collectVariableAccesses(emit_read, emit_write)
        subnode_obj = self.subnode_obj

        if subnode_obj is not None:
            self.subnode_obj.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ExpressionBuiltinMakeExceptionAttributeErrorBase = (
    ChildrenHavingArgsTupleNameOptionalObjOptionalFinalNoRaiseForRaiseMixin
)


class ChildrenHavingArgsTupleNameOptionalPathOptionalFinalNoRaiseForRaiseMixin(
    ExpressionBase
):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinMakeExceptionImportError
    #   ExpressionBuiltinMakeExceptionModuleNotFoundError

    def __init__(self, args, name, path, for_raise, source_ref):
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

        self.for_raise = for_raise

        ExpressionBase.__init__(self, source_ref)

    def getDetails(self):
        return {
            "for_raise": self.for_raise,
        }

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
            "name": (
                self.subnode_name.makeClone() if self.subnode_name is not None else None
            ),
            "path": (
                self.subnode_path.makeClone() if self.subnode_path is not None else None
            ),
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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        for element in self.subnode_args:
            element.collectVariableAccesses(emit_read, emit_write)
        subnode_name = self.subnode_name

        if subnode_name is not None:
            self.subnode_name.collectVariableAccesses(emit_read, emit_write)
        subnode_path = self.subnode_path

        if subnode_path is not None:
            self.subnode_path.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ExpressionBuiltinMakeExceptionImportErrorBase = (
    ChildrenHavingArgsTupleNameOptionalPathOptionalFinalNoRaiseForRaiseMixin
)
ExpressionBuiltinMakeExceptionModuleNotFoundErrorBase = (
    ChildrenHavingArgsTupleNameOptionalPathOptionalFinalNoRaiseForRaiseMixin
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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_callable_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_sentinel.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ExpressionBuiltinIter2Base = ChildrenHavingCallableArgSentinelFinalMixin


class ChildHavingDistributionNameFinalChildrenMixin(ExpressionBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionImportlibMetadataBackportDistributionFailedCall
    #   ExpressionImportlibMetadataDistributionFailedCall

    def __init__(self, distribution_name, source_ref):
        distribution_name.parent = self

        self.subnode_distribution_name = distribution_name

        ExpressionBase.__init__(self, source_ref)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_distribution_name,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("distribution_name", self.subnode_distribution_name),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_distribution_name
        if old_node is value:
            new_node.parent = self

            self.subnode_distribution_name = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "distribution_name": self.subnode_distribution_name.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_distribution_name.finalize()
        del self.subnode_distribution_name

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    @abstractmethod
    def computeExpression(self, trace_collection):
        """Must be overloaded for non-final node."""

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_distribution_name.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ExpressionImportlibMetadataBackportDistributionFailedCallBase = (
    ChildHavingDistributionNameFinalChildrenMixin
)
ExpressionImportlibMetadataDistributionFailedCallBase = (
    ChildHavingDistributionNameFinalChildrenMixin
)


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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        for element in self.subnode_elements:
            element.collectVariableAccesses(emit_read, emit_write)


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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_expression.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ExpressionAttributeLookupBase = ChildHavingExpressionAttributeNameMixin
ExpressionAttributeLookupSpecialBase = ChildHavingExpressionAttributeNameMixin


class ChildrenHavingExpressionNameRaiseWaitConstantNameMixin(ExpressionBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinHasattr

    def __init__(self, expression, name, source_ref):
        expression.parent = self

        self.subnode_expression = expression

        name.parent = self

        self.subnode_name = name

        ExpressionBase.__init__(self, source_ref)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_expression,
            self.subnode_name,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("expression", self.subnode_expression),
            ("name", self.subnode_name),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_expression
        if old_node is value:
            new_node.parent = self

            self.subnode_expression = new_node

            return

        value = self.subnode_name
        if old_node is value:
            new_node.parent = self

            self.subnode_name = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "expression": self.subnode_expression.makeClone(),
            "name": self.subnode_name.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_expression.finalize()
        del self.subnode_expression
        self.subnode_name.finalize()
        del self.subnode_name

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

        if self.subnode_name.isCompileTimeConstant():
            try:
                return self.computeExpressionConstantName(trace_collection)
            finally:
                trace_collection.onExceptionRaiseExit(BaseException)

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    @abstractmethod
    def computeExpression(self, trace_collection):
        """Must be overloaded for non-final node."""

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_expression.collectVariableAccesses(emit_read, emit_write)
        self.subnode_name.collectVariableAccesses(emit_read, emit_write)

    @abstractmethod
    def computeExpressionConstantName(self, trace_collection):
        """Called when attribute name is constant."""


# Assign the names that are easier to import with a stable name.
ExpressionBuiltinHasattrBase = ChildrenHavingExpressionNameRaiseWaitConstantNameMixin


class ChildrenHavingLeftRightFinalNoRaiseMixin(ExpressionBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionSubtypeCheck

    def __init__(self, left, right, source_ref):
        left.parent = self

        self.subnode_left = left

        right.parent = self

        self.subnode_right = right

        ExpressionBase.__init__(self, source_ref)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_left,
            self.subnode_right,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("left", self.subnode_left),
            ("right", self.subnode_right),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_left
        if old_node is value:
            new_node.parent = self

            self.subnode_left = new_node

            return

        value = self.subnode_right
        if old_node is value:
            new_node.parent = self

            self.subnode_right = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "left": self.subnode_left.makeClone(),
            "right": self.subnode_right.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_left.finalize()
        del self.subnode_left
        self.subnode_right.finalize()
        del self.subnode_right

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
        return self.subnode_left.mayRaiseException(
            exception_type
        ) or self.subnode_right.mayRaiseException(exception_type)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_left.collectVariableAccesses(emit_read, emit_write)
        self.subnode_right.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ExpressionSubtypeCheckBase = ChildrenHavingLeftRightFinalNoRaiseMixin


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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_list_arg.collectVariableAccesses(emit_read, emit_write)


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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_list_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_item.collectVariableAccesses(emit_read, emit_write)


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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_list_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_value.collectVariableAccesses(emit_read, emit_write)


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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        for element in self.subnode_pairs:
            element.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ExpressionImportlibMetadataBackportSelectableGroupsValueRefBase = (
    ChildHavingPairsTupleFinalNoRaiseMixin
)
ExpressionImportlibMetadataSelectableGroupsValueRefBase = (
    ChildHavingPairsTupleFinalNoRaiseMixin
)


class ChildHavingPromptOptionalFinalMixin(ExpressionBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinInput

    def __init__(self, prompt, source_ref):
        if prompt is not None:
            prompt.parent = self

        self.subnode_prompt = prompt

        ExpressionBase.__init__(self, source_ref)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        value = self.subnode_prompt

        if value is None:
            return ()
        else:
            return (value,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("prompt", self.subnode_prompt),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_prompt
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_prompt = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "prompt": (
                self.subnode_prompt.makeClone()
                if self.subnode_prompt is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        if self.subnode_prompt is not None:
            self.subnode_prompt.finalize()
        del self.subnode_prompt

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = self.subnode_prompt

        if expression is not None:
            expression = trace_collection.onExpression(expression)

            if expression.willRaiseAnyException():
                return (
                    expression,
                    "new_raise",
                    lambda: "For '%s' the child expression '%s' will raise."
                    % (self.getChildNameNice(), expression.getChildNameNice()),
                )

        trace_collection.onExceptionRaiseExit(BaseException)
        return self, None, None

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        subnode_prompt = self.subnode_prompt

        if subnode_prompt is not None:
            self.subnode_prompt.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ExpressionBuiltinInputBase = ChildHavingPromptOptionalFinalMixin


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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_value.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ExpressionBuiltinClassmethodBase = ChildHavingValueFinalNoRaiseMixin
ExpressionBuiltinStaticmethodBase = ChildHavingValueFinalNoRaiseMixin

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
