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
""" Registry of all variables.

Makes information about variables available. Initially based solely on the
level of what function took what closure, later on the basic of live traces
giving information about what really needs to be closure taken.

"""

# The key is a plain variable object, not a reference. The value is a set
# of information about that variable.
variable_registry = {}


class VariableInformation:
    def __init__(self, variable):
        self.variable = variable
        self.users = set()

    def addUser(self, user):
        self.users.add(user)

    def getUsers(self):
        return self.users

    def getTopOwner(self):
        return self.variable.getOwner()


def addVariableUsage(variable, user):
    if variable.isMaybeLocalVariable():
        addVariableUsage(variable.getMaybeVariable(), user)

    if variable not in variable_registry:
        variable_registry[variable] = VariableInformation(variable)

    variable_info = variable_registry[variable]
    variable_info.addUser(user)


# TODO: This seems practically unused and not needed.
def isSharedLogically(variable):
    variable_info = variable_registry[variable]

    return len(variable_info.users) > 1


def isSharedTechnically(variable):
    variable_info = variable_registry[variable]

    top_owner = variable_info.getTopOwner()

    for user in variable_info.getUsers():
        # May have been optimized away.
        if variable not in user.getVariables():
            continue

        while user != top_owner and \
              user.isExpressionFunctionBody() and \
              not user.needsCreation() and \
              not user.isGenerator():
            user = user.getParentVariableProvider()

        if user != top_owner:
            return True

    return False


# The key is a variable name, and the value is a set of traces.
variable_traces = {}

variable_traces_full = {}

class GlobalVariableTrace:
    def __init__(self):
        self.traces = set()

    def add(self, variable_trace):
        self.traces.add(variable_trace)

    def hasDefiniteWrites(self):
        for trace in self.traces:
            if trace.isAssignTrace():
                return True

        return False

def addVariableTrace(variable_trace):
    variable = variable_trace.getVariable()

    if variable not in variable_traces:
        variable_traces[variable] = GlobalVariableTrace()

    variable_traces[variable].add(variable_trace)

def startTraversal():
    # Using global here, as this is really a singleton, in the form of a module,
    # pylint: disable=W0603
    global variable_traces_full, variable_traces

    variable_traces_full = variable_traces
    variable_traces = {}

def getGlobalVariableTrace(variable):
    return variable_traces_full.get(variable, None)
