#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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
""" Code generation contexts.

"""

from .Identifiers import (
    Identifier,
    ConstantIdentifier,
    TempObjectIdentifier,
    TempVariableIdentifier,
    LocalVariableIdentifier,
    ClosureVariableIdentifier
)

from .Namify import namifyConstant

from nuitka.Constants import HashableConstant

from nuitka.__past__ import iterItems

from nuitka.Utils import python_version

# False alarms about "hashlib.md5" due to its strange way of defining what is
# exported, pylint won't understand it. pylint: disable=E1101

import hashlib

if python_version < 300:
    def calcHash( key ):
        hash_value = hashlib.md5(
            "%s%s%d%s%s" % key
        )

        return hash_value.hexdigest()
else:
    def calcHash( key ):
        hash_value = hashlib.md5(
            ( "%s%s%d%s%s" % key ).encode( "utf-8" )
        )

        return hash_value.hexdigest()

# Many methods won't use self, but it's the interface. pylint: disable=R0201

class PythonContextBase:
    def __init__( self ):
        self.while_loop_count = 0
        self.for_loop_count = 0

        self.try_count = 0
        self.with_count = 0

        self.preservations = {}

    def allocateForLoopNumber( self ):
        self.for_loop_count += 1

        return self.for_loop_count

    def allocateTryNumber( self ):
        self.try_count += 1

        return self.try_count

    def isClosureViaContext( self ):
        return True

    def isParametersViaContext( self ):
        return False

    def hasLocalsDict( self ):
        return False

    def needsFrameExceptionKeeper( self ):
        return False

    def getTempObjectHandle( self, var_name ):
        return TempObjectIdentifier( var_name )

    def getTempVarHandle( self, var_name ):
        return TempVariableIdentifier( var_name )


class PythonChildContextBase( PythonContextBase ):
    def __init__( self, parent ):
        PythonContextBase.__init__( self )

        self.parent = parent

    def addEvalOrderUse( self, value ):
        self.parent.addEvalOrderUse( value )

    def addMakeTupleUse( self, value ):
        self.parent.addMakeTupleUse( value )

    def addMakeListUse( self, value ):
        self.parent.addMakeListUse( value )

    def addMakeDictUse( self, value ):
        self.parent.addMakeDictUse( value )

    def getParent( self ):
        return self.parent

    def getConstantHandle( self, constant ):
        return self.parent.getConstantHandle( constant )

    def addFunctionCodes( self, code_name, function_decl, function_code ):
        self.parent.addFunctionCodes( code_name, function_decl, function_code )

    def addClassCodes( self, code_name, class_decl, class_code ):
        self.parent.addClassCodes( code_name, class_decl, class_code )

    def addGlobalVariableNameUsage( self, var_name ):
        self.parent.addGlobalVariableNameUsage( var_name )

    def getModuleCodeName( self ):
        return self.parent.getModuleCodeName()

    def getModuleName( self ):
        return self.parent.getModuleName()

    def getCodeObjectHandle( self, filename, code_name, line_number, arg_names, is_generator ):
        return self.parent.getCodeObjectHandle( filename, code_name, line_number, arg_names, is_generator )

class PythonGlobalContext:
    def __init__( self ):
        self.constants = {}

        # Basic values that the code uses all the times.
        self.getConstantHandle( () )
        self.getConstantHandle( {} )
        self.getConstantHandle( "" )
        self.getConstantHandle( True )
        self.getConstantHandle( False )
        self.getConstantHandle( 0 )
        # For Python3 empty bytes, no effect for Python2, same as ""
        self.getConstantHandle( b"" )

        # Python mechanics.
        self.getConstantHandle( "__module__" )
        self.getConstantHandle( "__class__" )
        self.getConstantHandle( "__dict__" )
        self.getConstantHandle( "__doc__" )
        self.getConstantHandle( "__file__" )
        self.getConstantHandle( "__enter__" )
        self.getConstantHandle( "__exit__" )
        self.getConstantHandle( "__builtins__" )
        # For Python3 modules
        self.getConstantHandle( "__cached__" )

        # Patched module name.
        self.getConstantHandle( "inspect" )

        # Names of builtins used in helper code.
        self.getConstantHandle( "compile" )
        self.getConstantHandle( "range" )
        self.getConstantHandle( "open" )
        self.getConstantHandle( "print" )
        self.getConstantHandle( "__import__" )

        # The print builtin needs some argument names.
        self.getConstantHandle( "end" )
        self.getConstantHandle( "file" )

        # COMPILE_CODE uses read/strip method lookups.
        self.getConstantHandle( "read" )
        self.getConstantHandle( "strip" )

        # Executables only
        self.getConstantHandle( "__main__" )

        # sys exception attributes
        self.getConstantHandle( "exc_type" )
        self.getConstantHandle( "exc_value" )
        self.getConstantHandle( "exc_traceback" )

        # Have EVAL_ORDER for 1..6 in any case, so we can use it in the C++ code freely
        # without concern.
        self.make_tuples_used = set( range( 1, 6 ) )
        self.make_lists_used = set( range( 0, 1 ) )
        self.make_dicts_used = set( range( 0, 3 ) )

        # Include 0, so list and tuple making can use it without being special.
        self.eval_orders_used = set( range( 0, 6 ) )

        # Code objects needed.
        self.code_objects = {}

    def getConstantHandle( self, constant ):
        if constant is None:
            return Identifier( "Py_None", 0 )
        elif constant is True:
            return Identifier( "Py_True", 0 )
        elif constant is False:
            return Identifier( "Py_False", 0 )
        elif constant is Ellipsis:
            return Identifier( "Py_Ellipsis", 0 )
        else:
            key = ( type( constant ), HashableConstant( constant ) )

            if key not in self.constants:
                self.constants[ key ] = "_python_" + namifyConstant( constant )

            return ConstantIdentifier( self.constants[ key ], constant )

    def getConstants( self ):
        return sorted( self.constants.items(), key = lambda x: x[1] )

    def getCodeObjectHandle( self, filename, code_name, line_number, arg_names, is_generator ):
        key = ( filename, code_name, line_number, arg_names, is_generator )

        if key not in self.code_objects:
            self.code_objects[ key ] = Identifier(
                "_codeobj_%s" % calcHash( key ),
                0
            )

            self.getConstantHandle( filename )
            self.getConstantHandle( code_name )
            self.getConstantHandle( arg_names )

        return self.code_objects[ key ]

    def getCodeObjects( self ):
        return sorted( iterItems( self.code_objects ) )

    def addEvalOrderUse( self, value ):
        assert type( value ) is int

        self.eval_orders_used.add( value )

    def getEvalOrdersUsed( self ):
        return sorted( self.eval_orders_used )

    def addMakeTupleUse( self, value ):
        assert type( value ) is int

        self.addEvalOrderUse( value ) # generated code uses it
        self.make_tuples_used.add( value )

    def addMakeListUse( self, value ):
        assert type( value ) is int

        self.addEvalOrderUse( value ) # generated code uses it
        self.make_lists_used.add( value )

    def addMakeDictUse( self, value ):
        assert type( value ) is int

        self.addEvalOrderUse( value * 2 ) # generated code uses it
        self.make_dicts_used.add( value )

    def getMakeTuplesUsed( self ):
        return sorted( self.make_tuples_used )

    def getMakeListsUsed( self ):
        return sorted( self.make_lists_used )

    def getMakeDictsUsed( self ):
        return sorted( self.make_dicts_used )


class PythonModuleContext( PythonContextBase ):
    # Plent of attributes, because it's storing so many different things.
    # pylint: disable=R0902

    def __init__( self, module_name, code_name, filename, global_context ):
        PythonContextBase.__init__( self )

        self.name = module_name
        self.code_name = code_name
        self.filename = filename

        self.global_context = global_context

        self.class_codes = {}
        self.function_codes = {}

        self.global_var_names = set()
        self.temp_var_names = set()

    def __repr__( self ):
        return "<PythonModuleContext instance for module %s>" % self.filename

    def getFrameHandle( self ):
        return Identifier( "frame_guard.getFrame()", 1 )

    def hasFrameGuard( self ):
        return True

    def getParent( self ):
        return None

    def getConstantHandle( self, constant ):
        return self.global_context.getConstantHandle( constant )

    def getCodeObjectHandle( self, filename, code_name, line_number, arg_names, is_generator ):
        return self.global_context.getCodeObjectHandle( filename, code_name, line_number, arg_names, is_generator )

    def addFunctionCodes( self, code_name, function_decl, function_code ):
        assert code_name not in self.function_codes

        self.function_codes[ code_name ] = ( function_decl, function_code )

    def getFunctionsCodes( self ):
        return self.function_codes

    def addClassCodes( self, code_name, class_decl, class_code ):
        assert code_name not in self.class_codes

        self.class_codes[ code_name ] = ( class_decl, class_code )

    def getClassesCodes( self ):
        return self.class_codes

    def getName( self ):
        return self.name

    getModuleName = getName

    def getModuleCodeName( self ):
        return self.code_name

    # There cannot ne local variable in modules no need to consider the name.
    # pylint: disable=W0613
    def hasLocalVariable( self, var_name ):
        return False

    def hasClosureVariable( self, var_name ):
        return False
    # pylint: enable=W0613

    def canHaveLocalVariables( self ):
        return False

    def addGlobalVariableNameUsage( self, var_name ):
        self.global_var_names.add( var_name )

    def getGlobalVariableNames( self ):
        return self.global_var_names

    def getTracebackName( self ):
        return "<module>"

    def getTracebackFilename( self ):
        return self.filename

    def addEvalOrderUse( self, value ):
        self.global_context.addEvalOrderUse( value )

    def addMakeTupleUse( self, value ):
        self.global_context.addMakeTupleUse( value )

    def addMakeListUse( self, value ):
        self.global_context.addMakeListUse( value )

    def addMakeDictUse( self, value ):
        self.global_context.addMakeDictUse( value )


class PythonFunctionContext( PythonChildContextBase ):
    def __init__( self, parent, function ):
        PythonChildContextBase.__init__( self, parent = parent )

        self.function = function

        self.needs_creation = function.needsCreation()

        # Make sure the local names are available as constants
        for local_name in function.getLocalVariableNames():
            self.getConstantHandle( constant = local_name )

    def __repr__( self ):
        return "<PythonFunctionContext for function '%s'>" % self.function.getName()

    def hasLocalsDict( self ):
        return self.function.hasLocalsDict()

    def hasLocalVariable( self, var_name ):
        return var_name in self.function.getLocalVariableNames()

    def hasClosureVariable( self, var_name ):
        return var_name in self.function.getClosureVariableNames()

    def canHaveLocalVariables( self ):
        return True

    def isParametersViaContext( self ):
        return self.function.isGenerator()

    def getFrameHandle( self ):
        if self.function.isGenerator():
            return Identifier( "generator->m_frame", 0 )
        else:
            return Identifier( "frame_guard.getFrame()", 1 )

    def hasFrameGuard( self ):
        return not self.function.isGenerator()

    def getLocalHandle( self, var_name ):
        return LocalVariableIdentifier( var_name, from_context = self.function.isGenerator() )

    def getClosureHandle( self, var_name ):
        if self.needs_creation:
            if self.function.isGenerator():
                return ClosureVariableIdentifier( var_name, from_context = "_python_context->common_context->" )
            else:
                return ClosureVariableIdentifier( var_name, from_context = "_python_context->" )
        else:
            if self.function.isGenerator():
                return ClosureVariableIdentifier( var_name, from_context = "_python_context->" )
            else:
                return ClosureVariableIdentifier( var_name, from_context = "" )

    def getTempObjectHandle( self, var_name ):
        return TempObjectIdentifier( var_name )

    def getTracebackName( self ):
        return self.function.getName()

    # TODO: Memoize would do wonders for these things mayhaps.
    def getTracebackFilename( self ):
        return self.function.getParentModule().getFilename()

    def needsFrameExceptionKeeper( self ):
        return self.function.needsFrameExceptionKeeper()


class PythonClassContext( PythonChildContextBase ):
    def __init__( self, parent, class_def ):
        PythonChildContextBase.__init__( self, parent = parent )

        self.class_def = class_def

    def hasLocalVariable( self, var_name ):
        return var_name in self.class_def.getClassVariableNames()

    def hasClosureVariable( self, var_name ):
        return var_name in self.class_def.getClosureVariableNames()

    def getFrameHandle( self ):
        return Identifier( "frame_guard.getFrame()", 1 )

    def hasFrameGuard( self ):
        return True

    def getLocalHandle( self, var_name ):
        return LocalVariableIdentifier( var_name )

    def getClosureHandle( self, var_name ):
        return ClosureVariableIdentifier( var_name, from_context = "" )

    def isClosureViaContext( self ):
        return False

    def getTracebackName( self ):
        return self.class_def.getName()

    def getTracebackFilename( self ):
        return self.class_def.getParentModule().getFilename()

    def hasLocalsDict( self ):
        return self.class_def.hasLocalsDict()

    def needsFrameExceptionKeeper( self ):
        return self.class_def.needsFrameExceptionKeeper()


class PythonExecInlineContext( PythonChildContextBase ):
    def __init__( self, parent ):
        PythonChildContextBase.__init__( self, parent = parent )

    def canHaveLocalVariables( self ):
        return self.parent.canHaveLocalVariables()

    def getClosureHandle( self, var_name ):
        return self.parent.getLocalHandle( var_name )

    def getLocalHandle( self, var_name ):
        return self.parent.getLocalHandle( var_name )

    def hasLocalsDict( self ):
        return self.parent.hasLocalsDict()
