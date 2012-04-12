#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit patches or make the software available to licensors of
#     this software in either form, you automatically them grant them a
#     license for your part of the code under "Apache License 2.0" unless you
#     choose to remove this notice.
#
#     Kay Hayen uses the right to license his code under only GPL version 3,
#     to discourage a fork of Nuitka before it is "finished". He will later
#     make a new "Nuitka" release fully under "Apache License 2.0".
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
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

        # TODO: More appropiate tag maybe.
        return result, "new_statements", "Replaced call to created function body with direct function call"

    except TooManyArguments as e:
        return CPythonExpressionCall(
            called_expression = makeRaiseExceptionReplacementExpressionFromInstance(
                expression     = call_node,
                exception      = e.getRealException()
            ),
            list_star_arg     = call_spec.getStarListArg(),
            dict_star_arg     = call_node.getStarDictArg(),
            positional_args   = call_node.getPositionalArguments(),
            pairs             = call_node.getNamedArgumentPairs(),
            source_ref        = call_node.getSourceReference()
        )


    return call_node, None, None

def register():
    CallRegistry.registerCallHandler(
        kind    = CPythonExpressionFunctionBody.kind,
        handler = computeOwnedFunctionCall
    )
