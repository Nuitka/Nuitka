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
""" Optimization step that inlines exec where it's parameter is known.

Replace exec with string constant as parameters with the code inlined instead. This is an
optimization that is easy to do and useful for large parts of the CPython test suite that
exec constant strings.

It avoids non-compiled code and might be useful to make lazy people's usage of exec with
dynamic string built from constants to generate code on the fly performant as well.

When it strikes, it tags with "reset", because it requires a restart of all steps.

"""

from OptimizeBase import OptimizationVisitorBase, warning

from nuitka import TreeBuilding

class OptimizeExecVisitor( OptimizationVisitorBase ):
    """ Inline constant execs.

    """
    def __call__( self, node ):
        if node.isStatementExec() and node.getLocals() is None and node.getGlobals() is None:
            source = node.getSource()

            if source.isConstantReference():
                source_ref = node.getSourceReference().getExecReference()

                try:
                    new_node = TreeBuilding.buildReplacementTree(
                        provider    = node.getParentVariableProvider(),
                        parent      = node.getParent(),
                        source_code = source.getConstant(),
                        source_ref  = source_ref
                    )

                    node.replaceWith( new_node )

                    self.signalChange( "new_code" )
                except SyntaxError:
                    warning( "Syntax error will be raised at runtime for exec at '%s'." % source_ref.getAsString() )
