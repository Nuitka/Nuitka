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
""" This module maintains the locals dict handles. """

from nuitka import Variables
from nuitka.containers.odict import OrderedDict
from nuitka.utils.InstanceCounters import counted_del, counted_init

from .shapes.BuiltinTypeShapes import ShapeTypeDict
from .shapes.StandardShapes import ShapeUnknown

locals_dict_handles = {}

def setLocalsDictType(locals_dict_name, kind):
    assert locals_dict_name not in locals_dict_handles, locals_dict_name

    if kind == "python2_function_exec":
        locals_scope = LocalsDictExecHandle(locals_dict_name)
    elif kind == "python3_function":
        locals_scope = LocalsDictFunctionHandle(locals_dict_name)
    elif kind == "python3_class":
        locals_scope = LocalsMappingHandle(locals_dict_name)
    elif kind == "python2_class":
        locals_scope = LocalsDictHandle(locals_dict_name)
    else:
        assert False, kind

    locals_dict_handles[locals_dict_name] = locals_scope

def getLocalsDictHandle(locals_dict_name):
    return locals_dict_handles[locals_dict_name]


def getLocalsDictHandles():
    return locals_dict_handles


class LocalsDictHandle(object):
    __slots__ = (
        "locals_name",
        "variables",
        "mark_for_propagation",
        "propagation"
    )

    @counted_init
    def __init__(self, locals_name):
        self.locals_name = locals_name

        # For locals dict variables in this scope.
        self.variables = {}

        # Can this be eliminated through replacement of temporary variables
        self.mark_for_propagation = False

        self.propagation = None

    __del__ = counted_del()

    def __repr__(self):
        return "<%s of %s>" % (
            self.__class__.__name__,
            self.locals_name
        )

    def getName(self):
        return self.locals_name

    @staticmethod
    def getTypeShape():
        return ShapeTypeDict

    def getCodeName(self):
        return self.locals_name

    def getLocalsDictVariable(self, variable_name):
        if variable_name not in self.variables:
            result = Variables.LocalsDictVariable(
                owner         = self,
                variable_name = variable_name
            )

            self.variables[variable_name] = result

        return self.variables[variable_name]


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
                temp_scope = None,
                name       = self.getCodeName() + "_key_" + variable_name
            )

        return self.propagation[variable_name]

    def getPropagationVariables(self):
        if self.propagation is None:
            return ()

        return self.propagation

    def finalize(self):
        del self.propagation
        del self.mark_for_propagation

        for variable in self.variables.values():
            variable.finalize()

        del self.variables

class LocalsDictExecHandle(LocalsDictHandle):
    pass


class LocalsDictFunctionHandle(LocalsDictHandle):
    pass


class LocalsMappingHandle(LocalsDictHandle):
    @staticmethod
    def getTypeShape():
        # TODO: Make mapping available for this.
        return ShapeUnknown
