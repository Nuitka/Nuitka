#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

Consult the Developer Manual for information. TODO: Add ability to sync
source code comments with Developer Manual sections.

"""

from nuitka.__past__ import intern
from nuitka.nodes.AsyncgenNodes import (
    ExpressionAsyncgenObjectBody,
    ExpressionMakeAsyncgenObject,
)
from nuitka.nodes.BuiltinIteratorNodes import (
    ExpressionAsyncIter,
    ExpressionAsyncNext,
    ExpressionBuiltinIter1,
)
from nuitka.nodes.BuiltinNextNodes import ExpressionBuiltinNext1
from nuitka.nodes.CodeObjectSpecs import CodeObjectSpec
from nuitka.nodes.ConditionalNodes import makeStatementConditional
from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.ContainerOperationNodes import (
    StatementListOperationAppend,
    StatementSetOperationAdd,
)
from nuitka.nodes.DictionaryNodes import (
    StatementDictOperationSet,
    StatementDictOperationSetKeyValue,
)
from nuitka.nodes.FrameNodes import (
    StatementsFrameFunction,
    StatementsFrameGenerator,
)
from nuitka.nodes.FunctionNodes import ExpressionFunctionRef
from nuitka.nodes.GeneratorNodes import (
    ExpressionGeneratorObjectBody,
    ExpressionMakeGeneratorObject,
    StatementGeneratorReturnNone,
)
from nuitka.nodes.LoopNodes import StatementLoop, StatementLoopBreak
from nuitka.nodes.NodeMakingHelpers import makeVariableRefNode
from nuitka.nodes.OutlineNodes import (
    ExpressionOutlineBody,
    ExpressionOutlineFunction,
)
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.StatementNodes import (
    StatementExpressionOnly,
    StatementsSequence,
)
from nuitka.nodes.VariableAssignNodes import makeStatementAssignmentVariable
from nuitka.nodes.VariableRefNodes import ExpressionTempVariableRef
from nuitka.nodes.VariableReleaseNodes import makeStatementReleaseVariable
from nuitka.nodes.YieldNodes import (
    ExpressionYield,
    ExpressionYieldFromWaitable,
)
from nuitka.PythonVersions import python_version

from .ReformulationAssignmentStatements import buildAssignmentStatements
from .ReformulationBooleanExpressions import makeAndNode
from .ReformulationTryExceptStatements import makeTryExceptSingleHandlerNode
from .ReformulationTryFinallyStatements import makeTryFinallyStatement
from .TreeHelpers import (
    buildNode,
    buildNodeList,
    detectFunctionBodyKind,
    getKind,
    makeStatementsSequenceFromStatement,
    makeStatementsSequenceFromStatements,
    mergeStatements,
)


def _makeIteratorCreation(provider, qual, for_asyncgen, source_ref):
    if getattr(qual, "is_async", 0):
        result = ExpressionAsyncIter(
            value=buildNode(provider=provider, node=qual.iter, source_ref=source_ref),
            source_ref=source_ref,
        )

        if not for_asyncgen or python_version < 0x370:
            result = ExpressionYieldFromWaitable(
                expression=result, source_ref=source_ref
            )

        return result
    else:
        return ExpressionBuiltinIter1(
            value=buildNode(provider=provider, node=qual.iter, source_ref=source_ref),
            source_ref=source_ref,
        )


def _makeIteratorNext(qual, iterator_ref, source_ref):
    if getattr(qual, "is_async", 0):
        return ExpressionYieldFromWaitable(
            expression=ExpressionAsyncNext(value=iterator_ref, source_ref=source_ref),
            source_ref=source_ref,
        )
    else:
        return ExpressionBuiltinNext1(value=iterator_ref, source_ref=source_ref)


def _getStopIterationName(qual):
    if getattr(qual, "is_async", 0):
        return "StopAsyncIteration"
    else:
        return "StopIteration"


def _buildPython2ListContraction(provider, node, source_ref):
    # The contraction nodes are reformulated to function bodies, with loops as
    # described in the Developer Manual. They use a lot of temporary names,
    # nested blocks, etc. and so a lot of variable names.

    # Note: The assign_provider is only to cover Python2 list contractions,
    # assigning one of the loop variables to the outside scope.
    function_body = ExpressionOutlineBody(
        provider=provider, name="list_contraction", source_ref=source_ref
    )

    iter_tmp = function_body.allocateTempVariable(temp_scope=None, name=".0")

    container_tmp = function_body.allocateTempVariable(
        temp_scope=None, name="contraction_result"
    )

    statements, release_statements = _buildContractionBodyNode(
        provider=provider,
        node=node,
        emit_class=StatementListOperationAppend,
        iter_tmp=iter_tmp,
        temp_scope=None,
        start_value=[],
        container_tmp=container_tmp,
        function_body=function_body,
        assign_provider=True,
        for_asyncgen=False,
        source_ref=source_ref,
    )

    return_statement = StatementReturn(
        expression=ExpressionTempVariableRef(
            variable=container_tmp, source_ref=source_ref
        ),
        source_ref=source_ref,
    )

    statement = makeTryFinallyStatement(
        provider=function_body,
        tried=mergeStatements((statements, return_statement)),
        final=release_statements,
        source_ref=source_ref.atInternal(),
    )

    function_body.setChildBody(makeStatementsSequenceFromStatement(statement=statement))

    return function_body


def buildListContractionNode(provider, node, source_ref):
    # List contractions are dealt with by general code.
    if python_version < 0x300:
        return _buildPython2ListContraction(
            provider=provider, node=node, source_ref=source_ref
        )

    return _buildContractionNode(
        provider=provider,
        node=node,
        name="<listcomp>",
        emit_class=StatementListOperationAppend,
        start_value=[],
        source_ref=source_ref,
    )


def buildSetContractionNode(provider, node, source_ref):
    # Set contractions are dealt with by general code.

    return _buildContractionNode(
        provider=provider,
        node=node,
        name="<setcontraction>",
        emit_class=StatementSetOperationAdd,
        start_value=set(),
        source_ref=source_ref,
    )


def buildDictContractionNode(provider, node, source_ref):
    # Dict contractions are dealt with by general code.

    return _buildContractionNode(
        provider=provider,
        node=node,
        name="<dictcontraction>",
        emit_class=StatementDictOperationSet
        if python_version < 0x380
        else StatementDictOperationSetKeyValue,
        start_value={},
        source_ref=source_ref,
    )


def buildGeneratorExpressionNode(provider, node, source_ref):
    # Generator expressions are dealt with by general code.

    assert getKind(node) == "GeneratorExp"

    function_body = ExpressionOutlineBody(
        provider=provider, name="genexpr", source_ref=source_ref
    )

    iter_tmp = function_body.allocateTempVariable(temp_scope=None, name=".0")

    parent_module = provider.getParentModule()

    code_object = CodeObjectSpec(
        co_name="<genexpr>",
        co_qualname=provider.getChildQualname("<genexpr>"),
        co_kind="Generator",
        co_varnames=(".0",),
        co_freevars=(),
        co_argcount=1,
        co_posonlyargcount=0,
        co_kwonlyargcount=0,
        co_has_starlist=False,
        co_has_stardict=False,
        co_filename=parent_module.getRunTimeFilename(),
        co_lineno=source_ref.getLineNumber(),
        future_spec=parent_module.getFutureSpec(),
    )

    is_async = any(getattr(qual, "is_async", 0) for qual in node.generators)

    # Some of the newly allowed stuff in 3.7 fails to set the async flag.
    if not is_async and python_version >= 0x370:
        is_async = detectFunctionBodyKind(nodes=node.generators)[0] in (
            "Asyncgen",
            "Coroutine",
        )

    if is_async:
        code_body = ExpressionAsyncgenObjectBody(
            provider=provider,
            name="<genexpr>",
            code_object=code_object,
            flags=None,
            auto_release=None,
            source_ref=source_ref,
        )

        maker_class = ExpressionMakeAsyncgenObject
    else:
        code_body = ExpressionGeneratorObjectBody(
            provider=provider,
            name="<genexpr>",
            code_object=code_object,
            flags=None,
            auto_release=None,
            source_ref=source_ref.atColumnNumber(node.col_offset + 1),
        )

        maker_class = ExpressionMakeGeneratorObject

    function_body.setChildBody(
        makeStatementsSequenceFromStatements(
            makeStatementAssignmentVariable(
                variable=iter_tmp,
                source=_makeIteratorCreation(
                    provider=provider,
                    qual=node.generators[0],
                    for_asyncgen=is_async,
                    source_ref=source_ref,
                ),
                source_ref=source_ref,
            ),
            makeTryFinallyStatement(
                provider=function_body,
                tried=StatementReturn(
                    expression=maker_class(
                        ExpressionFunctionRef(
                            function_body=code_body, source_ref=source_ref
                        ),
                        source_ref=source_ref,
                    ),
                    source_ref=source_ref,
                ),
                final=makeStatementReleaseVariable(
                    variable=iter_tmp, source_ref=source_ref
                ),
                source_ref=source_ref,
            ),
        )
    )

    statements, release_statements = _buildContractionBodyNode(
        provider=provider,
        node=node,
        emit_class=ExpressionYield,
        iter_tmp=iter_tmp,
        temp_scope=None,
        start_value=None,
        container_tmp=None,
        function_body=code_body,
        assign_provider=False,
        for_asyncgen=is_async,
        source_ref=source_ref,
    )

    if is_async:
        statements += (StatementGeneratorReturnNone(source_ref=source_ref),)

    statements = (
        makeTryFinallyStatement(
            provider=function_body,
            tried=statements,
            final=release_statements,
            source_ref=source_ref.atInternal(),
        ),
    )

    code_body.setChildBody(
        makeStatementsSequenceFromStatement(
            statement=StatementsFrameGenerator(
                statements=mergeStatements(statements, False),
                code_object=code_object,
                source_ref=source_ref,
            )
        )
    )

    return function_body


def _buildContractionBodyNode(
    provider,
    node,
    emit_class,
    start_value,
    container_tmp,
    iter_tmp,
    temp_scope,
    assign_provider,
    function_body,
    for_asyncgen,
    source_ref,
):

    # This uses lots of variables and branches. There is no good way
    # around that, and we deal with many cases, due to having generator
    # expressions sharing this code, pylint: disable=too-many-branches,too-many-locals

    # Note: The assign_provider is only to cover Python2 list contractions,
    # assigning one of the loop variables to the outside scope.

    tmp_variables = []
    if emit_class is not ExpressionYield:
        tmp_variables.append(iter_tmp)

    if container_tmp is not None:
        tmp_variables.append(container_tmp)

    statements = []

    # First assign the iterator if we are an outline.
    if assign_provider:
        statements.append(
            makeStatementAssignmentVariable(
                variable=iter_tmp,
                source=_makeIteratorCreation(
                    provider=provider,
                    qual=node.generators[0],
                    for_asyncgen=False,
                    source_ref=source_ref,
                ),
                source_ref=source_ref.atInternal(),
            )
        )

    if for_asyncgen and python_version >= 0x370 and node.generators[0].is_async:
        statements.append(
            makeStatementAssignmentVariable(
                variable=iter_tmp,
                source=ExpressionTempVariableRef(
                    variable=iter_tmp, source_ref=source_ref
                ),
                source_ref=source_ref,
            )
        )

    if start_value is not None:
        statements.append(
            makeStatementAssignmentVariable(
                variable=container_tmp,
                source=makeConstantRefNode(constant=start_value, source_ref=source_ref),
                source_ref=source_ref.atInternal(),
            )
        )

    if hasattr(node, "elt"):
        if start_value is not None:
            current_body = emit_class(
                ExpressionTempVariableRef(
                    variable=container_tmp, source_ref=source_ref
                ),
                buildNode(
                    provider=function_body if not assign_provider else provider,
                    node=node.elt,
                    source_ref=source_ref,
                ),
                source_ref=source_ref,
            )
        else:
            assert emit_class is ExpressionYield

            current_body = emit_class(
                buildNode(provider=function_body, node=node.elt, source_ref=source_ref),
                source_ref=source_ref,
            )
    else:
        current_body = emit_class(
            dict_arg=ExpressionTempVariableRef(
                variable=container_tmp, source_ref=source_ref
            ),
            key=buildNode(
                provider=function_body if not assign_provider else provider,
                node=node.key,
                source_ref=source_ref,
            ),
            value=buildNode(
                provider=function_body if not assign_provider else provider,
                node=node.value,
                source_ref=source_ref,
            ),
            source_ref=source_ref,
        )

    if current_body.isExpression():
        current_body = StatementExpressionOnly(
            expression=current_body, source_ref=source_ref
        )

    for count, qual in enumerate(reversed(node.generators)):
        tmp_value_variable = function_body.allocateTempVariable(
            temp_scope=temp_scope, name="iter_value_%d" % count
        )

        tmp_variables.append(tmp_value_variable)

        # The first iterated value is to be calculated outside of the function
        # and will be given as a parameter "_iterated", the others are built
        # inside the function.

        if qual is node.generators[0]:
            iterator_ref = makeVariableRefNode(variable=iter_tmp, source_ref=source_ref)

            if for_asyncgen and python_version >= 0x370:
                iterator_ref = ExpressionYieldFromWaitable(
                    expression=iterator_ref, source_ref=source_ref
                )

            tmp_iter_variable = None

            nested_statements = []
        else:
            # First create the iterator and store it, next should be loop body
            value_iterator = _makeIteratorCreation(
                provider=provider if assign_provider else function_body,
                qual=qual,
                for_asyncgen=False,
                source_ref=source_ref,
            )

            tmp_iter_variable = function_body.allocateTempVariable(
                temp_scope=temp_scope, name="contraction_iter_%d" % count
            )

            tmp_variables.append(tmp_iter_variable)

            nested_statements = [
                makeStatementAssignmentVariable(
                    variable=tmp_iter_variable,
                    source=value_iterator,
                    source_ref=source_ref,
                )
            ]

            iterator_ref = ExpressionTempVariableRef(
                variable=tmp_iter_variable, source_ref=source_ref
            )

        loop_statements = [
            makeTryExceptSingleHandlerNode(
                tried=makeStatementAssignmentVariable(
                    variable=tmp_value_variable,
                    source=_makeIteratorNext(
                        iterator_ref=iterator_ref, qual=qual, source_ref=source_ref
                    ),
                    source_ref=source_ref,
                ),
                exception_name=_getStopIterationName(qual),
                handler_body=StatementLoopBreak(source_ref=source_ref),
                source_ref=source_ref,
            ),
            buildAssignmentStatements(
                provider=provider if assign_provider else function_body,
                temp_provider=function_body,
                node=qual.target,
                source=ExpressionTempVariableRef(
                    variable=tmp_value_variable, source_ref=source_ref
                ),
                source_ref=source_ref,
            ),
        ]

        conditions = buildNodeList(
            provider=provider if assign_provider else function_body,
            nodes=qual.ifs,
            source_ref=source_ref,
        )

        if len(conditions) >= 1:
            loop_statements.append(
                makeStatementConditional(
                    condition=makeAndNode(values=conditions, source_ref=source_ref),
                    yes_branch=current_body,
                    no_branch=None,
                    source_ref=source_ref,
                )
            )
        else:
            loop_statements.append(current_body)

        nested_statements.append(
            StatementLoop(
                loop_body=StatementsSequence(
                    statements=mergeStatements(loop_statements), source_ref=source_ref
                ),
                source_ref=source_ref,
            )
        )

        if tmp_iter_variable is not None:
            nested_statements.append(
                makeStatementReleaseVariable(
                    variable=tmp_iter_variable, source_ref=source_ref
                )
            )

        current_body = StatementsSequence(
            statements=mergeStatements(nested_statements, False), source_ref=source_ref
        )

    statements.append(current_body)
    statements = mergeStatements(statements)

    release_statements = tuple(
        makeStatementReleaseVariable(variable=tmp_variable, source_ref=source_ref)
        for tmp_variable in tmp_variables
    )

    return statements, release_statements


def _buildContractionNode(provider, node, name, emit_class, start_value, source_ref):
    # The contraction nodes are reformulated to function bodies, with loops as
    # described in the Developer Manual. They use a lot of temporary names,
    # nested blocks, etc. and so a lot of variable names, pylint:disable=too-many-locals

    function_body = ExpressionOutlineFunction(
        provider=provider, name=intern(name[1:-1]), source_ref=source_ref
    )

    iter_tmp = function_body.allocateTempVariable(temp_scope=None, name=".0")

    container_tmp = function_body.allocateTempVariable(
        temp_scope=None, name="contraction"
    )

    statements, release_statements = _buildContractionBodyNode(
        provider=provider,
        node=node,
        emit_class=emit_class,
        iter_tmp=iter_tmp,
        temp_scope=None,
        start_value=start_value,
        container_tmp=container_tmp,
        function_body=function_body,
        assign_provider=False,
        for_asyncgen=False,
        source_ref=source_ref,
    )

    assign_iter_statement = makeStatementAssignmentVariable(
        source=_makeIteratorCreation(
            provider=provider,
            qual=node.generators[0],
            for_asyncgen=False,
            source_ref=source_ref,
        ),
        variable=iter_tmp,
        source_ref=source_ref,
    )

    return_statement = StatementReturn(
        expression=ExpressionTempVariableRef(
            variable=container_tmp, source_ref=source_ref
        ),
        source_ref=source_ref,
    )

    statements = (
        makeTryFinallyStatement(
            provider=function_body,
            tried=mergeStatements((statements, return_statement)),
            final=release_statements,
            source_ref=source_ref.atInternal(),
        ),
    )

    if python_version < 0x300:
        body = makeStatementsSequenceFromStatements(assign_iter_statement, statements)
    else:
        parent_module = provider.getParentModule()

        code_object = CodeObjectSpec(
            co_name=name,
            co_qualname=provider.getChildQualname(name),
            co_kind="Function",
            co_varnames=(),
            co_freevars=(),
            co_argcount=1,
            co_posonlyargcount=0,
            co_kwonlyargcount=0,
            co_has_starlist=False,
            co_has_stardict=False,
            co_filename=parent_module.getRunTimeFilename(),
            co_lineno=source_ref.getLineNumber(),
            future_spec=parent_module.getFutureSpec(),
        )

        body = makeStatementsSequenceFromStatements(
            assign_iter_statement,
            StatementsFrameFunction(
                statements=mergeStatements(statements, False),
                code_object=code_object,
                source_ref=source_ref,
            ),
        )

    function_body.setChildBody(body)

    return function_body
