#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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
* Uninit (definitely not initialized, first version, or after "del" statement)
* Init (definitely initialized, e.g. parameter variables)
* Merge (result of diverged code paths, loop potentially)
* LoopInitial (aggregation during loops, not yet fully known)
* LoopComplete (complete knowledge of loop types)
"""


from logging import debug

from nuitka.nodes.shapes.StandardShapes import (
    ShapeLoopCompleteAlternative,
    ShapeLoopInitialAlternative,
    tshape_unknown,
)
from nuitka.utils import InstanceCounters


class ValueTraceBase(object):
    # We are going to have many instance attributes, pylint: disable=too-many-instance-attributes

    __slots__ = (
        "owner",
        "usage_count",
        "has_potential_usages",
        "name_usages",
        "loop_usages",
        "closure_usages",
        "is_escaped",
        "previous",
    )

    @InstanceCounters.counted_init
    def __init__(self, owner, previous):
        self.owner = owner

        # Definite usage indicator.
        self.usage_count = 0

        # Potential usages indicator that an assignment value may be used.
        self.has_potential_usages = False

        # If 0, this indicates, the variable name needs to be assigned as name.
        self.name_usages = 0

        self.loop_usages = 0

        self.closure_usages = False

        # If False, this indicates that the value is not yet escaped.
        self.is_escaped = False

        # Previous trace this is replacing.
        self.previous = previous

    __del__ = InstanceCounters.counted_del()

    def __repr__(self):
        return "<%s of %s>" % (self.__class__.__name__, self.owner.getCodeName())

    def getOwner(self):
        return self.owner

    def addClosureUsage(self):
        self.addUsage()
        self.closure_usages = True

    def addUsage(self):
        self.usage_count += 1

    def addPotentialUsage(self):
        self.has_potential_usages = True

    def addNameUsage(self):
        self.usage_count += 1
        self.name_usages += 1

    def addLoopUsage(self):
        self.usage_count += 1
        self.loop_usages += 1

    def onValueEscape(self):
        self.is_escaped = True

    def isEscaped(self):
        return self.is_escaped

    def hasDefiniteUsages(self):
        return self.usage_count > 0

    def getDefiniteUsages(self):
        return self.usage_count

    def hasPotentialUsages(self):
        return self.has_potential_usages

    def getNameUsageCount(self):
        return self.name_usages

    def hasLoopUsages(self):
        return self.loop_usages > 0

    def getPrevious(self):
        return self.previous

    @staticmethod
    def isAssignTrace():
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
        # Merge traces have this overloaded.

        return self.isInitTrace() or self.isAssignTrace()

    @staticmethod
    def mustNotHaveValue():
        return False

    def getReplacementNode(self, usage):
        # Virtual method, pylint: disable=no-self-use,unused-argument

        return None

    def hasShapeDictionaryExact(self):
        # Virtual method, pylint: disable=no-self-use
        return False


class ValueTraceUninit(ValueTraceBase):
    __slots__ = ()

    def __init__(self, owner, previous):
        ValueTraceBase.__init__(self, owner=owner, previous=previous)

    @staticmethod
    def getTypeShape():
        return tshape_unknown

    @staticmethod
    def isUninitTrace():
        return True

    def mustNotHaveValue(self):
        return True

    def dump(self):
        debug("  Starts out uninitialized")

        if self.usage_count:
            debug("  -> has %s usages" % self.usage_count)

        if self.is_escaped:
            debug("  -> value escapes")


class ValueTraceInit(ValueTraceBase):
    __slots__ = ()

    def __init__(self, owner):
        ValueTraceBase.__init__(self, owner=owner, previous=None)

    @staticmethod
    def getTypeShape():
        return tshape_unknown

    def dump(self):
        debug("  Starts initialized")

        if self.usage_count:
            debug("  -> has %s usages" % self.usage_count)

        if self.is_escaped:
            debug("  -> value escapes")

    @staticmethod
    def isInitTrace():
        return True


class ValueTraceUnknown(ValueTraceBase):
    __slots__ = ()

    def __init__(self, owner, previous):
        ValueTraceBase.__init__(self, owner=owner, previous=previous)

    @staticmethod
    def getTypeShape():
        return tshape_unknown

    def dump(self):
        debug("  Starts unknown")

        if self.usage_count:
            debug("  -> has %s usages" % self.usage_count)

        if self.is_escaped:
            debug("  -> value escapes")

    @staticmethod
    def isUnknownTrace():
        return True

    def addUsage(self):
        self.usage_count += 1

        if self.previous is not None:
            self.previous.addPotentialUsage()

    def addNameUsage(self):
        self.addUsage()
        self.name_usages += 1

        if self.name_usages <= 2 and self.previous is not None:
            self.previous.addNameUsage()

    def addLoopUsage(self):
        self.addUsage()
        self.loop_usages += 1

        if self.loop_usages <= 2 and self.previous is not None:
            self.previous.addLoopUsage()

    def addPotentialUsage(self):
        old = self.has_potential_usages

        if not old:
            self.has_potential_usages = True

            if self.previous is not None:
                self.previous.addPotentialUsage()


class ValueTraceLoopComplete(ValueTraceBase):
    # Need them all, pylint: disable=too-many-instance-attributes

    __slots__ = ("type_shapes", "type_shape", "incomplete")

    def __init__(self, previous, type_shapes):
        assert type_shapes

        ValueTraceBase.__init__(self, owner=previous.owner, previous=(previous,))

        self.type_shapes = type_shapes
        self.type_shape = None

        assert ShapeLoopCompleteAlternative not in type_shapes
        previous.addLoopUsage()

        self.incomplete = False

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

    def addUsage(self):
        self.usage_count += 1

        for previous in self.previous:
            previous.addPotentialUsage()

    def addNameUsage(self):
        self.addUsage()
        self.name_usages += 1

        if self.name_usages <= 2 and self.previous is not None:
            for previous in self.previous:
                previous.addNameUsage()

    def addLoopUsage(self):
        self.addUsage()
        self.loop_usages += 1

        if self.loop_usages <= 2 and self.previous is not None:
            for previous in self.previous:
                previous.addLoopUsage()

    def addPotentialUsage(self):
        old = self.has_potential_usages

        if not old:
            self.has_potential_usages = True
            for previous in self.previous:
                previous.addPotentialUsage()

    def addLoopContinueTraces(self, continue_traces):
        self.previous += tuple(continue_traces)

        self.addPotentialUsage()

        for previous in continue_traces:
            previous.addLoopUsage()

    def markLoopTraceComplete(self):
        pass

    def mustHaveValue(self):
        if self.incomplete is True:
            return False
        elif self.incomplete is None:
            # Lie to ourselves.
            return True
        else:
            # To detect recursion.
            self.incomplete = None

            for previous in self.previous:
                if not previous.mustHaveValue():
                    self.incomplete = False
                    return False

            self.incomplete = False
            return True


class ValueTraceLoopInitial(ValueTraceLoopComplete):
    __slots__ = ()

    def __init__(self, previous, type_shapes):
        ValueTraceLoopComplete.__init__(self, previous, type_shapes)

        # TODO: Do not use this attribute then, the inheritance is
        # probably backwards.
        self.incomplete = True

    def getTypeShape(self):
        if self.type_shape is None:
            self.type_shape = ShapeLoopInitialAlternative(self.type_shapes)

        return self.type_shape

    def markLoopTraceComplete(self):
        self.incomplete = False


class ValueTraceAssign(ValueTraceBase):
    __slots__ = ("assign_node", "replace_it")

    def __init__(self, owner, assign_node, previous):
        ValueTraceBase.__init__(self, owner=owner, previous=previous)

        self.assign_node = assign_node
        self.replace_it = None

    def __repr__(self):
        return "<ValueTraceAssign at {source_ref} of {value}>".format(
            source_ref=self.assign_node.getSourceReference().getAsString(),
            value=self.assign_node.getAssignSource(),
        )

    @staticmethod
    def isAssignTrace():
        return True

    def getTypeShape(self):
        return self.assign_node.subnode_source.getTypeShape()

    def dump(self):
        debug("  Starts assigned")

        if self.usage_count:
            debug("  -> has %s usages" % self.usage_count)

        if self.is_escaped:
            debug("  -> value escapes")

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
        return self.assign_node.getAssignSource().hasShapeDictionaryExact()


class ValueTraceMerge(ValueTraceBase):
    """ Merge of two or more traces.

        Happens at the end of conditional blocks. This is "phi" in
        SSA theory. Also used for merging multiple "return", "break" or
        "continue" exits.
    """

    __slots__ = ()

    def __init__(self, traces):
        ValueTraceBase.__init__(self, owner=traces[0].owner, previous=tuple(traces))

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

    def dump(self):
        debug("  Merge of %s", " <-> ".join(self.previous))

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

        for previous in self.previous:
            previous.addPotentialUsage()

    def addNameUsage(self):
        self.usage_count += 1

        for previous in self.previous:
            previous.addPotentialUsage()
            previous.addNameUsage()

    def addLoopUsage(self):
        self.loop_usages += 1

        for previous in self.previous:
            previous.addPotentialUsage()
            previous.addLoopUsage()

    def addPotentialUsage(self):
        old = self.has_potential_usages

        if not old:
            self.has_potential_usages = True

            for previous in self.previous:
                previous.addPotentialUsage()

    def hasShapeDictionaryExact(self):
        for previous in self.previous:
            if not previous.hasShapeDictionaryExact():
                return False

        return True
