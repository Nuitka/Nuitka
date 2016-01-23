#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Registry of all variables.

Makes information about variables available. Initially based solely on the
level of what function took what closure, later on the basic of live traces
giving information about what really needs to be closure taken.

"""

from nuitka.utils.InstanceCounters import counted_del, counted_init

# The key is a plain variable object, not a reference. The value is a set
# of information about that variable.
variable_registry = {}


class VariableInformation:
    @counted_init
    def __init__(self, variable):
        self.variable = variable

        self.users = set()
        self.active_users = set()

    def __repr__(self):
        return "<%s object for %s>" % (
            self.__class__.__name__,
            self.variable
        )

    __del__ = counted_del()

    def addUser(self, user):
        self.users.add(user)
        self.active_users.add(user)

    def removeUser(self, user):
        try:
            self.active_users.remove(user)
        except KeyError:
            raise KeyError(self, user)

    def getUsers(self):
        return self.users

    def getActiveUsers(self):
        return self.active_users

    def getTopOwner(self):
        return self.variable.getOwner()


def addVariableUsage(variable, user):
    if variable.isMaybeLocalVariable():
        addVariableUsage(variable.getMaybeVariable(), user)

    if variable not in variable_registry:
        variable_registry[variable] = VariableInformation(variable)

    variable_info = variable_registry[variable]
    variable_info.addUser(user)


def removeVariableUsage(variable, user):
    variable_info = variable_registry[variable]
    variable_info.removeUser(user)


def isSharedAmongScopes(variable):
    variable_info = variable_registry[variable]

    if not variable.isParameterVariable():
        return len(variable_info.users) > 1

    count = 0

    for user in variable_info.users:
        if user.isExpressionGeneratorObjectBody() or \
           user.isExpressionCoroutineObjectBody():
            if variable.getOwner() is user.getParentVariableProvider():
                continue

        count += 1

        if count > 1:
            return True

    return False


def isSharedTechnically(variable):
    variable_info = variable_registry[variable]

    top_owner = variable_info.getTopOwner()

    variable_name = variable.getName()

    for user in variable_info.getActiveUsers():
        # May have been optimized away, but then this would be false.
        assert user.hasVariableName(variable_name), (variable, user)

        while user is not top_owner and \
              (
               (user.isExpressionFunctionBody() and not user.needsCreation()) or \
               user.isExpressionClassBody()
              ):
            user = user.getParentVariableProvider()

        if user is not top_owner:
            return True

    return False


# The key is a variable name, and the value is a set of traces.
variable_traces = {}

class GlobalVariableTrace:
    @counted_init
    def __init__(self):
        self.traces = set()

    __del__ = counted_del()

    def addTrace(self, variable_trace):
        self.traces.add(variable_trace)

    def removeTrace(self, variable_trace):
        self.traces.remove(variable_trace)

    def hasDefiniteWrites(self):
        for trace in self.traces:
            if trace.isAssignTrace():
                return True

        return False

    def getMatchingAssignTrace(self, assign_node):
        for trace in self.traces:
            if trace.isAssignTrace() and trace.getAssignNode() is assign_node:
                return trace

        return None

    def hasWritesOutsideOf(self, provider):
        for trace in self.traces:
            if trace.isAssignTrace():
                if trace.owner is not provider:
                    return True

        return False

    def hasAccessesOutsideOf(self, provider):
        for trace in self.traces:
            if trace.owner is not provider:
                return True

        return False


def updateFromCollection(old_collection, new_collection):
    if old_collection is not None:
        for variable_trace in old_collection.getVariableTracesAll().values():
            variable = variable_trace.getVariable()

            variable_traces[variable].removeTrace(variable_trace)

    if new_collection is not None:
        for variable_trace in new_collection.getVariableTracesAll().values():
            variable = variable_trace.getVariable()

            if variable not in variable_traces:
                variable_traces[variable] = GlobalVariableTrace()

            variable_traces[variable].addTrace(variable_trace)

        # Release the memory, and prevent the "active" state from being ever
        # inspected, it's useless now.
        new_collection.variable_actives.clear()
        del new_collection.variable_actives

complete = False

def getGlobalVariableTrace(variable):
    # Global variable traces are not being handed out, before the first total
    # run was completed.
    if not complete:
        return None

    return variable_traces.get(variable, None)
