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
""" Build the internal node tree from source code.

Does all the Python parsing and puts it into a tree structure for use in later stages of
the compiler. This may happen recursively when exec statements are inlined.
"""

# pylint: disable=W0622
from .__past__ import long, unicode
# pylint: enable=W0622

from . import (
    SourceCodeReferences,
    SyntaxErrors,
    Tracing,
    Utils
)

from .nodes.ParameterSpec import ParameterSpec
from .nodes.FutureSpec import FutureSpec

from .nodes import Nodes
from .nodes.VariableRefNode import CPythonExpressionVariableRef
from .nodes.ConstantRefNode import CPythonExpressionConstantRef
from .nodes.BuiltinReferenceNodes import CPythonExpressionBuiltinExceptionRef
from .nodes.ExceptionNodes import CPythonStatementRaiseException
from .nodes.ComparisonNode import CPythonExpressionComparison

from .nodes.ContainerMakingNodes import (
    CPythonExpressionKeyValuePair,
    CPythonExpressionMakeSequence,
    CPythonExpressionMakeDict,
    CPythonExpressionMakeSet
)

from .nodes.StatementNodes import (
    CPythonStatementsSequenceLoopBody,
    CPythonStatementExpressionOnly,
    CPythonStatementsSequence
)

from .nodes.ImportNodes import (
    CPythonExpressionImportModule,
    CPythonExpressionImportName,
    CPythonStatementImportStar,
)

from .nodes.OperatorNodes import (
    CPythonExpressionOperationBinary,
    CPythonExpressionOperationUnary,
    CPythonExpressionOperationNOT
)

import ast, sys

from logging import warning

def dump( node ):
    Tracing.printLine( ast.dump( node ) )

def getKind( node ):
    return node.__class__.__name__.split( "." )[-1]

# pylint: disable=W0603
_delayed_works = []

def pushDelayedWork( delayed_work ):
    # pylint: disable=W0602
    global _delayed_works

    _delayed_works.append( delayed_work )


def _buildConstantReferenceNode( constant, source_ref ):
    return CPythonExpressionConstantRef(
        constant   = constant,
        source_ref = source_ref
    )

def _buildVariableReferenceNode( variable_name, source_ref ):
    return CPythonExpressionVariableRef(
        variable_name = variable_name,
        source_ref    = source_ref
    )

def buildVariableReferenceNode( node, source_ref ):
    return _buildVariableReferenceNode(
        variable_name = node.id,
        source_ref    = source_ref
    )

def buildStatementsNode( provider, nodes, source_ref, allow_none = False ):
    if nodes is None and allow_none:
        return None

    statements = buildNodeList( provider, nodes, source_ref )

    if not statements and allow_none:
        return None

    return CPythonStatementsSequence(
        statements = statements,
        source_ref = source_ref
    )

def buildLoopBodyNode( provider, nodes, source_ref ):
    statements = buildNodeList( provider, nodes, source_ref )

    return CPythonStatementsSequenceLoopBody(
        statements = statements,
        source_ref = source_ref
    )

def buildDecoratorNodes( provider, nodes, source_ref ):
    return buildNodeList( provider, nodes, source_ref )

def buildClassNode( provider, node, source_ref ):
    assert getKind( node ) == "ClassDef"

    class_statements, class_doc = _extractDocFromBody( node )

    decorators = buildDecoratorNodes( provider, node.decorator_list, source_ref )

    bases = buildNodeList( provider, node.bases, source_ref )

    result = Nodes.CPythonStatementClassBuilder(
        target     = buildVariableRefAssignTarget( node.name, source_ref ),
        bases      = bases,
        decorators = decorators,
        source_ref = source_ref
    )

    def delayedWork():
        class_body = Nodes.CPythonExpressionClassBody(
            provider   = provider,
            name       = node.name,
            doc        = class_doc,
            source_ref = source_ref
        )

        result.setBody( class_body )

        body = buildStatementsNode(
            provider   = class_body,
            nodes      = class_statements,
            source_ref = source_ref,
        )

        class_body.setBody( body )

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

    function_statements, function_doc = _extractDocFromBody( node )

    decorators = buildDecoratorNodes( provider, node.decorator_list, source_ref )
    defaults = buildNodeList( provider, node.args.defaults, source_ref )

    result = Nodes.CPythonStatementFunctionBuilder(
        target     = buildVariableRefAssignTarget( node.name, source_ref ),
        defaults   = defaults,
        decorators = decorators,
        source_ref = source_ref
    )

    def delayedWork():
        real_provider = provider

        while real_provider.isExpressionClassBody():
            real_provider = real_provider.provider

        function_body = Nodes.CPythonExpressionFunctionBody(
            provider   = real_provider,
            name       = node.name,
            doc        = function_doc,
            parameters = buildParameterSpec( node ),
            source_ref = source_ref
        )

        result.setBody( function_body )

        statements = buildStatementsNode(
            provider   = function_body,
            nodes      = function_statements,
            source_ref = source_ref,
        )

        function_body.setBody( statements )

    pushDelayedWork( delayedWork )

    return result

def isSameListContent( a, b ):
    return list( sorted( a ) ) == list( sorted( b ) )

def buildLambdaNode( provider, node, source_ref ):
    defaults = buildNodeList( provider, node.args.defaults, source_ref )

    result = Nodes.CPythonExpressionLambdaBuilder(
        defaults   = defaults,
        source_ref = source_ref,
    )

    def delayedWork():
        real_provider = provider

        while real_provider.isExpressionClassBody():
            real_provider = real_provider.provider

        function_body = Nodes.CPythonExpressionFunctionBody(
            provider   = real_provider,
            name       = "lambda",
            doc        = None,
            parameters = buildParameterSpec( node ),
            source_ref = source_ref
        )

        result.setBody( function_body )

        body = buildNode(
            provider   = function_body,
            node       = node.body,
            source_ref = source_ref,
        )

        if function_body.isGenerator():
            body = CPythonStatementExpressionOnly(
                expression = Nodes.CPythonExpressionYield(
                    expression = body,
                    for_return = True,
                    source_ref = function_body.getSourceReference()
                ),
                source_ref = function_body.getSourceReference()
            )
        else:
            body = Nodes.CPythonStatementReturn(
                expression = body,
                source_ref = function_body.getSourceReference()
            )

        body = CPythonStatementsSequence(
            statements = ( body, ),
            source_ref = function_body.getSourceReference()
        )

        function_body.setBody( body )

    pushDelayedWork( delayedWork )

    return result

def buildForLoopNode( provider, node, source_ref ):
    return Nodes.CPythonStatementForLoop(
        source     = buildNode( provider, node.iter, source_ref ),
        target     = buildAssignTarget( provider, node.target, source_ref ),
        body       = buildLoopBodyNode( provider, node.body, source_ref ),
        no_break   = buildStatementsNode(
            provider   = provider,
            nodes      = node.orelse if node.orelse else None,
            source_ref = source_ref,
            allow_none = True
        ),
        source_ref = source_ref
    )

def buildWhileLoopNode( provider, node, source_ref ):
    return Nodes.CPythonStatementWhileLoop(
        condition  = buildNode( provider, node.test, source_ref ),
        body       = buildLoopBodyNode( provider, node.body, source_ref ),
        no_enter   = buildStatementsNode(
            provider   = provider,
            nodes      = node.orelse if node.orelse else None,
            source_ref = source_ref,
            allow_none = True
        ),
        source_ref = source_ref
    )


def buildFunctionCallNode( provider, node, source_ref ):
    positional_args = buildNodeList( provider, node.args, source_ref )

    # TODO: Clarify if the source_ref could be better
    pairs = [
        CPythonExpressionKeyValuePair(
            key        = _buildConstantReferenceNode(
                constant   = keyword.arg,
                source_ref = source_ref
            ),
            value      = buildNode( provider, keyword.value, source_ref ),
            source_ref = source_ref
        )
        for keyword in
        node.keywords
    ]

    return Nodes.CPythonExpressionFunctionCall(
        called_expression = buildNode( provider, node.func, source_ref ),
        positional_args   = positional_args,
        pairs             = pairs,
        list_star_arg     = buildNode( provider, node.starargs, source_ref, True ),
        dict_star_arg     = buildNode( provider, node.kwargs, source_ref, True ),
        source_ref        = source_ref,
    )

def buildSequenceCreationNode( provider, node, source_ref ):
    elements = buildNodeList( provider, node.elts, source_ref )

    for element in elements:
        if not element.isExpressionConstantRef() or element.isMutable():
            constant = False
            break
    else:
        constant = True

    sequence_kind = getKind( node ).upper()

    # TODO: This should happen in optimization instead.
    if constant:
        const_type = tuple if sequence_kind == "TUPLE" else list

        return _buildConstantReferenceNode(
            constant   = const_type( element.getConstant() for element in elements ),
            source_ref = source_ref
        )
    else:
        return CPythonExpressionMakeSequence(
            sequence_kind = sequence_kind,
            elements      = elements,
            source_ref    = source_ref
        )

def _areConstants( expressions ):
    for expression in expressions:
        if not expression.isExpressionConstantRef():
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

        constant = constant and key_node.isExpressionConstantRef()
        constant = constant and value_node.isExpressionConstantRef() and not value_node.isMutable()

    # TODO: Again, this is for optimization to do.
    if constant:
        # Create the dictionary in its full size, so that no growing occurs and the
        # constant becomes as similar as possible before being marshalled.
        constant_value = dict.fromkeys(
            [ key.getConstant() for key in keys ],
            None
        )

        for key, value in zip( keys, values ):
            constant_value[ key.getConstant() ] = value.getConstant()

        return _buildConstantReferenceNode(
            constant   = constant_value,
            source_ref = source_ref
        )
    else:
        return CPythonExpressionMakeDict(
            pairs      = [
                CPythonExpressionKeyValuePair( key, value, key.getSourceReference() )
                for key, value in
                zip( keys, values )
            ],
            source_ref = source_ref
        )

def buildSetNode( provider, node, source_ref ):
    values = buildNodeList( provider, node.elts, source_ref )

    constant = True

    for value in values:
        if not value.isExpressionConstantRef():
            constant = False
            break

    # TODO: Again, this is for optimization to do.
    if constant:
        constant_value = frozenset( value.getConstant() for value in values )

        return _buildConstantReferenceNode(
            constant   = constant_value,
            source_ref = source_ref
        )
    else:
        return CPythonExpressionMakeSet(
            values     = values,
            source_ref = source_ref
        )

def buildVariableRefAssignTarget( variable_name, source_ref ):
    return Nodes.CPythonAssignTargetVariable(
        variable_ref = _buildVariableReferenceNode(
            variable_name = variable_name,
            source_ref    = source_ref
        ),
        source_ref   = source_ref
    )

def buildAttributeAssignTarget( provider, attribute_name, value, source_ref ):
    assert type( attribute_name ) is str

    return Nodes.CPythonAssignTargetAttribute(
        expression      = buildNode( provider, value, source_ref ),
        attribute_name  = attribute_name,
        source_ref      = source_ref
    )

def buildSubscriptAssignTarget( provider, node, source_ref ):
    slice_kind = getKind( node.slice )

    if slice_kind == "Index":
        result = Nodes.CPythonAssignTargetSubscript(
            expression = buildNode( provider, node.value, source_ref ),
            subscript  = buildNode( provider, node.slice.value, source_ref ),
            source_ref = source_ref
        )
    elif slice_kind == "Slice":
        lower = buildNode( provider, node.slice.lower, source_ref, True )
        upper = buildNode( provider, node.slice.upper, source_ref, True )

        if node.slice.step is not None:
            step = buildNode( provider, node.slice.step, source_ref )

            result = Nodes.CPythonAssignTargetSubscript(
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
            result = Nodes.CPythonAssignTargetSlice(
                expression = buildNode( provider, node.value, source_ref ),
                lower      = lower,
                upper      = upper,
                source_ref = source_ref
            )
    elif slice_kind == "ExtSlice":
        result = Nodes.CPythonAssignTargetSubscript(
            expression = buildNode( provider, node.value, source_ref ),
            subscript  = _buildExtSliceNode( provider, node, source_ref ),
            source_ref = source_ref
        )
    elif slice_kind == "Ellipsis":
        result = Nodes.CPythonAssignTargetSubscript(
            expression = buildNode( provider, node.value, source_ref ),
            subscript  = _buildConstantReferenceNode(
                constant   = Ellipsis,
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    else:
        assert False, node.slice

    return result


def buildAssignTarget( provider, node, source_ref, allow_none = False ):
    if node is None and allow_none:
        return None

    if hasattr( node, "ctx" ):
        assert getKind( node.ctx ) in ( "Store", "Del" )

    kind = getKind( node )

    if type( node ) is str:
        # Python >= 3.x only
        result = buildVariableRefAssignTarget(
            variable_name = node,
            source_ref    = source_ref
        )
    elif kind == "Name":
        result = buildVariableRefAssignTarget(
            variable_name = node.id,
            source_ref    = source_ref
        )
    elif kind == "Attribute":
        result = buildAttributeAssignTarget(
            provider       = provider,
            value          = node.value,
            attribute_name = node.attr,
            source_ref     = source_ref
        )
    elif kind in ( "Tuple", "List" ):
        result = Nodes.CPythonAssignTargetTuple(
            elements   = buildAssignTargets( provider, node.elts, source_ref ),
            source_ref = source_ref
        )
    elif kind == "Subscript":
        result = buildSubscriptAssignTarget(
            provider   = provider,
            node       = node,
            source_ref = source_ref
        )
    else:
        assert False, ( source_ref, ast.dump( node ) )


    return result

def buildAssignTargets( provider, nodes, source_ref, allow_none = False ):
    return [ buildAssignTarget( provider, node, source_ref, allow_none ) for node in nodes ]

def buildAssignNode( provider, node, source_ref ):
    assert len( node.targets ) >= 1, source_ref

    # Evaluate the right hand side first, so it can get names provided
    # before the left hand side exists.
    expression = buildNode( provider, node.value, source_ref )

    # Only now the left hand side, so the right hand side is first.
    targets = buildAssignTargets( provider, node.targets, source_ref )

    return Nodes.CPythonStatementAssignment(
        targets    = targets,
        expression = expression,
        source_ref = source_ref
    )

def buildDeleteNode( provider, node, source_ref ):
    return Nodes.CPythonStatementAssignment(
        targets    = buildAssignTargets( provider, node.targets, source_ref ),
        expression = None,
        source_ref = source_ref
    )

def buildTargetsFromQuals( provider, target_owner, quals, source_ref ):
    assert len( quals ) >= 1

    targets = []

    for qual in quals:
        assert getKind( qual ) == "comprehension"

        targets.append(
            buildAssignTarget(
                provider   = provider,
                node       = qual.target,
                source_ref = source_ref
            )
        )

    target_owner.setTargets( targets )

def buildSourceFromQuals( provider, contraction_builder, quals, source_ref ):
    assert len( quals ) >= 1

    qual = quals[ 0 ]
    assert getKind( qual ) == "comprehension"

    contraction_builder.setSource0(
        buildNode(
            provider   = provider,
            node       = qual.iter,
            source_ref = source_ref
        )
    )

def buildBodyQuals( contraction_body, quals, source_ref ):
    assert len( quals ) >= 1

    qual_conditions = []
    qual_sources = []

    for count, qual in enumerate( quals ):
        assert getKind( qual ) == "comprehension"

        if qual.ifs:
            conditions = [
                buildNode(
                    provider   = contraction_body,
                    node       = condition,
                    source_ref = source_ref
                )
                for condition in
                qual.ifs
            ]

            if len( conditions ) == 1:
                condition = conditions[ 0 ]
            else:
                condition = Nodes.CPythonExpressionBoolAND(
                    operands   = conditions,
                    source_ref = source_ref
                )
        else:
            condition = _buildConstantReferenceNode(
                constant   = True,
                source_ref = source_ref
            )

        # Different for list contractions and generator expressions
        if count > 0:
            qual_sources.append(
                buildNode(
                    provider   = contraction_body,
                    node       = qual.iter,
                    source_ref = source_ref
                )
            )

        qual_conditions.append( condition )

    contraction_body.setSources( qual_sources )
    contraction_body.setConditions( qual_conditions )


def _buildContractionNode( provider, node, builder_class, body_class, list_contraction, source_ref ):
    assert provider.isParentVariableProvider(), provider

    result = builder_class(
        source_ref = source_ref
    )

    buildSourceFromQuals(
        provider            = provider,
        contraction_builder = result,
        quals               = node.generators,
        source_ref          = source_ref
    )

    def delayedWork():
        contraction_body = body_class(
            provider   = provider,
            source_ref = source_ref,
        )

        result.setBody( contraction_body )

        if hasattr( node, "elt" ):
            contraction_body.setBody(
                buildNode(
                    provider   = contraction_body,
                    node       = node.elt,
                    source_ref = source_ref
                )
            )
        else:
            key_node = buildNode(
                provider   = contraction_body,
                node       = node.key,
                source_ref = source_ref,
            )

            value_node = buildNode(
                provider   = contraction_body,
                node       = node.value,
                source_ref = source_ref,
            )

            contraction_body.setBody(
                CPythonExpressionKeyValuePair(
                    key        = key_node,
                    value      = value_node,
                    source_ref = source_ref
                )
            )

        buildTargetsFromQuals(
            provider     = provider if list_contraction else contraction_body,
            target_owner = contraction_body,
            quals        = node.generators,
            source_ref   = source_ref
        )

        buildBodyQuals(
            contraction_body = contraction_body,
            quals            = node.generators,
            source_ref       = source_ref
        )

        # The horror hereafter transforms the result into something else if a yield
        # expression was discovered. We take the lambda generator expression and convert
        # it to a lambda generator function, something that does not exist in CPython, but
        # for which we can generator code.
        if contraction_body.isExpressionGeneratorBody() and contraction_body.isGenerator():
            generator_function_body = Nodes.CPythonExpressionFunctionBody(
                provider   = provider,
                name       = "pseudo",
                doc        = None,
                parameters = ParameterSpec( ( "_iterated", ), None, None, 0 ),
                source_ref = source_ref
            )

            body = CPythonStatementExpressionOnly(
                expression = Nodes.CPythonExpressionYield(
                    expression = contraction_body.getBody(),
                    for_return = False,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )

            body = CPythonStatementsSequence(
                statements = ( body, ),
                source_ref = source_ref
            )

            sources = [
                CPythonExpressionVariableRef(
                    variable_name = "_iterated",
                    source_ref    = source_ref
                )
            ]
            sources += contraction_body.getSources()

            for target, source, condition in zip(
                contraction_body.getTargets(),
                sources,
                contraction_body.getConditions() ):

                body = Nodes.CPythonStatementConditional(
                    condition  = condition,
                    yes_branch = body,
                    no_branch  = None,
                    source_ref = source_ref
                )

                body = CPythonStatementsSequenceLoopBody(
                    statements = ( body, ),
                    source_ref = source_ref
                )

                body = Nodes.CPythonStatementForLoop(
                    source     = source,
                    target     = target,
                    body       = body,
                    no_break   = None,
                    source_ref = source_ref,
                )

                body = CPythonStatementsSequence(
                    statements = ( body, ),
                    source_ref = source_ref
                )

            generator_function_body.setBody( body )
            generator_function_body.markAsGenerator()

            new_result = Nodes.CPythonExpressionLambdaBuilder(
                defaults   = (),
                source_ref = source_ref,
            )
            new_result.setBody( generator_function_body )

            new_result = Nodes.CPythonExpressionFunctionCall(
                called_expression = new_result,
                positional_args   = ( result.getSource0(), ),
                pairs             = (),
                list_star_arg     = None,
                dict_star_arg     = None,
                source_ref        = source_ref
            )

            result.replaceWith( new_result )


    pushDelayedWork( delayedWork )

    return result

def buildListContractionNode( provider, node, source_ref ):
    return _buildContractionNode(
        provider         = provider,
        node             = node,
        builder_class    = Nodes.CPythonExpressionListContractionBuilder,
        body_class       = Nodes.CPythonExpressionListContractionBody,
        list_contraction = True,
        source_ref       = source_ref
    )

def buildSetContractionNode( provider, node, source_ref ):
    return _buildContractionNode(
        provider         = provider,
        node             = node,
        builder_class    = Nodes.CPythonExpressionSetContractionBuilder,
        body_class       = Nodes.CPythonExpressionSetContractionBody,
        list_contraction = False,
        source_ref       = source_ref
    )

def buildDictContractionNode( provider, node, source_ref ):
    return _buildContractionNode(
        provider         = provider,
        node             = node,
        builder_class    = Nodes.CPythonExpressionDictContractionBuilder,
        body_class       = Nodes.CPythonExpressionDictContractionBody,
        list_contraction = False,
        source_ref       = source_ref
    )

def buildGeneratorExpressionNode( provider, node, source_ref ):
    assert getKind( node ) == "GeneratorExp"

    return _buildContractionNode(
        provider         = provider,
        node             = node,
        builder_class    = Nodes.CPythonExpressionGeneratorBuilder,
        body_class       = Nodes.CPythonExpressionGeneratorBody,
        list_contraction = False,
        source_ref       = source_ref
    )

def buildComparisonNode( provider, node, source_ref ):
    comparison = [ buildNode( provider, node.left, source_ref ) ]

    assert len( node.comparators ) == len( node.ops )

    for comparator, operand in zip( node.ops, node.comparators ):
        comparison.append( getKind( comparator ) )
        comparison.append( buildNode( provider, operand, source_ref ) )

    return CPythonExpressionComparison(
        comparison = comparison,
        source_ref = source_ref
    )

def buildConditionNode( provider, node, source_ref ):
    return Nodes.CPythonStatementConditional(
        condition  = buildNode( provider, node.test, source_ref ),
        yes_branch = buildStatementsNode( provider, node.body, source_ref ),
        no_branch  = buildStatementsNode(
            provider   = provider,
            nodes      = node.orelse if node.orelse else None,
            source_ref = source_ref,
            allow_none = True
        ),
        source_ref = source_ref
    )

def buildTryExceptionNode( provider, node, source_ref ):
    handlers = []

    for handler in node.handlers:
        exception_expression, exception_assign, exception_block = handler.type, handler.name, handler.body

        handlers.append(
            Nodes.CPythonStatementExceptHandler(
                exception_type = buildNode( provider, exception_expression, source_ref, True ),
                target         = buildAssignTarget
                ( provider, exception_assign, source_ref, True ),
                body           = buildStatementsNode( provider, exception_block, source_ref ),
                source_ref     = source_ref
            )
        )

    return Nodes.CPythonStatementTryExcept(
        tried      = buildStatementsNode( provider, node.body, source_ref ),
        handlers   = handlers,
        no_raise   = buildStatementsNode( provider, node.orelse, source_ref, True ),
        source_ref = source_ref
    )

def buildTryFinallyNode( provider, node, source_ref ):
    return Nodes.CPythonStatementTryFinally(
        tried      = buildStatementsNode( provider, node.body, source_ref ),
        final      = buildStatementsNode( provider, node.finalbody, source_ref ),
        source_ref = source_ref
    )

_has_raise_value = Utils.getPythonVersion() < 300

def buildRaiseNode( provider, node, source_ref ):
    if _has_raise_value:
        return CPythonStatementRaiseException(
            exception_type  = buildNode( provider, node.type, source_ref, True ),
            exception_value = buildNode( provider, node.inst, source_ref, True ),
            exception_trace = buildNode( provider, node.tback, source_ref, True ),
            source_ref      = source_ref
        )
    else:
        assert node.cause is None

        return CPythonStatementRaiseException(
            exception_type  = buildNode( provider, node.exc, source_ref, True ),
            exception_value = None,
            exception_trace = None,
            source_ref      = source_ref
        )


def buildAssertNode( provider, node, source_ref ):
    # Underlying assumption:
    #
    # Assert x, y is the same as:
    # if not x:
    #     raise AssertionError, y
    #
    # Therefore assert statements are really just conditional statements with a static
    # raise contained.
    return Nodes.CPythonStatementConditional(
        condition = CPythonExpressionOperationNOT(
            operand    = buildNode( provider, node.test, source_ref ),
            source_ref = source_ref
        ),
        yes_branch = CPythonStatementsSequence(
            statements = (
                CPythonStatementRaiseException(
                    exception_type = CPythonExpressionBuiltinExceptionRef(
                        exception_name = "AssertionError",
                        source_ref     = source_ref
                    ),
                    exception_value = buildNode( provider, node.msg, source_ref, True ),
                    exception_trace = None,
                    source_ref      = source_ref
                ),
            ),
            source_ref = source_ref
        ),
        no_branch  = None,
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
            element = _buildConstantReferenceNode(
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

    return CPythonExpressionMakeSequence(
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
        return Nodes.CPythonExpressionSubscriptLookup(
            expression = buildNode( provider, node.value, source_ref ),
            subscript  = buildNode( provider, node.slice.value, source_ref ),
            source_ref = source_ref
        )
    elif kind == "Slice":
        lower = buildNode( provider, node.slice.lower, source_ref, True )
        upper = buildNode( provider, node.slice.upper, source_ref, True )

        if node.slice.step is not None:
            step = buildNode( provider, node.slice.step,  source_ref )

            return Nodes.CPythonExpressionSubscriptLookup(
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
        return Nodes.CPythonExpressionSubscriptLookup(
            expression = buildNode( provider, node.value, source_ref ),
            subscript  = _buildExtSliceNode( provider, node, source_ref ),
            source_ref = source_ref
        )
    elif kind == "Ellipsis":
        return Nodes.CPythonExpressionSubscriptLookup(
            expression = buildNode( provider, node.value, source_ref ),
            subscript  = _buildConstantReferenceNode(
                constant   = Ellipsis,
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    else:
        assert False, kind

def _buildImportModulesNode( import_names, source_ref ):
    import_nodes = []

    for import_desc in import_names:
        module_name, local_name = import_desc

        module_topname = module_name.split(".")[0]

        # If a name was given, use the one provided, otherwise the import gives the top
        # level package name given for assignment of the imported module.
        target = buildVariableRefAssignTarget(
            variable_name = local_name if local_name is not None else module_topname,
            source_ref    = source_ref
        )

        if local_name:
            import_node = CPythonExpressionImportModule(
                module_name = module_name,
                import_list = None,
                level       = -1, # TODO: Correct?!
                source_ref  = source_ref
            )

            for import_name in module_name.split(".")[1:]:
                import_node = CPythonExpressionImportName(
                    module      = import_node,
                    import_name = import_name,
                    source_ref  = source_ref
                )
        else:
            import_node = CPythonExpressionImportModule(
                module_name = module_name,
                import_list = None,
                level       = -1, # TODO: Correct?!
                source_ref  = source_ref
            )

        import_nodes.append(
            Nodes.CPythonStatementAssignment(
                targets    = ( target, ),
                expression = import_node,
                source_ref = source_ref
            )
        )

    # Note: Each import is sequential. It can succeed, and the failure of a later one is
    # not changing one. We can therefore have a sequence of imports that only import one
    # thing therefore.
    return CPythonStatementsSequence(
        statements = import_nodes,
        source_ref = source_ref
    )

def buildImportModulesNode( node, source_ref ):
    return _buildImportModulesNode(
        import_names   = [
            ( import_desc.name, import_desc.asname )
            for import_desc in
            node.names
        ],
        source_ref     = source_ref
    )

def enableFutureFeature( object_name, future_spec ):
    if object_name == "unicode_literals":
        future_spec.enableUnicodeLiterals()
    elif object_name == "absolute_import":
        future_spec.enableAbsoluteImport()
    elif object_name == "division":
        future_spec.enableFutureDivision()
    elif object_name == "print_function":
        future_spec.enableFuturePrint()
    elif object_name in ( "nested_scopes", "generators", "with_statement" ):
        pass
    else:
        warning( "Ignoring unkown future directive '%s'" % object_name )


def buildImportFromNode( provider, node, source_ref ):
    module_name = node.module if node.module is not None else ""
    level = node.level

    if module_name == "__future__":
        assert provider.isModule() or source_ref.isExecReference()

        for import_desc in node.names:
            object_name, _local_name = import_desc.name, import_desc.asname

            enableFutureFeature(
                object_name = object_name,
                future_spec = source_ref.getFutureSpec()
            )

    targets = []
    imports = []

    for import_desc in node.names:
        object_name, local_name = import_desc.name, import_desc.asname

        if object_name == "*":
            target = None
        else:
            target = buildVariableRefAssignTarget(
                variable_name = local_name if local_name is not None else object_name,
                source_ref = source_ref
            )

        targets.append( target )
        imports.append( object_name )

    if None in targets:
        return CPythonStatementImportStar(
            module_import = CPythonExpressionImportModule(
                module_name = module_name,
                import_list = ( "*", ),
                level       = level,
                source_ref  = source_ref
            ),
            source_ref  = source_ref
        )
    else:
        import_nodes = []

        for target, import_name in zip( targets, imports ):
            import_nodes.append(
                Nodes.CPythonStatementAssignment(
                    targets    = ( target, ),
                    expression = CPythonExpressionImportName(
                        module      = CPythonExpressionImportModule(
                            module_name = module_name,
                            import_list = imports,
                            level       = level,
                            source_ref  = source_ref
                        ),
                        import_name = import_name,
                        source_ref  = source_ref
                    ),
                    source_ref  = source_ref
                )
            )

        # Note: Each import is sequential. It can succeed, and the failure of a later one is
        # not changing one. We can therefore have a sequence of imports that only import one
        # thing therefore.
        return CPythonStatementsSequence(
            statements = import_nodes,
            source_ref = source_ref
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

    if locals_node is not None and locals_node.isExpressionConstantRef() and locals_node.getConstant() is None:
        locals_node = None

    if locals_node is None and globals_node is not None:
        if globals_node.isExpressionConstantRef() and globals_node.getConstant() is None:
            globals_node = None

    if provider.isExpressionFunctionBody():
        provider.markAsExecContaining()

    return Nodes.CPythonStatementExec(
        source_code = buildNode( provider, body, source_ref ),
        globals_arg = globals_node,
        locals_arg  = locals_node,
        source_ref  = source_ref
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

    return Nodes.CPythonStatementDeclareGlobal(
        variable_names = node.names,
        source_ref     = source_ref
    )


def buildStringNode( node, source_ref ):
    assert type( node.s ) in ( str, unicode )

    return _buildConstantReferenceNode(
        constant   = node.s,
        source_ref = source_ref
    )

def buildNumberNode( node, source_ref ):
    assert type( node.n ) in ( int, long, float, complex ), type( node.n )

    return _buildConstantReferenceNode(
        constant   = node.n,
        source_ref = source_ref
    )


def buildBoolOpNode( provider, node, source_ref ):
    bool_op = getKind( node.op )

    if bool_op == "Or":
        # The "or" may be short circuit and is therefore not a plain operation
        return Nodes.CPythonExpressionBoolOR(
            operands   = buildNodeList( provider, node.values, source_ref ),
            source_ref = source_ref
        )
    elif bool_op == "And":
        # The "and" may be short circuit and is therefore not a plain operation
        return Nodes.CPythonExpressionBoolAND(
            operands    = buildNodeList( provider, node.values, source_ref ),
            source_ref  = source_ref
        )
    elif bool_op == "Not":
        # The "not" is really only a unary operation and no special.
        return CPythonExpressionOperationNOT(
            operand    = buildNode( provider, node.operand, source_ref ),
            source_ref = source_ref
        )
    else:
        assert False, bool_op


def buildAttributeNode( provider, node, source_ref ):
    return Nodes.CPythonExpressionAttributeLookup(
        expression     = buildNode( provider, node.value, source_ref ),
        attribute_name = node.attr,
        source_ref     = source_ref
    )

def buildReturnNode( provider, node, source_ref ):
    if node.value is not None:
        return Nodes.CPythonStatementReturn(
            expression = buildNode( provider, node.value, source_ref ),
            source_ref = source_ref
        )
    else:
        return Nodes.CPythonStatementReturn(
            expression = _buildConstantReferenceNode(
                constant   = None,
                source_ref = source_ref
            ),
            source_ref = source_ref
        )


def buildYieldNode( provider, node, source_ref ):
    if provider.isModule():
        SyntaxErrors.raiseSyntaxError( "'yield' outside function", source_ref )

    provider.markAsGenerator()

    if node.value is not None:
        return Nodes.CPythonExpressionYield(
            expression = buildNode( provider, node.value, source_ref ),
            for_return = False,
            source_ref = source_ref
        )
    else:
        return Nodes.CPythonExpressionYield(
            expression = _buildConstantReferenceNode(
                constant   = None,
                source_ref = source_ref
            ),
            for_return = False,
            source_ref = source_ref
        )

def buildExprOnlyNode( provider, node, source_ref ):
    return CPythonStatementExpressionOnly(
        expression = buildNode( provider, node.value, source_ref ),
        source_ref = source_ref
    )


def buildUnaryOpNode( provider, node, source_ref ):
    if getKind( node.op ) == "Not":
        return buildBoolOpNode(
            provider   = provider,
            node       = node,
            source_ref = source_ref
        )
    else:
        return CPythonExpressionOperationUnary(
            operator   = getKind( node.op ),
            operand    = buildNode( provider, node.operand, source_ref ),
            source_ref = source_ref
        )


def buildBinaryOpNode( provider, node, source_ref ):
    operator = getKind( node.op )

    if operator == "Div" and source_ref.getFutureSpec().isFutureDivision():
        operator = "TrueDiv"

    return CPythonExpressionOperationBinary(
        operator   = operator,
        left       = buildNode( provider, node.left, source_ref ),
        right      = buildNode( provider, node.right, source_ref ),
        source_ref = source_ref
    )

def buildReprNode( provider, node, source_ref ):
    return CPythonExpressionOperationUnary(
        operator   = "Repr",
        operand    = buildNode( provider, node.value, source_ref ),
        source_ref = source_ref
    )

def buildInplaceAssignNode( provider, node, source_ref ):
    return Nodes.CPythonStatementAssignmentInplace(
        operator   = getKind( node.op ),
        target     = buildAssignTarget( provider, node.target, source_ref ),
        expression = buildNode( provider, node.value, source_ref ),
        source_ref = source_ref
    )

def buildConditionalExpressionNode( provider, node, source_ref ):
    return Nodes.CPythonExpressionConditional(
        condition      = buildNode( provider, node.test, source_ref ),
        yes_expression = buildNode( provider, node.body, source_ref ),
        no_expression  = buildNode( provider, node.orelse, source_ref ),
        source_ref     = source_ref
    )




_fast_path_args3 = {
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
    "Attribute"    : buildAttributeNode,
    "Return"       : buildReturnNode,
    "Yield"        : buildYieldNode,
    "Expr"         : buildExprOnlyNode,
    "UnaryOp"      : buildUnaryOpNode,
    "BinOp"        : buildBinaryOpNode,
    "Repr"         : buildReprNode,
    "AugAssign"    : buildInplaceAssignNode,
    "IfExp"        : buildConditionalExpressionNode,
}

_fast_path_args2 = {
    "Name"         : buildVariableReferenceNode,
    "Import"       : buildImportModulesNode,
    "Str"          : buildStringNode,
    "Num"          : buildNumberNode,
}

_fast_path_args1 = {
    "Continue" : Nodes.CPythonStatementContinueLoop,
    "Break"    : Nodes.CPythonStatementBreakLoop,
    "Pass"     : Nodes.CPythonStatementPass,
}

def buildNode( provider, node, source_ref, allow_none = False ):
    if node is None and allow_none:
        return None

    try:
        kind = getKind( node )

        source_ref = source_ref.atLineNumber( node.lineno )

        if kind in _fast_path_args3:
            result = _fast_path_args3[kind](
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind in _fast_path_args2:
            result = _fast_path_args2[kind](
                node       = node,
                source_ref = source_ref
            )
        elif kind in _fast_path_args1:
            result = _fast_path_args1[kind](
                source_ref = source_ref
            )
        else:
            assert False, kind

        assert isinstance( result, Nodes.CPythonNodeBase )

        return result
    except SyntaxError:
        raise
    except:
        warning( "Problem at '%s' with %s." % ( source_ref, ast.dump( node ) ) )
        raise

def _extractDocFromBody( node ):
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

    body, doc = _extractDocFromBody( body )

    result = buildStatementsNode(
        provider   = provider,
        nodes      = body,
        source_ref = source_ref
    )

    # TODO: The handling of doc strings should be done in an early optimization step that
    # handles this.
    if not replacement:
        provider.setDoc( doc )
        provider.setBody( result )

    while _delayed_works:
        delayed_work = _delayed_works.pop()

        delayed_work()

    return result

def buildReplacementTree( provider, source_code, source_ref ):
    return buildParseTree(
        provider    = provider,
        source_code = source_code,
        source_ref  = source_ref,
        replacement = True
    )

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
    elif Utils.isDir( filename ) and Utils.joinpath( filename, "__init__.py" ):
        source_filename = Utils.joinpath( filename, "__init__.py" )

        source_ref = SourceCodeReferences.fromFilename(
            filename    = Utils.abspath( source_filename ),
            future_spec = FutureSpec()
        )

        result = Nodes.CPythonPackage(
            name       = Utils.basename( filename ),
            package    = package,
            source_ref = source_ref
        )
    else:
        sys.stderr.write(  "Nuitka: can't open file '%s'.\n" % filename )
        sys.exit( 2 )

    buildParseTree(
        provider    = result,
        source_code = open( source_filename, "rU" ).read(),
        source_ref  = source_ref,
        replacement = False,
    )

    return result
