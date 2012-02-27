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
""" Finalize the temp variables.

If a temp variable is used in a holder, notice that and later set these temp variables
for use by code generation to add declarations for them to a suitable spot.

"""

from .FinalizeBase import FinalizationVisitorScopedBase

class FinalizeTempVariables( FinalizationVisitorScopedBase ):
    def __init__( self ):
        self.variables = set()
        self.current = None

    def onEnterScope( self, node ):
        self.current = node

    def onLeaveScope( self, node ):
        assert node is self.current

        self.current.setTempVariables( self.variables )

        self.variables = set()
        self.current = None

    def onEnterNode( self, node ):
        if node.isExpressionTempVariableRef() and node.getVariable().getOwner() is self.current:
            self.variables.add( node.getVariable().getReferenced() )
