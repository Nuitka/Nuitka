#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.nodes.AssignNodes import (
    ExpressionTargetTempVariableRef,
    ExpressionTempVariableRef,
    StatementAssignmentVariable,
    StatementReleaseVariable
)
from nuitka.nodes.BuiltinIteratorNodes import (
    ExpressionBuiltinIter1,
    ExpressionBuiltinNext1
)
from nuitka.nodes.CodeObjectSpecs import CodeObjectSpec
from nuitka.nodes.ConditionalNodes import StatementConditional
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.ContainerOperationNodes import (
    StatementListOperationAppend,
    StatementSetOperationAdd
)
from nuitka.nodes.DictionaryNodes import StatementDictOperationSet
from nuitka.nodes.FrameNodes import StatementsFrame
from nuitka.nodes.FunctionNodes import (
    ExpressionFunctionBody,
    ExpressionFunctionCall,
    ExpressionFunctionCreation,
    ExpressionFunctionRef
)
from nuitka.nodes.GeneratorNodes import (
    ExpressionGeneratorObjectBody,
    ExpressionMakeGeneratorObject
)
from nuitka.nodes.LoopNodes import StatementLoop, StatementLoopBreak
from nuitka.nodes.NodeMakingHelpers import (
    makeVariableRefNode,
    makeVariableTargetRefNode
)
from nuitka.nodes.OutlineNodes import ExpressionOutlineBody
from nuitka.nodes.ParameterSpecs import ParameterSpec
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.StatementNodes import (
    StatementExpressionOnly,
    StatementGeneratorEntry,
    StatementsSequence
)
from nuitka.nodes.YieldNodes import ExpressionYield
from nuitka.PythonVersions import python_version

from .Helpers import (
    buildNode,
    buildNodeList,
    getKind,
    makeStatementsSequenceFromStatement,
    mergeStatements
)
from .ReformulationAssignmentStatements import buildAssignmentStatements
from .ReformulationBooleanExpressions import buildAndNode
from .ReformulationTryExceptStatements import makeTryExceptSingleHandlerNode
from .ReformulationTryFinallyStatements import makeTryFinallyStatement


def buildListContractionNode(provider, node, source_ref):
    # List contractions are dealt with by general code.

    return _buildContractionNode(
        provider        = provider,
        node            = node,
        name            = "list_contraction"
                            if python_version < 300 else
                          "<listcontraction>",
        emit_class      = StatementListOperationAppend,
        start_value     = ExpressionConstantRef(
            constant   = [],
            source_ref = source_ref
        ),
        # Note: For Python3, the list contractions no longer assign to the outer
        # scope.
        assign_provider = python_version < 300,
        source_ref      = source_ref
    )


def buildSetContractionNode(provider, node, source_ref):
    # Set contractions are dealt with by general code.

    return _buildContractionNode(
        provider        = provider,
        node            = node,
        name            = "<setcontraction>",
        emit_class      = StatementSetOperationAdd,
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
        emit_class      = StatementDictOperationSet,
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
                              container_tmp, iter_tmp, temp_scope,
                              assign_provider, function_body, source_ref):

    # This uses lots of variables and branches. There is no good way
    # around that, and we deal with many cases, due to having generator
    # expressions sharing this code, pylint: disable=R0912,R0914
    tmp_variables = []

    if assign_provider:
        tmp_variables.append(iter_tmp)

    if container_tmp is not None:
        tmp_variables.append(container_tmp)

    # First assign the iterator if we are an outline.
    if assign_provider:
        statements = [
            StatementAssignmentVariable(
                variable_ref = makeVariableTargetRefNode(
                    variable   = iter_tmp,
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
                source_ref   = source_ref.atInternal()
            )
        ]
    else:
        statements = []

    if start_value is not None:
        statements.append(
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetTempVariableRef(
                    variable   = container_tmp,
                    source_ref = source_ref
                ),
                source       = start_value,
                source_ref   = source_ref.atInternal()
            )
        )


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

            current_body = emit_class(
                buildNode(
                    provider   = function_body,
                    node       = node.elt,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
    else:
        assert emit_class is StatementDictOperationSet

        current_body = StatementDictOperationSet(
            dict_arg   = ExpressionTempVariableRef(
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

    if current_body.isExpression():
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
            iterator_ref = makeVariableRefNode(
                variable   = iter_tmp,
                source_ref = source_ref
            )

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
                tried          = StatementAssignmentVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = tmp_value_variable,
                        source_ref = source_ref
                    ),
                    source       = ExpressionBuiltinNext1(
                        value      = iterator_ref,
                        source_ref = source_ref
                    ),
                    source_ref   = source_ref
                ),
                exception_name = "StopIteration",
                handler_body   = StatementLoopBreak(
                    source_ref = source_ref.atInternal()
                ),
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

        if len(conditions) >= 1:
            loop_statements.append(
                StatementConditional(
                    condition  = buildAndNode(
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
                    source_ref = source_ref
                )
            )

        current_body = StatementsSequence(
            statements = mergeStatements(nested_statements, False),
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
    if assign_provider:
        function_body = ExpressionOutlineBody(
            provider   = provider,
            name       = name,
            source_ref = source_ref
        )

        iter_tmp = function_body.allocateTempVariable(
            temp_scope = None,
            name       = ".0"
        )
    else:
        # TODO: No function ought to be necessary.

        function_body = ExpressionFunctionBody(
            provider   = provider,
            name       = name,
            doc        = None,
            parameters = ParameterSpec(
                name          = name,
                normal_args   = (".0",),
                list_star_arg = None,
                dict_star_arg = None,
                default_count = 0,
                kw_only_args  = ()
            ),
            flags      = set(),
            source_ref = source_ref
        )

        iter_tmp = function_body.getVariableForAssignment(
            variable_name = ".0"
        )
        assert iter_tmp.isParameterVariable()

    code_object = CodeObjectSpec(
        code_name     = name,
        code_kind     = "Generator" if emit_class is ExpressionYield else "Function",
        arg_names     = () if assign_provider else function_body.getParameters().getParameterNames(),
        kw_only_count = 0,
        has_starlist  = False,
        has_stardict  = False,
    )

    if emit_class is ExpressionYield:
        code_body = ExpressionGeneratorObjectBody(
            provider   = function_body,
            name       = "<genexpr>",
            flags      = set(),
            source_ref = source_ref
        )

        iter_tmp = code_body.getVariableForReference(
            variable_name = ".0"
        )
        assert iter_tmp.isLocalVariable()

        function_body.setBody(
            makeStatementsSequenceFromStatement(
                statement = StatementReturn(
                    expression = ExpressionMakeGeneratorObject(
                        generator_ref = ExpressionFunctionRef(
                            function_body = code_body,
                            source_ref    = source_ref
                        ),
                        code_object   = code_object,
                        source_ref    = source_ref
                    ),
                    source_ref = source_ref
                )
            )
        )
    else:
        code_body = function_body

    if start_value is not None:
        container_tmp = code_body.allocateTempVariable(
            temp_scope = None,
            name       = "contraction_result"
        )
    else:
        container_tmp = None

    statements, release_statements = _buildContractionBodyNode(
        function_body   = code_body,
        assign_provider = assign_provider,
        provider        = provider,
        node            = node,
        emit_class      = emit_class,
        iter_tmp        = iter_tmp,
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
            provider   = function_body,
            tried      = statements,
            final      = release_statements,
            source_ref = source_ref.atInternal()
        ),
    )

    code_body.setBody(
        makeStatementsSequenceFromStatement(
            statement = StatementsFrame(
                statements  = mergeStatements(statements, False),
                guard_mode  = "pass_through"
                                  if emit_class is not ExpressionYield else
                                "generator",
                code_object = code_object,
                source_ref  = source_ref
            )
        )
    )

    if not assign_provider:
        return ExpressionFunctionCall(
            function   = ExpressionFunctionCreation(
                function_ref = ExpressionFunctionRef(
                    function_body = function_body,
                    source_ref    = source_ref
                ),
                code_object  = code_object,
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
    else:
        return function_body
