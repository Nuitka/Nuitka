#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# We are not avoiding these in generated code at all
# pylint: disable=I0021,line-too-long,too-many-instance-attributes,too-many-lines
# pylint: disable=I0021,too-many-arguments,too-many-return-statements,too-many-statements


"""Children having statement bases

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

from .Checkers import (
    checkStatementsSequence,
    checkStatementsSequenceOrNone,
    convertNoneConstantToNone,
)
from .NodeBases import StatementBase


class StatementNoChildHavingLocalsScopeMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementSetLocalsDictionary

    def __init__(self, locals_scope, source_ref):
        self.locals_scope = locals_scope

        StatementBase.__init__(self, source_ref)

    def getDetails(self):
        return {
            "locals_scope": self.locals_scope,
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

        del self.locals_scope

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""


# Assign the names that are easier to import with a stable name.
StatementSetLocalsDictionaryBase = StatementNoChildHavingLocalsScopeMixin


class StatementChildrenHavingConditionYesBranchOptionalStatementsOrNoneNoBranchOptionalStatementsOrNoneMixin(
    StatementBase
):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementConditional

    def __init__(self, condition, yes_branch, no_branch, source_ref):
        condition.parent = self

        self.subnode_condition = condition

        yes_branch = checkStatementsSequenceOrNone(yes_branch)
        if yes_branch is not None:
            yes_branch.parent = self

        self.subnode_yes_branch = yes_branch

        no_branch = checkStatementsSequenceOrNone(no_branch)
        if no_branch is not None:
            no_branch.parent = self

        self.subnode_no_branch = no_branch

        StatementBase.__init__(self, source_ref)

    def setChildNoBranch(self, value):
        value = checkStatementsSequenceOrNone(value)
        if value is not None:
            value.parent = self

        self.subnode_no_branch = value

    def setChildYesBranch(self, value):
        value = checkStatementsSequenceOrNone(value)
        if value is not None:
            value.parent = self

        self.subnode_yes_branch = value

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_condition)
        value = self.subnode_yes_branch
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_no_branch
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
            ("condition", self.subnode_condition),
            ("yes_branch", self.subnode_yes_branch),
            ("no_branch", self.subnode_no_branch),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_condition
        if old_node is value:
            new_node.parent = self

            self.subnode_condition = new_node

            return

        value = self.subnode_yes_branch
        if old_node is value:
            new_node = checkStatementsSequenceOrNone(new_node)
            if new_node is not None:
                new_node.parent = self

            self.subnode_yes_branch = new_node

            return

        value = self.subnode_no_branch
        if old_node is value:
            new_node = checkStatementsSequenceOrNone(new_node)
            if new_node is not None:
                new_node.parent = self

            self.subnode_no_branch = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "condition": self.subnode_condition.makeClone(),
            "yes_branch": (
                self.subnode_yes_branch.makeClone()
                if self.subnode_yes_branch is not None
                else None
            ),
            "no_branch": (
                self.subnode_no_branch.makeClone()
                if self.subnode_no_branch is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_condition.finalize()
        del self.subnode_condition
        if self.subnode_yes_branch is not None:
            self.subnode_yes_branch.finalize()
        del self.subnode_yes_branch
        if self.subnode_no_branch is not None:
            self.subnode_no_branch.finalize()
        del self.subnode_no_branch

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_condition.collectVariableAccesses(emit_read, emit_write)
        subnode_yes_branch = self.subnode_yes_branch

        if subnode_yes_branch is not None:
            self.subnode_yes_branch.collectVariableAccesses(emit_read, emit_write)
        subnode_no_branch = self.subnode_no_branch

        if subnode_no_branch is not None:
            self.subnode_no_branch.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementConditionalBase = StatementChildrenHavingConditionYesBranchOptionalStatementsOrNoneNoBranchOptionalStatementsOrNoneMixin


class StatementChildHavingDestOptionalOperationMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementPrintNewline

    def __init__(self, dest, source_ref):
        if dest is not None:
            dest.parent = self

        self.subnode_dest = dest

        StatementBase.__init__(self, source_ref)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        value = self.subnode_dest

        if value is None:
            return ()
        else:
            return (value,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("dest", self.subnode_dest),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_dest
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_dest = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "dest": (
                self.subnode_dest.makeClone() if self.subnode_dest is not None else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        if self.subnode_dest is not None:
            self.subnode_dest.finalize()
        del self.subnode_dest

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.computeStatementOperation(trace_collection)

    @abstractmethod
    def computeStatementOperation(self, trace_collection):
        """Must be overloaded for non-final node."""

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        subnode_dest = self.subnode_dest

        if subnode_dest is not None:
            self.subnode_dest.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementPrintNewlineBase = StatementChildHavingDestOptionalOperationMixin


class StatementChildrenHavingDestOptionalValueOperationMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementPrintValue

    def __init__(self, dest, value, source_ref):
        if dest is not None:
            dest.parent = self

        self.subnode_dest = dest

        value.parent = self

        self.subnode_value = value

        StatementBase.__init__(self, source_ref)

    def setChildValue(self, value):
        value.parent = self

        self.subnode_value = value

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        value = self.subnode_dest
        if value is None:
            pass
        else:
            result.append(value)
        result.append(self.subnode_value)
        return tuple(result)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("dest", self.subnode_dest),
            ("value", self.subnode_value),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_dest
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_dest = new_node

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
            "dest": (
                self.subnode_dest.makeClone() if self.subnode_dest is not None else None
            ),
            "value": self.subnode_value.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        if self.subnode_dest is not None:
            self.subnode_dest.finalize()
        del self.subnode_dest
        self.subnode_value.finalize()
        del self.subnode_value

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.computeStatementOperation(trace_collection)

    @abstractmethod
    def computeStatementOperation(self, trace_collection):
        """Must be overloaded for non-final node."""

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        subnode_dest = self.subnode_dest

        if subnode_dest is not None:
            self.subnode_dest.collectVariableAccesses(emit_read, emit_write)
        self.subnode_value.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementPrintValueBase = StatementChildrenHavingDestOptionalValueOperationMixin


class StatementChildrenHavingDictArgKeyOperationMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementDictOperationRemove

    def __init__(self, dict_arg, key, source_ref):
        dict_arg.parent = self

        self.subnode_dict_arg = dict_arg

        key.parent = self

        self.subnode_key = key

        StatementBase.__init__(self, source_ref)

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

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.computeStatementOperation(trace_collection)

    @abstractmethod
    def computeStatementOperation(self, trace_collection):
        """Must be overloaded for non-final node."""

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_dict_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_key.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementDictOperationRemoveBase = StatementChildrenHavingDictArgKeyOperationMixin


class StatementChildrenHavingDictArgValueOperationMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementDictOperationUpdate

    def __init__(self, dict_arg, value, source_ref):
        dict_arg.parent = self

        self.subnode_dict_arg = dict_arg

        value.parent = self

        self.subnode_value = value

        StatementBase.__init__(self, source_ref)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_dict_arg,
            self.subnode_value,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("dict_arg", self.subnode_dict_arg),
            ("value", self.subnode_value),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_dict_arg
        if old_node is value:
            new_node.parent = self

            self.subnode_dict_arg = new_node

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
            "dict_arg": self.subnode_dict_arg.makeClone(),
            "value": self.subnode_value.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_dict_arg.finalize()
        del self.subnode_dict_arg
        self.subnode_value.finalize()
        del self.subnode_value

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.computeStatementOperation(trace_collection)

    @abstractmethod
    def computeStatementOperation(self, trace_collection):
        """Must be overloaded for non-final node."""

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_dict_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_value.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementDictOperationUpdateBase = StatementChildrenHavingDictArgValueOperationMixin


class StatementChildrenHavingExceptionTypeExceptionValueOptionalExceptionTraceOptionalExceptionCauseOptionalOperationPostInitMixin(
    StatementBase
):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementRaiseException

    def __init__(
        self,
        exception_type,
        exception_value,
        exception_trace,
        exception_cause,
        source_ref,
    ):
        exception_type.parent = self

        self.subnode_exception_type = exception_type

        if exception_value is not None:
            exception_value.parent = self

        self.subnode_exception_value = exception_value

        if exception_trace is not None:
            exception_trace.parent = self

        self.subnode_exception_trace = exception_trace

        if exception_cause is not None:
            exception_cause.parent = self

        self.subnode_exception_cause = exception_cause

        StatementBase.__init__(self, source_ref)

        self.postInitNode()

    @abstractmethod
    def postInitNode(self):
        """For overload"""

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_exception_type)
        value = self.subnode_exception_value
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_exception_trace
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_exception_cause
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
            ("exception_type", self.subnode_exception_type),
            ("exception_value", self.subnode_exception_value),
            ("exception_trace", self.subnode_exception_trace),
            ("exception_cause", self.subnode_exception_cause),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_exception_type
        if old_node is value:
            new_node.parent = self

            self.subnode_exception_type = new_node

            return

        value = self.subnode_exception_value
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_exception_value = new_node

            return

        value = self.subnode_exception_trace
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_exception_trace = new_node

            return

        value = self.subnode_exception_cause
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_exception_cause = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "exception_type": self.subnode_exception_type.makeClone(),
            "exception_value": (
                self.subnode_exception_value.makeClone()
                if self.subnode_exception_value is not None
                else None
            ),
            "exception_trace": (
                self.subnode_exception_trace.makeClone()
                if self.subnode_exception_trace is not None
                else None
            ),
            "exception_cause": (
                self.subnode_exception_cause.makeClone()
                if self.subnode_exception_cause is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_exception_type.finalize()
        del self.subnode_exception_type
        if self.subnode_exception_value is not None:
            self.subnode_exception_value.finalize()
        del self.subnode_exception_value
        if self.subnode_exception_trace is not None:
            self.subnode_exception_trace.finalize()
        del self.subnode_exception_trace
        if self.subnode_exception_cause is not None:
            self.subnode_exception_cause.finalize()
        del self.subnode_exception_cause

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.computeStatementOperation(trace_collection)

    @abstractmethod
    def computeStatementOperation(self, trace_collection):
        """Must be overloaded for non-final node."""

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_exception_type.collectVariableAccesses(emit_read, emit_write)
        subnode_exception_value = self.subnode_exception_value

        if subnode_exception_value is not None:
            self.subnode_exception_value.collectVariableAccesses(emit_read, emit_write)
        subnode_exception_trace = self.subnode_exception_trace

        if subnode_exception_trace is not None:
            self.subnode_exception_trace.collectVariableAccesses(emit_read, emit_write)
        subnode_exception_cause = self.subnode_exception_cause

        if subnode_exception_cause is not None:
            self.subnode_exception_cause.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementRaiseExceptionBase = StatementChildrenHavingExceptionTypeExceptionValueOptionalExceptionTraceOptionalExceptionCauseOptionalOperationPostInitMixin


class StatementChildHavingExpressionOperationAttributeNameMixin(StatementBase):
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

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.computeStatementOperation(trace_collection)

    @abstractmethod
    def computeStatementOperation(self, trace_collection):
        """Must be overloaded for non-final node."""

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_expression.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementDelAttributeBase = StatementChildHavingExpressionOperationAttributeNameMixin


class StatementChildHavingExpressionMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementExpressionOnly
    #   StatementGeneratorReturn
    #   StatementReturn

    def __init__(self, expression, source_ref):
        expression.parent = self

        self.subnode_expression = expression

        StatementBase.__init__(self, source_ref)

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_expression.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementExpressionOnlyBase = StatementChildHavingExpressionMixin
StatementGeneratorReturnBase = StatementChildHavingExpressionMixin
StatementReturnBase = StatementChildHavingExpressionMixin


class StatementChildrenHavingExpressionLowerOptionalUpperOptionalMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementDelSlice

    def __init__(self, expression, lower, upper, source_ref):
        expression.parent = self

        self.subnode_expression = expression

        if lower is not None:
            lower.parent = self

        self.subnode_lower = lower

        if upper is not None:
            upper.parent = self

        self.subnode_upper = upper

        StatementBase.__init__(self, source_ref)

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
            if new_node is not None:
                new_node.parent = self

            self.subnode_lower = new_node

            return

        value = self.subnode_upper
        if old_node is value:
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
StatementDelSliceBase = StatementChildrenHavingExpressionLowerOptionalUpperOptionalMixin


class StatementChildHavingIteratedLengthOperationCountMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementSpecialUnpackCheckFromIterated

    def __init__(self, iterated_length, count, source_ref):
        iterated_length.parent = self

        self.subnode_iterated_length = iterated_length

        self.count = count

        StatementBase.__init__(self, source_ref)

    def getDetails(self):
        return {
            "count": self.count,
        }

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_iterated_length,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("iterated_length", self.subnode_iterated_length),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_iterated_length
        if old_node is value:
            new_node.parent = self

            self.subnode_iterated_length = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "iterated_length": self.subnode_iterated_length.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_iterated_length.finalize()
        del self.subnode_iterated_length

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.computeStatementOperation(trace_collection)

    @abstractmethod
    def computeStatementOperation(self, trace_collection):
        """Must be overloaded for non-final node."""

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_iterated_length.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementSpecialUnpackCheckFromIteratedBase = (
    StatementChildHavingIteratedLengthOperationCountMixin
)


class StatementChildHavingIteratorOperationCountMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementSpecialUnpackCheck

    def __init__(self, iterator, count, source_ref):
        iterator.parent = self

        self.subnode_iterator = iterator

        self.count = count

        StatementBase.__init__(self, source_ref)

    def getDetails(self):
        return {
            "count": self.count,
        }

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_iterator,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("iterator", self.subnode_iterator),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_iterator
        if old_node is value:
            new_node.parent = self

            self.subnode_iterator = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "iterator": self.subnode_iterator.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_iterator.finalize()
        del self.subnode_iterator

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.computeStatementOperation(trace_collection)

    @abstractmethod
    def computeStatementOperation(self, trace_collection):
        """Must be overloaded for non-final node."""

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_iterator.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementSpecialUnpackCheckBase = StatementChildHavingIteratorOperationCountMixin


class StatementChildrenHavingListArgValueOperationMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementListOperationAppend

    def __init__(self, list_arg, value, source_ref):
        list_arg.parent = self

        self.subnode_list_arg = list_arg

        value.parent = self

        self.subnode_value = value

        StatementBase.__init__(self, source_ref)

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

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.computeStatementOperation(trace_collection)

    @abstractmethod
    def computeStatementOperation(self, trace_collection):
        """Must be overloaded for non-final node."""

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_list_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_value.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementListOperationAppendBase = StatementChildrenHavingListArgValueOperationMixin


class StatementChildHavingLocalsArgOperationPostInitLocalsScopeMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementLocalsDictSync

    def __init__(self, locals_arg, locals_scope, source_ref):
        locals_arg.parent = self

        self.subnode_locals_arg = locals_arg

        self.locals_scope = locals_scope

        StatementBase.__init__(self, source_ref)

        self.postInitNode()

    @abstractmethod
    def postInitNode(self):
        """For overload"""

    def getDetails(self):
        return {
            "locals_scope": self.locals_scope,
        }

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_locals_arg,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("locals_arg", self.subnode_locals_arg),)

    def replaceChild(self, old_node, new_node):
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
            "locals_arg": self.subnode_locals_arg.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_locals_arg.finalize()
        del self.subnode_locals_arg

        del self.locals_scope

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.computeStatementOperation(trace_collection)

    @abstractmethod
    def computeStatementOperation(self, trace_collection):
        """Must be overloaded for non-final node."""

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_locals_arg.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementLocalsDictSyncBase = (
    StatementChildHavingLocalsArgOperationPostInitLocalsScopeMixin
)


class StatementChildHavingLoopBodyOptionalStatementsOrNonePostInitMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementLoop

    def __init__(self, loop_body, source_ref):
        loop_body = checkStatementsSequenceOrNone(loop_body)
        if loop_body is not None:
            loop_body.parent = self

        self.subnode_loop_body = loop_body

        StatementBase.__init__(self, source_ref)

        self.postInitNode()

    @abstractmethod
    def postInitNode(self):
        """For overload"""

    def setChildLoopBody(self, value):
        value = checkStatementsSequenceOrNone(value)
        if value is not None:
            value.parent = self

        self.subnode_loop_body = value

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        value = self.subnode_loop_body

        if value is None:
            return ()
        else:
            return (value,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("loop_body", self.subnode_loop_body),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_loop_body
        if old_node is value:
            new_node = checkStatementsSequenceOrNone(new_node)
            if new_node is not None:
                new_node.parent = self

            self.subnode_loop_body = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "loop_body": (
                self.subnode_loop_body.makeClone()
                if self.subnode_loop_body is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        if self.subnode_loop_body is not None:
            self.subnode_loop_body.finalize()
        del self.subnode_loop_body

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        subnode_loop_body = self.subnode_loop_body

        if subnode_loop_body is not None:
            self.subnode_loop_body.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementLoopBase = StatementChildHavingLoopBodyOptionalStatementsOrNonePostInitMixin


class StatementChildHavingModuleOperationPostInitTargetScopeMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementImportStar

    def __init__(self, module, target_scope, source_ref):
        module.parent = self

        self.subnode_module = module

        self.target_scope = target_scope

        StatementBase.__init__(self, source_ref)

        self.postInitNode()

    @abstractmethod
    def postInitNode(self):
        """For overload"""

    def getDetails(self):
        return {
            "target_scope": self.target_scope,
        }

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

        del self.target_scope

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.computeStatementOperation(trace_collection)

    @abstractmethod
    def computeStatementOperation(self, trace_collection):
        """Must be overloaded for non-final node."""

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_module.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementImportStarBase = StatementChildHavingModuleOperationPostInitTargetScopeMixin


class StatementChildHavingNewLocalsOperationLocalsScopeMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementSetLocals

    def __init__(self, new_locals, locals_scope, source_ref):
        new_locals.parent = self

        self.subnode_new_locals = new_locals

        self.locals_scope = locals_scope

        StatementBase.__init__(self, source_ref)

    def getDetails(self):
        return {
            "locals_scope": self.locals_scope,
        }

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (self.subnode_new_locals,)

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("new_locals", self.subnode_new_locals),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_new_locals
        if old_node is value:
            new_node.parent = self

            self.subnode_new_locals = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "new_locals": self.subnode_new_locals.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_new_locals.finalize()
        del self.subnode_new_locals

        del self.locals_scope

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.computeStatementOperation(trace_collection)

    @abstractmethod
    def computeStatementOperation(self, trace_collection):
        """Must be overloaded for non-final node."""

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_new_locals.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementSetLocalsBase = StatementChildHavingNewLocalsOperationLocalsScopeMixin


class StatementChildrenHavingSetArgValueOperationMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementSetOperationAdd

    def __init__(self, set_arg, value, source_ref):
        set_arg.parent = self

        self.subnode_set_arg = set_arg

        value.parent = self

        self.subnode_value = value

        StatementBase.__init__(self, source_ref)

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

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.computeStatementOperation(trace_collection)

    @abstractmethod
    def computeStatementOperation(self, trace_collection):
        """Must be overloaded for non-final node."""

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_set_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_value.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementSetOperationAddBase = StatementChildrenHavingSetArgValueOperationMixin


class StatementChildHavingSourcePostInitProviderVariableNameMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementAssignmentVariableName

    def __init__(self, source, provider, variable_name, source_ref):
        source.parent = self

        self.subnode_source = source

        self.provider = provider
        self.variable_name = variable_name

        StatementBase.__init__(self, source_ref)

        self.postInitNode()

    @abstractmethod
    def postInitNode(self):
        """For overload"""

    def getDetails(self):
        return {
            "provider": self.provider,
            "variable_name": self.variable_name,
        }

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

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_source.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementAssignmentVariableNameBase = (
    StatementChildHavingSourcePostInitProviderVariableNameMixin
)


class StatementChildHavingSourcePostInitVariableVariableVersionMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementAssignmentVariableConstantImmutable
    #   StatementAssignmentVariableConstantImmutableTrusted
    #   StatementAssignmentVariableConstantMutable
    #   StatementAssignmentVariableConstantMutableTrusted
    #   StatementAssignmentVariableFromTempVariable
    #   StatementAssignmentVariableFromVariable
    #   StatementAssignmentVariableGeneric
    #   StatementAssignmentVariableHardValue
    #   StatementAssignmentVariableIterator

    def __init__(self, source, variable, variable_version, source_ref):
        source.parent = self

        self.subnode_source = source

        self.variable = variable
        self.variable_version = variable_version

        StatementBase.__init__(self, source_ref)

        self.postInitNode()

    @abstractmethod
    def postInitNode(self):
        """For overload"""

    def getDetails(self):
        return {
            "variable": self.variable,
            "variable_version": self.variable_version,
        }

    def setChildSource(self, value):
        value.parent = self

        self.subnode_source = value

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

        del self.variable

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_source.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementAssignmentVariableConstantImmutableBase = (
    StatementChildHavingSourcePostInitVariableVariableVersionMixin
)
StatementAssignmentVariableConstantImmutableTrustedBase = (
    StatementChildHavingSourcePostInitVariableVariableVersionMixin
)
StatementAssignmentVariableConstantMutableBase = (
    StatementChildHavingSourcePostInitVariableVariableVersionMixin
)
StatementAssignmentVariableConstantMutableTrustedBase = (
    StatementChildHavingSourcePostInitVariableVariableVersionMixin
)
StatementAssignmentVariableFromTempVariableBase = (
    StatementChildHavingSourcePostInitVariableVariableVersionMixin
)
StatementAssignmentVariableFromVariableBase = (
    StatementChildHavingSourcePostInitVariableVariableVersionMixin
)
StatementAssignmentVariableGenericBase = (
    StatementChildHavingSourcePostInitVariableVariableVersionMixin
)
StatementAssignmentVariableHardValueBase = (
    StatementChildHavingSourcePostInitVariableVariableVersionMixin
)
StatementAssignmentVariableIteratorBase = (
    StatementChildHavingSourcePostInitVariableVariableVersionMixin
)


class StatementChildHavingSourceOperationPostInitLocalsScopeVariableNameMixin(
    StatementBase
):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementLocalsDictOperationSet

    def __init__(self, source, locals_scope, variable_name, source_ref):
        source.parent = self

        self.subnode_source = source

        self.locals_scope = locals_scope
        self.variable_name = variable_name

        StatementBase.__init__(self, source_ref)

        self.postInitNode()

    @abstractmethod
    def postInitNode(self):
        """For overload"""

    def getDetails(self):
        return {
            "locals_scope": self.locals_scope,
            "variable_name": self.variable_name,
        }

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

        del self.locals_scope

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.computeStatementOperation(trace_collection)

    @abstractmethod
    def computeStatementOperation(self, trace_collection):
        """Must be overloaded for non-final node."""

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_source.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementLocalsDictOperationSetBase = (
    StatementChildHavingSourceOperationPostInitLocalsScopeVariableNameMixin
)


class StatementChildrenHavingSourceExpressionOperationAttributeNameMixin(StatementBase):
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

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.computeStatementOperation(trace_collection)

    @abstractmethod
    def computeStatementOperation(self, trace_collection):
        """Must be overloaded for non-final node."""

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_source.collectVariableAccesses(emit_read, emit_write)
        self.subnode_expression.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementAssignmentAttributeBase = (
    StatementChildrenHavingSourceExpressionOperationAttributeNameMixin
)


class StatementChildrenHavingSourceExpressionLowerOptionalUpperOptionalMixin(
    StatementBase
):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementAssignmentSlice

    def __init__(self, source, expression, lower, upper, source_ref):
        source.parent = self

        self.subnode_source = source

        expression.parent = self

        self.subnode_expression = expression

        if lower is not None:
            lower.parent = self

        self.subnode_lower = lower

        if upper is not None:
            upper.parent = self

        self.subnode_upper = upper

        StatementBase.__init__(self, source_ref)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_source)
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
            ("source", self.subnode_source),
            ("expression", self.subnode_expression),
            ("lower", self.subnode_lower),
            ("upper", self.subnode_upper),
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

        value = self.subnode_lower
        if old_node is value:
            if new_node is not None:
                new_node.parent = self

            self.subnode_lower = new_node

            return

        value = self.subnode_upper
        if old_node is value:
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
            "source": self.subnode_source.makeClone(),
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

        self.subnode_source.finalize()
        del self.subnode_source
        self.subnode_expression.finalize()
        del self.subnode_expression
        if self.subnode_lower is not None:
            self.subnode_lower.finalize()
        del self.subnode_lower
        if self.subnode_upper is not None:
            self.subnode_upper.finalize()
        del self.subnode_upper

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_source.collectVariableAccesses(emit_read, emit_write)
        self.subnode_expression.collectVariableAccesses(emit_read, emit_write)
        subnode_lower = self.subnode_lower

        if subnode_lower is not None:
            self.subnode_lower.collectVariableAccesses(emit_read, emit_write)
        subnode_upper = self.subnode_upper

        if subnode_upper is not None:
            self.subnode_upper.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementAssignmentSliceBase = (
    StatementChildrenHavingSourceExpressionLowerOptionalUpperOptionalMixin
)


class StatementChildrenHavingSourceSubscribedSubscriptOperationMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementAssignmentSubscript

    def __init__(self, source, subscribed, subscript, source_ref):
        source.parent = self

        self.subnode_source = source

        subscribed.parent = self

        self.subnode_subscribed = subscribed

        subscript.parent = self

        self.subnode_subscript = subscript

        StatementBase.__init__(self, source_ref)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_source,
            self.subnode_subscribed,
            self.subnode_subscript,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("source", self.subnode_source),
            ("subscribed", self.subnode_subscribed),
            ("subscript", self.subnode_subscript),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_source
        if old_node is value:
            new_node.parent = self

            self.subnode_source = new_node

            return

        value = self.subnode_subscribed
        if old_node is value:
            new_node.parent = self

            self.subnode_subscribed = new_node

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
            "source": self.subnode_source.makeClone(),
            "subscribed": self.subnode_subscribed.makeClone(),
            "subscript": self.subnode_subscript.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_source.finalize()
        del self.subnode_source
        self.subnode_subscribed.finalize()
        del self.subnode_subscribed
        self.subnode_subscript.finalize()
        del self.subnode_subscript

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.computeStatementOperation(trace_collection)

    @abstractmethod
    def computeStatementOperation(self, trace_collection):
        """Must be overloaded for non-final node."""

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_source.collectVariableAccesses(emit_read, emit_write)
        self.subnode_subscribed.collectVariableAccesses(emit_read, emit_write)
        self.subnode_subscript.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementAssignmentSubscriptBase = (
    StatementChildrenHavingSourceSubscribedSubscriptOperationMixin
)


class StatementChildrenHavingSourceCodeGlobalsArgAutoNoneLocalsArgAutoNoneOperationMixin(
    StatementBase
):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementExec

    def __init__(self, source_code, globals_arg, locals_arg, source_ref):
        source_code.parent = self

        self.subnode_source_code = source_code

        globals_arg = convertNoneConstantToNone(globals_arg)
        if globals_arg is not None:
            globals_arg.parent = self

        self.subnode_globals_arg = globals_arg

        locals_arg = convertNoneConstantToNone(locals_arg)
        if locals_arg is not None:
            locals_arg.parent = self

        self.subnode_locals_arg = locals_arg

        StatementBase.__init__(self, source_ref)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_source_code)
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
        return tuple(result)

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
            new_node = convertNoneConstantToNone(new_node)
            if new_node is not None:
                new_node.parent = self

            self.subnode_globals_arg = new_node

            return

        value = self.subnode_locals_arg
        if old_node is value:
            new_node = convertNoneConstantToNone(new_node)
            if new_node is not None:
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
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_source_code.finalize()
        del self.subnode_source_code
        if self.subnode_globals_arg is not None:
            self.subnode_globals_arg.finalize()
        del self.subnode_globals_arg
        if self.subnode_locals_arg is not None:
            self.subnode_locals_arg.finalize()
        del self.subnode_locals_arg

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.computeStatementOperation(trace_collection)

    @abstractmethod
    def computeStatementOperation(self, trace_collection):
        """Must be overloaded for non-final node."""

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_source_code.collectVariableAccesses(emit_read, emit_write)
        subnode_globals_arg = self.subnode_globals_arg

        if subnode_globals_arg is not None:
            self.subnode_globals_arg.collectVariableAccesses(emit_read, emit_write)
        subnode_locals_arg = self.subnode_locals_arg

        if subnode_locals_arg is not None:
            self.subnode_locals_arg.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementExecBase = (
    StatementChildrenHavingSourceCodeGlobalsArgAutoNoneLocalsArgAutoNoneOperationMixin
)


class StatementChildHavingStatementsTupleMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementsFrameAsyncgen
    #   StatementsFrameClass
    #   StatementsFrameCoroutine
    #   StatementsFrameFunction
    #   StatementsFrameGenerator
    #   StatementsFrameModule
    #   StatementsSequence

    def __init__(self, statements, source_ref):
        assert type(statements) is tuple

        for val in statements:
            val.parent = self

        self.subnode_statements = statements

        StatementBase.__init__(self, source_ref)

    def setChildStatements(self, value):
        assert type(value) is tuple, type(value)

        for val in value:
            val.parent = self

        self.subnode_statements = value

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return self.subnode_statements

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (("statements", self.subnode_statements),)

    def replaceChild(self, old_node, new_node):
        value = self.subnode_statements
        if old_node in value:
            if new_node is not None:
                new_node.parent = self

                self.subnode_statements = tuple(
                    (val if val is not old_node else new_node) for val in value
                )
            else:
                self.subnode_statements = tuple(
                    val for val in value if val is not old_node
                )

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "statements": tuple(v.makeClone() for v in self.subnode_statements),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        for c in self.subnode_statements:
            c.finalize()
        del self.subnode_statements

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        for element in self.subnode_statements:
            element.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementsFrameAsyncgenBase = StatementChildHavingStatementsTupleMixin
StatementsFrameClassBase = StatementChildHavingStatementsTupleMixin
StatementsFrameCoroutineBase = StatementChildHavingStatementsTupleMixin
StatementsFrameFunctionBase = StatementChildHavingStatementsTupleMixin
StatementsFrameGeneratorBase = StatementChildHavingStatementsTupleMixin
StatementsFrameModuleBase = StatementChildHavingStatementsTupleMixin
StatementsSequenceBase = StatementChildHavingStatementsTupleMixin


class StatementChildrenHavingSubscribedSubscriptOperationMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementDelSubscript

    def __init__(self, subscribed, subscript, source_ref):
        subscribed.parent = self

        self.subnode_subscribed = subscribed

        subscript.parent = self

        self.subnode_subscript = subscript

        StatementBase.__init__(self, source_ref)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_subscribed,
            self.subnode_subscript,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("subscribed", self.subnode_subscribed),
            ("subscript", self.subnode_subscript),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_subscribed
        if old_node is value:
            new_node.parent = self

            self.subnode_subscribed = new_node

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
            "subscribed": self.subnode_subscribed.makeClone(),
            "subscript": self.subnode_subscript.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_subscribed.finalize()
        del self.subnode_subscribed
        self.subnode_subscript.finalize()
        del self.subnode_subscript

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.computeStatementOperation(trace_collection)

    @abstractmethod
    def computeStatementOperation(self, trace_collection):
        """Must be overloaded for non-final node."""

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_subscribed.collectVariableAccesses(emit_read, emit_write)
        self.subnode_subscript.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementDelSubscriptBase = StatementChildrenHavingSubscribedSubscriptOperationMixin


class StatementChildrenHavingTriedStatementsExceptHandlerOptionalStatementsOrNoneBreakHandlerOptionalStatementsOrNoneContinueHandlerOptionalStatementsOrNoneReturnHandlerOptionalStatementsOrNonePostInitMixin(
    StatementBase
):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementTry

    def __init__(
        self,
        tried,
        except_handler,
        break_handler,
        continue_handler,
        return_handler,
        source_ref,
    ):
        tried = checkStatementsSequence(tried)
        tried.parent = self

        self.subnode_tried = tried

        except_handler = checkStatementsSequenceOrNone(except_handler)
        if except_handler is not None:
            except_handler.parent = self

        self.subnode_except_handler = except_handler

        break_handler = checkStatementsSequenceOrNone(break_handler)
        if break_handler is not None:
            break_handler.parent = self

        self.subnode_break_handler = break_handler

        continue_handler = checkStatementsSequenceOrNone(continue_handler)
        if continue_handler is not None:
            continue_handler.parent = self

        self.subnode_continue_handler = continue_handler

        return_handler = checkStatementsSequenceOrNone(return_handler)
        if return_handler is not None:
            return_handler.parent = self

        self.subnode_return_handler = return_handler

        StatementBase.__init__(self, source_ref)

        self.postInitNode()

    @abstractmethod
    def postInitNode(self):
        """For overload"""

    def setChildBreakHandler(self, value):
        value = checkStatementsSequenceOrNone(value)
        if value is not None:
            value.parent = self

        self.subnode_break_handler = value

    def setChildContinueHandler(self, value):
        value = checkStatementsSequenceOrNone(value)
        if value is not None:
            value.parent = self

        self.subnode_continue_handler = value

    def setChildExceptHandler(self, value):
        value = checkStatementsSequenceOrNone(value)
        if value is not None:
            value.parent = self

        self.subnode_except_handler = value

    def setChildReturnHandler(self, value):
        value = checkStatementsSequenceOrNone(value)
        if value is not None:
            value.parent = self

        self.subnode_return_handler = value

    def setChildTried(self, value):
        value = checkStatementsSequence(value)
        value.parent = self

        self.subnode_tried = value

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        result = []
        result.append(self.subnode_tried)
        value = self.subnode_except_handler
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_break_handler
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_continue_handler
        if value is None:
            pass
        else:
            result.append(value)
        value = self.subnode_return_handler
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
            ("tried", self.subnode_tried),
            ("except_handler", self.subnode_except_handler),
            ("break_handler", self.subnode_break_handler),
            ("continue_handler", self.subnode_continue_handler),
            ("return_handler", self.subnode_return_handler),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_tried
        if old_node is value:
            new_node = checkStatementsSequence(new_node)
            new_node.parent = self

            self.subnode_tried = new_node

            return

        value = self.subnode_except_handler
        if old_node is value:
            new_node = checkStatementsSequenceOrNone(new_node)
            if new_node is not None:
                new_node.parent = self

            self.subnode_except_handler = new_node

            return

        value = self.subnode_break_handler
        if old_node is value:
            new_node = checkStatementsSequenceOrNone(new_node)
            if new_node is not None:
                new_node.parent = self

            self.subnode_break_handler = new_node

            return

        value = self.subnode_continue_handler
        if old_node is value:
            new_node = checkStatementsSequenceOrNone(new_node)
            if new_node is not None:
                new_node.parent = self

            self.subnode_continue_handler = new_node

            return

        value = self.subnode_return_handler
        if old_node is value:
            new_node = checkStatementsSequenceOrNone(new_node)
            if new_node is not None:
                new_node.parent = self

            self.subnode_return_handler = new_node

            return

        raise AssertionError("Didn't find child", old_node, "in", self)

    def getCloneArgs(self):
        """Get clones of all children to pass for a new node.

        Needs to make clones of child nodes too.
        """

        values = {
            "tried": self.subnode_tried.makeClone(),
            "except_handler": (
                self.subnode_except_handler.makeClone()
                if self.subnode_except_handler is not None
                else None
            ),
            "break_handler": (
                self.subnode_break_handler.makeClone()
                if self.subnode_break_handler is not None
                else None
            ),
            "continue_handler": (
                self.subnode_continue_handler.makeClone()
                if self.subnode_continue_handler is not None
                else None
            ),
            "return_handler": (
                self.subnode_return_handler.makeClone()
                if self.subnode_return_handler is not None
                else None
            ),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_tried.finalize()
        del self.subnode_tried
        if self.subnode_except_handler is not None:
            self.subnode_except_handler.finalize()
        del self.subnode_except_handler
        if self.subnode_break_handler is not None:
            self.subnode_break_handler.finalize()
        del self.subnode_break_handler
        if self.subnode_continue_handler is not None:
            self.subnode_continue_handler.finalize()
        del self.subnode_continue_handler
        if self.subnode_return_handler is not None:
            self.subnode_return_handler.finalize()
        del self.subnode_return_handler

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_tried.collectVariableAccesses(emit_read, emit_write)
        subnode_except_handler = self.subnode_except_handler

        if subnode_except_handler is not None:
            self.subnode_except_handler.collectVariableAccesses(emit_read, emit_write)
        subnode_break_handler = self.subnode_break_handler

        if subnode_break_handler is not None:
            self.subnode_break_handler.collectVariableAccesses(emit_read, emit_write)
        subnode_continue_handler = self.subnode_continue_handler

        if subnode_continue_handler is not None:
            self.subnode_continue_handler.collectVariableAccesses(emit_read, emit_write)
        subnode_return_handler = self.subnode_return_handler

        if subnode_return_handler is not None:
            self.subnode_return_handler.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementTryBase = StatementChildrenHavingTriedStatementsExceptHandlerOptionalStatementsOrNoneBreakHandlerOptionalStatementsOrNoneContinueHandlerOptionalStatementsOrNoneReturnHandlerOptionalStatementsOrNonePostInitMixin


class StatementChildrenHavingValueDictArgKeyOperationMixin(StatementBase):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    # This is generated for use in
    #   StatementDictOperationSet
    #   StatementDictOperationSetKeyValue

    def __init__(self, value, dict_arg, key, source_ref):
        value.parent = self

        self.subnode_value = value

        dict_arg.parent = self

        self.subnode_dict_arg = dict_arg

        key.parent = self

        self.subnode_key = key

        StatementBase.__init__(self, source_ref)

    def getVisitableNodes(self):
        """The visitable nodes, with tuple values flattened."""

        return (
            self.subnode_value,
            self.subnode_dict_arg,
            self.subnode_key,
        )

    def getVisitableNodesNamed(self):
        """Named children dictionary.

        For use in cloning nodes, debugging and XML output.
        """

        return (
            ("value", self.subnode_value),
            ("dict_arg", self.subnode_dict_arg),
            ("key", self.subnode_key),
        )

    def replaceChild(self, old_node, new_node):
        value = self.subnode_value
        if old_node is value:
            new_node.parent = self

            self.subnode_value = new_node

            return

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
            "value": self.subnode_value.makeClone(),
            "dict_arg": self.subnode_dict_arg.makeClone(),
            "key": self.subnode_key.makeClone(),
        }

        values.update(self.getDetails())

        return values

    def finalize(self):
        del self.parent

        self.subnode_value.finalize()
        del self.subnode_value
        self.subnode_dict_arg.finalize()
        del self.subnode_dict_arg
        self.subnode_key.finalize()
        del self.subnode_key

    def computeStatement(self, trace_collection):
        result, change_tags, change_desc = self.computeStatementSubExpressions(
            trace_collection=trace_collection
        )

        if result is not self:
            return result, change_tags, change_desc

        return self.computeStatementOperation(trace_collection)

    @abstractmethod
    def computeStatementOperation(self, trace_collection):
        """Must be overloaded for non-final node."""

    def collectVariableAccesses(self, emit_read, emit_write):
        """Collect variable reads and writes of child nodes."""

        self.subnode_value.collectVariableAccesses(emit_read, emit_write)
        self.subnode_dict_arg.collectVariableAccesses(emit_read, emit_write)
        self.subnode_key.collectVariableAccesses(emit_read, emit_write)


# Assign the names that are easier to import with a stable name.
StatementDictOperationSetBase = StatementChildrenHavingValueDictArgKeyOperationMixin
StatementDictOperationSetKeyValueBase = (
    StatementChildrenHavingValueDictArgKeyOperationMixin
)

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
