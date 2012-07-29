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
""" Generator for C++ and Python C/API.

This is the actual C++ code generator. It has methods and should be the only place to know
what C++ is like. Ideally it would be possible to replace the target language by changing
this one and the templates, and otherwise nothing else.

"""


from .Identifiers import (
    Identifier,
    ModuleVariableIdentifier,
    DefaultValueIdentifier,
    HelperCallIdentifier,
    ThrowingIdentifier,
    CallIdentifier,
    getCodeTemporaryRefs,
    getCodeExportRefs
)

from .Indentation import indented

from .Pickling import getStreamedConstant

from .OrderedEvaluation import getEvalOrderedCode

from .ConstantCodes import getConstantHandle, getConstantCode
from .VariableCodes import getVariableHandle, getVariableCode

from .TupleCodes import getTupleCreationCode
from .ListCodes import getListCreationCode # imported from here pylint: disable=W0611
from .SetCodes import getSetCreationCode # imported from here pylint: disable=W0611
from .DictCodes import getDictionaryCreationCode # imported from here pylint: disable=W0611

from .ParameterParsing import (
    getDirectFunctionEntryPointIdentifier,
    getParameterEntryPointIdentifier,
    getDefaultParameterDeclarations,
    getParameterParsingCode,
    getParameterContextCode,
)

from . import (
    CppRawStrings,
    CodeTemplates,
    OperatorCodes
)

from nuitka import (
    Variables,
    Constants,
    Builtins,
    Options
)

# pylint: disable=W0622
from ..__past__ import long, unicode
# pylint: enable=W0622

import re, sys

def getConstantAccess( context, constant ):
    # Many cases, because for each type, we may copy or optimize by creating empty.
    # pylint: disable=R0911

    if type( constant ) is dict:
        if constant:
            return Identifier(
                "PyDict_Copy( %s )" % getConstantCode(
                    constant = constant,
                    context  = context
                ),
                1
            )
        else:
            return Identifier(
                "PyDict_New()",
                1
            )
    elif type( constant ) is set:
        if constant:
            return Identifier(
                "PySet_New( %s )" % getConstantCode(
                    constant = constant,
                    context  = context
                ),
                1
            )
        else:
            return Identifier(
                "PySet_New( NULL )",
                1
            )
    elif type( constant ) is list:
        if constant:
            return Identifier(
                "LIST_COPY( %s )" % getConstantCode(
                    constant = constant,
                    context  = context
                ),
                1
            )
        else:
            return Identifier(
                "PyList_New( 0 )",
                1
            )
    else:
        return context.getConstantHandle(
            constant = constant
        )

def getVariableAccess( variable, context ):
    return getVariableHandle(
        variable = variable,
        context  = context
    )

def getReturnCode( identifier ):
    if identifier is not None:
        return "return %s;" % identifier.getCodeExportRef()
    else:
        return "return;"

def getYieldCode( identifier, for_return ):
    if for_return:
        return Identifier(
            "YIELD_RETURN( generator, %s )" % identifier.getCodeExportRef(),
            0
        )
    else:
        return Identifier(
            "YIELD_VALUE( generator, %s )" % identifier.getCodeExportRef(),
            0
        )

def getYieldTerminatorCode():
    return "throw ReturnException();"

def getMetaclassVariableCode( context ):
    package_var_identifier = ModuleVariableIdentifier(
        var_name         = "__metaclass__",
        module_code_name = context.getModuleCodeName()
    )

    return "( %s.isInitialized( false ) ? %s : NULL )" % (
        package_var_identifier.getCode(),
        package_var_identifier.getCodeTemporaryRef()
    )

def getBuiltinImportCode( module_identifier, globals_dict, locals_dict, import_list, level ):
    assert type( module_identifier ) is not str
    assert type( globals_dict ) is not str
    assert type( locals_dict ) is not str

    return Identifier(
        "IMPORT_MODULE( %s, %s, %s, %s, %s )" % (
            module_identifier.getCodeTemporaryRef(),
            globals_dict.getCodeTemporaryRef(),
            locals_dict.getCodeTemporaryRef(),
            import_list.getCodeTemporaryRef(),
            level.getCodeTemporaryRef()
        ),
        1
    )


def getImportFromStarCode( context, module_identifier ):
    if not context.hasLocalsDict():
        return "IMPORT_MODULE_STAR( %s, true, %s );" % (
            getModuleAccessCode(
                context = context
            ),
            module_identifier.getCodeTemporaryRef()
        )
    else:
        return "IMPORT_MODULE_STAR( locals_dict.asObject(), false, %s );" % (
            module_identifier.getCodeTemporaryRef()
        )


def getMaxIndexCode():
    return Identifier( "PY_SSIZE_T_MAX", 0 )

def getMinIndexCode():
    return Identifier( "0", 0 )

def getIndexValueCode( number ):
    return Identifier( "%s" % number, 0 )

def getIndexCode( identifier ):
    return Identifier(
        "CONVERT_TO_INDEX( %s )" % identifier.getCodeTemporaryRef(),
        0
    )

def _getCallNoStarArgsCode( function_identifier, argument_tuple, argument_dictionary ):
    if argument_dictionary is None:
        if argument_tuple is None:
            return Identifier(
                "CALL_FUNCTION_NO_ARGS( %(function)s )" % {
                    "function"   : function_identifier.getCodeTemporaryRef(),
                },
                1
            )
        else:
            return Identifier(
                "CALL_FUNCTION_WITH_POSARGS( %(function)s, %(pos_args)s )" % {
                    "function"   : function_identifier.getCodeTemporaryRef(),
                    "pos_args"   : argument_tuple.getCodeTemporaryRef()
                },
                1
            )
    else:
        if argument_tuple is None:
            return Identifier(
                "CALL_FUNCTION_WITH_KEYARGS( %(function)s, %(named_args)s )" % {
                    "function"   : function_identifier.getCodeTemporaryRef(),
                    "named_args" : argument_dictionary.getCodeTemporaryRef()
                },
                1
            )
        else:
            return Identifier(
                "CALL_FUNCTION( %(function)s, %(pos_args)s, %(named_args)s )" % {
                    "function"   : function_identifier.getCodeTemporaryRef(),
                    "pos_args"   : argument_tuple.getCodeTemporaryRef(),
                    "named_args" : argument_dictionary.getCodeTemporaryRef()
                },
                1
            )

def _getCallListStarArgsCode( function_identifier, argument_tuple, argument_dictionary, star_list_identifier ):
    if argument_dictionary is None:
        if argument_tuple is None:
            return Identifier(
                CodeTemplates.template_call_star_list % {
                    "function"      : function_identifier.getCodeTemporaryRef(),
                    "star_list_arg" : star_list_identifier.getCodeTemporaryRef()
                },
                1
            )
        else:
            return Identifier(
                CodeTemplates.template_call_pos_star_list % {
                    "function"      : function_identifier.getCodeTemporaryRef(),
                    "pos_args"      : argument_tuple.getCodeTemporaryRef(),
                    "star_list_arg" : star_list_identifier.getCodeTemporaryRef()
                },
                1
            )
    else:
        if argument_tuple is None:
            return Identifier(
                CodeTemplates.template_call_named_star_list % {
                    "function"      : function_identifier.getCodeTemporaryRef(),
                    "named_args"    : argument_dictionary.getCodeTemporaryRef(),
                    "star_list_arg" : star_list_identifier.getCodeTemporaryRef()
                },
                1
            )
        else:
            return Identifier(
                CodeTemplates.template_call_pos_named_star_list % {
                    "function"      : function_identifier.getCodeTemporaryRef(),
                    "pos_args"      : argument_tuple.getCodeTemporaryRef(),
                    "named_args"    : argument_dictionary.getCodeTemporaryRef(),
                    "star_list_arg" : star_list_identifier.getCodeTemporaryRef()
                },
                1
            )

def _getCallDictStarArgsCode( function_identifier, argument_tuple, argument_dictionary, star_dict_identifier ):
    if argument_dictionary is None:
        if argument_tuple is None:
            return Identifier(
                CodeTemplates.template_call_star_dict % {
                    "function"      : function_identifier.getCodeTemporaryRef(),
                    "star_dict_arg" : star_dict_identifier.getCodeTemporaryRef()
                },
                1
            )
        else:
            return Identifier(
                CodeTemplates.template_call_pos_star_dict % {
                    "function"      : function_identifier.getCodeTemporaryRef(),
                    "pos_args"      : argument_tuple.getCodeTemporaryRef(),
                    "star_dict_arg" : star_dict_identifier.getCodeTemporaryRef()
                },
                1
            )
    else:
        if argument_tuple is None:
            return Identifier(
                CodeTemplates.template_call_named_star_dict % {
                    "function"      : function_identifier.getCodeTemporaryRef(),
                    "named_args"    : argument_dictionary.getCodeTemporaryRef(),
                    "star_dict_arg" : star_dict_identifier.getCodeTemporaryRef()
                },
                1
            )
        else:
            return Identifier(
                CodeTemplates.template_call_pos_named_star_dict % {
                    "function"      : function_identifier.getCodeTemporaryRef(),
                    "pos_args"      : argument_tuple.getCodeTemporaryRef(),
                    "named_args"    : argument_dictionary.getCodeTemporaryRef(),
                    "star_dict_arg" : star_dict_identifier.getCodeTemporaryRef()
                },
                1
            )

def _getCallBothStarArgsCode( function_identifier, argument_tuple, argument_dictionary, \
                                      star_list_identifier, star_dict_identifier ):
    if argument_dictionary is None:
        if argument_tuple is None:
            return Identifier(
                CodeTemplates.template_call_star_list_star_dict % {
                    "function"      : function_identifier.getCodeTemporaryRef(),
                    "star_list_arg" : star_list_identifier.getCodeTemporaryRef(),
                    "star_dict_arg" : star_dict_identifier.getCodeTemporaryRef()
                },
                1
            )
        else:
            return Identifier(
                CodeTemplates.template_call_pos_star_list_star_dict % {
                    "function"      : function_identifier.getCodeTemporaryRef(),
                    "pos_args"      : argument_tuple.getCodeTemporaryRef(),
                    "star_list_arg" : star_list_identifier.getCodeTemporaryRef(),
                    "star_dict_arg" : star_dict_identifier.getCodeTemporaryRef()
                },
                1
            )
    else:
        if argument_tuple is None:
            return Identifier(
                CodeTemplates.template_call_named_star_list_star_dict % {
                    "function"      : function_identifier.getCodeTemporaryRef(),
                    "named_args"    : argument_dictionary.getCodeTemporaryRef(),
                    "star_list_arg" : star_list_identifier.getCodeTemporaryRef(),
                    "star_dict_arg" : star_dict_identifier.getCodeTemporaryRef()
                },
                1
            )
        else:
            return Identifier(
                CodeTemplates.template_call_pos_named_star_list_star_dict % {
                    "function"      : function_identifier.getCodeTemporaryRef(),
                    "pos_args"      : argument_tuple.getCodeTemporaryRef(),
                    "named_args"    : argument_dictionary.getCodeTemporaryRef(),
                    "star_list_arg" : star_list_identifier.getCodeTemporaryRef(),
                    "star_dict_arg" : star_dict_identifier.getCodeTemporaryRef()
                },
                1
            )


def getDirectionFunctionCallCode( function_identifier, arguments, closure_variables, extra_arguments, context ):
    function_identifier = getDirectFunctionEntryPointIdentifier(
        function_identifier = function_identifier
    )

    call_args = [
        extra_argument.getCodeTemporaryRef() if extra_argument is not None else "NULL"
        for extra_argument in
        extra_arguments
    ]

    call_args += getCodeExportRefs( arguments )

    call_args += getClosureVariableProvisionCode(
        context           = context,
        closure_variables = closure_variables
    )

    return Identifier(
        "%s( %s )" % (
            function_identifier,
            ", ".join( call_args )
        ),
        1
    )


def getCallCode( function_identifier, argument_tuple, argument_dictionary, \
                         star_list_identifier, star_dict_identifier ):
    if star_dict_identifier is None:
        if star_list_identifier is None:
            return _getCallNoStarArgsCode(
                function_identifier = function_identifier,
                argument_tuple      = argument_tuple,
                argument_dictionary = argument_dictionary
            )
        else:
            return _getCallListStarArgsCode(
                function_identifier  = function_identifier,
                argument_tuple       = argument_tuple,
                argument_dictionary  = argument_dictionary,
                star_list_identifier = star_list_identifier
            )
    else:
        if star_list_identifier is not None:
            return _getCallBothStarArgsCode(
                function_identifier  = function_identifier,
                argument_tuple       = argument_tuple,
                argument_dictionary  = argument_dictionary,
                star_list_identifier = star_list_identifier,
                star_dict_identifier = star_dict_identifier
            )
        else:
            return _getCallDictStarArgsCode(
                function_identifier  = function_identifier,
                argument_tuple       = argument_tuple,
                argument_dictionary  = argument_dictionary,
                star_dict_identifier = star_dict_identifier
            )

def getUnpackNextCode( iterator_identifier, count ):
    return Identifier(
        "UNPACK_NEXT( %s, %d )" % (
            iterator_identifier.getCodeTemporaryRef(),
            count - 1
        ),
        1
    )

def getUnpackCheckCode( iterator_identifier, count ):
    return "UNPACK_ITERATOR_CHECK( %s, %d );" % (
        iterator_identifier.getCodeTemporaryRef(),
        count
    )

def getSpecialAttributeLookupCode( attribute, source ):
    return Identifier(
        "LOOKUP_SPECIAL( %s, %s )" % (
            source.getCodeTemporaryRef(),
            attribute.getCodeTemporaryRef()
        ),
        1
    )

def getAttributeLookupCode( attribute, source ):
    return Identifier(
        "LOOKUP_ATTRIBUTE( %s, %s )" % (
            source.getCodeTemporaryRef(),
            attribute.getCodeTemporaryRef()
        ),
        1
    )

def getImportNameCode( import_name, module ):
    return Identifier(
        "IMPORT_NAME( %s, %s )" % (
            module.getCodeTemporaryRef(),
            import_name.getCodeTemporaryRef()
        ),
        1
    )

def getSubscriptLookupCode( subscript, source ):
    if subscript.isConstantIdentifier():
        constant = subscript.getConstant()

        if Constants.isIndexConstant( constant ):
            constant_value = int( constant )

            if abs( constant_value ) < 2**31:
                return Identifier(
                    "LOOKUP_SUBSCRIPT_CONST( %s, %s, %s )" % (
                        source.getCodeTemporaryRef(),
                        subscript.getCodeTemporaryRef(),
                        "%d" % constant
                    ),
                    1
                )

    return Identifier(
        "LOOKUP_SUBSCRIPT( %s, %s )" % (
            source.getCodeTemporaryRef(),
            subscript.getCodeTemporaryRef()
        ),
        1
    )

def getHasKeyCode( source, key ):
    return "HAS_KEY( %s, %s )" % (
        source.getCodeTemporaryRef(),
        key.getCodeTemporaryRef()
    )

def getSliceLookupCode( lower, upper, source ):
    return Identifier(
        "LOOKUP_SLICE( %s, %s, %s )" % (
            source.getCodeTemporaryRef(),
            "Py_None" if lower is None else lower.getCodeTemporaryRef(),
            "Py_None" if upper is None else upper.getCodeTemporaryRef()
        ),
        1
    )

def getSliceLookupIndexesCode( lower, upper, source ):
    return Identifier(
        "LOOKUP_INDEX_SLICE( %s, %s, %s )" % (
            source.getCodeTemporaryRef(),
            lower.getCodeTemporaryRef(),
            upper.getCodeTemporaryRef()
        ),
        1
    )

def getSliceObjectCode( lower, upper, step ):
    lower = "Py_None" if lower is None else lower.getCodeTemporaryRef()
    upper = "Py_None" if upper is None else upper.getCodeTemporaryRef()
    step  = "Py_None" if step  is None else step.getCodeTemporaryRef()

    return Identifier(
        "MAKE_SLICEOBJ( %s, %s, %s )" % ( lower, upper, step ),
        1
    )

def getStatementCode( identifier ):
    return identifier.getCodeDropRef() + ";"

def getBlockCode( codes ):
    if type( codes ) is str:
        assert codes == codes.rstrip(), codes

    return "{\n%s\n}" % indented( codes )

def getOperationCode( operator, identifiers ):
    identifier_refs = getCodeTemporaryRefs( identifiers )

    if operator == "Pow":
        assert len( identifiers ) == 2

        return Identifier(
            "POWER_OPERATION( %s, %s )" % (
                identifier_refs[0],
                identifier_refs[1]
            ),
            1
        )
    elif operator == "IPow":
        assert len( identifiers ) == 2

        return Identifier(
            "POWER_OPERATION_INPLACE( %s, %s )" % (
                identifier_refs[0],
                identifier_refs[1]
            ),
            1
        )
    elif operator == "Add":
        return Identifier(
            "BINARY_OPERATION_ADD( %s, %s )" % (
                identifier_refs[0],
                identifier_refs[1]
            ),
            1
        )
    elif operator == "Sub":
        return Identifier(
            "BINARY_OPERATION_SUB( %s, %s )" % (
                identifier_refs[0],
                identifier_refs[1]
            ),
            1
        )
    elif operator == "Div":
        return Identifier(
            "BINARY_OPERATION_DIV( %s, %s )" % (
                identifier_refs[0],
                identifier_refs[1]
            ),
            1
        )
    elif operator == "Mult":
        return Identifier(
            "BINARY_OPERATION_MUL( %s, %s )" % (
                identifier_refs[0],
                identifier_refs[1]
            ),
            1
        )
    elif operator == "Mod":
        return Identifier(
            "BINARY_OPERATION_REMAINDER( %s, %s )" % (
                identifier_refs[0],
                identifier_refs[1]
            ),
            1
        )
    elif len( identifiers ) == 2:
        return Identifier(
            "BINARY_OPERATION( %s, %s, %s )" % (
                OperatorCodes.binary_operator_codes[ operator ],
                identifier_refs[0],
                identifier_refs[1]
            ),
            1
        )
    elif len( identifiers ) == 1:
        helper, ref_count = OperatorCodes.unary_operator_codes[ operator ]

        return Identifier(
            "UNARY_OPERATION( %s, %s )" % (
                helper,
                identifier_refs[0]
            ),
            ref_count
        )
    else:
        assert False, (operator, identifiers)

def getPrintCode( newline, identifiers, target_file ):
    print_elements_code = []

    for identifier in identifiers:
        print_elements_code.append(
            CodeTemplates.template_print_value % {
                "print_value" : identifier.getCodeTemporaryRef(),
                "target_file" : "target_file" if target_file is not None else "NULL"
            }
        )

    if newline:
        print_elements_code.append(
            CodeTemplates.template_print_newline  % {
                "target_file" : "target_file" if target_file is not None else "NULL"
            }
        )

    if target_file is not None:
        return CodeTemplates.template_print_statement % {
            "target_file"         : target_file.getCodeExportRef() if target_file is not None else "NULL",
            "print_elements_code" : indented( print_elements_code )
        }
    else:
        return "\n".join( print_elements_code )


def getClosureVariableProvisionCode( context, closure_variables ):
    result = []

    for variable in closure_variables:
        assert variable.isClosureReference()

        variable = variable.getProviderVariable()

        result.append(
            getVariableCode(
                context  = context,
                variable = variable
            )
        )

    return result

def getConditionalExpressionCode( condition, codes_no, codes_yes ):
    if codes_yes.getCheapRefCount() == codes_no.getCheapRefCount():
        if codes_yes.getCheapRefCount == 0:
            return Identifier(
                "( %s ? %s : %s )" % (
                    condition.getCode(),
                    codes_yes.getCodeTemporaryRef(),
                    codes_no.getCodeTemporaryRef()
                ),
                0
            )
        else:
            return Identifier(
                "( %s ? %s : %s )" % (
                    condition.getCode(),
                    codes_yes.getCodeExportRef(),
                    codes_no.getCodeExportRef()
                ),
                1
            )
    else:
        return Identifier(
            "( %s ? %s : %s )" % (
                condition.getCode(),
                codes_yes.getCodeExportRef(),
                codes_no.getCodeExportRef()
            ),
            1
        )

def getFunctionCreationCode( context, function_identifier, default_identifiers, closure_variables ):
    args = getCodeExportRefs( default_identifiers )

    args += getClosureVariableProvisionCode(
        context           = context,
        closure_variables = closure_variables
    )

    return CallIdentifier(
        called  = "MAKE_FUNCTION_%s" % function_identifier,
        args    = args
    )

def getBranchCode( condition, yes_codes, no_codes ):
    assert yes_codes or no_codes

    if no_codes is None:
        return CodeTemplates.template_branch_one % {
            "condition"   : condition.getCode(),
            "branch_code" : indented( yes_codes if yes_codes is not None else "" )
        }
    else:
        assert no_codes, no_codes

        return CodeTemplates.template_branch_two % {
            "condition"       : condition.getCode(),
            "branch_yes_code" : indented( yes_codes if yes_codes is not None else "" ),
            "branch_no_code"  : indented( no_codes )
        }

def getLoopContinueCode( needs_exceptions ):
    if needs_exceptions:
        return "throw ContinueException();"
    else:
        return "continue;"

def getLoopBreakCode( needs_exceptions ):
    if needs_exceptions:
        return "throw BreakException();"
    else:
        return "break;"

def getComparisonExpressionCode( comparator, left, right ):
    # There is an awful lot of cases, and it's not helped by the need to generate more
    # complex code in the case of comparison chains. pylint: disable=R0912

    if comparator in OperatorCodes.normal_comparison_codes:
        py_api = OperatorCodes.normal_comparison_codes[ comparator ]

        assert py_api.startswith( "SEQUENCE_CONTAINS" )

        return Identifier(
            "%s( %s, %s )" % (
                py_api,
                left.getCodeTemporaryRef(),
                right.getCodeTemporaryRef()
            ),
            0
        )
    elif comparator in OperatorCodes.rich_comparison_codes:
        return Identifier(
            "RICH_COMPARE_%s( %s, %s )" % (
                OperatorCodes.rich_comparison_codes[ comparator ],
                left.getCodeTemporaryRef(),
                right.getCodeTemporaryRef()
            ),
            1
        )
    elif comparator == "Is":
        return Identifier(
            "BOOL_FROM( %s == %s )" % (
                left.getCodeTemporaryRef(),
                right.getCodeTemporaryRef()
            ),
            0
        )
    elif comparator == "IsNot":
        return Identifier(
            "BOOL_FROM( %s != %s )" % (
                left.getCodeTemporaryRef(),
                right.getCodeTemporaryRef()
            ),
            0
        )

    assert False, comparator

def getComparisonExpressionBoolCode( comparator, left, right ):
    # There is an awful lot of cases, and it's not helped by the need to generate more
    # complex code in the case of comparison chains. pylint: disable=R0912

    if comparator in OperatorCodes.normal_comparison_codes:
        py_api = OperatorCodes.normal_comparison_codes[ comparator ]

        assert py_api.startswith( "SEQUENCE_CONTAINS" )

        comparison = Identifier(
            "%s_BOOL( %s, %s )" % (
                py_api,
                left.getCodeTemporaryRef(),
                right.getCodeTemporaryRef()
            ),
            0
        )
    elif comparator in OperatorCodes.rich_comparison_codes:
        comparison = Identifier(
            "RICH_COMPARE_BOOL_%s( %s, %s )" % (
                OperatorCodes.rich_comparison_codes[ comparator ],
                left.getCodeTemporaryRef(),
                right.getCodeTemporaryRef()
            ),
            0
        )
    elif comparator == "Is":
        comparison = Identifier(
            "( %s == %s )" % (
                left.getCodeTemporaryRef(),
                right.getCodeTemporaryRef()
            ),
            0
        )
    elif comparator == "IsNot":
        comparison = Identifier(
            "( %s != %s )" % (
                left.getCodeTemporaryRef(),
                right.getCodeTemporaryRef()
            ),
            0
        )
    else:
        assert False, comparator

    return comparison

def getConditionNotBoolCode( condition ):
    return Identifier(
        "(!( %s ))" % condition.getCodeTemporaryRef(),
        0
    )

def getConditionAndCode( identifiers ):
    return Identifier(
        "( %s )" % " && ".join( [ identifier.getCode() for identifier in identifiers ] ),
        0
    )

def getConditionOrCode( identifiers ):
    return Identifier(
        "( %s )" % " || ".join( [ identifier.getCode() for identifier in identifiers ] ),
        0
    )

def getConditionCheckTrueCode( condition ):
    return Identifier(
        "CHECK_IF_TRUE( %s )" % condition.getCodeTemporaryRef(),
        0
    )

def getConditionCheckFalseCode( condition ):
    return Identifier(
        "CHECK_IF_FALSE( %s )" % condition.getCodeTemporaryRef(),
        0
    )

def getTrueExpressionCode():
    return Identifier( "true", 0 )

def getFalseExpressionCode():
    return Identifier( "false", 0 )

def getSelectionOrCode( conditions ):
    result = " ?: ".join(
        [
            "SELECT_IF_TRUE( %s )" % condition.getCodeExportRef()
            for condition in
            conditions[:-1]
        ]
    )

    return Identifier(
        "(%s ?: %s)" % (
            result,
            conditions[-1].getCodeExportRef()
        ),
        1
    )

def getSelectionAndCode( conditions ):
    result = " ?: ".join(
        [
            "SELECT_IF_FALSE( %s )" % condition.getCodeExportRef()
            for condition in
            conditions[:-1]
        ]
    )

    return Identifier(
        "(%s ?: %s)" % (
            result,
            conditions[-1].getCodeExportRef()
        ),
        1
    )

def getAttributeAssignmentCode( target, attribute, identifier ):
    return "SET_ATTRIBUTE( %s, %s, %s );" % (
        target.getCodeTemporaryRef(),
        attribute.getCodeTemporaryRef(),
        identifier.getCodeTemporaryRef()
    )

def getAttributeDelCode( target, attribute ):
    return "DEL_ATTRIBUTE( %s, %s );" % (
        target.getCodeTemporaryRef(),
        attribute.getCodeTemporaryRef()
    )

def getSliceAssignmentIndexesCode( target, lower, upper, identifier ):
    return "SET_INDEX_SLICE( %s, %s, %s, %s );" % (
        target.getCodeTemporaryRef(),
        lower.getCodeTemporaryRef(),
        upper.getCodeTemporaryRef(),
        identifier.getCodeTemporaryRef()
    )

def getSliceAssignmentCode( target, lower, upper, identifier ):
    return "SET_SLICE( %s, %s, %s, %s );" % (
        identifier.getCodeTemporaryRef(),
        target.getCodeTemporaryRef(),
        "Py_None" if lower is None else lower.getCodeTemporaryRef(),
        "Py_None" if upper is None else upper.getCodeTemporaryRef()
    )

def getSliceDelCode( target, lower, upper ):
    return "DEL_SLICE( %s, %s, %s );" % (
        target.getCodeTemporaryRef(),
        "Py_None" if lower is None else lower.getCodeTemporaryRef(),
        "Py_None" if upper is None else upper.getCodeTemporaryRef()
    )

def getLineNumberCode( context, source_ref ):
    if source_ref.shallSetCurrentLine():
        if context.hasFrameGuard():
            template = "frame_guard.setLineNumber( %d );\n"
        else:
            template = "generator->m_frame->f_lineno = %d;\n"

        return template % source_ref.getLineNumber()
    else:
        return ""

def getLoopCode( loop_body_codes, needs_exceptions ):
    if needs_exceptions:
        while_loop_template = CodeTemplates.template_loop_break_continue_catching
    else:
        while_loop_template = CodeTemplates.template_loop_break_continue_direct

    return while_loop_template % {
        "loop_body_codes" : indented(
            loop_body_codes if loop_body_codes is not None else ""
        ),
    }

def getVariableAssignmentCode( context, variable, identifier ):
    assert isinstance( variable, Variables.Variable ), variable

    # This ought to be impossible to happen, as an assignment to an overflow variable
    # would have made it a local one.
    assert not variable.isMaybeLocalVariable()

    if variable.isTempVariableReference():
        referenced = variable.getReferenced()

        if not referenced.declared:
            referenced.declared = True

            return _getLocalVariableInitCode(
                context   = context,
                variable  = variable.getReferenced(),
                init_from = identifier
            )
        elif not referenced.getNeedsFree():
            # So won't get a reference, and take none, or else it may get lost, which we
            # don't want to happen.

            # This must be true, otherwise the needs no free statement was made in error.
            assert identifier.getCheapRefCount() == 0

            return "%s = %s;" % (
                getVariableCode(
                    variable = variable,
                    context  = context
                ),
                identifier.getCodeTemporaryRef()
            )

    if identifier.getCheapRefCount() == 0:
        identifier_code = identifier.getCodeTemporaryRef()
        assign_code = "assign0"
    else:
        identifier_code = identifier.getCodeExportRef()
        assign_code = "assign1"

    return "%s.%s( %s );" % (
        getVariableCode(
            variable = variable,
            context  = context
        ),
        assign_code,
        identifier_code
    )

def getVariableDelCode( context, variable ):
    assert isinstance( variable, Variables.Variable ), variable

    if variable.isModuleVariable():
        var_name = variable.getName()

        context.addGlobalVariableNameUsage( var_name )

        return "_mvar_%s_%s.del();" % (
            context.getModuleCodeName(),
            var_name
        )
    else:
        return "%s.del();" % getVariableCode(
            variable = variable,
            context  = context
        )

def getSubscriptAssignmentCode( subscribed, subscript, identifier ):
    return "SET_SUBSCRIPT( %s, %s, %s );" % (
        identifier.getCodeTemporaryRef(),
        subscribed.getCodeTemporaryRef(),
        subscript.getCodeTemporaryRef()
    )

def getSubscriptDelCode( subscribed, subscript ):
    return "DEL_SUBSCRIPT( %s, %s );" % (
        subscribed.getCodeTemporaryRef(),
        subscript.getCodeTemporaryRef()
    )

def getTryFinallyCode( context, code_tried, code_final ):
    tb_making = getTracebackMakingIdentifier( context )

    return CodeTemplates.try_finally_template % {
        "try_count"  : context.allocateTryNumber(),
        "tried_code" : indented( code_tried ),
        "final_code" : indented( code_final, 0 ),
        "tb_making"  : tb_making.getCodeExportRef(),
    }

def getTryExceptHandlerCode( exception_identifiers, handler_code, first_handler ):
    exception_code = []

    cond_keyword = "if" if first_handler else "else if"

    if exception_identifiers:
        exception_code.append(
            "%s ( %s )" % (
                cond_keyword,
                " || ".join(
                    "_exception.matches( %s )" % exception_identifier.getCodeTemporaryRef()
                    for exception_identifier in
                    exception_identifiers
                )
            )
        )
    else:
        exception_code.append(
            "%s (true)" % cond_keyword
        )

    exception_code += getBlockCode(
        handler_code or ""
    ).split( "\n" )

    return exception_code

def getTryExceptCode( context, code_tried, handler_codes ):
    exception_code = handler_codes
    exception_code += CodeTemplates.try_except_reraise_unmatched_template.split( "\n" )

    tb_making = getTracebackMakingIdentifier( context )

    return CodeTemplates.try_except_template % {
        "tried_code"     : indented( code_tried or "" ),
        "exception_code" : indented( exception_code ),
        "tb_making"      : tb_making.getCodeExportRef(),
    }


def getRaiseExceptionCode( exception_type_identifier, exception_value_identifier, \
                           exception_tb_identifier, exception_tb_maker ):
    if exception_value_identifier is None and exception_tb_identifier is None:
        return "traceback = true; RAISE_EXCEPTION( %s, %s );" % (
            exception_type_identifier.getCodeExportRef(),
            exception_tb_maker.getCodeExportRef()
        )
    elif exception_tb_identifier is None:
        return "traceback = true; RAISE_EXCEPTION( %s, %s, %s );" % (
            exception_type_identifier.getCodeExportRef(),
            exception_value_identifier.getCodeExportRef(),
            exception_tb_maker.getCodeExportRef()
        )
    else:
        return "traceback = true; RAISE_EXCEPTION( %s, %s, %s );" % (
            exception_type_identifier.getCodeExportRef(),
            exception_value_identifier.getCodeExportRef(),
            exception_tb_identifier.getCodeExportRef()
        )

def getReRaiseExceptionCode( local ):
    if local:
        return "traceback = true; throw;"
    else:
        return "traceback = true; RERAISE_EXCEPTION();"

def getRaiseExceptionExpressionCode( exception_type_identifier, exception_value_identifier, \
                                     exception_tb_maker ):
    return ThrowingIdentifier(
        "THROW_EXCEPTION( %s, %s, %s, &traceback )" % (
            exception_type_identifier.getCodeExportRef(),
            exception_value_identifier.getCodeExportRef(),
            exception_tb_maker.getCodeExportRef()
        )
    )

def getSideEffectsCode( side_effects, identifier ):
    if not side_effects:
        return identifier

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


def getBuiltinRefCode( context, builtin_name ):
    return Identifier(
        "LOOKUP_BUILTIN( %s )" % getConstantCode(
            constant = builtin_name,
            context  = context
        ),
        0
    )

def getBuiltinAnonymousRefCode( builtin_name ):
    return Identifier(
        "(PyObject *)%s" % Builtins.builtin_anon_codes[ builtin_name ],
        0
    )


def getExceptionRefCode( exception_type ):
    return Identifier(
        "PyExc_%s" % exception_type,
        0
    )

def getMakeBuiltinExceptionCode( context, exception_type, exception_args ):
    return getCallCode(
        function_identifier = Identifier( "PyExc_%s" % exception_type, 0 ),
        argument_tuple      = getTupleCreationCode(
            element_identifiers = exception_args,
            context             = context,
        ),
        argument_dictionary  = None,
        star_list_identifier = None,
        star_dict_identifier = None
    )

def _getLocalVariableList( context, provider ):
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

        include_closure = not provider.isUnoptimized() and not provider.isClassDictCreation()
    else:
        variables = provider.getVariables()

        include_closure = True

    return [
        "&%s" % getVariableCode(
            variable = variable,
            context = context
        )
        for variable in
        variables
        if not variable.isModuleVariable()
        if not variable.isMaybeLocalVariable()
        if ( not variable.isClosureReference() or include_closure )
    ]


def getLoadDirCode( context, provider ):
    if provider.isModule():
        # TODO: Giving 1 for a temporary ref looks wrong.
        return Identifier(
            "PyDict_Keys( %s )" % getLoadGlobalsCode(
                context = context
            ).getCodeTemporaryRef(),
            1
        )
    else:
        local_list = _getLocalVariableList(
            context  = context,
            provider = provider
        )

        if context.hasLocalsDict():
            return Identifier(
                "PyDict_Keys( UPDATED_LOCALS_DICT( locals.asObject()%s )" % (
                    "".join( ", %s" % x for x in local_list ),
                ),
                1
            )
        else:
            return Identifier(
                "MAKE_LOCALS_DIR( %s )" % (
                    ", ".join( local_list ),
                ),
                1
            )

def getLoadVarsCode( identifier ):
    return Identifier(
        "LOOKUP_VARS( %s )" % identifier.getCodeTemporaryRef(),
        1
    )

def getLoadGlobalsCode( context ):
    return Identifier(
        "PyModule_GetDict( %(module_identifier)s )" % {
            "module_identifier" : getModuleAccessCode( context )
        },
        0
    )

def getLoadLocalsCode( context, provider, mode ):
    assert not provider.isModule()

    if not context.hasLocalsDict():
        local_list = _getLocalVariableList(
            provider = provider,
            context  = context
        )

        return Identifier(
            "MAKE_LOCALS_DICT( %s )" % ", ".join( local_list ),
            1
        )
    else:
        if mode == "copy":
            return Identifier(
                "PyDict_Copy( locals_dict.asObject() )",
                1
            )
        elif mode == "updated":
            local_list = _getLocalVariableList(
                provider = provider,
                context  = context
            )

            return Identifier(
                "UPDATED_LOCALS_DICT( locals_dict.asObject()%s )" % (
                    "".join( ", %s" % x for x in local_list ),
                ),
                1
            )
        else:
            assert False

def getStoreLocalsCode( context, source_identifier, provider ):
    assert not provider.isModule()

    code = ""

    for variable in provider.getVariables():
        if not variable.isModuleVariable() and not variable.isMaybeLocalVariable():
            key_identifier = getConstantHandle(
                context  = context,
                constant = variable.getName()
            )

            var_assign_code = getVariableAssignmentCode(
                context    = context,
                variable   = variable,
                identifier = getSubscriptLookupCode(
                    subscript = key_identifier,
                    source    = source_identifier
                )
            )

            # This ought to re-use the condition code stuff.
            code += "if ( %s )\n" % getHasKeyCode(
                source = source_identifier,
                key    = key_identifier
            )

            code += getBlockCode( var_assign_code ) + "\n"

    return code

def getFutureFlagsCode( future_spec ):
    flags = future_spec.asFlags()

    if flags:
        return " | ".join( flags )
    else:
        return 0


def getEvalCode( context, exec_code, filename_identifier, globals_identifier, \
                 locals_identifier, mode_identifier, future_flags, provider ):
    if context.getParent() is None:
        return Identifier(
            CodeTemplates.eval_global_template % {
                "globals_identifier"      : globals_identifier.getCodeTemporaryRef(),
                "locals_identifier"       : locals_identifier.getCodeTemporaryRef(),
                "make_globals_identifier" : getLoadGlobalsCode(
                    context = context
                ).getCodeExportRef(),
                "source_identifier"       : exec_code.getCodeTemporaryRef(),
                "filename_identifier"     : filename_identifier,
                "mode_identifier"         : mode_identifier,
                "future_flags"            : future_flags,
            },
            1
        )
    else:
        make_globals_identifier = getLoadGlobalsCode(
            context = context
        )
        make_locals_identifier = getLoadLocalsCode(
            context  = context,
            provider = provider,
            mode     = "updated"
        )

        return Identifier(
            CodeTemplates.eval_local_template % {
                "globals_identifier"      : globals_identifier.getCodeTemporaryRef(),
                "locals_identifier"       : locals_identifier.getCodeTemporaryRef(),
                "make_globals_identifier" : make_globals_identifier.getCodeExportRef(),
                "make_locals_identifier"  : make_locals_identifier.getCodeExportRef(),
                "source_identifier"       : exec_code.getCodeTemporaryRef(),
                "filename_identifier"     : filename_identifier,
                "mode_identifier"         : mode_identifier,
                "future_flags"            : future_flags,
            },
            1
        )

def getExecCode( context, exec_code, globals_identifier, locals_identifier, future_flags, provider ):
    make_globals_identifier = getLoadGlobalsCode(
        context = context
    )

    if context.getParent() is None:
        return CodeTemplates.exec_global_template % {
            "globals_identifier"      : globals_identifier.getCodeExportRef(),
            "locals_identifier"       : locals_identifier.getCodeExportRef(),
            "make_globals_identifier" : make_globals_identifier.getCodeExportRef(),
            "source_identifier"       : exec_code.getCodeTemporaryRef(),
            "filename_identifier"     : getConstantCode(
                constant = "<string>",
                context  = context
            ),
            "mode_identifier"         : getConstantCode(
                constant = "exec",
                context  = context
            ),
            "future_flags"            : future_flags,
        }
    else:
        locals_temp_identifier = Identifier( "locals.asObject()", 0 )

        make_locals_identifier = getLoadLocalsCode(
            context  = context,
            provider = provider,
            mode     = "updated"
        )

        return CodeTemplates.exec_local_template % {
            "globals_identifier"      : globals_identifier.getCodeExportRef(),
            "locals_identifier"       : locals_identifier.getCodeExportRef(),
            "make_globals_identifier" : make_globals_identifier.getCodeExportRef(),
            "make_locals_identifier"  : make_locals_identifier.getCodeExportRef(),
            "source_identifier"       : exec_code.getCodeTemporaryRef(),
            # TODO: Move to the outside, and make using the real source reference an
            # option.
            "filename_identifier"     : getConstantCode(
                constant = "<string>",
                context = context
            ),
            "mode_identifier"         : getConstantCode(
                constant = "exec",
                context  = context
            ),
            "future_flags"            : future_flags,
            "store_locals_code"       : indented(
                getStoreLocalsCode(
                    context           = context,
                    source_identifier = locals_temp_identifier,
                    provider          = provider
                ),
                2
            )
        }

def getBuiltinSuperCode( type_identifier, object_identifier ):
    super_type = type_identifier.getCodeTemporaryRef() if type_identifier is not None else "NULL"
    super_object = object_identifier.getCodeTemporaryRef() if object_identifier is not None else "NULL"

    return Identifier(
        "BUILTIN_SUPER( %s, %s )" % (
            super_type,
            super_object
        ),
        1
    )

def getBuiltinOpenCode( filename, mode, buffering ):
    filename = filename.getCodeTemporaryRef() if filename is not None else "NULL"
    mode = mode.getCodeTemporaryRef() if mode is not None else "NULL"
    buffering = buffering.getCodeTemporaryRef() if buffering is not None else "NULL"

    return Identifier(
        "OPEN_FILE( %s, %s, %s )" % (
            filename,
            mode,
            buffering
        ),
        1
    )

def getBuiltinLenCode( identifier ):
    return Identifier( "BUILTIN_LEN( %s )" % identifier.getCodeTemporaryRef(), 1 )

def getBuiltinDir1Code( identifier ):
    return Identifier( "BUILTIN_DIR1( %s )" % identifier.getCodeTemporaryRef(), 1 )

def getBuiltinRangeCode( low, high, step ):
    if step is not None:
        return HelperCallIdentifier(
            "BUILTIN_RANGE", low, high, step
        )
    elif high is not None:
        return HelperCallIdentifier(
            "BUILTIN_RANGE", low, high
        )
    else:
        return HelperCallIdentifier(
            "BUILTIN_RANGE", low
        )

def getBuiltinChrCode( value ):
    return HelperCallIdentifier( "BUILTIN_CHR", value )

def getBuiltinOrdCode( value ):
    return HelperCallIdentifier( "BUILTIN_ORD", value )

def getBuiltinBinCode( value ):
    return HelperCallIdentifier( "BUILTIN_BIN", value )

def getBuiltinOctCode( value ):
    return HelperCallIdentifier( "BUILTIN_OCT", value )

def getBuiltinHexCode( value ):
    return HelperCallIdentifier( "BUILTIN_HEX", value )

def getBuiltinType1Code( value ):
    return HelperCallIdentifier( "BUILTIN_TYPE1", value )

def getBuiltinIter1Code( value ):
    return HelperCallIdentifier( "MAKE_ITERATOR", value )

def getBuiltinIter2Code( callable_identifier, sentinel_identifier ):
    return Identifier(
        "BUILTIN_ITER2( %s, %s )" % (
            callable_identifier.getCodeExportRef(),
            sentinel_identifier.getCodeExportRef()
        ),
        1
    )

def getBuiltinNext1Code( value ):
    return HelperCallIdentifier( "BUILTIN_NEXT1", value )

def getBuiltinNext2Code( iterator_identifier, default_identifier ):
    return Identifier(
        "BUILTIN_NEXT2( %s, %s )" % (
            iterator_identifier.getCodeTemporaryRef(),
            default_identifier.getCodeTemporaryRef()
        ),
        1
    )

def getBuiltinType3Code( context, name_identifier, bases_identifier, dict_identifier ):
    return Identifier(
        "BUILTIN_TYPE3( %s, %s, %s, %s )" % (
            getConstantCode(
                constant = context.getModuleName(),
                context  = context
            ),
            name_identifier.getCodeTemporaryRef(),
            bases_identifier.getCodeTemporaryRef(),
            dict_identifier.getCodeTemporaryRef()
        ),
        1
    )

def getBuiltinTupleCode( identifier ):
    return HelperCallIdentifier( "TO_TUPLE", identifier )

def getBuiltinListCode( identifier ):
    return HelperCallIdentifier( "TO_LIST", identifier )

def getBuiltinDictCode( seq_identifier, dict_identifier ):
    assert seq_identifier is not None or dict_identifier is not None

    if seq_identifier is not None:
        return Identifier(
            "TO_DICT( %s, %s )" % (
                seq_identifier.getCodeTemporaryRef(),
                dict_identifier.getCodeTemporaryRef() if dict_identifier is not None else "NULL"
            ),
            1
        )
    else:
        return dict_identifier

def getBuiltinFloatCode( identifier ):
    return HelperCallIdentifier( "TO_FLOAT", identifier )

def getBuiltinLongCode( context, identifier, base ):
    if identifier is None:
        identifier = getConstantHandle( context = context, constant = "0" )

    if base is None:
        return HelperCallIdentifier( "TO_LONG", identifier )
    else:
        return HelperCallIdentifier( "TO_LONG", identifier, base )

def getBuiltinIntCode( context, identifier, base ):
    if identifier is None:
        identifier = getConstantHandle( context = context, constant = "0" )

    if base is None:
        return HelperCallIdentifier( "TO_INT", identifier )
    else:
        return HelperCallIdentifier( "TO_INT", identifier, base )

def getBuiltinStrCode( identifier ):
    return HelperCallIdentifier( "TO_STR", identifier )

def getBuiltinUnicodeCode( identifier ):
    return HelperCallIdentifier( "TO_UNICODE", identifier )

def getBuiltinBoolCode( identifier ):
    return Identifier(
        "TO_BOOL( %s )" % identifier.getCodeTemporaryRef(),
        0
    )

def getModuleAccessCode( context ):
    return Identifier( "_module_%s" % context.getModuleCodeName(), 0 ).getCode()

def getFrameMakingIdentifier( context ):
    return context.getFrameHandle()

def getTracebackMakingIdentifier( context ):
    return Identifier(
        "MAKE_TRACEBACK( %s )" % (
            getFrameMakingIdentifier( context = context ).getCodeExportRef(),
        ),
        1
    )

def getModuleIdentifier( module_name ):
    return module_name.replace( ".", "__" ).replace( "-", "_" )

def getPackageIdentifier( module_name ):
    return module_name.replace( ".", "__" )

def getModuleCode( context, module_name, package_name, codes, tmp_variables, \
                   doc_identifier, path_identifier, source_ref ):

    # For the module code, lots of attributes come together. pylint: disable=R0914

    functions_decl = getFunctionsDecl( context = context )
    functions_code = getFunctionsCode( context = context )

    module_var_names = context.getGlobalVariableNames()

    # These ones are used in the init code to set these variables to their values
    # after module creation.
    module_var_names.add( "__file__" )
    module_var_names.add( "__doc__" )
    module_var_names.add( "__package__" )

    if path_identifier is not None:
        module_var_names.add( "__path__" )

    module_identifier = getModuleIdentifier( module_name )

    module_globals = "\n".join(
        [
            "static %s _mvar_%s_%s( &_module_%s, &%s );" % (
                "PyObjectGlobalVariable_%s" % module_identifier,
                module_identifier,
                var_name,
                module_identifier,
                getConstantCode( constant = var_name, context = context )
            )
            for var_name in
            sorted( module_var_names )
        ]
    )

    if package_name is None:
        module_inits = CodeTemplates.module_init_no_package_template % {
            "module_identifier"   : module_identifier,
            "filename_identifier" : getConstantCode(
                constant = source_ref.getFilename(),
                context  = context
            ),
            "doc_identifier"      : doc_identifier.getCode(),
            "is_package"          : 0 if path_identifier is None else 1,
            "path_identifier"     : path_identifier.getCode() if path_identifier else "",
        }
    else:
        module_inits = CodeTemplates.module_init_in_package_template % {
            "module_identifier"       : module_identifier,
            "module_name"             : getConstantCode(
                constant = module_name.split(".")[-1],
                context  = context
            ),
            "filename_identifier"     : getConstantCode(
                constant = source_ref.getFilename(),
                context  = context
            ),
            "is_package"              : 0 if path_identifier is None else 1,
            "path_identifier"         : path_identifier.getCode() if path_identifier else "",
            "doc_identifier"          : doc_identifier.getCode(),
            "package_identifier"      : getPackageIdentifier( package_name )
        }

    assert module_inits.endswith( "\n" )

    header = CodeTemplates.global_copyright % {
        "name"    : module_name,
        "version" : Options.getVersion()
    }

    module_local_decl = [
        "PyObjectTempHolder %s;" % tmp_variable
        for tmp_variable in tmp_variables
    ]

    code_identifier = context.getCodeObjectHandle(
        filename     = source_ref.getFilename(),
        arg_names    = (),
        line_number  = 0,
        code_name    = module_name if module_name != "__main__" else "<module>",
        is_generator = False
    )

    module_code = CodeTemplates.module_body_template % {
        "module_name"           : module_name,
        "module_name_obj"       : getConstantCode(
            context  = context,
            constant = module_name
        ),
        "module_identifier"     : module_identifier,
        "code_identifier"       : code_identifier.getCodeTemporaryRef(),
        "module_functions_decl" : functions_decl,
        "module_functions_code" : functions_code,
        "module_globals"        : module_globals,
        "module_inits"          : module_inits + indented( module_local_decl ),
        "module_code"           : indented( codes, 2 )
    }

    return header + module_code

def getModuleDeclarationCode( module_name ):
    module_header_code = CodeTemplates.module_header_template % {
        "module_identifier" : getModuleIdentifier( module_name ),
    }

    return CodeTemplates.template_header_guard % {
        "header_guard_name" : "__%s_H__" % getModuleIdentifier( module_name ),
        "header_body"       : module_header_code
    }

def getMainCode( codes, other_module_names ):
    module_inittab = []

    for other_module_name in other_module_names:
        module_inittab.append (
            CodeTemplates.module_inittab_entry % {
                "module_name"       : other_module_name,
                "module_identifier" : getModuleIdentifier( other_module_name ),
            }
        )

    main_code = CodeTemplates.main_program % {
        "module_inittab" : indented( sorted( module_inittab ) ),
        "sys_executable" : CppRawStrings.encodeString(
            "python.exe" if Options.isWindowsTarget() else sys.executable
        ),
        "use_unfreezer"  : 1 if other_module_names else 0
    }

    return codes + main_code


def getFunctionsCode( context ):
    result = ""

    for _code_name, ( _function_decl, function_code ) in sorted( context.getFunctionsCodes().items() ):
        result += function_code

    return result

def getFunctionsDecl( context ):
    result = ""

    for _code_name, ( function_decl, _function_code ) in sorted( context.getFunctionsCodes().items() ):
        result += function_decl

    return result

def _getFunctionCreationArgs( default_identifiers, closure_variables ):
    result = getDefaultParameterDeclarations(
        default_identifiers = default_identifiers
    )

    for closure_variable in closure_variables:
        result.append( "PyObjectSharedLocalVariable &python_closure_%s" % closure_variable.getName() )

    return result

def _extractArgNames( args ):
    def extractArgName( value ):
        value = value.strip()

        if " " in value:
            value = value.split()[-1]
        value = value.split("*")[-1]
        value = value.split("&")[-1]

        return value

    return [
        extractArgName( part.strip() )
        for part in
        args
    ]

def getFunctionDecl( context, function_identifier, default_identifiers, closure_variables, \
                     function_parameter_variables ):

    if context.function.needsCreation():
        # TODO: These two branches probably mean it's two different things.

        function_creation_arg_spec = _getFunctionCreationArgs(
            default_identifiers = default_identifiers,
            closure_variables   = closure_variables
        )

        function_creation_arg_names = _extractArgNames( function_creation_arg_spec )

        return CodeTemplates.template_function_make_declaration % {
            "function_identifier"            : function_identifier,
            "function_creation_arg_spec"     : getEvalOrderedCode(
                context = context,
                args    = function_creation_arg_spec
            ),
            "function_creation_arg_names"    : ", ".join( function_creation_arg_names ),
            "function_creation_arg_reversal" : getEvalOrderedCode(
                context = context,
                args    = function_creation_arg_names
            )
        }
    else:
        parameter_objects_decl = []

        if context.function.isClassDictCreation():
            parameter_objects_decl += [ "PyObject *metaclass", "PyObject *bases" ]

        parameter_objects_decl += [
            "PyObject *_python_par_" + variable.getName()
            for variable in
            function_parameter_variables
        ]

        for closure_variable in closure_variables:
            parameter_objects_decl.append(
                closure_variable.getDeclarationCode(
                    for_reference = True,
                    for_local     = False
                )
            )

        return CodeTemplates.template_function_direct_declaration % {
            "function_identifier"    : function_identifier,
            "parameter_objects_decl" : ", ".join( parameter_objects_decl ),
        }

# TODO: Move this to VariableCodes, it's that subject.
def _getLocalVariableInitCode( context, variable, init_from = None, in_context = False ):
    # This has many cases to deal with, so there need to be a lot of branches. It could
    # be cleaner a bit by solving the TODOs, but the fundamental problem renames.
    # pylint: disable=R0912

    assert not variable.isModuleVariable()

    assert init_from is None or hasattr( init_from, "getCodeTemporaryRef" )

    result = variable.getDeclarationTypeCode()

    # For pointer types, we don't have to separate with spaces.
    if not result.endswith( "*" ):
        result += " "

    store_name = variable.getMangledName()

    if not in_context:
        result += "_"

    result += variable.getCodeName()

    if not in_context:
        if variable.isTempVariable():
            if init_from is None:
                result += " = " + variable.getDeclarationInitValueCode()
            elif not variable.getNeedsFree():
                result += " = %s" % init_from.getCodeTemporaryRef()
            else:
                result += "( %s )" % init_from.getCodeExportRef()
        else:
            result += "( "

            result += "%s" % getConstantCode(
                context  = context,
                constant = store_name
            )

            if init_from is not None:
                if context.hasLocalsDict():
                    if init_from.getCheapRefCount() == 0:
                        result += ", %s" % init_from.getCodeTemporaryRef()
                    else:
                        result += ", %s" % init_from.getCodeExportRef()

                        if not variable.isParameterVariable():
                            result += ", true"
                else:
                    result += ", %s" % init_from.getCodeExportRef()

            result += " )"

    result += ";"

    return result

def _getFuncDefaultValue( identifiers, context ):
    if len( identifiers ) > 0:
        return getTupleCreationCode(
            element_identifiers = identifiers,
            context             = context
        )
    else:
        return getConstantHandle(
            constant = None,
            context  = context
        )

def getGeneratorFunctionCode( context, function_name, function_identifier, parameters, \
                              closure_variables, user_variables, default_access_identifiers,
                              tmp_variables, function_codes, needs_creation, source_ref, \
                              function_doc ):
    # We really need this many parameters here.
    # pylint: disable=R0913

    parameter_variables, entry_point_code, parameter_objects_decl, mparse_identifier = getParameterParsingCode(
        function_identifier     = function_identifier,
        function_name           = function_name,
        parameters              = parameters,
        default_identifiers     = default_access_identifiers,
        context_access_template = CodeTemplates.generator_context_access_template,
        needs_creation          = needs_creation,
        context                 = context,
    )

    context_decl, context_copy, context_free = getParameterContextCode(
        default_access_identifiers = default_access_identifiers
    )

    function_parameter_decl = [
        _getLocalVariableInitCode(
            context    = context,
            variable   = variable,
            in_context = True
        )
        for variable in
        parameter_variables
    ]

    parameter_context_assign = []

    for variable in parameter_variables:
        parameter_context_assign.append(
            "_python_context->python_var_%s.setVariableNameAndValue( %s, _python_par_%s );" % (
                variable.getName(),
                getConstantCode(
                    constant = variable.getName(),
                    context = context
                ),
                variable.getName()
            )
        )

    function_var_inits = []
    local_var_decl = []

    for user_variable in user_variables:
        local_var_decl.append(
            _getLocalVariableInitCode(
                context    = context,
                variable   = user_variable,
                in_context = True
            )
        )
        function_var_inits.append(
            "_python_context->python_var_%s.setVariableName( %s );" % (
                user_variable.getName(),
                getConstantCode(
                    constant = user_variable.getName(),
                    context  = context
                )
            )
        )

    # These are for keeping values during evaluation of comparison chains.
    function_var_inits += [
        "PyObjectTempHolder %s;" % tmp_variable
        for tmp_variable in tmp_variables
    ]

    for closure_variable in closure_variables:
        assert closure_variable.isShared()

        context_decl.append(
            _getLocalVariableInitCode(
                context    = context,
                variable   = closure_variable,
                in_context = True
            )
        )
        context_copy.append(
            "_python_context->python_closure_%s.shareWith( python_closure_%s );" % (
                closure_variable.getName(),
                closure_variable.getName()
            )
        )

    function_creation_args  = _getFunctionCreationArgs(
        default_identifiers = default_access_identifiers,
        closure_variables   = closure_variables
    )

    function_doc = getConstantCode(
        context  = context,
        constant = function_doc
    )

    function_name_obj = getConstantCode(
        constant = function_name,
        context  = context,
    )

    instance_context_decl = function_parameter_decl + local_var_decl

    if not needs_creation:
        instance_context_decl = context_decl + instance_context_decl
        context_decl = []

    if context_decl:
        result = CodeTemplates.genfunc_context_body_template % {
            "function_identifier"            : function_identifier,
            "function_common_context_decl"   : indented( context_decl ),
            "function_instance_context_decl" : indented( instance_context_decl ),
            "context_free"                   : indented( context_free, 2 ),
        }
    elif instance_context_decl:
        result = CodeTemplates.genfunc_context_local_only_template % {
            "function_identifier"            : function_identifier,
            "function_instance_context_decl" : indented( instance_context_decl )
        }
    else:
        result = ""

    if instance_context_decl or context_decl:
        context_access_instance = CodeTemplates.generator_context_access_template2  % {
            "function_identifier" : function_identifier
        }
    else:
        context_access_instance = ""

    function_locals = []

    if context.needsFrameExceptionKeeper():
        function_locals += CodeTemplates.frame_exceptionkeeper_setup.split( "\n" )

    if context.hasLocalsDict():
        function_locals += CodeTemplates.function_dict_setup.split( "\n" )

    function_locals += function_var_inits

    result += CodeTemplates.genfunc_yielder_template % {
        "function_identifier" : function_identifier,
        "function_body"       : indented( function_codes, 2 ),
        "function_var_inits"  : indented( function_locals, 2 ),
        "context_access"      : indented( context_access_instance, 2 ),
    }

    code_identifier = context.getCodeObjectHandle(
        filename     = source_ref.getFilename(),
        arg_names    = parameters.getCoArgNames(),
        line_number  = source_ref.getLineNumber(),
        code_name    = function_name,
        is_generator = True
    )

    if context_decl or instance_context_decl:
        if context_decl:
            context_making = CodeTemplates.genfunc_common_context_use_template % {
                "function_identifier"        : function_identifier,
            }
        else:
            context_making = CodeTemplates.genfunc_local_context_use_template  % {
                "function_identifier"        : function_identifier,
            }

        context_making = context_making.split( "\n" )

        if not needs_creation:
            context_making += context_copy

        generator_making = CodeTemplates.genfunc_generator_with_context_making  % {
            "function_name_obj"   : function_name_obj,
            "function_identifier" : function_identifier,
            "code_identifier"     : code_identifier.getCodeTemporaryRef()
        }
    else:
        generator_making = CodeTemplates.genfunc_generator_without_context_making  % {
            "function_name_obj"   : function_name_obj,
            "function_identifier" : function_identifier,
            "code_identifier"     : code_identifier.getCodeTemporaryRef()
        }

        context_making = []

    if not needs_creation:
        for closure_variable in closure_variables:
            parameter_objects_decl.append(
                closure_variable.getDeclarationCode(
                    for_reference = True,
                    for_local     = False
                )
            )

    result += CodeTemplates.genfunc_function_maker_template % {
        "function_name"              : function_name,
        "function_identifier"        : function_identifier,
        "context_making"             : indented( context_making, 1 ),
        "context_copy"               : indented( parameter_context_assign, 2 ),
        "generator_making"           : generator_making,
        "parameter_objects_decl"     : ", ".join( parameter_objects_decl ),
    }

    func_defaults = _getFuncDefaultValue(
        identifiers = default_access_identifiers,
        context     = context
    )

    if needs_creation:
        result += entry_point_code

        if context_decl:
            result += CodeTemplates.make_genfunc_with_context_template % {
                "function_name_obj"          : getConstantCode(
                    context  = context,
                    constant = function_name
                ),
                "function_identifier"        : function_identifier,
                "fparse_function_identifier" : getParameterEntryPointIdentifier(
                    function_identifier = function_identifier,
                    is_method           = False
                ),
                "mparse_function_identifier" : mparse_identifier,
                "code_identifier"            : code_identifier.getCodeTemporaryRef(),
                "function_creation_args"     : getEvalOrderedCode(
                    context = context,
                    args    = function_creation_args
                ),
                "context_copy"               : indented( context_copy ),
                "function_doc"               : function_doc,
                "defaults"                   : func_defaults.getCodeExportRef(),
                "module_identifier"          : getModuleAccessCode(
                    context = context
                )
            }
        else:
            result += CodeTemplates.make_genfunc_without_context_template % {
                "function_name_obj"          : getConstantCode(
                    context  = context,
                    constant = function_name
                ),
                "function_identifier"        : function_identifier,
                "fparse_function_identifier" : getParameterEntryPointIdentifier(
                    function_identifier = function_identifier,
                    is_method           = False
                ),
                "mparse_function_identifier" : mparse_identifier,
                "code_identifier"            : code_identifier.getCodeTemporaryRef(),
                "function_creation_args"     : getEvalOrderedCode(
                    context = context,
                    args    = function_creation_args
                ),
                "function_doc"               : function_doc,
                "defaults"                   : func_defaults.getCodeExportRef(),
                "module_identifier"          : getModuleAccessCode(
                    context = context
                ),
            }

    return result

def getFunctionCode( context, function_name, function_identifier, parameters, closure_variables, \
                     user_variables, tmp_variables, default_access_identifiers, \
                     function_codes, needs_creation, source_ref, function_doc ):
    # We really need this many parameters here.
    # pylint: disable=R0913

    parameter_variables, entry_point_code, parameter_objects_decl, mparse_identifier = getParameterParsingCode(
        function_identifier     = function_identifier,
        function_name           = function_name,
        parameters              = parameters,
        default_identifiers     = default_access_identifiers,
        context_access_template = CodeTemplates.function_context_access_template,
        needs_creation          = needs_creation,
        context                 = context,
    )

    context_decl, context_copy, context_free = getParameterContextCode(
        default_access_identifiers = default_access_identifiers
    )

    function_parameter_decl = [
        _getLocalVariableInitCode(
            context   = context,
            variable  = variable,
            init_from = Identifier( "_python_par_" + variable.getName(), 1 )
        )
        for variable in
        parameter_variables
    ]

    for closure_variable in closure_variables:
        context_decl.append(
            _getLocalVariableInitCode(
                context    = context,
                variable   = closure_variable,
                in_context = True
            )
        )

        context_copy.append(
            "_python_context->python_closure_%s.shareWith( python_closure_%s );" % (
                closure_variable.getName(),
                closure_variable.getName()
            )
        )

    function_creation_args = _getFunctionCreationArgs(
        default_identifiers = default_access_identifiers,
        closure_variables   = closure_variables,
    )

    # User local variable initializations
    local_var_inits = [
        _getLocalVariableInitCode(
            context  = context,
            variable = variable
        )
        for variable in
        user_variables
    ]

    local_var_inits += [
        "PyObjectTempHolder %s;" % tmp_variable
        for tmp_variable in tmp_variables
    ]

    function_doc = getConstantCode(
        context  = context,
        constant = function_doc
    )

    function_locals = function_parameter_decl + local_var_inits

    if context.hasLocalsDict():
        function_locals = CodeTemplates.function_dict_setup.split("\n") + function_locals

    if context.needsFrameExceptionKeeper():
        function_locals = CodeTemplates.frame_exceptionkeeper_setup.split("\n") + function_locals

    result = ""

    if context_decl and needs_creation:
        result += CodeTemplates.function_context_body_template % {
            "function_identifier" : function_identifier,
            "context_decl"        : indented( context_decl ),
            "context_free"        : indented( context_free ),
        }

    if closure_variables and needs_creation:
        context_access_function_impl = CodeTemplates.function_context_access_template % {
            "function_identifier" : function_identifier,
        }
    else:
        context_access_function_impl = str( CodeTemplates.function_context_unused_template )

    if not needs_creation:
        for closure_variable in closure_variables:
            parameter_objects_decl.append(
                closure_variable.getDeclarationCode(
                    for_reference = True,
                    for_local     = False
                )
            )

    if context.function.isClassDictCreation():
        parameter_objects_decl = [ "PyObject *metaclass", "PyObject *bases" ] + parameter_objects_decl

    function_name_obj = getConstantCode(
        context  = context,
        constant = function_name
    )

    result += CodeTemplates.function_body_template % {
        "function_identifier"          : function_identifier,
        "context_access_function_impl" : context_access_function_impl,
        "parameter_objects_decl"       : ", ".join( parameter_objects_decl ),
        "function_locals"              : indented( function_locals ),
        "function_body"                : indented( function_codes ),
    }

    if needs_creation:
        result += entry_point_code

    func_defaults = _getFuncDefaultValue(
        identifiers = default_access_identifiers,
        context     = context
    )

    if needs_creation:
        code_identifier = context.getCodeObjectHandle(
            filename     = source_ref.getFilename(),
            arg_names    = parameters.getCoArgNames(),
            line_number  = source_ref.getLineNumber(),
            code_name    = function_name,
            is_generator = False
        )

        if context_decl:
            result += CodeTemplates.make_function_with_context_template % {
                "function_name_obj"          : function_name_obj,
                "function_identifier"        : function_identifier,
                "fparse_function_identifier" : getParameterEntryPointIdentifier(
                    function_identifier = function_identifier,
                    is_method           = False
                ),
                "mparse_function_identifier" : mparse_identifier,
                "function_creation_args"     : getEvalOrderedCode(
                    context = context,
                    args    = function_creation_args
                ),
                "code_identifier"            : code_identifier.getCodeTemporaryRef(),
                "context_copy"               : indented( context_copy ),
                "function_doc"               : function_doc,
                "defaults"                   : func_defaults.getCodeExportRef(),
                "module_identifier"          : getModuleAccessCode( context = context ),
            }
        else:
            result += CodeTemplates.make_function_without_context_template % {
                "function_name_obj"          : function_name_obj,
                "function_identifier"        : function_identifier,
                "fparse_function_identifier" : getParameterEntryPointIdentifier(
                    function_identifier = function_identifier,
                    is_method           = False
                ),
                "code_identifier"            : code_identifier.getCodeTemporaryRef(),
                "mparse_function_identifier" : mparse_identifier,
                "function_doc"               : function_doc,
                "defaults"                   : func_defaults.getCodeExportRef(),
                "module_identifier"          : getModuleAccessCode( context = context ),
            }

    return result


def getMetaclassAccessCode( context ):
    return Identifier( "metaclass", 0 )

def getBasesAccessCode( context ):
    return Identifier( "bases", 0 )

def getClassCreationCode( metaclass_global_code, metaclass_class_code, \
                          name_identifier, dict_identifier, bases_identifier ):
    args = (
        metaclass_global_code,
        metaclass_class_code.getCodeTemporaryRef() if metaclass_class_code is not None else "NULL",
        name_identifier.getCodeTemporaryRef(),
        bases_identifier.getCodeTemporaryRef(),
        dict_identifier.getCodeTemporaryRef()
    )

    return Identifier(
        "MAKE_CLASS( %s )" % (
            ", ".join( args )
        ),
        1
    )

def getRawStringLiteralCode( value ):
    return CppRawStrings.encodeString( value )

def getStatementTrace( source_desc, statement_repr ):
    return 'puts( "Execute: %s " %s );' % (
        source_desc,
        getRawStringLiteralCode( statement_repr )
    )


def _getConstantsDeclarationCode( context, for_header ):
    statements = []

    for _code_object_key, code_identifier in context.getCodeObjects():
        declaration = "PyCodeObject *%s;" % code_identifier.getCode()

        if for_header:
            declaration = "extern " + declaration

        statements.append( declaration )

    for _constant_desc, constant_identifier in context.getConstants():
        declaration = "PyObject *%s;" % constant_identifier

        if for_header:
            declaration = "extern " + declaration

        statements.append( declaration )

    return "\n".join( statements )

# TODO: The determation of this should already happen in TreeBuilding or in a helper not
# during code generation.
_match_attribute_names = re.compile( r"[a-zA-Z_][a-zA-Z0-9_]*$" )

def _isAttributeName( value ):
    return _match_attribute_names.match( value )

def _getUnstreamCode( constant_value, constant_identifier ):
    saved = getStreamedConstant(
        constant_value = constant_value
    )

    return "%s = UNSTREAM_CONSTANT( %s, %d );" % (
        constant_identifier,
        CppRawStrings.encodeString( saved ),
        len( saved )
    )

def _getConstantsDefinitionCode( context ):
    # There are many cases for constants to be created in the most efficient way,
    # pylint: disable=R0912

    statements = []

    for constant_desc, constant_identifier in context.getConstants():
        constant_type, constant_value = constant_desc
        constant_value = constant_value.getConstant()

        # Use shortest code for ints and longs, except when they are big, then fall
        # fallback to pickling.
        if constant_type is int and abs( constant_value ) < 2**31:
            statements.append(
                "%s = PyInt_FromLong( %s );" % (
                    constant_identifier,
                    constant_value
                )
            )

            continue

        if constant_type is long and abs( constant_value ) < 2**31:
            statements.append(
                "%s = PyLong_FromLong( %s );" % (
                    constant_identifier,
                    constant_value
                )
            )

            continue

        if constant_type is dict and constant_value == {}:
            statements.append(
                "%s = PyDict_New();" % constant_identifier
            )

            continue

        if constant_type is tuple and constant_value == ():
            statements.append(
                "%s = PyTuple_New( 0 );" % constant_identifier
            )

            continue

        if constant_type is list and constant_value == []:
            statements.append(
                "%s = PyList_New( 0 );" % constant_identifier
            )

            continue

        if constant_type is set and constant_value == set():
            statements.append(
                "%s = PySet_New( NULL );" % constant_identifier
            )

            continue

        if constant_type is str:
            statements.append(
                '%s = UNSTREAM_STRING( %s, %d, %d );assert( %s );' % (
                    constant_identifier,
                    CppRawStrings.encodeString( constant_value ),
                    len(constant_value),
                    1 if _isAttributeName( constant_value ) else 0,
                    constant_identifier
                )
            )

            continue

        if constant_value is None:
            continue

        if constant_value is False:
            continue

        if constant_value is True:
            continue

        if constant_type in ( tuple, list, float, complex, unicode, int, long, dict, frozenset, set, bytes, range ):
            statements.append(
                _getUnstreamCode( constant_value, constant_identifier )
            )

            continue

        assert False, (type(constant_value), constant_value, constant_identifier)

    for code_object_key, code_identifier in context.getCodeObjects():
        code = "%s = MAKE_CODEOBJ( %s, %s, %d, %s, %d, %s );" % (
            code_identifier.getCode(),
            getConstantCode(
                constant = code_object_key[0],
                context  = context
            ),
            getConstantCode(
                constant = code_object_key[1],
                context  = context
            ),
            code_object_key[2],
            getConstantCode(
                constant = code_object_key[3],
                context  = context
            ),
            len( code_object_key[3] ),
            "true" if code_object_key[4] else "false"
        )

        statements.append( code )

    return indented( statements )

def getReversionMacrosCode( context ):
    reverse_macros = []
    noreverse_macros = []

    for value in sorted( context.getEvalOrdersUsed() ):
        assert type( value ) is int

        reverse_macro = CodeTemplates.template_reverse_macro % {
            "count"    : value,
            "args"     : ", ".join(
                "arg%s" % (d+1) for d in range( value )
            ),
            "expanded" : ", ".join(
                "arg%s" % (d+1) for d in reversed( range( value ) )
            )
        }

        reverse_macros.append( reverse_macro.rstrip() )

        noreverse_macro = CodeTemplates.template_noreverse_macro % {
            "count"    : value,
            "args"     : ", ".join(
                "arg%s" % (d+1) for d in range( value )
            )
        }

        noreverse_macros.append( noreverse_macro.rstrip() )

    reverse_macros_declaration = CodeTemplates.template_reverse_macros_declaration % {
        "reverse_macros"   : "\n".join( reverse_macros ),
        "noreverse_macros" : "\n".join( noreverse_macros )
    }

    return CodeTemplates.template_header_guard % {
        "header_guard_name" : "__NUITKA_REVERSES_H__",
        "header_body"       : reverse_macros_declaration
    }

def getMakeTuplesCode( context ):
    make_tuples_codes = []

    for arg_count in context.getMakeTuplesUsed():
        add_elements_code = []

        for arg_index in range( arg_count ):
            add_elements_code.append(
                CodeTemplates.template_add_tuple_element_code % {
                    "tuple_index" : arg_index,
                    "tuple_value" : "element%d" % arg_index
                }
            )

        make_tuples_codes.append(
            CodeTemplates.template_make_tuple_function % {
                "argument_count"             : arg_count,
                "args"                       : ", ".join(
                    "arg%s" % (arg_index+1) for arg_index in range( arg_count )
                ),
                "argument_decl"              : ", ".join(
                    "PyObject *element%d" % arg_index
                    for arg_index in
                    range( arg_count )
                ),
                "add_elements_code"          : "\n".join( add_elements_code ),
            }
        )

    return CodeTemplates.template_header_guard % {
        "header_guard_name" : "__NUITKA_TUPLES_H__",
        "header_body"       : "\n".join( make_tuples_codes )
    }

def getMakeListsCode( context ):
    make_lists_codes = []

    for arg_count in context.getMakeListsUsed():
        add_elements_code = []

        for arg_index in range( arg_count ):
            add_elements_code.append(
                CodeTemplates.template_add_list_element_code % {
                    "list_index" : arg_index,
                    "list_value" : "element%d" % arg_index
                }
            )

        make_lists_codes.append(
            CodeTemplates.template_make_list_function % {
                "argument_count"             : arg_count,
                "args"                       : ", ".join(
                    "arg%s" % (arg_index+1) for arg_index in range( arg_count )
                ),
                "argument_decl"              : ", ".join(
                    "PyObject *element%d" % arg_index
                    for arg_index in
                    range( arg_count )
                ),
                "add_elements_code"          : "\n".join( add_elements_code ),
            }
        )

    return CodeTemplates.template_header_guard % {
        "header_guard_name" : "__NUITKA_LISTS_H__",
        "header_body"       : "\n".join( make_lists_codes )
    }

def getMakeDictsCode( context ):
    make_dicts_codes = []

    for arg_count in context.getMakeDictsUsed():
        add_elements_code = []

        for arg_index in range( arg_count ):
            add_elements_code.append(
                CodeTemplates.template_add_dict_element_code % {
                    "dict_key"   : "key%d" % ( arg_index + 1 ),
                    "dict_value" : "value%d" % ( arg_index + 1 )
                }
            )

        make_dicts_codes.append(
            CodeTemplates.template_make_dict_function % {
                "pair_count"                 : arg_count,
                "argument_count"             : arg_count * 2,
                "args"                       : ", ".join(
                    "value%(index)d, key%(index)d" % { "index" : (arg_index+1) }
                    for arg_index in
                    range( arg_count )
                ),
                "argument_decl"              : ", ".join(
                    "PyObject *value%(index)d, PyObject *key%(index)d" % { "index" : (arg_index+1) }
                    for arg_index in
                    range( arg_count )
                ),
                "add_elements_code"          : "\n".join( add_elements_code ),
            }
        )

    return CodeTemplates.template_header_guard % {
        "header_guard_name" : "__NUITKA_DICTS_H__",
        "header_body"       : "\n".join( make_dicts_codes )
    }

def getConstantsDeclarationCode( context ):
    constants_declarations = CodeTemplates.template_constants_declaration % {
        "constant_declarations" : _getConstantsDeclarationCode(
            context    = context,
            for_header = True
        ),
    }

    return CodeTemplates.template_header_guard % {
        "header_guard_name" : "__NUITKA_DECLARATIONS_H__",
        "header_body"       : constants_declarations
    }

def getConstantsDefinitionCode( context ):
    return CodeTemplates.template_constants_reading % {
        "constant_inits"        : _getConstantsDefinitionCode(
            context    = context
        ),
        "constant_declarations" : _getConstantsDeclarationCode(
            context    = context,
            for_header = False
        )
    }

def getDefaultValueAccess( variable ):
    if variable.isNestedParameterVariable():
        default_access_identifier = DefaultValueIdentifier(
            var_name = "__".join( variable.getParameterNames() ),
            nested   = True
        )
    else:
        default_access_identifier = DefaultValueIdentifier(
            var_name = variable.getName(),
            nested   = False
        )

    return default_access_identifier

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

def getListOperationAppendCode( list_identifier, value_identifier ):
    return Identifier(
        "APPEND_TO_LIST( %s, %s ), Py_None" % (
            list_identifier.getCodeTemporaryRef(),
            value_identifier.getCodeTemporaryRef()
        ),
        0
    )

def getSetOperationAddCode( set_identifier, value_identifier ):
    return Identifier(
        "ADD_TO_SET( %s, %s ), Py_None" % (
            set_identifier.getCodeTemporaryRef(),
            value_identifier.getCodeTemporaryRef()
        ),
        0
    )

def getDictOperationSetCode( dict_identifier, key_identifier, value_identifier ):
    return Identifier(
        "DICT_SET_ITEM( %s, %s, %s ), Py_None" % (
            dict_identifier.getCodeTemporaryRef(),
            key_identifier.getCodeTemporaryRef(),
            value_identifier.getCodeTemporaryRef()
        ),
        0
    )

def getFrameGuardHeavyCode( frame_identifier, code_identifier, codes, is_class, context ):
    return CodeTemplates.frame_guard_full_template % {
        "frame_identifier"  : frame_identifier,
        "code_identifier"   : code_identifier.getCodeTemporaryRef(),
        "codes"             : indented( codes ),
        "module_identifier" : getModuleAccessCode( context = context ),
        "return_code"       : CodeTemplates.frame_guard_cpp_return if is_class else CodeTemplates.frame_guard_python_return
    }

def getFrameGuardLightCode( frame_identifier, code_identifier, codes, context ):
    return CodeTemplates.frame_guard_genfunc_template % {
        "frame_identifier"  : frame_identifier,
        "code_identifier"   : code_identifier.getCodeTemporaryRef(),
        "codes"             : indented( codes ),
        "module_identifier" : getModuleAccessCode( context = context ),
    }

def getFrameGuardVeryLightCode( codes ):
    return CodeTemplates.frame_guard_listcontr_template % {
        "codes"             : indented( codes, 0 ),
    }
