# 
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
# 
#     Part of "Nuitka", my attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
# 
#     If you submit patches to this software in either form, you automatically
#     grant me a copyright assignment to the code, or in the alternative a BSD
#     license to the code, should your jurisdiction prevent this. This is to
#     reserve my ability to re-license the code at any time.
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
from nodes.ParameterSpec import ParameterSpec

import TreeTransforming
import PythonOperators
import Variables
import Options
import Nodes

import compiler, imp

class SourceCodeReference:
    @classmethod
    def fromFilename( cls, filename ):
        return cls.fromFilenameAndLine( filename, 1 )

    @classmethod
    def fromFilenameAndLine( cls, filename, line ):
        result = cls()

        result.filename = filename
        result.line = line

        return result

    def __init__( self ):
        self.line = None
        self.filename = None

    def __repr__( self ):
        return "<SourceCodeReference to %s:%s>" % ( self.filename, self.line )

    def atLineNumber( self, line ):
        return SourceCodeReference.fromFilenameAndLine(
            filename = self.filename,
            line = line
        )

    def getLineNumber( self ):
        return self.line

    def getFilename( self ):
        return self.filename

    def getAsString( self ):
        return "%s:%s" % ( self.filename, self.line )

def getKind( node ):
    return node.__class__.__name__.split( "." )[-1]

def buildStatementsNode( provider, node, source_ref ):
    assert getKind( node ) == "Stmt"

    return Nodes.CPythonStatementSequence(
        statements = buildNodeList( provider, node.nodes, source_ref ),
        source_ref = source_ref
    )

def buildDecoratorNodes( provider, node, source_ref ):
    if node.decorators is None:
        decorators = ()
    else:
        assert getKind( node.decorators ) == "Decorators"
        decorators = buildNodeList( provider, reversed( node.decorators.nodes ), source_ref )

    return decorators

def buildClassNode( provider, node, source_ref ):
    assert getKind( node ) == "Class"

    # Class decorators are new in Python 2.6, default to no decoration
    if not hasattr( node, "decorators" ):
        node.decorators = None

    decorators = buildDecoratorNodes( provider, node, source_ref )

    bases = []

    for base in node.bases:
        bases.append( buildNode( provider, base, source_ref ) )

    result = Nodes.CPythonClass(
        provider       = TransitiveProvider( provider ),
        name           = node.name,
        doc            = node.doc,
        bases          = bases,
        decorators     = decorators,
        source_ref     = source_ref
    )

    # Make sure class name is taken as a variable by the provider. Defining a classes
    # always assigns a variable of the same name to it.
    provider.getVariableForAssignment( node.name )

    _delayed_bodies.append( ( result, node.code, source_ref ) )

    return result


def buildParameterSpec( provider, node, source_ref ):
    kind = getKind( node )

    assert kind in ( "Function", "Lambda" ), "unsupported for kind " + kind
    argnames = node.argnames[:]

    if node.kwargs is not None:
        kwargs = argnames[-1]
        argnames = argnames[:-1]
    else:
        kwargs = None

    if node.varargs is not None:
        varargs = argnames[-1]
        argnames = argnames[:-1]
    else:
        varargs = None

    default_values = buildNodeList( provider, node.defaults, source_ref )

    return ParameterSpec(
        normal_args    = argnames,
        list_star_arg  = varargs,
        dict_star_arg  = kwargs,
        default_values = default_values
    )

def buildFunctionNode( provider, node, source_ref ):
    assert getKind( node ) == "Function"

    decorators = buildDecoratorNodes( provider, node, source_ref )

    result = Nodes.CPythonFunction(
        provider             = TransitiveProvider( provider ),
        name                 = node.name,
        doc                  = node.doc,
        parameters           = buildParameterSpec( provider, node, source_ref ),
        decorators           = decorators,
        source_ref           = source_ref
    )

    _delayed_bodies.append( ( result, node.code, source_ref ) )

    # Make sure the provider knows it has a variable of the functions name.
    _function_variable = provider.getVariableForAssignment( node.name )

    return result

def isSameListContent( a, b ):
    return list( sorted( a ) ) == list( sorted( b ) )

def buildLambdaNode( provider, node, source_ref ):
    result = Nodes.CPythonExpressionLambda(
        provider       = provider,
        parameters     = buildParameterSpec( provider, node, source_ref ),
        source_ref     = source_ref,
    )

    _delayed_bodies.append( ( result, node.code, source_ref ) )

    return result

def buildForLoopNode( provider, node, source_ref ):
    return Nodes.CPythonStatementForLoop(
        source     = buildNode( provider, node.list, source_ref ),
        target     = buildAssignTarget( provider, node.assign, source_ref ),
        body       = buildNode( provider, node.body, source_ref ),
        no_break   = buildNode( provider, node.else_, source_ref ) if node.else_ else None,
        source_ref = source_ref
    )

def buildWhileLoopNode( provider, node, source_ref ):
    return Nodes.CPythonStatementWhileLoop(
        condition  = buildNode( provider, node.test, source_ref ),
        body       = buildNode( provider, node.body, source_ref ),
        no_enter   = buildNode( provider, node.else_, source_ref ) if node.else_ is not None else None,
        source_ref = source_ref
    )


def buildFunctionCallNode( provider, node, source_ref ):
    positional_args = []
    named_args = []

    for arg in node.args:
        if getKind( arg ) == "Keyword":
            named_args.append( ( arg.name, buildNode( provider, arg.expr, source_ref ) ) )
        else:
            positional_args.append( buildNode( provider, arg, source_ref ) )

    return Nodes.CPythonExpressionFunctionCall(
        called_expression = buildNode( provider, node.node, source_ref ),
        positional_args   = positional_args,
        list_star_arg     = buildNode( provider, node.star_args, source_ref ) if node.star_args is not None else None,
        dict_star_arg     = buildNode( provider, node.dstar_args, source_ref ) if node.dstar_args is not None else None,
        named_args        = named_args,
        source_ref        = source_ref,
    )

def buildSequenceCreationNode( provider, node, source_ref ):
    elements = []

    for element_node in node.nodes:
        elements.append( buildNode( provider, element_node, source_ref ) )

    return Nodes.CPythonExpressionSequenceCreation(
        sequence_kind = getKind( node ).upper(),
        elements      = elements,
        source_ref    = source_ref
    )

def _areConstants( expressions ):
    for expression in expressions:
        if not expression.isConstantReference():
            return False
    else:
        return True

def buildDictionaryNode( provider, node, source_ref ):
    keys = []
    values = []

    constant = True
    constant_value = {}

    for item in node.items:
        key, value = item

        key_node = buildNode( provider, key, source_ref )
        value_node = buildNode( provider, value, source_ref )

        keys.append( key_node )
        values.append( value_node )

        constant = constant and key_node.isConstantReference()
        constant = constant and value_node.isConstantReference()

        if constant:
            constant_value[ key_node.getConstant() ] = value_node.getConstant()

    if False and constant:
        return Nodes.CPythonExpressionConstant(
            constant   = constant_value,
            source_ref = source_ref
        )
    else:
        return Nodes.CPythonExpressionDictionaryCreation(
            keys       = keys,
            values     = values,
            source_ref = source_ref
        )

def buildAssignTarget( provider, node, source_ref ):
    kind = getKind( node )

    if kind == "AssName":
        return Nodes.CPythonAssignTargetVariable( variable = provider.getVariableForAssignment( variable_name = node.name ), source_ref = source_ref )
    elif kind == "AssAttr":
        return Nodes.CPythonAssignAttribute( expression = buildNode( provider, node.expr, source_ref ), attribute = node.attrname, source_ref = source_ref )
    elif kind in ( "AssTuple", "AssList" ):
        elements = []

        for element in node.nodes:
            elements.append( buildAssignTarget( provider, element, source_ref ) )

        return Nodes.CPythonAssignTuple( elements = elements, source_ref = source_ref )
    elif kind == "Subscript":
        if len( node.subs ) == 1:
            return Nodes.CPythonAssignSubscript(
                expression = buildNode( provider, node.expr, source_ref ),
                subscript  = buildNode( provider, node.subs[0], source_ref ),
                source_ref = source_ref
            )
        else:
            return Nodes.CPythonAssignSubscript(
                expression = buildNode( provider, node.expr, source_ref ),
                subscript = Nodes.CPythonExpressionSequenceCreation(
                    sequence_kind  = "TUPLE",
                    elements       = buildNodeList( provider, node.subs, source_ref ),
                    source_ref     = source_ref
                ),
                source_ref = source_ref
            )
    elif kind == "Slice":
        lower = buildNode( provider, node.lower, source_ref ) if node.lower is not None else None
        upper = buildNode( provider, node.upper, source_ref ) if node.upper is not None else None

        return Nodes.CPythonAssignSlice(
            expression = buildNode( provider, node.expr, source_ref ),
            lower      = lower,
            upper      = upper,
            source_ref = source_ref
        )
    else:
        print source_ref
        print node
        print dir(node)

        assert False

def buildAssignNode( provider, node, source_ref ):
    assert len( node.nodes ) >= 1, source_ref

    targets = []

    # Evaluate the right hand side first, so it can get names provided
    # before the left hand side exists.
    expression = buildNode( provider, node.expr, source_ref )

    for target_node in node.nodes:
        targets.append( buildAssignTarget( provider, target_node, source_ref ) )

    return Nodes.CPythonStatementAssignment(
        targets    = targets,
        expression = expression,
        source_ref = source_ref
    )

def buildDelNode( provider, node, source_ref ):
    target = buildAssignTarget( provider, node, source_ref )

    return Nodes.CPythonStatementAssignment(
        targets    = ( target, ),
        expression = None,
        source_ref = source_ref
    )

def buildQuals( provider, result, quals, expected_kind, source_ref ):
    assert len( quals ) >= 1

    targets = []

    qual_conditions = []
    qual_sources = []

    for count, qual in enumerate( quals ):
        assert getKind( qual ) == expected_kind, source_ref

        target = buildAssignTarget( result, qual.assign, source_ref )
        targets.append( target )

        if qual.ifs:
            conditions = [ buildNode( provider = result, node = condition.test, source_ref = source_ref ) for condition in qual.ifs ]

            if len( conditions ) == 1:
                condition = conditions[ 0 ]
            else:
                condition = Nodes.CPythonExpressionAND( expressions = conditions, source_ref = source_ref )
        else:
            condition = None

        # Different for list contractions and generator expressions
        try:
            source = qual.list
        except AttributeError:
            source = qual.iter

        if count == 0:
            source_provider = provider
        else:
            source_provider = result

        qual_sources.append( buildNode( provider = source_provider, node = source, source_ref = source_ref ) )
        qual_conditions.append( condition )

    result.setTargets( targets )
    result.setSources( qual_sources )
    result.setConditions( qual_conditions )

def buildListContractionNode( provider, node, source_ref ):
    result = Nodes.CPythonExpressionListContraction(
        provider    = provider,
        source_ref  = source_ref
    )

    _delayed_bodies.append( ( result, node.expr, source_ref ) )

    buildQuals(
        provider      = provider,
        result        = result,
        quals         = node.quals,
        expected_kind = "ListCompFor",
        source_ref    = source_ref
    )

    return result

def buildGeneratorExpressionNode( provider, node, source_ref ):
    assert getKind( node.code ) == "GenExprInner"

    result = Nodes.CPythonGeneratorExpression(
        provider   = provider,
        source_ref = source_ref
    )

    _delayed_bodies.append( ( result, node.code.expr, source_ref ) )

    buildQuals(
        provider      = provider,
        result        = result,
        quals         = node.code.quals,
        expected_kind = "GenExprFor",
        source_ref    = source_ref
    )

    return result

def buildComparisonNode( provider, node, source_ref ):
    comparison = [ buildNode( provider, node.expr, source_ref ) ]

    for comparator, operand in node.ops:
        comparison.append( comparator )
        comparison.append( buildNode( provider, operand, source_ref ) )

    return Nodes.CPythonComparison(
        comparison = comparison,
        source_ref = source_ref
    )

def buildConditionNode( provider, node, source_ref ):
    conditions = []
    branches = []

    for test in node.tests:
        condition, branch = test

        conditions.append( buildNode( provider, condition, source_ref ) )
        branches.append( buildNode( provider, branch, source_ref ) )

    if node.else_ is not None:
        branches.append( buildNode( provider, node.else_, source_ref ) )

    return Nodes.CPythonStatementConditional(
        conditions = conditions,
        branches   = branches,
        source_ref = source_ref
    )

def buildTryExceptionNode( provider, node, source_ref ):
    catchers = []
    assigns = []
    catcheds = []

    for handler in node.handlers:
        exception_expression, exception_assign, exception_block = handler

        catchers.append( buildNode( provider, exception_expression, source_ref ) if exception_expression is not None else None )
        assigns.append( buildAssignTarget( provider, exception_assign, source_ref ) if exception_assign is not None else None )

        catcheds.append( buildNode( provider, exception_block, source_ref ) )

    return Nodes.CPythonStatementTryExcept(
        tried      = buildNode( provider, node.body, source_ref ),
        catchers   = catchers,
        assigns    = assigns,
        catcheds   = catcheds,
        no_raise   = buildNode( provider, node.else_, source_ref ) if node.else_ else None,
        source_ref = source_ref
    )

def buildTryFinallyNode( provider, node, source_ref ):
    if getKind( node.body ) == "Stmt":
        tried = buildNode( provider, node.body, source_ref )
    else:
        tried = Nodes.CPythonStatementSequence(
            statements = [ buildNode( provider, node.body, source_ref ) ],
            source_ref = source_ref
        )

    return Nodes.CPythonStatementTryFinally(
        tried      = tried,
        final      = buildNode( provider, node.final, source_ref ),
        source_ref = source_ref
    )

def buildRaiseNode( provider, node, source_ref ):
    return Nodes.CPythonStatementRaiseException(
        exception_type  = buildNode( provider, node.expr1, source_ref ) if node.expr1 is not None else None,
        exception_value = buildNode( provider, node.expr2, source_ref ) if node.expr2 is not None else None,
        exception_trace = buildNode( provider, node.expr3, source_ref ) if node.expr3 is not None else None,
        source_ref      = source_ref
    )

def buildAssertNode( provider, node, source_ref ):
    return Nodes.CPythonStatementAssert(
        expression = buildNode( provider, node.test, source_ref ),
        failure    = buildNode( provider, node.fail, source_ref ) if node.fail is not None else None,
        source_ref = source_ref
    )


def buildSubscriptNode( provider, node, source_ref ):
    assert node.flags == "OP_APPLY", source_ref

    if len( node.subs ) == 1:
        subscript = buildNode( provider, node.subs[0], source_ref )
    else:
        subscript = Nodes.CPythonExpressionSequenceCreation(
            sequence_kind  = "TUPLE",
            elements       = buildNodeList( provider, node.subs, source_ref ),
            source_ref     = source_ref
        )

    return Nodes.CPythonExpressionSubscriptionLookup(
        expression = buildNode( provider, node.expr, source_ref ),
        subscript  = subscript,
        source_ref = source_ref
    )

def buildSliceNode( provider, node, source_ref ):

    lower = buildNode( provider, node.lower, source_ref ) if node.lower is not None else None
    upper = buildNode( provider, node.upper, source_ref ) if node.upper is not None else None

    if node.flags == "OP_APPLY":
        return Nodes.CPythonExpressionSlice(
            expression = buildNode( provider, node.expr, source_ref ),
            lower      = lower,
            upper      = upper,
            source_ref = source_ref
        )
    else:
        raise Exception( "unsupported slice flags", node.flags, source_ref )

def buildSliceObjectNode( provider, node, source_ref ):
    assert len( node.nodes ) == 3

    return Nodes.CPythonExpressionSliceObject(
        lower      = buildNode( node = node.nodes[0], provider = provider, source_ref = source_ref ),
        upper      = buildNode( node = node.nodes[1], provider = provider, source_ref = source_ref ),
        step       = buildNode( node = node.nodes[2], provider = provider, source_ref = source_ref ),
        source_ref = source_ref
    )

def _findModule( module_name ):
    # The os.path is strangely hacked into the os module, dispatching per platform, We either
    # cannot look into it, or we require to be on the target platform. Non Linux is unusually
    # enough, cross platform compile, I give up on.
    if module_name == "os.path":
        module_name = os.path.basename( os.path.__file__ ).replace( ".pyc", "" )

    dot_pos = module_name.rfind( "." )

    if dot_pos == -1:
        module_fh, module_filename, module_desc = imp.find_module( module_name )
    else:
        parent_module_name = module_name[:dot_pos]
        child_module_name = module_name[dot_pos+1:]

        P = imp.find_module( parent_module_name )

        parent_module_filename = _findModule( parent_module_name )[1]
        module_fh, module_filename, module_desc = imp.find_module( child_module_name, [ P[1] ] )

    if module_filename == "":
        module_filename = None

    return module_fh, module_filename, module_desc

def _isWhiteListedNotExistingModule( module_name ):
    return module_name in ( "mac", "nt", "os2", "_emx_link", "riscos", "ce", "riscospath", "riscosenviron", "Carbon.File", "org.python.core", "_sha", "_sha256", "_sha512", "_md5", "_subprocess", "msvcrt" )

def buildImportModulesNode( provider, node, source_ref ):
    imports = []

    for import_desc in node.names:
        module_name, local_name = import_desc

        variable = provider.getVariableForAssignment( local_name if local_name is not None else module_name.split(".")[0] )

        import_name = module_name.split(".")[0] if not local_name else module_name

        if Options.shallFollowImports():
            try:
                _module_fh, module_filename, _module_desc = _findModule( module_name )
            except ImportError:
                if not _isWhiteListedNotExistingModule( module_name ):
                    print "Warning, cannot find", module_name

                module_filename = None
        else:
            module_filename = None

        imports.append( ( module_name, import_name, variable, module_filename ) )

    return Nodes.CPythonStatementImportModules(
        imports     = imports,
        source_ref  = source_ref
    )

def buildImportFromNode( provider, node, source_ref ):
#    assert node.level == 0, source_ref

    module_name = node.modname

    imports = []

    for import_desc in node.names:
        object_name, local_name = import_desc

        imports.append( ( object_name, local_name if local_name is not None else object_name ) )

    if Options.shallFollowImports():
        try:
            _module_fh, module_filename, _module_desc = _findModule( module_name )
        except ImportError:
            if not _isWhiteListedNotExistingModule( module_name ):
                print "Warning, cannot find", module_name

            module_filename = None
    else:
        module_filename = None


    return Nodes.CPythonStatementImportFrom(
        provider        = provider,
        module_name     = module_name,
        module_filename = module_filename,
        imports         = imports,
        source_ref      = source_ref
    )


def buildPrintNode( provider, node, source_ref ):
    values = []

    for print_arg in node.nodes:
        values.append( buildNode( provider, print_arg, source_ref ) )

    return Nodes.CPythonStatementPrint(
        newline    = getKind( node ) == "Printnl",
        dest       = buildNode( provider, node.dest, source_ref ) if node.dest is not None else None,
        values     = values,
        source_ref = source_ref
    )

def buildExecNode( provider, node, source_ref ):
    # TODO: Find out if this a CPython bug, globals and locals need to be swapped and appear
    # to be wrong in the AST node already.
    expr, locals, globals = node.expr, node.globals, node.locals

    if getKind( expr ) == "Tuple":
        assert locals is None and globals is None

        nodes = expr.nodes

        expr = nodes[0]
        globals = nodes[1] if len(nodes) > 1 else None
        locals = nodes[2] if len(nodes) > 2 else None

    globals = buildNode( provider, globals, source_ref ) if globals is not None else None
    locals = buildNode( provider, locals, source_ref ) if locals is not None else None

    return Nodes.CPythonStatementExec(
        source      = buildNode( provider, expr, source_ref ),
        globals     = globals,
        locals      = locals,
        source_ref  = source_ref
    )

def buildWithNode( provider, node, source_ref ):
    return Nodes.CPythonStatementWith(
        source     = buildNode( provider, node.expr, source_ref ),
        target     = buildAssignTarget( provider, node.vars, source_ref ) if node.vars else None,
        body       = buildNode( provider, node.body, source_ref ),
        source_ref = source_ref
    )

def buildNodeList( provider, nodes, source_ref ):
    if nodes is not None:
        return [ buildNode( provider, node, source_ref.atLineNumber( node.lineno ) ) for node in nodes ]
    else:
        return []

def buildGlobalDeclarationNode( provider, node, source_ref ):
    for variable_name in node.names:
        variable = provider.getParentModule().createProvidedVariable( variable_name = variable_name )

        # Big friendship with closure taker here. Something that takes module variables has that
        # self.taken from being a CPythonClosureTaker, could be an interface of it too.
        provider.taken.add( variable )

    return Nodes.CPythonDeclareGlobal(
        variables  = node.names,
        source_ref = source_ref
    )

class TransitiveProvider:
    def __init__( self, provider ):
        if provider.isClassReference():
            self.effective_provider  = TransitiveProvider( provider.provider )
            self.transient = True
        else:
            self.effective_provider = provider
            self.transient = False

        self.original_provider = provider

    def getName( self ):
        return self.original_provider.getName()

    def getFilename( self ):
        return self.original_provider.getFilename()

    def getVariableForAssignment( self, variable_name ):
        return self.original_provider.getVariableForAssignment( variable_name )

    def getVariableForReference( self, variable_name ):
        if self.transient:
            result = self.original_provider.getClosureVariable( variable_name )
        else:
            result = self.effective_provider.getVariableForReference( variable_name )

        return result

    def isClassReference( self ):
        return self.effective_provider.isClassReference()

    def isModule( self ):
        return self.effective_provider.isModule()

    def createProvidedVariable( self, variable_name ):
        return self.effective_provider.createProvidedVariable( variable_name = variable_name )

def buildNode( provider, node, source_ref ):
    kind = getKind( node )

    source_ref = source_ref.atLineNumber( node.lineno if node.lineno is not None else 1 )

    if kind == "Stmt":
        result = buildStatementsNode( provider, node, source_ref )
    elif kind == "Assign":
        result = buildAssignNode( provider, node, source_ref )
    elif kind in ( "AssName", "AssTuple", "AssAttr" ) or ( kind in ( "Subscript", "Slice" ) and node.flags == "OP_DELETE" ):
        result = buildDelNode( provider, node, source_ref )
    elif kind == "Const":
        result = Nodes.CPythonExpressionConstant(
            constant   = node.value,
            source_ref = source_ref
        )
    elif kind == "Name":
        result = Nodes.CPythonExpressionVariable(
            variable   = provider.getVariableForReference( node.name ),
            source_ref = source_ref
        )
    elif kind == "Subscript":
        result = buildSubscriptNode( provider, node, source_ref )
    elif kind == "Slice":
        result = buildSliceNode( provider, node, source_ref )
    elif kind == "Sliceobj":
        result = buildSliceObjectNode( provider, node, source_ref )
    elif kind == "Class":
        result = buildClassNode( provider, node, source_ref )
    elif kind == "Function":
        result = buildFunctionNode( provider, node, source_ref )
    elif kind == "Lambda":
        result = buildLambdaNode( provider, node, source_ref )
    elif kind == "GenExpr":
        result = buildGeneratorExpressionNode( provider, node, source_ref )
    elif kind == "Return":
        result = Nodes.CPythonStatementReturn(
            expression = buildNode( provider, node.value, source_ref ),
            source_ref = source_ref
        )
    elif kind == "Yield":
        result = Nodes.CPythonStatementYield(
            expression = buildNode( provider, node.value, source_ref ),
            source_ref = source_ref
        )

        provider.markAsGenerator()
    elif kind == "For":
        result = buildForLoopNode( provider, node, source_ref )
    elif kind == "While":
        result = buildWhileLoopNode( provider, node, source_ref )
    elif kind == "Continue":
        result = Nodes.CPythonStatementContinueLoop(
            source_ref = source_ref
        )
    elif kind == "Break":
        result = Nodes.CPythonStatementBreakLoop(
            source_ref = source_ref
        )
    elif kind in ( "Printnl", "Print" ):
        result = buildPrintNode( provider, node, source_ref )
    elif kind == "CallFunc":
        result = buildFunctionCallNode( provider, node, source_ref )
    elif kind == "ListComp":
        result = buildListContractionNode( provider, node, source_ref )
    elif kind in ( "List", "Tuple" ):
        result = buildSequenceCreationNode( provider, node, source_ref )
    elif kind == "Dict":
        result = buildDictionaryNode( provider, node, source_ref )
    elif kind == "Discard":
        # Although the Python doc calls it a statement, you can write "a = yield value" and expect it to work. The tree
        # we are visiting represents that by discarding the value that yield produced (None normally). We allow yield to
        # be a real statement to us. Another hack would be needed to assignments to use None to handle the syntax fully,
        # but for the time being this is not even a plan to add.

        if getKind( node.expr ) != "Yield":
            result = Nodes.CPythonStatementExpressionOnly(
                expression = buildNode( provider, node.expr, source_ref ),
                source_ref = source_ref
            )
        else:
            result = buildNode( provider, node.expr, source_ref )
    elif kind == "Getattr":
        result = Nodes.CPythonExpressionAttributeLookup(
            expression = buildNode( provider, node.expr, source_ref ),
            attribute  = node.attrname,
            source_ref = source_ref
        )
    elif kind in PythonOperators.multiple_arg_operators:
        result = Nodes.CPythonExpressionMultiArgOperation(
            operator   = PythonOperators.multiple_arg_operators[ kind ],
            operands   = buildNodeList( provider, node.nodes, source_ref ),
            source_ref = source_ref
        )
    elif kind in PythonOperators.binary_operators:
        result = Nodes.CPythonExpressionBinaryOperation(
            operator   = PythonOperators.binary_operators[ kind ],
            left       = buildNode( provider, node.left, source_ref ),
            right      = buildNode( provider, node.right, source_ref ),
            source_ref = source_ref
        )
    elif kind in PythonOperators.unary_operators:
        result = Nodes.CPythonExpressionUnaryOperation(
            operator   = PythonOperators.unary_operators[ kind ],
            operand    = buildNode( provider, node.expr, source_ref ),
            source_ref = source_ref
        )
    elif kind == "AugAssign":
        result = Nodes.CPythonStatementAssignmentInplace(
            operator   = node.op,
            target     = buildNode( provider, node.node, source_ref ),
            expression = buildNode( provider, node.expr, source_ref ),
            source_ref = source_ref
        )
    elif kind == "Compare":
        result = buildComparisonNode( provider, node, source_ref )
    elif kind == "Global":
        result = buildGlobalDeclarationNode( provider, node, source_ref )
    elif kind == "IfExp":
        result = Nodes.CPythonExpressionConditional(
            condition      = buildNode( provider, node.test, source_ref ),
            yes_expression = buildNode( provider, node.then, source_ref ),
            no_expression  = buildNode( provider, node.else_, source_ref ),
            source_ref     = source_ref
        )
    elif kind == "If":
        result = buildConditionNode( provider, node, source_ref )
    elif kind == "Or":
        result = Nodes.CPythonExpressionOR(
            expressions = [ buildNode( provider, expression, source_ref ) for expression in node.nodes ],
            source_ref  = source_ref
        )
    elif kind == "And":
        result = Nodes.CPythonExpressionAND(
            expressions = [ buildNode( provider, expression, source_ref ) for expression in node.nodes ],
            source_ref  = source_ref
        )
    elif kind == "Not":
        result = Nodes.CPythonExpressionNOT(
            expression = buildNode( provider, node.expr, source_ref ),
            source_ref = source_ref
        )
    elif kind == "TryExcept":
        result = buildTryExceptionNode(
            provider   = provider,
            node       = node,
            source_ref = source_ref
        )
    elif kind == "TryFinally":
        result = buildTryFinallyNode(
            provider   = provider,
            node       = node,
            source_ref = source_ref
        )
    elif kind == "Pass":
        result = Nodes.CPythonStatementPass(
            source_ref = source_ref
        )
    elif kind == "Import":
        result = buildImportModulesNode(
            provider   = provider,
            node       = node,
            source_ref = source_ref
        )
    elif kind ==  "From":
        result = buildImportFromNode(
            provider   = provider,
            node       = node,
            source_ref = source_ref
        )
    elif kind == "Raise":
        result = buildRaiseNode(
            provider   = provider,
            node       = node,
            source_ref = source_ref
        )
    elif kind == "Assert":
        result = buildAssertNode(
            provider   = provider,
            node       = node,
            source_ref = source_ref
        )
    elif kind == "Exec":
        result = buildExecNode(
            provider   = provider,
            node       = node,
            source_ref = source_ref
        )
    elif kind == "With":
        result = buildWithNode(
            provider   = provider,
            node       = node,
            source_ref = source_ref
        )
    else:
        print source_ref
        print node
        print dir( node )

        assert False

    assert isinstance( result, Nodes.CPythonNode )

    return result

class TreeVisitorAssignParent:
    def __call__( self, node ):
        for child in node.getVisitableNodes():
            if child is None:
                raise AssertionError( "none child encountered", node, node.source_ref )

            child.parent = node

            # print node, "<-", child

class ModuleRecursionVisitor:
    imported_modules = {}

    def __init__( self, module, module_filename, stdlib ):
        self.imported_modules[ module_filename ] = module
        self.stdlib = stdlib

    def __call__( self, node ):
        if node.isStatementImport() or node.isStatementImportFrom():
            for module_filename in node.getModuleFilenames():
                if self.stdlib or not module_filename.startswith( "/usr/lib/python" ):
                    if module_filename.endswith( ".py" ):
                        if module_filename not in self.imported_modules:
                            print "Recurse to", module_filename

                            imported_module = buildModuleTree( module_filename )

                            self.imported_modules[ module_filename ] = buildModuleTree( module_filename )

def getOtherModules():
    return ModuleRecursionVisitor.imported_modules.values()

def visitTree( tree, visitor ):
    visitor( tree )

    for visitable in tree.getVisitableNodes():
        visitTree( visitable, visitor )

_delayed_bodies = []


import os

def assignParent( tree ):
    visitTree( tree, TreeVisitorAssignParent() )

def buildModuleTree( filename ):
    module = compiler.parseFile( filename )

    source_ref = SourceCodeReference.fromFilename( filename )

    # I prefer to be text based instead of checking against compiler.ast classes, because it will
    # be more Py3k conform potentially with its different method to get at this.

    assert getKind( module ) == "Module"

    result = Nodes.CPythonModule(
        name       = os.path.basename( filename ).replace( ".py", "" ),
        filename   = os.path.abspath( filename ),
        doc        = module.doc,
        source_ref = source_ref,
    )

    global _delayed_bodies

    _delayed_bodies = []

    body = buildNode(
        provider   = result,
        node       = module.node,
        source_ref = source_ref
    )

    result.setBody( body )

    while _delayed_bodies:
        delayed_body = _delayed_bodies.pop()

        structure, code, source_ref = delayed_body

        structure.setBody(
            buildNode(
                provider   = structure,
                node       = code,
                source_ref = source_ref,
            )
        )

    assignParent( result )

    if Options.shallFollowImports():
        visitTree( result, ModuleRecursionVisitor( result, filename, Options.includeStandardLibrary() ) )

    # Some things that the compiler can or should always do.
    # 1. Replace calls to locals, globals or eval with our own variants, because these
    # will refuse to work (exe case) or give incorrect results (module case).
    TreeTransforming.replaceBuiltinsCallsThatRequireInterpreter( result )

    return result
