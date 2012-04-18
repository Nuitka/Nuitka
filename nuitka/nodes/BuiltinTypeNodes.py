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
""" Builtin type nodes tuple/list/float/int etc.

These are all very simple and have predictable properties, because we know their type and
that should allow some important optimizations.
"""

from .NodeBases import (
    CPythonExpressionBuiltinSingleArgBase,
    CPythonExpressionSpecBasedComputationMixin,
    CPythonChildrenHaving,
    CPythonNodeBase
)

from .NodeMakingHelpers import makeConstantReplacementNode

from nuitka.transform.optimizations import BuiltinOptimization

from nuitka.Utils import python_version

class CPythonExpressionBuiltinTypeBase( CPythonExpressionBuiltinSingleArgBase ):
    pass


class CPythonExpressionBuiltinTuple( CPythonExpressionBuiltinTypeBase ):
    kind = "EXPRESSION_BUILTIN_TUPLE"

    builtin_spec = BuiltinOptimization.builtin_tuple_spec


class CPythonExpressionBuiltinList( CPythonExpressionBuiltinTypeBase ):
    kind = "EXPRESSION_BUILTIN_LIST"

    builtin_spec = BuiltinOptimization.builtin_list_spec


class CPythonExpressionBuiltinFloat( CPythonExpressionBuiltinTypeBase ):
    kind = "EXPRESSION_BUILTIN_FLOAT"

    builtin_spec = BuiltinOptimization.builtin_float_spec


class CPythonExpressionBuiltinBool( CPythonExpressionBuiltinTypeBase ):
    kind = "EXPRESSION_BUILTIN_BOOL"

    builtin_spec = BuiltinOptimization.builtin_bool_spec


class CPythonExpressionBuiltinStr( CPythonExpressionBuiltinTypeBase ):
    kind = "EXPRESSION_BUILTIN_STR"

    builtin_spec = BuiltinOptimization.builtin_str_spec


class CPythonExpressionBuiltinIntLongBase( CPythonChildrenHaving, CPythonNodeBase, \
                                           CPythonExpressionSpecBasedComputationMixin ):
    named_children = ( "value", "base" )

    def __init__( self, value, base, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        if value is None:
            value = makeConstantReplacementNode(
                constant = "0",
                node     = self
            )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "value" : value,
                "base"  : base
            }
        )

    getValue = CPythonChildrenHaving.childGetter( "value" )
    getBase = CPythonChildrenHaving.childGetter( "base" )

    def computeNode( self ):
        value = self.getValue()
        base = self.getBase()

        given_values = []

        if value is None:
            # Note: Prevented that case above.
            assert base is not None

            given_values = ()
        elif base is None:
            given_values = ( value, )
        else:
            given_values = ( value, base )

        return self.computeBuiltinSpec( given_values )


class CPythonExpressionBuiltinInt( CPythonExpressionBuiltinIntLongBase ):
    kind = "EXPRESSION_BUILTIN_INT"

    builtin_spec = BuiltinOptimization.builtin_int_spec


if python_version < 300:
    class CPythonExpressionBuiltinLong( CPythonExpressionBuiltinIntLongBase ):
        kind = "EXPRESSION_BUILTIN_LONG"

        builtin_spec = BuiltinOptimization.builtin_long_spec


class CPythonExpressionBuiltinUnicode( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_BUILTIN_UNICODE"

    named_children = ( "value", "encoding", "errors" )

    def __init__( self, value, encoding, errors, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "value"    : value,
                "encoding" : encoding,
                "errors"   : errors
            }
        )

    getValue = CPythonChildrenHaving.childGetter( "value" )
