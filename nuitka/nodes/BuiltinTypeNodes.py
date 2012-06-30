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

from .NodeMakingHelpers import (
    makeConstantReplacementNode,
    wrapExpressionWithSideEffects
)

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

    def computeNode( self, constraint_collection ):
        new_node, change_tags, change_desc = CPythonExpressionBuiltinTypeBase.computeNode(
            self,
            constraint_collection
        )

        if new_node is self:
            str_value = self.getValue().getStrValue()

            if str_value is not None:
                new_node = wrapExpressionWithSideEffects(
                    new_node = str_value,
                    old_node = self.getValue()
                )

                change_tags = "new_expression"
                change_desc = "Predicted str builtin result"

        return new_node, change_tags, change_desc


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

    def computeNode( self, constraint_collection ):
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
