#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
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

from . import (
    Variables,
    TreeXML,
    Utils
)

from .odict import OrderedDict
from .nodes import OverflowCheck
from .nodes import UsageCheck
from .nodes import CallSpec

from .Constants import isMutable, isIterableConstant, isNumberConstant

class NodeCheckMetaClass( type ):
    kinds = set()

    def __init__( mcs, name, bases, dictionary ):
        if not name.endswith( "Base" ):
            assert ( "kind" in dictionary ), name
            kind = dictionary[ "kind" ]

            assert type( kind ) is str, name
            assert kind not in NodeCheckMetaClass.kinds, name

            NodeCheckMetaClass.kinds.add( kind )

            def convert( value ):
                if value in ( "AND", "OR", "NOT" ):
                    return value
                else:
                    return value.title()

            kind_to_name_part = "".join( [ convert( x ) for x in kind.split( "_" ) ] )

            assert name.endswith( kind_to_name_part ), ( name, kind_to_name_part )

            checker_method = "is" + kind_to_name_part

            if name.startswith( "CPython" ):
                checker_method = checker_method.replace( "CPython", "" )

            # Automatically add checker methods for everything.

            def checkKind( self ):
                return self.kind == kind

            if not hasattr( CPythonNodeBase, checker_method ):
                setattr( CPythonNodeBase, checker_method, checkKind )

        type.__init__( mcs, name, bases, dictionary )

# For every node type, there is a test, and then some more members, pylint: disable=R0904

class CPythonNodeBase:
    __metaclass__ = NodeCheckMetaClass

    kind = None

    def __init__( self, source_ref ):
        assert source_ref is not None
        assert source_ref.line is not None

        self.parent = None

        self.source_ref = source_ref

    def __repr__( self ):
        # This is to avoid crashes, because of bugs in detail. pylint: disable=W0702
        try:
            detail = self.getDetail()
        except:
            detail = "detail raises exception"

        if detail == "":
            return "<Node %s>" % self.getDescription()
        else:
            return "<Node %s %s>" % ( self.getDescription(), detail )

    def getDescription( self ):
        """ Description of the node, intented for use in __repr__ and graphical display.

        """
        return "%s at %s" % ( self.kind, self.source_ref.getAsString() )

    def getDetails( self ):
        """ Details of the node, intented for use in __repr__ and dumps.

        """
        # Virtual method, pylint: disable=R0201,W0613
        return {}

    def getDetail( self ):
        """ Details of the node, intented for use in __repr__ and graphical display.

        """
        # Virtual method, pylint: disable=R0201,W0613
        return ""

    def getParent( self ):
        """ Parent of the node. Every node except modules have to have a parent.

        """

        if self.parent is None and not self.isModule():
            assert False, ( self,  self.source_ref )

        return self.parent

    def getParentExecInline( self ):
        """ Return the parent that is an inlined exec.

        """

        parent = self.getParent()

        while parent is not None and not parent.isStatementExecInline():
            parent = parent.getParent()

        return parent

    def getParentFunction( self ):
        """ Return the parent that is a function.

        """

        parent = self.getParent()

        while parent is not None and not parent.isExpressionFunctionBody():
            parent = parent.getParent()

        return parent

    def getParentClass( self ):
        """ Return the parent that is a class body.

        """

        parent = self.getParent()

        while parent is not None and not parent.isExpressionClassBody():
            parent = parent.getParent()

        return parent

    def getParentModule( self ):
        """ Return the parent that is module.

        """
        parent = self

        while not parent.isModule():
            if hasattr( parent, "provider" ):
                # After we checked, we can use it, will be much faster, pylint: disable=E1101
                parent = parent.provider
            else:
                parent = parent.getParent()

        assert isinstance( parent, CPythonModule ), parent.__class__

        return parent

    def isParentVariableProvider( self ):
        # Check if it's a closure giver or a class, in which cases it can provide
        # variables, pylint: disable=E1101
        return isinstance( self, CPythonClosureGiverNodeBase ) or self.isExpressionClassBody()

    def isClosureVariableTaker( self ):
        return isinstance( self, CPythonClosureTaker )

    def getParentVariableProvider( self ):
        parent = self.getParent()

        while not parent.isParentVariableProvider():
            parent = parent.getParent()

        return parent

    def getSourceReference( self ):
        return self.source_ref

    def asXml( self ):
        result = TreeXML.makeNodeElement(
            node = self
        )

        for child in self.getVisitableNodes():
            result.append(
                child.asXml()
            )

        return result

    def dump( self, level = 0 ):
        print( "    " * level, self )

        print( "    " * level, "*" * 10 )

        for visitable in self.getVisitableNodes():
            visitable.dump( level + 1 )

        print( "    " * level, "*" * 10 )

    def isModule( self ):
        return self.kind in ( "MODULE", "PACKAGE" )

    def isExpression( self ):
        return self.kind.startswith( "EXPRESSION_" )

    def isStatement( self ):
        return self.kind.startswith( "STATEMENT_" )

    def isExpressionBuiltin( self ):
        return self.kind.startswith( "EXPRESSION_BUILTIN_" )

    def isOperation( self ):
        return self.kind.startswith( "EXPRESSION_" ) and self.kind.endswith( "_OPERATION" )

    def isAssignTargetSomething( self ):
        return self.kind.startswith( "ASSIGN_" )

    def visit( self, context, visitor ):
        visitor( self )

        for visitable in self.getVisitableNodes():
            visitable.visit( context, visitor )

    def getVisitableNodes( self ):
        # Virtual method, pylint: disable=R0201,W0613
        return ()

    def getSameScopeNodes( self ):
        """ Get nodes to be evaluated within the same scope.

            These are all that are not closure variable takers.
        """

        return [
            node
            for node in
            self.getVisitableNodes()
            if not node.isClosureVariableTaker()
        ]


    def replaceWith( self, new_node ):
        self.parent.replaceChild( old_node = self, new_node = new_node )

    def getName( self ):
        # Virtual method, pylint: disable=R0201,W0613
        return None

class CPythonNamedNodeBase( CPythonNodeBase ):
    def __init__( self, name, source_ref ):
        assert name is not None
        assert " " not in name
        assert "<" not in name

        CPythonNodeBase.__init__( self, source_ref = source_ref )

        self.name = name

    def getName( self ):
        return self.name

    def getFullName( self ):
        result = self.getName()

        current = self

        while True:
            current = current.getParent()

            if current is None:
                break

            name = current.getName()

            if name is not None:
                result = "%s__%s" % ( name, result )

        assert "<" not in result, result

        return result

class CPythonCodeNodeBase( CPythonNamedNodeBase ):
    def __init__( self, name, code_prefix, source_ref ):
        CPythonNamedNodeBase.__init__(
            self,
            name       = name,
            source_ref = source_ref
        )

        self.code_prefix = code_prefix
        self.uids = {}

        self.code_name = None

    def getCodeName( self ):
        if self.code_name is None:

            search = self.parent

            while search is not None:
                if isinstance( search, CPythonCodeNodeBase ):
                    break

                search = search.parent

            if search is None:
                assert self.isModule()

                return "module_" + self.name

            parent_name = search.getCodeName()

            uid = "_%d" % search.getChildUID( self )

            if isinstance( self, CPythonNamedNodeBase ):
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



class CPythonChildrenHaving:
    named_children = ()

    def __init__( self, values ):
        assert len( self.named_children )
        assert type( self.named_children ) is tuple

        for key in values.keys():
            assert key in self.named_children

        self.child_values = dict.fromkeys( self.named_children )
        self.child_values.update( values )

        for value in values.values():
            assert type( value ) != list

    def setChild( self, name, value ):
        assert name in self.child_values, name

        if type( value ) == list:
            value = tuple( value )

        self.child_values[ name ] = value

    def getChild( self, name ):
        assert name in self.child_values, name

        return self.child_values[ name ]

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

        for name in self.named_children:
            value = self.child_values[ name ]

            if value is None:
                pass
            elif type( value ) is tuple:
                result += list( value )
            elif isinstance( value, CPythonNodeBase ):
                result.append( value )
            else:
                assert False, ( name, value, value.__class__ )

        return tuple( result )


    def replaceChild( self, old_node, new_node ):
        for key, value in self.child_values.items():
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
            elif isinstance( value, CPythonNodeBase ):
                if old_node == value:
                    self.setChild( key, new_node )

                    break
            else:
                assert False, ( key, value, value.__class__ )
        else:
            assert False, ( "didn't find child", old_node, "in", self )

        if new_node is not None:
            new_node.parent = old_node.parent

class CPythonClosureGiverNodeBase( CPythonCodeNodeBase ):
    """ Mixin for nodes that provide variables for closure takers. """
    def __init__( self, name, code_prefix, source_ref ):
        CPythonCodeNodeBase.__init__(
            self,
            name        = name,
            code_prefix = code_prefix,
            source_ref  = source_ref
        )

        self.providing = OrderedDict()

    def hasProvidedVariable( self, variable_name ):
        return variable_name in self.providing

    def getProvidedVariable( self, variable_name ):
        if variable_name not in self.providing:
            self.providing[ variable_name ] = self.createProvidedVariable(
                variable_name = variable_name
            )

        return self.providing[ variable_name ]

    def createProvidedVariable( self, variable_name ):
        # Virtual method, pylint: disable=R0201,W0613
        assert type( variable_name ) is str

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
        # Abstract method, pylint: disable=R0201,W0613
        return False

    def reconsiderVariable( self, variable ):
        # TODO: Why doesn't this fit in as well.
        if self.isModule():
            return

        assert variable.getOwner() is self

        if variable.getName() in  self.providing:
            assert self.providing[ variable.getName() ] is variable, (
                self.providing[ variable.getName() ], "is not", variable, self
            )

            if not variable.isShared():
                # TODO: The functions/classes should have have a clearer scope too.
                usages = UsageCheck.getVariableUsages( self, variable )

                if not usages:
                    del self.providing[ variable.getName() ]


class CPythonParameterHavingNodeBase( CPythonClosureGiverNodeBase ):
    def __init__( self, name, code_prefix, parameters, source_ref ):
        CPythonClosureGiverNodeBase.__init__(
            self,
            name        = name,
            code_prefix = code_prefix,
            source_ref  = source_ref
        )

        self.parameters = parameters
        self.parameters.setOwner( self )

        self.registerProvidedVariables(
            variables = self.parameters.getVariables()
        )

    def getParameters( self ):
        return self.parameters


class CPythonClosureTaker:
    """ Mixin for nodes that accept variables from closure givers. """

    def __init__( self, provider ):
        assert self.__class__.early_closure is not None, self

        assert provider.isParentVariableProvider(), provider

        self.provider = provider

        self.taken = set()

    def getParentVariableProvider( self ):
        return self.provider

    def getClosureVariable( self, variable_name ):
        result = self.provider.getVariableForClosure(
            variable_name = variable_name
        )
        assert result is not None, variable_name

        # There is no maybe with closures. It means, it is global variable in
        # this case.
        if result.isMaybeLocalVariable():
            # This mixin is used with nodes only, but doesn't want to inherit from
            # it, pylint: disable=E1101
            result = self.getParentModule().getVariableForClosure(
                variable_name = variable_name
            )

        return self.addClosureVariable( result )

    def addClosureVariable( self, variable, global_statement = False ):
        variable = variable.makeReference( self )

        if variable.isModuleVariable() and global_statement:
            variable.markFromGlobalStatement()

        self.taken.add( variable )

        return variable

    def getClosureVariables( self ):
        return tuple(
            sorted(
                [ take for take in self.taken if take.isClosureReference() ],
                key = lambda x : x.getName()
            )
        )

    def hasTakenVariable( self, variable_name ):
        for variable in self.taken:
            if variable.getName() == variable_name:
                return True
        else:
            return False

    def getTakenVariable( self, variable_name ):
        for variable in self.taken:
            if variable.getName() == variable_name:
                return variable
        else:
            return None

    # Normally it's good to lookup name references immediately, but in case of a function
    # body it is not allowed to do that, because a later assignment needs to be queried
    # first. Nodes need to indicate via this if they would like to resolve references at
    # the same time as assignments.
    early_closure = None

    def isEarlyClosure( self ):
        return self.early_closure

class MarkExceptionBreakContinueIndicator:
    """ Mixin for indication that a break and continue could be real exceptions.

    """

    def __init__( self ):
        self.break_continue_exception = False

    def markAsExceptionBreakContinue( self ):
        self.break_continue_exception = True

    def needsExceptionBreakContinue( self ):
        return self.break_continue_exception

class CPythonModule( CPythonChildrenHaving, CPythonClosureTaker, CPythonClosureGiverNodeBase ):
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
        assert package is None or type( package ) is str

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


class CPythonExpressionClassBody( CPythonChildrenHaving, CPythonClosureTaker, CPythonCodeNodeBase ):
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

        self.doc = doc

        self.variables = {}
        self.locals_dict = False

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

    def hasLocalsDict( self ):
        return self.locals_dict

    def markAsLocalsDict( self ):
        self.locals_dict = True


class CPythonStatementsSequence( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENTS_SEQUENCE"

    named_children = ( "statements", )

    def __init__( self, statements, source_ref ):
        for statement in statements:
            assert statement.isStatement() or statement.isStatementsSequence(), statement

        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "statements" : tuple( statements )
            }
        )

    getStatements = CPythonChildrenHaving.childGetter( "statements" )


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

    def getAssignTargetVariableNodes( self ):
        return ( self, )

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
                "subscript" : subscript
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

    def getAssignTargetVariableNodes( self ):
        result = []

        for element in self.elements:
            result += element.getAssignTargetVariableNodes()

        return tuple( result )

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

class CPythonExpressionConstantRef( CPythonNodeBase ):
    kind = "EXPRESSION_CONSTANT_REF"

    def __init__( self, constant, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        self.constant = constant

    def getDetails( self ):
        return { "value" : self.constant }

    def getDetail( self ):
        return repr( self.constant )

    def getConstant( self ):
        return self.constant

    def isMutable( self ):
        return isMutable( self.constant )

    def isNumberConstant( self ):
        return isNumberConstant( self.constant )

    def isIterableConstant( self ):
        return isIterableConstant( self.constant )

    def isBoolConstant( self ):
        return type( self.constant ) is bool

def makeConstantReplacementNode( constant, node ):
    return CPythonExpressionConstantRef(
        constant   = constant,
        source_ref = node.getSourceReference()
    )

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

    def getParameters( self ):
        return self.getBody().getParameters()

    def isGenerator( self ):
        return self.getBody().isGenerator()


class CPythonExpressionLambdaBody( CPythonChildrenHaving, CPythonParameterHavingNodeBase, CPythonClosureTaker ):
    kind = "EXPRESSION_LAMBDA_BODY"

    named_children = ( "body", )

    early_closure = True

    def __init__( self, provider, parameters, source_ref ):
        CPythonClosureTaker.__init__(
            self,
            provider = provider
        )

        CPythonParameterHavingNodeBase.__init__(
            self,
            name        = "lamda",
            code_prefix = "lamda",
            parameters  = parameters,
            source_ref  = source_ref
        )

        CPythonChildrenHaving.__init__(
            self,
            values = {}
        )

        self.is_generator = False

    getBody = CPythonChildrenHaving.childGetter( "body" )
    setBody = CPythonChildrenHaving.childSetter( "body" )

    def isGenerator( self ):
        return self.is_generator

    def markAsGenerator( self ):
        self.is_generator = True

    def getVariables( self ):
        return self.providing.values()

    def getUserLocalVariables( self ):
        return [
            variable
            for variable in self.providing.values()
            if variable.isLocalVariable() and not variable.isParameterVariable()
        ]

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


class CPythonExpressionFunctionBody( CPythonChildrenHaving, CPythonParameterHavingNodeBase, CPythonClosureTaker ):
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

        self.parent = provider

        self.is_generator = False
        self.contains_exec = False
        self.locals_dict = False

        self.doc = doc

    def getDetails( self ):
        return { "name" : self.getFunctionName(), "parameters" : self.getParameters() }

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
        return [
            variable for
            variable in
            self.providing.values()
            if variable.isLocalVariable() and not variable.isParameterVariable()
        ]

    def getVariables( self ):
        return self.providing.values()

    def markAsGenerator( self ):
        self.is_generator = True

    def markAsLocalsDict( self ):
        self.locals_dict = True

    def markAsExecContaining( self ):
        self.contains_exec = True

    def hasLocalsDict( self ):
        return self.locals_dict

    def isGenerator( self ):
        return self.is_generator

    def isExecContaining( self ):
        return self.contains_exec

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
                # TODO: Allow closures other than modules.
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

class CPythonExpressionVariableRef( CPythonNodeBase ):
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

    def getVariableName( self ):
        return self.variable_name

    def getVariable( self ):
        return self.variable

    def setVariable( self, variable, replace = False ):
        assert isinstance( variable, Variables.Variable ), repr( variable )

        assert self.variable is None or replace

        self.variable = variable

class CPythonExpressionYield( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_YIELD"

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

class CPythonStatementAssert( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_ASSERT"

    named_children = ( "expression", "failure" )

    def __init__( self, expression, failure, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "expression" : expression,
                "failure"    : failure
            }
        )

    getExpression = CPythonChildrenHaving.childGetter( "expression" )
    getArgument   = CPythonChildrenHaving.childGetter( "failure" )

class CPythonExpressionFunctionCall( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_FUNCTION_CALL"

    named_children = ( "called", "positional_args", "named_args", "list_star_arg", "dict_star_arg" )

    def __init__( self, called_expression, positional_args, list_star_arg, dict_star_arg, named_args, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        assert called_expression.isExpression()

        for positional_arg in positional_args:
            assert positional_arg.isExpression()

        named_argument_names = []
        named_argument_values = []

        for named_arg_desc in named_args:
            named_arg_name, named_arg_value = named_arg_desc

            assert type( named_arg_name ) == str
            assert named_arg_value.isExpression()

            named_argument_names.append( named_arg_name )
            named_argument_values.append( named_arg_value )

        self.named_argument_names = tuple( named_argument_names )

        CPythonChildrenHaving.__init__(
            self,
            values = {
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
    setPositionalArguments = CPythonChildrenHaving.childSetter( "positional_args" )
    getStarListArg = CPythonChildrenHaving.childGetter( "list_star_arg" )
    setStarListArg = CPythonChildrenHaving.childSetter( "list_star_arg" )
    getStarDictArg = CPythonChildrenHaving.childGetter( "dict_star_arg" )
    setStarDictArg = CPythonChildrenHaving.childSetter( "dict_star_arg" )

    def getNamedArgumentNames( self ):
        return self.named_argument_names

    def getNamedArguments( self ):
        return zip( self.named_argument_names, self.getChild( "named_args" ) )

    def isEmptyCall( self ):
        return not self.getPositionalArguments() and not self.getChild( "named_args" ) and \
               not self.getStarListArg() and not self.getStarDictArg()

    def hasOnlyPositionalArguments( self ):
        return not self.getNamedArguments() and not self.getStarListArg() and not self.getStarDictArg()

    def hasOnlyConstantArguments( self ):
        for positional_arg in self.getPositionalArguments():
            if not positional_arg.isExpressionConstantRef():
                return False

        for named_arg in self.getChild( "named_args" ):
            if not named_arg.isExpressionConstantRef():
                return False

        list_star_arg = self.getStarListArg()

        if list_star_arg is not None and not list_star_arg.isExpressionConstantRef():
            return False

        dict_star_arg = self.getStarDictArg()

        if dict_star_arg is not None and not dict_star_arg.isExpressionConstantRef():
            return False

        return True

    def getCallSpec( self ):
        return CallSpec.CallSpec(
            positional_args = self.getPositionalArguments(),
            named_args      = self.getNamedArguments(),
            list_star_arg   = self.getStarListArg(),
            dict_star_arg   = self.getStarDictArg()
        )


class CPythonExpressionBinaryOperation( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_BINARY_OPERATION"

    named_children = ( "operands", )

    def __init__( self, operator, left, right, source_ref ):
        assert left.isExpression() and right.isExpression, ( left, right )

        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "operands" : ( left, right )
            }
        )

        self.operator = operator

    def getOperator( self ):
        return self.operator

    def getDetail( self ):
        return self.operator

    getOperands = CPythonChildrenHaving.childGetter( "operands" )

class CPythonExpressionUnaryOperation( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_UNARY_OPERATION"

    named_children = ( "operands", )

    def __init__( self, operator, operand, source_ref ):
        assert operand.isExpression(), operand

        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "operands" : ( operand, )
            }
        )

        self.operand = operand
        self.operator = operator

    def isOperation( self ):
        return True

    def getOperator( self ):
        return self.operator

    getOperands = CPythonChildrenHaving.childGetter( "operands" )

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


class CPythonExpressionGeneratorBody( CPythonExpressionContractionBodyBase ):
    kind = "EXPRESSION_GENERATOR_BODY"

    def __init__( self, provider, source_ref ):
        CPythonExpressionContractionBodyBase.__init__(
            self,
            code_prefix = "genexpr",
            provider    = provider,
            source_ref  = source_ref
        )

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

class CPythonExpressionDictContractionKeyValue( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_DICT_CONTRACTION_KEY_VALUE"

    named_children = ( "key", "value" )

    def __init__( self, key, value, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "key"   : key,
                "value" : value
            }
        )

    getKey = CPythonChildrenHaving.childGetter( "key" )
    getValue = CPythonChildrenHaving.childGetter( "value" )

class CPythonExpressionMakeSequence( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_MAKE_SEQUENCE"

    named_children = ( "elements", )

    def __init__( self, sequence_kind, elements, source_ref ):
        assert sequence_kind in ( "TUPLE", "LIST" ), sequence_kind

        for element in elements:
            assert element.isExpression(), element

        CPythonNodeBase.__init__( self, source_ref = source_ref )

        self.sequence_kind = sequence_kind.lower()

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "elements" : tuple( elements ),
            }
        )

    def getSequenceKind( self ):
        return self.sequence_kind

    getElements = CPythonChildrenHaving.childGetter( "elements" )


class CPythonExpressionMakeDict( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_MAKE_DICT"

    # TODO: Not correct, should be using value pairs!
    named_children = ( "values", "keys" )

    def __init__( self, keys, values, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "keys" : tuple( keys ),
                "values" : tuple( values )
            }
        )

    getKeys = CPythonChildrenHaving.childGetter( "keys" )
    getValues = CPythonChildrenHaving.childGetter( "values" )

class CPythonExpressionMakeSet( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_MAKE_SET"

    named_children = ( "values", )

    def __init__( self, values, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "values" : tuple( values )
            }
        )

    getValues = CPythonChildrenHaving.childGetter( "values" )


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
    getNoBreak = CPythonChildrenHaving.childGetter( "else" )
    setNoBreak = CPythonChildrenHaving.childSetter( "else" )

class CPythonStatementWhileLoop( CPythonChildrenHaving, CPythonNodeBase, MarkExceptionBreakContinueIndicator ):
    kind = "STATEMENT_WHILE_LOOP"

    named_children = ( "condition", "frame", "else" )

    def __init__( self, condition, body, no_enter, source_ref ):
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


class CPythonStatementExpressionOnly( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_EXPRESSION_ONLY"

    named_children = ( "expression", )

    def __init__( self, expression, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "expression" : expression
            }
        )

    def getDetail( self ):
        return "expression %s" % self.getExpression()

    getExpression = CPythonChildrenHaving.childGetter( "expression" )


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
    getUpper = CPythonChildrenHaving.childGetter( "upper" )
    getLower = CPythonChildrenHaving.childGetter( "lower" )


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

class CPythonExpressionComparison( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_COMPARISON"

    named_children = ( "operands", )

    def __init__( self, comparison, source_ref ):
        operands = []
        comparators = []

        for count, operand in enumerate( comparison ):
            if count % 2 == 0:
                assert operand.isExpression()

                operands.append( operand )
            else:
                comparators.append( operand )

        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "operands" : tuple( operands ),
            }
        )

        self.comparators = tuple( comparators )

    getOperands = CPythonChildrenHaving.childGetter( "operands" )

    def getComparators( self ):
        return self.comparators


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

class CPythonExpressionBoolOR( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_BOOL_OR"

    named_children = ( "expressions", )

    def __init__( self, expressions, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        assert len( expressions ) >= 2

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "expressions" : tuple( expressions )
            }
        )


    getExpressions = CPythonChildrenHaving.childGetter( "expressions" )

class CPythonExpressionBoolAND( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_BOOL_AND"

    named_children = ( "expressions", )

    def __init__( self, expressions, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        assert len( expressions ) >= 2

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "expressions" : tuple( expressions )
            }
        )


    getExpressions = CPythonChildrenHaving.childGetter( "expressions" )

class CPythonExpressionBoolNOT( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_BOOL_NOT"

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


class CPythonStatementTryExcept( CPythonNodeBase ):
    kind = "STATEMENT_TRY_EXCEPT"

    def __init__( self, tried, no_raise, catchers, assigns, catcheds, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        self.tried = tried

        self.catchers = catchers[:]
        self.assigns = assigns[:]
        self.catcheds = catcheds[:]

        assert len( self.catchers ) == len( self.assigns ) == len( self.catcheds )

        self.no_raise = no_raise

    def getVisitableNodes( self ):
        if self.tried is not None:
            result = [ self.tried ]
        else:
            result = []

        for catcher, assign, catched in zip( self.catchers, self.assigns, self.catcheds ):
            if catcher is not None:
                result.append( catcher )

            if assign is not None:
                result.append( assign )

            if catched is not None:
                result.append( catched )

        if self.no_raise is not None:
            result.append( self.no_raise )

        return result

    def replaceChild( self, old_node, new_node ):
        if old_node is self.tried:
            self.tried = new_node
        elif old_node is self.no_raise:
            self.no_raise = new_node
        elif old_node in self.catchers:
            self.catchers[ self.catchers.index( old_node ) ] = new_node
        elif old_node in self.catcheds:
            self.catcheds[ self.catcheds.index( old_node ) ] = new_node
        elif old_node in self.assigns:
            self.assigns[ self.assigns.index( old_node ) ] = new_node
        else:
            assert False, ( "didn't find child", old_node, "in", self )

        if new_node is not None:
            new_node.parent = old_node.parent

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


class CPythonStatementRaiseException( CPythonNodeBase ):
    kind = "STATEMENT_RAISE_EXCEPTION"

    def __init__( self, exception_type, exception_value, exception_trace, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        self.exception_type = exception_type
        self.exception_value = exception_value
        self.exception_trace = exception_trace

        self.reraise_local = False

    def getExceptionParameters( self ):
        if self.exception_trace is not None:
            return self.exception_type, self.exception_value, self.exception_trace
        elif self.exception_value is not None:
            return self.exception_type, self.exception_value
        elif self.exception_type is not None:
            return self.exception_type,
        else:
            return ()

    def isReraiseException( self ):
        return self.getExceptionParameters() == ()

    def isReraiseExceptionLocal( self ):
        assert self.isReraiseException()

        return self.reraise_local

    def markAsReraiseLocal( self ):
        self.reraise_local = True

    def getVisitableNodes( self ):
        return self.getExceptionParameters()

class CPythonExpressionRaiseException( CPythonNodeBase ):
    kind = "EXPRESSION_RAISE_EXCEPTION"

    def __init__( self, exception_type, exception_value, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        self.exception_type = exception_type
        self.exception_value = exception_value

    def getExceptionParameters( self ):
        if self.exception_value is not None:
            return self.exception_type, self.exception_value
        elif self.exception_type is not None:
            return self.exception_type,
        else:
            return ()

    def getExceptionType( self ):
        return self.exception_type

    def getExceptionValue( self ):
        return self.exception_value

    def getVisitableNodes( self ):
        return self.getExceptionParameters()


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

class CPythonExpressionBuiltinImport( CPythonNodeBase ):
    kind = "EXPRESSION_BUILTIN_IMPORT"

    def __init__( self, module_name, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        self.module_name = module_name

    def getModuleName( self ):
        return self.module_name

    def getImportName( self ):
        return self.module_name.split(".")[0]

    def getLevel( self ):
        return 0 if self.source_ref.getFutureSpec().isAbsoluteImport() else 1

class CPythonStatementImportEmbedded( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_IMPORT_EMBEDDED"

    named_children = ( "target", "module" )

    def __init__( self, target, module_name, import_name, module, source_ref ):
        CPythonChildrenHaving.__init__(
            self,
            values = {
                "target" : target,
                "module" : module
            }
        )

        self.module_name = module_name
        self.import_name = import_name

        CPythonNodeBase.__init__( self, source_ref = source_ref )

    def getDetails( self ):
        return { "import_name" : self.import_name, "module_name" : self.module_name }

    def getModuleName( self ):
        return self.module_name

    def getImportName( self ):
        return self.import_name

    # TODO: visitForest should see the module.
    def getVisitableNodes( self ):
        return ( self.getTarget(), )

    getTarget = CPythonChildrenHaving.childGetter( "target" )
    getModule = CPythonChildrenHaving.childGetter( "module" )

class CPythonStatementImportExternal( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_IMPORT_EXTERNAL"

    named_children = ( "target", )

    def __init__( self, target, module_name, import_name, level, source_ref ):
        assert target is not None

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "target" : target,
            }
        )

        CPythonNodeBase.__init__( self, source_ref = source_ref )

        self.module_name = module_name
        self.import_name = import_name
        self.level = level

    def getDetails( self ):
        return {
            "import_name" : self.import_name,
            "module_name" : self.module_name,
            "level"       : self.level
        }

    def getModuleName( self ):
        return self.module_name

    def getImportName( self ):
        return self.import_name

    def getLevel( self ):
        return self.level

    getTarget = CPythonChildrenHaving.childGetter( "target" )


class CPythonStatementImportFromExternal( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_IMPORT_FROM_EXTERNAL"

    named_children = ( "targets", )

    def __init__( self, targets, module_name, imports, level, source_ref ):
        CPythonChildrenHaving.__init__(
            self,
            values = {
                "targets" : tuple( targets ),
            }
        )

        CPythonNodeBase.__init__( self, source_ref = source_ref )

        self.module_name = module_name
        self.level = level

        self.imports = tuple( imports )

    def getDetail( self ):
        return ";".join( self.getImports() )

    def getImports( self ):
        return self.imports

    def getModuleName( self ):
        return self.module_name

    def getLevel( self ):
        return self.level

    getTargets = CPythonChildrenHaving.childGetter( "targets" )

class CPythonStatementImportFromEmbedded( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_IMPORT_FROM_EMBEDDED"

    named_children = ( "targets", "sub_modules" )

    def __init__( self, targets, module_name, sub_modules, imports, source_ref ):
        CPythonChildrenHaving.__init__(
            self,
            values = {
                "targets"     : tuple( targets ),
                "sub_modules" : tuple( sub_modules )
            }
        )

        CPythonNodeBase.__init__( self, source_ref = source_ref )

        self.module_name = module_name

        self.imports = tuple( imports )

    def getDetail( self ):
        return ";".join( self.getImports() )

    def getImports( self ):
        return self.imports

    def getModuleName( self ):
        return self.module_name

    # TODO: visitForest should see the module.
    def getVisitableNodes( self ):
        return self.getTargets()

    getTargets = CPythonChildrenHaving.childGetter( "targets" )
    getSubModules = CPythonChildrenHaving.childGetter( "sub_modules" )

class CPythonStatementImportStarExternal( CPythonNodeBase ):
    kind = "STATEMENT_IMPORT_STAR_EXTERNAL"

    def __init__( self, module_name, level, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        self.module_name = module_name
        self.level = level

    def getModuleName( self ):
        return self.module_name

    def getLevel( self ):
        return self.level

class CPythonStatementImportStarEmbedded( CPythonNodeBase ):
    kind = "STATEMENT_IMPORT_STAR_EMBEDDED"

    def __init__( self, module_name, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        self.module_name = module_name

    def getModuleName( self ):
        return self.module_name


def _convertNoneConstantToNone( value ):
    if value is not None and value.isExpressionConstantRef() and value.getConstant() is None:
        return None
    else:
        return value

class CPythonStatementExec( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_EXEC"

    named_children = ( "source", "globals", "locals" )

    def __init__( self, source_code, globals_arg, locals_arg, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "globals" : globals_arg,
                "locals"  : locals_arg,
                "source"  : source_code
            }
        )

    getSourceCode = CPythonChildrenHaving.childGetter( "source" )
    _getGlobals = CPythonChildrenHaving.childGetter( "globals" )
    _getLocals = CPythonChildrenHaving.childGetter( "locals" )

    def getLocals( self ):
        return _convertNoneConstantToNone( self._getLocals() )

    def getGlobals( self ):
        if self.getLocals() is None:
            return _convertNoneConstantToNone( self._getGlobals() )
        else:
            return self._getGlobals()

class CPythonStatementExecInline( CPythonChildrenHaving, CPythonClosureTaker, CPythonClosureGiverNodeBase ):
    kind = "STATEMENT_EXEC_INLINE"

    named_children = ( "body", )

    early_closure = True

    def __init__( self, provider, source_ref ):
        CPythonClosureTaker.__init__( self, provider )
        CPythonClosureGiverNodeBase.__init__(
            self,
            name        = "exec_inline",
            code_prefix = "exec_inline",
            source_ref  = source_ref
        )

        CPythonChildrenHaving.__init__(
            self,
            values = {}
        )

    getBody = CPythonChildrenHaving.childGetter( "body" )
    setBody = CPythonChildrenHaving.childSetter( "body" )

    def getVariableForAssignment( self, variable_name ):
        # print ( "ASS inline", self, variable_name )

        if self.hasProvidedVariable( variable_name ):
            return self.getProvidedVariable( variable_name )

        result = self.getProvidedVariable( variable_name )

        # Remember that we need that closure for something.
        self.registerProvidedVariable( result )

        # print ( "RES inline", result )

        return result

    def getVariableForReference( self, variable_name ):
        # print ( "REF inline", self, variable_name )

        result = self.getVariableForAssignment( variable_name )

        # print ( "RES inline", result )

        return result

    def createProvidedVariable( self, variable_name ):
        # print ( "CREATE inline", self, variable_name )

        # An exec in a module gives a module variable always, on the top level
        # of an exec, if it's not already a global through a global statement,
        # the parent receives a local variable now.
        if self.provider.isModule():
            return self.provider.getProvidedVariable(
                variable_name = variable_name
            )
        else:
            return Variables.LocalVariable(
                owner         = self.provider,
                variable_name = variable_name
            )


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

class CPythonExpressionBuiltinEval( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_BUILTIN_EVAL"

    named_children = ( "source", "globals", "locals" )

    def __init__( self, source_code, globals_arg, locals_arg, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "source"  : source_code,
                "globals" : globals_arg,
                "locals"  : locals_arg,
            }
        )

    getSourceCode = CPythonChildrenHaving.childGetter( "source" )
    getGlobals = CPythonChildrenHaving.childGetter( "globals" )
    getLocals = CPythonChildrenHaving.childGetter( "locals" )

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

class CPythonExpressionBuiltinSingleArgBase( CPythonChildrenHaving, CPythonNodeBase ):
    named_children = ( "value", )

    def __init__( self, value, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "value" : value,
            }
        )

    getValue = CPythonChildrenHaving.childGetter( "value" )


class CPythonExpressionBuiltinChr( CPythonExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_CHR"

class CPythonExpressionBuiltinOrd( CPythonExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_ORD"

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

class CPythonExpressionBuiltinRange( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_BUILTIN_RANGE"

    named_children = ( "low", "high", "step" )

    def __init__( self, low, high, step, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "low"  : low,
                "high" : high,
                "step" : step
            }
        )

    getLow  = CPythonChildrenHaving.childGetter( "low" )
    getHigh = CPythonChildrenHaving.childGetter( "high" )
    getStep = CPythonChildrenHaving.childGetter( "step" )

class CPythonExpressionBuiltinDict( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_BUILTIN_DICT"

    named_children = ( "pos_arg", "named_args" )

    def __init__( self, pos_arg, named_args, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

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
            values = {
                "pos_arg"    : pos_arg,
                "named_args" : tuple( named_argument_values )
            }
        )

    getPositionalArgument = CPythonChildrenHaving.childGetter( "pos_arg" )

    def getNamedArguments( self ):
        return zip( self.named_argument_names, self.getChild( "named_args" ) )

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
