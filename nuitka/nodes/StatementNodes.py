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

from .NodeBases import StatementChildrenHavingBase

from nuitka.Utils import python_version

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


class StatementsSequence( StatementChildrenHavingBase ):
    kind = "STATEMENTS_SEQUENCE"

    named_children = ( "statements", )

    def __init__( self, statements, source_ref ):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "statements" : tuple( statements )
            },
            source_ref = source_ref
        )

    getStatements = StatementChildrenHavingBase.childGetter( "statements" )
    setStatements = StatementChildrenHavingBase.childSetterNotNone( "statements" )

    def getDetails( self ):
        if self.getStatements():
            return { "statement_count" : len( self.getStatements() ) }
        else:
            return { "statement_count" : 0 }

    def setChild( self, name, value ):
        assert name == "statements"

        assert None not in value, value

        return StatementChildrenHavingBase.setChild(
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
        assert constraint_collection is None

        # Statement sequences have a side effect if one of the statements does.
        for statement in self.getStatements():
            if statement.mayHaveSideEffects():
                return True
        else:
            return False

    def isStatementAborting( self ):
        return self.getStatements()[-1].isStatementAborting()


class StatementsFrame( StatementsSequence ):
    kind = "STATEMENTS_FRAME"

    def __init__( self, statements, guard_mode, code_name, var_names, arg_count,
                  kw_only_count, has_starlist, has_stardict, source_ref ):
        StatementsSequence.__init__(
            self,
            statements = statements,
            source_ref = source_ref
        )

        self.var_names = tuple( var_names )
        self.code_name = code_name

        self.kw_only_count = kw_only_count
        self.arg_count = arg_count

        self.guard_mode = guard_mode

        self.has_starlist = has_starlist
        self.has_stardict = has_stardict

    def getDetails( self ):
        result = {
            "code_name"  : self.code_name,
            "var_names"  : ", ".join( self.var_names ),
            "guard_mode" : self.guard_mode
        }

        if python_version >= 300:
            result[ "kw_only_count" ] = self.kw_only_count

        return result

    def needsLineNumber( self ):
        return False

    def getGuardMode( self ):
        return self.guard_mode

    def getVarNames( self ):
        return self.var_names

    def getCodeObjectName( self ):
        return self.code_name

    def getKwOnlyParameterCount( self ):
        return self.kw_only_count

    def getArgumentCount( self ):
        return self.arg_count

    def makeCloneAt( self, source_ref ):
        assert False

    def getCodeObjectHandle( self, context ):
        provider = self.getParentVariableProvider()

        # TODO: Why do this accessing a node, do this outside.
        from nuitka.codegen.CodeObjectCodes import getCodeObjectHandle

        return getCodeObjectHandle(
            context       = context,
            filename      = self.source_ref.getFilename(),
            var_names     = self.getVarNames(),
            arg_count     = self.getArgumentCount(),
            kw_only_count = self.getKwOnlyParameterCount(),
            line_number   = 0
                              if provider.isPythonModule() else
                            self.source_ref.getLineNumber(),
            code_name     = self.getCodeObjectName(),
            is_generator  = provider.isExpressionFunctionBody() and \
                            provider.isGenerator(),
            is_optimized  = not provider.isPythonModule() and \
                            not provider.isClassDictCreation() and \
                            not context.hasLocalsDict(),
            has_starlist  = self.has_starlist,
            has_stardict  = self.has_stardict
        )


class StatementExpressionOnly( StatementChildrenHavingBase ):
    kind = "STATEMENT_EXPRESSION_ONLY"

    named_children = ( "expression", )

    def __init__( self, expression, source_ref ):
        assert expression.isExpression()

        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "expression" : expression
            },
            source_ref = source_ref
        )

    def getDetail( self ):
        return "expression %s" % self.getExpression()

    def mayHaveSideEffects( self ):
        return self.getExpression().mayHaveSideEffects()

    getExpression = StatementChildrenHavingBase.childGetter( "expression" )

    def computeStatement( self, constraint_collection ):
        constraint_collection.onExpression( self.getExpression() )
        expression = self.getExpression()

        # Side effects can  become statements.
        if expression.isExpressionSideEffects():
            from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions

            result = makeStatementOnlyNodesFromExpressions(
                expressions = expression.getSideEffects() + \
                              ( expression.getExpression(), )
            )

            return result, "new_statements", """\
Turned side effects of expression only statement into statements."""

        elif not expression.mayHaveSideEffects():
            return None, "new_statements", "Removed statement without effect."

        elif expression.isExpressionRaiseException():
            from .ExceptionNodes import StatementRaiseExceptionImplicit

            result = StatementRaiseExceptionImplicit(
                exception_type  = expression.getExceptionType(),
                exception_value = expression.getExceptionValue(),
                exception_trace = None,
                exception_cause = None,
                source_ref      = expression.getSourceReference()
            )

            return result, "new_raise", """\
Propgated implict raise expression to raise statement."""
        elif python_version < 300 and expression.isExpressionBuiltinExecfile():
            # In this case, the copy-back must be done and will only be done
            # correctly by the code for exec statements.
            provider = self.getParentVariableProvider()

            if provider.isExpressionFunctionBody() and provider.isClassDictCreation():
                from .ExecEvalNodes import StatementExec

                result = StatementExec(
                    source_code = expression.getSourceCode(),
                    globals_arg = expression.getGlobals(),
                    locals_arg  = expression.getLocals(),
                    source_ref  = expression.getSourceReference()
                )

                return result, "new_statements", """\
Changed execfile to exec on class level"""
        elif python_version >= 300 and expression.isExpressionBuiltinExec():
            if self.getParentVariableProvider().isEarlyClosure():
                from .ExecEvalNodes import StatementExec

                result = StatementExec(
                    source_code = expression.getSourceCode(),
                    globals_arg = expression.getGlobals(),
                    locals_arg  = expression.getLocals(),
                    source_ref  = expression.getSourceReference()
                )

                return result, "new_statements", """\
Replaced builtin exec call to exec statement in early closure context."""

        return self, None, None
