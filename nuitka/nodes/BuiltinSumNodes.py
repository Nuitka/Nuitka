#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Node the calls to the 'sum' built-in.

This is a rather challenging case for optimization, as it has C code behind
it that could be in-lined sometimes for more static analysis.

"""

from nuitka.specs import BuiltinParameterSpecs

from .ExpressionBases import (
    ExpressionChildHavingBase,
    ExpressionChildrenHavingBase,
)


class ExpressionBuiltinSumMixin(object):
    # Mixins are required to slots
    __slots__ = ()

    builtin_spec = BuiltinParameterSpecs.builtin_sum_spec

    def computeBuiltinSpec(self, trace_collection, given_values):
        assert self.builtin_spec is not None, self

        if not self.builtin_spec.isCompileTimeComputable(given_values):
            trace_collection.onExceptionRaiseExit(BaseException)

            # TODO: Raise exception known step 0.

            return self, None, None

        return trace_collection.getCompileTimeComputationResult(
            node=self,
            computation=lambda: self.builtin_spec.simulateCall(given_values),
            description="Built-in call to '%s' computed."
            % (self.builtin_spec.getName()),
        )


class ExpressionBuiltinSum1(ExpressionBuiltinSumMixin, ExpressionChildHavingBase):
    kind = "EXPRESSION_BUILTIN_SUM1"

    named_child = "sequence"

    def __init__(self, sequence, source_ref):
        assert sequence is not None

        ExpressionChildHavingBase.__init__(self, value=sequence, source_ref=source_ref)

    def computeExpression(self, trace_collection):
        sequence = self.subnode_sequence

        # TODO: Protect against large xrange constants
        return self.computeBuiltinSpec(
            trace_collection=trace_collection, given_values=(sequence,)
        )


class ExpressionBuiltinSum2(ExpressionBuiltinSumMixin, ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_SUM2"

    named_children = ("sequence", "start")

    def __init__(self, sequence, start, source_ref):
        assert sequence is not None
        assert start is not None

        ExpressionChildrenHavingBase.__init__(
            self, values={"sequence": sequence, "start": start}, source_ref=source_ref
        )

    def computeExpression(self, trace_collection):
        sequence = self.subnode_sequence
        start = self.subnode_start

        # TODO: Protect against large xrange constants
        return self.computeBuiltinSpec(
            trace_collection=trace_collection, given_values=(sequence, start)
        )
