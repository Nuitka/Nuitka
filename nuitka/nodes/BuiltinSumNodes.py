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


def _getGeneratorLoopBody(generator_body):  # pylint: disable=too-many-return-statements
    """Walk down the post-optimization AST to extract the generator loop body.

    After optimization the AST looks like:
        StatementsSequence
          STATEMENT_TRY (outer cleanup)
            tried: StatementsSequence
              STATEMENTS_FRAME_GENERATOR
                STATEMENT_TRY (StopIteration handler)
                  tried: StatementsSequence
                    STATEMENT_LOOP
                      loop_body: StatementsSequence

    Returns the loop body StatementsSequence, or None.
    """
    from .GeneratorNodes import ExpressionGeneratorObjectBody

    if not isinstance(generator_body, ExpressionGeneratorObjectBody):
        return None

    node = generator_body.subnode_body
    if node is None or not node.isStatementsSequence():
        return None

    stmts = node.subnode_statements
    if len(stmts) < 1 or not stmts[0].isStatementTry():
        return None

    node = stmts[0].subnode_tried
    if node is None or not node.isStatementsSequence():
        return None

    stmts = node.subnode_statements
    if len(stmts) < 1 or stmts[0].kind != "STATEMENTS_FRAME_GENERATOR":
        return None

    node = stmts[0].subnode_statements
    if len(node) < 1 or not node[0].isStatementTry():
        return None

    node = node[0].subnode_tried
    if node is None or not node.isStatementsSequence():
        return None

    stmts = node.subnode_statements
    if len(stmts) < 1 or not stmts[0].isStatementLoop():
        return None

    loop_body = stmts[0].subnode_loop_body
    if loop_body is None or not loop_body.isStatementsSequence():
        return None

    return loop_body


def _isIdentityGenexprBody(
    generator_body,
):  # pylint: disable=too-many-return-statements
    """Check that a generator body is identity (yields loop variable directly).

    Returns the loop variable if identity, None otherwise.
    """
    loop_body = _getGeneratorLoopBody(generator_body)
    if loop_body is None:
        return None

    loop_stmts = loop_body.subnode_statements

    if len(loop_stmts) < 3:
        return None

    if not loop_stmts[0].isStatementTry():
        return None

    node = loop_stmts[0].subnode_tried
    if node is None or not node.isStatementsSequence():
        return None

    stmts = node.subnode_statements
    if len(stmts) != 1:
        return None

    if not stmts[0].isStatementAssignmentVariable():
        return None
    from .BuiltinNextNodes import ExpressionBuiltinNext1

    if not isinstance(stmts[0].subnode_source, ExpressionBuiltinNext1):
        return None

    if not loop_stmts[1].isStatementAssignmentVariable():
        return None

    if not loop_stmts[2].isStatementExpressionOnly():
        return None
    from .YieldNodes import ExpressionYield

    if not isinstance(loop_stmts[2].subnode_expression, ExpressionYield):
        return None

    yielded = loop_stmts[2].subnode_expression.subnode_expression

    from .VariableRefNodes import (
        ExpressionTempVariableRef,
        ExpressionVariableRef,
    )

    if isinstance(yielded, (ExpressionVariableRef, ExpressionTempVariableRef)):
        if yielded.variable is loop_stmts[1].variable:
            return loop_stmts[1].variable

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
    """
    from .OutlineNodes import ExpressionOutlineBody

    if not isinstance(sequence, ExpressionOutlineBody):
        return None

    if (
        sequence.subnode_body is None
        or not sequence.subnode_body.isStatementsSequence()
    ):
        return None

    stmts = sequence.subnode_body.subnode_statements

    iter_assign = None
    generator_expr = None

    for stmt in stmts:
        if stmt.isStatementAssignmentVariable():
            from .BuiltinIteratorNodes import ExpressionBuiltinIter1

            if isinstance(stmt.subnode_source, ExpressionBuiltinIter1):
                iter_assign = stmt
        elif stmt.isStatementTry():
            generator_expr = _getGeneratorExprFromTry(stmt) or generator_expr

    if iter_assign is None or generator_expr is None:
        return None

    if (
        _isIdentityGenexprBody(generator_expr.subnode_generator_ref.getFunctionBody())
        is None
    ):
        return None

    range_node = iter_assign.subnode_source.subnode_value

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
