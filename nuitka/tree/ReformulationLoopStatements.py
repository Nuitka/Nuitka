#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.nodes.VariableRefNodes import (
    CPythonExpressionTempVariableRef,
    CPythonStatementTempBlock
)
from nuitka.nodes.ConstantRefNodes import CPythonExpressionConstantRef
from nuitka.nodes.BuiltinRefNodes import CPythonExpressionBuiltinExceptionRef

from nuitka.nodes.BuiltinIteratorNodes import (
    CPythonExpressionBuiltinNext1,
    CPythonExpressionBuiltinIter1
)
from nuitka.nodes.ComparisonNodes import CPythonExpressionComparisonIs
from nuitka.nodes.StatementNodes import CPythonStatementsSequence
from nuitka.nodes.LoopNodes import (
    CPythonStatementBreakLoop,
    CPythonStatementLoop
)
from nuitka.nodes.ConditionalNodes import CPythonStatementConditional
from nuitka.nodes.AssignNodes import CPythonStatementAssignmentVariable
from nuitka.nodes.TryNodes import (
    CPythonStatementExceptHandler,
    CPythonStatementTryExcept
)

from .Helpers import (
    makeStatementsSequence,
    buildStatementsNode,
    buildNode
)

from .ReformulationAssignmentStatements import buildAssignmentStatements

def buildForLoopNode( provider, node, source_ref ):
    # The for loop is re-formulated according to developer manual. An iterator is created,
    # and looped until it gives StopIteration. The else block is taken if a for loop exits
    # normally, i.e. because of iterator exhaustion. We do this by introducing an
    # indicator variable.

    source = buildNode( provider, node.iter, source_ref )

    result = CPythonStatementTempBlock(
        source_ref = source_ref
    )

    tmp_iter_variable = result.getTempVariable( "for_iterator" )

    iterate_tmp_block = CPythonStatementTempBlock(
        source_ref = source_ref
    )

    tmp_value_variable = iterate_tmp_block.getTempVariable( "iter_value" )

    else_block = buildStatementsNode(
        provider   = provider,
        nodes      = node.orelse if node.orelse else None,
        source_ref = source_ref
    )

    if else_block is not None:
        tmp_break_indicator_variable = result.getTempVariable( "break_indicator" )

        statements = [
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTempVariableRef(
                    variable   = tmp_break_indicator_variable.makeReference( result ),
                    source_ref = source_ref
                ),
                source     = CPythonExpressionConstantRef(
                    constant   = True,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        ]
    else:
        statements = []

    statements.append(
        CPythonStatementBreakLoop(
            source_ref = source_ref.atInternal()
        )
    )

    handler_body = makeStatementsSequence(
        statements = statements,
        allow_none = True,
        source_ref = source_ref
    )

    statements = (
        CPythonStatementTryExcept(
            tried      = CPythonStatementsSequence(
                statements = (
                    CPythonStatementAssignmentVariable(
                        variable_ref = CPythonExpressionTempVariableRef(
                            variable   = tmp_value_variable.makeReference( iterate_tmp_block ),
                            source_ref = source_ref
                        ),
                        source     = CPythonExpressionBuiltinNext1(
                            value      = CPythonExpressionTempVariableRef(
                                variable   = tmp_iter_variable.makeReference( result ),
                                source_ref = source_ref
                            ),
                            source_ref = source_ref
                        ),
                        source_ref = source_ref
                    ),
                ),
                source_ref = source_ref
            ),
            handlers   = (
                CPythonStatementExceptHandler(
                    exception_types = (
                        CPythonExpressionBuiltinExceptionRef(
                            exception_name = "StopIteration",
                            source_ref     = source_ref
                        ),
                    ),
                    body           = handler_body,
                    source_ref     = source_ref
                ),
            ),
            source_ref = source_ref
        ),
        buildAssignmentStatements(
            provider   = provider,
            node       = node.target,
            source     = CPythonExpressionTempVariableRef(
                variable   = tmp_value_variable.makeReference( iterate_tmp_block ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    iterate_tmp_block.setBody(
        CPythonStatementsSequence(
            statements = statements,
            source_ref = source_ref
        )
    )

    statements = (
        iterate_tmp_block,
        buildStatementsNode(
            provider   = provider,
            nodes      = node.body,
            source_ref = source_ref
        )
    )

    loop_body = makeStatementsSequence(
        statements = statements,
        allow_none = True,
        source_ref = source_ref
    )

    if else_block is not None:
        statements = [
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTempVariableRef(
                    variable   = tmp_break_indicator_variable.makeReference( result ),
                    source_ref = source_ref
                ),
                source     = CPythonExpressionConstantRef(
                    constant = False,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        ]
    else:
        statements = []

    statements += [
        # First create the iterator and store it.
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_iter_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source     = CPythonExpressionBuiltinIter1(
                value       = source,
                source_ref  = source.getSourceReference()
            ),
            source_ref = source_ref
        ),
        CPythonStatementLoop(
            body       = loop_body,
            source_ref = source_ref
        )
    ]

    if else_block is not None:
        statements += [
            CPythonStatementConditional(
                condition  = CPythonExpressionComparisonIs(
                    left       = CPythonExpressionTempVariableRef(
                        variable   = tmp_break_indicator_variable.makeReference( result ),
                        source_ref = source_ref
                    ),
                    right      = CPythonExpressionConstantRef(
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

    result.setBody(
        CPythonStatementsSequence(
            statements = statements,
            source_ref = source_ref
        )
    )

    return result

def buildWhileLoopNode( provider, node, source_ref ):
    # The while loop is re-formulated according to developer manual. The condition becomes
    # an early condition to break the loop. The else block is taken if a while loop exits
    # normally, i.e. because of condition not being true. We do this by introducing an
    # indicator variable.

    else_block = buildStatementsNode(
        provider   = provider,
        nodes      = node.orelse if node.orelse else None,
        source_ref = source_ref
    )

    if else_block is not None:
        temp_block = CPythonStatementTempBlock(
            source_ref = source_ref
        )

        tmp_break_indicator_variable = temp_block.getTempVariable( "break_indicator" )

        statements = (
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTempVariableRef(
                    variable   = tmp_break_indicator_variable.makeReference( temp_block ),
                    source_ref = source_ref
                ),
                source     = CPythonExpressionConstantRef(
                    constant   = True,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            CPythonStatementBreakLoop(
                source_ref = source_ref
            )
        )
    else:
        statements = (
            CPythonStatementBreakLoop(
                source_ref = source_ref
            ),
        )

    # The loop body contains a conditional statement at the start that breaks the loop if
    # it fails.
    loop_body = makeStatementsSequence(
        statements = (
            CPythonStatementConditional(
                condition = buildNode( provider, node.test, source_ref ),
                no_branch = CPythonStatementsSequence(
                    statements = statements,
                    source_ref = source_ref
                ),
                yes_branch = None,
                source_ref = source_ref
            ),
            buildStatementsNode(
                provider   = provider,
                nodes      = node.body,
                source_ref = source_ref
            )
        ),
        allow_none = True,
        source_ref = source_ref
    )

    loop_statement = CPythonStatementLoop(
        body       = loop_body,
        source_ref = source_ref
    )

    if else_block is None:
        return loop_statement
    else:
        statements = (
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTempVariableRef(
                    variable   = tmp_break_indicator_variable.makeReference( temp_block ),
                    source_ref = source_ref
                ),
                source = CPythonExpressionConstantRef(
                    constant   = False,
                    source_ref = source_ref
                ),
                source_ref   = source_ref
            ),
            loop_statement,
            CPythonStatementConditional(
                condition  = CPythonExpressionComparisonIs(
                    left       = CPythonExpressionTempVariableRef(
                        variable   = tmp_break_indicator_variable.makeReference( temp_block ),
                        source_ref = source_ref
                    ),
                    right      = CPythonExpressionConstantRef(
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

        temp_block.setBody(
            CPythonStatementsSequence(
               statements = statements,
               source_ref = source_ref
            )
        )

        return temp_block
