#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Reformulation of Python3.10 match statements.

Consult the Developer Manual for information. TODO: Add ability to sync
source code comments with Developer Manual sections.

"""

import ast

from nuitka.nodes.AssignNodes import (
    StatementAssignmentVariable,
    StatementAssignmentVariableName,
    StatementReleaseVariable,
)
from nuitka.nodes.AttributeNodes import (
    ExpressionAttributeCheck,
    makeExpressionAttributeLookup,
)
from nuitka.nodes.BuiltinLenNodes import ExpressionBuiltinLen
from nuitka.nodes.ComparisonNodes import makeComparisonExpression
from nuitka.nodes.ConditionalNodes import makeStatementConditional
from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.SubscriptNodes import (
    ExpressionSubscriptCheck,
    ExpressionSubscriptLookup,
)
from nuitka.nodes.TypeMatchNodes import (
    ExpressionMatchTypeCheckMapping,
    ExpressionMatchTypeCheckSequence,
)
from nuitka.nodes.TypeNodes import ExpressionBuiltinIsinstance
from nuitka.nodes.VariableRefNodes import ExpressionTempVariableRef

from .ReformulationBooleanExpressions import makeAndNode, makeOrNode
from .ReformulationTryFinallyStatements import makeTryFinallyStatement
from .TreeHelpers import buildNode, buildStatementsNode, makeStatementsSequence


def _makeMatchComparison(left, right, source_ref):
    if right.isExpressionConstantBoolRef() or right.isExpressionConstantNoneRef():
        comparator = "Is"
    else:
        comparator = "Eq"

    return makeComparisonExpression(
        left=left,
        right=right,
        comparator=comparator,
        source_ref=source_ref,
    )


def _buildCaseBodyCode(provider, case, source_ref):
    guard_condition = buildNode(
        provider=provider,
        node=case.guard,
        source_ref=source_ref,
        allow_none=True,
    )

    body_code = buildStatementsNode(provider, case.body, source_ref)

    return body_code, guard_condition


def _buildMatchAs(provider, variable_name, source_value, source_ref):
    assert "." not in variable_name, variable_name
    assert "!" not in variable_name, variable_name

    return StatementAssignmentVariableName(
        provider=provider,
        variable_name=variable_name,
        source=source_value,
        source_ref=source_ref,
    )


def _buildMatchValue(provider, against, pattern, source_ref):
    if type(pattern) is ast.MatchValue:
        right = buildNode(provider, pattern.value, source_ref)
    else:
        right = makeConstantRefNode(constant=pattern.value, source_ref=source_ref)

    return _makeMatchComparison(
        left=against,
        right=right,
        source_ref=source_ref,
    )


def _buildMatchSequence(provider, pattern, against, source_ref):
    # Many cases due to recursion, pylint: disable=too-many-locals

    conditions = [
        ExpressionMatchTypeCheckSequence(
            value=against.makeClone(),
            source_ref=source_ref,
        )
    ]

    assignments = []

    min_length = len(
        tuple(
            seq_pattern
            for seq_pattern in pattern.patterns
            if seq_pattern.__class__ is not ast.MatchStar
        )
    )

    if min_length:
        exact = all(
            seq_pattern.__class__ is not ast.MatchStar
            for seq_pattern in pattern.patterns
        )

        # TODO: Could special case "1" with truth check.
        conditions.append(
            makeComparisonExpression(
                left=ExpressionBuiltinLen(
                    value=against.makeClone(),
                    source_ref=source_ref,
                ),
                right=makeConstantRefNode(constant=min_length, source_ref=source_ref),
                comparator="Eq" if exact else "GtE",
                source_ref=source_ref,
            )
        )

    star_pos = None

    count = seq_pattern = None

    for count, seq_pattern in enumerate(pattern.patterns):
        # offset from the start.
        if star_pos is None:
            offset = count
        else:
            # offset from the end.
            offset = -(len(pattern.patterns) - count)

        if seq_pattern.__class__ is ast.MatchStar:
            variable_name = seq_pattern.name

            if variable_name is not None:
                assert "." not in variable_name, variable_name
                assert "!" not in variable_name, variable_name

                star_pos = count

                # Last one
                if star_pos == len(pattern.patterns):
                    slice_value = slice(count)
                else:
                    slice_value = slice(count, -(len(pattern.patterns) - (count + 1)))

                assignments.append(
                    StatementAssignmentVariableName(
                        provider=provider,
                        variable_name=variable_name,
                        source=ExpressionSubscriptLookup(
                            expression=against.makeClone(),
                            subscript=makeConstantRefNode(
                                constant=slice_value, source_ref=source_ref
                            ),
                            source_ref=source_ref,
                        ),
                        source_ref=source_ref,
                    )
                )
        else:
            item_conditions, item_assignments = _buildMatch(
                provider=provider,
                pattern=seq_pattern,
                against=ExpressionSubscriptLookup(
                    expression=against.makeClone(),
                    subscript=makeConstantRefNode(
                        constant=offset, source_ref=source_ref
                    ),
                    source_ref=source_ref,
                ),
                source_ref=source_ref,
            )

            if item_conditions:
                conditions.extend(item_conditions)

            if item_assignments:
                assignments.extend(item_assignments)

    return conditions, assignments


def _buildMatchMapping(provider, pattern, against, source_ref):
    conditions = [
        ExpressionMatchTypeCheckMapping(
            value=against.makeClone(),
            source_ref=source_ref,
        )
    ]

    assignments = []

    assert len(pattern.keys) == len(pattern.patterns), ast.dump(pattern)

    key = kwd_pattern = None

    for key, kwd_pattern in zip(pattern.keys, pattern.patterns):
        conditions.append(
            ExpressionSubscriptCheck(
                expression=against.makeClone(),
                subscript=makeConstantRefNode(
                    constant=key.value, source_ref=source_ref
                ),
                source_ref=source_ref,
            )
        )

        item_against = ExpressionSubscriptLookup(
            expression=against.makeClone(),
            subscript=makeConstantRefNode(constant=key.value, source_ref=source_ref),
            source_ref=source_ref,
        )

        item_conditions, item_assignments = _buildMatch(
            provider=provider,
            against=item_against,
            pattern=kwd_pattern,
            source_ref=source_ref,
        )

        if item_conditions:
            conditions.extend(item_conditions)

        if item_assignments:
            assignments.extend(item_assignments)

    return conditions, assignments


def _buildMatchClass(provider, pattern, against, source_ref):
    # TODO: What is that when set.
    assert not pattern.patterns

    cls_node = buildNode(provider, pattern.cls, source_ref)

    assert len(pattern.kwd_attrs) == len(pattern.kwd_patterns), ast.dump(pattern)

    conditions = [
        ExpressionBuiltinIsinstance(
            instance=against.makeClone(),
            classes=cls_node,
            source_ref=source_ref,
        )
    ]

    assignments = []

    assert len(pattern.kwd_attrs) == len(pattern.kwd_patterns), ast.dump(pattern)

    for key, kwd_pattern in zip(pattern.kwd_attrs, pattern.kwd_patterns):
        conditions.append(
            ExpressionAttributeCheck(
                expression=against.makeClone(),
                attribute_name=key,
                source_ref=source_ref,
            )
        )

        item_conditions, item_assignments = _buildMatch(
            provider=provider,
            against=makeExpressionAttributeLookup(
                expression=against.makeClone(),
                attribute_name=key,
                source_ref=source_ref,
            ),
            pattern=kwd_pattern,
            source_ref=source_ref,
        )

        if item_conditions:
            conditions.extend(item_conditions)

        if item_assignments:
            assignments.extend(item_assignments)

    return conditions, assignments


def _buildMatch(provider, pattern, against, source_ref):
    if pattern.__class__ is ast.MatchOr:
        or_condition_list = []
        for or_pattern in pattern.patterns:
            or_conditions, or_assignments = _buildMatch(
                provider=provider,
                pattern=or_pattern,
                against=against,
                source_ref=source_ref,
            )
            assert not or_assignments

            or_condition_list.append(
                makeAndNode(values=or_conditions, source_ref=source_ref)
            )

        condition = makeOrNode(values=or_condition_list, source_ref=source_ref)
        conditions = (condition,)
        assignments = None

    elif pattern.__class__ is ast.MatchClass:
        conditions, assignments = _buildMatchClass(
            provider=provider, pattern=pattern, against=against, source_ref=source_ref
        )
    elif pattern.__class__ is ast.MatchMapping:
        conditions, assignments = _buildMatchMapping(
            provider=provider,
            pattern=pattern,
            against=against,
            source_ref=source_ref,
        )

    elif pattern.__class__ is ast.MatchSequence:
        conditions, assignments = _buildMatchSequence(
            provider=provider,
            pattern=pattern,
            against=against,
            source_ref=source_ref,
        )

    elif pattern.__class__ is ast.MatchAs:
        conditions = None

        # default match only current with or without a name assigned. TODO: This ought to only
        # happen once, Python raises it, we do not yet: SyntaxError: name capture 'var' makes
        # remaining patterns unreachable
        if pattern.name is None:
            # case _:
            # Assigns to nothing and should be last one in a match statement, anything
            # after that will be syntax error.
            assignments = None
        else:
            # case var:
            # Assigns to var and should be last one in a match statement, anything
            # after that will be syntax error.
            assignment = _buildMatchAs(
                provider=provider,
                variable_name=pattern.name,
                source_value=against,
                source_ref=source_ref,
            )
            assignments = (assignment,)

    elif pattern.__class__ is ast.MatchValue or pattern.__class__ is ast.MatchSingleton:
        conditions = [
            _buildMatchValue(
                provider=provider,
                against=against,
                pattern=pattern,
                source_ref=source_ref,
            )
        ]

        assignments = None

    else:
        assert False, ast.dump(pattern)

    return conditions, assignments


def _buildCase(provider, case, tmp_subject, source_ref):
    assert case.__class__ is ast.match_case, case

    pattern = case.pattern

    against = ExpressionTempVariableRef(variable=tmp_subject, source_ref=source_ref)

    conditions, assignments = _buildMatch(
        provider=provider,
        pattern=pattern,
        against=against,
        source_ref=source_ref,
    )

    branch_code, guard = _buildCaseBodyCode(provider, case, source_ref)
    return (conditions, assignments, guard, branch_code)


def buildMatchNode(provider, node, source_ref):
    """Python3.10 or higher, match statements."""

    subject_node = buildNode(provider, node.subject, source_ref)

    temp_scope = provider.allocateTempScope("match_statement")

    # The value matched against, must be released in the end.
    tmp_subject = provider.allocateTempVariable(temp_scope, "subject")

    # Indicator variable, will end up with C bool type, and need not be released.
    tmp_indicator_variable = provider.allocateTempVariable(
        temp_scope=temp_scope, name="indicator", temp_type="bool"
    )

    cases = []

    for case in node.cases:
        cases.append(
            _buildCase(
                provider=provider,
                case=case,
                tmp_subject=tmp_subject,
                source_ref=source_ref,
            )
        )

    case_statements = []

    for case in cases:
        conditions, assignments, guard, branch_code = case

        # Set indicator variable at end of branch code, unless it's last branch
        # where there would be no usage of it.
        if case is not cases[-1]:
            branch_code = makeStatementsSequence(
                statements=(
                    branch_code,
                    StatementAssignmentVariable(
                        variable=tmp_indicator_variable,
                        source=makeConstantRefNode(
                            constant=True, source_ref=source_ref
                        ),
                        source_ref=source_ref,
                    ),
                ),
                allow_none=True,
                source_ref=source_ref,
            )

        if guard is not None:
            branch_code = makeStatementConditional(
                condition=guard,
                yes_branch=branch_code,
                no_branch=None,
                source_ref=source_ref,
            )

        del guard

        branch_code = makeStatementsSequence(
            statements=(assignments, branch_code),
            allow_none=True,
            source_ref=source_ref,
        )

        del assignments

        if conditions is not None:
            branch_code = makeStatementConditional(
                condition=makeAndNode(values=conditions, source_ref=source_ref),
                yes_branch=branch_code,
                no_branch=None,
                source_ref=source_ref,
            )

        del conditions

        if case is not cases[0]:
            statement = makeStatementConditional(
                condition=makeComparisonExpression(
                    comparator="Is",
                    left=ExpressionTempVariableRef(
                        variable=tmp_indicator_variable, source_ref=source_ref
                    ),
                    right=makeConstantRefNode(constant=False, source_ref=source_ref),
                    source_ref=source_ref,
                ),
                yes_branch=branch_code,
                no_branch=None,
                source_ref=source_ref,
            )
        else:
            statement = branch_code

        case_statements.append(statement)

    return makeStatementsSequence(
        statements=(
            StatementAssignmentVariable(
                variable=tmp_subject,
                source=subject_node,
                source_ref=subject_node.getSourceReference(),
            ),
            makeTryFinallyStatement(
                provider=provider,
                tried=case_statements,
                final=StatementReleaseVariable(
                    variable=tmp_indicator_variable, source_ref=source_ref
                ),
                source_ref=source_ref,
            ),
        ),
        allow_none=False,
        source_ref=source_ref,
    )
