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
""" Reformulation of loop statements.

Consult the developer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

from nuitka.nodes.AssignNodes import (
    StatementAssignmentVariable,
    StatementDelVariable
)
from nuitka.nodes.BuiltinIteratorNodes import (
    ExpressionBuiltinIter1,
    ExpressionBuiltinNext1
)
from nuitka.nodes.ComparisonNodes import ExpressionComparisonIs
from nuitka.nodes.ConditionalNodes import StatementConditional
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.LoopNodes import StatementBreakLoop, StatementLoop
from nuitka.nodes.StatementNodes import StatementsSequence
from nuitka.nodes.VariableRefNodes import (
    ExpressionTargetTempVariableRef,
    ExpressionTempVariableRef
)

from .Helpers import (
    buildNode,
    buildStatementsNode,
    makeStatementsSequence,
    makeStatementsSequenceFromStatement,
    makeTryFinallyStatement,
    popBuildContext,
    popIndicatorVariable,
    pushBuildContext,
    pushIndicatorVariable
)
from .ReformulationAssignmentStatements import buildAssignmentStatements
from .ReformulationTryExceptStatements import makeTryExceptSingleHandlerNode


def buildForLoopNode(provider, node, source_ref):
    # The for loop is re-formulated according to developer manual. An iterator
    # is created, and looped until it gives StopIteration. The else block is
    # taken if a for loop exits normally, i.e. because of iterator
    # exhaustion. We do this by introducing an indicator variable.

    source = buildNode(provider, node.iter, source_ref)

    temp_scope = provider.allocateTempScope("for_loop")

    tmp_iter_variable = provider.allocateTempVariable(
        temp_scope = temp_scope,
        name       = "for_iterator"
    )

    tmp_value_variable = provider.allocateTempVariable(
        temp_scope = temp_scope,
        name       = "iter_value"
    )

    else_block = buildStatementsNode(
        provider   = provider,
        nodes      = node.orelse if node.orelse else None,
        source_ref = source_ref
    )

    if else_block is not None:
        tmp_break_indicator = provider.allocateTempVariable(
            temp_scope = temp_scope,
            name       = "break_indicator"
        )

        statements = [
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetTempVariableRef(
                    variable   = tmp_break_indicator.makeReference(
                        provider
                    ),
                    source_ref = source_ref
                ),
                source       = ExpressionConstantRef(
                    constant   = True,
                    source_ref = source_ref
                ),
                source_ref   = source_ref
            )
        ]
    else:
        statements = []

    statements.append(
        StatementBreakLoop(
            source_ref = source_ref
        )
    )

    handler_body = makeStatementsSequence(
        statements = statements,
        allow_none = False,
        source_ref = source_ref
    )

    statements = (
        makeTryExceptSingleHandlerNode(
            tried         = makeStatementsSequenceFromStatement(
                statement = StatementAssignmentVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = tmp_value_variable.makeReference(
                            provider
                        ),
                        source_ref = source_ref
                    ),
                    source       = ExpressionBuiltinNext1(
                        value      = ExpressionTempVariableRef(
                            variable   = tmp_iter_variable.makeReference(
                                provider
                            ),
                            source_ref = source_ref
                        ),
                        source_ref = source_ref
                    ),
                    source_ref   = source_ref
                )
            ),
            exception_name = "StopIteration",
            handler_body   = handler_body,
            public_exc     = False,
            source_ref     = source_ref
        ),
        buildAssignmentStatements(
            provider   = provider,
            node       = node.target,
            source     = ExpressionTempVariableRef(
                variable   = tmp_value_variable.makeReference(
                    provider
                ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    pushBuildContext("loop_body")
    pushIndicatorVariable(None)
    statements += (
        buildStatementsNode(
            provider   = provider,
            nodes      = node.body,
            source_ref = source_ref
        ),
    )
    popIndicatorVariable()
    popBuildContext()

    loop_body = makeStatementsSequence(
        statements = statements,
        allow_none = True,
        source_ref = source_ref
    )

    cleanup_statements = [
        StatementDelVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_value_variable.makeReference(provider),
                source_ref = source_ref
            ),
            tolerant     = True,
            source_ref   = source_ref
        ),
        StatementDelVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_iter_variable.makeReference(provider),
                source_ref = source_ref
            ),
            tolerant     = True,
            source_ref   = source_ref
        )
    ]

    if else_block is not None:
        statements = [
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetTempVariableRef(
                    variable   = tmp_break_indicator.makeReference(
                        provider
                    ),
                    source_ref = source_ref
                ),
                source       = ExpressionConstantRef(
                    constant   = False,
                    source_ref = source_ref
                ),
                source_ref   = source_ref
            )
        ]
    else:
        statements = []

    statements += [
        # First create the iterator and store it.
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_iter_variable.makeReference(
                    provider
                ),
                source_ref = source_ref
            ),
            source       = ExpressionBuiltinIter1(
                value       = source,
                source_ref  = source.getSourceReference()
            ),
            source_ref   = source_ref
        ),
        makeTryFinallyStatement(
            tried = StatementLoop(
                body       = loop_body,
                source_ref = source_ref
            ),
            final = StatementsSequence(
                statements = cleanup_statements,
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    ]

    if else_block is not None:
        statements += [
            StatementConditional(
                condition  = ExpressionComparisonIs(
                    left       = ExpressionTempVariableRef(
                        variable   = tmp_break_indicator.makeReference(
                            provider
                        ),
                        source_ref = source_ref
                    ),
                    right      = ExpressionConstantRef(
                        constant   = True,
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
                yes_branch = else_block,
                no_branch  = None,
                source_ref = source_ref
            )
        ]

        statements = (
            makeTryFinallyStatement(
                tried = statements,
                final = StatementDelVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = tmp_break_indicator.makeReference(
                            provider
                        ),
                        source_ref = source_ref
                    ),
                    tolerant     = False,
                    source_ref   = source_ref
                ),
                source_ref = source_ref
            ),
        )

    return StatementsSequence(
        statements = statements,
        source_ref = source_ref
    )


def buildWhileLoopNode(provider, node, source_ref):
    # The while loop is re-formulated according to developer manual. The
    # condition becomes an early condition to break the loop. The else block is
    # taken if a while loop exits normally, i.e. because of condition not being
    # true. We do this by introducing an indicator variable.

    else_block = buildStatementsNode(
        provider   = provider,
        nodes      = node.orelse if node.orelse else None,
        source_ref = source_ref
    )

    if else_block is not None:
        temp_scope = provider.allocateTempScope( "while_loop" )

        tmp_break_indicator = provider.allocateTempVariable(
            temp_scope = temp_scope,
            name       = "break_indicator"
        )

        statements = (
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetTempVariableRef(
                    variable   = tmp_break_indicator.makeReference(
                        provider
                    ),
                    source_ref = source_ref
                ),
                source     = ExpressionConstantRef(
                    constant   = True,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            StatementBreakLoop(
                source_ref = source_ref
            )
        )
    else:
        statements = (
            StatementBreakLoop(
                source_ref = source_ref
            ),
        )

    pushBuildContext("loop_body")
    pushIndicatorVariable(None)
    loop_statements = buildStatementsNode(
        provider   = provider,
        nodes      = node.body,
        source_ref = source_ref
    )
    popIndicatorVariable()
    popBuildContext()

    # The loop body contains a conditional statement at the start that breaks
    # the loop if it fails.
    loop_body = makeStatementsSequence(
        statements = (
            StatementConditional(
                condition = buildNode(provider, node.test, source_ref),
                no_branch = StatementsSequence(
                    statements = statements,
                    source_ref = source_ref
                ),
                yes_branch = None,
                source_ref = source_ref
            ),
            loop_statements
        ),
        allow_none = True,
        source_ref = source_ref
    )

    loop_statement = StatementLoop(
        body       = loop_body,
        source_ref = source_ref
    )

    if else_block is None:
        return loop_statement
    else:
        statements = (
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetTempVariableRef(
                    variable   = tmp_break_indicator.makeReference(
                        provider
                    ),
                    source_ref = source_ref
                ),
                source = ExpressionConstantRef(
                    constant   = False,
                    source_ref = source_ref
                ),
                source_ref   = source_ref
            ),
            loop_statement,
            StatementConditional(
                condition  = ExpressionComparisonIs(
                    left       = ExpressionTempVariableRef(
                        variable   = tmp_break_indicator.makeReference(
                            provider
                        ),
                        source_ref = source_ref
                    ),
                    right      = ExpressionConstantRef(
                        constant   = True,
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
                yes_branch = else_block,
                no_branch  = None,
                source_ref = source_ref
            )
        )

        statements = (
            makeTryFinallyStatement(
                tried = statements,
                final = StatementDelVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = tmp_break_indicator.makeReference(
                            provider
                        ),
                        source_ref = source_ref
                    ),
                    tolerant     = False,
                    source_ref   = source_ref
                ),
                source_ref = source_ref
            ),
        )

        return StatementsSequence(
            statements = statements,
            source_ref = source_ref
        )
