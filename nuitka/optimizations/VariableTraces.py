#!/usr/bin/env python
# -*- coding: utf-8 -*-


#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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


"""
Variable trace objects.

Variable traces indicate the flow of variables and merges their versions for
the SSA (Single State Assignment) form being used in Nuitka.

Variable version can start out:

* Unknown (maybe initialized, maybe not
* Uninit (definitely not initialized, first version, or after "del" statement)
* Init (definitely initialized, e.g. parameter variables)
* Merge (result of diverging code paths)

"""


from logging import debug


class VariableTraceBase:
    def __init__(self, variable, version):
        self.variable = variable
        self.version = version

        # List of references.
        self.usages = []

        # List of releases of the node.
        self.releases = []

        # If not None, this indicates the last usage, where the value was not
        # yet escaped. If it is 0, it escaped immediately. Escaping is a one
        # time action.
        self.escaped_at = None

    def isNode(self):
        return False

    def getVariable(self):
        return self.variable

    def getVersion(self):
        return self.version

    def addUsage(self, ref_node):
        self.usages.append(ref_node)

    def addRelease(self, release_node):
        self.releases.append(release_node)

    def onValueEscape(self):
        self.escaped_at = len(self.usages)

    def isEscaped(self):
        return self.escaped_at is not None

    def getPotentialUsages(self):
        return self.usages

    def getDefiniteUsages(self):
        return self.usages

    def getReleases(self):
        return self.releases

    def isAssignTrace(self):
        return False

    def isUninitTrace(self):
        return False

    def isUnknownTrace(self):
        return False

    def isMergeTrace(self):
        return False


class VariableUninitTrace(VariableTraceBase):
    def __init__(self, variable, version):
        VariableTraceBase.__init__(self, variable=variable, version=version)

    def __repr__( self ):
        return "<VariableUninitTrace {} {}>".format(self.variable, self.version)

    def isUninitTrace(self):
        return True

    def dump(self):
        debug("Trace of %s %d:", self.variable, self.version)
        debug("  Starts out uninitialized")

        for count, usage in enumerate(self.usages):
            if count == self.escaped_at:
                debug("  Escaped value")

            debug("  Used at %s", usage)


class VariableUnknownTrace( VariableTraceBase ):
    def __init__( self, variable, version ):
        VariableTraceBase.__init__(self, variable=variable, version=version)

    def __repr__(self):
        return "<VariableUnknownTrace {} {}>".format(self.variable,
                                                     self.version)

    def dump( self ):
        debug("Trace of %s %d:", self.variable, self.version)
        debug("  Starts unknown")

        for count, usage in enumerate(self.usages):
            if count == self.escaped_at:
                debug("  Escaped value")

            debug("  Used at %s", usage)

    def isUnknownTrace(self):
        return True


class VariableAssignTrace(VariableTraceBase):
    def __init__(self, assign_node, variable, version):
        VariableTraceBase.__init__(self, variable=variable, version=version)

        self.assign_node = assign_node

    def __repr__(self):
        return "<VariableAssignTrace {} {} at {}>".format(self.variable,
                            self.version, self.assign_node.getSourceReference())

    def dump(self):
        debug("Trace of %s %d:", self.variable, self.version)

        for count, usage in enumerate(self.usages):
            if count == self.escaped_at:
                debug("  Escaped value")

            debug("  Used at %s", usage)

    def isAssignTrace(self):
        return True

    def getAssignNode(self):
        return self.assign_node


class VariableMergeTrace( VariableTraceBase ):
    def __init__(self, variable, version, trace_yes, trace_no):
        assert trace_no is not trace_yes, (variable, version, trace_no)

        VariableTraceBase.__init__(self, variable=variable, version=version)

        self.trace_yes = trace_yes
        self.trace_no = trace_no

        self.forwarded = True

    def isMergeTrace(self):
        return True

    def addUsage(self, ref_node):
        if not self.usages:
            # Merging is usage.
            self.trace_yes.addUsage(self)
            if self.trace_no is not None:
                self.trace_no.addUsage(self)

        VariableTraceBase.addUsage(self, ref_node)

    def getPotentialUsages(self):
        assert False

    def dump(self):
        debug("Trace of %s %d:", self.variable, self.version)
        debug("  Merge of %s <-> %s", self.trace_yes, self.trace_no)
