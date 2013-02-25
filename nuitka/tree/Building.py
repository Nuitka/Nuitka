#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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
the compiler.

At the bottom of the file, the dispatching is happening. One function deals with every
node kind as found in the AST. The parsing is centered around the module "ast" output.

Many higher level language features and translated into lower level ones. Inplace
assignments, for loops, while loops, classes, complex calls, with statements, and even
or/and etc. are all translated to simpler constructs.

The output of this module is a node tree, which contains only relatively low level
operations. A property of the output module is also an overlaid tree of provider structure
that indicates variable provision.

"""

# pylint: disable=W0622
from nuitka.__past__ import long, unicode
# pylint: enable=W0622

from nuitka import (
    SourceCodeReferences,
    SyntaxErrors,
    Options,
    Utils
)

from nuitka.nodes.FutureSpec import FutureSpec

from nuitka.nodes.VariableRefNodes import (
    ExpressionTargetVariableRef,
    ExpressionVariableRef
)
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.BuiltinRefNodes import ExpressionBuiltinExceptionRef
from nuitka.nodes.ExceptionNodes import StatementRaiseException
from nuitka.nodes.ExecEvalNodes import StatementExec
from nuitka.nodes.AttributeNodes import ExpressionAttributeLookup
from nuitka.nodes.SubscriptNodes import ExpressionSubscriptLookup
from nuitka.nodes.SliceNodes import (
    ExpressionSliceLookup,
    ExpressionSliceObject
)
from nuitka.nodes.ContainerMakingNodes import (
    ExpressionKeyValuePair,
    ExpressionMakeTuple,
    ExpressionMakeList,
    ExpressionMakeDict,
    ExpressionMakeSet
)
from nuitka.nodes.StatementNodes import (
    StatementExpressionOnly,
    StatementsSequence,
)
from nuitka.nodes.ImportNodes import (
    ExpressionImportModule,
    ExpressionImportName,
    StatementImportStar,
)
from nuitka.nodes.OperatorNodes import (
    ExpressionOperationBinary,
    ExpressionOperationUnary
)
from nuitka.nodes.LoopNodes import (
    StatementContinueLoop,
    StatementBreakLoop,
)
from nuitka.nodes.ConditionalNodes import (
    ExpressionConditional,
    StatementConditional
)
from nuitka.nodes.YieldNodes import ExpressionYield
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.AssignNodes import StatementAssignmentVariable
from nuitka.nodes.PrintNodes import StatementPrint
from nuitka.nodes.ModuleNodes import (
    PythonPackage,
    PythonModule
)
from nuitka.nodes.TryNodes import StatementTryFinally

from .VariableClosure import completeVariableClosures

# Classes are handled in a separate file. They are re-formulated into functions producing
# dictionaries used to call the metaclass with.
from .ReformulationClasses import buildClassNode

# Try/except/else statements are handled in a separate file. They are re-formulated into
# using a temporary variable to track if the else branch should execute.
from .ReformulationTryExceptStatements import buildTryExceptionNode

# With statements are handled in a separate file. They are re-formulated into special
# attribute lookups for "__enter__" and "__exit__", calls of them, catching and passing in
# exceptions raised.
from .ReformulationWithStatements import buildWithNode

from .ReformulationAssignmentStatements import (
    buildInplaceAssignNode,
    buildExtSliceNode,
    buildAssignNode,
    buildDeleteNode
)

from .ReformulationLoopStatements import (
    buildWhileLoopNode,
    buildForLoopNode
)

from .ReformulationAssertStatements import buildAssertNode

from .ReformulationFunctionStatements import buildFunctionNode

from .ReformulationLambdaExpressions import buildLambdaNode

from .ReformulationBooleanExpressions import buildBoolOpNode

from .ReformulationComparisonExpressions import buildComparisonNode

from .ReformulationContractionExpressions import (
    buildGeneratorExpressionNode,
    buildListContractionNode,
    buildDictContractionNode,
    buildSetContractionNode
)

from .ReformulationCallExpressions import buildCallNode

# Some helpers.
from .Helpers import (
    makeStatementsSequenceOrStatement,
    buildStatementsNode,
    setBuildDispatchers,
    extractDocFromBody,
    buildNodeList,
    buildNode,
    getKind
)

from .SourceReading import readSourceCodeFromFilename

import ast, sys, re

def buildVariableReferenceNode( provider, node, source_ref ):
    # Python3 is influenced by the mere use of a variable name. So we need to remember it,
    # esp. for cases, where it is optimized away.
    if Utils.python_version >= 300 and node.id == "super" and provider.isExpressionFunctionBody():
        provider.markAsClassClosureTaker()

    return ExpressionVariableRef(
        variable_name = node.id,
        source_ref    = source_ref
    )


def buildSequenceCreationNode( provider, node, source_ref ):
    # Sequence creation. Tries to avoid creations with only constant elements. Would be
    # caught by optimization, but would be useless churn. For mutable constants we cannot
    # do it though.

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

        return ExpressionConstantRef(
            constant   = const_type( element.getConstant() for element in elements ),
            source_ref = source_ref
        )
    else:
        if sequence_kind == "TUPLE":
            return ExpressionMakeTuple(
                elements   = elements,
                source_ref = source_ref
            )
        elif sequence_kind == "LIST":
            return ExpressionMakeList(
                elements   = elements,
                source_ref = source_ref
            )
        elif sequence_kind == "SET":
            return ExpressionMakeSet(
                elements   = elements,
                source_ref = source_ref
            )
        else:
            assert False, sequence_kind


def buildDictionaryNode( provider, node, source_ref ):
    # Create dictionary node. Tries to avoid it for constant values that are not mutable.

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

        return ExpressionConstantRef(
            constant   = constant_value,
            source_ref = source_ref
        )
    else:
        return ExpressionMakeDict(
            pairs      = [
                ExpressionKeyValuePair( key, value, key.getSourceReference() )
                for key, value in
                zip( keys, values )
            ],
            source_ref = source_ref
        )

def buildConditionNode( provider, node, source_ref ):
    # Conditional statements may have one or two branches. We will never see an "elif",
    # because that's already dealt with by module "ast", which turns it into nested
    # conditional statements.

    return StatementConditional(
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

def buildTryFinallyNode( provider, node, source_ref ):
    # Try/finally node statements.

    return StatementTryFinally(
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

def buildTryNode( provider, node, source_ref ):
    # Note: This variant is used for Python3.3 or higher only, older stuff uses the above
    # ones, this one merges try/except with try/finally in the "ast". We split it up
    # again, as it's logically separated of course.
    return StatementTryFinally(
        tried      = StatementsSequence(
            statements = (
                buildTryExceptionNode(
                    provider   = provider,
                    node       = node,
                    source_ref = source_ref
                ),
            ),
            source_ref = source_ref
        ),
        final      = buildStatementsNode(
            provider   = provider,
            nodes      = node.finalbody,
            source_ref = source_ref
        ),
        source_ref = source_ref
    )

def buildRaiseNode( provider, node, source_ref ):
    # Raise statements. Under Python2 they may have type, value and traceback attached,
    # for Python3, you can only give type (actually value) and cause.

    if Utils.python_version < 300:
        return StatementRaiseException(
            exception_type  = buildNode( provider, node.type, source_ref, allow_none = True ),
            exception_value = buildNode( provider, node.inst, source_ref, allow_none = True ),
            exception_trace = buildNode( provider, node.tback, source_ref, allow_none = True ),
            exception_cause = None,
            source_ref      = source_ref
        )
    else:
        return StatementRaiseException(
            exception_type  = buildNode( provider, node.exc, source_ref, allow_none = True ),
            exception_value = None,
            exception_trace = None,
            exception_cause = buildNode( provider, node.cause, source_ref, allow_none = True ),
            source_ref      = source_ref
        )

def buildSubscriptNode( provider, node, source_ref ):
    # Subscript expression nodes.

    assert getKind( node.ctx ) == "Load", source_ref

    # The subscribt "[]" operator is one of many different things. This is expressed by
    # this kind, there are "slice" lookups (two values, even if one is using default), and
    # then "index" lookups. The form with three argument is really an "index" lookup, with
    # a slice object. And the "..." lookup is also an index loopup, with it as the
    # argument. So this splits things into two different operations, "subscript" with a
    # single "subscript" object. Or a slice lookup with a lower and higher boundary. These
    # things should behave similar, but they are different slots.
    kind = getKind( node.slice )

    if kind == "Index":
        return ExpressionSubscriptLookup(
            expression = buildNode( provider, node.value, source_ref ),
            subscript  = buildNode( provider, node.slice.value, source_ref ),
            source_ref = source_ref
        )
    elif kind == "Slice":
        lower = buildNode( provider, node.slice.lower, source_ref, True )
        upper = buildNode( provider, node.slice.upper, source_ref, True )

        if node.slice.step is not None:
            step = buildNode( provider, node.slice.step,  source_ref )

            return ExpressionSubscriptLookup(
                expression = buildNode( provider, node.value, source_ref ),
                subscript  = ExpressionSliceObject(
                    lower      = lower,
                    upper      = upper,
                    step       = step,
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        else:
            return ExpressionSliceLookup(
                expression = buildNode( provider, node.value, source_ref ),
                lower      = lower,
                upper      = upper,
                source_ref = source_ref
            )
    elif kind == "ExtSlice":
        return ExpressionSubscriptLookup(
            expression = buildNode( provider, node.value, source_ref ),
            subscript  = buildExtSliceNode( provider, node, source_ref ),
            source_ref = source_ref
        )
    elif kind == "Ellipsis":
        return ExpressionSubscriptLookup(
            expression = buildNode( provider, node.value, source_ref ),
            subscript  = ExpressionConstantRef(
                constant   = Ellipsis,
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    else:
        assert False, kind

def buildImportModulesNode( node, source_ref ):
    # Import modules statement. As described in the developer manual, these statements can
    # be treated as several ones.

    import_names   = [
        ( import_desc.name, import_desc.asname )
        for import_desc in
        node.names
    ]

    import_nodes = []

    for import_desc in import_names:
        module_name, local_name = import_desc

        module_topname = module_name.split(".")[0]

        # Note: The "level" of import is influenced by the future absolute imports.
        level = 0 if source_ref.getFutureSpec().isAbsoluteImport() else -1

        if local_name:
            import_node = ExpressionImportModule(
                module_name = module_name,
                import_list = None,
                level       = level,
                source_ref  = source_ref
            )

            for import_name in module_name.split(".")[1:]:
                import_node = ExpressionImportName(
                    module      = import_node,
                    import_name = import_name,
                    source_ref  = source_ref
                )
        else:
            import_node = ExpressionImportModule(
                module_name = module_name,
                import_list = None,
                level       = level,
                source_ref  = source_ref
            )

        # If a name was given, use the one provided, otherwise the import gives the top
        # level package name given for assignment of the imported module.

        import_nodes.append(
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetVariableRef(
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
    return makeStatementsSequenceOrStatement(
        statements = import_nodes,
        source_ref = source_ref
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
    elif object_name == "barry_as_FLUFL" and Utils.python_version >= 300:
        future_spec.enableBarry()
    elif object_name == "braces":
        SyntaxErrors.raiseSyntaxError(
            "not a chance",
            source_ref
        )
    elif object_name in ( "nested_scopes", "generators", "with_statement" ):
        # These are enabled in all cases already.
        pass
    else:
        SyntaxErrors.raiseSyntaxError(
            "future feature %s is not defined" % object_name,
            source_ref
        )

def buildImportFromNode( provider, node, source_ref ):
    # "from .. import .." statements. This may trigger a star import, or multiple names
    # being looked up from the given module variable name.

    module_name = node.module if node.module is not None else ""
    level = node.level

    # Importing from "__future__" module may enable flags.
    if module_name == "__future__":
        assert provider.isPythonModule() or source_ref.isExecReference()

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
        if not provider.isPythonModule() and Utils.python_version >= 300:
            SyntaxErrors.raiseSyntaxError(
                "import * only allowed at module level",
                provider.getSourceReference()
            )

        if provider.isExpressionFunctionBody():
            provider.markAsStarImportContaining()

        return StatementImportStar(
            module_import = ExpressionImportModule(
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
                StatementAssignmentVariable(
                    variable_ref = ExpressionTargetVariableRef(
                        variable_name = target_name,
                        source_ref    = source_ref
                    ),
                    source     = ExpressionImportName(
                        module      = ExpressionImportModule(
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
        return StatementsSequence(
            statements = import_nodes,
            source_ref = source_ref
        )

def buildPrintNode( provider, node, source_ref ):
    # "print" statements, should only occur with Python2.

    return StatementPrint(
        newline    = node.nl,
        dest       = buildNode( provider, node.dest, source_ref, allow_none = True ),
        values     = buildNodeList( provider, node.values, source_ref ),
        source_ref = source_ref
    )

def buildExecNode( provider, node, source_ref ):
    # "exec" statements, should only occur with Python2.

    exec_globals = node.globals
    exec_locals = node.locals
    body = node.body

    orig_globals = exec_globals

    # Handle exec(a,b,c) to be same as exec a, b, c
    if exec_locals is None and exec_globals is None and getKind( body ) == "Tuple":
        parts = body.elts
        body  = parts[0]

        if len( parts ) > 1:
            exec_globals = parts[1]

            if len( parts ) > 2:
                exec_locals = parts[2]
        else:
            return StatementRaiseException(
                exception_type = ExpressionBuiltinExceptionRef(
                    exception_name = "TypeError",
                    source_ref     = source_ref
                ),
                exception_value = ExpressionConstantRef(
                    constant   = "exec: arg 1 must be a string, file, or code object",
                    source_ref = source_ref
                ),
                exception_trace = None,
                exception_cause = None,
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

    return StatementExec(
        source_code = buildNode( provider, body, source_ref ),
        globals_arg = globals_node,
        locals_arg  = locals_node,
        source_ref  = source_ref
    )


def handleGlobalDeclarationNode( provider, node, source_ref ):
    # The source reference of the global really doesn't matter, pylint: disable=W0613

    # Need to catch the error of declaring a parameter variable as global ourselves
    # here. The AST parsing doesn't catch it.
    try:
        parameters = provider.getParameters()

        for variable_name in node.names:
            if variable_name in parameters.getParameterNames():
                SyntaxErrors.raiseSyntaxError(
                    reason     = "name '%s' is %s and global" % (
                        variable_name,
                        "local" if Utils.python_version < 300 else "parameter"
                    ),
                    source_ref = provider.getSourceReference()
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

        provider.registerProvidedVariable(
            variable = closure_variable
        )

    return None

def handleNonlocalDeclarationNode( provider, node, source_ref ):
    # The source reference of the nonlocal really doesn't matter, pylint: disable=W0613

    # Need to catch the error of declaring a parameter variable as global ourselves
    # here. The AST parsing doesn't catch it, but we can do it here.
    parameters = provider.getParameters()

    for variable_name in node.names:
        if variable_name in parameters.getParameterNames():
            SyntaxErrors.raiseSyntaxError(
                reason       = "name '%s' is parameter and nonlocal" % (
                    variable_name
                ),
                source_ref   = None if Options.isFullCompat() else source_ref,
                display_file = not Options.isFullCompat(),
                display_line = not Options.isFullCompat()
            )

    provider.addNonlocalsDeclaration( node.names, source_ref )

    return None


def buildStringNode( node, source_ref ):
    assert type( node.s ) in ( str, unicode )

    return ExpressionConstantRef(
        constant   = node.s,
        source_ref = source_ref
    )

def buildNumberNode( node, source_ref ):
    assert type( node.n ) in ( int, long, float, complex ), type( node.n )

    return ExpressionConstantRef(
        constant   = node.n,
        source_ref = source_ref
    )

def buildBytesNode( node, source_ref ):
    return ExpressionConstantRef(
        constant   = node.s,
        source_ref = source_ref
    )

def buildEllipsisNode( source_ref ):
    return ExpressionConstantRef(
        constant   = Ellipsis,
        source_ref = source_ref
    )

def buildAttributeNode( provider, node, source_ref ):
    return ExpressionAttributeLookup(
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
                node.col_offset if provider.isPythonModule() else node.col_offset+4
            )
        )

    if node.value is not None:
        return StatementReturn(
            expression = buildNode( provider, node.value, source_ref ),
            source_ref = source_ref
        )
    else:
        return StatementReturn(
            expression = ExpressionConstantRef(
                constant   = None,
                source_ref = source_ref
            ),
            source_ref = source_ref
        )


def buildYieldNode( provider, node, source_ref ):
    if provider.isPythonModule():
        SyntaxErrors.raiseSyntaxError(
            "'yield' outside function",
            source_ref,
            None if Utils.python_version < 300 else node.col_offset
        )

    provider.markAsGenerator()

    if node.value is not None:
        return ExpressionYield(
            expression = buildNode( provider, node.value, source_ref ),
            source_ref = source_ref
        )
    else:
        return ExpressionYield(
            expression = ExpressionConstantRef(
                constant   = None,
                source_ref = source_ref
            ),
            source_ref = source_ref
        )

def buildExprOnlyNode( provider, node, source_ref ):
    return StatementExpressionOnly(
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
        return ExpressionOperationUnary(
            operator   = getKind( node.op ),
            operand    = buildNode( provider, node.operand, source_ref ),
            source_ref = source_ref
        )


def buildBinaryOpNode( provider, node, source_ref ):
    operator = getKind( node.op )

    if operator == "Div" and source_ref.getFutureSpec().isFutureDivision():
        operator = "TrueDiv"

    return ExpressionOperationBinary(
        operator   = operator,
        left       = buildNode( provider, node.left, source_ref ),
        right      = buildNode( provider, node.right, source_ref ),
        source_ref = source_ref
    )

def buildReprNode( provider, node, source_ref ):
    return ExpressionOperationUnary(
        operator   = "Repr",
        operand    = buildNode( provider, node.value, source_ref ),
        source_ref = source_ref
    )

def buildConditionalExpressionNode( provider, node, source_ref ):
    return ExpressionConditional(
        condition      = buildNode( provider, node.test, source_ref ),
        yes_expression = buildNode( provider, node.body, source_ref ),
        no_expression  = buildNode( provider, node.orelse, source_ref ),
        source_ref     = source_ref
    )


setBuildDispatchers(
    path_args3 = {
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
        "Global"       : handleGlobalDeclarationNode,
        "Nonlocal"     : handleNonlocalDeclarationNode,
        "TryExcept"    : buildTryExceptionNode,
        "TryFinally"   : buildTryFinallyNode,
        "Try"          : buildTryNode,
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
    },
    path_args2 = {
        "Import"       : buildImportModulesNode,
        "Str"          : buildStringNode,
        "Num"          : buildNumberNode,
        "Bytes"        : buildBytesNode,
    },
    path_args1 = {
        "Ellipsis"     : buildEllipsisNode,
        "Continue"     : StatementContinueLoop,
        "Break"        : StatementBreakLoop,
    }
)

def buildParseTree( provider, source_code, source_ref ):
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
        source_ref = source_ref,
        frame      = True
    )

    provider.setDoc( doc )
    provider.setBody( result )

    return result

imported_modules = {}

def addImportedModule( module_relpath, imported_module ):
    imported_modules[ module_relpath ] = imported_module

def isImportedPath( module_relpath ):
    return module_relpath in imported_modules

def getImportedModule( module_relpath ):
    return imported_modules[ module_relpath ]

def getImportedModules():
    return imported_modules.values()


def buildModuleTree( filename, package, is_top, is_main ):
    # Many variables, branches, due to the many cases, pylint: disable=R0912

    assert package is None or type( package ) is str

    if is_main and Utils.isDir( filename ):
        source_filename = Utils.joinpath( filename, "__main__.py" )

        if not Utils.isFile( source_filename ):
            sys.stderr.write(
                "%s: can't find '__main__' module in '%s'\n" % (
                    Utils.basename( sys.argv[0] ),
                    filename
                )
            )
            sys.exit( 2 )

        filename = source_filename

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

            if "." in module_name:
                sys.stderr.write(
                    "Error, '%s' is not a proper python module name.\n" % (
                        module_name
                    )
                )

                sys.exit( 2 )

        result = PythonModule(
            name       = module_name,
            package    = package,
            is_main    = is_main,
            source_ref = source_ref
        )
    elif Utils.isDir( filename ) and Utils.isFile( Utils.joinpath( filename, "__init__.py" ) ):
        source_filename = Utils.joinpath( filename, "__init__.py" )

        if is_top:
            source_ref = SourceCodeReferences.fromFilename(
                filename    = Utils.abspath( source_filename ),
                future_spec = FutureSpec()
            )

            package_name = Utils.splitpath( filename )[-1]
        else:
            source_ref = SourceCodeReferences.fromFilename(
                filename    = Utils.abspath( source_filename ),
                future_spec = FutureSpec()
            )

            package_name = Utils.basename( filename )

        result = PythonPackage(
            name       = package_name,
            package    = package,
            source_ref = source_ref
        )
    else:
        sys.stderr.write(
            "%s: can't open file '%s'.\n" % (
                Utils.basename( sys.argv[0] ),
                filename
            )
        )
        sys.exit( 2 )

    if not Options.shallHaveStatementLines():
        source_ref = source_ref.atInternal()

    source_code = readSourceCodeFromFilename( source_filename )

    buildParseTree(
        provider    = result,
        source_code = source_code,
        source_ref  = source_ref
    )

    addImportedModule( Utils.relpath( filename ), result )

    completeVariableClosures( result )

    return result
