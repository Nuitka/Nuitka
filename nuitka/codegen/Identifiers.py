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
""" Identifiers hold code references.

These are generally the means to effectively hide the reference count. The best
part is where getCheapRefCount allows to not allocate references not needed.
"""

# The method signatures do not always require usage of self, sometimes can be
# decided based on class. pylint: disable=R0201

class Identifier:
    def __init__(self, code, ref_count):
        self.code = code
        self.ref_count = ref_count

    def getRefCount(self):
        return self.ref_count

    def getCheapRefCount(self):
        return self.ref_count

    def getCode(self):
        return self.code

    def getCodeObject(self):
        return self.code

    def getCodeExportRef(self):
        if self.getRefCount():
            return self.getCodeObject()
        else:
            return "INCREASE_REFCOUNT( %s )" % self.getCodeObject()

    def getCodeTemporaryRef(self):
        if self.getRefCount():
            return "PyObjectTemporary( %s ).asObject0()" % self.getCodeObject()
        else:
            return self.getCodeObject()

    def getCodeDropRef(self):
        if self.ref_count == 0:
            return self.getCodeTemporaryRef()
        else:
            return "DECREASE_REFCOUNT( %s )" % self.getCodeObject()

    def __repr__(self):
        return "<Identifier %s (%d)>" % ( self.code, self.ref_count )

    def isConstantIdentifier(self):
        return False


class NameIdentifier(Identifier):
    def __init__(self, name, hint, code, ref_count):
        self.name = name
        self.hint = hint

        Identifier.__init__(
            self,
            code      = code,
            ref_count = ref_count
        )

    def __repr__(self):
        return "<NameIdentifier %s '%s' %s>" % (
            self.hint,
            self.name,
            self.code
        )

    def getCodeObject(self):
        return "%s.asObject0()" % self.getCode()

    def getCodeTemporaryRef(self):
        return "%s.asObject0()" % self.getCode()

    def getCodeExportRef(self):
        return "%s.asObject1()" % self.getCode()

    def getCodeDropRef(self):
        return self.getCodeTemporaryRef()


class ConstantIdentifier(Identifier):
    def __init__(self, constant_code, constant_value):
        Identifier.__init__( self, constant_code, 0 )

        self.constant_value = constant_value

    def __repr__(self):
        return "<ConstantIdentifier %s>" % self.code

    def isConstantIdentifier(self):
        return True

    def getCheapRefCount(self):
        return 0

    def getConstant(self):
        return self.constant_value


class SpecialConstantIdentifier(ConstantIdentifier):
    def __init__(self, constant_value):
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


class EmptyDictIdentifier(Identifier):
    def __init__(self):
        Identifier.__init__( self, "PyDict_New()", 1 )

    def getCheapRefCount(self):
        return 1

    def isConstantIdentifier(self):
        return True

    def getConstant(self):
        return {}


class ModuleVariableIdentifier:
    def __init__(self, var_name, var_code_name):
        self.var_name = var_name

        self.var_code_name = var_code_name

    def isConstantIdentifier(self):
        return False

    def __repr__(self):
        return "<ModuleVariableIdentifier %s>" % self.var_name

    def getRefCount(self):
        return 0

    def getCheapRefCount(self):
        # The asObject0 is the fastest way, stealing a reference directly from
        # the module dictionary if possible.
        return 0

    def getCodeTemporaryRef(self):
        return "GET_MODULE_VALUE0( %s )" % (
            self.var_code_name
        )

    def getCodeExportRef(self):
        return "GET_MODULE_VALUE1( %s )" % (
            self.var_code_name
        )

    def getCodeDropRef(self):
        return self.getCodeTemporaryRef()



class MaybeModuleVariableIdentifier(ModuleVariableIdentifier):
    def __init__(self, var_name, var_code_name):
        ModuleVariableIdentifier.__init__(
            self,
            var_name         = var_name,
            var_code_name    = var_code_name
        )

    def __repr__(self):
        return "<MaybeModuleVariableIdentifier %s>" % self.var_name

    def getCodeTemporaryRef(self):
        return "GET_LOCALS_OR_MODULE_VALUE0( locals_dict.asObject0(), %s )" % (
            self.var_code_name
        )

    def getCodeExportRef(self):
        return "GET_LOCALS_OR_MODULE_VALUE1( locals_dict.asObject0(), %s )" % (
            self.var_code_name
        )


class TempObjectIdentifier(Identifier):
    def __init__(self, var_name, code):
        self.var_name = var_name

        Identifier.__init__( self, code, 0 )

    def __repr__(self):
        return "<TempObjectIdentifier %s>" % self.var_name



class KeeperAccessIdentifier(Identifier):
    def __init__(self, var_name):
        Identifier.__init__( self, var_name, 1 )

    def getCheapRefCount(self):
        return 0


class NullIdentifier(Identifier):
    def __init__(self):
        Identifier.__init__(
            self,
            code      = "NULL",
            ref_count = 0
        )

    def getCodeExportRef(self):
        return "NULL"


class ThrowingIdentifier(Identifier):
    def __init__(self, code):
        Identifier.__init__(
            self,
            code      = code,
            ref_count = 0
        )

    def getCodeExportRef(self):
        return self.getCodeObject()

    def getCodeTemporaryRef(self):
        return self.getCodeObject()

    def getCheapRefCount(self):
        return 0


class CallIdentifier(Identifier):
    def __init__(self, called, args):
        Identifier.__init__(
            self,
            code      = "%s( %s )" % (
                called,
                ", ".join( args )
            ),
            ref_count = 1
        )


class HelperCallIdentifier(CallIdentifier):
    def __init__(self, helper, *args):
        CallIdentifier.__init__(
            self,
            called = helper,
            args   = [
                arg.getCodeTemporaryRef() if arg is not None else "NULL"
                for arg in
                args
            ]
        )


def getCodeTemporaryRefs(identifiers):
    """ Helper to create temporary reference code of many identifiers at once.

    """

    return [ identifier.getCodeTemporaryRef() for identifier in identifiers ]

def getCodeExportRefs(identifiers):
    """ Helper to create export reference code of many identifiers at once.

    """

    return [ identifier.getCodeExportRef() for identifier in identifiers ]

def defaultToNullIdentifier(identifier):
    if identifier is not None:
        return identifier
    else:
        return NullIdentifier()

def defaultToNoneIdentifier(identifier):
    if identifier is not None:
        return identifier
    else:
        return SpecialConstantIdentifier( constant_value = None )
