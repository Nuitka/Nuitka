#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Variables link the storage and use of a Python variable together.

Different kinds of variables represent different scopes and owners types,
and their links between each other, i.e. references as in closure or
module variable references.

"""

from abc import abstractmethod

from nuitka.__past__ import iterItems
from nuitka.nodes.shapes.BuiltinTypeShapes import tshape_dict
from nuitka.nodes.shapes.StandardShapes import tshape_unknown
from nuitka.utils.CStrings import encodePythonIdentifierToC
from nuitka.utils.InstanceCounters import (
    counted_del,
    counted_init,
    isCountingInstances,
)
from nuitka.utils.SlotMetaClasses import getMetaClassBase

complete = False


class Variable(getMetaClassBase("Variable", require_slots=True)):
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
        # assert type(variable_name) is str, variable_name
        # assert type(owner) not in (tuple, list), owner

        self.variable_name = variable_name
        self.owner = owner

        self.version_number = 0

        self.shared_users = False

        self.traces = {}

        # Derived from all traces.
        self.writers = set()

    if isCountingInstances():
        __del__ = counted_del()

    def finalize(self):
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

    def getVariableCodeName(self):
        return encodePythonIdentifierToC(self.variable_name)

    def allocateTargetNumber(self):
        self.version_number += 3

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

        if not self.traces:
            return False

        owner = self.owner.getEntryPoint()

        for user in self.traces:
            user = user.getEntryPoint()

            while user is not owner and (
                (user.isExpressionFunctionBody() and not user.needsCreation())
                or user.isExpressionClassBodyBase()
            ):
                user = user.getParentVariableProvider()

            if user is not owner:
                return True

        return False

    def setTracesForUserFirst(self, user, variable_traces):
        self.traces[user] = variable_traces

        for trace in variable_traces.values():
            if trace.isAssignTrace():
                self.writers.add(user)

                break
            if user is not self.owner and trace.isDeletedTrace():
                self.writers.add(user)

                break

    def setTracesForUserUpdate(self, user, variable_traces):
        self.traces[user] = variable_traces

        if user in self.writers:
            for trace in variable_traces.values():
                if trace.isAssignTrace():
                    break
                if user is not self.owner and trace.isDeletedTrace():
                    break
            else:
                self.writers.remove(user)

    def removeTracesForUser(self, user):
        del self.traces[user]

        if user in self.writers:
            self.writers.remove(user)

    def hasEmptyTracesFor(self, user):
        """Do these traces contain any usage."""
        if user in self.traces:
            for trace in self.traces[user].values():
                if trace.isUsingTrace():
                    return False

        return True

    def hasNoWritingTraces(self):
        """Do these traces contain any writes."""

        for traces in self.traces.values():
            for trace in traces.values():
                if trace.isWritingTrace():
                    return False

        return True

    def hasAccessesOutsideOf(self, provider):
        if not self.owner.locals_scope.complete:
            return None
        elif not self.traces:
            return False
        elif provider in self.traces:
            return len(self.traces) > 1
        else:
            return True

    def hasWritersOutsideOf(self, provider):
        if not self.owner.locals_scope.complete:
            # TODO: Maybe this doesn't have to be limited to these types.
            if not self.shared_users and (
                self.isLocalVariable() or self.isTempVariable()
            ):
                return False
            return None
        elif not self.writers:
            return False
        elif provider in self.writers:
            return len(self.writers) > 1
        else:
            return True

    def getMatchingUnescapedAssignTrace(self, assign_node):
        found = None
        for traces in self.traces.values():
            for trace in traces.values():
                if trace.isAssignTrace():
                    if trace.getAssignNode() is assign_node:
                        found = trace
                elif trace.isEscapeTrace():
                    return None

            if found is not None:
                return found

        return found

    def getTypeShapes(self):
        result = set()

        for traces in self.traces.values():
            for trace in traces.values():
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

    def makeClone(self, new_owner):
        return LocalVariable(owner=new_owner, variable_name=self.variable_name)

    @staticmethod
    def isLocalVariable():
        return True

    def initVariableLate(self, trace_collection):
        """Initialize variable in trace collection state."""
        trace_collection.variable_escapable.add(self)
        trace_collection.has_unescaped_variables = True
        return trace_collection.initVariableUninitialized(self, None)

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

    def makeClone(self, new_owner):
        return ParameterVariable(owner=new_owner, parameter_name=self.variable_name)

    def getDescription(self):
        return "parameter variable '%s'" % self.variable_name

    @staticmethod
    def isParameterVariable():
        return True

    def initVariableLate(self, trace_collection):
        """Initialize variable in trace collection state."""
        return trace_collection.initVariableInit(self, None)


class ModuleVariable(Variable):
    __slots__ = ()

    def __init__(self, module, variable_name):
        # assert type(variable_name) is str, repr(variable_name)
        # assert module.isCompiledPythonModule()

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

    def initVariableLate(self, trace_collection):
        """Initialize variable in trace collection state."""
        trace_collection.variable_escapable.add(self)
        trace_collection.has_unescaped_variables = True
        return trace_collection.initVariableModule(self, None)

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
    __slots__ = ("variable_type",)

    def __init__(self, owner, variable_name, variable_type):
        Variable.__init__(self, owner=owner, variable_name=variable_name)

        # TODO: Push this later down to Variable itself.
        self.variable_type = variable_type

    @staticmethod
    def isTempVariable():
        return True

    def getVariableType(self):
        return self.variable_type

    def isTempVariableBool(self):
        return self.variable_type == "bool"

    def getDescription(self):
        return "temp variable '%s'" % self.variable_name

    def initVariableLate(self, trace_collection):
        """Initialize variable in trace collection state."""
        return trace_collection.initVariableUninitialized(self, None)

    @staticmethod
    def removeAllKnowledge(trace_collection):
        """Remove all knowledge for the variable marking as unknown, or keep it depending on variable type."""
        # For temporary variables, the knowledge is not by name, so never gets
        # lost to outside star imports or exec/eval uses.


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

    def initVariableLate(self, trace_collection):
        """Initialize variable in trace collection state."""
        if self.owner.getTypeShape() is tshape_dict:
            return trace_collection.initVariableUninitialized(self, None)
        else:
            return trace_collection.initVariableUnknown(self, None)

    def inhibitsClassScopeForwardPropagation(self):
        for traces in self.traces.values():
            for trace in traces.values():
                if trace.inhibitsClassScopeForwardPropagation():
                    return True

        return False


def _updateVariablesFromCollectionFirst(new_collection):
    for variable, variable_traces in iterItems(new_collection.getVariableTracesAll()):
        variable.setTracesForUserFirst(new_collection.owner, variable_traces)

    # Release the memory, and prevent the "active" state from being ever
    # inspected, it's useless now.
    new_collection.variable_actives.clear()
    del new_collection.variable_actives


def updateVariablesFromCollection(old_collection, new_collection, source_ref):

    if old_collection is None:
        return _updateVariablesFromCollectionFirst(new_collection)

    old_traces = old_collection.getVariableTracesAll()
    new_traces = new_collection.getVariableTracesAll()
    owner = new_collection.owner
    # Release the memory, and prevent the "active" state from being ever
    # inspected, it's useless now.
    new_collection.variable_actives.clear()
    del new_collection.variable_actives

    for variable, variable_traces in iterItems(new_traces):
        variable.setTracesForUserUpdate(owner, variable_traces)

    for variable in old_traces:
        # Remove traces for variables that are not in the new collection unless
        # they are finalized, then we don't need to update them.
        if variable not in new_traces and hasattr(variable, "users"):
            variable.removeTracesForUser(owner)

    if old_collection.loop_variables != new_collection.loop_variables:
        new_collection.signalChange(
            "var_usage",
            source_ref,
            lambda: "Loop variable '%s' usage ceased."
            % ",".join(
                sorted(
                    variable.getName()
                    for variable in (
                        old_collection.loop_variables - new_collection.loop_variables
                    )
                )
            ),
        )


def removeVariablesFromCollection(old_collection):
    if old_collection is not None:
        owner = old_collection.owner

        for variable in old_collection.getVariableTracesAll():
            variable.removeTracesForUser(owner)


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
