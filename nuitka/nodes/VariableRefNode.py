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
""" Node for variable references.

These represent all variable references in the node tree. Can be in assignments and it
expressions, changing the meaning of course dramatically.

"""

from nuitka import Variables, Builtins

from .NodeBases import CPythonChildrenHaving, CPythonNodeBase, CPythonExpressionMixin

from .BuiltinReferenceNodes import (
    CPythonExpressionBuiltinExceptionRef,
    CPythonExpressionBuiltinRef
)

from .ConstantRefNode import CPythonExpressionConstantRef

def _isReadOnlyModuleVariable( variable ):
    return ( variable.isModuleVariable() and variable.getReadOnlyIndicator() is True ) or \
           variable.isMaybeLocalVariable()

class CPythonExpressionVariableRef( CPythonNodeBase, CPythonExpressionMixin ):
    kind = "EXPRESSION_VARIABLE_REF"

    def __init__( self, variable_name, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        self.variable_name = variable_name
        self.variable = None

    def getDetails( self ):
        if self.variable is None:
            return { "name" : self.variable_name }
        else:
            return { "name" : self.variable_name, "variable" : self.variable }

    def getDetail( self ):
        if self.variable is None:
            return self.variable_name
        else:
            return repr( self.variable )

    def makeCloneAt( self, source_ref ):
        assert self.variable is None

        return CPythonExpressionVariableRef(
            variable_name = self.variable_name,
            source_ref    = source_ref
        )

    def getVariableName( self ):
        return self.variable_name

    def getVariable( self ):
        return self.variable

    def setVariable( self, variable, replace = False ):
        assert isinstance( variable, Variables.Variable ), repr( variable )

        assert self.variable is None or replace

        self.variable = variable

    def computeNode( self ):
        assert self.variable is not None

        if _isReadOnlyModuleVariable( self.variable ):
            if self.variable_name in Builtins.builtin_exception_names:
                new_node = CPythonExpressionBuiltinExceptionRef(
                    exception_name = self.variable_name,
                    source_ref     = self.getSourceReference()
                )

                # TODO: More like "removed_variable and new_constant" probably
                change_tags = "new_builtin"
                change_desc = "Module variable '%s' found to be builtin exception reference." % self.variable_name
            elif self.variable_name in Builtins.builtin_names:
                new_node = CPythonExpressionBuiltinRef(
                    builtin_name = self.variable_name,
                    source_ref   = self.getSourceReference()
                )

                # TODO: More like "removed_variable and new_constant" probably
                change_tags = "new_builtin"
                change_desc = "Module variable '%s' found to be builtin reference." % self.variable_name
            elif self.variable_name == "__name__":
                new_node = CPythonExpressionConstantRef(
                    constant   = self.variable.getReferenced().getOwner().getName(),
                    source_ref = self.getSourceReference()
                )

                change_tags = "new_constant"
                change_desc = "Replaced read-only module attribute '__name__' with constant value."
            elif self.variable_name == "__doc__":
                new_node = CPythonExpressionConstantRef(
                    constant   = self.variable.getReferenced().getOwner().getDoc(),
                    source_ref = self.getSourceReference()
                )

                change_tags = "new_constant"
                change_desc = "Replaced read-only module attribute '__doc__' with constant value."
            elif self.variable_name == "__package__":
                new_node = CPythonExpressionConstantRef(
                    constant   = self.variable.getReferenced().getOwner().getPackage(),
                    source_ref = self.getSourceReference()
                )

                change_tags = "new_constant"
                change_desc = "Replaced read-only module attribute '__package__' with constant value."
            elif self.variable_name == "__file__":
                # TODO: We have had talks of this becoming more dynamic, but currently it isn't so.
                new_node = CPythonExpressionConstantRef(
                    constant   = self.variable.getReferenced().getOwner().getFilename(),
                    source_ref = self.getSourceReference()
                )

                change_tags = "new_constant"
                change_desc = "Replaced read-only module attribute '__file__' with constant value."
            else:
                # Probably should give a warning once about it.
                new_node = self
                change_tags = None
                change_desc = None

            return new_node, change_tags, change_desc

        return self, None, None

    def isKnownToBeIterable( self, count ):
        return None


class CPythonExpressionTempVariableRef( CPythonNodeBase, CPythonExpressionMixin ):
    kind = "EXPRESSION_TEMP_VARIABLE_REF"

    def __init__( self, variable, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        self.variable = variable

    def getDetails( self ):
        return { "name" : self.variable.getName() }

    def getDetail( self ):
        return self.variable.getName()

    def getVariableName( self ):
        return self.variable.getName()

    def getVariable( self ):
        return self.variable

    def computeNode( self ):
        # Nothing to do here.
        return self, None, None


class CPythonStatementTempBlock( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_TEMP_BLOCK"

    named_children = ( "body", )

    getBody = CPythonChildrenHaving.childGetter( "body" )
    setBody = CPythonChildrenHaving.childSetter( "body" )

    def __init__( self, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "body" : None
            }
        )

        self.temp_variables = set()

    def getTempVariable( self, name ):
        assert name not in self.temp_variables

        result = Variables.TempVariable(
            owner         = self,
            variable_name = "__tmp_%s" % name
        )

        self.temp_variables.add( result )

        return result

    def getTempVariables( self ):
        return self.temp_variables
