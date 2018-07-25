#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .ExpressionBases import ExpressionChildrenHavingBase
from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions


def checkSideEffects(value):
    real_value = []

    for child in value:
        if child.isExpressionSideEffects():
            real_value.extend(child.getSideEffects())
            real_value.append(child.getExpression())
        else:
            assert child.isExpression()

            real_value.append(child)

    return tuple(real_value)


class ExpressionSideEffects(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_SIDE_EFFECTS"

    named_children = (
        "side_effects",
        "expression"
    )

    checkers = {
        "side_effects" : checkSideEffects
    }

    def __init__(self, side_effects, expression, source_ref):
        # We expect to be not used without there actually being side effects.
        assert side_effects

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "side_effects" : tuple(side_effects),
                "expression"   : expression
            },
            source_ref = source_ref
        )

    getSideEffects  = ExpressionChildrenHavingBase.childGetter("side_effects")
    setSideEffects  = ExpressionChildrenHavingBase.childSetter("side_effects")

    getExpression = ExpressionChildrenHavingBase.childGetter("expression")

    def isExpressionSideEffects(self):
        return True

    def computeExpressionRaw(self, trace_collection):
        new_side_effects = []

        side_effects = self.getSideEffects()

        for count, side_effect in enumerate(side_effects):
            side_effect = trace_collection.onExpression(side_effect)

            if side_effect.willRaiseException(BaseException):
                for c in side_effects[count+1:]:
                    c.finalize()

                if new_side_effects:
                    expression = self.getExpression()
                    expression.finalize()

                    self.setChild("expression", side_effect)

                    return self, "new_expression", "Side effects caused exception raise."
                else:
                    del self.parent
                    del self.subnode_side_effects

                    return side_effect, "new_expression", "Side effects caused exception raise."

            if side_effect.isExpressionSideEffects():
                new_side_effects.extend(
                    side_effect.getSideEffects()
                )

                del side_effect.parent
                del side_effect.subnode_side_effects

            if side_effect is not None and side_effect.mayHaveSideEffects():
                new_side_effects.append(side_effect)

        trace_collection.onExpression(self.subnode_expression)

        if not new_side_effects:
            return self.subnode_expression, "new_expression", "Removed empty side effects."

        return self, None, None

    def willRaiseException(self, exception_type):
        for child in self.getVisitableNodes():
            if child.willRaiseException(exception_type):
                return True

        return False

    def getTruthValue(self):
        return self.getExpression().getTruthValue()

    def computeExpressionDrop(self, statement, trace_collection):
        # Side effects can  become statements.

        expressions = self.getSideEffects() + (self.getExpression(),)

        result = makeStatementOnlyNodesFromExpressions(
            expressions = expressions
        )

        return result, "new_statements", """\
Turned side effects of expression only statement into statements."""
