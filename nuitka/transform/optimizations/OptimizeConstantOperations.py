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

class OptimizeOperationVisitor( OptimizationVisitorBase ):
    def _optimizeConstantOperandsOperation( self, node, operands ):
        operands = [ constant.getConstant() for constant in operands ]

        def simulate():
            # This is a convinent way to execute no matter what the number of
            # operands is. pylint: disable=W0142
            return node.getSimulator()( *operands )

        self.replaceWithComputationResult(
            node        = node,
            computation = simulate,
            description = "Operation with constant args"
        )

    def _optimizeConstantOperandsComparison( self, node ):
        operand1, operand2 = node.getOperands()

        if areConstants( ( operand1, operand2 ) ):
            value1 = operand1.getConstant()
            value2 = operand2.getConstant()

            simulator = node.getSimulator()

            def simulate():
                return simulator( value1, value2 )

            self.replaceWithComputationResult(
                node        = node,
                computation = simulate,
                description = "Comparison with constant args"
            )

    def _optimizeConstantSliceLookup( self, node ):
        lower = node.getLower()
        upper = node.getUpper()

        if lower is not None and lower.isExpressionConstantRef() and lower.getConstant() is None:
            node.setLower( None )

        if upper is not None and upper.isExpressionConstantRef() and upper.getConstant() is None:
            node.setUpper( None )

    def _optimizeConstantSequenceMaking( self, node ):
        new_node, tags, descr = node.computeNode()

        if new_node is not node:
            node.replaceWith( new_node )

            self.signalChange(
                tags,
                node.getSourceReference(),
                descr
            )


    def _optimizeConstantDictMaking( self, node ):
        pairs = node.getPairs()

        for pair in pairs:
            if not pair.getKey().isExpressionConstantRef():
                break

            value = pair.getValue()

            if not value.isExpressionConstantRef() or value.isMutable():
                break
        else:
            constant_value = dict.fromkeys(
                [
                    pair.getKey().getConstant()
                    for pair in
                    pairs
                ],
                None
            )

            for pair in pairs:
                constant_value[ pair.getKey().getConstant() ] = pair.getValue().getConstant()

            new_node = makeConstantReplacementNode(
                constant = constant_value,
                node     = node
            )

            node.replaceWith( new_node )

            self.signalChange(
                "new_constant",
                node.getSourceReference(),
                "Created dictionary found to be constant."
            )

    def onEnterNode( self, node ):
        if node.isOperation() or node.isExpressionOperationBool2():
            operands = node.getOperands()

            if areConstants( operands ):
                self._optimizeConstantOperandsOperation(
                    node     = node,
                    operands = operands
                )
        elif node.isExpressionComparison():
            self._optimizeConstantOperandsComparison(
                node = node
            )
        elif node.isExpressionSliceLookup():
            self._optimizeConstantSliceLookup(
                node = node
            )
        elif node.isExpressionMakeSequence():
            self._optimizeConstantSequenceMaking(
                node = node
            )
        elif node.isExpressionMakeDict():
            self._optimizeConstantDictMaking(
                node = node
            )
        # TODO: Move this to a separate optimization step.
        elif node.isExpressionFunctionCall():
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
