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
""" This module maintains the locals dict handles. """

from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.Errors import NuitkaOptimizationError
from nuitka.PythonVersions import python_version
from nuitka.utils.InstanceCounters import (
    counted_del,
    counted_init,
    isCountingInstances,
)
from nuitka.Variables import LocalsDictVariable, LocalVariable

from .shapes.BuiltinTypeShapes import tshape_dict
from .shapes.StandardShapes import tshape_unknown

locals_dict_handles = {}


def getLocalsDictType(kind):

    if kind == "python2_function_exec":
        locals_scope = LocalsDictExecHandle
    elif kind == "python_function":
        locals_scope = LocalsDictFunctionHandle
    elif kind == "python3_class":
        locals_scope = LocalsMappingHandle
    elif kind == "python2_class":
        locals_scope = LocalsDictHandle
    elif kind == "module_dict":
        locals_scope = GlobalsDictHandle
    else:
        assert False, kind

    return locals_scope


def getLocalsDictHandle(locals_name, kind, owner):
    # Duplicates are bad and cannot be tolerated.
    if locals_name in locals_dict_handles:
        raise NuitkaOptimizationError(
            "duplicate locals name",
            locals_name,
            kind,
            owner.getFullName(),
            owner.getCompileTimeFilename(),
            locals_dict_handles[locals_name].owner.getFullName(),
            locals_dict_handles[locals_name].owner.getCompileTimeFilename(),
        )

    locals_dict_handles[locals_name] = getLocalsDictType(kind)(
        locals_name=locals_name, owner=owner
    )
    return locals_dict_handles[locals_name]


class LocalsDictHandleBase(object):
    # TODO: Might remove some of these later, pylint: disable=too-many-instance-attributes

    __slots__ = (
        "locals_name",
        # TODO: Specialize what the kinds really use what.
        "variables",
        "local_variables",
        "providing",
        "mark_for_propagation",
        "prevented_propagation",
        "propagation",
        "owner",
        "complete",
    )

    @counted_init
    def __init__(self, locals_name, owner):
        self.locals_name = locals_name
        self.owner = owner

        # For locals dict variables in this scope.
        self.variables = {}

        # For local variables in this scope.
        self.local_variables = {}
        self.providing = OrderedDict()

        # Can this be eliminated through replacement of temporary variables, or has
        # e.g. the use of locals prevented this, which it should in classes.
        self.mark_for_propagation = False

        self.propagation = None

        self.complete = False

    if isCountingInstances():
        __del__ = counted_del()

    def __repr__(self):
        return "<%s of %s>" % (self.__class__.__name__, self.locals_name)

    def getName(self):
        return self.locals_name

    def makeClone(self, new_owner):
        count = 1

        # Make it unique.
        while 1:
            locals_name = self.locals_name + "_inline_%d" % count

            if locals_name not in locals_dict_handles:
                break

            count += 1

        result = self.__class__(locals_name=locals_name, owner=new_owner)

        variable_translation = {}

        # Clone variables as well.
        for variable_name, variable in self.variables.items():
            new_variable = variable.makeClone(new_owner=new_owner)

            variable_translation[variable] = new_variable
            result.variables[variable_name] = new_variable

        for variable_name, variable in self.local_variables.items():
            new_variable = variable.makeClone(new_owner=new_owner)

            variable_translation[variable] = new_variable
            result.local_variables[variable_name] = new_variable

        result.providing = OrderedDict()

        for variable_name, variable in self.providing.items():
            if variable in variable_translation:
                new_variable = variable_translation[variable]
            else:
                new_variable = variable.makeClone(new_owner=new_owner)
                variable_translation[variable] = new_variable

            result.providing[variable_name] = new_variable

        return result, variable_translation

    @staticmethod
    def getTypeShape():
        return tshape_dict

    @staticmethod
    def hasShapeDictionaryExact():
        return True

    def getCodeName(self):
        return self.locals_name

    @staticmethod
    def isModuleScope():
        return False

    @staticmethod
    def isClassScope():
        return False

    @staticmethod
    def isFunctionScope():
        return False

    @staticmethod
    def isUnoptimizedFunctionScope():
        return False

    def getProvidedVariables(self):
        return self.providing.values()

    def registerProvidedVariable(self, variable):
        variable_name = variable.getName()

        self.providing[variable_name] = variable

    def unregisterProvidedVariable(self, variable):
        """Remove provided variable, e.g. because it became unused."""

        variable_name = variable.getName()

        if variable_name in self.providing:
            del self.providing[variable_name]

    registerClosureVariable = registerProvidedVariable
    unregisterClosureVariable = unregisterProvidedVariable

    def hasProvidedVariable(self, variable_name):
        """Test if a variable is provided."""

        return variable_name in self.providing

    def getProvidedVariable(self, variable_name):
        """Test if a variable is provided."""

        return self.providing[variable_name]

    def getLocalsRelevantVariables(self):
        """The variables relevant to locals."""

        return self.providing.values()

    def getLocalsDictVariable(self, variable_name):
        if variable_name not in self.variables:
            result = LocalsDictVariable(owner=self, variable_name=variable_name)

            self.variables[variable_name] = result

        return self.variables[variable_name]

    # TODO: Have variable ownership moved to the locals scope, so owner becomes not needed here.
    def getLocalVariable(self, owner, variable_name):
        if variable_name not in self.local_variables:
            result = LocalVariable(owner=owner, variable_name=variable_name)

            self.local_variables[variable_name] = result

        return self.local_variables[variable_name]

    @staticmethod
    def preventLocalsDictPropagation():
        pass

    @staticmethod
    def isPreventedPropagation():
        return False

    def markForLocalsDictPropagation(self):
        self.mark_for_propagation = True

    def isMarkedForPropagation(self):
        return self.mark_for_propagation

    def allocateTempReplacementVariable(self, trace_collection, variable_name):
        if self.propagation is None:
            self.propagation = OrderedDict()

        if variable_name not in self.propagation:
            provider = trace_collection.getOwner()

            self.propagation[variable_name] = provider.allocateTempVariable(
                temp_scope=None, name=self.getCodeName() + "_key_" + variable_name
            )

        return self.propagation[variable_name]

    def getPropagationVariables(self):
        if self.propagation is None:
            return ()

        return self.propagation

    def finalize(self):
        # Make it unusable when it's become empty, not used.
        self.owner.locals_scope = None
        del self.owner

        del self.propagation
        del self.mark_for_propagation

        for variable in self.variables.values():
            variable.finalize()

        for variable in self.local_variables.values():
            variable.finalize()

        del self.variables
        del self.providing

    def markAsComplete(self, trace_collection):
        self.complete = True

        self._considerUnusedUserLocalVariables(trace_collection)
        self._considerPropagation(trace_collection)

    # TODO: Limited to Python2 classes for now, more overloads need to be added, this
    # ought to be abstract and have variants with TODOs for each of them.
    @staticmethod
    def _considerPropagation(trace_collection):
        """For overload by scope type. Check if this can be replaced."""

    def onPropagationComplete(self):
        self.variables = {}
        self.mark_for_propagation = False

    def _considerUnusedUserLocalVariables(self, trace_collection):
        """Check scope for unused variables."""

        provided = self.getProvidedVariables()
        removals = []

        for variable in provided:
            if (
                variable.isLocalVariable()
                and not variable.isParameterVariable()
                and variable.getOwner() is self.owner
            ):
                empty = trace_collection.hasEmptyTraces(variable)

                if empty:
                    removals.append(variable)

        for variable in removals:
            self.unregisterProvidedVariable(variable)

            trace_collection.signalChange(
                "var_usage",
                self.owner.getSourceReference(),
                message="Remove unused local variable '%s'." % variable.getName(),
            )


class LocalsDictHandle(LocalsDictHandleBase):
    """Locals dict for a Python class with mere dict."""

    __slots__ = ()

    @staticmethod
    def isClassScope():
        return True

    @staticmethod
    def getMappingValueShape(variable):
        # We don't yet track dictionaries, let alone mapping values.
        # pylint: disable=unused-argument
        return tshape_unknown

    def _considerPropagation(self, trace_collection):
        if not self.variables:
            return

        for variable in self.variables.values():
            for variable_trace in variable.traces:
                if variable_trace.inhibitsClassScopeForwardPropagation():
                    return

        trace_collection.signalChange(
            "var_usage",
            self.owner.getSourceReference(),
            message="Forward propagate locals dictionary.",
        )

        self.markForLocalsDictPropagation()


class LocalsMappingHandle(LocalsDictHandle):
    """Locals dict of a Python3 class with a mapping."""

    __slots__ = ("type_shape",)

    # TODO: Removable condition once Python 3.3 support is dropped.
    if python_version >= 0x340:
        __slots__ += ("prevented_propagation",)

    def __init__(self, locals_name, owner):
        LocalsDictHandle.__init__(self, locals_name=locals_name, owner=owner)

        self.type_shape = tshape_unknown

        if python_version >= 0x340:
            self.prevented_propagation = False

    def getTypeShape(self):
        # TODO: Make mapping available for this.
        return self.type_shape

    def setTypeShape(self, type_shape):
        self.type_shape = type_shape

    def hasShapeDictionaryExact(self):
        return self.type_shape is tshape_dict

    if python_version >= 0x340:

        def markAsComplete(self, trace_collection):
            # For this run, it cannot be done yet.
            if self.prevented_propagation:
                # False alarm, this is available.
                self.prevented_propagation = False
                return

            self.complete = True

        def preventLocalsDictPropagation(self):
            self.prevented_propagation = True

        def isPreventedPropagation(self):
            return self.prevented_propagation

    def _considerPropagation(self, trace_collection):
        if not self.variables:
            return

        if self.type_shape is not tshape_dict:
            return

        for variable in self.variables.values():
            for variable_trace in variable.traces:
                if variable_trace.inhibitsClassScopeForwardPropagation():
                    return

        trace_collection.signalChange(
            "var_usage",
            self.owner.getSourceReference(),
            message="Forward propagate locals dictionary.",
        )

        self.markForLocalsDictPropagation()

    @staticmethod
    def isClassScope():
        return True


class LocalsDictExecHandle(LocalsDictHandleBase):
    """Locals dict of a Python2 function with an exec."""

    __slots__ = ("closure_variables",)

    def __init__(self, locals_name, owner):
        LocalsDictHandleBase.__init__(self, locals_name=locals_name, owner=owner)

        self.closure_variables = None

    @staticmethod
    def isFunctionScope():
        return True

    @staticmethod
    def isUnoptimizedFunctionScope():
        return True

    def getLocalsRelevantVariables(self):
        if self.closure_variables is None:
            return self.providing.values()
        else:
            return [
                variable
                for variable in self.providing.values()
                if variable not in self.closure_variables
            ]

            # TODO: What about the ".0" variety, we used to exclude it.

    def registerClosureVariable(self, variable):
        self.registerProvidedVariable(variable)

        if self.closure_variables is None:
            self.closure_variables = set()

        self.closure_variables.add(variable)

    def unregisterClosureVariable(self, variable):
        self.unregisterProvidedVariable(variable)

        variable_name = variable.getName()

        if variable_name in self.providing:
            del self.providing[variable_name]


class LocalsDictFunctionHandle(LocalsDictHandleBase):
    """Locals dict of a Python3 function or Python2 function without an exec."""

    __slots__ = ()

    @staticmethod
    def isFunctionScope():
        return True


class GlobalsDictHandle(LocalsDictHandleBase):
    __slots__ = ("escaped",)

    def __init__(self, locals_name, owner):
        LocalsDictHandleBase.__init__(self, locals_name=locals_name, owner=owner)

        self.escaped = False

    @staticmethod
    def isModuleScope():
        return True

    def markAsEscaped(self):
        self.escaped = True

    def isEscaped(self):
        return self.escaped
