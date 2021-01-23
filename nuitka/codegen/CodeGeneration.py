#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.build.DataComposerInterface import deriveModuleConstantsBlobName

from . import Contexts
from .AsyncgenCodes import (
    generateMakeAsyncgenObjectCode,
    getAsyncgenObjectCode,
    getAsyncgenObjectDeclCode,
)
from .AttributeCodes import (
    generateAssignmentAttributeCode,
    generateAttributeCheckCode,
    generateAttributeLookupCode,
    generateAttributeLookupSpecialCode,
    generateBuiltinGetattrCode,
    generateBuiltinHasattrCode,
    generateBuiltinSetattrCode,
    generateDelAttributeCode,
)
from .BranchCodes import generateBranchCode
from .BuiltinCodes import (
    generateBuiltinAbsCode,
    generateBuiltinAnonymousRefCode,
    generateBuiltinBinCode,
    generateBuiltinBoolCode,
    generateBuiltinBytearray1Code,
    generateBuiltinBytearray3Code,
    generateBuiltinClassmethodCode,
    generateBuiltinComplex1Code,
    generateBuiltinComplex2Code,
    generateBuiltinFloatCode,
    generateBuiltinHexCode,
    generateBuiltinOctCode,
    generateBuiltinOpenCode,
    generateBuiltinRange1Code,
    generateBuiltinRange2Code,
    generateBuiltinRange3Code,
    generateBuiltinRefCode,
    generateBuiltinStaticmethodCode,
    generateBuiltinSum1Code,
    generateBuiltinSum2Code,
    generateBuiltinType1Code,
    generateBuiltinType3Code,
    generateBuiltinXrange1Code,
    generateBuiltinXrange2Code,
    generateBuiltinXrange3Code,
)
from .CallCodes import generateCallCode, getCallsCode, getCallsDecls
from .ClassCodes import generateBuiltinSuperCode, generateSelectMetaclassCode
from .CodeHelpers import setExpressionDispatchDict, setStatementDispatchDict
from .ComparisonCodes import (
    generateBuiltinIsinstanceCode,
    generateComparisonExpressionCode,
)
from .ConditionalCodes import (
    generateConditionalAndOrCode,
    generateConditionalCode,
)
from .ConstantCodes import (
    generateConstantEllipsisReferenceCode,
    generateConstantFalseReferenceCode,
    generateConstantNoneReferenceCode,
    generateConstantReferenceCode,
    generateConstantTrueReferenceCode,
    getConstantsDefinitionCode,
)
from .CoroutineCodes import (
    generateAsyncIterCode,
    generateAsyncNextCode,
    generateAsyncWaitCode,
    generateMakeCoroutineObjectCode,
    getCoroutineObjectCode,
    getCoroutineObjectDeclCode,
)
from .DictCodes import (
    generateBuiltinDictCode,
    generateDictionaryCreationCode,
    generateDictOperationGetCode,
    generateDictOperationInCode,
    generateDictOperationRemoveCode,
    generateDictOperationSetCode,
    generateDictOperationSetCodeKeyValue,
    generateDictOperationUpdateCode,
)
from .EvalCodes import (
    generateBuiltinCompileCode,
    generateEvalCode,
    generateExecCode,
    generateExecfileCode,
    generateLocalsDictSyncCode,
)
from .ExceptionCodes import (
    generateBuiltinMakeExceptionCode,
    generateExceptionCaughtTracebackCode,
    generateExceptionCaughtTypeCode,
    generateExceptionCaughtValueCode,
    generateExceptionPublishCode,
    generateExceptionRefCode,
)
from .ExpressionCodes import (
    generateExpressionOnlyCode,
    generateSideEffectsCode,
)
from .FrameCodes import (
    generateFramePreserveExceptionCode,
    generateFrameRestoreExceptionCode,
)
from .FunctionCodes import (
    generateFunctionCallCode,
    generateFunctionCreationCode,
    generateFunctionErrorStrCode,
    generateFunctionOutlineCode,
    getExportScopeCode,
    getFunctionCode,
    getFunctionDirectDecl,
)
from .GeneratorCodes import (
    generateMakeGeneratorObjectCode,
    getGeneratorObjectCode,
    getGeneratorObjectDeclCode,
)
from .GlobalsLocalsCodes import (
    generateBuiltinDir1Code,
    generateBuiltinGlobalsCode,
    generateBuiltinLocalsCode,
    generateBuiltinLocalsRefCode,
    generateBuiltinVarsCode,
)
from .IdCodes import generateBuiltinHashCode, generateBuiltinIdCode
from .ImportCodes import (
    generateBuiltinImportCode,
    generateImportModuleHardCode,
    generateImportModuleNameHardCode,
    generateImportNameCode,
    generateImportStarCode,
)
from .IntegerCodes import (
    generateBuiltinInt1Code,
    generateBuiltinInt2Code,
    generateBuiltinLong1Code,
    generateBuiltinLong2Code,
)
from .IteratorCodes import (
    generateBuiltinAllCode,
    generateBuiltinAnyCode,
    generateBuiltinIter1Code,
    generateBuiltinIter2Code,
    generateBuiltinIterForUnpackCode,
    generateBuiltinLenCode,
    generateBuiltinNext1Code,
    generateBuiltinNext2Code,
    generateSpecialUnpackCode,
    generateUnpackCheckCode,
)
from .ListCodes import (
    generateBuiltinListCode,
    generateListCreationCode,
    generateListOperationAppendCode,
    generateListOperationExtendCode,
    generateListOperationPopCode,
)
from .LocalsDictCodes import (
    generateLocalsDictDelCode,
    generateLocalsDictSetCode,
    generateLocalsDictVariableCheckCode,
    generateLocalsDictVariableRefCode,
    generateLocalsDictVariableRefOrFallbackCode,
    generateReleaseLocalsDictCode,
    generateSetLocalsDictCode,
)
from .LoopCodes import (
    generateLoopBreakCode,
    generateLoopCode,
    generateLoopContinueCode,
)
from .ModuleCodes import (
    generateModuleAttributeCode,
    generateModuleAttributeFileCode,
    generateNuitkaLoaderCreationCode,
    getModuleCode,
)
from .OperationCodes import (
    generateOperationBinaryCode,
    generateOperationNotCode,
    generateOperationUnaryCode,
)
from .PrintCodes import generatePrintNewlineCode, generatePrintValueCode
from .RaisingCodes import (
    generateRaiseCode,
    generateRaiseExpressionCode,
    generateReraiseCode,
)
from .ReturnCodes import (
    generateGeneratorReturnNoneCode,
    generateGeneratorReturnValueCode,
    generateReturnCode,
    generateReturnConstantCode,
    generateReturnedValueCode,
)
from .SetCodes import (
    generateBuiltinFrozensetCode,
    generateBuiltinSetCode,
    generateSetCreationCode,
    generateSetLiteralCreationCode,
    generateSetOperationAddCode,
    generateSetOperationUpdateCode,
)
from .SliceCodes import (
    generateAssignmentSliceCode,
    generateBuiltinSlice1Code,
    generateBuiltinSlice2Code,
    generateBuiltinSlice3Code,
    generateDelSliceCode,
    generateSliceLookupCode,
)
from .StringCodes import (
    generateBuiltinAsciiCode,
    generateBuiltinBytes1Code,
    generateBuiltinBytes3Code,
    generateBuiltinChrCode,
    generateBuiltinFormatCode,
    generateBuiltinOrdCode,
    generateBuiltinStrCode,
    generateBuiltinUnicodeCode,
    generateStringContenationCode,
)
from .SubscriptCodes import (
    generateAssignmentSubscriptCode,
    generateDelSubscriptCode,
    generateSubscriptLookupCode,
)
from .TryCodes import generateTryCode
from .TupleCodes import generateBuiltinTupleCode, generateTupleCreationCode
from .VariableCodes import (
    generateAssignmentVariableCode,
    generateDelVariableCode,
    generateVariableReferenceCode,
    generateVariableReleaseCode,
)
from .YieldCodes import (
    generateYieldCode,
    generateYieldFromCode,
    generateYieldFromWaitableCode,
)

_generated_functions = {}


def generateFunctionBodyCode(function_body, context):
    # TODO: Generate both codes, and base direct/etc. decisions on context.
    # pylint: disable=too-many-branches

    function_identifier = function_body.getCodeName()

    if function_identifier in _generated_functions:
        return _generated_functions[function_identifier]

    if function_body.isExpressionGeneratorObjectBody():
        function_context = Contexts.PythonGeneratorObjectContext(
            parent=context, function=function_body
        )
    elif function_body.isExpressionClassBody():
        function_context = Contexts.PythonFunctionDirectContext(
            parent=context, function=function_body
        )
    elif function_body.isExpressionCoroutineObjectBody():
        function_context = Contexts.PythonCoroutineObjectContext(
            parent=context, function=function_body
        )
    elif function_body.isExpressionAsyncgenObjectBody():
        function_context = Contexts.PythonAsyncgenObjectContext(
            parent=context, function=function_body
        )
    elif function_body.needsCreation():
        function_context = Contexts.PythonFunctionCreatedContext(
            parent=context, function=function_body
        )
    else:
        function_context = Contexts.PythonFunctionDirectContext(
            parent=context, function=function_body
        )

    needs_exception_exit = function_body.mayRaiseException(BaseException)

    if function_body.isExpressionGeneratorObjectBody():
        function_code = getGeneratorObjectCode(
            context=function_context,
            function_identifier=function_identifier,
            closure_variables=function_body.getClosureVariables(),
            user_variables=function_body.getUserLocalVariables(),
            outline_variables=function_body.getOutlineLocalVariables(),
            temp_variables=function_body.getTempVariables(),
            needs_exception_exit=needs_exception_exit,
            needs_generator_return=function_body.needsGeneratorReturnExit(),
        )

        function_decl = getGeneratorObjectDeclCode(
            function_identifier=function_identifier,
            closure_variables=function_body.getClosureVariables(),
        )
    elif function_body.isExpressionCoroutineObjectBody():
        function_code = getCoroutineObjectCode(
            context=function_context,
            function_identifier=function_identifier,
            closure_variables=function_body.getClosureVariables(),
            user_variables=function_body.getUserLocalVariables(),
            outline_variables=function_body.getOutlineLocalVariables(),
            temp_variables=function_body.getTempVariables(),
            needs_exception_exit=needs_exception_exit,
            needs_generator_return=function_body.needsGeneratorReturnExit(),
        )

        function_decl = getCoroutineObjectDeclCode(
            function_identifier=function_body.getCodeName(),
            closure_variables=function_body.getClosureVariables(),
        )

    elif function_body.isExpressionAsyncgenObjectBody():
        function_code = getAsyncgenObjectCode(
            context=function_context,
            function_identifier=function_identifier,
            closure_variables=function_body.getClosureVariables(),
            user_variables=function_body.getUserLocalVariables(),
            outline_variables=function_body.getOutlineLocalVariables(),
            temp_variables=function_body.getTempVariables(),
            needs_exception_exit=needs_exception_exit,
            needs_generator_return=function_body.needsGeneratorReturnExit(),
        )

        function_decl = getAsyncgenObjectDeclCode(
            function_identifier=function_body.getCodeName(),
            closure_variables=function_body.getClosureVariables(),
        )

    elif function_body.isExpressionClassBody():
        function_code = getFunctionCode(
            context=function_context,
            function_identifier=function_identifier,
            parameters=None,
            closure_variables=function_body.getClosureVariables(),
            user_variables=function_body.getUserLocalVariables()
            + function_body.getOutlineLocalVariables(),
            temp_variables=function_body.getTempVariables(),
            function_doc=function_body.getDoc(),
            needs_exception_exit=needs_exception_exit,
            file_scope=getExportScopeCode(cross_module=False),
        )

        function_decl = getFunctionDirectDecl(
            function_identifier=function_identifier,
            closure_variables=function_body.getClosureVariables(),
            file_scope=getExportScopeCode(cross_module=False),
            context=function_context,
        )

    else:
        function_code = getFunctionCode(
            context=function_context,
            function_identifier=function_identifier,
            parameters=function_body.getParameters(),
            closure_variables=function_body.getClosureVariables(),
            user_variables=function_body.getUserLocalVariables()
            + function_body.getOutlineLocalVariables(),
            temp_variables=function_body.getTempVariables(),
            function_doc=function_body.getDoc(),
            needs_exception_exit=needs_exception_exit,
            file_scope=getExportScopeCode(
                cross_module=function_body.isCrossModuleUsed()
            ),
        )

        if function_body.needsDirectCall():
            function_decl = getFunctionDirectDecl(
                function_identifier=function_identifier,
                closure_variables=function_body.getClosureVariables(),
                file_scope=getExportScopeCode(
                    cross_module=function_body.isCrossModuleUsed()
                ),
                context=function_context,
            )
        else:
            function_decl = None

    return function_code, function_decl


def generateModuleCode(module, data_filename):
    # As this not only creates all modules, but also functions, it deals
    # also with its functions.

    assert module.isCompiledPythonModule(), module

    context = Contexts.PythonModuleContext(
        module=module,
        data_filename=data_filename,
    )

    context.setExceptionEscape("module_exception_exit")

    function_decl_codes = []
    function_body_codes = []

    for function_body in module.getUsedFunctions():
        # Constant function returners get no code.
        (
            is_constant_returning,
            _constant_return_value,
        ) = function_body.getConstantReturnValue()
        if is_constant_returning:
            continue

        function_code, function_decl = generateFunctionBodyCode(
            function_body=function_body, context=context
        )

        function_body_codes.append(function_code)

        if function_decl is not None:
            function_decl_codes.append(function_decl)

    # These are for functions used from other modules. Due to cyclic
    # dependencies, we cannot rely on those to be already created.
    for function_body in module.getCrossUsedFunctions():
        assert function_body.isCrossModuleUsed()

        function_decl = getFunctionDirectDecl(
            function_identifier=function_body.getCodeName(),
            closure_variables=function_body.getClosureVariables(),
            file_scope=getExportScopeCode(
                cross_module=function_body.isCrossModuleUsed()
            ),
            context=Contexts.PythonFunctionDirectContext(
                parent=context, function=function_body
            ),
        )

        function_decl_codes.append(function_decl)

    return getModuleCode(
        module=module,
        function_decl_codes=function_decl_codes,
        function_body_codes=function_body_codes,
        module_const_blob_name=deriveModuleConstantsBlobName(data_filename),
        context=context,
    )


def generateHelpersCode():
    calls_decl_code = getCallsDecls()

    calls_body_code = getCallsCode()

    constants_header_code, constants_body_code = getConstantsDefinitionCode()

    return (
        calls_decl_code,
        calls_body_code,
        constants_header_code,
        constants_body_code,
    )


setExpressionDispatchDict(
    {
        "EXPRESSION_ATTRIBUTE_CHECK": generateAttributeCheckCode,
        "EXPRESSION_ATTRIBUTE_LOOKUP": generateAttributeLookupCode,
        "EXPRESSION_ATTRIBUTE_LOOKUP_SPECIAL": generateAttributeLookupSpecialCode,
        "EXPRESSION_BUILTIN_SLICE3": generateBuiltinSlice3Code,
        "EXPRESSION_BUILTIN_SLICE2": generateBuiltinSlice2Code,
        "EXPRESSION_BUILTIN_SLICE1": generateBuiltinSlice1Code,
        "EXPRESSION_BUILTIN_HASH": generateBuiltinHashCode,
        "EXPRESSION_BUILTIN_ID": generateBuiltinIdCode,
        "EXPRESSION_BUILTIN_COMPILE": generateBuiltinCompileCode,
        "EXPRESSION_BUILTIN_EXECFILE": generateExecfileCode,
        "EXPRESSION_BUILTIN_EVAL": generateEvalCode,
        "EXPRESSION_BUILTIN_EXEC": generateEvalCode,
        "EXPRESSION_BUILTIN_ITER_FOR_UNPACK": generateBuiltinIterForUnpackCode,
        "EXPRESSION_BUILTIN_ITER1": generateBuiltinIter1Code,
        "EXPRESSION_BUILTIN_ITER2": generateBuiltinIter2Code,
        "EXPRESSION_BUILTIN_NEXT1": generateBuiltinNext1Code,
        "EXPRESSION_BUILTIN_NEXT2": generateBuiltinNext2Code,
        "EXPRESSION_BUILTIN_SUM1": generateBuiltinSum1Code,
        "EXPRESSION_BUILTIN_SUM2": generateBuiltinSum2Code,
        "EXPRESSION_BUILTIN_TYPE1": generateBuiltinType1Code,
        "EXPRESSION_BUILTIN_TYPE3": generateBuiltinType3Code,
        "EXPRESSION_BUILTIN_IMPORT": generateBuiltinImportCode,
        "EXPRESSION_BUILTIN_BOOL": generateBuiltinBoolCode,
        "EXPRESSION_BUILTIN_BYTEARRAY1": generateBuiltinBytearray1Code,
        "EXPRESSION_BUILTIN_BYTEARRAY3": generateBuiltinBytearray3Code,
        "EXPRESSION_BUILTIN_INT1": generateBuiltinInt1Code,
        "EXPRESSION_BUILTIN_INT2": generateBuiltinInt2Code,
        "EXPRESSION_BUILTIN_LONG1": generateBuiltinLong1Code,
        "EXPRESSION_BUILTIN_LONG2": generateBuiltinLong2Code,
        "EXPRESSION_BUILTIN_FLOAT": generateBuiltinFloatCode,
        "EXPRESSION_BUILTIN_COMPLEX1": generateBuiltinComplex1Code,
        "EXPRESSION_BUILTIN_COMPLEX2": generateBuiltinComplex2Code,
        "EXPRESSION_BUILTIN_LEN": generateBuiltinLenCode,
        "EXPRESSION_BUILTIN_STR_P2": generateBuiltinStrCode,
        "EXPRESSION_BUILTIN_STR_P3": generateBuiltinStrCode,
        "EXPRESSION_BUILTIN_BYTES1": generateBuiltinBytes1Code,
        "EXPRESSION_BUILTIN_BYTES3": generateBuiltinBytes3Code,
        "EXPRESSION_BUILTIN_UNICODE_P2": generateBuiltinUnicodeCode,
        "EXPRESSION_BUILTIN_CHR": generateBuiltinChrCode,
        "EXPRESSION_BUILTIN_ORD": generateBuiltinOrdCode,
        "EXPRESSION_BUILTIN_BIN": generateBuiltinBinCode,
        "EXPRESSION_BUILTIN_OCT": generateBuiltinOctCode,
        "EXPRESSION_BUILTIN_HEX": generateBuiltinHexCode,
        "EXPRESSION_BUILTIN_TUPLE": generateBuiltinTupleCode,
        "EXPRESSION_BUILTIN_LIST": generateBuiltinListCode,
        "EXPRESSION_BUILTIN_SET": generateBuiltinSetCode,
        "EXPRESSION_BUILTIN_ANY": generateBuiltinAnyCode,
        "EXPRESSION_BUILTIN_FROZENSET": generateBuiltinFrozensetCode,
        "EXPRESSION_BUILTIN_ALL": generateBuiltinAllCode,
        "EXPRESSION_BUILTIN_DICT": generateBuiltinDictCode,
        "EXPRESSION_BUILTIN_LOCALS_COPY": generateBuiltinLocalsCode,
        "EXPRESSION_BUILTIN_LOCALS_UPDATED": generateBuiltinLocalsCode,
        "EXPRESSION_BUILTIN_LOCALS_REF": generateBuiltinLocalsRefCode,
        "EXPRESSION_BUILTIN_GLOBALS": generateBuiltinGlobalsCode,
        "EXPRESSION_BUILTIN_SUPER": generateBuiltinSuperCode,
        "EXPRESSION_BUILTIN_ISINSTANCE": generateBuiltinIsinstanceCode,
        "EXPRESSION_BUILTIN_DIR1": generateBuiltinDir1Code,
        "EXPRESSION_BUILTIN_VARS": generateBuiltinVarsCode,
        "EXPRESSION_BUILTIN_HASATTR": generateBuiltinHasattrCode,
        "EXPRESSION_BUILTIN_GETATTR": generateBuiltinGetattrCode,
        "EXPRESSION_BUILTIN_SETATTR": generateBuiltinSetattrCode,
        "EXPRESSION_BUILTIN_OPEN": generateBuiltinOpenCode,
        "EXPRESSION_BUILTIN_STATICMETHOD": generateBuiltinStaticmethodCode,
        "EXPRESSION_BUILTIN_CLASSMETHOD": generateBuiltinClassmethodCode,
        "EXPRESSION_BUILTIN_RANGE1": generateBuiltinRange1Code,
        "EXPRESSION_BUILTIN_RANGE2": generateBuiltinRange2Code,
        "EXPRESSION_BUILTIN_RANGE3": generateBuiltinRange3Code,
        "EXPRESSION_BUILTIN_XRANGE1": generateBuiltinXrange1Code,
        "EXPRESSION_BUILTIN_XRANGE2": generateBuiltinXrange2Code,
        "EXPRESSION_BUILTIN_XRANGE3": generateBuiltinXrange3Code,
        "EXPRESSION_BUILTIN_MAKE_EXCEPTION": generateBuiltinMakeExceptionCode,
        "EXPRESSION_BUILTIN_MAKE_EXCEPTION_IMPORT_ERROR": generateBuiltinMakeExceptionCode,
        "EXPRESSION_BUILTIN_REF": generateBuiltinRefCode,
        "EXPRESSION_BUILTIN_WITH_CONTEXT_REF": generateBuiltinRefCode,
        "EXPRESSION_BUILTIN_EXCEPTION_REF": generateExceptionRefCode,
        "EXPRESSION_BUILTIN_ANONYMOUS_REF": generateBuiltinAnonymousRefCode,
        "EXPRESSION_CAUGHT_EXCEPTION_TYPE_REF": generateExceptionCaughtTypeCode,
        "EXPRESSION_CAUGHT_EXCEPTION_VALUE_REF": generateExceptionCaughtValueCode,
        "EXPRESSION_CAUGHT_EXCEPTION_TRACEBACK_REF": generateExceptionCaughtTracebackCode,
        "EXPRESSION_CALL_EMPTY": generateCallCode,
        "EXPRESSION_CALL_KEYWORDS_ONLY": generateCallCode,
        "EXPRESSION_CALL_NO_KEYWORDS": generateCallCode,
        "EXPRESSION_CALL": generateCallCode,
        "EXPRESSION_CONSTANT_NONE_REF": generateConstantNoneReferenceCode,
        "EXPRESSION_CONSTANT_TRUE_REF": generateConstantTrueReferenceCode,
        "EXPRESSION_CONSTANT_FALSE_REF": generateConstantFalseReferenceCode,
        "EXPRESSION_CONSTANT_STR_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_STR_EMPTY_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_UNICODE_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_UNICODE_EMPTY_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_BYTES_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_BYTES_EMPTY_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_INT_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_LONG_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_FLOAT_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_COMPLEX_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_ELLIPSIS_REF": generateConstantEllipsisReferenceCode,
        "EXPRESSION_CONSTANT_DICT_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_DICT_EMPTY_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_TUPLE_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_TUPLE_EMPTY_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_TUPLE_MUTABLE_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_LIST_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_LIST_EMPTY_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_SET_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_SET_EMPTY_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_FROZENSET_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_FROZENSET_EMPTY_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_SLICE_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_XRANGE_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_TYPE_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_BYTEARRAY_REF": generateConstantReferenceCode,
        "EXPRESSION_CONDITIONAL": generateConditionalCode,
        "EXPRESSION_CONDITIONAL_OR": generateConditionalAndOrCode,
        "EXPRESSION_CONDITIONAL_AND": generateConditionalAndOrCode,
        "EXPRESSION_COMPARISON": generateComparisonExpressionCode,
        "EXPRESSION_COMPARISON_IS": generateComparisonExpressionCode,
        "EXPRESSION_COMPARISON_IS_NOT": generateComparisonExpressionCode,
        "EXPRESSION_COMPARISON_IN": generateComparisonExpressionCode,
        "EXPRESSION_COMPARISON_NOT_IN": generateComparisonExpressionCode,
        "EXPRESSION_COMPARISON_EXCEPTION_MATCH": generateComparisonExpressionCode,
        "EXPRESSION_COMPARISON_EXCEPTION_MISMATCH": generateComparisonExpressionCode,
        "EXPRESSION_COMPARISON_LT": generateComparisonExpressionCode,
        "EXPRESSION_COMPARISON_LTE": generateComparisonExpressionCode,
        "EXPRESSION_COMPARISON_GT": generateComparisonExpressionCode,
        "EXPRESSION_COMPARISON_GTE": generateComparisonExpressionCode,
        "EXPRESSION_COMPARISON_EQ": generateComparisonExpressionCode,
        "EXPRESSION_COMPARISON_NEQ": generateComparisonExpressionCode,
        "EXPRESSION_DICT_OPERATION_GET": generateDictOperationGetCode,
        "EXPRESSION_DICT_OPERATION_IN": generateDictOperationInCode,
        "EXPRESSION_DICT_OPERATION_NOT_IN": generateDictOperationInCode,
        "EXPRESSION_FUNCTION_CREATION": generateFunctionCreationCode,
        "EXPRESSION_FUNCTION_CALL": generateFunctionCallCode,
        "EXPRESSION_FUNCTION_ERROR_STR": generateFunctionErrorStrCode,
        "EXPRESSION_IMPORT_MODULE_HARD": generateImportModuleHardCode,
        "EXPRESSION_IMPORT_MODULE_NAME_HARD": generateImportModuleNameHardCode,
        "EXPRESSION_IMPORT_NAME": generateImportNameCode,
        "EXPRESSION_LIST_OPERATION_EXTEND": generateListOperationExtendCode,
        "EXPRESSION_LIST_OPERATION_EXTEND_FOR_UNPACK": generateListOperationExtendCode,
        "EXPRESSION_LIST_OPERATION_POP": generateListOperationPopCode,
        "EXPRESSION_MODULE_ATTRIBUTE_FILE_REF": generateModuleAttributeFileCode,
        "EXPRESSION_MODULE_ATTRIBUTE_NAME_REF": generateModuleAttributeCode,
        "EXPRESSION_MODULE_ATTRIBUTE_PACKAGE_REF": generateModuleAttributeCode,
        "EXPRESSION_MODULE_ATTRIBUTE_LOADER_REF": generateModuleAttributeCode,
        "EXPRESSION_MODULE_ATTRIBUTE_SPEC_REF": generateModuleAttributeCode,
        "EXPRESSION_MAKE_GENERATOR_OBJECT": generateMakeGeneratorObjectCode,
        "EXPRESSION_MAKE_COROUTINE_OBJECT": generateMakeCoroutineObjectCode,
        "EXPRESSION_MAKE_ASYNCGEN_OBJECT": generateMakeAsyncgenObjectCode,
        "EXPRESSION_MAKE_SET": generateSetCreationCode,
        "EXPRESSION_MAKE_SET_LITERAL": generateSetLiteralCreationCode,
        "EXPRESSION_MAKE_TUPLE": generateTupleCreationCode,
        "EXPRESSION_MAKE_LIST": generateListCreationCode,
        "EXPRESSION_MAKE_DICT": generateDictionaryCreationCode,
        "EXPRESSION_OPERATION_BINARY_ADD": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_BINARY_SUB": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_BINARY_MULT": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_BINARY_FLOOR_DIV": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_BINARY_OLD_DIV": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_BINARY_TRUE_DIV": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_BINARY_DIVMOD": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_BINARY_MOD": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_BINARY_POW": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_BINARY_LSHIFT": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_BINARY_RSHIFT": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_BINARY_BIT_OR": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_BINARY_BIT_AND": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_BINARY_BIT_XOR": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_BINARY_MAT_MULT": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_INPLACE_ADD": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_INPLACE_SUB": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_INPLACE_MULT": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_INPLACE_FLOOR_DIV": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_INPLACE_OLD_DIV": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_INPLACE_TRUE_DIV": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_INPLACE_MOD": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_INPLACE_POW": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_INPLACE_LSHIFT": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_INPLACE_RSHIFT": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_INPLACE_BIT_OR": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_INPLACE_BIT_AND": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_INPLACE_BIT_XOR": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_INPLACE_MAT_MULT": generateOperationBinaryCode,
        "EXPRESSION_OPERATION_UNARY": generateOperationUnaryCode,
        "EXPRESSION_OPERATION_NOT": generateOperationNotCode,
        "EXPRESSION_OPERATION_ABS": generateBuiltinAbsCode,
        "EXPRESSION_OUTLINE_BODY": generateFunctionOutlineCode,
        "EXPRESSION_OUTLINE_FUNCTION": generateFunctionOutlineCode,
        # TODO: Rename to make more clear it is an outline
        "EXPRESSION_CLASS_BODY": generateFunctionOutlineCode,
        "EXPRESSION_SUBSCRIPT_LOOKUP": generateSubscriptLookupCode,
        "EXPRESSION_SLICE_LOOKUP": generateSliceLookupCode,
        "EXPRESSION_SET_OPERATION_UPDATE": generateSetOperationUpdateCode,
        "EXPRESSION_SIDE_EFFECTS": generateSideEffectsCode,
        "EXPRESSION_SPECIAL_UNPACK": generateSpecialUnpackCode,
        "EXPRESSION_TEMP_VARIABLE_REF": generateVariableReferenceCode,
        "EXPRESSION_VARIABLE_REF": generateVariableReferenceCode,
        "EXPRESSION_VARIABLE_OR_BUILTIN_REF": generateVariableReferenceCode,
        "EXPRESSION_YIELD": generateYieldCode,
        "EXPRESSION_YIELD_FROM": generateYieldFromCode,
        "EXPRESSION_YIELD_FROM_WAITABLE": generateYieldFromWaitableCode,
        "EXPRESSION_ASYNC_WAIT": generateAsyncWaitCode,
        "EXPRESSION_ASYNC_WAIT_ENTER": generateAsyncWaitCode,
        "EXPRESSION_ASYNC_WAIT_EXIT": generateAsyncWaitCode,
        "EXPRESSION_ASYNC_ITER": generateAsyncIterCode,
        "EXPRESSION_ASYNC_NEXT": generateAsyncNextCode,
        "EXPRESSION_SELECT_METACLASS": generateSelectMetaclassCode,
        "EXPRESSION_STRING_CONCATENATION": generateStringContenationCode,
        "EXPRESSION_BUILTIN_FORMAT": generateBuiltinFormatCode,
        "EXPRESSION_BUILTIN_ASCII": generateBuiltinAsciiCode,
        "EXPRESSION_LOCALS_VARIABLE_CHECK": generateLocalsDictVariableCheckCode,
        "EXPRESSION_LOCALS_VARIABLE_REF_OR_FALLBACK": generateLocalsDictVariableRefOrFallbackCode,
        "EXPRESSION_LOCALS_VARIABLE_REF": generateLocalsDictVariableRefCode,
        "EXPRESSION_RAISE_EXCEPTION": generateRaiseExpressionCode,
        "EXPRESSION_NUITKA_LOADER_CREATION": generateNuitkaLoaderCreationCode,
    }
)

setStatementDispatchDict(
    {
        "STATEMENT_ASSIGNMENT_VARIABLE": generateAssignmentVariableCode,
        "STATEMENT_ASSIGNMENT_ATTRIBUTE": generateAssignmentAttributeCode,
        "STATEMENT_ASSIGNMENT_SUBSCRIPT": generateAssignmentSubscriptCode,
        "STATEMENT_ASSIGNMENT_SLICE": generateAssignmentSliceCode,
        "STATEMENT_DEL_VARIABLE": generateDelVariableCode,
        "STATEMENT_DEL_ATTRIBUTE": generateDelAttributeCode,
        "STATEMENT_DEL_SUBSCRIPT": generateDelSubscriptCode,
        "STATEMENT_DEL_SLICE": generateDelSliceCode,
        "STATEMENT_DICT_OPERATION_REMOVE": generateDictOperationRemoveCode,
        "STATEMENT_DICT_OPERATION_UPDATE": generateDictOperationUpdateCode,
        "STATEMENT_RELEASE_VARIABLE": generateVariableReleaseCode,
        "STATEMENT_EXPRESSION_ONLY": generateExpressionOnlyCode,
        "STATEMENT_RETURN": generateReturnCode,
        "STATEMENT_RETURN_TRUE": generateReturnConstantCode,
        "STATEMENT_RETURN_FALSE": generateReturnConstantCode,
        "STATEMENT_RETURN_NONE": generateReturnConstantCode,
        "STATEMENT_RETURN_CONSTANT": generateReturnConstantCode,
        "STATEMENT_RETURN_RETURNED_VALUE": generateReturnedValueCode,
        "STATEMENT_GENERATOR_RETURN": generateGeneratorReturnValueCode,
        "STATEMENT_GENERATOR_RETURN_NONE": generateGeneratorReturnNoneCode,
        "STATEMENT_CONDITIONAL": generateBranchCode,
        "STATEMENT_TRY": generateTryCode,
        "STATEMENT_PRINT_VALUE": generatePrintValueCode,
        "STATEMENT_PRINT_NEWLINE": generatePrintNewlineCode,
        "STATEMENT_IMPORT_STAR": generateImportStarCode,
        "STATEMENT_LIST_OPERATION_APPEND": generateListOperationAppendCode,
        "STATEMENT_SET_OPERATION_ADD": generateSetOperationAddCode,
        "STATEMENT_DICT_OPERATION_SET": generateDictOperationSetCode,
        "STATEMENT_DICT_OPERATION_SET_KEY_VALUE": generateDictOperationSetCodeKeyValue,
        "STATEMENT_LOCALS_DICT_OPERATION_SET": generateLocalsDictSetCode,
        "STATEMENT_LOCALS_DICT_OPERATION_DEL": generateLocalsDictDelCode,
        "STATEMENT_LOOP": generateLoopCode,
        "STATEMENT_LOOP_BREAK": generateLoopBreakCode,
        "STATEMENT_LOOP_CONTINUE": generateLoopContinueCode,
        "STATEMENT_RAISE_EXCEPTION": generateRaiseCode,
        "STATEMENT_RAISE_EXCEPTION_IMPLICIT": generateRaiseCode,
        "STATEMENT_RERAISE_EXCEPTION": generateReraiseCode,
        "STATEMENT_SPECIAL_UNPACK_CHECK": generateUnpackCheckCode,
        "STATEMENT_EXEC": generateExecCode,
        "STATEMENT_LOCALS_DICT_SYNC": generateLocalsDictSyncCode,
        "STATEMENT_SET_LOCALS": generateSetLocalsDictCode,
        "STATEMENT_SET_LOCALS_DICTIONARY": generateSetLocalsDictCode,
        "STATEMENT_RELEASE_LOCALS": generateReleaseLocalsDictCode,
        "STATEMENT_PRESERVE_FRAME_EXCEPTION": generateFramePreserveExceptionCode,
        "STATEMENT_RESTORE_FRAME_EXCEPTION": generateFrameRestoreExceptionCode,
        "STATEMENT_PUBLISH_EXCEPTION": generateExceptionPublishCode,
    }
)
