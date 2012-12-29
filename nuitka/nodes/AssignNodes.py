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
        assert variable_ref is not None, source_ref
        assert source is not None, source_ref

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
