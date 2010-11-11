#
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
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

class Variable:
    def __init__( self, owner, variable_name ):
        assert type( variable_name ) == str, variable_name

        self.variable_name = variable_name
        self.owner = owner

        self.references = []

    def getName( self ):
        return self.variable_name

    def getOwner( self ):
        return self.owner

    def addReference( self, reference ):
        self.references.append( reference )

    def isLocalVariable( self ):
        return False

    def isLocalLoopVariable( self ):
        return False

    def isClassVariable( self ):
        return False

    def isParameterVariable( self ):
        return False

    def isNestedParameterVariable( self ):
        return False

    def isClosureReference( self ):
        return False

    def isModuleVariable( self ):
        return False

    def _checkShared( self, variable ):
        for reference in variable.references:
            # print "Checking", reference, "of", variable

            if self._checkShared( reference ):
                return True

            top_owner = reference.getReferenced().getOwner()
            owner = reference.getOwner()

            while owner != top_owner:
                if not owner.isListContraction():
                    return True

                owner = owner.getParentVariableProvider()
        else:
            return False


    def isShared( self ):
        variable = self

        while variable.isClosureReference():
            variable = variable.getReferenced()

        return self._checkShared( variable )


class ParameterVariable( Variable ):
    def __init__( self, owner, parameter_name ):
        Variable.__init__( self, owner, variable_name = parameter_name )

    def __repr__( self ):
        return "<ParameterVariable %s>" % self.getName()

    def isLocalVariable( self ):
        return True

    def isParameterVariable( self ):
        return True

class NestedParameterVariable( Variable ):
    def __init__( self, owner, parameter_name, parameter_spec ):
        Variable.__init__( self, owner, variable_name = parameter_name )
        self.parameter_spec = parameter_spec

    def __repr__( self ):
        return "<NestedParameterVariable %s>" % self.getName()

    def isLocalVariable( self ):
        return True

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
    return [ ParameterVariable( owner = owner, parameter_name = parameter_name ) for parameter_name in parameter_names ]

class ClassVariable( Variable ):
    def __init__( self, owner, variable_name ):
        Variable.__init__( self, owner = owner, variable_name = variable_name )

    def __repr__( self ):
        return "<ClassVariable '%s' of '%s'>" % ( self.variable_name, self.owner.getName() )

    def isClassVariable( self ):
        return True


class LocalVariable( Variable ):
    def __init__( self, owner, variable_name ):
        Variable.__init__( self, owner = owner, variable_name = variable_name )

    def __repr__( self ):
        return "<LocalVariable '%s' of '%s'>" % ( self.variable_name, self.owner.getName() )

    def isLocalVariable( self ):
        return True

class LocalLoopVariable( LocalVariable ):
    def __init__( self, owner, variable_name ):
        LocalVariable.__init__( self, owner = owner, variable_name = variable_name )

    def __repr__( self ):
        return "<LocalLoopVariable '%s' of '%s'>" % ( self.variable_name, self.owner.getName() )

    def isLocalLoopVariable( self ):
        return True

class ModuleVariable( Variable ):
    def __init__( self, module, variable_name ):
        Variable.__init__( self, owner = module, variable_name = variable_name )

        self.module = module

    def __repr__( self ):
        return "<ModuleVariable '%s' of '%s'>" % ( self.variable_name, self.owner.getName() )

    def isModuleVariable( self ):
        return True

    def getModuleName( self ):
        return self.module.getName()

class ClosureVariableReference( Variable ):
    def __init__( self, owner, variable ):
        Variable.__init__( self, owner = owner, variable_name = variable.getName() )

        variable.addReference( self )
        self.variable = variable

    def getReferenced( self ):
        return self.variable

    def isClosureReference( self ):
        return True

    def __repr__( self ):
        return "<ClosureVariableReference to %s>" % self.variable

    def __cmp__( self, other ):
        return cmp( self.getReferenced(), other.getReferenced() )

    def __hash__( self ):
        return hash( self.getReferenced() )

def getNames( variables ):
    return [ variable.getName() for variable in variables ]
