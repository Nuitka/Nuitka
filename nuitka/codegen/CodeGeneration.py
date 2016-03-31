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
""" The code generation.

No language specifics at all are supposed to be present here. Instead it is
using primitives from the given generator to build code sequences (list of
strings).

As such this is the place that knows how to take a condition and two code
branches and make a code block out of it. But it doesn't contain any target
language syntax.
"""

from nuitka import Options
from nuitka.__past__ import iterItems
from nuitka.PythonVersions import python_version

from . import Contexts, Emission, Helpers
from .AttributeCodes import (
    generateAssignmentAttributeCode,
    generateAttributeLookupCode,
    generateAttributeLookupSpecialCode,
    generateBuiltinGetattrCode,
    generateBuiltinHasattrCode,
    generateBuiltinSetattrCode,
    generateDelAttributeCode
)
from .BranchCodes import generateBranchCode
from .BuiltinCodes import (
    generateBuiltinAnonymousRefCode,
    generateBuiltinBinCode,
    generateBuiltinBoolCode,
    generateBuiltinBytearrayCode,
    generateBuiltinComplexCode,
    generateBuiltinFloatCode,
    generateBuiltinHexCode,
    generateBuiltinOctCode,
    generateBuiltinOpenCode,
    generateBuiltinRange1Code,
    generateBuiltinRange2Code,
    generateBuiltinRange3Code,
    generateBuiltinRefCode,
    generateBuiltinType1Code,
    generateBuiltinType3Code,
    generateBuiltinXrangeCode
)
from .CallCodes import generateCallCode, getCallsCode, getCallsDecls
from .ClassCodes import (
    generateBuiltinIsinstanceCode,
    generateBuiltinSuperCode,
    generateSelectMetaclassCode
)
from .ComparisonCodes import generateComparisonExpressionCode
from .ConditionalCodes import (
    generateConditionalAndOrCode,
    generateConditionalCode
)
from .ConstantCodes import generateConstantReferenceCode
from .CoroutineCodes import (
    generateAsyncIterCode,
    generateAsyncNextCode,
    generateAsyncWaitCode,
    generateMakeCoroutineObjectCode,
    getCoroutineObjectCode
)
from .DictCodes import (
    generateBuiltinDictCode,
    generateDictionaryCreationCode,
    generateDictOperationGetCode,
    generateDictOperationInCode,
    generateDictOperationRemoveCode,
    generateDictOperationSetCode,
    generateDictOperationUpdateCode
)
from .EvalCodes import (
    generateBuiltinCompileCode,
    generateEvalCode,
    generateExecCode,
    generateExecfileCode,
    generateLocalsDictSyncCode
)
from .ExceptionCodes import (
    generateBuiltinMakeExceptionCode,
    generateExceptionCaughtTracebackCode,
    generateExceptionCaughtTypeCode,
    generateExceptionCaughtValueCode,
    generateExceptionPublishCode,
    generateExceptionRefCode
)
from .ExpressionCodes import (
    generateExpressionOnlyCode,
    generateSideEffectsCode
)
from .FrameCodes import (
    generateFramePreserveExceptionCode,
    generateFrameRestoreExceptionCode,
    generateStatementsFrameCode
)
from .FunctionCodes import (
    generateFunctionCallCode,
    generateFunctionCreationCode,
    generateFunctionDeclCode,
    generateFunctionOutlineCode,
    getExportScopeCode,
    getFunctionCode,
    getFunctionDirectDecl
)
from .GeneratorCodes import (
    generateGeneratorEntryCode,
    generateMakeGeneratorObjectCode,
    getGeneratorObjectCode
)
from .GlobalsLocalsCodes import (
    generateBuiltinDir1Code,
    generateBuiltinGlobalsCode,
    generateBuiltinLocalsCode,
    generateBuiltinVarsCode,
    generateSetLocalsCode
)
from .Helpers import generateStatementCode
from .IdCodes import generateBuiltinHashCode, generateBuiltinIdCode
from .ImportCodes import (
    generateBuiltinImportCode,
    generateImportModuleCode,
    generateImportModuleHardCode,
    generateImportNameCode,
    generateImportStarCode
)
from .IntegerCodes import generateBuiltinIntCode, generateBuiltinLongCode
from .IteratorCodes import (
    generateBuiltinIter1Code,
    generateBuiltinIter2Code,
    generateBuiltinLenCode,
    generateBuiltinNext1Code,
    generateBuiltinNext2Code,
    generateSpecialUnpackCode,
    generateUnpackCheckCode
)
from .LabelCodes import getStatementTrace
from .ListCodes import (
    generateBuiltinListCode,
    generateListCreationCode,
    generateListOperationAppendCode,
    generateListOperationExtendCode,
    generateListOperationPopCode
)
from .LoaderCodes import getMetapathLoaderBodyCode
from .LoopCodes import (
    generateLoopBreakCode,
    generateLoopCode,
    generateLoopContinueCode
)
from .ModuleCodes import (
    generateModuleFileAttributeCode,
    getModuleCode,
    getModuleValues
)
from .OperationCodes import (
    generateOperationBinaryCode,
    generateOperationUnaryCode
)
from .PrintCodes import generatePrintNewlineCode, generatePrintValueCode
from .RaisingCodes import generateRaiseCode
from .ReturnCodes import (
    generateGeneratorReturnCode,
    generateReturnCode,
    generateReturnedValueRefCode
)
from .SetCodes import (
    generateBuiltinSetCode,
    generateSetCreationCode,
    generateSetOperationAddCode,
    generateSetOperationUpdateCode
)
from .SliceCodes import (
    generateAssignmentSliceCode,
    generateBuiltinSliceCode,
    generateDelSliceCode,
    generateSliceLookupCode
)
from .StringCodes import (
    generateBuiltinChrCode,
    generateBuiltinOrdCode,
    generateBuiltinStrCode,
    generateBuiltinUnicodeCode
)
from .SubscriptCodes import (
    generateAssignmentSubscriptCode,
    generateDelSubscriptCode,
    generateSubscriptLookupCode
)
from .TryCodes import generateTryCode
from .TupleCodes import generateBuiltinTupleCode, generateTupleCreationCode
from .VariableCodes import (
    generateAssignmentVariableCode,
    generateDelVariableCode,
    generateVariableReferenceCode,
    generateVariableReleaseCode
)
from .YieldCodes import generateYieldCode, generateYieldFromCode

_generated_functions = {}


def generateFunctionBodyCode(function_body, context):
    function_identifier = function_body.getCodeName()

    if function_identifier in _generated_functions:
        return _generated_functions[function_identifier]

    # TODO: Generate both codes, and base direct/etc. decisions on context.

    if function_body.isExpressionGeneratorObjectBody():
        function_context = Contexts.PythonGeneratorObjectContext(
            parent   = context,
            function = function_body
        )
    elif function_body.isExpressionCoroutineObjectBody():
        function_context = Contexts.PythonCoroutineObjectContext(
            parent   = context,
            function = function_body
        )
    elif function_body.isExpressionClassBody():
        function_context = Contexts.PythonFunctionDirectContext(
            parent   = context,
            function = function_body
        )
    elif function_body.needsCreation():
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

    needs_exception_exit = function_body.mayRaiseException(BaseException)

    if function_body.isExpressionGeneratorObjectBody():
        function_code = getGeneratorObjectCode(
            context                = function_context,
            function_identifier    = function_identifier,
            user_variables         = function_body.getUserLocalVariables(),
            temp_variables         = function_body.getTempVariables(),
            function_codes         = function_codes.codes,
            needs_exception_exit   = needs_exception_exit,
            needs_generator_return = function_body.needsGeneratorReturnExit()
        )
    elif function_body.isExpressionCoroutineObjectBody():
        function_code = getCoroutineObjectCode(
            context                = function_context,
            function_identifier    = function_identifier,
            user_variables         = function_body.getUserLocalVariables(),
            temp_variables         = function_body.getTempVariables(),
            function_codes         = function_codes.codes,
            needs_exception_exit   = needs_exception_exit,
            needs_generator_return = function_body.needsGeneratorReturnExit()
        )
    elif function_body.isExpressionClassBody():
        function_code = getFunctionCode(
            context              = function_context,
            function_identifier  = function_identifier,
            parameters           = None,
            closure_variables    = function_body.getClosureVariables(),
            user_variables       = function_body.getUserLocalVariables(),
            temp_variables       = function_body.getTempVariables(),
            function_codes       = function_codes.codes,
            function_doc         = function_body.getDoc(),
            needs_exception_exit = needs_exception_exit,
            file_scope           = getExportScopeCode(
                cross_module = False
            )
        )
    else:
        parameters = function_body.getParameters()

        function_code = getFunctionCode(
            context              = function_context,
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


def _generateStatementSequenceCode(statement_sequence, emit, context):
    if statement_sequence is None:
        return

    for statement in statement_sequence.getStatements():
        if Options.shallTraceExecution():
            source_ref = statement.getSourceReference()

            statement_repr = repr(statement)
            source_repr = source_ref.getAsString()

            if python_version >= 300:
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

        function_decl = generateFunctionDeclCode(
            function_body = function_body
        )

        if function_decl is not None:
            function_decl_codes.append(function_decl)


    for function_body in module.getCrossUsedFunctions():
        assert function_body.isCrossModuleUsed()

        function_decl = getFunctionDirectDecl(
            function_identifier = function_body.getCodeName(),
            closure_variables   = function_body.getClosureVariables(),
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

    if python_version >= 330:
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


Helpers.setExpressionDispatchDict(
    {
        "EXPRESSION_ATTRIBUTE_LOOKUP"               : generateAttributeLookupCode,
        "EXPRESSION_ATTRIBUTE_LOOKUP_SPECIAL"       : generateAttributeLookupSpecialCode,
        "EXPRESSION_BUILTIN_SLICE"                  : generateBuiltinSliceCode,
        "EXPRESSION_BUILTIN_HASH"                   : generateBuiltinHashCode,
        "EXPRESSION_BUILTIN_ID"                     : generateBuiltinIdCode,
        "EXPRESSION_BUILTIN_COMPILE"                : generateBuiltinCompileCode,
        "EXPRESSION_BUILTIN_EXECFILE"               : generateExecfileCode,
        "EXPRESSION_BUILTIN_EVAL"                   : generateEvalCode,
        "EXPRESSION_BUILTIN_EXEC"                   : generateEvalCode,
        "EXPRESSION_BUILTIN_ITER1"                  : generateBuiltinIter1Code,
        "EXPRESSION_BUILTIN_ITER2"                  : generateBuiltinIter2Code,
        "EXPRESSION_BUILTIN_NEXT1"                  : generateBuiltinNext1Code,
        "EXPRESSION_BUILTIN_NEXT2"                  : generateBuiltinNext2Code,
        "EXPRESSION_BUILTIN_TYPE1"                  : generateBuiltinType1Code,
        "EXPRESSION_BUILTIN_TYPE3"                  : generateBuiltinType3Code,
        "EXPRESSION_BUILTIN_IMPORT"                 : generateBuiltinImportCode,
        "EXPRESSION_BUILTIN_BOOL"                   : generateBuiltinBoolCode,
        "EXPRESSION_BUILTIN_BYTEARRAY"              : generateBuiltinBytearrayCode,
        "EXPRESSION_BUILTIN_INT"                    : generateBuiltinIntCode,
        "EXPRESSION_BUILTIN_LONG"                   : generateBuiltinLongCode,
        "EXPRESSION_BUILTIN_FLOAT"                  : generateBuiltinFloatCode,
        "EXPRESSION_BUILTIN_COMPLEX"                : generateBuiltinComplexCode,
        "EXPRESSION_BUILTIN_LEN"                    : generateBuiltinLenCode,
        "EXPRESSION_BUILTIN_STR"                    : generateBuiltinStrCode,
        "EXPRESSION_BUILTIN_UNICODE"                : generateBuiltinUnicodeCode,
        "EXPRESSION_BUILTIN_CHR"                    : generateBuiltinChrCode,
        "EXPRESSION_BUILTIN_ORD"                    : generateBuiltinOrdCode,
        "EXPRESSION_BUILTIN_BIN"                    : generateBuiltinBinCode,
        "EXPRESSION_BUILTIN_OCT"                    : generateBuiltinOctCode,
        "EXPRESSION_BUILTIN_HEX"                    : generateBuiltinHexCode,
        "EXPRESSION_BUILTIN_TUPLE"                  : generateBuiltinTupleCode,
        "EXPRESSION_BUILTIN_LIST"                   : generateBuiltinListCode,
        "EXPRESSION_BUILTIN_SET"                    : generateBuiltinSetCode,
        "EXPRESSION_BUILTIN_DICT"                   : generateBuiltinDictCode,
        "EXPRESSION_BUILTIN_LOCALS"                 : generateBuiltinLocalsCode,
        "EXPRESSION_BUILTIN_GLOBALS"                : generateBuiltinGlobalsCode,
        "EXPRESSION_BUILTIN_SUPER"                  : generateBuiltinSuperCode,
        "EXPRESSION_BUILTIN_ISINSTANCE"             : generateBuiltinIsinstanceCode,
        "EXPRESSION_BUILTIN_DIR1"                   : generateBuiltinDir1Code,
        "EXPRESSION_BUILTIN_VARS"                   : generateBuiltinVarsCode,
        "EXPRESSION_BUILTIN_HASATTR"                : generateBuiltinHasattrCode,
        "EXPRESSION_BUILTIN_GETATTR"                : generateBuiltinGetattrCode,
        "EXPRESSION_BUILTIN_SETATTR"                : generateBuiltinSetattrCode,
        "EXPRESSION_BUILTIN_OPEN"                   : generateBuiltinOpenCode,
        "EXPRESSION_BUILTIN_RANGE1"                 : generateBuiltinRange1Code,
        "EXPRESSION_BUILTIN_RANGE2"                 : generateBuiltinRange2Code,
        "EXPRESSION_BUILTIN_RANGE3"                 : generateBuiltinRange3Code,
        "EXPRESSION_BUILTIN_XRANGE"                 : generateBuiltinXrangeCode,
        "EXPRESSION_BUILTIN_MAKE_EXCEPTION"         : generateBuiltinMakeExceptionCode,
        "EXPRESSION_BUILTIN_REF"                    : generateBuiltinRefCode,
        "EXPRESSION_BUILTIN_EXCEPTION_REF"          : generateExceptionRefCode,
        "EXPRESSION_BUILTIN_ANONYMOUS_REF"          : generateBuiltinAnonymousRefCode,
        "EXPRESSION_CAUGHT_EXCEPTION_TYPE_REF"      : generateExceptionCaughtTypeCode,
        "EXPRESSION_CAUGHT_EXCEPTION_VALUE_REF"     : generateExceptionCaughtValueCode,
        "EXPRESSION_CAUGHT_EXCEPTION_TRACEBACK_REF" : generateExceptionCaughtTracebackCode,
        "EXPRESSION_CALL_EMPTY"                     : generateCallCode,
        "EXPRESSION_CALL_KEYWORDS_ONLY"             : generateCallCode,
        "EXPRESSION_CALL_NO_KEYWORDS"               : generateCallCode,
        "EXPRESSION_CALL"                           : generateCallCode,
        "EXPRESSION_CONSTANT_REF"                   : generateConstantReferenceCode,
        "EXPRESSION_CONDITIONAL"                    : generateConditionalCode,
        "EXPRESSION_CONDITIONAL_OR"                 : generateConditionalAndOrCode,
        "EXPRESSION_CONDITIONAL_AND"                : generateConditionalAndOrCode,
        "EXPRESSION_COMPARISON"                     : generateComparisonExpressionCode,
        "EXPRESSION_COMPARISON_IS"                  : generateComparisonExpressionCode,
        "EXPRESSION_COMPARISON_IS_NOT"              : generateComparisonExpressionCode,
        "EXPRESSION_COMPARISON_IN"                  : generateComparisonExpressionCode,
        "EXPRESSION_COMPARISON_NOT_IN"              : generateComparisonExpressionCode,
        "EXPRESSION_COMPARISON_EXCEPTION_MATCH"     : generateComparisonExpressionCode,
        "EXPRESSION_DICT_OPERATION_GET"             : generateDictOperationGetCode,
        "EXPRESSION_DICT_OPERATION_IN"              : generateDictOperationInCode,
        "EXPRESSION_DICT_OPERATION_NOT_IN"          : generateDictOperationInCode,
        "EXPRESSION_FUNCTION_CREATION"              : generateFunctionCreationCode,
        "EXPRESSION_FUNCTION_CALL"                  : generateFunctionCallCode,
        "EXPRESSION_IMPORT_MODULE"                  : generateImportModuleCode,
        "EXPRESSION_IMPORT_MODULE_HARD"             : generateImportModuleHardCode,
        "EXPRESSION_IMPORT_NAME"                    : generateImportNameCode,
        "EXPRESSION_LIST_OPERATION_EXTEND"          : generateListOperationExtendCode,
        "EXPRESSION_LIST_OPERATION_POP"             : generateListOperationPopCode,
        "EXPRESSION_MODULE_FILE_ATTRIBUTE_REF"      : generateModuleFileAttributeCode,
        "EXPRESSION_MAKE_GENERATOR_OBJECT"          : generateMakeGeneratorObjectCode,
        "EXPRESSION_MAKE_COROUTINE_OBJECT"          : generateMakeCoroutineObjectCode,
        "EXPRESSION_MAKE_SET"                       : generateSetCreationCode,
        "EXPRESSION_MAKE_TUPLE"                     : generateTupleCreationCode,
        "EXPRESSION_MAKE_LIST"                      : generateListCreationCode,
        "EXPRESSION_MAKE_DICT"                      : generateDictionaryCreationCode,
        "EXPRESSION_OPERATION_BINARY"               : generateOperationBinaryCode,
        "EXPRESSION_OPERATION_BINARY_INPLACE"       : generateOperationBinaryCode,
        "EXPRESSION_OPERATION_UNARY"                : generateOperationUnaryCode,
        "EXPRESSION_OPERATION_NOT"                  : generateOperationUnaryCode,
        "EXPRESSION_OUTLINE_BODY"                   : generateFunctionOutlineCode,
        "EXPRESSION_RETURNED_VALUE_REF"             : generateReturnedValueRefCode,
        "EXPRESSION_SUBSCRIPT_LOOKUP"               : generateSubscriptLookupCode,
        "EXPRESSION_SLICE_LOOKUP"                   : generateSliceLookupCode,
        "EXPRESSION_SET_OPERATION_UPDATE"           : generateSetOperationUpdateCode,
        "EXPRESSION_SIDE_EFFECTS"                   : generateSideEffectsCode,
        "EXPRESSION_SPECIAL_UNPACK"                 : generateSpecialUnpackCode,
        "EXPRESSION_TEMP_VARIABLE_REF"              : generateVariableReferenceCode,
        "EXPRESSION_VARIABLE_REF"                   : generateVariableReferenceCode,
        "EXPRESSION_YIELD"                          : generateYieldCode,
        "EXPRESSION_YIELD_FROM"                     : generateYieldFromCode,
        "EXPRESSION_SELECT_METACLASS"               : generateSelectMetaclassCode,
        "EXPRESSION_ASYNC_WAIT"                     : generateAsyncWaitCode,
        "EXPRESSION_ASYNC_ITER"                     : generateAsyncIterCode,
        "EXPRESSION_ASYNC_NEXT"                     : generateAsyncNextCode,
    }
)

Helpers.setStatementDispatchDict(
    {
        "STATEMENT_ASSIGNMENT_VARIABLE"      : generateAssignmentVariableCode,
        "STATEMENT_ASSIGNMENT_ATTRIBUTE"     : generateAssignmentAttributeCode,
        "STATEMENT_ASSIGNMENT_SUBSCRIPT"     : generateAssignmentSubscriptCode,
        "STATEMENT_ASSIGNMENT_SLICE"         : generateAssignmentSliceCode,
        "STATEMENT_DEL_VARIABLE"             : generateDelVariableCode,
        "STATEMENT_DEL_ATTRIBUTE"            : generateDelAttributeCode,
        "STATEMENT_DEL_SUBSCRIPT"            : generateDelSubscriptCode,
        "STATEMENT_DEL_SLICE"                : generateDelSliceCode,
        "STATEMENT_DICT_OPERATION_REMOVE"    : generateDictOperationRemoveCode,
        "STATEMENT_DICT_OPERATION_UPDATE"    : generateDictOperationUpdateCode,
        "STATEMENT_RELEASE_VARIABLE"         : generateVariableReleaseCode,
        "STATEMENT_EXPRESSION_ONLY"          : generateExpressionOnlyCode,
        "STATEMENT_RETURN"                   : generateReturnCode,
        "STATEMENT_GENERATOR_RETURN"         : generateGeneratorReturnCode,
        "STATEMENT_CONDITIONAL"              : generateBranchCode,
        "STATEMENT_TRY"                      : generateTryCode,
        "STATEMENT_PRINT_VALUE"              : generatePrintValueCode,
        "STATEMENT_PRINT_NEWLINE"            : generatePrintNewlineCode,
        "STATEMENT_IMPORT_STAR"              : generateImportStarCode,
        "STATEMENT_LIST_OPERATION_APPEND"    : generateListOperationAppendCode,
        "STATEMENT_SET_OPERATION_ADD"        : generateSetOperationAddCode,
        "STATEMENT_DICT_OPERATION_SET"       : generateDictOperationSetCode,
        "STATEMENT_LOOP"                     : generateLoopCode,
        "STATEMENT_LOOP_BREAK"               : generateLoopBreakCode,
        "STATEMENT_LOOP_CONTINUE"            : generateLoopContinueCode,
        "STATEMENT_RAISE_EXCEPTION"          : generateRaiseCode,
        "STATEMENT_RAISE_EXCEPTION_IMPLICIT" : generateRaiseCode,
        "STATEMENT_SPECIAL_UNPACK_CHECK"     : generateUnpackCheckCode,
        "STATEMENT_EXEC"                     : generateExecCode,
        "STATEMENT_LOCALS_DICT_SYNC"         : generateLocalsDictSyncCode,
        "STATEMENT_SET_LOCALS"               : generateSetLocalsCode,
        "STATEMENT_GENERATOR_ENTRY"          : generateGeneratorEntryCode,
        "STATEMENT_PRESERVE_FRAME_EXCEPTION" : generateFramePreserveExceptionCode,
        "STATEMENT_RESTORE_FRAME_EXCEPTION"  : generateFrameRestoreExceptionCode,
        "STATEMENT_PUBLISH_EXCEPTION"        : generateExceptionPublishCode
    }
)
