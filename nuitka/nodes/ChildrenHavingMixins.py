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
# pylint: disable=I0021,too-many-lines
# pylint: disable=I0021,line-too-long

"""Children having mixins

WARNING, this code is GENERATED. Modify the template ChildrenHavingMixin.py.j2 instead!

spell-checker: ignore capitalize casefold center clear copy count decode encode endswith expandtabs find format formatmap get haskey hex index isalnum isalpha isascii isdecimal isdigit isidentifier islower isnumeric isprintable isspace istitle isupper items iteritems iterkeys itervalues join keys ljust lower lstrip maketrans partition pop popitem replace rfind rindex rjust rpartition rsplit rstrip setdefault split splitlines startswith strip swapcase title translate update upper values viewitems viewkeys viewvalues zfill
spell-checker: ignore args chars count default encoding end errors fillchar iterable keepends key maxsplit new old pairs prefix sep start sub suffix table tabsize width
"""


# Loop unrolling over child names, pylint: disable=too-many-branches

from .NodeBases import NodeBase
from .NodeMetaClasses import NuitkaNodeDesignError


class ChildrenHavingMixinGroupName(object):
    # Mixins are not allow to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    named_children = ("group", "name")

    checkers = {}

    def __init__(self, values):
        assert (
            type(self.named_children) is tuple and self.named_children
        ), self.named_children

        # Check for completeness of given values, everything should be there
        # but of course, might be put to None.
        if set(values.keys()) != set(self.named_children):
            raise NuitkaNodeDesignError(
                "Must pass named children in value dictionary",
                set(values.keys()),
                set(self.named_children),
            )

        value = values["group"]

        if "group" in self.checkers:
            value = self.checkers["group"](value)

        if type(value) is tuple:
            assert None not in value, "group"

            for val in value:
                val.parent = self
        elif value is None:
            pass
        else:
            value.parent = self

        self.subnode_group = value
        value = values["name"]

        if "name" in self.checkers:
            value = self.checkers["name"](value)

        if type(value) is tuple:
            assert None not in value, "name"

            for val in value:
                val.parent = self
        elif value is None:
            pass
        else:
            value.parent = self

        self.subnode_name = value

    def setChild(self, name, value):
        """Set a child value.

        Do not overload, provider self.checkers instead.
        """
        # Only accept legal child names
        assert name in self.named_children, name

        # Lists as inputs are OK, but turn them into tuples.
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

        attr_name = "subnode_" + name

        # Determine old value, and inform it about losing its parent.
        old_value = getattr(self, attr_name)

        assert old_value is not value, value

        setattr(self, attr_name, value)

    def clearChild(self, name):
        # Only accept legal child names
        assert name in ("group", "name"), name

        if name in self.checkers:
            self.checkers[name](None)

        # Determine old value, and check it has no parent anymore.
        attr_name = "subnode_" + name
        # Determine old value, and inform it about losing its parent.
        old_value = getattr(self, attr_name)
        assert old_value is not None
        assert old_value.parent is None

        setattr(self, attr_name, None)

    def getChild(self, name):
        attr_name = "subnode_" + name
        return getattr(self, attr_name)

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
                    self.setChild(
                        "group",
                        tuple(
                            (val if val is not old_node else new_node) for val in value
                        ),
                    )
                else:
                    self.setChild(
                        "group", tuple(val for val in value if val is not old_node)
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
                    self.setChild(
                        "name",
                        tuple(
                            (val if val is not old_node else new_node) for val in value
                        ),
                    )
                else:
                    self.setChild(
                        "name", tuple(val for val in value if val is not old_node)
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


class ChildrenHavingMixinDistributionName(object):
    # Mixins are not allow to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    named_children = ("distribution_name",)

    checkers = {}

    def __init__(self, values):
        assert (
            type(self.named_children) is tuple and self.named_children
        ), self.named_children

        # Check for completeness of given values, everything should be there
        # but of course, might be put to None.
        if set(values.keys()) != set(self.named_children):
            raise NuitkaNodeDesignError(
                "Must pass named children in value dictionary",
                set(values.keys()),
                set(self.named_children),
            )

        value = values["distribution_name"]

        if "distribution_name" in self.checkers:
            value = self.checkers["distribution_name"](value)

        if type(value) is tuple:
            assert None not in value, "distribution_name"

            for val in value:
                val.parent = self
        elif value is None:
            pass
        else:
            value.parent = self

        self.subnode_distribution_name = value

    def setChild(self, name, value):
        """Set a child value.

        Do not overload, provider self.checkers instead.
        """
        # Only accept legal child names
        assert name in self.named_children, name

        # Lists as inputs are OK, but turn them into tuples.
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

        attr_name = "subnode_" + name

        # Determine old value, and inform it about losing its parent.
        old_value = getattr(self, attr_name)

        assert old_value is not value, value

        setattr(self, attr_name, value)

    def clearChild(self, name):
        # Only accept legal child names
        assert name in ("distribution_name",), name

        if name in self.checkers:
            self.checkers[name](None)

        # Determine old value, and check it has no parent anymore.
        old_value = self.subnode_distribution_name
        assert old_value is not None
        assert old_value.parent is None
        self.subnode_distribution_name = None

    def getChild(self, name):
        attr_name = "subnode_" + name
        return getattr(self, attr_name)

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


class ChildrenHavingMixinDist(object):
    # Mixins are not allow to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    named_children = ("dist",)

    checkers = {}

    def __init__(self, values):
        assert (
            type(self.named_children) is tuple and self.named_children
        ), self.named_children

        # Check for completeness of given values, everything should be there
        # but of course, might be put to None.
        if set(values.keys()) != set(self.named_children):
            raise NuitkaNodeDesignError(
                "Must pass named children in value dictionary",
                set(values.keys()),
                set(self.named_children),
            )

        value = values["dist"]

        if "dist" in self.checkers:
            value = self.checkers["dist"](value)

        if type(value) is tuple:
            assert None not in value, "dist"

            for val in value:
                val.parent = self
        elif value is None:
            pass
        else:
            value.parent = self

        self.subnode_dist = value

    def setChild(self, name, value):
        """Set a child value.

        Do not overload, provider self.checkers instead.
        """
        # Only accept legal child names
        assert name in self.named_children, name

        # Lists as inputs are OK, but turn them into tuples.
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

        attr_name = "subnode_" + name

        # Determine old value, and inform it about losing its parent.
        old_value = getattr(self, attr_name)

        assert old_value is not value, value

        setattr(self, attr_name, value)

    def clearChild(self, name):
        # Only accept legal child names
        assert name in ("dist",), name

        if name in self.checkers:
            self.checkers[name](None)

        # Determine old value, and check it has no parent anymore.
        old_value = self.subnode_dist
        assert old_value is not None
        assert old_value.parent is None
        self.subnode_dist = None

    def getChild(self, name):
        attr_name = "subnode_" + name
        return getattr(self, attr_name)

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


class ChildrenHavingMixinRequirements(object):
    # Mixins are not allow to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    named_children = ("requirements",)

    checkers = {}

    def __init__(self, values):
        assert (
            type(self.named_children) is tuple and self.named_children
        ), self.named_children

        # Check for completeness of given values, everything should be there
        # but of course, might be put to None.
        if set(values.keys()) != set(self.named_children):
            raise NuitkaNodeDesignError(
                "Must pass named children in value dictionary",
                set(values.keys()),
                set(self.named_children),
            )

        value = values["requirements"]

        if "requirements" in self.checkers:
            value = self.checkers["requirements"](value)

        if type(value) is tuple:
            assert None not in value, "requirements"

            for val in value:
                val.parent = self
        elif value is None:
            pass
        else:
            value.parent = self

        self.subnode_requirements = value

    def setChild(self, name, value):
        """Set a child value.

        Do not overload, provider self.checkers instead.
        """
        # Only accept legal child names
        assert name in self.named_children, name

        # Lists as inputs are OK, but turn them into tuples.
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

        attr_name = "subnode_" + name

        # Determine old value, and inform it about losing its parent.
        old_value = getattr(self, attr_name)

        assert old_value is not value, value

        setattr(self, attr_name, value)

    def clearChild(self, name):
        # Only accept legal child names
        assert name in ("requirements",), name

        if name in self.checkers:
            self.checkers[name](None)

        # Determine old value, and check it has no parent anymore.
        old_value = self.subnode_requirements
        assert old_value is not None
        assert old_value.parent is None
        self.subnode_requirements = None

    def getChild(self, name):
        attr_name = "subnode_" + name
        return getattr(self, attr_name)

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

        for c in self.requirements:
            c.finalize()
