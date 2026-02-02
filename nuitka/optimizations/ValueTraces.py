#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Value trace objects.

Value traces indicate the flow of values and merges their versions for
the SSA (Single State Assignment) form being used in Nuitka.

Values can be seen as:

* Unknown (maybe initialized, maybe not, we cannot know)
* Uninitialized (definitely not initialized, first version)
* Init (definitely initialized, e.g. parameter variables)
* Assign (assignment was done)
* Deleted (del was done, now unassigned, uninitialized)
* Merge (result of diverged code paths, loop potentially)
* LoopIncomplete (aggregation during loops, not yet fully known)
* LoopComplete (complete knowledge of loop types)
"""

from abc import abstractmethod

from nuitka.nodes.shapes.BuiltinTypeShapes import (
    tshape_bool,
    tshape_bytes,
    tshape_dict,
    tshape_list,
    tshape_str,
    tshape_tuple,
    tshape_unicode,
)
from nuitka.nodes.shapes.ControlFlowDescriptions import (
    ControlFlowDescriptionElementBasedEscape,
    ControlFlowDescriptionFullEscape,
    ControlFlowDescriptionNoEscape,
)
from nuitka.nodes.shapes.StandardShapes import (
    ShapeLoopCompleteAlternative,
    ShapeLoopInitialAlternative,
    tshape_uninitialized,
    tshape_unknown,
)
from nuitka.States import states
from nuitka.Tracing import my_print
from nuitka.utils.InstanceCounters import (
    counted_del,
    counted_init,
    isCountingInstances,
)


class ValueTraceBase(object):
    # We are going to have many instance attributes, but should strive to minimize, as
    # there is going to be a lot of fluctuation in these objects.

    __slots__ = (
        "owner",
        "usage_count",
        "name_usage_count",
        "merge_usage_count",
    )

    if isCountingInstances():
        __del__ = counted_del()

    def __repr__(self):
        return "<%s of %s>" % (self.__class__.__name__, self.owner.getCodeName())

    def dump(self, indent="  "):
        my_print("%s%s %s:" % (indent, self.__class__.__name__, id(self)))

        if type(self.previous) is tuple:
            for trace in self.previous:
                trace.dump(indent + "  ")
        elif self.previous is not None:
            self.previous.dump(indent + "  ")

    def getOwner(self):
        return self.owner

    def emitShapeAlternativesForLoop(self, emit, loop_node):
        # Virtual method, pylint: disable=unused-argument
        self.getTypeShape().emitAlternatives(emit)

    @staticmethod
    def isLoopTrace():
        return False

    def addUsage(self):
        self.usage_count += 1

    def removeUsage(self):
        self.usage_count -= 1

    def addNameUsage(self):
        self.usage_count += 1
        self.name_usage_count += 1

        if self.name_usage_count <= 2 and self.previous is not None:
            self.previous.addNameUsage()

    def removeNameUsage(self):
        self.usage_count -= 1
        self.name_usage_count -= 1

        if self.name_usage_count < 2 and self.previous is not None:
            self.previous.removeNameUsage()

    def addMergeUsage(self):
        self.usage_count += 1
        self.merge_usage_count += 1

    def removeMergeUsage(self):
        self.usage_count -= 1
        self.merge_usage_count -= 1

    def getUsageCount(self):
        return self.usage_count

    def getNameUsageCount(self):
        return self.name_usage_count

    def getMergeUsageCount(self):
        return self.merge_usage_count

    def hasNoMergeOrNameUsage(self):
        return (self.merge_usage_count | self.name_usage_count) == 0

    def getPrevious(self):
        return self.previous

    @abstractmethod
    def isUsingTrace(self):
        """Is the trace indicating a usage of the variable."""

    @abstractmethod
    def isWritingTrace(self):
        """Is the trace indicating a usage of the variable."""

    @staticmethod
    def isAssignTrace():
        return False

    @staticmethod
    def isUnassignedTrace():
        return False

    @staticmethod
    def isDeletedTrace():
        return False

    @staticmethod
    def isUninitializedTrace():
        return False

    @staticmethod
    def isInitTrace():
        return False

    @staticmethod
    def isUnknownTrace():
        return False

    @staticmethod
    def isUnknownStartTrace():
        return False

    @staticmethod
    def isAssignTraceVeryTrusted():
        return False

    @staticmethod
    def isUnknownOrVeryTrustedTrace():
        return False

    @staticmethod
    def isEscapeTrace():
        return False

    @staticmethod
    def isTraceThatNeedsEscape():
        return True

    @staticmethod
    def isMergeTrace():
        return False

    @abstractmethod
    def mustHaveValue(self):
        """Will this definitely have a value."""

    @abstractmethod
    def mustNotHaveValue(self):
        """Will this definitely have a value."""

    def getReplacementNode(self, usage):
        # Virtual method, pylint: disable=no-self-use,unused-argument

        return None

    @staticmethod
    def hasShapeListExact():
        return False

    @staticmethod
    def hasShapeDictionaryExact():
        return False

    @staticmethod
    def hasShapeStrExact():
        return False

    @staticmethod
    def hasShapeUnicodeExact():
        return False

    @staticmethod
    def hasShapeTupleExact():
        return False

    @staticmethod
    def hasShapeBoolExact():
        return False

    @staticmethod
    def getTruthValue():
        return None

    @staticmethod
    def getComparisonValue():
        return False, None

    @staticmethod
    def getAttributeNode():
        """Node to use for attribute lookups."""
        return None

    @staticmethod
    def getAttributeNodeTrusted():
        """Node to use for attribute lookups, with increased trust.

        Used with hard imports mainly.
        """
        return None

    @staticmethod
    def getAttributeNodeVeryTrusted():
        """Node to use for attribute lookups, with highest trust.

        Used for hard imports mainly.
        """
        return None

    @staticmethod
    def getIterationSourceNode():
        """Node to use for iteration decisions."""
        return None

    @staticmethod
    def getDictInValue(key):
        """Value to use for dict in decisions."""

        # virtual method, pylint: disable=unused-argument
        return None

    @staticmethod
    def inhibitsClassScopeForwardPropagation():
        return True


class ValueTraceUnassignedBase(ValueTraceBase):
    # Base classes can be abstract, pylint: disable=I0021,abstract-method

    __slots__ = ()

    @staticmethod
    def isUnassignedTrace():
        return True

    @staticmethod
    def getTypeShape():
        return tshape_uninitialized

    @staticmethod
    def getReleaseEscape():
        return ControlFlowDescriptionNoEscape

    def compareValueTrace(self, other):
        # We are unassigned, just need to know if the other one is, pylint: disable=no-self-use
        return other.isUnassignedTrace()

    @staticmethod
    def mustHaveValue():
        return False

    @staticmethod
    def mustNotHaveValue():
        return True


class ValueTraceStartMixin(object):
    # Mixins are not allowed to specify slots, pylint: disable=assigning-non-slot
    __slots__ = ()

    def addUsage(self):
        self.usage_count += 1

    def removeUsage(self):
        self.usage_count -= 1

    def addMergeUsage(self):
        self.usage_count += 1
        self.merge_usage_count += 1

    def removeMergeUsage(self):
        self.usage_count -= 1
        self.merge_usage_count -= 1

    def addNameUsage(self):
        self.usage_count += 1
        self.name_usage_count += 1

    def removeNameUsage(self):
        self.usage_count -= 1
        self.name_usage_count -= 1

    @staticmethod
    def getAttributeNode():
        return None

    @staticmethod
    def getAttributeNodeTrusted():
        return None

    @staticmethod
    def getAttributeNodeVeryTrusted():
        return None


class ValueTraceStartUninitialized(ValueTraceStartMixin, ValueTraceUnassignedBase):
    __slots__ = ()

    @counted_init
    def __init__(self, owner):
        self.owner = owner
        self.usage_count = 0
        self.name_usage_count = 0
        self.merge_usage_count = 0

    @staticmethod
    def isUninitializedTrace():
        return True

    def isUsingTrace(self):
        return self.usage_count

    @staticmethod
    def isWritingTrace():
        return False

    @staticmethod
    def isTraceThatNeedsEscape():
        return False

    @staticmethod
    def inhibitsClassScopeForwardPropagation():
        return False


class ValueTraceDeleted(ValueTraceUnassignedBase):
    """Trace caused by a deletion."""

    __slots__ = (
        "previous",
        "del_node",
    )

    @counted_init
    def __init__(self, owner, previous, del_node):
        self.owner = owner
        self.usage_count = 0
        self.name_usage_count = 0
        self.merge_usage_count = 0

        self.previous = previous
        self.del_node = del_node

    @staticmethod
    def isDeletedTrace():
        return True

    @staticmethod
    def isUsingTrace():
        return True

    @staticmethod
    def isWritingTrace():
        return True

    def getDelNode(self):
        return self.del_node


class ValueTraceStartInit(ValueTraceStartMixin, ValueTraceBase):
    __slots__ = ()

    @counted_init
    def __init__(self, owner):
        self.owner = owner
        self.usage_count = 0
        self.name_usage_count = 0
        self.merge_usage_count = 0

    @staticmethod
    def getTypeShape():
        return tshape_unknown

    @staticmethod
    def getReleaseEscape():
        return ControlFlowDescriptionFullEscape

    def compareValueTrace(self, other):
        # We are initialized, just need to know if the other one is, pylint: disable=no-self-use
        return other.isInitTrace()

    @staticmethod
    def isInitTrace():
        return True

    @staticmethod
    def isUsingTrace():
        return True

    @staticmethod
    def isWritingTrace():
        return False

    @staticmethod
    def mustHaveValue():
        return True

    @staticmethod
    def mustNotHaveValue():
        return False


class ValueTraceStartInitStarArgs(ValueTraceStartInit):
    @staticmethod
    def getTypeShape():
        return tshape_tuple

    @staticmethod
    def getReleaseEscape():
        return ControlFlowDescriptionElementBasedEscape

    @staticmethod
    def hasShapeTupleExact():
        return True


class ValueTraceStartInitStarDict(ValueTraceStartInit):
    @staticmethod
    def getTypeShape():
        return tshape_dict

    @staticmethod
    def getReleaseEscape():
        return ControlFlowDescriptionElementBasedEscape

    @staticmethod
    def hasShapeDictionaryExact():
        return True


class ValueTraceUnknownBase(ValueTraceBase):

    @staticmethod
    def getTypeShape():
        return tshape_unknown

    @staticmethod
    def getReleaseEscape():
        return ControlFlowDescriptionFullEscape

    def addUsage(self):
        self.usage_count += 1

        if self.previous:
            self.previous.addUsage()

    def removeUsage(self):
        self.usage_count -= 1

        if self.previous:
            self.previous.removeUsage()

    def addMergeUsage(self):
        self.usage_count += 1
        self.merge_usage_count += 1

        if self.previous:
            self.previous.addMergeUsage()

    def removeMergeUsage(self):
        self.usage_count -= 1
        self.merge_usage_count -= 1

        if self.previous:
            self.previous.removeMergeUsage()

    def compareValueTrace(self, other):
        # We are unknown, just need to know if the other one is, pylint: disable=no-self-use
        return other.isUnknownTrace()

    @staticmethod
    def isUnknownTrace():
        return True

    def isUsingTrace(self):
        return self.usage_count

    @staticmethod
    def isWritingTrace():
        return True

    @staticmethod
    def isUnknownOrVeryTrustedTrace():
        return True

    @staticmethod
    def isTraceThatNeedsEscape():
        return False

    @staticmethod
    def mustHaveValue():
        return False

    @staticmethod
    def mustNotHaveValue():
        return False

    def getAttributeNode(self):
        # TODO: Differentiate unknown with not previous node from ones with for performance and
        # clarity.
        if self.previous is not None:
            return self.previous.getAttributeNodeVeryTrusted()

    def getAttributeNodeTrusted(self):
        if self.previous is not None:
            return self.previous.getAttributeNodeVeryTrusted()

    def getAttributeNodeVeryTrusted(self):
        if self.previous is not None:
            return self.previous.getAttributeNodeVeryTrusted()


class ValueTraceUnknown(ValueTraceUnknownBase):
    __slots__ = ("previous",)

    @counted_init
    def __init__(self, owner, previous):
        self.owner = owner
        self.usage_count = 0
        self.name_usage_count = 0
        self.merge_usage_count = 0

        self.previous = previous


class ValueTraceStartUnknown(ValueTraceStartMixin, ValueTraceUnknownBase):

    @counted_init
    def __init__(self, owner):
        self.owner = owner
        self.usage_count = 0
        self.name_usage_count = 0
        self.merge_usage_count = 0

    __slots__ = ()

    @staticmethod
    def isUnknownStartTrace():
        return True


class ValueTraceEscaped(ValueTraceUnknown):
    __slots__ = ()

    def addUsage(self):
        self.usage_count += 1

        # The previous must be prevented from optimization if still used afterwards.
        if self.usage_count <= 2:
            self.previous.addNameUsage()

    def removeUsage(self):
        self.usage_count -= 1

        # The previous must be prevented from optimization if still used afterwards.
        if self.usage_count < 2:
            self.previous.removeNameUsage()

    def addMergeUsage(self):
        self.usage_count += 1
        if self.usage_count <= 2:
            self.previous.addNameUsage()

        self.merge_usage_count += 1
        if self.merge_usage_count <= 2:
            self.previous.addMergeUsage()

    def removeMergeUsage(self):
        self.usage_count -= 1
        if self.usage_count < 2:
            self.previous.removeNameUsage()

        self.merge_usage_count -= 1
        if self.merge_usage_count < 2:
            self.previous.removeMergeUsage()

    def getTypeShape(self):
        return self.previous.getTypeShape()

    def mustHaveValue(self):
        return self.previous.mustHaveValue()

    def mustNotHaveValue(self):
        return self.previous.mustNotHaveValue()

    def getReplacementNode(self, usage):
        return self.previous.getReplacementNode(usage)

    @staticmethod
    def isUnknownTrace():
        return False

    @staticmethod
    def isUnknownOrVeryTrustedTrace():
        return False

    @staticmethod
    def isEscapeTrace():
        return True

    @staticmethod
    def isWritingTrace():
        return False

    def isUsingTrace(self):
        return self.usage_count

    @staticmethod
    def isTraceThatNeedsEscape():
        return False

    def getAttributeNode(self):
        return self.previous.getAttributeNodeTrusted()

    def getAttributeNodeTrusted(self):
        return self.previous.getAttributeNodeTrusted()

    def getAttributeNodeVeryTrusted(self):
        return self.previous.getAttributeNodeVeryTrusted()

    # For escaped values, these do not have to forget their shape, the mutable ones
    # and the only ones affected.
    def hasShapeListExact(self):
        trusted_node = self.previous.getAttributeNodeTrusted()
        return trusted_node is not None and trusted_node.hasShapeListExact()

    def hasShapeDictionaryExact(self):
        trusted_node = self.previous.getAttributeNodeTrusted()
        return trusted_node is not None and trusted_node.hasShapeDictionaryExact()


class ValueTraceAssign(ValueTraceBase):
    __slots__ = (
        "previous",
        "assign_node",
    )

    @counted_init
    def __init__(self, owner, assign_node, previous):
        # assert assign_node.isStatementAssignmentVariable(), assign_node

        self.owner = owner
        self.usage_count = 0
        self.name_usage_count = 0
        self.merge_usage_count = 0

        self.previous = previous
        self.assign_node = assign_node

    def __repr__(self):
        return "<%s at %s of %s>" % (
            self.__class__.__name__,
            self.assign_node.getSourceReference().getAsString(),
            self.assign_node.subnode_source,
        )

    @staticmethod
    def isAssignTrace():
        return True

    @staticmethod
    def isUsingTrace():
        return True

    @staticmethod
    def isWritingTrace():
        return True

    def compareValueTrace(self, other):
        return other.isAssignTrace() and self.assign_node is other.assign_node

    @staticmethod
    def mustHaveValue():
        return True

    @staticmethod
    def mustNotHaveValue():
        return False

    def getTypeShape(self):
        return self.assign_node.getTypeShape()

    def getReleaseEscape(self):
        return self.assign_node.getReleaseEscape()

    def getAssignNode(self):
        return self.assign_node

    def hasShapeListExact(self):
        return self.assign_node.subnode_source.hasShapeListExact()

    def hasShapeDictionaryExact(self):
        return self.assign_node.subnode_source.hasShapeDictionaryExact()

    def hasShapeStrExact(self):
        return self.assign_node.subnode_source.hasShapeStrExact()

    def hasShapeUnicodeExact(self):
        return self.assign_node.subnode_source.hasShapeUnicodeExact()

    def hasShapeBoolExact(self):
        return self.assign_node.subnode_source.hasShapeBoolExact()

    def getTruthValue(self):
        return self.assign_node.subnode_source.getTruthValue()

    def getComparisonValue(self):
        return self.assign_node.subnode_source.getComparisonValue()

    def getAttributeNode(self):
        return self.assign_node.subnode_source

    def getAttributeNodeTrusted(self):
        source_node = self.assign_node.subnode_source

        if source_node.hasShapeTrustedAttributes():
            return source_node
        else:
            return None

    def getAttributeNodeVeryTrusted(self):
        # Hard imports typically.
        if self.assign_node.hasVeryTrustedValue():
            return self.assign_node.subnode_source
        else:
            return None

    def getIterationSourceNode(self):
        return self.assign_node.subnode_source

    def getDictInValue(self, key):
        """Value to use for dict in decisions."""
        return self.assign_node.subnode_source.getExpressionDictInConstant(key)

    def inhibitsClassScopeForwardPropagation(self):
        return self.assign_node.subnode_source.mayHaveSideEffects()


class ValueTraceAssignUnescapable(ValueTraceAssign):
    @staticmethod
    def isTraceThatNeedsEscape():
        return False


class ValueTraceAssignVeryTrusted(ValueTraceAssignUnescapable):
    @staticmethod
    def isAssignTraceVeryTrusted():
        return True

    @staticmethod
    def isUnknownOrVeryTrustedTrace():
        return True


class ValueTraceAssignUnescapablePropagated(ValueTraceAssignUnescapable):
    """Assignment from value where it is not that escaping doesn't matter."""

    __slots__ = ("replacement",)

    @counted_init
    def __init__(self, owner, assign_node, previous, replacement):
        # For performance reasons, we don't do super init, but duplicate it here.
        # pylint: disable=super-init-not-called

        self.owner = owner
        self.usage_count = 0
        self.name_usage_count = 0
        self.merge_usage_count = 0

        self.previous = previous
        self.assign_node = assign_node

        self.replacement = replacement

    def getReplacementNode(self, usage):
        return self.replacement(usage)


class ValueTraceMergeBase(ValueTraceBase):
    """Merge of two or more traces or start of loops."""

    # Base classes can be abstract, pylint: disable=I0021,abstract-method

    __slots__ = ("previous",)

    def addNameUsage(self):  # pylint: disable=I0021,too-many-branches
        self.usage_count += 1
        self.name_usage_count += 1

        if self.name_usage_count <= 2 and self.previous is not None:
            for previous in self.previous:
                previous.addNameUsage()

    def removeNameUsage(self):
        self.usage_count -= 1
        self.name_usage_count -= 1

        if self.name_usage_count < 2 and self.previous is not None:
            for previous in self.previous:
                previous.removeNameUsage()

    def addUsage(self):
        self.usage_count += 1

        # Only do it once.
        if self.usage_count == 1:
            for trace in self.previous:
                trace.addMergeUsage()

    def removeUsage(self):
        self.usage_count -= 1

        # Only do it once.
        if self.usage_count == 0:
            for trace in self.previous:
                trace.removeMergeUsage()

    def addMergeUsage(self):
        self.addUsage()
        self.merge_usage_count += 1

    def removeMergeUsage(self):
        self.removeUsage()
        self.merge_usage_count -= 1

    def isUsingTrace(self):
        # Checking definite is enough, the merges, we shall see them as well.
        return self.usage_count


class ValueTraceMerge(ValueTraceMergeBase):
    """Merge of two or more traces.

    Happens at the end of conditional blocks. This is "phi" in
    SSA theory. Also used for merging multiple "return", "break" or
    "continue" exits.
    """

    __slots__ = ()

    @counted_init
    def __init__(self, traces):
        shorted = []

        for trace in traces:
            if type(trace) is ValueTraceMerge:
                for trace2 in trace.previous:
                    if trace2 not in shorted:
                        shorted.append(trace2)
            else:
                if trace not in shorted:
                    shorted.append(trace)

        if _is_debug:
            assert len(shorted) > 1, traces

        traces = tuple(shorted)

        self.owner = traces[0].owner
        self.previous = traces

        self.usage_count = 0
        self.name_usage_count = 0
        self.merge_usage_count = 0

    def __repr__(self):
        return "<ValueTraceMerge of {previous}>".format(previous=self.previous)

    def getTypeShape(self):
        type_shape_found = None

        for trace in self.previous:
            type_shape = trace.getTypeShape()

            if type_shape is tshape_unknown:
                return tshape_unknown

            if type_shape_found is None:
                type_shape_found = type_shape
            elif type_shape is not type_shape_found:
                # TODO: Find the lowest common denominator.
                return tshape_unknown

        return type_shape_found

    def getReleaseEscape(self):
        release_escape_found = None

        for trace in self.previous:
            release_escape = trace.getReleaseEscape()

            if release_escape is ControlFlowDescriptionFullEscape:
                return ControlFlowDescriptionFullEscape

            if release_escape_found is None:
                release_escape_found = release_escape
            elif release_escape is not release_escape_found:
                # TODO: Find the lowest common denominator.
                return ControlFlowDescriptionFullEscape

        return release_escape_found

    @staticmethod
    def isMergeTrace():
        return True

    def isUsingTrace(self):
        # Checking definite is enough, the merges, we shall see them as well.
        return self.usage_count

    @staticmethod
    def isWritingTrace():
        return False

    def compareValueTrace(self, other):
        if not other.isMergeTrace():
            return False

        if len(self.previous) != len(other.previous):
            return False

        for a, b in zip(self.previous, other.previous):
            if not a.compareValueTrace(b):
                return False

        return True

    def mustHaveValue(self):
        for previous in self.previous:
            if not previous.isInitTrace() and not previous.isAssignTrace():
                return False

        return True

    def mustNotHaveValue(self):
        for previous in self.previous:
            if not previous.mustNotHaveValue():
                return False

        return True

    def hasShapeListExact(self):
        return all(previous.hasShapeListExact() for previous in self.previous)

    def hasShapeDictionaryExact(self):
        return all(previous.hasShapeDictionaryExact() for previous in self.previous)

    def getTruthValue(self):
        any_false = False
        any_true = False

        for previous in self.previous:
            truth_value = previous.getTruthValue()

            # One unknown kills it.
            if truth_value is None:
                return None
            elif truth_value is True:
                # True and false values resembled unknown.
                if any_false:
                    return None
                any_true = True
            else:
                # True and false values resembled unknown.
                if any_true:
                    return None
                any_false = True

        # Now all agreed and were not unknown, so we can conclude all false or all true.
        return any_true

    def getComparisonValue(self):
        # TODO: Support multiple values as candidates, e.g. both 1, 3 could be compared to 2, for
        # now we are delaying that.
        return False, None


class ValueTraceLoopBase(ValueTraceMergeBase):
    # Base classes can be abstract, pylint: disable=I0021,abstract-method

    # This one has many attributes, pylint: disable=too-many-instance-attributes
    __slots__ = ("loop_node", "type_shapes", "type_shape", "recursion")

    @counted_init
    def __init__(self, loop_node, previous, type_shapes):
        # For performance reasons, we don't do super init, but duplicate it here.
        # pylint: disable=super-init-not-called

        self.owner = previous.owner

        # Note: That previous is being added to later, we will learn about more.
        self.previous = (previous,)

        self.usage_count = 0
        self.name_usage_count = 0
        self.merge_usage_count = 0

        self.loop_node = loop_node
        self.type_shapes = type_shapes
        self.type_shape = None

        self.recursion = False

    def __repr__(self):
        return "<%s shapes %s of %s>" % (
            self.__class__.__name__,
            self.type_shapes,
            self.owner.getCodeName(),
        )

    @staticmethod
    def isLoopTrace():
        return True

    @staticmethod
    def isUsingTrace():
        return True

    @staticmethod
    def isWritingTrace():
        return False

    def getTypeShape(self):
        if self.type_shape is None:
            if len(self.type_shapes) > 1:
                self.type_shape = ShapeLoopCompleteAlternative(self.type_shapes)
            else:
                self.type_shape = next(iter(self.type_shapes))

        return self.type_shape

    def addLoopContinueTraces(self, continue_traces):
        self.previous += tuple(continue_traces)

        for previous in continue_traces:
            previous.addMergeUsage()

    def mustHaveValue(self):
        # To handle recursion, we lie to ourselves.
        if self.recursion:
            return True

        self.recursion = True

        for previous in self.previous:
            if not previous.mustHaveValue():
                self.recursion = False
                return False

        self.recursion = False
        return True

    def hasShapeListExact(self):
        return self.type_shapes == _only_list_shape

    def hasShapeDictionaryExact(self):
        return self.type_shapes == _only_dict_shape

    def hasShapeStrExact(self):
        return self.type_shapes == _only_str_shape

    def hasShapeUnicodeExact(self):
        return self.type_shapes == _only_unicode_shape

    if str is bytes:

        def hasShapeStrOrUnicodeExact(self):
            return (
                self.hasShapeStrExact()
                or self.hasShapeUnicodeExact()
                or self.type_shapes == _str_plus_unicode_shape
            )

    else:

        hasShapeStrOrUnicodeExact = hasShapeUnicodeExact

    def hasShapeBytesExact(self):
        return self.type_shapes == _only_bytes_shape

    def hasShapeBoolExact(self):
        return self.type_shapes == _only_bool_shape


_only_list_shape = frozenset((tshape_list,))
_only_dict_shape = frozenset((tshape_dict,))
_only_str_shape = frozenset((tshape_str,))
_only_unicode_shape = frozenset((tshape_unicode,))
_str_plus_unicode_shape = frozenset((tshape_unicode, tshape_str))
_only_bytes_shape = frozenset((tshape_bytes,))
_only_bool_shape = frozenset((tshape_bool,))


class ValueTraceLoopComplete(ValueTraceLoopBase):
    __slots__ = ()

    @staticmethod
    def getReleaseEscape():
        # TODO: May consider the shapes for better result
        return ControlFlowDescriptionFullEscape

    def compareValueTrace(self, other):
        # Incomplete loop value traces behave the same.
        return (
            self.__class__ is other.__class__
            and self.loop_node == other.loop_node
            and self.type_shapes == other.type_shapes
        )

    # TODO: These could be better
    @staticmethod
    def mustHaveValue():
        return False

    @staticmethod
    def mustNotHaveValue():
        return False

    @staticmethod
    def getTruthValue():
        return None

    @staticmethod
    def getComparisonValue():
        return False, None


class ValueTraceLoopIncomplete(ValueTraceLoopBase):
    __slots__ = ()

    def getTypeShape(self):
        if self.type_shape is None:
            self.type_shape = ShapeLoopInitialAlternative(self.type_shapes)

        return self.type_shape

    @staticmethod
    def getReleaseEscape():
        return ControlFlowDescriptionFullEscape

    def compareValueTrace(self, other):
        # Incomplete loop value traces behave the same.
        return self.__class__ is other.__class__ and self.loop_node == other.loop_node

    @staticmethod
    def mustHaveValue():
        return False

    @staticmethod
    def mustNotHaveValue():
        return False

    @staticmethod
    def getTruthValue():
        return None

    @staticmethod
    def getComparisonValue():
        return False, None

    def emitShapeAlternativesForLoop(self, emit, loop_node):
        if self.loop_node is loop_node:
            self.getTypeShape().emitAlternatives(emit)
        else:
            emit(tshape_unknown)


_is_debug = None


def setupValueTraceFromOptions():
    # singleton, pylint: disable=global-statement

    global _is_debug
    _is_debug = states.is_debug


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
