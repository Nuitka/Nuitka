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
""" Reformulation of boolean and/or expressions.

Consult the developer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

from nuitka.nodes.AssignNodes import (
    StatementAssignmentVariable,
    StatementDelVariable
)
from nuitka.nodes.ConditionalNodes import ExpressionConditional
from nuitka.nodes.OperatorNodes import ExpressionOperationNOT
from nuitka.nodes.VariableRefNodes import (
    ExpressionTargetTempVariableRef,
    ExpressionTempVariableRef
)

from .Helpers import (
    buildNode,
    buildNodeList,
    getKind,
    makeTryFinallyExpression,
    wrapTryFinallyLater
)


def buildBoolOpNode(provider, node, source_ref):
    bool_op = getKind(node.op)

    if bool_op == "Or":
        # The "or" may be short circuit and is therefore not a plain operation
        return buildOrNode(
            provider   = provider,
            values     = buildNodeList(provider, node.values, source_ref),
            source_ref = source_ref
        )

    elif bool_op == "And":
        # The "and" may be short circuit and is therefore not a plain operation
        return buildAndNode(
            provider   = provider,
            values     = buildNodeList(provider, node.values, source_ref),
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


def buildOrNode(provider, values, source_ref):
    values = list(values)

    result = values[-1]
    del values[-1]

    temp_scope = None
    count = 1

    while values:
        if temp_scope is None:
            temp_scope = provider.allocateTempScope(
                name = "or"
            )

        keeper_variable = provider.allocateTempVariable(
            temp_scope = temp_scope,
            name       = "value_%d" % count
        )
        count += 1

        tried = StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = keeper_variable,
                source_ref = source_ref
            ),
            source       = values[-1],
            source_ref   = source_ref,
        )

        result = makeTryFinallyExpression(
            tried      = tried,
            final      = None,
            expression = ExpressionConditional(
                condition      = ExpressionTempVariableRef(
                    variable   = keeper_variable,
                    source_ref = source_ref
                ),
                yes_expression = ExpressionTempVariableRef(
                    variable   = keeper_variable,
                    source_ref = source_ref
                ),
                no_expression  = makeTryFinallyExpression(
                    expression = result,
                    final      = None,
                    tried      = StatementDelVariable(
                        variable_ref = ExpressionTargetTempVariableRef(
                            variable   = keeper_variable,
                            source_ref = source_ref
                        ),
                        tolerant     = False,
                        source_ref   = source_ref,
                    ),
                    source_ref = source_ref
                ),
                source_ref     = source_ref
            ),
            source_ref = source_ref
        )

        wrapTryFinallyLater(
            result,
            StatementDelVariable(
                variable_ref = ExpressionTargetTempVariableRef(
                    variable   = keeper_variable,
                    source_ref = source_ref
                ),
                tolerant     = True,
                source_ref   = source_ref,
            )
        )

        del values[-1]

    return result


def buildAndNode(provider, values, source_ref):
    values = list(values)

    result = values[-1]
    del values[-1]

    temp_scope = None
    count = 1

    while values:
        if temp_scope is None:
            temp_scope = provider.allocateTempScope(
                name = "and"
            )

        keeper_variable = provider.allocateTempVariable(
            temp_scope = temp_scope,
            name       = "value_%d" % count
        )
        count += 1

        tried = StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = keeper_variable,
                source_ref = source_ref
            ),
            source       = values[-1],
            source_ref   = source_ref,
        )

        result = makeTryFinallyExpression(
            tried      = tried,
            final      = None,
            expression = ExpressionConditional(
                condition      = ExpressionTempVariableRef(
                    variable   = keeper_variable,
                    source_ref = source_ref
                ),
                no_expression  = ExpressionTempVariableRef(
                    variable   = keeper_variable,
                    source_ref = source_ref
                ),
                yes_expression = makeTryFinallyExpression(
                    expression = result,
                    final      = None,
                    tried      = StatementDelVariable(
                        variable_ref = ExpressionTargetTempVariableRef(
                            variable   = keeper_variable,
                            source_ref = source_ref
                        ),
                        tolerant     = False,
                        source_ref   = source_ref,
                    ),
                    source_ref = source_ref
                ),
                source_ref     = source_ref
            ),
            source_ref = source_ref
        )

        wrapTryFinallyLater(
            result,
            StatementDelVariable(
                variable_ref = ExpressionTargetTempVariableRef(
                    variable   = keeper_variable,
                    source_ref = source_ref
                ),
                tolerant     = True,
                source_ref   = source_ref,
            )
        )


        del values[-1]

    return result
