#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Code generation for dicts.

Right now only the creation is done here. But more should be added later on.
"""

from .OrderedEvaluation import getOrderRelevanceEnforcedArgsCode

def getDictionaryCreationCode( context, order_relevance, args_identifiers ):
    assert len( args_identifiers ) % 2 == 0

    args_length = len( args_identifiers ) // 2
    context.addMakeDictUse( args_length )

    return getOrderRelevanceEnforcedArgsCode(
        helper          = "MAKE_DICT%d" % args_length,
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "make_dict",
        order_relevance = order_relevance,
        args            = args_identifiers,
        context         = context
    )
