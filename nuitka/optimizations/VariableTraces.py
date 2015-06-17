#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Variable trace objects.

Variable traces indicate the flow of variables and merges their versions for
the SSA (Single State Assignment) form being used in Nuitka.

Variable version can start as:

* Unknown (maybe initialized, maybe not, we cannot know)
* Uninit (definitely not initialized, first version, or after "del" statement)
* Init (definitely initialized, e.g. parameter variables)
* Merge (result of diverged code paths)

"""


from logging import debug

from nuitka.utils import InstanceCounters


class VariableTraceBase:
    @InstanceCounters.counted_init
    def __init__(self, variable, version, previous):
        self.variable = variable
        self.version = version

        # Definite usage indicator.
        self.has_usages = False

        # Potential usages indicator that an assignment value may be used.
        self.has_potential_usages = False

        # If False, this indicates the trace has no explicit releases.
        self.has_releases = False

        # If False, this indicates that the value is not yet escaped.
        self.is_escaped = False

        # Previous trace this is replacing.
        self.previous = previous

    __del__ = InstanceCounters.counted_del()

    def getVariable(self):
        return self.variable

    def getVersion(self):
        return self.version

    def addUsage(self):
        self.has_usages = True

    def addPotentialUsage(self):
        self.has_potential_usages = True

    def addRelease(self):
        self.has_releases = True

    def onValueEscape(self):
        self.is_escaped = True

    def isEscaped(self):
        return self.is_escaped

    def hasDefiniteUsages(self):
        return self.has_usages

    def hasPotentialUsages(self):
        return self.has_potential_usages

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
        # TODO: Temporarily disable far reaching of assumptions, until value
        # escaping can be trusted.
        if self.variable.isModuleVariable() or \
           self.variable.isSharedTechnically():
            return False

        # Merge traces have this overloaded.

        return self.isInitTrace() or self.isAssignTrace()

    def mustNotHaveValue(self):
        if self.variable.isModuleVariable() or \
           self.variable.isSharedTechnically():
            return False

        return self.isUninitTrace()

    def getReplacementNode(self, usage):
        # Virtual method, pylint: disable=R0201,W0613

        return None


class VariableTraceUninit(VariableTraceBase):
    def __init__(self, variable, version, previous):
        VariableTraceBase.__init__(
            self,
            variable = variable,
            version  = version,
            previous = previous
        )

    def __repr__(self):
        return "<VariableTraceUninit {variable} {version}>".format(
            variable = self.variable,
            version  = self.version
        )

    @staticmethod
    def isUninitTrace():
        return True

    def dump(self):
        debug(
            "Trace of %s %d:",
            self.variable,
            self.version
        )
        debug("  Starts out uninitialized")

        if self.has_usages:
            debug("  -> has usages")

        if self.is_escaped:
            debug("  -> value escapes")

        if self.has_releases:
            debug("   -> has released")


class VariableTraceInit(VariableTraceBase):
    def __init__(self, variable, version):
        VariableTraceBase.__init__(
            self,
            variable = variable,
            version  = version,
            previous = None
        )

    def __repr__(self):
        return "<VariableTraceInit {variable} {version}>".format(
            variable = self.variable,
            version  = self.version
        )

    def dump(self):
        debug(
            "Trace of %s %d:",
            self.variable,
            self.version
        )
        debug("  Starts initialized")

        if self.has_usages:
            debug("  -> has usages")

        if self.is_escaped:
            debug("  -> value escapes")

        if self.has_releases:
            debug("   -> has released")

    @staticmethod
    def isInitTrace():
        return True


class VariableTraceUnknown(VariableTraceBase):
    def __init__(self, variable, version, previous):
        VariableTraceBase.__init__(
            self,
            variable = variable,
            version  = version,
            previous = previous
        )

    def __repr__(self):
        return "<VariableTraceUnknown {variable} {version}>".format(
            variable = self.variable,
            version  = self.version
        )

    def dump(self):
        debug(
            "Trace of %s %d:",
            self.variable,
            self.version
        )
        debug("  Starts unknown")

        if self.has_usages:
            debug("  -> has usages")

        if self.is_escaped:
            debug("  -> value escapes")

        if self.has_releases:
            debug("   -> has released")

    @staticmethod
    def isUnknownTrace():
        return True

    def addUsage(self):
        self.has_usages = True

        if self.previous is not None:
            self.previous.addPotentialUsage()

    def addPotentialUsage(self):
        old = self.has_potential_usages

        if not old:
            self.has_potential_usages = True

            if self.previous is not None:
                self.previous.addPotentialUsage()


class VariableTraceAssign(VariableTraceBase):
    def __init__(self, assign_node, variable, version, previous):
        VariableTraceBase.__init__(
            self,
            variable = variable,
            version  = version,
            previous = previous
        )

        self.assign_node = assign_node
        self.replace_it = None

    def __repr__(self):
        return """\
<VariableTraceAssign {variable} {version} at {source_ref}>""".format(
            variable   = self.variable,
            version    = self.version,
            source_ref = self.assign_node.getSourceReference().getAsString()
        )

    def dump(self):
        debug("Trace of %s %d:",
            self.variable,
            self.version)
        debug("  Starts assigned")

        if self.has_usages:
            debug("  -> has usages")

        if self.is_escaped:
            debug("  -> value escapes")

        if self.has_releases:
            debug("   -> has released")

    @staticmethod
    def isAssignTrace():
        return True

    def getAssignNode(self):
        return self.assign_node

    def setReplacementNode(self, replacement):
        self.replace_it = replacement

    def getReplacementNode(self, usage):

        if self.replace_it is not None:
            return self.replace_it.makeCloneAt(
                self.assign_node.getSourceReference()
            )
        else:
            return None


class VariableTraceMerge(VariableTraceBase):
    """ Merge of two traces.

        Happens at the end of two conditional blocks. This is "phi" in
        SSA theory.
    """
    def __init__(self, variable, version, trace_yes, trace_no):
        assert trace_no is not trace_yes, (variable, version, trace_no)

        VariableTraceBase.__init__(
            self,
            variable = variable,
            version  = version,
            previous = (trace_yes, trace_no)
        )

    @staticmethod
    def isMergeTrace():
        return True

    def dump(self):
        debug(
            "Trace of %s %d:",
            self.variable,
            self.version
        )
        debug(
            "  Merge of %s <-> %s",
            self.previous[0],
            self.previous[1]
        )

    def mustHaveValue(self):
        # TODO: Temporarily disable far reaching of assumptions, until value
        # escaping can be trusted.
        if self.variable.isModuleVariable() or \
           self.variable.isSharedTechnically():
            return False

        for previous in self.previous:
            if not previous.isInitTrace() and not previous.isAssignTrace():
                return False

        return True

    def mustNotHaveValue(self):
        if self.variable.isModuleVariable() or \
           self.variable.isSharedTechnically():
            return False

        for previous in self.previous:
            if not previous.isUninitTrace():
                return False

        return True

    def addUsage(self):
        self.has_usages = True

        a, b = self.previous

        a.addPotentialUsage()
        b.addPotentialUsage()

    def addPotentialUsage(self):
        old = self.has_potential_usages

        if not old:
            self.has_potential_usages = True

            a, b = self.previous

            a.addPotentialUsage()
            b.addPotentialUsage()


class VariableTraceMergeMultiple(VariableTraceBase):
    """ Merge of two or more traces.

        Happens at the end of conditional blocks. This is "phi" in
        SSA theory. Also used for merging multiple "return", "break" or
        "continue" exits.
    """
    def __init__(self, variable, version, traces):
        VariableTraceBase.__init__(
            self,
            variable = variable,
            version  = version,
            previous = tuple(traces)
        )

    @staticmethod
    def isMergeTrace():
        return True

    def dump(self):
        debug(
            "Trace of %s %d:",
            self.variable,
            self.version
        )

        debug(
            "  Merge of %s",
            " <-> ".join(self.previous),
        )

    def mustHaveValue(self):
        # TODO: Temporarily disable far reaching of assumptions, until value
        # escaping can be trusted.
        if self.variable.isModuleVariable() or \
           self.variable.isSharedTechnically():
            return False

        for previous in self.previous:
            if not previous.isInitTrace() and not previous.isAssignTrace():
                return False

        return True

    def mustNotHaveValue(self):
        if self.variable.isModuleVariable() or \
           self.variable.isSharedTechnically():
            return False

        for previous in self.previous:
            if not previous.isUninitTrace():
                return False

        return True

    def addUsage(self):
        self.has_usages = True

        for previous in self.previous:
            previous.addPotentialUsage()

    def addPotentialUsage(self):
        old = self.has_potential_usages

        if not old:
            self.has_potential_usages = True

            for previous in self.previous:
                previous.addPotentialUsage()
