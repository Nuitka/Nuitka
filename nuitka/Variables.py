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
""" Variables link the storage and use of a Python variable together.

Different kinds of variables represent different scopes and owners types,
and their links between each other, i.e. references as in closure or
module variable references.

"""

from nuitka.utils import InstanceCounters, Utils


class Variable:
    @InstanceCounters.counted_init
    def __init__(self, owner, variable_name):
        assert type(variable_name) is str, variable_name
        assert type(owner) not in (tuple, list), owner
        assert owner.getFullName

        self.variable_name = variable_name
        self.owner = owner

        self.version_number = 0

        self.global_trace = None

    __del__ = InstanceCounters.counted_del()

    def getName(self):
        return self.variable_name

    def getOwner(self):
        return self.owner

    def getGlobalVariableTrace(self):
        # Monkey patched later to then use it, pylint: disable=R0201
        return None

    def _getGlobalVariableTrace(self):
        return self.global_trace

    def setGlobalVariableTrace(self, global_trace):
        self.global_trace = global_trace

    def getCodeName(self):
        var_name = self.variable_name
        var_name = var_name.replace('.', '$')
        var_name = Utils.encodeNonAscii(var_name)

        return var_name

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

    def isModuleVariable(self):
        return False

    def isTempVariable(self):
        return False
    # pylint: enable=R0201

    def isSharedTechnically(self):
        from nuitka.VariableRegistry import isSharedTechnically
        return isSharedTechnically(self)


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
    def __init__(self, owner, parameter_name):
        LocalVariable.__init__(
            self,
            owner         = owner,
            variable_name = parameter_name
        )

    def isParameterVariable(self):
        return True


class ModuleVariable(Variable):
    def __init__(self, module, variable_name):
        assert type(variable_name) is str, repr(variable_name)
        assert module.isCompiledPythonModule()

        Variable.__init__(
            self,
            owner         = module,
            variable_name = variable_name
        )

        self.module = module

    def __repr__(self):
        return "<ModuleVariable '%s' of '%s'>" % (
            self.variable_name,
            self.getModule().getFullName()
        )

    def isModuleVariable(self):
        return True

    def getModule(self):
        return self.module


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
