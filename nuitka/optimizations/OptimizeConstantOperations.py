#
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
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


from OptimizeBase import OptimizationVisitorBase, areConstants

from nuitka import PythonOperators, Nodes

class OptimizeOperationVisitor( OptimizationVisitorBase ):
    def __call__( self, node ):
        if node.isOperation():
            operands = node.getOperands()

            if areConstants( operands ):
                operator = node.getOperator()

                if operator != "Repr":
                    operands = [ constant.getConstant() for constant in operands ]

                    try:
                        if len( operands ) == 2:
                            result = PythonOperators.binary_operator_functions[ operator ]( *operands )
                        elif len( operands ) == 1:
                            result = PythonOperators.unary_operator_functions[ operator ]( *operands )
                        else:
                            assert False, operands
                    except AssertionError:
                        raise
                    except Exception, e:
                        # TODO: If not an AssertError, we can create a raise exception
                        # node that does it.
                        return

                    new_node = Nodes.makeConstantReplacementNode(
                        constant = result,
                        node     = node
                    )

                    node.replaceWith( new_node )

                    self.signalChange( "new_constant" )
