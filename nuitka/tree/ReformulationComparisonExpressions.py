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

from nuitka.nodes.KeeperNodes import (
    ExpressionAssignmentTempKeeper,
    ExpressionTempKeeperRef
)

from .ReformulationBooleanExpressions import buildAndNode

from .Helpers import (
    buildNode,
    getKind
)

def buildComparisonNode(provider, node, source_ref):
    from nuitka.nodes.NodeMakingHelpers import makeComparisonNode

    assert len( node.comparators ) == len( node.ops )

    # Comparisons are re-formulated as described in the developer manual. When
    # having multiple compators, things require assignment expressions and
    # references of them to work properly. Then they can become normal "and"
    # code.

    # The operands are split out
    left = buildNode( provider, node.left, source_ref )
    rights = [
        buildNode( provider, comparator, source_ref )
        for comparator in
        node.comparators
    ]

    # Only the first comparison has as left operands as the real thing, the
    # others must reference the previous comparison right one temp variable ref.
    result = []

    # For PyLint to like it, this will hold the previous one, normally.
    keeper_variable = None

    for comparator, right in zip( node.ops, rights ):
        if result:
            # Now we know it's not the only one, so we change the "left" to be a
            # reference to the previously saved right side.
            left = ExpressionTempKeeperRef(
                variable   = keeper_variable.makeReference( provider ),
                source_ref = source_ref
            )

            keeper_variable = None

        if right is not rights[-1]:
            # Now we know it's not the last one, so we ought to preseve the
            # "right" so it can be referenced by the next part that will
            # come. We do it by assining it to a temp variable to be shared with
            # the next part.
            keeper_variable = provider.allocateTempKeeperVariable()

            right = ExpressionAssignmentTempKeeper(
                variable   = keeper_variable.makeReference( provider ),
                source     = right,
                source_ref = source_ref
            )

        comparator = getKind( comparator )

        result.append(
            makeComparisonNode(
                left       = left,
                right      = right,
                comparator = comparator,
                source_ref = source_ref
            )
        )

    assert keeper_variable is None

    return buildAndNode(
        provider   = provider,
        values     = result,
        source_ref = source_ref
    )
