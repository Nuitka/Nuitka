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
