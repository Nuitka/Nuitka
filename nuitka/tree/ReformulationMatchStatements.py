#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Reformulation of Python3.10 match statements.

Consult the Developer Manual for information. TODO: Add ability to sync
source code comments with Developer Manual sections.

"""

import ast

from nuitka.nodes.AttributeNodes import ExpressionAttributeCheck
from nuitka.nodes.BuiltinDictNodes import ExpressionBuiltinDict
from nuitka.nodes.BuiltinLenNodes import ExpressionBuiltinLen
from nuitka.nodes.BuiltinTypeNodes import ExpressionBuiltinList
from nuitka.nodes.ComparisonNodes import (
    ExpressionComparisonIs,
    makeComparisonExpression,
)
from nuitka.nodes.ConditionalNodes import makeStatementConditional
from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.DictionaryNodes import StatementDictOperationRemove
from nuitka.nodes.MatchNodes import ExpressionMatchArgs
from nuitka.nodes.OperatorNodes import ExpressionOperationBinarySub
from nuitka.nodes.OutlineNodes import ExpressionOutlineBody
from nuitka.nodes.ReturnNodes import makeStatementReturnConstant
from nuitka.nodes.SubscriptNodes import (
    ExpressionMatchSubscriptCheck,
    ExpressionSubscriptLookup,
)
from nuitka.nodes.TypeMatchNodes import (
    ExpressionMatchTypeCheckMapping,
    ExpressionMatchTypeCheckSequence,
)
from nuitka.nodes.TypeNodes import ExpressionBuiltinIsinstance
from nuitka.nodes.VariableAssignNodes import makeStatementAssignmentVariable
from nuitka.nodes.VariableNameNodes import (
    ExpressionVariableNameRef,
    StatementAssignmentVariableName,
)
from nuitka.nodes.VariableRefNodes import ExpressionTempVariableRef
from nuitka.nodes.VariableReleaseNodes import makeStatementReleaseVariable

from .ReformulationBooleanExpressions import makeAndNode, makeOrNode
from .ReformulationTryFinallyStatements import makeTryFinallyReleaseStatement
from .TreeHelpers import (
    buildNode,
    buildStatementsNode,
    makeStatementsSequence,
    makeStatementsSequenceFromStatement,
)


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


def _buildMatchAs(provider, pattern, make_against, source_ref):
    variable_name = pattern.name

    if variable_name is None:
        # case _:

        # Assigns to nothing and should be last one in a match
        # statement, anything after that will be syntax error. TODO: This
        # ought to only happen once, Python raises it, we do not yet:
        # SyntaxError: name capture 'var' makes remaining patterns
        # unreachable
        assignments = None
        conditions = None
    else:
        assert "." not in variable_name, variable_name
        assert "!" not in variable_name, variable_name

        if pattern.pattern is not None:
            conditions, assignments = _buildMatch(
                provider=provider,
                pattern=pattern.pattern,
                make_against=make_against,
                source_ref=source_ref,
            )

            if assignments is None:
                assignments = []
        else:
            assignments = []
            conditions = None

        assignments.append(
            StatementAssignmentVariableName(
                provider=provider,
                variable_name=variable_name,
                source=make_against(),
                source_ref=source_ref,
            )
        )

    return conditions, assignments


def _buildMatchValue(provider, make_against, pattern, source_ref):
    if type(pattern) is ast.MatchValue:
        right = buildNode(provider, pattern.value, source_ref)
    else:
        right = makeConstantRefNode(constant=pattern.value, source_ref=source_ref)

    return _makeMatchComparison(
        left=make_against(),
        right=right,
        source_ref=source_ref,
    )


def _buildMatchSequence(provider, pattern, make_against, source_ref):
    # Many cases due to recursion, pylint: disable=too-many-locals

    conditions = [
        ExpressionMatchTypeCheckSequence(
            value=make_against(),
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

    exact = all(
        seq_pattern.__class__ is not ast.MatchStar for seq_pattern in pattern.patterns
    )

    # Could special case ">=1" or "==0" with truth checks potentially, but that
    # is for generic optimization to recognize, we don't know much about the
    # matched value at this point yet.
    if min_length > 0 or exact:
        conditions.append(
            makeComparisonExpression(
                left=ExpressionBuiltinLen(
                    value=make_against(),
                    source_ref=source_ref,
                ),
                right=makeConstantRefNode(constant=min_length, source_ref=source_ref),
                comparator="Eq" if exact else "GtE",
                source_ref=source_ref,
            )
        )

    star_pos = None

    def makeOffsetNode(count):
        if star_pos is None:
            return makeConstantRefNode(constant=count, source_ref=source_ref)
        else:
            return ExpressionOperationBinarySub(
                ExpressionBuiltinLen(
                    value=make_against(),
                    source_ref=source_ref,
                ),
                makeConstantRefNode(
                    constant=len(pattern.patterns) - count,
                    source_ref=source_ref,
                ),
                source_ref=source_ref,
            )

    for count, seq_pattern in enumerate(pattern.patterns):
        if seq_pattern.__class__ is ast.MatchStar:
            star_pos = count

            variable_name = seq_pattern.name

            if variable_name is not None:
                assert "." not in variable_name, variable_name
                assert "!" not in variable_name, variable_name

                # Last one
                if star_pos == len(pattern.patterns) - 1:
                    slice_value = slice(star_pos, None)
                else:
                    slice_value = slice(count, -(len(pattern.patterns) - (count + 1)))

                assignments.append(
                    StatementAssignmentVariableName(
                        provider=provider,
                        variable_name=variable_name,
                        source=ExpressionBuiltinList(
                            ExpressionSubscriptLookup(
                                expression=make_against(),
                                subscript=makeConstantRefNode(
                                    constant=slice_value, source_ref=source_ref
                                ),
                                source_ref=source_ref,
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
                # It's called before return, pylint: disable=cell-var-from-loop
                make_against=lambda: ExpressionSubscriptLookup(
                    expression=make_against(),
                    subscript=makeOffsetNode(count),
                    source_ref=source_ref,
                ),
                source_ref=source_ref,
            )

            if item_conditions:
                conditions.extend(item_conditions)

            if item_assignments:
                assignments.extend(item_assignments)

    return conditions, assignments


def _buildMatchMapping(provider, pattern, make_against, source_ref):
    conditions = [
        ExpressionMatchTypeCheckMapping(
            value=make_against(),
            source_ref=source_ref,
        )
    ]

    assignments = []

    assert len(pattern.keys) == len(pattern.patterns), ast.dump(pattern)

    key = kwd_pattern = None

    for key, kwd_pattern in zip(pattern.keys, pattern.patterns):
        conditions.append(
            ExpressionMatchSubscriptCheck(
                expression=make_against(),
                subscript=buildNode(provider, key, source_ref),
                source_ref=source_ref,
            )
        )

        # It's called before return, pylint: disable=cell-var-from-loop
        item_conditions, item_assignments = _buildMatch(
            provider=provider,
            make_against=lambda: ExpressionSubscriptLookup(
                expression=make_against(),
                subscript=buildNode(provider, key, source_ref),
                source_ref=source_ref,
            ),
            pattern=kwd_pattern,
            source_ref=source_ref,
        )

        if item_conditions:
            conditions.extend(item_conditions)

        if item_assignments:
            assignments.extend(item_assignments)

    if pattern.rest:
        assert type(pattern.rest) is str, pattern.rest

        assignments.append(
            StatementAssignmentVariableName(
                provider=provider,
                variable_name=pattern.rest,
                source=ExpressionBuiltinDict(
                    pos_arg=make_against(),
                    pairs=(),
                    source_ref=source_ref,
                ),
                source_ref=source_ref,
            )
        )

        for key in pattern.keys:
            assert type(key) is ast.Constant, key

            assignments.append(
                StatementDictOperationRemove(
                    dict_arg=ExpressionVariableNameRef(
                        provider=provider,
                        variable_name=pattern.rest,
                        source_ref=source_ref,
                    ),
                    key=buildNode(provider, key, source_ref),
                    source_ref=source_ref,
                )
            )

    return conditions, assignments


def _buildMatchClass(provider, pattern, make_against, source_ref):
    # Slightly complicated, due to using an outline body and there is also
    # keyword and positional arguments to deal with, pylint: disable=too-many-locals

    cls_node = buildNode(provider, pattern.cls, source_ref)

    assert len(pattern.kwd_attrs) == len(pattern.kwd_patterns), (
        source_ref,
        ast.dump(pattern),
    )

    if len(pattern.kwd_attrs) + len(pattern.patterns) == 0:
        conditions = [
            ExpressionBuiltinIsinstance(
                instance=make_against(),
                classes=cls_node,
                source_ref=source_ref,
            )
        ]
        assignments = None

        return conditions, assignments

    class_conditions_list = []
    class_assignments_list = []

    outline_body = ExpressionOutlineBody(
        provider=provider, name="match_class", source_ref=source_ref
    )
    tmp_match_args = outline_body.allocateTempVariable(
        temp_scope=None, name="match_args", temp_type="PyObject *"
    )

    for count, pos_pattern in enumerate(pattern.patterns):
        # It's called before return, pylint: disable=cell-var-from-loop
        item_conditions, item_assignments = _buildMatch(
            provider=provider,
            make_against=lambda: ExpressionSubscriptLookup(
                expression=ExpressionTempVariableRef(
                    variable=tmp_match_args, source_ref=source_ref
                ),
                subscript=makeConstantRefNode(constant=count, source_ref=source_ref),
                source_ref=source_ref,
            ),
            pattern=pos_pattern,
            source_ref=source_ref,
        )

        class_conditions_list.append(item_conditions)
        class_assignments_list.append(item_assignments)

    for count, (key, kwd_pattern) in enumerate(
        zip(pattern.kwd_attrs, pattern.kwd_patterns)
    ):
        # It's called before return, pylint: disable=cell-var-from-loop
        item_conditions, item_assignments = _buildMatch(
            provider=provider,
            make_against=lambda: ExpressionSubscriptLookup(
                expression=ExpressionTempVariableRef(
                    variable=tmp_match_args, source_ref=source_ref
                ),
                subscript=makeConstantRefNode(
                    constant=count + len(pattern.patterns), source_ref=source_ref
                ),
                source_ref=source_ref,
            ),
            pattern=kwd_pattern,
            source_ref=source_ref,
        )

        item_conditions = list(item_conditions or ())

        item_conditions.insert(
            0,
            ExpressionAttributeCheck(
                expression=make_against(),
                attribute_name=key,
                source_ref=source_ref,
            ),
        )

        item_conditions = tuple(item_conditions)

        class_conditions_list.append(item_conditions)
        class_assignments_list.append(item_assignments)

    statements = []

    for count, (class_conditions, class_assignments) in enumerate(
        zip(class_conditions_list, class_assignments_list)
    ):
        class_assignments = class_assignments or ()

        if class_conditions:
            class_conditions = makeAndNode(
                values=class_conditions, source_ref=source_ref
            )
        else:
            class_conditions = makeConstantRefNode(constant=True, source_ref=source_ref)

        if count == len(class_assignments_list) - 1:
            class_assignments = list(class_assignments or ())
            class_assignments.append(
                makeStatementReturnConstant(constant=True, source_ref=source_ref)
            )

        statements.append(
            makeStatementConditional(
                condition=class_conditions,
                yes_branch=makeStatementsSequence(
                    statements=class_assignments,
                    allow_none=False,
                    source_ref=source_ref,
                ),
                no_branch=makeStatementReturnConstant(
                    constant=False, source_ref=source_ref
                ),
                source_ref=source_ref,
            )
        )

    assert statements

    statements = [
        makeStatementAssignmentVariable(
            variable=tmp_match_args,
            source=ExpressionMatchArgs(
                expression=make_against(),
                # TODO: Maybe use a temp variable instead for caching.
                match_type=cls_node.makeClone(),
                max_allowed=len(pattern.patterns),
                keywords=pattern.kwd_attrs,
                source_ref=source_ref,
            ),
            source_ref=source_ref,
        ),
        makeStatementConditional(
            condition=ExpressionComparisonIs(
                ExpressionTempVariableRef(
                    variable=tmp_match_args, source_ref=source_ref
                ),
                makeConstantRefNode(constant=None, source_ref=source_ref),
                source_ref=source_ref,
            ),
            yes_branch=makeStatementsSequence(
                statements=(
                    makeStatementReleaseVariable(
                        variable=tmp_match_args, source_ref=source_ref
                    ),
                    makeStatementReturnConstant(constant=False, source_ref=source_ref),
                ),
                allow_none=False,
                source_ref=source_ref,
            ),
            no_branch=None,
            source_ref=source_ref,
        ),
        makeTryFinallyReleaseStatement(
            provider=provider,
            tried=statements,
            variables=(tmp_match_args,),
            source_ref=source_ref,
        ),
    ]

    body = makeStatementsSequence(
        statements=statements, allow_none=False, source_ref=source_ref
    )

    outline_body.setChildBody(body)

    conditions = [
        ExpressionBuiltinIsinstance(
            instance=make_against(),
            classes=cls_node,
            source_ref=source_ref,
        ),
        outline_body,
    ]
    assignments = None

    return conditions, assignments


def _buildMatchOr(provider, pattern, make_against, source_ref):
    # Slightly complicated, due to using an outline body, pylint: disable=too-many-locals

    or_condition_list = []
    or_assignments_list = []

    for or_pattern in pattern.patterns:
        or_conditions, or_assignments = _buildMatch(
            provider=provider,
            pattern=or_pattern,
            make_against=make_against,
            source_ref=source_ref,
        )

        if or_conditions:
            or_condition_list.append(
                makeAndNode(values=or_conditions, source_ref=source_ref)
            )
        else:
            or_condition_list.append(
                makeConstantRefNode(constant=True, source_ref=source_ref)
            )

        # TODO: Inconsistency somewhere, can return empty.
        or_assignments_list.append(or_assignments or None)

    if all(or_assignments is None for or_assignments in or_assignments_list):
        condition = makeOrNode(values=or_condition_list, source_ref=source_ref)
        conditions = (condition,)
        assignments = None
    else:
        body = None

        for or_condition, or_assignments in zip(
            reversed(or_condition_list), reversed(or_assignments_list)
        ):
            assert or_assignments is not None, (source_ref, or_assignments_list)
            statements = list(or_assignments)
            statements.append(
                makeStatementReturnConstant(constant=True, source_ref=source_ref)
            )

            if body is None:
                body = makeStatementConditional(
                    condition=or_condition,
                    yes_branch=makeStatementsSequence(
                        statements=statements, allow_none=False, source_ref=source_ref
                    ),
                    no_branch=makeStatementReturnConstant(
                        constant=False, source_ref=source_ref
                    ),
                    source_ref=source_ref,
                )
            else:
                body = makeStatementConditional(
                    condition=or_condition,
                    yes_branch=makeStatementsSequence(
                        statements=statements, allow_none=False, source_ref=source_ref
                    ),
                    no_branch=body,
                    source_ref=source_ref,
                )

        body = makeStatementsSequenceFromStatement(body)

        outline_body = ExpressionOutlineBody(
            provider=provider, name="match_or", source_ref=source_ref
        )

        outline_body.setChildBody(body)

        conditions = (outline_body,)
        assignments = None

    return conditions, assignments


def _buildMatch(provider, pattern, make_against, source_ref):
    if pattern.__class__ is ast.MatchOr:
        conditions, assignments = _buildMatchOr(
            provider=provider,
            pattern=pattern,
            make_against=make_against,
            source_ref=source_ref,
        )
    elif pattern.__class__ is ast.MatchClass:
        conditions, assignments = _buildMatchClass(
            provider=provider,
            pattern=pattern,
            make_against=make_against,
            source_ref=source_ref,
        )
    elif pattern.__class__ is ast.MatchMapping:
        conditions, assignments = _buildMatchMapping(
            provider=provider,
            pattern=pattern,
            make_against=make_against,
            source_ref=source_ref,
        )
    elif pattern.__class__ is ast.MatchSequence:
        conditions, assignments = _buildMatchSequence(
            provider=provider,
            pattern=pattern,
            make_against=make_against,
            source_ref=source_ref,
        )
    elif pattern.__class__ is ast.MatchAs:
        conditions, assignments = _buildMatchAs(
            provider=provider,
            pattern=pattern,
            make_against=make_against,
            source_ref=source_ref,
        )
    elif pattern.__class__ is ast.MatchValue or pattern.__class__ is ast.MatchSingleton:
        conditions = [
            _buildMatchValue(
                provider=provider,
                make_against=make_against,
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

    make_against = lambda: ExpressionTempVariableRef(
        variable=tmp_subject, source_ref=source_ref
    )

    conditions, assignments = _buildMatch(
        provider=provider,
        pattern=pattern,
        make_against=make_against,
        source_ref=source_ref,
    )

    branch_code, guard = _buildCaseBodyCode(provider, case, source_ref)
    return (conditions, assignments, guard, branch_code)


def buildMatchNode(provider, node, source_ref):
    """Python3.10 or higher, match statements."""

    subject_node = buildNode(provider, node.subject, source_ref)

    temp_scope = provider.allocateTempScope("match_statement")

    # The value matched against, must be released in the end.
    tmp_subject = provider.allocateTempVariable(
        temp_scope, "subject", temp_type="object"
    )

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
                    makeStatementAssignmentVariable(
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
            makeStatementAssignmentVariable(
                variable=tmp_indicator_variable,
                source=makeConstantRefNode(constant=False, source_ref=source_ref),
                source_ref=source_ref,
            ),
            makeStatementAssignmentVariable(
                variable=tmp_subject,
                source=subject_node,
                source_ref=subject_node.getSourceReference(),
            ),
            makeTryFinallyReleaseStatement(
                provider=provider,
                tried=case_statements,
                variables=(tmp_indicator_variable,),
                source_ref=source_ref,
            ),
        ),
        allow_none=False,
        source_ref=source_ref,
    )


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
