#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

In the "nuitka.tree.TreeHelpers" module, the dispatching is happening. One function
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
import marshal
import os

from nuitka import (
    ModuleRegistry,
    Options,
    OutputDirectories,
    SourceCodeReferences,
)
from nuitka.__past__ import long, unicode
from nuitka.BytecodeCaching import (
    getCachedImportedModuleUsageAttempts,
    hasCachedImportedModuleUsageAttempts,
)
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.Errors import CodeTooComplexCode
from nuitka.freezer.Standalone import detectEarlyImports
from nuitka.importing import Importing
from nuitka.importing.ImportCache import addImportedModule
from nuitka.importing.PreloadedPackages import getPthImportedPackages
from nuitka.importing.StandardLibrary import isStandardLibraryPath
from nuitka.nodes.AttributeNodes import (
    StatementAssignmentAttribute,
    makeExpressionAttributeLookup,
)
from nuitka.nodes.BuiltinFormatNodes import (
    ExpressionBuiltinAscii,
    ExpressionBuiltinFormat,
)
from nuitka.nodes.BuiltinRefNodes import quick_names
from nuitka.nodes.BuiltinTypeNodes import ExpressionBuiltinStrP3
from nuitka.nodes.ConditionalNodes import (
    ExpressionConditional,
    makeStatementConditional,
)
from nuitka.nodes.ConstantRefNodes import (
    ExpressionConstantEllipsisRef,
    ExpressionConstantNoneRef,
    makeConstantRefNode,
)
from nuitka.nodes.CoroutineNodes import ExpressionAsyncWait
from nuitka.nodes.ExceptionNodes import (
    StatementRaiseException,
    StatementReraiseException,
)
from nuitka.nodes.FutureSpecs import FutureSpec
from nuitka.nodes.GeneratorNodes import StatementGeneratorReturn
from nuitka.nodes.ImportNodes import (
    isHardModuleWithoutSideEffect,
    makeExpressionImportModuleFixed,
)
from nuitka.nodes.LoopNodes import StatementLoopBreak, StatementLoopContinue
from nuitka.nodes.ModuleAttributeNodes import (
    ExpressionModuleAttributeFileRef,
    ExpressionModuleAttributeSpecRef,
)
from nuitka.nodes.ModuleNodes import (
    CompiledPythonModule,
    CompiledPythonPackage,
    PythonExtensionModule,
    PythonMainModule,
    makeUncompiledPythonModule,
)
from nuitka.nodes.NodeMakingHelpers import (
    makeRaiseExceptionStatementFromInstance,
)
from nuitka.nodes.OperatorNodes import makeBinaryOperationNode
from nuitka.nodes.OperatorNodesUnary import makeExpressionOperationUnary
from nuitka.nodes.ReturnNodes import makeStatementReturn
from nuitka.nodes.SliceNodes import makeExpressionBuiltinSlice
from nuitka.nodes.StatementNodes import StatementExpressionOnly
from nuitka.nodes.StringConcatenationNodes import ExpressionStringConcatenation
from nuitka.nodes.VariableNameNodes import (
    ExpressionVariableNameRef,
    StatementAssignmentVariableName,
)
from nuitka.nodes.YieldNodes import ExpressionYieldFromWaitable
from nuitka.optimizations.BytecodeDemotion import demoteSourceCodeToBytecode
from nuitka.Options import shallWarnUnusualCode
from nuitka.pgo.PGO import decideCompilationFromPGO
from nuitka.plugins.Plugins import Plugins
from nuitka.PythonVersions import python_version
from nuitka.Tracing import (
    general,
    memory_logger,
    optimization_logger,
    plugins_logger,
    recursion_logger,
    unusual_logger,
)
from nuitka.utils import MemoryUsage
from nuitka.utils.ModuleNames import ModuleName

from . import SyntaxErrors
from .ReformulationAssertStatements import buildAssertNode
from .ReformulationAssignmentStatements import (
    buildAnnAssignNode,
    buildAssignNode,
    buildDeleteNode,
    buildInplaceAssignNode,
    buildNamedExprNode,
)
from .ReformulationBooleanExpressions import buildBoolOpNode
from .ReformulationCallExpressions import buildCallNode
from .ReformulationClasses import buildClassNode
from .ReformulationComparisonExpressions import buildComparisonNode
from .ReformulationContractionExpressions import (
    buildDictContractionNode,
    buildGeneratorExpressionNode,
    buildListContractionNode,
    buildSetContractionNode,
)
from .ReformulationDictionaryCreation import buildDictionaryNode
from .ReformulationExecStatements import buildExecNode
from .ReformulationForLoopStatements import (
    buildAsyncForLoopNode,
    buildForLoopNode,
)
from .ReformulationFunctionStatements import (
    buildAsyncFunctionNode,
    buildFunctionNode,
)
from .ReformulationImportStatements import (
    buildImportFromNode,
    buildImportModulesNode,
    checkFutureImportsOnlyAtStart,
    getFutureSpec,
    popFutureSpec,
    pushFutureSpec,
)
from .ReformulationLambdaExpressions import buildLambdaNode
from .ReformulationMatchStatements import buildMatchNode
from .ReformulationNamespacePackages import (
    createImporterCacheAssignment,
    createNamespacePackage,
    createPathAssignment,
)
from .ReformulationPrintStatements import buildPrintNode
from .ReformulationSequenceCreation import (
    buildListCreationNode,
    buildSetCreationNode,
    buildTupleCreationNode,
)
from .ReformulationSubscriptExpressions import buildSubscriptNode
from .ReformulationTryExceptStatements import buildTryExceptionNode
from .ReformulationTryFinallyStatements import buildTryFinallyNode
from .ReformulationWhileLoopStatements import buildWhileLoopNode
from .ReformulationWithStatements import buildAsyncWithNode, buildWithNode
from .ReformulationYieldExpressions import buildYieldFromNode, buildYieldNode
from .SourceHandling import (
    checkPythonVersionFromCode,
    getSourceCodeDiff,
    readSourceCodeFromFilenameWithInformation,
)
from .TreeHelpers import (
    buildNode,
    buildNodeTuple,
    buildStatementsNode,
    extractDocFromBody,
    getBuildContext,
    getKind,
    makeModuleFrame,
    makeStatementsSequence,
    makeStatementsSequenceFromStatement,
    mangleName,
    mergeStatements,
    parseSourceCodeToAst,
    setBuildingDispatchers,
)
from .VariableClosure import completeVariableClosures

if str is not bytes:

    def buildVariableReferenceNode(provider, node, source_ref):
        # Shortcut for Python3, which gives syntax errors for assigning these.
        if node.id in quick_names:
            return makeConstantRefNode(
                constant=quick_names[node.id], source_ref=source_ref
            )

        return ExpressionVariableNameRef(
            provider=provider,
            variable_name=mangleName(node.id, provider),
            source_ref=source_ref,
        )

else:

    def buildVariableReferenceNode(provider, node, source_ref):
        return ExpressionVariableNameRef(
            provider=provider,
            variable_name=mangleName(node.id, provider),
            source_ref=source_ref,
        )


# Python3.4 or higher, True and False, are not given as variables anymore.
# Python3.8, all kinds of constants are like this.
def buildNamedConstantNode(node, source_ref):
    return makeConstantRefNode(
        constant=node.value, source_ref=source_ref, user_provided=True
    )


def buildConditionNode(provider, node, source_ref):
    # Conditional statements may have one or two branches. We will never see an
    # "elif", because that's already dealt with by module "ast", which turns it
    # into nested conditional statements.

    return makeStatementConditional(
        condition=buildNode(provider, node.test, source_ref),
        yes_branch=buildStatementsNode(
            provider=provider, nodes=node.body, source_ref=source_ref
        ),
        no_branch=buildStatementsNode(
            provider=provider,
            nodes=node.orelse if node.orelse else None,
            source_ref=source_ref,
        ),
        source_ref=source_ref,
    )


def buildTryFinallyNode2(provider, node, source_ref):
    # Try/finally node statements of old style.

    return buildTryFinallyNode(
        provider=provider,
        build_tried=lambda: buildStatementsNode(
            provider=provider, nodes=node.body, source_ref=source_ref
        ),
        node=node,
        source_ref=source_ref,
    )


def buildTryNode(provider, node, source_ref):
    # Note: This variant is used for Python3.3 or higher only, older stuff uses
    # the above ones, this one merges try/except with try/finally in the
    # "ast". We split it up again, as it's logically separated of course.

    # Shortcut missing try/finally.
    if not node.handlers:
        return buildTryFinallyNode2(provider, node, source_ref)

    if not node.finalbody:
        return buildTryExceptionNode(
            provider=provider, node=node, source_ref=source_ref
        )

    return buildTryFinallyNode(
        provider=provider,
        build_tried=lambda: makeStatementsSequence(
            statements=mergeStatements(
                (
                    buildTryExceptionNode(
                        provider=provider, node=node, source_ref=source_ref
                    ),
                ),
                allow_none=True,
            ),
            allow_none=True,
            source_ref=source_ref,
        ),
        node=node,
        source_ref=source_ref,
    )


def buildRaiseNode(provider, node, source_ref):
    # Raise statements. Under Python2 they may have type, value and traceback
    # attached, for Python3, you can only give type (actually value) and cause.

    if python_version < 0x300:
        exception_type = buildNode(provider, node.type, source_ref, allow_none=True)
        exception_value = buildNode(provider, node.inst, source_ref, allow_none=True)
        exception_trace = buildNode(provider, node.tback, source_ref, allow_none=True)
        exception_cause = None
    else:
        exception_type = buildNode(provider, node.exc, source_ref, allow_none=True)
        exception_value = None
        exception_trace = None
        exception_cause = buildNode(provider, node.cause, source_ref, allow_none=True)

    if exception_type is None:
        assert exception_value is None
        assert exception_trace is None
        assert exception_cause is None

        result = StatementReraiseException(source_ref=source_ref)
    else:
        result = StatementRaiseException(
            exception_type=exception_type,
            exception_value=exception_value,
            exception_trace=exception_trace,
            exception_cause=exception_cause,
            source_ref=source_ref,
        )

        if exception_cause is not None:
            result.setCompatibleSourceReference(
                source_ref=exception_cause.getCompatibleSourceReference()
            )
        elif exception_trace is not None:
            result.setCompatibleSourceReference(
                source_ref=exception_trace.getCompatibleSourceReference()
            )
        elif exception_value is not None:
            result.setCompatibleSourceReference(
                source_ref=exception_value.getCompatibleSourceReference()
            )
        elif exception_type is not None:
            result.setCompatibleSourceReference(
                source_ref=exception_type.getCompatibleSourceReference()
            )

    return result


def handleGlobalDeclarationNode(provider, node, source_ref):

    # On the module level, there is nothing to do.
    if provider.isCompiledPythonModule():
        if shallWarnUnusualCode():
            unusual_logger.warning(
                "%s: Using 'global' statement on module level has no effect."
                % source_ref.getAsString(),
            )

        return None

    # Need to catch the error of declaring a parameter variable as global
    # ourselves here. The AST parsing doesn't catch it, so we check here.
    if provider.isExpressionFunctionBody():
        parameters = provider.getParameters()

        for variable_name in node.names:
            if variable_name in parameters.getParameterNames():
                SyntaxErrors.raiseSyntaxError(
                    "name '%s' is %s and global"
                    % (
                        variable_name,
                        "local" if python_version < 0x300 else "parameter",
                    ),
                    source_ref.atColumnNumber(node.col_offset),
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
                variable_name=variable_name
            )

            closure_variable = provider.addClosureVariable(variable=module_variable)

        assert closure_variable.isModuleVariable()

        # Special case, since Python 3.5 it is allowed to use global on the "__class__"
        # variable as well, but it's not changing visibility of implicit "__class__" of
        # functions, and as such it will just not be registered.
        if (
            provider.isExpressionClassBody()
            and closure_variable.getName() == "__class__"
        ):
            if python_version < 0x340:
                SyntaxErrors.raiseSyntaxError(
                    "cannot make __class__ global", source_ref
                )
        else:
            provider.getLocalsScope().registerClosureVariable(
                variable=closure_variable,
            )

    # Drop this, not really part of our tree.
    return None


def handleNonlocalDeclarationNode(provider, node, source_ref):
    # Need to catch the error of declaring a parameter variable as global
    # ourselves here. The AST parsing doesn't catch it, but we can do it here.
    parameter_provider = provider

    while (
        parameter_provider.isExpressionGeneratorObjectBody()
        or parameter_provider.isExpressionCoroutineObjectBody()
        or parameter_provider.isExpressionAsyncgenObjectBody()
    ):
        parameter_provider = parameter_provider.getParentVariableProvider()

    if parameter_provider.isExpressionClassBody():
        parameter_names = ()
    else:
        parameter_names = parameter_provider.getParameters().getParameterNames()

    for variable_name in node.names:
        if variable_name in parameter_names:
            SyntaxErrors.raiseSyntaxError(
                "name '%s' is parameter and nonlocal" % (variable_name),
                source_ref.atColumnNumber(node.col_offset),
            )

    provider.addNonlocalsDeclaration(
        names=tuple(node.names),
        user_provided=True,
        source_ref=source_ref.atColumnNumber(node.col_offset),
    )

    # Drop this, not really part of our tree.
    return None


def buildStringNode(node, source_ref):
    assert type(node.s) in (str, unicode)

    return makeConstantRefNode(
        constant=node.s, source_ref=source_ref, user_provided=True
    )


def buildNumberNode(node, source_ref):
    assert type(node.n) in (int, long, float, complex), type(node.n)

    return makeConstantRefNode(
        constant=node.n, source_ref=source_ref, user_provided=True
    )


def buildBytesNode(node, source_ref):
    return makeConstantRefNode(
        constant=node.s, source_ref=source_ref, user_provided=True
    )


def buildEllipsisNode(source_ref):
    return ExpressionConstantEllipsisRef(source_ref=source_ref)


def buildStatementLoopContinue(node, source_ref):
    source_ref = source_ref.atColumnNumber(node.col_offset)

    # Python forbids this, although technically it's probably not much of
    # an issue.
    if getBuildContext() == "finally" and python_version < 0x380:
        SyntaxErrors.raiseSyntaxError(
            "'continue' not supported inside 'finally' clause", source_ref
        )

    return StatementLoopContinue(source_ref=source_ref)


def buildStatementLoopBreak(provider, node, source_ref):
    # A bit unusual, we need the provider, but not the node,
    # pylint: disable=unused-argument

    return StatementLoopBreak(source_ref=source_ref.atColumnNumber(node.col_offset))


def buildAttributeNode(provider, node, source_ref):
    return makeExpressionAttributeLookup(
        expression=buildNode(provider, node.value, source_ref),
        attribute_name=mangleName(node.attr, provider),
        source_ref=source_ref,
    )


def buildReturnNode(provider, node, source_ref):
    if provider.isExpressionClassBody() or provider.isCompiledPythonModule():
        SyntaxErrors.raiseSyntaxError(
            "'return' outside function", source_ref.atColumnNumber(node.col_offset)
        )

    expression = buildNode(provider, node.value, source_ref, allow_none=True)

    if provider.isExpressionGeneratorObjectBody():
        if expression is not None and python_version < 0x300:
            SyntaxErrors.raiseSyntaxError(
                "'return' with argument inside generator",
                source_ref.atColumnNumber(node.col_offset),
            )

    if provider.isExpressionAsyncgenObjectBody():
        if expression is not None:
            SyntaxErrors.raiseSyntaxError(
                "'return' with value in async generator",
                source_ref.atColumnNumber(node.col_offset),
            )

    if (
        provider.isExpressionGeneratorObjectBody()
        or provider.isExpressionAsyncgenObjectBody()
    ):
        if expression is None:
            expression = ExpressionConstantNoneRef(source_ref=source_ref)

        return StatementGeneratorReturn(expression=expression, source_ref=source_ref)
    else:
        return makeStatementReturn(expression=expression, source_ref=source_ref)


def buildExprOnlyNode(provider, node, source_ref):
    result = StatementExpressionOnly(
        expression=buildNode(provider, node.value, source_ref), source_ref=source_ref
    )

    result.setCompatibleSourceReference(
        result.subnode_expression.getCompatibleSourceReference()
    )

    return result


def buildUnaryOpNode(provider, node, source_ref):
    operator = getKind(node.op)

    # Delegate this one to boolean operation code.
    if operator == "Not":
        return buildBoolOpNode(provider=provider, node=node, source_ref=source_ref)

    operand = buildNode(provider, node.operand, source_ref)

    return makeExpressionOperationUnary(
        operator=operator, operand=operand, source_ref=source_ref
    )


def buildBinaryOpNode(provider, node, source_ref):
    operator = getKind(node.op)

    if operator == "Div":
        operator = "TrueDiv" if getFutureSpec().isFutureDivision() else "OldDiv"

    left = buildNode(provider, node.left, source_ref)
    right = buildNode(provider, node.right, source_ref)

    result = makeBinaryOperationNode(
        operator=operator, left=left, right=right, source_ref=source_ref
    )

    result.setCompatibleSourceReference(source_ref=right.getCompatibleSourceReference())

    return result


def buildReprNode(provider, node, source_ref):
    return makeExpressionOperationUnary(
        operator="Repr",
        operand=buildNode(provider, node.value, source_ref),
        source_ref=source_ref,
    )


def buildConditionalExpressionNode(provider, node, source_ref):
    return ExpressionConditional(
        condition=buildNode(provider, node.test, source_ref),
        expression_yes=buildNode(provider, node.body, source_ref),
        expression_no=buildNode(provider, node.orelse, source_ref),
        source_ref=source_ref,
    )


def buildAwaitNode(provider, node, source_ref):
    return ExpressionYieldFromWaitable(
        expression=ExpressionAsyncWait(
            expression=buildNode(provider, node.value, source_ref),
            source_ref=source_ref,
        ),
        source_ref=source_ref,
    )


def buildFormattedValueNode(provider, node, source_ref):
    value = buildNode(provider, node.value, source_ref)

    conversion = node.conversion % 4 if node.conversion > 0 else 0

    if conversion == 0:
        pass
    elif conversion == 3:
        # TODO: We might start using this for Python2 too.
        assert str is not bytes

        value = ExpressionBuiltinStrP3(
            value=value, encoding=None, errors=None, source_ref=source_ref
        )
    elif conversion == 2:
        value = makeExpressionOperationUnary(
            operator="Repr", operand=value, source_ref=source_ref
        )
    elif conversion == 1:
        value = ExpressionBuiltinAscii(value=value, source_ref=source_ref)
    else:
        assert False, conversion

    return ExpressionBuiltinFormat(
        value=value,
        format_spec=buildNode(provider, node.format_spec, source_ref, allow_none=True),
        source_ref=source_ref,
    )


def buildJoinedStrNode(provider, node, source_ref):
    if node.values:
        return ExpressionStringConcatenation(
            values=buildNodeTuple(provider, node.values, source_ref),
            source_ref=source_ref,
        )
    else:
        return makeConstantRefNode(constant="", source_ref=source_ref)


def buildSliceNode(provider, node, source_ref):
    """Python3.9 or higher, slice notations."""
    return makeExpressionBuiltinSlice(
        start=buildNode(provider, node.lower, source_ref, allow_none=True),
        stop=buildNode(provider, node.upper, source_ref, allow_none=True),
        step=buildNode(provider, node.step, source_ref, allow_none=True),
        source_ref=source_ref,
    )


setBuildingDispatchers(
    path_args3={
        "Name": buildVariableReferenceNode,
        "Assign": buildAssignNode,
        "AnnAssign": buildAnnAssignNode,
        "Delete": buildDeleteNode,
        "Lambda": buildLambdaNode,
        "GeneratorExp": buildGeneratorExpressionNode,
        "If": buildConditionNode,
        "While": buildWhileLoopNode,
        "For": buildForLoopNode,
        "AsyncFor": buildAsyncForLoopNode,
        "Compare": buildComparisonNode,
        "ListComp": buildListContractionNode,
        "DictComp": buildDictContractionNode,
        "SetComp": buildSetContractionNode,
        "Dict": buildDictionaryNode,
        "Set": buildSetCreationNode,
        "Tuple": buildTupleCreationNode,
        "List": buildListCreationNode,
        "Global": handleGlobalDeclarationNode,
        "Nonlocal": handleNonlocalDeclarationNode,
        "TryExcept": buildTryExceptionNode,
        "TryFinally": buildTryFinallyNode2,
        "Try": buildTryNode,
        "Raise": buildRaiseNode,
        "Import": buildImportModulesNode,
        "ImportFrom": buildImportFromNode,
        "Assert": buildAssertNode,
        "Exec": buildExecNode,
        "With": buildWithNode,
        "AsyncWith": buildAsyncWithNode,
        "FunctionDef": buildFunctionNode,
        "AsyncFunctionDef": buildAsyncFunctionNode,
        "Await": buildAwaitNode,
        "ClassDef": buildClassNode,
        "Print": buildPrintNode,
        "Call": buildCallNode,
        "Subscript": buildSubscriptNode,
        "BoolOp": buildBoolOpNode,
        "Attribute": buildAttributeNode,
        "Return": buildReturnNode,
        "Yield": buildYieldNode,
        "YieldFrom": buildYieldFromNode,
        "Expr": buildExprOnlyNode,
        "UnaryOp": buildUnaryOpNode,
        "BinOp": buildBinaryOpNode,
        "Repr": buildReprNode,
        "AugAssign": buildInplaceAssignNode,
        "IfExp": buildConditionalExpressionNode,
        "Break": buildStatementLoopBreak,
        "JoinedStr": buildJoinedStrNode,
        "FormattedValue": buildFormattedValueNode,
        "NamedExpr": buildNamedExprNode,
        "Slice": buildSliceNode,
        "Match": buildMatchNode,
    },
    path_args2={
        "Constant": buildNamedConstantNode,  # Python3.8
        "NameConstant": buildNamedConstantNode,  # Python3.8 or below
        "Str": buildStringNode,
        "Num": buildNumberNode,
        "Bytes": buildBytesNode,
        "Continue": buildStatementLoopContinue,
    },
    path_args1={"Ellipsis": buildEllipsisNode},
)


def buildParseTree(provider, ast_tree, source_ref, is_module, is_main):
    # There are a bunch of branches here, mostly to deal with version
    # differences for module default variables. pylint: disable=too-many-branches

    # Maybe one day, we do exec inlining again, that is what this is for,
    # then is_module won't be True, for now it always is.
    pushFutureSpec()
    if is_module:
        provider.setFutureSpec(getFutureSpec())

    body, doc = extractDocFromBody(ast_tree)

    if is_module and is_main and python_version >= 0x360:
        provider.markAsNeedsAnnotationsDictionary()

    result = buildStatementsNode(provider=provider, nodes=body, source_ref=source_ref)

    # After building, we can verify that all future statements were where they
    # belong, namely at the start of the module.
    checkFutureImportsOnlyAtStart(body)

    internal_source_ref = source_ref.atInternal()

    statements = []

    if is_module:
        # Add import of "site" module of main programs visibly in the node tree,
        # so recursion and optimization can pick it up, checking its effects.
        if is_main and not Options.hasPythonFlagNoSite():
            statements.append(
                StatementExpressionOnly(
                    expression=makeExpressionImportModuleFixed(
                        module_name="site", source_ref=source_ref
                    ),
                    source_ref=source_ref,
                )
            )

            for path_imported_name in getPthImportedPackages():
                if isHardModuleWithoutSideEffect(path_imported_name):
                    continue

                statements.append(
                    StatementExpressionOnly(
                        expression=makeExpressionImportModuleFixed(
                            module_name=path_imported_name, source_ref=source_ref
                        ),
                        source_ref=source_ref,
                    )
                )

        statements.append(
            StatementAssignmentVariableName(
                provider=provider,
                variable_name="__doc__",
                source=makeConstantRefNode(
                    constant=doc, source_ref=internal_source_ref, user_provided=True
                ),
                source_ref=internal_source_ref,
            )
        )

        statements.append(
            StatementAssignmentVariableName(
                provider=provider,
                variable_name="__file__",
                source=ExpressionModuleAttributeFileRef(
                    variable=provider.getVariableForReference("__file__"),
                    source_ref=internal_source_ref,
                ),
                source_ref=internal_source_ref,
            )
        )

        if provider.isCompiledPythonPackage():
            # This assigns "__path__" value.
            statements.append(createPathAssignment(provider, internal_source_ref))
            statements.append(
                createImporterCacheAssignment(provider, internal_source_ref)
            )

        if python_version >= 0x340 and not is_main:
            statements += (
                StatementAssignmentAttribute(
                    expression=ExpressionModuleAttributeSpecRef(
                        variable=provider.getVariableForReference("__spec__"),
                        source_ref=internal_source_ref,
                    ),
                    attribute_name="origin",
                    source=ExpressionModuleAttributeFileRef(
                        variable=provider.getVariableForReference("__file__"),
                        source_ref=internal_source_ref,
                    ),
                    source_ref=internal_source_ref,
                ),
                StatementAssignmentAttribute(
                    expression=ExpressionModuleAttributeSpecRef(
                        variable=provider.getVariableForReference("__spec__"),
                        source_ref=internal_source_ref,
                    ),
                    attribute_name="has_location",
                    source=makeConstantRefNode(True, internal_source_ref),
                    source_ref=internal_source_ref,
                ),
            )

            if provider.isCompiledPythonPackage():
                statements.append(
                    StatementAssignmentAttribute(
                        expression=ExpressionModuleAttributeSpecRef(
                            variable=provider.getVariableForReference("__spec__"),
                            source_ref=internal_source_ref,
                        ),
                        attribute_name="submodule_search_locations",
                        source=ExpressionVariableNameRef(
                            provider=provider,
                            variable_name="__path__",
                            source_ref=internal_source_ref,
                        ),
                        source_ref=internal_source_ref,
                    )
                )

    if python_version >= 0x300:
        statements.append(
            StatementAssignmentVariableName(
                provider=provider,
                variable_name="__cached__",
                source=ExpressionConstantNoneRef(source_ref=internal_source_ref),
                source_ref=internal_source_ref,
            )
        )

    needs__initializing__ = (
        not provider.isMainModule() and 0x300 <= python_version < 0x340
    )

    if needs__initializing__:
        # Set "__initializing__" at the beginning to True
        statements.append(
            StatementAssignmentVariableName(
                provider=provider,
                variable_name="__initializing__",
                source=makeConstantRefNode(
                    constant=True, source_ref=internal_source_ref, user_provided=True
                ),
                source_ref=internal_source_ref,
            )
        )

    if provider.needsAnnotationsDictionary():
        # Set "__annotations__" on module level to {}
        statements.append(
            StatementAssignmentVariableName(
                provider=provider,
                variable_name="__annotations__",
                source=makeConstantRefNode(
                    constant={}, source_ref=internal_source_ref, user_provided=True
                ),
                source_ref=internal_source_ref,
            )
        )

    # Now the module body if there is any at all.
    if result is not None:
        statements.extend(result.subnode_statements)

    if needs__initializing__:
        # Set "__initializing__" at the end to False
        statements.append(
            StatementAssignmentVariableName(
                provider=provider,
                variable_name="__initializing__",
                source=makeConstantRefNode(
                    constant=False, source_ref=internal_source_ref, user_provided=True
                ),
                source_ref=internal_source_ref,
            )
        )

    if is_module:
        result = makeModuleFrame(
            module=provider, statements=statements, source_ref=source_ref
        )

        popFutureSpec()

        return result
    else:
        assert False


def decideCompilationMode(is_top, module_name, for_pgo):
    """Decide the compilation mode for a module.

    module_name - The module to decide compilation mode for.
    for_pgo - consider PGO information or not
    """

    result = Plugins.decideCompilation(module_name)

    # Cannot change mode of __main__ to bytecode, that is not going
    # to work currently.
    if result == "bytecode" and is_top:
        plugins_logger.warning(
            """\
Ignoring plugin decision to compile top level package '%s' \
as bytecode, the extension module entry point is technically \
required to compiled."""
            % module_name
        )
        result = "compiled"

    # Include all of standard library as bytecode, for now. We need to identify
    # which ones really need that.
    if not is_top:
        module_filename = Importing.locateModule(
            module_name=module_name, parent_package=None, level=0
        )[1]

        if module_filename is not None and isStandardLibraryPath(module_filename):
            result = "bytecode"

    # Plugins need to win over PGO, as they might know it better
    if result is None and not for_pgo:
        result = decideCompilationFromPGO(module_name=module_name)

    # Default if neither plugins nor PGO have expressed an opinion
    if result is None:
        result = "compiled"

    return result


def _loadUncompiledModuleFromCache(module_name, is_package, source_code, source_ref):
    result = makeUncompiledPythonModule(
        module_name=module_name,
        filename=source_ref.getFilename(),
        bytecode=demoteSourceCodeToBytecode(
            module_name=module_name,
            source_code=source_code,
            filename=source_ref.getFilename(),
        ),
        user_provided=False,
        technical=False,
        is_package=is_package,
    )

    used_modules = OrderedSet()

    used_modules = getCachedImportedModuleUsageAttempts(
        module_name=module_name, source_code=source_code, source_ref=source_ref
    )

    # assert not is_package, (module_name, used_modules, result, result.getCompileTimeFilename())

    result.setUsedModules(used_modules)

    return result


def _createModule(
    module_name,
    source_code,
    source_ref,
    is_extension,
    is_namespace,
    is_package,
    is_top,
    is_main,
    main_added,
):
    if is_extension:
        result = PythonExtensionModule(
            module_name=module_name, technical=False, source_ref=source_ref
        )
    elif is_main:
        result = PythonMainModule(
            main_added=main_added,
            module_name=module_name,
            mode=decideCompilationMode(
                is_top=is_top, module_name=module_name, for_pgo=False
            ),
            future_spec=None,
            source_ref=source_ref,
        )

        checkPythonVersionFromCode(source_code)
    elif is_namespace:
        result = createNamespacePackage(module_name, is_top, source_ref)
    else:
        mode = decideCompilationMode(
            is_top=is_top, module_name=module_name, for_pgo=False
        )

        if (
            mode == "bytecode"
            and not is_top
            and not Options.shallDisableBytecodeCacheUsage()
            and hasCachedImportedModuleUsageAttempts(
                module_name=module_name, source_code=source_code, source_ref=source_ref
            )
        ):
            result = _loadUncompiledModuleFromCache(
                module_name=module_name,
                is_package=is_package,
                source_code=source_code,
                source_ref=source_ref,
            )

            # Not used anymore
            source_code = None
        else:
            if is_package:
                result = CompiledPythonPackage(
                    module_name=module_name,
                    is_top=is_top,
                    mode=mode,
                    future_spec=None,
                    source_ref=source_ref,
                )
            else:
                result = CompiledPythonModule(
                    module_name=module_name,
                    is_top=is_top,
                    mode=mode,
                    future_spec=None,
                    source_ref=source_ref,
                )

    return result


def createModuleTree(module, source_ref, ast_tree, is_main):
    if Options.isShowMemory():
        memory_watch = MemoryUsage.MemoryWatch()

    module_body = buildParseTree(
        provider=module,
        ast_tree=ast_tree,
        source_ref=source_ref,
        is_module=True,
        is_main=is_main,
    )

    if module_body.isStatementsFrame():
        module_body = makeStatementsSequenceFromStatement(statement=module_body)

    module.setChildBody(module_body)

    completeVariableClosures(module)

    if Options.isShowMemory():
        memory_watch.finish()

        memory_logger.info(
            "Memory usage changed loading module '%s': %s"
            % (module.getFullName(), memory_watch.asStr())
        )


def buildMainModuleTree(filename, is_main, source_code):
    # Detect to be frozen modules if any, so we can consider to not follow
    # to them.

    if is_main:
        # TODO: Doesn't work for deeply nested packages at all.
        if Options.hasPythonFlagPackageMode():
            module_name = ModuleName(os.path.basename(filename) + ".__main__")
        else:
            module_name = ModuleName("__main__")
    else:
        module_name = Importing.getModuleNameAndKindFromFilename(filename)[0]

    module, _added = buildModule(
        module_name=module_name,
        module_filename=filename,
        source_code=source_code,
        is_top=True,
        is_main=is_main,
        is_extension=False,
        is_fake=source_code is not None,
        hide_syntax_error=False,
    )

    if is_main and Options.isStandaloneMode():
        module.setEarlyModules(detectEarlyImports())

    # Main modules do not get added to the import cache, but plugins get to see it.
    if module.isMainModule():
        Plugins.onModuleDiscovered(module)
    else:
        addImportedModule(imported_module=module)

    return module


def _makeModuleBodyFromSyntaxError(exc, module_name, module_filename):
    if module_filename not in Importing.warned_about:
        Importing.warned_about.add(module_filename)

        recursion_logger.warning(
            """\
Cannot follow import to module '%s' because of '%s'."""
            % (module_name, exc.__class__.__name__)
        )

    source_ref = SourceCodeReferences.fromFilename(filename=module_filename)

    module = CompiledPythonModule(
        module_name=module_name,
        is_top=False,
        mode="compiled",
        future_spec=FutureSpec(),
        source_ref=source_ref,
    )

    module_body = makeModuleFrame(
        module=module,
        statements=(
            makeRaiseExceptionStatementFromInstance(
                source_ref=source_ref, exception=exc
            ),
        ),
        source_ref=source_ref,
    )

    module_body = makeStatementsSequenceFromStatement(statement=module_body)
    module.setChildBody(module_body)

    return module


def _makeModuleBodyTooComplex(module_name, module_filename, source_code, is_package):
    if module_filename not in Importing.warned_about:
        Importing.warned_about.add(module_filename)

        recursion_logger.warning(
            """\
Cannot follow import to import module '%r' ('%s') because code is too complex."""
            % (
                module_name,
                module_filename,
            )
        )

    module = makeUncompiledPythonModule(
        module_name=module_name,
        filename=module_filename,
        bytecode=marshal.dumps(
            compile(source_code, module_filename, "exec", dont_inherit=True)
        ),
        is_package=is_package,
        user_provided=True,
        technical=False,
    )

    ModuleRegistry.addUncompiledModule(module)


def buildModule(
    module_name,
    module_filename,
    source_code,
    is_top,
    is_main,
    is_extension,
    is_fake,
    hide_syntax_error,
):
    # Many details to deal with,
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements
    (
        main_added,
        is_package,
        is_namespace,
        source_ref,
        source_filename,
    ) = Importing.decideModuleSourceRef(
        filename=module_filename,
        module_name=module_name,
        is_main=is_main,
        is_fake=is_fake,
        logger=general,
    )

    if Options.hasPythonFlagPackageMode():
        if is_top and Options.shallMakeModule():
            optimization_logger.warning(
                "Python flag -m (package_mode) has no effect in module mode, it's only for executables."
            )
        elif is_main and not main_added:
            optimization_logger.warning(
                "Python flag -m (package_mode) only works on packages with '__main__.py'."
            )

    # Read source code if necessary. Might give a SyntaxError due to not being proper
    # encoded source.
    if source_filename is not None and not is_namespace and not is_extension:
        # For fake modules, source is provided directly.
        original_source_code = None
        contributing_plugins = ()

        if source_code is None:
            try:
                (
                    source_code,
                    original_source_code,
                    contributing_plugins,
                ) = readSourceCodeFromFilenameWithInformation(
                    module_name=module_name, source_filename=source_filename
                )
            except SyntaxError as e:
                # Avoid hiding our own syntax errors.
                if not hasattr(e, "generated_by_nuitka"):
                    raise

                # Do not hide SyntaxError in main module.
                if not hide_syntax_error:
                    raise

                module = _makeModuleBodyFromSyntaxError(
                    exc=e, module_name=module_name, module_filename=module_filename
                )
                return module, True

        try:
            ast_tree = parseSourceCodeToAst(
                source_code=source_code,
                module_name=module_name,
                filename=source_filename,
                line_offset=0,
            )
        except (SyntaxError, IndentationError) as e:
            # Do not hide SyntaxError if asked not to.
            if not hide_syntax_error:
                raise

            if original_source_code is not None:
                try:
                    parseSourceCodeToAst(
                        source_code=original_source_code,
                        module_name=module_name,
                        filename=source_filename,
                        line_offset=0,
                    )
                except (SyntaxError, IndentationError):
                    # Also an exception without the plugins, that is OK
                    pass
                else:
                    source_diff = getSourceCodeDiff(original_source_code, source_code)

                    for line in source_diff:
                        plugins_logger.warning(line)

                    if len(contributing_plugins) == 1:
                        contributing_plugins[0].sysexit(
                            "Making changes to '%s' that cause SyntaxError '%s'"
                            % (module_name, e)
                        )
                    else:
                        plugins_logger.sysexit(
                            "One of the plugins '%s' is making changes to '%s' that cause SyntaxError '%s'"
                            % (",".join(contributing_plugins), module_name, e)
                        )

            module = _makeModuleBodyFromSyntaxError(
                exc=e, module_name=module_name, module_filename=module_filename
            )
            return module, True
        except CodeTooComplexCode:
            # Do not hide CodeTooComplexCode in main module.
            if is_main:
                raise

            module = _makeModuleBodyTooComplex(
                module_name=module_name,
                module_filename=module_filename,
                source_code=source_code,
                is_package=is_package,
            )
            return module, False
    else:
        ast_tree = None
        source_code = None

    module = _createModule(
        module_name=module_name,
        source_code=source_code,
        source_ref=source_ref,
        is_top=is_top,
        is_main=is_main,
        is_extension=is_extension,
        is_namespace=is_namespace,
        is_package=is_package,
        main_added=main_added,
    )

    if is_top:
        ModuleRegistry.addRootModule(module)

        OutputDirectories.setMainModule(module)

    if module.isCompiledPythonModule() and source_code is not None:
        createModuleTree(
            module=module,
            source_ref=source_ref,
            ast_tree=ast_tree,
            is_main=is_main,
        )

    return module, True
