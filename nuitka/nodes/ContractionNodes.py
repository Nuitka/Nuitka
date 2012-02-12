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
""" Contraction nodes

These ones should probably all become replaced with 'for' loop lambda functions. and not
exist at all. Right now they exist, because we have fast code generation for them, but
that may not last, as soon as we can optimize those 'for' loop things to the same level or
higher in terms of efficiency.
"""

from .NodeBases import (
    CPythonExpressionChildrenHavingBase,
    CPythonClosureGiverNodeBase,
    CPythonExpressionMixin,
    CPythonChildrenHaving,
    CPythonClosureTaker
)

from .IndicatorMixins import MarkGeneratorIndicator

from nuitka import Variables


class CPythonExpressionContractionBuilderBase( CPythonExpressionChildrenHavingBase ):
    named_children = ( "source0", "body" )

    def __init__( self, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {},
            source_ref = source_ref
        )

    setSource0 = CPythonExpressionChildrenHavingBase.childSetter( "source0" )
    getSource0 = CPythonExpressionChildrenHavingBase.childGetter( "source0" )

    setBody = CPythonExpressionChildrenHavingBase.childSetter( "body" )
    getBody = CPythonExpressionChildrenHavingBase.childGetter( "body" )

    def getTargets( self ):
        return self.getBody().getTargets()

    def getInnerSources( self ):
        return self.getBody().getSources()

    def getConditions( self ):
        return self.getBody().getConditions()

    def getCodeName( self ):
        return self.getBody().getCodeName()

    def getClosureVariables( self ):
        return self.getBody().getClosureVariables()

    def getProvidedVariables( self ):
        return self.getBody().getProvidedVariables()

    def getTempVariables( self ):
        return self.getBody().getTempVariables()

    def computeNode( self ):
        return self, None, None

    def isKnownToBeIterable( self, count ):
        return None


class CPythonExpressionContractionBodyBase( CPythonChildrenHaving, CPythonClosureTaker, \
                                            CPythonClosureGiverNodeBase, \
                                            CPythonExpressionMixin ):
    early_closure = False

    named_children = ( "sources", "body", "conditions", "targets" )

    def __init__( self, code_prefix, provider, source_ref ):
        CPythonClosureTaker.__init__(
            self,
            provider = provider
        )

        CPythonClosureGiverNodeBase.__init__(
            self,
            name        = code_prefix,
            code_prefix = code_prefix,
            source_ref  = source_ref
        )

        CPythonChildrenHaving.__init__(
            self,
            values = {}
        )

    setSources = CPythonChildrenHaving.childSetter( "sources" )
    getSources = CPythonChildrenHaving.childGetter( "sources" )

    setConditions = CPythonChildrenHaving.childSetter( "conditions" )
    getConditions = CPythonChildrenHaving.childGetter( "conditions" )

    setTargets = CPythonChildrenHaving.childSetter( "targets" )
    getTargets = CPythonChildrenHaving.childGetter( "targets" )

    getBody = CPythonChildrenHaving.childGetter( "body" )
    setBody = CPythonChildrenHaving.childSetter( "body" )

    def getVariableForReference( self, variable_name ):
        # print ( "REF", self, variable_name )

        if self.hasProvidedVariable( variable_name ):
            return self.getProvidedVariable( variable_name )
        else:
            return self.getClosureVariable( variable_name )

    def getVariableForAssignment( self, variable_name ):
        # print ( "ASS", self, variable_name )

        result = self.getProvidedVariable( variable_name )

        # Check if it's a local variable, or a list contraction closure,
        # pylint: disable=E1101
        assert result.isLocalVariable() or self.isExpressionListContractionBody()

        return result

    def getVariableForClosure( self, variable_name ):
        if self.hasProvidedVariable( variable_name ):
            return self.getProvidedVariable( variable_name )
        else:
            return self.provider.getVariableForClosure( variable_name )

    def getVariables( self ):
        return self.providing.values()

    def computeNode( self ):
        return self, None, None


class CPythonExpressionListContractionBuilder( CPythonExpressionContractionBuilderBase ):
    kind = "EXPRESSION_LIST_CONTRACTION_BUILDER"

    def __init__( self, source_ref ):
        CPythonExpressionContractionBuilderBase.__init__( self, source_ref )


class CPythonExpressionListContractionBody( CPythonExpressionContractionBodyBase ):
    kind = "EXPRESSION_LIST_CONTRACTION_BODY"

    def __init__( self, provider, source_ref ):
        CPythonExpressionContractionBodyBase.__init__(
            self,
            code_prefix = "listcontr",
            provider    = provider,
            source_ref  = source_ref
        )

    def createProvidedVariable( self, variable_name ):
        # Make sure the provider knows it has to provide a variable of this name for
        # the assigment.
        self.provider.getVariableForAssignment(
            variable_name = variable_name
        )

        return self.getClosureVariable(
            variable_name = variable_name
        )


class CPythonExpressionGeneratorBuilder( CPythonExpressionContractionBuilderBase ):
    kind = "EXPRESSION_GENERATOR_BUILDER"

    def __init__( self, source_ref ):
        CPythonExpressionContractionBuilderBase.__init__( self, source_ref )


class CPythonExpressionGeneratorBody( CPythonExpressionContractionBodyBase, MarkGeneratorIndicator ):
    kind = "EXPRESSION_GENERATOR_BODY"

    def __init__( self, provider, source_ref ):
        CPythonExpressionContractionBodyBase.__init__(
            self,
            code_prefix = "genexpr",
            provider    = provider,
            source_ref  = source_ref
        )

        MarkGeneratorIndicator.__init__( self )

    def createProvidedVariable( self, variable_name ):
        return Variables.LocalVariable(
            owner         = self,
            variable_name = variable_name
        )

class CPythonExpressionSetContractionBuilder( CPythonExpressionContractionBuilderBase ):
    kind = "EXPRESSION_SET_CONTRACTION_BUILDER"

    def __init__( self, source_ref ):
        CPythonExpressionContractionBuilderBase.__init__( self, source_ref )


class CPythonExpressionSetContractionBody( CPythonExpressionContractionBodyBase ):
    kind = "EXPRESSION_SET_CONTRACTION_BODY"

    def __init__( self, provider, source_ref ):
        CPythonExpressionContractionBodyBase.__init__(
            self,
            code_prefix = "setcontr",
            provider    = provider,
            source_ref  = source_ref
        )

    def createProvidedVariable( self, variable_name ):
        return Variables.LocalVariable(
            owner         = self,
            variable_name = variable_name
        )


class CPythonExpressionDictContractionBuilder( CPythonExpressionContractionBuilderBase ):
    kind = "EXPRESSION_DICT_CONTRACTION_BUILDER"

    def __init__( self, source_ref ):
        CPythonExpressionContractionBuilderBase.__init__( self, source_ref )


class CPythonExpressionDictContractionBody( CPythonExpressionContractionBodyBase ):
    kind = "EXPRESSION_DICT_CONTRACTION_BODY"

    def __init__( self, provider, source_ref ):
        CPythonExpressionContractionBodyBase.__init__(
            self,
            code_prefix = "dictcontr",
            provider    = provider,
            source_ref  = source_ref
        )

    def createProvidedVariable( self, variable_name ):
        return Variables.LocalVariable(
            owner         = self,
            variable_name = variable_name
        )
