#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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

Different kinds of variables represent different scopes and owners.

"""

from .__past__ import iterItems

class Variable:
    def __init__( self, owner, variable_name ):
        assert type( variable_name ) is str, variable_name
        assert type( owner ) not in ( tuple, list ), owner

        self.variable_name = variable_name
        self.owner = owner


        self.references = []

        self.read_only_indicator = None
        self.has_del = False

        self.version_number = 0

    def getName( self ):
        return self.variable_name

    def getOwner( self ):
        return self.owner

    def getRealOwner( self ):
        result = self.owner

        if result.isStatementTempBlock():
            return result.getParentVariableProvider()
        else:
            return result

    def addReference( self, reference ):
        self.references.append( reference )

    def getReferences( self ):
        return self.references

    def getReferenced( self ):
        # Abstract method, pylint: disable=R0201,W0613
        return None

    def getReadOnlyIndicator( self ):
        return self.read_only_indicator

    def setReadOnlyIndicator( self, value ):
        assert value in ( True, False )

        self.read_only_indicator = value

    def getHasDelIndicator( self ):
        return self.has_del

    def setHasDelIndicator( self ):
        self.has_del = True

    def allocateTargetNumber( self ):
        self.version_number += 1

        return self.version_number

    # pylint: disable=R0201
    def isLocalVariable( self ):
        return False

    def isClassVariable( self ):
        return False

    def isMaybeLocalVariable( self ):
        return False

    def isParameterVariable( self ):
        return False

    def isNestedParameterVariable( self ):
        return False

    def isClosureReference( self ):
        return False

    def isModuleVariableReference( self ):
        return False

    def isReference( self ):
        return self.isClosureReference() or self.isModuleVariableReference()

    def isModuleVariable( self ):
        return False

    def isTempVariableReference( self ):
        return False

    def isTempVariable( self ):
        return False

    def isTempKeeperVariable( self ):
        return False

    # pylint: enable=R0201

    def _checkShared( self, variable ):
        for reference in variable.references:
            # print "Checking", reference, "of", variable

            if self._checkShared( reference ):
                return True

            top_owner = reference.getReferenced().getOwner()
            owner = reference.getOwner()

            while owner.isExpressionFunctionBody() and not owner.isGenerator() and not owner.needsCreation():
                owner = owner.getParentVariableProvider()

            # This defines being shared. Owned by one, and references that are owned by
            # another node.
            if owner != top_owner:
                return True
        else:
            return False


    def isShared( self ):
        variable = self

        while variable.isClosureReference():
            variable = variable.getReferenced()

        return self._checkShared( variable )

    reference_class = None

    def makeReference( self, owner ):
        # Need to provider a reference class, or else making references cannot work.
        assert self.reference_class, self

        # Search for existing references to be re-used before making a new one.
        for reference in self.references:
            if reference.getOwner() is owner:
                return reference
        else:
            # The reference_class will be overloaded with something callable, pylint: disable=E1102
            return self.reference_class(
                owner    = owner,
                variable = self
            )

    def getDeclarationCode( self ):
        return self.getDeclarationTypeCode( in_context = False ) + " &" + self.getCodeName()

    def getMangledName( self ):
        return self.getName()

    def getDeclarationTypeCode( self, in_context ):
        # Abstract method, pylint: disable=R0201,W0613
        assert False

    def getCodeName( self ):
        # Abstract method, pylint: disable=R0201
        assert False, self


class VariableReferenceBase( Variable ):
    def __init__( self, owner, variable ):
        Variable.__init__(
            self,
            owner         = owner,
            variable_name = variable.getName()
        )

        if self.reference_class is None:
            self.reference_class = variable.reference_class

        variable.addReference( self )
        self.variable = variable

        del self.read_only_indicator

    def getReadOnlyIndicator( self ):
        return self.getReferenced().read_only_indicator

    def __repr__( self ):
        return "<%s to %s>" % (
            self.__class__.__name__,
            str( self.variable )[1:-1]
        )

    def getReferenced( self ):
        return self.variable

    def __cmp__( self, other ):
        # Compare the referenced variable, so de-reference until it's no more possible.

        while other.getReferenced() is not None:
            other = other.getReferenced()

        this = self

        while this.getReferenced() is not None:
            this = this.getReferenced()

        return cmp( this, other )

    def __hash__( self ):
        return hash( self.getReferenced() )


class ClosureVariableReference( VariableReferenceBase ):
    def __init__( self, owner, variable ):
        assert not variable.isModuleVariable()

        VariableReferenceBase.__init__(
            self,
            owner    = owner,
            variable = variable
        )

    def isClosureReference( self ):
        return True

    def getProviderVariable( self ):
        current = self.getOwner().getParentVariableProvider()

        if current is self.getReferenced().getOwner():
            return self.getReferenced()
        else:
            for variable in current.getClosureVariables():
                if variable.getName() == self.getName():
                    return variable
            else:
                assert False, self

    def getDeclarationTypeCode( self, in_context ):
        if self.getReferenced().isShared():
            if in_context:
                return "PyObjectClosureVariable"
            else:
                return "PyObjectSharedLocalVariable"
        else:
            return self.getReferenced().getDeclarationTypeCode(
                in_context = in_context
            )

    def getCodeName( self ):
        return "python_closure_%s" % self.getName()


class ModuleVariableReference( VariableReferenceBase ):
    def __init__( self, owner, variable ):

        # Module variable access are direct pass-through, so de-reference them if
        # possible.
        while variable.isModuleVariableReference():
            variable = variable.getReferenced()

        assert variable.isModuleVariable()

        VariableReferenceBase.__init__(
            self,
            owner    = owner,
            variable = variable
        )

        self.global_statement = False
        self.exec_statement = False

    def __repr__( self ):
        return "<ModuleVariableReference '%s' of '%s'%s%s>" % (
            self.variable_name,
            self.getReferenced().getModuleName(),
            " from global statement" if self.global_statement else "",
            " from exec statement" if self.exec_statement else "",
        )

    def markFromGlobalStatement( self ):
        self.global_statement = True

    def isFromGlobalStatement( self ):
        return self.global_statement

    def markFromExecStatement( self ):
        self.exec_statement = True

    def isFromExecStatement( self ):
        return self.exec_statement

    def isModuleVariableReference( self ):
        return True

    def isModuleVariable( self ):
        return True


class LocalVariable( Variable ):
    reference_class = ClosureVariableReference

    def __init__( self, owner, variable_name ):
        Variable.__init__(
            self,
            owner         = owner,
            variable_name = variable_name
        )

        assert not owner.isExpressionFunctionBody() or owner.local_locals or self.__class__ is not LocalVariable

    def __repr__( self ):
        return "<%s '%s' of '%s'>" % (
            self.__class__.__name__,
            self.variable_name,
            self.owner.getName()
        )

    def isLocalVariable( self ):
        return True

    def getCodeName( self ):
        return "python_var_" + self.getName()

    def getDeclarationTypeCode( self, in_context ):
        if self.isShared():
            return "PyObjectSharedLocalVariable"
        else:
            return "PyObjectLocalVariable"


class ClassVariable( LocalVariable ):

    def getMangledName( self ):
        # Names like "__name__" are not mangled, only "__name" would be.
        if not self.variable_name.startswith( "__" ) or self.variable_name.endswith( "__" ):
            return self.variable_name
        else:
            return "_" + self.owner.getName() + self.variable_name


class MaybeLocalVariable( Variable ):
    reference_class = ClosureVariableReference

    def __init__( self, owner, variable_name ):
        Variable.__init__(
            self,
            owner         = owner,
            variable_name = variable_name
        )

    def __repr__( self ):
        return "<%s '%s' of '%s' maybe a global reference>" % (
            self.__class__.__name__,
            self.variable_name,
            self.owner.getName()
        )

    def isMaybeLocalVariable( self ):
        return True


class ParameterVariable( LocalVariable ):
    def __init__( self, owner, parameter_name, kw_only ):
        LocalVariable.__init__(
            self,
            owner         = owner,
            variable_name = parameter_name
        )

        self.kw_only = kw_only

    def isParameterVariable( self ):
        return True

    def isParameterVariableKwOnly( self ):
        return self.kw_only

    def getDeclarationTypeCode( self, in_context ):
        if self.isShared():
            return "PyObjectSharedLocalVariable"
        elif self.getHasDelIndicator():
            return "PyObjectLocalParameterVariableWithDel"
        else:
            return "PyObjectLocalParameterVariableNoDel"



class NestedParameterVariable( ParameterVariable ):
    def __init__( self, owner, parameter_name, parameter_spec ):
        ParameterVariable.__init__(
            self,
            owner          = owner,
            parameter_name = parameter_name,
            kw_only        = False
        )

        self.parameter_spec = parameter_spec

    def isNestedParameterVariable( self ):
        return True

    def getVariables( self ):
        return self.parameter_spec.getVariables()

    def getAllVariables( self ):
        return self.parameter_spec.getAllVariables()

    def getTopLevelVariables( self ):
        return self.parameter_spec.getTopLevelVariables()

    def getParameterNames( self ):
        return self.parameter_spec.getParameterNames()

def makeParameterVariables( owner, parameter_names ):
    return [
        ParameterVariable( owner = owner, parameter_name = parameter_name )
        for parameter_name in
        parameter_names
    ]

class ModuleVariable( Variable ):
    module_variables = {}

    reference_class = ModuleVariableReference

    def __init__( self, module, variable_name ):
        assert type( variable_name ) is str, repr( variable_name )

        Variable.__init__( self, owner = module, variable_name = variable_name )
        self.module = module

        key = self._getKey()

        assert key not in self.module_variables, key
        self.module_variables[ key ] = self

    def __repr__( self ):
        return "<ModuleVariable '%s' of '%s'>" % (
            self.variable_name,
            self.getModuleName()
        )

    def _getKey( self ):
        """ The module name and the variable name form the key."""

        return self.getModule(), self.getName()

    def isModuleVariable( self ):
        return True

    def getModule( self ):
        return self.module

    def getModuleName( self ):
        return self.module.getFullName()

    def _checkShared( self, variable ):
        assert False, variable


def getModuleVariables( module ):
    result = []

    for key, variable in iterItems( ModuleVariable.module_variables ):
        if key[0] is module:
            result.append( variable )

    return result


class TempVariableReference2( VariableReferenceBase ):
    reference_class = None

    def isClosureReference( self ):
        # Virtual method, pylint: disable=R0201
        return True

    def isTempVariableReference( self ):
        # Virtual method, pylint: disable=R0201
        return True

    def getDeclarationTypeCode( self, in_context ):
        if self.getReferenced().getReferenced().needs_free:
            return "PyObjectTemporary"
        else:
            return "PyObject *"

    def getCodeName( self ):
        # Abstract method, pylint: disable=R0201
        return "_" + self.getReferenced().getReferenced().getCodeName()

    def getProviderVariable( self ):
        return self.getReferenced()


class TempVariableReference( VariableReferenceBase ):
    reference_class = TempVariableReference2

    def isTempVariableReference( self ):
        # Virtual method, pylint: disable=R0201
        return True


class TempVariable( Variable ):
    reference_class = TempVariableReference

    def __init__( self, owner, variable_name ):
        Variable.__init__(
            self,
            owner         = owner,
            variable_name = variable_name
        )

        # For code generation.
        self.declared = False

        self.needs_free = None

    def __repr__( self ):
        return "<TempVariable '%s' of '%s'>" % (
            self.getName(),
            self.getOwner()
        )

    def isTempVariable( self ):
        # Virtual method, pylint: disable=R0201
        return True

    def getNeedsFree( self ):
        return self.needs_free

    def setNeedsFree( self, needs_free ):
        assert needs_free is not None

        self.needs_free = needs_free

    def isDeclared( self ):
        return self.declared

    def markAsDeclared( self ):
        assert not self.declared

        self.declared = True

    def getDeclarationTypeCode( self, in_context ):
        assert self.needs_free is not None, self

        if self.needs_free:
            return "PyObjectTemporary"
        else:
            return "PyObject *"

    def getCodeName( self ):
        return "python_tmp_%s" % self.getName()

    def getDeclarationInitValueCode( self ):
        # Virtual method, pylint: disable=R0201
        return "NULL"


class TempKeeperVariable( TempVariable ):
    def __init__( self, owner, variable_name ):
        TempVariable.__init__(
            self,
            owner         = owner,
            variable_name = variable_name
        )

        self.write_only = False

    def isTempKeeperVariable( self ):
        return True

    def isWriteOnly( self ):
        return self.write_only

    def setWriteOnly( self ):
        self.write_only = True


def getNames( variables ):
    return [ variable.getName() for variable in variables ]
