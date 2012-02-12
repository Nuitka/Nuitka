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


class CPythonStatementExceptHandler( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_EXCEPT_HANDLER"

    named_children = ( "exception_type", "target", "body" )

    def __init__( self, exception_type, target, body, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "exception_type" : exception_type,
                "target"         : target,
                "body"           : body,
            }
        )

    getExceptionType   = CPythonChildrenHaving.childGetter( "exception_type" )
    getExceptionTarget = CPythonChildrenHaving.childGetter( "target" )
    getExceptionBranch = CPythonChildrenHaving.childGetter( "body" )


class CPythonStatementTryExcept( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_TRY_EXCEPT"

    named_children = ( "tried", "handlers", "no_raise" )

    def __init__( self, tried, no_raise, handlers, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "tried"    : tried,
                "handlers" : tuple( handlers ),
                "no_raise" : no_raise
            }
        )

    getBlockTry = CPythonChildrenHaving.childGetter( "tried" )
    getBlockNoRaise = CPythonChildrenHaving.childGetter( "no_raise" )
    getExceptionHandlers = CPythonChildrenHaving.childGetter( "handlers" )
