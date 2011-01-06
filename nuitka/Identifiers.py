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

from __future__ import print_function
# pylint: disable=W0622
from __past__ import long, unicode
# pylint: enable=W0622

import hashlib, re

from logging import warning

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

class ConstantIdentifier( Identifier ):
    def __init__( self, constant_code ):
        Identifier.__init__( self, constant_code, 0 )

    def __repr__( self ):
        return "<ConstantIdentifier %s>" % self.code

    def getCheapRefCount( self ):
        return 0

class ModuleVariableIdentifier:
    def __init__( self, var_name, module_code_name ):
        self.var_name = var_name
        self.module_code_name = module_code_name

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

class ExceptionCannotNamify( Exception ):
    pass

def digest( value ):
    if str is not unicode:
        return hashlib.md5( value ).hexdigest()
    else:
        return hashlib.md5( value.encode( "utf_8" ) ).hexdigest()

_re_str_needs_no_digest = re.compile( r"^([a-z]|[A-Z]|[0-9]|_){1,40}$", re.S )

def _namifyString( string ):
    if string == "":
        return "empty"
    elif _re_str_needs_no_digest.match( string ) and "\n" not in string:
        # Some strings can be left intact for source code readability.
        return "plain_" + string
    elif len( string ) > 2 and string[0] == "<" and string[-1] == ">" and _re_str_needs_no_digest.match( string[1:-1] ) and "\n" not in string:
        return "angle_" + string[1:-1]
    else:
        # Others are better digested to not cause compiler trouble
        return "digest_" + digest( string )



def isAscii( string ):
    try:
        _unused = str( string )

        return True
    except UnicodeEncodeError:
        return False

def namifyConstant( constant ):
    if type( constant ) == int:
        if constant == 0:
            return "int_0"
        elif constant > 0:
            return "int_pos_%d" % constant
        else:
            return "int_neg_%d" % abs( constant )
    elif type( constant ) == long:
        if constant == 0:
            return "long_0"
        elif constant > 0:
            return "long_pos_%d" % constant
        else:
            return "long_neg_%d" % abs( constant )
    elif type( constant ) == bool:
        return "bool_%s" % constant
    elif constant is None:
        return "none"
    elif constant is Ellipsis:
        return "ellipsis"
    elif type( constant ) == str:
        return "str_" + _namifyString( constant )
    elif type( constant ) == unicode:
        if isAscii( constant ):
            return "unicode_" + _namifyString( str( constant ) )
        else:
            # Others are better digested to not cause compiler trouble
            return "unicode_digest_" + digest( repr( constant ) )
    elif type( constant ) == float:
        return "float_%s" % repr( constant ).replace( ".", "_" ).replace( "-", "_minus_" ).replace( "+", "" )
    elif type( constant ) == complex:
        value = str( constant ).replace( "+", "p" ).replace( "-", "m" ).replace(".","_")

        if value.startswith( "(" ) and value.endswith( ")" ):
            value = value[1:-1]

        return "complex_%s" % value
    elif type( constant ) == dict:
        if constant == {}:
            return "dict_empty"
        else:
            return "dict_" + digest( repr( constant ) )
    elif type( constant ) == set:
        if constant == set():
            return "set_empty"
        else:
            return "set_" + digest( repr( constant ) )
    elif type( constant ) == frozenset:
        if constant == frozenset():
            return "frozenset_empty"
        else:
            return "frozenset_" + digest( repr( constant ) )
    elif type( constant ) == tuple:
        if constant == ():
            return "tuple_empty"
        else:
            result = "tuple_"

            try:
                parts = []

                for value in constant:
                    parts.append( namifyConstant( value ) )

                return result + "_".join( parts )
            except ExceptionCannotNamify:
                warning( "Couldn't namify '%r'" % value )

                return "tuple_" + hashlib.md5( repr( constant ) ).hexdigest()
    elif type( constant ) == list:
        if constant == []:
            return "list_empty"
        else:
            result = "list_"

            try:
                parts = []

                for value in constant:
                    parts.append( namifyConstant( value ) )

                return result + "_".join( parts )
            except ExceptionCannotNamify:
                warning( "Couldn't namify '%r'" % value )

                return "list_" + hashlib.md5( repr( constant ) ).hexdigest()
    else:
        raise ExceptionCannotNamify( constant )


def getCodeTemporaryRefs( identifiers ):
    """ Helper to create temporary reference code of many identifiers at once.

    """

    return [ identifier.getCodeTemporaryRef() for identifier in identifiers ]

def getCodeExportRefs( identifiers ):
    """ Helper to create export reference code of many identifiers at once.

    """

    return [ identifier.getCodeExportRef() for identifier in identifiers ]
