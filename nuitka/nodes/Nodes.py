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
""" Node classes for the analysis tree.

These nodes form a tree created by tree building process. Then all analysis
works on it. Optimizations are frequently transformations of the tree.

"""

from nuitka import (
    Variables,
    Utils
)

from .IndicatorMixins import (
    MarkExceptionBreakContinueIndicator,
    MarkContainsTryExceptIndicator,
    MarkLocalsDictIndicator,
    MarkGeneratorIndicator,
)

from .NodeBases import (
    CPythonNodeBase,
    CPythonCodeNodeBase,
    CPythonChildrenHaving,
    CPythonClosureTaker,
    CPythonClosureGiverNodeBase,
    CPythonExpressionBuiltinSingleArgBase,
)

class CPythonModule( CPythonChildrenHaving, CPythonClosureTaker, CPythonClosureGiverNodeBase, \
                     MarkContainsTryExceptIndicator ):
    """ Module

        The module is the only possible root of a tree. When there are many modules
        they form a forrest.
    """

    kind = "MODULE"

    early_closure = True

    named_children = ( "body", )

    def __init__( self, name, package, source_ref ):
        assert type(name) is str, type(name)
        assert "." not in name
        assert package is None or ( type( package ) is str and package != "" )

        CPythonClosureGiverNodeBase.__init__(
            self,
            name        = name,
            code_prefix = "module",
            source_ref  = source_ref
        )

        CPythonClosureTaker.__init__(
            self,
            provider = self
        )

        CPythonChildrenHaving.__init__(
            self,
            values = {}
        )

        MarkContainsTryExceptIndicator.__init__( self )

        self.package = package
        self.doc = None

        self.variables = set()

    def getDetails( self ):
        return { "filename" : self.source_ref.getFilename()  }

    getBody = CPythonChildrenHaving.childGetter( "body" )
    setBody = CPythonChildrenHaving.childSetter( "body" )

    def getVariables( self ):
        return self.variables

    def getDoc( self ):
        return self.doc

    def setDoc( self, doc ):
        self.doc = doc

    def getFilename( self ):
        return self.source_ref.getFilename()

    def getPackage( self ):
        return self.package

    def getFullName( self ):
        if self.package:
            return self.package + "." + self.getName()
        else:
            return self.getName()

    def getVariableForAssignment( self, variable_name ):
        result = self.getProvidedVariable( variable_name )

        return result.makeReference( self )

    def getVariableForReference( self, variable_name ):
        result = self.getProvidedVariable( variable_name )

        return result.makeReference( self )

    def getVariableForClosure( self, variable_name ):
        return self.getProvidedVariable(
            variable_name = variable_name
        )

    def createProvidedVariable( self, variable_name ):
        result = Variables.ModuleVariable(
            module        = self,
            variable_name = variable_name
        )

        assert result not in self.variables
        self.variables.add( result )

        return result

    def isEarlyClosure( self ):
        return True

    def getCodeName( self ):
        return "module_" + self.getFullName().replace( ".", "__" ).replace( "-", "_" )

class CPythonPackage( CPythonModule ):
    kind = "PACKAGE"

    def __init__( self, name, package, source_ref ):
        CPythonModule.__init__(
            self,
            name       = name,
            package    = package,
            source_ref = source_ref
        )

    def getPathAttribute( self ):
        return [ Utils.dirname( self.getFilename() ) ]


class CPythonStatementClassBuilder( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_CLASS_BUILDER"

    named_children = ( "bases", "decorators", "target", "body", )

    def __init__( self, target, bases, decorators, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "target"     : target,
                "decorators" : tuple( decorators ),
                "bases"      : tuple( bases ),
            }
        )

    getBaseClasses = CPythonChildrenHaving.childGetter( "bases" )
    getDecorators = CPythonChildrenHaving.childGetter( "decorators" )

    getBody = CPythonChildrenHaving.childGetter( "body" )
    setBody = CPythonChildrenHaving.childSetter( "body" )

    getTarget = CPythonChildrenHaving.childGetter( "target" )

    def getClassName( self ):
        return self.getBody().getName()

    def getCodeName( self ):
        return self.getBody().getCodeName()

    def getClosureVariables( self ):
        return self.getBody().getClosureVariables()

    def getClassVariables( self ):
        return self.getBody().getClassVariables()

    def getTempVariables( self ):
        return self.getBody().getTempVariables()


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



class CPythonAssignTargetVariable( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "ASSIGN_TARGET_VARIABLE"

    named_children = ( "variable_ref", )

    def __init__( self, variable_ref, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "variable_ref" : variable_ref,
            }
        )

    def getDetail( self ):
        return "to variable %s" % self.getTargetVariableRef()

    getTargetVariableRef = CPythonChildrenHaving.childGetter( "variable_ref" )

class CPythonAssignTargetAttribute( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "ASSIGN_TARGET_ATTRIBUTE"

    named_children = ( "expression", )

    def __init__( self, expression, attribute_name, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "expression" : expression,
            }
        )

        self.attribute_name = attribute_name

    def getDetails( self ):
        return { "attribute" : self.attribute_name }

    def getDetail( self ):
        return "to attribute %s" % self.attribute_name

    def getAttributeName( self ):
        return self.attribute_name

    getLookupSource = CPythonChildrenHaving.childGetter( "expression" )


class CPythonAssignTargetSubscript( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "ASSIGN_TARGET_SUBSCRIPT"

    named_children = ( "expression", "subscript" )

    def __init__( self, expression, subscript, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "expression" : expression,
                "subscript"  : subscript
            }
        )

    getSubscribed = CPythonChildrenHaving.childGetter( "expression" )
    getSubscript = CPythonChildrenHaving.childGetter( "subscript" )


class CPythonAssignTargetSlice( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "ASSIGN_TARGET_SLICE"

    named_children = ( "expression", "lower", "upper" )

    def __init__( self, expression, lower, upper, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "expression" : expression,
                "lower"      : lower,
                "upper"      : upper
            }
        )

    getLookupSource = CPythonChildrenHaving.childGetter( "expression" )
    getUpper = CPythonChildrenHaving.childGetter( "upper" )
    getLower = CPythonChildrenHaving.childGetter( "lower" )


class CPythonAssignTargetTuple( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "ASSIGN_TARGET_TUPLE"

    named_children = ( "elements", )

    def __init__( self, elements, source_ref ):
        self.elements = elements[:]

        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "elements" : tuple( elements ),
            }
        )

    getElements = CPythonChildrenHaving.childGetter( "elements" )

class CPythonStatementAssignment( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_ASSIGNMENT"

    named_children = ( "source", "targets" )

    def __init__( self, targets, expression, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "source"  : expression,
                "targets" : tuple( targets )
            }
        )

    def getDetail( self ):
        targets = self.getTargets()

        targets = [ target.getDetail() for target in targets ]

        if len( targets ) == 1:
            targets = targets[0]

        return "%s from %s" % ( targets, self.getSource() )

    getTargets = CPythonChildrenHaving.childGetter( "targets" )
    getSource = CPythonChildrenHaving.childGetter( "source" )


class CPythonExpressionAssignment( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_ASSIGNMENT"

    named_children = ( "source", "target" )

    def __init__( self, target, source, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "source" : source,
                "target" : target
            }
        )

    def getDetail( self ):
        return "%s from %s" % ( self.getTarget(), self.getSource() )

    getTarget = CPythonChildrenHaving.childGetter( "target" )
    getSource = CPythonChildrenHaving.childGetter( "source" )


class CPythonStatementAssignmentInplace( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_ASSIGNMENT_INPLACE"

    named_children = ( "target", "expression" )

    def __init__( self, target, operator, expression, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "expression" : expression,
                "target"     : target
            }
        )

        self.operator = operator

    def getDetail( self ):
        return "to %s" % self.getTarget()

    def getOperator( self ):
        return self.operator

    getTarget = CPythonChildrenHaving.childGetter( "target" )
    getExpression = CPythonChildrenHaving.childGetter( "expression" )



class CPythonExpressionYield( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_YIELD"

    named_children = ( "expression", )

    def __init__( self, expression, for_return, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "expression" : expression
            }
        )

        self.for_return = for_return

    def isForReturn( self ):
        return self.for_return

    getExpression = CPythonChildrenHaving.childGetter( "expression" )


class CPythonStatementReturn( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_RETURN"

    named_children = ( "expression", )

    def __init__( self, expression, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "expression" : expression
            }
        )

    getExpression = CPythonChildrenHaving.childGetter( "expression" )


class CPythonStatementPrint( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_PRINT"

    named_children = ( "dest", "values" )

    def __init__( self, dest, values, newline, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "values" : tuple( values ),
                "dest"   : dest
            }
        )

        self.newline = newline


    def isNewlinePrint( self ):
        return self.newline

    getDestination = CPythonChildrenHaving.childGetter( "dest" )
    getValues = CPythonChildrenHaving.childGetter( "values" )


class CPythonExpressionFunctionCall( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_FUNCTION_CALL"

    named_children = ( "called", "positional_args", "pairs", "list_star_arg", "dict_star_arg" )

    def __init__( self, called_expression, positional_args, pairs, list_star_arg, dict_star_arg, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        assert called_expression.isExpression()

        for positional_arg in positional_args:
            assert positional_arg.isExpression()

        assert type( pairs ) in ( list, tuple ), pairs

        for pair in pairs:
            assert pair.isExpressionKeyValuePair()

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "called"          : called_expression,
                "positional_args" : tuple( positional_args ),
                "pairs"           : tuple( pairs ),
                "list_star_arg"   : list_star_arg,
                "dict_star_arg"   : dict_star_arg
           }
        )

        assert self.getChild( "called" ) is called_expression

    getCalled = CPythonChildrenHaving.childGetter( "called" )
    getPositionalArguments = CPythonChildrenHaving.childGetter( "positional_args" )
    setPositionalArguments = CPythonChildrenHaving.childSetter( "positional_args" )
    getNamedArgumentPairs = CPythonChildrenHaving.childGetter( "pairs" )
    setNamedArgumentPairs = CPythonChildrenHaving.childSetter( "pairs" )
    getStarListArg = CPythonChildrenHaving.childGetter( "list_star_arg" )
    setStarListArg = CPythonChildrenHaving.childSetter( "list_star_arg" )
    getStarDictArg = CPythonChildrenHaving.childGetter( "dict_star_arg" )
    setStarDictArg = CPythonChildrenHaving.childSetter( "dict_star_arg" )

    def isEmptyCall( self ):
        return not self.getPositionalArguments() and not self.getNamedArgumentPairs() and \
               not self.getStarListArg() and not self.getStarDictArg()

    def hasOnlyPositionalArguments( self ):
        return not self.getNamedArgumentPairs() and not self.getStarListArg() and \
               not self.getStarDictArg()

    def hasOnlyConstantArguments( self ):
        for positional_arg in self.getPositionalArguments():
            if not positional_arg.isExpressionConstantRef():
                return False

        for pair in self.getNamedArgumentPairs():
            if not pair.getKey().isExpressionConstantRef():
                return False

            if not pair.getValue().isExpressionConstantRef():
                return False

        list_star_arg = self.getStarListArg()

        if list_star_arg is not None and not list_star_arg.isExpressionConstantRef():
            return False

        dict_star_arg = self.getStarDictArg()

        if dict_star_arg is not None and not dict_star_arg.isExpressionConstantRef():
            return False

        return True


class CPythonExpressionContractionBuilderBase( CPythonChildrenHaving, CPythonNodeBase ):
    named_children = ( "source0", "body" )

    def __init__( self, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {}
        )

    setSource0 = CPythonChildrenHaving.childSetter( "source0" )
    getSource0 = CPythonChildrenHaving.childGetter( "source0" )

    setBody = CPythonChildrenHaving.childSetter( "body" )
    getBody = CPythonChildrenHaving.childGetter( "body" )

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


class CPythonExpressionContractionBodyBase( CPythonChildrenHaving, CPythonClosureTaker, CPythonClosureGiverNodeBase ):
    early_closure = False

    named_children = ( "source0", "sources", "body", "conditions", "targets" )

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


class CPythonStatementWith( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_WITH"

    named_children = ( "target", "expression", "frame" )

    def __init__( self, source, target, body, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "expression" : source,
                "target"     : target,
                "frame"      : body
            }
        )

    getWithBody = CPythonChildrenHaving.childGetter( "frame" )
    getTarget = CPythonChildrenHaving.childGetter( "target" )
    getExpression = CPythonChildrenHaving.childGetter( "expression" )


class CPythonStatementForLoop( CPythonChildrenHaving, CPythonNodeBase, MarkExceptionBreakContinueIndicator ):
    kind = "STATEMENT_FOR_LOOP"

    named_children = ( "iterated", "target", "body", "else" )

    def __init__( self, source, target, body, no_break, source_ref ):
        assert body.isStatementsSequenceLoopBody()

        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "iterated" : source,
                "target"   : target,
                "else"     : no_break,
                "body"     : body
            }
        )

        MarkExceptionBreakContinueIndicator.__init__( self )

    getIterated = CPythonChildrenHaving.childGetter( "iterated" )
    getLoopVariableAssignment = CPythonChildrenHaving.childGetter( "target" )
    getBody = CPythonChildrenHaving.childGetter( "body" )
    setBody = CPythonChildrenHaving.childSetter( "body" )
    getNoBreak = CPythonChildrenHaving.childGetter( "else" )
    setNoBreak = CPythonChildrenHaving.childSetter( "else" )


class CPythonStatementWhileLoop( CPythonChildrenHaving, CPythonNodeBase, MarkExceptionBreakContinueIndicator ):
    kind = "STATEMENT_WHILE_LOOP"

    named_children = ( "condition", "frame", "else" )

    def __init__( self, condition, body, no_enter, source_ref ):
        assert body.isStatementsSequenceLoopBody()

        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "condition" : condition,
                "else"      : no_enter,
                "frame"     : body
            }
        )

        MarkExceptionBreakContinueIndicator.__init__( self )

    getLoopBody = CPythonChildrenHaving.childGetter( "frame" )
    getCondition = CPythonChildrenHaving.childGetter( "condition" )
    getNoEnter = CPythonChildrenHaving.childGetter( "else" )
    setNoEnter = CPythonChildrenHaving.childSetter( "else" )


class CPythonExpressionAttributeLookup( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_ATTRIBUTE_LOOKUP"

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

    def getAttributeName( self ):
        return self.attribute_name

    def getDetails( self ):
        return { "attribute" : self.getAttributeName() }

    def getDetail( self ):
        return "attribute %s from %s" % ( self.getAttributeName(), self.getLookupSource() )

    getLookupSource = CPythonChildrenHaving.childGetter( "expression" )


class CPythonExpressionSubscriptLookup( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_SUBSCRIPT_LOOKUP"

    named_children = ( "expression", "subscript" )

    def __init__( self, expression, subscript, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "expression" : expression,
                "subscript"  : subscript
            }
        )

    getLookupSource = CPythonChildrenHaving.childGetter( "expression" )
    getSubscript = CPythonChildrenHaving.childGetter( "subscript" )


class CPythonExpressionSliceLookup( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_SLICE_LOOKUP"

    named_children = ( "expression", "lower", "upper" )

    def __init__( self, expression, lower, upper, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "expression" : expression,
                "upper"      : upper,
                "lower"      : lower
            }
        )

    getLookupSource = CPythonChildrenHaving.childGetter( "expression" )

    getLower = CPythonChildrenHaving.childGetter( "lower" )
    setLower = CPythonChildrenHaving.childSetter( "lower" )

    getUpper = CPythonChildrenHaving.childGetter( "upper" )
    setUpper = CPythonChildrenHaving.childSetter( "upper" )


class CPythonExpressionSliceObject( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_SLICE_OBJECT"

    named_children = ( "lower", "upper", "step" )

    def __init__( self, lower, upper, step, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "upper"      : upper,
                "lower"      : lower,
                "step"       : step
            }
        )

    getLower = CPythonChildrenHaving.childGetter( "lower" )
    getUpper = CPythonChildrenHaving.childGetter( "upper" )
    getStep  = CPythonChildrenHaving.childGetter( "step" )


class CPythonStatementDeclareGlobal( CPythonNodeBase ):
    kind = "STATEMENT_DECLARE_GLOBAL"

    def __init__( self, variable_names, source_ref ):
        self.variable_names = tuple( variable_names )

        CPythonNodeBase.__init__( self, source_ref = source_ref )

    def getVariableNames( self ):
        return self.variable_names


class CPythonExpressionConditional( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_CONDITIONAL"

    named_children = ( "condition", "expression_yes", "expression_no" )

    def __init__( self, condition, yes_expression, no_expression, source_ref ):

        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "condition"      : condition,
                "expression_yes" : yes_expression,
                "expression_no"  : no_expression
            }
        )

    def getBranches( self ):
        return ( self.getExpressionYes(), self.getExpressionNo() )

    getExpressionYes = CPythonChildrenHaving.childGetter( "expression_yes" )
    getExpressionNo = CPythonChildrenHaving.childGetter( "expression_no" )
    getCondition = CPythonChildrenHaving.childGetter( "condition" )


class CPythonExpressionBool2Base( CPythonChildrenHaving, CPythonNodeBase ):
    """ The "and/or" are short circuit and is therefore are not plain operations.

    """
    tags = ( "short_circuit", )

    named_children = ( "operands", )

    def __init__( self, operands, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        assert len( operands ) >= 2

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "operands" : tuple( operands )
            }
        )


    getOperands = CPythonChildrenHaving.childGetter( "operands" )

class CPythonExpressionBoolOR( CPythonExpressionBool2Base ):
    """ The "or" is short circuit and is therefore not a plain operation.

    """

    kind = "EXPRESSION_BOOL_OR"

    def getSimulator( self ):
        # Virtual method, pylint: disable=R0201
        # Virtual method, pylint: disable=R0201
        def simulateOR( *operands ):
            for operand in operands:
                if operand:
                    return operand
            else:
                return operands[-1]

        return simulateOR


class CPythonExpressionBoolAND( CPythonExpressionBool2Base ):
    """ The "and" is short circuit and is therefore not a plain operation.

    """

    kind = "EXPRESSION_BOOL_AND"

    def getSimulator( self ):
        # Virtual method, pylint: disable=R0201
        def simulateAND( *operands ):
            for operand in operands:
                if not operand:
                    return operand
            else:
                return operands[-1]

        return simulateAND

class CPythonStatementConditional( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_CONDITIONAL"

    named_children = ( "condition", "yes_branch", "no_branch" )

    def __init__( self, condition, yes_branch, no_branch, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "condition"  : condition,
                "yes_branch" : yes_branch,
                "no_branch"  : no_branch
            }
        )

    getCondition = CPythonChildrenHaving.childGetter( "condition" )
    getBranchYes = CPythonChildrenHaving.childGetter( "yes_branch" )
    setBranchYes = CPythonChildrenHaving.childSetter( "yes_branch" )
    getBranchNo = CPythonChildrenHaving.childGetter( "no_branch" )
    setBranchNo = CPythonChildrenHaving.childSetter( "no_branch" )

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

class CPythonStatementPass( CPythonNodeBase ):
    kind = "STATEMENT_PASS"

    def __init__( self, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

    def mayHaveSideEffects( self ):
        return False



class CPythonExpressionBuiltinGlobals( CPythonNodeBase ):
    kind = "EXPRESSION_BUILTIN_GLOBALS"

    def __init__( self, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

class CPythonExpressionBuiltinLocals( CPythonNodeBase ):
    kind = "EXPRESSION_BUILTIN_LOCALS"

    def __init__( self, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

class CPythonExpressionBuiltinDir( CPythonNodeBase ):
    kind = "EXPRESSION_BUILTIN_DIR"

    def __init__( self, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

class CPythonExpressionBuiltinVars( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_BUILTIN_VARS"

    named_children = ( "source", )

    def __init__( self, source, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "source"  : source,
            }
        )

    getSource = CPythonChildrenHaving.childGetter( "source" )


class CPythonExpressionBuiltinOpen( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_BUILTIN_OPEN"

    named_children = ( "filename", "mode", "buffering" )

    def __init__( self, filename, mode, buffering, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "filename"  : filename,
                "mode"      : mode,
                "buffering" : buffering
            }
        )

    getFilename = CPythonChildrenHaving.childGetter( "filename" )
    getMode = CPythonChildrenHaving.childGetter( "mode" )
    getBuffering = CPythonChildrenHaving.childGetter( "buffering" )


class CPythonExpressionBuiltinChr( CPythonExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_CHR"


class CPythonExpressionBuiltinOrd( CPythonExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_ORD"


class CPythonExpressionBuiltinOct( CPythonExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_OCT"


class CPythonExpressionBuiltinType1( CPythonExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_TYPE1"


class CPythonExpressionBuiltinLen( CPythonExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_LEN"


class CPythonExpressionBuiltinTuple( CPythonExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_TUPLE"


class CPythonExpressionBuiltinList( CPythonExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_LIST"


class CPythonExpressionBuiltinFloat( CPythonExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_FLOAT"


class CPythonExpressionBuiltinBool( CPythonExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_BOOL"


class CPythonExpressionBuiltinStr( CPythonExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_STR"


class CPythonExpressionBuiltinType3( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_BUILTIN_TYPE3"

    named_children = ( "type_name", "bases", "dict" )

    def __init__( self, type_name, bases, type_dict, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "type_name" : type_name,
                "bases"     : bases,
                "dict"      : type_dict
            }
        )

    getTypeName = CPythonChildrenHaving.childGetter( "type_name" )
    getBases = CPythonChildrenHaving.childGetter( "bases" )
    getDict = CPythonChildrenHaving.childGetter( "dict" )


class CPythonExpressionBuiltinInt( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_BUILTIN_INT"

    named_children = ( "value", "base" )

    def __init__( self, value, base, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "value" : value,
                "base"  : base
            }
        )

    getValue = CPythonChildrenHaving.childGetter( "value" )
    getBase = CPythonChildrenHaving.childGetter( "base" )


class CPythonExpressionBuiltinLong( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_BUILTIN_LONG"

    named_children = ( "value", "base" )

    def __init__( self, value, base, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "value" : value,
                "base"  : base
            }
        )

    getValue = CPythonChildrenHaving.childGetter( "value" )
    getBase = CPythonChildrenHaving.childGetter( "base" )


class CPythonExpressionBuiltinUnicode( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_BUILTIN_UNICODE"

    named_children = ( "value", "encoding", "errors" )

    def __init__( self, value, encoding, errors, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "value"    : value,
                "encoding" : encoding,
                "errors"   : errors
            }
        )

    getValue = CPythonChildrenHaving.childGetter( "value" )
