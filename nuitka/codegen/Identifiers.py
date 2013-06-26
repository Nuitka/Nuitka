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
""" Identifiers hold code references.

These are generally the means to effectively hide the reference count. The best part
is where getCheapRefCount tries to not allocate references not needed.
"""

# The method signatures do not always require usage of self, sometimes can be decided
# based on class. pylint: disable=R0201

from nuitka import Utils

def encodeNonAscii( var_name ):
    if Utils.python_version < 300:
        return var_name
    else:
        var_name = var_name.encode( "ascii", "xmlcharrefreplace" )

        return var_name.decode( "ascii" ).replace( "&#", "$$" ).replace( ";", "" )

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
            return self.getCodeTemporaryRef()
        else:
            return "DECREASE_REFCOUNT( %s )" % self.getCodeObject()

    def __repr__( self ):
        return "<Identifier %s (%d)>" % ( self.code, self.ref_count )

    def isConstantIdentifier( self ):
        return False


class ConstantIdentifier( Identifier ):
    def __init__( self, constant_code, constant_value ):
        Identifier.__init__( self, constant_code, 0 )

        self.constant_value = constant_value

    def __repr__( self ):
        return "<ConstantIdentifier %s>" % self.code

    def isConstantIdentifier( self ):
        return True

    def getCheapRefCount( self ):
        return 0

    def getConstant( self ):
        return self.constant_value


class SpecialConstantIdentifier( ConstantIdentifier ):
    def __init__( self, constant_value ):
        if constant_value is None:
            ConstantIdentifier.__init__( self, "Py_None", None )
        elif constant_value is True:
            ConstantIdentifier.__init__( self, "Py_True", True )
        elif constant_value is False:
            ConstantIdentifier.__init__( self, "Py_False", False )
        elif constant_value is Ellipsis:
            ConstantIdentifier.__init__( self, "Py_Ellipsis", Ellipsis )
        else:
            assert False, constant_value


class EmptyDictIdentifier( Identifier ):
    def __init__( self ):
        Identifier.__init__( self, "PyDict_New()", 1 )

    def getCheapRefCount( self ):
        return 1

    def isConstantIdentifier( self ):
        return True

    def getConstant( self ):
        return {}


class ModuleVariableIdentifier:
    def __init__( self, var_name, module_code_name ):
        self.var_name = var_name
        self.module_code_name = module_code_name

    def isConstantIdentifier( self ):
        return False

    def __repr__( self ):
        return "<ModuleVariableIdentifier %s>" % self.var_name

    def getRefCount( self ):
        return 0

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
        return "_mvar_%s_%s" % ( self.module_code_name, encodeNonAscii( self.var_name ) )


class MaybeModuleVariableIdentifier( Identifier ):
    def __init__( self, var_name, module_code_name ):
        Identifier.__init__(
            self,
            "_mvar_%s_%s.asObject0( locals_dict.asObject() )" % (
                module_code_name,
                var_name
            ),
            0
        )


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
            return "_python_var_" + encodeNonAscii( self.var_name )
        else:
            return "_python_context->python_var_" + encodeNonAscii( self.var_name )

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

    def getCodeDropRef( self ):
        return self.getCodeTemporaryRef()


class TempVariableIdentifier( Identifier ):
    def __init__( self, var_name ):
        self.tempvar_name = var_name

        Identifier.__init__( self, "_python_tmp_" + var_name, 0 )

    def __repr__( self ):
        return "<TempVariableIdentifier %s >" % self.tempvar_name

    def getCheapRefCount( self ):
        return 0

    def getCodeObject( self ):
        return "%s.asObject()" % self.getCode()

    def getClass( self ):
        return "PyObjectTemporary"


class TempObjectIdentifier( Identifier ):
    def __init__( self, var_name ):
        self.tempvar_name = var_name

        Identifier.__init__( self, "_python_tmp_" + var_name, 0 )

    def getCodeTemporaryRef( self ):
        return self.code



class KeeperAccessIdentifier( Identifier ):
    def __init__( self, var_name ):
        Identifier.__init__( self, var_name, 1 )

    def getCheapRefCount( self ):
        return 0


class ClosureVariableIdentifier( Identifier ):
    def __init__( self, var_name, from_context ):
        assert type( from_context ) is str

        self.var_name = var_name
        self.from_context = from_context

        if self.from_context:
            Identifier.__init__( self, self.from_context + "python_closure_" + encodeNonAscii( self.var_name ), 0 )
        else:
            # TODO: Use a variable object to decide naming policy

            Identifier.__init__( self, "python_closure_" + encodeNonAscii( self.var_name ), 0 )

    def __repr__( self ):
        return "<ClosureVariableIdentifier %s >" % self.var_name

    def getCheapRefCount( self ):
        return 0

    def getCodeObject( self ):
        return self.getCode() + ".asObject()"


class NullIdentifier( Identifier ):
    def __init__( self ):
        Identifier.__init__(
            self,
            code      = "NULL",
            ref_count = 0
        )

    def getCodeExportRef( self ):
        return "NULL"


class ThrowingIdentifier( Identifier ):
    def __init__( self, code ):
        Identifier.__init__(
            self,
            code      = code,
            ref_count = 0
        )

    def getCodeExportRef( self ):
        return self.getCodeObject()

    def getCodeTemporaryRef( self ):
        return self.getCodeObject()

    def getCheapRefCount( self ):
        return 0


class CallIdentifier( Identifier ):
    def __init__( self, called, args ):
        Identifier.__init__(
            self,
            code      = "%s( %s )" % (
                called,
                ", ".join( args )
            ),
            ref_count = 1
        )


class HelperCallIdentifier( CallIdentifier ):
    def __init__( self, helper, *args ):
        CallIdentifier.__init__(
            self,
            called = helper,
            args   = [
                arg.getCodeTemporaryRef() if arg is not None else "NULL"
                for arg in
                args
            ]
        )


def getCodeTemporaryRefs( identifiers ):
    """ Helper to create temporary reference code of many identifiers at once.

    """

    return [ identifier.getCodeTemporaryRef() for identifier in identifiers ]

def getCodeExportRefs( identifiers ):
    """ Helper to create export reference code of many identifiers at once.

    """

    return [ identifier.getCodeExportRef() for identifier in identifiers ]
