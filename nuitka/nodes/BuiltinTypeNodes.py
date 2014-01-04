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
""" Builtin type nodes tuple/list/float/int etc.

These are all very simple and have predictable properties, because we know their type and
that should allow some important optimizations.
"""

from .NodeBases import (
    ExpressionSpecBasedComputationMixin,
    ExpressionBuiltinSingleArgBase,
    ChildrenHavingMixin,
    NodeBase
)

from nuitka.optimizations import BuiltinOptimization

from nuitka.Utils import python_version

class ExpressionBuiltinTypeBase(ExpressionBuiltinSingleArgBase):
    pass


class ExpressionBuiltinTuple(ExpressionBuiltinTypeBase):
    kind = "EXPRESSION_BUILTIN_TUPLE"

    builtin_spec = BuiltinOptimization.builtin_tuple_spec


class ExpressionBuiltinList(ExpressionBuiltinTypeBase):
    kind = "EXPRESSION_BUILTIN_LIST"

    builtin_spec = BuiltinOptimization.builtin_list_spec


class ExpressionBuiltinSet(ExpressionBuiltinTypeBase):
    kind = "EXPRESSION_BUILTIN_SET"

    builtin_spec = BuiltinOptimization.builtin_set_spec


class ExpressionBuiltinFloat(ExpressionBuiltinTypeBase):
    kind = "EXPRESSION_BUILTIN_FLOAT"

    builtin_spec = BuiltinOptimization.builtin_float_spec


class ExpressionBuiltinBool(ExpressionBuiltinTypeBase):
    kind = "EXPRESSION_BUILTIN_BOOL"

    builtin_spec = BuiltinOptimization.builtin_bool_spec

    def mayProvideReference(self):
        # Dedicated code returns "True" or "False" only, which requires no reference
        return False

    def computeExpression(self, constraint_collection):
        value = self.getValue()

        if value is not None:
            truth_value = self.getValue().getTruthValue()

            if truth_value is not None:
                from .NodeMakingHelpers import wrapExpressionWithNodeSideEffects, makeConstantReplacementNode

                result = wrapExpressionWithNodeSideEffects(
                    new_node = makeConstantReplacementNode(
                        constant = truth_value,
                        node     = self,
                    ),
                    old_node = self.getValue()
                )

                return result, "new_constant", "Predicted truth value of builtin bool argument"

        return ExpressionBuiltinTypeBase.computeExpression( self, constraint_collection )


class ExpressionBuiltinIntLongBase( ChildrenHavingMixin, NodeBase,
                                    ExpressionSpecBasedComputationMixin ):
    named_children = ( "value", "base" )

    try:
        int( base = 2 )
    except TypeError:
        base_only_value = False
    else:
        base_only_value = True

    def __init__(self, value, base, source_ref):
        from .NodeMakingHelpers import makeConstantReplacementNode

        NodeBase.__init__( self, source_ref = source_ref )

        if value is None and self.base_only_value:
            value = makeConstantReplacementNode(
                constant = "0",
                node     = self
            )

        ChildrenHavingMixin.__init__(
            self,
            values = {
                "value" : value,
                "base"  : base
            }
        )

    getValue = ChildrenHavingMixin.childGetter( "value" )
    getBase = ChildrenHavingMixin.childGetter( "base" )

    def computeExpression(self, constraint_collection):
        # Children can tell all we need to know, pylint: disable=W0613

        value = self.getValue()
        base = self.getBase()

        given_values = []

        if value is None:
            if base is not None:
                if not self.base_only_value:
                    from .NodeMakingHelpers import getComputationResult

                    return getComputationResult(
                        node        = self,
                        computation = lambda : int( base = 2 ),
                        description = "int builtin call with only base argument"
                    )

            given_values = ()
        elif base is None:
            given_values = ( value, )
        else:
            given_values = ( value, base )

        return self.computeBuiltinSpec( given_values )


class ExpressionBuiltinInt(ExpressionBuiltinIntLongBase):
    kind = "EXPRESSION_BUILTIN_INT"

    builtin_spec = BuiltinOptimization.builtin_int_spec


class ExpressionBuiltinUnicodeBase( ChildrenHavingMixin, NodeBase,
                                    ExpressionSpecBasedComputationMixin ):
    named_children = ( "value", "encoding", "errors" )

    def __init__(self, value, encoding, errors, source_ref):
        NodeBase.__init__( self, source_ref = source_ref )

        ChildrenHavingMixin.__init__(
            self,
            values = {
                "value"    : value,
                "encoding" : encoding,
                "errors"   : errors
            }
        )

    getValue = ChildrenHavingMixin.childGetter( "value" )
    getEncoding = ChildrenHavingMixin.childGetter( "encoding" )
    getErrors = ChildrenHavingMixin.childGetter( "errors" )

    def computeExpression(self, constraint_collection):
        # Children can tell all we need to know, pylint: disable=W0613

        args = [
            self.getValue(),
            self.getEncoding(),
            self.getErrors()
        ]

        while args and args[-1] is None:
            del args[-1]

        return self.computeBuiltinSpec( tuple( args ) )


if python_version < 300:
    class ExpressionBuiltinStr(ExpressionBuiltinTypeBase):
        kind = "EXPRESSION_BUILTIN_STR"

        builtin_spec = BuiltinOptimization.builtin_str_spec

        def computeExpression(self, constraint_collection):
            new_node, change_tags, change_desc = ExpressionBuiltinTypeBase.computeExpression(
                self,
                constraint_collection
            )

            if new_node is self:
                str_value = self.getValue().getStrValue()

                if str_value is not None:
                    from .NodeMakingHelpers import wrapExpressionWithNodeSideEffects

                    new_node = wrapExpressionWithNodeSideEffects(
                        new_node = str_value,
                        old_node = self.getValue()
                    )

                    change_tags = "new_expression"
                    change_desc = "Predicted str builtin result"

            return new_node, change_tags, change_desc


    class ExpressionBuiltinLong(ExpressionBuiltinIntLongBase):
        kind = "EXPRESSION_BUILTIN_LONG"

        builtin_spec = BuiltinOptimization.builtin_long_spec


    class ExpressionBuiltinUnicode(ExpressionBuiltinUnicodeBase):
        kind = "EXPRESSION_BUILTIN_UNICODE"

        builtin_spec = BuiltinOptimization.builtin_unicode_spec
else:
    class ExpressionBuiltinStr(ExpressionBuiltinUnicodeBase):
        kind = "EXPRESSION_BUILTIN_STR"

        builtin_spec = BuiltinOptimization.builtin_str_spec
