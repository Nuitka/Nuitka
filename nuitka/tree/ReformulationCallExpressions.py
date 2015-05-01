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
""" Reformulation of call expressions.

Consult the developer manual for information. TODO: Add ability to sync
source code comments with developer manual sections.

"""

from nuitka.nodes.CallNodes import makeExpressionCall
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.FunctionNodes import (
    ExpressionFunctionCall,
    ExpressionFunctionCreation,
    ExpressionFunctionRef
)

from .Helpers import (
    buildNode,
    buildNodeList,
    makeDictCreationOrConstant,
    makeSequenceCreationOrConstant
)


def buildCallNode(provider, node, source_ref):
    positional_args = buildNodeList(provider, node.args, source_ref)

    # Only the values of keyword pairs have a real source ref, and those only
    # really matter, so that makes sense.
    keys = []
    values = []

    for keyword in node.keywords:
        keys.append(
            ExpressionConstantRef(
                constant      = keyword.arg,
                source_ref    = source_ref,
                user_provided = True
            )
        )
        values.append(
            buildNode(provider, keyword.value, source_ref)
        )

    list_star_arg = buildNode(provider, node.starargs, source_ref, True)
    dict_star_arg = buildNode(provider, node.kwargs, source_ref, True)

    return _makeCallNode(
        called          = buildNode(provider, node.func, source_ref),
        positional_args = positional_args,
        keys            = keys,
        values          = values,
        list_star_arg   = list_star_arg,
        dict_star_arg   = dict_star_arg,
        source_ref      = source_ref,
    )


def _makeCallNode(called, positional_args, keys, values, list_star_arg,
                  dict_star_arg, source_ref):
    # Many variables, but only to cover the many complex call cases.
    # pylint: disable=R0914

    if list_star_arg is None and dict_star_arg is None:
        result = makeExpressionCall(
            called     = called,
            args       = makeSequenceCreationOrConstant(
                sequence_kind = "tuple",
                elements      = positional_args,
                source_ref    = source_ref
            ),
            kw         = makeDictCreationOrConstant(
                keys       = keys,
                values     = values,
                lazy_order = True,
                source_ref = source_ref
            ),
            source_ref = source_ref,
        )

        if values:
            result.setCompatibleSourceReference(
                source_ref = values[-1].getCompatibleSourceReference()
            )
        elif positional_args:
            result.setCompatibleSourceReference(
                source_ref = positional_args[-1].getCompatibleSourceReference()
            )

        return result
    else:
        # Dispatch to complex helper function for each case. These do
        # re-formulation of complex calls according to developer manual.

        key = (
            len(positional_args) > 0,
            len(keys) > 0,
            list_star_arg is not None,
            dict_star_arg is not None
        )

        from .ComplexCallHelperFunctions import (
            getFunctionCallHelperPosKeywordsStarList,
            getFunctionCallHelperPosStarList,
            getFunctionCallHelperKeywordsStarList,
            getFunctionCallHelperStarList,
            getFunctionCallHelperPosKeywordsStarDict,
            getFunctionCallHelperPosStarDict,
            getFunctionCallHelperKeywordsStarDict,
            getFunctionCallHelperStarDict,
            getFunctionCallHelperPosKeywordsStarListStarDict,
            getFunctionCallHelperPosStarListStarDict,
            getFunctionCallHelperKeywordsStarListStarDict,
            getFunctionCallHelperStarListStarDict,
        )

        table = {
            (True,   True,  True, False) :
                getFunctionCallHelperPosKeywordsStarList,
            (True,  False,  True, False) :
                getFunctionCallHelperPosStarList,
            (False,   True,  True, False) :
                getFunctionCallHelperKeywordsStarList,
            (False,  False,  True, False) :
                getFunctionCallHelperStarList,
            (True,   True, False,  True) :
                getFunctionCallHelperPosKeywordsStarDict,
            (True,  False, False,  True) :
                getFunctionCallHelperPosStarDict,
            (False,   True, False,  True) :
                getFunctionCallHelperKeywordsStarDict,
            (False,  False, False,  True) :
                getFunctionCallHelperStarDict,
            (True,   True,  True,  True) :
                getFunctionCallHelperPosKeywordsStarListStarDict,
            (True,  False,  True,  True) :
                getFunctionCallHelperPosStarListStarDict,
            (False,   True,  True,  True) :
                getFunctionCallHelperKeywordsStarListStarDict,
            (False,  False,  True,  True) :
                getFunctionCallHelperStarListStarDict,
        }

        get_helper = table[ key ]

        helper_args = [called]

        if positional_args:
            helper_args.append(
                makeSequenceCreationOrConstant(
                    sequence_kind = "tuple",
                    elements      = positional_args,
                    source_ref    = source_ref
                )
            )

        if keys:
            helper_args.append(
                makeDictCreationOrConstant(
                    keys       = keys,
                    values     = values,
                    lazy_order = True,
                    source_ref = source_ref
                )
            )

        if list_star_arg is not None:
            helper_args.append(list_star_arg)

        if dict_star_arg is not None:
            helper_args.append(dict_star_arg)

        result = ExpressionFunctionCall(
            function   = ExpressionFunctionCreation(
                function_ref = ExpressionFunctionRef(
                    function_body = get_helper(),
                    source_ref    = source_ref
                ),
                defaults     = (),
                kw_defaults  = None,
                annotations  = None,
                source_ref   = source_ref
            ),
            values     = helper_args,
            source_ref = source_ref,
        )

        result.setCompatibleSourceReference(
            source_ref = helper_args[-1].getCompatibleSourceReference()
        )

        return result
