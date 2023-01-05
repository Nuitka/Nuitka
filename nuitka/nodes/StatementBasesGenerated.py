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


"""Children having statement bases

WARNING, this code is GENERATED. Modify the template ChildrenHavingMixin.py.j2 instead!

spell-checker: ignore capitalize casefold center clear copy count decode encode endswith expandtabs find format formatmap get haskey index isalnum isalpha isascii isdecimal isdigit isidentifier islower isnumeric isprintable isspace istitle isupper items iteritems iterkeys itervalues join keys ljust lower lstrip maketrans partition pop popitem replace rfind rindex rjust rpartition rsplit rstrip setdefault split splitlines startswith strip swapcase title translate update upper values viewitems viewkeys viewvalues zfill
spell-checker: ignore args chars count default delete encoding end errors fillchar iterable keepends key maxsplit new old pairs prefix sep start sub suffix table tabsize width
"""


# Loop unrolling over child names, pylint: disable=too-many-branches

from .NodeBases import StatementBase


class StatementChildHavingExpressionAttributeNameMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementDelAttribute

    def __init__(self, expression, attribute_name, source_ref):
        expression.parent = self

        self.subnode_expression = expression

        self.attribute_name = attribute_name

        StatementBase.__init__(self, source_ref)

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


# Assign the names that are easier to import with a stable name.
StatementDelAttributeBase = StatementChildHavingExpressionAttributeNameMixin


class StatementChildrenHavingSourceExpressionAttributeNameMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementAssignmentAttribute

    def __init__(self, source, expression, attribute_name, source_ref):
        source.parent = self

        self.subnode_source = source

        expression.parent = self

        self.subnode_expression = expression

        self.attribute_name = attribute_name

        StatementBase.__init__(self, source_ref)

    def getDetails(self):
        return {
            "attribute_name": self.attribute_name,
        }

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_source,
            self.subnode_expression,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("source", self.subnode_source),
            ("expression", self.subnode_expression),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_source
        if old_node is value:
            new_node.parent = self

            self.subnode_source = new_node

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
            "source": self.subnode_source.makeClone(),
            "expression": self.subnode_expression.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_source.finalize()
        del self.subnode_source
        self.subnode_expression.finalize()
        del self.subnode_expression


# Assign the names that are easier to import with a stable name.
StatementAssignmentAttributeBase = (
    StatementChildrenHavingSourceExpressionAttributeNameMixin
)
