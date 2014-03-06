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

from nuitka.nodes.OperatorNodes import ExpressionOperationNOT
from nuitka.nodes.ConditionalNodes import ExpressionConditional
from nuitka.nodes.KeeperNodes import (
    ExpressionAssignmentTempKeeper,
    ExpressionTempKeeperRef
)

from .Helpers import (
    buildNodeList,
    buildNode,
    getKind
)

def buildBoolOpNode(provider, node, source_ref):
    bool_op = getKind( node.op )

    if bool_op == "Or":
        # The "or" may be short circuit and is therefore not a plain operation
        return buildOrNode(
            provider   = provider,
            values     = buildNodeList( provider, node.values, source_ref ),
            source_ref = source_ref
        )

    elif bool_op == "And":
        # The "and" may be short circuit and is therefore not a plain operation
        return buildAndNode(
            provider   = provider,
            values     = buildNodeList( provider, node.values, source_ref ),
            source_ref = source_ref
        )
    elif bool_op == "Not":
        # The "not" is really only a unary operation and no special.
        return ExpressionOperationNOT(
            operand    = buildNode( provider, node.operand, source_ref ),
            source_ref = source_ref
        )
    else:
        assert False, bool_op


def buildOrNode(provider, values, source_ref):
    result = values[ -1 ]
    del values[ -1 ]

    while True:
        keeper_variable = provider.allocateTempKeeperVariable()

        tmp_assign = ExpressionAssignmentTempKeeper(
            variable   = keeper_variable.makeReference( provider ),
            source     = values[ -1 ],
            source_ref = source_ref
        )
        del values[ -1 ]

        result = ExpressionConditional(
            condition      = tmp_assign,
            yes_expression = ExpressionTempKeeperRef(
                variable   = keeper_variable.makeReference( provider ),
                source_ref = source_ref
            ),
            no_expression  = result,
            source_ref      = source_ref
        )

        if not values:
            break

    return result

def buildAndNode(provider, values, source_ref):
    result = values[ -1 ]
    del values[ -1 ]

    while values:
        keeper_variable = provider.allocateTempKeeperVariable()

        tmp_assign = ExpressionAssignmentTempKeeper(
            variable   = keeper_variable.makeReference( provider ),
            source     = values[ -1 ],
            source_ref = source_ref
        )
        del values[ -1 ]

        result = ExpressionConditional(
            condition      = tmp_assign,
            no_expression = ExpressionTempKeeperRef(
                variable   = keeper_variable.makeReference( provider ),
                source_ref = source_ref
            ),
            yes_expression  = result,
            source_ref      = source_ref
        )

    return result
