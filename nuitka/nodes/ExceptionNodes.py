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
""" Nodes related to raising and making exceptions.

"""

from .NodeBases import (
    CPythonExpressionChildrenHavingBase,
    CPythonChildrenHaving,
    CPythonNodeBase
)

class CPythonStatementRaiseException( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_RAISE_EXCEPTION"

    named_children = ( "exception_type", "exception_value", "exception_trace" )

    def __init__( self, exception_type, exception_value, exception_trace, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        if exception_type is None:
            assert exception_value is None

        if exception_value is None:
            assert exception_trace is None

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "exception_type"  : exception_type,
                "exception_value" : exception_value,
                "exception_trace" : exception_trace,
            }
        )

        self.reraise_local = False

    getExceptionType = CPythonChildrenHaving.childGetter( "exception_type" )
    getExceptionValue = CPythonChildrenHaving.childGetter( "exception_value" )
    getExceptionTrace = CPythonChildrenHaving.childGetter( "exception_trace" )

    def isReraiseException( self ):
        return self.getExceptionType() is None

    def isReraiseExceptionLocal( self ):
        assert self.isReraiseException()

        return self.reraise_local

    def markAsReraiseLocal( self ):
        self.reraise_local = True


class CPythonExpressionRaiseException( CPythonExpressionChildrenHavingBase ):
    """ This node type is only produced via optimization.

    CPython only knows exception raising as a statement, but often the raising
    of exceptions can be predicted to occur as part of an expression, which it
    replaces then.

    The side_effects is there, to represent that an exception is to be raised
    after doing certain things first.
    """

    kind = "EXPRESSION_RAISE_EXCEPTION"

    named_children = ( "side_effects", "exception_type", "exception_value" )

    def __init__( self, exception_type, exception_value, side_effects, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "exception_type"  : exception_type,
                "exception_value" : exception_value,
                "side_effects"    : tuple( side_effects )
            },
            source_ref = source_ref
        )

    getExceptionType = CPythonExpressionChildrenHavingBase.childGetter( "exception_type" )
    getExceptionValue = CPythonExpressionChildrenHavingBase.childGetter( "exception_value" )
    getSideEffects = CPythonExpressionChildrenHavingBase.childGetter( "side_effects" )

    def addSideEffects( self, side_effects ):
        self.setChild( "side_effects", tuple( side_effects ) + self.getSideEffects() )

    def computeNode( self ):
        return self, None, None


class CPythonExpressionBuiltinMakeException( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_BUILTIN_MAKE_EXCEPTION"

    named_children = ( "args", )

    def __init__( self, exception_name, args, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "args" : tuple( args ),
            },
            source_ref = source_ref
        )

        self.exception_name = exception_name

    def getDetails( self ):
        return { "exception_name" : self.exception_name }

    def getExceptionName( self ):
        return self.exception_name

    getArgs = CPythonExpressionChildrenHavingBase.childGetter( "args" )
