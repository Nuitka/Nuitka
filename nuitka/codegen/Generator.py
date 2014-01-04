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
""" Generator for C++ and Python C/API.

This is the actual C++ code generator. It has methods and should be the only
place to know what C++ is like. Ideally it would be possible to replace the
target language by changing this one and the templates, and otherwise nothing
else.

"""

from .Identifiers import (
    defaultToNullIdentifier,
    defaultToNoneIdentifier,
    KeeperAccessIdentifier,
    HelperCallIdentifier,
    EmptyDictIdentifier,
    ThrowingIdentifier,
    CallIdentifier,
    Identifier
)

from .Indentation import (
    getBlockCode,
    indented
)

# imported from here pylint: disable=W0611
from .OrderedEvaluation import (
    getOrderRelevanceEnforcedCallCode,
    getOrderRelevanceEnforcedArgsCode,
    _getAssignmentTempKeeperCode,
    pickFirst
)

from .LineNumberCodes import (
    mergeLineNumberBranches,
    pushLineNumberBranch,
    popLineNumberBranch,
    getLineNumberCode,
    resetLineNumber
)

from .TupleCodes import (
    getTupleCreationCode,
    getMakeTuplesCode
)
from .ListCodes import (
    getListCreationCode,
    getMakeListsCode
)
from .DictCodes import (
    getDictionaryCreationCode,
    getMakeDictsCode
)
from .SetCodes import (
    getSetCreationCode,
    getMakeSetsCode
)

from .CallCodes import (
    getCallCodePosKeywordArgs,
    getCallCodePosArgsQuick,
    getCallCodeKeywordArgs,
    getCallCodePosArgs,
    getCallCodeNoArgs,
    getCallsDecls,
    getCallsCode
)

from .ConstantCodes import (
    getConstantsInitCode,
    getConstantsDeclCode,
    getConstantAccess,
    getConstantHandle,
    getConstantCode,
    needsPickleInit,
    stream_data
)

from .FunctionCodes import (
    getFunctionContextDefinitionCode,
    getDirectionFunctionCallCode,
    getGeneratorFunctionCode,
    getFunctionCreationCode,
    getFunctionDirectDecl,
    getFunctionMakerCode,
    getFunctionMakerDecl,
    getFunctionCode,
)

from .ModuleCodes import (
    getModuleMetapathLoaderEntryCode,
    getModuleDeclarationCode,
    getModuleAccessCode,
    getModuleIdentifier,
    getModuleCode
)

from .MainCodes import getMainCode

# imported from here pylint: enable=W0611

# These are here to be imported from here
# pylint: disable=W0611
from .VariableCodes import (
    getVariableAssignmentCode,
    getLocalVariableInitCode,
    getVariableDelCode,
    getVariableHandle,
    getVariableCode
)
# pylint: enable=W0611

from .CodeObjectCodes import (
    getCodeObjectsDeclCode,
    getCodeObjectsInitCode,
)

from . import (
    CodeTemplates,
    OperatorCodes,
    CppStrings
)

from nuitka import (
    Constants,
    Builtins,
    Options,
    Utils
)

def getReturnCode(identifier, via_exception, context):
    if via_exception:
        if identifier is None:
            identifier = getConstantHandle(
                context  = context,
                constant = None
            )

        return "throw ReturnValueException( %s );" % (
            identifier.getCodeExportRef()
        )
    else:
        if identifier is not None:
            return "return %s;" % identifier.getCodeExportRef()
        else:
            return "return;"

def getYieldCode(identifier, in_handler):
    if in_handler:
        return Identifier(
            "YIELD_IN_HANDLER( generator, %s )" % (
                identifier.getCodeExportRef(),
            ),
            0
        )
    else:
        return Identifier(
            "YIELD( generator, %s )" % identifier.getCodeExportRef(),
            0
        )

def getYieldFromCode(identifier, in_handler):
    # TODO: Clarify, if the difference as in getYieldCode is needed.
    if False and in_handler:
        return Identifier(
            "YIELD_FROM_IN_HANDLER( generator, %s )" % (
                identifier.getCodeTemporaryRef(),
            ),
            1
        )
    else:
        return Identifier(
            "YIELD_FROM( generator, %s )" % identifier.getCodeTemporaryRef(),
            1
        )

def getMetaclassVariableCode(context):
    assert Utils.python_version < 300

    return "GET_STRING_DICT_VALUE( moduledict_%s, (Nuitka_StringObject *)%s )" % (
        context.getModuleCodeName(),
        getConstantCode(
            constant = "__metaclass__",
            context  = context
        )
    )

def getBuiltinImportCode( context, order_relevance, module_identifier,
                          globals_dict, locals_dict, import_list, level ):
    assert type( module_identifier ) is not str
    assert type( globals_dict ) is not str
    assert type( locals_dict ) is not str

    return getOrderRelevanceEnforcedArgsCode(
        helper          = "IMPORT_MODULE",
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "import",
        order_relevance = order_relevance,
        args            = (
            module_identifier,
            globals_dict,
            locals_dict,
            import_list,
            level
        ),
        context         = context
    )

def getImportFromStarCode(context, module_identifier):
    if not context.hasLocalsDict():
        return "IMPORT_MODULE_STAR( %s, true, %s );" % (
            getModuleAccessCode(
                context = context
            ),
            module_identifier.getCodeTemporaryRef()
        )
    else:
        return "IMPORT_MODULE_STAR( locals_dict.asObject0(), false, %s );" % (
            module_identifier.getCodeTemporaryRef()
        )


def getMaxIndexCode():
    return Identifier( "PY_SSIZE_T_MAX", 0 )

def getMinIndexCode():
    return Identifier( "0", 0 )

def getIndexValueCode(number):
    return Identifier( "%s" % number, 0 )

def getIndexCode(identifier):
    return Identifier(
        "CONVERT_TO_INDEX( %s )" % identifier.getCodeTemporaryRef(),
        0
    )


def getUnpackNextCode(iterator_identifier, count):
    return Identifier(
        "UNPACK_NEXT( %s, %d )" % (
            iterator_identifier.getCodeTemporaryRef(),
            count - 1
        ),
        1
    )

def getUnpackCheckCode(iterator_identifier, count):
    return "UNPACK_ITERATOR_CHECK( %s, %d );" % (
        iterator_identifier.getCodeTemporaryRef(),
        count
    )

def getSpecialAttributeLookupCode(attribute, source):
    assert attribute.getConstant not in ( "__dict__", "__class__" )

    return Identifier(
        "LOOKUP_SPECIAL( %s, %s )" % (
            source.getCodeTemporaryRef(),
            attribute.getCodeTemporaryRef()
        ),
        1
    )

def getAttributeLookupCode(attribute, source):
    assert attribute.getConstant not in ( "__dict__", "__class__" )

    return Identifier(
        "LOOKUP_ATTRIBUTE( %s, %s )" % (
            source.getCodeTemporaryRef(),
            attribute.getCodeTemporaryRef()
        ),
        1
    )


def getAttributeLookupDictSlotCode(source):
    return Identifier(
        "LOOKUP_ATTRIBUTE_DICT_SLOT( %s )" % (
            source.getCodeTemporaryRef(),
        ),
        1
    )

def getAttributeLookupClassSlotCode(source):
    return Identifier(
        "LOOKUP_ATTRIBUTE_CLASS_SLOT( %s )" % (
            source.getCodeTemporaryRef(),
        ),
        1
    )

def getAttributeCheckCode(context, order_relevance, attribute, source):
    return getBoolFromCode(
        code = getAttributeCheckBoolCode(
            order_relevance = order_relevance,
            source          = source,
            attribute       = attribute,
            context         = context
        )
    )

def getAttributeCheckBoolCode(context, order_relevance, source, attribute):
    return getOrderRelevanceEnforcedArgsCode(
        helper          = "HAS_ATTRIBUTE",
        export_ref      = 0,
        ref_count       = None,
        tmp_scope       = "hasattr",
        order_relevance = order_relevance,
        args            = ( source, attribute ),
        context         = context
    )

def getAttributeGetCode(context, order_relevance, source, attribute, default):
    return getOrderRelevanceEnforcedArgsCode(
        helper          = "BUILTIN_GETATTR",
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "getattr",
        order_relevance = order_relevance,
        args            = (
            source,
            attribute,
            defaultToNullIdentifier(default)
        ),
        context         = context
    )

def getAttributeSetCode(context, order_relevance, attribute, source, value):
    result = getOrderRelevanceEnforcedArgsCode(
        helper          = "BUILTIN_SETATTR",
        export_ref      = 0,
        ref_count       = None,
        tmp_scope       = "setattr",
        order_relevance = order_relevance,
        args            = (
            source,
            attribute,
            value
        ),
        context         = context
    )

    # It's a void function "BUILTIN_SETATTR", but "setattr" returns "None".
    return Identifier(
        "( %s, Py_None )" % result,
        0
    )

def getImportNameCode(import_name, module):
    return Identifier(
        "IMPORT_NAME( %s, %s )" % (
            module.getCodeTemporaryRef(),
            import_name.getCodeTemporaryRef()
        ),
        1
    )

def getSubscriptLookupCode(context, order_relevance, subscript, source):
    helper = "LOOKUP_SUBSCRIPT"
    suffix_args = []

    if subscript.isConstantIdentifier():
        constant = subscript.getConstant()

        if Constants.isIndexConstant( constant ):
            constant_value = int( constant )

            if abs( constant_value ) < 2**31:
                helper = "LOOKUP_SUBSCRIPT_CONST"
                suffix_args = [ "%d" % constant ]

    return getOrderRelevanceEnforcedArgsCode(
        helper          = helper,
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "subscr",
        order_relevance = order_relevance,
        args            = ( source, subscript ),
        suffix_args     = suffix_args,
        context         = context
    )


def getHasKeyBoolCode(source, key):
    return "HAS_KEY( %s, %s )" % (
        source.getCodeTemporaryRef(),
        key.getCodeTemporaryRef()
    )

def getSliceLookupCode(order_relevance, source, lower, upper, context):
    return getOrderRelevanceEnforcedArgsCode(
        helper          = "LOOKUP_SLICE",
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "slice",
        order_relevance = order_relevance,
        args            = (
            source,
            defaultToNoneIdentifier(lower),
            defaultToNoneIdentifier(upper)
        ),
        context         = context
    )

def getSliceLookupIndexesCode(lower, upper, source):
    return Identifier(
        "LOOKUP_INDEX_SLICE( %s, %s, %s )" % (
            source.getCodeTemporaryRef(),
            lower.getCodeTemporaryRef(),
            upper.getCodeTemporaryRef()
        ),
        1
    )

def getSliceObjectCode(order_relevance, lower, upper, step, context):
    return getOrderRelevanceEnforcedArgsCode(
        helper          = "MAKE_SLICEOBJ",
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "sliceobj",
        order_relevance = order_relevance,
        args            = (
            defaultToNoneIdentifier(lower),
            defaultToNoneIdentifier(upper),
            defaultToNoneIdentifier(step)
        ),
        context         = context
    )

def getStatementCode(identifier):
    return identifier.getCodeDropRef() + ";"

def getOperationCode(context, order_relevance, operator, identifiers):
    # This needs to have one return per operation of Python, and there are many
    # of these, pylint: disable=R0911

    prefix_args = []
    ref_count = 1

    if operator == "Pow":
        helper = "POWER_OPERATION"
    elif operator == "IPow":
        helper = "POWER_OPERATION_INPLACE"
    elif operator == "Add":
        helper = "BINARY_OPERATION_ADD"
    elif operator == "Sub":
        helper = "BINARY_OPERATION_SUB"
    elif operator == "Div":
        helper = "BINARY_OPERATION_DIV"
    elif operator == "Mult":
        helper = "BINARY_OPERATION_MUL"
    elif operator == "Mod":
        helper = "BINARY_OPERATION_REMAINDER"
    elif len( identifiers ) == 2:
        helper = "BINARY_OPERATION"
        prefix_args = [ OperatorCodes.binary_operator_codes[ operator ] ]
    elif len( identifiers ) == 1:
        impl_helper, ref_count = OperatorCodes.unary_operator_codes[ operator ]
        helper = "UNARY_OPERATION"
        prefix_args = [ impl_helper ]
    else:
        assert False, (operator, identifiers)

    return getOrderRelevanceEnforcedArgsCode(
        helper          = helper,
        export_ref      = 0,
        ref_count       = ref_count,
        tmp_scope       = "op",
        order_relevance = order_relevance,
        prefix_args     = prefix_args,
        args            = identifiers,
        context         = context
    )

def getPrintCode(newline, identifiers, target_file):
    print_elements_code = []

    for identifier in identifiers:
        print_elements_code.append(
            CodeTemplates.template_print_value % {
                "print_value" : identifier.getCodeTemporaryRef(),
                "target_file" : "target_file"
                                  if target_file is not None
                                else "NULL"
            }
        )

    if newline:
        print_elements_code.append(
            CodeTemplates.template_print_newline  % {
                "target_file" : "target_file"
                                  if target_file is not None
                                else "NULL"
            }
        )

    if target_file is not None:
        return CodeTemplates.template_print_statement % {
            "target_file"         : defaultToNullIdentifier(
                target_file
            ).getCodeExportRef(),
            "print_elements_code" : indented( print_elements_code )
        }
    else:
        return "\n".join( print_elements_code )


def getConditionalExpressionCode( condition_code, identifier_no,
                                  identifier_yes ):
    if identifier_yes.getCheapRefCount() == identifier_no.getCheapRefCount():
        if identifier_yes.getCheapRefCount() == 0:
            codes_yes = identifier_yes.getCodeTemporaryRef()
            codes_no  = identifier_no.getCodeTemporaryRef()
            ref_count = 0
        else:
            codes_yes = identifier_yes.getCodeExportRef()
            codes_no  = identifier_no.getCodeExportRef()
            ref_count = 1
    else:
        codes_yes = identifier_yes.getCodeExportRef()
        codes_no  = identifier_no.getCodeExportRef()
        ref_count = 1

    return Identifier(
        CodeTemplates.template_conditional_expression % {
            "condition" : condition_code,
            "yes"       : codes_yes,
            "no"        : codes_no
        },
        ref_count
    )


def getBranchCode(condition_code, yes_codes, no_codes):
    assert yes_codes or no_codes

    if no_codes is None:
        return CodeTemplates.template_branch_one % {
            "condition"   : condition_code,
            "branch_code" : indented(
                yes_codes if yes_codes is not None else ""
            )
        }
    else:
        assert no_codes, no_codes

        return CodeTemplates.template_branch_two % {
            "condition"       : condition_code,
            "branch_yes_code" : indented(
                yes_codes if yes_codes is not None else ""
            ),
            "branch_no_code"  : indented( no_codes )
        }

def getLoopContinueCode(needs_exceptions):
    if needs_exceptions:
        return "throw ContinueException();"
    else:
        return "CONSIDER_THREADING(); continue;"

def getLoopBreakCode(needs_exceptions):
    if needs_exceptions:
        return "throw BreakException();"
    else:
        return "break;"

def getComparisonExpressionCode( context, comparator, order_relevance, left,
                                 right ):
    # There is an awful lot of cases, pylint: disable=R0912

    if comparator in OperatorCodes.normal_comparison_codes:
        helper = OperatorCodes.normal_comparison_codes[ comparator ]
        assert helper.startswith("SEQUENCE_CONTAINS")

        ref_count = 0
    elif comparator in OperatorCodes.rich_comparison_codes:
        helper = "RICH_COMPARE_%s" % (
            OperatorCodes.rich_comparison_codes[ comparator ]
        )
        ref_count = 1
    elif comparator == "Is":
        # This is special, and "==" enforces order of evalulation already, or so
        # we believe.
        return getBoolFromCode(
            code = "( %s == %s )" % (
                left.getCodeTemporaryRef(),
                right.getCodeTemporaryRef()
            )
        )
    elif comparator == "IsNot":
        # This is special, and "!=" enforces order of evalulation already, or so
        # we believe.
        return getBoolFromCode(
            code = "( %s != %s )" % (
                left.getCodeTemporaryRef(),
                right.getCodeTemporaryRef()
            )
        )
    else:
        assert False, comparator

    return getOrderRelevanceEnforcedArgsCode(
        helper          = helper,
        export_ref      = 0,
        ref_count       = ref_count,
        tmp_scope       = "cmp",
        order_relevance = order_relevance,
        args            = ( left, right ),
        context         = context
    )


def getComparisonExpressionBoolCode(context, comparator, order_relevance, left,
                                    right):
    # There is an awful lot of cases, pylint: disable=R0912

    if comparator in OperatorCodes.normal_comparison_codes:
        helper = "%s_BOOL" % (
            OperatorCodes.normal_comparison_codes[ comparator ]
        )
        assert helper.startswith("SEQUENCE_CONTAINS")
    elif comparator in OperatorCodes.rich_comparison_codes:
        helper = "RICH_COMPARE_BOOL_%s" % (
            OperatorCodes.rich_comparison_codes[ comparator ]
        )
    elif comparator == "Is":
        # This is special, and "==" enforces order of evalulation already, or so
        # we believe.
        return "( %s == %s )" % (
            left.getCodeTemporaryRef(),
            right.getCodeTemporaryRef()
        )
    elif comparator == "IsNot":
        # This is special, and "!=" enforces order of evalulation already, or so
        # we believe.
        return "( %s != %s )" % (
            left.getCodeTemporaryRef(),
            right.getCodeTemporaryRef()
        )
    else:
        assert False, comparator

    return getOrderRelevanceEnforcedArgsCode(
        helper          = helper,
        export_ref      = 0,
        ref_count       = None,
        tmp_scope       = "cmp",
        order_relevance = order_relevance,
        args            = ( left, right ),
        context         = context
    )

def getConditionNotBoolCode(condition):
    return "(!( %s ))" % condition

def getConditionAndCode(operands):
    return "( %s )" % " && ".join( operands )

def getConditionOrCode(operands):
    return "( %s )" % " || ".join( operands )

def getConditionSelectionCode(condition_code, yes_code, no_code):
    return "( %s ) ? ( %s ) : ( %s )" % (
        condition_code,
        yes_code,
        no_code
    )

def getConditionCheckTrueCode(condition):
    return "CHECK_IF_TRUE( %s )" % condition.getCodeTemporaryRef()

def getConditionCheckFalseCode(condition):
    return "CHECK_IF_FALSE( %s )" % condition.getCodeTemporaryRef()

def getTrueExpressionCode():
    return "true"

def getFalseExpressionCode():
    return "false"

def getAttributeAssignmentCode( order_relevance, target, attribute,
                                identifier ):
    assert attribute.getConstant not in ( "__dict__", "__class__" )

    return getOrderRelevanceEnforcedCallCode(
        order_relevance = order_relevance,
        helper          = "SET_ATTRIBUTE",
        names           = ( "identifier", "target", "attribute" ),
        values          = ( identifier, target, attribute )
    )


def getAttributeAssignmentDictSlotCode(order_relevance, target, identifier):
    """ Get code for special case target.__dict__ = value """
    return getOrderRelevanceEnforcedCallCode(
        order_relevance = order_relevance,
        helper          = "SET_ATTRIBUTE_DICT_SLOT",
        names           = ( "identifier", "target" ),
        values          = ( identifier, target )
    )


def getAttributeAssignmentClassSlotCode(order_relevance, target, identifier):
    """ Get code for special case target.__class__ = value """
    return getOrderRelevanceEnforcedCallCode(
        order_relevance = order_relevance,
        helper          = "SET_ATTRIBUTE_CLASS_SLOT",
        names           = ( "identifier", "target" ),
        values          = ( identifier, target )
    )

def getAttributeDelCode(target, attribute):
    return "DEL_ATTRIBUTE( %s, %s );" % (
        target.getCodeTemporaryRef(),
        attribute.getCodeTemporaryRef()
    )

def getSliceAssignmentIndexesCode(target, lower, upper, identifier):
    return "SET_INDEX_SLICE( %s, %s, %s, %s );" % (
        target.getCodeTemporaryRef(),
        lower.getCodeTemporaryRef(),
        upper.getCodeTemporaryRef(),
        identifier.getCodeTemporaryRef()
    )

def getSliceAssignmentCode(order_relevance, target, lower, upper, identifier):
    return getOrderRelevanceEnforcedCallCode(
        order_relevance = order_relevance,
        helper          = "SET_SLICE",
        names           = ( "identifier", "target", "lower", "upper" ),
        values          = (
            identifier,
            target,
            defaultToNoneIdentifier(lower),
            defaultToNoneIdentifier(upper)
        )
    )

def getSliceDelCode(target, lower, upper):
    return "DEL_SLICE( %s, %s, %s );" % (
        target.getCodeTemporaryRef(),
        defaultToNoneIdentifier(lower).getCodeTemporaryRef(),
        defaultToNoneIdentifier(upper).getCodeTemporaryRef()
    )

def getLoopCode( loop_body_codes, needs_break_exception,
                 needs_continue_exception ):
    if needs_break_exception and needs_continue_exception:
        while_loop_template = \
            CodeTemplates.template_loop_break_continue_catching
        indentation = 2
    elif needs_break_exception:
        while_loop_template = CodeTemplates.template_loop_break_catching
        indentation = 2
    elif needs_continue_exception:
        while_loop_template = CodeTemplates.template_loop_continue_catching
        indentation = 2
    else:
        while_loop_template = CodeTemplates.template_loop_simple
        indentation = 1

    return while_loop_template % {
        "loop_body_codes" : indented(
            loop_body_codes if loop_body_codes is not None else "",
            indentation
        ),
    }


def getAssignmentTempKeeperCode(source_identifier, variable, context):
    ref_count = source_identifier.getCheapRefCount()
    variable_name = variable.getName()

    assert not ref_count or variable.getReferenced().getNeedsFree(), \
           ( variable, variable.getReferenced().getNeedsFree(), ref_count,
             source_identifier, source_identifier.__class__ )

    return _getAssignmentTempKeeperCode(
        source_identifier = source_identifier,
        variable_name     = variable_name,
        context           = context
    )

def getTempKeeperHandle(variable, context):
    variable_name = variable.getName()
    ref_count = context.getTempKeeperRefCount( variable_name )

    if ref_count == 1:
        return KeeperAccessIdentifier(
            "%s.asObject1()" % variable_name
        )
    else:
        # TODO: Could create an identifier, where 0 is just cheap, and 1 is
        # still available, may give nicer to read code occasionally.
        return Identifier(
            "%s.asObject0()" % variable_name,
            0
        )


def getSubscriptAssignmentCode( order_relevance, subscribed, subscript,
                                identifier ):
    helper = "SET_SUBSCRIPT"
    suffix_args = []

    if subscript.isConstantIdentifier():
        constant = subscript.getConstant()

        if Constants.isIndexConstant( constant ):
            constant_value = int( constant )

            if abs( constant_value ) < 2**31:
                helper = "SET_SUBSCRIPT_CONST"
                suffix_args = [ "%d" % constant ]

    return getOrderRelevanceEnforcedCallCode(
        order_relevance = order_relevance,
        helper          = helper,
        names           = ( "identifier", "subscribed", "subscript" ),
        values          = ( identifier, subscribed, subscript ),
        suffix_args     = suffix_args
    )

def getSubscriptDelCode(order_relevance, subscribed, subscript):
    return getOrderRelevanceEnforcedCallCode(
        order_relevance = order_relevance,
        helper          = "DEL_SUBSCRIPT",
        names           = ( "subscribed", "subscript" ),
        values          = ( subscribed, subscript )
    )

def getTryFinallyCode( context, needs_continue, needs_break,
                       needs_return_value_catch, needs_return_value_reraise,
                       aborting, code_tried, code_final, try_count ):
    tb_making = getTracebackMakingIdentifier( context )

    rethrow_setups = ""
    rethrow_catchers = ""
    rethrow_raisers = ""

    values = {
        "try_count" : try_count
    }

    if needs_continue:
        rethrow_setups += CodeTemplates.try_finally_template_setup_continue % (
            values
        )
        rethrow_catchers += CodeTemplates.try_finally_template_catch_continue % values
        rethrow_raisers += CodeTemplates.try_finally_template_reraise_continue % values

    if needs_break:
        rethrow_setups += CodeTemplates.try_finally_template_setup_break  % values
        rethrow_catchers += CodeTemplates.try_finally_template_catch_break % values
        rethrow_raisers += CodeTemplates.try_finally_template_reraise_break % values

    if needs_return_value_catch:
        rethrow_setups += CodeTemplates.try_finally_template_setup_return_value % values
        rethrow_catchers += CodeTemplates.try_finally_template_catch_return_value % values

        if needs_return_value_reraise:
            rethrow_raisers += CodeTemplates.try_finally_template_reraise_return_value % values
        elif not aborting:
            if context.getFunction().isGenerator():
                rethrow_raisers += CodeTemplates.try_finally_template_indirect_generator_return_value % values
            else:
                rethrow_raisers += CodeTemplates.try_finally_template_indirect_return_value % values
        else:
            if context.getFunction().isGenerator():
                rethrow_raisers += CodeTemplates.try_finally_template_direct_generator_return_value % values
            else:
                rethrow_raisers += CodeTemplates.try_finally_template_direct_return_value % values

    result = CodeTemplates.try_finally_template % {
        "try_count"        : try_count,
        "tried_code"       : indented( code_tried ),
        "final_code"       : indented( code_final, 0 ),
        "tb_making"        : tb_making.getCodeExportRef(),
        "rethrow_setups"   : rethrow_setups,
        "rethrow_catchers" : rethrow_catchers,
        "rethrow_raisers"  : rethrow_raisers,
    }

    if not rethrow_raisers:
        result = result.rstrip()

    return result

def getTryExceptHandlerCode( exception_identifiers, handler_code,
                             needs_frame_detach, first_handler ):
    exception_code = []

    cond_keyword = "if" if first_handler else "else if"

    if exception_identifiers:
        exception_code.append(
            "%s ( %s )" % (
                cond_keyword,
                " || ".join(
                    "_exception.matches( %s )" % (
                        exception_identifier.getCodeTemporaryRef()
                    )
                    for exception_identifier in
                    exception_identifiers
                )
            )
        )
    else:
        exception_code.append(
            "%s (true)" % cond_keyword
        )

    if handler_code is None:
        handler_code = []

    if needs_frame_detach:
        handler_code.insert(
            0,
            CodeTemplates.template_setup_except_handler_detaching % {
            }
        )

    exception_code += getBlockCode(
        handler_code
    ).split( "\n" )

    return exception_code

def getTryExceptCode(context, code_tried, handler_codes):
    exception_code = list( handler_codes )
    exception_code += CodeTemplates.try_except_reraise_unmatched_template.split( "\n" )

    tb_making = getTracebackMakingIdentifier( context )

    return CodeTemplates.try_except_template % {
        "tried_code"     : indented( code_tried or "" ),
        "exception_code" : indented( exception_code ),
        "guard_class"    : context.getFrameGuardClass(),
        "tb_making"      : tb_making.getCodeExportRef(),
    }

def getTryNextExceptStopIterationIdentifier(context):
    try_count = context.allocateTryNumber()

    return Identifier( "_tmp_unpack_%d" % try_count, 1 )

def getTryNextExceptStopIterationCode( source_identifier, handler_code,
                                       assign_code, temp_identifier ):
    return CodeTemplates.template_try_next_except_stop_iteration % {
        "temp_var"          : temp_identifier.getCode(),
        "handler_code"      : indented( handler_code ),
        "assignment_code"   : assign_code,
        "source_identifier" : source_identifier.getCodeTemporaryRef()
    }


def getRaiseExceptionWithCauseCode( context, order_relevance, exception_type,
                                    exception_cause ):
    # Must enforce tb_maker to be last.
    exception_tb_maker = getTracebackMakingIdentifier(
        context = context
    )

    return getOrderRelevanceEnforcedCallCode(
        order_relevance = order_relevance + [ None ],
        helper          = "RAISE_EXCEPTION_WITH_CAUSE",
        names           = (
            "exception_type", "exception_cause", "exception_tb"
        ),
        values          = (
            exception_type, exception_cause, exception_tb_maker
        )
    )

def getRaiseExceptionWithTypeCode(context, order_relevance, exception_type):
    # Must enforce tb_maker to be last.
    exception_tb_maker = getTracebackMakingIdentifier(
        context = context
    )

    return getOrderRelevanceEnforcedCallCode(
        order_relevance = order_relevance + [ None ],
        helper          = "RAISE_EXCEPTION_WITH_TYPE",
        names           = (
            "exception_type", "exception_tb"
        ),
        values          = (
            exception_type, exception_tb_maker
        )
    )

def getRaiseExceptionWithValueCode( context, order_relevance, exception_type,
                                    exception_value, implicit ):
    # Must enforce tb_maker to be last.
    exception_tb_maker = getTracebackMakingIdentifier(
        context = context
    )

    if implicit:
        helper = "RAISE_EXCEPTION_WITH_VALUE_NO_NORMALIZE"
    else:
        helper = "RAISE_EXCEPTION_WITH_VALUE"

    return getOrderRelevanceEnforcedCallCode(
        order_relevance = order_relevance + [ None ],
        helper          = helper,
        names           = (
            "exception_type", "exception_value", "exception_tb"
        ),
        values          = (
            exception_type, exception_value, exception_tb_maker
        )
    )

def getRaiseExceptionWithTracebackCode( order_relevance, exception_type,
                                        exception_value, exception_tb ):
    return getOrderRelevanceEnforcedCallCode(
        order_relevance = order_relevance,
        helper          = "RAISE_EXCEPTION_WITH_TRACEBACK",
        names           = (
            "exception_type", "exception_value", "exception_tb"
        ),
        values          = (
            exception_type, exception_value, exception_tb
        )
    )


def getReRaiseExceptionCode(local, final):
    if local:
        thrower_code = CodeTemplates.try_except_reraise_template % {}
    else:
        thrower_code = "RERAISE_EXCEPTION();"

    if final:
        return CodeTemplates.try_except_reraise_finally_template % {
            "try_count"    : final,
            "thrower_code" : thrower_code
        }
    else:
        return thrower_code

def getRaiseExceptionExpressionCode(context, exception_type, exception_value):
    # Order is supposed to not matter, as these were run time detected and
    # contain no side effects.
    exception_tb_maker = getTracebackMakingIdentifier(
        context = context
    )

    return ThrowingIdentifier(
        "THROW_EXCEPTION( %s, %s, %s )" % (
            exception_type.getCodeExportRef(),
            exception_value.getCodeExportRef(),
            exception_tb_maker.getCodeExportRef()
        )
    )

def getSideEffectsCode(side_effects, identifier):
    assert side_effects

    side_effects_code = ", ".join(
        side_effect.getCodeTemporaryRef()
        for side_effect in
        side_effects
    )

    if identifier.getCheapRefCount() == 0:
        return Identifier(
            "( %s, %s )" % (
                side_effects_code,
                identifier.getCodeTemporaryRef()
            ),
            0
        )
    else:
        return Identifier(
            "( %s, %s )" % (
                side_effects_code,
                identifier.getCodeExportRef()
            ),
            1
        )

def getBuiltinRefCode(context, builtin_name):
    return Identifier(
        "LOOKUP_BUILTIN( %s )" % getConstantCode(
            constant = builtin_name,
            context  = context
        ),
        0
    )

def getBuiltinOriginalRefCode(builtin_name):
    return Identifier(
        "_python_original_builtin_value_%s" % builtin_name,
        0
    )

def getBuiltinAnonymousRefCode(builtin_name):
    return Identifier(
        "(PyObject *)%s" % Builtins.builtin_anon_codes[ builtin_name ],
        0
    )

def getExceptionRefCode(exception_type):
    if exception_type == "NotImplemented":
        return Identifier(
            "Py_NotImplemented",
            0
        )

    return Identifier(
        "PyExc_%s" % exception_type,
        0
    )

def getMakeBuiltinExceptionCode(context, order_relevance, exception_type,
                                exception_args):

    return getCallCodePosArgs(
        called_identifier = getExceptionRefCode( exception_type ),
        argument_tuple    = getTupleCreationCode(
            element_identifiers = exception_args,
            order_relevance     = order_relevance,
            context             = context,
        ),
        order_relevance   = ( None, None ),
        context           = context
    )

def _getLocalVariableList(provider):
    if provider.isExpressionFunctionBody():
        # Sort parameter variables of functions to the end.

        start_part = []
        end_part = []

        for variable in provider.getVariables():
            if variable.isParameterVariable():
                end_part.append( variable )
            else:
                start_part.append( variable )

        variables = start_part + end_part

        include_closure = not provider.isUnoptimized() and \
                          not provider.isClassDictCreation()
    else:
        variables = provider.getVariables()

        include_closure = True

    return [
        variable
        for variable in
        variables
        if not variable.isModuleVariable()
        if not variable.isMaybeLocalVariable()
        if ( not variable.isClosureReference() or include_closure )
    ]


def getLoadDirCode(context, provider):
    if provider.isPythonModule():
        globals_identifier = getLoadGlobalsCode(
            context = context
        )

        return Identifier(
            "PyDict_Keys( %s )" % (
                globals_identifier.getCodeTemporaryRef(),
            ),
            1
        )
    else:
        if context.hasLocalsDict():
            locals_identifier = getLoadLocalsCode(
                context  = context,
                provider = provider,
                mode     = "updated"
            )

            return Identifier(
                "PyDict_Keys( %s )" % (
                    locals_identifier.getCodeTemporaryRef()
                ),
                1
            )
        else:
            local_list = _getLocalVariableList(
                provider = provider
            )

            result = getListCreationCode(
                context             = context,
                order_relevance     = (),
                element_identifiers = (),
            )

            for local_var in local_list:
                if local_var.isTempVariableReference():
                    result = Identifier(
                        "%s.updateLocalsDir( %s, %s )" % (
                            getVariableCode(
                                context  = context,
                                variable = local_var
                            ),
                            getConstantCode(
                                constant = local_var.getReferenced().getName(),
                                context  = context
                            ),
                            result.getCodeTemporaryRef()
                        ),
                        0
                    )
                else:
                    result = Identifier(
                        "%s.updateLocalsDir( %s )" % (
                            getVariableCode(
                                context  = context,
                                variable = local_var
                            ),
                            result.getCodeTemporaryRef()
                        ),
                        0
                    )

            return result

def getLoadVarsCode(identifier):
    return Identifier(
        "LOOKUP_VARS( %s )" % identifier.getCodeTemporaryRef(),
        1
    )

def getLoadGlobalsCode(context):
    return Identifier(
        "((PyModuleObject *)%(module_identifier)s)->md_dict" % {
            "module_identifier" : getModuleAccessCode( context )
        },
        0
    )

def getLoadLocalsCode(context, provider, mode):

    def _getUpdateLocalsDictCode(context, result, local_var, ref_count):
        if local_var.isTempVariableReference():
            result = Identifier(
                "%s.updateLocalsDict( %s, %s )" % (
                    getVariableCode(
                        context  = context,
                        variable = local_var
                    ),
                    getConstantCode(
                        constant = local_var.getReferenced().getName(),
                        context  = context
                    ),
                    result.getCodeExportRef() if ref_count else result.getCodeTemporaryRef()
                ),
                ref_count
            )
        else:
            result = Identifier(
                "%s.updateLocalsDict( %s )" % (
                    getVariableCode(
                        context  = context,
                        variable = local_var
                    ),
                    result.getCodeExportRef() if ref_count else result.getCodeTemporaryRef()
                ),
                ref_count
            )

        return result

    if provider.isPythonModule():
        return getLoadGlobalsCode( context )
    elif not context.hasLocalsDict():
        local_list = _getLocalVariableList(
            provider = provider,
        )

        result = EmptyDictIdentifier()

        for local_var in local_list:
            result = _getUpdateLocalsDictCode(
                local_var = local_var,
                result    = result,
                context   = context,
                ref_count = result.getRefCount()
            )

        return result
    else:
        if mode == "copy":
            return Identifier(
                "PyDict_Copy( locals_dict.asObject0() )",
                1
            )
        elif mode == "updated":
            local_list = _getLocalVariableList(
                provider = provider
            )

            result = Identifier(
                "locals_dict.asObject0()",
                0
            )

            for local_var in local_list:
                result = _getUpdateLocalsDictCode(
                    local_var = local_var,
                    result    = result,
                    context   = context,
                    ref_count = result.getRefCount()
                )

            return result
        else:
            assert False

def getSetLocalsCode(new_locals_identifier):
    return "locals_dict.assign1( %s );" % (
        new_locals_identifier.getCodeExportRef()
    )

def getStoreLocalsCode(context, source_identifier, provider):
    assert not provider.isPythonModule()

    code = ""

    for variable in provider.getVariables():
        if not variable.isModuleVariable() and \
           not variable.isMaybeLocalVariable():
            key_identifier = getConstantHandle(
                context  = context,
                constant = variable.getName()
            )

            var_assign_code = getVariableAssignmentCode(
                context    = context,
                variable   = variable,
                identifier = getSubscriptLookupCode(
                    order_relevance = ( None, None ),
                    subscript       = key_identifier,
                    source          = source_identifier,
                    context         = context
                )
            )

            # This ought to re-use the condition code stuff.
            code += "if ( %s )\n" % getHasKeyBoolCode(
                source = source_identifier,
                key    = key_identifier
            )

            code += getBlockCode( var_assign_code ) + "\n"

    return code.rstrip( "\n" )

def getFutureFlagsCode(future_spec):
    flags = future_spec.asFlags()

    if flags:
        return " | ".join( flags )
    else:
        return 0

def getCompileCode(context, order_relevance, source_identifier,
                   filename_identifier, mode_identifier, future_flags):
    return getOrderRelevanceEnforcedArgsCode(
        helper          = "COMPILE_CODE",
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "compile",
        order_relevance = order_relevance,
        args            = (
            source_identifier,
            filename_identifier,
            mode_identifier,
            future_flags
        ),
        context         = context
    )


def getEvalCode(context, order_relevance, exec_code, filename_identifier,
                globals_identifier, locals_identifier, mode_identifier,
                future_flags):
    code_identifier = getCompileCode(
        order_relevance     = [ None ] * 4, # TODO: Probably wrong.
        source_identifier   = exec_code,
        filename_identifier = filename_identifier,
        mode_identifier     = mode_identifier,
        future_flags        = Identifier( str( future_flags ), 0 ),
        context             = context
    )

    return getOrderRelevanceEnforcedArgsCode(
        helper          = "EVAL_CODE",
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "eval",
        order_relevance = order_relevance,
        args            = (
            code_identifier,
            globals_identifier,
            locals_identifier
        ),
        context         = context
    )



def getExecCode(context, exec_code, globals_identifier, locals_identifier, future_flags, provider, source_ref):

    # Filename with origin if improved mode.
    if Options.isFullCompat():
        filename_identifier = getConstantCode(
            constant = "<string>",
            context  = context
        )
    else:
        filename_identifier = getConstantCode(
            constant = "<string at %s>" % source_ref.getAsString(),
            context  = context
        )

    result = CodeTemplates.exec_template % {
        "globals_identifier"      : globals_identifier.getCodeExportRef(),
        "locals_identifier"       : locals_identifier.getCodeExportRef(),
        "source_identifier"       : exec_code.getCodeTemporaryRef(),
        "filename_identifier"     : filename_identifier,
        "mode_identifier"         : getConstantCode(
            constant = "exec",
            context  = context
        ),
        "future_flags"            : future_flags,
    }

    if provider.isExpressionFunctionBody() and provider.isUnqualifiedExec():
        locals_temp_identifier = Identifier( "locals_source", 0 )

        result += CodeTemplates.exec_copy_back_template % {
            "store_locals_code"       : indented(
                getStoreLocalsCode(
                    context           = context,
                    source_identifier = locals_temp_identifier,
                    provider          = provider
                ),
            )
        }

    return getBlockCode( result )

def getBuiltinSuperCode( order_relevance, type_identifier, object_identifier,
                         context ):
    return getOrderRelevanceEnforcedArgsCode(
        helper          = "BUILTIN_SUPER",
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "super",
        order_relevance = order_relevance,
        args            = (
            defaultToNullIdentifier(type_identifier),
            defaultToNullIdentifier(object_identifier)
        ),
        context         = context
    )


def getBuiltinIsinstanceCode( context, order_relevance, inst_identifier,
                              cls_identifier ):
    return getBoolFromCode(
        code = getBuiltinIsinstanceBoolCode(
            order_relevance = order_relevance,
            inst_identifier = inst_identifier,
            cls_identifier  = cls_identifier,
            context         = context
        )
    )

def getBuiltinIsinstanceBoolCode( context, order_relevance, inst_identifier,
                                  cls_identifier ):
    return getOrderRelevanceEnforcedArgsCode(
        helper          = "BUILTIN_ISINSTANCE_BOOL",
        export_ref      = 0,
        ref_count       = None,
        tmp_scope       = "isinstance",
        order_relevance = order_relevance,
        args            = (
            inst_identifier,
            cls_identifier
        ),
        context         = context
    )

def getBuiltinOpenCode(context, order_relevance, filename, mode, buffering):
    return getOrderRelevanceEnforcedArgsCode(
        helper          = "OPEN_FILE",
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "open",
        order_relevance = order_relevance,
        args            = (
            defaultToNullIdentifier(filename),
            defaultToNullIdentifier(mode),
            defaultToNullIdentifier(buffering)
        ),
        context         = context
    )

def getBuiltinLenCode(identifier):
    return HelperCallIdentifier(
        "BUILTIN_LEN", identifier
    )

def getBuiltinDir1Code(identifier):
    return HelperCallIdentifier(
        "BUILTIN_DIR1", identifier
    )

def getBuiltinRange1Code(value):
    return HelperCallIdentifier(
        "BUILTIN_RANGE", value
    )

def getBuiltinRange2Code(order_relevance, low, high, context):
    return getOrderRelevanceEnforcedArgsCode(
        helper          = "BUILTIN_RANGE2",
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "range",
        order_relevance = order_relevance,
        args            = (
            low,
            high
        ),
        context         = context
    )

def getBuiltinRange3Code(order_relevance, low, high, step, context):
    return getOrderRelevanceEnforcedArgsCode(
        helper          = "BUILTIN_RANGE3",
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "range",
        order_relevance = order_relevance,
        args            = (
            low,
            high,
            step
        ),
        context         = context
    )

def getBuiltinXrangeCode(order_relevance, low, high, step, context):
    return getOrderRelevanceEnforcedArgsCode(
        helper          = "BUILTIN_XRANGE",
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "xrange",
        order_relevance = order_relevance,
        args            = (
            low,
            defaultToNullIdentifier(high),
            defaultToNullIdentifier(step)
        ),
        context         = context
    )


def getBuiltinChrCode(value):
    return HelperCallIdentifier( "BUILTIN_CHR", value )

def getBuiltinOrdCode(value):
    return HelperCallIdentifier( "BUILTIN_ORD", value )

def getBuiltinBinCode(value):
    return HelperCallIdentifier( "BUILTIN_BIN", value )

def getBuiltinOctCode(value):
    return HelperCallIdentifier( "BUILTIN_OCT", value )

def getBuiltinHexCode(value):
    return HelperCallIdentifier( "BUILTIN_HEX", value )

def getBuiltinType1Code(value):
    return HelperCallIdentifier( "BUILTIN_TYPE1", value )

def getBuiltinIter1Code(value):
    return HelperCallIdentifier( "MAKE_ITERATOR", value )

def getBuiltinIter2Code( context, order_relevance, callable_identifier,
                         sentinel_identifier ):
    return getOrderRelevanceEnforcedArgsCode(
        helper          = "BUILTIN_ITER2",
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "iter",
        order_relevance = order_relevance,
        args            = (
            callable_identifier,
            sentinel_identifier
        ),
        context         = context
    )

def getBuiltinNext1Code(value):
    return HelperCallIdentifier( "BUILTIN_NEXT1", value )

def getBuiltinNext2Code( context, order_relevance, iterator_identifier,
                         default_identifier ):
    return getOrderRelevanceEnforcedArgsCode(
        helper          = "BUILTIN_NEXT2",
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "next",
        order_relevance = order_relevance,
        args            = (
            iterator_identifier,
            default_identifier
        ),
        context         = context
    )

def getBuiltinType3Code( context, order_relevance, name_identifier,
                         bases_identifier, dict_identifier ):
    return getOrderRelevanceEnforcedArgsCode(
        helper          = "BUILTIN_TYPE3",
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "type3",
        order_relevance = order_relevance,
        prefix_args     = (
            getConstantCode(
                constant = context.getModuleName(),
                context  = context
            ),
        ),
        args            = (
            name_identifier,
            bases_identifier,
            dict_identifier
        ),
        context         = context
    )

def getBuiltinTupleCode(identifier):
    return HelperCallIdentifier( "TO_TUPLE", identifier )

def getBuiltinListCode(identifier):
    return HelperCallIdentifier( "TO_LIST", identifier )

def getBuiltinSetCode(identifier):
    return HelperCallIdentifier( "TO_SET", identifier )

def getBuiltinDictCode(seq_identifier, dict_identifier):
    if dict_identifier.isConstantIdentifier() and dict_identifier.getConstant() == {}:
        dict_identifier = None

    assert seq_identifier is not None or dict_identifier is not None

    if seq_identifier is not None:
        return Identifier(
            "TO_DICT( %s, %s )" % (
                seq_identifier.getCodeTemporaryRef(),
                defaultToNullIdentifier(dict_identifier).getCodeTemporaryRef()
            ),
            1
        )
    else:
        return dict_identifier

def getBuiltinFloatCode(identifier):
    return HelperCallIdentifier( "TO_FLOAT", identifier )

def getBuiltinLong1Code(context, identifier):
    if identifier is None:
        identifier = getConstantHandle( context = context, constant = "0" )

    return HelperCallIdentifier( "TO_LONG", identifier )

def getBuiltinLong2Code(context, order_relevance, identifier, base):
    if identifier is None:
        identifier = getConstantHandle( context = context, constant = "0" )

    return getOrderRelevanceEnforcedArgsCode(
        helper          = "TO_LONG2",
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "long",
        order_relevance = order_relevance,
        args            = (
            identifier,
            base
        ),
        context         = context
    )

def getBuiltinInt1Code(context, identifier):
    if identifier is None:
        identifier = getConstantHandle( context = context, constant = "0" )

    return HelperCallIdentifier( "TO_INT", identifier )

def getBuiltinInt2Code(context, order_relevance, identifier, base):
    if identifier is None:
        identifier = getConstantHandle( context = context, constant = "0" )

    return getOrderRelevanceEnforcedArgsCode(
        helper          = "TO_INT2",
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "int",
        order_relevance = order_relevance,
        args            = (
            identifier,
            base
        ),
        context         = context
    )

def getBuiltinStrCode(identifier):
    return HelperCallIdentifier( "TO_STR", identifier )

def getBuiltinUnicode1Code(identifier):
    return HelperCallIdentifier( "TO_UNICODE", identifier )

def getBuiltinUnicode3Code( context, order_relevance, identifier, encoding,
                            errors ):
    return getOrderRelevanceEnforcedArgsCode(
        helper          = "TO_UNICODE3",
        export_ref      = 0,
        ref_count       = 1,
        tmp_scope       = "unicode",
        order_relevance = order_relevance,
        args            = (
            identifier,
            defaultToNullIdentifier(encoding),
            defaultToNullIdentifier(errors),
        ),
        context         = context
    )

def getBoolFromCode(code):
    assert type( code ) is str

    return Identifier(
        "BOOL_FROM( %s )" % code,
        0
    )

def getBuiltinBoolCode(identifier):
    return Identifier(
        "TO_BOOL( %s )" % identifier.getCodeTemporaryRef(),
        0
    )

def getFrameMakingIdentifier(context):
    return context.getFrameHandle()

def getTracebackMakingIdentifier(context):
    return Identifier(
        "MAKE_TRACEBACK( %s )" % (
            getFrameMakingIdentifier( context = context ).getCodeExportRef(),
        ),
        1
    )

def getExportScopeCode(cross_module):
    if cross_module:
        return "NUITKA_CROSS_MODULE"
    else:
        return "NUITKA_LOCAL_MODULE"

def getSelectMetaclassCode(metaclass_identifier, bases_identifier, context):
    if Utils.python_version < 300:
        assert metaclass_identifier is None

        args = [
            bases_identifier.getCodeTemporaryRef(),
            getMetaclassVariableCode(context = context)
        ]
    else:
        args = [
            metaclass_identifier.getCodeTemporaryRef(),
            bases_identifier.getCodeTemporaryRef()
        ]


    return CallIdentifier( "SELECT_METACLASS", args )

def getStatementTrace(source_desc, statement_repr):
    return 'puts( "Execute: " %s );' % (
        CppStrings.encodeString( source_desc + " " + statement_repr ),
    )


def getConstantsDeclarationCode(context):
    constant_declarations, _constant_locals = getConstantsDeclCode(
        context    = context,
        for_header = True
    )

    constant_declarations += getCodeObjectsDeclCode(
        for_header = True
    )

    header_body = CodeTemplates.template_constants_declaration % {
        "constant_declarations" : "\n".join(constant_declarations)
    }

    return CodeTemplates.template_header_guard % {
        "header_guard_name" : "__NUITKA_DECLARATIONS_H__",
        "header_body"       : header_body
    }

def getConstantsDefinitionCode(context):
    constant_inits = getConstantsInitCode(
        context    = context
    )

    constant_inits += getCodeObjectsInitCode(
        context    = context
    )

    constant_declarations, constant_locals = getConstantsDeclCode(
        context    = context,
        for_header = False
    )

    constant_declarations += getCodeObjectsDeclCode(
        for_header = False
    )

    return CodeTemplates.template_constants_reading % {
        "constant_declarations" : "\n".join(constant_declarations),
        "constant_inits"        : indented(constant_inits),
        "constant_locals"       : indented(constant_locals)
    }

def getCurrentExceptionTypeCode():
    return Identifier(
        "_exception.getType()",
        0
    )

def getCurrentExceptionValueCode():
    return Identifier(
        "_exception.getValue()",
        0
    )

def getCurrentExceptionTracebackCode():
    return Identifier(
        "(PyObject *)_exception.getTraceback()",
        0
    )

def getListOperationAppendCode(list_identifier, value_identifier):
    return Identifier(
        "APPEND_TO_LIST( %s, %s ), Py_None" % (
            list_identifier.getCodeTemporaryRef(),
            value_identifier.getCodeTemporaryRef()
        ),
        0
    )

def getSetOperationAddCode(set_identifier, value_identifier):
    return Identifier(
        "ADD_TO_SET( %s, %s ), Py_None" % (
            set_identifier.getCodeTemporaryRef(),
            value_identifier.getCodeTemporaryRef()
        ),
        0
    )

def getDictOperationSetCode( dict_identifier, key_identifier,
                             value_identifier ):
    return Identifier(
        "DICT_SET_ITEM( %s, %s, %s ), Py_None" % (
            dict_identifier.getCodeTemporaryRef(),
            key_identifier.getCodeTemporaryRef(),
            value_identifier.getCodeTemporaryRef()
        ),
        0
    )

def getDictOperationGetCode(dict_identifier, key_identifier):
    return Identifier(
        "DICT_GET_ITEM( %s, %s )" % (
            dict_identifier.getCodeTemporaryRef(),
            key_identifier.getCodeTemporaryRef(),
        ),
        1
    )

def getDictOperationRemoveCode(dict_identifier, key_identifier):
    return "DICT_REMOVE_ITEM( %s, %s );" % (
        dict_identifier.getCodeTemporaryRef(),
        key_identifier.getCodeTemporaryRef()
    )

def getFrameLocalsUpdateCode(locals_identifier):
    if locals_identifier.isConstantIdentifier() and \
         locals_identifier.getConstant() == {}:
        return ""
    else:
        return CodeTemplates.template_frame_locals_update % {
            "locals_identifier" : locals_identifier.getCodeExportRef()
        }

def getFrameGuardHeavyCode( frame_identifier, code_identifier, codes,
                            locals_code, needs_preserve, context ):
    if context.isForDirectCall():
        return_code = CodeTemplates.frame_guard_cpp_return
    else:
        return_code = CodeTemplates.frame_guard_python_return

    tb_making = getTracebackMakingIdentifier( context )

    if needs_preserve:
        frame_class_name = "FrameGuardWithExceptionPreservation"
    else:
        frame_class_name = "FrameGuard"

    return CodeTemplates.frame_guard_full_template % {
        "frame_identifier"  : frame_identifier,
        "frame_class_name"  : frame_class_name,
        "code_identifier"   : code_identifier.getCodeTemporaryRef(),
        "codes"             : indented( codes ),
        "module_identifier" : getModuleAccessCode( context = context ),
        "frame_locals"      : indented( locals_code, vert_block = True ),
        "tb_making"         : tb_making.getCodeExportRef(),
        "return_code"       : return_code
    }

def getFrameGuardOnceCode( frame_identifier, code_identifier, locals_identifier,
                           codes, needs_preserve, context ):
    tb_making = getTracebackMakingIdentifier( context )

    if needs_preserve:
        frame_class_name = "FrameGuardWithExceptionPreservation"
    else:
        frame_class_name = "FrameGuard"

    return CodeTemplates.frame_guard_once_template % {
        "frame_identifier"  : frame_identifier,
        "frame_class_name"  : frame_class_name,
        "code_identifier"   : code_identifier.getCodeTemporaryRef(),
        "codes"             : indented( codes ),
        "module_identifier" : getModuleAccessCode( context = context ),
        "frame_locals"      : locals_identifier.getCodeExportRef(),
        "tb_making"         : tb_making.getCodeExportRef(),
        "return_code"       : indented( context.getReturnErrorCode() )
    }

def getFrameGuardLightCode(frame_identifier, code_identifier, codes, context):
    tb_making = getTracebackMakingIdentifier( context )

    return CodeTemplates.frame_guard_genfunc_template % {
        "frame_identifier"  : frame_identifier,
        "code_identifier"   : code_identifier.getCodeTemporaryRef(),
        "codes"             : indented( codes ),
        "module_identifier" : getModuleAccessCode( context = context ),
        "tb_making"         : tb_making.getCodeExportRef(),
    }

def getFrameGuardVeryLightCode(codes):
    return CodeTemplates.frame_guard_listcontr_template % {
        "codes"             : indented( codes, 0 ),
    }
