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
""" Reformulation of comparison chain expressions.

Consult the developer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

from nuitka.nodes.AssignNodes import (
    StatementAssignmentVariable,
    StatementDelVariable
)
from nuitka.nodes.VariableRefNodes import (
    ExpressionTargetTempVariableRef,
    ExpressionTempVariableRef
)

from .Helpers import buildNode, getKind, makeTryFinallyExpression
from .ReformulationBooleanExpressions import buildAndNode


def buildComparisonNode(provider, node, source_ref):
    from nuitka.nodes.NodeMakingHelpers import makeComparisonNode

    assert len(node.comparators) == len(node.ops)

    # Comparisons are re-formulated as described in the developer manual. When
    # having multiple compators, things require assignment expressions and
    # references of them to work properly. Then they can become normal "and"
    # code.

    # The operands are split out
    left = buildNode(provider, node.left, source_ref)
    rights = [
        buildNode(provider, comparator, source_ref)
        for comparator in
        node.comparators
    ]

    # Only the first comparison has as left operands as the real thing, the
    # others must reference the previous comparison right one temp variable ref.
    values = []

    # For PyLint to like it, this will hold the previous one, normally.
    keeper_variable = None

    temp_scope = None

    final = []

    for comparator, right in zip(node.ops, rights):
        if values:
            # Now we know it's not the only one, so we change the "left" to be a
            # reference to the previously saved right side.
            left = ExpressionTempVariableRef(
                variable   = keeper_variable,
                source_ref = source_ref
            )

            keeper_variable = None

        if right is not rights[-1]:
            # Now we know it's not the last one, so we ought to preseve the
            # "right" so it can be referenced by the next part that will
            # come. We do it by assining it to a temp variable to be shared with
            # the next part.
            if temp_scope is None:
                temp_scope = provider.allocateTempScope(
                    name = "comparison"
                )

            keeper_variable = provider.allocateTempVariable(
                temp_scope = temp_scope,
                name       = "value_%d" % (rights.index(right)+2),
            )

            tried = StatementAssignmentVariable(
                variable_ref = ExpressionTargetTempVariableRef(
                    variable   = keeper_variable,
                    source_ref = source_ref
                ),
                source       = right,
                source_ref   = source_ref,
            )

            # TODO: The delete must be placed later.
            final.append(
                StatementDelVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = keeper_variable,
                        source_ref = source_ref
                    ),
                    tolerant     = True,
                    source_ref   = source_ref,
                )
            )

            right = makeTryFinallyExpression(
                tried       = tried,
                final       = None,
                expression  = ExpressionTempVariableRef(
                    variable   = keeper_variable,
                    source_ref = source_ref
                ),
                source_ref  = source_ref
            )

        comparator = getKind(comparator)

        values.append(
            makeComparisonNode(
                left       = left,
                right      = right,
                comparator = comparator,
                source_ref = source_ref
            )
        )

    assert keeper_variable is None

    result = buildAndNode(
        provider   = provider,
        values     = values,
        source_ref = source_ref
    )

    if final:
        return makeTryFinallyExpression(
            tried      = None,
            expression = result,
            final      = final,
            source_ref = source_ref
        )
    else:
        return result
