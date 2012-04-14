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

def mergeStatements( statements ):
    """ Helper function that merges nested statement sequences. """
    merged_statements = []

    for statement in statements:
        if statement.isStatement():
            merged_statements.append( statement )
        elif statement.isStatementsSequence():
            merged_statements.extend( mergeStatements( statement.getStatements() ) )
        else:
            assert False, statement

    return merged_statements


class CPythonStatementsSequence( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENTS_SEQUENCE"

    named_children = ( "statements", )

    def __init__( self, statements, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "statements" : tuple( statements )
            }
        )

    getStatements = CPythonChildrenHaving.childGetter( "statements" )
    setStatements = CPythonChildrenHaving.childSetterNotNone( "statements" )

    def setChild( self, name, value ):
        assert name == "statements"

        return CPythonChildrenHaving.setChild(
            self,
            name  = name,
            value = mergeStatements( value )
        )

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

    def isStatementAbortative( self ):
        return self.getStatements()[-1].isStatementAbortative()


class CPythonStatementsFrame( CPythonStatementsSequence ):
    kind = "STATEMENTS_FRAME"

    def __init__( self, statements, code_name, arg_names, source_ref ):
        CPythonStatementsSequence.__init__(
            self,
            statements = statements,
            source_ref = source_ref
        )

        self.arg_names = tuple( arg_names )
        self.code_name = code_name

    def getArgNames( self ):
        return self.arg_names

    def getCodeObjectName( self ):
        return self.code_name


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

    def mayHaveSideEffects( self ):
        return self.getExpression().mayHaveSideEffects()

    getExpression = CPythonChildrenHaving.childGetter( "expression" )
