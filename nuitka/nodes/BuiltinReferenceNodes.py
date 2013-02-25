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
""" Tree nodes for builtin references.

There is 2 major types of builtin references. One is the values from
builtins, the other is builtin exceptions. They work differently and
mean different things, but they have similar origin, that is, access
to variables only ever read.

"""


from .NodeBases import CPythonNodeBase, CompileTimeConstantExpressionMixin

from .ConstantRefNode import CPythonExpressionConstantRef

from nuitka.optimizations import BuiltinOptimization
from nuitka.optimizations.OptimizeBuiltinCalls import computeBuiltinCall

from nuitka.Builtins import (
    builtin_exception_names,
    builtin_exception_values,
    builtin_anon_names,
    builtin_names
)

from nuitka.Utils import python_version

class CPythonExpressionBuiltinRefBase( CompileTimeConstantExpressionMixin, CPythonNodeBase ):
    def __init__( self, builtin_name, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        self.builtin_name = builtin_name

    def makeCloneAt( self, source_ref ):
        return self.__class__( self.builtin_name, source_ref )

    def getDetails( self ):
        return { "builtin_name" : self.builtin_name }

    def getBuiltinName( self ):
        return self.builtin_name

    def mayHaveSideEffects( self, constraint_collection ):
        # Referencing the builtin name has no side effect
        return False


class CPythonExpressionBuiltinRef( CPythonExpressionBuiltinRefBase ):
    kind = "EXPRESSION_BUILTIN_REF"

    def __init__( self, builtin_name, source_ref ):
        assert builtin_name in builtin_names, builtin_name

        CPythonExpressionBuiltinRefBase.__init__(
            self,
            builtin_name = builtin_name,
            source_ref   = source_ref
        )

    def isExpressionBuiltin( self ):
        # Means if it's a builtin function call.
        return False

    def isCompileTimeConstant( self ):
        # Virtual method, pylint: disable=R0201
        return True

    def getCompileTimeConstant( self ):
        return __builtins__[ self.builtin_name ]

    def computeNode( self, constraint_collection ):
        quick_names = {
            "None"      : None,
            "True"      : True,
            "False"     : False,
            "__debug__" : __debug__,
            "Ellipsis"  : Ellipsis,
        }

        if self.builtin_name in quick_names:
            new_node = CPythonExpressionConstantRef(
                constant   = quick_names[ self.builtin_name ],
                source_ref = self.getSourceReference()
            )

            return new_node, "new_constant", "Builtin constant %s resolved" % self.builtin_name

        return self, None, None

    def computeNodeCall( self, call_node, constraint_collection ):

        return computeBuiltinCall(
            call_node = call_node,
            called    = self
        )

    def getStringValue( self, constraint_collection ):
        return repr( self.getCompileTimeConstant() )

    def isKnownToBeIterable( self, count ):
        # TODO: Why yes, some may be, could be told here.
        return None

    def mayProvideReference( self ):
        # Dedicated code returns which returns from builtin module dictionary, but isn't
        # available for Python3 yet.

        return python_version >= 300

class CPythonExpressionBuiltinAnonymousRef( CPythonExpressionBuiltinRefBase ):
    kind = "EXPRESSION_BUILTIN_ANONYMOUS_REF"

    def __init__( self, builtin_name, source_ref ):
        assert builtin_name in builtin_anon_names

        CPythonExpressionBuiltinRefBase.__init__(
            self,
            builtin_name = builtin_name,
            source_ref   = source_ref
        )

    def isExpressionBuiltin( self ):
        # Means if it's a builtin function call.
        return False

    def isCompileTimeConstant( self ):
        # Virtual method, pylint: disable=R0201
        return True

    def mayProvideReference( self ):
        # No reference provided from this, there are just a global identifiers, or
        # accesses to them.

        return False

    def getCompileTimeConstant( self ):
        return builtin_anon_names[ self.builtin_name ]

    def computeNode( self, constraint_collection ):
        return self, None, None

    def getStringValue( self, constraint_collection ):
        return repr( self.getCompileTimeConstant() )


class CPythonExpressionBuiltinExceptionRef( CPythonExpressionBuiltinRefBase ):
    kind = "EXPRESSION_BUILTIN_EXCEPTION_REF"

    def __init__( self, exception_name, source_ref ):
        assert exception_name in builtin_exception_names

        CPythonExpressionBuiltinRefBase.__init__(
            self,
            builtin_name = exception_name,
            source_ref   = source_ref
        )

    def getDetails( self ):
        return { "exception_name" : self.builtin_name }

    getExceptionName = CPythonExpressionBuiltinRefBase.getBuiltinName

    def isExpressionBuiltin( self ):
        # Means if it's a builtin function call.
        return False

    def isCompileTimeConstant( self ):
        # Virtual method, pylint: disable=R0201
        return True

    def mayProvideReference( self ):
        # No reference provided from this, it's just a global identifier.

        return False

    def getCompileTimeConstant( self ):
        return builtin_exception_values[ self.builtin_name ]

    def computeNode( self, constraint_collection ):
        return self, None, None

    def computeNodeCall( self, call_node, constraint_collection ):
        exception_name = self.getExceptionName()

        def createBuiltinMakeException( args, source_ref ):
            from nuitka.nodes.ExceptionNodes import CPythonExpressionBuiltinMakeException

            return CPythonExpressionBuiltinMakeException(
                exception_name = exception_name,
                args           = args,
                source_ref     = source_ref
            )

        new_node = BuiltinOptimization.extractBuiltinArgs(
            node          = call_node,
            builtin_class = createBuiltinMakeException,
            builtin_spec  = BuiltinOptimization.BuiltinParameterSpecExceptions(
                name          = exception_name,
                default_count = 0
            )
        )

        # TODO: Don't allow this to happen.
        if new_node is None:
            return call_node, None, None

        return new_node, "new_expression", "detected builtin exception making"
