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
from nuitka.nodes.FunctionNodes import (
    CPythonExpressionFunctionCreation,
    CPythonExpressionFunctionBody,
    CPythonExpressionFunctionRef
)
from nuitka.nodes.StatementNodes import (
    CPythonStatementExpressionOnly,
    CPythonStatementsSequence,
    CPythonStatementsFrame
)
from nuitka.nodes.ComparisonNodes import CPythonExpressionComparisonIsNOT
from nuitka.nodes.ConditionalNodes import CPythonStatementConditional
from nuitka.nodes.YieldNodes import CPythonExpressionYield
from nuitka.nodes.ReturnNodes import CPythonStatementReturn
from nuitka.nodes.AssignNodes import CPythonStatementAssignmentVariable

from .ReformulationFunctionStatements import (
    buildParameterKwDefaults,
    buildParameterAnnotations,
    buildParameterSpec
)

from .Helpers import (
    buildNodeList,
    buildNode,
    getKind
)

def buildLambdaNode( provider, node, source_ref ):
    assert getKind( node ) == "Lambda"

    function_body = CPythonExpressionFunctionBody(
        provider   = provider,
        name       = "<lambda>",
        doc        = None,
        parameters = buildParameterSpec( "<lambda>", node, source_ref ),
        source_ref = source_ref,
    )

    defaults = buildNodeList( provider, node.args.defaults, source_ref )
    kw_defaults = buildParameterKwDefaults( provider, node, function_body, source_ref )

    body = buildNode(
        provider   = function_body,
        node       = node.body,
        source_ref = source_ref,
    )

    if function_body.isGenerator():
        if Utils.python_version < 270:
            temp_block = CPythonStatementTempBlock(
                source_ref = source_ref,
            )

            tmp_return_value = temp_block.getTempVariable( "yield_return" )

            statements = (
                CPythonStatementAssignmentVariable(
                    variable_ref = CPythonExpressionTempVariableRef(
                        variable = tmp_return_value.makeReference( temp_block ),
                        source_ref = source_ref,
                    ),
                    source     = body,
                    source_ref = source_ref
                ),
                CPythonStatementConditional(
                    condition = CPythonExpressionComparisonIsNOT(
                        left       = CPythonExpressionTempVariableRef(
                            variable = tmp_return_value.makeReference( temp_block ),
                            source_ref = source_ref,
                        ),
                        right      = CPythonExpressionConstantRef(
                            constant   = None,
                            source_ref = source_ref
                        ),
                        source_ref = source_ref
                    ),
                    yes_branch = CPythonStatementsSequence(
                        statements = (
                            CPythonStatementExpressionOnly(
                                expression = CPythonExpressionYield(
                                    expression = CPythonExpressionTempVariableRef(
                                        variable = tmp_return_value.makeReference( temp_block ),
                                        source_ref = source_ref,
                                    ),
                                    source_ref = source_ref
                                ),
                                source_ref = source_ref
                            ),
                        ),
                        source_ref = source_ref
                    ),
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

            body = temp_block
        else:
            body = CPythonStatementExpressionOnly(
                expression = body,
                source_ref = source_ref
            )
    else:
        body = CPythonStatementReturn(
            expression = body,
            source_ref = source_ref
        )

    body = CPythonStatementsFrame(
        statements    = ( body, ),
        guard_mode    = "generator" if function_body.isGenerator() else "full",
        arg_names     = function_body.getParameters().getCoArgNames(),
        kw_only_count = function_body.getParameters().getKwOnlyParameterCount(),
        code_name     = "<lambda>",
        source_ref    = body.getSourceReference()
    )

    function_body.setBody( body )

    annotations = buildParameterAnnotations( provider, node, source_ref )

    return CPythonExpressionFunctionCreation(
        function_ref = CPythonExpressionFunctionRef(
            function_body = function_body,
            source_ref    = source_ref
        ),
        defaults     = defaults,
        kw_defaults  = kw_defaults,
        annotations  = annotations,
        source_ref   = source_ref
    )
