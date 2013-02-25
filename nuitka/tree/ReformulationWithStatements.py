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
    CPythonExpressionTempVariableRef,
    CPythonStatementTempBlock
)
from nuitka.nodes.ConstantRefNodes import CPythonExpressionConstantRef
from nuitka.nodes.BuiltinRefNodes import CPythonExpressionBuiltinExceptionRef
from nuitka.nodes.ContainerMakingNodes import CPythonExpressionMakeTuple
from nuitka.nodes.ExceptionNodes import (
    CPythonExpressionCaughtExceptionTracebackRef,
    CPythonExpressionCaughtExceptionValueRef,
    CPythonExpressionCaughtExceptionTypeRef,
    CPythonStatementRaiseException
)
from nuitka.nodes.CallNodes import (
    CPythonExpressionCallNoKeywords,
    CPythonExpressionCallEmpty
)
from nuitka.nodes.AttributeNodes import (
    CPythonExpressionSpecialAttributeLookup,
    CPythonExpressionAttributeLookup
)
from nuitka.nodes.StatementNodes import (
    CPythonStatementExpressionOnly,
    CPythonStatementsSequence
)
from nuitka.nodes.ConditionalNodes import CPythonStatementConditional
from nuitka.nodes.AssignNodes import CPythonStatementAssignmentVariable
from nuitka.nodes.TryNodes import CPythonStatementExceptHandler

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

    result = CPythonStatementTempBlock(
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
            source     = CPythonExpressionTempVariableRef(
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
        attribute_lookup_class = CPythonExpressionAttributeLookup
    else:
        attribute_lookup_class = CPythonExpressionSpecialAttributeLookup

    statements = [
        # First assign the with context to a temporary variable.
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_source_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source       = with_source,
            source_ref   = source_ref
        ),
        # Next, assign "__enter__" and "__exit__" attributes to temporary variables.
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_exit_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source       = attribute_lookup_class(
                expression     = CPythonExpressionTempVariableRef(
                    variable   = tmp_source_variable.makeReference( result ),
                    source_ref = source_ref
                ),
                attribute_name = "__exit__",
                source_ref     = source_ref
            ),
            source_ref   = source_ref
        ),
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_enter_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source       = CPythonExpressionCallEmpty(
                called         = attribute_lookup_class(
                    expression     = CPythonExpressionTempVariableRef(
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
                CPythonStatementExceptHandler(
                    exception_types = (
                        CPythonExpressionBuiltinExceptionRef(
                            exception_name = "BaseException",
                            source_ref     = source_ref
                        ),
                    ),
                    body           = CPythonStatementsSequence(
                        statements = (
                            CPythonStatementConditional(
                                condition     = CPythonExpressionCallNoKeywords(
                                    called          = CPythonExpressionTempVariableRef(
                                        variable   = tmp_exit_variable.makeReference( result ),
                                        source_ref = source_ref
                                    ),
                                    args = CPythonExpressionMakeTuple(
                                        elements   = (
                                            CPythonExpressionCaughtExceptionTypeRef(
                                                source_ref = source_ref
                                            ),
                                            CPythonExpressionCaughtExceptionValueRef(
                                                source_ref = source_ref
                                            ),
                                            CPythonExpressionCaughtExceptionTracebackRef(
                                                source_ref = source_ref
                                            ),
                                        ),
                                        source_ref = source_ref
                                    ),
                                    source_ref      = source_ref
                                ),
                                no_branch = CPythonStatementsSequence(
                                    statements = (
                                        CPythonStatementRaiseException(
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
            no_raise   = CPythonStatementsSequence(
                statements = (
                    CPythonStatementExpressionOnly(
                        expression = CPythonExpressionCallNoKeywords(
                            called     = CPythonExpressionTempVariableRef(
                                variable   = tmp_exit_variable.makeReference( result ),
                                source_ref = source_ref
                            ),
                            args       = CPythonExpressionConstantRef(
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
        CPythonStatementsSequence(
            statements = statements,
            source_ref = source_ref
        )
    )

    return result
