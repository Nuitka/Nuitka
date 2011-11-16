#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Generator for C++ and Python C/API.

This is the actual C++ code generator. It has methods and should be the only place to know
what C++ is like. Ideally it would be possible to replace the target language by changing
this one and the templates, and otherwise nothing else.

"""


from .Identifiers import (
    Identifier,
    ModuleVariableIdentifier,
    HolderVariableIdentifier,
    TempVariableIdentifier,
    DefaultValueIdentifier,
    ReversedCallIdentifier,
    CallIdentifier,
    getCodeTemporaryRefs,
    getCodeExportRefs
)

from .Indentation import indented

from .Pickling import getStreamedConstant

from .OrderedEvaluation import getEvalOrderedCode

from .ConstantCodes import getConstantHandle, getConstantCode
from .VariableCodes import getVariableHandle, getVariableCode

from .ParameterParsing import (
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
    Options
)

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

def getReturnCode( identifier ):
    if identifier is not None:
        return "return %s;" % identifier.getCodeExportRef()
    else:
        return "return;"

def getYieldCode( identifier, for_return ):
    if not for_return:
        return Identifier(
            "YIELD_VALUE( generator, %s )" % identifier.getCodeExportRef(),
            0
        )
    else:
        return Identifier(
            "YIELD_RETURN( generator, %s )" % identifier.getCodeExportRef(),
            0
        )

def getYieldTerminatorCode():
    return "throw ReturnException();"

def getSequenceCreationCode( context, sequence_kind, element_identifiers ):
    assert sequence_kind in ( "tuple", "list" )

    # Disallow building the empty tuple with this assertion, we want users to not let
    # us here optimize it away.
    assert sequence_kind != "list" or element_identifiers

    if sequence_kind == "tuple":
        arg_codes = getCodeTemporaryRefs( element_identifiers )
    else:
        arg_codes = getCodeExportRefs( element_identifiers )

    return ReversedCallIdentifier(
        context = context,
        called  = "MAKE_%s" % sequence_kind.upper(),
        args    = arg_codes
    )

def getDictionaryCreationCode( context, keys, values ):
    key_codes = getCodeTemporaryRefs( keys )
    value_codes = getCodeTemporaryRefs( values )

    arg_codes = []

    # Strange as it is, CPython evalutes the key/value pairs strictly in order, but for
    # each pair, the value first.
    for key_code, value_code in zip( key_codes, value_codes ):
        arg_codes.append( value_code )
        arg_codes.append( key_code )

    return ReversedCallIdentifier(
        context = context,
        called  = "MAKE_DICT",
        args    = arg_codes
    )

def getSetCreationCode( values ):
    arg_codes = getCodeTemporaryRefs( values )

    return Identifier(
        "MAKE_SET( %s )" % ( ", ".join( reversed( arg_codes ) ) ),
        1
    )

def getPackageVariableCode( context ):
    package_var_identifier = ModuleVariableIdentifier(
        var_name         = "__package__",
        module_code_name = context.getModuleCodeName()
    )

    return "( %s.isInitialized( false ) ? %s : NULL )" % (
        package_var_identifier.getCode(),
        package_var_identifier.getCodeTemporaryRef()
    )

def getImportModuleCode( context, module_name, globals_dict, locals_dict, import_list, level ):
    return Identifier(
        "IMPORT_MODULE( %s, %s, %s, %s, %s )" % (
            getConstantCode(
                constant = module_name,
                context  = context
            ),
            globals_dict.getCodeTemporaryRef(),
            locals_dict.getCodeTemporaryRef(),
            getConstantCode(
                constant = import_list,
                context  = context
            ),
            getConstantCode(
                constant = level,
                context  = context
            )
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

def _getFunctionCallNoStarArgsCode( function_identifier, argument_tuple, argument_dictionary ):
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

def _getFunctionCallListStarArgsCode( function_identifier, argument_tuple, argument_dictionary, star_list_identifier ):
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

def _getFunctionCallDictStarArgsCode( function_identifier, argument_tuple, argument_dictionary, star_dict_identifier ):
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

def _getFunctionCallBothStarArgsCode( function_identifier, argument_tuple, argument_dictionary, \
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


def getFunctionCallCode( function_identifier, argument_tuple, argument_dictionary, \
                         star_list_identifier, star_dict_identifier ):
    if star_dict_identifier is None:
        if star_list_identifier is None:
            return _getFunctionCallNoStarArgsCode(
                function_identifier = function_identifier,
                argument_tuple      = argument_tuple,
                argument_dictionary = argument_dictionary
            )
        else:
            return _getFunctionCallListStarArgsCode(
                function_identifier  = function_identifier,
                argument_tuple       = argument_tuple,
                argument_dictionary  = argument_dictionary,
                star_list_identifier = star_list_identifier
            )
    else:
        if star_list_identifier is not None:
            return _getFunctionCallBothStarArgsCode(
                function_identifier  = function_identifier,
                argument_tuple       = argument_tuple,
                argument_dictionary  = argument_dictionary,
                star_list_identifier = star_list_identifier,
                star_dict_identifier = star_dict_identifier
            )
        else:
            return _getFunctionCallDictStarArgsCode(
                function_identifier  = function_identifier,
                argument_tuple       = argument_tuple,
                argument_dictionary  = argument_dictionary,
                star_dict_identifier = star_dict_identifier
            )

def getIteratorCreationCode( iterated ):
    return Identifier(
        "MAKE_ITERATOR( %s )" % iterated.getCodeTemporaryRef(),
        1
    )

def getUnpackNextCode( iterator, element_count ):
    return Identifier(
        "UNPACK_NEXT( %s, %d )" % ( iterator.getCodeTemporaryRef(), element_count-1 ),
        1
    )

def getUnpackTupleCode( assign_source, iterator_identifier, lvalue_identifiers ):
    result = "PyObjectTemporary %s( %s );\n" % (
        iterator_identifier.getCode(),
        getIteratorCreationCode( iterated = assign_source ).getCodeExportRef()
    )

    for count, lvalue_identifier in enumerate( lvalue_identifiers ):
        result += "%s %s( %s );\n" % (
            lvalue_identifier.getClass(),
            lvalue_identifier.getCode(),
            getUnpackNextCode(
                iterator      = iterator_identifier,
                element_count = count+1
            ).getCodeExportRef()
        )

    result += "UNPACK_ITERATOR_CHECK( %s );\n" % iterator_identifier.getCodeTemporaryRef()

    return result

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

def getAttributeCheckCode( attribute, source ):
    return Identifier(
        "HAS_ATTRIBUTE( %s, %s )" % (
            source.getCodeTemporaryRef(),
            attribute.getCodeTemporaryRef()
        ),
        0
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
    if type( codes ) == str:
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
    elif operator == "Add":
        return Identifier(
            "BINARY_OPERATION_ADD( %s, %s )" % (
                identifier_refs[0],
                identifier_refs[1]
            ),
            1
        )
    elif operator == "Mul":
        return Identifier(
            "BINARY_OPERATION_MUL( %s, %s )" % (
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
        return Identifier(
            "UNARY_OPERATION( %s, %s )" % (
                OperatorCodes.unary_operator_codes[ operator ],
                identifier_refs[0]
            ),
            1
        )
    else:
        assert False, (operator, identifiers)

def getPrintCode( newline, identifiers, target_file ):
    print_elements_code = ""

    for identifier in identifiers:
        print_elements_code += CodeTemplates.template_print_value % {
            "print_value" : identifier.getCodeTemporaryRef()
        }

    if newline:
        print_elements_code += CodeTemplates.template_print_newline

    return CodeTemplates.template_print_statement % {
        "target_file"         : target_file.getCodeExportRef() if target_file is not None else "NULL",
        "print_elements_code" : print_elements_code
    }

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

def getContractionCallCode( is_genexpr, contraction_identifier, contraction_iterated, closure_var_codes ):
    args = [ contraction_iterated.getCodeTemporaryRef() ] + closure_var_codes

    return CallIdentifier(
        called  = "%s%s" % (
            "MAKE_FUNCTION_" if is_genexpr else "",
            contraction_identifier
        ),
        args    = args
    )

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

def getFunctionCreationCode( context, function_identifier, decorators, default_identifiers, closure_variables ):
    args = getCodeTemporaryRefs( decorators )

    args += getCodeExportRefs( default_identifiers )

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

def getComparisonExpressionCode( context, comparators, operands ):
    # There is an awful lot of cases, and it's not helped by the need to generate more
    # complex code in the case of comparison chains. pylint: disable=R0912

    if len( comparators ) == 1:
        comparator = comparators[0]

        left, right = operands

        if comparator in OperatorCodes.normal_comparison_codes:
            py_api = OperatorCodes.normal_comparison_codes[ comparator ]

            assert py_api.startswith( "SEQUENCE_CONTAINS" )

            comparison = Identifier(
                "%s( %s, %s )" % (
                    py_api,
                    left.getCodeTemporaryRef(),
                    right.getCodeTemporaryRef()
                ),
                0
            )
        elif comparator in OperatorCodes.rich_comparison_codes:
            comparison = Identifier(
                "RICH_COMPARE_%s( %s, %s )" % (
                    OperatorCodes.rich_comparison_codes[ comparator ],
                    left.getCodeTemporaryRef(),
                    right.getCodeTemporaryRef()
                ),
                1
            )
        elif comparator == "Is":
            comparison = Identifier(
                "BOOL_FROM( %s == %s )" % (
                    left.getCodeTemporaryRef(),
                    right.getCodeTemporaryRef()
                ),
                0
            )
        elif comparator == "IsNot":
            comparison = Identifier(
                "BOOL_FROM( %s != %s )" % (
                    left.getCodeTemporaryRef(),
                    right.getCodeTemporaryRef()
                ),
                0
            )
        else:
            assert False, comparator
    else:
        left_tmp = operands[0]

        comparison = ""

        for count, comparator in enumerate( comparators ):
            right_tmp = operands[ count + 1 ].getCodeTemporaryRef()

            if count < len( comparators ) - 1:
                temp_storage_var = context.getTempObjectVariable()

                right_tmp = "( %s = %s )" % (
                    temp_storage_var.getCode(),
                    right_tmp
                )

            if comparator in OperatorCodes.normal_comparison_codes:
                py_api = OperatorCodes.normal_comparison_codes[ comparator ]

                assert py_api.startswith( "SEQUENCE_CONTAINS" )

                chunk = "%s_BOOL( %s, %s )" % (
                    py_api,
                    left_tmp.getCodeTemporaryRef(),
                    right_tmp
                )
            elif comparator in OperatorCodes.rich_comparison_codes:
                chunk = "RICH_COMPARE_BOOL_%s( %s, %s )" % (
                    OperatorCodes.rich_comparison_codes[ comparator ],
                    left_tmp.getCodeTemporaryRef(),
                    right_tmp
                )
            elif comparator == "Is":
                chunk = "( %s == %s )" % (
                    left_tmp.getCodeTemporaryRef(),
                    right_tmp
                )
            elif comparator == "IsNot":
                chunk = "( %s != %s )" % (
                    left_tmp.getCodeTemporaryRef(),
                    right_tmp
                )
            else:
                assert False, comparator

            if comparison == "":
                comparison = chunk
            else:
                comparison = comparison + " && " + chunk

            if count < len( comparators ):
                left_tmp = temp_storage_var

        comparison = Identifier( "BOOL_FROM( %s )" % comparison, 0 )

    return comparison

def getComparisonExpressionBoolCode( context, comparators, operands ):
    # There is an awful lot of cases, and it's not helped by the need to generate more
    # complex code in the case of comparison chains. pylint: disable=R0912

    if len( comparators ) == 1:
        comparator = comparators[0]

        left, right = operands

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
    else:
        left_tmp = operands[0]

        comparison = ""

        for count, comparator in enumerate( comparators ):
            right_tmp = operands[ count + 1 ].getCodeTemporaryRef()

            if count < len( comparators ) - 1:
                temp_storage_var = context.getTempObjectVariable()

                right_tmp = "( %s = %s )" % (
                    temp_storage_var.getCode(),
                    right_tmp
                )

            if comparator in OperatorCodes.normal_comparison_codes:
                py_api = OperatorCodes.normal_comparison_codes[ comparator ]

                assert py_api.startswith( "SEQUENCE_CONTAINS" )

                chunk = "%s_BOOL( %s, %s )" % (
                    py_api,
                    left_tmp.getCodeTemporaryRef(),
                    right_tmp
                )
            elif comparator in OperatorCodes.rich_comparison_codes:
                chunk = "RICH_COMPARE_BOOL_%s( %s, %s )" % (
                    OperatorCodes.rich_comparison_codes[ comparator ],
                    left_tmp.getCodeTemporaryRef(),
                    right_tmp
                )
            elif comparator == "Is":
                chunk = "( %s == %s )" % (
                    left_tmp.getCodeTemporaryRef(),
                    right_tmp
                )
            elif comparator == "IsNot":
                chunk = "( %s != %s )" % (
                    left_tmp.getCodeTemporaryRef(),
                    right_tmp
                )
            else:
                assert False, comparator

            if comparison == "":
                comparison = chunk
            else:
                comparison = comparison + " && " + chunk

            if count < len( comparators ):
                left_tmp = temp_storage_var

        comparison = Identifier(
            "( %s )" % comparison,
            0
        )

    return comparison


def getConditionNotCode( condition ):
    return Identifier(
        "UNARY_NOT( %s )" % condition.getCodeTemporaryRef(),
        0
    )

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

def getWithNames( context ):
    with_count = context.allocateWithNumber()

    return (
        TempVariableIdentifier( "_python_with_context_%d" % with_count ),
        TempVariableIdentifier( "_python_with_value_%d" % with_count )
    )


def getWithCode( context, body_codes, assign_codes, source_identifier, with_manager_identifier, with_value_identifier ):

    traceback_name = context.getTracebackName()
    traceback_filename = context.getTracebackFilename()

    if assign_codes is None:
        assign_codes = "// No 'as' target variable for withed expression."

    frame_making = getFrameMakingIdentifier(
        context = context
    )

    return CodeTemplates.with_template % {
        "assign"              : indented( assign_codes ),
        "body"                : indented( body_codes, 2 ),
        "source"              : source_identifier.getCodeExportRef(),
        "manager"             : with_manager_identifier.getCode(),
        "value"               : with_value_identifier.getCode(),
        "with_count"          : context.with_count,
        "module_identifier"   : getModuleAccessCode( context = context ),
        "frame_making"        : frame_making.getCodeExportRef(),
        "triple_none_tuple"   : getConstantCode(
            constant = ( None, None, None ),
            context  = context
        ),
        "name_identifier"     : getConstantCode(
            constant = traceback_name,
            context = context
        ),
        "filename_identifier" : getConstantCode(
            context  = context,
            constant = traceback_filename
        ),
    }

def getForLoopNames( context ):
    for_count = context.allocateForLoopNumber()

    return (
        "_python_for_loop_iterator_%d" % for_count,
        "_python_for_loop_itervalue_%d" % for_count,
        "itertemp_%d" % for_count
    )

def getForLoopCode( context, line_number_code, iterator, iter_name, iter_value, iter_object, \
                    loop_var_code, loop_body_codes, loop_else_codes, needs_exceptions ):

    loop_body_codes = loop_body_codes if loop_body_codes is not None else ""
    loop_else_codes = loop_else_codes if loop_else_codes is not None else ""

    # TODO: Make this true
    # assert loop_else_codes or loop_body_codes

    for_loop_template = CodeTemplates.getForLoopTemplate(
        needs_exceptions = needs_exceptions,
        has_else_codes   = loop_else_codes
    )


    indicator_name = "_python_for_loop_indicator_%d" % context.allocateForLoopNumber()

    return for_loop_template % {
        "body"                     : indented( loop_body_codes, 2 ),
        "else_codes"               : indented( loop_else_codes ),
        "iterator"                 : iterator.getCodeExportRef(),
        "line_number_code"         : line_number_code,
        "loop_iter_identifier"     : iter_name,
        "loop_value_identifier"    : iter_value,
        "loop_object_identifier"   : iter_object.getCode(),
        "loop_var_assignment_code" : indented( loop_var_code, 3 ),
        "indicator_name"           : indicator_name
    }

def getWhileLoopCode( context, condition, loop_body_codes, loop_else_codes, needs_exceptions ):
    while_loop_template = CodeTemplates.getWhileLoopTemplate(
        needs_exceptions = needs_exceptions,
        has_else_codes   = loop_else_codes
    )

    indicator_name = "_python_for_loop_indicator_%d" % context.allocateWhileLoopNumber()

    return while_loop_template % {
        "condition"       : condition.getCode(),
        "loop_body_codes" : indented( loop_body_codes if loop_body_codes is not None else "" ),
        "loop_else_codes" : indented( loop_else_codes if loop_else_codes is not None else "" ),
        "indicator_name"  : indicator_name
    }

def getVariableAssignmentCode( context, variable, identifier ):
    assert isinstance( variable, Variables.Variable ), variable

    if variable.isModuleVariable():
        var_name = variable.getName()

        context.addGlobalVariableNameUsage( var_name )

        if identifier.getCheapRefCount() == 0:
            return "_mvar_%s_%s.assign0( %s );" % (
                context.getModuleCodeName(),
                var_name,
                identifier.getCodeTemporaryRef()
            )
        else:
            return "_mvar_%s_%s.assign( %s );" % (
                context.getModuleCodeName(),
                var_name,
                identifier.getCodeExportRef()
            )
    elif variable.isMaybeLocalVariable():
        # TODO: This branch ought to be impossible to take, as an assignment to an overflow
        # variable would make it a local one.
        assert False, variable

        return getSubscriptAssignmentCode(
            subscribed = Identifier( "locals_dict.asObject()", 0 ),
            subscript  = getConstantCode(
                context  = context,
                constant = variable.getName(),

            ),
            identifier = identifier
        )
    else:
        return "%s = %s;" % (
            getVariableCode(
                variable = variable,
                context  = context
            ),
            identifier.getCodeExportRef()
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

def getVariableTestCode( context, variable ):
    assert isinstance( variable, Variables.Variable ), variable

    if variable.isModuleVariable():
        var_name = variable.getName()

        context.addGlobalVariableNameUsage( var_name )

        return "_mvar_%s_%s.isInitialized()" % (
            context.getModuleCodeName(),
            var_name
        )
    else:
        return "%s.isInitialized();" % getVariableCode(
            variable = variable,
            context = context
        )

def getSequenceElementCode( sequence, index ):
    return Identifier(
        "SEQUENCE_ELEMENT( %s, %d )" % (
            sequence.getCodeTemporaryRef(),
            index
        ),
        1
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

def _getInplaceOperationCode( operator, operand1, operand2 ):
    operator = OperatorCodes.inplace_operator_codes[ operator ]

    if operator == "PyNumber_InPlacePower":
        return Identifier(
            "POWER_OPERATION_INPLACE( %s, %s )" % (
                operand1.getCodeTemporaryRef(),
                operand2.getCodeTemporaryRef()
            ),
            1
        )
    else:
        return Identifier(
            "BINARY_OPERATION( %s, %s, %s )" % (
                operator,
                operand1.getCodeTemporaryRef(),
                operand2.getCodeTemporaryRef()
            ),
            1
        )

def getInplaceVarAssignmentCode( context, variable, operator, identifier ):
    value_identifier = Identifier( "value.asObject()", 0 )
    result_identifier = Identifier( "result", 0 )

    return CodeTemplates.template_inplace_var_assignment % {
        "assign_source_identifier" : getVariableHandle(
            variable = variable,
            context  = context
        ).getCodeExportRef(),
        "inplace_operation_code" : _getInplaceOperationCode(
            operator = operator,
            operand1 = value_identifier,
            operand2 = identifier
        ).getCode(),
        "assignment_code" : getVariableAssignmentCode(
            variable   = variable,
            context    = context,
            identifier = result_identifier
        )
    }


def getInplaceSubscriptAssignmentCode( subscribed, subscript, operator, identifier ):
    operation_identifier = _getInplaceOperationCode(
        operator = operator,
        operand1 = Identifier( "value.asObject()", 0 ),
        operand2 = identifier
    )

    return CodeTemplates.template_inplace_subscript_assignment % {
        "subscribed_identifier" : subscribed.getCodeExportRef(),
        "subscript_identifier"  : subscript.getCodeExportRef(),
        "operation_identifier"  : operation_identifier.getCode()
    }

def getInplaceAttributeAssignmentCode( target, attribute, operator, identifier ):
    operation_identifier = _getInplaceOperationCode(
        operator = operator,
        operand1 = Identifier( "value.asObject()", 0 ),
        operand2 = identifier
    )

    return CodeTemplates.template_inplace_attribute_assignment % {
        "target_identifier"    : target.getCodeExportRef(),
        "attribute_identifier" : attribute.getCodeTemporaryRef(),
        "operation_identifier" : operation_identifier.getCode()
    }

def getInplaceSliceAssignmentCode( target, lower, upper, operator, identifier ):
    operation_identifier = _getInplaceOperationCode(
        operator = operator,
        operand1 = Identifier( "value.asObject()", 0 ),
        operand2 = identifier
    )

    return CodeTemplates.template_inplace_slice_assignment % {
        "target_identifier"    : target.getCodeExportRef(),
        "lower"                : lower.getCode(),
        "upper"                : upper.getCode(),
        "operation_identifier" : operation_identifier.getCode()
    }

def getTryFinallyCode( context, code_tried, code_final ):
    return CodeTemplates.try_finally_template % {
        "try_count"  : context.allocateTryNumber(),
        "tried_code" : indented( code_tried ),
        "final_code" : indented( code_final, 0 )
    }

def getTryExceptHandlerCode( exception_identifier, exception_assignment, handler_code, \
                             first_handler ):
    exception_code = []

    cond_keyword = "if" if first_handler else "else if"

    if exception_identifier is not None:
        exception_code.append(
            "%s ( _exception.matches(%s) )" % (
                cond_keyword,
                exception_identifier.getCodeTemporaryRef()
            )
        )
    else:
        exception_code.append(
            "%s (true)" % cond_keyword
        )

    exception_code.append( "{" )
    exception_code.append( "    traceback = false;" )

    if exception_assignment is not None:
        exception_code.append(
            indented( exception_assignment, 1 )
        )

    exception_code += indented( handler_code or "", 1 ).split("\n")
    exception_code.append( "}" )

    return exception_code

def getTryExceptCode( context, code_tried, handler_codes, else_code ):
    exception_code = handler_codes
    exception_code += [ "else", "{", "    throw;", "}" ]

    tb_making = getTracebackMakingIdentifier( context, "_exception.getLine()" )

    if else_code is not None:
        return CodeTemplates.try_except_else_template % {
            "tried_code"     : indented( code_tried or "" ),
            "exception_code" : indented( exception_code ),
            "else_code"      : indented( else_code ),
            "tb_making"      : tb_making.getCodeExportRef(),
            "except_count"   : context.allocateTryNumber()
        }
    else:
        return CodeTemplates.try_except_template % {
            "tried_code"     : indented( code_tried or "" ),
            "exception_code" : indented( exception_code ),
            "tb_making"      : tb_making.getCodeExportRef(),
        }


def getRaiseExceptionCode( exception_type_identifier, exception_value_identifier, \
                           exception_tb_identifier, exception_tb_maker ):
    if exception_value_identifier is None and exception_tb_identifier is None:
        return "RAISE_EXCEPTION( &traceback, %s, %s );" % (
            exception_type_identifier.getCodeExportRef(),
            exception_tb_maker.getCodeExportRef()
        )
    elif exception_tb_identifier is None:
        return "RAISE_EXCEPTION( &traceback, %s, %s, %s );" % (
            exception_type_identifier.getCodeExportRef(),
            exception_value_identifier.getCodeExportRef(),
            exception_tb_maker.getCodeExportRef()
        )
    else:
        return "RAISE_EXCEPTION( &traceback, %s, %s, %s );" % (
            exception_type_identifier.getCodeExportRef(),
            exception_value_identifier.getCodeExportRef(),
            exception_tb_identifier.getCodeExportRef()
        )

def getReRaiseExceptionCode( local ):
    if local:
        return "throw;"
    else:
        return "traceback = true; RERAISE_EXCEPTION();"

def getRaiseExceptionExpressionCode( side_effects, exception_type_identifier, \
                                     exception_value_identifier, exception_tb_maker ):
    # TODO: Check out if the NUITKA_NO_RETURN avoids any temporary refcount to ever be
    # created or else avoid it with special identifier class that uses code for reference
    # counts 0 and both.

    result = Identifier(
        "THROW_EXCEPTION( %s, %s, %s, &traceback )" % (
            exception_type_identifier.getCodeExportRef(),
            exception_value_identifier.getCodeExportRef(),
            exception_tb_maker.getCodeExportRef()
        ),
        0
    )

    if side_effects:
        result = Identifier(
            "( %s, %s )" % (
                ", ".join( side_effect.getCodeTemporaryRef() for side_effect in side_effects ),
                result.getCodeTemporaryRef()
            ),
            0
        )

    return result

def getAssertCode( condition_identifier, failure_identifier, exception_tb_maker ):
    if failure_identifier is None:
        return CodeTemplates.assertion_without_arg % {
            "condition" : condition_identifier.getCode(),
            "tb_maker"  : exception_tb_maker.getCodeExportRef()
        }
    else:
        return CodeTemplates.assertion_with_arg % {
            "condition"   : condition_identifier.getCode(),
            "failure_arg" : failure_identifier.getCodeExportRef(),
            "tb_maker"    : exception_tb_maker.getCodeExportRef()
        }


def getExceptionRefCode( exception_type ):
    return Identifier(
        "PyExc_%s" % exception_type,
        0
    )

def getMakeExceptionCode( context, exception_type, exception_args ):
    return getFunctionCallCode(
        function_identifier = Identifier( "PyExc_%s" % exception_type, 0 ),
        argument_tuple      = getSequenceCreationCode(
            sequence_kind       = "tuple",
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
    else:
        variables = provider.getVariables()

    return [
        "&%s" % getVariableCode(
            variable = variable,
            context = context
        )
        for variable in
        variables
        if not variable.isModuleVariable()
        if not variable.isMaybeLocalVariable()
    ]


def getLoadDirCode( context, provider ):
    if provider.isModule():
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
                "PyDict_Keys( UPDATED_LOCALS_DICT( locals.asObject() %s )" % (
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
                "UPDATED_LOCALS_DICT( locals_dict.asObject() %s )" % (
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


def getEvalCode( context, exec_code, filename_identifier, globals_identifier, locals_identifier, mode_identifier, future_flags, provider ):
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

def getBuiltinRangeCode( low, high, step ):
    # TODO: Have an Identifier class that calls a helper with arguments.

    if step is not None:
        return Identifier(
            "BUILTIN_RANGE( %s, %s, %s )" % (
                low.getCodeTemporaryRef(),
                high.getCodeTemporaryRef(),
                step.getCodeTemporaryRef()
            ),
            1
        )
    elif high is not None:
        return Identifier(
            "BUILTIN_RANGE( %s, %s )" % (
                low.getCodeTemporaryRef(),
                high.getCodeTemporaryRef()
            ),
            1
        )
    else:
        return Identifier(
            "BUILTIN_RANGE( %s )" % (
                low.getCodeTemporaryRef()
            ),
            1
        )

def getBuiltinChrCode( value ):
    return Identifier( "CHR( %s )" % value.getCodeTemporaryRef(), 1 )

def getBuiltinOrdCode( value ):
    return Identifier( "ORD( %s )" % value.getCodeTemporaryRef(), 1 )

def getBuiltinType1Code( value ):
    return Identifier(
        "BUILTIN_TYPE1( %s )" % value.getCodeTemporaryRef(),
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
    return Identifier(
        "TO_TUPLE( %s )" % identifier.getCodeTemporaryRef(),
        1
    )

def getBuiltinListCode( identifier ):
    return Identifier(
        "TO_LIST( %s )" % identifier.getCodeTemporaryRef(),
        1
    )

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
    return Identifier(
        "TO_FLOAT( %s )" % identifier.getCodeTemporaryRef(),
        1
    )

def getBuiltinLongCode( context, identifier, base ):
    if identifier is None:
        identifier = getConstantHandle( context = context, constant = "0" )

    if base is None:
        return Identifier(
            "TO_LONG( %s )" % identifier.getCodeTemporaryRef(),
            1
        )
    else:
        return Identifier(
            "TO_LONG( %s, %s )" % (
                identifier.getCodeTemporaryRef(),
                base.getCodeTemporaryRef()
            ),
            1
        )
def getBuiltinIntCode( context, identifier, base ):
    if identifier is None:
        identifier = getConstantHandle( context = context, constant = "0" )

    if base is None:
        return Identifier(
            "TO_INT( %s )" % identifier.getCodeTemporaryRef(),
            1
        )
    else:
        return Identifier(
            "TO_INT( %s, %s )" % (
                identifier.getCodeTemporaryRef(),
                base.getCodeTemporaryRef()
            ),
            1
        )

def getBuiltinStrCode( identifier ):
    return Identifier(
        "TO_STR( %s )" % identifier.getCodeTemporaryRef(),
        1
    )

def getBuiltinUnicodeCode( identifier ):
    return Identifier(
        "TO_UNICODE( %s )" % identifier.getCodeTemporaryRef(),
        1
    )

def getBuiltinBoolCode( identifier ):
    return Identifier(
        "TO_BOOL( %s )" % identifier.getCodeTemporaryRef(),
        0
    )

def getModuleAccessCode( context ):
    return Identifier( "_module_%s" % context.getModuleCodeName(), 0 ).getCode()

def getFrameMakingIdentifier( context ):
    return context.getFrameHandle()

def getTracebackMakingIdentifier( context, line ):
    return Identifier(
        "MAKE_TRACEBACK( %s, %s )" % (
            getFrameMakingIdentifier( context = context ).getCodeExportRef(),
            line
        ),
        1
    )

def getModuleIdentifier( module_name ):
    return module_name.replace( ".", "__" ).replace( "-", "_" )

def getPackageIdentifier( module_name ):
    return module_name.replace( ".", "__" )

def getModuleCode( context, module_name, package_name, codes, doc_identifier, \
                   path_identifier, filename_identifier ):

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

    # Make sure that _python_str_angle_module is available to the template
    # context.getConstantHandle( constant = "<module>" )
    context.getConstantHandle( constant = "." )

    if package_name is None:
        module_inits = CodeTemplates.module_init_no_package_template % {
            "module_identifier"   : module_identifier,
            "filename_identifier" : filename_identifier.getCode(),
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
            "filename_identifier"     : filename_identifier.getCode(),
            "is_package"              : 0 if path_identifier is None else 1,
            "path_identifier"         : path_identifier.getCode() if path_identifier else "",
            "doc_identifier"          : doc_identifier.getCode(),
            "package_identifier"      : getPackageIdentifier( package_name )
        }

    local_expression_temp_inits = _getLocalExpressionTempsInitCode(
        context = context
    )

    if local_expression_temp_inits:
        local_expression_temp_inits += "\n"

    header = CodeTemplates.global_copyright % {
        "name"    : module_name,
        "version" : Options.getVersion()
    }

    module_code = CodeTemplates.module_body_template % {
        "module_name"           : module_name,
        "module_name_obj"       : getConstantCode(
            context  = context,
            constant = module_name if module_name != "__main__" else "<module>"
        ),
        "module_identifier"     : module_identifier,
        "module_functions_decl" : functions_decl,
        "module_functions_code" : functions_code,
        "module_globals"        : module_globals,
        "module_inits"          : module_inits,
        "filename_identifier"   : filename_identifier.getCode(),
        "module_code"           : indented( codes, 2 ),
        "expression_temp_decl"  : local_expression_temp_inits
    }

    return header + module_code

def getModuleDeclarationCode( module_name ):
    module_header_code = CodeTemplates.module_header_template % {
        "module_name"       : module_name,
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
        )
    }

    return codes + main_code


def getFunctionsCode( context ):
    result = ""

    for _code_name, ( _contraction_decl, contraction_code ) in sorted( context.getContractionsCodes().iteritems() ):
        result += contraction_code

    for _code_name, ( _function_decl, function_code ) in sorted( context.getFunctionsCodes().iteritems() ):
        result += function_code

    for _code_name, ( _class_decl, class_code ) in sorted( context.getClassesCodes().iteritems() ):
        result += class_code

    return result

def getFunctionsDecl( context ):
    result = ""

    for _code_name, ( contraction_decl, _contraction_code ) in sorted( context.getContractionsCodes().iteritems() ):
        result += contraction_decl

    for _code_name, ( function_decl, _function_code ) in sorted( context.getFunctionsCodes().iteritems() ):
        result += function_decl

    for _code_name, ( class_decl, _class_code ) in sorted( context.getClassesCodes().iteritems() ):
        result += class_decl

    return result

def _getContractionParameters( closure_variables ):
    contraction_parameters = [ "PyObject *iterated" ]

    for variable in closure_variables:
        assert variable.isClosureReference()

        contraction_parameters.append(
            _getClosureVariableDecl(
                variable     = variable
            )
        )

    return contraction_parameters

def getContractionDecl( context, contraction_identifier, closure_variables ):
    contraction_creation_arg_spec = _getContractionParameters(
        closure_variables = closure_variables
    )

    contraction_creation_arg_names = _extractArgNames( contraction_creation_arg_spec )

    return CodeTemplates.template_contraction_declaration % {
       "contraction_identifier"             : contraction_identifier,
       "contraction_creation_arg_spec"      : getEvalOrderedCode(
            context = context,
            args    = contraction_creation_arg_spec
        ),
        "contraction_creation_arg_names"    : ", ".join( contraction_creation_arg_names ),
        "contraction_creation_arg_reversal" : getEvalOrderedCode(
            context = context,
            args    = contraction_creation_arg_names
        )
    }

def getContractionCode( context, contraction_identifier, contraction_kind, loop_var_codes, \
                        contraction_code, contraction_conditions, contraction_iterateds, \
                        closure_variables, provided_variables ):

    if contraction_kind == "list":
        contraction_decl_template = CodeTemplates.list_contration_var_decl
        contraction_loop = CodeTemplates.list_contraction_loop_production % {
            "contraction_body" : contraction_code.getCodeTemporaryRef(),
        }
    elif contraction_kind == "set":
        contraction_decl_template = CodeTemplates.set_contration_var_decl
        contraction_loop = CodeTemplates.set_contraction_loop_production % {
            "contraction_body" : contraction_code.getCodeTemporaryRef(),
        }
    elif contraction_kind == "dict":
        contraction_decl_template = CodeTemplates.dict_contration_var_decl
        contraction_loop = CodeTemplates.dict_contraction_loop_production % {
            "key_identifier" : contraction_code[0].getCodeTemporaryRef(),
            "value_identifier" : contraction_code[1].getCodeTemporaryRef()
        }
    else:
        assert False, contraction_kind

    local_var_decl = []

    for variable in provided_variables:
        if not variable.isClosureReference() and not variable.isModuleVariable():
            local_var_decl.append(
                _getLocalVariableInitCode(
                    context    = context,
                    variable   = variable,
                    in_context = False
                )
            )

    contraction_iterateds.insert( 0, Identifier( "iterated", 0 ) )

    for count, ( contraction_condition, contraction_iterated, loop_var_code ) in enumerate (
        reversed( list( zip( contraction_conditions, contraction_iterateds, loop_var_codes ) ) )
    ):
        contraction_loop = CodeTemplates.contraction_loop_iterated % {
            "contraction_loop"         : contraction_loop,
            "iter_count"               : len( loop_var_codes ) - count,
            "iterated"                 : contraction_iterated.getCodeTemporaryRef(),
            "loop_var_assignment_code" : loop_var_code,
            "contraction_condition"    : contraction_condition.getCode()
        }

    contraction_var_decl = contraction_decl_template % {
        "local_var_decl" : indented( local_var_decl )
    }

    local_expression_temp_inits = _getLocalExpressionTempsInitCode(
        context = context
    )

    contraction_creation_arg_spec = _getContractionParameters(
        closure_variables = closure_variables
    )

    return CodeTemplates.contraction_code_template % {
        "contraction_identifier" : contraction_identifier,
        "contraction_parameters" : getEvalOrderedCode(
            args    = contraction_creation_arg_spec,
            context = context
        ),
        "contraction_body"       : contraction_loop,
        "contraction_var_decl"   : indented( contraction_var_decl ),
        "contraction_temp_decl"  : indented( local_expression_temp_inits + "\n" if local_expression_temp_inits else "" )
    }

def getContractionIterValueIdentifier( context, index ):
    if not context.isGeneratorExpression():
        return Identifier( "_python_contraction_iter_value_%d" % index, 1 )
    else:
        return Identifier( "_python_genexpr_iter_value", 1 )

def _getFunctionCreationArgs( decorator_count, default_identifiers, closure_variables, is_genexpr ):
    if decorator_count:
        result = [
            "PyObject *decorator_%d" % ( d + 1 )
            for d in
            range( decorator_count )
        ]
    else:
        result = []

    if is_genexpr:
        result += [ "PyObject *iterator" ]


    result += getDefaultParameterDeclarations(
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


def getFunctionDecl( context, function_identifier, decorator_count, default_identifiers, closure_variables, is_genexpr ):
    function_creation_arg_spec = _getFunctionCreationArgs(
        decorator_count     = decorator_count,
        default_identifiers = default_identifiers,
        closure_variables   = closure_variables,
        is_genexpr          = is_genexpr
    )

    function_creation_arg_names = _extractArgNames( function_creation_arg_spec )

    return CodeTemplates.template_function_declaration % {
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

def _getLocalVariableInitCode( context, variable, init_from = None, needs_no_free = False, \
                               in_context = False, shared = False, mangle_name = None ):
    assert not variable.isModuleVariable()

    var_name = variable.getName()
    shared = shared or variable.isShared()

    if shared:
        result = "PyObjectSharedLocalVariable"
    elif init_from is not None and not needs_no_free:
        if variable.getHasDelIndicator():
            result = "PyObjectLocalParameterVariableWithDel"
        else:
            result = "PyObjectLocalParameterVariableNoDel"
    else:
        result = "PyObjectLocalVariable"

    def mangleName( name ):
        if mangle_name is None or not name.startswith( "__" ) or name.endswith( "__" ):
            return name
        else:
            return "_" + mangle_name + name

    store_name = mangleName( var_name )

    result += " "

    if not in_context:
        result += "_"

    if variable.isClosureReference():
        result += "python_closure_%s" % var_name
    else:
        result += "python_var_%s" % var_name

    if not in_context:
        result += "( "

        result += "%s" % getConstantCode(
            context  = context,
            constant = store_name
        )

        if init_from is not None:
            if context.hasLocalsDict():
                if needs_no_free:
                    result += ", INCREASE_REFCOUNT( %s )"  % init_from
                else:
                    result += ", %s" % init_from
            else:
                result += ", %s" % init_from

                if not needs_no_free:
                    if shared:
                        result += ", true"

        result += " )"

    result += ";"

    return result

def _getLocalExpressionTempsInitCode( context ):
    count = context.getTempObjectCounter()

    if count:
        return "PyObject *_expression_temps[ %d ];" % count
    else:
        return ""

def _getDecoratorsCallCode( context, decorator_count ):
    def _getCall( count ):
        return getFunctionCallCode(
            function_identifier  = Identifier( "decorator_%d" % count, 0 ),
            argument_tuple       = getSequenceCreationCode(
                sequence_kind       = "tuple",
                element_identifiers = [ Identifier( "result", 1 ) ],
                context             = context
            ),
            argument_dictionary  = Identifier( "NULL", 0 ),
            star_dict_identifier = None,
            star_list_identifier = None
        )

    decorator_calls = [
        "result = %s;" % _getCall( count + 1 ).getCode()
        for count in
        reversed( range( decorator_count ) )
    ]

    return decorator_calls


def getGeneratorFunctionCode( context, function_name, function_identifier, parameters, \
                              closure_variables, user_variables, decorator_count, \
                              default_access_identifiers, function_codes, source_ref, \
                              function_doc ):
    parameter_variables, entry_point_code, parameter_objects_decl, mparse_identifier = getParameterParsingCode(
        function_identifier     = function_identifier,
        function_name           = function_name,
        parameters              = parameters,
        default_identifiers     = default_access_identifiers,
        context_access_template = CodeTemplates.generator_context_access_template,
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
            "_python_context->python_var_%s.setVariableName( %s );" % (
                variable.getName(),
                getConstantCode(
                    constant = variable.getName(),
                    context = context
                )
            )
        )
        parameter_context_assign.append(
            "_python_context->python_var_%s = _python_par_%s;" % (
                variable.getName(),
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

    local_expression_temp_inits = _getLocalExpressionTempsInitCode(
        context = context
    )

    if local_expression_temp_inits:
        local_expression_temp_inits = [ local_expression_temp_inits ]
    else:
        local_expression_temp_inits = []

    for closure_variable in closure_variables:
        context_decl.append(
            _getLocalVariableInitCode(
                context    = context,
                variable   = closure_variable,
                in_context = True,
                shared     = True
            )
        )
        context_copy.append(
            "_python_context->python_closure_%s.shareWith( python_closure_%s );" % (
                closure_variable.getName(),
                closure_variable.getName()
            )
        )

    function_creation_args  = _getFunctionCreationArgs(
        decorator_count     = decorator_count,
        default_identifiers = default_access_identifiers,
        closure_variables   = closure_variables,
        is_genexpr          = False
    )

    function_decorator_calls = _getDecoratorsCallCode(
        context         = context,
        decorator_count = decorator_count
    )

    function_doc = getConstantCode(
        context  = context,
        constant = function_doc
    )

    function_name_obj = getConstantCode(
        constant = function_name,
        context  = context,
    )

    result = CodeTemplates.genfunc_context_body_template % {
        "function_identifier"            : function_identifier,
        "function_common_context_decl"   : indented( context_decl ),
        "function_instance_context_decl" : indented( function_parameter_decl + local_var_decl ),
        "context_free"                   : indented( context_free, 2 ),
    }

    if closure_variables or user_variables or parameter_variables:
        context_access_instance = CodeTemplates.generator_context_access_template2  % {
            "function_identifier" : function_identifier
        }
    else:
        context_access_instance = ""

    function_locals = function_var_inits + local_expression_temp_inits

    if context.hasLocalsDict():
        function_locals = CodeTemplates.function_dict_setup.split("\n") + function_locals

    if context.needsFrameExceptionKeeper():
        function_locals = CodeTemplates.frame_exceptionkeeper_setup.split("\n") + function_locals

    result += CodeTemplates.genfunc_yielder_template % {
        "function_name"       : function_name,
        "function_name_obj"   : function_name_obj,
        "function_identifier" : function_identifier,
        "function_body"       : indented( function_codes, 2 ),
        "function_var_inits"  : indented( function_locals, 2 ),
        "context_access"      : indented( context_access_instance, 2 ),
        "module_identifier"   : getModuleAccessCode( context = context ),
        "name_identifier"     : getConstantCode(
            context  = context,
            constant = function_name
        ),
        "filename_identifier" : getConstantCode(
            context  = context,
            constant = source_ref.getFilename()
        )
    }

    result += CodeTemplates.genfunc_function_template % {
        "function_name"              : function_name,
        "function_name_obj"          : function_name_obj,
        "function_identifier"        : function_identifier,
        "fparse_identifier"          : getParameterEntryPointIdentifier(
            function_identifier = function_identifier,
            is_method           = False
        ),
        "mparse_identifier"          : mparse_identifier,
        "parameter_context_assign"   : indented( parameter_context_assign, 2 ),
        "parameter_entry_point_code" : entry_point_code,
        "parameter_objects_decl"     : parameter_objects_decl,
        "context_copy"               : indented( context_copy ),
        "module_identifier"          : getModuleAccessCode( context = context )
    }

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
        "function_creation_args"     : getEvalOrderedCode(
            context = context,
            args    = function_creation_args
        ),
        "function_decorator_calls"   : indented( function_decorator_calls ),
        "context_copy"               : indented( context_copy ),
        "function_doc"               : function_doc,
        "filename_identifier"        : getConstantCode(
            context  = context,
            constant = source_ref.getFilename()
        ),
        "line_number"                : source_ref.getLineNumber(),
        "arg_count"                  : parameters.getArgumentCount(),
        "module_identifier"          : getModuleAccessCode( context = context ),
    }

    return result

def getFunctionCode( context, function_name, function_identifier, parameters, closure_variables, \
                     user_variables, decorator_count, default_access_identifiers, function_codes, \
                     source_ref, function_doc ):
    parameter_variables, entry_point_code, parameter_objects_decl, mparse_identifier = getParameterParsingCode(
        function_identifier     = function_identifier,
        function_name           = function_name,
        parameters              = parameters,
        default_identifiers     = default_access_identifiers,
        context_access_template = CodeTemplates.function_context_access_template,
        context                 = context,
    )

    context_decl, context_copy, context_free = getParameterContextCode(
        default_access_identifiers = default_access_identifiers
    )

    function_parameter_decl = [
        _getLocalVariableInitCode(
            context    = context,
            variable   = variable,
            in_context = False,
            init_from  = "_python_par_" + variable.getName()
        )
        for variable in
        parameter_variables
    ]

    for closure_variable in closure_variables:
        context_decl.append(
            "PyObjectSharedLocalVariable python_closure_%s;" % closure_variable.getName()
        )
        context_copy.append(
            "_python_context->python_closure_%s.shareWith( python_closure_%s );" % (
                closure_variable.getName(),
                closure_variable.getName()
            )
        )

    function_creation_args = _getFunctionCreationArgs(
        decorator_count     = decorator_count,
        closure_variables   = closure_variables,
        default_identifiers = default_access_identifiers,
        is_genexpr          = False
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

    local_expression_temp_inits = _getLocalExpressionTempsInitCode(
        context = context
    )

    if local_expression_temp_inits:
        local_expression_temp_inits = [ local_expression_temp_inits ]
    else:
        local_expression_temp_inits = []

    function_decorator_calls = _getDecoratorsCallCode(
        context         = context,
        decorator_count = decorator_count
    )

    function_doc = getConstantCode(
        context  = context,
        constant = function_doc
    )


    function_locals = function_parameter_decl + local_var_inits + local_expression_temp_inits

    if context.hasLocalsDict():
        function_locals = CodeTemplates.function_dict_setup.split("\n") + function_locals

    if context.needsFrameExceptionKeeper():
        function_locals = CodeTemplates.frame_exceptionkeeper_setup.split("\n") + function_locals

    result = ""

    if context_decl:
        result += CodeTemplates.function_context_body_template % {
            "function_identifier" : function_identifier,
            "context_decl"        : indented( context_decl ),
            "context_free"        : indented( context_free ),
        }

    if closure_variables:
        context_access_function_impl = CodeTemplates.function_context_access_template % {
            "function_identifier" : function_identifier,
        }
    else:
        context_access_function_impl = CodeTemplates.function_context_unused_template


    module_identifier = getModuleAccessCode( context = context )

    function_name_obj = getConstantCode(
        context  = context,
        constant = function_name
    )


    result += CodeTemplates.function_body_template % {
        "function_name"                : function_name,
        "function_name_obj"            : function_name_obj,
        "function_identifier"          : function_identifier,
        "context_access_function_impl" : context_access_function_impl,
        "parameter_entry_point_code"   : entry_point_code,
        "parameter_objects_decl"       : parameter_objects_decl,
        "function_locals"              : indented( function_locals, 2 ),
        "function_body"                : indented( function_codes, 2 ),
        "module_identifier"            : module_identifier,
        "name_identifier"              : getConstantCode(
            context  = context,
            constant = function_name
        ),
        "filename_identifier"          : getConstantCode(
            context  = context,
            constant = source_ref.getFilename()
        ),
    }

    if context_decl:
        result += CodeTemplates.make_function_with_context_template % {
            "function_name"              : function_name,
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
            "function_decorator_calls"   : indented( function_decorator_calls ),
            "context_copy"               : indented( context_copy ),
            "function_doc"               : function_doc,
            "filename_identifier"        : getConstantCode(
                context  = context,
                constant = source_ref.getFilename()
            ),
            "line_number"                : source_ref.getLineNumber(),
            "arg_count"                  : parameters.getArgumentCount(),
            "module_identifier"          : getModuleAccessCode( context = context ),
        }
    else:
        result += CodeTemplates.make_function_without_context_template % {
            "function_name"              : function_name,
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
            "function_decorator_calls"   : indented( function_decorator_calls ),
            "function_doc"               : function_doc,
            "filename_identifier"        : getConstantCode(
                context  = context,
                constant = source_ref.getFilename()
            ),
            "line_number"                : source_ref.getLineNumber(),
            "arg_count"                  : parameters.getArgumentCount(),
            "module_identifier"          : getModuleAccessCode( context = context ),
        }

    return result

def getGeneratorExpressionCode( context, generator_identifier, generator_name, source_ref, \
                                generator_code, generator_conditions, generator_iterateds, \
                                line_number_code, loop_var_codes, closure_variables, \
                                provided_variables ):
    function_name     = "<" + generator_name + ">"

    context_decl = []
    context_copy = []
    function_context_release = []

    function_creation_args = [ "PyObject *iterated" ]

    for closure_variable in closure_variables:
        context_decl.append(
            "PyObjectSharedLocalVariable python_closure_%s;" % closure_variable.getName()
        )
        context_copy.append(
            "_python_context->python_closure_%s.shareWith( python_closure_%s );" % (
                closure_variable.getName(),
                closure_variable.getName()
            )
        )

        function_creation_args.append(
            "PyObjectSharedLocalVariable &python_closure_%s" % closure_variable.getName()
        )

    # Into the context the provided variables must go:
    for provided_variable in provided_variables:
        assert not provided_variable.isClosureReference()

        context_decl.append(
            "PyObjectLocalVariable python_var_%s;" % provided_variable.getName()
        )

    result = ""

    result += CodeTemplates.genexpr_context_body_template % {
        "function_identifier"      : generator_identifier,
        "context_decl"             : indented( context_decl ),
        "function_context_release" : indented( function_context_release ),
    }

    iterator_value_assign = ""

    for count, ( loop_var_code, generator_condition ) in enumerate( zip( loop_var_codes, generator_conditions ) ):
        iterator_value_assign += CodeTemplates.genexpr_iterator_value_assignment % {
            "iterator_index"  : count,
            "assignment_code" : loop_var_code,
            "condition_code"  : generator_condition.getCode()
        }

    iterator_making = ""

    for count, generator_iterated in enumerate( generator_iterateds ):
        iterator_making += CodeTemplates.genexpr_iterator_making % {
            "iterator_index"  : count + 1,
            "iterated_code"   : generator_iterated.getCodeTemporaryRef()
        }

    function_name_obj = getConstantCode(
        context  = context,
        constant = generator_name
    )

    local_expression_temp_inits = _getLocalExpressionTempsInitCode(
        context = context
    )

    if local_expression_temp_inits:
        local_expression_temp_inits += "\n"

    result += CodeTemplates.genexpr_function_template % {
        "function_name"              : function_name,
        "function_identifier"        : generator_identifier,
        "context_decl"               : indented( context_decl ),
        "context_copy"               : indented( context_copy ),
        "function_context_release"   : indented( function_context_release ),
        "iterator_count"             : len( generator_iterateds ) + 1,
        "iterator_making"            : indented( iterator_making.split( "\n" ), 5 ),
        "iterator_value_assign"      : indented( iterator_value_assign, 5 ),
        "function_body"              : getReturnCode( identifier = generator_code ),
        "module_identifier"          : getModuleAccessCode( context = context ),
        "name_identifier"            : getConstantCode(
            context  = context,
            constant = function_name
        ),
        "line_number_code"           : line_number_code,
        "expression_temp_decl"       : local_expression_temp_inits
    }

    result += CodeTemplates.make_genexpr_with_context_template % {
        "function_name_obj"          : function_name_obj,
        "function_identifier"        : generator_identifier,
        "function_creation_args"     : ", ".join( function_creation_args ),
        "context_copy"               : indented( context_copy ),
        "filename_identifier"        : getConstantCode(
            context  = context,
            constant = source_ref.getFilename()
        ),
        "line_number"                : source_ref.getLineNumber(),
        "iterator_count"             : len( generator_iterateds ) + 1,
    }

    return result

def getCurrentLineCode( source_ref ):
    return "_current_line = %d;\n" % source_ref.getLineNumber()

def getCurrentExceptionObjectCode():
    return Identifier( "_exception.getObject()", 0 )

def getTupleUnpackIteratorCode( recursion ):
    return TempVariableIdentifier( "tuple_iterator_%d" % recursion )

def getTupleUnpackLeftValueCode( recursion, count, single_use ):
    if single_use:
        return HolderVariableIdentifier( "tuple_lvalue_%d_%d" % ( recursion, count ) )
    else:
        return TempVariableIdentifier( "tuple_lvalue_%d_%d" % ( recursion, count ) )

def _getClosureVariableDecl( variable ):
    owner = variable.getOwner()

    if not owner.isParentVariableProvider():
        owner = owner.getParentVariableProvider()

    if variable.getReferenced().isShared():
        kind = "PyObjectSharedLocalVariable"
    elif variable.getReferenced().isParameterVariable():
        if variable.getReferenced().getHasDelIndicator():
            kind = "PyObjectLocalParameterVariableWithDel"
        else:
            kind = "PyObjectLocalParameterVariableNoDel"
    else:
        kind = "PyObjectLocalVariable"

    return "%s &_python_closure_%s" % ( kind, variable.getName() )

def getClassCreationCode( context, code_name, dict_identifier, bases_identifier, decorators ):
    args = decorators + [ bases_identifier, dict_identifier ]

    return Identifier(
        "MAKE_CLASS_%s( %s )" % (
            code_name,
            getEvalOrderedCode(
                context = context,
                args    = getCodeTemporaryRefs( args )
            )
        ),
        1
    )

def getClassDictCreationCode( context, class_identifier, closure_variables ):
    args = getClosureVariableProvisionCode(
        context           = context,
        closure_variables = closure_variables
    )

    return Identifier(
        "%s( %s )" % (
            class_identifier,
            ", ".join( args )
        ),
        1
    )

def _getClassCreationArgs( decorator_count, closure_variables ):
    class_creation_args = [
        "PyObject *decorator_%d" % ( d + 1 )
        for d in
        range( decorator_count )
    ]
    class_creation_args.append( "PyObject *bases" )
    class_creation_args.append( "PyObject *dict" )

    class_dict_args = []

    for closure_variable in closure_variables:
        class_dict_args.append(
            _getClosureVariableDecl(
                variable     = closure_variable
            )
        )

    return class_creation_args, class_dict_args

def getClassDecl( context, class_identifier, closure_variables, decorator_count ):
    class_creation_args, class_dict_args = _getClassCreationArgs(
        closure_variables = closure_variables,
        decorator_count   = decorator_count
    )

    return CodeTemplates.class_decl_template % {
        "class_identifier"    : class_identifier,
        "class_dict_args"     : ", ".join( class_dict_args ),
        "class_creation_args" : getEvalOrderedCode(
            context = context,
            args    = class_creation_args
        )
    }

def getClassCode( context, class_def, class_name, class_filename, class_identifier, \
                  class_variables, closure_variables, decorator_count, module_name, class_doc, \
                  class_codes, metaclass_variable ):
    assert metaclass_variable.isModuleVariable()

    class_var_decl = []

    for class_variable in class_variables:
        if class_variable.getName() == "__module__":
            init_from = getConstantCode(
                constant   = module_name,
                context    = context,
            )
        elif class_variable.getName() == "__doc__":
            init_from = getConstantCode(
                constant = class_doc,
                context  = context
            )
        else:
            init_from = None

        class_var_decl.append(
            _getLocalVariableInitCode(
                context       = context,
                variable      = class_variable,
                init_from     = init_from,
                needs_no_free = True,
                in_context    = False,
                mangle_name   = class_name
            )
        )

    local_expression_temp_inits = _getLocalExpressionTempsInitCode(
        context = context
    )

    if local_expression_temp_inits:
        local_expression_temp_inits = [ local_expression_temp_inits ]
    else:
        local_expression_temp_inits = []

    if context.hasLocalsDict():
        class_locals = CodeTemplates.function_dict_setup.split("\n") + class_var_decl + local_expression_temp_inits
    else:
        class_locals = class_var_decl + local_expression_temp_inits

    if context.needsFrameExceptionKeeper():
        class_locals = CodeTemplates.frame_exceptionkeeper_setup.split("\n") + class_locals

    class_creation_args, class_dict_args = _getClassCreationArgs(
        closure_variables = closure_variables,
        decorator_count   = decorator_count
    )

    class_dict_creation = getReturnCode(
        identifier = getLoadLocalsCode(
            provider = class_def.getBody(),
            context  = context,
            mode     = "updated"
        )
    )

    class_decorator_calls = _getDecoratorsCallCode(
        context         = context,
        decorator_count = decorator_count
    )

    context.addGlobalVariableNameUsage(
        var_name = metaclass_variable.getName()
    )

    meta_class_identifier = Identifier(
        "_mvar_%s_%s.asObject()" % (
            context.getModuleCodeName(),
            metaclass_variable.getName()
        ),
        1
    )

    source_ref = class_def.getSourceReference()

    return CodeTemplates.class_dict_template % {
        "class_identifier"      : class_identifier,
        "name_identifier"       : getConstantCode(
            context  = context,
            constant = class_name
        ),
        "module_name"           : getConstantCode(
            constant = context.getModuleName(),
            context  = context
        ),
        "filename_identifier"   : getConstantCode(
            constant = source_ref.getFilename(),
            context  = context
        ),
        "line_number"           : source_ref.getLineNumber(),
        "class_dict_args"       : ", ".join( class_dict_args ),
        "class_creation_args"   : getEvalOrderedCode(
            context = context,
            args    = class_creation_args
        ),
        "class_var_decl"        : indented( class_locals ),
        "class_dict_creation"   : indented( class_dict_creation, 2 ),
        "class_decorator_calls" : indented( class_decorator_calls ),
        "class_body"            : indented( class_codes, 2 ),
        "module_identifier"     : getModuleAccessCode( context = context ),
        "metaclass_global_test" : getVariableTestCode(
            context  = context,
            variable = metaclass_variable
        ),
        "metaclass_global_var"  : meta_class_identifier.getCodeTemporaryRef()
    }

def getDefineGuardedCode( code, define ):
    return "#ifdef %(define)s\n%(code)s\n#endif" % {
        "define" : define,
        "code"   : code
    }

def getRawStringLiteralCode( value ):
    return CppRawStrings.encodeString( value )

def getStatementTrace( source_desc, statement_repr ):
    return 'puts( "Execute: %s "%s );' % (
        source_desc,
        getRawStringLiteralCode( statement_repr )
    )


def _getConstantsDeclarationCode( context, for_header ):
    statements = []

    for _constant_desc, constant_identifier in context.getConstants():
        if for_header:
            declaration = 'extern PyObject *%s;' % constant_identifier
        else:
            declaration = 'PyObject *%s;' % constant_identifier

        statements.append( declaration )

    return "\n".join( statements )

# TODO: The determation of this should already happen in TreeBuilding or in a helper not
# during code generation.
_match_attribute_names = re.compile( r"[a-zA-Z_][a-zA-Z0-9_]*$" )

def _isAttributeName( value ):
    return _match_attribute_names.match( value )

def _getUnstreamCode( constant_value, constant_type, constant_identifier ):
    saved = getStreamedConstant(
        constant_value = constant_value,
        constant_type  = constant_type
    )

    if str is unicode:
        saved = saved.decode( "utf_8" )

    return "%s = UNSTREAM_CONSTANT( %s, %d );" % (
        constant_identifier,
        CppRawStrings.encodeString( saved ),
        len( saved )
    )

def _getConstantsDefinitionCode( context ):
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

        # Use shortest code for ints and longs, except when they are big, then fall
        # fallback to pickling.
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

        if constant_type is tuple and constant_value == ():
            statements.append(
                "%s = PyTuple_New( 0 );" % constant_identifier
            )

        if constant_type is list and constant_value == []:
            statements.append(
                "%s = PyList_New( 0 );" % constant_identifier
            )

        if constant_type is set and constant_value == set():
            statements.append(
                "%s = PySet_New( NULL );" % constant_identifier
            )

        if constant_type in ( tuple, list, float, complex, unicode, int, long, dict, frozenset, set ):
            statements.append(
                _getUnstreamCode( constant_value, constant_type, constant_identifier )
            )
        elif constant_type is str:
            statements.append(
                '%s = UNSTREAM_STRING( %s, %d, %d );assert( %s );' % (
                    constant_identifier,
                    CppRawStrings.encodeString( constant_value ),
                    len(constant_value),
                    1 if _isAttributeName( constant_value ) else 0,
                    constant_identifier
                )
            )
        elif constant_value in ( None, True, False ):
            pass
        else:
            assert False, (type(constant_value), constant_value, constant_identifier)

    return indented( statements )

def getReversionMacrosCode( context ):
    reverse_macros = []
    noreverse_macros = []

    for value in sorted( context.getEvalOrdersUsed() ):
        assert type( value ) is int

        reverse_macros.append(
            CodeTemplates.template_reverse_macro % {
                "count"    : value,
                "args"     : ", ".join(
                    "arg%s" % (d+1) for d in range( value )
                ),
                "expanded" : ", ".join(
                    "arg%s" % (d+1) for d in reversed( range( value ) )
                )
            }
        )

        noreverse_macros.append(
            CodeTemplates.template_noreverse_macro % {
                "count"    : value,
                "args"     : ", ".join(
                    "arg%s" % (d+1) for d in range( value )
                )
            }
        )

    reverse_macros_declaration = CodeTemplates.template_reverse_macros_declaration % {
        "reverse_macros" : "\n".join( reverse_macros ),
        "noreverse_macros" : "\n".join( noreverse_macros )
    }

    return CodeTemplates.template_header_guard % {
        "header_guard_name" : "__NUITKA_REVERSES_H__",
        "header_body"       : reverse_macros_declaration
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
