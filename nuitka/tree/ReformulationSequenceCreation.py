#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Reformulation of sequence creations.

Sequences might be directly translated to constants, or they might become
nodes that build tuples, lists, or sets.

For Python3.5, unpacking can happen while creating sequences, these are
being re-formulated to an internal function.

Consult the Developer Manual for information. TODO: Add ability to sync
source code comments with Developer Manual sections.

"""

from nuitka.nodes.BuiltinIteratorNodes import ExpressionBuiltinIter1
from nuitka.nodes.BuiltinNextNodes import ExpressionBuiltinNext1
from nuitka.nodes.BuiltinTypeNodes import ExpressionBuiltinTuple
from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.ContainerMakingNodes import (
    makeExpressionMakeListOrConstant,
    makeExpressionMakeSetLiteralOrConstant,
    makeExpressionMakeTuple,
    makeExpressionMakeTupleOrConstant,
)
from nuitka.nodes.ContainerOperationNodes import ExpressionSetOperationUpdate
from nuitka.nodes.FunctionNodes import (
    ExpressionFunctionRef,
    makeExpressionFunctionCall,
    makeExpressionFunctionCreation,
)
from nuitka.nodes.ListOperationNodes import (
    ExpressionListOperationExtend,
    ExpressionListOperationExtendForUnpack,
)
from nuitka.nodes.LoopNodes import StatementLoop, StatementLoopBreak
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.StatementNodes import StatementExpressionOnly
from nuitka.nodes.VariableAssignNodes import makeStatementAssignmentVariable
from nuitka.nodes.VariableRefNodes import (
    ExpressionTempVariableRef,
    ExpressionVariableRef,
)
from nuitka.nodes.VariableReleaseNodes import makeStatementReleaseVariable
from nuitka.PythonVersions import python_version
from nuitka.specs.ParameterSpecs import ParameterSpec

from . import SyntaxErrors
from .InternalModule import (
    internal_source_ref,
    makeInternalHelperFunctionBody,
    once_decorator,
)
from .ReformulationTryExceptStatements import makeTryExceptSingleHandlerNode
from .ReformulationTryFinallyStatements import makeTryFinallyStatement
from .TreeHelpers import (
    buildNode,
    buildNodeTuple,
    getKind,
    makeStatementsSequenceFromStatement,
    makeStatementsSequenceFromStatements,
)


def _raiseStarredSyntaxError(element, source_ref):
    SyntaxErrors.raiseSyntaxError(
        "can use starred expression only as assignment target",
        source_ref.atColumnNumber(element.col_offset),
    )


def buildTupleCreationNode(provider, node, source_ref):
    if python_version >= 0x300:
        for element in node.elts:
            if getKind(element) == "Starred":
                if python_version < 0x350:
                    _raiseStarredSyntaxError(element, source_ref)
                else:
                    return buildTupleUnpacking(
                        provider=provider, elements=node.elts, source_ref=source_ref
                    )

    return makeExpressionMakeTupleOrConstant(
        elements=buildNodeTuple(provider, node.elts, source_ref),
        user_provided=True,
        source_ref=source_ref,
    )


def buildListCreationNode(provider, node, source_ref):
    if python_version >= 0x300:
        for element in node.elts:
            if getKind(element) == "Starred":
                if python_version < 0x350:
                    _raiseStarredSyntaxError(element, source_ref)
                else:
                    return buildListUnpacking(
                        provider=provider, elements=node.elts, source_ref=source_ref
                    )

    return makeExpressionMakeListOrConstant(
        elements=buildNodeTuple(provider, node.elts, source_ref),
        user_provided=True,
        source_ref=source_ref,
    )


def buildSetCreationNode(provider, node, source_ref):
    if python_version >= 0x300:
        for element in node.elts:
            if getKind(element) == "Starred":
                if python_version < 0x350:
                    _raiseStarredSyntaxError(element, source_ref)
                else:
                    return _buildSetUnpacking(
                        provider=provider, elements=node.elts, source_ref=source_ref
                    )

    return makeExpressionMakeSetLiteralOrConstant(
        elements=buildNodeTuple(provider, node.elts, source_ref),
        user_provided=True,
        source_ref=source_ref,
    )


@once_decorator
def getListUnpackingHelper():
    helper_name = "_unpack_list"

    result = makeInternalHelperFunctionBody(
        name=helper_name,
        parameters=ParameterSpec(
            ps_name=helper_name,
            ps_normal_args=(),
            ps_list_star_arg="args",
            ps_dict_star_arg=None,
            ps_default_count=0,
            ps_kw_only_args=(),
            ps_pos_only_args=(),
        ),
    )

    temp_scope = None

    tmp_result_variable = result.allocateTempVariable(temp_scope, "list")
    tmp_iter_variable = result.allocateTempVariable(temp_scope, "iter")
    tmp_item_variable = result.allocateTempVariable(temp_scope, "keys")

    if python_version < 0x390:
        list_operation_extend = ExpressionListOperationExtend
    else:
        list_operation_extend = ExpressionListOperationExtendForUnpack

    loop_body = makeStatementsSequenceFromStatements(
        makeTryExceptSingleHandlerNode(
            tried=makeStatementAssignmentVariable(
                variable=tmp_item_variable,
                source=ExpressionBuiltinNext1(
                    value=ExpressionTempVariableRef(
                        variable=tmp_iter_variable, source_ref=internal_source_ref
                    ),
                    source_ref=internal_source_ref,
                ),
                source_ref=internal_source_ref,
            ),
            exception_name="StopIteration",
            handler_body=StatementLoopBreak(source_ref=internal_source_ref),
            source_ref=internal_source_ref,
        ),
        StatementExpressionOnly(
            expression=list_operation_extend(
                list_arg=ExpressionTempVariableRef(
                    variable=tmp_result_variable, source_ref=internal_source_ref
                ),
                value=ExpressionTempVariableRef(
                    variable=tmp_item_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
    )

    args_variable = result.getVariableForAssignment(variable_name="args")

    final = (
        makeStatementReleaseVariable(
            variable=tmp_result_variable, source_ref=internal_source_ref
        ),
        makeStatementReleaseVariable(
            variable=tmp_iter_variable, source_ref=internal_source_ref
        ),
        makeStatementReleaseVariable(
            variable=tmp_item_variable, source_ref=internal_source_ref
        ),
    )

    tried = makeStatementsSequenceFromStatements(
        makeStatementAssignmentVariable(
            variable=tmp_iter_variable,
            source=ExpressionBuiltinIter1(
                value=ExpressionVariableRef(
                    variable=args_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
        makeStatementAssignmentVariable(
            variable=tmp_result_variable,
            source=makeConstantRefNode(constant=[], source_ref=internal_source_ref),
            source_ref=internal_source_ref,
        ),
        StatementLoop(loop_body=loop_body, source_ref=internal_source_ref),
        StatementReturn(
            expression=ExpressionTempVariableRef(
                variable=tmp_result_variable, source_ref=internal_source_ref
            ),
            source_ref=internal_source_ref,
        ),
    )

    result.setChildBody(
        makeStatementsSequenceFromStatement(
            makeTryFinallyStatement(
                provider=result,
                tried=tried,
                final=final,
                source_ref=internal_source_ref,
            )
        )
    )

    return result


@once_decorator
def getSetUnpackingHelper():
    helper_name = "_unpack_set"

    result = makeInternalHelperFunctionBody(
        name=helper_name,
        parameters=ParameterSpec(
            ps_name=helper_name,
            ps_normal_args=(),
            ps_list_star_arg="args",
            ps_dict_star_arg=None,
            ps_default_count=0,
            ps_kw_only_args=(),
            ps_pos_only_args=(),
        ),
    )

    temp_scope = None

    tmp_result_variable = result.allocateTempVariable(temp_scope, "set")
    tmp_iter_variable = result.allocateTempVariable(temp_scope, "iter")
    tmp_item_variable = result.allocateTempVariable(temp_scope, "keys")

    loop_body = makeStatementsSequenceFromStatements(
        makeTryExceptSingleHandlerNode(
            tried=makeStatementAssignmentVariable(
                variable=tmp_item_variable,
                source=ExpressionBuiltinNext1(
                    value=ExpressionTempVariableRef(
                        variable=tmp_iter_variable, source_ref=internal_source_ref
                    ),
                    source_ref=internal_source_ref,
                ),
                source_ref=internal_source_ref,
            ),
            exception_name="StopIteration",
            handler_body=StatementLoopBreak(source_ref=internal_source_ref),
            source_ref=internal_source_ref,
        ),
        StatementExpressionOnly(
            expression=ExpressionSetOperationUpdate(
                set_arg=ExpressionTempVariableRef(
                    variable=tmp_result_variable, source_ref=internal_source_ref
                ),
                value=ExpressionTempVariableRef(
                    variable=tmp_item_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
    )

    args_variable = result.getVariableForAssignment(variable_name="args")

    final = (
        makeStatementReleaseVariable(
            variable=tmp_result_variable, source_ref=internal_source_ref
        ),
        makeStatementReleaseVariable(
            variable=tmp_iter_variable, source_ref=internal_source_ref
        ),
        makeStatementReleaseVariable(
            variable=tmp_item_variable, source_ref=internal_source_ref
        ),
    )

    tried = makeStatementsSequenceFromStatements(
        makeStatementAssignmentVariable(
            variable=tmp_iter_variable,
            source=ExpressionBuiltinIter1(
                value=ExpressionVariableRef(
                    variable=args_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
        makeStatementAssignmentVariable(
            variable=tmp_result_variable,
            source=makeConstantRefNode(constant=set(), source_ref=internal_source_ref),
            source_ref=internal_source_ref,
        ),
        StatementLoop(loop_body=loop_body, source_ref=internal_source_ref),
        StatementReturn(
            expression=ExpressionTempVariableRef(
                variable=tmp_result_variable, source_ref=internal_source_ref
            ),
            source_ref=internal_source_ref,
        ),
    )

    result.setChildBody(
        makeStatementsSequenceFromStatement(
            makeTryFinallyStatement(
                provider=result,
                tried=tried,
                final=final,
                source_ref=internal_source_ref,
            )
        )
    )

    return result


def buildListUnpacking(provider, elements, source_ref):
    helper_args = []

    for element in elements:

        # We could be a lot cleverer about the tuples for non-starred
        # arguments, but lets get this to work first. And then rely on
        # future optimization to inline the list unpacking helper in a
        # way that has the same effect.
        if getKind(element) == "Starred":
            helper_args.append(buildNode(provider, element.value, source_ref))
        else:
            helper_args.append(
                makeExpressionMakeTupleOrConstant(
                    elements=(buildNode(provider, element, source_ref),),
                    user_provided=True,
                    source_ref=source_ref,
                )
            )

    result = makeExpressionFunctionCall(
        function=makeExpressionFunctionCreation(
            function_ref=ExpressionFunctionRef(
                function_body=getListUnpackingHelper(), source_ref=source_ref
            ),
            defaults=(),
            kw_defaults=None,
            annotations=None,
            source_ref=source_ref,
        ),
        values=(makeExpressionMakeTuple(tuple(helper_args), source_ref),),
        source_ref=source_ref,
    )

    result.setCompatibleSourceReference(helper_args[-1].getCompatibleSourceReference())

    return result


def buildTupleUnpacking(provider, elements, source_ref):
    return ExpressionBuiltinTuple(
        value=buildListUnpacking(provider, elements, source_ref), source_ref=source_ref
    )


def _buildSetUnpacking(provider, elements, source_ref):
    helper_args = []

    for element in elements:

        # We could be a lot cleverer about the tuples for non-starred
        # arguments, but lets get this to work first. And then rely on
        # future optimization to inline the list unpacking helper in a
        # way that has the same effect.
        if getKind(element) == "Starred":
            helper_args.append(buildNode(provider, element.value, source_ref))
        else:
            helper_args.append(
                makeExpressionMakeTupleOrConstant(
                    elements=(buildNode(provider, element, source_ref),),
                    user_provided=True,
                    source_ref=source_ref,
                )
            )

    result = makeExpressionFunctionCall(
        function=makeExpressionFunctionCreation(
            function_ref=ExpressionFunctionRef(
                function_body=getSetUnpackingHelper(), source_ref=source_ref
            ),
            defaults=(),
            kw_defaults=None,
            annotations=None,
            source_ref=source_ref,
        ),
        values=(makeExpressionMakeTuple(tuple(helper_args), source_ref),),
        source_ref=source_ref,
    )

    result.setCompatibleSourceReference(helper_args[-1].getCompatibleSourceReference())

    return result
