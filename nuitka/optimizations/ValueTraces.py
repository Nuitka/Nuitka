#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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

"""


from logging import debug

from nuitka.utils import InstanceCounters


class ValueTraceBase(object):
    # We are going to have many instance attributes

    __slots__ = (
        "owner", "usage_count", "has_potential_usages",
        "name_usages", "closure_usages", "is_escaped", "previous"
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

        self.closure_usages = False

        # If False, this indicates that the value is not yet escaped.
        self.is_escaped = False

        # Previous trace this is replacing.
        self.previous = previous

    __del__ = InstanceCounters.counted_del()

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
        ValueTraceBase.__init__(
            self,
            owner    = owner,
            previous = previous
        )

    def __repr__(self):
        return "<ValueTraceUninit of {owner}>".format(
            owner = self.owner
        )

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
        ValueTraceBase.__init__(
            self,
            owner    = owner,
            previous = None
        )

    def __repr__(self):
        return "<ValueTraceInit of {owner}>".format(
            owner = self.owner
        )

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
    def __init__(self, owner, previous):
        ValueTraceBase.__init__(
            self,
            owner    = owner,
            previous = previous
        )

    def __repr__(self):
        return "<ValueTraceUnknown of {owner}>".format(
            owner = self.owner
        )

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

    def addPotentialUsage(self):
        old = self.has_potential_usages

        if not old:
            self.has_potential_usages = True

            if self.previous is not None:
                self.previous.addPotentialUsage()


class ValueTraceAssign(ValueTraceBase):
    __slots__ = ("assign_node", "replace_it")

    def __init__(self, owner, assign_node, previous):
        ValueTraceBase.__init__(
            self,
            owner    = owner,
            previous = previous
        )

        self.assign_node = assign_node
        self.replace_it = None

    def __repr__(self):
        return "<ValueTraceAssign at {source_ref} of {value}>".format(
            source_ref = self.assign_node.getSourceReference().getAsString(),
            value      = self.assign_node.getAssignSource()
        )

    def dump(self):
        debug("  Starts assigned")

        if self.usage_count:
            debug("  -> has %s usages" % self.usage_count)

        if self.is_escaped:
            debug("  -> value escapes")

    @staticmethod
    def isAssignTrace():
        return True

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
        ValueTraceBase.__init__(
            self,
            owner    = traces[0].owner,
            previous = tuple(traces)
        )

    def __repr__(self):
        return """\
<ValueTraceMerge of {previous}>""".format(
            previous = self.previous
        )

    @staticmethod
    def isMergeTrace():
        return True

    def dump(self):
        debug(
            "  Merge of %s",
            " <-> ".join(self.previous),
        )

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


class ValueTraceLoopMerge(ValueTraceBase):
    """ Merge of loop wrap around with loop start value.

        Happens at the start of loop blocks. This is for loop closed SSA, to
        make it clear, that the entered value, cannot be trusted inside the
        loop.

        They will start out with just one previous, and later be updated with
        all of the variable versions at loop continue times.
    """

    __slots__ = ("loop_finished",)

    def __init__(self, previous):
        ValueTraceBase.__init__(
            self,
            owner    = previous.owner,
            previous = previous
        )

        self.loop_finished = False

        previous.addPotentialUsage()

    def hasDefiniteUsages(self):
        if not self.loop_finished:
            return True

        return self.usage_count > 0

    def hasPotentialUsages(self):
        if not self.loop_finished:
            return True

        return self.has_potential_usages

    def getNameUsageCount(self):
        if not self.loop_finished:
            return 10000

        return self.name_usages

    def getPrevious(self):
        assert self.loop_finished

        return self.previous

    @staticmethod
    def isMergeTrace():
        return True

    def addLoopContinueTraces(self, continue_traces):
        self.previous.addPotentialUsage()

        for continue_trace in continue_traces:
            continue_trace.addPotentialUsage()

        self.previous = (self.previous,) + tuple(continue_traces)
