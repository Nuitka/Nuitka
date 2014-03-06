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
""" Code generation contexts.

"""

from .Identifiers import (
    SpecialConstantIdentifier,
    ConstantIdentifier,
    Identifier
)

from .Namify import namifyConstant
from .ConstantCodes import HashableConstant

from nuitka.Constants import constant_builtin_types

from nuitka.Utils import python_version

from nuitka import Options

from ..__past__ import iterItems

# Many methods won't use self, but it's the interface. pylint: disable=R0201

class PythonContextBase:
    def __init__(self):
        self.try_count = 0

        self.try_finally_counts = []

        self.temp_counts = {}

    def isPythonModule(self):
        return False

    def hasLocalsDict(self):
        return False

    def allocateTryNumber(self):
        self.try_count += 1

        return self.try_count

    def setTryFinallyCount(self, value):
        self.try_finally_counts.append( value )

    def removeFinallyCount(self):
        del self.try_finally_counts[-1]

    def getTryFinallyCount(self):
        if self.try_finally_counts:
            return self.try_finally_counts[-1]
        else:
            return None

    def allocateTempNumber(self, tmp_scope):
        result = self.temp_counts.get( tmp_scope, 0 ) + 1
        self.temp_counts[ tmp_scope ] = result
        return result


class PythonChildContextBase(PythonContextBase):
    def __init__(self, parent):
        PythonContextBase.__init__( self )

        self.parent = parent

    def getConstantHandle(self, constant):
        return self.parent.getConstantHandle( constant )

    def getModuleCodeName(self):
        return self.parent.getModuleCodeName()

    def getModuleName(self):
        return self.parent.getModuleName()

    def addHelperCode(self, key, code):
        self.parent.addHelperCode( key, code )

    def addDeclaration(self, key, code):
        self.parent.addDeclaration( key, code )


def _getConstantDefaultPopulation():
    result = (
        # Basic values that the helper code uses all the times.
        (),
        {},
        "",
        True,
        False,
        0,
        1,

        # For Python3 empty bytes, no effect for Python2, same as "", used for
        # code objects.
        b"",

        # Python mechanics, used in various helpers.
        "__module__",
        "__class__",
        "__name__",
        "__metaclass__",
        "__dict__",
        "__doc__",
        "__file__",
        "__enter__",
        "__exit__",
        "__builtins__",
        "__all__",
        "__cmp__",

        # Patched module name.
        "inspect",

        # Names of builtins used in helper code.
        "compile",
        "range",
        "open",
        "__import__",

        # COMPILE_CODE uses read/strip method lookups.
        "read",
        "strip",
    )

    # For Python3 modules
    if python_version >= 300:
        result += ( "__cached__",  )

    # For Python3 print
    if python_version >= 300:
        result += ( "print", "end", "file" )

    if python_version >= 330:
        result += ( "__loader__", )

    # For patching Python2 internal class type
    if python_version < 300:
        result += (
            "__getattr__",
            "__setattr__",
            "__delattr__"
        )

    # For patching Python2 sys attributes for current exception
    if python_version < 300:
        result += (
            "exc_type",
            "exc_value",
            "exc_traceback"
        )

    # The xrange built-in is Python2 only.
    if python_version < 300:
        result += (
            "xrange",
        )

    # Executables only
    if not Options.shallMakeModule():
        result += ( "__main__", )

        # The "site" module is referenced in inspect patching.
        result += ( "site", )

    # Builtin original values
    if not Options.shallMakeModule():
        result += (
            "type",
            "len",
            "range",
            "repr",
            "int",
            "iter",
        )

        if python_version < 300:
            result += (
                "long",
            )

    return result


class PythonGlobalContext:
    def __init__(self):
        self.constants = {}

        for value in _getConstantDefaultPopulation():
            self.getConstantHandle(value)

    def getConstantHandle(self, constant, real_use = True):
        # There are many branches, each supposed to return.
        # pylint: disable=R0911

        if constant is None:
            return SpecialConstantIdentifier( None )
        elif constant is True:
            return SpecialConstantIdentifier( True )
        elif constant is False:
            return SpecialConstantIdentifier( False )
        elif constant is Ellipsis:
            return SpecialConstantIdentifier( Ellipsis )
        elif constant in constant_builtin_types:
            type_name = constant.__name__

            if constant is int and python_version >= 300:
                type_name = "long"

            if constant is str and python_version < 300:
                type_name = "string"

            if constant is str and python_version > 300:
                type_name = "unicode"

            return Identifier(
                "(PyObject *)&Py%s_Type" % type_name.title(),
                0
            )
        else:
            if real_use:
                key = HashableConstant(constant)

                if key not in self.constants:
                    self.constants[key] = "const_" + namifyConstant(
                        constant
                    )

                return ConstantIdentifier(self.constants[ key ], constant)
            else:
                return Identifier("const_" + namifyConstant( constant ), 0)

    def getConstants(self):
        return self.constants


class PythonModuleContext(PythonContextBase):
    # Plent of attributes, because it's storing so many different things.
    # pylint: disable=R0902

    def __init__( self, module_name, code_name, filename, is_empty,
                  global_context ):
        PythonContextBase.__init__( self )

        self.name = module_name
        self.code_name = code_name
        self.filename = filename
        self.is_empty = is_empty

        self.global_context = global_context

        self.declaration_codes = {}
        self.helper_codes = {}

    def __repr__(self):
        return "<PythonModuleContext instance for module %s>" % self.filename

    def isPythonModule(self):
        return True

    def getFrameHandle(self):
        return Identifier( "frame_guard.getFrame()", 1 )

    def getFrameGuardClass(self):
        return "FrameGuard"

    def getConstantHandle(self, constant):
        return self.global_context.getConstantHandle(constant)

    def getName(self):
        return self.name

    def getFilename(self):
        return self.filename

    def isEmptyModule(self):
        return self.is_empty

    getModuleName = getName

    def getModuleCodeName(self):
        return self.code_name

    # There cannot be local variable in modules no need to consider the name.
    # pylint: disable=W0613
    def hasLocalVariable(self, var_name):
        return False

    def hasClosureVariable(self, var_name):
        return False
    # pylint: enable=W0613

    def setFrameGuardMode(self, guard_mode):
        assert guard_mode == "once"

    def getReturnErrorCode(self):
        return "return MOD_RETURN_VALUE( NULL );"

    def addHelperCode(self, key, code):
        assert key not in self.helper_codes, key

        self.helper_codes[ key ] = code

    def getHelperCodes(self):
        return self.helper_codes

    def addDeclaration(self, key, code):
        assert key not in self.declaration_codes

        self.declaration_codes[ key ] = code

    def getDeclarations(self):
        return self.declaration_codes


class PythonFunctionContext(PythonChildContextBase):
    def __init__(self, parent, function):
        PythonChildContextBase.__init__(
            self,
            parent = parent
        )

        self.function = function

        # Make sure the local names are available as constants
        for local_name in function.getLocalVariableNames():
            self.getConstantHandle(
                constant = local_name
            )

        self.guard_mode = None

    def __repr__(self):
        return "<PythonFunctionContext for %s '%s'>" % (
            "function" if not self.function.isClassDictCreation() else "class",
            self.function.getName()
        )

    def getFunction(self):
        return self.function

    def hasLocalsDict(self):
        return self.function.hasLocalsDict()

    def hasLocalVariable(self, var_name):
        return var_name in self.function.getLocalVariableNames()

    def hasClosureVariable(self, var_name):
        return var_name in self.function.getClosureVariableNames()

    def getFrameHandle(self):
        if self.function.isGenerator():
            return Identifier(
                "generator->m_frame",
                0
            )
        else:
            return Identifier(
                "frame_guard.getFrame()",
                1
            )

    def getFrameGuardMode(self):
        return self.guard_mode

    def setFrameGuardMode(self, guard_mode):
        self.guard_mode = guard_mode

    def getFrameGuardClass(self):
        if self.guard_mode == "generator":
            return "FrameGuardLight"
        elif self.guard_mode == "full":
            return "FrameGuard"
        elif self.guard_mode == "pass_through":
            return "FrameGuardVeryLight"
        else:
            assert False, (self, self.guard_mode)


class PythonFunctionDirectContext(PythonFunctionContext):
    def isForDirectCall(self):
        return True

    def isForCrossModuleUsage(self):
        return self.function.isCrossModuleUsed()

    def isForCreatedFunction(self):
        return False


class PythonFunctionCreatedContext(PythonFunctionContext):
    def isForDirectCall(self):
        return False

    def isForCreatedFunction(self):
        return True


class PythonStatementContext(PythonChildContextBase):
    def __init__(self, parent):
        PythonChildContextBase.__init__( self, parent = parent )

        self.temp_keepers = {}

    def getFrameHandle(self):
        return self.parent.getFrameHandle()

    def getFrameGuardClass(self):
        return self.parent.getFrameGuardClass()

    def hasLocalsDict(self):
        return self.parent.hasLocalsDict()

    def isPythonModule(self):
        return self.parent.isPythonModule()

    def getFunction(self):
        return self.parent.getFunction()

    def allocateCallTempNumber(self):
        return self.parent.allocateCallTempNumber()

    def addTempKeeperUsage(self, variable_name, ref_count):
        self.temp_keepers[ variable_name ] = ref_count

    def getTempKeeperRefCount(self, variable_name):
        return self.temp_keepers[ variable_name ]

    def getTempKeeperUsages(self):
        result = self.temp_keepers
        self.temp_keepers = {}
        return result

    def getTempKeeperDecl(self):
        tmp_keepers = self.getTempKeeperUsages()

        return [
            "PyObjectTempKeeper%s %s;" % ( ref_count, tmp_variable )
            for tmp_variable, ref_count in sorted( iterItems( tmp_keepers ) )
        ]

    def allocateTryNumber(self):
        return self.parent.allocateTryNumber()

    def setTryFinallyCount(self, value):
        self.parent.setTryFinallyCount( value )

    def removeFinallyCount(self):
        self.parent.removeFinallyCount()

    def getTryFinallyCount(self):
        return self.parent.getTryFinallyCount()
