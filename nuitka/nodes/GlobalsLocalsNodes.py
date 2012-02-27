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
""" Globals/locals/dir0 nodes

These nodes give access to variables, highly problematic, because using them, the code may
change or access anything about them, so nothing can be trusted anymore, if we start to
not know where their value goes.

"""


from .NodeBases import CPythonNodeBase, CPythonExpressionMixin


class CPythonExpressionBuiltinGlobals( CPythonNodeBase, CPythonExpressionMixin ):
    kind = "EXPRESSION_BUILTIN_GLOBALS"

    def __init__( self, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

    def computeNode( self ):
        return self, None, None


class CPythonExpressionBuiltinLocals( CPythonNodeBase, CPythonExpressionMixin ):
    kind = "EXPRESSION_BUILTIN_LOCALS"

    def __init__( self, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

    def computeNode( self ):
        return self, None, None


class CPythonExpressionBuiltinDir0( CPythonNodeBase, CPythonExpressionMixin ):
    kind = "EXPRESSION_BUILTIN_DIR0"

    def __init__( self, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

    def computeNode( self ):
        return self, None, None
