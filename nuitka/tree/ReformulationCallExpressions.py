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
""" Reformulation of call expressions.

Consult the Developer Manual for information. TODO: Add ability to sync
source code comments with Developer Manual sections.

"""

from nuitka.nodes.CallNodes import makeExpressionCall
from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.ContainerMakingNodes import (
    makeExpressionMakeTuple,
    makeExpressionMakeTupleOrConstant,
)
from nuitka.nodes.DictionaryNodes import makeExpressionMakeDictOrConstant
from nuitka.nodes.FunctionNodes import (
    ExpressionFunctionCall,
    ExpressionFunctionCreation,
    ExpressionFunctionRef,
)
from nuitka.nodes.KeyValuePairNodes import makeExpressionPairs
from nuitka.nodes.OutlineNodes import ExpressionOutlineBody
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.VariableAssignNodes import makeStatementAssignmentVariable
from nuitka.nodes.VariableRefNodes import ExpressionTempVariableRef
from nuitka.PythonVersions import python_version

from .ComplexCallHelperFunctions import (
    getFunctionCallHelperDictionaryUnpacking,
    getFunctionCallHelperKeywordsStarDict,
    getFunctionCallHelperKeywordsStarList,
    getFunctionCallHelperKeywordsStarListStarDict,
    getFunctionCallHelperPosKeywordsStarDict,
    getFunctionCallHelperPosKeywordsStarList,
    getFunctionCallHelperPosKeywordsStarListStarDict,
    getFunctionCallHelperPosStarDict,
    getFunctionCallHelperPosStarList,
    getFunctionCallHelperPosStarListStarDict,
    getFunctionCallHelperStarDict,
    getFunctionCallHelperStarList,
    getFunctionCallHelperStarListStarDict,
)
from .ReformulationDictionaryCreation import buildDictionaryUnpackingArgs
from .ReformulationSequenceCreation import buildListUnpacking
from .TreeHelpers import (
    buildNode,
    buildNodeList,
    getKind,
    makeStatementsSequenceFromStatements,
)


def buildCallNode(provider, node, source_ref):
    called = buildNode(provider, node.func, source_ref)

    if python_version >= 0x350:
        list_star_arg = None
        dict_star_arg = None

    positional_args = []

    # For Python3.5 compatibility, the error handling with star argument last
    # is the old one, only with a starred argument before that, things use the
    # new unpacking code.
    for node_arg in node.args[:-1]:
        if getKind(node_arg) == "Starred":
            assert python_version >= 0x350
            list_star_arg = buildListUnpacking(provider, node.args, source_ref)
            positional_args = []
            break
    else:
        if node.args and getKind(node.args[-1]) == "Starred":
            assert python_version >= 0x350

            list_star_arg = buildNode(provider, node.args[-1].value, source_ref)
            positional_args = buildNodeList(provider, node.args[:-1], source_ref)
        else:
            positional_args = buildNodeList(provider, node.args, source_ref)

    # Only the values of keyword pairs have a real source ref, and those only
    # really matter, so that makes sense.
    keys = []
    values = []

    for keyword in node.keywords[:-1]:
        if keyword.arg is None:
            assert python_version >= 0x350

            outline_body = ExpressionOutlineBody(
                provider=provider, name="dict_unpacking_call", source_ref=source_ref
            )

            tmp_called = outline_body.allocateTempVariable(
                temp_scope=None, name="called"
            )

            helper_args = [
                ExpressionTempVariableRef(variable=tmp_called, source_ref=source_ref),
                makeExpressionMakeTuple(
                    elements=buildDictionaryUnpackingArgs(
                        provider=provider,
                        keys=(keyword.arg for keyword in node.keywords),
                        values=(keyword.value for keyword in node.keywords),
                        source_ref=source_ref,
                    ),
                    source_ref=source_ref,
                ),
            ]

            dict_star_arg = ExpressionFunctionCall(
                function=ExpressionFunctionCreation(
                    function_ref=ExpressionFunctionRef(
                        function_body=getFunctionCallHelperDictionaryUnpacking(),
                        source_ref=source_ref,
                    ),
                    defaults=(),
                    kw_defaults=None,
                    annotations=None,
                    source_ref=source_ref,
                ),
                values=helper_args,
                source_ref=source_ref,
            )

            outline_body.setChild(
                "body",
                makeStatementsSequenceFromStatements(
                    makeStatementAssignmentVariable(
                        variable=tmp_called, source=called, source_ref=source_ref
                    ),
                    StatementReturn(
                        expression=_makeCallNode(
                            called=ExpressionTempVariableRef(
                                variable=tmp_called, source_ref=source_ref
                            ),
                            positional_args=positional_args,
                            keys=keys,
                            values=values,
                            list_star_arg=list_star_arg,
                            dict_star_arg=dict_star_arg,
                            source_ref=source_ref,
                        ),
                        source_ref=source_ref,
                    ),
                ),
            )

            return outline_body

    # For Python3.5 compatibility, the error handling with star argument last
    # is the old one, only with a starred argument before that, things use the
    # new unpacking code.

    if node.keywords and node.keywords[-1].arg is None:
        assert python_version >= 0x350

        dict_star_arg = buildNode(provider, node.keywords[-1].value, source_ref)
        keywords = node.keywords[:-1]
    else:
        keywords = node.keywords

    for keyword in keywords:
        keys.append(
            makeConstantRefNode(
                constant=keyword.arg, source_ref=source_ref, user_provided=True
            )
        )
        values.append(buildNode(provider, keyword.value, source_ref))

    if python_version < 0x350:
        list_star_arg = buildNode(provider, node.starargs, source_ref, True)
        dict_star_arg = buildNode(provider, node.kwargs, source_ref, True)

    return _makeCallNode(
        called=called,
        positional_args=positional_args,
        keys=keys,
        values=values,
        list_star_arg=list_star_arg,
        dict_star_arg=dict_star_arg,
        source_ref=source_ref,
    )


def _makeCallNode(
    called, positional_args, keys, values, list_star_arg, dict_star_arg, source_ref
):
    # Many variables, but only to cover the many complex call cases.

    if list_star_arg is None and dict_star_arg is None:
        result = makeExpressionCall(
            called=called,
            args=makeExpressionMakeTupleOrConstant(
                elements=positional_args,
                user_provided=True,
                source_ref=source_ref,
            ),
            kw=makeExpressionMakeDictOrConstant(
                makeExpressionPairs(keys=keys, values=values),
                user_provided=True,
                source_ref=source_ref,
            ),
            source_ref=source_ref,
        )

        # Bug compatible line numbers before Python 3.8
        if python_version < 0x380:
            if values:
                result.setCompatibleSourceReference(
                    source_ref=values[-1].getCompatibleSourceReference()
                )
            elif positional_args:
                result.setCompatibleSourceReference(
                    source_ref=positional_args[-1].getCompatibleSourceReference()
                )

        return result
    else:
        # Dispatch to complex helper function for each case. These do
        # re-formulation of complex calls according to Developer Manual.

        key = (
            bool(positional_args),
            bool(keys),
            list_star_arg is not None,
            dict_star_arg is not None,
        )

        table = {
            (True, True, True, False): getFunctionCallHelperPosKeywordsStarList,
            (True, False, True, False): getFunctionCallHelperPosStarList,
            (False, True, True, False): getFunctionCallHelperKeywordsStarList,
            (False, False, True, False): getFunctionCallHelperStarList,
            (True, True, False, True): getFunctionCallHelperPosKeywordsStarDict,
            (True, False, False, True): getFunctionCallHelperPosStarDict,
            (False, True, False, True): getFunctionCallHelperKeywordsStarDict,
            (False, False, False, True): getFunctionCallHelperStarDict,
            (True, True, True, True): getFunctionCallHelperPosKeywordsStarListStarDict,
            (True, False, True, True): getFunctionCallHelperPosStarListStarDict,
            (False, True, True, True): getFunctionCallHelperKeywordsStarListStarDict,
            (False, False, True, True): getFunctionCallHelperStarListStarDict,
        }

        get_helper = table[key]

        helper_args = [called]

        if positional_args:
            helper_args.append(
                makeExpressionMakeTupleOrConstant(
                    elements=positional_args,
                    user_provided=True,
                    source_ref=source_ref,
                )
            )

        # Order of evaluation changed in Python3.5.
        if python_version >= 0x350 and list_star_arg is not None:
            helper_args.append(list_star_arg)

        if keys:
            helper_args.append(
                makeExpressionMakeDictOrConstant(
                    pairs=makeExpressionPairs(keys=keys, values=values),
                    user_provided=True,
                    source_ref=source_ref,
                )
            )

        # Order of evaluation changed in Python3.5.
        if python_version < 0x350 and list_star_arg is not None:
            helper_args.append(list_star_arg)

        if dict_star_arg is not None:
            helper_args.append(dict_star_arg)

        result = ExpressionFunctionCall(
            function=ExpressionFunctionCreation(
                function_ref=ExpressionFunctionRef(
                    function_body=get_helper(), source_ref=source_ref
                ),
                defaults=(),
                kw_defaults=None,
                annotations=None,
                source_ref=source_ref,
            ),
            values=helper_args,
            source_ref=source_ref,
        )

        # Bug compatible line numbers before Python 3.8
        if python_version < 0x380:
            result.setCompatibleSourceReference(
                source_ref=helper_args[-1].getCompatibleSourceReference()
            )

        return result
