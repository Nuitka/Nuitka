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
""" Code generation for tuples.

Right now only the creation is done here. But more should be added later on.
"""

from .Identifiers import ConstantIdentifier
from . import CodeTemplates

# Take note of the MAKE_TUPLE variants actually used, but have EVAL_ORDER for
# 1..6 in any case, so we can use it in the C++ code freely without concern.
make_tuples_used = set( range( 1, 6 ) )

def addMakeTupleUse(value):
    assert type( value ) is int

    make_tuples_used.add( value )

def getTupleCreationCode(context, order_relevance, element_identifiers):
    if len( element_identifiers ) == 0:
        return ConstantIdentifier( "const_tuple_empty", () )

    from .OrderedEvaluation import getOrderRelevanceEnforcedArgsCode

    args_length = len( element_identifiers )
    addMakeTupleUse( args_length )

    return getOrderRelevanceEnforcedArgsCode(
        helper          = "MAKE_TUPLE%d" % args_length,
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "make_tuple",
        order_relevance = order_relevance,
        args            = element_identifiers,
        context         = context
    )

def getMakeTuplesCode():
    make_tuples_codes = []

    for arg_count in sorted( make_tuples_used ):
        add_elements_code = []

        for arg_index in range( arg_count ):
            add_elements_code.append(
                CodeTemplates.template_add_tuple_element_code % {
                    "tuple_index" : arg_index,
                    "tuple_value" : "element%d" % arg_index
                }
            )

        make_tuples_codes.append(
            CodeTemplates.template_make_tuple_function % {
                "argument_count"    : arg_count,
                "argument_decl"     : ", ".join(
                    "PyObject *element%d" % arg_index
                    for arg_index in
                    range( arg_count )
                ),
                "add_elements_code" : "\n".join( add_elements_code ),
            }
        )

    # TODO: Why is this not a helper function.
    return CodeTemplates.template_header_guard % {
        "header_guard_name" : "__NUITKA_TUPLES_H__",
        "header_body"       : "\n".join( make_tuples_codes )
    }
