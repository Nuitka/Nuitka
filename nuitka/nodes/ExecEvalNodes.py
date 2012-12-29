#     Copyright 2012, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Nodes concern with exec and eval builtins.

These are the dynamic codes, and as such rather difficult. We would like
to eliminate or limit their impact as much as possible, but it's difficult
to do.
"""

from .NodeBases import (
    CPythonExpressionChildrenHavingBase,
    CPythonChildrenHaving,
    CPythonNodeBase,
    CPythonClosureTaker,
    CPythonClosureGiverNodeBase
)

from .NodeMakingHelpers import convertNoneConstantToNone

from nuitka import Variables, Utils

class CPythonExpressionBuiltinEval( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_BUILTIN_EVAL"

    named_children = ( "source", "globals", "locals" )

    def __init__( self, source_code, globals_arg, locals_arg, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "source"  : source_code,
                "globals" : globals_arg,
                "locals"  : locals_arg,
            },
            source_ref = source_ref
        )

    getSourceCode = CPythonExpressionChildrenHavingBase.childGetter( "source" )
    getGlobals = CPythonExpressionChildrenHavingBase.childGetter( "globals" )
    getLocals = CPythonExpressionChildrenHavingBase.childGetter( "locals" )

    def computeNode( self, constraint_collection ):
        # TODO: Attempt for constant values to do it.
        return self, None, None


# Note: Python3 only so far.
if Utils.python_version >= 300:
    class CPythonExpressionBuiltinExec( CPythonExpressionBuiltinEval ):
        kind = "EXPRESSION_BUILTIN_EXEC"

        def needsLocalsDict( self ):
            return True

# Note: Python2 only
if Utils.python_version < 300:
    class CPythonExpressionBuiltinExecfile( CPythonExpressionBuiltinEval ):
        kind = "EXPRESSION_BUILTIN_EXECFILE"

        named_children = ( "source", "globals", "locals" )

        def __init__( self, source_code, globals_arg, locals_arg, source_ref ):
            CPythonExpressionBuiltinEval.__init__( self, source_code, globals_arg, locals_arg, source_ref )

        def needsLocalsDict( self ):
            return True


# TODO: Find a place for this. Potentially as an attribute of nodes themselves.
def _couldBeNone( node ):
    if node is None:
        return True
    elif node.isExpressionMakeDict():
        return False
    elif node.isExpressionBuiltinGlobals() or node.isExpressionBuiltinLocals() or \
           node.isExpressionBuiltinDir0() or node.isExpressionBuiltinVars():
        return False
    else:
        # assert False, node
        return True

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

    def setChild( self, name, value ):
        if name in ( "globals", "locals" ):
            value = convertNoneConstantToNone( value )

        return CPythonChildrenHaving.setChild( self, name, value )

    getSourceCode = CPythonChildrenHaving.childGetter( "source" )
    getGlobals = CPythonChildrenHaving.childGetter( "globals" )
    getLocals = CPythonChildrenHaving.childGetter( "locals" )

    def needsLocalsDict( self ):
        return _couldBeNone( self.getGlobals() ) or \
               self.getGlobals().isExpressionBuiltinLocals() or \
               self.getLocals() is not None and self.getLocals().isExpressionBuiltinLocals()


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

    def needsLocalsDict( self ):
        return True
