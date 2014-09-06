#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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


class Variable:
    def __init__(self, owner, variable_name):
        assert type(variable_name) is str, variable_name
        assert type(owner) not in (tuple, list), owner

        self.variable_name = variable_name
        self.owner = owner

        self.read_only_indicator = None

        self.version_number = 0

    def getName(self):
        return self.variable_name

    def getOwner(self):
        return self.owner

    def getReadOnlyIndicator(self):
        return self.read_only_indicator

    def setReadOnlyIndicator(self, value):
        assert value in ( True, False )

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

    def getMangledName(self):
        """ Get the mangled name of the variable.

            By default no mangling is applied.
        """

        return self.getName()

    def getDeclarationTypeCode(self, in_context):
        # Abstract method, pylint: disable=R0201,W0613
        assert False




def mangleName(variable_name, owner):
    if not variable_name.startswith( "__" ) or variable_name.endswith( "__" ):
        return variable_name
    else:
        # The mangling of function variable names depends on being inside a
        # class.
        class_container = owner.getContainingClassDictCreation()

        if class_container is None:
            return variable_name
        else:
            return "_%s%s" % (
                class_container.getName().lstrip("_"),
                variable_name
            )


class LocalVariable(Variable):
    def __init__(self, owner, variable_name):
        Variable.__init__(
            self,
            owner         = owner,
            variable_name = variable_name
        )

        assert not owner.isExpressionFunctionBody() or \
               owner.local_locals or \
               self.__class__ is not LocalVariable

    def __repr__(self):
        return "<%s '%s' of '%s'>" % (
            self.__class__.__name__,
            self.variable_name,
            self.owner.getName()
        )

    def isLocalVariable(self):
        return True

    def getDeclarationTypeCode(self, in_context):
        if self.isSharedTechnically():
            return "PyObjectSharedLocalVariable"
        else:
            return "PyObjectLocalVariable"

    def getMangledName(self):
        return mangleName(self.variable_name, self.owner)


class ClassVariable(LocalVariable):

    def getMangledName(self):
        """ Get the mangled name of the variable.

            In classes, names like "__name__" are not mangled, only "__name"
            would be.
        """
        if not self.variable_name.startswith( "__" ) or \
           self.variable_name.endswith( "__" ):
            return self.variable_name
        else:
            return "_%s%s" % (
                self.getOwner().getName().lstrip("_"),
                self.variable_name
            )


class MaybeLocalVariable(Variable):
    def __init__(self, owner, variable_name):
        Variable.__init__(
            self,
            owner         = owner,
            variable_name = variable_name
        )

    def __repr__(self):
        return "<%s '%s' of '%s' maybe a global reference>" % (
            self.__class__.__name__,
            self.variable_name,
            self.owner.getName()
        )

    def isMaybeLocalVariable(self):
        return True


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
        assert type( variable_name ) is str, repr( variable_name )

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
        # Virtual method, pylint: disable=R0201
        return True

    def getDeclarationTypeCode(self, in_context):
        if self.isSharedTechnically():
            return "PyObjectSharedTempVariable"
        else:
            return "PyObjectTempVariable"

    def getDeclarationInitValueCode(self):
        # Virtual method, pylint: disable=R0201
        return "NULL"


def getNames(variables):
    return [
        variable.getName()
        for variable in
        variables
    ]
