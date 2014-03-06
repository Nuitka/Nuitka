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
""" Code generation for calls.

The different kinds of calls get dedicated code. Most notable, calls with
only positional arguments, are attempted through helpers that might be
able to execute them without creating the argument dictionary at all.

"""

from . import CodeTemplates

from .Identifiers import Identifier

def getCallCodeNoArgs(called_identifier):
    return Identifier(
        "CALL_FUNCTION_NO_ARGS( %(function)s )" % {
            "function" : called_identifier.getCodeTemporaryRef(),
        },
        1
    )

# Outside helper code relies on some quick call to be present.
quick_calls_used = set( [ 1, 2, 3 ] )

def getCallCodePosArgsQuick(context, order_relevance, called_identifier,
                            arguments ):

    arg_size = len( arguments )
    quick_calls_used.add( arg_size )

    from .TupleCodes import addMakeTupleUse
    addMakeTupleUse( arg_size )

    from .OrderedEvaluation import getOrderRelevanceEnforcedArgsCode

    return getOrderRelevanceEnforcedArgsCode(
        helper          = "CALL_FUNCTION_WITH_ARGS%d" % arg_size,
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "call",
        order_relevance = order_relevance,
        args            = [ called_identifier ] + arguments,
        context         = context
    )


def getCallCodePosArgs(context, order_relevance, called_identifier,
                       argument_tuple ):
    from .OrderedEvaluation import getOrderRelevanceEnforcedArgsCode

    return getOrderRelevanceEnforcedArgsCode(
        helper          = "CALL_FUNCTION_WITH_POSARGS",
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "call",
        order_relevance = order_relevance,
        args            = ( called_identifier, argument_tuple ),
        context         = context
    )

def getCallCodeKeywordArgs(context, order_relevance, called_identifier,
                           argument_dictionary):
    from .OrderedEvaluation import getOrderRelevanceEnforcedArgsCode

    return getOrderRelevanceEnforcedArgsCode(
        helper          = "CALL_FUNCTION_WITH_KEYARGS",
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "call",
        order_relevance = order_relevance,
        args            = ( called_identifier, argument_dictionary ),
        context         = context
    )

def getCallCodePosKeywordArgs(context, order_relevance, called_identifier,
                              argument_tuple, argument_dictionary):
    from .OrderedEvaluation import getOrderRelevanceEnforcedArgsCode

    return getOrderRelevanceEnforcedArgsCode(
        helper          = "CALL_FUNCTION",
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "call",
        order_relevance = order_relevance,
        args            = (
            called_identifier,
            argument_tuple,
            argument_dictionary
        ),
        context         = context
    )

def getCallsDecls():
    result = []

    for quick_call_used in sorted(quick_calls_used):
        args_decl = [
            "PyObject *arg%d" % d
            for d in range(quick_call_used)
        ]

        result.append(
            CodeTemplates.template_call_function_with_args_decl % {
                "args_decl"  : ", ".join(args_decl),
                "args_count" : quick_call_used
            }
        )

    return CodeTemplates.template_header_guard % {
        "header_guard_name" : "__NUITKA_CALLS_H__",
        "header_body"       : "\n".join(result)
    }


def getCallsCode():
    result = []

    result.append(
        CodeTemplates.template_helper_impl_decl % {}
    )

    result.append(
        CodeTemplates.template_call_cpython_function_fast_impl % {}
    )

    for quick_call_used in sorted( quick_calls_used ):
        args_decl = [
            "PyObject *arg%d" % d
            for d in range(1, quick_call_used + 1)
        ]
        args_list = [
            "arg%d" % d
            for d in range(1, quick_call_used + 1)
        ]

        result.append(
            CodeTemplates.template_call_function_with_args_impl % {
                "args_decl"  : ", ".join(args_decl),
                "args_list"  : ", ".join(args_list),
                "args_count" : quick_call_used
            }
        )

    return "\n".join(result)
