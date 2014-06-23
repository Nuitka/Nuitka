#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

Does all the Python parsing and puts it into a tree structure for use in later
stages of the compilation process.

At the bottom of the file, the dispatching is happening. One function deals
with every node kind as found in the AST. The parsing is centered around the
module "ast" output.

Many higher level language features and translated into lower level ones.

Inplace assignments, for loops, while loops, classes, complex calls, with
statements, and even or/and etc. are all translated to simpler constructs.

The output of this module is a node tree, which contains only relatively low
level operations. A property of the output module is also an overlaid tree
of provider structure that indicates variable provision.

Classes are handled in a separate module. They are re-formulated into functions
producing dictionaries used to call the metaclass with.

Try/except/else statements are handled in a separate module. They are
re-formulated into using a temporary variable to track if the else branch
should execute.

Try/finally statements are handled in a separate module. They are re-formulated
to use a nested try/finally for (un)publishing the exception for Python3.

With statements are handled in a separate module. They are re-formulated into
special attribute lookups for "__enter__" and "__exit__", calls of them,
catching and passing in exceptions raised.

"""


import ast
import sys

from nuitka import (
    Importing,
    Options,
    SourceCodeReferences,
    SyntaxErrors,
    Tracing,
    Utils
)
from nuitka.__past__ import long, unicode  # pylint: disable=W0622
from nuitka.nodes.AssignNodes import StatementAssignmentVariable
from nuitka.nodes.AttributeNodes import ExpressionAttributeLookup
from nuitka.nodes.ConditionalNodes import (
    ExpressionConditional,
    StatementConditional
)
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.ExceptionNodes import StatementRaiseException
from nuitka.nodes.FutureSpecs import FutureSpec
from nuitka.nodes.ImportNodes import (
    ExpressionImportModule,
    ExpressionImportName,
    StatementImportStar
)
from nuitka.nodes.LoopNodes import StatementBreakLoop, StatementContinueLoop
from nuitka.nodes.ModuleNodes import (
    PythonMainModule,
    PythonModule,
    PythonPackage,
    PythonShlibModule
)
from nuitka.nodes.OperatorNodes import (
    ExpressionOperationBinary,
    ExpressionOperationUnary
)
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.SliceNodes import ExpressionSliceLookup, ExpressionSliceObject
from nuitka.nodes.StatementNodes import (
    StatementExpressionOnly,
    StatementsSequence
)
from nuitka.nodes.SubscriptNodes import ExpressionSubscriptLookup
from nuitka.nodes.VariableRefNodes import (
    ExpressionTargetVariableRef,
    ExpressionVariableRef
)

from .Helpers import (
    applyLaterWrappers,
    buildNode,
    buildNodeList,
    buildStatementsNode,
    extractDocFromBody,
    getBuildContext,
    getKind,
    makeDictCreationOrConstant,
    makeModuleFrame,
    makeSequenceCreationOrConstant,
    makeStatementsSequenceOrStatement,
    mergeStatements,
    setBuildDispatchers
)
from .ImportCache import addImportedModule
from .ReformulationAssertStatements import buildAssertNode
from .ReformulationAssignmentStatements import (
    buildAssignNode,
    buildDeleteNode,
    buildExtSliceNode,
    buildInplaceAssignNode
)
from .ReformulationBooleanExpressions import buildBoolOpNode
from .ReformulationCallExpressions import buildCallNode
from .ReformulationClasses import buildClassNode
from .ReformulationComparisonExpressions import buildComparisonNode
from .ReformulationContractionExpressions import (
    buildDictContractionNode,
    buildGeneratorExpressionNode,
    buildListContractionNode,
    buildSetContractionNode
)
from .ReformulationExecStatements import buildExecNode
from .ReformulationFunctionStatements import buildFunctionNode
from .ReformulationLambdaExpressions import buildLambdaNode
from .ReformulationLoopStatements import buildForLoopNode, buildWhileLoopNode
from .ReformulationNamespacePackages import createNamespacePackage
from .ReformulationPrintStatements import buildPrintNode
from .ReformulationTryExceptStatements import buildTryExceptionNode
from .ReformulationTryFinallyStatements import (
    buildTryFinallyNode,
    makeTryFinallyIndicator
)
from .ReformulationWithStatements import buildWithNode
from .ReformulationYieldExpressions import buildYieldFromNode, buildYieldNode
from .SourceReading import readSourceCodeFromFilename
from .VariableClosure import completeVariableClosures


def buildVariableReferenceNode(provider, node, source_ref):
    # Python3 is influenced by the mere use of a variable name. So we need to
    # remember it, esp. for cases, where it is optimized away.
    if Utils.python_version >= 300 and \
       node.id == "super" and \
       provider.isExpressionFunctionBody():
        provider.markAsClassClosureTaker()

    return ExpressionVariableRef(
        variable_name = node.id,
        source_ref    = source_ref
    )

# Python3.4 only, True and False, are not given as variables anymore.
def buildNamedConstantNode(node, source_ref):
    return ExpressionConstantRef(
        constant   = node.value,
        source_ref = source_ref
    )

def buildSequenceCreationNode(provider, node, source_ref):
    return makeSequenceCreationOrConstant(
        sequence_kind = getKind(node).upper(),
        elements      = buildNodeList(provider, node.elts, source_ref),
        source_ref    = source_ref
    )


def buildDictionaryNode(provider, node, source_ref):
    return makeDictCreationOrConstant(
        keys       = buildNodeList(provider, node.keys, source_ref),
        values     = buildNodeList(provider, node.values, source_ref),
        lazy_order = False,
        source_ref = source_ref
    )

def buildConditionNode(provider, node, source_ref):
    # Conditional statements may have one or two branches. We will never see an
    # "elif", because that's already dealt with by module "ast", which turns it
    # into nested conditional statements.

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


def _buildTryFinallyNode(provider, node, source_ref):
    # Try/finally node statements of old style.

    return buildTryFinallyNode(
        provider    = provider,
        build_tried = lambda : buildStatementsNode(
            provider   = provider,
            nodes      = node.body,
            source_ref = source_ref
        ),
        node        = node,
        source_ref  = source_ref
    )


def buildTryNode(provider, node, source_ref):
    # Note: This variant is used for Python3.3 or higher only, older stuff uses
    # the above ones, this one merges try/except with try/finally in the
    # "ast". We split it up again, as it's logically separated of course.

    # Shortcut missing try/finally.
    if not node.handlers:
        return _buildTryFinallyNode(provider, node, source_ref)

    if not node.finalbody:
        return buildTryExceptionNode(
            provider   = provider,
            node       = node,
            source_ref = source_ref
        )

    return buildTryFinallyNode(
        provider    = provider,
        build_tried = lambda : StatementsSequence(
            statements = mergeStatements(
                (
                    buildTryExceptionNode(
                        provider   = provider,
                        node       = node,
                        source_ref = source_ref
                    ),
                )
            ),
            source_ref = source_ref
        ),
        node        = node,
        source_ref  = source_ref
    )


def buildRaiseNode(provider, node, source_ref):
    # Raise statements. Under Python2 they may have type, value and traceback
    # attached, for Python3, you can only give type (actually value) and cause.

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

def buildSubscriptNode(provider, node, source_ref):
    # Subscript expression nodes.

    assert getKind( node.ctx ) == "Load", source_ref

    # The subscribt "[]" operator is one of many different things. This is
    # expressed by this kind, there are "slice" lookups (two values, even if one
    # is using default), and then "index" lookups. The form with three argument
    # is really an "index" lookup, with a slice object. And the "..." lookup is
    # also an index loopup, with it as the argument. So this splits things into
    # two different operations, "subscript" with a single "subscript" object. Or
    # a slice lookup with a lower and higher boundary. These things should
    # behave similar, but they are different slots.
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

def buildImportModulesNode(node, source_ref):
    # Import modules statement. As described in the developer manual, these
    # statements can be treated as several ones.

    import_names   = [
        ( import_desc.name, import_desc.asname )
        for import_desc in
        node.names
    ]

    import_nodes = []

    for import_desc in import_names:
        module_name, local_name = import_desc

        module_topname = module_name.split(".")[0]

        # Note: The "level" of import is influenced by the future absolute
        # imports.
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

        # If a name was given, use the one provided, otherwise the import gives
        # the top level package name given for assignment of the imported
        # module.

        import_nodes.append(
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetVariableRef(
                    variable_name = local_name
                                      if local_name is not None else
                                    module_topname,
                    source_ref    = source_ref
                ),
                source     = import_node,
                source_ref = source_ref
            )
        )

    # Note: Each import is sequential. It will potentially succeed, and the
    # failure of a later one is not changing that one bit . We can therefore
    # have a sequence of imports that only import one thing therefore.
    return makeStatementsSequenceOrStatement(
        statements = import_nodes,
        source_ref = source_ref
    )

def enableFutureFeature(object_name, future_spec, source_ref):
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

# For checking afterwards, if it was at the beginning of the file.
_future_import_nodes = []

def buildImportFromNode(provider, node, source_ref):
    # "from .. import .." statements. This may trigger a star import, or
    # multiple names being looked up from the given module variable name.

    module_name = node.module if node.module is not None else ""
    level = node.level

    # Importing from "__future__" module may enable flags.
    if module_name == "__future__":
        if not provider.isPythonModule() and not source_ref.isExecReference():
            SyntaxErrors.raiseSyntaxError(
                reason     = """\
from __future__ imports must occur at the beginning of the file""",
                col_offset = 8
                  if Utils.python_version >= 300 or \
                  not Options.isFullCompat()
                else None,
                source_ref = source_ref
            )


        for import_desc in node.names:
            object_name, _local_name = import_desc.name, import_desc.asname

            enableFutureFeature(
                object_name = object_name,
                future_spec = source_ref.getFutureSpec(),
                source_ref  = source_ref
            )

        # Remember it for checks to be applied once module is complete.
        node.source_ref = source_ref
        _future_import_nodes.append(node)

    target_names = []
    import_names = []

    for import_desc in node.names:
        object_name, local_name = import_desc.name, import_desc.asname

        if object_name == "*":
            target_names.append(None)
        else:
            target_names.append(
                local_name
                  if local_name is not None else
                object_name
            )

        import_names.append(object_name)

    if None in target_names:
        # More than "*" is a syntax error in Python, need not care about this at
        # all, it's only allowed value for import list in  this case.
        assert target_names == [None]

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
                import_list = ("*",),
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
                            import_list = tuple(import_names),
                            level       = level,
                            source_ref  = source_ref
                        ),
                        import_name = import_name,
                        source_ref  = source_ref
                    ),
                    source_ref = source_ref
                )
            )

        # Note: Each import is sequential. It can succeed, and the failure of a
        # later one is not changing one. We can therefore have a sequence of
        # imports that only import one thing therefore.
        return StatementsSequence(
            statements = import_nodes,
            source_ref = source_ref
        )


def handleGlobalDeclarationNode(provider, node, source_ref):

    if not source_ref.isExecReference():
        # On the module level, there is nothing to do.
        if provider.isPythonModule():
            return None

        # Need to catch the error of declaring a parameter variable as global
        # ourselves here. The AST parsing doesn't catch it.
        try:
            parameters = provider.getParameters()

            for variable_name in node.names:
                if variable_name in parameters.getParameterNames():
                    SyntaxErrors.raiseSyntaxError(
                        reason     = "name '%s' is %s and global" % (
                            variable_name,
                            "local"
                              if Utils.python_version < 300 else
                            "parameter"
                        ),
                        source_ref = (
                            source_ref
                              if not Options.isFullCompat() or \
                                 Utils.python_version >= 340 else
                            provider.getSourceReference()
                        )
                    )
        except AttributeError:
            pass

    module = provider.getParentModule()

    for variable_name in node.names:
        closure_variable = None

        # Re-use already taken global variables, in order to avoid creating yet
        # another instance, esp. as the markups could then potentially not be
        # shared.
        if provider.hasTakenVariable( variable_name ):
            closure_variable = provider.getTakenVariable( variable_name )

            if not closure_variable.isModuleVariableReference():
                closure_variable = None

        if closure_variable is None:
            module_variable = module.getVariableForAssignment(
                variable_name = variable_name
            )

            closure_variable = provider.addClosureVariable(
                variable = module_variable
            )

        assert closure_variable.isModuleVariableReference()

        closure_variable.markFromGlobalStatement()

        if source_ref.isExecReference():
            closure_variable.markFromExecStatement()

        provider.registerProvidedVariable(
            variable = closure_variable
        )

    return None

def handleNonlocalDeclarationNode(provider, node, source_ref):
    # The source reference of the nonlocal really doesn't matter.
    # pylint: disable=W0613

    # Need to catch the error of declaring a parameter variable as global
    # ourselves here. The AST parsing doesn't catch it, but we can do it here.
    parameters = provider.getParameters()

    for variable_name in node.names:
        if variable_name in parameters.getParameterNames():
            SyntaxErrors.raiseSyntaxError(
                reason       = "name '%s' is parameter and nonlocal" % (
                    variable_name
                ),
                source_ref   = None
                                 if Options.isFullCompat() and \
                                 Utils.python_version < 340 else
                               source_ref,
                display_file = not Options.isFullCompat() or \
                               Utils.python_version >= 340,
                display_line = not Options.isFullCompat() or \
                               Utils.python_version >= 340
            )

    provider.addNonlocalsDeclaration(node.names, source_ref)

    return None


def buildStringNode(node, source_ref):
    assert type(node.s) in (str, unicode)

    return ExpressionConstantRef(
        constant      = node.s,
        source_ref    = source_ref,
        user_provided = True
    )


def buildNumberNode(node, source_ref):
    assert type( node.n ) in ( int, long, float, complex ), type( node.n )

    return ExpressionConstantRef(
        constant      = node.n,
        source_ref    = source_ref,
        user_provided = True
    )


def buildBytesNode(node, source_ref):
    return ExpressionConstantRef(
        constant      = node.s,
        source_ref    = source_ref,
        user_provided = True
    )


def buildEllipsisNode(source_ref):
    return ExpressionConstantRef(
        constant      = Ellipsis,
        source_ref    = source_ref,
        user_provided = True
    )


def buildStatementContinueLoop(provider, node, source_ref):
    if getBuildContext() == "finally":
        if not Options.isFullCompat() or Utils.python_version >= 300:
            col_offset = node.col_offset - 9
        else:
            col_offset = None

        if Utils.python_version >= 300 and Options.isFullCompat():
            source_line = ""
        else:
            source_line = None

        SyntaxErrors.raiseSyntaxError(
            "'continue' not supported inside 'finally' clause",
            source_ref,
            col_offset  = col_offset,
            source_line = source_line
        )


    return makeTryFinallyIndicator(
        provider     = provider,
        statement    = StatementContinueLoop(
            source_ref = source_ref
        ),
        is_loop_exit = True
    )


def buildStatementBreakLoop(provider, node, source_ref):
    # A bit unusual, we need the provider, but not the node,
    # pylint: disable=W0613

    return makeTryFinallyIndicator(
        provider     = provider,
        statement    = StatementBreakLoop(
            source_ref = source_ref
        ),
        is_loop_exit = True
    )


def buildAttributeNode(provider, node, source_ref):
    return ExpressionAttributeLookup(
        expression     = buildNode( provider, node.value, source_ref ),
        attribute_name = node.attr,
        source_ref     = source_ref
    )


def buildReturnNode(provider, node, source_ref):
    if not provider.isExpressionFunctionBody() or \
       provider.isClassDictCreation():
        SyntaxErrors.raiseSyntaxError(
            "'return' outside function",
            source_ref,
            None if Utils.python_version < 300 else (
                node.col_offset
                  if provider.isPythonModule() else
                node.col_offset+4
            )
        )

    expression = buildNode(provider, node.value, source_ref, allow_none = True)

    if expression is None:
        expression = ExpressionConstantRef(
            constant      = None,
            source_ref    = source_ref,
            user_provided = True
        )


    return makeTryFinallyIndicator(
        provider    = provider,
        statement   = StatementReturn(
            expression = expression,
            source_ref = source_ref
        ),
        is_loop_exit = False
    )


def buildExprOnlyNode(provider, node, source_ref):
    return StatementExpressionOnly(
        expression = buildNode( provider, node.value, source_ref ),
        source_ref = source_ref
    )


def buildUnaryOpNode(provider, node, source_ref):
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


def buildBinaryOpNode(provider, node, source_ref):
    operator = getKind(node.op)

    if operator == "Div" and source_ref.getFutureSpec().isFutureDivision():
        operator = "TrueDiv"

    return ExpressionOperationBinary(
        operator   = operator,
        left       = buildNode(provider, node.left, source_ref),
        right      = buildNode(provider, node.right, source_ref),
        source_ref = source_ref
    )


def buildReprNode(provider, node, source_ref):
    return ExpressionOperationUnary(
        operator   = "Repr",
        operand    = buildNode(provider, node.value, source_ref),
        source_ref = source_ref
    )


def buildConditionalExpressionNode(provider, node, source_ref):
    return ExpressionConditional(
        condition      = buildNode(provider, node.test, source_ref),
        yes_expression = buildNode(provider, node.body, source_ref),
        no_expression  = buildNode(provider, node.orelse, source_ref),
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
        "TryFinally"   : _buildTryFinallyNode,
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
        "YieldFrom"    : buildYieldFromNode,
        "Expr"         : buildExprOnlyNode,
        "UnaryOp"      : buildUnaryOpNode,
        "BinOp"        : buildBinaryOpNode,
        "Repr"         : buildReprNode,
        "AugAssign"    : buildInplaceAssignNode,
        "IfExp"        : buildConditionalExpressionNode,
        "Continue"     : buildStatementContinueLoop,
        "Break"        : buildStatementBreakLoop,
    },
    path_args2 = {
        "NameConstant" : buildNamedConstantNode,
        "Import"       : buildImportModulesNode,
        "Str"          : buildStringNode,
        "Num"          : buildNumberNode,
        "Bytes"        : buildBytesNode,
    },
    path_args1 = {
        "Ellipsis"     : buildEllipsisNode,
    }
)

def buildParseTree(provider, source_code, source_ref, is_module, is_main):
    # There are a bunch of branches here, mostly to deal with version
    # differences for module default variables. pylint: disable=R0912

    # Workaround: ast.parse cannot cope with some situations where a file is not
    # terminated by a new line.
    if not source_code.endswith("\n"):
        source_code = source_code + "\n"

    body = ast.parse(source_code, source_ref.getFilename())
    assert getKind(body) == "Module"

    line_offset = source_ref.getLineNumber() - 1

    if line_offset > 0:
        for created_node in ast.walk(body):
            if hasattr(created_node, "lineno"):
                created_node.lineno += line_offset

    body, doc = extractDocFromBody(body)

    result = buildStatementsNode(
        provider   = provider,
        nodes      = body,
        source_ref = source_ref
    )

    # Check if a __future__ imports really were at the beginning of the file.
    for node in body:
        if node in _future_import_nodes:
            _future_import_nodes.remove(node)
        else:
            if _future_import_nodes:
                SyntaxErrors.raiseSyntaxError(
                    reason     = """\
from __future__ imports must occur at the beginning of the file""",
                    col_offset = 1
                      if Utils.python_version >= 300 or \
                      not Options.isFullCompat() else
                    None,
                    source_ref = _future_import_nodes[0].source_ref
                )

    internal_source_ref = source_ref.atInternal()

    statements = []

    if is_module:
        # Add import of "site" module of main programs visibly in the node tree,
        # so recursion and optimization can pick it up, checking its effects.
        if is_main and not sys.flags.no_site:
            statements.append(
                StatementExpressionOnly(
                    expression = ExpressionImportModule(
                        module_name    = "site",
                        import_list    = (),
                        level          = 0,
                        source_ref     = source_ref,
                    ),
                    source_ref  = source_ref
                )
            )

        statements.append(
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetVariableRef(
                    variable_name = "__doc__",
                    source_ref    = internal_source_ref
                ),
                source       = ExpressionConstantRef(
                    constant      = doc,
                    source_ref    = internal_source_ref,
                    user_provided = True
                ),
                source_ref   = internal_source_ref
            )
        )

        statements.append(
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetVariableRef(
                    variable_name = "__file__",
                    source_ref    = internal_source_ref
                ),
                source       = ExpressionConstantRef(
                    constant      = source_ref.getFilename(),
                    source_ref    = internal_source_ref,
                    user_provided = True
                ),
                source_ref   = internal_source_ref
            )
        )

        if provider.isPythonPackage():
            # TODO: __package__ is not set here, but automatically, which makes
            # it invisible though
            statements.append(
                StatementAssignmentVariable(
                    variable_ref = ExpressionTargetVariableRef(
                        variable_name = "__path__",
                        source_ref    = internal_source_ref
                    ),
                    source       = ExpressionConstantRef(
                        constant      = [
                            Utils.dirname(source_ref.getFilename())
                        ],
                        source_ref    = internal_source_ref,
                        user_provided = True
                    ),
                    source_ref   = internal_source_ref
                )
            )

    if Utils.python_version >= 300:
        statements.append(
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetVariableRef(
                    variable_name = "__cached__",
                    source_ref    = internal_source_ref
                ),
                source       = ExpressionConstantRef(
                    constant      = None,
                    source_ref    = internal_source_ref,
                    user_provided = True
                ),
                source_ref   = internal_source_ref
            )
        )


    if Utils.python_version >= 330:
        # For Python3.3, it's set for both packages and non-packages.
        statements.append(
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetVariableRef(
                    variable_name = "__package__",
                    source_ref    = internal_source_ref
                ),
                source       = ExpressionConstantRef(
                    constant      = provider.getFullName()
                                      if provider.isPythonPackage() else
                                    provider.getPackage(),
                    source_ref    = internal_source_ref,
                    user_provided = True
                ),
                source_ref   = internal_source_ref
            )
        )

    needs__initializing__ = not provider.isMainModule() and \
      (Utils.python_version >= 330 and Utils.python_version < 340)

    if needs__initializing__:
        # Set initialzing at the beginning to True
        statements.append(
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetVariableRef(
                    variable_name = "__initializing__",
                    source_ref    = internal_source_ref
                ),
                source       = ExpressionConstantRef(
                    constant      = True,
                    source_ref    = internal_source_ref,
                    user_provided = True
                ),
                source_ref   = internal_source_ref
            )
        )

    # Now the module body if there is any at all.
    if result is not None:
        statements.extend(
            result.getStatements()
        )

    if needs__initializing__:
        # Set initialzing at the beginning to True
        statements.append(
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetVariableRef(
                    variable_name = "__initializing__",
                    source_ref    = internal_source_ref
                ),
                source       = ExpressionConstantRef(
                    constant      = False,
                    source_ref    = internal_source_ref,
                    user_provided = True
                ),
                source_ref   = internal_source_ref
            )
        )



    if is_module:
        result = makeModuleFrame(
            module     = provider,
            statements = statements,
            source_ref = source_ref
        )

        applyLaterWrappers()

        return result
    else:
        assert False


def decideModuleTree(filename, package, is_shlib, is_top, is_main):
    # Many variables, branches, due to the many cases, pylint: disable=R0912

    assert package is None or type(package) is str

    if is_main and Utils.isDir(filename):
        source_filename = Utils.joinpath(filename, "__main__.py")

        if not Utils.isFile(source_filename):
            sys.stderr.write(
                "%s: can't find '__main__' module in '%s'\n" % (
                    Utils.basename(sys.argv[0]),
                    filename
                )
            )
            sys.exit(2)

        filename = source_filename

        main_added = True
    else:
        main_added = False

    if Utils.isFile(filename):
        source_filename = filename

        source_ref = SourceCodeReferences.fromFilename(
            filename    = filename,
            future_spec = FutureSpec()
        )

        if is_main:
            module_name = "__main__"
        else:
            module_name = Utils.basename(filename)

            if module_name.endswith(".py"):
                module_name = module_name[:-3]

            if is_shlib:
                module_name = module_name.split(".")[0]

            if "." in module_name:
                sys.stderr.write(
                    "Error, '%s' is not a proper python module name.\n" % (
                        module_name
                    )
                )

                sys.exit(2)

        if is_shlib:
            result = PythonShlibModule(
                name         = module_name,
                source_ref   = source_ref,
                package_name = package,
            )
        elif is_main:
            result = PythonMainModule(
                source_ref = source_ref,
                main_added = main_added
            )
        else:
            result = PythonModule(
                name         = module_name,
                package_name = package,
                source_ref   = source_ref
            )
    elif Importing.isPackageDir(filename):
        if is_top:
            package_name = Utils.splitpath(filename)[-1]
        else:
            package_name = Utils.basename(filename)

        source_filename = Utils.joinpath(filename, "__init__.py")

        if not Utils.isFile( source_filename ):
            assert Utils.python_version >= 330, source_filename

            source_ref, result = createNamespacePackage(
                package_name = package_name,
                module_relpath = filename
            )
            source_filename = None
        else:
            source_ref = SourceCodeReferences.fromFilename(
                filename    = Utils.abspath( source_filename ),
                future_spec = FutureSpec()
            )

            result = PythonPackage(
                name         = package_name,
                package_name = package,
                source_ref   = source_ref
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

    return result, source_ref, source_filename


def createModuleTree(module, source_ref, source_filename, is_main):
    if Options.isShowProgress():
        memory_watch = Utils.MemoryWatch()

    source_code = readSourceCodeFromFilename( source_filename )

    module_body = buildParseTree(
        provider    = module,
        source_code = source_code,
        source_ref  = source_ref,
        is_module   = True,
        is_main     = is_main
    )

    module.setBody(
        module_body
    )

    completeVariableClosures( module )

    if Options.isShowProgress():
        memory_watch.finish()

        Tracing.printLine(
            "Memory usage changed loading module '%s': %s" % (
                module.getFullName(),
                memory_watch.asStr()
            )
        )

def buildModuleTree(filename, package, is_top, is_main):
    module, source_ref, source_filename = decideModuleTree(
        filename = filename,
        package  = package,
        is_top   = is_top,
        is_main  = is_main,
        is_shlib = False
    )

    addImportedModule( Utils.relpath( filename ), module )

    # If there is source code associated (not the case for namespace packages of
    # Python3.3 or higher, then read it.
    if source_filename is not None:
        createModuleTree(
            module          = module,
            source_ref      = source_ref,
            source_filename = source_filename,
            is_main         = is_main
        )

    return module
