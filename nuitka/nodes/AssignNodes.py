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
""" Assignment related nodes.

All kinds of assignment targets as well as the assignment statement and expression are
located here. These are the core of value control flow.

"""

from .NodeBases import (
    CPythonExpressionChildrenHavingBase,
    CPythonChildrenHaving,
    CPythonNodeBase
)


class CPythonStatementAssignmentVariable( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_ASSIGNMENT_VARIABLE"

    named_children = ( "source", "variable_ref" )

    def __init__( self, variable_ref, source, source_ref ):
        assert variable_ref is not None
        assert not variable_ref.isExpressionVariableRef()

        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "source"       : source,
                "variable_ref" : variable_ref
            }
        )

    def getDetail( self ):
        return "%s from %s" % ( self.getTargetVariableRef(), self.getAssignSource() )

    getTargetVariableRef = CPythonChildrenHaving.childGetter( "variable_ref" )
    getAssignSource = CPythonChildrenHaving.childGetter( "source" )

    def mayRaiseException( self, exception_type ):
        return self.getAssignSource().mayRaiseException( exception_type )


class CPythonStatementAssignmentAttribute( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_ASSIGNMENT_ATTRIBUTE"

    named_children = ( "source", "expression" )

    def __init__( self, expression, attribute_name, source, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "expression" : expression,
                "source"     : source,
            }
        )

        self.attribute_name = attribute_name

    def getDetails( self ):
        return { "attribute" : self.attribute_name }

    def getDetail( self ):
        return "to attribute %s" % self.attribute_name

    def getAttributeName( self ):
        return self.attribute_name

    getLookupSource = CPythonExpressionChildrenHavingBase.childGetter( "expression" )
    getAssignSource = CPythonExpressionChildrenHavingBase.childGetter( "source" )


class CPythonStatementAssignmentSubscript( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_ASSIGNMENT_SUBSCRIPT"

    named_children = ( "source", "expression", "subscript" )

    def __init__( self, expression, subscript, source, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values     = {
                "source"     : source,
                "expression" : expression,
                "subscript"  : subscript
            }
        )

    getSubscribed = CPythonExpressionChildrenHavingBase.childGetter( "expression" )
    getSubscript = CPythonExpressionChildrenHavingBase.childGetter( "subscript" )
    getAssignSource = CPythonExpressionChildrenHavingBase.childGetter( "source" )


class CPythonStatementAssignmentSlice( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_ASSIGNMENT_SLICE"

    named_children = ( "source", "expression", "lower", "upper" )

    def __init__( self, expression, lower, upper, source, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values     = {
                "source"     : source,
                "expression" : expression,
                "lower"      : lower,
                "upper"      : upper
            }
        )

    getLookupSource = CPythonExpressionChildrenHavingBase.childGetter( "expression" )
    getLower = CPythonExpressionChildrenHavingBase.childGetter( "lower" )
    getUpper = CPythonExpressionChildrenHavingBase.childGetter( "upper" )
    getAssignSource = CPythonExpressionChildrenHavingBase.childGetter( "source" )


class CPythonStatementDelVariable( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_DEL_VARIABLE"

    named_children = ( "variable_ref", )

    def __init__( self, variable_ref, source_ref ):
        assert variable_ref is not None
        assert not variable_ref.isExpressionVariableRef()

        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "variable_ref" : variable_ref
            }
        )

    def getDetail( self ):
        variable_ref = self.getTargetVariableRef()
        variable = variable_ref.getVariable()

        if variable is not None:
            return "to variable %s" % variable
        else:
            return "to variable %s" % self.getTargetVariableRef()

    getTargetVariableRef = CPythonChildrenHaving.childGetter( "variable_ref" )


class CPythonStatementDelAttribute( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_DEL_ATTRIBUTE"

    named_children = ( "expression", )

    def __init__( self, expression, attribute_name, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "expression" : expression
            }
        )

        self.attribute_name = attribute_name

    def getDetails( self ):
        return { "attribute" : self.attribute_name }

    def getDetail( self ):
        return "to attribute %s" % self.attribute_name

    def getAttributeName( self ):
        return self.attribute_name

    getLookupSource = CPythonExpressionChildrenHavingBase.childGetter( "expression" )


class CPythonStatementDelSubscript( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_DEL_SUBSCRIPT"

    named_children = ( "expression", "subscript" )

    def __init__( self, expression, subscript, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values     = {
                "expression" : expression,
                "subscript"  : subscript
            }
        )

    getSubscribed = CPythonExpressionChildrenHavingBase.childGetter( "expression" )
    getSubscript = CPythonExpressionChildrenHavingBase.childGetter( "subscript" )


class CPythonStatementDelSlice( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_DEL_SLICE"

    named_children = ( "expression", "lower", "upper" )

    def __init__( self, expression, lower, upper, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values     = {
                "expression" : expression,
                "lower"      : lower,
                "upper"      : upper
            }
        )

    getLookupSource = CPythonExpressionChildrenHavingBase.childGetter( "expression" )
    getLower = CPythonExpressionChildrenHavingBase.childGetter( "lower" )
    getUpper = CPythonExpressionChildrenHavingBase.childGetter( "upper" )
