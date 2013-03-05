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

from nuitka import Utils

from nuitka.nodes.VariableRefNodes import (
    ExpressionTargetTempVariableRef,
    ExpressionTempVariableRef,
    StatementTempBlock
)
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.BuiltinRefNodes import ExpressionBuiltinExceptionRef
from nuitka.nodes.ContainerMakingNodes import ExpressionMakeTuple
from nuitka.nodes.ExceptionNodes import (
    ExpressionCaughtExceptionTracebackRef,
    ExpressionCaughtExceptionValueRef,
    ExpressionCaughtExceptionTypeRef,
    StatementRaiseException
)
from nuitka.nodes.CallNodes import (
    ExpressionCallNoKeywords,
    ExpressionCallEmpty
)
from nuitka.nodes.AttributeNodes import (
    ExpressionSpecialAttributeLookup,
    ExpressionAttributeLookup
)
from nuitka.nodes.StatementNodes import (
    StatementExpressionOnly,
    StatementsSequence
)
from nuitka.nodes.ConditionalNodes import StatementConditional
from nuitka.nodes.AssignNodes import StatementAssignmentVariable
from nuitka.nodes.TryNodes import StatementExceptHandler

from .ReformulationTryExceptStatements import makeTryExceptNoRaise
from .ReformulationAssignmentStatements import buildAssignmentStatements


from .Helpers import (
    makeStatementsSequence,
    buildStatementsNode,
    buildNode
)

def buildWithNode( provider, node, source_ref ):
    # "with" statements are re-formulated as described in the developer manual. Catches
    # exceptions, and provides them to "__exit__", while making the "__enter__" value
    # available under a given name.

    with_source = buildNode( provider, node.context_expr, source_ref )

    result = StatementTempBlock(
        source_ref = source_ref
    )

    tmp_source_variable = result.getTempVariable( "with_source" )
    tmp_exit_variable = result.getTempVariable( "with_exit" )
    tmp_enter_variable = result.getTempVariable( "with_enter" )

    statements = (
        buildAssignmentStatements(
            provider   = provider,
            node       = node.optional_vars,
            allow_none = True,
            source     = ExpressionTempVariableRef(
                variable   = tmp_enter_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
        buildStatementsNode( provider, node.body, source_ref )
    )

    with_body = makeStatementsSequence(
        statements = statements,
        allow_none = True,
        source_ref = source_ref
    )

    # The "__enter__" and "__exit__" were normal attribute lookups under CPython2.6, but
    # that changed with CPython2.7.
    if Utils.python_version < 270:
        attribute_lookup_class = ExpressionAttributeLookup
    else:
        attribute_lookup_class = ExpressionSpecialAttributeLookup

    statements = [
        # First assign the with context to a temporary variable.
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_source_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source       = with_source,
            source_ref   = source_ref
        ),
        # Next, assign "__enter__" and "__exit__" attributes to temporary variables.
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_exit_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source       = attribute_lookup_class(
                expression     = ExpressionTempVariableRef(
                    variable   = tmp_source_variable.makeReference( result ),
                    source_ref = source_ref
                ),
                attribute_name = "__exit__",
                source_ref     = source_ref
            ),
            source_ref   = source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_enter_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source       = ExpressionCallEmpty(
                called         = attribute_lookup_class(
                    expression     = ExpressionTempVariableRef(
                        variable   = tmp_source_variable.makeReference( result ),
                        source_ref = source_ref
                    ),
                    attribute_name = "__enter__",
                    source_ref     = source_ref
                ),
                source_ref      = source_ref
            ),
            source_ref   = source_ref
        )
    ]

    source_ref = source_ref.atInternal()

    statements += [
        makeTryExceptNoRaise(
            tried      = with_body,
            handlers   = (
                StatementExceptHandler(
                    exception_types = (
                        ExpressionBuiltinExceptionRef(
                            exception_name = "BaseException",
                            source_ref     = source_ref
                        ),
                    ),
                    body           = StatementsSequence(
                        statements = (
                            StatementConditional(
                                condition     = ExpressionCallNoKeywords(
                                    called          = ExpressionTempVariableRef(
                                        variable   = tmp_exit_variable.makeReference( result ),
                                        source_ref = source_ref
                                    ),
                                    args = ExpressionMakeTuple(
                                        elements   = (
                                            ExpressionCaughtExceptionTypeRef(
                                                source_ref = source_ref
                                            ),
                                            ExpressionCaughtExceptionValueRef(
                                                source_ref = source_ref
                                            ),
                                            ExpressionCaughtExceptionTracebackRef(
                                                source_ref = source_ref
                                            ),
                                        ),
                                        source_ref = source_ref
                                    ),
                                    source_ref      = source_ref
                                ),
                                no_branch = StatementsSequence(
                                    statements = (
                                        StatementRaiseException(
                                            exception_type  = None,
                                            exception_value = None,
                                            exception_trace = None,
                                            exception_cause = None,
                                            source_ref      = source_ref
                                        ),
                                    ),
                                    source_ref = source_ref
                                ),
                                yes_branch  = None,
                                source_ref = source_ref
                            ),
                        ),
                        source_ref     = source_ref
                    ),
                    source_ref = source_ref
                ),
            ),
            no_raise   = StatementsSequence(
                statements = (
                    StatementExpressionOnly(
                        expression = ExpressionCallNoKeywords(
                            called     = ExpressionTempVariableRef(
                                variable   = tmp_exit_variable.makeReference( result ),
                                source_ref = source_ref
                            ),
                            args       = ExpressionConstantRef(
                                constant   = ( None, None, None ),
                                source_ref = source_ref
                            ),
                            source_ref = source_ref
                        ),
                        source_ref     = source_ref
                    ),
                ),
                source_ref     = source_ref
            ),
            source_ref = source_ref
        )
    ]

    result.setBody(
        StatementsSequence(
            statements = statements,
            source_ref = source_ref
        )
    )

    return result
