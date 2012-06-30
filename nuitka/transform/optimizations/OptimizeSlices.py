#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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
""" Optimize slicing of compile time constant nodes.

This works via the slice registry.
"""

from .registry import SliceRegistry

from nuitka.nodes.ConstantRefNode import CPythonExpressionConstantRef
from nuitka.nodes.NodeMakingHelpers import getComputationResult

def computeConstantSlice( slice_node, lookup, lower, upper ):
    assert lookup.isCompileTimeConstant()

    # TODO: Could be happy with predictable index values and not require constants.
    if lower is not None:
        if upper is not None:
            if lower.isCompileTimeConstant() and upper.isCompileTimeConstant():
                return getComputationResult(
                    node        = slice_node,
                    computation = lambda : lookup.getCompileTimeConstant()[
                        lower.getCompileTimeConstant() : upper.getCompileTimeConstant()
                    ],
                    description = "Slicing of constant with constant indexes."
                )
        else:
            if lower.isCompileTimeConstant():
                return getComputationResult(
                    node        = slice_node,
                    computation = lambda : lookup.getCompileTimeConstant()[
                        lower.getCompileTimeConstant() :
                    ],
                    description = "Slicing of constant with constant indexes."
                )
    else:
        if upper is not None:
            if upper.isCompileTimeConstant():
                return getComputationResult(
                    node        = slice_node,
                    computation = lambda : lookup.getCompileTimeConstant()[
                        : upper.getCompileTimeConstant()
                    ],
                    description = "Slicing of constant with constant indexes."
                )
        else:
            return getComputationResult(
                node        = slice_node,
                computation = lambda : lookup.getCompileTimeConstant()[ : ],
                description = "Slicing of constant with constant indexes."
            )

    return slice_node, None, None

def register():
    # TODO: Actually we should register for all compile time constant values, and know
    # what kinds these are.
    SliceRegistry.registerSliceHandler(
        kind    = CPythonExpressionConstantRef.kind,
        handler = computeConstantSlice
    )
