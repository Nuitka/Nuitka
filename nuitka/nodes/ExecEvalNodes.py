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

from .NodeBases import CPythonChildrenHaving, CPythonNodeBase, CPythonClosureTaker, CPythonClosureGiverNodeBase

from nuitka import Variables

class CPythonExpressionBuiltinEval( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_BUILTIN_EVAL"

    named_children = ( "source", "globals", "locals" )

    def __init__( self, source_code, globals_arg, locals_arg, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "source"  : source_code,
                "globals" : globals_arg,
                "locals"  : locals_arg,
            }
        )

    getSourceCode = CPythonChildrenHaving.childGetter( "source" )
    getGlobals = CPythonChildrenHaving.childGetter( "globals" )
    getLocals = CPythonChildrenHaving.childGetter( "locals" )


# Note: Python3 only so far.
class CPythonExpressionBuiltinExec( CPythonExpressionBuiltinEval ):
    kind = "EXPRESSION_BUILTIN_EXEC"


class CPythonExpressionBuiltinExecfile( CPythonExpressionBuiltinEval ):
    kind = "EXPRESSION_BUILTIN_EXECFILE"

    named_children = ( "source", "globals", "locals" )

    def __init__( self, source_code, globals_arg, locals_arg, source_ref ):
        CPythonExpressionBuiltinEval.__init__( self, source_code, globals_arg, locals_arg, source_ref )


def _convertNoneConstantToNone( value ):
    if value is not None and value.isExpressionConstantRef() and value.getConstant() is None:
        return None
    else:
        return value

class CPythonStatementExec( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_EXEC"

    named_children = ( "source", "globals", "locals" )

    def __init__( self, source_code, globals_arg, locals_arg, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "globals" : globals_arg,
                "locals"  : locals_arg,
                "source"  : source_code
            }
        )

    getSourceCode = CPythonChildrenHaving.childGetter( "source" )
    _getGlobals = CPythonChildrenHaving.childGetter( "globals" )
    _getLocals = CPythonChildrenHaving.childGetter( "locals" )

    def getLocals( self ):
        return _convertNoneConstantToNone( self._getLocals() )

    def getGlobals( self ):
        if self.getLocals() is None:
            return _convertNoneConstantToNone( self._getGlobals() )
        else:
            return self._getGlobals()


# TODO: This is totally bitrot
class CPythonStatementExecInline( CPythonChildrenHaving, CPythonClosureTaker, CPythonClosureGiverNodeBase ):
    kind = "STATEMENT_EXEC_INLINE"

    named_children = ( "body", )

    early_closure = True

    def __init__( self, provider, source_ref ):
        CPythonClosureTaker.__init__( self, provider )
        CPythonClosureGiverNodeBase.__init__(
            self,
            name        = "exec_inline",
            code_prefix = "exec_inline",
            source_ref  = source_ref
        )

        CPythonChildrenHaving.__init__(
            self,
            values = {}
        )

    getBody = CPythonChildrenHaving.childGetter( "body" )
    setBody = CPythonChildrenHaving.childSetter( "body" )

    def getVariableForAssignment( self, variable_name ):
        # print ( "ASS inline", self, variable_name )

        if self.hasProvidedVariable( variable_name ):
            return self.getProvidedVariable( variable_name )

        result = self.getProvidedVariable( variable_name )

        # Remember that we need that closure for something.
        self.registerProvidedVariable( result )

        # print ( "RES inline", result )

        return result

    def getVariableForReference( self, variable_name ):
        # print ( "REF inline", self, variable_name )

        result = self.getVariableForAssignment( variable_name )

        # print ( "RES inline", result )

        return result

    def createProvidedVariable( self, variable_name ):
        # print ( "CREATE inline", self, variable_name )

        # An exec in a module gives a module variable always, on the top level
        # of an exec, if it's not already a global through a global statement,
        # the parent receives a local variable now.
        if self.provider.isModule():
            return self.provider.getProvidedVariable(
                variable_name = variable_name
            )
        else:
            return Variables.LocalVariable(
                owner         = self.provider,
                variable_name = variable_name
            )
