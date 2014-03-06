#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

from . import CodeTemplates

make_dicts_used = set( range( 0, 3 ) )

def addMakeDictUse(args_length):
    assert type( args_length ) is int

    make_dicts_used.add( args_length )

def getDictionaryCreationCode(context, order_relevance, args_identifiers):
    from .OrderedEvaluation import getOrderRelevanceEnforcedArgsCode

    assert len( args_identifiers ) % 2 == 0

    args_length = len( args_identifiers ) // 2
    addMakeDictUse( args_length )

    return getOrderRelevanceEnforcedArgsCode(
        helper          = "MAKE_DICT%d" % args_length,
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "make_dict",
        order_relevance = order_relevance,
        args            = args_identifiers,
        context         = context
    )

def getMakeDictsCode():
    make_dicts_codes = []

    for arg_count in sorted( make_dicts_used ):
        add_elements_code = []

        for arg_index in range( arg_count ):
            add_elements_code.append(
                CodeTemplates.template_add_dict_element_code % {
                    "dict_key"   : "key%d" % ( arg_index + 1 ),
                    "dict_value" : "value%d" % ( arg_index + 1 )
                }
            )

        make_dicts_codes.append(
            CodeTemplates.template_make_dict_function % {
                "pair_count"        : arg_count,
                "argument_decl"     : ", ".join(
                    "PyObject *value%(index)d, PyObject *key%(index)d" % {
                        "index" : (arg_index+1)
                    }
                    for arg_index in
                    range( arg_count )
                ),
                "add_elements_code" : "\n".join( add_elements_code ),
            }
        )

    return CodeTemplates.template_header_guard % {
        "header_guard_name" : "__NUITKA_DICTS_H__",
        "header_body"       : "\n".join( make_dicts_codes )
    }
