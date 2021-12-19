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

from .ReformulationBooleanExpressions import makeAndNode
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


def buildMatchNode(provider, node, source_ref):
    """Python3.10 or higher, match statements."""

    # Many details to work with, pylint: disable=too-many-branches,too-many-locals,too-many-statements

    temp_scope = provider.allocateTempScope("match_statement")

    subject_node = buildNode(provider, node.subject, source_ref)

    tmp_subject = provider.allocateTempVariable(temp_scope, "subject")
    tmp_case_cls = provider.allocateTempVariable(temp_scope, "cls")

    # Indicator variable, will end up with C bool type, and need not be released.
    tmp_indicator_variable = provider.allocateTempVariable(
        temp_scope=temp_scope, name="indicator", temp_type="bool"
    )

    cases = []

    for case in node.cases:
        assert case.__class__ is ast.match_case, case

        pattern = case.pattern

        if pattern.__class__ is ast.MatchClass:
            # TODO: What is that
            assert not pattern.patterns

            cls_node = buildNode(provider, pattern.cls, source_ref)

            prepare = StatementAssignmentVariable(
                variable=tmp_case_cls,
                source=cls_node,
                source_ref=cls_node.getSourceReference(),
            )

            assert len(pattern.kwd_attrs) == len(pattern.kwd_patterns), ast.dump(
                pattern
            )

            conditions = [
                ExpressionBuiltinIsinstance(
                    instance=ExpressionTempVariableRef(
                        variable=tmp_subject, source_ref=source_ref
                    ),
                    classes=ExpressionTempVariableRef(
                        variable=tmp_case_cls, source_ref=source_ref
                    ),
                    source_ref=source_ref,
                )
            ]

            assignments = []

            kwd_attr = kwd_pattern = None

            for kwd_attr, kwd_pattern in zip(pattern.kwd_attrs, pattern.kwd_patterns):
                assert type(kwd_attr) is str

                # TODO: Maybe move this to first things, CPython checks first all.
                conditions.append(
                    ExpressionAttributeCheck(
                        expression=ExpressionTempVariableRef(
                            variable=tmp_subject, source_ref=source_ref
                        ),
                        attribute_name=kwd_attr,
                        source_ref=source_ref,
                    )
                )

                if kwd_pattern.__class__ is ast.MatchValue:
                    conditions.append(
                        _makeMatchComparison(
                            left=makeExpressionAttributeLookup(
                                expression=ExpressionTempVariableRef(
                                    variable=tmp_subject, source_ref=source_ref
                                ),
                                attribute_name=kwd_attr,
                                source_ref=source_ref,
                            ),
                            right=buildNode(provider, kwd_pattern.value, source_ref),
                            source_ref=source_ref,
                        )
                    )
                elif kwd_pattern.__class__ is ast.MatchSingleton:
                    conditions.append(
                        _makeMatchComparison(
                            left=makeExpressionAttributeLookup(
                                expression=ExpressionTempVariableRef(
                                    variable=tmp_subject, source_ref=source_ref
                                ),
                                attribute_name=kwd_attr,
                                source_ref=source_ref,
                            ),
                            right=makeConstantRefNode(
                                constant=kwd_pattern.value, source_ref=source_ref
                            ),
                            source_ref=source_ref,
                        )
                    )
                elif kwd_pattern.__class__ is ast.MatchAs:
                    variable_name = kwd_pattern.name

                    assert "." not in variable_name, variable_name
                    assert "!" not in variable_name, variable_name

                    assignments.append(
                        StatementAssignmentVariableName(
                            provider=provider,
                            variable_name=variable_name,
                            source=makeExpressionAttributeLookup(
                                expression=ExpressionTempVariableRef(
                                    variable=tmp_subject, source_ref=source_ref
                                ),
                                attribute_name=kwd_attr,
                                source_ref=source_ref,
                            ),
                            source_ref=source_ref,
                        )
                    )
                else:
                    assert False, ast.dump(kwd_pattern)

            del kwd_attr, kwd_pattern

            branch_code, guard = _buildCaseBodyCode(provider, case, source_ref)
            cases.append((prepare, conditions, assignments, guard, branch_code))

        elif pattern.__class__ is ast.MatchMapping:
            prepare = None

            conditions = [
                ExpressionMatchTypeCheckMapping(
                    value=ExpressionTempVariableRef(
                        variable=tmp_subject, source_ref=source_ref
                    ),
                    source_ref=source_ref,
                )
            ]

            assignments = []

            assert len(pattern.keys) == len(pattern.patterns), ast.dump(pattern)

            key = kwd_pattern = None

            for key, kwd_pattern in zip(pattern.keys, pattern.patterns):
                conditions.append(
                    ExpressionSubscriptCheck(
                        expression=ExpressionTempVariableRef(
                            variable=tmp_subject, source_ref=source_ref
                        ),
                        subscript=makeConstantRefNode(
                            constant=key.value, source_ref=source_ref
                        ),
                        source_ref=source_ref,
                    )
                )

                if kwd_pattern.__class__ is ast.MatchValue:
                    conditions.append(
                        _makeMatchComparison(
                            left=ExpressionSubscriptLookup(
                                expression=ExpressionTempVariableRef(
                                    variable=tmp_subject, source_ref=source_ref
                                ),
                                subscript=makeConstantRefNode(
                                    constant=key.value, source_ref=source_ref
                                ),
                                source_ref=source_ref,
                            ),
                            right=buildNode(provider, kwd_pattern.value, source_ref),
                            source_ref=source_ref,
                        )
                    )
                elif kwd_pattern.__class__ is ast.MatchSingleton:
                    conditions.append(
                        _makeMatchComparison(
                            left=ExpressionSubscriptLookup(
                                expression=ExpressionTempVariableRef(
                                    variable=tmp_subject, source_ref=source_ref
                                ),
                                subscript=makeConstantRefNode(
                                    constant=key.value, source_ref=source_ref
                                ),
                                source_ref=source_ref,
                            ),
                            right=makeConstantRefNode(
                                constant=kwd_pattern.value, source_ref=source_ref
                            ),
                            source_ref=source_ref,
                        )
                    )
                elif kwd_pattern.__class__ is ast.MatchAs:
                    variable_name = kwd_pattern.name

                    assert "." not in variable_name, variable_name
                    assert "!" not in variable_name, variable_name

                    assignments.append(
                        StatementAssignmentVariableName(
                            provider=provider,
                            variable_name=variable_name,
                            source=ExpressionSubscriptLookup(
                                expression=ExpressionTempVariableRef(
                                    variable=tmp_subject, source_ref=source_ref
                                ),
                                subscript=makeConstantRefNode(
                                    constant=key.value, source_ref=source_ref
                                ),
                                source_ref=source_ref,
                            ),
                            source_ref=source_ref,
                        )
                    )
                else:
                    assert False, ast.dump(kwd_pattern)

            del key, pattern

            branch_code, guard = _buildCaseBodyCode(provider, case, source_ref)
            cases.append((prepare, conditions, assignments, guard, branch_code))

        elif pattern.__class__ is ast.MatchSequence:
            prepare = None

            conditions = [
                ExpressionMatchTypeCheckSequence(
                    value=ExpressionTempVariableRef(
                        variable=tmp_subject, source_ref=source_ref
                    ),
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
                            value=ExpressionTempVariableRef(
                                variable=tmp_subject, source_ref=source_ref
                            ),
                            source_ref=source_ref,
                        ),
                        right=makeConstantRefNode(
                            constant=min_length, source_ref=source_ref
                        ),
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

                if seq_pattern.__class__ is ast.MatchValue:
                    conditions.append(
                        _makeMatchComparison(
                            left=ExpressionSubscriptLookup(
                                expression=ExpressionTempVariableRef(
                                    variable=tmp_subject, source_ref=source_ref
                                ),
                                subscript=makeConstantRefNode(
                                    constant=offset, source_ref=source_ref
                                ),
                                source_ref=source_ref,
                            ),
                            right=buildNode(provider, seq_pattern.value, source_ref),
                            source_ref=source_ref,
                        )
                    )
                elif seq_pattern.__class__ is ast.MatchSingleton:
                    conditions.append(
                        _makeMatchComparison(
                            left=ExpressionSubscriptLookup(
                                expression=ExpressionTempVariableRef(
                                    variable=tmp_subject, source_ref=source_ref
                                ),
                                subscript=makeConstantRefNode(
                                    constant=offset, source_ref=source_ref
                                ),
                                source_ref=source_ref,
                            ),
                            right=makeConstantRefNode(
                                constant=seq_pattern.value, source_ref=source_ref
                            ),
                            source_ref=source_ref,
                        )
                    )
                elif seq_pattern.__class__ is ast.MatchAs:
                    variable_name = seq_pattern.name

                    assert "." not in variable_name, variable_name
                    assert "!" not in variable_name, variable_name

                    assignments.append(
                        StatementAssignmentVariableName(
                            provider=provider,
                            variable_name=variable_name,
                            source=ExpressionSubscriptLookup(
                                expression=ExpressionTempVariableRef(
                                    variable=tmp_subject, source_ref=source_ref
                                ),
                                subscript=makeConstantRefNode(
                                    constant=offset, source_ref=source_ref
                                ),
                                source_ref=source_ref,
                            ),
                            source_ref=source_ref,
                        )
                    )
                elif seq_pattern.__class__ is ast.MatchStar:
                    variable_name = seq_pattern.name

                    if variable_name is not None:
                        assert "." not in variable_name, variable_name
                        assert "!" not in variable_name, variable_name

                        star_pos = count

                        # Last one
                        if star_pos == len(pattern.patterns):
                            slice_value = slice(count)
                        else:
                            slice_value = slice(
                                count, -(len(pattern.patterns) - (count + 1))
                            )

                        assignments.append(
                            StatementAssignmentVariableName(
                                provider=provider,
                                variable_name=variable_name,
                                source=ExpressionSubscriptLookup(
                                    expression=ExpressionTempVariableRef(
                                        variable=tmp_subject, source_ref=source_ref
                                    ),
                                    subscript=makeConstantRefNode(
                                        constant=slice_value, source_ref=source_ref
                                    ),
                                    source_ref=source_ref,
                                ),
                                source_ref=source_ref,
                            )
                        )
                else:
                    assert False, ast.dump(seq_pattern)

            del count, seq_pattern

            branch_code, guard = _buildCaseBodyCode(provider, case, source_ref)
            cases.append((prepare, conditions, assignments, guard, branch_code))

        elif pattern.__class__ is ast.MatchAs:
            # default match only current with or without a name assigned. TODO: This ought to only
            # happen once, Python raises it, we do not yet: SyntaxError: name capture 'var' makes
            # remaining patterns unreachable
            if pattern.name is None:
                # case _:
                # Assigns to nothing and should be last one in a match statement, anything
                # after that will be syntax error.
                branch_code, guard = _buildCaseBodyCode(provider, case, source_ref)
                cases.append(
                    (
                        None,
                        None,
                        None,
                        guard,
                        branch_code,
                    )
                )
            else:
                # case var:
                # Assigns to var and should be last one in a match statement, anything
                # after that will be syntax error.
                variable_name = pattern.name

                assert "." not in variable_name, variable_name
                assert "!" not in variable_name, variable_name

                assignment = StatementAssignmentVariableName(
                    provider=provider,
                    variable_name=variable_name,
                    source=ExpressionTempVariableRef(
                        variable=tmp_subject, source_ref=source_ref
                    ),
                    source_ref=source_ref,
                )

                branch_code, guard = _buildCaseBodyCode(provider, case, source_ref)
                cases.append(
                    (
                        None,
                        None,
                        (assignment,),
                        guard,
                        branch_code,
                    )
                )
        elif pattern.__class__ is ast.MatchValue:
            conditions = [
                _makeMatchComparison(
                    left=ExpressionTempVariableRef(
                        variable=tmp_subject, source_ref=source_ref
                    ),
                    right=makeConstantRefNode(
                        constant=pattern.value.value, source_ref=source_ref
                    ),
                    source_ref=source_ref,
                )
            ]

            branch_code, guard = _buildCaseBodyCode(provider, case, source_ref)
            cases.append((None, conditions, None, guard, branch_code))

        else:
            assert False, ast.dump(case)

    case_statements = []

    for case in cases:
        prepare, conditions, assignments, guard, branch_code = case

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

        if conditions is not None:
            branch_code = makeStatementConditional(
                condition=makeAndNode(values=conditions, source_ref=source_ref),
                yes_branch=branch_code,
                no_branch=None,
                source_ref=source_ref,
            )

        del conditions

        statement = makeStatementsSequence(
            statements=(prepare, assignments, branch_code),
            allow_none=True,
            source_ref=source_ref,
        )

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
                yes_branch=statement,
                no_branch=None,
                source_ref=source_ref,
            )

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
