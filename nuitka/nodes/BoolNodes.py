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
""" Nodes for binary boolean operations.

Here short-circuit is involved, that means, the second argument may not be evaluated if
the first one provides the truth value needed to determine the result.

"""

from .NodeBases import CPythonExpressionChildrenHavingBase

from .NodeMakingHelpers import getComputationResult, wrapExpressionWithSideEffects

class CPythonExpressionBool2Base( CPythonExpressionChildrenHavingBase ):
    """ The "and/or" are short circuit and is therefore are not plain operations.

    """
    tags = ( "short_circuit", )

    named_children = ( "operands", )

    def __init__( self, operands, source_ref ):
        assert len( operands ) >= 2

        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "operands" : tuple( operands )
            },
            source_ref = source_ref
        )

    getOperands = CPythonExpressionChildrenHavingBase.childGetter( "operands" )

    def computeNode( self, constraint_collection ):
        operands = self.getOperands()
        values = []

        truth_value = operands[0].getTruthValue( constraint_collection )

        # Known true value
        if truth_value is True:
            if self.kind == "EXPRESSION_BOOL_OR":
                # In case "or", we can ignore the rest, the value is decided.

                return (
                    wrapExpressionWithSideEffects(
                        new_node = operands[0],
                        old_node = operands[0]
                    ),
                    "new_expression",
                    "Remove 'or' others argument because first argument is known true"
                )
            else:
                assert self.kind == "EXPRESSION_BOOL_AND"

                if len( operands ) > 2:
                    new_node = CPythonExpressionBoolAND(
                        operands   = operands[1:],
                        source_ref = self.getSourceReference()
                    )
                else:
                    new_node = operands[1]

                return (
                    wrapExpressionWithSideEffects(
                        new_node = new_node,
                        old_node = operands[0]
                    ),
                    "new_expression",
                    "Remove 'and' first argument because it is known true"
                )


        if truth_value is False:
            if self.kind == "EXPRESSION_BOOL_OR":
                if len( operands ) > 2:
                    new_node = CPythonExpressionBoolOR(
                        operands   = operands[1:],
                        source_ref = self.getSourceReference()
                    )
                else:
                    new_node = operands[1]

                return (
                    wrapExpressionWithSideEffects(
                        new_node = new_node,
                        old_node = operands[0]
                    ),
                    "new_expression",
                    "Remove 'or' first argument because it is known false"
                )
            else:
                assert self.kind == "EXPRESSION_BOOL_AND"

                # In case "and", we can ignore the rest, the value is decided.
                return (
                    wrapExpressionWithSideEffects(
                        new_node = operands[0],
                        old_node = operands[0]
                    ),
                    "new_expression",
                    "Remove 'and' others argument because first argument is known false"
                )

        for operand in operands:
            if not operand.isCompileTimeConstant():
                return self, None, None

            values.append( operand.getCompileTimeConstant() )

        # Fall through, which normally should not happen anymore, because all compile time
        # constants have known truth value, or should. In fact the default implementation
        # of truth value uses just that. TODO: Assert this is not happening.

        assert False, operands

        return getComputationResult(
            node        = self,
            # The simulator interface requires that we use star list calls,
            # pylint: disable=W0142
            computation = lambda : self.getSimulator()( *values ),
            description = "Boolean operator with known truth values"
        )

    def getSimulator( self ):
        """ Simulation of the node operation, given some values.

            The short circuit nature cannot be provided when calling this.
        """

        # Virtual method, pylint: disable=R0201
        raise SystemExit( "Fatal error, must overload getSimulator" )


class CPythonExpressionBoolOR( CPythonExpressionBool2Base ):
    """ The "or" is short circuit and is therefore not a plain operation.

    """

    kind = "EXPRESSION_BOOL_OR"

    def getSimulator( self ):
        # Virtual method, pylint: disable=R0201
        def simulateOR( *operands ):
            for operand in operands:
                if operand:
                    return operand
            else:
                return operands[-1]

        return simulateOR


class CPythonExpressionBoolAND( CPythonExpressionBool2Base ):
    """ The "and" is short circuit and is therefore not a plain operation.

    """

    kind = "EXPRESSION_BOOL_AND"

    def getSimulator( self ):
        # Virtual method, pylint: disable=R0201
        def simulateAND( *operands ):
            for operand in operands:
                if not operand:
                    return operand
            else:
                return operands[-1]

        return simulateAND
