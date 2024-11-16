#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# We are not avoiding these in generated code at all
# pylint: disable=I0021,line-too-long,too-many-instance-attributes,too-many-lines
# pylint: disable=I0021,too-many-arguments,too-many-return-statements,too-many-statements


"""Children having mixins

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

from .Checkers import (
    checkStatementsSequenceOrNone,
    convertEmptyStrConstantToNone,
    convertNoneConstantToNone,
)
from .NodeMakingHelpers import wrapExpressionWithSideEffects


class ModuleChildrenHavingBodyOptionalStatementsOrNoneFunctionsTupleMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   CompiledPythonModule
    #   CompiledPythonNamespacePackage
    #   CompiledPythonPackage
    #   PythonMainModule

    def __init__(
        self,
        body,
        functions,
    ):
        body = checkStatementsSequenceOrNone(body)
        if body is not None:
            body.parent = self

        self.subnode_body = body

        assert type(functions) is tuple

        for val in functions:
            val.parent = self

        self.subnode_functions = functions

    def setChildBody(self, value):
        value = checkStatementsSequenceOrNone(value)
        if value is not None:
            value.parent = self

        self.subnode_body = value

    def setChildFunctions(self, value):
        assert type(value) is tuple, type(value)

        for val in value:
            val.parent = self

        self.subnode_functions = value

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        value = self.subnode_body
        if value is None:
            pass
        else:
            result.append(value)
        result.extend(self.subnode_functions)
        return tuple(result)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("body", self.subnode_body),
            ("functions", self.subnode_functions),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_body
        if old_node is value:
            new_node = checkStatementsSequenceOrNone(new_node)
            if new_node is not None:
                new_node.parent = self

            self.subnode_body = new_node

            return

        value = self.subnode_functions
        if old_node in value:
            if new_node is not None:
                new_node.parent = self

                self.subnode_functions = tuple(
                    (val if val is not old_node else new_node) for val in value
                )
            else:
                self.subnode_functions = tuple(
                    val for val in value if val is not old_node
                )

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "body": (
                self.subnode_body.makeClone() if self.subnode_body is not None else None
            ),
            "functions": tuple(v.makeClone() for v in self.subnode_functions),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        if self.subnode_body is not None:
            self.subnode_body.finalize()
        del self.subnode_body
        for c in self.subnode_functions:
            c.finalize()
        del self.subnode_functions

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        subnode_body = self.subnode_body

        if subnode_body is not None:
            self.subnode_body.collectVariableAccesses(emit_read, emit_write)
        for element in self.subnode_functions:
            element.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenCompiledPythonModuleMixin = (
    ModuleChildrenHavingBodyOptionalStatementsOrNoneFunctionsTupleMixin
)
ChildrenCompiledPythonNamespacePackageMixin = (
    ModuleChildrenHavingBodyOptionalStatementsOrNoneFunctionsTupleMixin
)
ChildrenCompiledPythonPackageMixin = (
    ModuleChildrenHavingBodyOptionalStatementsOrNoneFunctionsTupleMixin
)
ChildrenPythonMainModuleMixin = (
    ModuleChildrenHavingBodyOptionalStatementsOrNoneFunctionsTupleMixin
)


class ChildHavingAsyncgenRefMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionMakeAsyncgenObject

    def __init__(
        self,
        asyncgen_ref,
    ):
        asyncgen_ref.parent = self

        self.subnode_asyncgen_ref = asyncgen_ref

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_asyncgen_ref,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("asyncgen_ref", self.subnode_asyncgen_ref),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_asyncgen_ref
        if old_node is value:
            new_node.parent = self

            self.subnode_asyncgen_ref = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "asyncgen_ref": self.subnode_asyncgen_ref.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_asyncgen_ref.finalize()
        del self.subnode_asyncgen_ref

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_asyncgen_ref)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_asyncgen_ref.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionMakeAsyncgenObjectMixin = ChildHavingAsyncgenRefMixin


class ChildHavingBodyOptionalMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionAsyncgenObjectBody
    #   ExpressionClassDictBody
    #   ExpressionClassDictBodyP2
    #   ExpressionClassMappingBody
    #   ExpressionCoroutineObjectBody
    #   ExpressionFunctionBody
    #   ExpressionFunctionPureBody
    #   ExpressionFunctionPureInlineConstBody
    #   ExpressionGeneratorObjectBody
    #   ExpressionOutlineBody
    #   ExpressionOutlineFunction

    def __init__(
        self,
        body,
    ):
        if body is not None:
            body.parent = self

        self.subnode_body = body

    def setChildBody(self, value):
        if value is not None:
            value.parent = self

        self.subnode_body = value

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        value = self.subnode_body

        if value is None:
            return ()
        else:
            return (value,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("body", self.subnode_body),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_body
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_body = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "body": (
                self.subnode_body.makeClone() if self.subnode_body is not None else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        if self.subnode_body is not None:
            self.subnode_body.finalize()
        del self.subnode_body

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = self.subnode_body

        if expression is not None:
            expression = trace_collection.onExpression(expression)

            if expression.willRaiseAnyException():
                return (
                    expression,
                    "new_raise",
                    lambda: "For '%s' the child expression '%s' will raise."
                    % (self.getChildNameNice(), expression.getChildNameNice()),
                )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        subnode_body = self.subnode_body

        if subnode_body is not None:
            self.subnode_body.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionAsyncgenObjectBodyMixin = ChildHavingBodyOptionalMixin
ChildrenExpressionClassDictBodyMixin = ChildHavingBodyOptionalMixin
ChildrenExpressionClassDictBodyP2Mixin = ChildHavingBodyOptionalMixin
ChildrenExpressionClassMappingBodyMixin = ChildHavingBodyOptionalMixin
ChildrenExpressionCoroutineObjectBodyMixin = ChildHavingBodyOptionalMixin
ChildrenExpressionFunctionBodyMixin = ChildHavingBodyOptionalMixin
ChildrenExpressionFunctionPureBodyMixin = ChildHavingBodyOptionalMixin
ChildrenExpressionFunctionPureInlineConstBodyMixin = ChildHavingBodyOptionalMixin
ChildrenExpressionGeneratorObjectBodyMixin = ChildHavingBodyOptionalMixin
ChildrenExpressionOutlineBodyMixin = ChildHavingBodyOptionalMixin
ChildrenExpressionOutlineFunctionMixin = ChildHavingBodyOptionalMixin


class ChildHavingBytesArgMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationCapitalize
    #   ExpressionBytesOperationCapitalizeBase
    #   ExpressionBytesOperationDecode1
    #   ExpressionBytesOperationExpandtabs1
    #   ExpressionBytesOperationIsalnum
    #   ExpressionBytesOperationIsalpha
    #   ExpressionBytesOperationIsalphaBase
    #   ExpressionBytesOperationIsdigit
    #   ExpressionBytesOperationIslower
    #   ExpressionBytesOperationIsspace
    #   ExpressionBytesOperationIsspaceBase
    #   ExpressionBytesOperationIstitle
    #   ExpressionBytesOperationIstitleBase
    #   ExpressionBytesOperationIsupper
    #   ExpressionBytesOperationLower
    #   ExpressionBytesOperationLstrip1
    #   ExpressionBytesOperationRsplit1
    #   ExpressionBytesOperationRstrip1
    #   ExpressionBytesOperationSplit1
    #   ExpressionBytesOperationSplitlines1
    #   ExpressionBytesOperationStrip1
    #   ExpressionBytesOperationSwapcase
    #   ExpressionBytesOperationSwapcaseBase
    #   ExpressionBytesOperationTitle
    #   ExpressionBytesOperationTitleBase
    #   ExpressionBytesOperationUpper

    def __init__(
        self,
        bytes_arg,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_bytes_arg,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("bytes_arg", self.subnode_bytes_arg),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_bytes_arg)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationCapitalizeMixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationCapitalizeBaseMixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationDecode1Mixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationExpandtabs1Mixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationIsalnumMixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationIsalphaMixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationIsalphaBaseMixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationIsdigitMixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationIslowerMixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationIsspaceMixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationIsspaceBaseMixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationIstitleMixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationIstitleBaseMixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationIsupperMixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationLowerMixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationLstrip1Mixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationRsplit1Mixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationRstrip1Mixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationSplit1Mixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationSplitlines1Mixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationStrip1Mixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationSwapcaseMixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationSwapcaseBaseMixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationTitleMixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationTitleBaseMixin = ChildHavingBytesArgMixin
ChildrenExpressionBytesOperationUpperMixin = ChildHavingBytesArgMixin


class ChildrenHavingBytesArgCharsMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationLstrip2
    #   ExpressionBytesOperationRstrip2
    #   ExpressionBytesOperationStrip2

    def __init__(
        self,
        bytes_arg,
        chars,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        chars.parent = self

        self.subnode_chars = chars

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_chars,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("chars", self.subnode_chars),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_chars
        if old_node is value:
            new_node.parent = self

            self.subnode_chars = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "chars": self.subnode_chars.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_chars.finalize()
        del self.subnode_chars

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_chars.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationLstrip2Mixin = ChildrenHavingBytesArgCharsMixin
ChildrenExpressionBytesOperationRstrip2Mixin = ChildrenHavingBytesArgCharsMixin
ChildrenExpressionBytesOperationStrip2Mixin = ChildrenHavingBytesArgCharsMixin


class ChildrenHavingBytesArgEncodingMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationDecode2

    def __init__(
        self,
        bytes_arg,
        encoding,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        encoding.parent = self

        self.subnode_encoding = encoding

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_encoding,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("encoding", self.subnode_encoding),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_encoding
        if old_node is value:
            new_node.parent = self

            self.subnode_encoding = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "encoding": self.subnode_encoding.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_encoding.finalize()
        del self.subnode_encoding

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_encoding.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationDecode2Mixin = ChildrenHavingBytesArgEncodingMixin


class ChildrenHavingBytesArgEncodingErrorsMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationDecode3

    def __init__(
        self,
        bytes_arg,
        encoding,
        errors,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        encoding.parent = self

        self.subnode_encoding = encoding

        errors.parent = self

        self.subnode_errors = errors

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_encoding,
            self.subnode_errors,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("encoding", self.subnode_encoding),
            ("errors", self.subnode_errors),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_encoding
        if old_node is value:
            new_node.parent = self

            self.subnode_encoding = new_node

            return

        value = self.subnode_errors
        if old_node is value:
            new_node.parent = self

            self.subnode_errors = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "encoding": self.subnode_encoding.makeClone(),
            "errors": self.subnode_errors.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_encoding.finalize()
        del self.subnode_encoding
        self.subnode_errors.finalize()
        del self.subnode_errors

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_encoding.collectVariableAccesses(emit_read, emit_write)
        self.subnode_errors.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationDecode3Mixin = ChildrenHavingBytesArgEncodingErrorsMixin


class ChildrenHavingBytesArgIterableMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationJoin

    def __init__(
        self,
        bytes_arg,
        iterable,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        iterable.parent = self

        self.subnode_iterable = iterable

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_iterable,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("iterable", self.subnode_iterable),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_iterable
        if old_node is value:
            new_node.parent = self

            self.subnode_iterable = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "iterable": self.subnode_iterable.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_iterable.finalize()
        del self.subnode_iterable

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_iterable.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationJoinMixin = ChildrenHavingBytesArgIterableMixin


class ChildrenHavingBytesArgKeependsMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationSplitlines2

    def __init__(
        self,
        bytes_arg,
        keepends,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        keepends.parent = self

        self.subnode_keepends = keepends

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_keepends,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("keepends", self.subnode_keepends),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_keepends
        if old_node is value:
            new_node.parent = self

            self.subnode_keepends = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "keepends": self.subnode_keepends.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_keepends.finalize()
        del self.subnode_keepends

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_keepends.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationSplitlines2Mixin = ChildrenHavingBytesArgKeependsMixin


class ChildrenHavingBytesArgOldNewMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationReplace3

    def __init__(
        self,
        bytes_arg,
        old,
        new,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        old.parent = self

        self.subnode_old = old

        new.parent = self

        self.subnode_new = new

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_old,
            self.subnode_new,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("old", self.subnode_old),
            ("new", self.subnode_new),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_old
        if old_node is value:
            new_node.parent = self

            self.subnode_old = new_node

            return

        value = self.subnode_new
        if old_node is value:
            new_node.parent = self

            self.subnode_new = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "old": self.subnode_old.makeClone(),
            "new": self.subnode_new.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_old.finalize()
        del self.subnode_old
        self.subnode_new.finalize()
        del self.subnode_new

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_old.collectVariableAccesses(emit_read, emit_write)
        self.subnode_new.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationReplace3Mixin = ChildrenHavingBytesArgOldNewMixin


class ChildrenHavingBytesArgOldNewCountMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationReplace4

    def __init__(
        self,
        bytes_arg,
        old,
        new,
        count,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        old.parent = self

        self.subnode_old = old

        new.parent = self

        self.subnode_new = new

        count.parent = self

        self.subnode_count = count

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_old,
            self.subnode_new,
            self.subnode_count,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("old", self.subnode_old),
            ("new", self.subnode_new),
            ("count", self.subnode_count),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_old
        if old_node is value:
            new_node.parent = self

            self.subnode_old = new_node

            return

        value = self.subnode_new
        if old_node is value:
            new_node.parent = self

            self.subnode_new = new_node

            return

        value = self.subnode_count
        if old_node is value:
            new_node.parent = self

            self.subnode_count = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "old": self.subnode_old.makeClone(),
            "new": self.subnode_new.makeClone(),
            "count": self.subnode_count.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_old.finalize()
        del self.subnode_old
        self.subnode_new.finalize()
        del self.subnode_new
        self.subnode_count.finalize()
        del self.subnode_count

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_old.collectVariableAccesses(emit_read, emit_write)
        self.subnode_new.collectVariableAccesses(emit_read, emit_write)
        self.subnode_count.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationReplace4Mixin = ChildrenHavingBytesArgOldNewCountMixin


class ChildrenHavingBytesArgPrefixMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationStartswith2

    def __init__(
        self,
        bytes_arg,
        prefix,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        prefix.parent = self

        self.subnode_prefix = prefix

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_prefix,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("prefix", self.subnode_prefix),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_prefix
        if old_node is value:
            new_node.parent = self

            self.subnode_prefix = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "prefix": self.subnode_prefix.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_prefix.finalize()
        del self.subnode_prefix

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_prefix.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationStartswith2Mixin = ChildrenHavingBytesArgPrefixMixin


class ChildrenHavingBytesArgPrefixStartMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationStartswith3

    def __init__(
        self,
        bytes_arg,
        prefix,
        start,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        prefix.parent = self

        self.subnode_prefix = prefix

        start.parent = self

        self.subnode_start = start

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_prefix,
            self.subnode_start,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("prefix", self.subnode_prefix),
            ("start", self.subnode_start),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_prefix
        if old_node is value:
            new_node.parent = self

            self.subnode_prefix = new_node

            return

        value = self.subnode_start
        if old_node is value:
            new_node.parent = self

            self.subnode_start = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "prefix": self.subnode_prefix.makeClone(),
            "start": self.subnode_start.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_prefix.finalize()
        del self.subnode_prefix
        self.subnode_start.finalize()
        del self.subnode_start

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_prefix.collectVariableAccesses(emit_read, emit_write)
        self.subnode_start.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationStartswith3Mixin = (
    ChildrenHavingBytesArgPrefixStartMixin
)


class ChildrenHavingBytesArgPrefixStartEndMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationStartswith4

    def __init__(
        self,
        bytes_arg,
        prefix,
        start,
        end,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        prefix.parent = self

        self.subnode_prefix = prefix

        start.parent = self

        self.subnode_start = start

        end.parent = self

        self.subnode_end = end

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_prefix,
            self.subnode_start,
            self.subnode_end,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("prefix", self.subnode_prefix),
            ("start", self.subnode_start),
            ("end", self.subnode_end),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_prefix
        if old_node is value:
            new_node.parent = self

            self.subnode_prefix = new_node

            return

        value = self.subnode_start
        if old_node is value:
            new_node.parent = self

            self.subnode_start = new_node

            return

        value = self.subnode_end
        if old_node is value:
            new_node.parent = self

            self.subnode_end = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "prefix": self.subnode_prefix.makeClone(),
            "start": self.subnode_start.makeClone(),
            "end": self.subnode_end.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_prefix.finalize()
        del self.subnode_prefix
        self.subnode_start.finalize()
        del self.subnode_start
        self.subnode_end.finalize()
        del self.subnode_end

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_prefix.collectVariableAccesses(emit_read, emit_write)
        self.subnode_start.collectVariableAccesses(emit_read, emit_write)
        self.subnode_end.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationStartswith4Mixin = (
    ChildrenHavingBytesArgPrefixStartEndMixin
)


class ChildrenHavingBytesArgSepMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationPartition
    #   ExpressionBytesOperationRpartition
    #   ExpressionBytesOperationRsplit2
    #   ExpressionBytesOperationSplit2

    def __init__(
        self,
        bytes_arg,
        sep,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        sep.parent = self

        self.subnode_sep = sep

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_sep,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("sep", self.subnode_sep),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_sep
        if old_node is value:
            new_node.parent = self

            self.subnode_sep = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "sep": self.subnode_sep.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_sep.finalize()
        del self.subnode_sep

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_sep.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationPartitionMixin = ChildrenHavingBytesArgSepMixin
ChildrenExpressionBytesOperationRpartitionMixin = ChildrenHavingBytesArgSepMixin
ChildrenExpressionBytesOperationRsplit2Mixin = ChildrenHavingBytesArgSepMixin
ChildrenExpressionBytesOperationSplit2Mixin = ChildrenHavingBytesArgSepMixin


class ChildrenHavingBytesArgSepMaxsplitMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationRsplit3
    #   ExpressionBytesOperationSplit3

    def __init__(
        self,
        bytes_arg,
        sep,
        maxsplit,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        sep.parent = self

        self.subnode_sep = sep

        maxsplit.parent = self

        self.subnode_maxsplit = maxsplit

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_sep,
            self.subnode_maxsplit,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("sep", self.subnode_sep),
            ("maxsplit", self.subnode_maxsplit),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_sep
        if old_node is value:
            new_node.parent = self

            self.subnode_sep = new_node

            return

        value = self.subnode_maxsplit
        if old_node is value:
            new_node.parent = self

            self.subnode_maxsplit = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "sep": self.subnode_sep.makeClone(),
            "maxsplit": self.subnode_maxsplit.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_sep.finalize()
        del self.subnode_sep
        self.subnode_maxsplit.finalize()
        del self.subnode_maxsplit

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_sep.collectVariableAccesses(emit_read, emit_write)
        self.subnode_maxsplit.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationRsplit3Mixin = ChildrenHavingBytesArgSepMaxsplitMixin
ChildrenExpressionBytesOperationSplit3Mixin = ChildrenHavingBytesArgSepMaxsplitMixin


class ChildrenHavingBytesArgSubMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationCount2
    #   ExpressionBytesOperationFind2
    #   ExpressionBytesOperationIndex2
    #   ExpressionBytesOperationRfind2
    #   ExpressionBytesOperationRindex2

    def __init__(
        self,
        bytes_arg,
        sub,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        sub.parent = self

        self.subnode_sub = sub

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_sub,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("sub", self.subnode_sub),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_sub
        if old_node is value:
            new_node.parent = self

            self.subnode_sub = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "sub": self.subnode_sub.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_sub.finalize()
        del self.subnode_sub

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_sub.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationCount2Mixin = ChildrenHavingBytesArgSubMixin
ChildrenExpressionBytesOperationFind2Mixin = ChildrenHavingBytesArgSubMixin
ChildrenExpressionBytesOperationIndex2Mixin = ChildrenHavingBytesArgSubMixin
ChildrenExpressionBytesOperationRfind2Mixin = ChildrenHavingBytesArgSubMixin
ChildrenExpressionBytesOperationRindex2Mixin = ChildrenHavingBytesArgSubMixin


class ChildrenHavingBytesArgSubStartMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationCount3
    #   ExpressionBytesOperationFind3
    #   ExpressionBytesOperationIndex3
    #   ExpressionBytesOperationRfind3
    #   ExpressionBytesOperationRindex3

    def __init__(
        self,
        bytes_arg,
        sub,
        start,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        sub.parent = self

        self.subnode_sub = sub

        start.parent = self

        self.subnode_start = start

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_sub,
            self.subnode_start,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("sub", self.subnode_sub),
            ("start", self.subnode_start),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_sub
        if old_node is value:
            new_node.parent = self

            self.subnode_sub = new_node

            return

        value = self.subnode_start
        if old_node is value:
            new_node.parent = self

            self.subnode_start = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "sub": self.subnode_sub.makeClone(),
            "start": self.subnode_start.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_sub.finalize()
        del self.subnode_sub
        self.subnode_start.finalize()
        del self.subnode_start

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_sub.collectVariableAccesses(emit_read, emit_write)
        self.subnode_start.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationCount3Mixin = ChildrenHavingBytesArgSubStartMixin
ChildrenExpressionBytesOperationFind3Mixin = ChildrenHavingBytesArgSubStartMixin
ChildrenExpressionBytesOperationIndex3Mixin = ChildrenHavingBytesArgSubStartMixin
ChildrenExpressionBytesOperationRfind3Mixin = ChildrenHavingBytesArgSubStartMixin
ChildrenExpressionBytesOperationRindex3Mixin = ChildrenHavingBytesArgSubStartMixin


class ChildrenHavingBytesArgSubStartEndMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationCount4
    #   ExpressionBytesOperationFind4
    #   ExpressionBytesOperationIndex4
    #   ExpressionBytesOperationRfind4
    #   ExpressionBytesOperationRindex4

    def __init__(
        self,
        bytes_arg,
        sub,
        start,
        end,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        sub.parent = self

        self.subnode_sub = sub

        start.parent = self

        self.subnode_start = start

        end.parent = self

        self.subnode_end = end

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_sub,
            self.subnode_start,
            self.subnode_end,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("sub", self.subnode_sub),
            ("start", self.subnode_start),
            ("end", self.subnode_end),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_sub
        if old_node is value:
            new_node.parent = self

            self.subnode_sub = new_node

            return

        value = self.subnode_start
        if old_node is value:
            new_node.parent = self

            self.subnode_start = new_node

            return

        value = self.subnode_end
        if old_node is value:
            new_node.parent = self

            self.subnode_end = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "sub": self.subnode_sub.makeClone(),
            "start": self.subnode_start.makeClone(),
            "end": self.subnode_end.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_sub.finalize()
        del self.subnode_sub
        self.subnode_start.finalize()
        del self.subnode_start
        self.subnode_end.finalize()
        del self.subnode_end

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_sub.collectVariableAccesses(emit_read, emit_write)
        self.subnode_start.collectVariableAccesses(emit_read, emit_write)
        self.subnode_end.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationCount4Mixin = ChildrenHavingBytesArgSubStartEndMixin
ChildrenExpressionBytesOperationFind4Mixin = ChildrenHavingBytesArgSubStartEndMixin
ChildrenExpressionBytesOperationIndex4Mixin = ChildrenHavingBytesArgSubStartEndMixin
ChildrenExpressionBytesOperationRfind4Mixin = ChildrenHavingBytesArgSubStartEndMixin
ChildrenExpressionBytesOperationRindex4Mixin = ChildrenHavingBytesArgSubStartEndMixin


class ChildrenHavingBytesArgSuffixMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationEndswith2

    def __init__(
        self,
        bytes_arg,
        suffix,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        suffix.parent = self

        self.subnode_suffix = suffix

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_suffix,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("suffix", self.subnode_suffix),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_suffix
        if old_node is value:
            new_node.parent = self

            self.subnode_suffix = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "suffix": self.subnode_suffix.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_suffix.finalize()
        del self.subnode_suffix

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_suffix.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationEndswith2Mixin = ChildrenHavingBytesArgSuffixMixin


class ChildrenHavingBytesArgSuffixStartMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationEndswith3

    def __init__(
        self,
        bytes_arg,
        suffix,
        start,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        suffix.parent = self

        self.subnode_suffix = suffix

        start.parent = self

        self.subnode_start = start

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_suffix,
            self.subnode_start,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("suffix", self.subnode_suffix),
            ("start", self.subnode_start),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_suffix
        if old_node is value:
            new_node.parent = self

            self.subnode_suffix = new_node

            return

        value = self.subnode_start
        if old_node is value:
            new_node.parent = self

            self.subnode_start = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "suffix": self.subnode_suffix.makeClone(),
            "start": self.subnode_start.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_suffix.finalize()
        del self.subnode_suffix
        self.subnode_start.finalize()
        del self.subnode_start

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_suffix.collectVariableAccesses(emit_read, emit_write)
        self.subnode_start.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationEndswith3Mixin = ChildrenHavingBytesArgSuffixStartMixin


class ChildrenHavingBytesArgSuffixStartEndMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationEndswith4

    def __init__(
        self,
        bytes_arg,
        suffix,
        start,
        end,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        suffix.parent = self

        self.subnode_suffix = suffix

        start.parent = self

        self.subnode_start = start

        end.parent = self

        self.subnode_end = end

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_suffix,
            self.subnode_start,
            self.subnode_end,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("suffix", self.subnode_suffix),
            ("start", self.subnode_start),
            ("end", self.subnode_end),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_suffix
        if old_node is value:
            new_node.parent = self

            self.subnode_suffix = new_node

            return

        value = self.subnode_start
        if old_node is value:
            new_node.parent = self

            self.subnode_start = new_node

            return

        value = self.subnode_end
        if old_node is value:
            new_node.parent = self

            self.subnode_end = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "suffix": self.subnode_suffix.makeClone(),
            "start": self.subnode_start.makeClone(),
            "end": self.subnode_end.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_suffix.finalize()
        del self.subnode_suffix
        self.subnode_start.finalize()
        del self.subnode_start
        self.subnode_end.finalize()
        del self.subnode_end

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_suffix.collectVariableAccesses(emit_read, emit_write)
        self.subnode_start.collectVariableAccesses(emit_read, emit_write)
        self.subnode_end.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationEndswith4Mixin = (
    ChildrenHavingBytesArgSuffixStartEndMixin
)


class ChildrenHavingBytesArgTableMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationTranslate2

    def __init__(
        self,
        bytes_arg,
        table,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        table.parent = self

        self.subnode_table = table

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_table,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("table", self.subnode_table),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_table
        if old_node is value:
            new_node.parent = self

            self.subnode_table = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "table": self.subnode_table.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_table.finalize()
        del self.subnode_table

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_table.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationTranslate2Mixin = ChildrenHavingBytesArgTableMixin


class ChildrenHavingBytesArgTableDeleteMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationTranslate3

    def __init__(
        self,
        bytes_arg,
        table,
        delete,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        table.parent = self

        self.subnode_table = table

        delete.parent = self

        self.subnode_delete = delete

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_table,
            self.subnode_delete,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("table", self.subnode_table),
            ("delete", self.subnode_delete),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_table
        if old_node is value:
            new_node.parent = self

            self.subnode_table = new_node

            return

        value = self.subnode_delete
        if old_node is value:
            new_node.parent = self

            self.subnode_delete = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "table": self.subnode_table.makeClone(),
            "delete": self.subnode_delete.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_table.finalize()
        del self.subnode_table
        self.subnode_delete.finalize()
        del self.subnode_delete

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_table.collectVariableAccesses(emit_read, emit_write)
        self.subnode_delete.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationTranslate3Mixin = ChildrenHavingBytesArgTableDeleteMixin


class ChildrenHavingBytesArgTabsizeMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationExpandtabs2

    def __init__(
        self,
        bytes_arg,
        tabsize,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        tabsize.parent = self

        self.subnode_tabsize = tabsize

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_tabsize,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("tabsize", self.subnode_tabsize),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_tabsize
        if old_node is value:
            new_node.parent = self

            self.subnode_tabsize = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "tabsize": self.subnode_tabsize.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_tabsize.finalize()
        del self.subnode_tabsize

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_tabsize.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationExpandtabs2Mixin = ChildrenHavingBytesArgTabsizeMixin


class ChildrenHavingBytesArgWidthMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationCenter2
    #   ExpressionBytesOperationLjust2
    #   ExpressionBytesOperationRjust2
    #   ExpressionBytesOperationZfill

    def __init__(
        self,
        bytes_arg,
        width,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        width.parent = self

        self.subnode_width = width

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_width,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("width", self.subnode_width),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_width
        if old_node is value:
            new_node.parent = self

            self.subnode_width = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "width": self.subnode_width.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_width.finalize()
        del self.subnode_width

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_width.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationCenter2Mixin = ChildrenHavingBytesArgWidthMixin
ChildrenExpressionBytesOperationLjust2Mixin = ChildrenHavingBytesArgWidthMixin
ChildrenExpressionBytesOperationRjust2Mixin = ChildrenHavingBytesArgWidthMixin
ChildrenExpressionBytesOperationZfillMixin = ChildrenHavingBytesArgWidthMixin


class ChildrenHavingBytesArgWidthFillcharMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBytesOperationCenter3
    #   ExpressionBytesOperationLjust3
    #   ExpressionBytesOperationRjust3

    def __init__(
        self,
        bytes_arg,
        width,
        fillchar,
    ):
        bytes_arg.parent = self

        self.subnode_bytes_arg = bytes_arg

        width.parent = self

        self.subnode_width = width

        fillchar.parent = self

        self.subnode_fillchar = fillchar

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_bytes_arg,
            self.subnode_width,
            self.subnode_fillchar,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("bytes_arg", self.subnode_bytes_arg),
            ("width", self.subnode_width),
            ("fillchar", self.subnode_fillchar),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_bytes_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_bytes_arg = new_node

            return

        value = self.subnode_width
        if old_node is value:
            new_node.parent = self

            self.subnode_width = new_node

            return

        value = self.subnode_fillchar
        if old_node is value:
            new_node.parent = self

            self.subnode_fillchar = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "bytes_arg": self.subnode_bytes_arg.makeClone(),
            "width": self.subnode_width.makeClone(),
            "fillchar": self.subnode_fillchar.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_bytes_arg.finalize()
        del self.subnode_bytes_arg
        self.subnode_width.finalize()
        del self.subnode_width
        self.subnode_fillchar.finalize()
        del self.subnode_fillchar

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_bytes_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_width.collectVariableAccesses(emit_read, emit_write)
        self.subnode_fillchar.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBytesOperationCenter3Mixin = ChildrenHavingBytesArgWidthFillcharMixin
ChildrenExpressionBytesOperationLjust3Mixin = ChildrenHavingBytesArgWidthFillcharMixin
ChildrenExpressionBytesOperationRjust3Mixin = ChildrenHavingBytesArgWidthFillcharMixin


class ChildHavingCalledMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionCallEmpty

    def __init__(
        self,
        called,
    ):
        called.parent = self

        self.subnode_called = called

    def setChildCalled(self, value):
        value.parent = self

        self.subnode_called = value

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_called,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("called", self.subnode_called),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_called
        if old_node is value:
            new_node.parent = self

            self.subnode_called = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "called": self.subnode_called.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_called.finalize()
        del self.subnode_called

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_called)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_called.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionCallEmptyMixin = ChildHavingCalledMixin


class ChildrenHavingCalledArgsMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionCallNoKeywords

    def __init__(
        self,
        called,
        args,
    ):
        called.parent = self

        self.subnode_called = called

        args.parent = self

        self.subnode_args = args

    def setChildCalled(self, value):
        value.parent = self

        self.subnode_called = value

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_called,
            self.subnode_args,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("called", self.subnode_called),
            ("args", self.subnode_args),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_called
        if old_node is value:
            new_node.parent = self

            self.subnode_called = new_node

            return

        value = self.subnode_args
        if old_node is value:
            new_node.parent = self

            self.subnode_args = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "called": self.subnode_called.makeClone(),
            "args": self.subnode_args.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_called.finalize()
        del self.subnode_called
        self.subnode_args.finalize()
        del self.subnode_args

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_called.collectVariableAccesses(emit_read, emit_write)
        self.subnode_args.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionCallNoKeywordsMixin = ChildrenHavingCalledArgsMixin


class ChildrenHavingCalledArgsKwargsMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionCall

    def __init__(
        self,
        called,
        args,
        kwargs,
    ):
        called.parent = self

        self.subnode_called = called

        args.parent = self

        self.subnode_args = args

        kwargs.parent = self

        self.subnode_kwargs = kwargs

    def setChildCalled(self, value):
        value.parent = self

        self.subnode_called = value

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_called,
            self.subnode_args,
            self.subnode_kwargs,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("called", self.subnode_called),
            ("args", self.subnode_args),
            ("kwargs", self.subnode_kwargs),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_called
        if old_node is value:
            new_node.parent = self

            self.subnode_called = new_node

            return

        value = self.subnode_args
        if old_node is value:
            new_node.parent = self

            self.subnode_args = new_node

            return

        value = self.subnode_kwargs
        if old_node is value:
            new_node.parent = self

            self.subnode_kwargs = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "called": self.subnode_called.makeClone(),
            "args": self.subnode_args.makeClone(),
            "kwargs": self.subnode_kwargs.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_called.finalize()
        del self.subnode_called
        self.subnode_args.finalize()
        del self.subnode_args
        self.subnode_kwargs.finalize()
        del self.subnode_kwargs

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_called.collectVariableAccesses(emit_read, emit_write)
        self.subnode_args.collectVariableAccesses(emit_read, emit_write)
        self.subnode_kwargs.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionCallMixin = ChildrenHavingCalledArgsKwargsMixin


class ChildrenHavingCalledKwargsMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionCallKeywordsOnly

    def __init__(
        self,
        called,
        kwargs,
    ):
        called.parent = self

        self.subnode_called = called

        kwargs.parent = self

        self.subnode_kwargs = kwargs

    def setChildCalled(self, value):
        value.parent = self

        self.subnode_called = value

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_called,
            self.subnode_kwargs,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("called", self.subnode_called),
            ("kwargs", self.subnode_kwargs),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_called
        if old_node is value:
            new_node.parent = self

            self.subnode_called = new_node

            return

        value = self.subnode_kwargs
        if old_node is value:
            new_node.parent = self

            self.subnode_kwargs = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "called": self.subnode_called.makeClone(),
            "kwargs": self.subnode_kwargs.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_called.finalize()
        del self.subnode_called
        self.subnode_kwargs.finalize()
        del self.subnode_kwargs

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_called.collectVariableAccesses(emit_read, emit_write)
        self.subnode_kwargs.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionCallKeywordsOnlyMixin = ChildrenHavingCalledKwargsMixin


class ChildHavingClsMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionTypeCheck

    def __init__(
        self,
        cls,
    ):
        cls.parent = self

        self.subnode_cls = cls

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_cls,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("cls", self.subnode_cls),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_cls
        if old_node is value:
            new_node.parent = self

            self.subnode_cls = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "cls": self.subnode_cls.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_cls.finalize()
        del self.subnode_cls

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_cls)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_cls.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionTypeCheckMixin = ChildHavingClsMixin


class ChildrenHavingClsClassesMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinIssubclass

    def __init__(
        self,
        cls,
        classes,
    ):
        cls.parent = self

        self.subnode_cls = cls

        classes.parent = self

        self.subnode_classes = classes

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_cls,
            self.subnode_classes,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("cls", self.subnode_cls),
            ("classes", self.subnode_classes),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_cls
        if old_node is value:
            new_node.parent = self

            self.subnode_cls = new_node

            return

        value = self.subnode_classes
        if old_node is value:
            new_node.parent = self

            self.subnode_classes = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "cls": self.subnode_cls.makeClone(),
            "classes": self.subnode_classes.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_cls.finalize()
        del self.subnode_cls
        self.subnode_classes.finalize()
        del self.subnode_classes

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_cls.collectVariableAccesses(emit_read, emit_write)
        self.subnode_classes.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinIssubclassMixin = ChildrenHavingClsClassesMixin


class ChildrenHavingConditionExpressionYesExpressionNoMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionConditional

    def __init__(
        self,
        condition,
        expression_yes,
        expression_no,
    ):
        condition.parent = self

        self.subnode_condition = condition

        expression_yes.parent = self

        self.subnode_expression_yes = expression_yes

        expression_no.parent = self

        self.subnode_expression_no = expression_no

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_condition,
            self.subnode_expression_yes,
            self.subnode_expression_no,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("condition", self.subnode_condition),
            ("expression_yes", self.subnode_expression_yes),
            ("expression_no", self.subnode_expression_no),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_condition
        if old_node is value:
            new_node.parent = self

            self.subnode_condition = new_node

            return

        value = self.subnode_expression_yes
        if old_node is value:
            new_node.parent = self

            self.subnode_expression_yes = new_node

            return

        value = self.subnode_expression_no
        if old_node is value:
            new_node.parent = self

            self.subnode_expression_no = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "condition": self.subnode_condition.makeClone(),
            "expression_yes": self.subnode_expression_yes.makeClone(),
            "expression_no": self.subnode_expression_no.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_condition.finalize()
        del self.subnode_condition
        self.subnode_expression_yes.finalize()
        del self.subnode_expression_yes
        self.subnode_expression_no.finalize()
        del self.subnode_expression_no

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_condition.collectVariableAccesses(emit_read, emit_write)
        self.subnode_expression_yes.collectVariableAccesses(emit_read, emit_write)
        self.subnode_expression_no.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionConditionalMixin = (
    ChildrenHavingConditionExpressionYesExpressionNoMixin
)


class ChildHavingCoroutineRefMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionMakeCoroutineObject

    def __init__(
        self,
        coroutine_ref,
    ):
        coroutine_ref.parent = self

        self.subnode_coroutine_ref = coroutine_ref

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_coroutine_ref,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("coroutine_ref", self.subnode_coroutine_ref),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_coroutine_ref
        if old_node is value:
            new_node.parent = self

            self.subnode_coroutine_ref = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "coroutine_ref": self.subnode_coroutine_ref.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_coroutine_ref.finalize()
        del self.subnode_coroutine_ref

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_coroutine_ref)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_coroutine_ref.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionMakeCoroutineObjectMixin = ChildHavingCoroutineRefMixin


class ChildrenHavingDefaultsTupleKwDefaultsOptionalAnnotationsOptionalFunctionRefMixin(
    object
):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionFunctionCreation

    def __init__(
        self,
        defaults,
        kw_defaults,
        annotations,
        function_ref,
    ):
        assert type(defaults) is tuple

        for val in defaults:
            val.parent = self

        self.subnode_defaults = defaults

        if kw_defaults is not None:
            kw_defaults.parent = self

        self.subnode_kw_defaults = kw_defaults

        if annotations is not None:
            annotations.parent = self

        self.subnode_annotations = annotations

        function_ref.parent = self

        self.subnode_function_ref = function_ref

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.extend(self.subnode_defaults)
        value = self.subnode_kw_defaults
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_annotations
        if value is None:
            pass
        else:
            result.append(value)
        result.append(self.subnode_function_ref)
        return tuple(result)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("defaults", self.subnode_defaults),
            ("kw_defaults", self.subnode_kw_defaults),
            ("annotations", self.subnode_annotations),
            ("function_ref", self.subnode_function_ref),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_defaults
        if old_node in value:
            if new_node is not None:
                new_node.parent = self

                self.subnode_defaults = tuple(
                    (val if val is not old_node else new_node) for val in value
                )
            else:
                self.subnode_defaults = tuple(
                    val for val in value if val is not old_node
                )

            return

        value = self.subnode_kw_defaults
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_kw_defaults = new_node

            return

        value = self.subnode_annotations
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_annotations = new_node

            return

        value = self.subnode_function_ref
        if old_node is value:
            new_node.parent = self

            self.subnode_function_ref = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "defaults": tuple(v.makeClone() for v in self.subnode_defaults),
            "kw_defaults": (
                self.subnode_kw_defaults.makeClone()
                if self.subnode_kw_defaults is not None
                else None
            ),
            "annotations": (
                self.subnode_annotations.makeClone()
                if self.subnode_annotations is not None
                else None
            ),
            "function_ref": self.subnode_function_ref.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        for c in self.subnode_defaults:
            c.finalize()
        del self.subnode_defaults
        if self.subnode_kw_defaults is not None:
            self.subnode_kw_defaults.finalize()
        del self.subnode_kw_defaults
        if self.subnode_annotations is not None:
            self.subnode_annotations.finalize()
        del self.subnode_annotations
        self.subnode_function_ref.finalize()
        del self.subnode_function_ref

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        for element in self.subnode_defaults:
            element.collectVariableAccesses(emit_read, emit_write)
        subnode_kw_defaults = self.subnode_kw_defaults

        if subnode_kw_defaults is not None:
            self.subnode_kw_defaults.collectVariableAccesses(emit_read, emit_write)
        subnode_annotations = self.subnode_annotations

        if subnode_annotations is not None:
            self.subnode_annotations.collectVariableAccesses(emit_read, emit_write)
        self.subnode_function_ref.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionFunctionCreationMixin = (
    ChildrenHavingDefaultsTupleKwDefaultsOptionalAnnotationsOptionalFunctionRefMixin
)


class ChildHavingDictArgMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionDictOperationClear
    #   ExpressionDictOperationCopy
    #   ExpressionDictOperationItems
    #   ExpressionDictOperationItemsBase
    #   ExpressionDictOperationIteritems
    #   ExpressionDictOperationIteritemsBase
    #   ExpressionDictOperationIterkeys
    #   ExpressionDictOperationIterkeysBase
    #   ExpressionDictOperationItervalues
    #   ExpressionDictOperationItervaluesBase
    #   ExpressionDictOperationKeys
    #   ExpressionDictOperationKeysBase
    #   ExpressionDictOperationPopitem
    #   ExpressionDictOperationValues
    #   ExpressionDictOperationValuesBase
    #   ExpressionDictOperationViewitems
    #   ExpressionDictOperationViewitemsBase
    #   ExpressionDictOperationViewkeys
    #   ExpressionDictOperationViewkeysBase
    #   ExpressionDictOperationViewvalues
    #   ExpressionDictOperationViewvaluesBase

    def __init__(
        self,
        dict_arg,
    ):
        dict_arg.parent = self

        self.subnode_dict_arg = dict_arg

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_dict_arg,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("dict_arg", self.subnode_dict_arg),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_dict_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_dict_arg = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "dict_arg": self.subnode_dict_arg.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_dict_arg.finalize()
        del self.subnode_dict_arg

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_dict_arg)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_dict_arg.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionDictOperationClearMixin = ChildHavingDictArgMixin
ChildrenExpressionDictOperationCopyMixin = ChildHavingDictArgMixin
ChildrenExpressionDictOperationItemsMixin = ChildHavingDictArgMixin
ChildrenExpressionDictOperationItemsBaseMixin = ChildHavingDictArgMixin
ChildrenExpressionDictOperationIteritemsMixin = ChildHavingDictArgMixin
ChildrenExpressionDictOperationIteritemsBaseMixin = ChildHavingDictArgMixin
ChildrenExpressionDictOperationIterkeysMixin = ChildHavingDictArgMixin
ChildrenExpressionDictOperationIterkeysBaseMixin = ChildHavingDictArgMixin
ChildrenExpressionDictOperationItervaluesMixin = ChildHavingDictArgMixin
ChildrenExpressionDictOperationItervaluesBaseMixin = ChildHavingDictArgMixin
ChildrenExpressionDictOperationKeysMixin = ChildHavingDictArgMixin
ChildrenExpressionDictOperationKeysBaseMixin = ChildHavingDictArgMixin
ChildrenExpressionDictOperationPopitemMixin = ChildHavingDictArgMixin
ChildrenExpressionDictOperationValuesMixin = ChildHavingDictArgMixin
ChildrenExpressionDictOperationValuesBaseMixin = ChildHavingDictArgMixin
ChildrenExpressionDictOperationViewitemsMixin = ChildHavingDictArgMixin
ChildrenExpressionDictOperationViewitemsBaseMixin = ChildHavingDictArgMixin
ChildrenExpressionDictOperationViewkeysMixin = ChildHavingDictArgMixin
ChildrenExpressionDictOperationViewkeysBaseMixin = ChildHavingDictArgMixin
ChildrenExpressionDictOperationViewvaluesMixin = ChildHavingDictArgMixin
ChildrenExpressionDictOperationViewvaluesBaseMixin = ChildHavingDictArgMixin


class ChildrenHavingDictArgIterableMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionDictOperationUpdate2

    def __init__(
        self,
        dict_arg,
        iterable,
    ):
        dict_arg.parent = self

        self.subnode_dict_arg = dict_arg

        iterable.parent = self

        self.subnode_iterable = iterable

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_dict_arg,
            self.subnode_iterable,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("dict_arg", self.subnode_dict_arg),
            ("iterable", self.subnode_iterable),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_dict_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_dict_arg = new_node

            return

        value = self.subnode_iterable
        if old_node is value:
            new_node.parent = self

            self.subnode_iterable = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "dict_arg": self.subnode_dict_arg.makeClone(),
            "iterable": self.subnode_iterable.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_dict_arg.finalize()
        del self.subnode_dict_arg
        self.subnode_iterable.finalize()
        del self.subnode_iterable

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_dict_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_iterable.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionDictOperationUpdate2Mixin = ChildrenHavingDictArgIterableMixin


class ChildrenHavingDictArgIterablePairsTupleMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionDictOperationUpdate3

    def __init__(
        self,
        dict_arg,
        iterable,
        pairs,
    ):
        dict_arg.parent = self

        self.subnode_dict_arg = dict_arg

        iterable.parent = self

        self.subnode_iterable = iterable

        assert type(pairs) is tuple

        for val in pairs:
            val.parent = self

        self.subnode_pairs = pairs

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_dict_arg)
        result.append(self.subnode_iterable)
        result.extend(self.subnode_pairs)
        return tuple(result)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("dict_arg", self.subnode_dict_arg),
            ("iterable", self.subnode_iterable),
            ("pairs", self.subnode_pairs),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_dict_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_dict_arg = new_node

            return

        value = self.subnode_iterable
        if old_node is value:
            new_node.parent = self

            self.subnode_iterable = new_node

            return

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
            "dict_arg": self.subnode_dict_arg.makeClone(),
            "iterable": self.subnode_iterable.makeClone(),
            "pairs": tuple(v.makeClone() for v in self.subnode_pairs),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_dict_arg.finalize()
        del self.subnode_dict_arg
        self.subnode_iterable.finalize()
        del self.subnode_iterable
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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_dict_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_iterable.collectVariableAccesses(emit_read, emit_write)
        for element in self.subnode_pairs:
            element.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionDictOperationUpdate3Mixin = (
    ChildrenHavingDictArgIterablePairsTupleMixin
)


class ChildrenHavingDictArgKeyMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionDictOperationGet2
    #   ExpressionDictOperationHaskey
    #   ExpressionDictOperationItem
    #   ExpressionDictOperationPop2
    #   ExpressionDictOperationSetdefault2

    def __init__(
        self,
        dict_arg,
        key,
    ):
        dict_arg.parent = self

        self.subnode_dict_arg = dict_arg

        key.parent = self

        self.subnode_key = key

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_dict_arg,
            self.subnode_key,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("dict_arg", self.subnode_dict_arg),
            ("key", self.subnode_key),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_dict_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_dict_arg = new_node

            return

        value = self.subnode_key
        if old_node is value:
            new_node.parent = self

            self.subnode_key = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "dict_arg": self.subnode_dict_arg.makeClone(),
            "key": self.subnode_key.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_dict_arg.finalize()
        del self.subnode_dict_arg
        self.subnode_key.finalize()
        del self.subnode_key

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_dict_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_key.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionDictOperationGet2Mixin = ChildrenHavingDictArgKeyMixin
ChildrenExpressionDictOperationHaskeyMixin = ChildrenHavingDictArgKeyMixin
ChildrenExpressionDictOperationItemMixin = ChildrenHavingDictArgKeyMixin
ChildrenExpressionDictOperationPop2Mixin = ChildrenHavingDictArgKeyMixin
ChildrenExpressionDictOperationSetdefault2Mixin = ChildrenHavingDictArgKeyMixin


class ChildrenHavingDictArgKeyDefaultMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionDictOperationGet3
    #   ExpressionDictOperationPop3
    #   ExpressionDictOperationSetdefault3

    def __init__(
        self,
        dict_arg,
        key,
        default,
    ):
        dict_arg.parent = self

        self.subnode_dict_arg = dict_arg

        key.parent = self

        self.subnode_key = key

        default.parent = self

        self.subnode_default = default

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_dict_arg,
            self.subnode_key,
            self.subnode_default,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("dict_arg", self.subnode_dict_arg),
            ("key", self.subnode_key),
            ("default", self.subnode_default),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_dict_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_dict_arg = new_node

            return

        value = self.subnode_key
        if old_node is value:
            new_node.parent = self

            self.subnode_key = new_node

            return

        value = self.subnode_default
        if old_node is value:
            new_node.parent = self

            self.subnode_default = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "dict_arg": self.subnode_dict_arg.makeClone(),
            "key": self.subnode_key.makeClone(),
            "default": self.subnode_default.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_dict_arg.finalize()
        del self.subnode_dict_arg
        self.subnode_key.finalize()
        del self.subnode_key
        self.subnode_default.finalize()
        del self.subnode_default

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_dict_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_key.collectVariableAccesses(emit_read, emit_write)
        self.subnode_default.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionDictOperationGet3Mixin = ChildrenHavingDictArgKeyDefaultMixin
ChildrenExpressionDictOperationPop3Mixin = ChildrenHavingDictArgKeyDefaultMixin
ChildrenExpressionDictOperationSetdefault3Mixin = ChildrenHavingDictArgKeyDefaultMixin


class ChildrenHavingDictArgPairsTupleMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionDictOperationUpdatePairs

    def __init__(
        self,
        dict_arg,
        pairs,
    ):
        dict_arg.parent = self

        self.subnode_dict_arg = dict_arg

        assert type(pairs) is tuple

        for val in pairs:
            val.parent = self

        self.subnode_pairs = pairs

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_dict_arg)
        result.extend(self.subnode_pairs)
        return tuple(result)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("dict_arg", self.subnode_dict_arg),
            ("pairs", self.subnode_pairs),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_dict_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_dict_arg = new_node

            return

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
            "dict_arg": self.subnode_dict_arg.makeClone(),
            "pairs": tuple(v.makeClone() for v in self.subnode_pairs),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_dict_arg.finalize()
        del self.subnode_dict_arg
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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_dict_arg.collectVariableAccesses(emit_read, emit_write)
        for element in self.subnode_pairs:
            element.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionDictOperationUpdatePairsMixin = ChildrenHavingDictArgPairsTupleMixin


class ChildHavingDistMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionPkgResourcesGetDistribution
    #   ExpressionPkgResourcesGetDistributionCall

    def __init__(
        self,
        dist,
    ):
        dist.parent = self

        self.subnode_dist = dist

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_dist,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("dist", self.subnode_dist),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_dist
        if old_node is value:
            new_node.parent = self

            self.subnode_dist = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "dist": self.subnode_dist.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_dist.finalize()
        del self.subnode_dist

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_dist)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_dist.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionPkgResourcesGetDistributionMixin = ChildHavingDistMixin
ChildrenExpressionPkgResourcesGetDistributionCallMixin = ChildHavingDistMixin


class ChildHavingDistributionNameMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionImportlibMetadataBackportDistribution
    #   ExpressionImportlibMetadataBackportDistributionCall
    #   ExpressionImportlibMetadataBackportMetadata
    #   ExpressionImportlibMetadataBackportVersion
    #   ExpressionImportlibMetadataBackportVersionCall
    #   ExpressionImportlibMetadataDistribution
    #   ExpressionImportlibMetadataDistributionCall
    #   ExpressionImportlibMetadataMetadata
    #   ExpressionImportlibMetadataVersion
    #   ExpressionImportlibMetadataVersionCall

    def __init__(
        self,
        distribution_name,
    ):
        distribution_name.parent = self

        self.subnode_distribution_name = distribution_name

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

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_distribution_name)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_distribution_name.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionImportlibMetadataBackportDistributionMixin = (
    ChildHavingDistributionNameMixin
)
ChildrenExpressionImportlibMetadataBackportDistributionCallMixin = (
    ChildHavingDistributionNameMixin
)
ChildrenExpressionImportlibMetadataBackportMetadataMixin = (
    ChildHavingDistributionNameMixin
)
ChildrenExpressionImportlibMetadataBackportVersionMixin = (
    ChildHavingDistributionNameMixin
)
ChildrenExpressionImportlibMetadataBackportVersionCallMixin = (
    ChildHavingDistributionNameMixin
)
ChildrenExpressionImportlibMetadataDistributionMixin = ChildHavingDistributionNameMixin
ChildrenExpressionImportlibMetadataDistributionCallMixin = (
    ChildHavingDistributionNameMixin
)
ChildrenExpressionImportlibMetadataMetadataMixin = ChildHavingDistributionNameMixin
ChildrenExpressionImportlibMetadataVersionMixin = ChildHavingDistributionNameMixin
ChildrenExpressionImportlibMetadataVersionCallMixin = ChildHavingDistributionNameMixin


class ChildHavingElementsTupleMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionMakeList
    #   ExpressionMakeSet
    #   ExpressionMakeSetLiteral
    #   ExpressionMakeTuple

    def __init__(
        self,
        elements,
    ):
        assert type(elements) is tuple

        for val in elements:
            val.parent = self

        self.subnode_elements = elements

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

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        for element in self.subnode_elements:
            element.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionMakeListMixin = ChildHavingElementsTupleMixin
ChildrenExpressionMakeSetMixin = ChildHavingElementsTupleMixin
ChildrenExpressionMakeSetLiteralMixin = ChildHavingElementsTupleMixin
ChildrenExpressionMakeTupleMixin = ChildHavingElementsTupleMixin


class ChildHavingExceptionTypeMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionRaiseException

    def __init__(
        self,
        exception_type,
    ):
        exception_type.parent = self

        self.subnode_exception_type = exception_type

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_exception_type,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("exception_type", self.subnode_exception_type),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_exception_type
        if old_node is value:
            new_node.parent = self

            self.subnode_exception_type = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "exception_type": self.subnode_exception_type.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_exception_type.finalize()
        del self.subnode_exception_type

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_exception_type)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_exception_type.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionRaiseExceptionMixin = ChildHavingExceptionTypeMixin


class ChildHavingExitCodeOptionalMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionSysExit

    def __init__(
        self,
        exit_code,
    ):
        if exit_code is not None:
            exit_code.parent = self

        self.subnode_exit_code = exit_code

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        value = self.subnode_exit_code

        if value is None:
            return ()
        else:
            return (value,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("exit_code", self.subnode_exit_code),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_exit_code
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_exit_code = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "exit_code": (
                self.subnode_exit_code.makeClone()
                if self.subnode_exit_code is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        if self.subnode_exit_code is not None:
            self.subnode_exit_code.finalize()
        del self.subnode_exit_code

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = self.subnode_exit_code

        if expression is not None:
            expression = trace_collection.onExpression(expression)

            if expression.willRaiseAnyException():
                return (
                    expression,
                    "new_raise",
                    lambda: "For '%s' the child expression '%s' will raise."
                    % (self.getChildNameNice(), expression.getChildNameNice()),
                )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        subnode_exit_code = self.subnode_exit_code

        if subnode_exit_code is not None:
            self.subnode_exit_code.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionSysExitMixin = ChildHavingExitCodeOptionalMixin


class ChildHavingExpressionMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionAsyncWait
    #   ExpressionAsyncWaitEnter
    #   ExpressionAsyncWaitExit
    #   ExpressionAttributeCheck
    #   ExpressionAttributeLookupBytesCapitalize
    #   ExpressionAttributeLookupBytesCenter
    #   ExpressionAttributeLookupBytesCount
    #   ExpressionAttributeLookupBytesDecode
    #   ExpressionAttributeLookupBytesEndswith
    #   ExpressionAttributeLookupBytesExpandtabs
    #   ExpressionAttributeLookupBytesFind
    #   ExpressionAttributeLookupBytesIndex
    #   ExpressionAttributeLookupBytesIsalnum
    #   ExpressionAttributeLookupBytesIsalpha
    #   ExpressionAttributeLookupBytesIsdigit
    #   ExpressionAttributeLookupBytesIslower
    #   ExpressionAttributeLookupBytesIsspace
    #   ExpressionAttributeLookupBytesIstitle
    #   ExpressionAttributeLookupBytesIsupper
    #   ExpressionAttributeLookupBytesJoin
    #   ExpressionAttributeLookupBytesLjust
    #   ExpressionAttributeLookupBytesLower
    #   ExpressionAttributeLookupBytesLstrip
    #   ExpressionAttributeLookupBytesPartition
    #   ExpressionAttributeLookupBytesReplace
    #   ExpressionAttributeLookupBytesRfind
    #   ExpressionAttributeLookupBytesRindex
    #   ExpressionAttributeLookupBytesRjust
    #   ExpressionAttributeLookupBytesRpartition
    #   ExpressionAttributeLookupBytesRsplit
    #   ExpressionAttributeLookupBytesRstrip
    #   ExpressionAttributeLookupBytesSplit
    #   ExpressionAttributeLookupBytesSplitlines
    #   ExpressionAttributeLookupBytesStartswith
    #   ExpressionAttributeLookupBytesStrip
    #   ExpressionAttributeLookupBytesSwapcase
    #   ExpressionAttributeLookupBytesTitle
    #   ExpressionAttributeLookupBytesTranslate
    #   ExpressionAttributeLookupBytesUpper
    #   ExpressionAttributeLookupBytesZfill
    #   ExpressionAttributeLookupDictClear
    #   ExpressionAttributeLookupDictCopy
    #   ExpressionAttributeLookupDictFromkeys
    #   ExpressionAttributeLookupDictGet
    #   ExpressionAttributeLookupDictHaskey
    #   ExpressionAttributeLookupDictItems
    #   ExpressionAttributeLookupDictIteritems
    #   ExpressionAttributeLookupDictIterkeys
    #   ExpressionAttributeLookupDictItervalues
    #   ExpressionAttributeLookupDictKeys
    #   ExpressionAttributeLookupDictPop
    #   ExpressionAttributeLookupDictPopitem
    #   ExpressionAttributeLookupDictSetdefault
    #   ExpressionAttributeLookupDictUpdate
    #   ExpressionAttributeLookupDictValues
    #   ExpressionAttributeLookupDictViewitems
    #   ExpressionAttributeLookupDictViewkeys
    #   ExpressionAttributeLookupDictViewvalues
    #   ExpressionAttributeLookupFixedAppend
    #   ExpressionAttributeLookupFixedCapitalize
    #   ExpressionAttributeLookupFixedCasefold
    #   ExpressionAttributeLookupFixedCenter
    #   ExpressionAttributeLookupFixedClear
    #   ExpressionAttributeLookupFixedCopy
    #   ExpressionAttributeLookupFixedCount
    #   ExpressionAttributeLookupFixedDecode
    #   ExpressionAttributeLookupFixedEncode
    #   ExpressionAttributeLookupFixedEndswith
    #   ExpressionAttributeLookupFixedExpandtabs
    #   ExpressionAttributeLookupFixedExtend
    #   ExpressionAttributeLookupFixedFind
    #   ExpressionAttributeLookupFixedFormat
    #   ExpressionAttributeLookupFixedFormatmap
    #   ExpressionAttributeLookupFixedFromkeys
    #   ExpressionAttributeLookupFixedGet
    #   ExpressionAttributeLookupFixedHaskey
    #   ExpressionAttributeLookupFixedIndex
    #   ExpressionAttributeLookupFixedInsert
    #   ExpressionAttributeLookupFixedIsalnum
    #   ExpressionAttributeLookupFixedIsalpha
    #   ExpressionAttributeLookupFixedIsascii
    #   ExpressionAttributeLookupFixedIsdecimal
    #   ExpressionAttributeLookupFixedIsdigit
    #   ExpressionAttributeLookupFixedIsidentifier
    #   ExpressionAttributeLookupFixedIslower
    #   ExpressionAttributeLookupFixedIsnumeric
    #   ExpressionAttributeLookupFixedIsprintable
    #   ExpressionAttributeLookupFixedIsspace
    #   ExpressionAttributeLookupFixedIstitle
    #   ExpressionAttributeLookupFixedIsupper
    #   ExpressionAttributeLookupFixedItems
    #   ExpressionAttributeLookupFixedIteritems
    #   ExpressionAttributeLookupFixedIterkeys
    #   ExpressionAttributeLookupFixedItervalues
    #   ExpressionAttributeLookupFixedJoin
    #   ExpressionAttributeLookupFixedKeys
    #   ExpressionAttributeLookupFixedLjust
    #   ExpressionAttributeLookupFixedLower
    #   ExpressionAttributeLookupFixedLstrip
    #   ExpressionAttributeLookupFixedMaketrans
    #   ExpressionAttributeLookupFixedPartition
    #   ExpressionAttributeLookupFixedPop
    #   ExpressionAttributeLookupFixedPopitem
    #   ExpressionAttributeLookupFixedPrepare
    #   ExpressionAttributeLookupFixedRemove
    #   ExpressionAttributeLookupFixedReplace
    #   ExpressionAttributeLookupFixedReverse
    #   ExpressionAttributeLookupFixedRfind
    #   ExpressionAttributeLookupFixedRindex
    #   ExpressionAttributeLookupFixedRjust
    #   ExpressionAttributeLookupFixedRpartition
    #   ExpressionAttributeLookupFixedRsplit
    #   ExpressionAttributeLookupFixedRstrip
    #   ExpressionAttributeLookupFixedSetdefault
    #   ExpressionAttributeLookupFixedSort
    #   ExpressionAttributeLookupFixedSplit
    #   ExpressionAttributeLookupFixedSplitlines
    #   ExpressionAttributeLookupFixedStartswith
    #   ExpressionAttributeLookupFixedStrip
    #   ExpressionAttributeLookupFixedSwapcase
    #   ExpressionAttributeLookupFixedTitle
    #   ExpressionAttributeLookupFixedTranslate
    #   ExpressionAttributeLookupFixedUpdate
    #   ExpressionAttributeLookupFixedUpper
    #   ExpressionAttributeLookupFixedValues
    #   ExpressionAttributeLookupFixedViewitems
    #   ExpressionAttributeLookupFixedViewkeys
    #   ExpressionAttributeLookupFixedViewvalues
    #   ExpressionAttributeLookupFixedZfill
    #   ExpressionAttributeLookupListAppend
    #   ExpressionAttributeLookupListClear
    #   ExpressionAttributeLookupListCopy
    #   ExpressionAttributeLookupListCount
    #   ExpressionAttributeLookupListExtend
    #   ExpressionAttributeLookupListIndex
    #   ExpressionAttributeLookupListInsert
    #   ExpressionAttributeLookupListPop
    #   ExpressionAttributeLookupListRemove
    #   ExpressionAttributeLookupListReverse
    #   ExpressionAttributeLookupListSort
    #   ExpressionAttributeLookupStrCapitalize
    #   ExpressionAttributeLookupStrCasefold
    #   ExpressionAttributeLookupStrCenter
    #   ExpressionAttributeLookupStrCount
    #   ExpressionAttributeLookupStrDecode
    #   ExpressionAttributeLookupStrEncode
    #   ExpressionAttributeLookupStrEndswith
    #   ExpressionAttributeLookupStrExpandtabs
    #   ExpressionAttributeLookupStrFind
    #   ExpressionAttributeLookupStrFormat
    #   ExpressionAttributeLookupStrFormatmap
    #   ExpressionAttributeLookupStrIndex
    #   ExpressionAttributeLookupStrIsalnum
    #   ExpressionAttributeLookupStrIsalpha
    #   ExpressionAttributeLookupStrIsascii
    #   ExpressionAttributeLookupStrIsdecimal
    #   ExpressionAttributeLookupStrIsdigit
    #   ExpressionAttributeLookupStrIsidentifier
    #   ExpressionAttributeLookupStrIslower
    #   ExpressionAttributeLookupStrIsnumeric
    #   ExpressionAttributeLookupStrIsprintable
    #   ExpressionAttributeLookupStrIsspace
    #   ExpressionAttributeLookupStrIstitle
    #   ExpressionAttributeLookupStrIsupper
    #   ExpressionAttributeLookupStrJoin
    #   ExpressionAttributeLookupStrLjust
    #   ExpressionAttributeLookupStrLower
    #   ExpressionAttributeLookupStrLstrip
    #   ExpressionAttributeLookupStrMaketrans
    #   ExpressionAttributeLookupStrPartition
    #   ExpressionAttributeLookupStrReplace
    #   ExpressionAttributeLookupStrRfind
    #   ExpressionAttributeLookupStrRindex
    #   ExpressionAttributeLookupStrRjust
    #   ExpressionAttributeLookupStrRpartition
    #   ExpressionAttributeLookupStrRsplit
    #   ExpressionAttributeLookupStrRstrip
    #   ExpressionAttributeLookupStrSplit
    #   ExpressionAttributeLookupStrSplitlines
    #   ExpressionAttributeLookupStrStartswith
    #   ExpressionAttributeLookupStrStrip
    #   ExpressionAttributeLookupStrSwapcase
    #   ExpressionAttributeLookupStrTitle
    #   ExpressionAttributeLookupStrTranslate
    #   ExpressionAttributeLookupStrUpper
    #   ExpressionAttributeLookupStrZfill
    #   ExpressionAttributeLookupTypePrepare
    #   ExpressionYield
    #   ExpressionYieldFrom
    #   ExpressionYieldFromAwaitable

    def __init__(
        self,
        expression,
    ):
        expression.parent = self

        self.subnode_expression = expression

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_expression.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionAsyncWaitMixin = ChildHavingExpressionMixin
ChildrenExpressionAsyncWaitEnterMixin = ChildHavingExpressionMixin
ChildrenExpressionAsyncWaitExitMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeCheckMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesCapitalizeMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesCenterMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesCountMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesDecodeMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesEndswithMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesExpandtabsMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesFindMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesIndexMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesIsalnumMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesIsalphaMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesIsdigitMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesIslowerMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesIsspaceMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesIstitleMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesIsupperMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesJoinMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesLjustMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesLowerMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesLstripMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesPartitionMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesReplaceMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesRfindMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesRindexMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesRjustMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesRpartitionMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesRsplitMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesRstripMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesSplitMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesSplitlinesMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesStartswithMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesStripMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesSwapcaseMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesTitleMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesTranslateMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesUpperMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupBytesZfillMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupDictClearMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupDictCopyMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupDictFromkeysMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupDictGetMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupDictHaskeyMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupDictItemsMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupDictIteritemsMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupDictIterkeysMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupDictItervaluesMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupDictKeysMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupDictPopMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupDictPopitemMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupDictSetdefaultMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupDictUpdateMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupDictValuesMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupDictViewitemsMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupDictViewkeysMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupDictViewvaluesMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedAppendMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedCapitalizeMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedCasefoldMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedCenterMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedClearMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedCopyMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedCountMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedDecodeMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedEncodeMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedEndswithMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedExpandtabsMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedExtendMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedFindMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedFormatMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedFormatmapMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedFromkeysMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedGetMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedHaskeyMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedIndexMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedInsertMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedIsalnumMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedIsalphaMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedIsasciiMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedIsdecimalMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedIsdigitMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedIsidentifierMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedIslowerMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedIsnumericMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedIsprintableMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedIsspaceMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedIstitleMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedIsupperMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedItemsMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedIteritemsMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedIterkeysMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedItervaluesMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedJoinMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedKeysMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedLjustMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedLowerMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedLstripMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedMaketransMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedPartitionMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedPopMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedPopitemMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedPrepareMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedRemoveMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedReplaceMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedReverseMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedRfindMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedRindexMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedRjustMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedRpartitionMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedRsplitMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedRstripMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedSetdefaultMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedSortMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedSplitMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedSplitlinesMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedStartswithMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedStripMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedSwapcaseMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedTitleMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedTranslateMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedUpdateMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedUpperMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedValuesMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedViewitemsMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedViewkeysMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedViewvaluesMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupFixedZfillMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupListAppendMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupListClearMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupListCopyMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupListCountMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupListExtendMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupListIndexMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupListInsertMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupListPopMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupListRemoveMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupListReverseMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupListSortMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrCapitalizeMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrCasefoldMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrCenterMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrCountMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrDecodeMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrEncodeMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrEndswithMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrExpandtabsMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrFindMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrFormatMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrFormatmapMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrIndexMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrIsalnumMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrIsalphaMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrIsasciiMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrIsdecimalMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrIsdigitMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrIsidentifierMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrIslowerMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrIsnumericMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrIsprintableMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrIsspaceMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrIstitleMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrIsupperMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrJoinMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrLjustMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrLowerMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrLstripMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrMaketransMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrPartitionMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrReplaceMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrRfindMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrRindexMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrRjustMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrRpartitionMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrRsplitMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrRstripMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrSplitMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrSplitlinesMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrStartswithMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrStripMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrSwapcaseMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrTitleMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrTranslateMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrUpperMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupStrZfillMixin = ChildHavingExpressionMixin
ChildrenExpressionAttributeLookupTypePrepareMixin = ChildHavingExpressionMixin
ChildrenExpressionYieldMixin = ChildHavingExpressionMixin
ChildrenExpressionYieldFromMixin = ChildHavingExpressionMixin
ChildrenExpressionYieldFromAwaitableMixin = ChildHavingExpressionMixin


class ChildrenHavingExpressionLowerAutoNoneUpperAutoNoneMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionSliceLookup

    def __init__(
        self,
        expression,
        lower,
        upper,
    ):
        expression.parent = self

        self.subnode_expression = expression

        lower = convertNoneConstantToNone(lower)
        if lower is not None:
            lower.parent = self

        self.subnode_lower = lower

        upper = convertNoneConstantToNone(upper)
        if upper is not None:
            upper.parent = self

        self.subnode_upper = upper

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_expression)
        value = self.subnode_lower
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_upper
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
            ("expression", self.subnode_expression),
            ("lower", self.subnode_lower),
            ("upper", self.subnode_upper),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_expression
        if old_node is value:
            new_node.parent = self

            self.subnode_expression = new_node

            return

        value = self.subnode_lower
        if old_node is value:
            new_node = convertNoneConstantToNone(new_node)
            if new_node is not None:
                new_node.parent = self

            self.subnode_lower = new_node

            return

        value = self.subnode_upper
        if old_node is value:
            new_node = convertNoneConstantToNone(new_node)
            if new_node is not None:
                new_node.parent = self

            self.subnode_upper = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "expression": self.subnode_expression.makeClone(),
            "lower": (
                self.subnode_lower.makeClone()
                if self.subnode_lower is not None
                else None
            ),
            "upper": (
                self.subnode_upper.makeClone()
                if self.subnode_upper is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_expression.finalize()
        del self.subnode_expression
        if self.subnode_lower is not None:
            self.subnode_lower.finalize()
        del self.subnode_lower
        if self.subnode_upper is not None:
            self.subnode_upper.finalize()
        del self.subnode_upper

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_expression.collectVariableAccesses(emit_read, emit_write)
        subnode_lower = self.subnode_lower

        if subnode_lower is not None:
            self.subnode_lower.collectVariableAccesses(emit_read, emit_write)
        subnode_upper = self.subnode_upper

        if subnode_upper is not None:
            self.subnode_upper.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionSliceLookupMixin = (
    ChildrenHavingExpressionLowerAutoNoneUpperAutoNoneMixin
)


class ChildrenHavingExpressionMatchTypeMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionMatchArgs

    def __init__(
        self,
        expression,
        match_type,
    ):
        expression.parent = self

        self.subnode_expression = expression

        match_type.parent = self

        self.subnode_match_type = match_type

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_expression,
            self.subnode_match_type,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("expression", self.subnode_expression),
            ("match_type", self.subnode_match_type),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_expression
        if old_node is value:
            new_node.parent = self

            self.subnode_expression = new_node

            return

        value = self.subnode_match_type
        if old_node is value:
            new_node.parent = self

            self.subnode_match_type = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "expression": self.subnode_expression.makeClone(),
            "match_type": self.subnode_match_type.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_expression.finalize()
        del self.subnode_expression
        self.subnode_match_type.finalize()
        del self.subnode_match_type

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_expression.collectVariableAccesses(emit_read, emit_write)
        self.subnode_match_type.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionMatchArgsMixin = ChildrenHavingExpressionMatchTypeMixin


class ChildrenHavingExpressionNameDefaultOptionalMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinGetattr

    def __init__(
        self,
        expression,
        name,
        default,
    ):
        expression.parent = self

        self.subnode_expression = expression

        name.parent = self

        self.subnode_name = name

        if default is not None:
            default.parent = self

        self.subnode_default = default

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_expression)
        result.append(self.subnode_name)
        value = self.subnode_default
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
            ("expression", self.subnode_expression),
            ("name", self.subnode_name),
            ("default", self.subnode_default),
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

        value = self.subnode_default
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_default = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "expression": self.subnode_expression.makeClone(),
            "name": self.subnode_name.makeClone(),
            "default": (
                self.subnode_default.makeClone()
                if self.subnode_default is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_expression.finalize()
        del self.subnode_expression
        self.subnode_name.finalize()
        del self.subnode_name
        if self.subnode_default is not None:
            self.subnode_default.finalize()
        del self.subnode_default

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_expression.collectVariableAccesses(emit_read, emit_write)
        self.subnode_name.collectVariableAccesses(emit_read, emit_write)
        subnode_default = self.subnode_default

        if subnode_default is not None:
            self.subnode_default.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinGetattrMixin = ChildrenHavingExpressionNameDefaultOptionalMixin


class ChildrenHavingExpressionNameValueMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinSetattr

    def __init__(
        self,
        expression,
        name,
        value,
    ):
        expression.parent = self

        self.subnode_expression = expression

        name.parent = self

        self.subnode_name = name

        value.parent = self

        self.subnode_value = value

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_expression,
            self.subnode_name,
            self.subnode_value,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("expression", self.subnode_expression),
            ("name", self.subnode_name),
            ("value", self.subnode_value),
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
            "expression": self.subnode_expression.makeClone(),
            "name": self.subnode_name.makeClone(),
            "value": self.subnode_value.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_expression.finalize()
        del self.subnode_expression
        self.subnode_name.finalize()
        del self.subnode_name
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

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_expression.collectVariableAccesses(emit_read, emit_write)
        self.subnode_name.collectVariableAccesses(emit_read, emit_write)
        self.subnode_value.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinSetattrMixin = ChildrenHavingExpressionNameValueMixin


class ChildrenHavingExpressionSubscriptMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionMatchSubscriptCheck
    #   ExpressionSubscriptLookup
    #   ExpressionSubscriptLookupForUnpack

    def __init__(
        self,
        expression,
        subscript,
    ):
        expression.parent = self

        self.subnode_expression = expression

        subscript.parent = self

        self.subnode_subscript = subscript

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_expression,
            self.subnode_subscript,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("expression", self.subnode_expression),
            ("subscript", self.subnode_subscript),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_expression
        if old_node is value:
            new_node.parent = self

            self.subnode_expression = new_node

            return

        value = self.subnode_subscript
        if old_node is value:
            new_node.parent = self

            self.subnode_subscript = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "expression": self.subnode_expression.makeClone(),
            "subscript": self.subnode_subscript.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_expression.finalize()
        del self.subnode_expression
        self.subnode_subscript.finalize()
        del self.subnode_subscript

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_expression.collectVariableAccesses(emit_read, emit_write)
        self.subnode_subscript.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionMatchSubscriptCheckMixin = ChildrenHavingExpressionSubscriptMixin
ChildrenExpressionSubscriptLookupMixin = ChildrenHavingExpressionSubscriptMixin
ChildrenExpressionSubscriptLookupForUnpackMixin = ChildrenHavingExpressionSubscriptMixin


class ChildHavingFallbackMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionLocalsMappingVariableRefOrFallback
    #   ExpressionLocalsVariableRefOrFallback

    def __init__(
        self,
        fallback,
    ):
        fallback.parent = self

        self.subnode_fallback = fallback

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_fallback,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("fallback", self.subnode_fallback),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_fallback
        if old_node is value:
            new_node.parent = self

            self.subnode_fallback = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "fallback": self.subnode_fallback.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_fallback.finalize()
        del self.subnode_fallback

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_fallback)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_fallback.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionLocalsMappingVariableRefOrFallbackMixin = ChildHavingFallbackMixin
ChildrenExpressionLocalsVariableRefOrFallbackMixin = ChildHavingFallbackMixin


class ChildrenHavingFilenameModeOptionalBufferingOptionalMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinOpenP2

    def __init__(
        self,
        filename,
        mode,
        buffering,
    ):
        filename.parent = self

        self.subnode_filename = filename

        if mode is not None:
            mode.parent = self

        self.subnode_mode = mode

        if buffering is not None:
            buffering.parent = self

        self.subnode_buffering = buffering

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_filename)
        value = self.subnode_mode
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_buffering
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
            ("filename", self.subnode_filename),
            ("mode", self.subnode_mode),
            ("buffering", self.subnode_buffering),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_filename
        if old_node is value:
            new_node.parent = self

            self.subnode_filename = new_node

            return

        value = self.subnode_mode
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_mode = new_node

            return

        value = self.subnode_buffering
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_buffering = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "filename": self.subnode_filename.makeClone(),
            "mode": (
                self.subnode_mode.makeClone() if self.subnode_mode is not None else None
            ),
            "buffering": (
                self.subnode_buffering.makeClone()
                if self.subnode_buffering is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_filename.finalize()
        del self.subnode_filename
        if self.subnode_mode is not None:
            self.subnode_mode.finalize()
        del self.subnode_mode
        if self.subnode_buffering is not None:
            self.subnode_buffering.finalize()
        del self.subnode_buffering

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_filename.collectVariableAccesses(emit_read, emit_write)
        subnode_mode = self.subnode_mode

        if subnode_mode is not None:
            self.subnode_mode.collectVariableAccesses(emit_read, emit_write)
        subnode_buffering = self.subnode_buffering

        if subnode_buffering is not None:
            self.subnode_buffering.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinOpenP2Mixin = (
    ChildrenHavingFilenameModeOptionalBufferingOptionalMixin
)


class ChildrenHavingFilenameModeOptionalBufferingOptionalEncodingOptionalErrorsOptionalNewlineOptionalClosefdOptionalOpenerOptionalMixin(
    object
):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinOpenP3

    def __init__(
        self,
        filename,
        mode,
        buffering,
        encoding,
        errors,
        newline,
        closefd,
        opener,
    ):
        filename.parent = self

        self.subnode_filename = filename

        if mode is not None:
            mode.parent = self

        self.subnode_mode = mode

        if buffering is not None:
            buffering.parent = self

        self.subnode_buffering = buffering

        if encoding is not None:
            encoding.parent = self

        self.subnode_encoding = encoding

        if errors is not None:
            errors.parent = self

        self.subnode_errors = errors

        if newline is not None:
            newline.parent = self

        self.subnode_newline = newline

        if closefd is not None:
            closefd.parent = self

        self.subnode_closefd = closefd

        if opener is not None:
            opener.parent = self

        self.subnode_opener = opener

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_filename)
        value = self.subnode_mode
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_buffering
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_encoding
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_errors
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_newline
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_closefd
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_opener
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
            ("filename", self.subnode_filename),
            ("mode", self.subnode_mode),
            ("buffering", self.subnode_buffering),
            ("encoding", self.subnode_encoding),
            ("errors", self.subnode_errors),
            ("newline", self.subnode_newline),
            ("closefd", self.subnode_closefd),
            ("opener", self.subnode_opener),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_filename
        if old_node is value:
            new_node.parent = self

            self.subnode_filename = new_node

            return

        value = self.subnode_mode
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_mode = new_node

            return

        value = self.subnode_buffering
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_buffering = new_node

            return

        value = self.subnode_encoding
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_encoding = new_node

            return

        value = self.subnode_errors
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_errors = new_node

            return

        value = self.subnode_newline
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_newline = new_node

            return

        value = self.subnode_closefd
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_closefd = new_node

            return

        value = self.subnode_opener
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_opener = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "filename": self.subnode_filename.makeClone(),
            "mode": (
                self.subnode_mode.makeClone() if self.subnode_mode is not None else None
            ),
            "buffering": (
                self.subnode_buffering.makeClone()
                if self.subnode_buffering is not None
                else None
            ),
            "encoding": (
                self.subnode_encoding.makeClone()
                if self.subnode_encoding is not None
                else None
            ),
            "errors": (
                self.subnode_errors.makeClone()
                if self.subnode_errors is not None
                else None
            ),
            "newline": (
                self.subnode_newline.makeClone()
                if self.subnode_newline is not None
                else None
            ),
            "closefd": (
                self.subnode_closefd.makeClone()
                if self.subnode_closefd is not None
                else None
            ),
            "opener": (
                self.subnode_opener.makeClone()
                if self.subnode_opener is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_filename.finalize()
        del self.subnode_filename
        if self.subnode_mode is not None:
            self.subnode_mode.finalize()
        del self.subnode_mode
        if self.subnode_buffering is not None:
            self.subnode_buffering.finalize()
        del self.subnode_buffering
        if self.subnode_encoding is not None:
            self.subnode_encoding.finalize()
        del self.subnode_encoding
        if self.subnode_errors is not None:
            self.subnode_errors.finalize()
        del self.subnode_errors
        if self.subnode_newline is not None:
            self.subnode_newline.finalize()
        del self.subnode_newline
        if self.subnode_closefd is not None:
            self.subnode_closefd.finalize()
        del self.subnode_closefd
        if self.subnode_opener is not None:
            self.subnode_opener.finalize()
        del self.subnode_opener

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_filename.collectVariableAccesses(emit_read, emit_write)
        subnode_mode = self.subnode_mode

        if subnode_mode is not None:
            self.subnode_mode.collectVariableAccesses(emit_read, emit_write)
        subnode_buffering = self.subnode_buffering

        if subnode_buffering is not None:
            self.subnode_buffering.collectVariableAccesses(emit_read, emit_write)
        subnode_encoding = self.subnode_encoding

        if subnode_encoding is not None:
            self.subnode_encoding.collectVariableAccesses(emit_read, emit_write)
        subnode_errors = self.subnode_errors

        if subnode_errors is not None:
            self.subnode_errors.collectVariableAccesses(emit_read, emit_write)
        subnode_newline = self.subnode_newline

        if subnode_newline is not None:
            self.subnode_newline.collectVariableAccesses(emit_read, emit_write)
        subnode_closefd = self.subnode_closefd

        if subnode_closefd is not None:
            self.subnode_closefd.collectVariableAccesses(emit_read, emit_write)
        subnode_opener = self.subnode_opener

        if subnode_opener is not None:
            self.subnode_opener.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinOpenP3Mixin = ChildrenHavingFilenameModeOptionalBufferingOptionalEncodingOptionalErrorsOptionalNewlineOptionalClosefdOptionalOpenerOptionalMixin


class ChildrenHavingFuncOptionalInputSignatureOptionalAutographOptionalJitCompileOptionalReduceRetracingOptionalExperimentalImplementsOptionalExperimentalAutographOptionsOptionalExperimentalAttributesOptionalExperimentalRelaxShapesOptionalExperimentalCompileOptionalExperimentalFollowTypeHintsOptionalMixin(
    object
):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionTensorflowFunction
    #   ExpressionTensorflowFunctionCall

    def __init__(
        self,
        func,
        input_signature,
        autograph,
        jit_compile,
        reduce_retracing,
        experimental_implements,
        experimental_autograph_options,
        experimental_attributes,
        experimental_relax_shapes,
        experimental_compile,
        experimental_follow_type_hints,
    ):
        if func is not None:
            func.parent = self

        self.subnode_func = func

        if input_signature is not None:
            input_signature.parent = self

        self.subnode_input_signature = input_signature

        if autograph is not None:
            autograph.parent = self

        self.subnode_autograph = autograph

        if jit_compile is not None:
            jit_compile.parent = self

        self.subnode_jit_compile = jit_compile

        if reduce_retracing is not None:
            reduce_retracing.parent = self

        self.subnode_reduce_retracing = reduce_retracing

        if experimental_implements is not None:
            experimental_implements.parent = self

        self.subnode_experimental_implements = experimental_implements

        if experimental_autograph_options is not None:
            experimental_autograph_options.parent = self

        self.subnode_experimental_autograph_options = experimental_autograph_options

        if experimental_attributes is not None:
            experimental_attributes.parent = self

        self.subnode_experimental_attributes = experimental_attributes

        if experimental_relax_shapes is not None:
            experimental_relax_shapes.parent = self

        self.subnode_experimental_relax_shapes = experimental_relax_shapes

        if experimental_compile is not None:
            experimental_compile.parent = self

        self.subnode_experimental_compile = experimental_compile

        if experimental_follow_type_hints is not None:
            experimental_follow_type_hints.parent = self

        self.subnode_experimental_follow_type_hints = experimental_follow_type_hints

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        value = self.subnode_func
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_input_signature
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_autograph
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_jit_compile
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_reduce_retracing
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_experimental_implements
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_experimental_autograph_options
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_experimental_attributes
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_experimental_relax_shapes
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_experimental_compile
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_experimental_follow_type_hints
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
            ("func", self.subnode_func),
            ("input_signature", self.subnode_input_signature),
            ("autograph", self.subnode_autograph),
            ("jit_compile", self.subnode_jit_compile),
            ("reduce_retracing", self.subnode_reduce_retracing),
            ("experimental_implements", self.subnode_experimental_implements),
            (
                "experimental_autograph_options",
                self.subnode_experimental_autograph_options,
            ),
            ("experimental_attributes", self.subnode_experimental_attributes),
            ("experimental_relax_shapes", self.subnode_experimental_relax_shapes),
            ("experimental_compile", self.subnode_experimental_compile),
            (
                "experimental_follow_type_hints",
                self.subnode_experimental_follow_type_hints,
            ),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_func
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_func = new_node

            return

        value = self.subnode_input_signature
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_input_signature = new_node

            return

        value = self.subnode_autograph
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_autograph = new_node

            return

        value = self.subnode_jit_compile
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_jit_compile = new_node

            return

        value = self.subnode_reduce_retracing
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_reduce_retracing = new_node

            return

        value = self.subnode_experimental_implements
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_experimental_implements = new_node

            return

        value = self.subnode_experimental_autograph_options
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_experimental_autograph_options = new_node

            return

        value = self.subnode_experimental_attributes
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_experimental_attributes = new_node

            return

        value = self.subnode_experimental_relax_shapes
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_experimental_relax_shapes = new_node

            return

        value = self.subnode_experimental_compile
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_experimental_compile = new_node

            return

        value = self.subnode_experimental_follow_type_hints
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_experimental_follow_type_hints = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "func": (
                self.subnode_func.makeClone() if self.subnode_func is not None else None
            ),
            "input_signature": (
                self.subnode_input_signature.makeClone()
                if self.subnode_input_signature is not None
                else None
            ),
            "autograph": (
                self.subnode_autograph.makeClone()
                if self.subnode_autograph is not None
                else None
            ),
            "jit_compile": (
                self.subnode_jit_compile.makeClone()
                if self.subnode_jit_compile is not None
                else None
            ),
            "reduce_retracing": (
                self.subnode_reduce_retracing.makeClone()
                if self.subnode_reduce_retracing is not None
                else None
            ),
            "experimental_implements": (
                self.subnode_experimental_implements.makeClone()
                if self.subnode_experimental_implements is not None
                else None
            ),
            "experimental_autograph_options": (
                self.subnode_experimental_autograph_options.makeClone()
                if self.subnode_experimental_autograph_options is not None
                else None
            ),
            "experimental_attributes": (
                self.subnode_experimental_attributes.makeClone()
                if self.subnode_experimental_attributes is not None
                else None
            ),
            "experimental_relax_shapes": (
                self.subnode_experimental_relax_shapes.makeClone()
                if self.subnode_experimental_relax_shapes is not None
                else None
            ),
            "experimental_compile": (
                self.subnode_experimental_compile.makeClone()
                if self.subnode_experimental_compile is not None
                else None
            ),
            "experimental_follow_type_hints": (
                self.subnode_experimental_follow_type_hints.makeClone()
                if self.subnode_experimental_follow_type_hints is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        if self.subnode_func is not None:
            self.subnode_func.finalize()
        del self.subnode_func
        if self.subnode_input_signature is not None:
            self.subnode_input_signature.finalize()
        del self.subnode_input_signature
        if self.subnode_autograph is not None:
            self.subnode_autograph.finalize()
        del self.subnode_autograph
        if self.subnode_jit_compile is not None:
            self.subnode_jit_compile.finalize()
        del self.subnode_jit_compile
        if self.subnode_reduce_retracing is not None:
            self.subnode_reduce_retracing.finalize()
        del self.subnode_reduce_retracing
        if self.subnode_experimental_implements is not None:
            self.subnode_experimental_implements.finalize()
        del self.subnode_experimental_implements
        if self.subnode_experimental_autograph_options is not None:
            self.subnode_experimental_autograph_options.finalize()
        del self.subnode_experimental_autograph_options
        if self.subnode_experimental_attributes is not None:
            self.subnode_experimental_attributes.finalize()
        del self.subnode_experimental_attributes
        if self.subnode_experimental_relax_shapes is not None:
            self.subnode_experimental_relax_shapes.finalize()
        del self.subnode_experimental_relax_shapes
        if self.subnode_experimental_compile is not None:
            self.subnode_experimental_compile.finalize()
        del self.subnode_experimental_compile
        if self.subnode_experimental_follow_type_hints is not None:
            self.subnode_experimental_follow_type_hints.finalize()
        del self.subnode_experimental_follow_type_hints

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        subnode_func = self.subnode_func

        if subnode_func is not None:
            self.subnode_func.collectVariableAccesses(emit_read, emit_write)
        subnode_input_signature = self.subnode_input_signature

        if subnode_input_signature is not None:
            self.subnode_input_signature.collectVariableAccesses(emit_read, emit_write)
        subnode_autograph = self.subnode_autograph

        if subnode_autograph is not None:
            self.subnode_autograph.collectVariableAccesses(emit_read, emit_write)
        subnode_jit_compile = self.subnode_jit_compile

        if subnode_jit_compile is not None:
            self.subnode_jit_compile.collectVariableAccesses(emit_read, emit_write)
        subnode_reduce_retracing = self.subnode_reduce_retracing

        if subnode_reduce_retracing is not None:
            self.subnode_reduce_retracing.collectVariableAccesses(emit_read, emit_write)
        subnode_experimental_implements = self.subnode_experimental_implements

        if subnode_experimental_implements is not None:
            self.subnode_experimental_implements.collectVariableAccesses(
                emit_read, emit_write
            )
        subnode_experimental_autograph_options = (
            self.subnode_experimental_autograph_options
        )

        if subnode_experimental_autograph_options is not None:
            self.subnode_experimental_autograph_options.collectVariableAccesses(
                emit_read, emit_write
            )
        subnode_experimental_attributes = self.subnode_experimental_attributes

        if subnode_experimental_attributes is not None:
            self.subnode_experimental_attributes.collectVariableAccesses(
                emit_read, emit_write
            )
        subnode_experimental_relax_shapes = self.subnode_experimental_relax_shapes

        if subnode_experimental_relax_shapes is not None:
            self.subnode_experimental_relax_shapes.collectVariableAccesses(
                emit_read, emit_write
            )
        subnode_experimental_compile = self.subnode_experimental_compile

        if subnode_experimental_compile is not None:
            self.subnode_experimental_compile.collectVariableAccesses(
                emit_read, emit_write
            )
        subnode_experimental_follow_type_hints = (
            self.subnode_experimental_follow_type_hints
        )

        if subnode_experimental_follow_type_hints is not None:
            self.subnode_experimental_follow_type_hints.collectVariableAccesses(
                emit_read, emit_write
            )


# Assign the names that are easier to import with a stable name.
ChildrenExpressionTensorflowFunctionMixin = ChildrenHavingFuncOptionalInputSignatureOptionalAutographOptionalJitCompileOptionalReduceRetracingOptionalExperimentalImplementsOptionalExperimentalAutographOptionsOptionalExperimentalAttributesOptionalExperimentalRelaxShapesOptionalExperimentalCompileOptionalExperimentalFollowTypeHintsOptionalMixin
ChildrenExpressionTensorflowFunctionCallMixin = ChildrenHavingFuncOptionalInputSignatureOptionalAutographOptionalJitCompileOptionalReduceRetracingOptionalExperimentalImplementsOptionalExperimentalAutographOptionsOptionalExperimentalAttributesOptionalExperimentalRelaxShapesOptionalExperimentalCompileOptionalExperimentalFollowTypeHintsOptionalMixin


class ChildrenHavingFunctionValuesTupleMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionFunctionCall

    def __init__(
        self,
        function,
        values,
    ):
        function.parent = self

        self.subnode_function = function

        assert type(values) is tuple

        for val in values:
            val.parent = self

        self.subnode_values = values

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_function)
        result.extend(self.subnode_values)
        return tuple(result)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("function", self.subnode_function),
            ("values", self.subnode_values),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_function
        if old_node is value:
            new_node.parent = self

            self.subnode_function = new_node

            return

        value = self.subnode_values
        if old_node in value:
            if new_node is not None:
                new_node.parent = self

                self.subnode_values = tuple(
                    (val if val is not old_node else new_node) for val in value
                )
            else:
                self.subnode_values = tuple(val for val in value if val is not old_node)

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "function": self.subnode_function.makeClone(),
            "values": tuple(v.makeClone() for v in self.subnode_values),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_function.finalize()
        del self.subnode_function
        for c in self.subnode_values:
            c.finalize()
        del self.subnode_values

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_function.collectVariableAccesses(emit_read, emit_write)
        for element in self.subnode_values:
            element.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionFunctionCallMixin = ChildrenHavingFunctionValuesTupleMixin


class ChildHavingGeneratorRefMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionMakeGeneratorObject

    def __init__(
        self,
        generator_ref,
    ):
        generator_ref.parent = self

        self.subnode_generator_ref = generator_ref

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_generator_ref,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("generator_ref", self.subnode_generator_ref),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_generator_ref
        if old_node is value:
            new_node.parent = self

            self.subnode_generator_ref = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "generator_ref": self.subnode_generator_ref.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_generator_ref.finalize()
        del self.subnode_generator_ref

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_generator_ref)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_generator_ref.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionMakeGeneratorObjectMixin = ChildHavingGeneratorRefMixin


class ChildrenHavingGroupNameOptionalMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionPkgResourcesIterEntryPoints
    #   ExpressionPkgResourcesIterEntryPointsCall

    def __init__(
        self,
        group,
        name,
    ):
        group.parent = self

        self.subnode_group = group

        if name is not None:
            name.parent = self

        self.subnode_name = name

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_group)
        value = self.subnode_name
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
            ("group", self.subnode_group),
            ("name", self.subnode_name),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_group
        if old_node is value:
            new_node.parent = self

            self.subnode_group = new_node

            return

        value = self.subnode_name
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_name = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "group": self.subnode_group.makeClone(),
            "name": (
                self.subnode_name.makeClone() if self.subnode_name is not None else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_group.finalize()
        del self.subnode_group
        if self.subnode_name is not None:
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

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_group.collectVariableAccesses(emit_read, emit_write)
        subnode_name = self.subnode_name

        if subnode_name is not None:
            self.subnode_name.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionPkgResourcesIterEntryPointsMixin = (
    ChildrenHavingGroupNameOptionalMixin
)
ChildrenExpressionPkgResourcesIterEntryPointsCallMixin = (
    ChildrenHavingGroupNameOptionalMixin
)


class ChildrenHavingInstanceClassesMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinIsinstance

    def __init__(
        self,
        instance,
        classes,
    ):
        instance.parent = self

        self.subnode_instance = instance

        classes.parent = self

        self.subnode_classes = classes

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_instance,
            self.subnode_classes,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("instance", self.subnode_instance),
            ("classes", self.subnode_classes),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_instance
        if old_node is value:
            new_node.parent = self

            self.subnode_instance = new_node

            return

        value = self.subnode_classes
        if old_node is value:
            new_node.parent = self

            self.subnode_classes = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "instance": self.subnode_instance.makeClone(),
            "classes": self.subnode_classes.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_instance.finalize()
        del self.subnode_instance
        self.subnode_classes.finalize()
        del self.subnode_classes

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_instance.collectVariableAccesses(emit_read, emit_write)
        self.subnode_classes.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinIsinstanceMixin = ChildrenHavingInstanceClassesMixin


class ChildHavingIterableMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionDictOperationFromkeys2

    def __init__(
        self,
        iterable,
    ):
        iterable.parent = self

        self.subnode_iterable = iterable

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_iterable,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("iterable", self.subnode_iterable),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_iterable
        if old_node is value:
            new_node.parent = self

            self.subnode_iterable = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "iterable": self.subnode_iterable.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_iterable.finalize()
        del self.subnode_iterable

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_iterable)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_iterable.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionDictOperationFromkeys2Mixin = ChildHavingIterableMixin


class ChildrenHavingIterableValueMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionDictOperationFromkeys3

    def __init__(
        self,
        iterable,
        value,
    ):
        iterable.parent = self

        self.subnode_iterable = iterable

        value.parent = self

        self.subnode_value = value

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_iterable,
            self.subnode_value,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("iterable", self.subnode_iterable),
            ("value", self.subnode_value),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_iterable
        if old_node is value:
            new_node.parent = self

            self.subnode_iterable = new_node

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
            "iterable": self.subnode_iterable.makeClone(),
            "value": self.subnode_value.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_iterable.finalize()
        del self.subnode_iterable
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

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_iterable.collectVariableAccesses(emit_read, emit_write)
        self.subnode_value.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionDictOperationFromkeys3Mixin = ChildrenHavingIterableValueMixin


class ChildrenHavingIteratorDefaultMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinNext2

    def __init__(
        self,
        iterator,
        default,
    ):
        iterator.parent = self

        self.subnode_iterator = iterator

        default.parent = self

        self.subnode_default = default

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_iterator,
            self.subnode_default,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("iterator", self.subnode_iterator),
            ("default", self.subnode_default),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_iterator
        if old_node is value:
            new_node.parent = self

            self.subnode_iterator = new_node

            return

        value = self.subnode_default
        if old_node is value:
            new_node.parent = self

            self.subnode_default = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "iterator": self.subnode_iterator.makeClone(),
            "default": self.subnode_default.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_iterator.finalize()
        del self.subnode_iterator
        self.subnode_default.finalize()
        del self.subnode_default

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_iterator.collectVariableAccesses(emit_read, emit_write)
        self.subnode_default.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinNext2Mixin = ChildrenHavingIteratorDefaultMixin


class ChildrenHavingKeyDictArgMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionDictOperationIn
    #   ExpressionDictOperationNotIn

    def __init__(
        self,
        key,
        dict_arg,
    ):
        key.parent = self

        self.subnode_key = key

        dict_arg.parent = self

        self.subnode_dict_arg = dict_arg

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_key,
            self.subnode_dict_arg,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("key", self.subnode_key),
            ("dict_arg", self.subnode_dict_arg),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_key
        if old_node is value:
            new_node.parent = self

            self.subnode_key = new_node

            return

        value = self.subnode_dict_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_dict_arg = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "key": self.subnode_key.makeClone(),
            "dict_arg": self.subnode_dict_arg.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_key.finalize()
        del self.subnode_key
        self.subnode_dict_arg.finalize()
        del self.subnode_dict_arg

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_key.collectVariableAccesses(emit_read, emit_write)
        self.subnode_dict_arg.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionDictOperationInMixin = ChildrenHavingKeyDictArgMixin
ChildrenExpressionDictOperationNotInMixin = ChildrenHavingKeyDictArgMixin


class ChildrenHavingKeyValueMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionKeyValuePairNew

    def __init__(
        self,
        key,
        value,
    ):
        key.parent = self

        self.subnode_key = key

        value.parent = self

        self.subnode_value = value

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_key,
            self.subnode_value,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("key", self.subnode_key),
            ("value", self.subnode_value),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_key
        if old_node is value:
            new_node.parent = self

            self.subnode_key = new_node

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
            "key": self.subnode_key.makeClone(),
            "value": self.subnode_value.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_key.finalize()
        del self.subnode_key
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

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_key.collectVariableAccesses(emit_read, emit_write)
        self.subnode_value.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionKeyValuePairNewMixin = ChildrenHavingKeyValueMixin


class ChildrenHavingKwDefaultsOptionalDefaultsTupleAnnotationsOptionalFunctionRefMixin(
    object
):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionFunctionCreationOld

    def __init__(
        self,
        kw_defaults,
        defaults,
        annotations,
        function_ref,
    ):
        if kw_defaults is not None:
            kw_defaults.parent = self

        self.subnode_kw_defaults = kw_defaults

        assert type(defaults) is tuple

        for val in defaults:
            val.parent = self

        self.subnode_defaults = defaults

        if annotations is not None:
            annotations.parent = self

        self.subnode_annotations = annotations

        function_ref.parent = self

        self.subnode_function_ref = function_ref

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        value = self.subnode_kw_defaults
        if value is None:
            pass
        else:
            result.append(value)
        result.extend(self.subnode_defaults)
        value = self.subnode_annotations
        if value is None:
            pass
        else:
            result.append(value)
        result.append(self.subnode_function_ref)
        return tuple(result)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("kw_defaults", self.subnode_kw_defaults),
            ("defaults", self.subnode_defaults),
            ("annotations", self.subnode_annotations),
            ("function_ref", self.subnode_function_ref),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_kw_defaults
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_kw_defaults = new_node

            return

        value = self.subnode_defaults
        if old_node in value:
            if new_node is not None:
                new_node.parent = self

                self.subnode_defaults = tuple(
                    (val if val is not old_node else new_node) for val in value
                )
            else:
                self.subnode_defaults = tuple(
                    val for val in value if val is not old_node
                )

            return

        value = self.subnode_annotations
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_annotations = new_node

            return

        value = self.subnode_function_ref
        if old_node is value:
            new_node.parent = self

            self.subnode_function_ref = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "kw_defaults": (
                self.subnode_kw_defaults.makeClone()
                if self.subnode_kw_defaults is not None
                else None
            ),
            "defaults": tuple(v.makeClone() for v in self.subnode_defaults),
            "annotations": (
                self.subnode_annotations.makeClone()
                if self.subnode_annotations is not None
                else None
            ),
            "function_ref": self.subnode_function_ref.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        if self.subnode_kw_defaults is not None:
            self.subnode_kw_defaults.finalize()
        del self.subnode_kw_defaults
        for c in self.subnode_defaults:
            c.finalize()
        del self.subnode_defaults
        if self.subnode_annotations is not None:
            self.subnode_annotations.finalize()
        del self.subnode_annotations
        self.subnode_function_ref.finalize()
        del self.subnode_function_ref

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        subnode_kw_defaults = self.subnode_kw_defaults

        if subnode_kw_defaults is not None:
            self.subnode_kw_defaults.collectVariableAccesses(emit_read, emit_write)
        for element in self.subnode_defaults:
            element.collectVariableAccesses(emit_read, emit_write)
        subnode_annotations = self.subnode_annotations

        if subnode_annotations is not None:
            self.subnode_annotations.collectVariableAccesses(emit_read, emit_write)
        self.subnode_function_ref.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionFunctionCreationOldMixin = (
    ChildrenHavingKwDefaultsOptionalDefaultsTupleAnnotationsOptionalFunctionRefMixin
)


class ChildrenHavingLeftRightMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionComparisonEq
    #   ExpressionComparisonExceptionMatch
    #   ExpressionComparisonExceptionMismatch
    #   ExpressionComparisonGt
    #   ExpressionComparisonGte
    #   ExpressionComparisonIn
    #   ExpressionComparisonIs
    #   ExpressionComparisonIsNot
    #   ExpressionComparisonLt
    #   ExpressionComparisonLte
    #   ExpressionComparisonNeq
    #   ExpressionComparisonNotIn
    #   ExpressionConditionalAnd
    #   ExpressionConditionalOr
    #   ExpressionOperationBinaryAdd
    #   ExpressionOperationBinaryBitAnd
    #   ExpressionOperationBinaryBitOr
    #   ExpressionOperationBinaryBitXor
    #   ExpressionOperationBinaryDivmod
    #   ExpressionOperationBinaryFloorDiv
    #   ExpressionOperationBinaryLshift
    #   ExpressionOperationBinaryMatMult
    #   ExpressionOperationBinaryMod
    #   ExpressionOperationBinaryMult
    #   ExpressionOperationBinaryPow
    #   ExpressionOperationBinaryRshift
    #   ExpressionOperationBinarySub
    #   ExpressionOperationBinaryTrueDiv
    #   ExpressionOperationInplaceAdd
    #   ExpressionOperationInplaceBitAnd
    #   ExpressionOperationInplaceBitOr
    #   ExpressionOperationInplaceBitXor
    #   ExpressionOperationInplaceFloorDiv
    #   ExpressionOperationInplaceLshift
    #   ExpressionOperationInplaceMatMult
    #   ExpressionOperationInplaceMod
    #   ExpressionOperationInplaceMult
    #   ExpressionOperationInplacePow
    #   ExpressionOperationInplaceRshift
    #   ExpressionOperationInplaceSub
    #   ExpressionOperationInplaceTrueDiv

    def __init__(
        self,
        left,
        right,
    ):
        left.parent = self

        self.subnode_left = left

        right.parent = self

        self.subnode_right = right

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

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_left.collectVariableAccesses(emit_read, emit_write)
        self.subnode_right.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionComparisonEqMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionComparisonExceptionMatchMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionComparisonExceptionMismatchMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionComparisonGtMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionComparisonGteMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionComparisonInMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionComparisonIsMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionComparisonIsNotMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionComparisonLtMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionComparisonLteMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionComparisonNeqMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionComparisonNotInMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionConditionalAndMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionConditionalOrMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationBinaryAddMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationBinaryBitAndMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationBinaryBitOrMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationBinaryBitXorMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationBinaryDivmodMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationBinaryFloorDivMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationBinaryLshiftMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationBinaryMatMultMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationBinaryModMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationBinaryMultMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationBinaryPowMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationBinaryRshiftMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationBinarySubMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationBinaryTrueDivMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationInplaceAddMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationInplaceBitAndMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationInplaceBitOrMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationInplaceBitXorMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationInplaceFloorDivMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationInplaceLshiftMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationInplaceMatMultMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationInplaceModMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationInplaceMultMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationInplacePowMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationInplaceRshiftMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationInplaceSubMixin = ChildrenHavingLeftRightMixin
ChildrenExpressionOperationInplaceTrueDivMixin = ChildrenHavingLeftRightMixin


class ChildHavingListArgMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionListOperationCopy
    #   ExpressionListOperationPop1
    #   ExpressionListOperationSort1

    def __init__(
        self,
        list_arg,
    ):
        list_arg.parent = self

        self.subnode_list_arg = list_arg

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_list_arg.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionListOperationCopyMixin = ChildHavingListArgMixin
ChildrenExpressionListOperationPop1Mixin = ChildHavingListArgMixin
ChildrenExpressionListOperationSort1Mixin = ChildHavingListArgMixin


class ChildrenHavingListArgIndexMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionListOperationPop2

    def __init__(
        self,
        list_arg,
        index,
    ):
        list_arg.parent = self

        self.subnode_list_arg = list_arg

        index.parent = self

        self.subnode_index = index

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_list_arg,
            self.subnode_index,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("list_arg", self.subnode_list_arg),
            ("index", self.subnode_index),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_list_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_list_arg = new_node

            return

        value = self.subnode_index
        if old_node is value:
            new_node.parent = self

            self.subnode_index = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "list_arg": self.subnode_list_arg.makeClone(),
            "index": self.subnode_index.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_list_arg.finalize()
        del self.subnode_list_arg
        self.subnode_index.finalize()
        del self.subnode_index

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_list_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_index.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionListOperationPop2Mixin = ChildrenHavingListArgIndexMixin


class ChildrenHavingListArgIndexItemMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionListOperationInsert

    def __init__(
        self,
        list_arg,
        index,
        item,
    ):
        list_arg.parent = self

        self.subnode_list_arg = list_arg

        index.parent = self

        self.subnode_index = index

        item.parent = self

        self.subnode_item = item

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_list_arg,
            self.subnode_index,
            self.subnode_item,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("list_arg", self.subnode_list_arg),
            ("index", self.subnode_index),
            ("item", self.subnode_item),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_list_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_list_arg = new_node

            return

        value = self.subnode_index
        if old_node is value:
            new_node.parent = self

            self.subnode_index = new_node

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
            "index": self.subnode_index.makeClone(),
            "item": self.subnode_item.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_list_arg.finalize()
        del self.subnode_list_arg
        self.subnode_index.finalize()
        del self.subnode_index
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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_list_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_index.collectVariableAccesses(emit_read, emit_write)
        self.subnode_item.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionListOperationInsertMixin = ChildrenHavingListArgIndexItemMixin


class ChildrenHavingListArgKeyMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionListOperationSort2

    def __init__(
        self,
        list_arg,
        key,
    ):
        list_arg.parent = self

        self.subnode_list_arg = list_arg

        key.parent = self

        self.subnode_key = key

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_list_arg,
            self.subnode_key,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("list_arg", self.subnode_list_arg),
            ("key", self.subnode_key),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_list_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_list_arg = new_node

            return

        value = self.subnode_key
        if old_node is value:
            new_node.parent = self

            self.subnode_key = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "list_arg": self.subnode_list_arg.makeClone(),
            "key": self.subnode_key.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_list_arg.finalize()
        del self.subnode_list_arg
        self.subnode_key.finalize()
        del self.subnode_key

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_list_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_key.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionListOperationSort2Mixin = ChildrenHavingListArgKeyMixin


class ChildrenHavingListArgKeyOptionalReverseMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionListOperationSort3

    def __init__(
        self,
        list_arg,
        key,
        reverse,
    ):
        list_arg.parent = self

        self.subnode_list_arg = list_arg

        if key is not None:
            key.parent = self

        self.subnode_key = key

        reverse.parent = self

        self.subnode_reverse = reverse

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_list_arg)
        value = self.subnode_key
        if value is None:
            pass
        else:
            result.append(value)
        result.append(self.subnode_reverse)
        return tuple(result)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("list_arg", self.subnode_list_arg),
            ("key", self.subnode_key),
            ("reverse", self.subnode_reverse),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_list_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_list_arg = new_node

            return

        value = self.subnode_key
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_key = new_node

            return

        value = self.subnode_reverse
        if old_node is value:
            new_node.parent = self

            self.subnode_reverse = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "list_arg": self.subnode_list_arg.makeClone(),
            "key": (
                self.subnode_key.makeClone() if self.subnode_key is not None else None
            ),
            "reverse": self.subnode_reverse.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_list_arg.finalize()
        del self.subnode_list_arg
        if self.subnode_key is not None:
            self.subnode_key.finalize()
        del self.subnode_key
        self.subnode_reverse.finalize()
        del self.subnode_reverse

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_list_arg.collectVariableAccesses(emit_read, emit_write)
        subnode_key = self.subnode_key

        if subnode_key is not None:
            self.subnode_key.collectVariableAccesses(emit_read, emit_write)
        self.subnode_reverse.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionListOperationSort3Mixin = ChildrenHavingListArgKeyOptionalReverseMixin


class ChildrenHavingListArgValueMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionListOperationExtend
    #   ExpressionListOperationExtendForUnpack
    #   ExpressionListOperationIndex2
    #   ExpressionListOperationRemove

    def __init__(
        self,
        list_arg,
        value,
    ):
        list_arg.parent = self

        self.subnode_list_arg = list_arg

        value.parent = self

        self.subnode_value = value

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

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_list_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_value.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionListOperationExtendMixin = ChildrenHavingListArgValueMixin
ChildrenExpressionListOperationExtendForUnpackMixin = ChildrenHavingListArgValueMixin
ChildrenExpressionListOperationIndex2Mixin = ChildrenHavingListArgValueMixin
ChildrenExpressionListOperationRemoveMixin = ChildrenHavingListArgValueMixin


class ChildrenHavingListArgValueStartMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionListOperationIndex3

    def __init__(
        self,
        list_arg,
        value,
        start,
    ):
        list_arg.parent = self

        self.subnode_list_arg = list_arg

        value.parent = self

        self.subnode_value = value

        start.parent = self

        self.subnode_start = start

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_list_arg,
            self.subnode_value,
            self.subnode_start,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("list_arg", self.subnode_list_arg),
            ("value", self.subnode_value),
            ("start", self.subnode_start),
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

        value = self.subnode_start
        if old_node is value:
            new_node.parent = self

            self.subnode_start = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "list_arg": self.subnode_list_arg.makeClone(),
            "value": self.subnode_value.makeClone(),
            "start": self.subnode_start.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_list_arg.finalize()
        del self.subnode_list_arg
        self.subnode_value.finalize()
        del self.subnode_value
        self.subnode_start.finalize()
        del self.subnode_start

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_list_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_value.collectVariableAccesses(emit_read, emit_write)
        self.subnode_start.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionListOperationIndex3Mixin = ChildrenHavingListArgValueStartMixin


class ChildrenHavingListArgValueStartStopMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionListOperationIndex4

    def __init__(
        self,
        list_arg,
        value,
        start,
        stop,
    ):
        list_arg.parent = self

        self.subnode_list_arg = list_arg

        value.parent = self

        self.subnode_value = value

        start.parent = self

        self.subnode_start = start

        stop.parent = self

        self.subnode_stop = stop

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_list_arg,
            self.subnode_value,
            self.subnode_start,
            self.subnode_stop,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("list_arg", self.subnode_list_arg),
            ("value", self.subnode_value),
            ("start", self.subnode_start),
            ("stop", self.subnode_stop),
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

        value = self.subnode_start
        if old_node is value:
            new_node.parent = self

            self.subnode_start = new_node

            return

        value = self.subnode_stop
        if old_node is value:
            new_node.parent = self

            self.subnode_stop = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "list_arg": self.subnode_list_arg.makeClone(),
            "value": self.subnode_value.makeClone(),
            "start": self.subnode_start.makeClone(),
            "stop": self.subnode_stop.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_list_arg.finalize()
        del self.subnode_list_arg
        self.subnode_value.finalize()
        del self.subnode_value
        self.subnode_start.finalize()
        del self.subnode_start
        self.subnode_stop.finalize()
        del self.subnode_stop

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_list_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_value.collectVariableAccesses(emit_read, emit_write)
        self.subnode_start.collectVariableAccesses(emit_read, emit_write)
        self.subnode_stop.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionListOperationIndex4Mixin = ChildrenHavingListArgValueStartStopMixin


class ChildHavingLowMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinRange1
    #   ExpressionBuiltinXrange1

    def __init__(
        self,
        low,
    ):
        low.parent = self

        self.subnode_low = low

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_low,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("low", self.subnode_low),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_low
        if old_node is value:
            new_node.parent = self

            self.subnode_low = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "low": self.subnode_low.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_low.finalize()
        del self.subnode_low

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_low)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_low.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinRange1Mixin = ChildHavingLowMixin
ChildrenExpressionBuiltinXrange1Mixin = ChildHavingLowMixin


class ChildrenHavingLowHighMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinRange2
    #   ExpressionBuiltinXrange2

    def __init__(
        self,
        low,
        high,
    ):
        low.parent = self

        self.subnode_low = low

        high.parent = self

        self.subnode_high = high

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_low,
            self.subnode_high,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("low", self.subnode_low),
            ("high", self.subnode_high),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_low
        if old_node is value:
            new_node.parent = self

            self.subnode_low = new_node

            return

        value = self.subnode_high
        if old_node is value:
            new_node.parent = self

            self.subnode_high = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "low": self.subnode_low.makeClone(),
            "high": self.subnode_high.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_low.finalize()
        del self.subnode_low
        self.subnode_high.finalize()
        del self.subnode_high

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_low.collectVariableAccesses(emit_read, emit_write)
        self.subnode_high.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinRange2Mixin = ChildrenHavingLowHighMixin
ChildrenExpressionBuiltinXrange2Mixin = ChildrenHavingLowHighMixin


class ChildrenHavingLowHighStepMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinRange3
    #   ExpressionBuiltinXrange3

    def __init__(
        self,
        low,
        high,
        step,
    ):
        low.parent = self

        self.subnode_low = low

        high.parent = self

        self.subnode_high = high

        step.parent = self

        self.subnode_step = step

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_low,
            self.subnode_high,
            self.subnode_step,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("low", self.subnode_low),
            ("high", self.subnode_high),
            ("step", self.subnode_step),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_low
        if old_node is value:
            new_node.parent = self

            self.subnode_low = new_node

            return

        value = self.subnode_high
        if old_node is value:
            new_node.parent = self

            self.subnode_high = new_node

            return

        value = self.subnode_step
        if old_node is value:
            new_node.parent = self

            self.subnode_step = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "low": self.subnode_low.makeClone(),
            "high": self.subnode_high.makeClone(),
            "step": self.subnode_step.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_low.finalize()
        del self.subnode_low
        self.subnode_high.finalize()
        del self.subnode_high
        self.subnode_step.finalize()
        del self.subnode_step

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_low.collectVariableAccesses(emit_read, emit_write)
        self.subnode_high.collectVariableAccesses(emit_read, emit_write)
        self.subnode_step.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinRange3Mixin = ChildrenHavingLowHighStepMixin
ChildrenExpressionBuiltinXrange3Mixin = ChildrenHavingLowHighStepMixin


class ChildrenHavingMetaclassBasesMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionSelectMetaclass

    def __init__(
        self,
        metaclass,
        bases,
    ):
        metaclass.parent = self

        self.subnode_metaclass = metaclass

        bases.parent = self

        self.subnode_bases = bases

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_metaclass,
            self.subnode_bases,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("metaclass", self.subnode_metaclass),
            ("bases", self.subnode_bases),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_metaclass
        if old_node is value:
            new_node.parent = self

            self.subnode_metaclass = new_node

            return

        value = self.subnode_bases
        if old_node is value:
            new_node.parent = self

            self.subnode_bases = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "metaclass": self.subnode_metaclass.makeClone(),
            "bases": self.subnode_bases.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_metaclass.finalize()
        del self.subnode_metaclass
        self.subnode_bases.finalize()
        del self.subnode_bases

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_metaclass.collectVariableAccesses(emit_read, emit_write)
        self.subnode_bases.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionSelectMetaclassMixin = ChildrenHavingMetaclassBasesMixin


class ChildHavingModuleMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionImportName

    def __init__(
        self,
        module,
    ):
        module.parent = self

        self.subnode_module = module

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_module,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("module", self.subnode_module),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_module
        if old_node is value:
            new_node.parent = self

            self.subnode_module = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "module": self.subnode_module.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_module.finalize()
        del self.subnode_module

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_module)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_module.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionImportNameMixin = ChildHavingModuleMixin


class ChildrenHavingNameGlobalsArgOptionalLocalsArgOptionalFromlistOptionalLevelOptionalMixin(
    object
):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinImport

    def __init__(
        self,
        name,
        globals_arg,
        locals_arg,
        fromlist,
        level,
    ):
        name.parent = self

        self.subnode_name = name

        if globals_arg is not None:
            globals_arg.parent = self

        self.subnode_globals_arg = globals_arg

        if locals_arg is not None:
            locals_arg.parent = self

        self.subnode_locals_arg = locals_arg

        if fromlist is not None:
            fromlist.parent = self

        self.subnode_fromlist = fromlist

        if level is not None:
            level.parent = self

        self.subnode_level = level

    def setChildName(self, value):
        value.parent = self

        self.subnode_name = value

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_name)
        value = self.subnode_globals_arg
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_locals_arg
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_fromlist
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_level
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
            ("name", self.subnode_name),
            ("globals_arg", self.subnode_globals_arg),
            ("locals_arg", self.subnode_locals_arg),
            ("fromlist", self.subnode_fromlist),
            ("level", self.subnode_level),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_name
        if old_node is value:
            new_node.parent = self

            self.subnode_name = new_node

            return

        value = self.subnode_globals_arg
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_globals_arg = new_node

            return

        value = self.subnode_locals_arg
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_locals_arg = new_node

            return

        value = self.subnode_fromlist
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_fromlist = new_node

            return

        value = self.subnode_level
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_level = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "name": self.subnode_name.makeClone(),
            "globals_arg": (
                self.subnode_globals_arg.makeClone()
                if self.subnode_globals_arg is not None
                else None
            ),
            "locals_arg": (
                self.subnode_locals_arg.makeClone()
                if self.subnode_locals_arg is not None
                else None
            ),
            "fromlist": (
                self.subnode_fromlist.makeClone()
                if self.subnode_fromlist is not None
                else None
            ),
            "level": (
                self.subnode_level.makeClone()
                if self.subnode_level is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_name.finalize()
        del self.subnode_name
        if self.subnode_globals_arg is not None:
            self.subnode_globals_arg.finalize()
        del self.subnode_globals_arg
        if self.subnode_locals_arg is not None:
            self.subnode_locals_arg.finalize()
        del self.subnode_locals_arg
        if self.subnode_fromlist is not None:
            self.subnode_fromlist.finalize()
        del self.subnode_fromlist
        if self.subnode_level is not None:
            self.subnode_level.finalize()
        del self.subnode_level

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_name.collectVariableAccesses(emit_read, emit_write)
        subnode_globals_arg = self.subnode_globals_arg

        if subnode_globals_arg is not None:
            self.subnode_globals_arg.collectVariableAccesses(emit_read, emit_write)
        subnode_locals_arg = self.subnode_locals_arg

        if subnode_locals_arg is not None:
            self.subnode_locals_arg.collectVariableAccesses(emit_read, emit_write)
        subnode_fromlist = self.subnode_fromlist

        if subnode_fromlist is not None:
            self.subnode_fromlist.collectVariableAccesses(emit_read, emit_write)
        subnode_level = self.subnode_level

        if subnode_level is not None:
            self.subnode_level.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinImportMixin = ChildrenHavingNameGlobalsArgOptionalLocalsArgOptionalFromlistOptionalLevelOptionalMixin


class ChildrenHavingNameModeOptionalHandleOptionalUseErrnoOptionalUseLastErrorOptionalMixin(
    object
):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionCtypesCdll

    def __init__(
        self,
        name,
        mode,
        handle,
        use_errno,
        use_last_error,
    ):
        name.parent = self

        self.subnode_name = name

        if mode is not None:
            mode.parent = self

        self.subnode_mode = mode

        if handle is not None:
            handle.parent = self

        self.subnode_handle = handle

        if use_errno is not None:
            use_errno.parent = self

        self.subnode_use_errno = use_errno

        if use_last_error is not None:
            use_last_error.parent = self

        self.subnode_use_last_error = use_last_error

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_name)
        value = self.subnode_mode
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_handle
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_use_errno
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_use_last_error
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
            ("name", self.subnode_name),
            ("mode", self.subnode_mode),
            ("handle", self.subnode_handle),
            ("use_errno", self.subnode_use_errno),
            ("use_last_error", self.subnode_use_last_error),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_name
        if old_node is value:
            new_node.parent = self

            self.subnode_name = new_node

            return

        value = self.subnode_mode
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_mode = new_node

            return

        value = self.subnode_handle
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_handle = new_node

            return

        value = self.subnode_use_errno
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_use_errno = new_node

            return

        value = self.subnode_use_last_error
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_use_last_error = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "name": self.subnode_name.makeClone(),
            "mode": (
                self.subnode_mode.makeClone() if self.subnode_mode is not None else None
            ),
            "handle": (
                self.subnode_handle.makeClone()
                if self.subnode_handle is not None
                else None
            ),
            "use_errno": (
                self.subnode_use_errno.makeClone()
                if self.subnode_use_errno is not None
                else None
            ),
            "use_last_error": (
                self.subnode_use_last_error.makeClone()
                if self.subnode_use_last_error is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_name.finalize()
        del self.subnode_name
        if self.subnode_mode is not None:
            self.subnode_mode.finalize()
        del self.subnode_mode
        if self.subnode_handle is not None:
            self.subnode_handle.finalize()
        del self.subnode_handle
        if self.subnode_use_errno is not None:
            self.subnode_use_errno.finalize()
        del self.subnode_use_errno
        if self.subnode_use_last_error is not None:
            self.subnode_use_last_error.finalize()
        del self.subnode_use_last_error

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_name.collectVariableAccesses(emit_read, emit_write)
        subnode_mode = self.subnode_mode

        if subnode_mode is not None:
            self.subnode_mode.collectVariableAccesses(emit_read, emit_write)
        subnode_handle = self.subnode_handle

        if subnode_handle is not None:
            self.subnode_handle.collectVariableAccesses(emit_read, emit_write)
        subnode_use_errno = self.subnode_use_errno

        if subnode_use_errno is not None:
            self.subnode_use_errno.collectVariableAccesses(emit_read, emit_write)
        subnode_use_last_error = self.subnode_use_last_error

        if subnode_use_last_error is not None:
            self.subnode_use_last_error.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionCtypesCdllMixin = ChildrenHavingNameModeOptionalHandleOptionalUseErrnoOptionalUseLastErrorOptionalMixin


class ChildrenHavingNameModeOptionalHandleOptionalUseErrnoOptionalUseLastErrorOptionalWinmodeOptionalMixin(
    object
):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionCtypesCdll

    def __init__(
        self,
        name,
        mode,
        handle,
        use_errno,
        use_last_error,
        winmode,
    ):
        name.parent = self

        self.subnode_name = name

        if mode is not None:
            mode.parent = self

        self.subnode_mode = mode

        if handle is not None:
            handle.parent = self

        self.subnode_handle = handle

        if use_errno is not None:
            use_errno.parent = self

        self.subnode_use_errno = use_errno

        if use_last_error is not None:
            use_last_error.parent = self

        self.subnode_use_last_error = use_last_error

        if winmode is not None:
            winmode.parent = self

        self.subnode_winmode = winmode

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_name)
        value = self.subnode_mode
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_handle
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_use_errno
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_use_last_error
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_winmode
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
            ("name", self.subnode_name),
            ("mode", self.subnode_mode),
            ("handle", self.subnode_handle),
            ("use_errno", self.subnode_use_errno),
            ("use_last_error", self.subnode_use_last_error),
            ("winmode", self.subnode_winmode),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_name
        if old_node is value:
            new_node.parent = self

            self.subnode_name = new_node

            return

        value = self.subnode_mode
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_mode = new_node

            return

        value = self.subnode_handle
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_handle = new_node

            return

        value = self.subnode_use_errno
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_use_errno = new_node

            return

        value = self.subnode_use_last_error
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_use_last_error = new_node

            return

        value = self.subnode_winmode
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_winmode = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "name": self.subnode_name.makeClone(),
            "mode": (
                self.subnode_mode.makeClone() if self.subnode_mode is not None else None
            ),
            "handle": (
                self.subnode_handle.makeClone()
                if self.subnode_handle is not None
                else None
            ),
            "use_errno": (
                self.subnode_use_errno.makeClone()
                if self.subnode_use_errno is not None
                else None
            ),
            "use_last_error": (
                self.subnode_use_last_error.makeClone()
                if self.subnode_use_last_error is not None
                else None
            ),
            "winmode": (
                self.subnode_winmode.makeClone()
                if self.subnode_winmode is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_name.finalize()
        del self.subnode_name
        if self.subnode_mode is not None:
            self.subnode_mode.finalize()
        del self.subnode_mode
        if self.subnode_handle is not None:
            self.subnode_handle.finalize()
        del self.subnode_handle
        if self.subnode_use_errno is not None:
            self.subnode_use_errno.finalize()
        del self.subnode_use_errno
        if self.subnode_use_last_error is not None:
            self.subnode_use_last_error.finalize()
        del self.subnode_use_last_error
        if self.subnode_winmode is not None:
            self.subnode_winmode.finalize()
        del self.subnode_winmode

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_name.collectVariableAccesses(emit_read, emit_write)
        subnode_mode = self.subnode_mode

        if subnode_mode is not None:
            self.subnode_mode.collectVariableAccesses(emit_read, emit_write)
        subnode_handle = self.subnode_handle

        if subnode_handle is not None:
            self.subnode_handle.collectVariableAccesses(emit_read, emit_write)
        subnode_use_errno = self.subnode_use_errno

        if subnode_use_errno is not None:
            self.subnode_use_errno.collectVariableAccesses(emit_read, emit_write)
        subnode_use_last_error = self.subnode_use_last_error

        if subnode_use_last_error is not None:
            self.subnode_use_last_error.collectVariableAccesses(emit_read, emit_write)
        subnode_winmode = self.subnode_winmode

        if subnode_winmode is not None:
            self.subnode_winmode.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionCtypesCdllMixin = ChildrenHavingNameModeOptionalHandleOptionalUseErrnoOptionalUseLastErrorOptionalWinmodeOptionalMixin


class ChildrenHavingNamePackageOptionalMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionImportlibImportModuleCall

    def __init__(
        self,
        name,
        package,
    ):
        name.parent = self

        self.subnode_name = name

        if package is not None:
            package.parent = self

        self.subnode_package = package

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_name)
        value = self.subnode_package
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
            ("name", self.subnode_name),
            ("package", self.subnode_package),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_name
        if old_node is value:
            new_node.parent = self

            self.subnode_name = new_node

            return

        value = self.subnode_package
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_package = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "name": self.subnode_name.makeClone(),
            "package": (
                self.subnode_package.makeClone()
                if self.subnode_package is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_name.finalize()
        del self.subnode_name
        if self.subnode_package is not None:
            self.subnode_package.finalize()
        del self.subnode_package

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_name.collectVariableAccesses(emit_read, emit_write)
        subnode_package = self.subnode_package

        if subnode_package is not None:
            self.subnode_package.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionImportlibImportModuleCallMixin = (
    ChildrenHavingNamePackageOptionalMixin
)


class ChildHavingOperandMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionOperationNot
    #   ExpressionOperationUnaryAbs
    #   ExpressionOperationUnaryAdd
    #   ExpressionOperationUnaryInvert
    #   ExpressionOperationUnaryRepr
    #   ExpressionOperationUnarySub

    def __init__(
        self,
        operand,
    ):
        operand.parent = self

        self.subnode_operand = operand

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_operand,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("operand", self.subnode_operand),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_operand
        if old_node is value:
            new_node.parent = self

            self.subnode_operand = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "operand": self.subnode_operand.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_operand.finalize()
        del self.subnode_operand

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_operand)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_operand.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionOperationNotMixin = ChildHavingOperandMixin
ChildrenExpressionOperationUnaryAbsMixin = ChildHavingOperandMixin
ChildrenExpressionOperationUnaryAddMixin = ChildHavingOperandMixin
ChildrenExpressionOperationUnaryInvertMixin = ChildHavingOperandMixin
ChildrenExpressionOperationUnaryReprMixin = ChildHavingOperandMixin
ChildrenExpressionOperationUnarySubMixin = ChildHavingOperandMixin


class ChildHavingPMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionOsPathBasename
    #   ExpressionOsPathDirname

    def __init__(
        self,
        p,
    ):
        p.parent = self

        self.subnode_p = p

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_p,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("p", self.subnode_p),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_p
        if old_node is value:
            new_node.parent = self

            self.subnode_p = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "p": self.subnode_p.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_p.finalize()
        del self.subnode_p

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_p)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_p.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionOsPathBasenameMixin = ChildHavingPMixin
ChildrenExpressionOsPathDirnameMixin = ChildHavingPMixin


class ChildHavingPackageMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionImportlibResourcesBackportFiles
    #   ExpressionImportlibResourcesBackportFilesCall
    #   ExpressionImportlibResourcesFiles
    #   ExpressionImportlibResourcesFilesCall

    def __init__(
        self,
        package,
    ):
        package.parent = self

        self.subnode_package = package

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_package,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("package", self.subnode_package),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_package
        if old_node is value:
            new_node.parent = self

            self.subnode_package = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "package": self.subnode_package.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_package.finalize()
        del self.subnode_package

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_package)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_package.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionImportlibResourcesBackportFilesMixin = ChildHavingPackageMixin
ChildrenExpressionImportlibResourcesBackportFilesCallMixin = ChildHavingPackageMixin
ChildrenExpressionImportlibResourcesFilesMixin = ChildHavingPackageMixin
ChildrenExpressionImportlibResourcesFilesCallMixin = ChildHavingPackageMixin


class ChildrenHavingPackageResourceMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionImportlibResourcesBackportReadBinary
    #   ExpressionImportlibResourcesBackportReadBinaryCall
    #   ExpressionImportlibResourcesReadBinary
    #   ExpressionImportlibResourcesReadBinaryCall
    #   ExpressionPkgutilGetData
    #   ExpressionPkgutilGetDataCall

    def __init__(
        self,
        package,
        resource,
    ):
        package.parent = self

        self.subnode_package = package

        resource.parent = self

        self.subnode_resource = resource

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_package,
            self.subnode_resource,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("package", self.subnode_package),
            ("resource", self.subnode_resource),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_package
        if old_node is value:
            new_node.parent = self

            self.subnode_package = new_node

            return

        value = self.subnode_resource
        if old_node is value:
            new_node.parent = self

            self.subnode_resource = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "package": self.subnode_package.makeClone(),
            "resource": self.subnode_resource.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_package.finalize()
        del self.subnode_package
        self.subnode_resource.finalize()
        del self.subnode_resource

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_package.collectVariableAccesses(emit_read, emit_write)
        self.subnode_resource.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionImportlibResourcesBackportReadBinaryMixin = (
    ChildrenHavingPackageResourceMixin
)
ChildrenExpressionImportlibResourcesBackportReadBinaryCallMixin = (
    ChildrenHavingPackageResourceMixin
)
ChildrenExpressionImportlibResourcesReadBinaryMixin = ChildrenHavingPackageResourceMixin
ChildrenExpressionImportlibResourcesReadBinaryCallMixin = (
    ChildrenHavingPackageResourceMixin
)
ChildrenExpressionPkgutilGetDataMixin = ChildrenHavingPackageResourceMixin
ChildrenExpressionPkgutilGetDataCallMixin = ChildrenHavingPackageResourceMixin


class ChildrenHavingPackageResourceEncodingOptionalErrorsOptionalMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionImportlibResourcesBackportReadText
    #   ExpressionImportlibResourcesBackportReadTextCall
    #   ExpressionImportlibResourcesReadText
    #   ExpressionImportlibResourcesReadTextCall

    def __init__(
        self,
        package,
        resource,
        encoding,
        errors,
    ):
        package.parent = self

        self.subnode_package = package

        resource.parent = self

        self.subnode_resource = resource

        if encoding is not None:
            encoding.parent = self

        self.subnode_encoding = encoding

        if errors is not None:
            errors.parent = self

        self.subnode_errors = errors

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_package)
        result.append(self.subnode_resource)
        value = self.subnode_encoding
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_errors
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
            ("package", self.subnode_package),
            ("resource", self.subnode_resource),
            ("encoding", self.subnode_encoding),
            ("errors", self.subnode_errors),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_package
        if old_node is value:
            new_node.parent = self

            self.subnode_package = new_node

            return

        value = self.subnode_resource
        if old_node is value:
            new_node.parent = self

            self.subnode_resource = new_node

            return

        value = self.subnode_encoding
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_encoding = new_node

            return

        value = self.subnode_errors
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_errors = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "package": self.subnode_package.makeClone(),
            "resource": self.subnode_resource.makeClone(),
            "encoding": (
                self.subnode_encoding.makeClone()
                if self.subnode_encoding is not None
                else None
            ),
            "errors": (
                self.subnode_errors.makeClone()
                if self.subnode_errors is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_package.finalize()
        del self.subnode_package
        self.subnode_resource.finalize()
        del self.subnode_resource
        if self.subnode_encoding is not None:
            self.subnode_encoding.finalize()
        del self.subnode_encoding
        if self.subnode_errors is not None:
            self.subnode_errors.finalize()
        del self.subnode_errors

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_package.collectVariableAccesses(emit_read, emit_write)
        self.subnode_resource.collectVariableAccesses(emit_read, emit_write)
        subnode_encoding = self.subnode_encoding

        if subnode_encoding is not None:
            self.subnode_encoding.collectVariableAccesses(emit_read, emit_write)
        subnode_errors = self.subnode_errors

        if subnode_errors is not None:
            self.subnode_errors.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionImportlibResourcesBackportReadTextMixin = (
    ChildrenHavingPackageResourceEncodingOptionalErrorsOptionalMixin
)
ChildrenExpressionImportlibResourcesBackportReadTextCallMixin = (
    ChildrenHavingPackageResourceEncodingOptionalErrorsOptionalMixin
)
ChildrenExpressionImportlibResourcesReadTextMixin = (
    ChildrenHavingPackageResourceEncodingOptionalErrorsOptionalMixin
)
ChildrenExpressionImportlibResourcesReadTextCallMixin = (
    ChildrenHavingPackageResourceEncodingOptionalErrorsOptionalMixin
)


class ChildrenHavingPackageOrRequirementResourceNameMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionPkgResourcesResourceStream
    #   ExpressionPkgResourcesResourceStreamCall
    #   ExpressionPkgResourcesResourceString
    #   ExpressionPkgResourcesResourceStringCall

    def __init__(
        self,
        package_or_requirement,
        resource_name,
    ):
        package_or_requirement.parent = self

        self.subnode_package_or_requirement = package_or_requirement

        resource_name.parent = self

        self.subnode_resource_name = resource_name

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_package_or_requirement,
            self.subnode_resource_name,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("package_or_requirement", self.subnode_package_or_requirement),
            ("resource_name", self.subnode_resource_name),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_package_or_requirement
        if old_node is value:
            new_node.parent = self

            self.subnode_package_or_requirement = new_node

            return

        value = self.subnode_resource_name
        if old_node is value:
            new_node.parent = self

            self.subnode_resource_name = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "package_or_requirement": self.subnode_package_or_requirement.makeClone(),
            "resource_name": self.subnode_resource_name.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_package_or_requirement.finalize()
        del self.subnode_package_or_requirement
        self.subnode_resource_name.finalize()
        del self.subnode_resource_name

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_package_or_requirement.collectVariableAccesses(
            emit_read, emit_write
        )
        self.subnode_resource_name.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionPkgResourcesResourceStreamMixin = (
    ChildrenHavingPackageOrRequirementResourceNameMixin
)
ChildrenExpressionPkgResourcesResourceStreamCallMixin = (
    ChildrenHavingPackageOrRequirementResourceNameMixin
)
ChildrenExpressionPkgResourcesResourceStringMixin = (
    ChildrenHavingPackageOrRequirementResourceNameMixin
)
ChildrenExpressionPkgResourcesResourceStringCallMixin = (
    ChildrenHavingPackageOrRequirementResourceNameMixin
)


class ChildHavingPairsTupleMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionMakeDict

    def __init__(
        self,
        pairs,
    ):
        assert type(pairs) is tuple

        for val in pairs:
            val.parent = self

        self.subnode_pairs = pairs

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

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        for element in self.subnode_pairs:
            element.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionMakeDictMixin = ChildHavingPairsTupleMixin


class ChildHavingParamsTupleMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionImportlibMetadataBackportEntryPoints
    #   ExpressionImportlibMetadataBackportEntryPointsCall
    #   ExpressionImportlibMetadataEntryPoints
    #   ExpressionImportlibMetadataEntryPointsSince310Call

    def __init__(
        self,
        params,
    ):
        assert type(params) is tuple

        for val in params:
            val.parent = self

        self.subnode_params = params

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return self.subnode_params

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("params", self.subnode_params),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_params
        if old_node in value:
            if new_node is not None:
                new_node.parent = self

                self.subnode_params = tuple(
                    (val if val is not old_node else new_node) for val in value
                )
            else:
                self.subnode_params = tuple(val for val in value if val is not old_node)

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "params": tuple(v.makeClone() for v in self.subnode_params),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        for c in self.subnode_params:
            c.finalize()
        del self.subnode_params

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expressions, as they are evaluated before
        # the actual operation.
        old_subnode_params = self.subnode_params

        for sub_expression in old_subnode_params:
            expression = trace_collection.onExpression(sub_expression)

            if expression.willRaiseAnyException():
                wrapped_expression = wrapExpressionWithSideEffects(
                    side_effects=self.subnode_params[
                        : old_subnode_params.index(sub_expression)
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

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        for element in self.subnode_params:
            element.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionImportlibMetadataBackportEntryPointsMixin = (
    ChildHavingParamsTupleMixin
)
ChildrenExpressionImportlibMetadataBackportEntryPointsCallMixin = (
    ChildHavingParamsTupleMixin
)
ChildrenExpressionImportlibMetadataEntryPointsMixin = ChildHavingParamsTupleMixin
ChildrenExpressionImportlibMetadataEntryPointsSince310CallMixin = (
    ChildHavingParamsTupleMixin
)


class ChildHavingPathMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionOsPathAbspath
    #   ExpressionOsPathExists
    #   ExpressionOsPathIsdir
    #   ExpressionOsPathIsfile
    #   ExpressionOsPathNormpath

    def __init__(
        self,
        path,
    ):
        path.parent = self

        self.subnode_path = path

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_path,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("path", self.subnode_path),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_path
        if old_node is value:
            new_node.parent = self

            self.subnode_path = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "path": self.subnode_path.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_path.finalize()
        del self.subnode_path

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_path)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_path.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionOsPathAbspathMixin = ChildHavingPathMixin
ChildrenExpressionOsPathExistsMixin = ChildHavingPathMixin
ChildrenExpressionOsPathIsdirMixin = ChildHavingPathMixin
ChildrenExpressionOsPathIsfileMixin = ChildHavingPathMixin
ChildrenExpressionOsPathNormpathMixin = ChildHavingPathMixin


class ChildHavingPathOptionalMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionOsListdir

    def __init__(
        self,
        path,
    ):
        if path is not None:
            path.parent = self

        self.subnode_path = path

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        value = self.subnode_path

        if value is None:
            return ()
        else:
            return (value,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("path", self.subnode_path),)

    def replaceChild(self, old_node, new_node):
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
            "path": (
                self.subnode_path.makeClone() if self.subnode_path is not None else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        if self.subnode_path is not None:
            self.subnode_path.finalize()
        del self.subnode_path

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = self.subnode_path

        if expression is not None:
            expression = trace_collection.onExpression(expression)

            if expression.willRaiseAnyException():
                return (
                    expression,
                    "new_raise",
                    lambda: "For '%s' the child expression '%s' will raise."
                    % (self.getChildNameNice(), expression.getChildNameNice()),
                )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        subnode_path = self.subnode_path

        if subnode_path is not None:
            self.subnode_path.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionOsListdirMixin = ChildHavingPathOptionalMixin


class ChildrenHavingPathOptionalDirFdOptionalMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionOsLstat

    def __init__(
        self,
        path,
        dir_fd,
    ):
        if path is not None:
            path.parent = self

        self.subnode_path = path

        if dir_fd is not None:
            dir_fd.parent = self

        self.subnode_dir_fd = dir_fd

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        value = self.subnode_path
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_dir_fd
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
            ("path", self.subnode_path),
            ("dir_fd", self.subnode_dir_fd),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_path
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_path = new_node

            return

        value = self.subnode_dir_fd
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_dir_fd = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "path": (
                self.subnode_path.makeClone() if self.subnode_path is not None else None
            ),
            "dir_fd": (
                self.subnode_dir_fd.makeClone()
                if self.subnode_dir_fd is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        if self.subnode_path is not None:
            self.subnode_path.finalize()
        del self.subnode_path
        if self.subnode_dir_fd is not None:
            self.subnode_dir_fd.finalize()
        del self.subnode_dir_fd

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        subnode_path = self.subnode_path

        if subnode_path is not None:
            self.subnode_path.collectVariableAccesses(emit_read, emit_write)
        subnode_dir_fd = self.subnode_dir_fd

        if subnode_dir_fd is not None:
            self.subnode_dir_fd.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionOsLstatMixin = ChildrenHavingPathOptionalDirFdOptionalMixin


class ChildrenHavingPathOptionalDirFdOptionalFollowSymlinksOptionalMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionOsStat

    def __init__(
        self,
        path,
        dir_fd,
        follow_symlinks,
    ):
        if path is not None:
            path.parent = self

        self.subnode_path = path

        if dir_fd is not None:
            dir_fd.parent = self

        self.subnode_dir_fd = dir_fd

        if follow_symlinks is not None:
            follow_symlinks.parent = self

        self.subnode_follow_symlinks = follow_symlinks

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        value = self.subnode_path
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_dir_fd
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_follow_symlinks
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
            ("path", self.subnode_path),
            ("dir_fd", self.subnode_dir_fd),
            ("follow_symlinks", self.subnode_follow_symlinks),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_path
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_path = new_node

            return

        value = self.subnode_dir_fd
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_dir_fd = new_node

            return

        value = self.subnode_follow_symlinks
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_follow_symlinks = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "path": (
                self.subnode_path.makeClone() if self.subnode_path is not None else None
            ),
            "dir_fd": (
                self.subnode_dir_fd.makeClone()
                if self.subnode_dir_fd is not None
                else None
            ),
            "follow_symlinks": (
                self.subnode_follow_symlinks.makeClone()
                if self.subnode_follow_symlinks is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        if self.subnode_path is not None:
            self.subnode_path.finalize()
        del self.subnode_path
        if self.subnode_dir_fd is not None:
            self.subnode_dir_fd.finalize()
        del self.subnode_dir_fd
        if self.subnode_follow_symlinks is not None:
            self.subnode_follow_symlinks.finalize()
        del self.subnode_follow_symlinks

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        subnode_path = self.subnode_path

        if subnode_path is not None:
            self.subnode_path.collectVariableAccesses(emit_read, emit_write)
        subnode_dir_fd = self.subnode_dir_fd

        if subnode_dir_fd is not None:
            self.subnode_dir_fd.collectVariableAccesses(emit_read, emit_write)
        subnode_follow_symlinks = self.subnode_follow_symlinks

        if subnode_follow_symlinks is not None:
            self.subnode_follow_symlinks.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionOsStatMixin = (
    ChildrenHavingPathOptionalDirFdOptionalFollowSymlinksOptionalMixin
)


class ChildrenHavingPosArgOptionalPairsTupleMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinDict

    def __init__(
        self,
        pos_arg,
        pairs,
    ):
        if pos_arg is not None:
            pos_arg.parent = self

        self.subnode_pos_arg = pos_arg

        assert type(pairs) is tuple

        for val in pairs:
            val.parent = self

        self.subnode_pairs = pairs

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        value = self.subnode_pos_arg
        if value is None:
            pass
        else:
            result.append(value)
        result.extend(self.subnode_pairs)
        return tuple(result)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("pos_arg", self.subnode_pos_arg),
            ("pairs", self.subnode_pairs),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_pos_arg
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_pos_arg = new_node

            return

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
            "pos_arg": (
                self.subnode_pos_arg.makeClone()
                if self.subnode_pos_arg is not None
                else None
            ),
            "pairs": tuple(v.makeClone() for v in self.subnode_pairs),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        if self.subnode_pos_arg is not None:
            self.subnode_pos_arg.finalize()
        del self.subnode_pos_arg
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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        subnode_pos_arg = self.subnode_pos_arg

        if subnode_pos_arg is not None:
            self.subnode_pos_arg.collectVariableAccesses(emit_read, emit_write)
        for element in self.subnode_pairs:
            element.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinDictMixin = ChildrenHavingPosArgOptionalPairsTupleMixin


class ChildrenHavingRealOptionalImagMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinComplex2

    def __init__(
        self,
        real,
        imag,
    ):
        if real is not None:
            real.parent = self

        self.subnode_real = real

        imag.parent = self

        self.subnode_imag = imag

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        value = self.subnode_real
        if value is None:
            pass
        else:
            result.append(value)
        result.append(self.subnode_imag)
        return tuple(result)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("real", self.subnode_real),
            ("imag", self.subnode_imag),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_real
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_real = new_node

            return

        value = self.subnode_imag
        if old_node is value:
            new_node.parent = self

            self.subnode_imag = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "real": (
                self.subnode_real.makeClone() if self.subnode_real is not None else None
            ),
            "imag": self.subnode_imag.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        if self.subnode_real is not None:
            self.subnode_real.finalize()
        del self.subnode_real
        self.subnode_imag.finalize()
        del self.subnode_imag

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        subnode_real = self.subnode_real

        if subnode_real is not None:
            self.subnode_real.collectVariableAccesses(emit_read, emit_write)
        self.subnode_imag.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinComplex2Mixin = ChildrenHavingRealOptionalImagMixin


class ChildHavingRequirementsTupleMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionPkgResourcesRequire
    #   ExpressionPkgResourcesRequireCall

    def __init__(
        self,
        requirements,
    ):
        assert type(requirements) is tuple

        for val in requirements:
            val.parent = self

        self.subnode_requirements = requirements

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return self.subnode_requirements

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("requirements", self.subnode_requirements),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_requirements
        if old_node in value:
            if new_node is not None:
                new_node.parent = self

                self.subnode_requirements = tuple(
                    (val if val is not old_node else new_node) for val in value
                )
            else:
                self.subnode_requirements = tuple(
                    val for val in value if val is not old_node
                )

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "requirements": tuple(v.makeClone() for v in self.subnode_requirements),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        for c in self.subnode_requirements:
            c.finalize()
        del self.subnode_requirements

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expressions, as they are evaluated before
        # the actual operation.
        old_subnode_requirements = self.subnode_requirements

        for sub_expression in old_subnode_requirements:
            expression = trace_collection.onExpression(sub_expression)

            if expression.willRaiseAnyException():
                wrapped_expression = wrapExpressionWithSideEffects(
                    side_effects=self.subnode_requirements[
                        : old_subnode_requirements.index(sub_expression)
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

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        for element in self.subnode_requirements:
            element.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionPkgResourcesRequireMixin = ChildHavingRequirementsTupleMixin
ChildrenExpressionPkgResourcesRequireCallMixin = ChildHavingRequirementsTupleMixin


class ChildHavingSMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionOsPathIsabs

    def __init__(
        self,
        s,
    ):
        s.parent = self

        self.subnode_s = s

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_s,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("s", self.subnode_s),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_s
        if old_node is value:
            new_node.parent = self

            self.subnode_s = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "s": self.subnode_s.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_s.finalize()
        del self.subnode_s

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_s)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_s.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionOsPathIsabsMixin = ChildHavingSMixin


class ChildHavingSequenceMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinSum1

    def __init__(
        self,
        sequence,
    ):
        sequence.parent = self

        self.subnode_sequence = sequence

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_sequence,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("sequence", self.subnode_sequence),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_sequence
        if old_node is value:
            new_node.parent = self

            self.subnode_sequence = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "sequence": self.subnode_sequence.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_sequence.finalize()
        del self.subnode_sequence

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_sequence)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_sequence.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinSum1Mixin = ChildHavingSequenceMixin


class ChildrenHavingSequenceStartMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinSum2

    def __init__(
        self,
        sequence,
        start,
    ):
        sequence.parent = self

        self.subnode_sequence = sequence

        start.parent = self

        self.subnode_start = start

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_sequence,
            self.subnode_start,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("sequence", self.subnode_sequence),
            ("start", self.subnode_start),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_sequence
        if old_node is value:
            new_node.parent = self

            self.subnode_sequence = new_node

            return

        value = self.subnode_start
        if old_node is value:
            new_node.parent = self

            self.subnode_start = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "sequence": self.subnode_sequence.makeClone(),
            "start": self.subnode_start.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_sequence.finalize()
        del self.subnode_sequence
        self.subnode_start.finalize()
        del self.subnode_start

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_sequence.collectVariableAccesses(emit_read, emit_write)
        self.subnode_start.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinSum2Mixin = ChildrenHavingSequenceStartMixin


class ChildrenHavingSetArgValueMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionSetOperationUpdate

    def __init__(
        self,
        set_arg,
        value,
    ):
        set_arg.parent = self

        self.subnode_set_arg = set_arg

        value.parent = self

        self.subnode_value = value

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_set_arg,
            self.subnode_value,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("set_arg", self.subnode_set_arg),
            ("value", self.subnode_value),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_set_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_set_arg = new_node

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
            "set_arg": self.subnode_set_arg.makeClone(),
            "value": self.subnode_value.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_set_arg.finalize()
        del self.subnode_set_arg
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

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_set_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_value.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionSetOperationUpdateMixin = ChildrenHavingSetArgValueMixin


class ChildrenHavingSideEffectsTupleExpressionMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionSideEffects

    def __init__(
        self,
        side_effects,
        expression,
    ):
        assert type(side_effects) is tuple

        for val in side_effects:
            val.parent = self

        self.subnode_side_effects = side_effects

        expression.parent = self

        self.subnode_expression = expression

    def setChildExpression(self, value):
        value.parent = self

        self.subnode_expression = value

    def setChildSideEffects(self, value):
        assert type(value) is tuple, type(value)

        for val in value:
            val.parent = self

        self.subnode_side_effects = value

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.extend(self.subnode_side_effects)
        result.append(self.subnode_expression)
        return tuple(result)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("side_effects", self.subnode_side_effects),
            ("expression", self.subnode_expression),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_side_effects
        if old_node in value:
            if new_node is not None:
                new_node.parent = self

                self.subnode_side_effects = tuple(
                    (val if val is not old_node else new_node) for val in value
                )
            else:
                self.subnode_side_effects = tuple(
                    val for val in value if val is not old_node
                )

            return

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
            "side_effects": tuple(v.makeClone() for v in self.subnode_side_effects),
            "expression": self.subnode_expression.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        for c in self.subnode_side_effects:
            c.finalize()
        del self.subnode_side_effects
        self.subnode_expression.finalize()
        del self.subnode_expression

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        for element in self.subnode_side_effects:
            element.collectVariableAccesses(emit_read, emit_write)
        self.subnode_expression.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionSideEffectsMixin = ChildrenHavingSideEffectsTupleExpressionMixin


class ChildHavingSourceMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinVars

    def __init__(
        self,
        source,
    ):
        source.parent = self

        self.subnode_source = source

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_source,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("source", self.subnode_source),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_source
        if old_node is value:
            new_node.parent = self

            self.subnode_source = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "source": self.subnode_source.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_source.finalize()
        del self.subnode_source

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_source)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_source.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinVarsMixin = ChildHavingSourceMixin


class ChildrenHavingSourceFilenameModeFlagsOptionalDontInheritOptionalOptimizeOptionalMixin(
    object
):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinCompile

    def __init__(
        self,
        source,
        filename,
        mode,
        flags,
        dont_inherit,
        optimize,
    ):
        source.parent = self

        self.subnode_source = source

        filename.parent = self

        self.subnode_filename = filename

        mode.parent = self

        self.subnode_mode = mode

        if flags is not None:
            flags.parent = self

        self.subnode_flags = flags

        if dont_inherit is not None:
            dont_inherit.parent = self

        self.subnode_dont_inherit = dont_inherit

        if optimize is not None:
            optimize.parent = self

        self.subnode_optimize = optimize

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_source)
        result.append(self.subnode_filename)
        result.append(self.subnode_mode)
        value = self.subnode_flags
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_dont_inherit
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_optimize
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
            ("source", self.subnode_source),
            ("filename", self.subnode_filename),
            ("mode", self.subnode_mode),
            ("flags", self.subnode_flags),
            ("dont_inherit", self.subnode_dont_inherit),
            ("optimize", self.subnode_optimize),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_source
        if old_node is value:
            new_node.parent = self

            self.subnode_source = new_node

            return

        value = self.subnode_filename
        if old_node is value:
            new_node.parent = self

            self.subnode_filename = new_node

            return

        value = self.subnode_mode
        if old_node is value:
            new_node.parent = self

            self.subnode_mode = new_node

            return

        value = self.subnode_flags
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_flags = new_node

            return

        value = self.subnode_dont_inherit
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_dont_inherit = new_node

            return

        value = self.subnode_optimize
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_optimize = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "source": self.subnode_source.makeClone(),
            "filename": self.subnode_filename.makeClone(),
            "mode": self.subnode_mode.makeClone(),
            "flags": (
                self.subnode_flags.makeClone()
                if self.subnode_flags is not None
                else None
            ),
            "dont_inherit": (
                self.subnode_dont_inherit.makeClone()
                if self.subnode_dont_inherit is not None
                else None
            ),
            "optimize": (
                self.subnode_optimize.makeClone()
                if self.subnode_optimize is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_source.finalize()
        del self.subnode_source
        self.subnode_filename.finalize()
        del self.subnode_filename
        self.subnode_mode.finalize()
        del self.subnode_mode
        if self.subnode_flags is not None:
            self.subnode_flags.finalize()
        del self.subnode_flags
        if self.subnode_dont_inherit is not None:
            self.subnode_dont_inherit.finalize()
        del self.subnode_dont_inherit
        if self.subnode_optimize is not None:
            self.subnode_optimize.finalize()
        del self.subnode_optimize

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_source.collectVariableAccesses(emit_read, emit_write)
        self.subnode_filename.collectVariableAccesses(emit_read, emit_write)
        self.subnode_mode.collectVariableAccesses(emit_read, emit_write)
        subnode_flags = self.subnode_flags

        if subnode_flags is not None:
            self.subnode_flags.collectVariableAccesses(emit_read, emit_write)
        subnode_dont_inherit = self.subnode_dont_inherit

        if subnode_dont_inherit is not None:
            self.subnode_dont_inherit.collectVariableAccesses(emit_read, emit_write)
        subnode_optimize = self.subnode_optimize

        if subnode_optimize is not None:
            self.subnode_optimize.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinCompileMixin = ChildrenHavingSourceFilenameModeFlagsOptionalDontInheritOptionalOptimizeOptionalMixin


class ChildrenHavingSourceCodeGlobalsArgLocalsArgMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinEval
    #   ExpressionBuiltinExecfile

    def __init__(
        self,
        source_code,
        globals_arg,
        locals_arg,
    ):
        source_code.parent = self

        self.subnode_source_code = source_code

        globals_arg.parent = self

        self.subnode_globals_arg = globals_arg

        locals_arg.parent = self

        self.subnode_locals_arg = locals_arg

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_source_code,
            self.subnode_globals_arg,
            self.subnode_locals_arg,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("source_code", self.subnode_source_code),
            ("globals_arg", self.subnode_globals_arg),
            ("locals_arg", self.subnode_locals_arg),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_source_code
        if old_node is value:
            new_node.parent = self

            self.subnode_source_code = new_node

            return

        value = self.subnode_globals_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_globals_arg = new_node

            return

        value = self.subnode_locals_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_locals_arg = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "source_code": self.subnode_source_code.makeClone(),
            "globals_arg": self.subnode_globals_arg.makeClone(),
            "locals_arg": self.subnode_locals_arg.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_source_code.finalize()
        del self.subnode_source_code
        self.subnode_globals_arg.finalize()
        del self.subnode_globals_arg
        self.subnode_locals_arg.finalize()
        del self.subnode_locals_arg

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_source_code.collectVariableAccesses(emit_read, emit_write)
        self.subnode_globals_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_locals_arg.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinEvalMixin = ChildrenHavingSourceCodeGlobalsArgLocalsArgMixin
ChildrenExpressionBuiltinExecfileMixin = (
    ChildrenHavingSourceCodeGlobalsArgLocalsArgMixin
)


class ChildrenHavingSourceCodeGlobalsArgLocalsArgClosureOptionalMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinExec

    def __init__(
        self,
        source_code,
        globals_arg,
        locals_arg,
        closure,
    ):
        source_code.parent = self

        self.subnode_source_code = source_code

        globals_arg.parent = self

        self.subnode_globals_arg = globals_arg

        locals_arg.parent = self

        self.subnode_locals_arg = locals_arg

        if closure is not None:
            closure.parent = self

        self.subnode_closure = closure

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_source_code)
        result.append(self.subnode_globals_arg)
        result.append(self.subnode_locals_arg)
        value = self.subnode_closure
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
            ("source_code", self.subnode_source_code),
            ("globals_arg", self.subnode_globals_arg),
            ("locals_arg", self.subnode_locals_arg),
            ("closure", self.subnode_closure),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_source_code
        if old_node is value:
            new_node.parent = self

            self.subnode_source_code = new_node

            return

        value = self.subnode_globals_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_globals_arg = new_node

            return

        value = self.subnode_locals_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_locals_arg = new_node

            return

        value = self.subnode_closure
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_closure = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "source_code": self.subnode_source_code.makeClone(),
            "globals_arg": self.subnode_globals_arg.makeClone(),
            "locals_arg": self.subnode_locals_arg.makeClone(),
            "closure": (
                self.subnode_closure.makeClone()
                if self.subnode_closure is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_source_code.finalize()
        del self.subnode_source_code
        self.subnode_globals_arg.finalize()
        del self.subnode_globals_arg
        self.subnode_locals_arg.finalize()
        del self.subnode_locals_arg
        if self.subnode_closure is not None:
            self.subnode_closure.finalize()
        del self.subnode_closure

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_source_code.collectVariableAccesses(emit_read, emit_write)
        self.subnode_globals_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_locals_arg.collectVariableAccesses(emit_read, emit_write)
        subnode_closure = self.subnode_closure

        if subnode_closure is not None:
            self.subnode_closure.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinExecMixin = (
    ChildrenHavingSourceCodeGlobalsArgLocalsArgClosureOptionalMixin
)


class ChildrenHavingStartStopMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinSlice2

    def __init__(
        self,
        start,
        stop,
    ):
        start.parent = self

        self.subnode_start = start

        stop.parent = self

        self.subnode_stop = stop

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_start,
            self.subnode_stop,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("start", self.subnode_start),
            ("stop", self.subnode_stop),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_start
        if old_node is value:
            new_node.parent = self

            self.subnode_start = new_node

            return

        value = self.subnode_stop
        if old_node is value:
            new_node.parent = self

            self.subnode_stop = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "start": self.subnode_start.makeClone(),
            "stop": self.subnode_stop.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_start.finalize()
        del self.subnode_start
        self.subnode_stop.finalize()
        del self.subnode_stop

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_start.collectVariableAccesses(emit_read, emit_write)
        self.subnode_stop.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinSlice2Mixin = ChildrenHavingStartStopMixin


class ChildrenHavingStartStopStepMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinSlice3

    def __init__(
        self,
        start,
        stop,
        step,
    ):
        start.parent = self

        self.subnode_start = start

        stop.parent = self

        self.subnode_stop = stop

        step.parent = self

        self.subnode_step = step

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_start,
            self.subnode_stop,
            self.subnode_step,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("start", self.subnode_start),
            ("stop", self.subnode_stop),
            ("step", self.subnode_step),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_start
        if old_node is value:
            new_node.parent = self

            self.subnode_start = new_node

            return

        value = self.subnode_stop
        if old_node is value:
            new_node.parent = self

            self.subnode_stop = new_node

            return

        value = self.subnode_step
        if old_node is value:
            new_node.parent = self

            self.subnode_step = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "start": self.subnode_start.makeClone(),
            "stop": self.subnode_stop.makeClone(),
            "step": self.subnode_step.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_start.finalize()
        del self.subnode_start
        self.subnode_stop.finalize()
        del self.subnode_stop
        self.subnode_step.finalize()
        del self.subnode_step

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_start.collectVariableAccesses(emit_read, emit_write)
        self.subnode_stop.collectVariableAccesses(emit_read, emit_write)
        self.subnode_step.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinSlice3Mixin = ChildrenHavingStartStopStepMixin


class ChildHavingStopMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinSlice1

    def __init__(
        self,
        stop,
    ):
        stop.parent = self

        self.subnode_stop = stop

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_stop,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("stop", self.subnode_stop),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_stop
        if old_node is value:
            new_node.parent = self

            self.subnode_stop = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "stop": self.subnode_stop.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_stop.finalize()
        del self.subnode_stop

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_stop)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_stop.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinSlice1Mixin = ChildHavingStopMixin


class ChildHavingStrArgMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationCapitalize
    #   ExpressionStrOperationCapitalizeBase
    #   ExpressionStrOperationCasefoldBase
    #   ExpressionStrOperationDecode1
    #   ExpressionStrOperationEncode1
    #   ExpressionStrOperationExpandtabs1
    #   ExpressionStrOperationFormatmapBase
    #   ExpressionStrOperationIsalnum
    #   ExpressionStrOperationIsalpha
    #   ExpressionStrOperationIsalphaBase
    #   ExpressionStrOperationIsasciiBase
    #   ExpressionStrOperationIsdecimalBase
    #   ExpressionStrOperationIsdigit
    #   ExpressionStrOperationIsidentifierBase
    #   ExpressionStrOperationIslower
    #   ExpressionStrOperationIsnumericBase
    #   ExpressionStrOperationIsprintableBase
    #   ExpressionStrOperationIsspace
    #   ExpressionStrOperationIsspaceBase
    #   ExpressionStrOperationIstitle
    #   ExpressionStrOperationIstitleBase
    #   ExpressionStrOperationIsupper
    #   ExpressionStrOperationLower
    #   ExpressionStrOperationLstrip1
    #   ExpressionStrOperationMaketransBase
    #   ExpressionStrOperationRsplit1
    #   ExpressionStrOperationRstrip1
    #   ExpressionStrOperationSplit1
    #   ExpressionStrOperationSplitlines1
    #   ExpressionStrOperationStrip1
    #   ExpressionStrOperationSwapcase
    #   ExpressionStrOperationSwapcaseBase
    #   ExpressionStrOperationTitle
    #   ExpressionStrOperationTitleBase
    #   ExpressionStrOperationUpper

    def __init__(
        self,
        str_arg,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_str_arg,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("str_arg", self.subnode_str_arg),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_str_arg)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationCapitalizeMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationCapitalizeBaseMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationCasefoldBaseMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationDecode1Mixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationEncode1Mixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationExpandtabs1Mixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationFormatmapBaseMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationIsalnumMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationIsalphaMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationIsalphaBaseMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationIsasciiBaseMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationIsdecimalBaseMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationIsdigitMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationIsidentifierBaseMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationIslowerMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationIsnumericBaseMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationIsprintableBaseMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationIsspaceMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationIsspaceBaseMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationIstitleMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationIstitleBaseMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationIsupperMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationLowerMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationLstrip1Mixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationMaketransBaseMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationRsplit1Mixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationRstrip1Mixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationSplit1Mixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationSplitlines1Mixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationStrip1Mixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationSwapcaseMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationSwapcaseBaseMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationTitleMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationTitleBaseMixin = ChildHavingStrArgMixin
ChildrenExpressionStrOperationUpperMixin = ChildHavingStrArgMixin


class ChildrenHavingStrArgArgsTuplePairsTupleMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationFormat

    def __init__(
        self,
        str_arg,
        args,
        pairs,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        assert type(args) is tuple

        for val in args:
            val.parent = self

        self.subnode_args = args

        assert type(pairs) is tuple

        for val in pairs:
            val.parent = self

        self.subnode_pairs = pairs

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_str_arg)
        result.extend(self.subnode_args)
        result.extend(self.subnode_pairs)
        return tuple(result)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("args", self.subnode_args),
            ("pairs", self.subnode_pairs),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

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
            "str_arg": self.subnode_str_arg.makeClone(),
            "args": tuple(v.makeClone() for v in self.subnode_args),
            "pairs": tuple(v.makeClone() for v in self.subnode_pairs),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        for c in self.subnode_args:
            c.finalize()
        del self.subnode_args
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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        for element in self.subnode_args:
            element.collectVariableAccesses(emit_read, emit_write)
        for element in self.subnode_pairs:
            element.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationFormatMixin = ChildrenHavingStrArgArgsTuplePairsTupleMixin


class ChildrenHavingStrArgCharsMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationLstrip2
    #   ExpressionStrOperationRstrip2
    #   ExpressionStrOperationStrip2

    def __init__(
        self,
        str_arg,
        chars,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        chars.parent = self

        self.subnode_chars = chars

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_chars,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("chars", self.subnode_chars),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_chars
        if old_node is value:
            new_node.parent = self

            self.subnode_chars = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "chars": self.subnode_chars.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_chars.finalize()
        del self.subnode_chars

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_chars.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationLstrip2Mixin = ChildrenHavingStrArgCharsMixin
ChildrenExpressionStrOperationRstrip2Mixin = ChildrenHavingStrArgCharsMixin
ChildrenExpressionStrOperationStrip2Mixin = ChildrenHavingStrArgCharsMixin


class ChildrenHavingStrArgEncodingMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationDecode2
    #   ExpressionStrOperationEncode2

    def __init__(
        self,
        str_arg,
        encoding,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        encoding.parent = self

        self.subnode_encoding = encoding

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_encoding,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("encoding", self.subnode_encoding),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_encoding
        if old_node is value:
            new_node.parent = self

            self.subnode_encoding = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "encoding": self.subnode_encoding.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_encoding.finalize()
        del self.subnode_encoding

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_encoding.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationDecode2Mixin = ChildrenHavingStrArgEncodingMixin
ChildrenExpressionStrOperationEncode2Mixin = ChildrenHavingStrArgEncodingMixin


class ChildrenHavingStrArgEncodingErrorsMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationDecode3
    #   ExpressionStrOperationEncode3

    def __init__(
        self,
        str_arg,
        encoding,
        errors,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        encoding.parent = self

        self.subnode_encoding = encoding

        errors.parent = self

        self.subnode_errors = errors

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_encoding,
            self.subnode_errors,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("encoding", self.subnode_encoding),
            ("errors", self.subnode_errors),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_encoding
        if old_node is value:
            new_node.parent = self

            self.subnode_encoding = new_node

            return

        value = self.subnode_errors
        if old_node is value:
            new_node.parent = self

            self.subnode_errors = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "encoding": self.subnode_encoding.makeClone(),
            "errors": self.subnode_errors.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_encoding.finalize()
        del self.subnode_encoding
        self.subnode_errors.finalize()
        del self.subnode_errors

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_encoding.collectVariableAccesses(emit_read, emit_write)
        self.subnode_errors.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationDecode3Mixin = ChildrenHavingStrArgEncodingErrorsMixin
ChildrenExpressionStrOperationEncode3Mixin = ChildrenHavingStrArgEncodingErrorsMixin


class ChildrenHavingStrArgIterableMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationJoin

    def __init__(
        self,
        str_arg,
        iterable,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        iterable.parent = self

        self.subnode_iterable = iterable

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_iterable,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("iterable", self.subnode_iterable),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_iterable
        if old_node is value:
            new_node.parent = self

            self.subnode_iterable = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "iterable": self.subnode_iterable.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_iterable.finalize()
        del self.subnode_iterable

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_iterable.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationJoinMixin = ChildrenHavingStrArgIterableMixin


class ChildrenHavingStrArgKeependsMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationSplitlines2

    def __init__(
        self,
        str_arg,
        keepends,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        keepends.parent = self

        self.subnode_keepends = keepends

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_keepends,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("keepends", self.subnode_keepends),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_keepends
        if old_node is value:
            new_node.parent = self

            self.subnode_keepends = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "keepends": self.subnode_keepends.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_keepends.finalize()
        del self.subnode_keepends

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_keepends.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationSplitlines2Mixin = ChildrenHavingStrArgKeependsMixin


class ChildrenHavingStrArgOldNewMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationReplace3

    def __init__(
        self,
        str_arg,
        old,
        new,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        old.parent = self

        self.subnode_old = old

        new.parent = self

        self.subnode_new = new

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_old,
            self.subnode_new,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("old", self.subnode_old),
            ("new", self.subnode_new),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_old
        if old_node is value:
            new_node.parent = self

            self.subnode_old = new_node

            return

        value = self.subnode_new
        if old_node is value:
            new_node.parent = self

            self.subnode_new = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "old": self.subnode_old.makeClone(),
            "new": self.subnode_new.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_old.finalize()
        del self.subnode_old
        self.subnode_new.finalize()
        del self.subnode_new

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_old.collectVariableAccesses(emit_read, emit_write)
        self.subnode_new.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationReplace3Mixin = ChildrenHavingStrArgOldNewMixin


class ChildrenHavingStrArgOldNewCountMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationReplace4

    def __init__(
        self,
        str_arg,
        old,
        new,
        count,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        old.parent = self

        self.subnode_old = old

        new.parent = self

        self.subnode_new = new

        count.parent = self

        self.subnode_count = count

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_old,
            self.subnode_new,
            self.subnode_count,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("old", self.subnode_old),
            ("new", self.subnode_new),
            ("count", self.subnode_count),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_old
        if old_node is value:
            new_node.parent = self

            self.subnode_old = new_node

            return

        value = self.subnode_new
        if old_node is value:
            new_node.parent = self

            self.subnode_new = new_node

            return

        value = self.subnode_count
        if old_node is value:
            new_node.parent = self

            self.subnode_count = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "old": self.subnode_old.makeClone(),
            "new": self.subnode_new.makeClone(),
            "count": self.subnode_count.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_old.finalize()
        del self.subnode_old
        self.subnode_new.finalize()
        del self.subnode_new
        self.subnode_count.finalize()
        del self.subnode_count

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_old.collectVariableAccesses(emit_read, emit_write)
        self.subnode_new.collectVariableAccesses(emit_read, emit_write)
        self.subnode_count.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationReplace4Mixin = ChildrenHavingStrArgOldNewCountMixin


class ChildrenHavingStrArgPrefixMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationStartswith2

    def __init__(
        self,
        str_arg,
        prefix,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        prefix.parent = self

        self.subnode_prefix = prefix

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_prefix,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("prefix", self.subnode_prefix),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_prefix
        if old_node is value:
            new_node.parent = self

            self.subnode_prefix = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "prefix": self.subnode_prefix.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_prefix.finalize()
        del self.subnode_prefix

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_prefix.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationStartswith2Mixin = ChildrenHavingStrArgPrefixMixin


class ChildrenHavingStrArgPrefixStartMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationStartswith3

    def __init__(
        self,
        str_arg,
        prefix,
        start,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        prefix.parent = self

        self.subnode_prefix = prefix

        start.parent = self

        self.subnode_start = start

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_prefix,
            self.subnode_start,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("prefix", self.subnode_prefix),
            ("start", self.subnode_start),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_prefix
        if old_node is value:
            new_node.parent = self

            self.subnode_prefix = new_node

            return

        value = self.subnode_start
        if old_node is value:
            new_node.parent = self

            self.subnode_start = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "prefix": self.subnode_prefix.makeClone(),
            "start": self.subnode_start.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_prefix.finalize()
        del self.subnode_prefix
        self.subnode_start.finalize()
        del self.subnode_start

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_prefix.collectVariableAccesses(emit_read, emit_write)
        self.subnode_start.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationStartswith3Mixin = ChildrenHavingStrArgPrefixStartMixin


class ChildrenHavingStrArgPrefixStartEndMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationStartswith4

    def __init__(
        self,
        str_arg,
        prefix,
        start,
        end,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        prefix.parent = self

        self.subnode_prefix = prefix

        start.parent = self

        self.subnode_start = start

        end.parent = self

        self.subnode_end = end

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_prefix,
            self.subnode_start,
            self.subnode_end,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("prefix", self.subnode_prefix),
            ("start", self.subnode_start),
            ("end", self.subnode_end),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_prefix
        if old_node is value:
            new_node.parent = self

            self.subnode_prefix = new_node

            return

        value = self.subnode_start
        if old_node is value:
            new_node.parent = self

            self.subnode_start = new_node

            return

        value = self.subnode_end
        if old_node is value:
            new_node.parent = self

            self.subnode_end = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "prefix": self.subnode_prefix.makeClone(),
            "start": self.subnode_start.makeClone(),
            "end": self.subnode_end.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_prefix.finalize()
        del self.subnode_prefix
        self.subnode_start.finalize()
        del self.subnode_start
        self.subnode_end.finalize()
        del self.subnode_end

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_prefix.collectVariableAccesses(emit_read, emit_write)
        self.subnode_start.collectVariableAccesses(emit_read, emit_write)
        self.subnode_end.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationStartswith4Mixin = ChildrenHavingStrArgPrefixStartEndMixin


class ChildrenHavingStrArgSepMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationPartition
    #   ExpressionStrOperationRpartition
    #   ExpressionStrOperationRsplit2
    #   ExpressionStrOperationSplit2

    def __init__(
        self,
        str_arg,
        sep,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        sep.parent = self

        self.subnode_sep = sep

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_sep,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("sep", self.subnode_sep),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_sep
        if old_node is value:
            new_node.parent = self

            self.subnode_sep = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "sep": self.subnode_sep.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_sep.finalize()
        del self.subnode_sep

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_sep.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationPartitionMixin = ChildrenHavingStrArgSepMixin
ChildrenExpressionStrOperationRpartitionMixin = ChildrenHavingStrArgSepMixin
ChildrenExpressionStrOperationRsplit2Mixin = ChildrenHavingStrArgSepMixin
ChildrenExpressionStrOperationSplit2Mixin = ChildrenHavingStrArgSepMixin


class ChildrenHavingStrArgSepMaxsplitMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationRsplit3
    #   ExpressionStrOperationSplit3

    def __init__(
        self,
        str_arg,
        sep,
        maxsplit,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        sep.parent = self

        self.subnode_sep = sep

        maxsplit.parent = self

        self.subnode_maxsplit = maxsplit

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_sep,
            self.subnode_maxsplit,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("sep", self.subnode_sep),
            ("maxsplit", self.subnode_maxsplit),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_sep
        if old_node is value:
            new_node.parent = self

            self.subnode_sep = new_node

            return

        value = self.subnode_maxsplit
        if old_node is value:
            new_node.parent = self

            self.subnode_maxsplit = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "sep": self.subnode_sep.makeClone(),
            "maxsplit": self.subnode_maxsplit.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_sep.finalize()
        del self.subnode_sep
        self.subnode_maxsplit.finalize()
        del self.subnode_maxsplit

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_sep.collectVariableAccesses(emit_read, emit_write)
        self.subnode_maxsplit.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationRsplit3Mixin = ChildrenHavingStrArgSepMaxsplitMixin
ChildrenExpressionStrOperationSplit3Mixin = ChildrenHavingStrArgSepMaxsplitMixin


class ChildrenHavingStrArgSubMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationCount2
    #   ExpressionStrOperationFind2
    #   ExpressionStrOperationIndex2
    #   ExpressionStrOperationRfind2
    #   ExpressionStrOperationRindex2

    def __init__(
        self,
        str_arg,
        sub,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        sub.parent = self

        self.subnode_sub = sub

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_sub,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("sub", self.subnode_sub),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_sub
        if old_node is value:
            new_node.parent = self

            self.subnode_sub = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "sub": self.subnode_sub.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_sub.finalize()
        del self.subnode_sub

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_sub.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationCount2Mixin = ChildrenHavingStrArgSubMixin
ChildrenExpressionStrOperationFind2Mixin = ChildrenHavingStrArgSubMixin
ChildrenExpressionStrOperationIndex2Mixin = ChildrenHavingStrArgSubMixin
ChildrenExpressionStrOperationRfind2Mixin = ChildrenHavingStrArgSubMixin
ChildrenExpressionStrOperationRindex2Mixin = ChildrenHavingStrArgSubMixin


class ChildrenHavingStrArgSubStartMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationCount3
    #   ExpressionStrOperationFind3
    #   ExpressionStrOperationIndex3
    #   ExpressionStrOperationRfind3
    #   ExpressionStrOperationRindex3

    def __init__(
        self,
        str_arg,
        sub,
        start,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        sub.parent = self

        self.subnode_sub = sub

        start.parent = self

        self.subnode_start = start

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_sub,
            self.subnode_start,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("sub", self.subnode_sub),
            ("start", self.subnode_start),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_sub
        if old_node is value:
            new_node.parent = self

            self.subnode_sub = new_node

            return

        value = self.subnode_start
        if old_node is value:
            new_node.parent = self

            self.subnode_start = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "sub": self.subnode_sub.makeClone(),
            "start": self.subnode_start.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_sub.finalize()
        del self.subnode_sub
        self.subnode_start.finalize()
        del self.subnode_start

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_sub.collectVariableAccesses(emit_read, emit_write)
        self.subnode_start.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationCount3Mixin = ChildrenHavingStrArgSubStartMixin
ChildrenExpressionStrOperationFind3Mixin = ChildrenHavingStrArgSubStartMixin
ChildrenExpressionStrOperationIndex3Mixin = ChildrenHavingStrArgSubStartMixin
ChildrenExpressionStrOperationRfind3Mixin = ChildrenHavingStrArgSubStartMixin
ChildrenExpressionStrOperationRindex3Mixin = ChildrenHavingStrArgSubStartMixin


class ChildrenHavingStrArgSubStartEndMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationCount4
    #   ExpressionStrOperationFind4
    #   ExpressionStrOperationIndex4
    #   ExpressionStrOperationRfind4
    #   ExpressionStrOperationRindex4

    def __init__(
        self,
        str_arg,
        sub,
        start,
        end,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        sub.parent = self

        self.subnode_sub = sub

        start.parent = self

        self.subnode_start = start

        end.parent = self

        self.subnode_end = end

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_sub,
            self.subnode_start,
            self.subnode_end,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("sub", self.subnode_sub),
            ("start", self.subnode_start),
            ("end", self.subnode_end),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_sub
        if old_node is value:
            new_node.parent = self

            self.subnode_sub = new_node

            return

        value = self.subnode_start
        if old_node is value:
            new_node.parent = self

            self.subnode_start = new_node

            return

        value = self.subnode_end
        if old_node is value:
            new_node.parent = self

            self.subnode_end = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "sub": self.subnode_sub.makeClone(),
            "start": self.subnode_start.makeClone(),
            "end": self.subnode_end.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_sub.finalize()
        del self.subnode_sub
        self.subnode_start.finalize()
        del self.subnode_start
        self.subnode_end.finalize()
        del self.subnode_end

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_sub.collectVariableAccesses(emit_read, emit_write)
        self.subnode_start.collectVariableAccesses(emit_read, emit_write)
        self.subnode_end.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationCount4Mixin = ChildrenHavingStrArgSubStartEndMixin
ChildrenExpressionStrOperationFind4Mixin = ChildrenHavingStrArgSubStartEndMixin
ChildrenExpressionStrOperationIndex4Mixin = ChildrenHavingStrArgSubStartEndMixin
ChildrenExpressionStrOperationRfind4Mixin = ChildrenHavingStrArgSubStartEndMixin
ChildrenExpressionStrOperationRindex4Mixin = ChildrenHavingStrArgSubStartEndMixin


class ChildrenHavingStrArgSuffixMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationEndswith2

    def __init__(
        self,
        str_arg,
        suffix,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        suffix.parent = self

        self.subnode_suffix = suffix

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_suffix,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("suffix", self.subnode_suffix),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_suffix
        if old_node is value:
            new_node.parent = self

            self.subnode_suffix = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "suffix": self.subnode_suffix.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_suffix.finalize()
        del self.subnode_suffix

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_suffix.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationEndswith2Mixin = ChildrenHavingStrArgSuffixMixin


class ChildrenHavingStrArgSuffixStartMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationEndswith3

    def __init__(
        self,
        str_arg,
        suffix,
        start,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        suffix.parent = self

        self.subnode_suffix = suffix

        start.parent = self

        self.subnode_start = start

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_suffix,
            self.subnode_start,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("suffix", self.subnode_suffix),
            ("start", self.subnode_start),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_suffix
        if old_node is value:
            new_node.parent = self

            self.subnode_suffix = new_node

            return

        value = self.subnode_start
        if old_node is value:
            new_node.parent = self

            self.subnode_start = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "suffix": self.subnode_suffix.makeClone(),
            "start": self.subnode_start.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_suffix.finalize()
        del self.subnode_suffix
        self.subnode_start.finalize()
        del self.subnode_start

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_suffix.collectVariableAccesses(emit_read, emit_write)
        self.subnode_start.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationEndswith3Mixin = ChildrenHavingStrArgSuffixStartMixin


class ChildrenHavingStrArgSuffixStartEndMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationEndswith4

    def __init__(
        self,
        str_arg,
        suffix,
        start,
        end,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        suffix.parent = self

        self.subnode_suffix = suffix

        start.parent = self

        self.subnode_start = start

        end.parent = self

        self.subnode_end = end

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_suffix,
            self.subnode_start,
            self.subnode_end,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("suffix", self.subnode_suffix),
            ("start", self.subnode_start),
            ("end", self.subnode_end),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_suffix
        if old_node is value:
            new_node.parent = self

            self.subnode_suffix = new_node

            return

        value = self.subnode_start
        if old_node is value:
            new_node.parent = self

            self.subnode_start = new_node

            return

        value = self.subnode_end
        if old_node is value:
            new_node.parent = self

            self.subnode_end = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "suffix": self.subnode_suffix.makeClone(),
            "start": self.subnode_start.makeClone(),
            "end": self.subnode_end.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_suffix.finalize()
        del self.subnode_suffix
        self.subnode_start.finalize()
        del self.subnode_start
        self.subnode_end.finalize()
        del self.subnode_end

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_suffix.collectVariableAccesses(emit_read, emit_write)
        self.subnode_start.collectVariableAccesses(emit_read, emit_write)
        self.subnode_end.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationEndswith4Mixin = ChildrenHavingStrArgSuffixStartEndMixin


class ChildrenHavingStrArgTableMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationTranslate
    #   ExpressionStrOperationTranslateBase

    def __init__(
        self,
        str_arg,
        table,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        table.parent = self

        self.subnode_table = table

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_table,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("table", self.subnode_table),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_table
        if old_node is value:
            new_node.parent = self

            self.subnode_table = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "table": self.subnode_table.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_table.finalize()
        del self.subnode_table

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_table.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationTranslateMixin = ChildrenHavingStrArgTableMixin
ChildrenExpressionStrOperationTranslateBaseMixin = ChildrenHavingStrArgTableMixin


class ChildrenHavingStrArgTabsizeMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationExpandtabs2

    def __init__(
        self,
        str_arg,
        tabsize,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        tabsize.parent = self

        self.subnode_tabsize = tabsize

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_tabsize,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("tabsize", self.subnode_tabsize),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_tabsize
        if old_node is value:
            new_node.parent = self

            self.subnode_tabsize = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "tabsize": self.subnode_tabsize.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_tabsize.finalize()
        del self.subnode_tabsize

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_tabsize.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationExpandtabs2Mixin = ChildrenHavingStrArgTabsizeMixin


class ChildrenHavingStrArgWidthMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationCenter2
    #   ExpressionStrOperationLjust2
    #   ExpressionStrOperationRjust2
    #   ExpressionStrOperationZfill

    def __init__(
        self,
        str_arg,
        width,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        width.parent = self

        self.subnode_width = width

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_width,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("width", self.subnode_width),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_width
        if old_node is value:
            new_node.parent = self

            self.subnode_width = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "width": self.subnode_width.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_width.finalize()
        del self.subnode_width

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_width.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationCenter2Mixin = ChildrenHavingStrArgWidthMixin
ChildrenExpressionStrOperationLjust2Mixin = ChildrenHavingStrArgWidthMixin
ChildrenExpressionStrOperationRjust2Mixin = ChildrenHavingStrArgWidthMixin
ChildrenExpressionStrOperationZfillMixin = ChildrenHavingStrArgWidthMixin


class ChildrenHavingStrArgWidthFillcharMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStrOperationCenter3
    #   ExpressionStrOperationLjust3
    #   ExpressionStrOperationRjust3

    def __init__(
        self,
        str_arg,
        width,
        fillchar,
    ):
        str_arg.parent = self

        self.subnode_str_arg = str_arg

        width.parent = self

        self.subnode_width = width

        fillchar.parent = self

        self.subnode_fillchar = fillchar

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_str_arg,
            self.subnode_width,
            self.subnode_fillchar,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("str_arg", self.subnode_str_arg),
            ("width", self.subnode_width),
            ("fillchar", self.subnode_fillchar),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_str_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_str_arg = new_node

            return

        value = self.subnode_width
        if old_node is value:
            new_node.parent = self

            self.subnode_width = new_node

            return

        value = self.subnode_fillchar
        if old_node is value:
            new_node.parent = self

            self.subnode_fillchar = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "str_arg": self.subnode_str_arg.makeClone(),
            "width": self.subnode_width.makeClone(),
            "fillchar": self.subnode_fillchar.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_str_arg.finalize()
        del self.subnode_str_arg
        self.subnode_width.finalize()
        del self.subnode_width
        self.subnode_fillchar.finalize()
        del self.subnode_fillchar

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_str_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_width.collectVariableAccesses(emit_read, emit_write)
        self.subnode_fillchar.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStrOperationCenter3Mixin = ChildrenHavingStrArgWidthFillcharMixin
ChildrenExpressionStrOperationLjust3Mixin = ChildrenHavingStrArgWidthFillcharMixin
ChildrenExpressionStrOperationRjust3Mixin = ChildrenHavingStrArgWidthFillcharMixin


class ChildrenHavingStringEncodingOptionalErrorsOptionalMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinBytearray3

    def __init__(
        self,
        string,
        encoding,
        errors,
    ):
        string.parent = self

        self.subnode_string = string

        if encoding is not None:
            encoding.parent = self

        self.subnode_encoding = encoding

        if errors is not None:
            errors.parent = self

        self.subnode_errors = errors

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_string)
        value = self.subnode_encoding
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_errors
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
            ("string", self.subnode_string),
            ("encoding", self.subnode_encoding),
            ("errors", self.subnode_errors),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_string
        if old_node is value:
            new_node.parent = self

            self.subnode_string = new_node

            return

        value = self.subnode_encoding
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_encoding = new_node

            return

        value = self.subnode_errors
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_errors = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "string": self.subnode_string.makeClone(),
            "encoding": (
                self.subnode_encoding.makeClone()
                if self.subnode_encoding is not None
                else None
            ),
            "errors": (
                self.subnode_errors.makeClone()
                if self.subnode_errors is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_string.finalize()
        del self.subnode_string
        if self.subnode_encoding is not None:
            self.subnode_encoding.finalize()
        del self.subnode_encoding
        if self.subnode_errors is not None:
            self.subnode_errors.finalize()
        del self.subnode_errors

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_string.collectVariableAccesses(emit_read, emit_write)
        subnode_encoding = self.subnode_encoding

        if subnode_encoding is not None:
            self.subnode_encoding.collectVariableAccesses(emit_read, emit_write)
        subnode_errors = self.subnode_errors

        if subnode_errors is not None:
            self.subnode_errors.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinBytearray3Mixin = (
    ChildrenHavingStringEncodingOptionalErrorsOptionalMixin
)


class ChildHavingTypeArgMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinSuper1

    def __init__(
        self,
        type_arg,
    ):
        type_arg.parent = self

        self.subnode_type_arg = type_arg

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_type_arg,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("type_arg", self.subnode_type_arg),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_type_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_type_arg = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "type_arg": self.subnode_type_arg.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_type_arg.finalize()
        del self.subnode_type_arg

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_type_arg)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_type_arg.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinSuper1Mixin = ChildHavingTypeArgMixin


class ChildrenHavingTypeArgArgsOptionalKwargsOptionalMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionTypeOperationPrepare

    def __init__(
        self,
        type_arg,
        args,
        kwargs,
    ):
        type_arg.parent = self

        self.subnode_type_arg = type_arg

        if args is not None:
            args.parent = self

        self.subnode_args = args

        if kwargs is not None:
            kwargs.parent = self

        self.subnode_kwargs = kwargs

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_type_arg)
        value = self.subnode_args
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_kwargs
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
            ("type_arg", self.subnode_type_arg),
            ("args", self.subnode_args),
            ("kwargs", self.subnode_kwargs),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_type_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_type_arg = new_node

            return

        value = self.subnode_args
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_args = new_node

            return

        value = self.subnode_kwargs
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_kwargs = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "type_arg": self.subnode_type_arg.makeClone(),
            "args": (
                self.subnode_args.makeClone() if self.subnode_args is not None else None
            ),
            "kwargs": (
                self.subnode_kwargs.makeClone()
                if self.subnode_kwargs is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_type_arg.finalize()
        del self.subnode_type_arg
        if self.subnode_args is not None:
            self.subnode_args.finalize()
        del self.subnode_args
        if self.subnode_kwargs is not None:
            self.subnode_kwargs.finalize()
        del self.subnode_kwargs

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_type_arg.collectVariableAccesses(emit_read, emit_write)
        subnode_args = self.subnode_args

        if subnode_args is not None:
            self.subnode_args.collectVariableAccesses(emit_read, emit_write)
        subnode_kwargs = self.subnode_kwargs

        if subnode_kwargs is not None:
            self.subnode_kwargs.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionTypeOperationPrepareMixin = (
    ChildrenHavingTypeArgArgsOptionalKwargsOptionalMixin
)


class ChildrenHavingTypeArgObjectArgMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinSuper0
    #   ExpressionBuiltinSuper2

    def __init__(
        self,
        type_arg,
        object_arg,
    ):
        type_arg.parent = self

        self.subnode_type_arg = type_arg

        object_arg.parent = self

        self.subnode_object_arg = object_arg

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_type_arg,
            self.subnode_object_arg,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("type_arg", self.subnode_type_arg),
            ("object_arg", self.subnode_object_arg),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_type_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_type_arg = new_node

            return

        value = self.subnode_object_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_object_arg = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "type_arg": self.subnode_type_arg.makeClone(),
            "object_arg": self.subnode_object_arg.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_type_arg.finalize()
        del self.subnode_type_arg
        self.subnode_object_arg.finalize()
        del self.subnode_object_arg

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_type_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_object_arg.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinSuper0Mixin = ChildrenHavingTypeArgObjectArgMixin
ChildrenExpressionBuiltinSuper2Mixin = ChildrenHavingTypeArgObjectArgMixin


class ChildrenHavingTypeNameBasesDictArgMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinType3

    def __init__(
        self,
        type_name,
        bases,
        dict_arg,
    ):
        type_name.parent = self

        self.subnode_type_name = type_name

        bases.parent = self

        self.subnode_bases = bases

        dict_arg.parent = self

        self.subnode_dict_arg = dict_arg

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_type_name,
            self.subnode_bases,
            self.subnode_dict_arg,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("type_name", self.subnode_type_name),
            ("bases", self.subnode_bases),
            ("dict_arg", self.subnode_dict_arg),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_type_name
        if old_node is value:
            new_node.parent = self

            self.subnode_type_name = new_node

            return

        value = self.subnode_bases
        if old_node is value:
            new_node.parent = self

            self.subnode_bases = new_node

            return

        value = self.subnode_dict_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_dict_arg = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "type_name": self.subnode_type_name.makeClone(),
            "bases": self.subnode_bases.makeClone(),
            "dict_arg": self.subnode_dict_arg.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_type_name.finalize()
        del self.subnode_type_name
        self.subnode_bases.finalize()
        del self.subnode_bases
        self.subnode_dict_arg.finalize()
        del self.subnode_dict_arg

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_type_name.collectVariableAccesses(emit_read, emit_write)
        self.subnode_bases.collectVariableAccesses(emit_read, emit_write)
        self.subnode_dict_arg.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinType3Mixin = ChildrenHavingTypeNameBasesDictArgMixin


class ChildHavingTypeParamsMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionTypeMakeGeneric

    def __init__(
        self,
        type_params,
    ):
        type_params.parent = self

        self.subnode_type_params = type_params

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_type_params,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("type_params", self.subnode_type_params),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_type_params
        if old_node is value:
            new_node.parent = self

            self.subnode_type_params = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "type_params": self.subnode_type_params.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_type_params.finalize()
        del self.subnode_type_params

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = trace_collection.onExpression(self.subnode_type_params)

        if expression.willRaiseAnyException():
            return (
                expression,
                "new_raise",
                lambda: "For '%s' the child expression '%s' will raise."
                % (self.getChildNameNice(), expression.getChildNameNice()),
            )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_type_params.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionTypeMakeGenericMixin = ChildHavingTypeParamsMixin


class ChildrenHavingTypeParamsTupleComputeValueMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionTypeAlias

    def __init__(
        self,
        type_params,
        compute_value,
    ):
        assert type(type_params) is tuple

        for val in type_params:
            val.parent = self

        self.subnode_type_params = type_params

        compute_value.parent = self

        self.subnode_compute_value = compute_value

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.extend(self.subnode_type_params)
        result.append(self.subnode_compute_value)
        return tuple(result)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("type_params", self.subnode_type_params),
            ("compute_value", self.subnode_compute_value),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_type_params
        if old_node in value:
            if new_node is not None:
                new_node.parent = self

                self.subnode_type_params = tuple(
                    (val if val is not old_node else new_node) for val in value
                )
            else:
                self.subnode_type_params = tuple(
                    val for val in value if val is not old_node
                )

            return

        value = self.subnode_compute_value
        if old_node is value:
            new_node.parent = self

            self.subnode_compute_value = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "type_params": tuple(v.makeClone() for v in self.subnode_type_params),
            "compute_value": self.subnode_compute_value.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        for c in self.subnode_type_params:
            c.finalize()
        del self.subnode_type_params
        self.subnode_compute_value.finalize()
        del self.subnode_compute_value

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        for element in self.subnode_type_params:
            element.collectVariableAccesses(emit_read, emit_write)
        self.subnode_compute_value.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionTypeAliasMixin = ChildrenHavingTypeParamsTupleComputeValueMixin


class ChildHavingValueMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionAsyncIter
    #   ExpressionAsyncNext
    #   ExpressionBuiltinAll
    #   ExpressionBuiltinAny
    #   ExpressionBuiltinAscii
    #   ExpressionBuiltinBin
    #   ExpressionBuiltinBool
    #   ExpressionBuiltinBytearray1
    #   ExpressionBuiltinBytes1
    #   ExpressionBuiltinChr
    #   ExpressionBuiltinComplex1
    #   ExpressionBuiltinDir1
    #   ExpressionBuiltinFloat
    #   ExpressionBuiltinFrozenset
    #   ExpressionBuiltinHash
    #   ExpressionBuiltinHex
    #   ExpressionBuiltinId
    #   ExpressionBuiltinInt1
    #   ExpressionBuiltinIter1
    #   ExpressionBuiltinIterForUnpack
    #   ExpressionBuiltinLen
    #   ExpressionBuiltinList
    #   ExpressionBuiltinLong1
    #   ExpressionBuiltinNext1
    #   ExpressionBuiltinOct
    #   ExpressionBuiltinOrd
    #   ExpressionBuiltinSet
    #   ExpressionBuiltinStrP2
    #   ExpressionBuiltinTuple
    #   ExpressionBuiltinType1
    #   ExpressionFunctionErrorStr
    #   ExpressionKeyValuePairConstantKey
    #   ExpressionMatchTypeCheckMapping
    #   ExpressionMatchTypeCheckSequence
    #   ExpressionSpecialUnpack

    def __init__(
        self,
        value,
    ):
        value.parent = self

        self.subnode_value = value

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

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_value.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionAsyncIterMixin = ChildHavingValueMixin
ChildrenExpressionAsyncNextMixin = ChildHavingValueMixin
ChildrenExpressionBuiltinAllMixin = ChildHavingValueMixin
ChildrenExpressionBuiltinAnyMixin = ChildHavingValueMixin
ChildrenExpressionBuiltinAsciiMixin = ChildHavingValueMixin
ChildrenExpressionBuiltinBinMixin = ChildHavingValueMixin
ChildrenExpressionBuiltinBoolMixin = ChildHavingValueMixin
ChildrenExpressionBuiltinBytearray1Mixin = ChildHavingValueMixin
ChildrenExpressionBuiltinBytes1Mixin = ChildHavingValueMixin
ChildrenExpressionBuiltinChrMixin = ChildHavingValueMixin
ChildrenExpressionBuiltinComplex1Mixin = ChildHavingValueMixin
ChildrenExpressionBuiltinDir1Mixin = ChildHavingValueMixin
ChildrenExpressionBuiltinFloatMixin = ChildHavingValueMixin
ChildrenExpressionBuiltinFrozensetMixin = ChildHavingValueMixin
ChildrenExpressionBuiltinHashMixin = ChildHavingValueMixin
ChildrenExpressionBuiltinHexMixin = ChildHavingValueMixin
ChildrenExpressionBuiltinIdMixin = ChildHavingValueMixin
ChildrenExpressionBuiltinInt1Mixin = ChildHavingValueMixin
ChildrenExpressionBuiltinIter1Mixin = ChildHavingValueMixin
ChildrenExpressionBuiltinIterForUnpackMixin = ChildHavingValueMixin
ChildrenExpressionBuiltinLenMixin = ChildHavingValueMixin
ChildrenExpressionBuiltinListMixin = ChildHavingValueMixin
ChildrenExpressionBuiltinLong1Mixin = ChildHavingValueMixin
ChildrenExpressionBuiltinNext1Mixin = ChildHavingValueMixin
ChildrenExpressionBuiltinOctMixin = ChildHavingValueMixin
ChildrenExpressionBuiltinOrdMixin = ChildHavingValueMixin
ChildrenExpressionBuiltinSetMixin = ChildHavingValueMixin
ChildrenExpressionBuiltinStrP2Mixin = ChildHavingValueMixin
ChildrenExpressionBuiltinTupleMixin = ChildHavingValueMixin
ChildrenExpressionBuiltinType1Mixin = ChildHavingValueMixin
ChildrenExpressionFunctionErrorStrMixin = ChildHavingValueMixin
ChildrenExpressionKeyValuePairConstantKeyMixin = ChildHavingValueMixin
ChildrenExpressionMatchTypeCheckMappingMixin = ChildHavingValueMixin
ChildrenExpressionMatchTypeCheckSequenceMixin = ChildHavingValueMixin
ChildrenExpressionSpecialUnpackMixin = ChildHavingValueMixin


class ChildrenHavingValueOptionalBaseMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinInt2
    #   ExpressionBuiltinLong2

    def __init__(
        self,
        value,
        base,
    ):
        if value is not None:
            value.parent = self

        self.subnode_value = value

        base.parent = self

        self.subnode_base = base

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        value = self.subnode_value
        if value is None:
            pass
        else:
            result.append(value)
        result.append(self.subnode_base)
        return tuple(result)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("value", self.subnode_value),
            ("base", self.subnode_base),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_value
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_value = new_node

            return

        value = self.subnode_base
        if old_node is value:
            new_node.parent = self

            self.subnode_base = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "value": (
                self.subnode_value.makeClone()
                if self.subnode_value is not None
                else None
            ),
            "base": self.subnode_base.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        if self.subnode_value is not None:
            self.subnode_value.finalize()
        del self.subnode_value
        self.subnode_base.finalize()
        del self.subnode_base

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        subnode_value = self.subnode_value

        if subnode_value is not None:
            self.subnode_value.collectVariableAccesses(emit_read, emit_write)
        self.subnode_base.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinInt2Mixin = ChildrenHavingValueOptionalBaseMixin
ChildrenExpressionBuiltinLong2Mixin = ChildrenHavingValueOptionalBaseMixin


class ChildrenHavingValueOptionalEncodingOptionalErrorsOptionalMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinBytes3
    #   ExpressionBuiltinStrP3
    #   ExpressionBuiltinUnicodeP2

    def __init__(
        self,
        value,
        encoding,
        errors,
    ):
        if value is not None:
            value.parent = self

        self.subnode_value = value

        if encoding is not None:
            encoding.parent = self

        self.subnode_encoding = encoding

        if errors is not None:
            errors.parent = self

        self.subnode_errors = errors

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        value = self.subnode_value
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_encoding
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_errors
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
            ("value", self.subnode_value),
            ("encoding", self.subnode_encoding),
            ("errors", self.subnode_errors),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_value
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_value = new_node

            return

        value = self.subnode_encoding
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_encoding = new_node

            return

        value = self.subnode_errors
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_errors = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "value": (
                self.subnode_value.makeClone()
                if self.subnode_value is not None
                else None
            ),
            "encoding": (
                self.subnode_encoding.makeClone()
                if self.subnode_encoding is not None
                else None
            ),
            "errors": (
                self.subnode_errors.makeClone()
                if self.subnode_errors is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        if self.subnode_value is not None:
            self.subnode_value.finalize()
        del self.subnode_value
        if self.subnode_encoding is not None:
            self.subnode_encoding.finalize()
        del self.subnode_encoding
        if self.subnode_errors is not None:
            self.subnode_errors.finalize()
        del self.subnode_errors

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        subnode_value = self.subnode_value

        if subnode_value is not None:
            self.subnode_value.collectVariableAccesses(emit_read, emit_write)
        subnode_encoding = self.subnode_encoding

        if subnode_encoding is not None:
            self.subnode_encoding.collectVariableAccesses(emit_read, emit_write)
        subnode_errors = self.subnode_errors

        if subnode_errors is not None:
            self.subnode_errors.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinBytes3Mixin = (
    ChildrenHavingValueOptionalEncodingOptionalErrorsOptionalMixin
)
ChildrenExpressionBuiltinStrP3Mixin = (
    ChildrenHavingValueOptionalEncodingOptionalErrorsOptionalMixin
)
ChildrenExpressionBuiltinUnicodeP2Mixin = (
    ChildrenHavingValueOptionalEncodingOptionalErrorsOptionalMixin
)


class ChildrenHavingValueFormatSpecOptionalAutoNoneEmptyStrMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionBuiltinFormat

    def __init__(
        self,
        value,
        format_spec,
    ):
        value.parent = self

        self.subnode_value = value

        format_spec = convertEmptyStrConstantToNone(format_spec)
        if format_spec is not None:
            format_spec.parent = self

        self.subnode_format_spec = format_spec

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_value)
        value = self.subnode_format_spec
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
            ("value", self.subnode_value),
            ("format_spec", self.subnode_format_spec),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_value
        if old_node is value:
            new_node.parent = self

            self.subnode_value = new_node

            return

        value = self.subnode_format_spec
        if old_node is value:
            new_node = convertEmptyStrConstantToNone(new_node)
            if new_node is not None:
                new_node.parent = self

            self.subnode_format_spec = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "value": self.subnode_value.makeClone(),
            "format_spec": (
                self.subnode_format_spec.makeClone()
                if self.subnode_format_spec is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_value.finalize()
        del self.subnode_value
        if self.subnode_format_spec is not None:
            self.subnode_format_spec.finalize()
        del self.subnode_format_spec

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_value.collectVariableAccesses(emit_read, emit_write)
        subnode_format_spec = self.subnode_format_spec

        if subnode_format_spec is not None:
            self.subnode_format_spec.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionBuiltinFormatMixin = (
    ChildrenHavingValueFormatSpecOptionalAutoNoneEmptyStrMixin
)


class ChildrenHavingValueKeyMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionKeyValuePairOld

    def __init__(
        self,
        value,
        key,
    ):
        value.parent = self

        self.subnode_value = value

        key.parent = self

        self.subnode_key = key

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_value,
            self.subnode_key,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("value", self.subnode_value),
            ("key", self.subnode_key),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_value
        if old_node is value:
            new_node.parent = self

            self.subnode_value = new_node

            return

        value = self.subnode_key
        if old_node is value:
            new_node.parent = self

            self.subnode_key = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "value": self.subnode_value.makeClone(),
            "key": self.subnode_key.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_value.finalize()
        del self.subnode_value
        self.subnode_key.finalize()
        del self.subnode_key

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_value.collectVariableAccesses(emit_read, emit_write)
        self.subnode_key.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionKeyValuePairOldMixin = ChildrenHavingValueKeyMixin


class ChildHavingValuesTupleMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   ExpressionStringConcatenation

    def __init__(
        self,
        values,
    ):
        assert type(values) is tuple

        for val in values:
            val.parent = self

        self.subnode_values = values

    def setChildValues(self, value):
        assert type(value) is tuple, type(value)

        for val in value:
            val.parent = self

        self.subnode_values = value

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return self.subnode_values

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("values", self.subnode_values),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_values
        if old_node in value:
            if new_node is not None:
                new_node.parent = self

                self.subnode_values = tuple(
                    (val if val is not old_node else new_node) for val in value
                )
            else:
                self.subnode_values = tuple(val for val in value if val is not old_node)

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "values": tuple(v.makeClone() for v in self.subnode_values),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        for c in self.subnode_values:
            c.finalize()
        del self.subnode_values

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expressions, as they are evaluated before
        # the actual operation.
        old_subnode_values = self.subnode_values

        for sub_expression in old_subnode_values:
            expression = trace_collection.onExpression(sub_expression)

            if expression.willRaiseAnyException():
                wrapped_expression = wrapExpressionWithSideEffects(
                    side_effects=self.subnode_values[
                        : old_subnode_values.index(sub_expression)
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

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        for element in self.subnode_values:
            element.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
ChildrenExpressionStringConcatenationMixin = ChildHavingValuesTupleMixin

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
