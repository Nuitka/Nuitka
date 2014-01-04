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

from nuitka import Utils

from nuitka.nodes.StatementNodes import (
    StatementPreserveFrameException,
    StatementReraiseFrameException,
    StatementPublishException,
    StatementsSequence
)
from nuitka.nodes.ConditionalNodes import StatementConditional
from nuitka.nodes.AssignNodes import StatementAssignmentVariable
from nuitka.nodes.VariableRefNodes import (
    ExpressionTargetTempVariableRef,
    ExpressionTempVariableRef
)
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.ComparisonNodes import ExpressionComparisonIs

from nuitka.nodes.TryNodes import StatementTryFinally

from .Helpers import (
    makeStatementsSequenceFromStatement,
    makeStatementsSequenceOrStatement,
    pushIndicatorVariable,
    popIndicatorVariable,
    getIndicatorVariables,
    buildStatementsNode,
    mergeStatements,
    pushBuildContext,
    popBuildContext,
)

def buildTryFinallyNode(provider, build_tried, node, source_ref):

    if Utils.python_version < 300:
        # Prevent "continue" statements in the final blocks
        pushBuildContext("finally")
        final = buildStatementsNode(
            provider   = provider,
            nodes      = node.finalbody,
            source_ref = source_ref
        )
        popBuildContext()

        return StatementTryFinally(
            tried      = build_tried(),
            final      = final,
            public_exc = Utils.python_version >= 300, # TODO: Use below code
            source_ref = source_ref
        )
    else:
        temp_scope = provider.allocateTempScope("try_finally")

        tmp_indicator_variable = provider.allocateTempVariable(
            temp_scope = temp_scope,
            name       = "unhandled_indicator"
        )

        pushIndicatorVariable(tmp_indicator_variable)

        statements = (
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetTempVariableRef(
                    variable   = tmp_indicator_variable.makeReference(
                        provider
                    ),
                    source_ref = source_ref.atInternal()
                ),
                source       = ExpressionConstantRef(
                    constant   = False,
                    source_ref = source_ref
                ),
                source_ref   = source_ref.atInternal()
            ),
            build_tried(),
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetTempVariableRef(
                    variable   = tmp_indicator_variable.makeReference(
                        provider
                    ),
                    source_ref = source_ref.atInternal()
                ),
                source       = ExpressionConstantRef(
                    constant   = True,
                    source_ref = source_ref
                ),
                source_ref   = source_ref.atInternal()
            )
        )

        # Prevent "continue" statements in the final blocks
        pushBuildContext("finally")
        final = buildStatementsNode(
            provider   = provider,
            nodes      = node.finalbody,
            source_ref = source_ref
        )
        popBuildContext()

        popIndicatorVariable()

        tried = StatementsSequence(
            statements = mergeStatements(statements, allow_none = True),
            source_ref = source_ref
        )

        statements = (
            StatementConditional(
                condition = ExpressionComparisonIs(
                    left       = ExpressionTempVariableRef(
                        variable   = tmp_indicator_variable.makeReference(
                            provider
                        ),
                        source_ref = source_ref.atInternal()
                    ),
                    right      = ExpressionConstantRef(
                        constant = False,
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
                yes_branch = StatementsSequence(
                    statements = (
                        StatementPreserveFrameException(
                            source_ref = source_ref.atInternal()
                        ),
                        StatementPublishException(
                            source_ref = source_ref.atInternal()
                        )
                    ),
                    source_ref = source_ref.atInternal()
                ),
                no_branch  = None,
                source_ref = source_ref.atInternal()
            ),
        )

        prelude = StatementsSequence(
            statements = statements,
            source_ref = source_ref
        )

        statements = (
            StatementConditional(
                condition = ExpressionComparisonIs(
                    left       = ExpressionTempVariableRef(
                        variable   = tmp_indicator_variable.makeReference(
                            provider
                        ),
                        source_ref = source_ref.atInternal()
                    ),
                    right      = ExpressionConstantRef(
                        constant = False,
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
                yes_branch = StatementsSequence(
                    statements = (
                        StatementReraiseFrameException(
                            source_ref = source_ref.atInternal()
                        ),
                    ),
                    source_ref = source_ref.atInternal()
                ),
                no_branch  = None,
                source_ref = source_ref.atInternal()
            ),
        )

        postlude = StatementsSequence(
            statements = statements,
            source_ref = source_ref
        )

        final = StatementsSequence(
            statements = mergeStatements(
                (
                    prelude,
                    StatementTryFinally(
                        tried      = final,
                        final      = postlude,
                        public_exc = False,
                        source_ref = source_ref.atInternal()
                    ),
                )
            ),
            source_ref = source_ref.atInternal()
        )

        return StatementTryFinally(
            tried      = tried,
            final      = final,
            public_exc = True,
            source_ref = source_ref
        )


def makeTryFinallyIndicator(provider, statement, is_loop_exit):
    statements = []

    indicator_variables = getIndicatorVariables()

    source_ref = statement.getSourceReference()
    indicator_value = True

    for indicator_variable in reversed(indicator_variables):
        if indicator_variable is Ellipsis:
            break
        elif indicator_variable is not None:
            statements.append(
                StatementAssignmentVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = indicator_variable.makeReference(
                            provider
                        ),
                        source_ref = source_ref.atInternal()
                    ),
                    source       = ExpressionConstantRef(
                        constant   = indicator_value,
                        source_ref = source_ref
                    ),
                    source_ref   = source_ref.atInternal()
                )
            )
        elif is_loop_exit:
            indicator_value = False


    statements.append(
        statement
    )

    return makeStatementsSequenceOrStatement(
        statements = statements,
        source_ref = source_ref
    )
