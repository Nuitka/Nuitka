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
""" Replace useless unpacking with multiple assignments where possible."""

from .OptimizeBase import (
    OptimizationVisitorBase,
    makeRaiseExceptionReplacementStatement,
    makeConstantReplacementNode
)

from nuitka.nodes import Nodes

from nuitka import Utils

_unpack_error_length_indication = Utils.getPythonVersion() < 300

class ReplaceUnpackingVisitor( OptimizationVisitorBase ):
    def __call__( self, node ):
        if node.isStatementAssignment():
            targets = node.getTargets()

            if len( targets ) == 1:
                target = targets[0]

                if target.isAssignTargetTuple():
                    source = node.getSource()

                    if source.isExpressionConstantRef():
                        try:
                            unpackable = iter( source.getConstant() )
                        except TypeError:
                            return

                        unpacked = list( unpackable )
                        elements = target.getElements()

                        if len( unpacked ) == len( elements ):
                            statements = []

                            for value, element in zip( unpacked, elements ):
                                statements.append(
                                    Nodes.CPythonStatementAssignment(
                                        targets    = ( element, ),
                                        expression = makeConstantReplacementNode(
                                            constant = value,
                                            node     = node
                                        ),
                                        source_ref = node.getSourceReference()
                                    )
                                )

                            node.replaceWith(
                                Nodes.CPythonStatementsSequence(
                                    statements = statements,
                                    source_ref = node.getSourceReference()
                                )
                            )

                            self.signalChange(
                                "new_statements",
                                node.getSourceReference(),
                                "Removed useless unpacking assignments."
                            )
                        else:
                            if len( unpacked ) > len( elements ):
                                if _unpack_error_length_indication:
                                    exception_value = "too many values to unpack"
                                else:
                                    exception_value = "too many values to unpack (expected %d)" % len( elements )

                                node.replaceWith(
                                    makeRaiseExceptionReplacementStatement(
                                        statement       = node,
                                        exception_type  = "ValueError",
                                        exception_value = exception_value,
                                    )
                                )
                            elif len( unpacked ) == 1:
                                node.replaceWith(
                                    makeRaiseExceptionReplacementStatement(
                                        statement       = node,
                                        exception_type  = "ValueError",
                                        exception_value = "need more than 1 value to unpack",
                                    )
                                )
                            else:
                                node.replaceWith(
                                    makeRaiseExceptionReplacementStatement(
                                        statement       = node,
                                        exception_type  = "ValueError",
                                        exception_value = "need more than %s values to unpack" % len( unpacked ),
                                    )
                                )


                            self.signalChange(
                                "new_code",
                                node.getSourceReference(),
                                "Removed bound to fail unpacking assignments."
                            )
