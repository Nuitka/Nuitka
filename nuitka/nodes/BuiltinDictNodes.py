#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.specs.BuiltinParameterSpecs import builtin_dict_spec

from .BuiltinIteratorNodes import ExpressionBuiltinIter1
from .ChildrenHavingMixins import ChildrenHavingPosArgOptionalPairsTupleMixin
from .DictionaryNodes import makeExpressionMakeDict
from .ExpressionBases import ExpressionBase
from .ExpressionShapeMixins import ExpressionDictShapeExactMixin
from .NodeMakingHelpers import wrapExpressionWithNodeSideEffects


class ExpressionBuiltinDict(
    ExpressionDictShapeExactMixin,
    ChildrenHavingPosArgOptionalPairsTupleMixin,
    ExpressionBase,
):
    kind = "EXPRESSION_BUILTIN_DICT"

    named_children = ("pos_arg|optional", "pairs|tuple")

    def __init__(self, pos_arg, pairs, source_ref):
        ChildrenHavingPosArgOptionalPairsTupleMixin.__init__(
            self,
            pos_arg=pos_arg,
            pairs=pairs,
        )

        ExpressionBase.__init__(self, source_ref)

    def hasOnlyConstantArguments(self):
        pos_arg = self.subnode_pos_arg

        if pos_arg is not None and not pos_arg.isCompileTimeConstant():
            return False

        for arg_pair in self.subnode_pairs:
            if not arg_pair.isCompileTimeConstant():
                return False

        return True

    def computeExpression(self, trace_collection):
        pos_arg = self.subnode_pos_arg
        pairs = self.subnode_pairs

        if pos_arg is None:
            new_node = makeExpressionMakeDict(
                pairs=self.subnode_pairs, source_ref=self.source_ref
            )

            # This cannot raise anymore than its arguments, as the keys will
            # be known as hashable, due to being Python parameters before.

            return (
                new_node,
                "new_expression",
                "Replace 'dict' built-in call dictionary creation from arguments.",
            )

        pos_iteration_length = pos_arg.getIterationLength()

        if pos_iteration_length == 0:
            new_node = makeExpressionMakeDict(
                pairs=self.subnode_pairs, source_ref=self.source_ref
            )

            # Maintain potential side effects from the positional arguments.
            new_node = wrapExpressionWithNodeSideEffects(
                old_node=ExpressionBuiltinIter1(
                    value=pos_arg, source_ref=self.source_ref
                ),
                new_node=new_node,
            )

            # Just in case, the iteration may do that.
            if not pos_arg.hasShapeSlotIter():
                trace_collection.onExceptionRaiseExit(BaseException)

            return (
                new_node,
                "new_expression",
                "Replace 'dict' built-in call dictionary creation from arguments.",
            )

        if (
            pos_iteration_length is not None
            and pos_iteration_length + len(pairs) < 256
            and self.hasOnlyConstantArguments()
        ):
            if pos_arg is not None:
                pos_args = (pos_arg,)
            else:
                pos_args = None

            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: builtin_dict_spec.simulateCall(
                    (pos_args, self.subnode_pairs)
                ),
                description="Replace 'dict' call with constant arguments.",
            )
        else:
            trace_collection.onExceptionRaiseExit(BaseException)

            return self, None, None

    def mayRaiseException(self, exception_type):
        pos_arg = self.subnode_pos_arg

        # TODO: Determining if it's sufficient is not easy but possible.
        if pos_arg is not None:
            return True

        for arg_pair in self.subnode_pairs:
            if arg_pair.mayRaiseException(exception_type):
                return True

        return False
