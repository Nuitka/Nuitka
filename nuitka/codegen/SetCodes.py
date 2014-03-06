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
""" Code generation for sets.

Right now only the creation is done here. But more should be added later on.
"""

from .Identifiers import ConstantIdentifier
from . import CodeTemplates

# Take note of the MAKE_SET element count variants actually used.
make_sets_used = set()

def addMakeSetUse(value):
    assert type( value ) is int

    make_sets_used.add( value )

def getSetCreationCode(context, order_relevance, element_identifiers):
    if len( element_identifiers ) == 0:
        return ConstantIdentifier( "_python_set_empty", set() )

    from .OrderedEvaluation import getOrderRelevanceEnforcedArgsCode

    args_length = len( element_identifiers )
    addMakeSetUse( args_length )

    return getOrderRelevanceEnforcedArgsCode(
        helper          = "MAKE_SET%d" % args_length,
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "make_set",
        order_relevance = order_relevance,
        args            = element_identifiers,
        context         = context
    )


def getMakeSetsCode():
    make_sets_codes = []

    for arg_count in sorted( make_sets_used ):
        add_elements_code = []

        for arg_index in range( arg_count ):
            add_elements_code.append(
                CodeTemplates.template_add_set_element_code % {
                    "set_value" : "element%d" % arg_index
                }
            )

        make_sets_codes.append(
            CodeTemplates.template_make_set_function % {
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
        "header_guard_name" : "__NUITKA_SETS_H__",
        "header_body"       : "\n".join( make_sets_codes )
    }
