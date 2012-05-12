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
""" Print nodes.

Right now there is only the print statement, but in principle, there should also be the
print function here. These perform output, which can be combined if possible, and could be
detected to fail, which would be perfect.

Predicting the behavior of 'print' is not trivial at all, due to many special cases.
"""

from .NodeBases import CPythonChildrenHaving, CPythonNodeBase


class CPythonStatementPrint( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_PRINT"

    named_children = ( "dest", "values" )

    def __init__( self, dest, values, newline, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "values" : tuple( values ),
                "dest"   : dest
            }
        )

        self.newline = newline


    def isNewlinePrint( self ):
        return self.newline

    getDestination = CPythonChildrenHaving.childGetter( "dest" )
    getValues = CPythonChildrenHaving.childGetter( "values" )
    setValues = CPythonChildrenHaving.childSetter( "values" )
