#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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

from abc import abstractmethod

from nuitka.__past__ import getMetaClassBase, iterItems
from nuitka.nodes.shapes.BuiltinTypeShapes import tshape_dict
from nuitka.nodes.shapes.StandardShapes import tshape_unknown
from nuitka.utils import Utils
from nuitka.utils.InstanceCounters import (
    counted_del,
    counted_init,
    isCountingInstances,
)

complete = False


class Variable(getMetaClassBase("Variable")):

    # We will need all of these attributes, since we track the global
    # state and cache some decisions as attributes. TODO: But in some
    # cases, part of the these might be moved to the outside.
    __slots__ = (
        "variable_name",
        "owner",
        "version_number",
        "shared_users",
        "traces",
        "users",
        "writers",
    )

    @counted_init
    def __init__(self, owner, variable_name):
        assert type(variable_name) is str, variable_name
        assert type(owner) not in (tuple, list), owner

        self.variable_name = variable_name
        self.owner = owner

        self.version_number = 0

        self.shared_users = False

        self.traces = set()

        # Derived from all traces.
        self.users = None
        self.writers = None

    if isCountingInstances():
        __del__ = counted_del()

    def finalize(self):
        del self.users
        del self.writers
        del self.traces
        del self.owner

    def __repr__(self):
        return "<%s '%s' of '%s'>" % (
            self.__class__.__name__,
            self.variable_name,
            self.owner.getName(),
        )

    @abstractmethod
    def getVariableType(self):
        pass

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

    @staticmethod
    def isLocalVariable():
        return False

    @staticmethod
    def isParameterVariable():
        return False

    @staticmethod
    def isModuleVariable():
        return False

    @staticmethod
    def isIncompleteModuleVariable():
        return False

    @staticmethod
    def isTempVariable():
        return False

    @staticmethod
    def isTempVariableBool():
        return False

    @staticmethod
    def isLocalsDictVariable():
        return False

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

            _variables_in_shared_scopes.add(self)

    def isSharedTechnically(self):
        if not self.shared_users:
            return False

        if not self.users:
            return False

        owner = self.owner.getEntryPoint()

        for user in self.users:
            user = user.getEntryPoint()

            while user is not owner and (
                (user.isExpressionFunctionBody() and not user.needsCreation())
                or user.isExpressionClassBodyBase()
            ):
                user = user.getParentVariableProvider()

            if user is not owner:
                return True

        return False

    def addTrace(self, variable_trace):
        self.traces.add(variable_trace)

    def removeTrace(self, variable_trace):
        self.traces.remove(variable_trace)

    def getTraces(self):
        """For debugging only"""
        return self.traces

    def updateUsageState(self):
        writers = set()
        users = set()

        for trace in self.traces:
            owner = trace.owner
            users.add(owner)

            if trace.isAssignTrace():
                writers.add(owner)
            elif trace.isDeletedTrace() and owner is not self.owner:
                writers.add(owner)

        self.writers = writers
        self.users = users

    def hasAccessesOutsideOf(self, provider):
        if not self.owner.locals_scope.complete:
            return None
        elif self.users is None:
            return False
        elif provider in self.users:
            return len(self.users) > 1
        else:
            return bool(self.users)

    def hasWritersOutsideOf(self, provider):
        if not self.owner.locals_scope.complete:
            return None
        elif self.writers is None:
            return False
        elif provider in self.writers:
            return len(self.writers) > 1
        else:
            return bool(self.writers)

    def getMatchingAssignTrace(self, assign_node):
        for trace in self.traces:
            if trace.isAssignTrace() and trace.getAssignNode() is assign_node:
                return trace

        return None

    def getMatchingUnescapedAssignTrace(self, assign_node):
        found = None
        for trace in self.traces:
            if trace.isAssignTrace() and trace.getAssignNode() is assign_node:
                found = trace
            if trace.isEscapeTrace():
                return None

        return found

    def getMatchingDelTrace(self, del_node):
        for trace in self.traces:
            if trace.isDeletedTrace() and trace.getDelNode() is del_node:
                return trace

        return None

    def getTypeShapes(self):
        result = set()

        for trace in self.traces:
            if trace.isAssignTrace():
                result.add(trace.getAssignNode().getTypeShape())
            elif trace.isUnknownTrace():
                result.add(tshape_unknown)
            elif trace.isEscapeTrace():
                result.add(tshape_unknown)
            elif trace.isInitTrace():
                result.add(tshape_unknown)
            elif trace.isUnassignedTrace():
                pass
            elif trace.isMergeTrace():
                pass
            # TODO: Remove this and be not unknown.
            elif trace.isLoopTrace():
                trace.getTypeShape().emitAlternatives(result.add)
            else:
                assert False, trace

        return result

    @staticmethod
    def onControlFlowEscape(trace_collection):
        """Mark the variable as escaped or unknown, or keep it depending on variable type."""

    def removeKnowledge(self, trace_collection):
        """Remove knowledge for the variable marking as unknown or escaped."""
        trace_collection.markActiveVariableAsEscaped(self)

    def removeAllKnowledge(self, trace_collection):
        """Remove all knowledge for the variable marking as unknown, or keep it depending on variable type."""
        trace_collection.markActiveVariableAsUnknown(self)


class LocalVariable(Variable):
    __slots__ = ()

    def __init__(self, owner, variable_name):
        Variable.__init__(self, owner=owner, variable_name=variable_name)

    @staticmethod
    def isLocalVariable():
        return True

    def initVariable(self, trace_collection):
        """Initialize variable in trace collection state."""
        return trace_collection.initVariableUninitialized(self)

    if str is not bytes:

        def onControlFlowEscape(self, trace_collection):
            if self.hasWritersOutsideOf(trace_collection.owner) is not False:
                trace_collection.markClosureVariableAsUnknown(self)
            elif self.hasAccessesOutsideOf(trace_collection.owner) is not False:
                trace_collection.markActiveVariableAsEscaped(self)

    else:

        def onControlFlowEscape(self, trace_collection):
            if self.hasAccessesOutsideOf(trace_collection.owner) is not False:
                trace_collection.markActiveVariableAsEscaped(self)

    @staticmethod
    def getVariableType():
        return "object"


class ParameterVariable(LocalVariable):
    __slots__ = ()

    def __init__(self, owner, parameter_name):
        LocalVariable.__init__(self, owner=owner, variable_name=parameter_name)

    def getDescription(self):
        return "parameter variable '%s'" % self.variable_name

    @staticmethod
    def isParameterVariable():
        return True

    def initVariable(self, trace_collection):
        """Initialize variable in trace collection state."""
        return trace_collection.initVariableInit(self)


class ModuleVariable(Variable):
    __slots__ = ()

    def __init__(self, module, variable_name):
        assert type(variable_name) is str, repr(variable_name)
        assert module.isCompiledPythonModule()

        Variable.__init__(self, owner=module, variable_name=variable_name)

    def __repr__(self):
        return "<ModuleVariable '%s' of '%s'>" % (
            self.variable_name,
            self.owner.getFullName(),
        )

    def getDescription(self):
        return "global variable '%s'" % self.variable_name

    @staticmethod
    def isModuleVariable():
        return True

    def initVariable(self, trace_collection):
        """Initialize variable in trace collection state."""
        return trace_collection.initVariableModule(self)

    def onControlFlowEscape(self, trace_collection):
        trace_collection.markActiveVariableAsUnknown(self)

    def removeKnowledge(self, trace_collection):
        """Remove knowledge for the variable marking as unknown or escaped."""
        trace_collection.markActiveVariableAsUnknown(self)

    def isIncompleteModuleVariable(self):
        return not self.owner.locals_scope.complete

    def hasDefiniteWrites(self):
        if not self.owner.locals_scope.complete:
            return None
        else:
            return bool(self.writers)

    def getModule(self):
        return self.owner

    @staticmethod
    def getVariableType():
        return "object"


class TempVariable(Variable):
    __slots__ = ()

    def __init__(self, owner, variable_name):
        Variable.__init__(self, owner=owner, variable_name=variable_name)

    def getDescription(self):
        return "temp variable '%s'" % self.variable_name

    @staticmethod
    def isTempVariable():
        return True

    @staticmethod
    def getVariableType():
        return "object"

    def initVariable(self, trace_collection):
        """Initialize variable in trace collection state."""
        return trace_collection.initVariableUninitialized(self)

    @staticmethod
    def removeAllKnowledge(trace_collection):
        """Remove all knowledge for the variable marking as unknown, or keep it depending on variable type."""
        # For temporary variables, the knowledge is not by name, so never gets
        # lost to outside star imports or exec/eval uses.


class TempVariableBool(TempVariable):
    __slots__ = ()

    def getDescription(self):
        return "temp bool variable '%s'" % self.variable_name

    @staticmethod
    def isTempVariableBool():
        return True

    @staticmethod
    def getVariableType():
        return "bool"


class LocalsDictVariable(Variable):
    __slots__ = ()

    def __init__(self, owner, variable_name):
        Variable.__init__(self, owner=owner, variable_name=variable_name)

    @staticmethod
    def isLocalsDictVariable():
        return True

    @staticmethod
    def getVariableType():
        return "object"

    def initVariable(self, trace_collection):
        """Initialize variable in trace collection state."""
        if self.owner.getTypeShape() is tshape_dict:
            return trace_collection.initVariableUninitialized(self)
        else:
            return trace_collection.initVariableUnknown(self)


def updateVariablesFromCollection(old_collection, new_collection, source_ref):
    # After removing/adding traces, we need to pre-compute the users state
    # information.
    touched_variables = set()
    loop_trace_removal = set()

    if old_collection is not None:
        for (variable, _version), variable_trace in iterItems(
            old_collection.getVariableTracesAll()
        ):
            variable.removeTrace(variable_trace)
            touched_variables.add(variable)

            if variable_trace.isLoopTrace():
                loop_trace_removal.add(variable)

    if new_collection is not None:
        for (variable, _version), variable_trace in iterItems(
            new_collection.getVariableTracesAll()
        ):
            variable.addTrace(variable_trace)
            touched_variables.add(variable)

            if variable_trace.isLoopTrace():
                if variable in loop_trace_removal:
                    loop_trace_removal.remove(variable)

        # Release the memory, and prevent the "active" state from being ever
        # inspected, it's useless now.
        new_collection.variable_actives.clear()
        del new_collection.variable_actives

    for variable in touched_variables:
        variable.updateUsageState()

    if loop_trace_removal:
        if new_collection is not None:
            new_collection.signalChange(
                "var_usage",
                source_ref,
                lambda: "Loop variable '%s' usage ceased."
                % ",".join(variable.getName() for variable in loop_trace_removal),
            )


# To detect the Python2 shared variable deletion, that would be a syntax
# error
_variables_in_shared_scopes = set()


def isSharedAmongScopes(variable):
    return variable in _variables_in_shared_scopes


def releaseSharedScopeInformation(tree):
    # Singleton, pylint: disable=global-statement

    assert tree.isCompiledPythonModule()

    global _variables_in_shared_scopes
    _variables_in_shared_scopes = set(
        variable
        for variable in _variables_in_shared_scopes
        if variable.getOwner().getParentModule() is not tree
    )
