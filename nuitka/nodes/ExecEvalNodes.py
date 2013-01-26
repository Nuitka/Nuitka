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
""" Nodes concern with exec and eval builtins.

These are the dynamic codes, and as such rather difficult. We would like
to eliminate or limit their impact as much as possible, but it's difficult
to do.
"""

from .NodeBases import (
    CPythonExpressionChildrenHavingBase,
    CPythonChildrenHaving,
    CPythonNodeBase
)

from nuitka import Utils

class CPythonExpressionBuiltinEval( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_BUILTIN_EVAL"

    named_children = ( "source", "globals", "locals" )

    # Need to accept globals and local keyword argument, that is just the API of eval,
    # pylint: disable=W0622

    def __init__( self, source, globals, locals, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "source"  : source,
                "globals" : globals,
                "locals"  : locals,
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
            from .NodeMakingHelpers import convertNoneConstantToNone

            value = convertNoneConstantToNone( value )

        return CPythonChildrenHaving.setChild( self, name, value )

    getSourceCode = CPythonChildrenHaving.childGetter( "source" )
    getGlobals = CPythonChildrenHaving.childGetter( "globals" )
    getLocals = CPythonChildrenHaving.childGetter( "locals" )

    def needsLocalsDict( self ):
        return _couldBeNone( self.getGlobals() ) or \
               self.getGlobals().isExpressionBuiltinLocals() or \
               self.getLocals() is not None and self.getLocals().isExpressionBuiltinLocals()
