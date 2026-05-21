#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Node the calls to the 'sum' built-in.

This is a rather challenging case for optimization, as it has C code behind
it that could be in-lined sometimes for more static analysis.

"""

from nuitka.specs import BuiltinParameterSpecs

from .ChildrenHavingMixins import (
    ChildHavingLowMixin,
    ChildHavingSequenceMixin,
    ChildrenHavingLowHighMixin,
    ChildrenHavingLowHighStepMixin,
    ChildrenHavingSequenceStartMixin,
)
from .ExpressionBases import ExpressionBase
from .ExpressionShapeMixins import ExpressionIntShapeExactMixin


def _isIdentityGenexprBody(generator_body):
    """Check that a generator body is a simple identity transform (yield loop var directly).

    After optimization the AST looks like:
        StatementsSequence
          STATEMENT_TRY (outer cleanup)
            tried: StatementsSequence
              STATEMENTS_FRAME_GENERATOR
                STATEMENT_TRY (StopIteration handler)
                  tried: StatementsSequence
                    STATEMENT_LOOP
                      loop_body: StatementsSequence
                        [0] STATEMENT_TRY
                              tried: STATEMENT_ASSIGNMENT_VARIABLE_GENERIC
                              source = BuiltinNext1(.0)
                        [1] STATEMENT_ASSIGNMENT_VARIABLE_FROM_TEMP_VARIABLE
                        [2] STATEMENT_EXPRESSION_ONLY (yield <loop_var>)

    Returns the loop variable if identity, None otherwise.
    """
    from .GeneratorNodes import ExpressionGeneratorObjectBody

    if not isinstance(generator_body, ExpressionGeneratorObjectBody):
        return None

    body = generator_body.subnode_body
    if body is None or not body.isStatementsSequence():
        return None

    bstmts = body.subnode_statements
    if len(bstmts) < 1 or not bstmts[0].isStatementTry():
        return None

    # Step into outer cleanup try
    outer_try_tried = bstmts[0].subnode_tried
    if outer_try_tried is None or not outer_try_tried.isStatementsSequence():
        return None

    outer_tried_stmts = outer_try_tried.subnode_statements
    if (
        len(outer_tried_stmts) < 1
        or outer_tried_stmts[0].kind != "STATEMENTS_FRAME_GENERATOR"
    ):
        return None

    frame_gen = outer_tried_stmts[0]
    frame_stmts = frame_gen.subnode_statements
    if len(frame_stmts) < 1 or not frame_stmts[0].isStatementTry():
        return None

    # Step into inner StopIteration try
    inner_try_tried = frame_stmts[0].subnode_tried
    if inner_try_tried is None or not inner_try_tried.isStatementsSequence():
        return None

    inner_tried_stmts = inner_try_tried.subnode_statements
    if len(inner_tried_stmts) < 1 or not inner_tried_stmts[0].isStatementLoop():
        return None

    loop = inner_tried_stmts[0]
    loop_body = loop.subnode_loop_body
    if loop_body is None or not loop_body.isStatementsSequence():
        return None

    loop_stmts = loop_body.subnode_statements

    # Need at least 3 statements: try/next, assign-to-var, yield
    if len(loop_stmts) < 3:
        return None

    # Statement [0]: try/except with next(.0) inside
    try_stmt = loop_stmts[0]
    if not try_stmt.isStatementTry():
        return None

    tried = try_stmt.subnode_tried
    if tried is None or not tried.isStatementsSequence():
        return None

    tried_stmts = tried.subnode_statements
    if len(tried_stmts) != 1:
        return None

    next_assign = tried_stmts[0]
    if not next_assign.isStatementAssignmentVariable():
        return None
    from .BuiltinNextNodes import ExpressionBuiltinNext1

    if not isinstance(next_assign.subnode_source, ExpressionBuiltinNext1):
        return None

    # Statement [1]: loop_var = iter_value (from temp variable)
    var_assign = loop_stmts[1]
    if not var_assign.isStatementAssignmentVariable():
        return None

    # Statement [2]: yield loop_var
    yield_stmt = loop_stmts[2]
    if not yield_stmt.isStatementExpressionOnly():
        return None

    from .YieldNodes import ExpressionYield

    if not isinstance(yield_stmt.subnode_expression, ExpressionYield):
        return None

    yielded = yield_stmt.subnode_expression.subnode_expression

    # Identity check: the yielded expression is the same variable that was assigned
    from .VariableRefNodes import (
        ExpressionTempVariableRef,
        ExpressionVariableRef,
    )

    if isinstance(yielded, (ExpressionVariableRef, ExpressionTempVariableRef)):
        if yielded.variable is var_assign.variable:
            return var_assign.variable

    return None


def _getGeneratorExprFromTry(stmt):
    """Extract ExpressionMakeGeneratorObject from a StatementTry's tried block.

    The tried block is a StatementsSequence wrapping StatementReturn.
    """
    tried = stmt.subnode_tried
    if tried is None:
        return None
    if tried.isStatementsSequence():
        for s in tried.subnode_statements:
            if s.isStatementReturn():
                candidate = s.subnode_expression
                from .GeneratorNodes import ExpressionMakeGeneratorObject

                if isinstance(candidate, ExpressionMakeGeneratorObject):
                    return candidate
    elif tried.isStatementReturn():
        candidate = tried.subnode_expression
        from .GeneratorNodes import ExpressionMakeGeneratorObject

        if isinstance(candidate, ExpressionMakeGeneratorObject):
            return candidate
    return None


def _tryExtractRangeFromGenexprOutline(sequence):
    """If sequence is an outline body wrapping sum(x for x in range(...)),
    extract and return the raw range node (Xrange1/2/3).

    The outline body structure for a genexpr is:
        StatementsSequence:
          [0] .0 = BuiltinIter1(Xrange1/2/3(n))
          [1] StatementTry:
                tried: StatementsSequence [StatementReturn(ExpressionMakeGeneratorObject(...))]
                final: release .0
    """
    from .OutlineNodes import ExpressionOutlineBody

    if not isinstance(sequence, ExpressionOutlineBody):
        return None

    body = sequence.subnode_body
    if body is None or not body.isStatementsSequence():
        return None

    stmts = body.subnode_statements

    iter_assign = None
    generator_expr = None

    for stmt in stmts:
        if stmt.isStatementAssignmentVariable():
            source = stmt.subnode_source
            from .BuiltinIteratorNodes import ExpressionBuiltinIter1

            if isinstance(source, ExpressionBuiltinIter1):
                iter_assign = stmt
        elif stmt.isStatementTry():
            gen_expr = _getGeneratorExprFromTry(stmt)
            if gen_expr is not None:
                generator_expr = gen_expr

    if iter_assign is None or generator_expr is None:
        return None

    gen_body = generator_expr.subnode_generator_ref.getFunctionBody()
    if _isIdentityGenexprBody(gen_body) is None:
        return None

    builtin_iter = iter_assign.subnode_source
    range_node = builtin_iter.subnode_value

    from .BuiltinRangeNodes import (
        ExpressionBuiltinXrange1,
        ExpressionBuiltinXrange2,
        ExpressionBuiltinXrange3,
    )

    if isinstance(
        range_node,
        (ExpressionBuiltinXrange1, ExpressionBuiltinXrange2, ExpressionBuiltinXrange3),
    ):
        return range_node

    return None


def _makeSumXrangeNode(range_node, source_ref):
    """Create the appropriate ExpressionBuiltinSumXrange* node from an Xrange* node."""
    from .BuiltinRangeNodes import (
        ExpressionBuiltinXrange1,
        ExpressionBuiltinXrange2,
        ExpressionBuiltinXrange3,
    )

    if isinstance(range_node, ExpressionBuiltinXrange1):
        return ExpressionBuiltinSumXrange1(
            low=range_node.subnode_low, source_ref=source_ref
        )
    if isinstance(range_node, ExpressionBuiltinXrange2):
        return ExpressionBuiltinSumXrange2(
            low=range_node.subnode_low,
            high=range_node.subnode_high,
            source_ref=source_ref,
        )
    if isinstance(range_node, ExpressionBuiltinXrange3):
        return ExpressionBuiltinSumXrange3(
            low=range_node.subnode_low,
            high=range_node.subnode_high,
            step=range_node.subnode_step,
            source_ref=source_ref,
        )

    return None


class ExpressionBuiltinSumMixin(object):
    # Mixins are required to define empty slots
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


class ExpressionBuiltinSum1(
    ExpressionBuiltinSumMixin, ChildHavingSequenceMixin, ExpressionBase
):
    kind = "EXPRESSION_BUILTIN_SUM1"

    named_children = ("sequence",)

    def __init__(self, sequence, source_ref):
        ChildHavingSequenceMixin.__init__(self, sequence=sequence)

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        sequence = self.subnode_sequence

        from .BuiltinRangeNodes import (
            ExpressionBuiltinXrange1,
            ExpressionBuiltinXrange2,
            ExpressionBuiltinXrange3,
        )

        if isinstance(
            sequence,
            (
                ExpressionBuiltinXrange1,
                ExpressionBuiltinXrange2,
                ExpressionBuiltinXrange3,
            ),
        ):
            return (
                _makeSumXrangeNode(sequence, self.source_ref),
                "new_expression",
                "Fused sum(range(...)) to direct C arithmetic",
            )

        range_node = _tryExtractRangeFromGenexprOutline(sequence)
        if range_node is not None:
            key = {
                ExpressionBuiltinXrange1: "stop",
                ExpressionBuiltinXrange2: "start,stop",
                ExpressionBuiltinXrange3: "start,stop,step",
            }.get(type(range_node), "...")
            return (
                _makeSumXrangeNode(range_node, self.source_ref),
                "new_expression",
                "Fused sum(x for x in range(%s)) to direct C arithmetic" % key,
            )

        return self.computeBuiltinSpec(
            trace_collection=trace_collection, given_values=(sequence,)
        )


class ExpressionBuiltinSum2(
    ExpressionBuiltinSumMixin, ChildrenHavingSequenceStartMixin, ExpressionBase
):
    kind = "EXPRESSION_BUILTIN_SUM2"

    named_children = ("sequence", "start")

    def __init__(self, sequence, start, source_ref):
        ChildrenHavingSequenceStartMixin.__init__(
            self,
            sequence=sequence,
            start=start,
        )

        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        sequence = self.subnode_sequence
        start = self.subnode_start

        # TODO: Protect against large xrange constants
        return self.computeBuiltinSpec(
            trace_collection=trace_collection, given_values=(sequence, start)
        )


class ExpressionBuiltinSumXrange1(
    ExpressionIntShapeExactMixin, ChildHavingLowMixin, ExpressionBase
):
    """Fused sum(range(stop)) — emits direct C arithmetic, no heap allocation."""

    kind = "EXPRESSION_BUILTIN_SUM_XRANGE1"

    named_children = ("low",)

    def __init__(self, low, source_ref):
        ChildHavingLowMixin.__init__(self, low=low)
        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        low = self.subnode_low

        if low.isCompileTimeConstant():
            stop = low.getCompileTimeConstant()
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: sum(range(stop)),
                description="sum(range(stop)) computed at compile time",
            )

        trace_collection.onExceptionRaiseExit(BaseException)
        return self, None, None

    def mayRaiseException(self, exception_type):
        return self.subnode_low.mayRaiseException(exception_type)


class ExpressionBuiltinSumXrange2(
    ExpressionIntShapeExactMixin, ChildrenHavingLowHighMixin, ExpressionBase
):
    """Fused sum(range(start, stop)) — emits direct C arithmetic, no heap allocation."""

    kind = "EXPRESSION_BUILTIN_SUM_XRANGE2"

    named_children = ("low", "high")

    def __init__(self, low, high, source_ref):
        ChildrenHavingLowHighMixin.__init__(self, low=low, high=high)
        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        low = self.subnode_low
        high = self.subnode_high

        if low.isCompileTimeConstant() and high.isCompileTimeConstant():
            start = low.getCompileTimeConstant()
            stop = high.getCompileTimeConstant()
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: sum(range(start, stop)),
                description="sum(range(start,stop)) computed at compile time",
            )

        trace_collection.onExceptionRaiseExit(BaseException)
        return self, None, None

    def mayRaiseException(self, exception_type):
        return self.subnode_low.mayRaiseException(
            exception_type
        ) or self.subnode_high.mayRaiseException(exception_type)


class ExpressionBuiltinSumXrange3(
    ExpressionIntShapeExactMixin, ChildrenHavingLowHighStepMixin, ExpressionBase
):
    """Fused sum(range(start, stop, step)) — emits direct C arithmetic, no heap allocation."""

    kind = "EXPRESSION_BUILTIN_SUM_XRANGE3"

    named_children = ("low", "high", "step")

    def __init__(self, low, high, step, source_ref):
        ChildrenHavingLowHighStepMixin.__init__(self, low=low, high=high, step=step)
        ExpressionBase.__init__(self, source_ref)

    def computeExpression(self, trace_collection):
        low = self.subnode_low
        high = self.subnode_high
        step = self.subnode_step

        if (
            low.isCompileTimeConstant()
            and high.isCompileTimeConstant()
            and step.isCompileTimeConstant()
        ):
            start = low.getCompileTimeConstant()
            stop = high.getCompileTimeConstant()
            step_val = step.getCompileTimeConstant()
            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: sum(range(start, stop, step_val)),
                description="sum(range(start,stop,step)) computed at compile time",
            )

        trace_collection.onExceptionRaiseExit(BaseException)
        return self, None, None

    def mayRaiseException(self, exception_type):
        return (
            self.subnode_low.mayRaiseException(exception_type)
            or self.subnode_high.mayRaiseException(exception_type)
            or self.subnode_step.mayRaiseException(exception_type)
        )


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
