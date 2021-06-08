#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
    StatementAssignmentVariable,
    StatementReleaseVariable,
)
from nuitka.nodes.ComparisonNodes import ExpressionComparisonIsNot
from nuitka.nodes.ConditionalNodes import makeStatementConditional
from nuitka.nodes.ConstantRefNodes import ExpressionConstantNoneRef
from nuitka.nodes.FrameNodes import (
    StatementsFrameFunction,
    StatementsFrameGenerator,
)
from nuitka.nodes.FunctionNodes import (
    ExpressionFunctionCreation,
    ExpressionFunctionRef,
)
from nuitka.nodes.GeneratorNodes import (
    ExpressionGeneratorObjectBody,
    ExpressionMakeGeneratorObject,
)
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.StatementNodes import StatementExpressionOnly
from nuitka.nodes.VariableRefNodes import ExpressionTempVariableRef
from nuitka.nodes.YieldNodes import ExpressionYield
from nuitka.PythonVersions import python_version

from .ReformulationFunctionStatements import (
    buildFunctionWithParsing,
    buildParameterAnnotations,
    buildParameterKwDefaults,
)
from .ReformulationTryFinallyStatements import makeTryFinallyStatement
from .TreeHelpers import (
    buildNode,
    buildNodeList,
    detectFunctionBodyKind,
    getKind,
    makeStatementsSequenceFromStatement,
    mergeStatements,
)


def buildLambdaNode(provider, node, source_ref):
    # Many details to deal with, pylint: disable=too-many-locals

    assert getKind(node) == "Lambda"

    function_kind, flags = detectFunctionBodyKind(nodes=(node.body,))

    outer_body, function_body, code_object = buildFunctionWithParsing(
        provider=provider,
        function_kind=function_kind,
        name="<lambda>",
        function_doc=None,
        flags=flags,
        node=node,
        source_ref=source_ref,
    )

    if function_kind == "Function":
        code_body = function_body
    else:
        code_body = ExpressionGeneratorObjectBody(
            provider=function_body,
            name="<lambda>",
            code_object=code_object,
            flags=None,
            auto_release=None,
            source_ref=source_ref,
        )
        code_body.qualname_provider = provider

    if function_kind == "Generator":
        function_body.setChild(
            "body",
            makeStatementsSequenceFromStatement(
                statement=StatementReturn(
                    expression=ExpressionMakeGeneratorObject(
                        generator_ref=ExpressionFunctionRef(
                            function_body=code_body, source_ref=source_ref
                        ),
                        source_ref=source_ref,
                    ),
                    source_ref=source_ref,
                )
            ),
        )

    defaults = buildNodeList(provider, node.args.defaults, source_ref)
    kw_defaults = buildParameterKwDefaults(
        provider=provider, node=node, function_body=function_body, source_ref=source_ref
    )

    body = buildNode(provider=code_body, node=node.body, source_ref=source_ref)

    if function_kind == "Generator":
        if python_version < 0x270:
            tmp_return_value = code_body.allocateTempVariable(
                temp_scope=None, name="yield_return"
            )

            statements = (
                StatementAssignmentVariable(
                    variable=tmp_return_value, source=body, source_ref=source_ref
                ),
                makeStatementConditional(
                    condition=ExpressionComparisonIsNot(
                        left=ExpressionTempVariableRef(
                            variable=tmp_return_value, source_ref=source_ref
                        ),
                        right=ExpressionConstantNoneRef(source_ref=source_ref),
                        source_ref=source_ref,
                    ),
                    yes_branch=StatementExpressionOnly(
                        expression=ExpressionYield(
                            expression=ExpressionTempVariableRef(
                                variable=tmp_return_value, source_ref=source_ref
                            ),
                            source_ref=source_ref,
                        ),
                        source_ref=source_ref,
                    ),
                    no_branch=None,
                    source_ref=source_ref,
                ),
            )
            body = makeTryFinallyStatement(
                provider=provider,
                tried=statements,
                final=StatementReleaseVariable(
                    variable=tmp_return_value, source_ref=source_ref
                ),
                source_ref=source_ref,
            )
        else:
            body = StatementExpressionOnly(expression=body, source_ref=source_ref)
    else:
        body = StatementReturn(expression=body, source_ref=source_ref)

    if function_kind == "Generator":
        frame_class = StatementsFrameGenerator
    else:
        frame_class = StatementsFrameFunction

    body = frame_class(
        statements=mergeStatements((body,)),
        code_object=code_object,
        source_ref=body.getSourceReference(),
    )

    body = makeStatementsSequenceFromStatement(statement=body)

    code_body.setChild("body", body)

    annotations = buildParameterAnnotations(provider, node, source_ref)

    return ExpressionFunctionCreation(
        function_ref=ExpressionFunctionRef(
            function_body=outer_body, source_ref=source_ref
        ),
        defaults=defaults,
        kw_defaults=kw_defaults,
        annotations=annotations,
        source_ref=source_ref,
    )
