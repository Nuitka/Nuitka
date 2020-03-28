#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
#                     Batakrishna, mailto:bablusahoo16@gmail.com
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
""" Reformulation of "min" and "max" statements

"""

# TODO: NOT statements
# TODO: Move to nuitka.optimization.OptimizeMinMaxCalls


from nuitka.nodes.AssignNodes import (
    StatementAssignmentVariable,
    StatementReleaseVariable,
)
from nuitka.nodes.ComparisonNodes import ExpressionComparisonGt, ExpressionComparisonLt
from nuitka.nodes.ConditionalNodes import makeStatementConditional
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.VariableRefNodes import ExpressionTempVariableRef

# createMinMaxCallReformulation.


def computeMinMax(outline_body, call_args, builtin_name, source_ref):
    assert len(call_args) >= 2

    if builtin_name == "max":
        condtionExpression = ExpressionComparisonLt
    else:
        condtionExpression = ExpressionComparisonGt

    arg_variables = [
        outline_body.allocateTempVariable(
            temp_scope=None, name="%s_arg_%d" % (builtin_name, i)
        )
        for i in range(len(call_args))
    ]

    # To be executed at beginning of outline body. These need
    # to be released, or else we loose reference
    statements = [
        StatementAssignmentVariable(
            variable=arg_variable, source=call_arg, source_ref=source_ref
        )
        for call_arg, arg_variable in zip(call_args, arg_variables)
    ]

    result_variable = outline_body.allocateTempVariable(
        temp_scope=None, name="%s_result" % builtin_name
    )

    statements.append(
        StatementAssignmentVariable(
            variable=result_variable,
            source=ExpressionTempVariableRef(
                variable=arg_variables[0], source_ref=source_ref
            ),
            source_ref=source_ref,
        )
    )

    for arg_variable in arg_variables[1:]:
        statements.append(
            makeStatementConditional(
                condition=condtionExpression(
                    left=ExpressionTempVariableRef(
                        variable=result_variable, source_ref=source_ref
                    ),
                    right=ExpressionTempVariableRef(
                        variable=arg_variable, source_ref=source_ref
                    ),
                    source_ref=source_ref,
                ),
                yes_branch=StatementAssignmentVariable(
                    variable=result_variable,
                    source=ExpressionTempVariableRef(
                        variable=arg_variable, source_ref=source_ref
                    ),
                    source_ref=source_ref,
                ),
                no_branch=None,
                source_ref=source_ref,
            )
        )

    statements.append(
        StatementReturn(
            expression=ExpressionTempVariableRef(
                variable=result_variable, source_ref=source_ref
            ),
            source_ref=source_ref,
        )
    )

    final_statements = [
        StatementReleaseVariable(variable=arg_variable, source_ref=source_ref)
        for arg_variable in arg_variables
    ]
    final_statements.append(
        StatementReleaseVariable(variable=result_variable, source_ref=source_ref)
    )

    return statements, final_statements
