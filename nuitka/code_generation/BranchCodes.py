#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Branch related codes.

"""

from .CodeHelpers import generateStatementSequenceCode
from .ConditionalCodes import generateConditionCode
from .Emission import withSubCollector
from .LabelCodes import getGotoCode, getLabelCode


def generateBranchCode(statement, emit, context):
    true_target = context.allocateLabel("branch_yes")
    false_target = context.allocateLabel("branch_no")
    end_target = context.allocateLabel("branch_end")

    old_true_target = context.getTrueBranchTarget()
    old_false_target = context.getFalseBranchTarget()

    context.setTrueBranchTarget(true_target)
    context.setFalseBranchTarget(false_target)

    # Have own declaration scope for condition, to limit visibility from branches
    # which can be huge.
    with withSubCollector(emit, context) as condition_emit:
        generateConditionCode(
            condition=statement.subnode_condition, emit=condition_emit, context=context
        )

    context.setTrueBranchTarget(old_true_target)
    context.setFalseBranchTarget(old_false_target)

    getLabelCode(true_target, emit)

    generateStatementSequenceCode(
        statement_sequence=statement.subnode_yes_branch, emit=emit, context=context
    )

    if statement.subnode_no_branch is not None:
        getGotoCode(end_target, emit)
        getLabelCode(false_target, emit)

        generateStatementSequenceCode(
            statement_sequence=statement.subnode_no_branch, emit=emit, context=context
        )

        getLabelCode(end_target, emit)
    else:
        getLabelCode(false_target, emit)


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
