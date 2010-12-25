#
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
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

"""

from __future__ import print_function
from __past__ import long, unicode

import Variables

from odict import OrderedDict

NoneType = type(None)

class CPythonNode:
    def __init__( self, kind, source_ref ):
        assert source_ref is not None
        assert source_ref.line is not None

        self.parent = None

        self.kind = kind
        self.source_ref = source_ref

    def __repr__( self ):
        detail = self.getDetail()

        if detail == "":
            return "<Node %s>" % self.getDescription()
        else:
            return "<Node %s %s>" % ( self.getDescription(), detail )

    def getDescription( self ):
        """ Description of the node, intented for use in __repr__ and graphical display."""
        return "%s at %s" % ( self.kind, self.source_ref )

    def getDetail( self ):
        """ Description of the node, intented for use in __repr__ and graphical display."""
        return ""

    def getParent( self ):
        """ Parent of the node. Every node except for modules have to have a parent."""

        if self.parent is None and not self.isModule():
            assert False, ( self,  self.source_ref )

        return self.parent

    def getParentFunction( self ):
        """ Return the parent that is a function."""

        parent = self.getParent()

        while parent is not None and not parent.isFunctionReference():
            parent = parent.getParent()

        return parent

    def getParentModule( self ):
        parent = self

        while not parent.isModule() or hasattr( parent, "original_provider" ):
            if hasattr( parent, "provider" ):
                parent = parent.provider
            elif hasattr( parent, "original_provider" ):
                parent = parent.original_provider
            else:
                parent = parent.getParent()

        assert parent.__class__ == CPythonModule, parent.__class__

        return parent

    def isParentVariableProvider( self ):
        return self.isModule() or self.isFunctionReference() or self.isClassReference() or self.isExpressionGenerator() or self.isExpressionLambda()

    def getParentVariableProvider( self ):
        previous = self
        parent = self.getParent()

        while not parent.isParentVariableProvider():
            previous = parent
            parent = parent.getParent()

        # Default values of functions and decorators of functions/classes are evaluated
        # in the function creator context.
        if parent.isFunctionReference():
            if previous in parent.getParameters().getDefaultExpressions():
                return parent.getParentVariableProvider()
            elif previous in parent.getDecorators():
                return parent.getParentVariableProvider()
            else:
                return parent
        elif parent.isExpressionLambda():
            if previous in parent.getParameters().getDefaultExpressions():
                return parent.getParentVariableProvider()
            else:
                return parent
        elif parent.isClassReference():
            if previous in parent.getDecorators() or previous in parent.getBaseClasses():
                return parent.getParentVariableProvider()
            else:
                return parent
        elif parent.isExpressionGenerator():
            if previous == parent.getIterateds()[0]:
                return parent.getParentVariableProvider()
            else:
                return parent
        else:
            return parent

    def getSourceReference( self ):
        return self.source_ref

    def dump( self, level = 0 ):
        print( "    " * level, self )

        print( "    " * level, "*" * 10 )

        for visitable in self.getVisitableNodes():
            visitable.dump( level + 1 )

        print( "    " * level, "*" * 10 )

    def isModule( self ):
        return self.kind == "MODULE"

    def isExpression( self ):
        return self.kind.startswith( "EXPRESSION_" )

    def isStatement( self ):
        return self.kind.startswith( "STATEMENT_" )

    def isFunctionReference( self ):
        return self.kind == "STATEMENT_FUNCTION_DEF"

    def isExpressionLambda( self ):
        return self.kind == "EXPRESSION_LAMBDA_DEF"

    def isExpressionGenerator( self ):
        return self.kind == "EXPRESSION_GENERATOR_DEF"

    def isListContraction( self ):
        return self.kind == "EXPRESSION_LIST_CONTRACTION"

    def isSetContraction( self ):
        return self.kind == "EXPRESSION_SET_CONTRACTION"

    def isDictContraction( self ):
        return self.kind == "EXPRESSION_DICT_CONTRACTION"

    def isClassReference( self ):
        return self.kind == "STATEMENT_CLASS_DEF"

    def isConditionOR( self ):
        return self.kind == "EXPRESSION_CONDITION_OR"

    def isConditionAND( self ):
        return self.kind == "EXPRESSION_CONDITION_AND"

    def isConditionNOT( self ):
        return self.kind == "EXPRESSION_CONDITION_NOT"

    def isVariableReference( self ):
        return self.kind == "EXPRESSION_VARIABLE_REF"

    def isConstantReference( self ):
        return self.kind == "EXPRESSION_CONSTANT_REF"

    def isBuiltinImport( self ):
        return self.kind == "EXPRESSION_BUILTIN_IMPORT"

    def isBuiltinGlobals( self ):
        return self.kind == "EXPRESSION_BUILTIN_GLOBALS"

    def isBuiltinLocals( self ):
        return self.kind == "EXPRESSION_BUILTIN_LOCALS"

    def isBuiltinDir( self ):
        return self.kind == "EXPRESSION_BUILTIN_DIR"

    def isBuiltinVars( self ):
        return self.kind == "EXPRESSION_BUILTIN_VARS"

    def isBuiltinEval( self ):
        return self.kind == "EXPRESSION_BUILTIN_EVAL"

    def isBuiltinOpen( self ):
        return self.kind == "EXPRESSION_BUILTIN_OPEN"

    def isBuiltinChr( self ):
        return self.kind == "EXPRESSION_BUILTIN_CHR"

    def isBuiltinOrd( self ):
        return self.kind == "EXPRESSION_BUILTIN_ORD"

    def isBuiltinType1( self ):
        return self.kind == "EXPRESSION_BUILTIN_TYPE1"

    def isBuiltinType3( self ):
        return self.kind == "EXPRESSION_BUILTIN_TYPE3"

    def isOperation( self ):
        return self.kind in ( "EXPRESSION_BINARY_OPERATION", "EXPRESSION_UNARY_OPERATION", "EXPRESSION_MULTIARG_OPERATION" )

    def isSequenceCreation( self ):
        return self.kind == "EXPRESSION_MAKE_SEQUENCE"

    def isDictionaryCreation( self ):
        return self.kind == "EXPRESSION_MAKE_DICTIONARY"

    def isSetCreation( self ):
        return self.kind == "EXPRESSION_MAKE_SET"

    def isFunctionCall( self ):
        return self.kind == "EXPRESSION_FUNCTION_CALL"

    def isAttributeLookup( self ):
        return self.kind == "EXPRESSION_ATTRIBUTE_REF"

    def isSubscriptLookup( self ):
        return self.kind == "EXPRESSION_SUBSCRIPTION_REF"

    def isSliceLookup( self ):
        return self.kind == "EXPRESSION_SLICE_REF"

    def isSliceObjectExpression( self ):
        return self.kind == "EXPRESSION_SLICEOBJ_REF"

    def isExpressionComparison( self ):
        return self.kind == "EXPRESSION_COMPARISON"

    def isConditionalExpression( self ):
        return self.kind == "EXPRESSION_CONDITIONAL"

    def isExpressionYield( self ):
        return self.kind == "EXPRESSION_YIELD"

    def isStatementAssignment( self ):
        return self.kind == "STATEMENT_ASSIGNMENT"

    def isStatementInplaceAssignment( self ):
        return self.kind == "STATEMENT_ASSIGNMENT_INPLACE"

    def isStatementExpression( self ):
        return self.kind == "STATEMENT_EXPRESSION"

    def isStatementPrint( self ):
        return self.kind == "STATEMENT_PRINT"

    def isStatementReturn( self ):
        return self.kind == "STATEMENT_RETURN"

    def isStatementImportModule( self ):
        return self.kind == "STATEMENT_IMPORT_MODULE"

    def isStatementImportFrom( self ):
        return self.kind == "STATEMENT_IMPORT_FROM"

    def isStatementImport( self ):
        return self.isStatementImportFrom() or self.isStatementImportModule()

    def isStatementsSequence( self ):
        return self.kind == "STATEMENTS_SEQUENCE"

    def isStatementRaiseException( self ):
        return self.kind == "STATEMENT_RAISE_EXCEPTION"

    def isStatementAssert( self ):
        return self.kind == "STATEMENT_ASSERT"

    def isStatementWith( self ):
        return self.kind == "STATEMENT_WITH"

    def isStatementForLoop( self ):
        return self.kind == "STATEMENT_FOR_LOOP"

    def isStatementWhileLoop( self ):
        return self.kind == "STATEMENT_WHILE_LOOP"

    def isStatementConditional( self ):
        return self.kind == "STATEMENT_CONDITIONAL"

    def isStatementContinue( self ):
        return self.kind == "STATEMENT_CONTINUE_LOOP"

    def isStatementBreak( self ):
        return self.kind == "STATEMENT_BREAK_LOOP"

    def isStatementPass( self ):
        return self.kind == "STATEMENT_PASS"

    def isStatementTryFinally( self ):
        return self.kind == "STATEMENT_TRY_FINALLY"

    def isStatementTryExcept( self ):
        return self.kind == "STATEMENT_TRY_EXCEPT"

    def isStatementDeclareGlobal( self ):
        return self.kind == "STATEMENT_DECLARE_GLOBAL"

    def isAssignToVariable( self ):
        return self.kind == "ASSIGN_TO_VARIABLE"

    def isAssignToTuple( self ):
        return self.kind == "ASSIGN_TO_TUPLE"

    def isAssignToSubscript( self ):
        return self.kind == "ASSIGN_TO_SUBSCRIPT"

    def isAssignToAttribute( self ):
        return self.kind == "ASSIGN_TO_ATTRIBUTE"

    def isAssignToSlice( self ):
        return self.kind == "ASSIGN_TO_SLICE"

    def isStatementExec( self ):
        return self.kind == "STATEMENT_EXEC"

    def visit( self, context, visitor ):
        visitor( self )

        for visitable in self.getVisitableNodes():
            visitable.visit( context, visitor )

    def getVisitableNodes( self ):
        return ()

    getSameScopeNodes = getVisitableNodes

    def _getNiceName( self ):
        if self.isExpressionLambda():
            result = "lambda"
        elif self.isExpressionGenerator():
            result = "genexpr"
        elif self.isSetContraction():
            result = "setcontr"
        elif self.isDictContraction():
            result = "dictcontr"
        else:
            result = self.getName()

        return result

    def getFullName( self ):
        result = self._getNiceName()

        assert "<" not in result, result

        current = self

        while current:
            current = current.getParent()

            if current and hasattr( current, "getName" ):
                result = current._getNiceName() + "__" + result

        return result

    def getLevel( self ):
        if self.parent is None:
            return 1
        else:
            return self.parent.getLevel() + 1

    def replaceWith( self, new_node ):
        self.parent.replaceChild( old_node = self, new_node = new_node )

class CPythonNamedCode:
    def __init__( self, code_prefix ):
        self.code_prefix = code_prefix
        self.uids = {}

        self.code_name = None

    def getCodeName( self ):
        if self.code_name is None:

            search = self.parent

            while search is not None:
                if isinstance( search, CPythonNamedCode ):
                    break

                search = search.parent

            if search is None:
                assert self.isModule()

                return "module_" + self.name

            parent_name = search.getCodeName()

            uid = "_%d" % search.getChildUID( self )

            if isinstance( self, CPythonNamedNode ):
                name = uid + "_" + self.name
            else:
                name = uid

            self.code_name = "%s%s_of_%s" % ( self.code_prefix, name, parent_name )

        return self.code_name

    def getChildUID( self, node ):
        if node.kind not in self.uids:
            self.uids[ node.kind ] = 0

        self.uids[ node.kind ] += 1

        return self.uids[ node.kind ]

class CPythonNamedNode( CPythonNode ):
    def __init__( self, name, kind, source_ref ):
        assert name is not None
        assert name.find( " " ) == -1

        CPythonNode.__init__( self, kind = kind, source_ref = source_ref )

        self.name = name

    def getDescription( self ):
        return "%s %s" % ( self.kind, self.name )

    def getName( self ):
        return self.name

    def getDetail( self ):
        return self.getFullName()

class CPythonChildrenHaving:
    def __init__( self, names ):
        self.named_children = dict( names )

        for value in names.values():
            assert type( value ) != list

    def setChild( self, name, value ):
        assert name in self.named_children

        if type( value ) == list:
            value = tuple( value )

        self.named_children[ name ] = value

    def getChild( self, name ):
        assert name in self.named_children

        return self.named_children[ name ]

    @staticmethod
    def childGetter( name ):
        def getter( self ):
            return self.getChild( name )

        return getter

    @staticmethod
    def childSetter( name ):
        def setter( self, value ):
            self.setChild( name, value )

        return setter

    def getVisitableNodes( self ):
        result = []

        for key, value in self.named_children.items():
            if value is None:
                pass
            elif type( value ) == tuple:
                result += list( value )
            elif isinstance( value, CPythonNode ):
                result.append( value )
            else:
                assert False, ( key, value, value.__class__ )

        return tuple( result )

    def getSameScopeNodes( self ):
        result = []

        for key, value in self.named_children.items():
            if value is None or key == "body":
                pass
            elif type( value ) == tuple:
                result += list( value )
            elif isinstance( value, CPythonNode ):
                result.append( value )
            else:
                assert False, ( key, value, value.__class__ )

        return tuple( result )

    def replaceChild( self, old_node, new_node ):
        for key, value in self.named_children.items():
            if value is None:
                pass
            elif type( value ) == tuple:
                if old_node in value:
                    new_value = []

                    for val in value:
                        if val != old_node:
                            new_value.append( val )
                        else:
                            new_value.append( new_node )

                    self.setChild( key, tuple( new_value ) )

                    break
            elif isinstance( value, CPythonNode ):
                if old_node == value:
                    self.setChild( key, new_node )

                    break
            else:
                assert False, ( key, value, value.__class__ )
        else:
            assert False

        new_node.parent = old_node.parent

class CPythonClosureGiver( CPythonNamedCode ):
    """ Mixin for nodes that provide variables for closure takers. """
    def __init__( self, code_prefix ):
        CPythonNamedCode.__init__( self, code_prefix )
        self.providing = OrderedDict()

    def hasProvidedVariable( self, variable_name ):
        return variable_name in self.providing

    def getProvidedVariable( self, variable_name ):
        if variable_name not in self.providing:
            self.providing[ variable_name ] = self.createProvidedVariable( variable_name )

        return self.providing[ variable_name ]

    def createProvidedVariable( self, variable_name ):
        return None

    def registerProvidedVariables( self, variables ):
        for variable in variables:
            self.registerProvidedVariable( variable )

    def registerProvidedVariable( self, variable ):
        assert variable is not None

        self.providing[ variable.getName() ] = variable

    def getProvidedVariables( self ):
        return self.providing.values()

    def hasLocalsDict( self ):
        return False

class CPythonClosureTaker:
    """ Mixin for nodes that accept variables from closure givers. """

    def __init__( self, provider ):
        self.provider = provider

        self.taken = set()
        self.closure = set()

    def getClosureVariable( self, variable_name ):
        result = self.provider.getVariableForReference( variable_name )
        assert result is not None, ( "Fail to closure", self, self.provider, variable_name )

        return self._addClosureVariable( result )

    def getModuleClosureVariable( self, variable_name ):
        result = self.provider.getParentModule().getProvidedVariable( variable_name = variable_name )

        return self._addClosureVariable( result )


    def _addClosureVariable( self, variable ):
        if variable.isModuleVariable():
            pass
        else:
            variable = Variables.ClosureVariableReference( self, variable )
            self.closure.add( variable )

        self.taken.add( variable )

        return variable

    def getClosureVariables( self ):
        return tuple( sorted( self.closure, key = lambda x : x.getName() ))

    def hasTakenVariable( self, variable_name ):
        for variable in self.taken:
            if variable.getName() == variable_name:
                return True
        else:
            return False

    # Normally it's good to lookup name references immediately, but in case of a function body it
    # is not allowed to do that, because a later assignment needs to be queried first.
    def isEarlyClosure( self ):
        return True

class MarkExceptionBreakContinueIndicator:
    """ Can have an indication of a break and continue as a real exception is needed. """

    def __init__( self ):
        self.break_continue_exception = False

    def markAsExceptionBreakContinue( self ):
        self.break_continue_exception = True

    def needsExceptionBreakContinue( self ):
        return self.break_continue_exception

class CPythonModule( CPythonChildrenHaving, CPythonNamedNode, CPythonClosureGiver ):
    """ Module

        The module is a possible root of a tree.
    """
    def __init__( self, name, package, filename, source_ref ):
        assert package is None or isinstance( package, CPythonPackage )

        CPythonNamedNode.__init__( self, name = name, kind = "MODULE", source_ref = source_ref )
        CPythonClosureGiver.__init__( self, "module" )
        CPythonChildrenHaving.__init__(
            self,
            names = {
                "frame" : None
            }
        )

        self.filename = filename
        self.package = package
        self.doc = None

    setBody = CPythonChildrenHaving.childSetter( "frame" )
    getStatementSequence = CPythonChildrenHaving.childGetter( "frame" )

    def getDoc( self ):
        return self.doc

    def setDoc( self, doc ):
        self.doc = doc

    def getFilename( self ):
        return self.filename

    def getPackage( self ):
        return self.package

    def getFullName( self ):
        if self.package:
            return self.package.getName() + "." + self.getName()
        else:
            return self.getName()

    def getVariableForAssignment( self, variable_name ):
        return self.getProvidedVariable( variable_name )

    def getVariableForReference( self, variable_name ):
        return self.getProvidedVariable( variable_name )

    def createProvidedVariable( self, variable_name ):
        return Variables.ModuleVariable( self, variable_name )

    def isEarlyClosure( self ):
        return True

class CPythonPackage( CPythonNamedNode ):
    def __init__( self, name, parent_package, source_ref ):
        assert type(name) is str, type(name)
        assert type(parent_package) in (type(None), CPythonPackage )

        CPythonNamedNode.__init__( self, name = name, kind = "PACKAGE", source_ref = source_ref )

    def getFilename( self ):
        return self.source_ref.getFilename()

    def getDoc( self ):
        # TODO: Check if they can have it.
        return None


class CPythonClass( CPythonChildrenHaving, CPythonNamedNode, CPythonClosureTaker, CPythonNamedCode ):
    def __init__( self, provider, variable, name, doc, bases, decorators, source_ref ):
        CPythonNamedNode.__init__( self, name = name, kind = "STATEMENT_CLASS_DEF", source_ref = source_ref )
        CPythonClosureTaker.__init__( self, provider )
        CPythonNamedCode.__init__( self, "class" )

        self.target_variable = variable

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "decorators" : tuple( decorators ),
                "bases"      : tuple( bases ),
                "body"       : None
            }
        )

        self.doc = doc

        self.variables = {}
        self.locals_dict = False

    def getTargetVariable( self ):
        return self.target_variable

    def getSameScopeNodes( self ):
        return self.getBaseClasses() + self.getDecorators()

    getBaseClasses = CPythonChildrenHaving.childGetter( "bases" )
    getDecorators = CPythonChildrenHaving.childGetter( "decorators" )

    getBody = CPythonChildrenHaving.childGetter( "body" )
    setBody = CPythonChildrenHaving.childSetter( "body" )

    def getVariableForAssignment( self, variable_name ):
        result = Variables.ClassVariable( owner = self, variable_name = variable_name )

        self.variables[ variable_name ] = result

        return result

    def getVariableForReference( self, variable_name ):
        if variable_name in self.variables:
            return self.variables[ variable_name ]
        else:
            return self.getClosureVariable( variable_name )

    def getClassVariables( self ):
        return self.variables.values()

    getVariables = getClassVariables

    def hasLocalsDict( self ):
        return self.locals_dict

    def markAsLocalsDict( self ):
        self.locals_dict = True


class CPythonStatementSequence( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, statements, replacement, source_ref ):
        for statement in statements:
            assert statement.isStatement(), statement

        CPythonNode.__init__( self, kind = "STATEMENTS_SEQUENCE", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "statements" : tuple( statements )
            }
        )

        self.replacement = replacement

    getStatements = CPythonChildrenHaving.childGetter( "statements" )

    def isReplacedStatement( self ):
        return self.replacement

class CPythonAssignTargetVariable( CPythonNode ):
    def __init__( self, variable, source_ref ):
        self.variable = variable

        CPythonNode.__init__( self, kind = "ASSIGN_TO_VARIABLE", source_ref = source_ref )

    def getDetail( self ):
        return "to variable %s" % self.variable

    def getTargetVariableName( self ):
        return self.getTargetVariable().getName()

    def getTargetVariableNames( self ):
        return [ self.getTargetVariableName() ]

    def getTargetVariable( self ):
        return self.variable

    def getTargetVariables( self ):
        return ( self.variable, )


class CPythonAssignAttribute( CPythonNode ):
    def __init__( self, expression, attribute, source_ref ):
        self.expression = expression
        self.attribute = attribute

        CPythonNode.__init__( self, kind = "ASSIGN_TO_ATTRIBUTE", source_ref = source_ref )

    def getDetail( self ):
        return "to attribute %s" % self.attribute

    def getVisitableNodes( self ):
        return ( self.expression, )

    def getAttributeName( self ):
        return self.attribute

    def getLookupSource( self ):
        return self.expression


class CPythonAssignSubscript( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, expression, subscript, source_ref ):
        CPythonNode.__init__( self, kind = "ASSIGN_TO_SUBSCRIPT", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "expression" : expression,
                "subscript" : subscript
            }
        )

    getSubscribed = CPythonChildrenHaving.childGetter( "expression" )
    getSubscript = CPythonChildrenHaving.childGetter( "subscript" )


class CPythonAssignSlice( CPythonNode ):
    # TODO: This class could shared with the expression, maybe all assigments could more or less share
    # code with the expression counterparts.

    def __init__( self, expression, lower, upper, source_ref ):
        CPythonNode.__init__( self, kind = "ASSIGN_TO_SLICE", source_ref = source_ref )

        self.expression = expression
        self.lower = lower
        self.upper = upper

    def getLower( self ):
        return self.lower

    def getUpper( self ):
        return self.upper

    def getLookupSource( self ):
        return self.expression

    def getVisitableNodes( self ):
        result = [ self.expression ]

        if self.lower is not None:
            result.append( self.lower )

        if self.upper is not None:
            result.append( self.upper )

        return result


class CPythonAssignTuple( CPythonNode ):
    def __init__( self, elements, source_ref ):
        self.elements = elements[:]

        CPythonNode.__init__( self, kind = "ASSIGN_TO_TUPLE", source_ref = source_ref )

    def getTargetVariables( self ):
        return [ element.getTargetVariable() for element in self.elements ]

    def getTargetVariableNames( self ):
        return [ element.getTargetVariableName() for element in self.elements ]

    def getVisitableNodes( self ):
        return self.elements

    def getElements( self ):
        return self.elements

class CPythonStatementAssignment( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, targets, expression, source_ref ):
        CPythonNode.__init__( self, kind = "STATEMENT_ASSIGNMENT", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "source"  : expression,
                "targets" : tuple( targets )
            }
        )

    def getDetail( self ):
        return "to %s" % ( self.getTargets(), )

    getTargets = CPythonChildrenHaving.childGetter( "targets" )
    getSource = CPythonChildrenHaving.childGetter( "source" )

class CPythonStatementAssignmentInplace( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, target, operator, expression, source_ref ):
        CPythonNode.__init__( self, kind = "STATEMENT_ASSIGNMENT_INPLACE", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
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

class CPythonExpressionConstant( CPythonNode ):
    def __init__( self, constant, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_CONSTANT_REF", source_ref = source_ref )

        self.constant = constant

    def getDetail( self ):
        return repr( self.constant )

    def getConstant( self ):
        return self.constant

    def _isMutable( self, constant ):
        constant_type = type( constant )

        if constant_type in ( str, unicode, complex, int, long, bool, float, NoneType ):
            return False
        elif constant_type in ( dict, list ):
            return True
        elif constant_type is tuple:
            for value in constant:
                if self._isMutable( value ):
                    return False
            else:
                return True
        elif constant is Ellipsis:
            # Note: Workaround for Ellipsis not being handled by the pickle module,
            # pretend it would be mutable, then it doesn't get pickled as part of lists or
            # tuples. This is a loss of efficiency, but usage of Ellipsis will be very
            # limited normally anyway.
            return True

            return False
        else:
            assert False, constant_type

    def isMutable( self ):
        return self._isMutable( self.constant )

class CPythonParameterHaving:
    def __init__( self, parameters ):
        self.parameters = parameters
        self.parameters.setOwner( self )

        self.registerProvidedVariables( self.parameters.getVariables() )

    def getParameters( self ):
        return self.parameters

class CPythonExpressionLambda( CPythonChildrenHaving, CPythonNode, CPythonParameterHaving, CPythonClosureTaker, CPythonClosureGiver ):
    def __init__( self, provider, parameters, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_LAMBDA_DEF", source_ref = source_ref )
        CPythonClosureTaker.__init__( self, provider )
        CPythonClosureGiver.__init__( self, code_prefix = "lamda" )
        CPythonParameterHaving.__init__( self, parameters )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "body" : None
            }
        )

        self.is_generator = False

    getLambdaExpression = CPythonChildrenHaving.childGetter( "body" )
    setBody = CPythonChildrenHaving.childSetter( "body" )

    def isGenerator( self ):
        return self.is_generator

    def markAsGenerator( self ):
        self.is_generator = True

    def getVisitableNodes( self ):
        return self.parameters.getDefaultExpressions() + ( self.getLambdaExpression(), )

    def getVariables( self ):
        return self.providing.values()

    def getUserLocalVariables( self ):
        return [ variable for variable in self.providing.values() if variable.isLocalVariable() and not variable.isParameterVariable() ]

    def getVariableForReference( self, variable_name ):
        if self.hasProvidedVariable( variable_name ):
            return self.getProvidedVariable( variable_name )
        else:
            result = self.getClosureVariable( variable_name )

            # Remember that we need that closure for something.
            self.registerProvidedVariable( result )

            return result

    def getVariableForAssignment( self, variable_name ):
        return self.getProvidedVariable( variable_name )

    def createProvidedVariable( self, variable_name ):
        return Variables.LocalVariable( owner = self, variable_name = variable_name )


class CPythonFunction( CPythonNamedNode, CPythonParameterHaving, CPythonClosureTaker, CPythonClosureGiver ):
    def __init__( self, provider, variable, name, doc, decorators, parameters, source_ref ):
        CPythonNamedNode.__init__( self, name = name, kind = "STATEMENT_FUNCTION_DEF", source_ref = source_ref )

        CPythonClosureTaker.__init__( self, provider )
        CPythonClosureGiver.__init__( self, code_prefix = "function" )

        CPythonParameterHaving.__init__( self, parameters )

        self.target_variable = variable

        self.body = None

        self.decorators = tuple( decorators )

        self.is_generator = False
        self.locals_dict = False

        self.doc = doc

    def getVisitableNodes( self ):
        return self.parameters.getDefaultExpressions() + ( self.body, ) + self.decorators

    def getSameScopeNodes( self ):
        return self.parameters.getDefaultExpressions() + self.decorators

    def getDescription( self ):
        return "Function '%s' with %s" % ( self.name, self.parameters )

    def getDetail( self ):
        return self.name

    def getTargetVariable( self ):
        return self.target_variable

    def getFunctionName( self ):
        return self.name

    def getDoc( self ):
        return self.doc

    def getDecorators( self ):
        return self.decorators

    def getLocalVariableNames( self ):
        return Variables.getNames( self.getLocalVariables() )

    def getLocalVariables( self ):
        return [ variable for variable in self.providing.values() if variable.isLocalVariable() ]

    def getUserLocalVariables( self ):
        return [ variable for variable in self.providing.values() if variable.isLocalVariable() and not variable.isParameterVariable() ]

    def getVariables( self ):
        return self.providing.values()

    def setBody( self, body ):
        self.body = body

    def getBody( self ):
        return self.body

    def markAsGenerator( self ):
        self.is_generator = True

    def markAsLocalsDict( self ):
        self.locals_dict = True

    def hasLocalsDict( self ):
        return self.locals_dict

    def isGenerator( self ):
        return self.is_generator

    def getVariableForAssignment( self, variable_name ):
        if self.hasTakenVariable( variable_name ):
            result = self.getClosureVariable( variable_name )

            if not result.isModuleVariable():
                raise SyntaxError

            assert result.isModuleVariable()

            return result
        else:
            return self.getProvidedVariable( variable_name )

    def getVariableForReference( self, variable_name ):
        # print "ref", self, variable_name

        if self.hasProvidedVariable( variable_name ):
            return self.getProvidedVariable( variable_name )
        else:
            result = self.getClosureVariable( variable_name )

            # Remember that we need that closure for something.
            self.registerProvidedVariable( result )

            return result

    def createProvidedVariable( self, variable_name ):
        return Variables.LocalVariable( owner = self, variable_name = variable_name )

    def isEarlyClosure( self ):
        return False


class CPythonExpressionVariable( CPythonNode ):
    def __init__( self, variable_name, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_VARIABLE_REF", source_ref = source_ref )

        self.variable_name = variable_name
        self.variable = None

    def getVariableName( self ):
        return self.variable_name

    def setVariable( self, variable ):
        assert isinstance( variable, Variables.Variable )

        self.variable = variable

    def getVariable( self ):
        return self.variable

    def getDetail( self ):
        return self.variable_name


class CPythonExpressionYield( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, expression, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_YIELD", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "expression" : expression
            }
        )

    getExpression = CPythonChildrenHaving.childGetter( "expression" )


class CPythonStatementReturn( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, expression, source_ref ):
        CPythonNode.__init__( self, kind = "STATEMENT_RETURN", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "expression" : expression
            }
        )

    getExpression = CPythonChildrenHaving.childGetter( "expression" )


class CPythonStatementPrint( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, dest, values, newline, source_ref ):
        CPythonNode.__init__( self, kind = "STATEMENT_PRINT", source_ref = source_ref )

        self.newline = newline

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "values" : tuple( values ),
                "dest"   : dest
            }
        )

    def isNewlinePrint( self ):
        return self.newline

    getDestination = CPythonChildrenHaving.childGetter( "dest" )
    getValues = CPythonChildrenHaving.childGetter( "values" )

class CPythonStatementAssert( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, expression, failure, source_ref ):
        CPythonNode.__init__( self, kind = "STATEMENT_ASSERT", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "expression" : expression,
                "failure"    : failure
            }
        )

    getExpression = CPythonChildrenHaving.childGetter( "expression" )
    getArgument   = CPythonChildrenHaving.childGetter( "failure" )

class CPythonExpressionFunctionCall( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, called_expression, positional_args, list_star_arg, dict_star_arg, named_args, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_FUNCTION_CALL", source_ref = source_ref )

        assert called_expression.isExpression()

        for positional_arg in positional_args:
            assert positional_arg.isExpression()

        self.named_argument_names = []
        named_argument_values = []

        for named_arg_desc in named_args:
            named_arg_name, named_arg_value = named_arg_desc

            assert type( named_arg_name ) == str
            assert named_arg_value.isExpression()

            self.named_argument_names.append( named_arg_name )
            named_argument_values.append( named_arg_value )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "called"          : called_expression,
                "positional_args" : tuple( positional_args ),
                "named_args"      : tuple( named_argument_values ),
                "list_star_arg"   : list_star_arg,
                "dict_star_arg"   : dict_star_arg
           }
        )

        assert self.getChild( "called" ) == called_expression

    getCalledExpression = CPythonChildrenHaving.childGetter( "called" )
    getPositionalArguments = CPythonChildrenHaving.childGetter( "positional_args" )
    getStarListArg = CPythonChildrenHaving.childGetter( "list_star_arg" )
    getStarDictArg = CPythonChildrenHaving.childGetter( "dict_star_arg" )

    def getNamedArguments( self ):
        return zip( self.named_argument_names, self.getChild( "named_args" ) )

    def isEmptyCall( self ):
        return not self.getPositionalArguments() and not self.getChild( "named_args" ) and not self.getStarListArg() and not self.getStarDictArg()

    def hasOnlyPositionalArguments( self ):
        return not self.getNamedArguments() and not self.getStarListArg() and not self.getStarDictArg()

class CPythonExpressionBinaryOperation( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, operator, left, right, source_ref ):
        assert left.isExpression() and right.isExpression, ( left, right )

        CPythonNode.__init__( self, kind = "EXPRESSION_BINARY_OPERATION", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "operands" : ( left, right )
            }
        )

        self.operator = operator

    def getOperation( self ):
        return self.operator

    def getDetail( self ):
        return self.operator

    getOperands = CPythonChildrenHaving.childGetter( "operands" )

class CPythonExpressionUnaryOperation( CPythonNode ):
    def __init__( self, operator, operand, source_ref ):
        assert operand.isExpression(), operand

        CPythonNode.__init__( self, kind = "EXPRESSION_UNARY_OPERATION", source_ref = source_ref )

        self.operand = operand
        self.operator = operator

    def isOperation( self ):
        return True

    def getOperation( self ):
        return self.operator

    def getOperands( self ):
        return ( self.operand, )

    def getVisitableNodes( self ):
        return ( self.operand, )


class CPythonExpressionContractionBase( CPythonChildrenHaving, CPythonNode, CPythonClosureTaker, CPythonClosureGiver ):
    def __init__( self, kind, code_prefix, provider, source_ref ):
        CPythonNode.__init__( self, kind = kind, source_ref = source_ref )
        CPythonClosureTaker.__init__( self, provider )
        CPythonClosureGiver.__init__( self, code_prefix = code_prefix )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "body"       : None,
                "conditions" : None,
                "sources"    : None,
                "targets"    : None
            }
        )

    def getName( self ):
        return "<%s> at %s" % ( self.code_prefix, self.source_ref.getAsString() )

    setSources = CPythonChildrenHaving.childSetter( "sources" )
    getIterateds = CPythonChildrenHaving.childGetter( "sources" )

    def getIteratedsCount( self ):
        return len( self.getIterateds() )

    setConditions = CPythonChildrenHaving.childSetter( "conditions" )
    getConditions = CPythonChildrenHaving.childGetter( "conditions" )

    getLoopVariableAssignments = CPythonChildrenHaving.childGetter( "targets" )
    getTargets = getLoopVariableAssignments

    setBody = CPythonChildrenHaving.childSetter( "body" )
    getBody = CPythonChildrenHaving.childGetter( "body" )

    def setTargets( self, targets ):
        assert self.getLoopVariableAssignments() is None

        self._setTargets( targets )

        for target in targets:
            self.registerProvidedVariables( target.getTargetVariables() )

    _setTargets = CPythonChildrenHaving.childSetter( "targets" )

    def getTargetVariables( self ):
        result = []

        for target in self.getLoopVariableAssignments():
            result += list( target.getTargetVariables() )

        return result

    def getVariableForReference( self, variable_name ):
        if self.hasProvidedVariable( variable_name ):
            return self.getProvidedVariable( variable_name )
        else:
            result = self.getClosureVariable( variable_name )

            # Remember that we need that closure for something.
            self.registerProvidedVariable( result )

            return result

    def getVariableForAssignment( self, variable_name ):
        return self.getProvidedVariable( variable_name )


class CPythonExpressionListContraction( CPythonExpressionContractionBase ):
    def __init__( self, provider, source_ref ):
        CPythonExpressionContractionBase.__init__(
            self,
            kind        = "EXPRESSION_LIST_CONTRACTION",
            code_prefix = "listcontr",
            provider    = provider,
            source_ref  = source_ref
        )

    def createProvidedVariable( self, variable_name ):
        # Make sure the provider knows it has to have a variable of this
        # name for assigment.
        self.provider.getVariableForAssignment( variable_name )

        return self.getClosureVariable( variable_name )

class CPythonGeneratorExpression( CPythonExpressionContractionBase ):
    def __init__( self, provider, source_ref ):
        CPythonExpressionContractionBase.__init__(
            self,
            kind        = "EXPRESSION_GENERATOR_DEF",
            code_prefix = "genexpr",
            provider    = provider,
            source_ref  = source_ref
        )

    def createProvidedVariable( self, variable_name ):
        return Variables.LocalLoopVariable( owner = self, variable_name = variable_name )

class CPythonExpressionSetContraction( CPythonExpressionContractionBase ):
    def __init__( self, provider, source_ref ):
        CPythonExpressionContractionBase.__init__(
            self,
            kind        = "EXPRESSION_SET_CONTRACTION",
            code_prefix = "setcontr",
            provider    = provider,
            source_ref  = source_ref
        )

    def createProvidedVariable( self, variable_name ):
        return Variables.LocalLoopVariable( owner = self, variable_name = variable_name )


class CPythonExpressionDictContraction( CPythonExpressionContractionBase ):
    def __init__( self, provider, source_ref ):
        CPythonExpressionContractionBase.__init__(
            self,
            kind        = "EXPRESSION_DICT_CONTRACTION",
            code_prefix = "dictcontr",
            provider    = provider,
            source_ref  = source_ref
        )

    def createProvidedVariable( self, variable_name ):
        return Variables.LocalLoopVariable( owner = self, variable_name = variable_name )

class CPythonExpressionDictContractionKeyValue( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, provider, key, value, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_DICT_PAIR", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "key"   : key,
                "value" : value
            }
        )

    getKey = CPythonChildrenHaving.childGetter( "key" )
    getValue = CPythonChildrenHaving.childGetter( "value" )

class CPythonExpressionSequenceCreation( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, sequence_kind, elements, source_ref ):
        assert sequence_kind in ( "TUPLE", "LIST" ), sequence_kind

        for element in elements:
            assert element.isExpression(), element

        CPythonNode.__init__( self, kind = "EXPRESSION_MAKE_SEQUENCE", source_ref = source_ref )

        self.sequence_kind = sequence_kind.lower()

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "elements" : tuple( elements ),
            }
        )

    def getSequenceKind( self ):
        return self.sequence_kind

    getElements = CPythonChildrenHaving.childGetter( "elements" )


class CPythonExpressionDictionaryCreation( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, keys, values, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_MAKE_DICTIONARY", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "keys" : tuple( keys ),
                "values" : tuple( values )
            }
        )

    getKeys = CPythonChildrenHaving.childGetter( "keys" )
    getValues = CPythonChildrenHaving.childGetter( "values" )

class CPythonExpressionSetCreation( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, values, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_MAKE_SET", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "values" : tuple( values )
            }
        )

    getValues = CPythonChildrenHaving.childGetter( "values" )


class CPythonStatementWith( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, source, target, body, source_ref ):
        CPythonNode.__init__( self, kind = "STATEMENT_WITH", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "expression" : source,
                "target"     : target,
                "frame"      : body
            }
        )

    getWithBody = CPythonChildrenHaving.childGetter( "frame" )
    getTarget = CPythonChildrenHaving.childGetter( "target" )
    getExpression = CPythonChildrenHaving.childGetter( "expression" )

class CPythonStatementForLoop( CPythonChildrenHaving, CPythonNode, MarkExceptionBreakContinueIndicator ):
    def __init__( self, source, target, body, no_break, source_ref ):
        CPythonNode.__init__( self, kind = "STATEMENT_FOR_LOOP", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "iterated" : source,
                "target"   : target,
                "else"     : no_break,
                "frame"    : body
            }
        )

        MarkExceptionBreakContinueIndicator.__init__( self )

    getIterated = CPythonChildrenHaving.childGetter( "iterated" )
    getLoopVariableAssignment = CPythonChildrenHaving.childGetter( "target" )
    getBody = CPythonChildrenHaving.childGetter( "frame" )
    getNoBreak = CPythonChildrenHaving.childGetter( "else" )

class CPythonStatementWhileLoop( CPythonChildrenHaving, CPythonNode, MarkExceptionBreakContinueIndicator ):
    def __init__( self, condition, body, no_enter, source_ref ):
        CPythonNode.__init__( self, kind = "STATEMENT_WHILE_LOOP", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "condition" : condition,
                "else"      : no_enter,
                "frame"     : body
            }
        )

        MarkExceptionBreakContinueIndicator.__init__( self )

    getLoopBody = CPythonChildrenHaving.childGetter( "frame" )
    getCondition = CPythonChildrenHaving.childGetter( "condition" )
    getNoEnter = CPythonChildrenHaving.childGetter( "else" )


class CPythonStatementExpressionOnly( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, expression, source_ref ):
        CPythonNode.__init__( self, kind = "STATEMENT_EXPRESSION", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "expression" : expression
            }
        )

    def getDetail( self ):
        return "expression %s" % self.getExpression()

    getExpression = CPythonChildrenHaving.childGetter( "expression" )


class CPythonExpressionAttributeLookup( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, expression, attribute, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_ATTRIBUTE_REF", source_ref = source_ref )

        self.attribute = attribute

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "expression" : expression
            }
        )

    def getAttributeName( self ):
        return self.attribute

    def getDetail( self ):
        return "attribute %s from %s" % ( self.getAttributeName(), self.getLookupSource() )

    getLookupSource = CPythonChildrenHaving.childGetter( "expression" )

class CPythonExpressionSubscriptionLookup( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, expression, subscript, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_SUBSCRIPTION_REF", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "expression" : expression,
                "subscript"  : subscript
            }
        )

    getLookupSource = CPythonChildrenHaving.childGetter( "expression" )
    getSubscript = CPythonChildrenHaving.childGetter( "subscript" )

class CPythonExpressionSlice( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, expression, lower, upper, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_SLICE_REF", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "expression" : expression,
                "upper"      : upper,
                "lower"      : lower
            }
        )

    getLookupSource = CPythonChildrenHaving.childGetter( "expression" )
    getUpper = CPythonChildrenHaving.childGetter( "upper" )
    getLower = CPythonChildrenHaving.childGetter( "lower" )


class CPythonExpressionSliceObject( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, lower, upper, step, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_SLICEOBJ_REF", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "upper"      : upper,
                "lower"      : lower,
                "step"       : step
            }
        )

    getLower = CPythonChildrenHaving.childGetter( "lower" )
    getUpper = CPythonChildrenHaving.childGetter( "upper" )
    getStep  = CPythonChildrenHaving.childGetter( "step" )

class CPythonComparison( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, comparison, source_ref ):
        operands = []
        comparators = []

        for count, operand in enumerate( comparison ):
            if count % 2 == 0:
                assert operand.isExpression()

                operands.append( operand )
            else:
                comparators.append( operand )

        CPythonNode.__init__( self, kind = "EXPRESSION_COMPARISON", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "operands" : tuple( operands ),
            }
        )

        self.comparators = tuple( comparators )

    getOperands = CPythonChildrenHaving.childGetter( "operands" )

    def getComparators( self ):
        return self.comparators


class CPythonDeclareGlobal( CPythonNode ):
    def __init__( self, variables, source_ref ):
        self.variables = variables[:]

        CPythonNode.__init__( self, kind = "STATEMENT_DECLARE_GLOBAL", source_ref = source_ref )

class CPythonExpressionConditional( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, condition, yes_expression, no_expression, source_ref ):

        CPythonNode.__init__( self, kind = "EXPRESSION_CONDITIONAL", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
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

class CPythonExpressionOR( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, expressions, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_CONDITION_OR", source_ref = source_ref )

        assert len( expressions ) >= 2

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "expressions" : tuple( expressions )
            }
        )


    getExpressions = CPythonChildrenHaving.childGetter( "expressions" )

class CPythonExpressionAND( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, expressions, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_CONDITION_AND", source_ref = source_ref )

        assert len( expressions ) >= 2

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "expressions" : tuple( expressions )
            }
        )


    getExpressions = CPythonChildrenHaving.childGetter( "expressions" )

class CPythonExpressionNOT( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, expression, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_CONDITION_NOT", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "expression" : expression
            }
        )

    getExpression = CPythonChildrenHaving.childGetter( "expression" )

class CPythonStatementConditional( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, conditions, branches, source_ref ):
        CPythonNode.__init__( self, kind = "STATEMENT_CONDITIONAL", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "conditions" : tuple( conditions ),
                "branches"   : tuple( branches )
            }
        )

    getConditions = CPythonChildrenHaving.childGetter( "conditions" )
    getBranches = CPythonChildrenHaving.childGetter( "branches" )


class CPythonStatementTryFinally( CPythonNode ):
    def __init__( self, tried, final, source_ref ):
        CPythonNode.__init__( self, kind = "STATEMENT_TRY_FINALLY", source_ref = source_ref )

        self.tried = tried
        self.final = final

    def getVisitableNodes( self ):
        return ( self.tried, self.final )

    def getBlockTry( self ):
        return self.tried

    def getBlockFinal( self ):
        return self.final


class CPythonStatementTryExcept( CPythonNode ):
    def __init__( self, tried, no_raise, catchers, assigns, catcheds, source_ref ):
        CPythonNode.__init__( self, kind = "STATEMENT_TRY_EXCEPT", source_ref = source_ref )

        self.tried = tried

        self.catchers = catchers[:]
        self.assigns = assigns[:]
        self.catcheds = catcheds[:]

        assert len( self.catchers ) == len( self.assigns ) == len( self.catcheds )

        self.no_raise = no_raise

    def getVisitableNodes( self ):
        result = [ self.tried ]

        for catcher, assign, catched in zip( self.catchers, self.assigns, self.catcheds ):
            if catcher is not None:
                result.append( catcher )

            if assign is not None:
                result.append( assign )

            result.append( catched )

        if self.no_raise is not None:
            result.append( self.no_raise )

        return result

    def getBlockTry( self ):
        return self.tried

    def getBlockNoRaise( self ):
        return self.no_raise

    def getExceptionAssigns( self ):
        return self.assigns

    def getExceptionCatchers( self ):
        return self.catchers

    def getExceptionCatchBranches( self ):
        return self.catcheds


class CPythonStatementRaiseException( CPythonNode ):
    def __init__( self, exception_type, exception_value, exception_trace, source_ref ):
        CPythonNode.__init__( self, kind = "STATEMENT_RAISE_EXCEPTION", source_ref = source_ref )

        self.exception_type = exception_type
        self.exception_value = exception_value
        self.exception_trace = exception_trace

    def getExceptionParameters( self ):
        if self.exception_trace is not None:
            return self.exception_type, self.exception_value, self.exception_trace
        elif self.exception_value is not None:
            return self.exception_type, self.exception_value
        elif self.exception_type is not None:
            return self.exception_type,
        else:
            return ()

    def getVisitableNodes( self ):
        return self.getExceptionParameters()

class CPythonStatementContinueLoop( CPythonNode, MarkExceptionBreakContinueIndicator ):
    def __init__( self, source_ref ):
        CPythonNode.__init__( self, kind = "STATEMENT_CONTINUE_LOOP", source_ref = source_ref )
        MarkExceptionBreakContinueIndicator.__init__( self )

class CPythonStatementBreakLoop( CPythonNode, MarkExceptionBreakContinueIndicator ):
    def __init__( self, source_ref ):
        CPythonNode.__init__( self, kind = "STATEMENT_BREAK_LOOP", source_ref = source_ref )
        MarkExceptionBreakContinueIndicator.__init__( self )

class CPythonStatementPass( CPythonNode ):
    def __init__( self, source_ref ):
        CPythonNode.__init__( self, kind = "STATEMENT_PASS", source_ref = source_ref )

class CPythonExpressionImport( CPythonNode ):
    def __init__( self, module_package, module_name, module_filename, source_ref ):
        assert module_package is None or isinstance( module_package, CPythonPackage )

        CPythonNode.__init__( self, kind = "EXPRESSION_BUILTIN_IMPORT", source_ref = source_ref )

        self.module_package = module_package
        self.module_name = module_name
        self.module_filename = module_filename

    def getModuleName( self ):
        return self.module_name

    def getModuleFilename( self ):
        return self.module_filename

    def getModulePackage( self ):
        return self.module_package

class CPythonStatementImportModules( CPythonNode ):
    def __init__( self, import_specs, source_ref ):
        CPythonNode.__init__( self, kind = "STATEMENT_IMPORT_MODULE", source_ref = source_ref )

        self.import_specs = tuple( import_specs )

    def getImports( self ):
        return self.import_specs

    def getModuleFilenames( self ):
        return [ import_spec.getFilename() for import_spec in self.import_specs if import_spec.getFilename() is not None ]

    def getModulePackages( self ):
        return [ import_spec.getPackage() for import_spec in self.import_specs if import_spec.getFilename() is not None ]


class CPythonStatementImportFrom( CPythonNode ):
    def __init__( self, provider, module_name, module_package, module_filename, imports, source_ref ):
        CPythonNode.__init__( self, kind = "STATEMENT_IMPORT_FROM", source_ref = source_ref )

        self.provider = provider

        self.module_filename = module_filename
        self.module_package = module_package
        self.module_name = module_name
        self.imports = imports[:]

    def getDetail( self ):
        return ";".join( str(v) for v in self.getImports() )

    def getImports( self ):
        return self.imports

    def getModuleName( self ):
        return self.module_name

    def getModulePackage( self ):
        return self.module_package

    def getTarget( self ):
        return self.provider

    def getModuleFilenames( self ):
        if self.module_filename is not None:
            return ( self.module_filename, )
        else:
            return ()

    def getModulePackages( self ):
        if self.module_filename is not None:
            return ( self.module_package, )
        else:
            return ()


class CPythonStatementExec( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, source, globals_arg, locals_arg, future_flags, source_ref ):
        CPythonNode.__init__( self, kind = "STATEMENT_EXEC", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "globals" : globals_arg,
                "locals"  : locals_arg,
                "source"  : source
            }
        )

        self.future_flags = future_flags

    _getGlobals = CPythonChildrenHaving.childGetter( "globals" )
    _getLocals = CPythonChildrenHaving.childGetter( "locals" )
    getSource = CPythonChildrenHaving.childGetter( "source" )

    def getMode( self ):
        return "exec"

    def getFutureFlags( self ):
        return self.future_flags

    def _convertNoneConstantToNone( self, value ):
        if value is not None and value.isConstantReference() and value.getConstant() is None:
            return None
        else:
            return value

    def getLocals( self ):
        return self._convertNoneConstantToNone( self._getLocals() )

    def getGlobals( self ):
        if self.getLocals() is None:
            return self._convertNoneConstantToNone( self._getGlobals() )
        else:
            return self._getGlobals()

class CPythonExpressionBuiltinCallGlobals( CPythonNode ):
    def __init__( self, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_BUILTIN_GLOBALS", source_ref = source_ref )

class CPythonExpressionBuiltinCallLocals( CPythonNode ):
    def __init__( self, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_BUILTIN_LOCALS", source_ref = source_ref )

class CPythonExpressionBuiltinCallDir( CPythonNode ):
    def __init__( self, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_BUILTIN_DIR", source_ref = source_ref )

class CPythonExpressionBuiltinCallVars( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, source, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_BUILTIN_VARS", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "source"  : source,
            }
        )

    getSource = CPythonChildrenHaving.childGetter( "source" )

class CPythonExpressionBuiltinCallEval( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, source, globals_arg, locals_arg, mode, future_flags, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_BUILTIN_EVAL", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "source"  : source,
                "globals" : globals_arg,
                "locals"  : locals_arg,
            }
        )

        self.mode = mode
        self.future_flags = future_flags

    getSource = CPythonChildrenHaving.childGetter( "source" )
    getGlobals = CPythonChildrenHaving.childGetter( "globals" )
    getLocals = CPythonChildrenHaving.childGetter( "locals" )

    def getMode( self ):
        return self.mode

    def getFutureFlags( self ):
        return self.future_flags

class CPythonExpressionBuiltinCallOpen( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, filename, mode, buffering, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_BUILTIN_OPEN", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "filename"  : filename,
                "mode"      : mode,
                "buffering" : buffering
            }
        )

    getFilename = CPythonChildrenHaving.childGetter( "filename" )
    getMode = CPythonChildrenHaving.childGetter( "mode" )
    getBuffering = CPythonChildrenHaving.childGetter( "buffering" )

class CPythonExpressionBuiltinCallChr( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, value, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_BUILTIN_CHR", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "value"     : value,
            }
        )

    getValue = CPythonChildrenHaving.childGetter( "value" )

class CPythonExpressionBuiltinCallOrd( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, value, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_BUILTIN_ORD", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "value"     : value,
            }
        )

    getValue = CPythonChildrenHaving.childGetter( "value" )

class CPythonExpressionBuiltinCallType1( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, value, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_BUILTIN_TYPE1", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "value"     : value,
            }
        )

    getValue = CPythonChildrenHaving.childGetter( "value" )

class CPythonExpressionBuiltinCallType3( CPythonChildrenHaving, CPythonNode ):
    def __init__( self, type_name, bases, type_dict, source_ref ):
        CPythonNode.__init__( self, kind = "EXPRESSION_BUILTIN_TYPE3", source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            names = {
                "type_name" : type_name,
                "bases"     : bases,
                "dict"      : type_dict
            }
        )

    getTypeName = CPythonChildrenHaving.childGetter( "type_name" )
    getBases = CPythonChildrenHaving.childGetter( "bases" )
    getDict = CPythonChildrenHaving.childGetter( "dict" )
