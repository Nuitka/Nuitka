# pylint: disable=I0021,too-many-lines
# pylint: disable=I0021,line-too-long

"""Children having mixins

WARNING, this code is GENERATED. Modify the template ChildrenHavingMixin.py.j2 instead!

spell-checker: ignore capitalize casefold center clear copy count decode encode endswith expandtabs find format formatmap get haskey hex index isalnum isalpha isascii isdecimal isdigit isidentifier islower isnumeric isprintable isspace istitle isupper items iteritems iterkeys itervalues join keys ljust lower lstrip maketrans partition pop popitem replace rfind rindex rjust rpartition rsplit rstrip setdefault split splitlines startswith strip swapcase title translate update upper values viewitems viewkeys viewvalues zfill
spell-checker: ignore args chars count default encoding end errors fillchar iterable keepends key maxsplit new old pairs prefix sep start sub suffix table tabsize width
"""


# Loop unrolling over child names, pylint: disable=too-many-branches
from .NodeBases import NodeBase
from .NodeMakingHelpers import wrapExpressionWithSideEffects


def convertNoneConstantToNone(node):
    if node is None or node.isExpressionConstantNoneRef():
        return None
    else:
        return node


class ChildrenHavingArgsTupleMixin(object):
    # Mixins are not allow to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    named_children = ("args",)

    checkers = {}

    def __init__(
        self,
        args,
    ):
        assert type(args) is tuple

        for val in args:
            assert val is not None
            val.parent = self

        self.subnode_args = args

    def setChild(self, name, value):
        """Set a child value.

        Do not overload, provider self.checkers instead.
        """
        # Lists as inputs are OK, but turn them into tuples on the fly.
        if type(value) is list:
            value = tuple(value)

        # Re-parent value to us.
        if type(value) is tuple:
            for val in value:
                val.parent = self
        elif value is not None:
            value.parent = self

        # Determine old value, and inform it about losing its parent.
        attr_name = "subnode_" + name
        old_value = getattr(self, attr_name)
        assert old_value is not value, value

        setattr(self, attr_name, value)

    def clearChild(self, name):
        # Only accept legal child names
        assert name in ("args",), name

        # Determine old value, and check it has no parent anymore.
        old_value = self.subnode_args
        assert old_value is not None
        assert old_value.parent is None
        self.subnode_args = None

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return self.subnode_args

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("args", self.subnode_args),)

    def replaceChild(self, old_node, new_node):
        if new_node is not None and not isinstance(new_node, NodeBase):
            raise AssertionError(
                "Cannot replace with", new_node, "old", old_node, "in", self
            )
        value = self.subnode_args
        if old_node not in value:
            raise AssertionError("Didn't find child", old_node, "in", self)

        if new_node is not None:
            new_value = tuple(
                (val if val is not old_node else new_node) for val in value
            )
        else:
            new_value = tuple(val for val in value if val is not old_node)

        new_node.parent = self

        self.subnode_args = new_value

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        value = self.subnode_args

        values = {"args": tuple(v.makeClone() for v in value)}
        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        for c in self.subnode_args:
            c.finalize()

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expressions, as they are evaluated before
        # the actual operation.
        for count, sub_expression in enumerate(self.subnode_args):
            expression = trace_collection.onExpression(sub_expression)

            if expression.willRaiseException(BaseException):
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


class ChildrenHavingDistMixin(object):
    # Mixins are not allow to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    named_children = ("dist",)

    checkers = {}

    def __init__(
        self,
        dist,
    ):
        assert type(dist) is not tuple

        if dist is not None:
            dist.parent = self

        self.subnode_dist = dist

    def setChild(self, name, value):
        """Set a child value.

        Do not overload, provider self.checkers instead.
        """
        # Lists as inputs are OK, but turn them into tuples on the fly.
        if type(value) is list:
            value = tuple(value)

        # Re-parent value to us.
        if type(value) is tuple:
            for val in value:
                val.parent = self
        elif value is not None:
            value.parent = self

        # Determine old value, and inform it about losing its parent.
        attr_name = "subnode_" + name
        old_value = getattr(self, attr_name)
        assert old_value is not value, value

        setattr(self, attr_name, value)

    def clearChild(self, name):
        # Only accept legal child names
        assert name in ("dist",), name

        # Determine old value, and check it has no parent anymore.
        old_value = self.subnode_dist
        assert old_value is not None
        assert old_value.parent is None
        self.subnode_dist = None

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        value = self.subnode_dist

        if value is None:
            return ()
        else:
            return (value,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("dist", self.subnode_dist),)

    def replaceChild(self, old_node, new_node):
        if new_node is not None and not isinstance(new_node, NodeBase):
            raise AssertionError(
                "Cannot replace with", new_node, "old", old_node, "in", self
            )
        value = self.subnode_dist
        # Find the replaced node, as an added difficulty, what might be
        # happening, is that the old node is an element of a tuple, in which we
        # may also remove that element, by setting it to None.

        if old_node is value:
            new_node.parent = self
            self.subnode_dist = new_node
        else:
            raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        value = self.subnode_dist

        values = {"dist": value.makeClone()}
        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_dist.finalize()

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = self.subnode_dist

        if expression is not None:
            expression = trace_collection.onExpression(expression)

            if expression.willRaiseException(BaseException):
                return (
                    expression,
                    "new_raise",
                    lambda: "For '%s' the child expression '%s' will raise."
                    % (self.getChildNameNice(), expression.getChildNameNice()),
                )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)


class ChildrenHavingDistributionNameMixin(object):
    # Mixins are not allow to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    named_children = ("distribution_name",)

    checkers = {}

    def __init__(
        self,
        distribution_name,
    ):
        assert type(distribution_name) is not tuple

        if distribution_name is not None:
            distribution_name.parent = self

        self.subnode_distribution_name = distribution_name

    def setChild(self, name, value):
        """Set a child value.

        Do not overload, provider self.checkers instead.
        """
        # Lists as inputs are OK, but turn them into tuples on the fly.
        if type(value) is list:
            value = tuple(value)

        # Re-parent value to us.
        if type(value) is tuple:
            for val in value:
                val.parent = self
        elif value is not None:
            value.parent = self

        # Determine old value, and inform it about losing its parent.
        attr_name = "subnode_" + name
        old_value = getattr(self, attr_name)
        assert old_value is not value, value

        setattr(self, attr_name, value)

    def clearChild(self, name):
        # Only accept legal child names
        assert name in ("distribution_name",), name

        # Determine old value, and check it has no parent anymore.
        old_value = self.subnode_distribution_name
        assert old_value is not None
        assert old_value.parent is None
        self.subnode_distribution_name = None

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        value = self.subnode_distribution_name

        if value is None:
            return ()
        else:
            return (value,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("distribution_name", self.subnode_distribution_name),)

    def replaceChild(self, old_node, new_node):
        if new_node is not None and not isinstance(new_node, NodeBase):
            raise AssertionError(
                "Cannot replace with", new_node, "old", old_node, "in", self
            )
        value = self.subnode_distribution_name
        # Find the replaced node, as an added difficulty, what might be
        # happening, is that the old node is an element of a tuple, in which we
        # may also remove that element, by setting it to None.

        if old_node is value:
            new_node.parent = self
            self.subnode_distribution_name = new_node
        else:
            raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        value = self.subnode_distribution_name

        values = {"distribution_name": value.makeClone()}
        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_distribution_name.finalize()

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expression, as they it's evaluated before.
        expression = self.subnode_distribution_name

        if expression is not None:
            expression = trace_collection.onExpression(expression)

            if expression.willRaiseException(BaseException):
                return (
                    expression,
                    "new_raise",
                    lambda: "For '%s' the child expression '%s' will raise."
                    % (self.getChildNameNice(), expression.getChildNameNice()),
                )

        # Then ask ourselves to work on it.
        return self.computeExpression(trace_collection)


class ChildrenHavingElementsTupleMixin(object):
    # Mixins are not allow to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    named_children = ("elements",)

    checkers = {}

    def __init__(
        self,
        elements,
    ):
        assert type(elements) is tuple

        for val in elements:
            assert val is not None
            val.parent = self

        self.subnode_elements = elements

    def setChild(self, name, value):
        """Set a child value.

        Do not overload, provider self.checkers instead.
        """
        # Lists as inputs are OK, but turn them into tuples on the fly.
        if type(value) is list:
            value = tuple(value)

        # Re-parent value to us.
        if type(value) is tuple:
            for val in value:
                val.parent = self
        elif value is not None:
            value.parent = self

        # Determine old value, and inform it about losing its parent.
        attr_name = "subnode_" + name
        old_value = getattr(self, attr_name)
        assert old_value is not value, value

        setattr(self, attr_name, value)

    def clearChild(self, name):
        # Only accept legal child names
        assert name in ("elements",), name

        # Determine old value, and check it has no parent anymore.
        old_value = self.subnode_elements
        assert old_value is not None
        assert old_value.parent is None
        self.subnode_elements = None

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return self.subnode_elements

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("elements", self.subnode_elements),)

    def replaceChild(self, old_node, new_node):
        if new_node is not None and not isinstance(new_node, NodeBase):
            raise AssertionError(
                "Cannot replace with", new_node, "old", old_node, "in", self
            )
        value = self.subnode_elements
        if old_node not in value:
            raise AssertionError("Didn't find child", old_node, "in", self)

        if new_node is not None:
            new_value = tuple(
                (val if val is not old_node else new_node) for val in value
            )
        else:
            new_value = tuple(val for val in value if val is not old_node)

        new_node.parent = self

        self.subnode_elements = new_value

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        value = self.subnode_elements

        values = {"elements": tuple(v.makeClone() for v in value)}
        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        for c in self.subnode_elements:
            c.finalize()

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expressions, as they are evaluated before
        # the actual operation.
        for count, sub_expression in enumerate(self.subnode_elements):
            expression = trace_collection.onExpression(sub_expression)

            if expression.willRaiseException(BaseException):
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


class ChildrenHavingExpressionLowerUpperMixin(object):
    # Mixins are not allow to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    named_children = ("expression", "lower", "upper")

    checkers = {
        "lower": convertNoneConstantToNone,
        "upper": convertNoneConstantToNone,
    }

    def __init__(
        self,
        expression,
        lower,
        upper,
    ):
        if expression is not None:
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

    def setChild(self, name, value):
        """Set a child value.

        Do not overload, provider self.checkers instead.
        """
        # Lists as inputs are OK, but turn them into tuples on the fly.
        if type(value) is list:
            value = tuple(value)

        if name in self.checkers:
            value = self.checkers[name](value)

        # Re-parent value to us.
        if type(value) is tuple:
            for val in value:
                val.parent = self
        elif value is not None:
            value.parent = self

        # Determine old value, and inform it about losing its parent.
        attr_name = "subnode_" + name
        old_value = getattr(self, attr_name)
        assert old_value is not value, value

        setattr(self, attr_name, value)

    def clearChild(self, name):
        # Only accept legal child names
        assert name in ("expression", "lower", "upper"), name

        if name in self.checkers:
            self.checkers[name](None)

        # Determine old value, and check it has no parent anymore.
        attr_name = "subnode_" + name
        # Determine old value, and inform it about losing its parent.
        old_value = getattr(self, attr_name)
        assert old_value is not None
        assert old_value.parent is None

        setattr(self, attr_name, None)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []

        value = self.subnode_expression

        if value is None:
            pass
        elif type(value) is tuple:
            result.extend(value)
        else:
            assert isinstance(value, NodeBase), (
                "has illegal child",
                "expression",
                value,
                value.__class__,
            )
            result.append(value)

        value = self.subnode_lower

        if value is None:
            pass
        elif type(value) is tuple:
            result.extend(value)
        else:
            assert isinstance(value, NodeBase), (
                "has illegal child",
                "lower",
                value,
                value.__class__,
            )
            result.append(value)

        value = self.subnode_upper

        if value is None:
            pass
        elif type(value) is tuple:
            result.extend(value)
        else:
            assert isinstance(value, NodeBase), (
                "has illegal child",
                "upper",
                value,
                value.__class__,
            )
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
        if new_node is not None and not isinstance(new_node, NodeBase):
            raise AssertionError(
                "Cannot replace with", new_node, "old", old_node, "in", self
            )
        # Find the replaced node, as an added difficulty, what might be
        # happening, is that the old node is an element of a tuple, in which we
        # may also remove that element, by setting it to None.
        value = self.subnode_expression

        if value is None:
            pass
        elif type(value) is tuple:
            if old_node in value:
                if new_node is not None:
                    self.subnode_expression = tuple(
                        (val if val is not old_node else new_node) for val in value
                    )
                else:
                    self.subnode_expression = tuple(
                        val for val in value if val is not old_node
                    )

                return "expression"
        else:
            assert isinstance(value, NodeBase), (
                "has illegal child",
                "expression",
                value,
                value.__class__,
            )

            if old_node is value:
                self.setChild("expression", new_node)

                return "expression"

        value = self.subnode_lower

        if value is None:
            pass
        elif type(value) is tuple:
            if old_node in value:
                if new_node is not None:
                    self.subnode_lower = tuple(
                        (val if val is not old_node else new_node) for val in value
                    )
                else:
                    self.subnode_lower = tuple(
                        val for val in value if val is not old_node
                    )

                return "lower"
        else:
            assert isinstance(value, NodeBase), (
                "has illegal child",
                "lower",
                value,
                value.__class__,
            )

            if old_node is value:
                self.setChild("lower", new_node)

                return "lower"

        value = self.subnode_upper

        if value is None:
            pass
        elif type(value) is tuple:
            if old_node in value:
                if new_node is not None:
                    self.subnode_upper = tuple(
                        (val if val is not old_node else new_node) for val in value
                    )
                else:
                    self.subnode_upper = tuple(
                        val for val in value if val is not old_node
                    )

                return "upper"
        else:
            assert isinstance(value, NodeBase), (
                "has illegal child",
                "upper",
                value,
                value.__class__,
            )

            if old_node is value:
                self.setChild("upper", new_node)

                return "upper"

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {}

        value = self.subnode_expression

        if value is None:
            values["expression"] = None
        elif type(value) is tuple:
            values["expression"] = tuple(v.makeClone() for v in value)
        else:
            values["expression"] = value.makeClone()
        value = self.subnode_lower

        if value is None:
            values["lower"] = None
        elif type(value) is tuple:
            values["lower"] = tuple(v.makeClone() for v in value)
        else:
            values["lower"] = value.makeClone()
        value = self.subnode_upper

        if value is None:
            values["upper"] = None
        elif type(value) is tuple:
            values["upper"] = tuple(v.makeClone() for v in value)
        else:
            values["upper"] = value.makeClone()

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_expression.finalize()
        self.subnode_lower.finalize()
        self.subnode_upper.finalize()

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

            if expression.willRaiseException(BaseException):
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


class ChildrenHavingGroupNameMixin(object):
    # Mixins are not allow to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    named_children = ("group", "name")

    checkers = {}

    def __init__(
        self,
        group,
        name,
    ):
        if group is not None:
            group.parent = self

        self.subnode_group = group

        if name is not None:
            name.parent = self

        self.subnode_name = name

    def setChild(self, name, value):
        """Set a child value.

        Do not overload, provider self.checkers instead.
        """
        # Lists as inputs are OK, but turn them into tuples on the fly.
        if type(value) is list:
            value = tuple(value)

        # Re-parent value to us.
        if type(value) is tuple:
            for val in value:
                val.parent = self
        elif value is not None:
            value.parent = self

        # Determine old value, and inform it about losing its parent.
        attr_name = "subnode_" + name
        old_value = getattr(self, attr_name)
        assert old_value is not value, value

        setattr(self, attr_name, value)

    def clearChild(self, name):
        # Only accept legal child names
        assert name in ("group", "name"), name

        # Determine old value, and check it has no parent anymore.
        attr_name = "subnode_" + name
        # Determine old value, and inform it about losing its parent.
        old_value = getattr(self, attr_name)
        assert old_value is not None
        assert old_value.parent is None

        setattr(self, attr_name, None)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []

        value = self.subnode_group

        if value is None:
            pass
        elif type(value) is tuple:
            result.extend(value)
        else:
            assert isinstance(value, NodeBase), (
                "has illegal child",
                "group",
                value,
                value.__class__,
            )
            result.append(value)

        value = self.subnode_name

        if value is None:
            pass
        elif type(value) is tuple:
            result.extend(value)
        else:
            assert isinstance(value, NodeBase), (
                "has illegal child",
                "name",
                value,
                value.__class__,
            )
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
        if new_node is not None and not isinstance(new_node, NodeBase):
            raise AssertionError(
                "Cannot replace with", new_node, "old", old_node, "in", self
            )
        # Find the replaced node, as an added difficulty, what might be
        # happening, is that the old node is an element of a tuple, in which we
        # may also remove that element, by setting it to None.
        value = self.subnode_group

        if value is None:
            pass
        elif type(value) is tuple:
            if old_node in value:
                if new_node is not None:
                    self.subnode_group = tuple(
                        (val if val is not old_node else new_node) for val in value
                    )
                else:
                    self.subnode_group = tuple(
                        val for val in value if val is not old_node
                    )

                return "group"
        else:
            assert isinstance(value, NodeBase), (
                "has illegal child",
                "group",
                value,
                value.__class__,
            )

            if old_node is value:
                self.setChild("group", new_node)

                return "group"

        value = self.subnode_name

        if value is None:
            pass
        elif type(value) is tuple:
            if old_node in value:
                if new_node is not None:
                    self.subnode_name = tuple(
                        (val if val is not old_node else new_node) for val in value
                    )
                else:
                    self.subnode_name = tuple(
                        val for val in value if val is not old_node
                    )

                return "name"
        else:
            assert isinstance(value, NodeBase), (
                "has illegal child",
                "name",
                value,
                value.__class__,
            )

            if old_node is value:
                self.setChild("name", new_node)

                return "name"

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {}

        value = self.subnode_group

        if value is None:
            values["group"] = None
        elif type(value) is tuple:
            values["group"] = tuple(v.makeClone() for v in value)
        else:
            values["group"] = value.makeClone()
        value = self.subnode_name

        if value is None:
            values["name"] = None
        elif type(value) is tuple:
            values["name"] = tuple(v.makeClone() for v in value)
        else:
            values["name"] = value.makeClone()

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_group.finalize()
        self.subnode_name.finalize()

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

            if expression.willRaiseException(BaseException):
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


class ChildrenHavingPairsTupleMixin(object):
    # Mixins are not allow to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    named_children = ("pairs",)

    checkers = {}

    def __init__(
        self,
        pairs,
    ):
        assert type(pairs) is tuple

        for val in pairs:
            assert val is not None
            val.parent = self

        self.subnode_pairs = pairs

    def setChild(self, name, value):
        """Set a child value.

        Do not overload, provider self.checkers instead.
        """
        # Lists as inputs are OK, but turn them into tuples on the fly.
        if type(value) is list:
            value = tuple(value)

        # Re-parent value to us.
        if type(value) is tuple:
            for val in value:
                val.parent = self
        elif value is not None:
            value.parent = self

        # Determine old value, and inform it about losing its parent.
        attr_name = "subnode_" + name
        old_value = getattr(self, attr_name)
        assert old_value is not value, value

        setattr(self, attr_name, value)

    def clearChild(self, name):
        # Only accept legal child names
        assert name in ("pairs",), name

        # Determine old value, and check it has no parent anymore.
        old_value = self.subnode_pairs
        assert old_value is not None
        assert old_value.parent is None
        self.subnode_pairs = None

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return self.subnode_pairs

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("pairs", self.subnode_pairs),)

    def replaceChild(self, old_node, new_node):
        if new_node is not None and not isinstance(new_node, NodeBase):
            raise AssertionError(
                "Cannot replace with", new_node, "old", old_node, "in", self
            )
        value = self.subnode_pairs
        if old_node not in value:
            raise AssertionError("Didn't find child", old_node, "in", self)

        if new_node is not None:
            new_value = tuple(
                (val if val is not old_node else new_node) for val in value
            )
        else:
            new_value = tuple(val for val in value if val is not old_node)

        new_node.parent = self

        self.subnode_pairs = new_value

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        value = self.subnode_pairs

        values = {"pairs": tuple(v.makeClone() for v in value)}
        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        for c in self.subnode_pairs:
            c.finalize()

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expressions, as they are evaluated before
        # the actual operation.
        for count, sub_expression in enumerate(self.subnode_pairs):
            expression = trace_collection.onExpression(sub_expression)

            if expression.willRaiseException(BaseException):
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


class ChildrenHavingRequirementsTupleMixin(object):
    # Mixins are not allow to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    named_children = ("requirements",)

    checkers = {}

    def __init__(
        self,
        requirements,
    ):
        assert type(requirements) is tuple

        for val in requirements:
            assert val is not None
            val.parent = self

        self.subnode_requirements = requirements

    def setChild(self, name, value):
        """Set a child value.

        Do not overload, provider self.checkers instead.
        """
        # Lists as inputs are OK, but turn them into tuples on the fly.
        if type(value) is list:
            value = tuple(value)

        # Re-parent value to us.
        if type(value) is tuple:
            for val in value:
                val.parent = self
        elif value is not None:
            value.parent = self

        # Determine old value, and inform it about losing its parent.
        attr_name = "subnode_" + name
        old_value = getattr(self, attr_name)
        assert old_value is not value, value

        setattr(self, attr_name, value)

    def clearChild(self, name):
        # Only accept legal child names
        assert name in ("requirements",), name

        # Determine old value, and check it has no parent anymore.
        old_value = self.subnode_requirements
        assert old_value is not None
        assert old_value.parent is None
        self.subnode_requirements = None

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return self.subnode_requirements

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("requirements", self.subnode_requirements),)

    def replaceChild(self, old_node, new_node):
        if new_node is not None and not isinstance(new_node, NodeBase):
            raise AssertionError(
                "Cannot replace with", new_node, "old", old_node, "in", self
            )
        value = self.subnode_requirements
        if old_node not in value:
            raise AssertionError("Didn't find child", old_node, "in", self)

        if new_node is not None:
            new_value = tuple(
                (val if val is not old_node else new_node) for val in value
            )
        else:
            new_value = tuple(val for val in value if val is not old_node)

        new_node.parent = self

        self.subnode_requirements = new_value

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        value = self.subnode_requirements

        values = {"requirements": tuple(v.makeClone() for v in value)}
        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        for c in self.subnode_requirements:
            c.finalize()

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expressions, as they are evaluated before
        # the actual operation.
        for count, sub_expression in enumerate(self.subnode_requirements):
            expression = trace_collection.onExpression(sub_expression)

            if expression.willRaiseException(BaseException):
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


class ChildrenHavingValuesTupleMixin(object):
    # Mixins are not allow to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    named_children = ("values",)

    checkers = {}

    def __init__(
        self,
        values,
    ):
        assert type(values) is tuple

        for val in values:
            assert val is not None
            val.parent = self

        self.subnode_values = values

    def setChild(self, name, value):
        """Set a child value.

        Do not overload, provider self.checkers instead.
        """
        # Lists as inputs are OK, but turn them into tuples on the fly.
        if type(value) is list:
            value = tuple(value)

        # Re-parent value to us.
        if type(value) is tuple:
            for val in value:
                val.parent = self
        elif value is not None:
            value.parent = self

        # Determine old value, and inform it about losing its parent.
        attr_name = "subnode_" + name
        old_value = getattr(self, attr_name)
        assert old_value is not value, value

        setattr(self, attr_name, value)

    def clearChild(self, name):
        # Only accept legal child names
        assert name in ("values",), name

        # Determine old value, and check it has no parent anymore.
        old_value = self.subnode_values
        assert old_value is not None
        assert old_value.parent is None
        self.subnode_values = None

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return self.subnode_values

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("values", self.subnode_values),)

    def replaceChild(self, old_node, new_node):
        if new_node is not None and not isinstance(new_node, NodeBase):
            raise AssertionError(
                "Cannot replace with", new_node, "old", old_node, "in", self
            )
        value = self.subnode_values
        if old_node not in value:
            raise AssertionError("Didn't find child", old_node, "in", self)

        if new_node is not None:
            new_value = tuple(
                (val if val is not old_node else new_node) for val in value
            )
        else:
            new_value = tuple(val for val in value if val is not old_node)

        new_node.parent = self

        self.subnode_values = new_value

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        value = self.subnode_values

        values = {"values": tuple(v.makeClone() for v in value)}
        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        for c in self.subnode_values:
            c.finalize()

    def computeExpressionRaw(self, trace_collection):
        """Compute an expression.

        Default behavior is to just visit the child expressions first, and
        then the node "computeExpression". For a few cases this needs to
        be overloaded, e.g. conditional expressions.
        """

        # First apply the sub-expressions, as they are evaluated before
        # the actual operation.
        for count, sub_expression in enumerate(self.subnode_values):
            expression = trace_collection.onExpression(sub_expression)

            if expression.willRaiseException(BaseException):
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
