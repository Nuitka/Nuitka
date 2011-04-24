#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
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
""" Identifiers hold code references.

These are generally the means to effectively hide the reference count. The best part
is where getCheapRefCount tries to not allocate references not needed.
"""

from __future__ import print_function


# The method signatures do not always require usage of self, sometimes can be decided
# based on class. pylint: disable=R0201

class Identifier:
    def __init__( self, code, ref_count ):
        self.code = code
        self.ref_count = ref_count

    def getRefCount( self ):
        return self.ref_count

    def getCheapRefCount( self ):
        return self.ref_count

    def getCode( self ):
        return self.code

    def getCodeObject( self ):
        return self.code

    def getCodeExportRef( self ):
        if self.getRefCount():
            return self.getCodeObject()
        else:
            return "INCREASE_REFCOUNT( %s )" % self.getCodeObject()

    def getCodeTemporaryRef( self ):
        if self.getRefCount():
            return "PyObjectTemporary( %s ).asObject()" % self.getCodeObject()
        else:
            return self.getCodeObject()

    def getCodeDropRef( self ):
        if self.ref_count == 0:
            return self.getCodeObject()
        else:
            return "DECREASE_REFCOUNT( %s )" % self.getCodeObject()

    def __repr__( self ):
        return "<Identifier %s (%d)>" % ( self.code, self.ref_count )

    def isConstantIdentifier( self ):
        return self.__class__ is ConstantIdentifier

class ConstantIdentifier( Identifier ):
    def __init__( self, constant_code, constant_value ):
        Identifier.__init__( self, constant_code, 0 )

        self.constant_value = constant_value

    def __repr__( self ):
        return "<ConstantIdentifier %s>" % self.code

    def getCheapRefCount( self ):
        return 0

    def getConstant( self ):
        return self.constant_value

class ModuleVariableIdentifier:
    def __init__( self, var_name, module_code_name ):
        self.var_name = var_name
        self.module_code_name = module_code_name

    def isConstantIdentifier( self ):
        return False

    def __repr__( self ):
        return "<ModuleVariableIdentifier %s>" % self.var_name

    def getCheapRefCount( self ):
        # The asObject0 is the fastest way, stealing a reference directly from the module
        # dictionary if possible.
        return 0

    def getCodeTemporaryRef( self ):
        return "_mvar_%s_%s.asObject0()" % ( self.module_code_name, self.var_name )

    def getCodeExportRef( self ):
        return "_mvar_%s_%s.asObject()" % ( self.module_code_name, self.var_name )

    def getCodeDropRef( self ):
        return self.getCodeTemporaryRef()

    def getCode( self ):
        return "_mvar_%s_%s" % ( self.module_code_name, self.var_name )

class LocalVariableIdentifier:
    def __init__( self, var_name, from_context = False ):
        assert type( var_name ) == str

        self.from_context = from_context
        self.var_name = var_name

    def isConstantIdentifier( self ):
        return False

    def __repr__( self ):
        return "<LocalVariableIdentifier %s>" % self.var_name

    def getCode( self ):
        if not self.from_context:
            return "_python_var_" + self.var_name
        else:
            return "_python_context->python_var_" + self.var_name

    def getRefCount( self ):
        return 0

    def getCheapRefCount( self ):
        return 0

    def getCodeObject( self ):
        return "%s.asObject()" % self.getCode()

    def getCodeTemporaryRef( self ):
        return "%s.asObject()" % self.getCode()

    def getCodeExportRef( self ):
        return "%s.asObject1()" % self.getCode()

class TempVariableIdentifier( Identifier ):
    def __init__( self, tempvar_name ):
        self.tempvar_name = tempvar_name

        Identifier.__init__( self, "_python_tmp_" + tempvar_name, 0 )

    def __repr__( self ):
        return "<TempVariableIdentifier %s >" % self.tempvar_name

    def getCheapRefCount( self ):
        return 0

    def getCodeObject( self ):
        return "%s.asObject()" % self.getCode()

    def getClass( self ):
        return "PyObjectTemporary"

class HolderVariableIdentifier( Identifier ):
    def __init__( self, tempvar_name ):
        self.tempvar_name = tempvar_name

        Identifier.__init__( self, "_python_holder_" + tempvar_name, 0 )

    def __repr__( self ):
        return "<HolderVariableIdentifier %s >" % self.tempvar_name

    def getRefCount( self ):
        return 1

    def getCheapRefCount( self ):
        return 1

    def getCodeObject( self ):
        return "%s.asObject()" % self.getCode()

    def getClass( self ):
        return "PyObjectTempHolder"


class ClosureVariableIdentifier( Identifier ):
    def __init__( self, var_name, from_context ):
        assert type( from_context ) == str

        self.var_name = var_name
        self.from_context = from_context

        if self.from_context:
            Identifier.__init__( self, self.from_context + "python_closure_" + self.var_name, 0 )
        else:
            Identifier.__init__( self, "_python_closure_" + self.var_name, 0 )

    def __repr__( self ):
        return "<ClosureVariableIdentifier %s >" % self.var_name

    def getCheapRefCount( self ):
        return 0

    def getCodeObject( self ):
        return self.getCode() + ".asObject()"

    def getCodeDropRef( self ):
        return "DECREASE_REFCOUNT( %s )" % self.getCodeObject()


class DefaultValueIdentifier( Identifier ):
    def __init__( self, var_name, nested ):
        if nested:
            Identifier.__init__(
                self,
                code      = "_python_context->default_values_" + var_name,
                ref_count = 0
            )
        else:
            Identifier.__init__(
                self,
                code      = "_python_context->default_value_" + var_name,
                ref_count = 0
            )

    def getCheapRefCount( self ):
        return 0


def getCodeTemporaryRefs( identifiers ):
    """ Helper to create temporary reference code of many identifiers at once.

    """

    return [ identifier.getCodeTemporaryRef() for identifier in identifiers ]

def getCodeExportRefs( identifiers ):
    """ Helper to create export reference code of many identifiers at once.

    """

    return [ identifier.getCodeExportRef() for identifier in identifiers ]
