#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka import Variables
from nuitka.containers.odict import OrderedDict
from nuitka.utils.InstanceCounters import counted_del, counted_init

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
    assert locals_name not in locals_dict_handles, locals_name

    locals_dict_handles[locals_name] = getLocalsDictType(kind)(
        locals_name=locals_name, owner=owner
    )
    return locals_dict_handles[locals_name]


def getLocalsDictHandles():
    return locals_dict_handles


class LocalsDictHandleBase(object):
    __slots__ = (
        "locals_name",
        # TODO: Specialize what the kinds really use.
        "variables",
        "local_variables",
        "providing",
        "mark_for_propagation",
        "propagation",
        "owner",
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

        # Can this be eliminated through replacement of temporary variables
        self.mark_for_propagation = False

        self.propagation = None

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

    def getProvidedVariables(self):
        return self.providing.values()

    def registerProvidedVariable(self, variable):
        variable_name = variable.getName()

        self.providing[variable_name] = variable

    def unregisterProvidedVariable(self, variable):
        """ Remove provided variable, e.g. because it became unused. """

        variable_name = variable.getName()

        if variable_name in self.providing:
            del self.providing[variable_name]

    registerClosureVariable = registerProvidedVariable
    unregisterClosureVariable = unregisterProvidedVariable

    def hasProvidedVariable(self, variable_name):
        """ Test if a variable is provided. """

        return variable_name in self.providing

    def getProvidedVariable(self, variable_name):
        """ Test if a variable is provided. """

        return self.providing[variable_name]

    def getLocalsRelevantVariables(self):
        """ The variables relevant to locals. """

        return self.providing.values()

    def getLocalsDictVariable(self, variable_name):
        if variable_name not in self.variables:
            result = Variables.LocalsDictVariable(
                owner=self, variable_name=variable_name
            )

            self.variables[variable_name] = result

        return self.variables[variable_name]

    # TODO: Have variable ownership moved to the locals scope, so owner becomes not needed here.
    def getLocalVariable(self, owner, variable_name):
        if variable_name not in self.local_variables:
            result = Variables.LocalVariable(owner=owner, variable_name=variable_name)

            self.local_variables[variable_name] = result

        return self.local_variables[variable_name]

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


class LocalsDictHandle(LocalsDictHandleBase):
    """ Locals dict for a Python class with mere dict. """

    __slots__ = ()

    @staticmethod
    def isClassScope():
        return True

    @staticmethod
    def getMappingValueShape(variable):
        # We don't yet track dictionaries, let alone mapping values.
        # pylint: disable=unused-argument
        return tshape_unknown


class LocalsMappingHandle(LocalsDictHandle):
    """Locals dict of a Python3 class with a mapping."""

    __slots__ = ()

    @staticmethod
    def getTypeShape():
        # TODO: Make mapping available for this.
        return tshape_unknown

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

    @staticmethod
    def isUnoptimizedFunctionScope():
        return False


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
