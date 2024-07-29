#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Reformulation of dictionary creations.

Dictionary creations might be directly translated to constants, or they might
become nodes that build dictionaries.

For Python3.5, unpacking can happen while creating dictionaries, these are
being re-formulated to an internal function.

Consult the Developer Manual for information. TODO: Add ability to sync
source code comments with Developer Manual sections.

"""

from nuitka.nodes.AttributeNodes import makeExpressionAttributeLookup
from nuitka.nodes.BuiltinIteratorNodes import ExpressionBuiltinIter1
from nuitka.nodes.BuiltinNextNodes import ExpressionBuiltinNext1
from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.ContainerMakingNodes import makeExpressionMakeTuple
from nuitka.nodes.DictionaryNodes import (
    StatementDictOperationUpdate,
    makeExpressionMakeDict,
    makeExpressionMakeDictOrConstant,
)
from nuitka.nodes.ExceptionNodes import (
    ExpressionBuiltinMakeException,
    StatementRaiseException,
)
from nuitka.nodes.FunctionNodes import (
    ExpressionFunctionRef,
    makeExpressionFunctionCall,
    makeExpressionFunctionCreation,
)
from nuitka.nodes.KeyValuePairNodes import (
    makeExpressionKeyValuePair,
    makeExpressionKeyValuePairConstantKey,
    makeExpressionPairs,
)
from nuitka.nodes.LoopNodes import StatementLoop, StatementLoopBreak
from nuitka.nodes.OperatorNodes import makeBinaryOperationNode
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.TypeNodes import ExpressionBuiltinType1
from nuitka.nodes.VariableAssignNodes import makeStatementAssignmentVariable
from nuitka.nodes.VariableRefNodes import (
    ExpressionTempVariableRef,
    ExpressionVariableRef,
)
from nuitka.PythonVersions import python_version
from nuitka.specs.ParameterSpecs import ParameterSpec

from .InternalModule import (
    internal_source_ref,
    makeInternalHelperFunctionBody,
    once_decorator,
)
from .ReformulationTryExceptStatements import makeTryExceptSingleHandlerNode
from .ReformulationTryFinallyStatements import makeTryFinallyReleaseStatement
from .TreeHelpers import (
    buildNode,
    buildNodeTuple,
    makeStatementsSequenceFromStatement,
    makeStatementsSequenceFromStatements,
)


def buildDictionaryNode(provider, node, source_ref):
    if python_version >= 0x350:
        for key in node.keys:
            if key is None:
                return buildDictionaryUnpacking(
                    provider=provider,
                    keys=node.keys,
                    values=node.values,
                    source_ref=source_ref,
                )

    return makeExpressionMakeDictOrConstant(
        pairs=makeExpressionPairs(
            keys=buildNodeTuple(provider, node.keys, source_ref),
            values=buildNodeTuple(provider, node.values, source_ref),
        ),
        user_provided=True,
        source_ref=source_ref,
    )


@once_decorator
def getDictUnpackingHelper():
    helper_name = "_unpack_dict"

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

    tmp_result_variable = result.allocateTempVariable(
        temp_scope, "dict", temp_type="object"
    )
    tmp_iter_variable = result.allocateTempVariable(
        temp_scope, "iter", temp_type="object"
    )
    tmp_item_variable = result.allocateTempVariable(
        temp_scope, "keys", temp_type="object"
    )

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
        makeTryExceptSingleHandlerNode(
            tried=StatementDictOperationUpdate(
                dict_arg=ExpressionTempVariableRef(
                    variable=tmp_result_variable, source_ref=internal_source_ref
                ),
                value=ExpressionTempVariableRef(
                    variable=tmp_item_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            exception_name="AttributeError",
            handler_body=StatementRaiseException(
                exception_type=ExpressionBuiltinMakeException(
                    exception_name="TypeError",
                    args=(
                        makeBinaryOperationNode(
                            operator="Mod",
                            left=makeConstantRefNode(
                                constant="""\
'%s' object is not a mapping""",
                                source_ref=internal_source_ref,
                                user_provided=True,
                            ),
                            right=makeExpressionMakeTuple(
                                elements=(
                                    makeExpressionAttributeLookup(
                                        expression=ExpressionBuiltinType1(
                                            value=ExpressionTempVariableRef(
                                                variable=tmp_item_variable,
                                                source_ref=internal_source_ref,
                                            ),
                                            source_ref=internal_source_ref,
                                        ),
                                        attribute_name="__name__",
                                        source_ref=internal_source_ref,
                                    ),
                                ),
                                source_ref=internal_source_ref,
                            ),
                            source_ref=internal_source_ref,
                        ),
                    ),
                    for_raise=False,
                    source_ref=internal_source_ref,
                ),
                exception_value=None,
                exception_trace=None,
                exception_cause=None,
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
    )

    args_variable = result.getVariableForAssignment(variable_name="args")

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
            source=makeConstantRefNode(constant={}, source_ref=internal_source_ref),
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
            makeTryFinallyReleaseStatement(
                provider=result,
                tried=tried,
                variables=(
                    tmp_result_variable,
                    tmp_iter_variable,
                    tmp_item_variable,
                ),
                source_ref=internal_source_ref,
            )
        )
    )

    return result


def buildDictionaryUnpackingArgs(provider, keys, values, source_ref):
    result = []

    for key, value in zip(keys, values):
        # TODO: We could be a lot cleverer about the dictionaries for non-starred
        # arguments, but lets get this to work first.
        if key is None:
            result.append(buildNode(provider, value, source_ref))
        elif type(key) is str:
            result.append(
                makeExpressionMakeDict(
                    pairs=(
                        makeExpressionKeyValuePairConstantKey(
                            key=key,
                            value=buildNode(provider, value, source_ref),
                        ),
                    ),
                    source_ref=source_ref,
                )
            )
        else:
            result.append(
                makeExpressionMakeDict(
                    pairs=(
                        makeExpressionKeyValuePair(
                            key=buildNode(provider, key, source_ref),
                            value=buildNode(provider, value, source_ref),
                        ),
                    ),
                    source_ref=source_ref,
                )
            )

    return tuple(result)


def buildDictionaryUnpacking(provider, keys, values, source_ref):
    helper_args = buildDictionaryUnpackingArgs(provider, keys, values, source_ref)

    result = makeExpressionFunctionCall(
        function=makeExpressionFunctionCreation(
            function_ref=ExpressionFunctionRef(
                function_body=getDictUnpackingHelper(), source_ref=source_ref
            ),
            defaults=(),
            kw_defaults=None,
            annotations=None,
            source_ref=source_ref,
        ),
        values=(makeExpressionMakeTuple(helper_args, source_ref),),
        source_ref=source_ref,
    )

    result.setCompatibleSourceReference(helper_args[-1].getCompatibleSourceReference())

    return result


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
