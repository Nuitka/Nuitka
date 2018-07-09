#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Reformulation of dictionary creations.

Dictionary creations might be directly translated to constants, or they might
become nodes that build dictionaries.

For Python3.5, unpacking can happen while creating dictionaries, these are
being re-formulated to an internal function.

Consult the developer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

from nuitka.nodes.AssignNodes import (
    StatementAssignmentVariable,
    StatementDelVariable,
    StatementReleaseVariable
)
from nuitka.nodes.AttributeNodes import ExpressionAttributeLookup
from nuitka.nodes.BuiltinIteratorNodes import ExpressionBuiltinIter1
from nuitka.nodes.BuiltinNextNodes import ExpressionBuiltinNext1
from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.ContainerMakingNodes import ExpressionMakeTuple
from nuitka.nodes.DictionaryNodes import (
    ExpressionKeyValuePair,
    ExpressionMakeDict,
    StatementDictOperationUpdate
)
from nuitka.nodes.ExceptionNodes import (
    ExpressionBuiltinMakeException,
    StatementRaiseException
)
from nuitka.nodes.FunctionNodes import (
    ExpressionFunctionBody,
    ExpressionFunctionCall,
    ExpressionFunctionCreation,
    ExpressionFunctionRef
)
from nuitka.nodes.LoopNodes import StatementLoop, StatementLoopBreak
from nuitka.nodes.OperatorNodes import makeBinaryOperationNode
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.TypeNodes import ExpressionBuiltinType1
from nuitka.nodes.VariableRefNodes import (
    ExpressionTempVariableRef,
    ExpressionVariableRef
)
from nuitka.PythonVersions import python_version
from nuitka.specs.ParameterSpecs import ParameterSpec

from .InternalModule import (
    getInternalModule,
    internal_source_ref,
    once_decorator
)
from .ReformulationTryExceptStatements import makeTryExceptSingleHandlerNode
from .ReformulationTryFinallyStatements import makeTryFinallyStatement
from .TreeHelpers import (
    buildNode,
    buildNodeList,
    makeDictCreationOrConstant,
    makeStatementsSequenceFromStatement,
    makeStatementsSequenceFromStatements
)


def buildDictionaryNode(provider, node, source_ref):
    if python_version >= 350:
        for key in node.keys:
            if key is None:
                return buildDictionaryUnpacking(
                    provider   = provider,
                    node       = node,
                    source_ref = source_ref
                )

    return makeDictCreationOrConstant(
        keys       = buildNodeList(provider, node.keys, source_ref),
        values     = buildNodeList(provider, node.values, source_ref),
        source_ref = source_ref
    )

@once_decorator
def getDictUnpackingHelper():
    helper_name = "_unpack_dict"

    result = ExpressionFunctionBody(
        provider   = getInternalModule(),
        name       = helper_name,
        doc        = None,
        parameters = ParameterSpec(
            ps_name          = helper_name,
            ps_normal_args   = (),
            ps_list_star_arg = "args",
            ps_dict_star_arg = None,
            ps_default_count = 0,
            ps_kw_only_args  = ()
        ),
        flags      = set(),
        source_ref = internal_source_ref
    )

    temp_scope = None

    tmp_result_variable = result.allocateTempVariable(temp_scope, "dict")
    tmp_iter_variable = result.allocateTempVariable(temp_scope, "iter")
    tmp_item_variable = result.allocateTempVariable(temp_scope, "keys")

    loop_body = makeStatementsSequenceFromStatements(
        makeTryExceptSingleHandlerNode(
            tried          = StatementAssignmentVariable(
                variable   = tmp_item_variable,
                source     = ExpressionBuiltinNext1(
                    value      = ExpressionTempVariableRef(
                        variable   = tmp_iter_variable,
                        source_ref = internal_source_ref
                    ),
                    source_ref = internal_source_ref
                ),
                source_ref = internal_source_ref
            ),
            exception_name = "StopIteration",
            handler_body   = StatementLoopBreak(
                source_ref = internal_source_ref
            ),
            source_ref     = internal_source_ref
        ),
        makeTryExceptSingleHandlerNode(
            tried          = StatementDictOperationUpdate(
                dict_arg   = ExpressionTempVariableRef(
                    variable   = tmp_result_variable,
                    source_ref = internal_source_ref
                ),
                value      = ExpressionTempVariableRef(
                    variable   = tmp_item_variable,
                    source_ref = internal_source_ref
                ),
                source_ref = internal_source_ref
            ),
            exception_name = "AttributeError",
            handler_body   = StatementRaiseException(
                exception_type  = ExpressionBuiltinMakeException(
                    exception_name = "TypeError",
                    args           = (
                        makeBinaryOperationNode(
                            operator   = "Mod",
                            left       =  makeConstantRefNode(
                                constant      = """\
'%s' object is not a mapping""",
                                source_ref    = internal_source_ref,
                                user_provided = True
                            ),
                            right      = ExpressionMakeTuple(
                                elements   = (
                                    ExpressionAttributeLookup(
                                        source         = ExpressionBuiltinType1(
                                            value      = ExpressionTempVariableRef(
                                                variable   = tmp_item_variable,
                                                source_ref = internal_source_ref
                                            ),
                                            source_ref = internal_source_ref
                                        ),
                                        attribute_name = "__name__",
                                        source_ref     = internal_source_ref
                                    ),
                                ),
                                source_ref = internal_source_ref
                            ),
                            source_ref = internal_source_ref
                        ),
                    ),
                    source_ref     = internal_source_ref
                ),
                exception_value = None,
                exception_trace = None,
                exception_cause = None,
                source_ref      = internal_source_ref
            ),
            source_ref     = internal_source_ref
        )
    )

    args_variable = result.getVariableForAssignment(
        variable_name = "args"
    )

    final = (
        StatementReleaseVariable(
            variable   = tmp_result_variable,
            source_ref = internal_source_ref
        ),
        StatementReleaseVariable(
            variable   = tmp_iter_variable,
            source_ref = internal_source_ref
        ),
        StatementReleaseVariable(
            variable   = tmp_item_variable,
            source_ref = internal_source_ref
        ),
        # We get handed our args responsibility.
        StatementDelVariable(
            variable   = args_variable,
            tolerant   = False,
            source_ref = internal_source_ref
        )
    )

    tried = makeStatementsSequenceFromStatements(
        StatementAssignmentVariable(
            variable   = tmp_iter_variable,
            source     = ExpressionBuiltinIter1(
                value      = ExpressionVariableRef(
                    variable   = args_variable,
                    source_ref = internal_source_ref
                ),
                source_ref = internal_source_ref
            ),
            source_ref = internal_source_ref
        ),
        StatementAssignmentVariable(
            variable   = tmp_result_variable,
            source     = makeConstantRefNode(
                constant   = {},
                source_ref = internal_source_ref
            ),
            source_ref = internal_source_ref
        ),
        StatementLoop(
            body       = loop_body,
            source_ref = internal_source_ref
        ),
        StatementReturn(
            expression = ExpressionTempVariableRef(
                variable   = tmp_result_variable,
                source_ref = internal_source_ref
            ),
            source_ref = internal_source_ref
        )
    )

    result.setBody(
        makeStatementsSequenceFromStatement(
            makeTryFinallyStatement(
                provider   = result,
                tried      = tried,
                final      = final,
                source_ref = internal_source_ref
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
            result.append(
                buildNode(provider, value, source_ref),
            )
        elif type(key) is str:
            result.append(
                ExpressionMakeDict(
                    pairs      = (
                        ExpressionKeyValuePair(
                            key        = makeConstantRefNode(
                                constant   = key,
                                source_ref = source_ref
                            ),
                            value      = buildNode(provider, value, source_ref),
                            source_ref = source_ref
                        ),
                    ),
                    source_ref = source_ref
                )
            )
        else:
            result.append(
                ExpressionMakeDict(
                    pairs      = (
                        ExpressionKeyValuePair(
                            key        = buildNode(provider, key, source_ref),
                            value      = buildNode(provider, value, source_ref),
                            source_ref = source_ref
                        ),
                    ),
                    source_ref = source_ref
                )
            )

    return result


def buildDictionaryUnpacking(provider, node, source_ref):
    helper_args = buildDictionaryUnpackingArgs(provider, node.keys, node.values, source_ref)

    result = ExpressionFunctionCall(
        function   = ExpressionFunctionCreation(
            function_ref = ExpressionFunctionRef(
                function_body = getDictUnpackingHelper(),
                source_ref    = source_ref
            ),
            code_object  = None,
            defaults     = (),
            kw_defaults  = None,
            annotations  = None,
            source_ref   = source_ref
        ),
        values     = (
            ExpressionMakeTuple(
                helper_args,
                source_ref
            ),
        ),
        source_ref = source_ref,
    )

    result.setCompatibleSourceReference(helper_args[-1].getCompatibleSourceReference())

    return result
