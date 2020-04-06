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
""" Variables link the storage and use of a Python variable together.

Different kinds of variables represent different scopes and owners types,
and their links between each other, i.e. references as in closure or
module variable references.

"""

from nuitka.__past__ import iterItems
from nuitka.nodes.shapes.StandardShapes import tshape_unknown
from nuitka.utils import InstanceCounters, Utils

complete = False


class Variable(object):

    # We will need all of these attributes, since we track the global
    # state and cache some decisions as attributes, pylint: disable=too-many-instance-attributes
    __slots__ = (
        "variable_name",
        "owner",
        "version_number",
        "shared_users",
        "shared_scopes",
        "traces",
        "users",
        "writers",
    )

    @InstanceCounters.counted_init
    def __init__(self, owner, variable_name):
        assert type(variable_name) is str, variable_name
        assert type(owner) not in (tuple, list), owner

        self.variable_name = variable_name
        self.owner = owner

        self.version_number = 0

        self.shared_users = False
        self.shared_scopes = False

        self.traces = set()

        # Derived from all traces.
        self.users = None
        self.writers = None

    __del__ = InstanceCounters.counted_del()

    def finalize(self):
        del self.users
        del self.writers
        del self.traces
        del self.owner

    def getDescription(self):
        return "variable '%s'" % self.variable_name

    def getName(self):
        return self.variable_name

    def getOwner(self):
        return self.owner

    def getEntryPoint(self):
        return self.owner.getEntryPoint()

    def getCodeName(self):
        var_name = self.variable_name
        var_name = var_name.replace(".", "$")
        var_name = Utils.encodeNonAscii(var_name)

        return var_name

    def allocateTargetNumber(self):
        self.version_number += 1

        return self.version_number

    # pylint: disable=no-self-use
    def isLocalVariable(self):
        return False

    def isParameterVariable(self):
        return False

    def isModuleVariable(self):
        return False

    def isTempVariable(self):
        return False

    def isLocalsDictVariable(self):
        return False

    # pylint: enable=R0201

    def addVariableUser(self, user):
        # Update the shared scopes flag.
        if user is not self.owner:
            self.shared_users = True

            # These are not really scopes, just shared uses.
            if (
                user.isExpressionGeneratorObjectBody()
                or user.isExpressionCoroutineObjectBody()
                or user.isExpressionAsyncgenObjectBody()
            ):
                if self.owner is user.getParentVariableProvider():
                    return

            self.shared_scopes = True

    def isSharedAmongScopes(self):
        # TODO: This is only used for Python2, and could be made
        # and optional slot.

        return self.shared_scopes

    def isSharedTechnically(self):
        if not self.shared_users:
            return False

        if not complete:
            return None

        if not self.users:
            return False

        owner = self.owner.getEntryPoint()

        for user in self.users:
            user = user.getEntryPoint()

            while user is not owner and (
                (user.isExpressionFunctionBody() and not user.needsCreation())
                or user.isExpressionClassBody()
            ):
                user = user.getParentVariableProvider()

            if user is not owner:
                return True

        return False

    def addTrace(self, variable_trace):
        self.traces.add(variable_trace)

    def removeTrace(self, variable_trace):
        # Make it unusable, and break GC cycles while at it.
        variable_trace.previous = None

        self.traces.remove(variable_trace)

    def updateUsageState(self):
        writers = set()
        users = set()

        for trace in self.traces:
            owner = trace.owner
            users.add(owner)

            if trace.isAssignTrace():
                writers.add(owner)
            elif trace.isUninitTrace() and owner is not self.owner:
                writers.add(owner)

        self.writers = writers
        self.users = users

    def hasWritesOutsideOf(self, user):
        if not complete:
            return None
        elif self.writers is not None and user in self.writers:
            return len(self.writers) > 1
        else:
            return bool(self.writers)

    def hasAccessesOutsideOf(self, provider):
        if not complete:
            return None
        elif self.users is None:
            return False
        elif provider in self.users:
            return len(self.users) > 1
        else:
            return bool(self.users)

    def hasDefiniteWrites(self):
        if not complete:
            return None
        else:
            return bool(self.writers)

    def getMatchingAssignTrace(self, assign_node):
        for trace in self.traces:
            if trace.isAssignTrace() and trace.getAssignNode() is assign_node:
                return trace

        return None

    def getTypeShapes(self):
        result = set()

        for trace in self.traces:
            if trace.isAssignTrace():
                result.add(trace.getAssignNode().getAssignSource().getTypeShape())
            elif trace.isUnknownTrace():
                result.add(tshape_unknown)
            elif trace.isUninitTrace():
                if trace.hasDefiniteUsages() or trace.hasPotentialUsages():
                    result.add(tshape_unknown)
            elif trace.isInitTrace():
                result.add(tshape_unknown)
            elif trace.isMergeTrace():
                pass
            # TODO: Remove this and be not unknown.
            elif trace.isLoopTrace():
                trace.getTypeShape().emitAlternatives(result.add)
            else:
                assert False, trace

        return result


class LocalVariable(Variable):
    __slots__ = ()

    def __init__(self, owner, variable_name):
        Variable.__init__(self, owner=owner, variable_name=variable_name)

    def __repr__(self):
        return "<%s '%s' of '%s'>" % (
            self.__class__.__name__,
            self.variable_name,
            self.owner.getName(),
        )

    def isLocalVariable(self):
        return True


class ParameterVariable(LocalVariable):
    __slots__ = ()

    def __init__(self, owner, parameter_name):
        LocalVariable.__init__(self, owner=owner, variable_name=parameter_name)

    def getDescription(self):
        return "parameter variable '%s'" % self.variable_name

    def isParameterVariable(self):
        return True


class ModuleVariable(Variable):
    __slots__ = ("module",)

    def __init__(self, module, variable_name):
        assert type(variable_name) is str, repr(variable_name)
        assert module.isCompiledPythonModule()

        Variable.__init__(self, owner=module, variable_name=variable_name)

        self.module = module

    def __repr__(self):
        return "<ModuleVariable '%s' of '%s'>" % (
            self.variable_name,
            self.getModule().getFullName(),
        )

    def getDescription(self):
        return "global variable '%s'" % self.variable_name

    def isModuleVariable(self):
        return True

    def getModule(self):
        return self.module


class TempVariable(Variable):
    __slots__ = ()

    def __init__(self, owner, variable_name):
        Variable.__init__(self, owner=owner, variable_name=variable_name)

    def __repr__(self):
        return "<TempVariable '%s' of '%s'>" % (
            self.getName(),
            self.getOwner().getName(),
        )

    def getDescription(self):
        return "temp variable '%s'" % self.variable_name

    def isTempVariable(self):
        return True


class LocalsDictVariable(Variable):
    __slots__ = ()

    def __init__(self, owner, variable_name):
        Variable.__init__(self, owner=owner, variable_name=variable_name)

    def __repr__(self):
        return "<LocalsDictVariable '%s' of '%s'>" % (
            self.getName(),
            self.getOwner().getName(),
        )

    def isLocalsDictVariable(self):
        return True


def updateVariablesFromCollection(old_collection, new_collection):
    # After removing/adding traces, we need to pre-compute the users state
    # information.
    touched_variables = set()

    if old_collection is not None:
        for (variable, _version), variable_trace in iterItems(
            old_collection.getVariableTracesAll()
        ):
            variable.removeTrace(variable_trace)
            touched_variables.add(variable)

    if new_collection is not None:
        for (variable, _version), variable_trace in iterItems(
            new_collection.getVariableTracesAll()
        ):
            variable.addTrace(variable_trace)
            touched_variables.add(variable)

        # Release the memory, and prevent the "active" state from being ever
        # inspected, it's useless now.
        new_collection.variable_actives.clear()
        del new_collection.variable_actives

    for variable in touched_variables:
        variable.updateUsageState()
