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
""" Nodes for functions and their creations.

Lambdas are functions too. The functions are at the core of the language and have their
complexities.

"""

from .NodeBases import (
    CPythonParameterHavingNodeBase,
    CPythonChildrenHaving,
    CPythonClosureTaker,
    CPythonNodeBase
)

from .IndicatorMixins import (
    MarkContainsTryExceptIndicator,
    MarkLocalsDictIndicator,
    MarkGeneratorIndicator,
    MarkExecContainingIndicator
)

from . import OverflowCheck

from nuitka import Variables


class CPythonExpressionLambdaBuilder( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_LAMBDA_BUILDER"

    named_children = ( "defaults", "body" )

    def __init__( self, defaults, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "defaults" : tuple( defaults )
            }
        )

    getBody = CPythonChildrenHaving.childGetter( "body" )
    setBody = CPythonChildrenHaving.childSetter( "body" )

    getDefaultExpressions = CPythonChildrenHaving.childGetter( "defaults" )

    def getCodeName( self ):
        return self.getBody().getCodeName()

    def getClosureVariables( self ):
        return self.getBody().getClosureVariables()

    def getUserLocalVariables( self ):
        return self.getBody().getUserLocalVariables()

    def getTempVariables( self ):
        return self.getBody().getTempVariables()

    def getParameters( self ):
        return self.getBody().getParameters()

    def isGenerator( self ):
        return self.getBody().isGenerator()


class CPythonStatementFunctionBuilder( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_FUNCTION_BUILDER"

    named_children = ( "defaults", "decorators", "target", "body" )

    def __init__( self, target, decorators, defaults, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "target"     : target,
                "decorators" : tuple( decorators ),
                "defaults"   : tuple( defaults )
            }
        )

    def getFunctionName( self ):
        return self.getBody().getName()

    def getCodeName( self ):
        return self.getBody().getCodeName()

    def getClosureVariables( self ):
        return self.getBody().getClosureVariables()

    def getUserLocalVariables( self ):
        return self.getBody().getUserLocalVariables()

    def getTempVariables( self ):
        return self.getBody().getTempVariables()

    def getParameters( self ):
        return self.getBody().getParameters()

    def isGenerator( self ):
        return self.getBody().isGenerator()

    getDecorators = CPythonChildrenHaving.childGetter( "decorators" )
    setDecorators = CPythonChildrenHaving.childSetter( "decorators" )

    getDefaultExpressions = CPythonChildrenHaving.childGetter( "defaults" )

    getTarget = CPythonChildrenHaving.childGetter( "target" )

    getBody = CPythonChildrenHaving.childGetter( "body" )
    setBody = CPythonChildrenHaving.childSetter( "body" )


class CPythonExpressionFunctionBody( CPythonChildrenHaving, CPythonParameterHavingNodeBase, \
                                     CPythonClosureTaker, MarkContainsTryExceptIndicator, \
                                     MarkGeneratorIndicator, MarkLocalsDictIndicator,
                                     MarkExecContainingIndicator ):
    # We really want these many ancestors, as per design, we add properties via base class
    # mixins a lot, pylint: disable=R0901

    kind = "EXPRESSION_FUNCTION_BODY"

    early_closure = False

    named_children = ( "body", )

    def __init__( self, provider, name, doc, parameters, source_ref ):
        CPythonClosureTaker.__init__(
            self,
            provider = provider
        )

        CPythonParameterHavingNodeBase.__init__(
            self,
            name        = name,
            code_prefix = "function",
            parameters  = parameters,
            source_ref  = source_ref
        )

        CPythonChildrenHaving.__init__(
            self,
            values = {}
        )

        MarkContainsTryExceptIndicator.__init__( self )

        MarkGeneratorIndicator.__init__( self )

        MarkLocalsDictIndicator.__init__( self )

        MarkExecContainingIndicator.__init__( self )

        self.parent = provider

        self.doc = doc

    def getDetails( self ):
        return {
            "name"       : self.getFunctionName(),
            "parameters" : self.getParameters()
        }

    def getDetail( self ):
        return "named %s with %s" % ( self.name, self.parameters )

    def getFunctionName( self ):
        return self.name

    def getDoc( self ):
        return self.doc

    def getLocalVariableNames( self ):
        return Variables.getNames( self.getLocalVariables() )

    def getLocalVariables( self ):
        return [
            variable for
            variable in
            self.providing.values()
            if variable.isLocalVariable()
        ]

    def getUserLocalVariables( self ):
        return tuple(
            variable for
            variable in
            self.providing.values()
            if variable.isLocalVariable() and not variable.isParameterVariable()
        )

    def getVariables( self ):
        return self.providing.values()

    def getVariableForAssignment( self, variable_name ):
        # print ( "ASS func", self, variable_name )

        if self.hasTakenVariable( variable_name ):
            result = self.getTakenVariable( variable_name )
        else:
            result = self.getProvidedVariable( variable_name )

        return result

    def getVariableForReference( self, variable_name ):
        # print ( "REF func", self, variable_name )

        if self.hasProvidedVariable( variable_name ):
            result = self.getProvidedVariable( variable_name )
        else:
            if self.hasStaticLocals():
                result = self.getClosureVariable(
                    variable_name = variable_name
                )
            else:
                result = Variables.MaybeLocalVariable(
                    owner            = self,
                    variable_name    = variable_name
                )

            # Remember that we need that closure for something.
            self.registerProvidedVariable( result )

        return result

    def getVariableForClosure( self, variable_name ):
        if self.hasProvidedVariable( variable_name ):
            return self.getProvidedVariable( variable_name )
        else:
            return self.provider.getVariableForClosure( variable_name )

    def createProvidedVariable( self, variable_name ):
        return Variables.LocalVariable(
            owner         = self,
            variable_name = variable_name
        )

    def hasStaticLocals( self ):
        return not OverflowCheck.check( self.getBody() )

    getBody = CPythonChildrenHaving.childGetter( "body" )
    setBody = CPythonChildrenHaving.childSetter( "body" )
