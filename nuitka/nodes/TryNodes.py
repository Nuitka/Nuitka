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
""" Nodes for try/except and try/finally

The try/except needs handlers, and these blocks are complex control flow.

"""

from .NodeBases import CPythonChildrenHaving, CPythonNodeBase


class CPythonStatementTryFinally( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_TRY_FINALLY"

    named_children = ( "tried", "final" )

    def __init__( self, tried, final, source_ref ):
        CPythonChildrenHaving.__init__(
            self,
            values = {
                "tried" : tried,
                "final" : final
            }
        )

        CPythonNodeBase.__init__( self, source_ref = source_ref )

    getBlockTry = CPythonChildrenHaving.childGetter( "tried" )
    getBlockFinal = CPythonChildrenHaving.childGetter( "final" )

    def isStatementAbortative( self ):
        return self.getBlockTry().isStatementAbortative()


class CPythonStatementExceptHandler( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_EXCEPT_HANDLER"

    named_children = ( "exception_types", "body" )

    def __init__( self, exception_types, body, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "exception_types" : tuple( exception_types ),
                "body"            : body,
            }
        )

    getExceptionTypes  = CPythonChildrenHaving.childGetter( "exception_types" )
    getExceptionBranch = CPythonChildrenHaving.childGetter( "body" )
    setExceptionBranch = CPythonChildrenHaving.childSetter( "body" )


class CPythonStatementTryExcept( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_TRY_EXCEPT"

    named_children = ( "tried", "handlers" )

    def __init__( self, tried, handlers, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "tried"    : tried,
                "handlers" : tuple( handlers )
            }
        )

    getBlockTry = CPythonChildrenHaving.childGetter( "tried" )
    getExceptionHandlers = CPythonChildrenHaving.childGetter( "handlers" )

    def isStatementAbortative( self ):
        if not self.getBlockTry().isStatementAbortative():
            return False

        for handler in self.getExceptionHandlers():
            if not handler.isStatementAbortative():
                return False

        return True
