#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit patches or make the software available to licensors of
#     this software in either form, you automatically them grant them a
#     license for your part of the code under "Apache License 2.0" unless you
#     choose to remove this notice.
#
#     Kay Hayen uses the right to license his code under only GPL version 3,
#     to discourage a fork of Nuitka before it is "finished". He will later
#     make a new "Nuitka" release fully under "Apache License 2.0".
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Variables link the storage and use of a Python variable together.

Different kinds of variables represent different scopes and owners.

"""

from .__past__ import iterItems

class Variable:
    def __init__( self, owner, variable_name ):
        assert type( variable_name ) is str, variable_name

        self.variable_name = variable_name
        self.owner = owner

        self.references = []

        self.read_only_indicator = None
        self.has_del = False

    def getName( self ):
        return self.variable_name

    def getOwner( self ):
        return self.owner

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

    def isModuleVariable( self ):
        return False

    def isTempVariableReference( self ):
        return False

    def isTempVariable( self ):
        return False
    # pylint: enable=R0201

    def _checkShared( self, variable ):
        for reference in variable.references:
            # print "Checking", reference, "of", variable

            if self._checkShared( reference ):
                return True

            top_owner = reference.getReferenced().getOwner()
            owner = reference.getOwner()

            # TODO: Check if this is necessary still.
            return owner != top_owner
        else:
            return False


    def isShared( self ):
        variable = self

        while variable.isClosureReference():
            variable = variable.getReferenced()

        return self._checkShared( variable )

    reference_class = None

    def makeReference( self, owner ):
        assert self.reference_class, self

        for reference in self.references:
            if reference.getOwner() is owner:
                return reference
        else:
            # The reference_class will be overloaded with something callable, pylint: disable=E1102
            return self.reference_class(
                owner    = owner,
                variable = self
            )


class VariableReferenceBase( Variable ):
    def __init__( self, owner, variable ):
        Variable.__init__(
            self,
            owner         = owner,
            variable_name = variable.getName()
        )

        self.reference_class = variable.reference_class

        variable.addReference( self )
        self.variable = variable

        del self.read_only_indicator

    def getReadOnlyIndicator( self ):
        return self.getReferenced().read_only_indicator

    def __repr__( self ):
        return "<%s to %s>" % ( self.__class__.__name__, str( self.variable )[1:-1] )

    def getReferenced( self ):
        return self.variable

    # Compare like the referenced variable.
    def __cmp__( self, other ):
        return cmp( self.getReferenced(), other.getReferenced() )

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
        current = self.getOwner().getParent()

        while not current.isClosureVariableTaker():
            current = current.getParent()

        if current is self.getReferenced().getOwner():
            return self.getReferenced()
        else:
            for variable in current.getClosureVariables():
                if variable.getName() == self.getName():
                    return variable
            else:
                assert False


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

    def markFromGlobalStatement( self ):
        self.global_statement = True

    def isFromGlobalStatement( self ):
        return self.global_statement

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
    def __init__( self, owner, parameter_name ):
        LocalVariable.__init__(
            self,
            owner         = owner,
            variable_name = parameter_name
        )

    def isParameterVariable( self ):
        return True


class NestedParameterVariable( ParameterVariable ):
    def __init__( self, owner, parameter_name, parameter_spec ):
        ParameterVariable.__init__(
            self,
            owner          = owner,
            parameter_name = parameter_name
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

class ClassVariable( Variable ):
    reference_class = ClosureVariableReference

    def __init__( self, owner, variable_name ):
        Variable.__init__(
            self,
            owner         = owner,
            variable_name = variable_name
        )

    def __repr__( self ):
        return "<ClassVariable '%s' of '%s'>" % (
            self.variable_name,
            self.owner.getName()
        )

    def isClassVariable( self ):
        return True


class ModuleVariable( Variable ):
    module_variables = {}

    reference_class = ModuleVariableReference

    def __init__( self, module, variable_name ):
        assert type( variable_name ) is str, variable_name

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


class TempVariableReference( VariableReferenceBase ):

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

    def __repr__( self ):
        return "<TempVariable '%s' of '%s'>" % (
            self.getName(),
            self.getOwner()
        )

    def isTempVariable( self ):
        # Virtual method, pylint: disable=R0201
        return True

    def getDeclarationTypeCode( self ):
        # TODO: Derive more effective type from use analysis.
        if self.getOwner().isClosureVariableTaker():
            return "PyObject *"
        else:
            return "PyObjectTemporary"

    def getDeclarationInitValueCode( self ):
        # Virtual method, pylint: disable=R0201
        return "NULL"


def getNames( variables ):
    return [ variable.getName() for variable in variables ]
