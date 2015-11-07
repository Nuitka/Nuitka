#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" The code generation.

No language specifics at all are supposed to be present here. Instead it is
using primitives from the given generator to build code sequences (list of
strings).

As such this is the place that knows how to take a condition and two code
branches and make a code block out of it. But it doesn't contain any target
language syntax.
"""

from nuitka import Constants, Options, Tracing
from nuitka.__past__ import iterItems
from nuitka.utils import Utils

from . import Contexts, Emission, Helpers
from .AttributeCodes import (
    generateAttributeLookupCode,
    generateAttributeLookupSpecialCode,
    getAttributeAssignmentClassSlotCode,
    getAttributeAssignmentCode,
    getAttributeAssignmentDictSlotCode,
    getAttributeDelCode
)
from .BuiltinCodes import (
    getBuiltinAnonymousRefCode,
    getBuiltinInt2Code,
    getBuiltinLong2Code,
    getBuiltinRefCode,
    getBuiltinSuperCode,
    getBuiltinType3Code
)
from .CallCodes import (
    generateCallCode,
    getCallsCode,
    getCallsDecls,
    getMakeBuiltinExceptionCode
)
from .ClassCodes import getSelectMetaclassCode
from .ComparisonCodes import getComparisonExpressionCode
from .ConditionalCodes import generateConditionCode, getConditionCheckTrueCode
from .ConstantCodes import generateConstantReferenceCode, getConstantCode
from .DictCodes import (
    generateDictionaryCreationCode,
    generateDictOperationUpdateCode,
    getBuiltinDict2Code,
    getDictOperationGetCode,
    getDictOperationRemoveCode,
    getDictOperationSetCode
)
from .ErrorCodes import getMustNotGetHereCode, getReleaseCode
from .EvalCodes import (
    getBuiltinCompileCode,
    getBuiltinEvalCode,
    getBuiltinExecCode,
    getLocalsDictSyncCode
)
from .ExceptionCodes import (
    generateExceptionPublishCode,
    getExceptionCaughtTracebackCode,
    getExceptionCaughtTypeCode,
    getExceptionCaughtValueCode,
    getExceptionRefCode
)
from .FrameCodes import (
    getFrameGuardHeavyCode,
    getFrameGuardLightCode,
    getFrameGuardOnceCode,
    getFramePreserveExceptionCode,
    getFrameRestoreExceptionCode
)
from .FunctionCodes import (
    generateCoroutineCreationCode,
    generateGeneratorEntryCode,
    getDirectFunctionCallCode,
    getExportScopeCode,
    getFunctionCode,
    getFunctionCreationCode,
    getFunctionDirectDecl,
    getFunctionMakerCode,
    getFunctionMakerDecl,
    getGeneratorFunctionCode
)
from .GlobalsLocalsCodes import (
    getLoadGlobalsCode,
    getLoadLocalsCode,
    getSetLocalsCode
)
from .ImportCodes import (
    getBuiltinImportCode,
    getImportFromStarCode,
    getImportModuleHardCode,
    getImportNameCode
)
from .IndexCodes import (
    getIndexCode,
    getIndexValueCode,
    getMaxIndexCode,
    getMinIndexCode
)
from .IteratorCodes import (
    getBuiltinLoopBreakNextCode,
    getBuiltinNext1Code,
    getUnpackCheckCode,
    getUnpackNextCode
)
from .LabelCodes import (
    getBranchingCode,
    getGotoCode,
    getLabelCode,
    getStatementTrace
)
from .ListCodes import (
    generateListCreationCode,
    generateListOperationAppendCode,
    generateListOperationExtendCode,
    generateListOperationPopCode
)
from .LoaderCodes import getMetapathLoaderBodyCode
from .LoopCodes import generateLoopCode, getLoopBreakCode, getLoopContinueCode
from .ModuleCodes import (
    generateModuleFileAttributeCode,
    getModuleCode,
    getModuleValues
)
from .OperationCodes import (
    generateOperationBinaryCode,
    generateOperationUnaryCode
)
from .PrintCodes import getPrintNewlineCode, getPrintValueCode
from .PythonAPICodes import generateCAPIObjectCode, generateCAPIObjectCode0
from .RaisingCodes import generateRaiseCode
from .ReturnCodes import (
    generateGeneratorReturnCode,
    generateReturnCode,
    generateReturnedValueRefCode
)
from .SetCodes import (
    generateSetCreationCode,
    generateSetOperationAddCode,
    generateSetOperationUpdateCode
)
from .SliceCodes import (
    generateBuiltinSliceCode,
    getSliceAssignmentCode,
    getSliceAssignmentIndexesCode,
    getSliceDelCode,
    getSliceDelIndexesCode,
    getSliceLookupCode,
    getSliceLookupIndexesCode,
    getSliceObjectCode
)
from .SubscriptCodes import (
    generateSubscriptLookupCode,
    getIntegerSubscriptAssignmentCode,
    getSubscriptAssignmentCode,
    getSubscriptDelCode
)
from .TryCodes import generateTryCode
from .TupleCodes import generateTupleCreationCode
from .VariableCodes import (
    generateVariableDelCode,
    generateVariableReferenceCode,
    generateVariableReleaseCode,
    getVariableAssignmentCode
)
from .YieldCodes import generateYieldCode, generateYieldFromCode


def generateFunctionCallCode(to_name, call_node, emit, context):
    assert call_node.getFunction().isExpressionFunctionCreation()

    function_body = call_node.getFunction().getFunctionRef().getFunctionBody()
    function_identifier = function_body.getCodeName()

    argument_values = call_node.getArgumentValues()

    arg_names = []
    for count, arg_value in enumerate(argument_values):
        arg_name = context.allocateTempName("dircall_arg%d" % (count+1))

        generateExpressionCode(
            to_name    = arg_name,
            expression = arg_value,
            emit       = emit,
            context    = context
        )

        arg_names.append(arg_name)

    context.setCurrentSourceCodeReference(
        call_node.getCompatibleSourceReference()
    )

    getDirectFunctionCallCode(
        to_name             = to_name,
        function_identifier = function_identifier,
        arg_names           = arg_names,
        closure_variables   = function_body.getClosureVariables(),
        emit                = emit,
        context             = context
    )


def generateFunctionOutlineCode(to_name, outline_body, emit, context):
    assert outline_body.isExpressionOutlineBody()

    # Need to set return target, to assign to_name from.
    old_return_release_mode = context.getReturnReleaseMode()

    return_target = context.allocateLabel("outline_result")
    old_return_target = context.setReturnTarget(return_target)

    return_value_name = context.allocateTempName("outline_return_value")
    old_return_value_name = context.setReturnValueName(return_value_name)

    generateStatementSequenceCode(
        statement_sequence = outline_body.getBody(),
        emit               = emit,
        context            = context,
        allow_none         = False
    )

    getMustNotGetHereCode(
        reason  = "Return statement must have exited already.",
        context = context,
        emit    = emit
    )

    getLabelCode(return_target, emit)
    emit(
        "%s = %s;" % (
            to_name,
            return_value_name
        )
    )

    context.addCleanupTempName(to_name)

    # Restore previous "return" handling.
    context.setReturnTarget(old_return_target)
    context.setReturnReleaseMode(old_return_release_mode)
    context.setReturnValueName(old_return_value_name)

_generated_functions = {}



def generateFunctionCreationCode(to_name, function_body, defaults, kw_defaults,
                                  annotations, defaults_first, emit, context):
    # This is about creating functions, which is detail ridden stuff,
    # pylint: disable=R0914

    assert function_body.needsCreation(), function_body

    parameters = function_body.getParameters()

    def handleKwDefaults():
        if kw_defaults:
            kw_defaults_name = context.allocateTempName("kw_defaults")

            assert not kw_defaults.isExpressionConstantRef() or \
                   not kw_defaults.getConstant() == {}, kw_defaults.getConstant()

            generateExpressionCode(
                to_name    = kw_defaults_name,
                expression = kw_defaults,
                emit       = emit,
                context    = context
            )
        else:
            kw_defaults_name = None

        return kw_defaults_name

    def handleDefaults():
        if defaults:
            defaults_name = context.allocateTempName("defaults")

            generateTupleCreationCode(
                to_name  = defaults_name,
                elements = defaults,
                emit     = emit,
                context  = context
            )
        else:
            defaults_name = None

        return defaults_name

    if defaults_first:
        defaults_name = handleDefaults()
        kw_defaults_name = handleKwDefaults()
    else:
        kw_defaults_name = handleKwDefaults()
        defaults_name = handleDefaults()

    if annotations:
        annotations_name = context.allocateTempName("annotations")

        generateExpressionCode(
            to_name    = annotations_name,
            expression = annotations,
            emit       = emit,
            context    = context,
        )
    else:
        annotations_name = None

    var_names = parameters.getCoArgNames()

    # Add names of local variables too.
    var_names += [
        local_variable.getName()
        for local_variable in
        function_body.getLocalVariables()
        if not local_variable.isParameterVariable()
    ]

    code_identifier = context.getCodeObjectHandle(
        filename      = function_body.getParentModule().getRunTimeFilename(),
        var_names     = var_names,
        arg_count     = parameters.getArgumentCount(),
        kw_only_count = parameters.getKwOnlyParameterCount(),
        line_number   = function_body.getSourceReference().getLineNumber(),
        code_name     = function_body.getFunctionName(),
        is_generator  = function_body.isGenerator(),
        is_optimized  = not function_body.needsLocalsDict(),
        has_starlist  = parameters.getStarListArgumentName() is not None,
        has_stardict  = parameters.getStarDictArgumentName() is not None,
        has_closure   = function_body.getClosureVariables() != (),
        future_flags  = function_body.getSourceReference().getFutureSpec().asFlags()
    )

    function_identifier = function_body.getCodeName()

    # Creation code needs to be done only once.
    if not context.hasHelperCode(function_identifier):

        maker_code = getFunctionMakerCode(
            function_name       = function_body.getFunctionName(),
            function_qualname   = function_body.getFunctionQualname(),
            function_identifier = function_identifier,
            code_identifier     = code_identifier,
            parameters          = parameters,
            closure_variables   = function_body.getClosureVariables(),
            defaults_name       = defaults_name,
            kw_defaults_name    = kw_defaults_name,
            annotations_name    = annotations_name,
            function_doc        = function_body.getDoc(),
            is_generator        = function_body.isGenerator(),
            context             = context
        )

        context.addHelperCode(function_identifier, maker_code)

        function_decl = getFunctionMakerDecl(
            function_identifier = function_body.getCodeName(),
            defaults_name       = defaults_name,
            kw_defaults_name    = kw_defaults_name,
            annotations_name    = annotations_name,
            closure_variables   = function_body.getClosureVariables()
        )

        context.addDeclaration(function_identifier, function_decl)

    getFunctionCreationCode(
        to_name             = to_name,
        function_identifier = function_body.getCodeName(),
        defaults_name       = defaults_name,
        kw_defaults_name    = kw_defaults_name,
        annotations_name    = annotations_name,
        closure_variables   = function_body.getClosureVariables(),
        emit                = emit,
        context             = context
    )

    getReleaseCode(
        release_name = annotations_name,
        emit         = emit,
        context      = context
    )


def generateFunctionBodyCode(function_body, context):
    function_identifier = function_body.getCodeName()

    if function_identifier in _generated_functions:
        return _generated_functions[function_identifier]

    # TODO: Generate both codes, and base direct/etc. decisions on context.
    if function_body.needsCreation():
        function_context = Contexts.PythonFunctionCreatedContext(
            parent   = context,
            function = function_body
        )
    else:
        function_context = Contexts.PythonFunctionDirectContext(
            parent   = context,
            function = function_body
        )

    function_codes = Emission.SourceCodeCollector()

    generateStatementSequenceCode(
        statement_sequence = function_body.getBody(),
        allow_none         = True,
        emit               = function_codes,
        context            = function_context
    )

    parameters = function_body.getParameters()

    needs_exception_exit = function_body.mayRaiseException(BaseException)
    needs_generator_return = function_body.needsGeneratorReturnExit()

    if function_body.isGenerator():
        source_ref = function_body.getSourceReference()

        code_identifier = function_context.getCodeObjectHandle(
            filename      = function_body.getParentModule().getRunTimeFilename(),
            var_names     = parameters.getCoArgNames(),
            arg_count     = parameters.getArgumentCount(),
            kw_only_count = parameters.getKwOnlyParameterCount(),
            line_number   = source_ref.getLineNumber(),
            code_name     = function_body.getFunctionName(),
            is_generator  = True,
            is_optimized  = not function_context.hasLocalsDict(),
            has_starlist  = parameters.getStarListArgumentName() is not None,
            has_stardict  = parameters.getStarDictArgumentName() is not None,
            has_closure   = function_body.getClosureVariables() != (),
            future_flags  = source_ref.getFutureSpec().asFlags()
        )

        function_code = getGeneratorFunctionCode(
            context                = function_context,
            function_name          = function_body.getFunctionName(),
            function_qualname      = function_body.getFunctionQualname(),
            function_identifier    = function_identifier,
            code_identifier        = code_identifier,
            parameters             = parameters,
            closure_variables      = function_body.getClosureVariables(),
            user_variables         = function_body.getUserLocalVariables(),
            temp_variables         = function_body.getTempVariables(),
            function_codes         = function_codes.codes,
            function_doc           = function_body.getDoc(),
            needs_exception_exit   = needs_exception_exit,
            needs_generator_return = needs_generator_return
        )
    else:
        function_code = getFunctionCode(
            context              = function_context,
            function_name        = function_body.getFunctionName(),
            function_identifier  = function_identifier,
            parameters           = parameters,
            closure_variables    = function_body.getClosureVariables(),
            user_variables       = function_body.getUserLocalVariables(),
            temp_variables       = function_body.getTempVariables(),
            function_codes       = function_codes.codes,
            function_doc         = function_body.getDoc(),
            needs_exception_exit = needs_exception_exit,
            file_scope           = getExportScopeCode(
                cross_module = function_body.isCrossModuleUsed()
            )
        )

    return function_code


def generateComparisonExpressionCode(to_name, comparison_expression, emit,
                                     context):
    left_name = context.allocateTempName("compexpr_left")
    right_name = context.allocateTempName("compexpr_right")

    generateExpressionCode(
        to_name    = left_name,
        expression = comparison_expression.getLeft(),
        emit       = emit,
        context    = context
    )
    generateExpressionCode(
        to_name    = right_name,
        expression = comparison_expression.getRight(),
        emit       = emit,
        context    = context
    )

    getComparisonExpressionCode(
        to_name     = to_name,
        comparator  = comparison_expression.getComparator(),
        left_name   = left_name,
        right_name  = right_name,
        needs_check = comparison_expression.mayRaiseExceptionBool(BaseException),
        emit        = emit,
        context     = context
    )


def generateSliceRangeIdentifier(lower, upper, scope, emit, context):
    lower_name = context.allocateTempName(
        scope + "slicedel_index_lower",
        "Py_ssize_t"
    )
    upper_name = context.allocateTempName(
        scope + "_index_upper",
        "Py_ssize_t"
    )

    def isSmallNumberConstant(node):
        value = node.getConstant()

        if Constants.isNumberConstant(value):
            return abs(int(value)) < 2**63-1
        else:
            return False

    if lower is None:
        getMinIndexCode(
            to_name = lower_name,
            emit    = emit
        )
    elif lower.isExpressionConstantRef() and isSmallNumberConstant(lower):
        getIndexValueCode(
            to_name = lower_name,
            value   = int(lower.getConstant()),
            emit    = emit
        )
    else:
        value_name = context.allocateTempName(scope + "_lower_index_value")

        generateExpressionCode(
            to_name    = value_name,
            expression = lower,
            emit       = emit,
            context    = context
        )

        getIndexCode(
            to_name    = lower_name,
            value_name = value_name,
            emit       = emit,
            context    = context
        )

    if upper is None:
        getMaxIndexCode(
            to_name = upper_name,
            emit    = emit
        )
    elif upper.isExpressionConstantRef() and isSmallNumberConstant(upper):
        getIndexValueCode(
            to_name = upper_name,
            value   = int(upper.getConstant()),
            emit    = emit
        )
    else:
        value_name = context.allocateTempName(scope + "_upper_index_value")

        generateExpressionCode(
            to_name    = value_name,
            expression = upper,
            emit       = emit,
            context    = context
        )

        getIndexCode(
            to_name    = upper_name,
            value_name = value_name,
            emit       = emit,
            context    = context
        )

    return lower_name, upper_name

def _decideSlicing(lower, upper):
    return (lower is None or lower.isIndexable()) and \
           (upper is None or upper.isIndexable())


def generateSliceLookupCode(to_name, expression, emit, context):
    assert Utils.python_version < 300

    lower = expression.getLower()
    upper = expression.getUpper()

    if _decideSlicing(lower, upper):
        lower_name, upper_name = generateSliceRangeIdentifier(
            lower   = lower,
            upper   = upper,
            scope   = "slice",
            emit    = emit,
            context = context
        )

        source_name = context.allocateTempName("slice_source")

        generateExpressionCode(
            to_name    = source_name,
            expression = expression.getLookupSource(),
            emit       = emit,
            context    = context
        )

        getSliceLookupIndexesCode(
            to_name     = to_name,
            source_name = source_name,
            lower_name  = lower_name,
            upper_name  = upper_name,
            emit        = emit,
            context     = context
        )
    else:
        source_name, lower_name, upper_name = generateExpressionsCode(
            names       = ("slice_source", "slice_lower", "slice_upper"),
            expressions = (
                expression.getLookupSource(),
                expression.getLower(),
                expression.getUpper()
            ),
            emit        = emit,
            context     = context
        )

        getSliceLookupCode(
            to_name     = to_name,
            source_name = source_name,
            lower_name  = lower_name,
            upper_name  = upper_name,
            emit        = emit,
            context     = context
        )


def generateBuiltinLocalsCode(to_name, locals_node, emit, context):
    provider = locals_node.getParentVariableProvider()

    return getLoadLocalsCode(
        to_name  = to_name,
        provider = provider,
        mode     = provider.getLocalsMode(),
        emit     = emit,
        context  = context
    )

def _generateExpressionCode(to_name, expression, emit, context, allow_none):
    # This is a dispatching function with a branch per expression node type, and
    # therefore many statements even if every branch is relatively small.
    # pylint: disable=R0912,R0914,R0915

    if expression is None and allow_none:
        return None

    # Make sure we don't generate code twice for any node, this uncovers bugs
    # where nodes are shared in the tree, which is not allowed.
    assert not hasattr(expression, "code_generated"), expression
    expression.code_generated = True

    old_source_ref = context.setCurrentSourceCodeReference(expression.getSourceReference())

    def makeExpressionCode(to_name, expression, allow_none = False):
        if allow_none and expression is None:
            return None

        generateExpressionCode(
            to_name    = to_name,
            expression = expression,
            emit       = emit,
            context    = context
        )

    if not expression.isExpression():
        Tracing.printError("No expression %r" % expression)

        expression.dump()
        assert False, expression

    res = Helpers.generateExpressionCode(
        to_name    = to_name,
        expression = expression,
        emit       = emit,
        context    = context
    )

    if res:
        pass
    elif expression.isExpressionSliceLookup():
        generateSliceLookupCode(
            to_name    = to_name,
            expression = expression,
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionSliceObject():
        lower_name, upper_name, step_name = generateExpressionsCode(
            expressions = (
                expression.getLower(),
                expression.getUpper(),
                expression.getStep()
            ),
            names       = (
                "sliceobj_lower", "sliceobj_upper", "sliceobj_step"
            ),
            emit        = emit,
            context     = context
        )

        getSliceObjectCode(
            to_name    = to_name,
            lower_name = lower_name,
            upper_name = upper_name,
            step_name  = step_name,
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionFunctionCall():
        generateFunctionCallCode(
            to_name   = to_name,
            call_node = expression,
            emit      = emit,
            context   = context
        )
    elif expression.isExpressionOutlineBody():
        generateFunctionOutlineCode(
            to_name      = to_name,
            outline_body = expression,
            emit         = emit,
            context      = context
        )
    elif expression.isExpressionBuiltinNext1():
        value_name = context.allocateTempName("next1_arg")

        makeExpressionCode(
            to_name    = value_name,
            expression = expression.getValue()
        )

        getBuiltinNext1Code(
            to_name = to_name,
            value   = value_name,
            emit    = emit,
            context = context
        )
    elif expression.isExpressionBuiltinNext2():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "BUILTIN_NEXT2",
            arg_desc   = (
                ("next_arg", expression.getIterator()),
                ("next_default", expression.getDefault()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionSpecialUnpack():
        value_name = context.allocateTempName("unpack")

        makeExpressionCode(
            to_name    = value_name,
            expression = expression.getValue()
        )

        getUnpackNextCode(
            to_name  = to_name,
            value    = value_name,
            count    = expression.getCount(),
            expected = expression.getExpected(),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinGlobals():
        getLoadGlobalsCode(
            to_name = to_name,
            emit    = emit,
            context = context
        )
    elif expression.isExpressionImportModule():
        generateImportModuleCode(
            to_name    = to_name,
            expression = expression,
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinImport():
        generateBuiltinImportCode(
            to_name    = to_name,
            expression = expression,
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionImportModuleHard():
        getImportModuleHardCode(
            to_name     = to_name,
            module_name = expression.getModuleName(),
            import_name = expression.getImportName(),
            needs_check = expression.mayRaiseException(BaseException),
            emit        = emit,
            context     = context
        )
    elif expression.isExpressionFunctionCreation():
        generateFunctionCreationCode(
            to_name        = to_name,
            function_body  = expression.getFunctionRef().getFunctionBody(),
            defaults       = expression.getDefaults(),
            kw_defaults    = expression.getKwDefaults(),
            annotations    = expression.getAnnotations(),
            defaults_first = not expression.kw_defaults_before_defaults,
            emit           = emit,
            context        = context
        )
    elif expression.isExpressionCaughtExceptionTypeRef():
        getExceptionCaughtTypeCode(
            to_name = to_name,
            emit    = emit,
            context = context
        )
    elif expression.isExpressionCaughtExceptionValueRef():
        getExceptionCaughtValueCode(
            to_name = to_name,
            emit    = emit,
            context = context
        )
    elif expression.isExpressionCaughtExceptionTracebackRef():
        getExceptionCaughtTracebackCode(
            to_name = to_name,
            emit    = emit,
            context = context
        )
    elif expression.isExpressionBuiltinExceptionRef():
        getExceptionRefCode(
            to_name        = to_name,
            exception_type = expression.getExceptionName(),
            emit           = emit,
            context        = context
        )
    elif expression.isExpressionBuiltinAnonymousRef():
        getBuiltinAnonymousRefCode(
            to_name      = to_name,
            builtin_name = expression.getBuiltinName(),
            emit         = emit
        )
    elif expression.isExpressionBuiltinMakeException():
        exception_arg_names = []

        for exception_arg in expression.getArgs():
            exception_arg_name = context.allocateTempName("make_exception_arg")

            makeExpressionCode(
                to_name    = exception_arg_name,
                expression = exception_arg
            )

            exception_arg_names.append(exception_arg_name)

        getMakeBuiltinExceptionCode(
            to_name        = to_name,
            exception_type = expression.getExceptionName(),
            arg_names      = exception_arg_names,
            emit           = emit,
            context        = context
        )
    elif expression.isExpressionComparison():
        generateComparisonExpressionCode(
            to_name               = to_name,
            comparison_expression = expression,
            emit                  = emit,
            context               = context
        )
    elif Utils.python_version < 300 and expression.isExpressionBuiltinStr():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "PyObject_Str",
            arg_desc   = (
                ("str_arg", expression.getValue()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif (
           Utils.python_version < 300 and \
           expression.isExpressionBuiltinUnicode()
        ) or (
           Utils.python_version >= 300 and \
           expression.isExpressionBuiltinStr()
        ):
        encoding = expression.getEncoding()
        errors = expression.getErrors()

        if encoding is None and errors is None:
            generateCAPIObjectCode(
                to_name    = to_name,
                capi       = "PyObject_Unicode",
                arg_desc   = (
                    (
                        "str_arg" if Utils.python_version < 300 \
                          else "unicode_arg",
                        expression.getValue()
                    ),
                ),
                may_raise  = expression.mayRaiseException(BaseException),
                source_ref = expression.getCompatibleSourceReference(),
                emit       = emit,
                context    = context
            )
        else:
            generateCAPIObjectCode(
                to_name    = to_name,
                capi       = "TO_UNICODE3",
                arg_desc   = (
                    ("unicode_arg", expression.getValue()),
                    ("unicode_encoding", encoding),
                    ("unicode_errors", errors),
                ),
                may_raise  = expression.mayRaiseException(BaseException),
                source_ref = expression.getCompatibleSourceReference(),
                none_null  = True,
                emit       = emit,
                context    = context,
            )

    elif expression.isExpressionBuiltinIter1():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "MAKE_ITERATOR",
            arg_desc   = (
                ("iter_arg", expression.getValue()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinIter2():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "BUILTIN_ITER2",
            arg_desc   = (
                ("iter_callable", expression.getCallable()),
                ("iter_sentinel", expression.getSentinel()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinType1():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "BUILTIN_TYPE1",
            arg_desc   = (
                ("type_arg", expression.getValue()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinIsinstance():
        generateCAPIObjectCode0(
            to_name    = to_name,
            capi       = "BUILTIN_ISINSTANCE",
            arg_desc   = (
                ("isinstance_inst", expression.getInstance()),
                ("isinstance_cls", expression.getCls()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinHasattr():
        generateCAPIObjectCode0(
            to_name    = to_name,
            capi       = "BUILTIN_HASATTR",
            arg_desc   = (
                ("hasattr_value", expression.getLookupSource()),
                ("hasattr_attr", expression.getAttribute()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinGetattr():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "BUILTIN_GETATTR",
            arg_desc   = (
                ("getattr_target", expression.getLookupSource()),
                ("getattr_attr", expression.getAttribute()),
                ("getattr_default", expression.getDefault()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            none_null  = True,
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinSetattr():
        generateCAPIObjectCode0(
            to_name    = to_name,
            capi       = "BUILTIN_SETATTR",
            arg_desc   = (
                ("setattr_target", expression.getLookupSource()),
                ("setattr_attr", expression.getAttribute()),
                ("setattr_value", expression.getValue()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context,
        )
    elif expression.isExpressionBuiltinRef():
        getBuiltinRefCode(
            to_name      = to_name,
            builtin_name = expression.getBuiltinName(),
            emit         = emit,
            context      = context
        )
    elif expression.isExpressionBuiltinOriginalRef():
        assert not expression.isExpressionBuiltinRef()

        # This is not implemented currently, but ought to be one day.
        assert False
    elif expression.isExpressionMakeTuple():
        generateTupleCreationCode(
            to_name  = to_name,
            elements = expression.getElements(),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionMakeList():
        generateListCreationCode(
            to_name  = to_name,
            elements = expression.getElements(),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionMakeSet():
        generateSetCreationCode(
            to_name  = to_name,
            elements = expression.getElements(),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionMakeDict():
        assert expression.getPairs()

        generateDictionaryCreationCode(
            to_name = to_name,
            pairs   = expression.getPairs(),
            emit    = emit,
            context = context
        )
    elif expression.isExpressionBuiltinInt():
        value = expression.getValue()
        base = expression.getBase()

        assert value is not None

        if base is None:
            generateCAPIObjectCode(
                to_name    = to_name,
                capi       = "PyNumber_Int",
                arg_desc   = (
                    ("int_arg", value),
                ),
                may_raise  = expression.mayRaiseException(BaseException),
                source_ref = expression.getCompatibleSourceReference(),
                emit       = emit,
                context    = context,
            )
        else:
            value_name = context.allocateTempName("int_value")

            makeExpressionCode(
                to_name    = value_name,
                expression = value
            )

            base_name = context.allocateTempName("int_base")

            makeExpressionCode(
                to_name    = base_name,
                expression = base
            )

            getBuiltinInt2Code(
                to_name    = to_name,
                base_name  = base_name,
                value_name = value_name,
                emit       = emit,
                context    = context
            )
    elif Utils.python_version < 300 and expression.isExpressionBuiltinLong():
        value = expression.getValue()
        base = expression.getBase()

        assert value is not None

        if base is None:
            generateCAPIObjectCode(
                to_name    = to_name,
                capi       = "PyNumber_Long",
                arg_desc   = (
                    ("long_arg", value),
                ),
                may_raise  = expression.mayRaiseException(BaseException),
                source_ref = expression.getCompatibleSourceReference(),
                emit       = emit,
                context    = context
            )
        else:
            value_name = context.allocateTempName("long_value")

            makeExpressionCode(
                to_name    = value_name,
                expression = value
            )

            base_name = context.allocateTempName("long_base")

            makeExpressionCode(
                to_name    = base_name,
                expression = base
            )

            getBuiltinLong2Code(
                to_name    = to_name,
                base_name  = base_name,
                value_name = value_name,
                emit       = emit,
                context    = context
            )
    elif expression.isExpressionImportName():
        from_arg_name = context.allocateTempName("import_name_from")

        makeExpressionCode(
            to_name    = from_arg_name,
            expression = expression.getModule()
        )

        getImportNameCode(
            to_name       = to_name,
            import_name   = expression.getImportName(),
            from_arg_name = from_arg_name,
            emit          = emit,
            context       = context
        )
    elif expression.isExpressionConditionalOR() or \
         expression.isExpressionConditionalAND():

        if expression.isExpressionConditionalOR():
            prefix = "or_"
        else:
            prefix = "and_"

        true_target = context.allocateLabel(prefix + "left")
        false_target = context.allocateLabel(prefix + "right")
        end_target = context.allocateLabel(prefix + "end")

        old_true_target = context.getTrueBranchTarget()
        old_false_target = context.getFalseBranchTarget()

        truth_name = context.allocateTempName(prefix + "left_truth", "int")

        left_name = context.allocateTempName(prefix + "left_value")
        right_name = context.allocateTempName(prefix + "right_value")

        left_value = expression.getLeft()

        generateExpressionCode(
            to_name    = left_name,
            expression = left_value,
            emit       = emit,
            context    = context
        )

        # We need to treat this mostly manually here. We remember to release
        # this, and we better do this manually later.
        needs_ref1 = context.needsCleanup(left_name)

        getConditionCheckTrueCode(
            to_name     = truth_name,
            value_name  = left_name,
            needs_check = left_value.mayRaiseExceptionBool(BaseException),
            emit        = emit,
            context     = context
        )

        if expression.isExpressionConditionalOR():
            context.setTrueBranchTarget(true_target)
            context.setFalseBranchTarget(false_target)
        else:
            context.setTrueBranchTarget(false_target)
            context.setFalseBranchTarget(true_target)

        getBranchingCode(
            condition = "%s == 1" % truth_name,
            emit      = emit,
            context   = context
        )

        getLabelCode(false_target,emit)

        # So it's not the left value, then lets release that one right away, it
        # is not needed, but we remember if it should be added above.
        getReleaseCode(
           release_name = left_name,
           emit         = emit,
           context      = context
        )

        # Evaluate the "right" value then.
        generateExpressionCode(
            to_name    = right_name,
            expression = expression.getRight(),
            emit       = emit,
            context    = context
        )

        # Again, remember the reference count to manage it manually.
        needs_ref2 = context.needsCleanup(right_name)

        if needs_ref2:
            context.removeCleanupTempName(right_name)

        if not needs_ref2 and needs_ref1:
            emit("Py_INCREF( %s );" % right_name)

        emit(
            "%s = %s;" % (
                to_name,
                right_name
            )
        )

        getGotoCode(end_target, emit)

        getLabelCode(true_target, emit)

        if not needs_ref1 and needs_ref2:
            emit("Py_INCREF( %s );" % left_name)

        emit(
            "%s = %s;" % (
                to_name,
                left_name
            )
        )

        getLabelCode(end_target, emit)

        if needs_ref1 or needs_ref2:
            context.addCleanupTempName(to_name)

        context.setTrueBranchTarget(old_true_target)
        context.setFalseBranchTarget(old_false_target)
    elif expression.isExpressionConditional():
        true_target = context.allocateLabel("condexpr_true")
        false_target = context.allocateLabel("condexpr_false")
        end_target = context.allocateLabel("condexpr_end")

        old_true_target = context.getTrueBranchTarget()
        old_false_target = context.getFalseBranchTarget()

        context.setTrueBranchTarget(true_target)
        context.setFalseBranchTarget(false_target)

        generateConditionCode(
            condition = expression.getCondition(),
            emit      = emit,
            context   = context
        )

        getLabelCode(true_target,emit)
        makeExpressionCode(
            to_name    = to_name,
            expression = expression.getExpressionYes()
        )
        needs_ref1 = context.needsCleanup(to_name)

        # Must not clean this up in other expression.
        if needs_ref1:
            context.removeCleanupTempName(to_name)

        real_emit = emit
        emit = Emission.SourceCodeCollector()

        makeExpressionCode(
            to_name    = to_name,
            expression = expression.getExpressionNo()
        )

        needs_ref2 = context.needsCleanup(to_name)

        # TODO: Need to buffer generated code, so we can emit extra reference if
        # not same.
        if needs_ref1 and not needs_ref2:
            getGotoCode(end_target, real_emit)
            getLabelCode(false_target, real_emit)

            for line in emit.codes:
                real_emit(line)
            emit = real_emit

            emit("Py_INCREF( %s );" % to_name)
            context.addCleanupTempName(to_name)
        elif not needs_ref1 and needs_ref2:
            real_emit("Py_INCREF( %s );" % to_name)
            getGotoCode(end_target, real_emit)
            getLabelCode(false_target, real_emit)

            for line in emit.codes:
                real_emit(line)
            emit = real_emit
        else:
            getGotoCode(end_target, real_emit)
            getLabelCode(false_target, real_emit)

            for line in emit.codes:
                real_emit(line)
            emit = real_emit

        getLabelCode(end_target,emit)

        context.setTrueBranchTarget(old_true_target)
        context.setFalseBranchTarget(old_false_target)
    elif expression.isExpressionDictOperationGet():
        dict_name, key_name = generateExpressionsCode(
            expressions = (
                expression.getDict(),
                expression.getKey()
            ),
            names       = ("dget_dict", "dget_key"),
            emit        = emit,
            context     = context
        )

        getDictOperationGetCode(
            to_name   = to_name,
            dict_name = dict_name,
            key_name  = key_name,
            emit      = emit,
            context   = context
        )
    elif expression.isExpressionDictOperationSet():
        dict_name, key_name, value_name = generateExpressionsCode(
            expressions = (
                expression.getDict(),
                expression.getKey(),
                expression.getValue()
            ),
            names       = ("dictset_to", "dictset_key", "dictset_value"),
            emit        = emit,
            context     = context
        )

        getDictOperationSetCode(
            to_name    = to_name,
            dict_name  = dict_name,
            key_name   = key_name,
            value_name = value_name,
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionSelectMetaclass():
        if expression.getMetaclass() is not None:
            metaclass_name = context.allocateTempName("class_meta")

            makeExpressionCode(
                to_name    = metaclass_name,
                expression = expression.getMetaclass()
            )
        else:
            metaclass_name = None

        bases_name = context.allocateTempName("class_bases")
        makeExpressionCode(
            to_name    = bases_name,
            expression = expression.getBases()
        )

        getSelectMetaclassCode(
            to_name        = to_name,
            metaclass_name = metaclass_name,
            bases_name     = bases_name,
            emit           = emit,
            context        = context
        )
    elif expression.isExpressionBuiltinLocals():
        generateBuiltinLocalsCode(
            to_name     = to_name,
            locals_node = expression,
            emit        = emit,
            context     = context
        )
    elif expression.isExpressionBuiltinDir1():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "PyObject_Dir",
            arg_desc   = (
                ("dir_arg", expression.getValue()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinVars():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "LOOKUP_VARS",
            arg_desc   = (
                ("vars_arg", expression.getSource()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinOpen():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "BUILTIN_OPEN",
            arg_desc   = (
                ("open_filename", expression.getFilename()),
                ("open_mode", expression.getMode()),
                ("open_buffering", expression.getBuffering()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            none_null  = True,
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinRange1():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "BUILTIN_RANGE",
            arg_desc   = (
                ("range_arg", expression.getLow()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinRange2():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "BUILTIN_RANGE2",
            arg_desc   = (
                ("range2_low", expression.getLow()),
                ("range2_high", expression.getHigh()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinRange3():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "BUILTIN_RANGE3",
            arg_desc   = (
                ("range3_low", expression.getLow()),
                ("range3_high", expression.getHigh()),
                ("range3_step", expression.getStep()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinXrange():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "BUILTIN_XRANGE",
            arg_desc   = (
                ("xrange_low", expression.getLow()),
                ("xrange_high", expression.getHigh()),
                ("xrange_step", expression.getStep()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context,
            none_null  = True,
        )
    elif expression.isExpressionBuiltinFloat():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "TO_FLOAT",
            arg_desc   = (
                ("float_arg", expression.getValue()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinComplex():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "TO_COMPLEX",
            arg_desc   = (
                ("real_arg", expression.getReal()),
                ("imag_arg", expression.getImag())
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            none_null  = True,
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinBool():
        generateCAPIObjectCode0(
            to_name    = to_name,
            capi       = "TO_BOOL",
            arg_desc   = (
                ("bool_arg", expression.getValue()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinChr():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "BUILTIN_CHR",
            arg_desc   = (
                ("chr_arg", expression.getValue()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinOrd():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "BUILTIN_ORD",
            arg_desc   = (
                ("ord_arg", expression.getValue()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinBin():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "BUILTIN_BIN",
            arg_desc   = (
                ("bin_arg", expression.getValue()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinOct():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "BUILTIN_OCT",
            arg_desc   = (
                ("oct_arg", expression.getValue()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinHex():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "BUILTIN_HEX",
            arg_desc   = (
                ("hex_arg", expression.getValue()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinLen():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "BUILTIN_LEN",
            arg_desc   = (
                ("len_arg", expression.getValue()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinTuple():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "PySequence_Tuple",
            arg_desc   = (
                ("tuple_arg", expression.getValue()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinList():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "PySequence_List",
            arg_desc   = (
                ("list_arg", expression.getValue()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinDict():
        if expression.getPositionalArgument():
            seq_name = context.allocateTempName("dict_seq")

            makeExpressionCode(
                to_name    = seq_name,
                expression = expression.getPositionalArgument(),
                allow_none = True
            )
        else:
            seq_name = None

        if expression.getNamedArgumentPairs():
            # If there is no sequence to mix in, then directly generate
            # into to_name.

            if seq_name is None:
                generateDictionaryCreationCode(
                    to_name = to_name,
                    pairs   = expression.getNamedArgumentPairs(),
                    emit    = emit,
                    context = context
                )

                dict_name = None
            else:
                dict_name = context.allocateTempName("dict_arg")

                generateDictionaryCreationCode(
                    to_name = dict_name,
                    pairs   = expression.getNamedArgumentPairs(),
                    emit    = emit,
                    context = context
                )
        else:
            dict_name = None

        if seq_name is not None:
            getBuiltinDict2Code(
                to_name   = to_name,
                seq_name  = seq_name,
                dict_name = dict_name,
                emit      = emit,
                context   = context
            )
    elif expression.isExpressionBuiltinSet():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "PySet_New",
            arg_desc   = (
                ("set_arg", expression.getValue()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinType3():
        type_name = context.allocateTempName("type_name")
        bases_name = context.allocateTempName("type_bases")
        dict_name = context.allocateTempName("type_dict")

        makeExpressionCode(
            to_name    = type_name,
            expression = expression.getTypeName()
        )
        makeExpressionCode(
            to_name    = bases_name,
            expression = expression.getBases()
        )
        makeExpressionCode(
            to_name    = dict_name,
            expression = expression.getDict()
        )

        getBuiltinType3Code(
            to_name    = to_name,
            type_name  = type_name,
            bases_name = bases_name,
            dict_name  = dict_name,
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinBytearray():
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "BUILTIN_BYTEARRAY",
            arg_desc   = (
                ("bytearray_arg", expression.getValue()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinSuper():
        type_name, object_name = generateExpressionsCode(
            expressions = (
                expression.getType(), expression.getObject()
            ),
            names       = (
                "super_type", "super_object"
            ),
            emit        = emit,
            context     = context
        )

        getBuiltinSuperCode(
            to_name     = to_name,
            type_name   = type_name,
            object_name = object_name,
            emit        = emit,
            context     = context
        )
    elif expression.isExpressionSideEffects():
        for side_effect in expression.getSideEffects():
            generateStatementOnlyCode(
                value   = side_effect,
                emit    = emit,
                context = context
            )

        makeExpressionCode(
            to_name    = to_name,
            expression = expression.getExpression()
        )
    elif expression.isExpressionBuiltinEval():
        generateEvalCode(
            to_name   = to_name,
            eval_node = expression,
            emit      = emit,
            context   = context
        )
    elif Utils.python_version < 300 and \
         expression.isExpressionBuiltinExecfile():
        generateExecfileCode(
            to_name       = to_name,
            execfile_node = expression,
            emit          = emit,
            context       = context
        )
    elif Utils.python_version >= 300 and \
         expression.isExpressionBuiltinExec():
        # "exec" built-in of Python3, as opposed to Python2 statement
        generateEvalCode(
            to_name   = to_name,
            eval_node = expression,
            emit      = emit,
            context   = context
        )
    elif expression.isExpressionBuiltinCompile():
        source_name = context.allocateTempName("compile_source")
        filename_name = context.allocateTempName("compile_filename")
        mode_name = context.allocateTempName("compile_mode")

        makeExpressionCode(
            to_name    = source_name,
            expression = expression.getSourceCode()
        )
        makeExpressionCode(
            to_name    = filename_name,
            expression = expression.getFilename()
        )
        makeExpressionCode(
            to_name    = mode_name,
            expression = expression.getMode()
        )

        if expression.getFlags() is not None:
            flags_name = context.allocateTempName("compile_flags")

            makeExpressionCode(
                to_name    = flags_name,
                expression = expression.getFlags(),
            )
        else:
            flags_name = "NULL"

        if expression.getDontInherit() is not None:
            dont_inherit_name = context.allocateTempName("compile_dont_inherit")

            makeExpressionCode(
                to_name    = dont_inherit_name,
                expression = expression.getDontInherit()
            )
        else:
            dont_inherit_name = "NULL"

        if expression.getOptimize() is not None:
            optimize_name = context.allocateTempName("compile_dont_inherit")

            makeExpressionCode(
                to_name    = optimize_name,
                expression = expression.getOptimize()
            )
        else:
            optimize_name = "NULL"

        context.setCurrentSourceCodeReference(
            expression.getCompatibleSourceReference()
        )

        getBuiltinCompileCode(
            to_name           = to_name,
            source_name       = source_name,
            filename_name     = filename_name,
            mode_name         = mode_name,
            flags_name        = flags_name,
            dont_inherit_name = dont_inherit_name,
            optimize_name     = optimize_name,
            emit              = emit,
            context           = context
        )
    else:
        assert False, expression

    context.setCurrentSourceCodeReference(old_source_ref)


def generateExpressionsCode(names, expressions, emit, context):
    assert len(names) == len(expressions)

    result = []
    for name, expression in zip(names, expressions):
        if expression is not None:
            to_name = context.allocateTempName(name)

            generateExpressionCode(
                to_name    = to_name,
                expression = expression,
                emit       = emit,
                context    = context
            )
        else:
            to_name = None

        result.append(to_name)

    return result


def generateExpressionCode(to_name, expression, emit, context,
                            allow_none = False):
    try:
        _generateExpressionCode(
            to_name    = to_name,
            expression = expression,
            emit       = emit,
            context    = context,
            allow_none = allow_none
        )
    except Exception:
        Tracing.printError(
            "Problem with %r at %s" % (
                expression,
                ""
                  if expression is None else
                expression.getSourceReference().getAsString()
            )
        )
        raise


def generateAssignmentAttributeCode(statement, emit, context):
    lookup_source  = statement.getLookupSource()
    attribute_name = statement.getAttributeName()
    value          = statement.getAssignSource()

    value_name = context.allocateTempName("assattr_name")
    generateExpressionCode(
        to_name    = value_name,
        expression = value,
        emit       = emit,
        context    = context
    )

    target_name = context.allocateTempName("assattr_target")
    generateExpressionCode(
        to_name    = target_name,
        expression = lookup_source,
        emit       = emit,
        context    = context
    )

    old_source_ref = context.setCurrentSourceCodeReference(
        value.getSourceReference()
           if Options.isFullCompat() else
        statement.getSourceReference()
    )

    if attribute_name == "__dict__":
        getAttributeAssignmentDictSlotCode(
            target_name = target_name,
            value_name  = value_name,
            emit        = emit,
            context     = context
        )
    elif attribute_name == "__class__":
        getAttributeAssignmentClassSlotCode(
            target_name = target_name,
            value_name  = value_name,
            emit        = emit,
            context     = context
        )
    else:
        getAttributeAssignmentCode(
            target_name    = target_name,
            value_name     = value_name,
            attribute_name = getConstantCode(
                context  = context,
                constant = attribute_name
            ),
            emit           = emit,
            context        = context
        )

    context.setCurrentSourceCodeReference(old_source_ref)


def generateAssignmentSubscriptCode(statement, emit, context):
    subscribed      = statement.getSubscribed()
    subscript       = statement.getSubscript()
    value           = statement.getAssignSource()

    integer_subscript = False
    if subscript.isExpressionConstantRef():
        constant = subscript.getConstant()

        if Constants.isIndexConstant(constant):
            constant_value = int(constant)

            if abs(constant_value) < 2**31:
                integer_subscript = True

    value_name = context.allocateTempName("ass_subvalue")

    generateExpressionCode(
        to_name    = value_name,
        expression = value,
        emit       = emit,
        context    = context
    )

    subscribed_name = context.allocateTempName("ass_subscribed")
    generateExpressionCode(
        to_name    = subscribed_name,
        expression = subscribed,
        emit       = emit,
        context    = context
    )


    subscript_name = context.allocateTempName("ass_subscript")

    generateExpressionCode(
        to_name    = subscript_name,
        expression = subscript,
        emit       = emit,
        context    = context
    )

    old_source_ref = context.setCurrentSourceCodeReference(
        value.getSourceReference()
           if Options.isFullCompat() else
        statement.getSourceReference()
    )

    if integer_subscript:
        getIntegerSubscriptAssignmentCode(
            subscribed_name = subscribed_name,
            subscript_name  = subscript_name,
            subscript_value = constant_value,
            value_name      = value_name,
            emit            = emit,
            context         = context
        )
    else:
        getSubscriptAssignmentCode(
            target_name    = subscribed_name,
            subscript_name = subscript_name,
            value_name     = value_name,
            emit           = emit,
            context        = context
        )
    context.setCurrentSourceCodeReference(old_source_ref)


def generateAssignmentSliceCode(statement, emit, context):
    assert Utils.python_version < 300

    lookup_source = statement.getLookupSource()
    lower         = statement.getLower()
    upper         = statement.getUpper()
    value         = statement.getAssignSource()

    value_name = context.allocateTempName("sliceass_value")

    generateExpressionCode(
        to_name    = value_name,
        expression = value,
        emit       = emit,
        context    = context
    )

    target_name = context.allocateTempName("sliceass_target")

    generateExpressionCode(
        to_name    = target_name,
        expression = lookup_source,
        emit       = emit,
        context    = context
    )


    if _decideSlicing(lower, upper):
        lower_name, upper_name = generateSliceRangeIdentifier(
            lower   = lower,
            upper   = upper,
            scope   = "sliceass",
            emit    = emit,
            context = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(
            value.getSourceReference()
               if Options.isFullCompat() else
            statement.getSourceReference()
        )

        getSliceAssignmentIndexesCode(
            target_name = target_name,
            lower_name  = lower_name,
            upper_name  = upper_name,
            value_name  = value_name,
            emit        = emit,
            context     = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)
    else:
        lower_name, upper_name = generateExpressionsCode(
            names       = (
                "sliceass_lower", "sliceass_upper"
            ),
            expressions = (
                lower,
                upper
            ),
            emit        = emit,
            context     = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(
            value.getSourceReference()
               if Options.isFullCompat() else
            statement.getSourceReference()
        )

        getSliceAssignmentCode(
            target_name = target_name,
            upper_name  = upper_name,
            lower_name  = lower_name,
            value_name  = value_name,
            emit        = emit,
            context     = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)



def generateDelSubscriptCode(statement, emit, context):
    subscribed = statement.getSubscribed()
    subscript  = statement.getSubscript()

    target_name, subscript_name = generateExpressionsCode(
        expressions = (subscribed, subscript),
        names       = ("delsubscr_target", "delsubscr_subscript"),
        emit        = emit,
        context     = context
    )

    old_source_ref = context.setCurrentSourceCodeReference(
        subscript.getSourceReference()
           if Options.isFullCompat() else
        statement.getSourceReference()
    )

    getSubscriptDelCode(
        target_name    = target_name,
        subscript_name = subscript_name,
        emit           = emit,
        context        = context
    )

    context.setCurrentSourceCodeReference(old_source_ref)


def generateDelSliceCode(statement, emit, context):
    assert Utils.python_version < 300

    target  = statement.getLookupSource()
    lower   = statement.getLower()
    upper   = statement.getUpper()

    target_name = context.allocateTempName("slicedel_target")

    generateExpressionCode(
        to_name    = target_name,
        expression = target,
        emit       = emit,
        context    = context
    )

    if _decideSlicing(lower, upper):
        lower_name, upper_name = generateSliceRangeIdentifier(
            lower   = lower,
            upper   = upper,
            scope   = "slicedel",
            emit    = emit,
            context = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(
            (upper or lower or statement).getSourceReference()
               if Options.isFullCompat() else
            statement.getSourceReference()
        )

        getSliceDelIndexesCode(
            target_name = target_name,
            lower_name  = lower_name,
            upper_name  = upper_name,
            emit        = emit,
            context     = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)
    else:
        lower_name, upper_name = generateExpressionsCode(
            names       = (
                "slicedel_lower", "slicedel_upper"
            ),
            expressions = (
                lower,
                upper
            ),
            emit        = emit,
            context     = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(
            (upper or lower or target).getSourceReference()
               if Options.isFullCompat() else
            statement.getSourceReference()
        )

        getSliceDelCode(
            target_name = target_name,
            lower_name  = lower_name,
            upper_name  = upper_name,
            emit        = emit,
            context     = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)


def generateDelAttributeCode(statement, emit, context):
    target_name = context.allocateTempName("attrdel_target")

    generateExpressionCode(
        to_name    = target_name,
        expression = statement.getLookupSource(),
        emit       = emit,
        context    = context
    )

    old_source_ref = context.setCurrentSourceCodeReference(
        statement.getLookupSource().getSourceReference()
           if Options.isFullCompat() else
        statement.getSourceReference()
    )

    getAttributeDelCode(
        target_name    = target_name,
        attribute_name = getConstantCode(
            context  = context,
            constant = statement.getAttributeName()
        ),
        emit           = emit,
        context        = context
    )

    context.setCurrentSourceCodeReference(old_source_ref)

def _generateEvalCode(to_name, node, emit, context):
    source_name = context.allocateTempName("eval_source")
    globals_name = context.allocateTempName("eval_globals")
    locals_name = context.allocateTempName("eval_locals")

    generateExpressionCode(
        to_name    = source_name,
        expression = node.getSourceCode(),
        emit       = emit,
        context    = context
    )

    generateExpressionCode(
        to_name    = globals_name,
        expression = node.getGlobals(),
        emit       = emit,
        context    = context
    )

    generateExpressionCode(
        to_name    = locals_name,
        expression = node.getLocals(),
        emit       = emit,
        context    = context
    )

    if node.isExpressionBuiltinEval() or \
         (Utils.python_version >= 300 and node.isExpressionBuiltinExec()):
        filename = "<string>"
    else:
        filename = "<execfile>"

    getBuiltinEvalCode(
        to_name       = to_name,
        source_name   = source_name,
        globals_name  = globals_name,
        locals_name   = locals_name,
        filename_name = getConstantCode(
            constant = filename,
            context  = context
        ),
        mode_name     = getConstantCode(
            constant = "eval" if node.isExpressionBuiltinEval() else "exec",
            context  = context
        ),
        emit          = emit,
        context       = context
    )

def generateEvalCode(to_name, eval_node, emit, context):
    return _generateEvalCode(
        to_name = to_name,
        node    = eval_node,
        emit    = emit,
        context = context
    )

def generateExecfileCode(to_name, execfile_node, emit, context):
    return _generateEvalCode(
        to_name = to_name,
        node    = execfile_node,
        emit    = emit,
        context = context
    )

def generateExecCode(statement, emit, context):
    source_arg = statement.getSourceCode()
    globals_arg = statement.getGlobals()
    locals_arg = statement.getLocals()

    source_name = context.allocateTempName("eval_source")
    globals_name = context.allocateTempName("eval_globals")
    locals_name = context.allocateTempName("eval_locals")

    generateExpressionCode(
        to_name    = source_name,
        expression = source_arg,
        emit       = emit,
        context    = context
    )

    generateExpressionCode(
        to_name    = globals_name,
        expression = globals_arg,
        emit       = emit,
        context    = context
    )

    generateExpressionCode(
        to_name    = locals_name,
        expression = locals_arg,
        emit       = emit,
        context    = context
    )

    source_ref = statement.getSourceReference()

    # Filename with origin in improved mode.
    if Options.isFullCompat():
        filename_name = getConstantCode(
            constant = "<string>",
            context  = context
        )
    else:
        filename_name = getConstantCode(
            constant = "<string at %s>" % source_ref.getAsString(),
            context  = context
        )

    old_source_ref = context.setCurrentSourceCodeReference(
        locals_arg.getSourceReference()
          if Options.isFullCompat() else
        statement.getSourceReference()
    )

    getBuiltinExecCode(
        source_name   = source_name,
        globals_name  = globals_name,
        locals_name   = locals_name,
        filename_name = filename_name,
        emit          = emit,
        context       = context,
    )

    context.setCurrentSourceCodeReference(old_source_ref)


def generateLocalsDictSyncCode(statement, emit, context):
    locals_arg = statement.getLocals()
    locals_name = context.allocateTempName("eval_locals")

    generateExpressionCode(
        to_name    = locals_name,
        expression = locals_arg,
        emit       = emit,
        context    = context
    )

    provider = statement.getParentVariableProvider()

    old_source_ref = context.setCurrentSourceCodeReference(
        statement.getSourceReference()
    )

    getLocalsDictSyncCode(
        locals_name = locals_name,
        provider    = provider,
        emit        = emit,
        context     = context,
    )

    context.setCurrentSourceCodeReference(old_source_ref)


def generateTryNextExceptStopIterationCode(statement, emit, context):
    # This has many branches which mean this optimized code generation is not
    # applicable, we return each time. pylint: disable=R0911

    if statement.public_exc:
        return False

    handling = statement.getExceptionHandling()

    if handling is None:
        return False

    tried_statements = statement.getBlockTry().getStatements()

    if len(tried_statements) != 1:
        return False

    handling_statements = handling.getStatements()

    if len(handling_statements) != 1:
        return False

    tried_statement = tried_statements[0]

    if not tried_statement.isStatementAssignmentVariable():
        return False

    assign_source = tried_statement.getAssignSource()

    if not assign_source.isExpressionBuiltinNext1():
        return False

    handling_statement = handling_statements[0]

    if not handling_statement.isStatementConditional():
        return False

    yes_statements = handling_statement.getBranchYes().getStatements()
    no_statements = handling_statement.getBranchNo().getStatements()

    if len(yes_statements) != 1:
        return False

    if not yes_statements[0].isStatementBreakLoop():
        return False

    if len(no_statements) != 1:
        return False

    if not no_statements[0].isStatementReraiseException() or \
       not no_statements[0].isStatementReraiseException():
        return False

    tmp_name = context.allocateTempName("next_source")

    generateExpressionCode(
        expression = assign_source.getValue(),
        to_name    = tmp_name,
        emit       = emit,
        context    = context
    )

    tmp_name2 = context.allocateTempName("assign_source")

    old_source_ref = context.setCurrentSourceCodeReference(
        assign_source.getSourceReference()
          if Options.isFullCompat() else
        statement.getSourceReference()
    )

    getBuiltinLoopBreakNextCode(
        to_name = tmp_name2,
        value   = tmp_name,
        emit    = emit,
        context = context
    )

    getVariableAssignmentCode(
        tmp_name      = tmp_name2,
        variable      = tried_statement.getTargetVariableRef().getVariable(),
        needs_release = None,
        in_place      = False,
        emit          = emit,
        context       = context
    )

    context.setCurrentSourceCodeReference(old_source_ref)

    if context.needsCleanup(tmp_name2):
        context.removeCleanupTempName(tmp_name2)

    return True




def generateUnpackCheckCode(statement, emit, context):
    iterator_name  = context.allocateTempName("iterator_name")

    generateExpressionCode(
        to_name    = iterator_name,
        expression = statement.getIterator(),
        emit       = emit,
        context    = context
    )

    getUnpackCheckCode(
        iterator_name = iterator_name,
        count         = statement.getCount(),
        emit          = emit,
        context       = context,
    )


def generateImportModuleCode(to_name, expression, emit, context):
    provider = expression.getParentVariableProvider()

    globals_name = context.allocateTempName("import_globals")

    getLoadGlobalsCode(
        to_name = globals_name,
        emit    = emit,
        context = context
    )

    if provider.isCompiledPythonModule():
        locals_name = globals_name
    else:
        locals_name = context.allocateTempName("import_locals")

        getLoadLocalsCode(
            to_name  = locals_name,
            provider = expression.getParentVariableProvider(),
            mode     = "updated",
            emit     = emit,
            context  = context
        )

    old_source_ref = context.setCurrentSourceCodeReference(expression.getSourceReference())

    getBuiltinImportCode(
        to_name          = to_name,
        module_name      = getConstantCode(
            constant = expression.getModuleName(),
            context  = context
        ),
        globals_name     = globals_name,
        locals_name      = locals_name,
        import_list_name = getConstantCode(
            constant = expression.getImportList(),
            context  = context
        ),
        level_name       = getConstantCode(
            constant = expression.getLevel(),
            context  = context
        ),
        emit             = emit,
        context          = context
    )

    context.setCurrentSourceCodeReference(old_source_ref)


def generateBuiltinImportCode(to_name, expression, emit, context):
    # We know that 5 expressions are created, pylint: disable=W0632
    module_name, globals_name, locals_name, import_list_name, level_name = \
      generateExpressionsCode(
        expressions = (
            expression.getImportName(),
            expression.getGlobals(),
            expression.getLocals(),
            expression.getFromList(),
            expression.getLevel()
        ),
        names       = (
            "import_modulename",
            "import_globals",
            "import_locals",
            "import_fromlist",
            "import_level"
        ),
        emit        = emit,
        context     = context
    )

    if expression.getGlobals() is None:
        globals_name = context.allocateTempName("import_globals")

        getLoadGlobalsCode(
            to_name = globals_name,
            emit    = emit,
            context = context
        )

    if expression.getLocals() is None:
        provider = expression.getParentVariableProvider()

        if provider.isCompiledPythonModule():
            locals_name = globals_name
        else:
            locals_name = context.allocateTempName("import_locals")

            getLoadLocalsCode(
                to_name  = locals_name,
                provider = provider,
                mode     = provider.getLocalsMode(),
                emit     = emit,
                context  = context
            )


    getBuiltinImportCode(
        to_name          = to_name,
        module_name      = module_name,
        globals_name     = globals_name,
        locals_name      = locals_name,
        import_list_name = import_list_name,
        level_name       = level_name,
        emit             = emit,
        context          = context
    )


def generateImportStarCode(statement, emit, context):
    module_name = context.allocateTempName("star_imported")

    generateImportModuleCode(
        to_name    = module_name,
        expression = statement.getModule(),
        emit       = emit,
        context    = context
    )

    old_source_ref = context.setCurrentSourceCodeReference(statement.getSourceReference())

    getImportFromStarCode(
        module_name = module_name,
        emit        = emit,
        context     = context
    )

    context.setCurrentSourceCodeReference(old_source_ref)


def generateBranchCode(statement, emit, context):
    true_target = context.allocateLabel("branch_yes")
    false_target = context.allocateLabel("branch_no")
    end_target = context.allocateLabel("branch_end")

    old_true_target = context.getTrueBranchTarget()
    old_false_target = context.getFalseBranchTarget()

    context.setTrueBranchTarget(true_target)
    context.setFalseBranchTarget(false_target)

    generateConditionCode(
        condition = statement.getCondition(),
        emit      = emit,
        context   = context
    )

    context.setTrueBranchTarget(old_true_target)
    context.setFalseBranchTarget(old_false_target)

    getLabelCode(true_target, emit)

    generateStatementSequenceCode(
        statement_sequence = statement.getBranchYes(),
        emit               = emit,
        context            = context
    )

    if statement.getBranchNo() is not None:
        getGotoCode(end_target, emit)
        getLabelCode(false_target, emit)

        generateStatementSequenceCode(
            statement_sequence = statement.getBranchNo(),
            emit               = emit,
            context            = context
        )

        getLabelCode(end_target, emit)
    else:
        getLabelCode(false_target, emit)



def generateAssignmentVariableCode(statement, emit, context):
    variable_ref  = statement.getTargetVariableRef()
    value         = statement.getAssignSource()

    tmp_name = context.allocateTempName("assign_source")

    generateExpressionCode(
        expression = value,
        to_name    = tmp_name,
        emit       = emit,
        context    = context
    )

    getVariableAssignmentCode(
        tmp_name      = tmp_name,
        variable      = variable_ref.getVariable(),
        needs_release = statement.needsReleasePreviousValue(),
        in_place      = statement.inplace_suspect,
        emit          = emit,
        context       = context
    )

    assert emit.emit

    # Ownership of that reference must have been transfered.
    assert not context.needsCleanup(tmp_name)


def generateStatementOnlyCode(value, emit, context):
    tmp_name = context.allocateTempName(
        base_name = "unused",
        type_code = "NUITKA_MAY_BE_UNUSED PyObject *",
        unique    = True
    )

    generateExpressionCode(
        expression = value,
        to_name    = tmp_name,
        emit       = emit,
        context    = context
    )

    getReleaseCode(
        release_name = tmp_name,
        emit         = emit,
        context      = context
    )


def generatePrintValueCode(statement, emit, context):
    destination = statement.getDestination()
    value       = statement.getValue()

    if destination is not None:
        tmp_name_dest = context.allocateTempName("print_dest", unique = True)

        generateExpressionCode(
            expression = destination,
            to_name    = tmp_name_dest,
            emit       = emit,
            context    = context
        )
    else:
        tmp_name_dest = None

    tmp_name_printed = context.allocateTempName("print_value", unique = True)

    generateExpressionCode(
        expression = value,
        to_name    = tmp_name_printed,
        emit       = emit,
        context    = context
    )

    old_source_ref = context.setCurrentSourceCodeReference(statement.getSourceReference())

    getPrintValueCode(
        dest_name  = tmp_name_dest,
        value_name = tmp_name_printed,
        emit       = emit,
        context    = context
    )
    context.setCurrentSourceCodeReference(old_source_ref)


def generatePrintNewlineCode(statement, emit, context):
    destination = statement.getDestination()

    if destination is not None:
        tmp_name_dest = context.allocateTempName("print_dest", unique = True)

        generateExpressionCode(
            expression = destination,
            to_name    = tmp_name_dest,
            emit       = emit,
            context    = context
        )
    else:
        tmp_name_dest = None

    old_source_ref = context.setCurrentSourceCodeReference(statement.getSourceReference())
    getPrintNewlineCode(
        dest_name = tmp_name_dest,
        emit      = emit,
        context   = context
    )
    context.setCurrentSourceCodeReference(old_source_ref)


def _generateStatementCode(statement, emit, context):
    # This is a dispatching function with a branch per statement node type.
    # pylint: disable=R0912,R0915
    if not statement.isStatement():
        statement.dump()
        assert False

    if statement.isStatementAssignmentVariable():
        generateAssignmentVariableCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementAssignmentAttribute():
        generateAssignmentAttributeCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementAssignmentSubscript():
        generateAssignmentSubscriptCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementAssignmentSlice():
        generateAssignmentSliceCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementDelVariable():
        generateVariableDelCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementReleaseVariable():
        generateVariableReleaseCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementDelSubscript():
        generateDelSubscriptCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementDelSlice():
        generateDelSliceCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementDelAttribute():
        generateDelAttributeCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementExpressionOnly():
        generateStatementOnlyCode(
            value   = statement.getExpression(),
            emit    = emit,
            context = context
        )
    elif statement.isStatementReturn():
        generateReturnCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementGeneratorReturn():
        generateGeneratorReturnCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementConditional():
        generateBranchCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementTry():
        generateTryCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementPrintValue():
        generatePrintValueCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementPrintNewline():
        generatePrintNewlineCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementImportStar():
        generateImportStarCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementLoop():
        generateLoopCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementBreakLoop():
        getLoopBreakCode(
            emit    = emit,
            context = context
        )
    elif statement.isStatementContinueLoop():
        getLoopContinueCode(
            emit    = emit,
            context = context
        )
    elif statement.isStatementRaiseException():
        generateRaiseCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementSpecialUnpackCheck():
        generateUnpackCheckCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementExec():
        generateExecCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementLocalsDictSync():
        generateLocalsDictSyncCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementDictOperationRemove():
        dict_name = context.allocateTempName("remove_dict", unique = True)
        key_name = context.allocateTempName("remove_key", unique = True)

        generateExpressionCode(
            to_name    = dict_name,
            expression = statement.getDict(),
            emit       = emit,
            context    = context
        )
        generateExpressionCode(
            to_name    = key_name,
            expression = statement.getKey(),
            emit       = emit,
            context    = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(
            statement.getKey().getSourceReference()
               if Options.isFullCompat() else
            statement.getSourceReference()
        )

        getDictOperationRemoveCode(
            dict_name = dict_name,
            key_name  = key_name,
            emit      = emit,
            context   = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(old_source_ref)
    elif statement.isStatementSetLocals():
        new_locals_name = context.allocateTempName("set_locals", unique = True)

        generateExpressionCode(
            to_name    = new_locals_name,
            expression = statement.getNewLocals(),
            emit       = emit,
            context    = context
        )

        getSetLocalsCode(
            new_locals_name = new_locals_name,
            emit            = emit,
            context         = context
        )
    elif statement.isStatementGeneratorEntry():
        generateGeneratorEntryCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementPreserveFrameException():
        getFramePreserveExceptionCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementRestoreFrameException():
        getFrameRestoreExceptionCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementPublishException():
        generateExceptionPublishCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    else:
        assert False, statement


def generateStatementCode(statement, emit, context):
    try:
        _generateStatementCode(statement, emit, context)

        try_finally_candidate = statement.parent.getParent()

        if try_finally_candidate is not None and \
           not try_finally_candidate.isExpression():
            # Complain if any temporary was not dealt with yet.
            assert not context.getCleanupTempnames(), \
              context.getCleanupTempnames()
    except Exception:
        Tracing.printError(
            "Problem with %r at %s" % (
                statement,
                statement.getSourceReference().getAsString()
            )
        )
        raise


def _generateStatementSequenceCode(statement_sequence, emit, context,
                                   allow_none = False):

    if statement_sequence is None and allow_none:
        return

    for statement in statement_sequence.getStatements():
        if Options.shallTraceExecution():
            source_ref = statement.getSourceReference()

            statement_repr = repr(statement)
            source_repr = source_ref.getAsString()

            if Utils.python_version >= 300:
                statement_repr = statement_repr.encode("utf8")
                source_repr = source_repr.encode("utf8")

            emit(
                getStatementTrace(
                    source_repr,
                    statement_repr
                )
            )

        # Might contain frame statement sequences as children.
        if statement.isStatementsFrame():
            generateStatementsFrameCode(
                statement_sequence = statement,
                emit               = emit,
                context            = context
            )
        else:
            generateStatementCode(
                statement = statement,
                emit      = emit,
                context   = context
            )


def generateStatementsFrameCode(statement_sequence, emit, context):
    # This is a wrapper that provides also handling of frames, which got a
    # lot of variants and details, therefore lots of branches.
    # pylint: disable=R0912

    context = Contexts.PythonStatementCContext(context)

    provider = statement_sequence.getParentVariableProvider()
    guard_mode = statement_sequence.getGuardMode()

    parent_exception_exit = context.getExceptionEscape()

    # Allow stacking of frame handles.
    old_frame_handle = context.getFrameHandle()

    if guard_mode != "pass_through":
        if provider.isExpressionFunctionBody():
            context.setFrameHandle("frame_function")
        else:
            context.setFrameHandle("frame_module")

        context.setExceptionEscape(
            context.allocateLabel("frame_exception_exit")
        )
    else:
        context.setFrameHandle("PyThreadState_GET()->frame")

    needs_preserve = statement_sequence.needsFrameExceptionPreserving()

    if statement_sequence.mayReturn() and guard_mode != "pass_through":
        parent_return_exit = context.getReturnTarget()

        context.setReturnTarget(
            context.allocateLabel("frame_return_exit")
        )
    else:
        parent_return_exit = None

    # Now generate the statements code into a local buffer, to we can wrap
    # the frame stuff around it.
    local_emit = Emission.SourceCodeCollector()

    _generateStatementSequenceCode(
        statement_sequence = statement_sequence,
        emit               = local_emit,
        context            = context
    )

    if statement_sequence.mayRaiseException(BaseException) or \
       guard_mode == "generator":
        frame_exception_exit = context.getExceptionEscape()
    else:
        frame_exception_exit = None

    if parent_return_exit is not None:
        frame_return_exit = context.getReturnTarget()
    else:
        frame_return_exit = None

    if guard_mode == "generator":
        assert provider.isExpressionFunctionBody() and \
               provider.isGenerator()

        # TODO: This case should care about "needs_preserve", as for
        # Python3 it is actually not a stub of empty code.

        codes = getFrameGuardLightCode(
            frame_identifier      = context.getFrameHandle(),
            code_identifier       = statement_sequence.getCodeObjectHandle(
                context = context
            ),
            codes                 = local_emit.codes,
            parent_exception_exit = parent_exception_exit,
            frame_exception_exit  = frame_exception_exit,
            parent_return_exit    = parent_return_exit,
            frame_return_exit     = frame_return_exit,
            provider              = provider,
            context               = context
        ).split('\n')
    elif guard_mode == "pass_through":
        # This case does not care about "needs_preserve", as for that kind
        # of frame, it is an empty code stub anyway.
        codes = '\n'.join(local_emit.codes),
    elif guard_mode == "full":
        assert provider.isExpressionFunctionBody()

        codes = getFrameGuardHeavyCode(
            frame_identifier      = context.getFrameHandle(),
            code_identifier       = statement_sequence.getCodeObjectHandle(
                context
            ),
            parent_exception_exit = parent_exception_exit,
            parent_return_exit    = parent_return_exit,
            frame_exception_exit  = frame_exception_exit,
            frame_return_exit     = frame_return_exit,
            codes                 = local_emit.codes,
            needs_preserve        = needs_preserve,
            provider              = provider,
            context               = context
        ).split('\n')
    elif guard_mode == "once":
        codes = getFrameGuardOnceCode(
            frame_identifier      = context.getFrameHandle(),
            code_identifier       = statement_sequence.getCodeObjectHandle(
                context = context
            ),
            parent_exception_exit = parent_exception_exit,
            parent_return_exit    = parent_return_exit,
            frame_exception_exit  = frame_exception_exit,
            frame_return_exit     = frame_return_exit,
            codes                 = local_emit.codes,
            needs_preserve        = needs_preserve,
            provider              = provider,
            context               = context
        ).split('\n')
    else:
        assert False, guard_mode

    context.setExceptionEscape(parent_exception_exit)

    if frame_return_exit is not None:
        context.setReturnTarget(parent_return_exit)

    context.setFrameHandle(old_frame_handle)

    for line in codes:
        emit(line)


    # Complain if any temporary was not dealt with yet.
    assert not context.getCleanupTempnames(), \
      context.getCleanupTempnames()


def generateStatementSequenceCode(statement_sequence, emit, context,
                                  allow_none = False):

    if allow_none and statement_sequence is None:
        return None

    assert statement_sequence.kind == "STATEMENTS_SEQUENCE", statement_sequence

    statement_context = Contexts.PythonStatementCContext(context)

    _generateStatementSequenceCode(
        statement_sequence = statement_sequence,
        emit               = emit,
        context            = statement_context
    )

    # Complain if any temporary was not dealt with yet.
    assert not statement_context.getCleanupTempnames(), \
      statement_context.getCleanupTempnames()


def prepareModuleCode(global_context, module, module_name):
    # As this not only creates all modules, but also functions, it deals
    # also with its functions.

    assert module.isCompiledPythonModule(), module

    context = Contexts.PythonModuleContext(
        module         = module,
        module_name    = module_name,
        code_name      = module.getCodeName(),
        filename       = module.getFilename(),
        global_context = global_context
    )

    context.setExceptionEscape("module_exception_exit")

    statement_sequence = module.getBody()

    codes = Emission.SourceCodeCollector()

    generateStatementSequenceCode(
        statement_sequence = statement_sequence,
        emit               = codes,
        allow_none         = True,
        context            = context,
    )

    function_decl_codes = []
    function_body_codes = []

    for function_body in module.getUsedFunctions():
        function_code = generateFunctionBodyCode(
            function_body = function_body,
            context       = context
        )

        assert type(function_code) is str

        function_body_codes.append(function_code)

        if function_body.needsDirectCall():
            function_decl = getFunctionDirectDecl(
                function_identifier = function_body.getCodeName(),
                closure_variables   = function_body.getClosureVariables(),
                parameter_variables = function_body.getParameters().getAllVariables(),
                file_scope          = getExportScopeCode(
                    cross_module = function_body.isCrossModuleUsed()
                )
            )

            function_decl_codes.append(function_decl)

    for function_body in module.getCrossUsedFunctions():
        assert function_body.isCrossModuleUsed()

        function_decl = getFunctionDirectDecl(
            function_identifier = function_body.getCodeName(),
            closure_variables   = function_body.getClosureVariables(),
            parameter_variables = function_body.getParameters().getAllVariables(),
            file_scope          = getExportScopeCode(
                cross_module = function_body.isCrossModuleUsed()
            )
        )

        function_decl_codes.append(function_decl)

    for _identifier, code in sorted(iterItems(context.getHelperCodes())):
        function_body_codes.append(code)

    for _identifier, code in sorted(iterItems(context.getDeclarations())):
        function_decl_codes.append(code)

    function_body_codes = "\n\n".join(function_body_codes)
    function_decl_codes = "\n\n".join(function_decl_codes)

    template_values = getModuleValues(
        module_name         = module_name,
        module_identifier   = module.getCodeName(),
        codes               = codes.codes,
        function_decl_codes = function_decl_codes,
        function_body_codes = function_body_codes,
        temp_variables      = module.getTempVariables(),
        is_main_module      = module.isMainModule(),
        is_internal_module  = module.isInternalModule(),
        context             = context
    )

    if Utils.python_version >= 330:
        context.getConstantCode("__loader__")

    return template_values, context

def generateModuleCode(module_context, template_values):
    return getModuleCode(
        module_context  = module_context,
        template_values = template_values
    )


def generateHelpersCode(other_modules):
    calls_decl_code = getCallsDecls()

    loader_code = getMetapathLoaderBodyCode(other_modules)

    calls_body_code = getCallsCode()

    return calls_decl_code, calls_body_code + loader_code


def makeGlobalContext():
    return Contexts.PythonGlobalContext()


# TODO: Find a proper home for this code
def generateBuiltinIdCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "PyLong_FromVoidPtr",
        arg_desc   = (
            ("id_arg", expression.getValue()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )

# TODO: Find a proper home for this code
def generateBuiltinHashCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "BUILTIN_HASH",
        arg_desc   = (
            ("hash_arg", expression.getValue()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )


Helpers.setExpressionDispatchDict(
    {
        "ATTRIBUTE_LOOKUP"          : generateAttributeLookupCode,
        "ATTRIBUTE_LOOKUP_SPECIAL"  : generateAttributeLookupSpecialCode,
        "BUILTIN_SLICE"             : generateBuiltinSliceCode,
        "BUILTIN_HASH"              : generateBuiltinHashCode,
        "BUILTIN_ID"                : generateBuiltinIdCode,
        "CALL_EMPTY"                : generateCallCode,
        "CALL_KEYWORDS_ONLY"        : generateCallCode,
        "CALL_NO_KEYWORDS"          : generateCallCode,
        "CALL"                      : generateCallCode,
        "CONSTANT_REF"              : generateConstantReferenceCode,
        "DICT_OPERATION_UPDATE"      :generateDictOperationUpdateCode,
        "LIST_OPERATION_APPEND"     : generateListOperationAppendCode,
        "LIST_OPERATION_EXTEND"     : generateListOperationExtendCode,
        "LIST_OPERATION_POP"        : generateListOperationPopCode,
        "MODULE_FILE_ATTRIBUTE_REF" : generateModuleFileAttributeCode,
        "OPERATION_BINARY"          : generateOperationBinaryCode,
        "OPERATION_BINARY_INPLACE"  : generateOperationBinaryCode,
        "OPERATION_UNARY"           : generateOperationUnaryCode,
        "OPERATION_NOT"             : generateOperationUnaryCode,
        "RETURNED_VALUE_REF"        : generateReturnedValueRefCode,
        "SUBSCRIPT_LOOKUP"          : generateSubscriptLookupCode,
        "SET_OPERATION_ADD"         : generateSetOperationAddCode,
        "SET_OPERATION_UPDATE"      : generateSetOperationUpdateCode,
        "TEMP_VARIABLE_REF"         : generateVariableReferenceCode,
        "VARIABLE_REF"              : generateVariableReferenceCode,
        "YIELD"                     : generateYieldCode,
        "YIELD_FROM"                : generateYieldFromCode,
        "COROUTINE_CREATION"        : generateCoroutineCreationCode
    }
)
