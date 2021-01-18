#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Value trace objects.

Value traces indicate the flow of values and merges their versions for
the SSA (Single State Assignment) form being used in Nuitka.

Values can be seen as:

* Unknown (maybe initialized, maybe not, we cannot know)
* Uninit (definitely not initialized, first version)
* Init (definitely initialized, e.g. parameter variables)
* Assign (assignment was done)
* Deleted (del was done, now unassigned, uninitialted)
* Merge (result of diverged code paths, loop potentially)
* LoopIncomplete (aggregation during loops, not yet fully known)
* LoopComplete (complete knowledge of loop types)
"""


from nuitka.nodes.shapes.StandardShapes import (
    ShapeLoopCompleteAlternative,
    ShapeLoopInitialAlternative,
    tshape_uninit,
    tshape_unknown,
)
from nuitka.utils import InstanceCounters


class ValueTraceBase(object):
    # We are going to have many instance attributes, but should strive to minimize, as
    # there is going to be a lot of fluctuation in these objects.

    __slots__ = (
        "owner",
        "usage_count",
        "name_usage_count",
        "merge_usage_count",
        "closure_usages",
        "previous",
    )

    @InstanceCounters.counted_init
    def __init__(self, owner, previous):
        self.owner = owner

        # Definite usage indicator.
        self.usage_count = 0

        # If 0, this indicates, the variable name needs to be assigned as name.
        self.name_usage_count = 0

        # If 0, this indicates no value merges happened on the value.
        self.merge_usage_count = 0

        self.closure_usages = False

        # Previous trace this is replacing.
        self.previous = previous

    __del__ = InstanceCounters.counted_del()

    def __repr__(self):
        return "<%s of %s>" % (self.__class__.__name__, self.owner.getCodeName())

    def getOwner(self):
        return self.owner

    @staticmethod
    def isLoopTrace():
        return False

    def addUsage(self):
        self.usage_count += 1

    def addNameUsage(self):
        self.usage_count += 1
        self.name_usage_count += 1

        if self.name_usage_count <= 2 and self.previous is not None:
            self.previous.addNameUsage()

    def addMergeUsage(self):
        self.usage_count += 1
        self.merge_usage_count += 1

    def getUsageCount(self):
        return self.usage_count

    def getNameUsageCount(self):
        return self.name_usage_count

    def getMergeUsageCount(self):
        return self.merge_usage_count

    def getMergeOrNameUsageCount(self):
        return self.merge_usage_count + self.name_usage_count

    def getPrevious(self):
        return self.previous

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
    def isUninitTrace():
        return False

    @staticmethod
    def isInitTrace():
        return False

    @staticmethod
    def isUnknownTrace():
        return False

    @staticmethod
    def isMergeTrace():
        return False

    def mustHaveValue(self):
        """Will this definitely have a value.

        Every trace has this overloaded.
        """
        assert False, self

    def mustNotHaveValue(self):
        """Will this definitely have a value.

        Every trace has this overloaded.
        """
        assert False, self

    def getReplacementNode(self, usage):
        # Virtual method, pylint: disable=no-self-use,unused-argument

        return None

    @staticmethod
    def hasShapeDictionaryExact():
        return False

    @staticmethod
    def getTruthValue():
        return None


class ValueTraceUnassignedBase(ValueTraceBase):
    __slots__ = ()

    @staticmethod
    def isUnassignedTrace():
        return True

    @staticmethod
    def getTypeShape():
        return tshape_uninit

    def compareValueTrace(self, other):
        # We are unassigned, just need to know if the other one is, pylint: disable=no-self-use
        return other.isUnassignedTrace()

    @staticmethod
    def mustHaveValue():
        return False

    @staticmethod
    def mustNotHaveValue():
        return True


class ValueTraceUninit(ValueTraceUnassignedBase):
    __slots__ = ()

    def __init__(self, owner, previous):
        ValueTraceUnassignedBase.__init__(self, owner=owner, previous=previous)

    @staticmethod
    def isUninitTrace():
        return True


class ValueTraceDeleted(ValueTraceUnassignedBase):
    """Trace caused by a deletion."""

    __slots__ = ("del_node",)

    def __init__(self, owner, previous, del_node):
        ValueTraceUnassignedBase.__init__(self, owner=owner, previous=previous)

        self.del_node = del_node

    @staticmethod
    def isDeletedTrace():
        return True

    def getDelNode(self):
        return self.del_node


class ValueTraceInit(ValueTraceBase):
    __slots__ = ()

    def __init__(self, owner):
        ValueTraceBase.__init__(self, owner=owner, previous=None)

    @staticmethod
    def getTypeShape():
        return tshape_unknown

    def compareValueTrace(self, other):
        # We are initialized, just need to know if the other one is, pylint: disable=no-self-use
        return other.isInitTrace()

    @staticmethod
    def isInitTrace():
        return True

    @staticmethod
    def mustHaveValue():
        return True

    @staticmethod
    def mustNotHaveValue():
        return False


class ValueTraceUnknown(ValueTraceBase):
    __slots__ = ()

    def __init__(self, owner, previous):
        ValueTraceBase.__init__(self, owner=owner, previous=previous)

    @staticmethod
    def getTypeShape():
        return tshape_unknown

    def addUsage(self):
        self.usage_count += 1

        if self.previous:
            self.previous.addUsage()

    def addMergeUsage(self):
        self.usage_count += 1
        self.merge_usage_count += 1

        if self.previous:
            self.previous.addMergeUsage()

    def compareValueTrace(self, other):
        # We are unknown, just need to know if the other one is, pylint: disable=no-self-use
        return other.isUnknownTrace()

    @staticmethod
    def isUnknownTrace():
        return True

    @staticmethod
    def mustHaveValue():
        return False

    @staticmethod
    def mustNotHaveValue():
        return False


class ValueTraceEscaped(ValueTraceUnknown):
    __slots__ = ()

    def addUsage(self):
        self.usage_count += 1

        # The previous must be prevented from optimization if still used afterwards.
        if self.usage_count <= 2:
            self.previous.addNameUsage()

    def addMergeUsage(self):
        self.usage_count += 1
        if self.usage_count <= 2:
            self.previous.addNameUsage()

        self.merge_usage_count += 1
        if self.merge_usage_count <= 2:
            self.previous.addMergeUsage()


class ValueTraceAssign(ValueTraceBase):
    __slots__ = ("assign_node", "replace_it")

    def __init__(self, owner, assign_node, previous):
        ValueTraceBase.__init__(self, owner=owner, previous=previous)

        self.assign_node = assign_node
        self.replace_it = None

    def __repr__(self):
        return "<ValueTraceAssign at {source_ref} of {value}>".format(
            source_ref=self.assign_node.getSourceReference().getAsString(),
            value=self.assign_node.subnode_source,
        )

    @staticmethod
    def isAssignTrace():
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

    def getAssignNode(self):
        return self.assign_node

    def setReplacementNode(self, replacement):
        self.replace_it = replacement

    def getReplacementNode(self, usage):
        if self.replace_it is not None:
            return self.replace_it(usage)
        else:
            return None

    def hasShapeDictionaryExact(self):
        return self.assign_node.subnode_source.hasShapeDictionaryExact()

    def getTruthValue(self):
        return self.assign_node.subnode_source.getTruthValue()


class ValueTraceMergeBase(ValueTraceBase):
    """Merge of two or more traces or start of loops."""

    __slots__ = ()

    def addNameUsage(self):
        self.usage_count += 1
        self.name_usage_count += 1

        if self.name_usage_count <= 2 and self.previous is not None:
            for previous in self.previous:
                previous.addNameUsage()


class ValueTraceMerge(ValueTraceMergeBase):
    """Merge of two or more traces.

    Happens at the end of conditional blocks. This is "phi" in
    SSA theory. Also used for merging multiple "return", "break" or
    "continue" exits.
    """

    __slots__ = ()

    def __init__(self, traces):
        ValueTraceMergeBase.__init__(self, owner=traces[0].owner, previous=traces)

        for trace in traces:
            trace.addMergeUsage()

    def __repr__(self):
        return "<ValueTraceMerge of {previous}>".format(previous=self.previous)

    def getTypeShape(self):
        type_shapes = set()

        for trace in self.previous:
            type_shape = trace.getTypeShape()

            if type_shape is tshape_unknown:
                return tshape_unknown

            type_shapes.add(type_shape)

        # TODO: Find the lowest common denominator.
        if len(type_shapes) == 1:
            return type_shapes.pop()
        else:
            return tshape_unknown

    @staticmethod
    def isMergeTrace():
        return True

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

    def addUsage(self):
        self.usage_count += 1

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


class ValueTraceLoopBase(ValueTraceMergeBase):
    __slots__ = ("loop_node", "type_shapes", "type_shape", "recursion")

    def __init__(self, loop_node, previous, type_shapes):
        # Note: That previous is being added to later.
        ValueTraceMergeBase.__init__(self, owner=previous.owner, previous=(previous,))

        previous.addMergeUsage()

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


class ValueTraceLoopComplete(ValueTraceLoopBase):
    __slots__ = ()

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


class ValueTraceLoopIncomplete(ValueTraceLoopBase):
    __slots__ = ()

    def getTypeShape(self):
        if self.type_shape is None:
            self.type_shape = ShapeLoopInitialAlternative(self.type_shapes)

        return self.type_shape

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
