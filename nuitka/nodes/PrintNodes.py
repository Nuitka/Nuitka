#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .NodeBases import StatementChildrenHavingBase


class StatementPrint( StatementChildrenHavingBase ):
    kind = "STATEMENT_PRINT"

    named_children = ( "dest", "values" )

    def __init__( self, dest, values, newline, source_ref ):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "values" : tuple( values ),
                "dest"   : dest
            },
            source_ref = source_ref
        )

        self.newline = newline

    def isNewlinePrint( self ):
        return self.newline

    def removeNewlinePrint( self ):
        self.newline = False

    getDestination = StatementChildrenHavingBase.childGetter( "dest" )
    getValues = StatementChildrenHavingBase.childGetter( "values" )
    setValues = StatementChildrenHavingBase.childSetter( "values" )
