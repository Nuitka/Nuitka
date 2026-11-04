#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# We are not avoiding these in generated code at all
# pylint: disable=I0021,line-too-long,too-many-instance-attributes,too-many-lines
# pylint: disable=too-many-arguments,too-many-return-statements,too-many-statements
# pylint: disable=literal-comparison


"""Value trace merge classes

WARNING, this code is GENERATED. Modify the template ValueTraceMerge.py.j2 instead!

spell-checker: ignore __prepare__ append args autograph buffering capitalize casefold
spell-checker: ignore center chars clear closefd copy count decode default delete dist
spell-checker: ignore distribution_name encode encoding end endswith errors exit_code
spell-checker: ignore expandtabs experimental_attributes experimental_autograph_options
spell-checker: ignore experimental_compile experimental_follow_type_hints
spell-checker: ignore experimental_implements experimental_relax_shapes extend file
spell-checker: ignore fillchar find format format_map formatmap fromkeys func get group
spell-checker: ignore handle has_key haskey index input_signature insert isalnum isalpha
spell-checker: ignore isascii isdecimal isdigit isidentifier islower isnumeric isprintable
spell-checker: ignore isspace istitle isupper item items iterable iteritems iterkeys
spell-checker: ignore itervalues jit_compile join keepends key keys kwargs ljust lower
spell-checker: ignore lstrip maketrans maxsplit mode name new newline object old opener p
spell-checker: ignore package package_or_requirement pairs partition path pop popitem
spell-checker: ignore prefix prepare reduce_retracing remove replace resource
spell-checker: ignore resource_name reverse rfind rindex rjust rpartition rsplit rstrip s
spell-checker: ignore sep setdefault sort split splitlines start startswith stop strip sub
spell-checker: ignore suffix swapcase table tabsize title translate update upper use_errno
spell-checker: ignore use_last_error value values viewitems viewkeys viewvalues width
spell-checker: ignore winmode zfill
"""

# pylint: disable=too-many-branches

from nuitka.Constants import compareConstants
from nuitka.nodes.shapes.ControlFlowDescriptions import (
    ControlFlowDescriptionFullEscape,
)
from nuitka.nodes.shapes.StandardShapes import tshape_unknown
from nuitka.utils.InstanceCounters import counted_init

from .ValueTracesStatic import (
    MustHaveValueQueryContext,
    ValueTraceMergeBase,
    ValueTraceMergeMethodsMixin,
)


class ValueTraceMerge2(ValueTraceMergeMethodsMixin, ValueTraceMergeBase):
    """Merge of 2 traces."""

    __slots__ = (
        "trace1",
        "trace2",
        "must_have_value_state",
    )

    @counted_init
    def __init__(self, trace1, trace2):
        self.owner = trace1.owner

        self.trace1 = trace1
        self.trace2 = trace2

        self.usage_count = 0
        self.name_usage_count = 0
        self.merge_usage_count = 0
        self.must_have_value_state = 0  # unknown

    def getPrevious(self):
        return (
            self.trace1,
            self.trace2,
        )

    def __repr__(self):
        return "<ValueTraceMerge2 of (%s, %s)>" % (
            repr(self.trace1),
            repr(self.trace2),
        )

    def extendPreviousTraces(self, result, seen):
        if self.trace1 not in seen:
            seen.add(self.trace1)
            result.append(self.trace1)
        if self.trace2 not in seen:
            seen.add(self.trace2)
            result.append(self.trace2)

    def isLoopDependent(self):
        state = self.must_have_value_state

        if state is 0:  # unknown
            state = 1  # not loop dependent

            if self.trace1.isLoopDependent() or self.trace2.isLoopDependent():
                state = 2  # loop dependent

            self.must_have_value_state = state

        return state is 2  # loop dependent

    def mustHaveValue(self, context=None):
        state = self.must_have_value_state

        if state is 3:  # must have value
            return True

        if state is 4:  # must not have value
            return False

        loop_dependent = self.isLoopDependent()

        if loop_dependent:
            if context is None:
                context = MustHaveValueQueryContext()
            else:
                cached = context.cache.get(self)

                if cached is not None:
                    return cached

        result = self.trace1.mustHaveValue(context) and self.trace2.mustHaveValue(
            context
        )

        if not loop_dependent:
            self.must_have_value_state = 3 if result else 4
        else:
            context.cache[self] = result

        return result

    def mustNotHaveValue(self):
        return self.trace1.mustNotHaveValue() and self.trace2.mustNotHaveValue()

    def getTypeShape(self):
        type_shape_found = self.trace1.getTypeShape()

        if type_shape_found is tshape_unknown:
            return tshape_unknown

        type_shape = self.trace2.getTypeShape()

        if type_shape is tshape_unknown:
            return tshape_unknown

        if type_shape is not type_shape_found:
            return tshape_unknown

        return type_shape_found

    def getReleaseEscape(self):
        release_escape_found = self.trace1.getReleaseEscape()

        if release_escape_found is ControlFlowDescriptionFullEscape:
            return ControlFlowDescriptionFullEscape

        release_escape = self.trace2.getReleaseEscape()

        if release_escape is ControlFlowDescriptionFullEscape:
            return ControlFlowDescriptionFullEscape

        if release_escape is not release_escape_found:
            return ControlFlowDescriptionFullEscape

        return release_escape_found

    def getAttributeNodeVeryTrustedMatching(self, visited):
        if self in visited:
            return Ellipsis

        visited.add(self)
        result = Ellipsis

        try:
            node = self.trace1.getAttributeNodeVeryTrustedMatching(visited)

            if node is None:
                return None

            if node is not Ellipsis:
                if result is Ellipsis:
                    result = node
                elif result is not node:
                    return None
            node = self.trace2.getAttributeNodeVeryTrustedMatching(visited)

            if node is None:
                return None

            if node is not Ellipsis:
                if result is Ellipsis:
                    result = node
                elif result is not node:
                    return None
        finally:
            visited.remove(self)

        if result is Ellipsis:
            return None

        return result

    def hasShapeListExact(self):
        return self.trace1.hasShapeListExact() and self.trace2.hasShapeListExact()

    def hasShapeDictionaryExact(self):
        return (
            self.trace1.hasShapeDictionaryExact()
            and self.trace2.hasShapeDictionaryExact()
        )

    def getTruthValue(self):
        truth_value = self.trace1.getTruthValue()

        if truth_value is None:
            return None

        result = truth_value

        truth_value = self.trace2.getTruthValue()

        if truth_value is not result:
            return None
        return result

    def getExpectedValue(self):
        expected_available, expected_value = self.trace1.getExpectedValue()

        if not expected_available:
            return False, None

        result = expected_value

        expected_available, expected_value = self.trace2.getExpectedValue()

        if not expected_available:
            return False, None

        if not compareConstants(result, expected_value):
            return False, None

        return True, result

    def compareValueTrace(self, other):
        if type(other) is not ValueTraceMerge2:
            return False

        return self.trace1.compareValueTrace(
            other.trace1
        ) and self.trace2.compareValueTrace(other.trace2)

    def isUnchangedResumeTrace(self, loop_entry_trace):
        return self.trace1.isUnchangedResumeTrace(
            loop_entry_trace
        ) and self.trace2.isUnchangedResumeTrace(loop_entry_trace)

    def addNameUsage(self):
        self.usage_count += 1
        self.name_usage_count += 1

        if self.name_usage_count <= 2:
            self.trace1.addNameUsage()
            self.trace2.addNameUsage()

    def removeNameUsage(self):
        self.usage_count -= 1
        self.name_usage_count -= 1

        if self.name_usage_count < 2:
            self.trace1.removeNameUsage()
            self.trace2.removeNameUsage()

    def addUsage(self):
        self.usage_count += 1

        if self.usage_count is 1:
            self.trace1.addMergeUsage()
            self.trace2.addMergeUsage()

    def removeUsage(self):
        self.usage_count -= 1

        if self.usage_count is 0:
            self.trace1.removeMergeUsage()
            self.trace2.removeMergeUsage()

    def addMergeUsage(self):
        self.addUsage()
        self.merge_usage_count += 1

    def removeMergeUsage(self):
        self.removeUsage()
        self.merge_usage_count -= 1


class ValueTraceMerge3(ValueTraceMergeMethodsMixin, ValueTraceMergeBase):
    """Merge of 3 traces."""

    __slots__ = (
        "trace1",
        "trace2",
        "trace3",
        "must_have_value_state",
    )

    @counted_init
    def __init__(self, trace1, trace2, trace3):
        self.owner = trace1.owner

        self.trace1 = trace1
        self.trace2 = trace2
        self.trace3 = trace3

        self.usage_count = 0
        self.name_usage_count = 0
        self.merge_usage_count = 0
        self.must_have_value_state = 0  # unknown

    def getPrevious(self):
        return (
            self.trace1,
            self.trace2,
            self.trace3,
        )

    def __repr__(self):
        return "<ValueTraceMerge3 of (%s, %s, %s)>" % (
            repr(self.trace1),
            repr(self.trace2),
            repr(self.trace3),
        )

    def extendPreviousTraces(self, result, seen):
        if self.trace1 not in seen:
            seen.add(self.trace1)
            result.append(self.trace1)
        if self.trace2 not in seen:
            seen.add(self.trace2)
            result.append(self.trace2)
        if self.trace3 not in seen:
            seen.add(self.trace3)
            result.append(self.trace3)

    def isLoopDependent(self):
        state = self.must_have_value_state

        if state is 0:  # unknown
            state = 1  # not loop dependent

            if (
                self.trace1.isLoopDependent()
                or self.trace2.isLoopDependent()
                or self.trace3.isLoopDependent()
            ):
                state = 2  # loop dependent

            self.must_have_value_state = state

        return state is 2  # loop dependent

    def mustHaveValue(self, context=None):
        state = self.must_have_value_state

        if state is 3:  # must have value
            return True

        if state is 4:  # must not have value
            return False

        loop_dependent = self.isLoopDependent()

        if loop_dependent:
            if context is None:
                context = MustHaveValueQueryContext()
            else:
                cached = context.cache.get(self)

                if cached is not None:
                    return cached

        result = (
            self.trace1.mustHaveValue(context)
            and self.trace2.mustHaveValue(context)
            and self.trace3.mustHaveValue(context)
        )

        if not loop_dependent:
            self.must_have_value_state = 3 if result else 4
        else:
            context.cache[self] = result

        return result

    def mustNotHaveValue(self):
        return (
            self.trace1.mustNotHaveValue()
            and self.trace2.mustNotHaveValue()
            and self.trace3.mustNotHaveValue()
        )

    def getTypeShape(self):
        type_shape_found = self.trace1.getTypeShape()

        if type_shape_found is tshape_unknown:
            return tshape_unknown

        type_shape = self.trace2.getTypeShape()

        if type_shape is tshape_unknown:
            return tshape_unknown

        if type_shape is not type_shape_found:
            return tshape_unknown

        type_shape = self.trace3.getTypeShape()

        if type_shape is tshape_unknown:
            return tshape_unknown

        if type_shape is not type_shape_found:
            return tshape_unknown

        return type_shape_found

    def getReleaseEscape(self):
        release_escape_found = self.trace1.getReleaseEscape()

        if release_escape_found is ControlFlowDescriptionFullEscape:
            return ControlFlowDescriptionFullEscape

        release_escape = self.trace2.getReleaseEscape()

        if release_escape is ControlFlowDescriptionFullEscape:
            return ControlFlowDescriptionFullEscape

        if release_escape is not release_escape_found:
            return ControlFlowDescriptionFullEscape

        release_escape = self.trace3.getReleaseEscape()

        if release_escape is ControlFlowDescriptionFullEscape:
            return ControlFlowDescriptionFullEscape

        if release_escape is not release_escape_found:
            return ControlFlowDescriptionFullEscape

        return release_escape_found

    def getAttributeNodeVeryTrustedMatching(self, visited):
        if self in visited:
            return Ellipsis

        visited.add(self)
        result = Ellipsis

        try:
            node = self.trace1.getAttributeNodeVeryTrustedMatching(visited)

            if node is None:
                return None

            if node is not Ellipsis:
                if result is Ellipsis:
                    result = node
                elif result is not node:
                    return None
            node = self.trace2.getAttributeNodeVeryTrustedMatching(visited)

            if node is None:
                return None

            if node is not Ellipsis:
                if result is Ellipsis:
                    result = node
                elif result is not node:
                    return None
            node = self.trace3.getAttributeNodeVeryTrustedMatching(visited)

            if node is None:
                return None

            if node is not Ellipsis:
                if result is Ellipsis:
                    result = node
                elif result is not node:
                    return None
        finally:
            visited.remove(self)

        if result is Ellipsis:
            return None

        return result

    def hasShapeListExact(self):
        return (
            self.trace1.hasShapeListExact()
            and self.trace2.hasShapeListExact()
            and self.trace3.hasShapeListExact()
        )

    def hasShapeDictionaryExact(self):
        return (
            self.trace1.hasShapeDictionaryExact()
            and self.trace2.hasShapeDictionaryExact()
            and self.trace3.hasShapeDictionaryExact()
        )

    def getTruthValue(self):
        truth_value = self.trace1.getTruthValue()

        if truth_value is None:
            return None

        result = truth_value

        truth_value = self.trace2.getTruthValue()

        if truth_value is not result:
            return None
        truth_value = self.trace3.getTruthValue()

        if truth_value is not result:
            return None
        return result

    def getExpectedValue(self):
        expected_available, expected_value = self.trace1.getExpectedValue()

        if not expected_available:
            return False, None

        result = expected_value

        expected_available, expected_value = self.trace2.getExpectedValue()

        if not expected_available:
            return False, None

        if not compareConstants(result, expected_value):
            return False, None

        expected_available, expected_value = self.trace3.getExpectedValue()

        if not expected_available:
            return False, None

        if not compareConstants(result, expected_value):
            return False, None

        return True, result

    def compareValueTrace(self, other):
        if type(other) is not ValueTraceMerge3:
            return False

        return (
            self.trace1.compareValueTrace(other.trace1)
            and self.trace2.compareValueTrace(other.trace2)
            and self.trace3.compareValueTrace(other.trace3)
        )

    def isUnchangedResumeTrace(self, loop_entry_trace):
        return (
            self.trace1.isUnchangedResumeTrace(loop_entry_trace)
            and self.trace2.isUnchangedResumeTrace(loop_entry_trace)
            and self.trace3.isUnchangedResumeTrace(loop_entry_trace)
        )

    def addNameUsage(self):
        self.usage_count += 1
        self.name_usage_count += 1

        if self.name_usage_count <= 2:
            self.trace1.addNameUsage()
            self.trace2.addNameUsage()
            self.trace3.addNameUsage()

    def removeNameUsage(self):
        self.usage_count -= 1
        self.name_usage_count -= 1

        if self.name_usage_count < 2:
            self.trace1.removeNameUsage()
            self.trace2.removeNameUsage()
            self.trace3.removeNameUsage()

    def addUsage(self):
        self.usage_count += 1

        if self.usage_count is 1:
            self.trace1.addMergeUsage()
            self.trace2.addMergeUsage()
            self.trace3.addMergeUsage()

    def removeUsage(self):
        self.usage_count -= 1

        if self.usage_count is 0:
            self.trace1.removeMergeUsage()
            self.trace2.removeMergeUsage()
            self.trace3.removeMergeUsage()

    def addMergeUsage(self):
        self.addUsage()
        self.merge_usage_count += 1

    def removeMergeUsage(self):
        self.removeUsage()
        self.merge_usage_count -= 1


class ValueTraceMerge4(ValueTraceMergeMethodsMixin, ValueTraceMergeBase):
    """Merge of 4 traces."""

    __slots__ = (
        "trace1",
        "trace2",
        "trace3",
        "trace4",
        "must_have_value_state",
    )

    @counted_init
    def __init__(self, trace1, trace2, trace3, trace4):
        self.owner = trace1.owner

        self.trace1 = trace1
        self.trace2 = trace2
        self.trace3 = trace3
        self.trace4 = trace4

        self.usage_count = 0
        self.name_usage_count = 0
        self.merge_usage_count = 0
        self.must_have_value_state = 0  # unknown

    def getPrevious(self):
        return (
            self.trace1,
            self.trace2,
            self.trace3,
            self.trace4,
        )

    def __repr__(self):
        return "<ValueTraceMerge4 of (%s, %s, %s, %s)>" % (
            repr(self.trace1),
            repr(self.trace2),
            repr(self.trace3),
            repr(self.trace4),
        )

    def extendPreviousTraces(self, result, seen):
        if self.trace1 not in seen:
            seen.add(self.trace1)
            result.append(self.trace1)
        if self.trace2 not in seen:
            seen.add(self.trace2)
            result.append(self.trace2)
        if self.trace3 not in seen:
            seen.add(self.trace3)
            result.append(self.trace3)
        if self.trace4 not in seen:
            seen.add(self.trace4)
            result.append(self.trace4)

    def isLoopDependent(self):
        state = self.must_have_value_state

        if state is 0:  # unknown
            state = 1  # not loop dependent

            if (
                self.trace1.isLoopDependent()
                or self.trace2.isLoopDependent()
                or self.trace3.isLoopDependent()
                or self.trace4.isLoopDependent()
            ):
                state = 2  # loop dependent

            self.must_have_value_state = state

        return state is 2  # loop dependent

    def mustHaveValue(self, context=None):
        state = self.must_have_value_state

        if state is 3:  # must have value
            return True

        if state is 4:  # must not have value
            return False

        loop_dependent = self.isLoopDependent()

        if loop_dependent:
            if context is None:
                context = MustHaveValueQueryContext()
            else:
                cached = context.cache.get(self)

                if cached is not None:
                    return cached

        result = (
            self.trace1.mustHaveValue(context)
            and self.trace2.mustHaveValue(context)
            and self.trace3.mustHaveValue(context)
            and self.trace4.mustHaveValue(context)
        )

        if not loop_dependent:
            self.must_have_value_state = 3 if result else 4
        else:
            context.cache[self] = result

        return result

    def mustNotHaveValue(self):
        return (
            self.trace1.mustNotHaveValue()
            and self.trace2.mustNotHaveValue()
            and self.trace3.mustNotHaveValue()
            and self.trace4.mustNotHaveValue()
        )

    def getTypeShape(self):
        type_shape_found = self.trace1.getTypeShape()

        if type_shape_found is tshape_unknown:
            return tshape_unknown

        type_shape = self.trace2.getTypeShape()

        if type_shape is tshape_unknown:
            return tshape_unknown

        if type_shape is not type_shape_found:
            return tshape_unknown

        type_shape = self.trace3.getTypeShape()

        if type_shape is tshape_unknown:
            return tshape_unknown

        if type_shape is not type_shape_found:
            return tshape_unknown

        type_shape = self.trace4.getTypeShape()

        if type_shape is tshape_unknown:
            return tshape_unknown

        if type_shape is not type_shape_found:
            return tshape_unknown

        return type_shape_found

    def getReleaseEscape(self):
        release_escape_found = self.trace1.getReleaseEscape()

        if release_escape_found is ControlFlowDescriptionFullEscape:
            return ControlFlowDescriptionFullEscape

        release_escape = self.trace2.getReleaseEscape()

        if release_escape is ControlFlowDescriptionFullEscape:
            return ControlFlowDescriptionFullEscape

        if release_escape is not release_escape_found:
            return ControlFlowDescriptionFullEscape

        release_escape = self.trace3.getReleaseEscape()

        if release_escape is ControlFlowDescriptionFullEscape:
            return ControlFlowDescriptionFullEscape

        if release_escape is not release_escape_found:
            return ControlFlowDescriptionFullEscape

        release_escape = self.trace4.getReleaseEscape()

        if release_escape is ControlFlowDescriptionFullEscape:
            return ControlFlowDescriptionFullEscape

        if release_escape is not release_escape_found:
            return ControlFlowDescriptionFullEscape

        return release_escape_found

    def getAttributeNodeVeryTrustedMatching(self, visited):
        if self in visited:
            return Ellipsis

        visited.add(self)
        result = Ellipsis

        try:
            node = self.trace1.getAttributeNodeVeryTrustedMatching(visited)

            if node is None:
                return None

            if node is not Ellipsis:
                if result is Ellipsis:
                    result = node
                elif result is not node:
                    return None
            node = self.trace2.getAttributeNodeVeryTrustedMatching(visited)

            if node is None:
                return None

            if node is not Ellipsis:
                if result is Ellipsis:
                    result = node
                elif result is not node:
                    return None
            node = self.trace3.getAttributeNodeVeryTrustedMatching(visited)

            if node is None:
                return None

            if node is not Ellipsis:
                if result is Ellipsis:
                    result = node
                elif result is not node:
                    return None
            node = self.trace4.getAttributeNodeVeryTrustedMatching(visited)

            if node is None:
                return None

            if node is not Ellipsis:
                if result is Ellipsis:
                    result = node
                elif result is not node:
                    return None
        finally:
            visited.remove(self)

        if result is Ellipsis:
            return None

        return result

    def hasShapeListExact(self):
        return (
            self.trace1.hasShapeListExact()
            and self.trace2.hasShapeListExact()
            and self.trace3.hasShapeListExact()
            and self.trace4.hasShapeListExact()
        )

    def hasShapeDictionaryExact(self):
        return (
            self.trace1.hasShapeDictionaryExact()
            and self.trace2.hasShapeDictionaryExact()
            and self.trace3.hasShapeDictionaryExact()
            and self.trace4.hasShapeDictionaryExact()
        )

    def getTruthValue(self):
        truth_value = self.trace1.getTruthValue()

        if truth_value is None:
            return None

        result = truth_value

        truth_value = self.trace2.getTruthValue()

        if truth_value is not result:
            return None
        truth_value = self.trace3.getTruthValue()

        if truth_value is not result:
            return None
        truth_value = self.trace4.getTruthValue()

        if truth_value is not result:
            return None
        return result

    def getExpectedValue(self):
        expected_available, expected_value = self.trace1.getExpectedValue()

        if not expected_available:
            return False, None

        result = expected_value

        expected_available, expected_value = self.trace2.getExpectedValue()

        if not expected_available:
            return False, None

        if not compareConstants(result, expected_value):
            return False, None

        expected_available, expected_value = self.trace3.getExpectedValue()

        if not expected_available:
            return False, None

        if not compareConstants(result, expected_value):
            return False, None

        expected_available, expected_value = self.trace4.getExpectedValue()

        if not expected_available:
            return False, None

        if not compareConstants(result, expected_value):
            return False, None

        return True, result

    def compareValueTrace(self, other):
        if type(other) is not ValueTraceMerge4:
            return False

        return (
            self.trace1.compareValueTrace(other.trace1)
            and self.trace2.compareValueTrace(other.trace2)
            and self.trace3.compareValueTrace(other.trace3)
            and self.trace4.compareValueTrace(other.trace4)
        )

    def isUnchangedResumeTrace(self, loop_entry_trace):
        return (
            self.trace1.isUnchangedResumeTrace(loop_entry_trace)
            and self.trace2.isUnchangedResumeTrace(loop_entry_trace)
            and self.trace3.isUnchangedResumeTrace(loop_entry_trace)
            and self.trace4.isUnchangedResumeTrace(loop_entry_trace)
        )

    def addNameUsage(self):
        self.usage_count += 1
        self.name_usage_count += 1

        if self.name_usage_count <= 2:
            self.trace1.addNameUsage()
            self.trace2.addNameUsage()
            self.trace3.addNameUsage()
            self.trace4.addNameUsage()

    def removeNameUsage(self):
        self.usage_count -= 1
        self.name_usage_count -= 1

        if self.name_usage_count < 2:
            self.trace1.removeNameUsage()
            self.trace2.removeNameUsage()
            self.trace3.removeNameUsage()
            self.trace4.removeNameUsage()

    def addUsage(self):
        self.usage_count += 1

        if self.usage_count is 1:
            self.trace1.addMergeUsage()
            self.trace2.addMergeUsage()
            self.trace3.addMergeUsage()
            self.trace4.addMergeUsage()

    def removeUsage(self):
        self.usage_count -= 1

        if self.usage_count is 0:
            self.trace1.removeMergeUsage()
            self.trace2.removeMergeUsage()
            self.trace3.removeMergeUsage()
            self.trace4.removeMergeUsage()

    def addMergeUsage(self):
        self.addUsage()
        self.merge_usage_count += 1

    def removeMergeUsage(self):
        self.removeUsage()
        self.merge_usage_count -= 1


class ValueTraceMerge5(ValueTraceMergeMethodsMixin, ValueTraceMergeBase):
    """Merge of 5 traces."""

    __slots__ = (
        "trace1",
        "trace2",
        "trace3",
        "trace4",
        "trace5",
        "must_have_value_state",
    )

    @counted_init
    def __init__(self, trace1, trace2, trace3, trace4, trace5):
        self.owner = trace1.owner

        self.trace1 = trace1
        self.trace2 = trace2
        self.trace3 = trace3
        self.trace4 = trace4
        self.trace5 = trace5

        self.usage_count = 0
        self.name_usage_count = 0
        self.merge_usage_count = 0
        self.must_have_value_state = 0  # unknown

    def getPrevious(self):
        return (
            self.trace1,
            self.trace2,
            self.trace3,
            self.trace4,
            self.trace5,
        )

    def __repr__(self):
        return "<ValueTraceMerge5 of (%s, %s, %s, %s, %s)>" % (
            repr(self.trace1),
            repr(self.trace2),
            repr(self.trace3),
            repr(self.trace4),
            repr(self.trace5),
        )

    def extendPreviousTraces(self, result, seen):
        if self.trace1 not in seen:
            seen.add(self.trace1)
            result.append(self.trace1)
        if self.trace2 not in seen:
            seen.add(self.trace2)
            result.append(self.trace2)
        if self.trace3 not in seen:
            seen.add(self.trace3)
            result.append(self.trace3)
        if self.trace4 not in seen:
            seen.add(self.trace4)
            result.append(self.trace4)
        if self.trace5 not in seen:
            seen.add(self.trace5)
            result.append(self.trace5)

    def isLoopDependent(self):
        state = self.must_have_value_state

        if state is 0:  # unknown
            state = 1  # not loop dependent

            if (
                self.trace1.isLoopDependent()
                or self.trace2.isLoopDependent()
                or self.trace3.isLoopDependent()
                or self.trace4.isLoopDependent()
                or self.trace5.isLoopDependent()
            ):
                state = 2  # loop dependent

            self.must_have_value_state = state

        return state is 2  # loop dependent

    def mustHaveValue(self, context=None):
        state = self.must_have_value_state

        if state is 3:  # must have value
            return True

        if state is 4:  # must not have value
            return False

        loop_dependent = self.isLoopDependent()

        if loop_dependent:
            if context is None:
                context = MustHaveValueQueryContext()
            else:
                cached = context.cache.get(self)

                if cached is not None:
                    return cached

        result = (
            self.trace1.mustHaveValue(context)
            and self.trace2.mustHaveValue(context)
            and self.trace3.mustHaveValue(context)
            and self.trace4.mustHaveValue(context)
            and self.trace5.mustHaveValue(context)
        )

        if not loop_dependent:
            self.must_have_value_state = 3 if result else 4
        else:
            context.cache[self] = result

        return result

    def mustNotHaveValue(self):
        return (
            self.trace1.mustNotHaveValue()
            and self.trace2.mustNotHaveValue()
            and self.trace3.mustNotHaveValue()
            and self.trace4.mustNotHaveValue()
            and self.trace5.mustNotHaveValue()
        )

    def getTypeShape(self):
        type_shape_found = self.trace1.getTypeShape()

        if type_shape_found is tshape_unknown:
            return tshape_unknown

        type_shape = self.trace2.getTypeShape()

        if type_shape is tshape_unknown:
            return tshape_unknown

        if type_shape is not type_shape_found:
            return tshape_unknown

        type_shape = self.trace3.getTypeShape()

        if type_shape is tshape_unknown:
            return tshape_unknown

        if type_shape is not type_shape_found:
            return tshape_unknown

        type_shape = self.trace4.getTypeShape()

        if type_shape is tshape_unknown:
            return tshape_unknown

        if type_shape is not type_shape_found:
            return tshape_unknown

        type_shape = self.trace5.getTypeShape()

        if type_shape is tshape_unknown:
            return tshape_unknown

        if type_shape is not type_shape_found:
            return tshape_unknown

        return type_shape_found

    def getReleaseEscape(self):
        release_escape_found = self.trace1.getReleaseEscape()

        if release_escape_found is ControlFlowDescriptionFullEscape:
            return ControlFlowDescriptionFullEscape

        release_escape = self.trace2.getReleaseEscape()

        if release_escape is ControlFlowDescriptionFullEscape:
            return ControlFlowDescriptionFullEscape

        if release_escape is not release_escape_found:
            return ControlFlowDescriptionFullEscape

        release_escape = self.trace3.getReleaseEscape()

        if release_escape is ControlFlowDescriptionFullEscape:
            return ControlFlowDescriptionFullEscape

        if release_escape is not release_escape_found:
            return ControlFlowDescriptionFullEscape

        release_escape = self.trace4.getReleaseEscape()

        if release_escape is ControlFlowDescriptionFullEscape:
            return ControlFlowDescriptionFullEscape

        if release_escape is not release_escape_found:
            return ControlFlowDescriptionFullEscape

        release_escape = self.trace5.getReleaseEscape()

        if release_escape is ControlFlowDescriptionFullEscape:
            return ControlFlowDescriptionFullEscape

        if release_escape is not release_escape_found:
            return ControlFlowDescriptionFullEscape

        return release_escape_found

    def getAttributeNodeVeryTrustedMatching(self, visited):
        if self in visited:
            return Ellipsis

        visited.add(self)
        result = Ellipsis

        try:
            node = self.trace1.getAttributeNodeVeryTrustedMatching(visited)

            if node is None:
                return None

            if node is not Ellipsis:
                if result is Ellipsis:
                    result = node
                elif result is not node:
                    return None
            node = self.trace2.getAttributeNodeVeryTrustedMatching(visited)

            if node is None:
                return None

            if node is not Ellipsis:
                if result is Ellipsis:
                    result = node
                elif result is not node:
                    return None
            node = self.trace3.getAttributeNodeVeryTrustedMatching(visited)

            if node is None:
                return None

            if node is not Ellipsis:
                if result is Ellipsis:
                    result = node
                elif result is not node:
                    return None
            node = self.trace4.getAttributeNodeVeryTrustedMatching(visited)

            if node is None:
                return None

            if node is not Ellipsis:
                if result is Ellipsis:
                    result = node
                elif result is not node:
                    return None
            node = self.trace5.getAttributeNodeVeryTrustedMatching(visited)

            if node is None:
                return None

            if node is not Ellipsis:
                if result is Ellipsis:
                    result = node
                elif result is not node:
                    return None
        finally:
            visited.remove(self)

        if result is Ellipsis:
            return None

        return result

    def hasShapeListExact(self):
        return (
            self.trace1.hasShapeListExact()
            and self.trace2.hasShapeListExact()
            and self.trace3.hasShapeListExact()
            and self.trace4.hasShapeListExact()
            and self.trace5.hasShapeListExact()
        )

    def hasShapeDictionaryExact(self):
        return (
            self.trace1.hasShapeDictionaryExact()
            and self.trace2.hasShapeDictionaryExact()
            and self.trace3.hasShapeDictionaryExact()
            and self.trace4.hasShapeDictionaryExact()
            and self.trace5.hasShapeDictionaryExact()
        )

    def getTruthValue(self):
        truth_value = self.trace1.getTruthValue()

        if truth_value is None:
            return None

        result = truth_value

        truth_value = self.trace2.getTruthValue()

        if truth_value is not result:
            return None
        truth_value = self.trace3.getTruthValue()

        if truth_value is not result:
            return None
        truth_value = self.trace4.getTruthValue()

        if truth_value is not result:
            return None
        truth_value = self.trace5.getTruthValue()

        if truth_value is not result:
            return None
        return result

    def getExpectedValue(self):
        expected_available, expected_value = self.trace1.getExpectedValue()

        if not expected_available:
            return False, None

        result = expected_value

        expected_available, expected_value = self.trace2.getExpectedValue()

        if not expected_available:
            return False, None

        if not compareConstants(result, expected_value):
            return False, None

        expected_available, expected_value = self.trace3.getExpectedValue()

        if not expected_available:
            return False, None

        if not compareConstants(result, expected_value):
            return False, None

        expected_available, expected_value = self.trace4.getExpectedValue()

        if not expected_available:
            return False, None

        if not compareConstants(result, expected_value):
            return False, None

        expected_available, expected_value = self.trace5.getExpectedValue()

        if not expected_available:
            return False, None

        if not compareConstants(result, expected_value):
            return False, None

        return True, result

    def compareValueTrace(self, other):
        if type(other) is not ValueTraceMerge5:
            return False

        return (
            self.trace1.compareValueTrace(other.trace1)
            and self.trace2.compareValueTrace(other.trace2)
            and self.trace3.compareValueTrace(other.trace3)
            and self.trace4.compareValueTrace(other.trace4)
            and self.trace5.compareValueTrace(other.trace5)
        )

    def isUnchangedResumeTrace(self, loop_entry_trace):
        return (
            self.trace1.isUnchangedResumeTrace(loop_entry_trace)
            and self.trace2.isUnchangedResumeTrace(loop_entry_trace)
            and self.trace3.isUnchangedResumeTrace(loop_entry_trace)
            and self.trace4.isUnchangedResumeTrace(loop_entry_trace)
            and self.trace5.isUnchangedResumeTrace(loop_entry_trace)
        )

    def addNameUsage(self):
        self.usage_count += 1
        self.name_usage_count += 1

        if self.name_usage_count <= 2:
            self.trace1.addNameUsage()
            self.trace2.addNameUsage()
            self.trace3.addNameUsage()
            self.trace4.addNameUsage()
            self.trace5.addNameUsage()

    def removeNameUsage(self):
        self.usage_count -= 1
        self.name_usage_count -= 1

        if self.name_usage_count < 2:
            self.trace1.removeNameUsage()
            self.trace2.removeNameUsage()
            self.trace3.removeNameUsage()
            self.trace4.removeNameUsage()
            self.trace5.removeNameUsage()

    def addUsage(self):
        self.usage_count += 1

        if self.usage_count is 1:
            self.trace1.addMergeUsage()
            self.trace2.addMergeUsage()
            self.trace3.addMergeUsage()
            self.trace4.addMergeUsage()
            self.trace5.addMergeUsage()

    def removeUsage(self):
        self.usage_count -= 1

        if self.usage_count is 0:
            self.trace1.removeMergeUsage()
            self.trace2.removeMergeUsage()
            self.trace3.removeMergeUsage()
            self.trace4.removeMergeUsage()
            self.trace5.removeMergeUsage()

    def addMergeUsage(self):
        self.addUsage()
        self.merge_usage_count += 1

    def removeMergeUsage(self):
        self.removeUsage()
        self.merge_usage_count -= 1


class ValueTraceMerge6(ValueTraceMergeMethodsMixin, ValueTraceMergeBase):
    """Merge of 6 traces."""

    __slots__ = (
        "trace1",
        "trace2",
        "trace3",
        "trace4",
        "trace5",
        "trace6",
        "must_have_value_state",
    )

    @counted_init
    def __init__(self, trace1, trace2, trace3, trace4, trace5, trace6):
        self.owner = trace1.owner

        self.trace1 = trace1
        self.trace2 = trace2
        self.trace3 = trace3
        self.trace4 = trace4
        self.trace5 = trace5
        self.trace6 = trace6

        self.usage_count = 0
        self.name_usage_count = 0
        self.merge_usage_count = 0
        self.must_have_value_state = 0  # unknown

    def getPrevious(self):
        return (
            self.trace1,
            self.trace2,
            self.trace3,
            self.trace4,
            self.trace5,
            self.trace6,
        )

    def __repr__(self):
        return "<ValueTraceMerge6 of (%s, %s, %s, %s, %s, %s)>" % (
            repr(self.trace1),
            repr(self.trace2),
            repr(self.trace3),
            repr(self.trace4),
            repr(self.trace5),
            repr(self.trace6),
        )

    def extendPreviousTraces(self, result, seen):
        if self.trace1 not in seen:
            seen.add(self.trace1)
            result.append(self.trace1)
        if self.trace2 not in seen:
            seen.add(self.trace2)
            result.append(self.trace2)
        if self.trace3 not in seen:
            seen.add(self.trace3)
            result.append(self.trace3)
        if self.trace4 not in seen:
            seen.add(self.trace4)
            result.append(self.trace4)
        if self.trace5 not in seen:
            seen.add(self.trace5)
            result.append(self.trace5)
        if self.trace6 not in seen:
            seen.add(self.trace6)
            result.append(self.trace6)

    def isLoopDependent(self):
        state = self.must_have_value_state

        if state is 0:  # unknown
            state = 1  # not loop dependent

            if (
                self.trace1.isLoopDependent()
                or self.trace2.isLoopDependent()
                or self.trace3.isLoopDependent()
                or self.trace4.isLoopDependent()
                or self.trace5.isLoopDependent()
                or self.trace6.isLoopDependent()
            ):
                state = 2  # loop dependent

            self.must_have_value_state = state

        return state is 2  # loop dependent

    def mustHaveValue(self, context=None):
        state = self.must_have_value_state

        if state is 3:  # must have value
            return True

        if state is 4:  # must not have value
            return False

        loop_dependent = self.isLoopDependent()

        if loop_dependent:
            if context is None:
                context = MustHaveValueQueryContext()
            else:
                cached = context.cache.get(self)

                if cached is not None:
                    return cached

        result = (
            self.trace1.mustHaveValue(context)
            and self.trace2.mustHaveValue(context)
            and self.trace3.mustHaveValue(context)
            and self.trace4.mustHaveValue(context)
            and self.trace5.mustHaveValue(context)
            and self.trace6.mustHaveValue(context)
        )

        if not loop_dependent:
            self.must_have_value_state = 3 if result else 4
        else:
            context.cache[self] = result

        return result

    def mustNotHaveValue(self):
        return (
            self.trace1.mustNotHaveValue()
            and self.trace2.mustNotHaveValue()
            and self.trace3.mustNotHaveValue()
            and self.trace4.mustNotHaveValue()
            and self.trace5.mustNotHaveValue()
            and self.trace6.mustNotHaveValue()
        )

    def getTypeShape(self):
        type_shape_found = self.trace1.getTypeShape()

        if type_shape_found is tshape_unknown:
            return tshape_unknown

        type_shape = self.trace2.getTypeShape()

        if type_shape is tshape_unknown:
            return tshape_unknown

        if type_shape is not type_shape_found:
            return tshape_unknown

        type_shape = self.trace3.getTypeShape()

        if type_shape is tshape_unknown:
            return tshape_unknown

        if type_shape is not type_shape_found:
            return tshape_unknown

        type_shape = self.trace4.getTypeShape()

        if type_shape is tshape_unknown:
            return tshape_unknown

        if type_shape is not type_shape_found:
            return tshape_unknown

        type_shape = self.trace5.getTypeShape()

        if type_shape is tshape_unknown:
            return tshape_unknown

        if type_shape is not type_shape_found:
            return tshape_unknown

        type_shape = self.trace6.getTypeShape()

        if type_shape is tshape_unknown:
            return tshape_unknown

        if type_shape is not type_shape_found:
            return tshape_unknown

        return type_shape_found

    def getReleaseEscape(self):
        release_escape_found = self.trace1.getReleaseEscape()

        if release_escape_found is ControlFlowDescriptionFullEscape:
            return ControlFlowDescriptionFullEscape

        release_escape = self.trace2.getReleaseEscape()

        if release_escape is ControlFlowDescriptionFullEscape:
            return ControlFlowDescriptionFullEscape

        if release_escape is not release_escape_found:
            return ControlFlowDescriptionFullEscape

        release_escape = self.trace3.getReleaseEscape()

        if release_escape is ControlFlowDescriptionFullEscape:
            return ControlFlowDescriptionFullEscape

        if release_escape is not release_escape_found:
            return ControlFlowDescriptionFullEscape

        release_escape = self.trace4.getReleaseEscape()

        if release_escape is ControlFlowDescriptionFullEscape:
            return ControlFlowDescriptionFullEscape

        if release_escape is not release_escape_found:
            return ControlFlowDescriptionFullEscape

        release_escape = self.trace5.getReleaseEscape()

        if release_escape is ControlFlowDescriptionFullEscape:
            return ControlFlowDescriptionFullEscape

        if release_escape is not release_escape_found:
            return ControlFlowDescriptionFullEscape

        release_escape = self.trace6.getReleaseEscape()

        if release_escape is ControlFlowDescriptionFullEscape:
            return ControlFlowDescriptionFullEscape

        if release_escape is not release_escape_found:
            return ControlFlowDescriptionFullEscape

        return release_escape_found

    def getAttributeNodeVeryTrustedMatching(self, visited):
        if self in visited:
            return Ellipsis

        visited.add(self)
        result = Ellipsis

        try:
            node = self.trace1.getAttributeNodeVeryTrustedMatching(visited)

            if node is None:
                return None

            if node is not Ellipsis:
                if result is Ellipsis:
                    result = node
                elif result is not node:
                    return None
            node = self.trace2.getAttributeNodeVeryTrustedMatching(visited)

            if node is None:
                return None

            if node is not Ellipsis:
                if result is Ellipsis:
                    result = node
                elif result is not node:
                    return None
            node = self.trace3.getAttributeNodeVeryTrustedMatching(visited)

            if node is None:
                return None

            if node is not Ellipsis:
                if result is Ellipsis:
                    result = node
                elif result is not node:
                    return None
            node = self.trace4.getAttributeNodeVeryTrustedMatching(visited)

            if node is None:
                return None

            if node is not Ellipsis:
                if result is Ellipsis:
                    result = node
                elif result is not node:
                    return None
            node = self.trace5.getAttributeNodeVeryTrustedMatching(visited)

            if node is None:
                return None

            if node is not Ellipsis:
                if result is Ellipsis:
                    result = node
                elif result is not node:
                    return None
            node = self.trace6.getAttributeNodeVeryTrustedMatching(visited)

            if node is None:
                return None

            if node is not Ellipsis:
                if result is Ellipsis:
                    result = node
                elif result is not node:
                    return None
        finally:
            visited.remove(self)

        if result is Ellipsis:
            return None

        return result

    def hasShapeListExact(self):
        return (
            self.trace1.hasShapeListExact()
            and self.trace2.hasShapeListExact()
            and self.trace3.hasShapeListExact()
            and self.trace4.hasShapeListExact()
            and self.trace5.hasShapeListExact()
            and self.trace6.hasShapeListExact()
        )

    def hasShapeDictionaryExact(self):
        return (
            self.trace1.hasShapeDictionaryExact()
            and self.trace2.hasShapeDictionaryExact()
            and self.trace3.hasShapeDictionaryExact()
            and self.trace4.hasShapeDictionaryExact()
            and self.trace5.hasShapeDictionaryExact()
            and self.trace6.hasShapeDictionaryExact()
        )

    def getTruthValue(self):
        truth_value = self.trace1.getTruthValue()

        if truth_value is None:
            return None

        result = truth_value

        truth_value = self.trace2.getTruthValue()

        if truth_value is not result:
            return None
        truth_value = self.trace3.getTruthValue()

        if truth_value is not result:
            return None
        truth_value = self.trace4.getTruthValue()

        if truth_value is not result:
            return None
        truth_value = self.trace5.getTruthValue()

        if truth_value is not result:
            return None
        truth_value = self.trace6.getTruthValue()

        if truth_value is not result:
            return None
        return result

    def getExpectedValue(self):
        expected_available, expected_value = self.trace1.getExpectedValue()

        if not expected_available:
            return False, None

        result = expected_value

        expected_available, expected_value = self.trace2.getExpectedValue()

        if not expected_available:
            return False, None

        if not compareConstants(result, expected_value):
            return False, None

        expected_available, expected_value = self.trace3.getExpectedValue()

        if not expected_available:
            return False, None

        if not compareConstants(result, expected_value):
            return False, None

        expected_available, expected_value = self.trace4.getExpectedValue()

        if not expected_available:
            return False, None

        if not compareConstants(result, expected_value):
            return False, None

        expected_available, expected_value = self.trace5.getExpectedValue()

        if not expected_available:
            return False, None

        if not compareConstants(result, expected_value):
            return False, None

        expected_available, expected_value = self.trace6.getExpectedValue()

        if not expected_available:
            return False, None

        if not compareConstants(result, expected_value):
            return False, None

        return True, result

    def compareValueTrace(self, other):
        if type(other) is not ValueTraceMerge6:
            return False

        return (
            self.trace1.compareValueTrace(other.trace1)
            and self.trace2.compareValueTrace(other.trace2)
            and self.trace3.compareValueTrace(other.trace3)
            and self.trace4.compareValueTrace(other.trace4)
            and self.trace5.compareValueTrace(other.trace5)
            and self.trace6.compareValueTrace(other.trace6)
        )

    def isUnchangedResumeTrace(self, loop_entry_trace):
        return (
            self.trace1.isUnchangedResumeTrace(loop_entry_trace)
            and self.trace2.isUnchangedResumeTrace(loop_entry_trace)
            and self.trace3.isUnchangedResumeTrace(loop_entry_trace)
            and self.trace4.isUnchangedResumeTrace(loop_entry_trace)
            and self.trace5.isUnchangedResumeTrace(loop_entry_trace)
            and self.trace6.isUnchangedResumeTrace(loop_entry_trace)
        )

    def addNameUsage(self):
        self.usage_count += 1
        self.name_usage_count += 1

        if self.name_usage_count <= 2:
            self.trace1.addNameUsage()
            self.trace2.addNameUsage()
            self.trace3.addNameUsage()
            self.trace4.addNameUsage()
            self.trace5.addNameUsage()
            self.trace6.addNameUsage()

    def removeNameUsage(self):
        self.usage_count -= 1
        self.name_usage_count -= 1

        if self.name_usage_count < 2:
            self.trace1.removeNameUsage()
            self.trace2.removeNameUsage()
            self.trace3.removeNameUsage()
            self.trace4.removeNameUsage()
            self.trace5.removeNameUsage()
            self.trace6.removeNameUsage()

    def addUsage(self):
        self.usage_count += 1

        if self.usage_count is 1:
            self.trace1.addMergeUsage()
            self.trace2.addMergeUsage()
            self.trace3.addMergeUsage()
            self.trace4.addMergeUsage()
            self.trace5.addMergeUsage()
            self.trace6.addMergeUsage()

    def removeUsage(self):
        self.usage_count -= 1

        if self.usage_count is 0:
            self.trace1.removeMergeUsage()
            self.trace2.removeMergeUsage()
            self.trace3.removeMergeUsage()
            self.trace4.removeMergeUsage()
            self.trace5.removeMergeUsage()
            self.trace6.removeMergeUsage()

    def addMergeUsage(self):
        self.addUsage()
        self.merge_usage_count += 1

    def removeMergeUsage(self):
        self.removeUsage()
        self.merge_usage_count -= 1


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
