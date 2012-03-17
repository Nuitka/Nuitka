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
""" Loop nodes.

There are for and loop nodes, and the break/continue statements for it. Loops are a very
difficult topic, and it might be that the two forms need to be reduced to one common form,
which is more general, the 'Forever' loop, with breaks

"""

from .NodeBases import CPythonChildrenHaving, CPythonNodeBase

from .IndicatorMixins import MarkExceptionBreakContinueIndicator


class CPythonStatementForLoop( CPythonChildrenHaving, CPythonNodeBase, \
                               MarkExceptionBreakContinueIndicator ):
    kind = "STATEMENT_FOR_LOOP"

    named_children = ( "iterator", "target", "body", "else" )

    def __init__( self, iterator, target, body, no_break, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "iterator" : iterator,
                "target"   : target,
                "else"     : no_break,
                "body"     : body
            }
        )

        MarkExceptionBreakContinueIndicator.__init__( self )

    getIterator = CPythonChildrenHaving.childGetter( "iterator" )
    getLoopVariableAssignment = CPythonChildrenHaving.childGetter( "target" )
    getLoopBody = CPythonChildrenHaving.childGetter( "body" )
    setLoopBody = CPythonChildrenHaving.childSetter( "body" )
    getNoBreak = CPythonChildrenHaving.childGetter( "else" )
    setNoBreak = CPythonChildrenHaving.childSetter( "else" )


class CPythonStatementWhileLoop( CPythonChildrenHaving, CPythonNodeBase, \
                                 MarkExceptionBreakContinueIndicator ):
    kind = "STATEMENT_WHILE_LOOP"

    named_children = ( "condition", "frame", "else" )

    def __init__( self, condition, body, no_break, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "condition" : condition,
                "else"      : no_break,
                "frame"     : body
            }
        )

        MarkExceptionBreakContinueIndicator.__init__( self )

    getLoopBody = CPythonChildrenHaving.childGetter( "frame" )
    getCondition = CPythonChildrenHaving.childGetter( "condition" )
    getNoBreak = CPythonChildrenHaving.childGetter( "else" )



class CPythonStatementContinueLoop( CPythonNodeBase, MarkExceptionBreakContinueIndicator ):
    kind = "STATEMENT_CONTINUE_LOOP"

    def __init__( self, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )
        MarkExceptionBreakContinueIndicator.__init__( self )


class CPythonStatementBreakLoop( CPythonNodeBase, MarkExceptionBreakContinueIndicator ):
    kind = "STATEMENT_BREAK_LOOP"

    def __init__( self, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )
        MarkExceptionBreakContinueIndicator.__init__( self )
