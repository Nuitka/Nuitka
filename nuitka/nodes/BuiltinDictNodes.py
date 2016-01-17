#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Node for the calls to the 'dict' built-in.

"""

from nuitka.nodes.DictionaryNodes import (
    ExpressionKeyValuePair,
    ExpressionMakeDict
)
from nuitka.nodes.NodeMakingHelpers import wrapExpressionWithNodeSideEffects
from nuitka.optimizations.BuiltinOptimization import builtin_dict_spec

from .BuiltinIteratorNodes import ExpressionBuiltinIter1
from .ConstantRefNodes import ExpressionConstantRef
from .NodeBases import ExpressionChildrenHavingBase


class ExpressionBuiltinDict(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_DICT"

    named_children = (
        "pos_arg",
        "pairs"
    )

    def __init__(self, pos_arg, pairs, source_ref):
        assert type(pos_arg) not in (tuple, list), source_ref
        assert type(pairs) in (tuple, list), source_ref

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "pos_arg" : pos_arg,
                "pairs"   : tuple(
                    ExpressionKeyValuePair(
                        ExpressionConstantRef(key, source_ref),
                        value,
                        value.getSourceReference()
                    )
                    for key, value in
                    pairs
                )
            },
            source_ref = source_ref
        )

    getPositionalArgument = ExpressionChildrenHavingBase.childGetter("pos_arg")
    getNamedArgumentPairs = ExpressionChildrenHavingBase.childGetter("pairs")

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
        pos_arg = self.getPositionalArgument()
        pairs = self.getNamedArgumentPairs()

        if pos_arg is None:
            new_node = ExpressionMakeDict(
                pairs      = self.getNamedArgumentPairs(),
                source_ref = self.source_ref
            )

            # This cannot raise anymore than its arguments, as the keys will
            # be known as hashable, due to being Python parameters before.

            return (
                new_node,
                "new_expression",
                "Replace 'dict' built-in call dictionary creation from arguments."
            )

        pos_iteration_length = pos_arg.getIterationLength()

        if pos_iteration_length == 0:
            new_node = ExpressionMakeDict(
                pairs      = self.getNamedArgumentPairs(),
                source_ref = self.source_ref
            )

            # Maintain potential side effects from the positional arguments.
            new_node = wrapExpressionWithNodeSideEffects(
                old_node = ExpressionBuiltinIter1(
                    value      = pos_arg,
                    source_ref = self.source_ref
                ),
                new_node = new_node
            )

            # Just in case, the iteration may do that.
            if pos_arg.mayRaiseExceptionIter(BaseException):
                constraint_collection.onExceptionRaiseExit(BaseException)

            return (
                new_node,
                "new_expression",
                "Replace 'dict' built-in call dictionary creation from arguments."
            )

        if pos_iteration_length is not None and \
           pos_iteration_length + len(pairs) < 256 and \
           self.hasOnlyConstantArguments():
            if pos_arg is not None:
                pos_args = (
                    pos_arg,
                )
            else:
                pos_args = None

            return constraint_collection.getCompileTimeComputationResult(
                node        = self,
                computation = lambda : builtin_dict_spec.simulateCall(
                    (pos_args, self.getNamedArgumentPairs())
                ),
                description = "Replace 'dict' call with constant arguments."
            )
        else:
            constraint_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

    def mayRaiseException(self, exception_type):
        pos_arg = self.getPositionalArgument()

        # TODO: Determining if it's sufficient is not easy but possible.
        if pos_arg is not None:
            return True

        for arg_pair in self.getNamedArgumentPairs():
            if arg_pair.mayRaiseException(exception_type):
                return True

        return False

    def hasShapeDictionaryExact(self):
        return True
