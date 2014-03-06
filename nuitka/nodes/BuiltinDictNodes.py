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
""" Node the calls to the 'dict' builtin.

"""

from .NodeBases import ExpressionChildrenHavingBase

from .ConstantRefNodes import ExpressionConstantRef
from .ContainerMakingNodes import ExpressionKeyValuePair

from nuitka.optimizations.BuiltinOptimization import builtin_dict_spec


class ExpressionBuiltinDict(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_DICT"

    named_children = ( "pos_arg", "pairs" )

    def __init__(self, pos_arg, pairs, source_ref):
        assert type( pos_arg ) not in ( tuple, list ), source_ref
        assert type( pairs ) in ( tuple, list ), source_ref

        ExpressionChildrenHavingBase.__init__(
            self,
            values = {
                "pos_arg" : pos_arg,
                "pairs"   : tuple(
                    ExpressionKeyValuePair(
                        ExpressionConstantRef( key, source_ref ),
                        value,
                        value.getSourceReference()
                    )
                    for key, value in
                    pairs
                )
            },
            source_ref = source_ref
        )

    getPositionalArgument = ExpressionChildrenHavingBase.childGetter( "pos_arg" )
    getNamedArgumentPairs = ExpressionChildrenHavingBase.childGetter( "pairs" )

    def hasOnlyConstantArguments(self):
        pos_arg = self.getPositionalArgument()

        if pos_arg is not None and not pos_arg.isCompileTimeConstant():
            return False

        for arg_pair in self.getNamedArgumentPairs():
            if not arg_pair.getKey().isCompileTimeConstant():
                return False
            if not arg_pair.getValue().isCompileTimeConstant():
                return False

        return True

    def computeExpression(self, constraint_collection):
        # Children can tell all we need to know, pylint: disable=W0613

        if self.hasOnlyConstantArguments():
            pos_arg = self.getPositionalArgument()

            if pos_arg is not None:
                pos_args = ( pos_arg, )
            else:
                pos_args = None

            from .NodeMakingHelpers import getComputationResult

            return getComputationResult(
                node         = self,
                computation = lambda : builtin_dict_spec.simulateCall(
                    ( pos_args, self.getNamedArgumentPairs() )
                ),
                description = "Replace dict call with constant arguments."
            )
        else:
            return self, None, None
