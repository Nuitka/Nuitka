#     Copyright 2012, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Optimize calls to function bodies.

This works via the call registry. For function bodies called, we check that it's not a star
argument call, which we wouldn't know how to safely handle (yet) and then we transform it
to a dedicated function call node.
"""

from .registry import CallRegistry

from nuitka.nodes.NodeMakingHelpers import makeRaiseExceptionReplacementExpressionFromInstance

from nuitka.nodes.ParameterSpec import TooManyArguments, matchCall

from nuitka.nodes.CallNode import CPythonExpressionCall

from nuitka.nodes.FunctionNodes import (
    CPythonExpressionFunctionBody,
    CPythonExpressionFunctionCall
)

from nuitka.__past__ import iterItems

def computeOwnedFunctionCall( call_node, function_body ):

    # We can't handle these yet. TODO: In principle, if e.g. the called function node takes
    # only those, we could in fact do more, but that's off limits for now.
    if call_node.getStarListArg() is not None or call_node.getStarDictArg() is not None:
        return None

    # TODO: Until we have something to re-order the arguments, we need to skip this. For
    # the immediate need, we avoid this complexity.
    if call_node.getNamedArgumentPairs():
        return None

    call_spec = function_body.getParameters()

    try:
        args_dict = matchCall(
            func_name     = function_body.getName(),
            args          = call_spec.getArgumentNames(),
            star_list_arg = call_spec.getStarListArgumentName(),
            star_dict_arg = call_spec.getStarDictArgumentName(),
            num_defaults  = call_spec.getDefaultCount(),
            positional    = call_node.getPositionalArguments(),
            pairs         = ()
        )

        values = []

        for positional_arg in call_node.getPositionalArguments():
            for _arg_name, arg_value in iterItems( args_dict ):
                if arg_value is positional_arg:
                    values.append( arg_value )

        result = CPythonExpressionFunctionCall(
            function_body = function_body,
            values        = values,
            source_ref    = call_node.getSourceReference()
        )


        return (
            result,
            "new_statements", # TODO: More appropiate tag maybe.
            "Replaced call to created function body '%s' with direct function call" % function_body.getName()
        )

    except TooManyArguments as e:
        return CPythonExpressionCall(
            called          = makeRaiseExceptionReplacementExpressionFromInstance(
                expression     = call_node,
                exception      = e.getRealException()
            ),
            positional_args = call_node.getPositionalArguments(),
            list_star_arg   = call_spec.getStarListArg(),
            dict_star_arg   = call_node.getStarDictArg(),
            pairs           = call_node.getNamedArgumentPairs(),
            source_ref      = call_node.getSourceReference()
        )


    return call_node, None, None

def register():
    CallRegistry.registerCallHandler(
        kind    = CPythonExpressionFunctionBody.kind,
        handler = computeOwnedFunctionCall
    )
