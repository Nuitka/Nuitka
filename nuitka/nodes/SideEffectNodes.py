#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Node that models side effects.

Sometimes, the effect of an expression needs to be had, but the value itself
does not matter at all.
"""

from .ChildrenHavingMixins import ChildrenHavingSideEffectsTupleExpressionMixin
from .ExpressionBases import ExpressionBase
from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions


class ExpressionSideEffects(
    ChildrenHavingSideEffectsTupleExpressionMixin, ExpressionBase
):
    kind = "EXPRESSION_SIDE_EFFECTS"

    named_children = ("side_effects|tuple+setter", "expression|setter")

    def __init__(self, side_effects, expression, source_ref):
        ChildrenHavingSideEffectsTupleExpressionMixin.__init__(
            self, side_effects=side_effects, expression=expression
        )

        ExpressionBase.__init__(self, source_ref)

    @staticmethod
    def isExpressionSideEffects():
        return True

    def getTypeShape(self):
        return self.subnode_expression.getTypeShape()

    def computeExpressionRaw(self, trace_collection):
        new_side_effects = []

        side_effects = self.subnode_side_effects

        for count, side_effect in enumerate(side_effects):
            side_effect = trace_collection.onExpression(side_effect)

            if side_effect.willRaiseAnyException():
                for c in side_effects[count + 1 :]:
                    c.finalize()

                if new_side_effects:
                    expression = self.subnode_expression
                    expression.finalize()

                    self.setChildExpression(side_effect)

                    return (
                        self,
                        "new_expression",
                        "Side effects caused exception raise.",
                    )
                else:
                    del self.parent
                    del self.subnode_side_effects

                    return (
                        side_effect,
                        "new_expression",
                        "Side effects caused exception raise.",
                    )

            if side_effect.isExpressionSideEffects():
                new_side_effects.extend(side_effect.subnode_side_effects)

                del side_effect.parent
                del side_effect.subnode_side_effects
            elif side_effect is not None and side_effect.mayHaveSideEffects():
                new_side_effects.append(side_effect)

        self.setChildSideEffects(tuple(new_side_effects))

        trace_collection.onExpression(self.subnode_expression)

        if not new_side_effects:
            return (
                self.subnode_expression,
                "new_expression",
                "Removed now empty side effects.",
            )

        return self, None, None

    def getTruthValue(self):
        return self.subnode_expression.getTruthValue()

    def computeExpressionDrop(self, statement, trace_collection):
        # Side effects can  become statements.

        expressions = self.subnode_side_effects + (self.subnode_expression,)

        result = makeStatementOnlyNodesFromExpressions(expressions=expressions)

        return (
            result,
            "new_statements",
            """\
Turned side effects of expression only statement into statements.""",
        )
