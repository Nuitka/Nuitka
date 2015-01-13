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
""" Reformulation of lambda expressions.

Consult the developer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

from nuitka import Utils
from nuitka.nodes.AssignNodes import (
    StatementAssignmentVariable,
    StatementDelVariable
)
from nuitka.nodes.ComparisonNodes import ExpressionComparisonIsNOT
from nuitka.nodes.ConditionalNodes import StatementConditional
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.FunctionNodes import (
    ExpressionFunctionBody,
    ExpressionFunctionCreation,
    ExpressionFunctionRef
)
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.StatementNodes import StatementExpressionOnly, StatementsFrame
from nuitka.nodes.VariableRefNodes import (
    ExpressionTargetTempVariableRef,
    ExpressionTempVariableRef
)
from nuitka.nodes.YieldNodes import ExpressionYield

from .Helpers import (
    buildNode,
    buildNodeList,
    getKind,
    makeStatementsSequenceFromStatement,
    makeTryFinallyStatement,
    mergeStatements
)
from .ReformulationFunctionStatements import (
    buildParameterAnnotations,
    buildParameterKwDefaults,
    buildParameterSpec
)


def buildLambdaNode(provider, node, source_ref):
    assert getKind(node) == "Lambda"

    parameters = buildParameterSpec(provider, "<lambda>", node, source_ref)

    function_body = ExpressionFunctionBody(
        provider   = provider,
        name       = "<lambda>",
        doc        = None,
        parameters = parameters,
        source_ref = source_ref,
    )

    defaults = buildNodeList(provider, node.args.defaults, source_ref)
    kw_defaults = buildParameterKwDefaults(
        provider      = provider,
        node          = node,
        function_body = function_body,
        source_ref    = source_ref
    )

    body = buildNode(
        provider   = function_body,
        node       = node.body,
        source_ref = source_ref,
    )

    if function_body.isGenerator():
        if Utils.python_version < 270:
            tmp_return_value = function_body.allocateTempVariable(
                temp_scope = None,
                name       = "yield_return"
            )

            statements = (
                StatementAssignmentVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = tmp_return_value,
                        source_ref = source_ref,
                    ),
                    source       = body,
                    source_ref   = source_ref
                ),
                StatementConditional(
                    condition  = ExpressionComparisonIsNOT(
                        left       = ExpressionTempVariableRef(
                            variable   = tmp_return_value,
                            source_ref = source_ref,
                        ),
                        right      = ExpressionConstantRef(
                            constant   = None,
                            source_ref = source_ref
                        ),
                        source_ref = source_ref
                    ),
                    yes_branch = makeStatementsSequenceFromStatement(
                        statement = StatementExpressionOnly(
                            expression = ExpressionYield(
                                expression = ExpressionTempVariableRef(
                                    variable   = tmp_return_value,
                                    source_ref = source_ref,
                                ),
                                source_ref = source_ref
                            ),
                            source_ref = source_ref
                        )
                    ),
                    no_branch  = None,
                    source_ref = source_ref
                )
            )
            body = makeTryFinallyStatement(
                tried      = statements,
                final      = StatementDelVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = tmp_return_value,
                        source_ref = source_ref,
                    ),
                    tolerant     = True,
                    source_ref   = source_ref
                ),
                source_ref = source_ref
            )
        else:
            body = StatementExpressionOnly(
                expression = body,
                source_ref = source_ref
            )
    else:
        body = StatementReturn(
            expression = body,
            source_ref = source_ref
        )

    body = StatementsFrame(
        statements    = mergeStatements(
            (body,)
        ),
        guard_mode    = "generator" if function_body.isGenerator() else "full",
        var_names     = parameters.getCoArgNames(),
        arg_count     = parameters.getArgumentCount(),
        kw_only_count = parameters.getKwOnlyParameterCount(),
        has_starlist  = parameters.getStarListArgumentName() is not None,
        has_stardict  = parameters.getStarDictArgumentName() is not None,
        code_name     = "<lambda>",
        source_ref    = body.getSourceReference()
    )

    function_body.setBody(body)

    annotations = buildParameterAnnotations(provider, node, source_ref)

    return ExpressionFunctionCreation(
        function_ref = ExpressionFunctionRef(
            function_body = function_body,
            source_ref    = source_ref
        ),
        defaults     = defaults,
        kw_defaults  = kw_defaults,
        annotations  = annotations,
        source_ref   = source_ref
    )
