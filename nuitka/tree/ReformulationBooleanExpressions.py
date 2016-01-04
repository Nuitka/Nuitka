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
""" Reformulation of boolean and/or expressions.

Consult the developer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

from nuitka.nodes.ConditionalNodes import (
    ExpressionConditionalAND,
    ExpressionConditionalOR
)
from nuitka.nodes.OperatorNodes import ExpressionOperationNOT

from .Helpers import buildNode, buildNodeList, getKind


def buildBoolOpNode(provider, node, source_ref):
    bool_op = getKind(node.op)

    if bool_op == "Or":
        # The "or" may be short circuit and is therefore not a plain operation.
        values = buildNodeList(provider, node.values, source_ref)

        for value in values[:-1]:
            value.setCompatibleSourceReference(values[-1].getSourceReference())

        source_ref = values[-1].getSourceReference()

        return buildOrNode(
            values     = values,
            source_ref = source_ref
        )

    elif bool_op == "And":
        # The "and" may be short circuit and is therefore not a plain operation.
        values = buildNodeList(provider, node.values, source_ref)

        for value in values[:-1]:
            value.setCompatibleSourceReference(values[-1].getSourceReference())

        source_ref = values[-1].getSourceReference()

        return buildAndNode(
            values     = values,
            source_ref = source_ref
        )
    elif bool_op == "Not":
        # The "not" is really only a unary operation and no special.
        return ExpressionOperationNOT(
            operand    = buildNode(provider, node.operand, source_ref),
            source_ref = source_ref
        )
    else:
        assert False, bool_op


def buildOrNode(values, source_ref):
    values = list(values)

    result = values.pop()

    # When we encounter, "or", we expect it to be at least two values.
    assert values

    while values:
        result = ExpressionConditionalOR(
            left       = values.pop(),
            right      = result,
            source_ref = source_ref
        )

    return result


def buildAndNode(values, source_ref):
    values = list(values)

    result = values.pop()

    # Unlike "or", for "and", this is used with only one value.

    while values:
        result = ExpressionConditionalAND(
            left       = values.pop(),
            right      = result,
            source_ref = source_ref
        )

    return result
