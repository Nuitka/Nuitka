#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Reformulation of comparison chain expressions.

Consult the Developer Manual for information. TODO: Add ability to sync
source code comments with Developer Manual sections.

"""

from nuitka.nodes.ComparisonNodes import makeComparisonExpression
from nuitka.nodes.ConditionalNodes import makeStatementConditional
from nuitka.nodes.OperatorNodesUnary import ExpressionOperationNot
from nuitka.nodes.OutlineNodes import ExpressionOutlineBody
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.VariableAssignNodes import makeStatementAssignmentVariable
from nuitka.nodes.VariableRefNodes import ExpressionTempVariableRef

from .ReformulationTryFinallyStatements import makeTryFinallyReleaseStatement
from .TreeHelpers import (
    buildNode,
    getKind,
    makeStatementsSequenceFromStatement,
)


def _makeComparisonNode(left, right, comparator, source_ref):
    result = makeComparisonExpression(left, right, comparator, source_ref)
    result.setCompatibleSourceReference(source_ref=right.getCompatibleSourceReference())

    return result


def buildComparisonNode(provider, node, source_ref):
    assert len(node.comparators) == len(node.ops)

    # Comparisons are re-formulated as described in the Developer Manual. When
    # having multiple comparators, things require assignment expressions and
    # references of them to work properly. Then they can become normal "and"
    # code.

    # The operands are split out in two parts strangely.
    left = buildNode(provider, node.left, source_ref)
    rights = [
        buildNode(provider, comparator, source_ref) for comparator in node.comparators
    ]
    comparators = [getKind(comparator) for comparator in node.ops]
    # Normal, and simple case, we only have one comparison, which is what our
    # node handles only. Then we can handle it
    if len(rights) == 1:
        return _makeComparisonNode(
            left=left,
            right=rights[0],
            # TODO: The terminology of Nuitka might be messed up here.
            comparator=comparators[0],
            source_ref=source_ref,
        )

    return buildComplexComparisonNode(provider, left, rights, comparators, source_ref)


def buildComplexComparisonNode(provider, left, rights, comparators, source_ref):
    # This is a bit complex, due to the many details, pylint: disable=too-many-locals

    outline_body = ExpressionOutlineBody(
        provider=provider, name="comparison_chain", source_ref=source_ref
    )

    variables = [
        outline_body.allocateTempVariable(
            temp_scope=None, name="operand_%d" % count, temp_type="object"
        )
        for count in range(2, len(rights) + 2)
    ]

    tmp_variable = outline_body.allocateTempVariable(
        temp_scope=None, name="comparison_result", temp_type="object"
    )

    def makeTempAssignment(count, value):
        return makeStatementAssignmentVariable(
            variable=variables[count], source=value, source_ref=source_ref
        )

    def makeValueComparisonReturn(left, right, comparator):
        yield makeStatementAssignmentVariable(
            variable=tmp_variable,
            source=_makeComparisonNode(
                left=left, right=right, comparator=comparator, source_ref=source_ref
            ),
            source_ref=source_ref,
        )

        yield makeStatementConditional(
            condition=ExpressionOperationNot(
                operand=ExpressionTempVariableRef(
                    variable=tmp_variable, source_ref=source_ref
                ),
                source_ref=source_ref,
            ),
            yes_branch=StatementReturn(
                expression=ExpressionTempVariableRef(
                    variable=tmp_variable, source_ref=source_ref
                ),
                source_ref=source_ref,
            ),
            no_branch=None,
            source_ref=source_ref,
        )

    statements = []
    release_variables = []

    for count, value in enumerate(rights):
        if value is not rights[-1]:
            statements.append(makeTempAssignment(count, value))
            release_variables.append(variables[count])
            right = ExpressionTempVariableRef(
                variable=variables[count], source_ref=source_ref
            )
        else:
            right = value

        if count != 0:
            left = ExpressionTempVariableRef(
                variable=variables[count - 1], source_ref=source_ref
            )

        comparator = comparators[count]

        if value is not rights[-1]:
            statements.extend(makeValueComparisonReturn(left, right, comparator))
        else:
            statements.append(
                StatementReturn(
                    expression=_makeComparisonNode(
                        left=left,
                        right=right,
                        comparator=comparator,
                        source_ref=source_ref,
                    ),
                    source_ref=source_ref,
                )
            )
            release_variables.append(tmp_variable)

    outline_body.setChildBody(
        makeStatementsSequenceFromStatement(
            statement=makeTryFinallyReleaseStatement(
                provider=outline_body,
                tried=statements,
                variables=release_variables,
                source_ref=source_ref,
            )
        )
    )

    return outline_body


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
