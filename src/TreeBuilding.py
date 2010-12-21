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
""" Build the internal node tree from source code.

Does all the Python parsing and puts it into a tree structure for use in
later stages of the compiler.

"""

from __future__ import print_function
from __past__ import long, unicode

import SourceCodeReferences
import TreeTransforming
import PythonOperators
import TreeOperations
import Importing
import Options

import Nodes

from nodes.ParameterSpec import ParameterSpec
from nodes.ImportSpec import ImportSpec

import ast, imp, sys

from logging import warning

def getPythonVersion():
    big, major, minor = sys.version_info[0:3]

    return big * 100 + major * 10 + minor

_future_stack = []

_future_division = None
_unicode_literals = None
_absolute_import = None
_future_print = None

def initFuture():
    global _future_division, _unicode_literals, _absolute_import, _future_print

    _future_division   = getPythonVersion() >= 300
    _unicode_literals  = getPythonVersion() >= 300
    _absolute_import   = getPythonVersion() >= 270
    _future_print      = getPythonVersion() >= 300

def pushFuture():
    _future_stack.append( ( _future_division, _unicode_literals, _absolute_import, _future_print ) )

def popFuture():
    global _future_division, _unicode_literals, _absolute_import, _future_print

    _future_division, _unicode_literals, _absolute_import, _future_print = _future_stack.pop()

def getFuture():
    return _future_division, _unicode_literals, _absolute_import, _future_print

def dump( node ):
    print( ast.dump( node ) )

def getKind( node ):
    return node.__class__.__name__.split( "." )[-1]

_delayed_works = []

def pushDelayedWork( delayed_work ):
    global _delayed_works

    _delayed_works.append( delayed_work )

def buildStatementsNode( provider, nodes, source_ref ):
    return Nodes.CPythonStatementSequence(
        statements  = buildNodeList( provider, nodes, source_ref ),
        replacement = False,
        source_ref  = source_ref
    )

def buildReplacementStatementsNode( provider, nodes, source_ref ):
    return Nodes.CPythonStatementSequence(
        statements  = buildNodeList( provider, nodes, source_ref ),
        replacement = True,
        source_ref  = source_ref
    )

def buildDecoratorNodes( provider, nodes, source_ref ):
    return buildNodeList( provider, reversed( nodes ), source_ref )

def buildClassNode( provider, node, source_ref ):
    assert getKind( node ) == "ClassDef"

    class_body, class_doc = extractDocFromBody( node )

    decorators = buildDecoratorNodes( provider, node.decorator_list, source_ref )

    bases = buildNodeList( provider, node.bases, source_ref )

    result = Nodes.CPythonClass(
        provider       = TransitiveProvider( provider ),
        variable       = provider.getVariableForAssignment( node.name ),
        name           = node.name,
        doc            = class_doc,
        bases          = bases,
        decorators     = decorators,
        source_ref     = source_ref
    )

    def delayedWork():
        body = buildStatementsNode(
            provider   = result,
            nodes      = class_body,
            source_ref = source_ref,
        )

        result.setBody( body )


    pushDelayedWork( delayedWork )

    return result


def buildParameterSpec( provider, node, source_ref ):
    kind = getKind( node )

    assert kind in ( "FunctionDef", "Lambda" ), "unsupported for kind " + kind

    def extractArg( arg ):
        if getKind( arg ) == "Name":
            return arg.id
        elif getKind( arg ) == "arg":
            assert arg.annotation is None

            return arg.arg
        elif getKind( arg ) == "Tuple":
            return tuple( [ extractArg( arg ) for arg in arg.elts ] )
        else:
            assert False, getKind( arg )

    argnames = [ extractArg( arg ) for arg in node.args.args ]

    kwargs = node.args.kwarg
    varargs = node.args.vararg

    default_values = buildNodeList( provider, node.args.defaults, source_ref )

    return ParameterSpec(
        normal_args    = argnames,
        list_star_arg  = varargs,
        dict_star_arg  = kwargs,
        default_values = default_values
    )

def buildFunctionNode( provider, node, source_ref ):
    assert getKind( node ) == "FunctionDef"

    body, function_doc = extractDocFromBody( node )

    decorators = buildDecoratorNodes( provider, node.decorator_list, source_ref )

    result = Nodes.CPythonFunction(
        provider   = TransitiveProvider( provider ),
        variable   = provider.getVariableForAssignment( node.name ),
        parameters = buildParameterSpec( provider, node, source_ref ),
        name       = node.name,
        doc        = function_doc,
        decorators = decorators,
        source_ref = source_ref
    )

    def delayedWork():
        body = buildStatementsNode(
            provider   = result,
            nodes      = node.body,
            source_ref = source_ref,
        )

        result.setBody( body )

    pushDelayedWork( delayedWork )

    return result

def isSameListContent( a, b ):
    return list( sorted( a ) ) == list( sorted( b ) )

def buildLambdaNode( provider, node, source_ref ):
    result = Nodes.CPythonExpressionLambda(
        provider   = provider,
        parameters = buildParameterSpec( provider, node, source_ref ),
        source_ref = source_ref,
    )

    def delayedWork():
        body = buildNode(
            provider   = result,
            node       = node.body,
            source_ref = source_ref,
        )

        result.setBody( body )


    pushDelayedWork( delayedWork )

    return result

def buildForLoopNode( provider, node, source_ref ):
    return Nodes.CPythonStatementForLoop(
        source     = buildNode( provider, node.iter, source_ref ),
        target     = buildAssignTarget( provider, node.target, source_ref ),
        body       = buildStatementsNode( provider, node.body, source_ref ),
        no_break   = buildStatementsNode( provider, node.orelse, source_ref ) if node.orelse else None,
        source_ref = source_ref
    )

def buildWhileLoopNode( provider, node, source_ref ):
    return Nodes.CPythonStatementWhileLoop(
        condition  = buildNode( provider, node.test, source_ref ),
        body       = buildStatementsNode( provider, node.body, source_ref ),
        no_enter   = buildStatementsNode( provider, node.orelse, source_ref ) if node.orelse is not None else None,
        source_ref = source_ref
    )


def buildFunctionCallNode( provider, node, source_ref ):
    positional_args = buildNodeList( provider, node.args, source_ref )

    named_args = []

    for keyword in node.keywords:
        named_args.append( ( keyword.arg, buildNode( provider, keyword.value, source_ref ) ) )

    return Nodes.CPythonExpressionFunctionCall(
        called_expression = buildNode( provider, node.func, source_ref ),
        positional_args   = positional_args,
        list_star_arg     = buildNode( provider, node.starargs, source_ref ) if node.starargs is not None else None,
        dict_star_arg     = buildNode( provider, node.kwargs, source_ref ) if node.kwargs is not None else None,
        named_args        = named_args,
        source_ref        = source_ref,
    )

def buildSequenceCreationNode( provider, node, source_ref ):
    elements = buildNodeList( provider, node.elts, source_ref )

    for element in elements:
        # TODO: The handling of mutable should be solved already.
        if not element.isConstantReference() or element.isMutable():
            constant = False
            break
    else:
        constant = True

    sequence_kind = getKind( node ).upper()

    if constant:
        const_type = tuple if sequence_kind == "TUPLE" else list

        return Nodes.CPythonExpressionConstant(
            constant   = const_type( element.getConstant() for element in elements ),
            source_ref = source_ref
        )
    else:
        return Nodes.CPythonExpressionSequenceCreation(
            sequence_kind = sequence_kind,
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

    for key, value in zip( node.keys, node.values ):
        key_node = buildNode( provider, key, source_ref )
        value_node = buildNode( provider, value, source_ref )

        keys.append( key_node )
        values.append( value_node )

        constant = constant and key_node.isConstantReference()
        constant = constant and value_node.isConstantReference() and not value_node.isMutable()

    if constant:
        constant_value = dict.fromkeys( [ key.getConstant() for key in keys ], None )

        for count, key in enumerate( keys ):
            constant_value[ key.getConstant() ] = values[ count ].getConstant()

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

def buildSetNode( provider, node, source_ref ):
    values = buildNodeList( provider, node.elts, source_ref )

    constant = True

    for value in values:
        if not value.isConstantReference():
            constant = False
            break

    if constant:
        constant_value = frozenset( value.getConstant() for value in values )

        return Nodes.CPythonExpressionConstant(
            constant   = constant_value,
            source_ref = source_ref
        )
    else:
        return Nodes.CPythonExpressionSetCreation(
            values     = values,
            source_ref = source_ref
        )

def buildAssignTarget( provider, node, source_ref ):
    if hasattr( node, "ctx" ):
        assert getKind( node.ctx ) in ( "Store", "Del" )

    kind = getKind( node )

    if type( node ) is str:
        # Python >= 3.1 only
        return Nodes.CPythonAssignTargetVariable( variable = provider.getVariableForAssignment( variable_name = node ), source_ref = source_ref )
    elif kind == "Name":
        return Nodes.CPythonAssignTargetVariable( variable = provider.getVariableForAssignment( variable_name = node.id ), source_ref = source_ref )
    elif kind == "Attribute":
        return Nodes.CPythonAssignAttribute( expression = buildNode( provider, node.value, source_ref ), attribute = node.attr, source_ref = source_ref )
    elif kind in ( "Tuple", "List" ):
        elements = []

        for element in node.elts:
            elements.append( buildAssignTarget( provider, element, source_ref ) )

        return Nodes.CPythonAssignTuple( elements = elements, source_ref = source_ref )
    elif kind == "Subscript":
        slice_kind = getKind( node.slice )

        if slice_kind == "Index":
            return Nodes.CPythonAssignSubscript(
                expression = buildNode( provider, node.value, source_ref ),
                subscript  = buildNode( provider, node.slice.value, source_ref ),
                source_ref = source_ref
            )
        elif slice_kind == "Slice":
            lower = buildNode( provider, node.slice.lower, source_ref ) if node.slice.lower is not None else None
            upper = buildNode( provider, node.slice.upper, source_ref ) if node.slice.upper is not None else None

            if node.slice.step is not None:
                step = buildNode( provider, node.slice.step,  source_ref )

                return Nodes.CPythonAssignSubscript(
                    expression = buildNode( provider, node.value, source_ref ),
                    subscript  = Nodes.CPythonExpressionSliceObject(
                        lower      = lower,
                        upper      = upper,
                        step       = step,
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                )
            else:
                return Nodes.CPythonAssignSlice(
                    expression = buildNode( provider, node.value, source_ref ),
                    lower      = lower,
                    upper      = upper,
                    source_ref = source_ref
                )
        elif slice_kind == "ExtSlice":
            return Nodes.CPythonAssignSubscript(
                expression = buildNode( provider, node.value, source_ref ),
                subscript  = _buildExtSliceNode( provider, node, source_ref ),
                source_ref = source_ref
            )
        elif slice_kind == "Ellipsis":
            return Nodes.CPythonAssignSubscript(
                expression = buildNode( provider, node.value, source_ref ),
                subscript  = Nodes.CPythonExpressionConstant(
                    constant   = Ellipsis,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        else:
            assert False, node.slice
    else:
        assert False, ( source_ref, ast.dump( node ) )

def buildAssignNode( provider, node, source_ref ):
    assert len( node.targets ) >= 1, source_ref

    # Evaluate the right hand side first, so it can get names provided
    # before the left hand side exists.
    expression = buildNode( provider, node.value, source_ref )

    targets = []
    for target_node in node.targets:
        targets.append( buildAssignTarget( provider, target_node, source_ref ) )

    return Nodes.CPythonStatementAssignment(
        targets    = targets,
        expression = expression,
        source_ref = source_ref
    )

def buildDeleteNode( provider, node, source_ref ):
    targets = [ buildAssignTarget( provider, target, source_ref ) for target in node.targets ]

    return Nodes.CPythonStatementAssignment(
        targets    = targets,
        expression = None,
        source_ref = source_ref
    )

def buildDelNode( provider, node, source_ref ):
    target = buildAssignTarget( provider, node, source_ref )

    return Nodes.CPythonStatementAssignment(
        targets    = ( target, ),
        expression = None,
        source_ref = source_ref
    )

def buildQuals( provider, result, quals, source_ref ):
    assert len( quals ) >= 1

    targets = []

    qual_conditions = []
    qual_sources = []

    for count, qual in enumerate( quals ):
        assert getKind( qual ) == "comprehension"

        target = buildAssignTarget( result, qual.target, source_ref )
        targets.append( target )

        if qual.ifs:
            conditions = [ buildNode( provider = result, node = condition, source_ref = source_ref ) for condition in qual.ifs ]

            if len( conditions ) == 1:
                condition = conditions[ 0 ]
            else:
                condition = Nodes.CPythonExpressionAND( expressions = conditions, source_ref = source_ref )
        else:
            condition = Nodes.CPythonExpressionConstant( constant = True, source_ref = source_ref )

        # Different for list contractions and generator expressions
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
        provider   = provider,
        source_ref = source_ref
    )

    buildQuals(
        provider   = provider,
        result     = result,
        quals      = node.generators,
        source_ref = source_ref
    )

    def delayedWork():
        body = buildNode(
            provider   = result,
            node       = node.elt,
            source_ref = source_ref,
        )

        result.setBody( body )

    pushDelayedWork( delayedWork )

    return result

def buildSetContractionNode( provider, node, source_ref ):
    result = Nodes.CPythonExpressionSetContraction(
        provider   = provider,
        source_ref = source_ref
    )

    buildQuals(
        provider   = provider,
        result     = result,
        quals      = node.generators,
        source_ref = source_ref
    )

    def delayedWork():
        body = buildNode(
            provider   = result,
            node       = node.elt,
            source_ref = source_ref,
        )

        result.setBody( body )

    pushDelayedWork( delayedWork )

    return result

def buildDictContractionNode( provider, node, source_ref ):
    result = Nodes.CPythonExpressionDictContraction(
        provider   = provider,
        source_ref = source_ref
    )

    buildQuals(
        provider   = provider,
        result     = result,
        quals      = node.generators,
        source_ref = source_ref
    )

    def delayedWork():
        key_node = buildNode(
            provider   = result,
            node       = node.key,
            source_ref = source_ref,
        )

        value_node = buildNode(
            provider   = result,
            node       = node.value,
            source_ref = source_ref,
        )

        result.setBody(
            Nodes.CPythonExpressionDictContractionKeyValue(
                provider   = result,
                key        = key_node,
                value      = value_node,
                source_ref = source_ref
            )
        )

    pushDelayedWork( delayedWork )

    return result

def buildGeneratorExpressionNode( provider, node, source_ref ):
    assert getKind( node ) == "GeneratorExp"

    result = Nodes.CPythonGeneratorExpression(
        provider   = provider,
        source_ref = source_ref
    )

    buildQuals(
        provider      = provider,
        result        = result,
        quals         = node.generators,
        source_ref    = source_ref
    )

    def delayedWork():
        body = buildNode(
            provider   = result,
            node       = node.elt,
            source_ref = source_ref,
        )

        result.setBody( body )


    pushDelayedWork( delayedWork )

    return result

def buildComparisonNode( provider, node, source_ref ):
    comparison = [ buildNode( provider, node.left, source_ref ) ]

    assert len( node.comparators ) == len( node.ops )

    for comparator, operand in zip( node.ops, node.comparators ):
        comparison.append( getKind( comparator ) )
        comparison.append( buildNode( provider, operand, source_ref ) )

    return Nodes.CPythonComparison(
        comparison = comparison,
        source_ref = source_ref
    )

def buildConditionNode( provider, node, source_ref ):
    conditions = []
    branches = []

    conditions.append( buildNode( provider, node.test, source_ref ) )
    branches.append( buildStatementsNode( provider, node.body, source_ref ) )

    if node.orelse is not None:
        branches.append( buildStatementsNode( provider, node.orelse, source_ref ) )

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
        exception_expression, exception_assign, exception_block = handler.type, handler.name, handler.body

        catchers.append( buildNode( provider, exception_expression, source_ref ) if exception_expression is not None else None )
        assigns.append( buildAssignTarget( provider, exception_assign, source_ref ) if exception_assign is not None else None )

        catcheds.append( buildStatementsNode( provider, exception_block, source_ref ) )

    return Nodes.CPythonStatementTryExcept(
        tried      = buildStatementsNode( provider, node.body, source_ref ),
        catchers   = catchers,
        assigns    = assigns,
        catcheds   = catcheds,
        no_raise   = buildStatementsNode( provider, node.orelse, source_ref ) if node.orelse else None,
        source_ref = source_ref
    )

def buildTryFinallyNode( provider, node, source_ref ):
    return Nodes.CPythonStatementTryFinally(
        tried      = buildStatementsNode( provider, node.body, source_ref ),
        final      = buildStatementsNode( provider, node.finalbody, source_ref ),
        source_ref = source_ref
    )

def buildRaiseNode( provider, node, source_ref ):
    return Nodes.CPythonStatementRaiseException(
        exception_type  = buildNode( provider, node.type, source_ref ) if node.type is not None else None,
        exception_value = buildNode( provider, node.inst, source_ref ) if node.inst is not None else None,
        exception_trace = buildNode( provider, node.tback, source_ref ) if node.tback is not None else None,
        source_ref      = source_ref
    )

def buildAssertNode( provider, node, source_ref ):
    return Nodes.CPythonStatementAssert(
        expression = buildNode( provider, node.test, source_ref ),
        failure    = buildNode( provider, node.msg, source_ref ) if node.msg is not None else None,
        source_ref = source_ref
    )


def _buildExtSliceNode( provider, node, source_ref ):
    elements = []

    for dim in node.slice.dims:
        dim_kind = getKind( dim )

        if dim_kind == "Slice":
            lower = buildNode( provider, dim.lower, source_ref ) if dim.lower is not None else None
            upper = buildNode( provider, dim.upper, source_ref ) if dim.upper is not None else None
            step = buildNode( provider, dim.step,  source_ref ) if dim.step is not None else None

            element = Nodes.CPythonExpressionSliceObject(
                lower      = lower,
                upper      = upper,
                step       = step,
                source_ref = source_ref
            )
        elif dim_kind == "Ellipsis":
            element = Nodes.CPythonExpressionConstant(
                constant   = Ellipsis,
                source_ref = source_ref
            )
        elif dim_kind == "Index":
            element = buildNode(
                provider   = provider,
                node       = dim.value,
                source_ref = source_ref
            )
        else:
            assert False, dim

        elements.append( element )

    return Nodes.CPythonExpressionSequenceCreation(
        sequence_kind = "TUPLE",
        elements      = elements,
        source_ref    = source_ref
    )

def buildSubscriptNode( provider, node, source_ref ):
    assert getKind( node.ctx ) == "Load", source_ref

    kind = getKind( node.slice )

    if kind == "Index":
        return Nodes.CPythonExpressionSubscriptionLookup(
            expression = buildNode( provider, node.value, source_ref ),
            subscript  = buildNode( provider, node.slice.value, source_ref ),
            source_ref = source_ref
        )
    elif kind == "Slice":
        lower = buildNode( provider, node.slice.lower, source_ref ) if node.slice.lower is not None else None
        upper = buildNode( provider, node.slice.upper, source_ref ) if node.slice.upper is not None else None

        if node.slice.step is not None:
            step = buildNode( provider, node.slice.step,  source_ref )

            return Nodes.CPythonExpressionSubscriptionLookup(
                expression = buildNode( provider, node.value, source_ref ),
                subscript  = Nodes.CPythonExpressionSliceObject(
                    lower      = lower,
                    upper      = upper,
                    step       = step,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        else:
            return Nodes.CPythonExpressionSlice(
                expression = buildNode( provider, node.value, source_ref ),
                lower      = lower,
                upper      = upper,
                source_ref = source_ref
            )
    elif kind == "ExtSlice":
        return Nodes.CPythonExpressionSubscriptionLookup(
            expression = buildNode( provider, node.value, source_ref ),
            subscript  = _buildExtSliceNode( provider, node, source_ref ),
            source_ref = source_ref
        )
    elif kind == "Ellipsis":
        return Nodes.CPythonExpressionSubscriptionLookup(
            expression = buildNode( provider, node.value, source_ref ),
            subscript  = Nodes.CPythonExpressionConstant(
                    constant   = Ellipsis,
                    source_ref = source_ref
            ),
            source_ref = source_ref
        )
    else:
        assert False, kind

from Importing import _isWhiteListedNotExistingModule

def _buildImportModulesNode( provider, parent_package, import_names, source_ref ):
    import_specs = []

    for import_desc in import_names:
        module_name, local_name = import_desc

        module_topname = module_name.split(".")[0]
        module_basename =  module_name.split(".")[-1]

        module_package, module_name, module_filename = Importing.findModule(
            module_name    = module_name,
            parent_package = parent_package
        )

        variable = provider.getVariableForAssignment( local_name if local_name is not None else module_topname )

        if local_name is not None:
            import_name = module_name
        elif parent_package is not None and module_package is not None and module_package.getName().startswith( parent_package.getName() ) and not module_name.startswith( module_package.getName() ):
            import_name = module_package.getName() + "." + module_topname
        else:
            import_name = module_topname

        import_spec = ImportSpec(
            module_package  = module_package,
            module_name     = module_basename,
            import_name     = import_name,
            variable        = variable,
            module_filename = module_filename,
        )

        import_specs.append( import_spec )

    return Nodes.CPythonStatementImportModules(
        import_specs = import_specs,
        source_ref   = source_ref
    )

def buildImportModulesNode( provider, node, source_ref ):
    return _buildImportModulesNode(
        provider       = provider,
        parent_package = provider.getParentModule().getPackage(),
        import_names   = [ ( import_desc.name, import_desc.asname ) for import_desc in node.names ],
        source_ref     = source_ref
    )

def buildImportFromNode( provider, node, source_ref ):
    parent_package = provider.getParentModule().getPackage()
    module_name = node.module

    if module_name == "__future__":
        assert provider.isModule()

        for import_desc in node.names:
            object_name, local_name = import_desc.name, import_desc.asname

            if object_name == "unicode_literals":
                global _unicode_literals
                _unicode_literals = True
            elif object_name == "absolute_import":
                global _absolute_import
                _absolute_import = True
            elif object_name == "division":
                global _future_division
                _future_division = True
            elif object_name == "print_function":
                global _future_print
                _future_print = True
            elif object_name in ( "nested_scopes", "generators", "with_statement" ):
                pass
            else:
                warning( "Ignoring unkown future directive '%s'" % object_name )
    elif module_name == "":
        return _buildImportModulesNode(
            provider       = provider,
            parent_package = None,
            import_names   = [ ( parent_package.getName() + "." +  import_desc.name, import_desc.asname ) for import_desc in node.names ],
            source_ref     = source_ref
        )

    imports = []

    for import_desc in node.names:
        object_name, local_name = import_desc.name, import_desc.asname

        if object_name == "*":
            local_variable = None
        else:
            local_variable = provider.getVariableForAssignment( local_name if local_name is not None else object_name )

        imports.append( ( object_name, local_variable ) )

    module_package, module_name, module_filename = Importing.findModule(
        module_name    = module_name,
        parent_package = parent_package
    )

    if module_package is not None:
        module_package = Nodes.CPythonPackage(
            parent_package = parent_package,
            package_name   = module_package
        )

    return Nodes.CPythonStatementImportFrom(
        provider        = provider,
        module_name     = module_name,
        module_package  = module_package,
        module_filename = module_filename,
        imports         = imports,
        source_ref      = source_ref
    )

def buildPrintNode( provider, node, source_ref ):
    values = buildNodeList( provider, node.values, source_ref )
    dest = buildNode( provider, node.dest, source_ref ) if node.dest is not None else None

    return Nodes.CPythonStatementPrint(
        newline    = node.nl,
        dest       = dest,
        values     = values,
        source_ref = source_ref
    )

def buildExecNode( provider, node, source_ref ):
    exec_globals = node.globals
    exec_locals = node.locals
    body = node.body

    # Allow exec(a,b,c) to be same as exec a, b, c
    if exec_locals is None and exec_globals is None and getKind( body ) == "Tuple":
        parts = body.elts
        body  = parts[0]
        exec_globals = parts[1]

        if len( parts ) > 2:
            exec_locals = parts[2]

    globals_node = buildNode( provider, exec_globals, source_ref ) if exec_globals is not None else None
    locals_node = buildNode( provider, exec_locals, source_ref ) if exec_locals is not None else None

    if locals_node is not None and locals_node.isConstantReference() and locals_node.getConstant() is None:
        locals_node = None

    if locals_node is None and globals_node is not None and globals_node.isConstantReference() and globals_node.getConstant() is None:
        globals_node = None

    return Nodes.CPythonStatementExec(
        source       = buildNode( provider, body, source_ref ),
        globals_arg  = globals_node,
        locals_arg   = locals_node,
        future_flags = getFuture(),
        source_ref   = source_ref
    )

def buildWithNode( provider, node, source_ref ):
    return Nodes.CPythonStatementWith(
        source     = buildNode( provider, node.context_expr, source_ref ),
        target     = buildAssignTarget( provider, node.optional_vars, source_ref ) if node.optional_vars else None,
        body       = buildStatementsNode( provider, node.body, source_ref ),
        source_ref = source_ref
    )

def buildNodeList( provider, nodes, source_ref ):
    if nodes is not None:
        return [ buildNode( provider, node, source_ref.atLineNumber( node.lineno ) ) for node in nodes ]
    else:
        return []

def buildGlobalDeclarationNode( provider, node, source_ref ):
    try:
        parameters = provider.getParameters()

        for variable_name in node.names:
            if variable_name in parameters.getParameterNames():
                raise SyntaxError( "global for parameter name" )
    except AttributeError:
        pass

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

_sources = {}

def buildStringNode( provider, node, source_ref ):
    assert type( node.s ) in ( str, unicode )

    value = node.s

    return Nodes.CPythonExpressionConstant(
        constant   = node.s,
        source_ref = source_ref
    )

def buildBoolOpNode( provider, node, source_ref ):
    bool_op = getKind( node.op )

    if bool_op == "Or":
        return Nodes.CPythonExpressionOR(
            expressions = buildNodeList( provider, node.values, source_ref ),
            source_ref  = source_ref
        )
    elif bool_op == "And":
        return Nodes.CPythonExpressionAND(
            expressions = buildNodeList( provider, node.values, source_ref ),
            source_ref  = source_ref
        )
    elif bool_op == "Not":
        return Nodes.CPythonExpressionNOT(
            expression = buildNode( provider, node.operand, source_ref ),
            source_ref = source_ref
        )
    else:
        assert False, bool_op

_quick_names = {
    "None"  : None,
    "True"  : True,
    "False" : False
}

def buildNode( provider, node, source_ref ):
    try:
        kind = getKind( node )

        source_ref = source_ref.atLineNumber( node.lineno )

        if kind == "Assign":
            result = buildAssignNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind == "Delete":
            result = buildDeleteNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind == "Subscript" and getKind( node.ctx ) == "Del":
            result = buildDelNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind == "Subscript":
            result = buildSubscriptNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind == "Attribute":
            result = Nodes.CPythonExpressionAttributeLookup(
                expression = buildNode( provider, node.value, source_ref ),
                attribute  = node.attr,
                source_ref = source_ref
            )
        elif kind == "Lambda":
            result = buildLambdaNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind == "Return":
            result = Nodes.CPythonStatementReturn(
                expression = buildNode( provider, node.value, source_ref ) if node.value is not None else None,
                source_ref = source_ref
            )
        elif kind == "Yield":
            provider.markAsGenerator()

            result = Nodes.CPythonExpressionYield(
                expression = buildNode( provider, node.value, source_ref ) if node.value is not None else None,
                source_ref = source_ref
            )
        elif kind == "While":
            result = buildWhileLoopNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind == "For":
            result = buildForLoopNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind == "Continue":
            result = Nodes.CPythonStatementContinueLoop(
                source_ref = source_ref
            )
        elif kind == "Break":
            result = Nodes.CPythonStatementBreakLoop(
                source_ref = source_ref
            )
        elif kind == "ListComp":
            result = buildListContractionNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind == "GeneratorExp":
            result = buildGeneratorExpressionNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind == "SetComp":
            result = buildSetContractionNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind == "DictComp":
            result = buildDictContractionNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind == "Dict":
            result = buildDictionaryNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind == "Set":
            result = buildSetNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind == "Expr":
            result = Nodes.CPythonStatementExpressionOnly(
                expression = buildNode( provider, node.value, source_ref ),
                source_ref = source_ref
            )
        elif kind == "BoolOp" or ( kind == "UnaryOp" and getKind( node.op ) == "Not" ):
            result = buildBoolOpNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind == "BinOp":
            operator = getKind( node.op )

            if operator == "Div" and _future_division:
                operator = "TrueDiv"

            result = Nodes.CPythonExpressionBinaryOperation(
                operator   = PythonOperators.binary_operators[ operator ],
                left       = buildNode( provider, node.left, source_ref ),
                right      = buildNode( provider, node.right, source_ref ),
                source_ref = source_ref
            )
        elif kind in "UnaryOp":
            result = Nodes.CPythonExpressionUnaryOperation(
                operator   = PythonOperators.unary_operators[ getKind( node.op ) ],
                operand    = buildNode( provider, node.operand, source_ref ),
                source_ref = source_ref
            )
        elif kind == "Repr":
            result = Nodes.CPythonExpressionUnaryOperation(
                operator   = PythonOperators.unary_operators[ "Repr" ],
                operand    = buildNode( provider, node.value, source_ref ),
                source_ref = source_ref
            )
        elif kind == "AugAssign":
            result = Nodes.CPythonStatementAssignmentInplace(
                operator   = getKind( node.op ),
                target     = buildAssignTarget( provider, node.target, source_ref ),
                expression = buildNode( provider, node.value, source_ref ),
                source_ref = source_ref
            )
        elif kind == "Global":
            result = buildGlobalDeclarationNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind == "IfExp":
            result = Nodes.CPythonExpressionConditional(
                condition      = buildNode( provider, node.test, source_ref ),
                yes_expression = buildNode( provider, node.body, source_ref ),
                no_expression  = buildNode( provider, node.orelse, source_ref ),
                source_ref     = source_ref
            )
        elif kind == "If":
            result = buildConditionNode(
                provider   = provider,
                node       = node,
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
        elif kind ==  "ImportFrom":
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
        elif kind == "FunctionDef":
            result = buildFunctionNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind == "ClassDef":
            result = buildClassNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind == "Name":
            if node.id in _quick_names:
                result = Nodes.CPythonExpressionConstant(
                    constant   = _quick_names[ node.id ],
                    source_ref = source_ref
                )
            else:
                result = Nodes.CPythonExpressionVariable(
                    variable_name = node.id,
                    source_ref    = source_ref
                )

                if provider.isEarlyClosure():
                    result.setVariable( provider.getVariableForReference( node.id ) )
        elif kind == "Str":
            result = buildStringNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind == "Num":
            assert type( node.n ) in ( int, long, float, complex ), type( node.n )

            result = Nodes.CPythonExpressionConstant(
                constant   = node.n,
                source_ref = source_ref
            )
        elif kind in ( "List", "Tuple" ):
            result = buildSequenceCreationNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind == "Print":
            result = buildPrintNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind == "Call":
            result = buildFunctionCallNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind == "Compare":
            result = buildComparisonNode(
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        else:
            assert False, kind

        assert isinstance( result, Nodes.CPythonNode )

        return result
    except SyntaxError:
        raise
    except:
        warning( "Problem at '%s' with %s." % ( source_ref, ast.dump( node ) ) )
        raise

class ModuleRecursionVisitor:
    imported_modules = {}

    def __init__( self, module, module_filename, stdlib ):
        if module_filename not in self.imported_modules:
            self.imported_modules[ os.path.relpath( module_filename ) ] = module

        self.stdlib = stdlib

    def _consider( self, module_filename, module_package ):
        assert module_package is None or isinstance( module_package, Nodes.CPythonPackage )

        if module_filename.endswith( ".py" ):
            if self.stdlib or not module_filename.startswith( "/usr/lib/python" ):
                if os.path.relpath( module_filename ) not in self.imported_modules:
                    print( "Recurse to", module_filename )

                    imported_module = buildModuleTree(
                        filename = module_filename,
                        package  = module_package
                    )

                    self.imported_modules[ os.path.relpath( module_filename ) ] = imported_module

    def __call__( self, node ):
        if node.isStatementImport() or node.isStatementImportFrom():
            for module_filename, module_package in zip( node.getModuleFilenames(), node.getModulePackages() ):
                self._consider(
                    module_filename = module_filename,
                    module_package  = module_package
                )
        elif node.isBuiltinImport():
           self._consider(
                module_filename = node.getModuleFilename(),
                module_package  = node.getModulePackage()
            )


class VariableClosureLookupVisitor:
    def __call__( self, node ):
        if node.isVariableReference() and node.getVariable() is None:
            node.setVariable( node.getParentVariableProvider().getVariableForReference( node.getVariableName() ) )

def getOtherModules():
    return ModuleRecursionVisitor.imported_modules.values()

import os

def extractDocFromBody( node ):
    # Work around ast.get_docstring breakage.
    if len( node.body ) > 0 and getKind( node.body[0] ) == "Expr" and getKind( node.body[0].value ) == "Str":
        return node.body[1:], node.body[0].value.s
    else:
        return node.body, None


def buildParseTree( provider, source_code, filename, line_offset, replacement ):
    # Workaround: ast.parse cannot cope with some situations where a file is not terminated
    # by a new line.
    if not source_code.endswith( "\n" ):
        source_code = source_code + "\n"

    body = ast.parse( source_code, filename )
    assert getKind( body ) == "Module"

    if line_offset > 0:
        for created_node in ast.walk( body ):
            if hasattr( created_node, "lineno" ):
                created_node.lineno += line_offset

    source_ref = SourceCodeReferences.fromFilename( filename )

    body, doc = extractDocFromBody( body )

    if not replacement:
        result = buildStatementsNode(
            provider   = provider,
            nodes      = body,
            source_ref = source_ref
        )
    else:
        result = buildReplacementStatementsNode(
            provider   = provider,
            nodes      = body,
            source_ref = source_ref
        )

    if not replacement:
        provider.setBody( result )
        provider.setDoc( doc )

    while _delayed_works:
        delayed_work = _delayed_works.pop()

        delayed_work()

    return result

def buildReplacementTree( provider, parent, source_code, filename, line_offset ):
    pushFuture()

    result = buildParseTree( provider, source_code, filename, line_offset, replacement = True )

    TreeOperations.assignParent( result )
    result.parent = parent

    applyImmediateTransformations( result )

    popFuture()

    return result

def applyImmediateTransformations( tree ):
    # Some things that the compiler can or should always do:

    # 1. Look at the imports and recurse into them
    if Options.shallFollowImports():
        parent_module = tree.getParentModule()

        TreeOperations.visitTree(
            tree    = tree,
            visitor = ModuleRecursionVisitor( parent_module, parent_module.getFilename(), Options.shallFollowStandardLibrary() )
        )

    # 2. Replace exec with string constant as parameters with the code inlined
    # instead. This is an optimization that is easy to do and useful for large parts of
    # the CPython test suite that exec constant strings.
    if Options.shallOptimizeStringExec():
        TreeTransforming.replaceConstantExecs( tree, buildReplacementTree )

    # 3. Now that the tree is complete, make a second pass and find the referenced
    # variable for every name lookup done. Afterwards no more getVariableForAssignment
    # should be called.
    TreeOperations.visitTree( tree, VariableClosureLookupVisitor() )

    # 4. Replace calls to locals, globals or eval with our own variants, because these
    # will refuse to work (exe case) or give incorrect results (module case).
    TreeTransforming.replaceBuiltinsCallsThatRequireInterpreter( tree, getFuture() )

    # 5. Look at the imports and recurse into them again, because new ones may have surfaced
    if Options.shallFollowImports():
        parent_module = tree.getParentModule()

        TreeOperations.visitTree(
            tree    = tree,
            visitor = ModuleRecursionVisitor( parent_module, parent_module.getFilename(), Options.shallFollowStandardLibrary() )
        )


def buildModuleTree( filename, package = None ):
    assert package is None or isinstance( package, Nodes.CPythonPackage )

    initFuture()

    global _delayed_works
    _delayed_works = []

    result = Nodes.CPythonModule(
        name       = os.path.basename( filename ).replace( ".py", "" ),
        package    = package,
        filename   = os.path.relpath( filename ),
        source_ref = SourceCodeReferences.fromFilename( filename )
    )

    buildParseTree(
        provider    = result,
        source_code = open( filename ).read(),
        filename    = filename,
        line_offset = 0,
        replacement = False
    )


    TreeOperations.assignParent( result )

    applyImmediateTransformations( result )

    return result
