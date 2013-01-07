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
""" Optimize subscript of compile time constant nodes.

This works via the subscript registry.
"""

from .registry import SubscriptRegistry

from nuitka.nodes.ConstantRefNode import CPythonExpressionConstantRef
from nuitka.nodes.NodeMakingHelpers import getComputationResult

def computeConstantSubscript( subscript_node, lookup, subscript, constraint_collection ):
    # The computation with constants has no impact on value states. pylint: disable=W0613

    assert lookup.isCompileTimeConstant()
    assert subscript is not None

    if subscript.isCompileTimeConstant():
        return getComputationResult(
            node        = subscript_node,
            computation = lambda : lookup.getCompileTimeConstant()[ subscript.getCompileTimeConstant() ],
            description = "Subscript of constant with constant value."
        )

    return subscript_node, None, None

def register():
    # TODO: Actually we should register for all compile time constant values, and know
    # what kinds these are.
    SubscriptRegistry.registerSubscriptHandler(
        kind    = CPythonExpressionConstantRef.kind,
        handler = computeConstantSubscript
    )
