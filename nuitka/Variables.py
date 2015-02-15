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
""" Variables link the storage and use of a Python variable together.

Different kinds of variables represent different scopes and owners types,
and their links between each other, i.e. references as in closure or
module variable references.

"""

from nuitka import Utils


class Variable:
    def __init__(self, owner, variable_name):
        assert type(variable_name) is str, variable_name
        assert type(owner) not in (tuple, list), owner
        assert owner.getFullName

        self.variable_name = variable_name
        self.owner = owner

        self.read_only_indicator = None

        self.version_number = 0

    def getName(self):
        return self.variable_name

    def getCodeName(self):
        var_name = self.variable_name
        var_name = var_name.replace('.', '$')
        var_name = Utils.encodeNonAscii(var_name)

        return var_name

    def getOwner(self):
        return self.owner

    def getReadOnlyIndicator(self):
        return self.read_only_indicator

    def setReadOnlyIndicator(self, value):
        assert value in (True, False)

        self.read_only_indicator = value

    def allocateTargetNumber(self):
        self.version_number += 1

        return self.version_number

    # pylint: disable=R0201
    def isLocalVariable(self):
        return False

    def isMaybeLocalVariable(self):
        return False

    def isParameterVariable(self):
        return False

    def isNestedParameterVariable(self):
        return False

    def isModuleVariable(self):
        return False

    def isTempVariable(self):
        return False
    # pylint: enable=R0201

    def isSharedTechnically(self):
        from nuitka.VariableRegistry import isSharedTechnically
        return isSharedTechnically(self)

    def getDeclarationTypeCode(self):
        # Abstract method, pylint: disable=R0201
        assert False


class LocalVariable(Variable):
    def __init__(self, owner, variable_name):
        Variable.__init__(
            self,
            owner         = owner,
            variable_name = variable_name
        )

    def __repr__(self):
        return "<%s '%s' of '%s'>" % (
            self.__class__.__name__,
            self.variable_name,
            self.owner.getName()
        )

    def isLocalVariable(self):
        return True

    def getDeclarationTypeCode(self):
        if self.isSharedTechnically():
            return "PyCellObject *"
        else:
            return "PyObject *"


class MaybeLocalVariable(Variable):
    def __init__(self, owner, maybe_variable):
        Variable.__init__(
            self,
            owner         = owner,
            variable_name = maybe_variable.getName()
        )

        self.maybe_variable = maybe_variable

    def __repr__(self):
        return "<%s '%s' of '%s' maybe '%s'" % (
            self.__class__.__name__,
            self.variable_name,
            self.owner.getName(),
            self.maybe_variable
        )

    def isMaybeLocalVariable(self):
        return True

    def getMaybeVariable(self):
        return self.maybe_variable


class ParameterVariable(LocalVariable):
    def __init__(self, owner, parameter_name, kw_only):
        LocalVariable.__init__(
            self,
            owner         = owner,
            variable_name = parameter_name
        )

        self.kw_only = kw_only

    def isParameterVariable(self):
        return True

    def isParameterVariableKwOnly(self):
        return self.kw_only


class NestedParameterVariable(ParameterVariable):
    def __init__(self, owner, parameter_name, parameter_spec):
        ParameterVariable.__init__(
            self,
            owner          = owner,
            parameter_name = parameter_name,
            kw_only        = False
        )

        self.parameter_spec = parameter_spec

    def isNestedParameterVariable(self):
        return True

    def getVariables(self):
        return self.parameter_spec.getVariables()

    def getAllVariables(self):
        return self.parameter_spec.getAllVariables()

    def getTopLevelVariables(self):
        return self.parameter_spec.getTopLevelVariables()

    def getParameterNames(self):
        return self.parameter_spec.getParameterNames()


class ModuleVariable(Variable):
    def __init__(self, module, variable_name):
        assert type(variable_name) is str, repr(variable_name)
        assert module.isPythonModule()

        Variable.__init__(
            self,
            owner         = module,
            variable_name = variable_name
        )

        self.module = module

    def __repr__(self):
        return "<ModuleVariable '%s' of '%s'>" % (
            self.variable_name,
            self.getModuleName()
        )

    def isModuleVariable(self):
        return True

    def getModule(self):
        return self.module

    def getModuleName(self):
        return self.module.getFullName()


class TempVariable(Variable):
    def __init__(self, owner, variable_name):
        Variable.__init__(
            self,
            owner         = owner,
            variable_name = variable_name
        )

    def __repr__(self):
        return "<TempVariable '%s' of '%s'>" % (
            self.getName(),
            self.getOwner()
        )

    def isTempVariable(self):
        return True

    def getDeclarationTypeCode(self):
        if self.isSharedTechnically():
            return "PyCellObject *"
        else:
            return "PyObject *"

    def getDeclarationInitValueCode(self):
        # Virtual method, pylint: disable=R0201
        return "NULL"


def getNames(variables):
    return [
        variable.getName()
        for variable in
        variables
    ]
