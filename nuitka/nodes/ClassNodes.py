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
""" Nodes for classes and their creations.

The classes are are at the core of the language and have their complexities.

"""

from .NodeBases import (
    CPythonChildrenHaving,
    CPythonCodeNodeBase,
    CPythonClosureTaker,
    CPythonNodeBase
)

from .IndicatorMixins import (
    MarkContainsTryExceptIndicator,
    MarkLocalsDictIndicator,
)

from nuitka import Variables

class CPythonExpressionClassBody( CPythonChildrenHaving, CPythonClosureTaker, CPythonCodeNodeBase, \
                                  MarkContainsTryExceptIndicator, MarkLocalsDictIndicator ):
    kind = "EXPRESSION_CLASS_BODY"

    early_closure = True

    named_children = ( "body", )

    def __init__( self, provider, name, doc, source_ref ):
        CPythonCodeNodeBase.__init__(
            self,
            name        = name,
            code_prefix = "class",
            source_ref  = source_ref
        )

        CPythonClosureTaker.__init__(
            self,
            provider = provider,
        )

        CPythonChildrenHaving.__init__(
            self,
            values = {}
        )

        MarkContainsTryExceptIndicator.__init__( self )

        MarkLocalsDictIndicator.__init__( self )

        self.doc = doc

        self.variables = {}

        self._addClassVariable(
            variable_name = "__module__"
        )
        self._addClassVariable(
            variable_name = "__doc__"
        )

    getBody = CPythonChildrenHaving.childGetter( "body" )
    setBody = CPythonChildrenHaving.childSetter( "body" )

    def getClassName( self ):
        return self.getName()

    def getDoc( self ):
        return self.doc

    def _addClassVariable( self, variable_name ):
        result = Variables.ClassVariable(
            owner         = self,
            variable_name = variable_name
        )

        self.variables[ variable_name ] = result

        return result

    def getVariableForAssignment( self, variable_name ):
        # print( "ASS class", variable_name, self )

        if self.hasTakenVariable( variable_name ):
            result = self.getTakenVariable( variable_name )

            if result.isClassVariable() and result.getOwner() == self:
                return result

            if result.isModuleVariableReference() and result.isFromGlobalStatement():
                return result

        return self._addClassVariable(
            variable_name = variable_name
        )

    def getVariableForReference( self, variable_name ):
        # print( "REF class", variable_name, self )

        if variable_name in self.variables:
            return self.variables[ variable_name ]
        else:
            return self.getClosureVariable( variable_name )

    def getVariableForClosure( self, variable_name ):
        if variable_name in self.variables:
            return self.variables[ variable_name ]
        else:
            return self.provider.getVariableForClosure( variable_name )

    def reconsiderVariable( self, variable ):
        pass

    def getClassVariables( self ):
        return self.variables.values()

    getVariables = getClassVariables


class CPythonExpressionClassBodyBased( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_CLASS_BODY_BASED"

    named_children = ( "bases", "class_body", )

    def __init__( self, bases, class_body, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "class_body" : class_body,
                "bases"      : tuple( bases ),
            }
        )

    getClassBody = CPythonChildrenHaving.childGetter( "class_body" )
    getBases = CPythonChildrenHaving.childGetter( "bases" )
