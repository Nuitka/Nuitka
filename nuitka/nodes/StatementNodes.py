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
""" Nodes for statements.

"""

from .NodeBases import CPythonChildrenHaving, CPythonNodeBase

def mergeStatements( statements ):
    """ Helper function that merges nested statement sequences. """
    merged_statements = []

    for statement in statements:
        if statement.isStatement() or statement.isStatementsFrame():
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


    def mayHaveSideEffects( self, constraint_collection ):
        assert constraint_collection is None

        # Statement sequences have a side effect if one of the statements does.
        for statement in self.getStatements():
            if statement.mayHaveSideEffects( None ):
                return True
        else:
            return False

    def isStatementAbortative( self ):
        return self.getStatements()[-1].isStatementAbortative()


class CPythonStatementsFrame( CPythonStatementsSequence ):
    kind = "STATEMENTS_FRAME"

    def __init__( self, statements, code_name, arg_names, kw_only_count, source_ref ):
        CPythonStatementsSequence.__init__(
            self,
            statements = statements,
            source_ref = source_ref
        )

        self.arg_names = tuple( arg_names )
        self.code_name = code_name

        self.kw_only_count = kw_only_count

    def getDetails( self ):
        return {
            "code_name" : self.code_name,
            "arg_names" : self.arg_names
        }

    def getArgNames( self ):
        return self.arg_names

    def getCodeObjectName( self ):
        return self.code_name

    def getKwOnlyParameterCount( self ):
        return self.kw_only_count


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

    def mayHaveSideEffects( self, constraint_collection ):
        return self.getExpression().mayHaveSideEffects( constraint_collection )

    getExpression = CPythonChildrenHaving.childGetter( "expression" )
