#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" The code generation.

No language specifics at all are supposed to be present here. Instead it is
using primitives from the given generator to build code sequences (list of
strings).

As such this is the place that knows how to take a condition and two code
branches and make a code block out of it. But it doesn't contain any target
language syntax.
"""

from nuitka.nodes.AttributeNodesGenerated import (
    attribute_classes,
    attribute_typed_classes,
)
from nuitka.nodes.BytesNodes import getBytesOperationClasses
from nuitka.nodes.StrNodes import getStrOperationClasses
from nuitka.plugins.Plugins import Plugins
from nuitka.utils.CStrings import encodePythonStringToC

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
    generateBuiltinInputCode,
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
from .CallCodes import generateCallCode, getCallsCode
from .ClassCodes import (
    generateBuiltinSuper1Code,
    generateBuiltinSuperCode,
    generateSelectMetaclassCode,
    generateTypeOperationPrepareCode,
)
from .CodeHelpers import addExpressionDispatchDict, setStatementDispatchDict
from .ComparisonCodes import (
    generateBuiltinIsinstanceCode,
    generateBuiltinIssubclassCode,
    generateComparisonExpressionCode,
    generateMatchTypeCheckMappingCode,
    generateMatchTypeCheckSequenceCode,
    generateRichComparisonExpressionCode,
    generateSubtypeCheckCode,
    generateTypeCheckCode,
)
from .ConditionalCodes import (
    generateConditionalAndOrCode,
    generateConditionalCode,
)
from .ConstantCodes import (
    generateConstantGenericAliasCode,
    generateConstantReferenceCode,
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
from .CtypesCodes import generateCtypesCdllCallCode
from .DictCodes import (
    generateBuiltinDictCode,
    generateDictionaryCreationCode,
    generateDictOperationClearCode,
    generateDictOperationCopyCode,
    generateDictOperationFromkeys2Code,
    generateDictOperationFromkeys3Code,
    generateDictOperationFromkeysRefCode,
    generateDictOperationGet2Code,
    generateDictOperationGet3Code,
    generateDictOperationInCode,
    generateDictOperationItemCode,
    generateDictOperationItemsCode,
    generateDictOperationIteritemsCode,
    generateDictOperationIterkeysCode,
    generateDictOperationItervaluesCode,
    generateDictOperationKeysCode,
    generateDictOperationPop2Code,
    generateDictOperationPop3Code,
    generateDictOperationPopitemCode,
    generateDictOperationRemoveCode,
    generateDictOperationSetCode,
    generateDictOperationSetCodeKeyValue,
    generateDictOperationSetdefault2Code,
    generateDictOperationSetdefault3Code,
    generateDictOperationUpdate2Code,
    generateDictOperationUpdate3Code,
    generateDictOperationUpdateCode,
    generateDictOperationValuesCode,
    generateDictOperationViewitemsCode,
    generateDictOperationViewkeysCode,
    generateDictOperationViewvaluesCode,
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
    generateConstantSysVersionInfoCode,
    generateImportlibImportCallCode,
    generateImportModuleFixedCode,
    generateImportModuleHardCode,
    generateImportModuleNameHardCode,
    generateImportNameCode,
    generateImportStarCode,
)
from .InjectCCodes import generateInjectCCode
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
    generateUnpackCheckFromIteratedCode,
)
from .ListCodes import (
    generateBuiltinListCode,
    generateListCreationCode,
    generateListOperationAppendCode,
    generateListOperationAppendCode2,
    generateListOperationClearCode,
    generateListOperationCopyCode,
    generateListOperationCountCode,
    generateListOperationExtendCode,
    generateListOperationIndex2Code,
    generateListOperationIndex3Code,
    generateListOperationIndex4Code,
    generateListOperationInsertCode,
    generateListOperationPop1Code,
    generateListOperationPop2Code,
    generateListOperationRemoveCode,
    generateListOperationReverseCode,
    generateListOperationSort1Code,
    generateListOperationSort2Code,
    generateListOperationSort3Code,
)
from .LocalsDictCodes import (
    generateLocalsDictDelCode,
    generateLocalsDictSetCode,
    generateLocalsDictVariableCheckCode,
    generateLocalsDictVariableRefCode,
    generateLocalsDictVariableRefOrFallbackCode,
    generateReleaseLocalsDictCode,
    generateSetLocalsDictCode,
    generateSetLocalsMappingCode,
)
from .LoopCodes import (
    generateLoopBreakCode,
    generateLoopCode,
    generateLoopContinueCode,
)
from .MatchCodes import generateMatchArgsCode
from .ModuleCodes import (
    generateModuleAttributeCode,
    generateModuleAttributeFileCode,
    getModuleCode,
)
from .NetworkxCodes import generateNetworkxUtilsDecoratorsArgmapCallCode
from .OperationCodes import (
    generateOperationBinaryCode,
    generateOperationNotCode,
    generateOperationUnaryCode,
)
from .PackageResourceCodes import (
    generateImportlibMetadataBackportEntryPointsCallCode,
    generateImportlibMetadataBackportEntryPointsValueCode,
    generateImportlibMetadataBackportEntryPointValueCode,
    generateImportlibMetadataBackportSelectableGroupsValueCode,
    generateImportlibMetadataBackportVersionCallCode,
    generateImportlibMetadataDistributionCallCode,
    generateImportlibMetadataDistributionValueCode,
    generateImportlibMetadataEntryPointsSince310CallCode,
    generateImportlibMetadataEntryPointsValueCode,
    generateImportlibMetadataEntryPointValueCode,
    generateImportlibMetadataSelectableGroupsValueCode,
    generateImportlibMetadataVersionCallCode,
    generateImportlibResourcesFilesCallCode,
    generateImportlibResourcesReadBinaryCallCode,
    generateImportlibResourcesReadTextCallCode,
    generateOsListdirCallCode,
    generateOsLstatCallCode,
    generateOsPathAbspathCallCode,
    generateOsPathBasenameCallCode,
    generateOsPathDirnameCallCode,
    generateOsPathExistsCallCode,
    generateOsPathIsabsCallCode,
    generateOsPathIsdirCallCode,
    generateOsPathIsfileCallCode,
    generateOsPathNormpathCallCode,
    generateOsStatCallCode,
    generateOsUnameCallCode,
    generatePkglibGetDataCallCode,
    generatePkgResourcesDistributionValueCode,
    generatePkgResourcesEntryPointValueCode,
    generatePkgResourcesGetDistributionCallCode,
    generatePkgResourcesIterEntryPointsCallCode,
    generatePkgResourcesRequireCallCode,
    generatePkgResourcesResourceStreamCallCode,
    generatePkgResourcesResourceStringCallCode,
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
    generateBytesOperationCode,
    generateStrFormatMethodCode,
    generateStringConcatenationCode,
    generateStrOperationCode,
)
from .SubscriptCodes import (
    generateAssignmentSubscriptCode,
    generateDelSubscriptCode,
    generateMatchSubscriptCheckCode,
    generateSubscriptLookupCode,
)
from .TensorflowCodes import generateTensorflowFunctionCallCode
from .TryCodes import generateTryCode
from .TupleCodes import generateBuiltinTupleCode, generateTupleCreationCode
from .TypeAliasCodes import (
    generateTypeAliasCode,
    generateTypeGenericCode,
    generateTypeVarCode,
)
from .VariableCodes import (
    generateAssignmentVariableCode,
    generateDelVariableCode,
    generateVariableReferenceCode,
    generateVariableReleaseCode,
)
from .YieldCodes import (
    generateYieldCode,
    generateYieldFromAwaitableCode,
    generateYieldFromCode,
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
    elif function_body.isExpressionClassBodyBase():
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
        if function_body.subnode_body is not None:
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
        else:
            function_code = None
            function_decl = None
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

    elif function_body.isExpressionClassBodyBase():
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


def _generateModuleCode(module, data_filename):
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
        if function_body.needsCreation():
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

        if function_code is not None:
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
        module_const_blob_name=encodePythonStringToC(
            Plugins.deriveModuleConstantsBlobName(data_filename)
        ),
        context=context,
    )


def generateModuleCode(module, data_filename):
    try:
        return _generateModuleCode(module=module, data_filename=data_filename)
    except KeyboardInterrupt:
        raise KeyboardInterrupt("Interrupted while working on", module)


def generateHelpersCode():
    calls_decl_code, calls_body_code = getCallsCode()

    constants_header_code, constants_body_code = getConstantsDefinitionCode()

    return (
        calls_decl_code,
        calls_body_code,
        constants_header_code,
        constants_body_code,
    )


# TODO: Some of these have names that are way too long, and this should be more automatic in
# standard cases, e.g. through generation.
# pylint: disable=line-too-long
addExpressionDispatchDict(
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
        "EXPRESSION_LOCALS_DICT_REF": generateBuiltinLocalsRefCode,
        "EXPRESSION_BUILTIN_GLOBALS": generateBuiltinGlobalsCode,
        "EXPRESSION_BUILTIN_SUPER0": generateBuiltinSuperCode,
        "EXPRESSION_BUILTIN_SUPER2": generateBuiltinSuperCode,
        "EXPRESSION_BUILTIN_SUPER1": generateBuiltinSuper1Code,
        "EXPRESSION_BUILTIN_ISINSTANCE": generateBuiltinIsinstanceCode,
        "EXPRESSION_BUILTIN_ISSUBCLASS": generateBuiltinIssubclassCode,
        "EXPRESSION_TYPE_CHECK": generateTypeCheckCode,
        "EXPRESSION_SUBTYPE_CHECK": generateSubtypeCheckCode,
        "EXPRESSION_MATCH_ARGS": generateMatchArgsCode,
        "EXPRESSION_MATCH_TYPE_CHECK_SEQUENCE": generateMatchTypeCheckSequenceCode,
        "EXPRESSION_MATCH_TYPE_CHECK_MAPPING": generateMatchTypeCheckMappingCode,
        "EXPRESSION_MATCH_SUBSCRIPT_CHECK": generateMatchSubscriptCheckCode,
        "EXPRESSION_BUILTIN_DIR1": generateBuiltinDir1Code,
        "EXPRESSION_BUILTIN_VARS": generateBuiltinVarsCode,
        "EXPRESSION_BUILTIN_HASATTR": generateBuiltinHasattrCode,
        "EXPRESSION_BUILTIN_GETATTR": generateBuiltinGetattrCode,
        "EXPRESSION_BUILTIN_SETATTR": generateBuiltinSetattrCode,
        "EXPRESSION_BUILTIN_INPUT": generateBuiltinInputCode,
        "EXPRESSION_BUILTIN_OPEN_P2": generateBuiltinOpenCode,
        "EXPRESSION_BUILTIN_OPEN_P3": generateBuiltinOpenCode,
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
        "EXPRESSION_BUILTIN_MAKE_EXCEPTION_MODULE_NOT_FOUND_ERROR": generateBuiltinMakeExceptionCode,
        "EXPRESSION_BUILTIN_MAKE_EXCEPTION_ATTRIBUTE_ERROR": generateBuiltinMakeExceptionCode,
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
        "EXPRESSION_CONSTANT_NONE_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_TRUE_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_FALSE_REF": generateConstantReferenceCode,
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
        "EXPRESSION_CONSTANT_ELLIPSIS_REF": generateConstantReferenceCode,
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
        "EXPRESSION_CONSTANT_TYPE_DICT_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_TYPE_SET_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_TYPE_FROZENSET_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_TYPE_LIST_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_TYPE_TUPLE_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_TYPE_TYPE_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_BYTEARRAY_REF": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_GENERIC_ALIAS": generateConstantGenericAliasCode,
        "EXPRESSION_CONSTANT_UNION_TYPE": generateConstantReferenceCode,
        "EXPRESSION_CONSTANT_SYS_VERSION_INFO_REF": generateConstantSysVersionInfoCode,
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
        "EXPRESSION_COMPARISON_LT": generateRichComparisonExpressionCode,
        "EXPRESSION_COMPARISON_LTE": generateRichComparisonExpressionCode,
        "EXPRESSION_COMPARISON_GT": generateRichComparisonExpressionCode,
        "EXPRESSION_COMPARISON_GTE": generateRichComparisonExpressionCode,
        "EXPRESSION_COMPARISON_EQ": generateRichComparisonExpressionCode,
        "EXPRESSION_COMPARISON_NEQ": generateRichComparisonExpressionCode,
        "EXPRESSION_DICT_OPERATION_ITEM": generateDictOperationItemCode,
        "EXPRESSION_DICT_OPERATION_GET2": generateDictOperationGet2Code,
        "EXPRESSION_DICT_OPERATION_GET3": generateDictOperationGet3Code,
        "EXPRESSION_DICT_OPERATION_HASKEY": generateDictOperationInCode,
        "EXPRESSION_DICT_OPERATION_IN": generateDictOperationInCode,
        "EXPRESSION_DICT_OPERATION_NOT_IN": generateDictOperationInCode,
        "EXPRESSION_DICT_OPERATION_COPY": generateDictOperationCopyCode,
        "EXPRESSION_DICT_OPERATION_CLEAR": generateDictOperationClearCode,
        "EXPRESSION_DICT_OPERATION_ITEMS": generateDictOperationItemsCode,
        "EXPRESSION_DICT_OPERATION_ITERITEMS": generateDictOperationIteritemsCode,
        "EXPRESSION_DICT_OPERATION_VIEWITEMS": generateDictOperationViewitemsCode,
        "EXPRESSION_DICT_OPERATION_KEYS": generateDictOperationKeysCode,
        "EXPRESSION_DICT_OPERATION_ITERKEYS": generateDictOperationIterkeysCode,
        "EXPRESSION_DICT_OPERATION_VIEWKEYS": generateDictOperationViewkeysCode,
        "EXPRESSION_DICT_OPERATION_VALUES": generateDictOperationValuesCode,
        "EXPRESSION_DICT_OPERATION_ITERVALUES": generateDictOperationItervaluesCode,
        "EXPRESSION_DICT_OPERATION_VIEWVALUES": generateDictOperationViewvaluesCode,
        "EXPRESSION_DICT_OPERATION_SETDEFAULT2": generateDictOperationSetdefault2Code,
        "EXPRESSION_DICT_OPERATION_SETDEFAULT3": generateDictOperationSetdefault3Code,
        "EXPRESSION_DICT_OPERATION_POP2": generateDictOperationPop2Code,
        "EXPRESSION_DICT_OPERATION_POP3": generateDictOperationPop3Code,
        "EXPRESSION_DICT_OPERATION_POPITEM": generateDictOperationPopitemCode,
        "EXPRESSION_DICT_OPERATION_UPDATE2": generateDictOperationUpdate2Code,
        "EXPRESSION_DICT_OPERATION_UPDATE3": generateDictOperationUpdate3Code,
        "EXPRESSION_DICT_OPERATION_UPDATE_PAIRS": generateDictOperationUpdate3Code,
        "EXPRESSION_DICT_OPERATION_FROMKEYS2": generateDictOperationFromkeys2Code,
        "EXPRESSION_DICT_OPERATION_FROMKEYS3": generateDictOperationFromkeys3Code,
        "EXPRESSION_FUNCTION_CREATION": generateFunctionCreationCode,
        "EXPRESSION_FUNCTION_CREATION_OLD": generateFunctionCreationCode,
        "EXPRESSION_FUNCTION_CALL": generateFunctionCallCode,
        "EXPRESSION_FUNCTION_ERROR_STR": generateFunctionErrorStrCode,
        "EXPRESSION_IMPORT_MODULE_BUILTIN": generateImportModuleFixedCode,
        "EXPRESSION_IMPORT_MODULE_FIXED": generateImportModuleFixedCode,
        "EXPRESSION_IMPORT_MODULE_HARD": generateImportModuleHardCode,
        "EXPRESSION_IMPORT_MODULE_NAME_HARD_MAYBE_EXISTS": generateImportModuleNameHardCode,
        "EXPRESSION_IMPORT_MODULE_NAME_HARD_EXISTS": generateImportModuleNameHardCode,
        "EXPRESSION_BUILTIN_PATCHABLE_TYPE_REF": generateImportModuleNameHardCode,
        "EXPRESSION_IMPORTLIB_IMPORT_MODULE_REF": generateImportModuleNameHardCode,
        "EXPRESSION_IMPORTLIB_IMPORT_MODULE_CALL": generateImportlibImportCallCode,
        "EXPRESSION_IMPORT_NAME": generateImportNameCode,
        "EXPRESSION_LIST_OPERATION_APPEND": generateListOperationAppendCode2,
        "EXPRESSION_LIST_OPERATION_EXTEND": generateListOperationExtendCode,
        "EXPRESSION_LIST_OPERATION_EXTEND_FOR_UNPACK": generateListOperationExtendCode,
        "EXPRESSION_LIST_OPERATION_CLEAR": generateListOperationClearCode,
        "EXPRESSION_LIST_OPERATION_COPY": generateListOperationCopyCode,
        "EXPRESSION_LIST_OPERATION_COUNT": generateListOperationCountCode,
        "EXPRESSION_LIST_OPERATION_INSERT": generateListOperationInsertCode,
        "EXPRESSION_LIST_OPERATION_INDEX2": generateListOperationIndex2Code,
        "EXPRESSION_LIST_OPERATION_INDEX3": generateListOperationIndex3Code,
        "EXPRESSION_LIST_OPERATION_INDEX4": generateListOperationIndex4Code,
        "EXPRESSION_LIST_OPERATION_POP1": generateListOperationPop1Code,
        "EXPRESSION_LIST_OPERATION_POP2": generateListOperationPop2Code,
        "EXPRESSION_LIST_OPERATION_REMOVE": generateListOperationRemoveCode,
        "EXPRESSION_LIST_OPERATION_REVERSE": generateListOperationReverseCode,
        "EXPRESSION_LIST_OPERATION_SORT1": generateListOperationSort1Code,
        "EXPRESSION_LIST_OPERATION_SORT2": generateListOperationSort2Code,
        "EXPRESSION_LIST_OPERATION_SORT3": generateListOperationSort3Code,
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
        "EXPRESSION_OPERATION_UNARY_REPR": generateOperationUnaryCode,
        "EXPRESSION_OPERATION_UNARY_SUB": generateOperationUnaryCode,
        "EXPRESSION_OPERATION_UNARY_ADD": generateOperationUnaryCode,
        "EXPRESSION_OPERATION_UNARY_INVERT": generateOperationUnaryCode,
        "EXPRESSION_OPERATION_UNARY_ABS": generateBuiltinAbsCode,
        "EXPRESSION_OPERATION_NOT": generateOperationNotCode,
        "EXPRESSION_OUTLINE_BODY": generateFunctionOutlineCode,
        "EXPRESSION_OUTLINE_FUNCTION": generateFunctionOutlineCode,
        "EXPRESSION_CLASS_MAPPING_BODY": generateFunctionOutlineCode,
        "EXPRESSION_CLASS_DICT_BODY": generateFunctionOutlineCode,
        "EXPRESSION_CLASS_DICT_BODY_P2": generateFunctionOutlineCode,
        "EXPRESSION_SUBSCRIPT_LOOKUP": generateSubscriptLookupCode,
        "EXPRESSION_SUBSCRIPT_LOOKUP_FOR_UNPACK": generateSubscriptLookupCode,
        "EXPRESSION_SLICE_LOOKUP": generateSliceLookupCode,
        "EXPRESSION_SET_OPERATION_UPDATE": generateSetOperationUpdateCode,
        "EXPRESSION_SIDE_EFFECTS": generateSideEffectsCode,
        "EXPRESSION_SPECIAL_UNPACK": generateSpecialUnpackCode,
        "EXPRESSION_TEMP_VARIABLE_REF": generateVariableReferenceCode,
        "EXPRESSION_VARIABLE_REF": generateVariableReferenceCode,
        "EXPRESSION_VARIABLE_OR_BUILTIN_REF": generateVariableReferenceCode,
        "EXPRESSION_YIELD": generateYieldCode,
        "EXPRESSION_YIELD_FROM": generateYieldFromCode,
        "EXPRESSION_YIELD_FROM_AWAITABLE": generateYieldFromAwaitableCode,
        "EXPRESSION_ASYNC_WAIT": generateAsyncWaitCode,
        "EXPRESSION_ASYNC_WAIT_ENTER": generateAsyncWaitCode,
        "EXPRESSION_ASYNC_WAIT_EXIT": generateAsyncWaitCode,
        "EXPRESSION_ASYNC_ITER": generateAsyncIterCode,
        "EXPRESSION_ASYNC_NEXT": generateAsyncNextCode,
        "EXPRESSION_SELECT_METACLASS": generateSelectMetaclassCode,
        "EXPRESSION_STRING_CONCATENATION": generateStringConcatenationCode,
        "EXPRESSION_BUILTIN_FORMAT": generateBuiltinFormatCode,
        "EXPRESSION_BUILTIN_ASCII": generateBuiltinAsciiCode,
        "EXPRESSION_LOCALS_VARIABLE_CHECK": generateLocalsDictVariableCheckCode,
        "EXPRESSION_LOCALS_VARIABLE_REF_OR_FALLBACK": generateLocalsDictVariableRefOrFallbackCode,
        "EXPRESSION_LOCALS_VARIABLE_REF": generateLocalsDictVariableRefCode,
        "EXPRESSION_RAISE_EXCEPTION": generateRaiseExpressionCode,
        "EXPRESSION_PKGUTIL_GET_DATA_REF": generateImportModuleNameHardCode,
        "EXPRESSION_PKG_RESOURCES_REQUIRE_REF": generateImportModuleNameHardCode,
        "EXPRESSION_PKG_RESOURCES_GET_DISTRIBUTION_REF": generateImportModuleNameHardCode,
        "EXPRESSION_PKG_RESOURCES_ITER_ENTRY_POINTS_REF": generateImportModuleNameHardCode,
        "EXPRESSION_PKG_RESOURCES_RESOURCE_STRING_REF": generateImportModuleNameHardCode,
        "EXPRESSION_PKG_RESOURCES_RESOURCE_STREAM_REF": generateImportModuleNameHardCode,
        "EXPRESSION_PKG_RESOURCES_DISTRIBUTION_VALUE_REF": generatePkgResourcesDistributionValueCode,
        "EXPRESSION_PKG_RESOURCES_ENTRY_POINT_VALUE_REF": generatePkgResourcesEntryPointValueCode,
        "EXPRESSION_IMPORTLIB_RESOURCES_READ_BINARY_REF": generateImportModuleNameHardCode,
        "EXPRESSION_IMPORTLIB_RESOURCES_READ_TEXT_REF": generateImportModuleNameHardCode,
        "EXPRESSION_IMPORTLIB_RESOURCES_FILES_REF": generateImportModuleNameHardCode,
        "EXPRESSION_IMPORTLIB_RESOURCES_BACKPORT_FILES_REF": generateImportModuleNameHardCode,
        "EXPRESSION_IMPORTLIB_METADATA_VERSION_REF": generateImportModuleNameHardCode,
        "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_VERSION_REF": generateImportModuleNameHardCode,
        "EXPRESSION_IMPORTLIB_METADATA_DISTRIBUTION_REF": generateImportModuleNameHardCode,
        "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_DISTRIBUTION_REF": generateImportModuleNameHardCode,
        "EXPRESSION_IMPORTLIB_METADATA_ENTRY_POINTS_REF": generateImportModuleNameHardCode,
        "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_ENTRY_POINTS_REF": generateImportModuleNameHardCode,
        "EXPRESSION_IMPORTLIB_METADATA_METADATA_REF": generateImportModuleNameHardCode,
        "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_METADATA_REF": generateImportModuleNameHardCode,
        "EXPRESSION_IMPORTLIB_METADATA_DISTRIBUTION_VALUE_REF": generateImportlibMetadataDistributionValueCode,
        "EXPRESSION_IMPORTLIB_METADATA_ENTRY_POINT_VALUE_REF": generateImportlibMetadataEntryPointValueCode,
        "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_ENTRY_POINT_VALUE_REF": generateImportlibMetadataBackportEntryPointValueCode,
        "EXPRESSION_IMPORTLIB_METADATA_SELECTABLE_GROUPS_VALUE_REF": generateImportlibMetadataSelectableGroupsValueCode,
        "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_SELECTABLE_GROUPS_VALUE_REF": generateImportlibMetadataBackportSelectableGroupsValueCode,
        "EXPRESSION_IMPORTLIB_METADATA_ENTRY_POINTS_VALUE_REF": generateImportlibMetadataEntryPointsValueCode,
        "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_ENTRY_POINTS_VALUE_REF": generateImportlibMetadataBackportEntryPointsValueCode,
        "EXPRESSION_IMPORTLIB_METADATA_ENTRY_POINTS_BEFORE310_CALL": generateImportlibMetadataEntryPointsSince310CallCode,
        "EXPRESSION_IMPORTLIB_METADATA_ENTRY_POINTS_SINCE310_CALL": generateImportlibMetadataEntryPointsSince310CallCode,
        "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_ENTRY_POINTS_CALL": generateImportlibMetadataBackportEntryPointsCallCode,
        "EXPRESSION_SYS_EXIT_REF": generateImportModuleNameHardCode,
        "EXPRESSION_OS_UNAME_REF": generateImportModuleNameHardCode,
        "EXPRESSION_OS_LISTDIR_REF": generateImportModuleNameHardCode,
        "EXPRESSION_OS_STAT_REF": generateImportModuleNameHardCode,
        "EXPRESSION_OS_LSTAT_REF": generateImportModuleNameHardCode,
        "EXPRESSION_OS_PATH_EXISTS_REF": generateImportModuleNameHardCode,
        "EXPRESSION_OS_PATH_ISFILE_REF": generateImportModuleNameHardCode,
        "EXPRESSION_OS_PATH_ISDIR_REF": generateImportModuleNameHardCode,
        "EXPRESSION_OS_PATH_DIRNAME_REF": generateImportModuleNameHardCode,
        "EXPRESSION_OS_PATH_BASENAME_REF": generateImportModuleNameHardCode,
        "EXPRESSION_OS_PATH_ABSPATH_REF": generateImportModuleNameHardCode,
        "EXPRESSION_OS_PATH_NORMPATH_REF": generateImportModuleNameHardCode,
        "EXPRESSION_BUILTINS_OPEN_REF": generateImportModuleNameHardCode,
        "EXPRESSION_CTYPES_CDLL_REF": generateImportModuleNameHardCode,
        "EXPRESSION_CTYPES_CDLL_SINCE38_CALL": generateCtypesCdllCallCode,
        "EXPRESSION_CTYPES_CDLL_BEFORE38_CALL": generateCtypesCdllCallCode,
        "EXPRESSION_PKGUTIL_GET_DATA_CALL": generatePkglibGetDataCallCode,
        "EXPRESSION_PKG_RESOURCES_REQUIRE_CALL": generatePkgResourcesRequireCallCode,
        "EXPRESSION_PKG_RESOURCES_GET_DISTRIBUTION_CALL": generatePkgResourcesGetDistributionCallCode,
        "EXPRESSION_PKG_RESOURCES_ITER_ENTRY_POINTS_CALL": generatePkgResourcesIterEntryPointsCallCode,
        "EXPRESSION_PKG_RESOURCES_RESOURCE_STRING_CALL": generatePkgResourcesResourceStringCallCode,
        "EXPRESSION_PKG_RESOURCES_RESOURCE_STREAM_CALL": generatePkgResourcesResourceStreamCallCode,
        "EXPRESSION_IMPORTLIB_RESOURCES_READ_BINARY_CALL": generateImportlibResourcesReadBinaryCallCode,
        "EXPRESSION_IMPORTLIB_RESOURCES_READ_TEXT_BEFORE_313_CALL": generateImportlibResourcesReadTextCallCode,
        "EXPRESSION_IMPORTLIB_RESOURCES_READ_TEXT_SINCE_313_CALL": generateImportlibResourcesReadTextCallCode,
        "EXPRESSION_IMPORTLIB_RESOURCES_FILES_CALL": generateImportlibResourcesFilesCallCode,
        "EXPRESSION_IMPORTLIB_RESOURCES_BACKPORT_FILES_CALL": generateImportlibResourcesFilesCallCode,
        "EXPRESSION_IMPORTLIB_RESOURCES_FILES_CALL_FIXED": generateImportlibResourcesFilesCallCode,
        "EXPRESSION_IMPORTLIB_RESOURCES_BACKPORT_FILES_CALL_FIXED": generateImportlibResourcesFilesCallCode,
        "EXPRESSION_IMPORTLIB_METADATA_VERSION_CALL": generateImportlibMetadataVersionCallCode,
        "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_VERSION_CALL": generateImportlibMetadataBackportVersionCallCode,
        "EXPRESSION_IMPORTLIB_METADATA_DISTRIBUTION_CALL": generateImportlibMetadataDistributionCallCode,
        "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_DISTRIBUTION_CALL": generateImportlibMetadataDistributionCallCode,
        "EXPRESSION_IMPORTLIB_METADATA_DISTRIBUTION_FAILED_CALL": generateImportlibMetadataDistributionCallCode,
        "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_DISTRIBUTION_FAILED_CALL": generateImportlibMetadataDistributionCallCode,
        "EXPRESSION_OS_UNAME_CALL": generateOsUnameCallCode,
        "EXPRESSION_OS_PATH_EXISTS_CALL": generateOsPathExistsCallCode,
        "EXPRESSION_OS_PATH_ISFILE_CALL": generateOsPathIsfileCallCode,
        "EXPRESSION_OS_PATH_ISDIR_CALL": generateOsPathIsdirCallCode,
        "EXPRESSION_OS_PATH_BASENAME_CALL": generateOsPathBasenameCallCode,
        "EXPRESSION_OS_PATH_DIRNAME_CALL": generateOsPathDirnameCallCode,
        "EXPRESSION_OS_PATH_ABSPATH_CALL": generateOsPathAbspathCallCode,
        "EXPRESSION_OS_PATH_NORMPATH_CALL": generateOsPathNormpathCallCode,
        "EXPRESSION_OS_PATH_ISABS_CALL": generateOsPathIsabsCallCode,
        "EXPRESSION_OS_LISTDIR_CALL": generateOsListdirCallCode,
        "EXPRESSION_OS_STAT_CALL": generateOsStatCallCode,
        "EXPRESSION_OS_LSTAT_CALL": generateOsLstatCallCode,
        "EXPRESSION_TYPE_ALIAS": generateTypeAliasCode,
        "EXPRESSION_TYPE_VARIABLE": generateTypeVarCode,
        "EXPRESSION_TYPE_MAKE_GENERIC": generateTypeGenericCode,
        "EXPRESSION_STR_OPERATION_FORMAT": generateStrFormatMethodCode,
        # TODO: Should have all of these generically or not. This one is required for now.
        "EXPRESSION_DICT_OPERATION_FROMKEYS_REF": generateDictOperationFromkeysRefCode,
        "EXPRESSION_TYPE_OPERATION_PREPARE": generateTypeOperationPrepareCode,
        # PyPI module "tensorflow" specific stuff
        "EXPRESSION_TENSORFLOW_FUNCTION_REF": generateImportModuleNameHardCode,
        "EXPRESSION_TENSORFLOW_FUNCTION_CALL": generateTensorflowFunctionCallCode,
        # PyPI module "networkx" specific stuff
        "EXPRESSION_NETWORKX_UTILS_DECORATORS_ARGMAP_REF": generateImportModuleNameHardCode,
        "EXPRESSION_NETWORKX_UTILS_DECORATORS_ARGMAP_CALL": generateNetworkxUtilsDecoratorsArgmapCallCode,
    }
)

# Add code generation for the EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_* variety
addExpressionDispatchDict(
    dict((cls.kind, generateAttributeLookupCode) for cls in attribute_classes.values())
)

# Add code generation for the EXPRESSION_ATTRIBUTE_LOOKUP_DICT|LIST|STR_* variety
addExpressionDispatchDict(
    dict((cls.kind, generateAttributeLookupCode) for cls in attribute_typed_classes)
)

# Add code generation for the EXPRESSION_STR_OPERATION_* nodes.
addExpressionDispatchDict(
    dict((cls.kind, generateStrOperationCode) for cls in getStrOperationClasses())
)

# Add code generation for the EXPRESSION_BYTES_OPERATION_* nodes.
addExpressionDispatchDict(
    dict((cls.kind, generateBytesOperationCode) for cls in getBytesOperationClasses())
)


setStatementDispatchDict(
    {
        "STATEMENT_ASSIGNMENT_VARIABLE_GENERIC": generateAssignmentVariableCode,
        "STATEMENT_ASSIGNMENT_VARIABLE_CONSTANT_MUTABLE": generateAssignmentVariableCode,
        "STATEMENT_ASSIGNMENT_VARIABLE_CONSTANT_MUTABLE_TRUSTED": generateAssignmentVariableCode,
        "STATEMENT_ASSIGNMENT_VARIABLE_CONSTANT_IMMUTABLE": generateAssignmentVariableCode,
        "STATEMENT_ASSIGNMENT_VARIABLE_CONSTANT_IMMUTABLE_TRUSTED": generateAssignmentVariableCode,
        "STATEMENT_ASSIGNMENT_VARIABLE_ITERATOR": generateAssignmentVariableCode,
        "STATEMENT_ASSIGNMENT_VARIABLE_FROM_VARIABLE": generateAssignmentVariableCode,
        "STATEMENT_ASSIGNMENT_VARIABLE_FROM_TEMP_VARIABLE": generateAssignmentVariableCode,
        "STATEMENT_ASSIGNMENT_VARIABLE_HARD_VALUE": generateAssignmentVariableCode,
        "STATEMENT_ASSIGNMENT_ATTRIBUTE": generateAssignmentAttributeCode,
        "STATEMENT_ASSIGNMENT_SUBSCRIPT": generateAssignmentSubscriptCode,
        "STATEMENT_ASSIGNMENT_SLICE": generateAssignmentSliceCode,
        "STATEMENT_DEL_VARIABLE_TOLERANT": generateDelVariableCode,
        "STATEMENT_DEL_VARIABLE_INTOLERANT": generateDelVariableCode,
        "STATEMENT_DEL_ATTRIBUTE": generateDelAttributeCode,
        "STATEMENT_DEL_SUBSCRIPT": generateDelSubscriptCode,
        "STATEMENT_DEL_SLICE": generateDelSliceCode,
        "STATEMENT_DICT_OPERATION_REMOVE": generateDictOperationRemoveCode,
        "STATEMENT_DICT_OPERATION_UPDATE": generateDictOperationUpdateCode,
        "STATEMENT_RELEASE_VARIABLE_TEMP": generateVariableReleaseCode,
        "STATEMENT_RELEASE_VARIABLE_LOCAL": generateVariableReleaseCode,
        "STATEMENT_RELEASE_VARIABLE_PARAMETER": generateVariableReleaseCode,
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
        "STATEMENT_RERAISE_EXCEPTION": generateReraiseCode,
        "STATEMENT_SPECIAL_UNPACK_CHECK": generateUnpackCheckCode,
        "STATEMENT_SPECIAL_UNPACK_CHECK_FROM_ITERATED": generateUnpackCheckFromIteratedCode,
        "STATEMENT_EXEC": generateExecCode,
        "STATEMENT_LOCALS_DICT_SYNC": generateLocalsDictSyncCode,
        "STATEMENT_SET_LOCALS": generateSetLocalsMappingCode,
        "STATEMENT_SET_LOCALS_DICTIONARY": generateSetLocalsDictCode,
        "STATEMENT_RELEASE_LOCALS": generateReleaseLocalsDictCode,
        "STATEMENT_PRESERVE_FRAME_EXCEPTION": generateFramePreserveExceptionCode,
        "STATEMENT_RESTORE_FRAME_EXCEPTION": generateFrameRestoreExceptionCode,
        "STATEMENT_PUBLISH_EXCEPTION": generateExceptionPublishCode,
        "STATEMENT_INJECT_C_CODE": generateInjectCCode,
    }
)

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
