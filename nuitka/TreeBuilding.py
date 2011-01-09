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
# pylint: disable=W0622
from .__past__ import long, unicode
# pylint: enable=W0622

from . import (
    SourceCodeReferences,
    TreeOperations,
    Importing,
    Nodes,
    Utils
)

from .nodes.ParameterSpec import ParameterSpec
from .nodes.FutureSpec import FutureSpec

import ast, sys

from logging import warning

def dump( node ):
    print( ast.dump( node ) )

def getKind( node ):
    return node.__class__.__name__.split( "." )[-1]

# pylint: disable=W0603
_delayed_works = []

def pushDelayedWork( delayed_work ):
    # pylint: disable=W0602
    global _delayed_works

    _delayed_works.append( delayed_work )

def buildStatementsNode( provider, nodes, source_ref, allow_none = False ):
    if nodes is None and allow_none:
        return None

    return Nodes.CPythonStatementsSequence(
        statements  = buildNodeList( provider, nodes, source_ref ),
        source_ref  = source_ref
    )

def buildDecoratorNodes( provider, nodes, source_ref ):
    return buildNodeList( provider, reversed( nodes ), source_ref )

def buildClassNode( provider, node, source_ref ):
    assert getKind( node ) == "ClassDef"

    class_body, class_doc = extractDocFromBody( node )

    decorators = buildDecoratorNodes( provider, node.decorator_list, source_ref )

    bases = buildNodeList( provider, node.bases, source_ref )

    result = Nodes.CPythonStatementClassDef(
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


def buildParameterSpec( node ):
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

    return ParameterSpec(
        normal_args    = argnames,
        list_star_arg  = varargs,
        dict_star_arg  = kwargs,
        default_count  = len( node.args.defaults )
    )

def buildFunctionNode( provider, node, source_ref ):
    assert getKind( node ) == "FunctionDef"

    function_body, function_doc = extractDocFromBody( node )

    decorators = buildDecoratorNodes( provider, node.decorator_list, source_ref )
    defaults = buildNodeList( provider, node.args.defaults, source_ref )

    result = Nodes.CPythonStatementFunctionDef(
        provider   = TransitiveProvider( provider ),
        variable   = provider.getVariableForAssignment( node.name ),
        parameters = buildParameterSpec( node ),
        defaults   = defaults,
        name       = node.name,
        doc        = function_doc,
        decorators = decorators,
        source_ref = source_ref
    )

    def delayedWork():
        body = buildStatementsNode(
            provider   = result,
            nodes      = function_body,
            source_ref = source_ref,
        )

        result.setBody( body )

    pushDelayedWork( delayedWork )

    return result

def isSameListContent( a, b ):
    return list( sorted( a ) ) == list( sorted( b ) )

def buildLambdaNode( provider, node, source_ref ):
    defaults = buildNodeList( provider, node.args.defaults, source_ref )

    result = Nodes.CPythonExpressionLambdaDef(
        provider   = provider,
        parameters = buildParameterSpec( node ),
        defaults   = defaults,
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
        no_break   = buildStatementsNode( provider, node.orelse, source_ref, True ),
        source_ref = source_ref
    )

def buildWhileLoopNode( provider, node, source_ref ):
    return Nodes.CPythonStatementWhileLoop(
        condition  = buildNode( provider, node.test, source_ref ),
        body       = buildStatementsNode( provider, node.body, source_ref ),
        no_enter   = buildStatementsNode( provider, node.orelse, source_ref, True ),
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
        list_star_arg     = buildNode( provider, node.starargs, source_ref, True ),
        dict_star_arg     = buildNode( provider, node.kwargs, source_ref, True ),
        named_args        = named_args,
        source_ref        = source_ref,
    )

def buildSequenceCreationNode( provider, node, source_ref ):
    elements = buildNodeList( provider, node.elts, source_ref )

    for element in elements:
        if not element.isConstantReference() or element.isMutable():
            constant = False
            break
    else:
        constant = True

    sequence_kind = getKind( node ).upper()

    # TODO: This should happen in optimization instead.
    if constant:
        const_type = tuple if sequence_kind == "TUPLE" else list

        return Nodes.CPythonExpressionConstantRef(
            constant   = const_type( element.getConstant() for element in elements ),
            source_ref = source_ref
        )
    else:
        return Nodes.CPythonExpressionMakeSequence(
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

    # TODO: Again, this is for optimization to do.
    if constant:
        # Create the dictionary in its full size, so that no growing occurs and the
        # constant becomes as similar as possible before being marshalled.
        constant_value = dict.fromkeys( [ key.getConstant() for key in keys ], None )

        for key, value in zip( keys, values ):
            constant_value[ key.getConstant() ] = value.getConstant()

        return Nodes.CPythonExpressionConstantRef(
            constant   = constant_value,
            source_ref = source_ref
        )
    else:
        return Nodes.CPythonExpressionMakeDict(
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

    # TODO: Again, this is for optimization to do.
    if constant:
        constant_value = frozenset( value.getConstant() for value in values )

        return Nodes.CPythonExpressionConstantRef(
            constant   = constant_value,
            source_ref = source_ref
        )
    else:
        return Nodes.CPythonExpressionMakeSet(
            values     = values,
            source_ref = source_ref
        )

def buildAssignTarget( provider, node, source_ref, allow_none = False ):
    if node is None and allow_none:
        return None

    if hasattr( node, "ctx" ):
        assert getKind( node.ctx ) in ( "Store", "Del" )

    kind = getKind( node )

    if type( node ) is str:
        # Python >= 3.1 only
        return Nodes.CPythonAssignTargetVariable(
            variable   = provider.getVariableForAssignment(
                variable_name = node
            ),
            source_ref = source_ref
        )
    elif kind == "Name":
        return Nodes.CPythonAssignTargetVariable(
            variable   = provider.getVariableForAssignment(
                variable_name = node.id
            ),
            source_ref = source_ref
        )
    elif kind == "Attribute":
        return Nodes.CPythonAssignTargetAttribute(
            expression = buildNode( provider, node.value, source_ref ),
            attribute  = node.attr,
            source_ref = source_ref
        )
    elif kind in ( "Tuple", "List" ):
        elements = []

        for element in node.elts:
            elements.append( buildAssignTarget( provider, element, source_ref ) )

        return Nodes.CPythonAssignTargetTuple(
            elements   = elements,
            source_ref = source_ref
        )
    elif kind == "Subscript":
        slice_kind = getKind( node.slice )

        if slice_kind == "Index":
            return Nodes.CPythonAssignTargetSubscript(
                expression = buildNode( provider, node.value, source_ref ),
                subscript  = buildNode( provider, node.slice.value, source_ref ),
                source_ref = source_ref
            )
        elif slice_kind == "Slice":
            lower = buildNode( provider, node.slice.lower, source_ref, True )
            upper = buildNode( provider, node.slice.upper, source_ref, True )

            if node.slice.step is not None:
                step = buildNode( provider, node.slice.step, source_ref )

                return Nodes.CPythonAssignTargetSubscript(
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
                return Nodes.CPythonAssignTargetSlice(
                    expression = buildNode( provider, node.value, source_ref ),
                    lower      = lower,
                    upper      = upper,
                    source_ref = source_ref
                )
        elif slice_kind == "ExtSlice":
            return Nodes.CPythonAssignTargetSubscript(
                expression = buildNode( provider, node.value, source_ref ),
                subscript  = _buildExtSliceNode( provider, node, source_ref ),
                source_ref = source_ref
            )
        elif slice_kind == "Ellipsis":
            return Nodes.CPythonAssignTargetSubscript(
                expression = buildNode( provider, node.value, source_ref ),
                subscript  = Nodes.CPythonExpressionConstantRef(
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
            conditions = [
                buildNode( provider = result, node = condition, source_ref = source_ref )
                for condition in
                qual.ifs
            ]

            if len( conditions ) == 1:
                condition = conditions[ 0 ]
            else:
                condition = Nodes.CPythonExpressionBoolAnd(
                    expressions = conditions,
                    source_ref  = source_ref
                )
        else:
            condition = Nodes.CPythonExpressionConstantRef(
                constant   = True,
                source_ref = source_ref
            )

        # Different for list contractions and generator expressions
        source = qual.iter

        if count == 0:
            source_provider = provider
        else:
            source_provider = result

        qual_sources.append(
            buildNode( provider = source_provider, node = source, source_ref = source_ref )
        )
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

    result = Nodes.CPythonExpressionGenerator(
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

    return Nodes.CPythonExpressionComparison(
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

        catchers.append(
            buildNode( provider, exception_expression, source_ref, True )
        )
        assigns.append(
            buildAssignTarget( provider, exception_assign, source_ref, True )
        )
        catcheds.append(
            buildStatementsNode( provider, exception_block, source_ref )
        )

    return Nodes.CPythonStatementTryExcept(
        tried      = buildStatementsNode( provider, node.body, source_ref ),
        catchers   = catchers,
        assigns    = assigns,
        catcheds   = catcheds,
        no_raise   = buildStatementsNode( provider, node.orelse, source_ref, True ),
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
        exception_type  = buildNode( provider, node.type, source_ref, True ),
        exception_value = buildNode( provider, node.inst, source_ref, True ),
        exception_trace = buildNode( provider, node.tback, source_ref, True ),
        source_ref      = source_ref
    )

def buildAssertNode( provider, node, source_ref ):
    return Nodes.CPythonStatementAssert(
        expression = buildNode( provider, node.test, source_ref ),
        failure    = buildNode( provider, node.msg, source_ref, True ),
        source_ref = source_ref
    )


def _buildExtSliceNode( provider, node, source_ref ):
    elements = []

    for dim in node.slice.dims:
        dim_kind = getKind( dim )

        if dim_kind == "Slice":
            lower = buildNode( provider, dim.lower, source_ref, True )
            upper = buildNode( provider, dim.upper, source_ref, True )
            step = buildNode( provider, dim.step, source_ref, True )

            element = Nodes.CPythonExpressionSliceObject(
                lower      = lower,
                upper      = upper,
                step       = step,
                source_ref = source_ref
            )
        elif dim_kind == "Ellipsis":
            element = Nodes.CPythonExpressionConstantRef(
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

    return Nodes.CPythonExpressionMakeSequence(
        sequence_kind = "TUPLE",
        elements      = elements,
        source_ref    = source_ref
    )

def buildSubscriptNode( provider, node, source_ref ):
    if getKind( node.ctx ) == "Del":
        target = buildAssignTarget( provider, node, source_ref )

        return Nodes.CPythonStatementAssignment(
            targets    = ( target, ),
            expression = None,
            source_ref = source_ref
        )

    assert getKind( node.ctx ) == "Load", source_ref

    kind = getKind( node.slice )

    if kind == "Index":
        return Nodes.CPythonExpressionSubscriptionLookup(
            expression = buildNode( provider, node.value, source_ref ),
            subscript  = buildNode( provider, node.slice.value, source_ref ),
            source_ref = source_ref
        )
    elif kind == "Slice":
        lower = buildNode( provider, node.slice.lower, source_ref, True )
        upper = buildNode( provider, node.slice.upper, source_ref, True )

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
            return Nodes.CPythonExpressionSliceLookup(
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
            subscript  = Nodes.CPythonExpressionConstantRef(
                    constant   = Ellipsis,
                    source_ref = source_ref
            ),
            source_ref = source_ref
        )
    else:
        assert False, kind

def _buildImportModulesNode( provider, import_names, source_ref ):
    import_nodes = []

    for import_desc in import_names:
        module_name, local_name = import_desc

        module_topname = module_name.split(".")[0]

        # If a name was given, use the one provided, otherwise the import gives the top
        # level package name given for assignment of the imported module.
        variable = provider.getVariableForAssignment(
            local_name if local_name is not None else module_topname
        )

        import_nodes.append(
            Nodes.CPythonStatementImportExternal(
                target      = Nodes.CPythonAssignTargetVariable(
                    variable   = variable,
                    source_ref = source_ref
                ),
                module_name = module_name,
                import_name = module_name if local_name else module_topname,
                source_ref  = source_ref
            )
        )

    return Nodes.CPythonStatementsSequence(
        statements  = import_nodes,
        source_ref  = source_ref
    )

def buildImportModulesNode( provider, node, source_ref ):
    return _buildImportModulesNode(
        provider       = provider,
        import_names   = [
            ( import_desc.name, import_desc.asname )
            for import_desc in
            node.names
        ],
        source_ref     = source_ref
    )

def buildImportFromNode( provider, node, source_ref ):
    parent_package = provider.getParentModule().getPackage()
    module_name = node.module if node.module is not None else ""

    if module_name == "__future__":
        assert provider.isModule()

        for import_desc in node.names:
            object_name, local_name = import_desc.name, import_desc.asname

            if object_name == "unicode_literals":
                source_ref.getFutureSpec().enableUnicodeLiterals()
            elif object_name == "absolute_import":
                source_ref.getFutureSpec().enableAbsoluteImport()
            elif object_name == "division":
                source_ref.getFutureSpec().enableFutureDivision()
            elif object_name == "print_function":
                source_ref.getFutureSpec().enableFuturePrint()
            elif object_name in ( "nested_scopes", "generators", "with_statement" ):
                pass
            else:
                warning( "Ignoring unkown future directive '%s'" % object_name )
    elif module_name == "":
        return _buildImportModulesNode(
            provider       = provider,
            import_names   = [
                ( import_desc.name, import_desc.asname )
                for import_desc in
                node.names
            ],
            source_ref     = source_ref
        )

    targets = []
    imports = []

    for import_desc in node.names:
        object_name, local_name = import_desc.name, import_desc.asname

        if object_name == "*":
            target = None
        else:
            target = Nodes.CPythonAssignTargetVariable(
                variable   = provider.getVariableForAssignment(
                    variable_name = local_name if local_name is not None else object_name
                ),
                source_ref = source_ref
            )


        targets.append( target )
        imports.append( object_name )

    _module_package, module_name, _module_filename = Importing.findModule(
        module_name    = module_name,
        parent_package = parent_package
    )

    if None in targets:
        return Nodes.CPythonStatementImportStarExternal(
            module_name     = module_name,
            source_ref      = source_ref
        )
    else:
        return Nodes.CPythonStatementImportFromExternal(
            targets         = targets,
            module_name     = module_name,
            imports         = imports,
            source_ref      = source_ref
        )

def buildPrintNode( provider, node, source_ref ):
    values = buildNodeList( provider, node.values, source_ref )
    dest = buildNode( provider, node.dest, source_ref, True )

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

    globals_node = buildNode( provider, exec_globals, source_ref, True )
    locals_node = buildNode( provider, exec_locals, source_ref, True )

    if locals_node is not None and locals_node.isConstantReference() and locals_node.getConstant() is None:
        locals_node = None

    if locals_node is None and globals_node is not None and globals_node.isConstantReference() and globals_node.getConstant() is None:
        globals_node = None

    return Nodes.CPythonStatementExec(
        source       = buildNode( provider, body, source_ref ),
        globals_arg  = globals_node,
        locals_arg   = locals_node,
        source_ref   = source_ref
    )

def buildWithNode( provider, node, source_ref ):
    return Nodes.CPythonStatementWith(
        source     = buildNode( provider, node.context_expr, source_ref ),
        target     = buildAssignTarget( provider, node.optional_vars, source_ref, True ),
        body       = buildStatementsNode( provider, node.body, source_ref ),
        source_ref = source_ref
    )

def buildNodeList( provider, nodes, source_ref ):
    if nodes is not None:
        return [
            buildNode( provider, node, source_ref.atLineNumber( node.lineno ) )
            for node in
            nodes
        ]
    else:
        return []

def buildGlobalDeclarationNode( provider, node, source_ref ):
    # Need to catch the error of declaring a parameter variable as global ourselves
    # here. The AST parsing doesn't catch it.
    try:
        parameters = provider.getParameters()

        for variable_name in node.names:
            if variable_name in parameters.getParameterNames():
                raise SyntaxError( "global for parameter name" )
    except AttributeError:
        pass

    # Make sure the provider has these global variables taken.
    for variable_name in node.names:
        provider.getModuleClosureVariable( variable_name = variable_name )

    return Nodes.CPythonStatementDeclareGlobal(
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

    def getParentModule( self ):
        return self.effective_provider.getParentModule()

    def createProvidedVariable( self, variable_name ):
        return self.effective_provider.createProvidedVariable(
            variable_name = variable_name
        )

_sources = {}

def buildStringNode( node, source_ref ):
    assert type( node.s ) in ( str, unicode )

    return Nodes.CPythonExpressionConstantRef(
        constant   = node.s,
        source_ref = source_ref
    )

def buildBoolOpNode( provider, node, source_ref ):
    bool_op = getKind( node.op )

    if bool_op == "Or":
        return Nodes.CPythonExpressionBoolOr(
            expressions = buildNodeList( provider, node.values, source_ref ),
            source_ref  = source_ref
        )
    elif bool_op == "And":
        return Nodes.CPythonExpressionBoolAnd(
            expressions = buildNodeList( provider, node.values, source_ref ),
            source_ref  = source_ref
        )
    elif bool_op == "Not":
        return Nodes.CPythonExpressionBoolNot(
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

_fastpath = {
    "Assign"       : buildAssignNode,
    "Delete"       : buildDeleteNode,
    "Lambda"       : buildLambdaNode,
    "GeneratorExp" : buildGeneratorExpressionNode,
    "If"           : buildConditionNode,
    "While"        : buildWhileLoopNode,
    "For"          : buildForLoopNode,
    "Compare"      : buildComparisonNode,
    "ListComp"     : buildListContractionNode,
    "DictComp"     : buildDictContractionNode,
    "SetComp"      : buildSetContractionNode,
    "Dict"         : buildDictionaryNode,
    "Set"          : buildSetNode,
    "Tuple"        : buildSequenceCreationNode,
    "List"         : buildSequenceCreationNode,
    "Global"       : buildGlobalDeclarationNode,
    "TryExcept"    : buildTryExceptionNode,
    "TryFinally"   : buildTryFinallyNode,
    "Raise"        : buildRaiseNode,
    "Import"       : buildImportModulesNode,
    "ImportFrom"   : buildImportFromNode,
    "Assert"       : buildAssertNode,
    "Exec"         : buildExecNode,
    "With"         : buildWithNode,
    "FunctionDef"  : buildFunctionNode,
    "ClassDef"     : buildClassNode,
    "Print"        : buildPrintNode,
    "Call"         : buildFunctionCallNode,
    "Subscript"    : buildSubscriptNode,
    "BoolOp"       : buildBoolOpNode,
}

def buildNode( provider, node, source_ref, allow_none = False ):
    if node is None and allow_none:
        return None

    try:
        kind = getKind( node )

        source_ref = source_ref.atLineNumber( node.lineno )

        if kind in _fastpath:
            result = _fastpath[kind](
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
        elif kind == "Return":
            result = Nodes.CPythonStatementReturn(
                expression = buildNode( provider, node.value, source_ref, True ),
                source_ref = source_ref
            )
        elif kind == "Yield":
            provider.markAsGenerator()

            result = Nodes.CPythonExpressionYield(
                expression = buildNode( provider, node.value, source_ref, True ),
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
        elif kind == "Expr":
            result = Nodes.CPythonStatementExpressionOnly(
                expression = buildNode( provider, node.value, source_ref ),
                source_ref = source_ref
            )
        elif kind == "UnaryOp":
            if getKind( node.op ) == "Not":
                result = buildBoolOpNode(
                    provider   = provider,
                    node       = node,
                    source_ref = source_ref
                )
            else:
                result = Nodes.CPythonExpressionUnaryOperation(
                    operator   = getKind( node.op ),
                    operand    = buildNode( provider, node.operand, source_ref ),
                    source_ref = source_ref
                )
        elif kind == "BinOp":
            operator = getKind( node.op )

            if operator == "Div" and source_ref.getFutureSpec().isFutureDivision():
                operator = "TrueDiv"

            result = Nodes.CPythonExpressionBinaryOperation(
                operator   = operator,
                left       = buildNode( provider, node.left, source_ref ),
                right      = buildNode( provider, node.right, source_ref ),
                source_ref = source_ref
            )
        elif kind == "Repr":
            result = Nodes.CPythonExpressionUnaryOperation(
                operator   = "Repr",
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
        elif kind == "IfExp":
            result = Nodes.CPythonExpressionConditional(
                condition      = buildNode( provider, node.test, source_ref ),
                yes_expression = buildNode( provider, node.body, source_ref ),
                no_expression  = buildNode( provider, node.orelse, source_ref ),
                source_ref     = source_ref
            )
        elif kind == "Pass":
            result = Nodes.CPythonStatementPass(
                source_ref = source_ref
            )
        elif kind == "Name":
            if node.id in _quick_names:
                result = Nodes.CPythonExpressionConstantRef(
                    constant   = _quick_names[ node.id ],
                    source_ref = source_ref
                )
            else:
                result = Nodes.CPythonExpressionVariableRef(
                    variable_name = node.id,
                    source_ref    = source_ref
                )

                if provider.isEarlyClosure():
                    result.setVariable( provider.getVariableForReference( node.id ) )
        elif kind == "Str":
            result = buildStringNode(
                node       = node,
                source_ref = source_ref
            )
        elif kind == "Num":
            assert type( node.n ) in ( int, long, float, complex ), type( node.n )

            result = Nodes.CPythonExpressionConstantRef(
                constant   = node.n,
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

def extractDocFromBody( node ):
    # Work around ast.get_docstring breakage.
    if len( node.body ) > 0 and getKind( node.body[0] ) == "Expr" and getKind( node.body[0].value ) == "Str":
        return node.body[1:], node.body[0].value.s
    else:
        return node.body, None


def buildParseTree( provider, source_code, source_ref, replacement ):
    # Workaround: ast.parse cannot cope with some situations where a file is not terminated
    # by a new line.
    if not source_code.endswith( "\n" ):
        source_code = source_code + "\n"

    body = ast.parse( source_code, source_ref.getFilename() )
    assert getKind( body ) == "Module"

    line_offset = source_ref.getLineNumber() - 1

    if line_offset > 0:
        for created_node in ast.walk( body ):
            if hasattr( created_node, "lineno" ):
                created_node.lineno += line_offset

    body, doc = extractDocFromBody( body )

    result = buildStatementsNode(
        provider   = provider,
        nodes      = body,
        source_ref = source_ref
    )

    # TODO: The handling of doc strings should be done in an early optimization step that
    # handles this.
    if not replacement:
        provider.provider.setDoc( doc )
        provider.setBody( result )

    while _delayed_works:
        delayed_work = _delayed_works.pop()

        delayed_work()

    return result

def buildReplacementTree( provider, parent, source_code, source_ref ):
    result = buildParseTree(
        provider    = provider,
        source_code = source_code,
        source_ref  = source_ref,
        replacement = True
    )

    result.parent = parent

    TreeOperations.assignParent( result )

    return result

def buildModuleTree( filename, package, is_main ):
    assert package is None or type( package ) is str

    # pylint: disable=W0602
    global _delayed_works
    _delayed_works = []

    if Utils.isFile( filename ):
        source_filename = filename

        source_ref = SourceCodeReferences.fromFilename(
            filename    = filename,
            future_spec = FutureSpec()
        )

        if is_main:
            module_name = "__main__"
        else:
            module_name = Utils.basename( filename ).replace( ".py", "" )

        result = Nodes.CPythonModule(
            name       = module_name,
            package    = package,
            source_ref = source_ref
        )
    elif Utils.isDir( filename ) and Utils.isFile( filename + "/__init__.py" ):
        source_filename = filename + "/__init__.py"

        source_ref = SourceCodeReferences.fromFilename(
            filename    = Utils.abspath( filename ) + "/__init__.py",
            future_spec = FutureSpec()
        )

        result = Nodes.CPythonPackage(
            name       = Utils.basename( filename ),
            package    = package,
            source_ref = source_ref
        )
    else:
        sys.exit( "Nuitka: can't open file '%s'." % filename )

    buildParseTree(
        provider    = result,
        source_code = open( source_filename ).read(),
        source_ref  = source_ref,
        replacement = False,
    )

    TreeOperations.assignParent( result )

    return result
