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
""" Optimize operations on constant nodes.

"""

from .OptimizeBase import (
    OptimizationVisitorBase,
    areConstants,
    makeConstantReplacementNode
)

class OptimizeFunctionCallArgsVisitor( OptimizationVisitorBase ):

    def onEnterNode( self, node ):
        if node.isExpressionFunctionCall():
            star_list_arg = node.getStarListArg()

            if star_list_arg is not None:
                if star_list_arg.isExpressionMakeSequence():
                    positional_args = node.getPositionalArguments()

                    node.setPositionalArguments( positional_args + star_list_arg.getElements() )
                    node.setStarListArg( None )
                elif star_list_arg.isExpressionConstantRef():
                    if star_list_arg.isKnownToBeIterable( count = None ):
                        positional_args = node.getPositionalArguments()

                        constant_nodes = []

                        for constant in star_list_arg.getConstant():
                            constant_nodes.append(
                                makeConstantReplacementNode(
                                    constant = constant,
                                    node     = star_list_arg
                                )
                            )

                        node.setPositionalArguments( positional_args + tuple( constant_nodes ) )
                        node.setStarListArg( None )


            star_dict_arg = node.getStarDictArg()

            if star_dict_arg is not None:
                if star_dict_arg.isExpressionMakeDict():
                    # TODO: Need to cleanup the named argument mess before it is possible.
                    pass
                elif star_dict_arg.isExpressionConstantRef():
                    # TODO: Need to cleanup the named argument mess before it is possible.
                    pass
