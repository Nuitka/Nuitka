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
""" Replace useless unpacking with multiple assignments where possible."""

from optimizations.OptimizeBase import OptimizationVisitorBase

import Nodes

class ReplaceUnpackingVisitor( OptimizationVisitorBase ):
    def __call__( self, node ):
        if node.isStatementAssignment():
            targets = node.getTargets()

            if len( targets ) == 1:
                target = targets[0]

                if target.isAssignToTuple():
                    source = node.getSource()

                    if source.isConstantReference():
                        try:
                            unpackable = iter( source.getConstant() )
                        except TypeError:
                            return

                        unpacked = list( unpackable )

                        if len( unpacked ) == len( target.getElements() ):
                            statements = []

                            for value, element in zip( unpacked, target.getElements() ):
                                statements.append(
                                    Nodes.CPythonStatementAssignment(
                                        targets    = ( element, ),
                                        expression = Nodes.CPythonExpressionConstant(
                                            constant   = value,
                                            source_ref = node.getSourceReference()
                                        ),
                                        source_ref = node.getSourceReference()
                                    )
                                )

                            node.replaceWith(
                                Nodes.CPythonStatementSequence(
                                    statements = statements,
                                    source_ref = node.getSourceReference()
                                )
                            )

                            self.signalChange( "new_statements" )
                        else:
                            # TODO: Raise the exception instead.
                            pass
