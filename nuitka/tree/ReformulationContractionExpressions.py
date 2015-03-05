#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Reformulation of contraction expressions.

Consult the developer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

from nuitka import Utils
from nuitka.nodes.AssignNodes import (
    StatementAssignmentVariable,
    StatementReleaseVariable,
)
from nuitka.nodes.BuiltinIteratorNodes import (
    ExpressionBuiltinIter1,
    ExpressionBuiltinNext1
)
from nuitka.nodes.ConditionalNodes import StatementConditional
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.ContainerOperationNodes import (
    ExpressionDictOperationSet,
    ExpressionListOperationAppend,
    ExpressionSetOperationAdd
)
from nuitka.nodes.FunctionNodes import (
    ExpressionFunctionBody,
    ExpressionFunctionCall,
    ExpressionFunctionCreation,
    ExpressionFunctionRef
)
from nuitka.nodes.LoopNodes import StatementBreakLoop, StatementLoop
from nuitka.nodes.ParameterSpecs import ParameterSpec
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.StatementNodes import (
    StatementExpressionOnly,
    StatementGeneratorEntry,
    StatementsFrame,
    StatementsSequence
)
from nuitka.nodes.VariableRefNodes import (
    ExpressionTargetTempVariableRef,
    ExpressionTempVariableRef,
    ExpressionVariableRef
)
from nuitka.nodes.YieldNodes import ExpressionYield

from .Helpers import (
    buildNode,
    buildNodeList,
    getKind,
    makeStatementsSequenceFromStatement,
    makeTryFinallyExpression,
    makeTryFinallyStatement,
    mergeStatements,
    wrapTryFinallyLater
)
from .ReformulationAssignmentStatements import buildAssignmentStatements
from .ReformulationBooleanExpressions import buildAndNode
from .ReformulationTryExceptStatements import makeTryExceptSingleHandlerNode


def buildListContractionNode(provider, node, source_ref):
    # List contractions are dealt with by general code.

    if Utils.python_version < 300:
        temp_scope = provider.allocateTempScope("listcontr")

        outer_iter_var = provider.allocateTempVariable(
            temp_scope = temp_scope,
            name       = "listcontr_iter"
        )

        outer_iter_ref = ExpressionTempVariableRef(
            variable   = outer_iter_var,
            source_ref = source_ref
        )

        container_tmp   = provider.allocateTempVariable(
            temp_scope = temp_scope,
            name       = "listcontr_result"
        )

        statements, release_statements = _buildContractionBodyNode(
            provider        = provider,
            node            = node,
            emit_class      = ExpressionListOperationAppend,
            start_value     = ExpressionConstantRef(
                constant   = [],
                source_ref = source_ref
            ),
            outer_iter_ref  = outer_iter_ref,
            container_tmp   = container_tmp,
            temp_scope      = temp_scope,
            assign_provider = True,
            source_ref      = source_ref,
            function_body   = provider
        )

        statements.insert(
            0,
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetTempVariableRef(
                    variable   = outer_iter_var,
                    source_ref = source_ref
                ),
                source       = ExpressionBuiltinIter1(
                    value      = buildNode(
                        provider   = provider,
                        node       = node.generators[0].iter,
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
                source_ref   = source_ref
            )
        )

        result = makeTryFinallyExpression(
            expression = ExpressionTempVariableRef(
                variable   = container_tmp,
                source_ref = source_ref
            ),
            tried      = statements,
            final      = release_statements,
            source_ref = source_ref
        )

        final = StatementsSequence(
            statements = (
                StatementReleaseVariable(
                    variable   = container_tmp,
                    tolerant   = True,
                    source_ref = source_ref
                ),
                StatementReleaseVariable(
                    variable   = outer_iter_var,
                    tolerant   = True,
                    source_ref = source_ref
                ),
            ),
            source_ref = source_ref
        )

        wrapTryFinallyLater(
            node  = result,
            final = final
        )

        return result

    return _buildContractionNode(
        provider        = provider,
        node            = node,
        name            = "<listcontraction>",
        emit_class      = ExpressionListOperationAppend,
        start_value     = ExpressionConstantRef(
            constant   = [],
            source_ref = source_ref
        ),
        # Note: For Python3, the list contractions no longer assign to the outer
        # scope.
        assign_provider = Utils.python_version < 300,
        source_ref      = source_ref
    )


def buildSetContractionNode(provider, node, source_ref):
    # Set contractions are dealt with by general code.

    return _buildContractionNode(
        provider        = provider,
        node            = node,
        name            = "<setcontraction>",
        emit_class      = ExpressionSetOperationAdd,
        start_value     = ExpressionConstantRef(
            constant   = set(),
            source_ref = source_ref
        ),
        assign_provider = False,
        source_ref      = source_ref
    )


def buildDictContractionNode(provider, node, source_ref):
    # Dict contractions are dealt with by general code.

    return _buildContractionNode(
        provider        = provider,
        node            = node,
        name            = "<dictcontraction>",
        emit_class      = ExpressionDictOperationSet,
        start_value     = ExpressionConstantRef(
            constant   = {},
            source_ref = source_ref
        ),
        assign_provider = False,
        source_ref      = source_ref
    )


def buildGeneratorExpressionNode(provider, node, source_ref):
    # Generator expressions are dealt with by general code.

    assert getKind(node) == "GeneratorExp"

    return _buildContractionNode(
        provider        = provider,
        node            = node,
        name            = "<genexpr>",
        emit_class      = ExpressionYield,
        start_value     = None,
        assign_provider = False,
        source_ref      = source_ref
    )


def _buildContractionBodyNode(provider, node, emit_class, start_value,
                              container_tmp, outer_iter_ref, temp_scope,
                              assign_provider, source_ref, function_body):
    # This uses lots of variables and branches. There is no good way
    # around that, and we deal with many cases, due to having generator
    # expressions sharing this code, pylint: disable=R0912,R0914
    if start_value is not None:
        statements = [
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetTempVariableRef(
                    variable   = container_tmp,
                    source_ref = source_ref
                ),
                source       = start_value,
                source_ref   = source_ref.atInternal()
            )
        ]

        if assign_provider:
            tmp_variables = []
        else:
            tmp_variables = [container_tmp]
    else:
        statements = []
        tmp_variables = []

    if hasattr(node, "elt"):
        if start_value is not None:
            current_body = emit_class(
                ExpressionTempVariableRef(
                    variable   = container_tmp,
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
            assert emit_class is ExpressionYield

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
        assert emit_class is ExpressionDictOperationSet

        current_body = emit_class(
            ExpressionTempVariableRef(
                variable   = container_tmp,
                source_ref = source_ref
            ),
            key        = buildNode(
                provider   = function_body,
                node       = node.key,
                source_ref = source_ref,
            ),
            value      = buildNode(
                provider   = function_body,
                node       = node.value,
                source_ref = source_ref,
            ),
            source_ref = source_ref
        )

    current_body = StatementExpressionOnly(
        expression = current_body,
        source_ref = source_ref
    )

    for count, qual in enumerate(reversed(node.generators)):
        tmp_value_variable = function_body.allocateTempVariable(
            temp_scope = temp_scope,
            name       = "iter_value_%d" % count
        )

        tmp_variables.append(tmp_value_variable)

        # The first iterated value is to be calculated outside of the function
        # and will be given as a parameter "_iterated", the others are built
        # inside the function.

        if qual is node.generators[0]:
            iterator_ref = outer_iter_ref.makeCloneAt(source_ref)

            tmp_iter_variable = None

            nested_statements = []
        else:
            # First create the iterator and store it, next should be loop body
            value_iterator = ExpressionBuiltinIter1(
                value      = buildNode(
                    provider   = function_body,
                    node       = qual.iter,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )

            tmp_iter_variable = function_body.allocateTempVariable(
                temp_scope = temp_scope,
                name       = "contraction_iter_%d" % count
            )

            tmp_variables.append(tmp_iter_variable)

            nested_statements = [
                StatementAssignmentVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = tmp_iter_variable,
                        source_ref = source_ref
                    ),
                    source       = value_iterator,
                    source_ref   = source_ref
                )
            ]

            iterator_ref = ExpressionTempVariableRef(
                variable   = tmp_iter_variable,
                source_ref = source_ref
            )

        loop_statements = [
            makeTryExceptSingleHandlerNode(
                tried          = makeStatementsSequenceFromStatement(
                    statement = StatementAssignmentVariable(
                        variable_ref = ExpressionTargetTempVariableRef(
                            variable   = tmp_value_variable,
                            source_ref = source_ref
                        ),
                        source       = ExpressionBuiltinNext1(
                            value      = iterator_ref,
                            source_ref = source_ref
                        ),
                        source_ref   = source_ref
                    )
                ),
                exception_name = "StopIteration",
                handler_body   = makeStatementsSequenceFromStatement(
                    statement = StatementBreakLoop(
                        source_ref = source_ref.atInternal()
                    )
                ),
                public_exc     = False,
                source_ref     = source_ref
            ),
            buildAssignmentStatements(
                provider      = provider if assign_provider else function_body,
                temp_provider = function_body,
                node          = qual.target,
                source        = ExpressionTempVariableRef(
                    variable   = tmp_value_variable,
                    source_ref = source_ref
                ),
                source_ref    = source_ref
            )
        ]

        conditions = buildNodeList(
            provider   = function_body,
            nodes      = qual.ifs,
            source_ref = source_ref
        )

        if len(conditions) == 1:
            loop_statements.append(
                StatementConditional(
                    condition  = conditions[0],
                    yes_branch = makeStatementsSequenceFromStatement(
                        statement = current_body
                    ),
                    no_branch  = None,
                    source_ref = source_ref
                )
            )
        elif len(conditions) > 1:
            loop_statements.append(
                StatementConditional(
                    condition  = buildAndNode(
                        provider   = function_body,
                        values     = conditions,
                        source_ref = source_ref
                    ),
                    yes_branch = makeStatementsSequenceFromStatement(
                        statement = current_body
                    ),
                    no_branch  = None,
                    source_ref = source_ref
                )
            )
        else:
            loop_statements.append(current_body)

        nested_statements.append(
            StatementLoop(
                body       = StatementsSequence(
                    statements = mergeStatements(loop_statements),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        )

        if tmp_iter_variable is not None:
            nested_statements.append(
                StatementReleaseVariable(
                    variable   = tmp_iter_variable,
                    tolerant   = False,
                    source_ref = source_ref
                )
            )

        current_body = StatementsSequence(
            statements = nested_statements,
            source_ref = source_ref
        )

    statements.append(current_body)
    statements = mergeStatements(statements)

    if emit_class is ExpressionYield:
        statements.insert(
            0,
            StatementGeneratorEntry(
                source_ref = source_ref
            )
        )

    release_statements = [
        StatementReleaseVariable(
            variable   = tmp_variable,
            tolerant   = True,
            source_ref = source_ref
        )
        for tmp_variable in
        tmp_variables
    ]

    return statements, release_statements


def _buildContractionNode(provider, node, name, emit_class, start_value,
                          assign_provider, source_ref):
    # The contraction nodes are reformulated to function bodies, with loops as
    # described in the developer manual. They use a lot of temporary names,
    # nested blocks, etc. and so a lot of variable names.

    # Note: The assign_provider is only to cover Python2 list contractions,
    # assigning one of the loop variables to the outside scope.

    assert provider.isParentVariableProvider(), provider

    iterator_var_name = ".0"

    function_body = ExpressionFunctionBody(
        provider   = provider,
        name       = name,
        doc        = None,
        parameters = ParameterSpec(
            name          = "contraction",
            normal_args   = (iterator_var_name,),
            list_star_arg = None,
            dict_star_arg = None,
            default_count = 0,
            kw_only_args  = ()
        ),
        source_ref = source_ref
    )

    if start_value is not None:
        container_tmp = function_body.allocateTempVariable(
            temp_scope = None,
            name       = "contraction_result"
        )
    else:
        container_tmp = None

    outer_iter_ref = ExpressionVariableRef(
        variable_name = iterator_var_name,
        source_ref    = source_ref
    )

    statements, del_statements = _buildContractionBodyNode(
        function_body   = function_body,
        assign_provider = assign_provider,
        provider        = provider,
        node            = node,
        emit_class      = emit_class,
        outer_iter_ref  = outer_iter_ref,
        temp_scope      = None,
        start_value     = start_value,
        container_tmp   = container_tmp,
        source_ref      = source_ref,
    )

    if start_value is not None:
        statements.append(
            StatementReturn(
                expression = ExpressionTempVariableRef(
                    variable   = container_tmp,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        )

    statements = (
        makeTryFinallyStatement(
            tried      = statements,
            final      = del_statements,
            source_ref = source_ref.atInternal()
        ),
    )

    function_body.setBody(
        StatementsFrame(
            statements    = statements,
            guard_mode    = "pass_through"
                              if emit_class is not ExpressionYield else
                            "generator",
            var_names     = (),
            arg_count     = 0,
            kw_only_count = 0,
            has_starlist  = False,
            has_stardict  = False,
            code_name     = "contraction",
            source_ref    = source_ref
        )
    )

    return ExpressionFunctionCall(
        function   = ExpressionFunctionCreation(
            function_ref = ExpressionFunctionRef(
                function_body = function_body,
                source_ref    = source_ref
            ),
            defaults     = (),
            kw_defaults  = None,
            annotations  = None,
            source_ref   = source_ref
        ),
        values     = (
            ExpressionBuiltinIter1(
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
