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

from nuitka.nodes.ParameterSpec import ParameterSpec

from nuitka.nodes.VariableRefNode import (
    CPythonExpressionVariableRef,
    CPythonExpressionTempVariableRef,
    CPythonStatementTempBlock
)
from nuitka.nodes.BuiltinReferenceNodes import CPythonExpressionBuiltinExceptionRef
from nuitka.nodes.ConstantRefNode import CPythonExpressionConstantRef
from nuitka.nodes.AssignNodes import CPythonStatementAssignmentVariable
from nuitka.nodes.StatementNodes import (
    CPythonStatementExpressionOnly,
    CPythonStatementsSequence,
    CPythonStatementsFrame
)
from nuitka.nodes.FunctionNodes import (
    CPythonExpressionFunctionCreation,
    CPythonExpressionFunctionBody,
    CPythonExpressionFunctionCall,
    CPythonExpressionFunctionRef
)
from nuitka.nodes.LoopNodes import (
    CPythonStatementBreakLoop,
    CPythonStatementLoop
)
from nuitka.nodes.ConditionalNodes import CPythonStatementConditional
from nuitka.nodes.BuiltinIteratorNodes import (
    CPythonExpressionBuiltinNext1,
    CPythonExpressionBuiltinIter1
)
from nuitka.nodes.ContainerOperationNodes import (
    CPythonExpressionListOperationAppend,
    CPythonExpressionDictOperationSet,
    CPythonExpressionSetOperationAdd
)
from nuitka.nodes.ReturnNode import CPythonStatementReturn
from nuitka.nodes.YieldNode import CPythonExpressionYield
from nuitka.nodes.TryNodes import (
    CPythonStatementExceptHandler,
    CPythonStatementTryExcept
)

make_contraction_parameters = ParameterSpec(
    name          = "contraction",
    normal_args   = ( "__iterator", ),
    list_star_arg = None,
    dict_star_arg = None,
    default_count = 0,
    kw_only_args  = ()
)

from .ReformulationAssignmentStatements import buildAssignmentStatements

from .ReformulationBooleanExpressions import buildAndNode

from .Helpers import (
    buildNodeList,
    buildNode,
    getKind
)

def buildListContractionNode( provider, node, source_ref ):
    # List contractions are dealt with by general code.

    return _buildContractionNode(
        provider         = provider,
        node             = node,
        name             = "<listcontraction>",
        emit_class       = CPythonExpressionListOperationAppend,
        start_value      = CPythonExpressionConstantRef(
            constant   = [],
            source_ref = source_ref
        ),
        # Note: For Python3, the list contractions no longer assign to the outer scope.
        assign_provider  = Utils.python_version < 300,
        source_ref       = source_ref
    )

def buildSetContractionNode( provider, node, source_ref ):
    # Set contractions are dealt with by general code.

    return _buildContractionNode(
        provider         = provider,
        node             = node,
        name             = "<setcontraction>",
        emit_class       = CPythonExpressionSetOperationAdd,
        start_value      = CPythonExpressionConstantRef(
            constant   = set(),
            source_ref = source_ref
        ),
        assign_provider  = False,
        source_ref       = source_ref
    )

def buildDictContractionNode( provider, node, source_ref ):
    # Dict contractions are dealt with by general code.

    return _buildContractionNode(
        provider         = provider,
        node             = node,
        name             = "<dictcontraction>",
        emit_class       = CPythonExpressionDictOperationSet,
        start_value      = CPythonExpressionConstantRef(
            constant   = {},
            source_ref = source_ref
        ),
        assign_provider  = False,
        source_ref       = source_ref
    )

def buildGeneratorExpressionNode( provider, node, source_ref ):
    # Generator expressions are dealt with by general code.

    assert getKind( node ) == "GeneratorExp"

    return _buildContractionNode(
        provider         = provider,
        node             = node,
        name             = "<genexpr>",
        emit_class       = CPythonExpressionYield,
        start_value      = None,
        assign_provider  = False,
        source_ref       = source_ref
    )

def _buildContractionNode( provider, node, name, emit_class, start_value, assign_provider, source_ref ):
    # The contraction nodes are reformulated to function bodies, with loops as described
    # in the developer manual. They use a lot of temporary names, nested blocks, etc. and
    # so a lot of variable names. There is no good way around that, and we deal with many
    # cases, due to having generator expressions sharing this code,
    # pylint: disable=R0912,R0914

    # Note: The assign_provider is only to cover Python2 list contractions, assigning one
    # of the loop variables to the outside scope.

    assert provider.isParentVariableProvider(), provider

    function_body = CPythonExpressionFunctionBody(
        provider   = provider,
        name       = name,
        doc        = None,
        parameters = make_contraction_parameters,
        source_ref = source_ref
    )

    temp_block = CPythonStatementTempBlock(
        source_ref = source_ref
    )

    if start_value is not None:
        container_tmp = temp_block.getTempVariable( "result" )

        statements = [
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTempVariableRef(
                    variable   = container_tmp.makeReference( temp_block ),
                    source_ref = source_ref
                ),
                source     = start_value,
                source_ref = source_ref.atInternal()
            )
        ]
    else:
        statements = []

    if hasattr( node, "elt" ):
        if start_value is not None:
            current_body = emit_class(
                CPythonExpressionTempVariableRef(
                    variable   = container_tmp.makeReference( temp_block ),
                    source_ref = source_ref
                ),
                buildNode(
                    provider   = function_body,
                    node       = node.elt,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        else:
            assert emit_class is CPythonExpressionYield

            function_body.markAsGenerator()

            current_body = emit_class(
                buildNode(
                    provider   = function_body,
                    node       = node.elt,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
    else:
        assert emit_class is CPythonExpressionDictOperationSet

        current_body = emit_class(
            CPythonExpressionTempVariableRef(
                variable   = container_tmp.makeReference( temp_block ),
                source_ref = source_ref
            ),
            key = buildNode(
                provider   = function_body,
                node       = node.key,
                source_ref = source_ref,
            ),
            value = buildNode(
                provider   = function_body,
                node       = node.value,
                source_ref = source_ref,
            ),
            source_ref = source_ref
        )

    current_body = CPythonStatementExpressionOnly(
        expression = current_body,
        source_ref = source_ref
    )

    for qual in reversed( node.generators ):
        nested_temp_block = CPythonStatementTempBlock(
            source_ref = source_ref
        )

        tmp_iter_variable = nested_temp_block.getTempVariable( "contraction_iter" )

        tmp_value_variable = nested_temp_block.getTempVariable( "iter_value" )

        # The first iterated value is to be calculated outside of the function and
        # will be given as a parameter "_iterated".
        if qual is node.generators[0]:
            value_iterator = CPythonExpressionVariableRef(
                variable_name = "__iterator",
                source_ref    = source_ref
            )
        else:
            value_iterator = CPythonExpressionBuiltinIter1(
                value      = buildNode(
                    provider   = function_body,
                    node       = qual.iter,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )

        # First create the iterator and store it, next should be loop body
        nested_statements = [
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTempVariableRef(
                    variable   = tmp_iter_variable.makeReference( nested_temp_block ),
                    source_ref = source_ref
                ),
                source     = value_iterator,
                source_ref = source_ref
            )
        ]

        loop_statements = [
            CPythonStatementTryExcept(
                tried      = CPythonStatementsSequence(
                    statements = (
                        CPythonStatementAssignmentVariable(
                            variable_ref = CPythonExpressionTempVariableRef(
                                variable   = tmp_value_variable.makeReference( nested_temp_block ),
                                source_ref = source_ref
                            ),
                            source     = CPythonExpressionBuiltinNext1(
                                value      = CPythonExpressionTempVariableRef(
                                    variable   = tmp_iter_variable.makeReference( nested_temp_block ),
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
                        body           = CPythonStatementsSequence(
                            statements = (
                                CPythonStatementBreakLoop(
                                    source_ref = source_ref.atInternal()
                                ),
                            ),
                            source_ref = source_ref
                        ),
                        source_ref     = source_ref
                    ),
                ),
                source_ref = source_ref
            ),
            buildAssignmentStatements(
                provider   = provider if assign_provider else function_body,
                node       = qual.target,
                source     = CPythonExpressionTempVariableRef(
                    variable   = tmp_value_variable.makeReference( nested_temp_block ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        ]

        conditions = buildNodeList(
            provider   = function_body,
            nodes      = qual.ifs,
            source_ref = source_ref
        )

        if len( conditions ) == 1:
            loop_statements.append(
                CPythonStatementConditional(
                    condition  = conditions[0],
                    yes_branch = CPythonStatementsSequence(
                        statements = ( current_body, ),
                        source_ref = source_ref
                    ),
                    no_branch  = None,
                    source_ref = source_ref
                )
            )
        elif len( conditions ) > 1:
            loop_statements.append(
                CPythonStatementConditional(
                    condition = buildAndNode(
                        provider   = function_body,
                        values     = conditions,
                        source_ref = source_ref
                    ),
                    yes_branch = CPythonStatementsSequence(
                        statements = ( current_body, ),
                        source_ref = source_ref
                    ),
                    no_branch  = None,
                    source_ref = source_ref
                )
            )
        else:
            loop_statements.append( current_body )

        nested_statements.append(
            CPythonStatementLoop(
                body       = CPythonStatementsSequence(
                    statements = loop_statements,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        )

        nested_temp_block.setBody(
            CPythonStatementsSequence(
                statements = nested_statements,
                source_ref = source_ref
            )
        )

        current_body = nested_temp_block

    statements.append( current_body )

    if start_value is not None:
        statements.append(
            CPythonStatementReturn(
                expression = CPythonExpressionTempVariableRef(
                    variable   = container_tmp.makeReference( temp_block ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        )

    temp_block.setBody(
        CPythonStatementsSequence(
            statements = statements,
            source_ref = source_ref
        )
    )

    function_body.setBody(
        CPythonStatementsFrame(
            statements    = [ temp_block ],
            guard_mode    = "pass_through" if emit_class is not CPythonExpressionYield else "generator",
            arg_names     = (),
            kw_only_count = 0,
            code_name     = "contraction",
            source_ref    = source_ref
        )
    )

    return CPythonExpressionFunctionCall(
        function   = CPythonExpressionFunctionCreation(
            function_ref = CPythonExpressionFunctionRef(
                function_body = function_body,
                source_ref    = source_ref
            ),
            defaults     = (),
            kw_defaults  = None,
            annotations  = None,
            source_ref   = source_ref
        ),
        values     = (
            CPythonExpressionBuiltinIter1(
                value      = buildNode(
                    provider   = provider,
                    node       = node.generators[0].iter,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
        ),
        source_ref = source_ref
    )
