#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
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
    Options,
    Tracing,
    Utils
)

from .nodes.NodeBases import CPythonClosureGiverNodeBase

from .nodes.ParameterSpec import ParameterSpec
from .nodes.FutureSpec import FutureSpec

from .nodes.NodeBases import CPythonNodeBase
from .nodes.VariableRefNode import (
    CPythonExpressionTargetVariableRef,
    CPythonExpressionVariableRef,
    CPythonExpressionTempVariableRef,
    CPythonStatementTempBlock
)
from .nodes.ConstantRefNode import CPythonExpressionConstantRef
from .nodes.BuiltinReferenceNodes import (
    CPythonExpressionBuiltinExceptionRef,
    CPythonExpressionBuiltinRef
)
from .nodes.BuiltinIteratorNodes import (
    CPythonStatementSpecialUnpackCheck,
    CPythonExpressionSpecialUnpack,
    CPythonExpressionBuiltinNext1,
    CPythonExpressionBuiltinIter1,
)
from .nodes.BoolNodes import (
    CPythonExpressionBoolAND,
    CPythonExpressionBoolOR
)

from .nodes.ExceptionNodes import (
    CPythonExpressionCaughtExceptionTracebackRef,
    CPythonExpressionCaughtExceptionValueRef,
    CPythonExpressionCaughtExceptionTypeRef,
    CPythonExpressionBuiltinMakeException,
    CPythonStatementRaiseException
)
from .nodes.ComparisonNode import CPythonExpressionComparison
from .nodes.ExecEvalNodes import CPythonStatementExec
from .nodes.CallNode import CPythonExpressionCall
from .nodes.AttributeNode import (
    CPythonExpressionSpecialAttributeLookup,
    CPythonExpressionAttributeLookup
)
from .nodes.SubscriptNode import CPythonExpressionSubscriptLookup
from .nodes.SliceNodes import (
    CPythonExpressionSliceLookup,
    CPythonExpressionSliceObject
)

from .nodes.FunctionNodes import (
    CPythonExpressionFunctionBodyDefaulted,
    CPythonExpressionFunctionBody,
    CPythonExpressionFunctionCall
)
from .nodes.ClassNodes import CPythonExpressionClassCreation

from .nodes.ContainerMakingNodes import (
    CPythonExpressionKeyValuePair,
    CPythonExpressionMakeTuple,
    CPythonExpressionMakeList,
    CPythonExpressionMakeDict,
    CPythonExpressionMakeSet
)
from .nodes.ContainerOperationNodes import (
    CPythonExpressionListOperationAppend,
    CPythonExpressionDictOperationSet,
    CPythonExpressionSetOperationAdd
)

from .nodes.StatementNodes import (
    CPythonStatementExpressionOnly,
    CPythonStatementsSequence,
    CPythonStatementsFrame,
    mergeStatements
)
from .nodes.ImportNodes import (
    CPythonExpressionImportModule,
    CPythonExpressionImportName,
    CPythonStatementImportStar,
)
from .nodes.OperatorNodes import (
    CPythonExpressionOperationBinaryInplace,
    CPythonExpressionOperationBinary,
    CPythonExpressionOperationUnary,
    CPythonExpressionOperationNOT
)
from .nodes.LoopNodes import (
    CPythonStatementContinueLoop,
    CPythonStatementBreakLoop,
    CPythonStatementLoop
)
from .nodes.ConditionalNodes import (
    CPythonExpressionConditional,
    CPythonStatementConditional
)
from .nodes.YieldNode import CPythonExpressionYield
from .nodes.ReturnNode import CPythonStatementReturn
from .nodes.AssignNodes import (
    CPythonStatementAssignmentVariable,
    CPythonStatementAssignmentAttribute,
    CPythonStatementAssignmentSubscript,
    CPythonStatementAssignmentSlice,
    CPythonStatementDelAttribute,
    CPythonStatementDelSubscript,
    CPythonStatementDelVariable,
    CPythonStatementDelSlice,
)
from .nodes.KeeperNodes import (
    CPythonExpressionAssignmentTempKeeper,
    CPythonExpressionTempKeeperRef
)
from .nodes.PrintNodes import CPythonStatementPrint
from .nodes.ModuleNodes import (
    CPythonPackage,
    CPythonModule
)
from .nodes.TryNodes import (
    CPythonStatementExceptHandler,
    CPythonStatementTryFinally,
    CPythonStatementTryExcept
)
from .nodes.GlobalsLocalsNodes import CPythonExpressionBuiltinLocals

import ast, sys, re

from logging import warning

def dump( node ):
    Tracing.printLine( ast.dump( node ) )

def getKind( node ):
    return node.__class__.__name__.split( "." )[-1]

def buildVariableReferenceNode( provider, node, source_ref ):
    if Utils.python_version >= 300 and node.id == "super" and provider.isExpressionFunctionBody():
        provider.markAsClassClosureTaker()

    return CPythonExpressionVariableRef(
        variable_name = node.id,
        source_ref    = source_ref
    )

def buildStatementsNode( provider, nodes, source_ref, frame = False ):
    if nodes is None:
        return None

    statements = buildNodeList( provider, nodes, source_ref, True )
    statements = mergeStatements( statements )

    if not statements:
        return None

    if frame:
        return CPythonStatementsFrame(
            statements = statements,
            arg_names  = provider.getParameters().getCoArgNames(),
            code_name  = provider.getFunctionName(),
            source_ref = source_ref
        )
    else:
        return CPythonStatementsSequence(
            statements = statements,
            source_ref = source_ref
        )

make_class_parameters = ParameterSpec(
    name          = "class",
    normal_args   = (),
    list_star_arg = None,
    dict_star_arg = None,
    default_count = 0
)

def buildClassNode( provider, node, source_ref ):
    assert getKind( node ) == "ClassDef"

    class_statements, class_doc = _extractDocFromBody( node )

    decorators = buildNodeList( provider, reversed( node.decorator_list ), source_ref )
    bases = buildNodeList( provider, node.bases, source_ref )

    if Utils.python_version >= 300:
        if len( node.keywords ) == 1:
            assert len( node.keywords ) == 1, node.keywords
            assert node.keywords[0].arg == "metaclass", node.keywords[0].arg
            metaclass = buildNode( provider, node.keywords[0].value, source_ref )
        elif not node.keywords:
            metaclass = None
        else:
            assert False, node.keywords
    else:
        # TODO: May be detected during compile time, but Python2 syntax does't
        # make it as easy.
        metaclass = None

    class_dict_function = CPythonExpressionFunctionBody(
        provider   = provider,
        is_class   = True,
        parameters = make_class_parameters,
        name       = node.name,
        doc        = class_doc,
        source_ref = source_ref
    )

    body = buildStatementsNode(
        provider   = class_dict_function,
        nodes      = class_statements,
        frame      = True,
        source_ref = source_ref
    )

    if body is not None:
        # The frame guard has nothing to tell its line number to.
        body.source_ref = source_ref.atInternal()

    # The class body is basically a function that implicitely, at the end returns its
    # locals and cannot have other return statements contained.
    body = _makeStatementsSequence(
        statements = (
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTargetVariableRef(
                    variable_name = "__module__",
                    source_ref    = source_ref
                ),
                source        = CPythonExpressionConstantRef(
                    constant   = provider.getParentModule().getName(),
                    source_ref = source_ref
                ),
                source_ref   = source_ref.atInternal()
            ),
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTargetVariableRef(
                    variable_name = "__doc__",
                    source_ref    = source_ref
                ),
                source        = CPythonExpressionConstantRef(
                    constant   = class_doc,
                    source_ref = source_ref
                ),
                source_ref   = source_ref.atInternal()
            ),
            body,
            CPythonStatementReturn(
                expression = CPythonExpressionBuiltinLocals(
                    source_ref = source_ref
                ),
                source_ref = source_ref.atInternal()
            )
        ),
        allow_none = True,
        source_ref = source_ref
    )

    # The class body is basically a function that implicitely, at the end returns its
    # locals and cannot have other return statements contained.

    class_dict_function.setBody( body )

    class_dict = CPythonExpressionFunctionCall(
        function_body = class_dict_function,
        values        = (),
        source_ref    = source_ref
    )

    decorated_body = CPythonExpressionClassCreation(
        class_name = node.name,
        bases      = bases,
        metaclass  = metaclass,
        class_dict = class_dict,
        source_ref = source_ref
    )

    for decorator in decorators:
        decorated_body = CPythonExpressionCall(
            called          = decorator,
            positional_args = ( decorated_body, ),
            pairs           = (),
            list_star_arg   = None,
            dict_star_arg   = None,
            source_ref      = decorator.getSourceReference()
        )

    return CPythonStatementAssignmentVariable(
        variable_ref = CPythonExpressionTargetVariableRef(
            variable_name = node.name,
            source_ref    = source_ref
        ),
        source     = decorated_body,
        source_ref = source_ref
    )

def buildParameterSpec( name, node, source_ref ):
    kind = getKind( node )

    assert kind in ( "FunctionDef", "Lambda" ), "unsupported for kind " + kind

    def extractArg( arg ):
        if getKind( arg ) == "Name":
            return arg.id
        elif getKind( arg ) == "arg":
            assert arg.annotation is None

            return arg.arg
        elif getKind( arg ) == "Tuple":
            return tuple( extractArg( arg ) for arg in arg.elts )
        else:
            assert False, getKind( arg )

    argnames = [ extractArg( arg ) for arg in node.args.args ]

    kwargs = node.args.kwarg
    varargs = node.args.vararg

    result = ParameterSpec(
        name           = name,
        normal_args    = argnames,
        list_star_arg  = varargs,
        dict_star_arg  = kwargs,
        default_count  = len( node.args.defaults )
    )

    message = result.checkValid()

    if message is not None:
        SyntaxErrors.raiseSyntaxError(
            message,
            source_ref
        )

    return result

def buildFunctionNode( provider, node, source_ref ):
    assert getKind( node ) == "FunctionDef"

    function_statements, function_doc = _extractDocFromBody( node )

    decorators = buildNodeList( provider, reversed( node.decorator_list ), source_ref )
    defaults = buildNodeList( provider, node.args.defaults, source_ref )

    real_provider = provider

    while real_provider.isExpressionFunctionBody() and real_provider.isClassDictCreation():
        real_provider = real_provider.provider

    function_body = CPythonExpressionFunctionBody(
        provider   = real_provider,
        name       = node.name,
        doc        = function_doc,
        parameters = buildParameterSpec( node.name, node, source_ref ),
        source_ref = source_ref
    )

    function_statements_body = buildStatementsNode(
        provider   = function_body,
        nodes      = function_statements,
        frame      = True,
        source_ref = source_ref
    )

    function_body.setBody( function_statements_body )

    if defaults:
        decorated_body = CPythonExpressionFunctionBodyDefaulted(
            function_body = function_body,
            defaults      = defaults,
            source_ref    = source_ref
        )
    else:
        decorated_body = function_body

    for decorator in decorators:
        decorated_body = CPythonExpressionCall(
            called          = decorator,
            positional_args = ( decorated_body, ),
            pairs           = (),
            list_star_arg   = None,
            dict_star_arg   = None,
            source_ref      = decorator.getSourceReference()
        )

    # Add the staticmethod decorator to __new__ methods if not provided.

    # CPython made these optional, but applies them to every class __new__. We better add
    # them early, so our analysis will see it
    if node.name == "__new__" and not decorators and provider.isExpressionFunctionBody() and provider.isClassDictCreation():
        decorated_body = CPythonExpressionCall(
            called          = CPythonExpressionBuiltinRef(
                builtin_name = "staticmethod",
                source_ref   = source_ref
            ),
            positional_args = ( decorated_body, ),
            pairs           = (),
            list_star_arg   = None,
            dict_star_arg   = None,
            source_ref      = source_ref,
        )

    return CPythonStatementAssignmentVariable(
        variable_ref = CPythonExpressionTargetVariableRef(
            variable_name = node.name,
            source_ref    = source_ref
        ),
        source       = decorated_body,
        source_ref   = source_ref
    )

def buildLambdaNode( provider, node, source_ref ):
    assert getKind( node ) == "Lambda"

    defaults = buildNodeList( provider, node.args.defaults, source_ref )

    real_provider = provider

    while real_provider.isExpressionFunctionBody() and real_provider.isClassDictCreation():
        real_provider = real_provider.provider

    result = CPythonExpressionFunctionBody(
        provider   = real_provider,
        name       = "<lambda>",
        doc        = None,
        parameters = buildParameterSpec( "<lambda>", node, source_ref ),
        source_ref = source_ref,
    )

    body = buildNode(
        provider   = result,
        node       = node.body,
        source_ref = source_ref,
    )

    if result.isGenerator():
        body = CPythonStatementExpressionOnly(
            expression = CPythonExpressionYield(
                expression = body,
                for_return = True,
                source_ref = body.getSourceReference()
            ),
            source_ref = body.getSourceReference()
        )
    else:
        body = CPythonStatementReturn(
            expression = body,
            source_ref = body.getSourceReference()
        )

    body = CPythonStatementsFrame(
        statements = ( body, ),
        arg_names  = result.getParameters().getCoArgNames(),
        code_name  = "<lambda>",
        source_ref = body.getSourceReference()
    )

    result.setBody( body )

    if defaults:
        result = CPythonExpressionFunctionBodyDefaulted(
            function_body = result,
            defaults      = defaults,
            source_ref    = source_ref
        )

    return result

def buildForLoopNode( provider, node, source_ref ):
    source = buildNode( provider, node.iter, source_ref )

    result = CPythonStatementTempBlock(
        source_ref = source_ref
    )

    tmp_iter_variable = result.getTempVariable( "for_iterator" )

    iterate_tmp_block = CPythonStatementTempBlock(
        source_ref = source_ref
    )

    tmp_value_variable = iterate_tmp_block.getTempVariable( "iter_value" )

    else_block = buildStatementsNode(
        provider   = provider,
        nodes      = node.orelse if node.orelse else None,
        source_ref = source_ref
    )

    if else_block is not None:
        tmp_break_indicator_variable = result.getTempVariable( "break_indicator" )

        statements = [
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTempVariableRef(
                    variable   = tmp_break_indicator_variable.makeReference( result ),
                    source_ref = source_ref
                ),
                source     = CPythonExpressionConstantRef(
                    constant   = True,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        ]
    else:
        statements = []

    statements.append(
        CPythonStatementBreakLoop(
            source_ref = source_ref.atInternal()
        )
    )

    handler_body = _makeStatementsSequence(
        statements = statements,
        allow_none = True,
        source_ref = source_ref
    )


    statements = (
        CPythonStatementTryExcept(
            tried      = CPythonStatementsSequence(
                statements = (
                    CPythonStatementAssignmentVariable(
                        variable_ref = CPythonExpressionTempVariableRef(
                            variable   = tmp_value_variable.makeReference( iterate_tmp_block ),
                            source_ref = source_ref
                        ),
                        source     = CPythonExpressionBuiltinNext1(
                            value      = CPythonExpressionTempVariableRef(
                                variable   = tmp_iter_variable.makeReference( result ),
                                source_ref = source_ref
                            ),
                            source_ref = source_ref
                        ),
                        source_ref = source_ref
                    ),
                ),
                source_ref = source_ref
            ),
            handlers   = (
                CPythonStatementExceptHandler(
                    exception_types = (
                        CPythonExpressionBuiltinExceptionRef(
                            exception_name = "StopIteration",
                            source_ref     = source_ref
                        ),
                    ),
                    body           = handler_body,
                    source_ref     = source_ref
                ),
            ),
            source_ref = source_ref
        ),
        buildAssignmentStatements(
            provider   = provider,
            node       = node.target,
            source     = CPythonExpressionTempVariableRef(
                variable   = tmp_value_variable.makeReference( iterate_tmp_block ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    iterate_tmp_block.setBody(
        CPythonStatementsSequence(
            statements = statements,
            source_ref = source_ref
        )
    )

    statements = (
        iterate_tmp_block,
        buildStatementsNode(
            provider   = provider,
            nodes      = node.body,
            source_ref = source_ref
        )
    )

    loop_body = _makeStatementsSequence(
        statements = statements,
        allow_none = True,
        source_ref = source_ref
    )

    if else_block is not None:
        statements = [
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTempVariableRef(
                    variable   = tmp_break_indicator_variable.makeReference( result ),
                    source_ref = source_ref
                ),
                source     = CPythonExpressionConstantRef(
                    constant = False,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        ]
    else:
        statements = []

    statements += [
        # First create the iterator and store it.
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_iter_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source     = CPythonExpressionBuiltinIter1(
                value       = source,
                source_ref  = source.getSourceReference()
            ),
            source_ref = source_ref
        ),
        CPythonStatementLoop(
            body       = loop_body,
            source_ref = source_ref
        )
    ]

    if else_block is not None:
        statements += [
            CPythonStatementConditional(
                condition  = CPythonExpressionComparison(
                    left = CPythonExpressionTempVariableRef(
                        variable   = tmp_break_indicator_variable.makeReference( result ),
                        source_ref = source_ref
                    ),
                    right = CPythonExpressionConstantRef(
                        constant   = True,
                        source_ref = source_ref
                    ),
                    comparator = "Is",
                    source_ref = source_ref
                ),
                yes_branch = else_block,
                no_branch  = None,
                source_ref = source_ref
            )
        ]

    result.setBody(
        CPythonStatementsSequence(
            statements = statements,
            source_ref = source_ref
        )
    )

    return result

def buildWhileLoopNode( provider, node, source_ref ):
    else_block = buildStatementsNode(
        provider   = provider,
        nodes      = node.orelse if node.orelse else None,
        source_ref = source_ref
    )

    if else_block is not None:
        temp_block = CPythonStatementTempBlock(
            source_ref = source_ref
        )

        tmp_break_indicator_variable = temp_block.getTempVariable( "break_indicator" )

        statements = (
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTempVariableRef(
                    variable   = tmp_break_indicator_variable.makeReference( temp_block ),
                    source_ref = source_ref
                ),
                source     = CPythonExpressionConstantRef(
                    constant   = True,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            CPythonStatementBreakLoop(
                source_ref = source_ref
            )
        )
    else:
        statements = (
            CPythonStatementBreakLoop(
                source_ref = source_ref
            ),
        )

    # The loop body contains a conditional statement at the start that breaks the loop if
    # it fails.
    loop_body = _makeStatementsSequence(
        statements = (
            CPythonStatementConditional(
                condition = buildNode( provider, node.test, source_ref ),
                no_branch = CPythonStatementsSequence(
                    statements = statements,
                    source_ref = source_ref
                ),
                yes_branch = None,
                source_ref = source_ref
            ),
            buildStatementsNode(
                provider   = provider,
                nodes      = node.body,
                source_ref = source_ref
            )
        ),
        allow_none = True,
        source_ref = source_ref
    )

    loop_statement = CPythonStatementLoop(
        body       = loop_body,
        source_ref = source_ref
    )

    if else_block is None:
        return loop_statement
    else:
        statements = (
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTempVariableRef(
                    variable   = tmp_break_indicator_variable.makeReference( temp_block ),
                    source_ref = source_ref
                ),
                source = CPythonExpressionConstantRef(
                    constant   = False,
                    source_ref = source_ref
                ),
                source_ref   = source_ref
            ),
            loop_statement,
            CPythonStatementConditional(
                condition  = CPythonExpressionComparison(
                    left = CPythonExpressionTempVariableRef(
                        variable   = tmp_break_indicator_variable.makeReference( temp_block ),
                        source_ref = source_ref
                    ),
                    right = CPythonExpressionConstantRef(
                        constant   = True,
                        source_ref = source_ref
                    ),
                    comparator = "Is",
                    source_ref = source_ref
                ),
                yes_branch = else_block,
                no_branch  = None,
                source_ref = source_ref
            )
        )

        temp_block.setBody(
            CPythonStatementsSequence(
               statements = statements,
               source_ref = source_ref
            )
        )

        return temp_block

def buildCallNode( provider, node, source_ref ):
    positional_args = buildNodeList( provider, node.args, source_ref )

    # Only the values of keyword pairs have a real source ref, and those only really
    # matter, so that makes sense.
    pairs = [
        CPythonExpressionKeyValuePair(
            key        = CPythonExpressionConstantRef(
                constant   = keyword.arg,
                source_ref = source_ref
            ),
            value      = buildNode( provider, keyword.value, source_ref ),
            source_ref = source_ref
        )
        for keyword in
        node.keywords
    ]

    return CPythonExpressionCall(
        called          = buildNode( provider, node.func, source_ref ),
        positional_args = positional_args,
        pairs           = pairs,
        list_star_arg   = buildNode( provider, node.starargs, source_ref, True ),
        dict_star_arg   = buildNode( provider, node.kwargs, source_ref, True ),
        source_ref      = source_ref,
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

    # Note: This would happen in optimization instead, but lets just do it immediately to
    # save some time.
    if constant:
        if sequence_kind == "TUPLE":
            const_type = tuple
        elif sequence_kind == "LIST":
            const_type = list
        elif sequence_kind == "SET":
            const_type = set
        else:
            assert False, sequence_kind

        return CPythonExpressionConstantRef(
            constant   = const_type( element.getConstant() for element in elements ),
            source_ref = source_ref
        )
    else:
        if sequence_kind == "TUPLE":
            return CPythonExpressionMakeTuple(
                elements      = elements,
                source_ref    = source_ref
            )
        elif sequence_kind == "LIST":
            return CPythonExpressionMakeList(
                elements      = elements,
                source_ref    = source_ref
            )
        elif sequence_kind == "SET":
            return CPythonExpressionMakeSet(
                elements      = elements,
                source_ref    = source_ref
            )
        else:
            assert False, sequence_kind


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

    # Note: This would happen in optimization instead, but lets just do it immediately to
    # save some time.
    if constant:
        # Create the dictionary in its full size, so that no growing occurs and the
        # constant becomes as similar as possible before being marshalled.
        constant_value = dict.fromkeys(
            [ key.getConstant() for key in keys ],
            None
        )

        for key, value in zip( keys, values ):
            constant_value[ key.getConstant() ] = value.getConstant()

        return CPythonExpressionConstantRef(
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

def buildAssignmentStatementsFromDecoded( provider, kind, detail, source, source_ref ):
    # This is using many variable names on purpose, so as to give names to the unpacked
    # detail values, pylint: disable=R0914

    if kind == "Name":
        variable_ref = detail

        return CPythonStatementAssignmentVariable(
            variable_ref = variable_ref,
            source       = source,
            source_ref   = source_ref
        )
    elif kind == "Attribute":
        lookup_source, attribute_name = detail

        return CPythonStatementAssignmentAttribute(
            expression     = lookup_source,
            attribute_name = attribute_name,
            source     = source,
            source_ref = source_ref
        )
    elif kind == "Subscript":
        subscribed, subscript = detail

        return CPythonStatementAssignmentSubscript(
            expression = subscribed,
            subscript  = subscript,
            source     = source,
            source_ref = source_ref
        )
    elif kind == "Slice":
        lookup_source, lower, upper = detail

        return CPythonStatementAssignmentSlice(
            expression = lookup_source,
            lower      = lower,
            upper      = upper,
            source     = source,
            source_ref = source_ref
        )
    elif kind == "Tuple":
        result = CPythonStatementTempBlock(
            source_ref = source_ref
        )

        source_iter_var = result.getTempVariable( "source_iter" )

        statements = [
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTempVariableRef(
                    variable   = source_iter_var.makeReference( result ),
                    source_ref = source_ref
                ),
                source = CPythonExpressionBuiltinIter1(
                    value      = source,
                    source_ref = source_ref
                ),
                source_ref   = source_ref
            )
        ]

        element_vars = [
            result.getTempVariable( "element_%d" % ( element_index + 1 ) )
            for element_index in
            range( len( detail ) )
        ]

        for element_index in range( len( detail ) ):
            statements.append(
                CPythonStatementAssignmentVariable(
                    variable_ref = CPythonExpressionTempVariableRef(
                        variable   = element_vars[ element_index ].makeReference( result ),
                        source_ref = source_ref
                    ),
                    source = CPythonExpressionSpecialUnpack(
                        value      = CPythonExpressionTempVariableRef(
                            variable   = source_iter_var.makeReference( result ),
                            source_ref = source_ref
                        ),
                        count      = element_index + 1,
                        source_ref = source_ref
                    ),
                    source_ref   = source_ref
                )
            )

        statements.append(
            CPythonStatementSpecialUnpackCheck(
                iterator   = CPythonExpressionTempVariableRef(
                    variable   = source_iter_var.makeReference( result ),
                    source_ref = source_ref
                ),
                count      = len( detail ),
                source_ref = source_ref
            )
        )

        for element_index, element in enumerate( detail ):
            statements.append(
                buildAssignmentStatementsFromDecoded(
                    provider   = provider,
                    kind       = element[0],
                    detail     = element[1],
                    source     = CPythonExpressionTempVariableRef(
                        variable   = element_vars[ element_index ].makeReference( result ),
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                )
            )

        result.setBody(
            CPythonStatementsSequence(
               statements = statements,
               source_ref = source_ref
            )
        )

        return result
    else:
        assert False, ( kind, source_ref, detail )

    return result

def buildAssignmentStatements( provider, node, source, source_ref, allow_none = False ):
    if node is None and allow_none:
        return None

    kind, detail = decodeAssignTarget( provider, node, source_ref )

    return buildAssignmentStatementsFromDecoded(
        provider   = provider,
        kind       = kind,
        detail     = detail,
        source     = source,
        source_ref = source_ref
    )

def decodeAssignTarget( provider, node, source_ref, allow_none = False ):
    # Many cases to deal with, because of the different assign targets,
    # pylint: disable=R0911,R0912

    if node is None and allow_none:
        return None

    if hasattr( node, "ctx" ):
        assert getKind( node.ctx ) in ( "Store", "Del" )

    kind = getKind( node )

    if type( node ) is str:
        return "Name", CPythonExpressionTargetVariableRef(
            variable_name = node,
            source_ref    = source_ref
        )
    elif kind == "Name":
        return kind, CPythonExpressionTargetVariableRef(
            variable_name = node.id,
            source_ref    = source_ref
        )
    elif kind == "Attribute":
        return kind, (
            buildNode( provider, node.value, source_ref ),
            node.attr
        )
    elif kind == "Subscript":
        slice_kind = getKind( node.slice )

        if slice_kind == "Index":
            return "Subscript", (
                buildNode( provider, node.value, source_ref ),
                buildNode( provider, node.slice.value, source_ref )
            )
        elif slice_kind == "Slice":
            lower = buildNode( provider, node.slice.lower, source_ref, True )
            upper = buildNode( provider, node.slice.upper, source_ref, True )

            if node.slice.step is not None:
                step = buildNode( provider, node.slice.step, source_ref )

                return "Subscript", (
                    buildNode( provider, node.value, source_ref ),
                    CPythonExpressionSliceObject(
                        lower      = lower,
                        upper      = upper,
                        step       = step,
                        source_ref = source_ref
                    )
                )
            else:
                return "Slice", (
                    buildNode( provider, node.value, source_ref ),
                    lower,
                    upper
                )
        elif slice_kind == "ExtSlice":
            return "Subscript", (
                buildNode( provider, node.value, source_ref ),
                _buildExtSliceNode( provider, node, source_ref )
            )
        elif slice_kind == "Ellipsis":
            return "Subscript", (
                buildNode( provider, node.value, source_ref ),
                CPythonExpressionConstantRef(
                    constant   = Ellipsis,
                    source_ref = source_ref
                )
            )
        else:
            assert False, slice_kind
    elif kind in ( "Tuple", "List" ):
        return "Tuple", tuple(
            decodeAssignTarget( provider, sub_node, source_ref, False )
            for sub_node in
            node.elts
        )
    else:
        assert False, ( source_ref, kind )

def buildAssignNode( provider, node, source_ref ):
    assert len( node.targets ) >= 1, source_ref

    # Evaluate the right hand side first, so it can get names provided
    # before the left hand side exists.
    source = buildNode( provider, node.value, source_ref )

    if len( node.targets ) == 1:
        return buildAssignmentStatements(
            provider   = provider,
            node       = node.targets[0],
            source     = source,
            source_ref = source_ref
        )
    else:
        result = CPythonStatementTempBlock(
            source_ref = source_ref
        )

        tmp_source = result.getTempVariable( "assign_source" )

        statements = [
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTempVariableRef(
                    variable   = tmp_source.makeReference( result ),
                    source_ref = source_ref
                ),
                source     = source,
                source_ref = source_ref
            )
        ]

        for target in node.targets:
            statements.append(
                buildAssignmentStatements(
                    provider   = provider,
                    node       = target,
                    source     = CPythonExpressionTempVariableRef(
                        variable   = tmp_source.makeReference( result ),
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                )
            )

        result.setBody(
            CPythonStatementsSequence(
                statements = statements,
                source_ref = source_ref
            )
        )

        return result

def buildDeleteNode( provider, node, source_ref ):
    # Note: Each delete is sequential. It can succeed, and the failure of a later one does
    # not prevent the former to succeed. We can therefore have a sequence of del
    # statements that each only delete one thing therefore.

    statements = []

    def handleTarget( kind, detail ):
        if kind == "Name":
            variable_ref = detail

            statements.append(
                CPythonStatementDelVariable(
                    variable_ref = variable_ref,
                    source_ref   = source_ref
                )
            )
        elif kind == "Attribute":
            lookup_source, attribute_name = detail

            statements.append(
                CPythonStatementDelAttribute(
                    expression     = lookup_source,
                    attribute_name = attribute_name,
                    source_ref     = source_ref
                )
            )
        elif kind == "Subscript":
            subscribed, subscript = detail

            statements.append(
                CPythonStatementDelSubscript(
                    expression = subscribed,
                    subscript  = subscript,
                    source_ref = source_ref
                )
            )
        elif kind == "Slice":
            lookup_source, lower, upper = detail

            statements.append(
                CPythonStatementDelSlice(
                    expression = lookup_source,
                    lower      = lower,
                    upper      = upper,
                    source_ref = source_ref
                )
            )
        elif kind == "Tuple":
            for sub_node in detail:
                handleTarget( sub_node[0], sub_node[1] )
        else:
            assert False, ( source_ref, ast.dump( node ) )

    for target in node.targets:
        kind, detail = decodeAssignTarget( provider, target, source_ref )

        handleTarget( kind, detail )

    return _makeStatementsSequenceOrStatement(
        statements = statements,
        source_ref = source_ref
    )

make_contraction_parameters = ParameterSpec(
    name          = "contraction",
    normal_args   = ( "__iterator", ),
    list_star_arg = None,
    dict_star_arg = None,
    default_count = 0
)

def _buildContractionNode( provider, node, name, emit_class, start_value, assign_provider, source_ref ):
    # The contraction nodes are reformulated to loop style nodes, and use a lot of
    # temporary names, nested blocks, etc. and so a lot of variable names. There is no
    # good way around that, and we deal with many cases, due to having generator
    # expressions sharing this code, pylint: disable=R0912,R0914

    assert provider.isParentVariableProvider(), provider

    function_body = CPythonExpressionFunctionBody(
        provider   = provider,
        name       = name,
        doc        = None,
        parameters = make_contraction_parameters,
        source_ref = source_ref
    )

    temp_block = CPythonStatementTempBlock(
        source_ref = source_ref
    )

    if start_value is not None:
        container_tmp = temp_block.getTempVariable( "result" )

        statements = [
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTempVariableRef(
                    variable   = container_tmp.makeReference( temp_block ),
                    source_ref = source_ref
                ),
                source     = start_value,
                source_ref = source_ref.atInternal()
            )
        ]
    else:
        statements = []

    if hasattr( node, "elt" ):
        if start_value is not None:
            current_body = emit_class(
                CPythonExpressionTempVariableRef(
                    variable   = container_tmp.makeReference( temp_block ),
                    source_ref = source_ref
                ),
                buildNode(
                    provider   = function_body,
                    node       = node.elt,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        else:
            assert emit_class is CPythonExpressionYield

            function_body.markAsGenerator()

            current_body = emit_class(
                buildNode(
                    provider   = function_body,
                    node       = node.elt,
                    source_ref = source_ref
                ),
                for_return = False,
                source_ref = source_ref
            )
    else:
        assert emit_class is CPythonExpressionDictOperationSet

        current_body = emit_class(
            CPythonExpressionTempVariableRef(
                variable   = container_tmp.makeReference( temp_block ),
                source_ref = source_ref
            ),
            key = buildNode(
                provider   = function_body,
                node       = node.key,
                source_ref = source_ref,
            ),
            value = buildNode(
                provider   = function_body,
                node       = node.value,
                source_ref = source_ref,
            ),
            source_ref = source_ref
        )

    current_body = CPythonStatementExpressionOnly(
        expression = current_body,
        source_ref = source_ref
    )

    for qual in reversed( node.generators ):
        nested_temp_block = CPythonStatementTempBlock(
            source_ref = source_ref
        )

        tmp_iter_variable = nested_temp_block.getTempVariable( "contraction_iter" )

        tmp_value_variable = nested_temp_block.getTempVariable( "iter_value" )

        # The first iterated value is to be calculated outside of the function and
        # will be given as a parameter "_iterated".
        if qual is node.generators[0]:
            value_iterator = CPythonExpressionVariableRef(
                variable_name = "__iterator",
                source_ref    = source_ref
            )
        else:
            value_iterator = CPythonExpressionBuiltinIter1(
                value      = buildNode(
                    provider   = function_body,
                    node       = qual.iter,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )

        # First create the iterator and store it, next should be loop body
        nested_statements = [
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTempVariableRef(
                    variable   = tmp_iter_variable.makeReference( nested_temp_block ),
                    source_ref = source_ref
                ),
                source     = value_iterator,
                source_ref = source_ref
            )
        ]

        loop_statements = [
            CPythonStatementTryExcept(
                tried      = CPythonStatementsSequence(
                    statements = (
                        CPythonStatementAssignmentVariable(
                            variable_ref = CPythonExpressionTempVariableRef(
                                variable   = tmp_value_variable.makeReference( nested_temp_block ),
                                source_ref = source_ref
                            ),
                            source     = CPythonExpressionBuiltinNext1(
                                value      = CPythonExpressionTempVariableRef(
                                    variable   = tmp_iter_variable.makeReference( nested_temp_block ),
                                    source_ref = source_ref
                                ),
                                source_ref = source_ref
                            ),
                            source_ref = source_ref
                        ),
                    ),
                    source_ref = source_ref
                ),
                handlers   = (
                    CPythonStatementExceptHandler(
                        exception_types = (
                            CPythonExpressionBuiltinExceptionRef(
                                exception_name = "StopIteration",
                                source_ref     = source_ref
                            ),
                        ),
                        body           = CPythonStatementsSequence(
                            statements = (
                                CPythonStatementBreakLoop(
                                    source_ref = source_ref.atInternal()
                                ),
                            ),
                            source_ref = source_ref
                        ),
                        source_ref     = source_ref
                    ),
                ),
                source_ref = source_ref
            ),
            buildAssignmentStatements(
                provider   = provider if assign_provider else function_body,
                node       = qual.target,
                source     = CPythonExpressionTempVariableRef(
                    variable   = tmp_value_variable.makeReference( nested_temp_block ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        ]

        conditions = buildNodeList(
            provider   = function_body,
            nodes      = qual.ifs,
            source_ref = source_ref
        )

        if len( conditions ) == 1:
            loop_statements.append(
                CPythonStatementConditional(
                    condition  = conditions[0],
                    yes_branch = CPythonStatementsSequence(
                        statements = ( current_body, ),
                        source_ref = source_ref
                    ),
                    no_branch  = None,
                    source_ref = source_ref
                )
            )
        elif len( conditions ) > 1:
            loop_statements.append(
                CPythonStatementConditional(
                    condition = CPythonExpressionBoolAND(
                        operands   = conditions,
                        source_ref = source_ref
                    ),
                    yes_branch = CPythonStatementsSequence(
                        statements = ( current_body, ),
                        source_ref = source_ref
                    ),
                    no_branch  = None,
                    source_ref = source_ref
                )
            )
        else:
            loop_statements.append( current_body )

        nested_statements.append(
            CPythonStatementLoop(
                body       = CPythonStatementsSequence(
                    statements = loop_statements,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        )

        nested_temp_block.setBody(
            CPythonStatementsSequence(
                statements = nested_statements,
                source_ref = source_ref
            )
        )

        current_body = nested_temp_block

    statements.append( current_body )

    if start_value is not None:
        statements.append(
            CPythonStatementReturn(
                expression = CPythonExpressionTempVariableRef(
                    variable   = container_tmp.makeReference( temp_block ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        )

    temp_block.setBody(
        CPythonStatementsSequence(
            statements = statements,
            source_ref = source_ref
        )
    )

    function_body.setBody(
        CPythonStatementsFrame(
            statements = [ temp_block ],
            arg_names  = (),
            code_name  = "contraction",
            source_ref = source_ref
        )
    )

    return CPythonExpressionFunctionCall(
        function_body = function_body,
        values        = (
            CPythonExpressionBuiltinIter1(
                value      = buildNode(
                    provider   = provider,
                    node       = node.generators[0].iter,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
        ),
        source_ref        = source_ref
    )

def buildListContractionNode( provider, node, source_ref ):

    return _buildContractionNode(
        provider         = provider,
        node             = node,
        name             = "<listcontraction>",
        emit_class       = CPythonExpressionListOperationAppend,
        start_value      = CPythonExpressionConstantRef(
            constant   = [],
            source_ref = source_ref
        ),
        # Note: For Python3, the list contractions no longer assign to the outer scope.
        assign_provider  = Utils.python_version < 300,
        source_ref       = source_ref
    )

def buildSetContractionNode( provider, node, source_ref ):
    return _buildContractionNode(
        provider         = provider,
        node             = node,
        name             = "<setcontraction>",
        emit_class       = CPythonExpressionSetOperationAdd,
        start_value      = CPythonExpressionConstantRef(
            constant   = set(),
            source_ref = source_ref
        ),
        assign_provider  = False,
        source_ref       = source_ref
    )

def buildDictContractionNode( provider, node, source_ref ):
    return _buildContractionNode(
        provider         = provider,
        node             = node,
        name             = "<dictcontraction>",
        emit_class       = CPythonExpressionDictOperationSet,
        start_value      = CPythonExpressionConstantRef(
            constant   = {},
            source_ref = source_ref
        ),
        assign_provider  = False,
        source_ref       = source_ref
    )

def buildGeneratorExpressionNode( provider, node, source_ref ):
    assert getKind( node ) == "GeneratorExp"

    return _buildContractionNode(
        provider         = provider,
        node             = node,
        name             = "<genexpr>",
        emit_class       = CPythonExpressionYield,
        start_value      = None,
        assign_provider  = False,
        source_ref       = source_ref
    )

def buildComparisonNode( provider, node, source_ref ):
    assert len( node.comparators ) == len( node.ops )

    # The operands are split out
    left = buildNode( provider, node.left, source_ref )
    rights = [
        buildNode( provider, comparator, source_ref )
        for comparator in
        node.comparators
    ]

    # Only the first comparison has as left operands as the real thing, the others must
    # reference the previous comparison right one temp variable ref.
    result = []

    # For PyLint to like it, this will hold the previous one, normally.
    tmp_assign = None

    for comparator, right in zip( node.ops, rights ):
        if result:
            # Now we know it's not the only one, so we change the "left" to be a reference
            # to the previously saved right side.
            left = CPythonExpressionTempKeeperRef(
                linked     = tmp_assign,
                source_ref = source_ref
            )

            tmp_assign = None

        if right is not rights[-1]:
            # Now we known it's not the last one, so we ought to preseve the "right" so it
            # can be referenced by the next part that will come. We do it by assining it
            # to a temp variable to be shared with the next part.
            right = CPythonExpressionAssignmentTempKeeper(
                variable_name = provider.allocateTempKeeperName(),
                source        = right,
                source_ref    = source_ref
            )

            tmp_assign = right

        result.append(
            CPythonExpressionComparison(
                left       = left,
                right      = right,
                comparator = getKind( comparator ),
                source_ref = source_ref
            )
        )

    assert tmp_assign is None

    if len( result ) > 1:
        return CPythonExpressionBoolAND(
            operands   = result,
            source_ref = source_ref
        )
    else:
        return result[ 0 ]

def buildConditionNode( provider, node, source_ref ):
    return CPythonStatementConditional(
        condition  = buildNode( provider, node.test, source_ref ),
        yes_branch = buildStatementsNode(
            provider   = provider,
            nodes      = node.body,
            source_ref = source_ref
        ),
        no_branch  = buildStatementsNode(
            provider   = provider,
            nodes      = node.orelse if node.orelse else None,
            source_ref = source_ref
        ),
        source_ref = source_ref
    )

def _makeTryExceptNoRaise( tried, handlers, no_raise, source_ref ):
    assert no_raise is not None
    assert len( handlers ) > 0

    result = CPythonStatementTempBlock(
        source_ref = source_ref
    )

    tmp_handler_indicator_variable = result.getTempVariable( "unhandled_indicator" )

    for handler in handlers:
        handler.setExceptionBranch(
            _makeStatementsSequence(
                statements = (
                    CPythonStatementAssignmentVariable(
                        variable_ref = CPythonExpressionTempVariableRef(
                            variable   = tmp_handler_indicator_variable.makeReference( result ),
                            source_ref = source_ref.atInternal()
                        ),
                        source     = CPythonExpressionConstantRef(
                            constant   = False,
                            source_ref = source_ref
                        ),
                        source_ref = no_raise.getSourceReference().atInternal()
                    ),
                    handler.getExceptionBranch()
                ),
                allow_none = True,
                source_ref = source_ref
            )
        )

    result.setBody(
        CPythonStatementsSequence(
            statements = (
                CPythonStatementAssignmentVariable(
                    variable_ref = CPythonExpressionTempVariableRef(
                        variable   = tmp_handler_indicator_variable.makeReference( result ),
                        source_ref = source_ref.atInternal()
                    ),
                    source     = CPythonExpressionConstantRef(
                        constant   = True,
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
                CPythonStatementTryExcept(
                    tried      = tried,
                    handlers   = handlers,
                    source_ref = source_ref
                ),
                CPythonStatementConditional(
                    condition  = CPythonExpressionComparison(
                        left = CPythonExpressionTempVariableRef(
                            variable   = tmp_handler_indicator_variable.makeReference( result ),
                            source_ref = source_ref
                        ),
                        right = CPythonExpressionConstantRef(
                            constant   = True,
                            source_ref = source_ref
                        ),
                        comparator = "Is",
                        source_ref = source_ref
                    ),
                    yes_branch = no_raise,
                    no_branch  = None,
                    source_ref = source_ref
                )
            ),
            source_ref = source_ref
        )
    )

    return result


def buildTryExceptionNode( provider, node, source_ref ):
    handlers = []

    for handler in node.handlers:
        exception_expression, exception_assign, exception_block = handler.type, handler.name, handler.body

        statements = (
            buildAssignmentStatements(
                provider   = provider,
                node       = exception_assign,
                allow_none = True,
                source     = CPythonExpressionCaughtExceptionValueRef(
                    source_ref = source_ref.atInternal()
                ),
                source_ref = source_ref.atInternal()
            ),
            buildStatementsNode(
                provider   = provider,
                nodes      = exception_block,
                source_ref = source_ref
            )
        )

        handler_body = _makeStatementsSequence(
            statements = statements,
            allow_none = True,
            source_ref = source_ref
        )

        exception_types = buildNode( provider, exception_expression, source_ref, True )

        if exception_types is None:
            exception_types = ()
        elif exception_types.isExpressionMakeSequence():
            exception_types = exception_types.getElements()
        else:
            exception_types = ( exception_types, )

        handlers.append(
            CPythonStatementExceptHandler(
                exception_types = exception_types,
                body            = handler_body,
                source_ref      = source_ref
            )
        )

    tried = buildStatementsNode(
        provider   = provider,
        nodes      = node.body,
        source_ref = source_ref
    )

    no_raise = buildStatementsNode(
        provider   = provider,
        nodes      = node.orelse,
        source_ref = source_ref
    )

    if no_raise is None:
        return CPythonStatementTryExcept(
            handlers   = handlers,
            tried      = tried,
            source_ref = source_ref
        )
    else:
        return _makeTryExceptNoRaise(
            handlers   = handlers,
            tried      = tried,
            no_raise   = no_raise,
            source_ref = source_ref
        )

def buildTryFinallyNode( provider, node, source_ref ):
    return CPythonStatementTryFinally(
        tried      = buildStatementsNode(
            provider   = provider,
            nodes      = node.body,
            source_ref = source_ref
        ),
        final      = buildStatementsNode(
            provider   = provider,
            nodes      = node.finalbody,
            source_ref = source_ref
        ),
        source_ref = source_ref
    )

_has_raise_value = Utils.python_version < 300

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
    #
    # Starting with CPython2.7, it is:
    # if not x:
    #     raise AssertionError( y )

    if Utils.python_version < 270 or node.msg is None:
        raise_statement = CPythonStatementRaiseException(
            exception_type = CPythonExpressionBuiltinExceptionRef(
                exception_name = "AssertionError",
                source_ref     = source_ref
                ),
            exception_value = buildNode( provider, node.msg, source_ref, True ),
            exception_trace = None,
            source_ref      = source_ref
        )
    else:
        raise_statement = CPythonStatementRaiseException(
            exception_type =  CPythonExpressionBuiltinMakeException(
                exception_name = "AssertionError",
                args           = ( buildNode( provider, node.msg, source_ref, True ), ),
                source_ref     = source_ref
            ),
            exception_value = None,
            exception_trace = None,
            source_ref      = source_ref
        )

    return CPythonStatementConditional(
        condition = CPythonExpressionOperationNOT(
            operand    = buildNode( provider, node.test, source_ref ),
            source_ref = source_ref
        ),
        yes_branch = CPythonStatementsSequence(
            statements = (
                raise_statement,
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

            element = CPythonExpressionSliceObject(
                lower      = lower,
                upper      = upper,
                step       = step,
                source_ref = source_ref
            )
        elif dim_kind == "Ellipsis":
            element = CPythonExpressionConstantRef(
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

    return CPythonExpressionMakeTuple(
        elements      = elements,
        source_ref    = source_ref
    )

def buildSubscriptNode( provider, node, source_ref ):
    assert getKind( node.ctx ) == "Load", source_ref

    kind = getKind( node.slice )

    if kind == "Index":
        return CPythonExpressionSubscriptLookup(
            expression = buildNode( provider, node.value, source_ref ),
            subscript  = buildNode( provider, node.slice.value, source_ref ),
            source_ref = source_ref
        )
    elif kind == "Slice":
        lower = buildNode( provider, node.slice.lower, source_ref, True )
        upper = buildNode( provider, node.slice.upper, source_ref, True )

        if node.slice.step is not None:
            step = buildNode( provider, node.slice.step,  source_ref )

            return CPythonExpressionSubscriptLookup(
                expression = buildNode( provider, node.value, source_ref ),
                subscript  = CPythonExpressionSliceObject(
                    lower      = lower,
                    upper      = upper,
                    step       = step,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        else:
            return CPythonExpressionSliceLookup(
                expression = buildNode( provider, node.value, source_ref ),
                lower      = lower,
                upper      = upper,
                source_ref = source_ref
            )
    elif kind == "ExtSlice":
        return CPythonExpressionSubscriptLookup(
            expression = buildNode( provider, node.value, source_ref ),
            subscript  = _buildExtSliceNode( provider, node, source_ref ),
            source_ref = source_ref
        )
    elif kind == "Ellipsis":
        return CPythonExpressionSubscriptLookup(
            expression = buildNode( provider, node.value, source_ref ),
            subscript  = CPythonExpressionConstantRef(
                constant   = Ellipsis,
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    else:
        assert False, kind

def _makeStatementsSequenceOrStatement( statements, source_ref ):
    """ Make a statement sequence, but only if more than one statement

    Useful for when we can unroll constructs already here, but are not sure if we actually
    did that. This avoids the branch or the pollution of doing it always.
    """

    if len( statements ) > 1:
        return CPythonStatementsSequence(
            statements = statements,
            source_ref = source_ref
        )
    else:
        return statements[0]

def _makeStatementsSequence( statements, allow_none, source_ref ):
    if allow_none:
        statements = tuple( statement for statement in statements if statement is not None )

    if statements:
        return CPythonStatementsSequence(
            statements = statements,
            source_ref = source_ref
        )
    else:
        return None


def _buildImportModulesNode( import_names, source_ref ):
    import_nodes = []

    for import_desc in import_names:
        module_name, local_name = import_desc

        module_topname = module_name.split(".")[0]

        level = 0 if source_ref.getFutureSpec().isAbsoluteImport() else -1

        if local_name:
            import_node = CPythonExpressionImportModule(
                module_name = module_name,
                import_list = None,
                level       = level,
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
                level       = level,
                source_ref  = source_ref
            )

        # If a name was given, use the one provided, otherwise the import gives the top
        # level package name given for assignment of the imported module.

        import_nodes.append(
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTargetVariableRef(
                    variable_name = local_name if local_name is not None else module_topname,
                    source_ref    = source_ref
                ),
                source     = import_node,
                source_ref = source_ref
            )
        )

    # Note: Each import is sequential. It can succeed, and the failure of a later one is
    # not changing one. We can therefore have a sequence of imports that only import one
    # thing therefore.
    return _makeStatementsSequenceOrStatement(
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

def enableFutureFeature( object_name, future_spec, source_ref ):
    if object_name == "unicode_literals":
        future_spec.enableUnicodeLiterals()
    elif object_name == "absolute_import":
        future_spec.enableAbsoluteImport()
    elif object_name == "division":
        future_spec.enableFutureDivision()
    elif object_name == "print_function":
        future_spec.enableFuturePrint()
    elif object_name == 'barry_as_FLUFL' and Utils.python_version >= 300:
        future_spec.enableBarry()
    elif object_name == 'braces':
        SyntaxErrors.raiseSyntaxError(
            "not a chance",
            source_ref
        )
    elif object_name in ( "nested_scopes", "generators", "with_statement" ):
        pass
    else:
        SyntaxErrors.raiseSyntaxError(
            "future feature %s is not defined" % object_name,
            source_ref
        )

def buildImportFromNode( provider, node, source_ref ):
    module_name = node.module if node.module is not None else ""
    level = node.level

    if module_name == "__future__":
        assert provider.isModule() or source_ref.isExecReference()

        for import_desc in node.names:
            object_name, _local_name = import_desc.name, import_desc.asname

            enableFutureFeature(
                object_name = object_name,
                future_spec = source_ref.getFutureSpec(),
                source_ref  = source_ref
            )

    target_names = []
    import_names = []

    for import_desc in node.names:
        object_name, local_name = import_desc.name, import_desc.asname

        if object_name == "*":
            target_names.append( None )
        else:
            target_names.append( local_name if local_name is not None else object_name )

        import_names.append( object_name )

    if None in target_names:
        # More than "*" is a syntax error in Python, need not care about this at
        # all, it's only allowed value for import list in  this case.
        assert target_names == [ None ]

        # Python3 made this a syntax error unfortunately.
        if not provider.isModule() and Utils.python_version >= 300:
            SyntaxErrors.raiseSyntaxError(
                "import * only allowed at module level",
                provider.getSourceReference()
            )

        if provider.isExpressionFunctionBody():
            provider.markAsStarImportContaining()

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

        for target_name, import_name in zip( target_names, import_names ):
            import_nodes.append(
                CPythonStatementAssignmentVariable(
                    variable_ref = CPythonExpressionTargetVariableRef(
                        variable_name = target_name,
                        source_ref    = source_ref
                    ),
                    source     = CPythonExpressionImportName(
                        module      = CPythonExpressionImportModule(
                            module_name = module_name,
                            import_list = import_names,
                            level       = level,
                            source_ref  = source_ref
                        ),
                        import_name = import_name,
                        source_ref  = source_ref
                    ),
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

def buildPrintNode( provider, node, source_ref ):
    values = buildNodeList( provider, node.values, source_ref )
    dest = buildNode( provider, node.dest, source_ref, True )

    return CPythonStatementPrint(
        newline    = node.nl,
        dest       = dest,
        values     = values,
        source_ref = source_ref
    )

def buildExecNode( provider, node, source_ref ):
    exec_globals = node.globals
    exec_locals = node.locals
    body = node.body

    orig_globals = exec_globals

    # Allow exec(a,b,c) to be same as exec a, b, c
    if exec_locals is None and exec_globals is None and getKind( body ) == "Tuple":
        parts = body.elts
        body  = parts[0]

        if len( parts ) > 1:
            exec_globals = parts[1]

            if len( parts ) > 2:
                exec_locals = parts[2]
        else:
            return CPythonStatementRaiseException(
                exception_type = CPythonExpressionBuiltinExceptionRef(
                    exception_name = "TypeError",
                    source_ref     = source_ref
                ),
                exception_value = CPythonExpressionConstantRef(
                    constant   = "exec: arg 1 must be a string, file, or code object",
                    source_ref = source_ref
                ),
                exception_trace = None,
                source_ref      = source_ref
            )

    globals_node = buildNode( provider, exec_globals, source_ref, True )
    locals_node = buildNode( provider, exec_locals, source_ref, True )

    if provider.isExpressionFunctionBody():
        provider.markAsExecContaining()

        if orig_globals is None:
            provider.markAsUnqualifiedExecContaining( source_ref )

    if locals_node is not None and locals_node.isExpressionConstantRef() and locals_node.getConstant() is None:
        locals_node = None

    if locals_node is None and globals_node is not None:
        if globals_node.isExpressionConstantRef() and globals_node.getConstant() is None:
            globals_node = None

    return CPythonStatementExec(
        source_code = buildNode( provider, body, source_ref ),
        globals_arg = globals_node,
        locals_arg  = locals_node,
        source_ref  = source_ref
    )


def buildWithNode( provider, node, source_ref ):
    with_source = buildNode( provider, node.context_expr, source_ref )

    result = CPythonStatementTempBlock(
        source_ref = source_ref
    )

    tmp_source_variable = result.getTempVariable( "with_source" )
    tmp_exit_variable = result.getTempVariable( "with_exit" )
    tmp_enter_variable = result.getTempVariable( "with_enter" )

    statements = (
        buildAssignmentStatements(
            provider   = provider,
            node       = node.optional_vars,
            allow_none = True,
            source     = CPythonExpressionTempVariableRef(
                variable   = tmp_enter_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
        buildStatementsNode( provider, node.body, source_ref )
    )

    with_body = _makeStatementsSequence(
        statements = statements,
        allow_none = True,
        source_ref = source_ref
    )

    # The "__enter__" and "__exit__" were normal attribute lookups under Python2.6, but
    # that changed later.
    if Utils.python_version < 270:
        attribute_lookup_class = CPythonExpressionAttributeLookup
    else:
        attribute_lookup_class = CPythonExpressionSpecialAttributeLookup

    statements = [
        # First assign the with context to a temporary variable.
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_source_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source       = with_source,
            source_ref   = source_ref
        ),
        # Next, assign "__enter__" and "__exit__" attributes to temporary variables.
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_exit_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source       = attribute_lookup_class(
                expression     = CPythonExpressionTempVariableRef(
                    variable   = tmp_source_variable.makeReference( result ),
                    source_ref = source_ref
                ),
                attribute_name = "__exit__",
                source_ref     = source_ref
            ),
            source_ref   = source_ref
        ),
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_enter_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source       = CPythonExpressionCall(
                called         = attribute_lookup_class(
                    expression     = CPythonExpressionTempVariableRef(
                        variable   = tmp_source_variable.makeReference( result ),
                        source_ref = source_ref
                    ),
                    attribute_name = "__enter__",
                    source_ref     = source_ref
                ),
                positional_args = (),
                pairs           = (),
                dict_star_arg   = None,
                list_star_arg   = None,
                source_ref      = source_ref
            ),
            source_ref   = source_ref
        )
    ]

    source_ref = source_ref.atInternal()

    statements += [
        _makeTryExceptNoRaise(
            tried      = with_body,
            handlers   = (
                CPythonStatementExceptHandler(
                    exception_types = (
                        CPythonExpressionBuiltinExceptionRef(
                            exception_name = "BaseException",
                            source_ref     = source_ref
                        ),
                    ),
                    body           = CPythonStatementsSequence(
                        statements = (
                            CPythonStatementConditional(
                                condition     = CPythonExpressionCall(
                                    called          = CPythonExpressionTempVariableRef(
                                        variable   = tmp_exit_variable.makeReference( result ),
                                        source_ref = source_ref
                                    ),
                                    positional_args = (
                                        CPythonExpressionCaughtExceptionTypeRef(
                                            source_ref = source_ref
                                        ),
                                        CPythonExpressionCaughtExceptionValueRef(
                                            source_ref = source_ref
                                        ),
                                        CPythonExpressionCaughtExceptionTracebackRef(
                                            source_ref = source_ref
                                        ),
                                    ),
                                    pairs           = (),
                                    list_star_arg   = None,
                                    dict_star_arg   = None,
                                    source_ref      = source_ref
                                ),
                                no_branch = CPythonStatementsSequence(
                                    statements = (
                                        CPythonStatementRaiseException(
                                            exception_type  = None,
                                            exception_value = None,
                                            exception_trace = None,
                                            source_ref      = source_ref
                                        ),
                                    ),
                                    source_ref = source_ref
                                ),
                                yes_branch  = None,
                                source_ref = source_ref
                            ),
                        ),
                        source_ref     = source_ref
                    ),
                    source_ref = source_ref
                ),
            ),
            no_raise   = CPythonStatementsSequence(
                statements = (
                    CPythonStatementExpressionOnly(
                        expression = CPythonExpressionCall(
                            called          = CPythonExpressionTempVariableRef(
                                variable   = tmp_exit_variable.makeReference( result ),
                                source_ref = source_ref
                            ),
                            positional_args = (
                                CPythonExpressionConstantRef(
                                    constant   = None,
                                    source_ref = source_ref
                                ),
                                CPythonExpressionConstantRef(
                                    constant   = None,
                                    source_ref = source_ref
                                ),
                                CPythonExpressionConstantRef(
                                    constant   = None,
                                    source_ref = source_ref
                                )
                            ),
                            pairs           = (),
                            list_star_arg   = None,
                            dict_star_arg   = None,
                            source_ref      = source_ref
                        ),
                        source_ref     = source_ref
                    ),
                ),
                source_ref     = source_ref
            ),
            source_ref = source_ref
        )
    ]

    result.setBody(
        CPythonStatementsSequence(
            statements = statements,
            source_ref = source_ref
        )
    )

    return result

def buildNodeList( provider, nodes, source_ref, allow_none = False ):
    if nodes is not None:
        result = []

        for node in nodes:
            entry = buildNode( provider, node, source_ref.atLineNumber( node.lineno ), allow_none )

            if entry is not None:
                result.append( entry )

        return result
    else:
        return []

def buildGlobalDeclarationNode( provider, node, source_ref ):
    # The source reference of the global really doesn't matter, pylint: disable=W0613

    # Need to catch the error of declaring a parameter variable as global ourselves
    # here. The AST parsing doesn't catch it.
    try:
        parameters = provider.getParameters()

        for variable_name in node.names:
            if variable_name in parameters.getParameterNames():
                SyntaxErrors.raiseSyntaxError(
                    "name '%s' is %s and global" % (
                        variable_name,
                        "local" if Utils.python_version < 300 else "parameter"
                    ),
                    provider.getSourceReference()
                )
    except AttributeError:
        pass

    module = provider.getParentModule()

    for variable_name in node.names:
        module_variable = module.getVariableForAssignment(
            variable_name = variable_name
        )

        closure_variable = provider.addClosureVariable(
            variable         = module_variable,
            global_statement = True
        )

        if isinstance( provider, CPythonClosureGiverNodeBase ):
            provider.registerProvidedVariable(
                variable = closure_variable
            )

    return None


def buildStringNode( node, source_ref ):
    assert type( node.s ) in ( str, unicode )

    return CPythonExpressionConstantRef(
        constant   = node.s,
        source_ref = source_ref
    )

def buildNumberNode( node, source_ref ):
    assert type( node.n ) in ( int, long, float, complex ), type( node.n )

    return CPythonExpressionConstantRef(
        constant   = node.n,
        source_ref = source_ref
    )

def buildBytesNode( node, source_ref ):
    return CPythonExpressionConstantRef(
        constant   = node.s,
        source_ref = source_ref
    )

def buildBoolOpNode( provider, node, source_ref ):
    bool_op = getKind( node.op )

    if bool_op == "Or":
        # The "or" may be short circuit and is therefore not a plain operation
        return CPythonExpressionBoolOR(
            operands   = buildNodeList( provider, node.values, source_ref ),
            source_ref = source_ref
        )
    elif bool_op == "And":
        # The "and" may be short circuit and is therefore not a plain operation
        return CPythonExpressionBoolAND(
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
    return CPythonExpressionAttributeLookup(
        expression     = buildNode( provider, node.value, source_ref ),
        attribute_name = node.attr,
        source_ref     = source_ref
    )

def buildReturnNode( provider, node, source_ref ):
    if not provider.isExpressionFunctionBody() or provider.isClassDictCreation():
        SyntaxErrors.raiseSyntaxError(
            "'return' outside function",
            source_ref,
            None if Utils.python_version < 300 else (
                node.col_offset if provider.isModule() else node.col_offset+4
            )
        )

    if node.value is not None:
        return CPythonStatementReturn(
            expression = buildNode( provider, node.value, source_ref ),
            source_ref = source_ref
        )
    else:
        return CPythonStatementReturn(
            expression = CPythonExpressionConstantRef(
                constant   = None,
                source_ref = source_ref
            ),
            source_ref = source_ref
        )


def buildYieldNode( provider, node, source_ref ):
    if provider.isModule():
        SyntaxErrors.raiseSyntaxError(
            "'yield' outside function",
            source_ref,
            None if Utils.python_version < 300 else node.col_offset
        )

    provider.markAsGenerator()

    if node.value is not None:
        return CPythonExpressionYield(
            expression = buildNode( provider, node.value, source_ref ),
            for_return = False,
            source_ref = source_ref
        )
    else:
        return CPythonExpressionYield(
            expression = CPythonExpressionConstantRef(
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

def _buildInplaceAssignVariableNode( result, variable_ref, tmp_variable1, tmp_variable2,
                                     operator, expression, source_ref ):
    assert variable_ref.isExpressionTargetVariableRef(), variable_ref

    return (
        # First assign the target value to a temporary variable.
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_variable1.makeReference( result ),
                source_ref = source_ref
            ),
            source     = CPythonExpressionVariableRef(
                variable_name = variable_ref.getVariableName(),
                source_ref    = source_ref
            ),
            source_ref = source_ref
        ),
        # Second assign the inplace result to a temporary variable.
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_variable2.makeReference( result ),
                source_ref = source_ref
            ),
            source     = CPythonExpressionOperationBinaryInplace(
                operator   = operator,
                left       = CPythonExpressionTempVariableRef(
                    variable   = tmp_variable1.makeReference( result ),
                    source_ref = source_ref
                ),
                right      = expression,
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
        # Copy it over, if the reference values change, i.e. IsNot is true.
        CPythonStatementConditional(
            condition = CPythonExpressionComparison(
                comparator = "IsNot",
                left     = CPythonExpressionTempVariableRef(
                    variable   = tmp_variable1.makeReference( result ),
                    source_ref = source_ref
                ),
                right    = CPythonExpressionTempVariableRef(
                    variable   = tmp_variable2.makeReference( result ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            yes_branch = CPythonStatementsSequence(
                statements = (
                    CPythonStatementAssignmentVariable(
                        variable_ref = variable_ref.makeCloneAt( source_ref ),
                        source     = CPythonExpressionTempVariableRef(
                            variable   = tmp_variable2.makeReference( result ),
                            source_ref = source_ref
                        ),
                        source_ref = source_ref
                    ),
                ),
                source_ref = source_ref
            ),
            no_branch = None,
            source_ref = source_ref
        )
    )

def _buildInplaceAssignAttributeNode( result, lookup_source, attribute_name, tmp_variable1, \
                                      tmp_variable2, operator, expression, source_ref ):
    return (
        # First assign the target value to a temporary variable.
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_variable1.makeReference( result ),
                source_ref = source_ref
            ),
            source     = CPythonExpressionAttributeLookup(
                expression     = lookup_source.makeCloneAt( source_ref ),
                attribute_name = attribute_name,
                source_ref     = source_ref
            ),
            source_ref = source_ref
        ),
        # Second assign the inplace result to a temporary variable.
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_variable2.makeReference( result ),
                source_ref = source_ref
            ),
            source     = CPythonExpressionOperationBinaryInplace(
                operator   = operator,
                left       = CPythonExpressionTempVariableRef(
                    variable   = tmp_variable1.makeReference( result ),
                    source_ref = source_ref
                ),
                right      = expression,
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
        # Copy it over, if the reference values change, i.e. IsNot is true.
        CPythonStatementConditional(
            condition = CPythonExpressionComparison(
                comparator = "IsNot",
                left     = CPythonExpressionTempVariableRef(
                    variable   = tmp_variable1.makeReference( result ),
                    source_ref = source_ref
                ),
                right    = CPythonExpressionTempVariableRef(
                    variable   = tmp_variable2.makeReference( result ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            yes_branch = CPythonStatementsSequence(
                statements = (
                    CPythonStatementAssignmentAttribute(
                        expression = lookup_source.makeCloneAt( source_ref ),
                        attribute_name = attribute_name,
                        source     = CPythonExpressionTempVariableRef(
                            variable   = tmp_variable2.makeReference( result ),
                            source_ref = source_ref
                        ),
                        source_ref = source_ref
                    ),
                ),
                source_ref = source_ref
            ),
            no_branch = None,
            source_ref = source_ref
        )
    )

def _buildInplaceAssignSubscriptNode( result, subscribed, subscript, tmp_variable1,
                                      tmp_variable2, operator, expression, source_ref ):
    return (
        # First assign the target value and subscript to temporary variables.
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_variable1.makeReference( result ),
                source_ref = source_ref
            ),
            source     = subscribed,
            source_ref = source_ref
        ),
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_variable2.makeReference( result ),
                source_ref = source_ref
            ),
            source     = subscript,
            source_ref = source_ref
        ),
        # Second assign the inplace result over the original value.
        CPythonStatementAssignmentSubscript(
            expression = CPythonExpressionTempVariableRef(
                variable   = tmp_variable1.makeReference( result ),
                source_ref = source_ref
            ),
            subscript  = CPythonExpressionTempVariableRef(
                variable   = tmp_variable2.makeReference( result ),
                source_ref = source_ref
            ),
            source     = CPythonExpressionOperationBinaryInplace(
                operator   = operator,
                left       = CPythonExpressionSubscriptLookup(
                    expression = CPythonExpressionTempVariableRef(
                        variable   = tmp_variable1.makeReference( result ),
                        source_ref = source_ref
                    ),
                    subscript  = CPythonExpressionTempVariableRef(
                        variable   = tmp_variable2.makeReference( result ),
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
                right      = expression,
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

def _buildInplaceAssignSliceNode( result, lookup_source, lower, upper, tmp_variable1, \
                                  tmp_variable2, tmp_variable3, operator, expression, \
                                  source_ref ):

    # First assign the target value, lower and upper to temporary variables.
    result = [
        CPythonStatementAssignmentVariable(
            variable_ref = CPythonExpressionTempVariableRef(
                variable   = tmp_variable1.makeReference( result ),
                source_ref = source_ref
            ),
            source     = lookup_source,
            source_ref = source_ref
        )
    ]

    if lower is not None:
        result.append(
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTempVariableRef(
                    variable   = tmp_variable2.makeReference( result ),
                    source_ref = source_ref
                ),
                source     = lower,
                source_ref = source_ref
            )
        )

        lower_ref1 = CPythonExpressionTempVariableRef(
            variable   = tmp_variable2.makeReference( result ),
            source_ref = source_ref
        )
        lower_ref2 = CPythonExpressionTempVariableRef(
            variable   = tmp_variable2.makeReference( result ),
            source_ref = source_ref
        )
    else:
        assert tmp_variable2 is None

        lower_ref1 = lower_ref2 = None

    if upper is not None:
        result.append(
            CPythonStatementAssignmentVariable(
                variable_ref = CPythonExpressionTempVariableRef(
                    variable   = tmp_variable3.makeReference( result ),
                    source_ref = source_ref
                ),
                source     = upper,
                source_ref = source_ref
            )
        )

        upper_ref1 = CPythonExpressionTempVariableRef(
            variable   = tmp_variable3.makeReference( result ),
            source_ref = source_ref
        )
        upper_ref2 = CPythonExpressionTempVariableRef(
            variable   = tmp_variable3.makeReference( result ),
            source_ref = source_ref
        )
    else:
        assert tmp_variable3 is None

        upper_ref1 = upper_ref2 = None

    # Second assign the inplace result over the original value.
    result.append(
        CPythonStatementAssignmentSlice(
            expression = CPythonExpressionTempVariableRef(
                variable   = tmp_variable1.makeReference( result ),
                source_ref = source_ref
            ),
            lower      = lower_ref1,
            upper      = upper_ref1,
            source     = CPythonExpressionOperationBinaryInplace(
                operator   = operator,
                left       = CPythonExpressionSliceLookup(
                    expression = CPythonExpressionTempVariableRef(
                        variable   = tmp_variable1.makeReference( result ),
                        source_ref = source_ref
                    ),
                    lower      = lower_ref2,
                    upper      = upper_ref2,
                    source_ref = source_ref
                ),
                right      = expression,
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    return result

def buildInplaceAssignNode( provider, node, source_ref ):
    # There are many inplace assignment variables, and the detail is unpacked into names,
    # so we end up with a lot of variables, which is on purpose, pylint: disable=R0914

    operator   = getKind( node.op )
    expression = buildNode( provider, node.value, source_ref )

    result = CPythonStatementTempBlock(
        source_ref = source_ref
    )

    kind, detail = decodeAssignTarget( provider, node.target, source_ref )

    if kind == "Name":
        variable_ref = detail

        tmp_variable1 = result.getTempVariable( "inplace_start" )
        tmp_variable2 = result.getTempVariable( "inplace_end" )

        statements = _buildInplaceAssignVariableNode(
            result        = result,
            variable_ref  = variable_ref,
            tmp_variable1 = tmp_variable1,
            tmp_variable2 = tmp_variable2,
            operator      = operator,
            expression    = expression,
            source_ref    = source_ref
        )
    elif kind == "Attribute":
        lookup_source, attribute_name = detail

        tmp_variable1 = result.getTempVariable( "inplace_start" )
        tmp_variable2 = result.getTempVariable( "inplace_end" )

        statements = _buildInplaceAssignAttributeNode(
            result         = result,
            lookup_source  = lookup_source,
            attribute_name = attribute_name,
            tmp_variable1  = tmp_variable1,
            tmp_variable2  = tmp_variable2,
            operator       = operator,
            expression     = expression,
            source_ref     = source_ref
        )
    elif kind == "Subscript":
        subscribed, subscript = detail

        tmp_variable1 = result.getTempVariable( "inplace_target" )
        tmp_variable2 = result.getTempVariable( "inplace_subscript" )

        statements = _buildInplaceAssignSubscriptNode(
            result        = result,
            subscribed    = subscribed,
            subscript     = subscript,
            tmp_variable1 = tmp_variable1,
            tmp_variable2 = tmp_variable2,
            operator      = operator,
            expression    = expression,
            source_ref    = source_ref
        )
    elif kind == "Slice":
        lookup_source, lower, upper = detail

        tmp_variable1 = result.getTempVariable( "inplace_target" )
        tmp_variable2 = result.getTempVariable( "inplace_lower" ) if lower is not None else None
        tmp_variable3 = result.getTempVariable( "inplace_upper" ) if upper is not None else None

        statements = _buildInplaceAssignSliceNode(
            result        = result,
            lookup_source = lookup_source,
            lower         = lower,
            upper         = upper,
            tmp_variable1 = tmp_variable1,
            tmp_variable2 = tmp_variable2,
            tmp_variable3 = tmp_variable3,
            operator      = operator,
            expression    = expression,
            source_ref    = source_ref
        )
    else:
        assert False, kind

    result.setBody(
        CPythonStatementsSequence(
            statements = statements,
            source_ref = source_ref
        )
    )

    return result

def buildConditionalExpressionNode( provider, node, source_ref ):
    return CPythonExpressionConditional(
        condition      = buildNode( provider, node.test, source_ref ),
        yes_expression = buildNode( provider, node.body, source_ref ),
        no_expression  = buildNode( provider, node.orelse, source_ref ),
        source_ref     = source_ref
    )




_fast_path_args3 = {
    "Name"         : buildVariableReferenceNode,
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
    "Set"          : buildSequenceCreationNode,
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
    "Call"         : buildCallNode,
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
    "Import"       : buildImportModulesNode,
    "Str"          : buildStringNode,
    "Num"          : buildNumberNode,
    "Bytes"        : buildBytesNode
}

_fast_path_args1 = {
    "Continue" : CPythonStatementContinueLoop,
    "Break"    : CPythonStatementBreakLoop,
}

def buildNode( provider, node, source_ref, allow_none = False ):
    if node is None and allow_none:
        return None

    try:
        kind = getKind( node )

        source_ref = source_ref.atLineNumber( node.lineno )

        if kind in _fast_path_args3:
            result = _fast_path_args3[ kind ](
                provider   = provider,
                node       = node,
                source_ref = source_ref
            )
        elif kind in _fast_path_args2:
            result = _fast_path_args2[ kind ](
                node       = node,
                source_ref = source_ref
            )
        elif kind in _fast_path_args1:
            result = _fast_path_args1[ kind ](
                source_ref = source_ref
            )
        elif kind == "Pass":
            result = None
        else:
            assert False, kind

        if result is None and allow_none:
            return None

        assert isinstance( result, CPythonNodeBase ), result

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

    if not replacement:
        provider.setDoc( doc )
        provider.setBody( result )

    return result

def buildReplacementTree( provider, source_code, source_ref ):
    assert False, "bitrot"

    return buildParseTree(
        provider    = provider,
        source_code = source_code,
        source_ref  = source_ref,
        replacement = True
    )

def buildModuleTree( filename, package, is_main ):
    assert package is None or type( package ) is str

    if Utils.isFile( filename ):
        source_filename = filename

        source_ref = SourceCodeReferences.fromFilename(
            filename    = filename,
            future_spec = FutureSpec()
        )

        if is_main:
            module_name = "__main__"
        else:
            module_name = Utils.basename( filename )

            if module_name.endswith( ".py" ):
                module_name = module_name[:-3]

        result = CPythonModule(
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

        result = CPythonPackage(
            name       = Utils.basename( filename ),
            package    = package,
            source_ref = source_ref
        )
    else:
        sys.stderr.write(  "Nuitka: can't open file '%s'.\n" % filename )
        sys.exit( 2 )

    if not Options.shallHaveStatementLines():
        source_ref = source_ref.atInternal()

    # Detect the encoding.
    encoding = "ascii"

    with open( source_filename, "rb" ) as source_file:
        line1 = source_file.readline()

        if line1.startswith( b'\xef\xbb\xbf' ):
            encoding = "utf-8"
        else:
            line1_match = re.search( b"coding[:=]\s*([-\w.]+)", line1 )

            if line1_match:
                encoding = line1_match.group(1)
            else:
                line2 = source_file.readline()

                line2_match = re.search( b"coding[:=]\s*([-\w.]+)", line2 )

                if line2_match:
                    encoding = line2_match.group(1)

    with open( source_filename, "rU" ) as source_file:
        source_code = source_file.read()

        # Try and detect SyntaxError from missing or wrong encodings.
        if type( source_code ) is not unicode and encoding == "ascii":
            try:
                source_code = source_code.decode( encoding )
            except UnicodeDecodeError as e:
                lines = source_code.split( "\n" )
                so_far = 0

                for count, line in enumerate( lines ):
                    so_far += len( line ) + 1

                    if so_far > e.args[2]:
                        break

                wrong_byte = re.search( "byte 0x([a-f0-9]{2}) in position", str( e ) ).group( 1 )

                raise SyntaxError(
                    "Non-ASCII character '\\x%s' in file %s on line %d, but no encoding declared; see http://www.python.org/peps/pep-0263.html for details" % (
                        wrong_byte,
                        source_filename,
                        count+1,
                    ),
                    (
                        source_filename,
                        count+1,
                        None,
                        None
                    )
                )

        buildParseTree(
            provider    = result,
            source_code = source_code,
            source_ref  = source_ref,
            replacement = False,
        )

    return result
