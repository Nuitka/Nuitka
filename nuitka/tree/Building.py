#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

In the "nuitka.tree.Helpers" module, the dispatching is happening. One function
deals with every node kind as found in the AST. The parsing is centered around
the module "ast" output.

Many higher level language features and translated into lower level ones.

In-place assignments, for loops, while loops, classes, complex calls, with
statements, and even or/and etc. are all translated to simpler constructs.

The output of this module is a node tree, which contains only relatively low
level operations. A property of the output is also an overlaid tree of provider
structure that indicates variable provision.

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

import sys

from nuitka import Options, SourceCodeReferences, Tracing
from nuitka.__past__ import long, unicode  # pylint: disable=W0622
from nuitka.importing import Importing
from nuitka.importing.ImportCache import addImportedModule
from nuitka.importing.PreloadedPackages import getPthImportedPackages
from nuitka.nodes.AssignNodes import (
    ExpressionTargetVariableRef,
    StatementAssignmentVariable
)
from nuitka.nodes.AttributeNodes import ExpressionAttributeLookup
from nuitka.nodes.ConditionalNodes import (
    ExpressionConditional,
    StatementConditional
)
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.CoroutineNodes import ExpressionAsyncWait
from nuitka.nodes.ExceptionNodes import StatementRaiseException
from nuitka.nodes.GeneratorNodes import StatementGeneratorReturn
from nuitka.nodes.ImportNodes import (
    ExpressionImportModule,
    ExpressionImportName
)
from nuitka.nodes.LoopNodes import StatementLoopBreak, StatementLoopContinue
from nuitka.nodes.ModuleNodes import (
    CompiledPythonModule,
    CompiledPythonPackage,
    ExpressionModuleFileAttributeRef,
    PythonMainModule,
    PythonShlibModule
)
from nuitka.nodes.OperatorNodes import (
    ExpressionOperationBinary,
    ExpressionOperationUnary
)
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.StatementNodes import StatementExpressionOnly
from nuitka.nodes.VariableRefNodes import ExpressionVariableRef
from nuitka.plugins.Plugins import Plugins
from nuitka.PythonVersions import python_version
from nuitka.tree.ReformulationForLoopStatements import (
    buildAsyncForLoopNode,
    buildForLoopNode
)
from nuitka.tree.ReformulationWhileLoopStatements import buildWhileLoopNode
from nuitka.utils import MemoryUsage, Utils

from . import SyntaxErrors
from .Helpers import (
    buildNode,
    buildStatementsNode,
    extractDocFromBody,
    getBuildContext,
    getKind,
    makeModuleFrame,
    makeStatementsSequence,
    makeStatementsSequenceFromStatement,
    makeStatementsSequenceOrStatement,
    mangleName,
    mergeStatements,
    parseSourceCodeToAst,
    setBuildingDispatchers
)
from .ReformulationAssertStatements import buildAssertNode
from .ReformulationAssignmentStatements import (
    buildAssignNode,
    buildDeleteNode,
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
from .ReformulationDictionaryCreation import buildDictionaryNode
from .ReformulationExecStatements import buildExecNode
from .ReformulationFunctionStatements import (
    buildAsyncFunctionNode,
    buildFunctionNode
)
from .ReformulationImportStatements import (
    buildImportFromNode,
    checkFutureImportsOnlyAtStart
)
from .ReformulationLambdaExpressions import buildLambdaNode
from .ReformulationNamespacePackages import (
    createNamespacePackage,
    createPathAssignment
)
from .ReformulationPrintStatements import buildPrintNode
from .ReformulationSequenceCreation import buildSequenceCreationNode
from .ReformulationSubscriptExpressions import buildSubscriptNode
from .ReformulationTryExceptStatements import buildTryExceptionNode
from .ReformulationTryFinallyStatements import buildTryFinallyNode
from .ReformulationWithStatements import buildAsyncWithNode, buildWithNode
from .ReformulationYieldExpressions import buildYieldFromNode, buildYieldNode
from .SourceReading import readSourceCodeFromFilename
from .VariableClosure import completeVariableClosures


def buildVariableReferenceNode(provider, node, source_ref):
    return ExpressionVariableRef(
        variable_name = mangleName(node.id, provider),
        source_ref    = source_ref
    )


# Python3.4 or higher, True and False, are not given as variables anymore.
def buildNamedConstantNode(node, source_ref):
    return ExpressionConstantRef(
        constant   = node.value,
        source_ref = source_ref
    )


def buildConditionNode(provider, node, source_ref):
    # Conditional statements may have one or two branches. We will never see an
    # "elif", because that's already dealt with by module "ast", which turns it
    # into nested conditional statements.

    return StatementConditional(
        condition  = buildNode(provider, node.test, source_ref),
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
        build_tried = lambda : makeStatementsSequence(
            statements = mergeStatements(
                (
                    buildTryExceptionNode(
                        provider   = provider,
                        node       = node,
                        source_ref = source_ref
                    ),
                ),
                allow_none = True
            ),
            allow_none = True,
            source_ref = source_ref
        ),
        node        = node,
        source_ref  = source_ref
    )


def buildRaiseNode(provider, node, source_ref):
    # Raise statements. Under Python2 they may have type, value and traceback
    # attached, for Python3, you can only give type (actually value) and cause.

    if python_version < 300:
        exception_type  = buildNode(provider, node.type, source_ref, allow_none = True)
        exception_value = buildNode(provider, node.inst, source_ref, allow_none = True)
        exception_trace = buildNode(provider, node.tback, source_ref, allow_none = True)
        exception_cause = None
    else:
        exception_type  = buildNode(provider, node.exc, source_ref, allow_none = True)
        exception_value = None
        exception_trace = None
        exception_cause = buildNode(provider, node.cause, source_ref, allow_none = True)

    result = StatementRaiseException(
        exception_type  = exception_type,
        exception_value = exception_value,
        exception_trace = exception_trace,
        exception_cause = exception_cause,
        source_ref      = source_ref
    )

    if exception_cause is not None:
        result.setCompatibleSourceReference(
            source_ref = exception_cause.getCompatibleSourceReference()
        )
    elif exception_trace is not None:
        result.setCompatibleSourceReference(
            source_ref = exception_trace.getCompatibleSourceReference()
        )
    elif exception_value is not None:
        result.setCompatibleSourceReference(
            source_ref = exception_value.getCompatibleSourceReference()
        )
    elif exception_type is not None:
        result.setCompatibleSourceReference(
            source_ref = exception_type.getCompatibleSourceReference()
        )

    return result

def buildImportModulesNode(provider, node, source_ref):
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

        module_topname = module_name.split('.')[0]

        # Note: The "level" of import is influenced by the future absolute
        # imports.
        level = 0 if source_ref.getFutureSpec().isAbsoluteImport() else -1

        if local_name:
            # If is gets a local name, the real name must be used as a
            # temporary value only, being looked up recursively.

            import_node = ExpressionImportModule(
                module_name = module_name,
                import_list = None,
                level       = level,
                source_ref  = source_ref
            )

            for import_name in module_name.split('.')[1:]:
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
                    variable_name = mangleName(
                        local_name
                          if local_name is not None else
                        module_topname,
                        provider
                    ),
                    source_ref    = source_ref
                ),
                source       = import_node,
                source_ref   = source_ref
            )
        )

    # Note: Each import is sequential. It will potentially succeed, and the
    # failure of a later one is not changing that one bit . We can therefore
    # have a sequence of imports that only import one thing therefore.
    return makeStatementsSequenceOrStatement(
        statements = import_nodes,
        source_ref = source_ref
    )


def handleGlobalDeclarationNode(provider, node, source_ref):

    # On the module level, there is nothing to do. TODO: Probably a warning
    # would be warranted.
    if provider.isCompiledPythonModule():
        return None

    # Need to catch the error of declaring a parameter variable as global
    # ourselves here. The AST parsing doesn't catch it, so we check here.
    if provider.isExpressionFunctionBody():
        parameters = provider.getParameters()

        for variable_name in node.names:
            if variable_name in parameters.getParameterNames():
                SyntaxErrors.raiseSyntaxError(
                    reason     = "name '%s' is %s and global" % (
                        variable_name,
                        "local"
                          if python_version < 300 else
                        "parameter"
                    ),
                    source_ref = (
                        source_ref
                          if not Options.isFullCompat() or \
                             python_version >= 340 else
                        provider.getSourceReference()
                    )
                )

    # The module the "global" statement refers to.
    module = provider.getParentModule()

    # Can give multiple names.
    for variable_name in node.names:
        closure_variable = None

        # Re-use already taken global variables, in order to avoid creating yet
        # another instance, esp. as the indications could then potentially not
        # be shared.
        if provider.hasTakenVariable(variable_name):
            closure_variable = provider.getTakenVariable(variable_name)

            # Only global variables count. Could have a closure reference to
            # a location of a parent function here.
            if not closure_variable.isModuleVariable():
                closure_variable = None

        if closure_variable is None:
            module_variable = module.getVariableForAssignment(
                variable_name = variable_name
            )

            closure_variable = provider.addClosureVariable(
                variable = module_variable
            )

        assert closure_variable.isModuleVariable()

        if python_version < 340 and \
           provider.isExpressionClassBody() and \
           closure_variable.getName() == "__class__":
            SyntaxErrors.raiseSyntaxError(
                reason     = "cannot make __class__ global",
                source_ref = source_ref
            )

        provider.registerProvidedVariable(
            variable = closure_variable
        )

    return None


def handleNonlocalDeclarationNode(provider, node, source_ref):
    # Need to catch the error of declaring a parameter variable as global
    # ourselves here. The AST parsing doesn't catch it, but we can do it here.
    parameter_provider = provider

    while parameter_provider.isExpressionGeneratorObjectBody() or \
          parameter_provider.isExpressionCoroutineObjectBody():
        parameter_provider = parameter_provider.getParentVariableProvider()

    if parameter_provider.isExpressionClassBody():
        parameter_names = ()
    else:
        parameter_names = parameter_provider.getParameters().getParameterNames()

    for variable_name in node.names:
        if variable_name in parameter_names:
            SyntaxErrors.raiseSyntaxError(
                reason       = "name '%s' is parameter and nonlocal" % (
                    variable_name
                ),
                source_ref   = None
                                 if Options.isFullCompat() and \
                                 python_version < 340 else
                               source_ref,
                display_file = not Options.isFullCompat() or \
                               python_version >= 340,
                display_line = not Options.isFullCompat() or \
                               python_version >= 340
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
    assert type(node.n) in (int, long, float, complex), type(node.n)

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


def buildStatementLoopContinue(node, source_ref):
    # Python forbids this, although technically it's probably not much of
    # an issue.
    if getBuildContext() == "finally":
        if not Options.isFullCompat() or python_version >= 300:
            col_offset = node.col_offset - 9
        else:
            col_offset = None

        if python_version >= 300 and Options.isFullCompat():
            source_line = ""
        else:
            source_line = None

        SyntaxErrors.raiseSyntaxError(
            "'continue' not supported inside 'finally' clause",
            source_ref,
            col_offset  = col_offset,
            source_line = source_line
        )

    return StatementLoopContinue(
        source_ref = source_ref
    )


def buildStatementLoopBreak(provider, node, source_ref):
    # A bit unusual, we need the provider, but not the node,
    # pylint: disable=W0613

    return StatementLoopBreak(
        source_ref = source_ref
    )


def buildAttributeNode(provider, node, source_ref):
    return ExpressionAttributeLookup(
        source         = buildNode(provider, node.value, source_ref),
        attribute_name = node.attr,
        source_ref     = source_ref
    )


def buildReturnNode(provider, node, source_ref):
    if provider.isExpressionClassBody() or provider.isCompiledPythonModule():
        SyntaxErrors.raiseSyntaxError(
            "'return' outside function",
            source_ref,
            None if python_version < 300 else (
                node.col_offset
                  if provider.isCompiledPythonModule() else
                node.col_offset+4
            )
        )

    expression = buildNode(provider, node.value, source_ref, allow_none = True)

    if provider.isExpressionGeneratorObjectBody():
        if expression is not None and python_version < 330:
            SyntaxErrors.raiseSyntaxError(
                "'return' with argument inside generator",
                source_ref = source_ref,
            )

    if expression is None:
        expression = ExpressionConstantRef(
            constant      = None,
            source_ref    = source_ref,
            user_provided = True
        )

    if provider.isExpressionGeneratorObjectBody():
        return StatementGeneratorReturn(
            expression = expression,
            source_ref = source_ref
        )
    else:
        return StatementReturn(
            expression = expression,
            source_ref = source_ref
        )


def buildExprOnlyNode(provider, node, source_ref):
    result = StatementExpressionOnly(
        expression = buildNode(provider, node.value, source_ref),
        source_ref = source_ref
    )

    result.setCompatibleSourceReference(
        result.getExpression().getCompatibleSourceReference()
    )

    return result


def buildUnaryOpNode(provider, node, source_ref):
    if getKind(node.op) == "Not":
        return buildBoolOpNode(
            provider   = provider,
            node       = node,
            source_ref = source_ref
        )
    else:
        return ExpressionOperationUnary(
            operator   = getKind(node.op),
            operand    = buildNode(provider, node.operand, source_ref),
            source_ref = source_ref
        )


def buildBinaryOpNode(provider, node, source_ref):
    operator = getKind(node.op)

    if operator == "Div" and source_ref.getFutureSpec().isFutureDivision():
        operator = "TrueDiv"

    left       = buildNode(provider, node.left, source_ref)
    right      = buildNode(provider, node.right, source_ref)

    result = ExpressionOperationBinary(
        operator   = operator,
        left       = left,
        right      = right,
        source_ref = source_ref
    )

    result.setCompatibleSourceReference(
        source_ref = right.getCompatibleSourceReference()
    )

    return result


def buildReprNode(provider, node, source_ref):
    return ExpressionOperationUnary(
        operator   = "Repr",
        operand    = buildNode(provider, node.value, source_ref),
        source_ref = source_ref
    )


def buildConditionalExpressionNode(provider, node, source_ref):
    return ExpressionConditional(
        condition      = buildNode(provider, node.test, source_ref),
        expression_yes = buildNode(provider, node.body, source_ref),
        expression_no  = buildNode(provider, node.orelse, source_ref),
        source_ref     = source_ref
    )


def buildAwaitNode(provider, node, source_ref):
    return ExpressionAsyncWait(
        expression = buildNode(provider, node.value, source_ref),
        source_ref = source_ref
    )


setBuildingDispatchers(
    path_args3 = {
        "Name"              : buildVariableReferenceNode,
        "Assign"            : buildAssignNode,
        "Delete"            : buildDeleteNode,
        "Lambda"            : buildLambdaNode,
        "GeneratorExp"      : buildGeneratorExpressionNode,
        "If"                : buildConditionNode,
        "While"             : buildWhileLoopNode,
        "For"               : buildForLoopNode,
        "AsyncFor"          : buildAsyncForLoopNode,
        "Compare"           : buildComparisonNode,
        "ListComp"          : buildListContractionNode,
        "DictComp"          : buildDictContractionNode,
        "SetComp"           : buildSetContractionNode,
        "Dict"              : buildDictionaryNode,
        "Set"               : buildSequenceCreationNode,
        "Tuple"             : buildSequenceCreationNode,
        "List"              : buildSequenceCreationNode,
        "Global"            : handleGlobalDeclarationNode,
        "Nonlocal"          : handleNonlocalDeclarationNode,
        "TryExcept"         : buildTryExceptionNode,
        "TryFinally"        : _buildTryFinallyNode,
        "Try"               : buildTryNode,
        "Raise"             : buildRaiseNode,
        "Import"            : buildImportModulesNode,
        "ImportFrom"        : buildImportFromNode,
        "Assert"            : buildAssertNode,
        "Exec"              : buildExecNode,
        "With"              : buildWithNode,
        "AsyncWith"         : buildAsyncWithNode,
        "FunctionDef"       : buildFunctionNode,
        "AsyncFunctionDef"  : buildAsyncFunctionNode,
        "Await"             : buildAwaitNode,
        "ClassDef"          : buildClassNode,
        "Print"             : buildPrintNode,
        "Call"              : buildCallNode,
        "Subscript"         : buildSubscriptNode,
        "BoolOp"            : buildBoolOpNode,
        "Attribute"         : buildAttributeNode,
        "Return"            : buildReturnNode,
        "Yield"             : buildYieldNode,
        "YieldFrom"         : buildYieldFromNode,
        "Expr"              : buildExprOnlyNode,
        "UnaryOp"           : buildUnaryOpNode,
        "BinOp"             : buildBinaryOpNode,
        "Repr"              : buildReprNode,
        "AugAssign"         : buildInplaceAssignNode,
        "IfExp"             : buildConditionalExpressionNode,
        "Break"             : buildStatementLoopBreak,
    },
    path_args2 = {
        "NameConstant" : buildNamedConstantNode,
        "Str"          : buildStringNode,
        "Num"          : buildNumberNode,
        "Bytes"        : buildBytesNode,
        "Continue"     : buildStatementLoopContinue,
    },
    path_args1 = {
        "Ellipsis"     : buildEllipsisNode,
    }
)


def buildParseTree(provider, source_code, source_ref, is_module, is_main):
    # There are a bunch of branches here, mostly to deal with version
    # differences for module default variables.

    body = parseSourceCodeToAst(
        source_code = source_code,
        filename    = source_ref.getFilename(),
        line_offset = source_ref.getLineNumber() - 1
    )
    body, doc = extractDocFromBody(body)

    result = buildStatementsNode(
        provider   = provider,
        nodes      = body,
        source_ref = source_ref
    )

    checkFutureImportsOnlyAtStart(body)

    internal_source_ref = source_ref.atInternal()

    statements = []

    if is_module:
        # Add import of "site" module of main programs visibly in the node tree,
        # so recursion and optimization can pick it up, checking its effects.
        if is_main and "no_site" not in Options.getPythonFlags():
            for path_imported_name in getPthImportedPackages():
                statements.append(
                    StatementExpressionOnly(
                        expression = ExpressionImportModule(
                            module_name = path_imported_name,
                            import_list = (),
                            level       = 0,
                            source_ref  = source_ref,
                        ),
                        source_ref = source_ref
                    )
                )

            statements.append(
                StatementExpressionOnly(
                    expression = ExpressionImportModule(
                        module_name = "site",
                        import_list = (),
                        level       = 0,
                        source_ref  = source_ref,
                    ),
                    source_ref = source_ref
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
                source       = ExpressionModuleFileAttributeRef(
                    source_ref = internal_source_ref,
                ),
                source_ref   = internal_source_ref
            )
        )

        if provider.isCompiledPythonPackage():
            # This assigns "__path__" value.
            statements.append(
                createPathAssignment(internal_source_ref)
            )

    if python_version >= 300:
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


    if python_version >= 330:
        # For Python3.3, it's set for both packages and non-packages.
        statements.append(
            StatementAssignmentVariable(
                variable_ref = ExpressionTargetVariableRef(
                    variable_name = "__package__",
                    source_ref    = internal_source_ref
                ),
                source       = ExpressionConstantRef(
                    constant      = provider.getFullName()
                                      if provider.isCompiledPythonPackage() else
                                    provider.getPackage(),
                    source_ref    = internal_source_ref,
                    user_provided = True
                ),
                source_ref   = internal_source_ref
            )
        )

    needs__initializing__ = not provider.isMainModule() and \
      (python_version >= 330 and python_version < 340)

    if needs__initializing__:
        # Set "__initializing__" at the beginning to True
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
        # Set "__initializing__" at the end to False
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
        return makeModuleFrame(
            module     = provider,
            statements = statements,
            source_ref = source_ref
        )
    else:
        assert False


def decideModuleTree(filename, package, is_shlib, is_top, is_main):
    # Many variables, branches, due to the many cases, pylint: disable=R0912,R0915

    assert package is None or type(package) is str
    assert filename is not None

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
            filename = filename,
        )

        if is_main:
            module_name = "__main__"
        else:
            module_name = Utils.basename(filename)

            if module_name.endswith(".py"):
                module_name = module_name[:-3]

            if is_shlib:
                module_name = module_name.split('.')[0]

            if '.' in module_name:
                sys.stderr.write(
                    "Error, '%s' is not a proper python module name.\n" % (
                        module_name
                    )
                )

                sys.exit(2)

        if is_shlib:
            result = PythonShlibModule(
                name         = module_name,
                package_name = package,
                source_ref   = source_ref
            )
        elif is_main:
            result = PythonMainModule(
                main_added = main_added,
                mode       = Plugins.decideCompilation("__main__", source_ref),
                source_ref = source_ref
            )
        else:
            if package is not None:
                full_name = package + '.' + module_name
            else:
                full_name = module_name

            result = CompiledPythonModule(
                name         = module_name,
                package_name = package,
                mode         = Plugins.decideCompilation(full_name, source_ref),
                source_ref   = source_ref
            )

    elif Importing.isPackageDir(filename):
        if is_top:
            package_name = Utils.splitpath(filename)[-1]
        else:
            package_name = Utils.basename(filename)

        source_filename = Utils.joinpath(filename, "__init__.py")

        if not Utils.isFile(source_filename):
            source_ref, result = createNamespacePackage(
                package_name   = package_name,
                module_relpath = filename
            )
            source_filename = None
        else:
            source_ref = SourceCodeReferences.fromFilename(
                filename = Utils.abspath(source_filename),
            )

            if package is not None:
                full_name = package + '.' + package_name
            else:
                full_name = package_name

            result = CompiledPythonPackage(
                name         = package_name,
                package_name = package,
                mode         = Plugins.decideCompilation(full_name, source_ref),
                source_ref   = source_ref
            )
    else:
        sys.stderr.write(
            "%s: can't open file '%s'.\n" % (
                Utils.basename(sys.argv[0]),
                filename
            )
        )
        sys.exit(2)

    if not Options.shallHaveStatementLines():
        source_ref = source_ref.atInternal()

    return result, source_ref, source_filename


class CodeTooComplexCode(Exception):
    """ The code of the module is too complex.

        It cannot be compiled, with recursive code, and therefore the bytecode
        should be used instead.

        Example of this is "idnadata".
    """

    pass


def createModuleTree(module, source_ref, source_code, is_main):
    if Options.isShowMemory():
        memory_watch = MemoryUsage.MemoryWatch()

    try:
        module_body = buildParseTree(
            provider    = module,
            source_code = source_code,
            source_ref  = source_ref,
            is_module   = True,
            is_main     = is_main
        )
    except RuntimeError as e:
        if "maximum recursion depth" in e.args[0]:
            raise CodeTooComplexCode(
                module.getFullName(),
                module.getCompileTimeFilename()
            )

        raise

    if module_body.isStatementsFrame():
        module_body = makeStatementsSequenceFromStatement(
            statement = module_body,
        )

    module.setBody(module_body)

    completeVariableClosures(module)

    if Options.isShowMemory():
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

    # If there is source code associated (not the case for namespace packages of
    # Python3.3 or higher, then read it.
    if source_filename is not None:
        # Read source code.
        createModuleTree(
            module      = module,
            source_ref  = source_ref,
            source_code = readSourceCodeFromFilename(module.getFullName(), source_filename),
            is_main     = is_main
        )

    if not module.isMainModule():
        addImportedModule(
            imported_module = module
        )

    return module
