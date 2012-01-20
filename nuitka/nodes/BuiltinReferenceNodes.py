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
""" Tree nodes for builtin references.

There is 2 major types of builtin references. One is the values from
builtins, the other is builtin exceptions. They work differently and
mean different things, but they have similar origin, that is, access
to variables only ever read.

"""


from .NodeBases import CPythonNodeBase

from nuitka.Builtins import builtin_names, builtin_exception_names

class CPythonExpressionBuiltinRefBase( CPythonNodeBase ):
    def __init__( self, builtin_name, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        self.builtin_name = builtin_name

    def makeCloneAt( self, source_ref ):
        return self.__class__( self.builtin_name, source_ref )

    def getDetails( self ):
        return { "builtin_name" : self.builtin_name }

    def isConstant( self ):
        return False

    def getBuiltinName( self ):
        return self.builtin_name

    def mayHaveSideEffects( self ):
        # Referencing the builtin name has no side effect
        return False

    def getValueFriend( self ):
        # These can speak for themselves and do not bother about being in danger of
        # mutation having any impact.
        return self


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
