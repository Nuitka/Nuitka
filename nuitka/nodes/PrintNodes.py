#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
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
