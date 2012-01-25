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
""" Optimization step that inlines exec where it's parameter is known.

Replace exec with string constant as parameters with the code inlined instead. This is an
optimization that is easy to do and useful for large parts of the CPython test suite that
exec constant strings.

It avoids non-compiled code and might be useful to make lazy people's usage of exec with
dynamic string built from constants to generate code on the fly performant as well.

When it strikes, it tags with "new_code", because the fresh code requires a restart of all
steps.

"""

from .OptimizeBase import OptimizationVisitorBase, warning

from nuitka.nodes.ExecEvalNodes import CPythonStatementExecInline

from nuitka import TreeBuilding

class OptimizeExecVisitor( OptimizationVisitorBase ):
    """ Inline constant execs.

    """
    def onEnterNode( self, node ):
        if node.isStatementExec() and node.getGlobals() is None and node.getLocals() is None:
            source = node.getSourceCode()

            if source.isExpressionConstantRef():
                source_ref = node.getSourceReference().getExecReference()

                try:
                    new_node = CPythonStatementExecInline(
                        provider    = node.getParentVariableProvider(),
                        source_ref  = source_ref
                    )
                    new_node.parent = node.getParent()

                    body = TreeBuilding.buildReplacementTree(
                        provider    = new_node,
                        source_code = source.getConstant(),
                        source_ref  = source_ref
                    )

                    body.parent = new_node

                    new_node.setBody( body )

                    node.replaceWith( new_node )

                    self.signalChange(
                        "new_code",
                        source_ref,
                        "Replaced 'exec' with known constant parameter with inlined code."
                    )
                except SyntaxError:
                    warning(
                        "Syntax error will be raised at runtime for exec at '%s'." %
                        source_ref.getAsString()
                    )
