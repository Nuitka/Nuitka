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
""" Reformulation of lambda expressions.

Consult the developer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

from nuitka.nodes.AssignNodes import (
    ExpressionTargetTempVariableRef,
    ExpressionTempVariableRef,
    StatementAssignmentVariable,
    StatementReleaseVariable
)
from nuitka.nodes.ComparisonNodes import ExpressionComparisonIsNOT
from nuitka.nodes.ConditionalNodes import StatementConditional
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.FrameNodes import StatementsFrame
from nuitka.nodes.FunctionNodes import (
    ExpressionFunctionCreation,
    ExpressionFunctionRef
)
from nuitka.nodes.GeneratorNodes import (
    ExpressionGeneratorObjectBody,
    ExpressionMakeGeneratorObject
)
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.StatementNodes import StatementExpressionOnly
from nuitka.nodes.YieldNodes import ExpressionYield
from nuitka.PythonVersions import python_version

from .Helpers import (
    buildNode,
    buildNodeList,
    detectFunctionBodyKind,
    getKind,
    makeStatementsSequenceFromStatement,
    mergeStatements
)
from .ReformulationFunctionStatements import (
    buildFunctionWithParsing,
    buildParameterAnnotations,
    buildParameterKwDefaults
)
from .ReformulationTryFinallyStatements import makeTryFinallyStatement


def buildLambdaNode(provider, node, source_ref):
    # Many details to deal with, pylint: disable=R0914

    assert getKind(node) == "Lambda"

    function_kind, flags, _written_variables, _non_local_declarations, _global_declarations = \
      detectFunctionBodyKind(
        nodes = (node.body,)
    )

    outer_body, function_body, code_object = buildFunctionWithParsing(
        provider      = provider,
        function_kind = function_kind,
        name          = "<lambda>",
        function_doc  = None,
        flags         = flags,
        node          = node,
        source_ref    = source_ref
    )

    if function_kind == "Function":
        code_body = function_body
    else:
        code_body = ExpressionGeneratorObjectBody(
            provider   = function_body,
            name       = "<lambda>",
            flags      = set(),
            source_ref = source_ref
        )

    if function_kind == "Generator":
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

    defaults = buildNodeList(provider, node.args.defaults, source_ref)
    kw_defaults = buildParameterKwDefaults(
        provider      = provider,
        node          = node,
        function_body = function_body,
        source_ref    = source_ref
    )

    body = buildNode(
        provider   = code_body,
        node       = node.body,
        source_ref = source_ref,
    )

    if function_kind == "Generator":
        if python_version < 270:
            tmp_return_value = code_body.allocateTempVariable(
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
                provider   = provider,
                tried      = statements,
                final      = StatementReleaseVariable(
                    variable   = tmp_return_value,
                    source_ref = source_ref
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
        statements  = mergeStatements(
            (body,)
        ),
        code_object = code_object,
        guard_mode  = "generator" if function_kind == "Generator" else "full",
        source_ref  = body.getSourceReference()
    )


    body = makeStatementsSequenceFromStatement(
        statement = body,
    )

    code_body.setBody(body)

    annotations = buildParameterAnnotations(provider, node, source_ref)

    return ExpressionFunctionCreation(
        function_ref = ExpressionFunctionRef(
            function_body = outer_body,
            source_ref    = source_ref
        ),
        code_object  = code_object,
        defaults     = defaults,
        kw_defaults  = kw_defaults,
        annotations  = annotations,
        source_ref   = source_ref
    )
