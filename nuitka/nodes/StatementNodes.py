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
""" Nodes for statements.

"""

from .NodeBases import CPythonChildrenHaving, CPythonNodeBase

class CPythonStatementsSequence( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENTS_SEQUENCE"

    named_children = ( "statements", )

    def __init__( self, statements, source_ref ):
        for statement in statements:
            assert statement.isStatement() or statement.isStatementsSequence(), statement

        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "statements" : tuple( statements )
            }
        )

    getStatements = CPythonChildrenHaving.childGetter( "statements" )

    # Overloading automatic check, so that derived ones know it too.
    def isStatementsSequence( self ):
        # Virtual method, pylint: disable=R0201,W0613

        return True

    def trimStatements( self, statement ):
        assert statement.parent is self

        old_statements = list( self.getStatements() )
        assert statement in old_statements, ( statement, self )

        new_statements = old_statements[ : old_statements.index( statement ) + 1 ]

        self.setChild( "statements", new_statements )

    def removeStatement( self, statement ):
        assert statement.parent is self

        statements = list( self.getStatements() )
        statements.remove( statement )
        self.setChild( "statements", statements )

    def mergeStatementsSequence( self, statement_sequence ):
        assert statement_sequence.parent is self

        old_statements = list( self.getStatements() )
        assert statement_sequence in old_statements, ( statement_sequence, self )

        merge_index =  old_statements.index( statement_sequence )

        new_statements = tuple( old_statements[ : merge_index ] )   + \
                         statement_sequence.getStatements()         + \
                         tuple( old_statements[ merge_index + 1 : ] )

        self.setChild( "statements", new_statements )


    def mayHaveSideEffects( self ):
        # Statement sequences have a side effect if one of the statements does.
        for statement in self.getStatements():
            if statement.mayHaveSideEffects():
                return True
        else:
            return False


class CPythonStatementExpressionOnly( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_EXPRESSION_ONLY"

    named_children = ( "expression", )

    def __init__( self, expression, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "expression" : expression
            }
        )

    def getDetail( self ):
        return "expression %s" % self.getExpression()

    getExpression = CPythonChildrenHaving.childGetter( "expression" )
